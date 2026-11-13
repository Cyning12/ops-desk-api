#!/usr/bin/env python3
"""R-4 金样评测 runner（task golden-query-set-v1）。

加载 queries_v1.yaml → 逐条 hybrid_recall →（可选 CE rerank）→ grade_chunks → decide
（复用 app/ops/rag 生产同路径函数，不旁路重写）→ 卫生过滤后断言 → 出报告。

用法：
  .venv/bin/python evals/golden/run_eval.py                  # 全量
  .venv/bin/python evals/golden/run_eval.py --limit 3        # 冒烟
  .venv/bin/python evals/golden/run_eval.py --stability 0    # 跳过评级稳定性抽查
  .venv/bin/python evals/golden/run_eval.py --out reports/r4.yaml
  .venv/bin/python evals/golden/run_eval.py --out reports/r4-A.yaml --resume
  RAG_RERANK_ENABLED=true .venv/bin/python evals/golden/run_eval.py --out reports/r4-R.yaml --stability 0
"""
from __future__ import annotations

import argparse
import ast
import asyncio
import os
import re
import sys
import tempfile
from collections import defaultdict
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.db.session import AsyncSessionLocal  # noqa: E402
from app.llm.factory import get_llm_provider  # noqa: E402
from app.ops.rag.embedder import Embedder, get_query_embedder  # noqa: E402
from app.ops.rag.grader import decide, grade_chunks, grader_prompt_version  # noqa: E402
from app.ops.rag.reranker import (  # noqa: E402
    recall_k_each,
    rerank_candidates,
    rerank_chunks,
    rerank_enabled,
    rerank_min_score,
    rerank_score_ratio,
)
from app.ops.rag.retrieve import RetrievedChunk, hybrid_recall_detail  # noqa: E402

# P0' T2a：app/ops/chat/rag_nodes 已删除，GRADER 默认值内联承接（语义逐字保持）
GRADER_PROVIDER = os.getenv("RAG_GRADER_PROVIDER", "siliconflow")
GRADER_MODEL = os.getenv("RAG_GRADER_MODEL", "Qwen/Qwen3.6-27B")

DEFAULT_QUERIES = Path(__file__).resolve().parent / "queries_v1.yaml"
DEFAULT_DENYLIST = Path(__file__).resolve().parent / "hygiene_denylist.yaml"

# 与 grader._RANK 对齐（断言用；不改生产模块）
_RANK = {
    "irrelevant": 0,
    "weak": 1,
    "relevant": 2,
    "exact": 3,
}

# 召回多取若干，卫生过滤后再截 top-5 送给 grader（避免污染槽位挤掉真命中）
RECALL_POOL = 15
GRADE_TOP_N = 5


def recall_knobs() -> tuple[int, int, bool]:
    """返回 (k_each, coarse_top_n, rerank_on)。

    rerank 开启：对齐生产 CE（默认 k_each=20、候选 M=20）；
    关闭：保持历史 runner（k_each=10、卫生池 RECALL_POOL）。
    """
    if rerank_enabled():
        return recall_k_each(), rerank_candidates(), True
    return 10, RECALL_POOL, False


def arm_report_meta() -> dict[str, Any]:
    """写入报告头/summary，便于与误跑 Normal 对照。"""
    k_each, coarse_n, on = recall_knobs()
    meta: dict[str, Any] = {
        "arm": "rerank" if on else "normal",
        "rerank_enabled": on,
        "recall_k_each": k_each,
        "coarse_top_n": coarse_n,
        "grader_prompt": grader_prompt_version(),
    }
    if on:
        meta["rerank_model"] = os.getenv("RAG_RERANK_MODEL") or "BAAI/bge-reranker-v2-m3"
        meta["rerank_min_score"] = rerank_min_score()
        meta["rerank_score_ratio"] = rerank_score_ratio()
        meta["compare_with"] = "reports/r4-R-misrun-no-ce.yaml"
    return meta


@dataclass
class DenyRule:
    source_type: str | None = None
    source_id_contains: str | None = None
    note: str = ""


@dataclass
class CaseResult:
    id: str
    quadrant: str
    top5: list[str]
    filtered_out: list[str]
    recall_at5: str | None
    best_relevance: str | None
    min_relevance: str | None
    citation_in_hits: str | None
    must_refuse: str | None
    gate_action: str | None
    verdict: str
    fail_reasons: list[str] = field(default_factory=list)
    semantic_hits: list[str] = field(default_factory=list)
    keyword_hits: list[str] = field(default_factory=list)


def load_golden(path: Path) -> list[dict[str, Any]]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    cases = data.get("golden") if isinstance(data, dict) else data
    if not isinstance(cases, list) or not cases:
        raise SystemExit(f"金样为空或格式错误: {path}")
    return cases


def load_denylist(path: Path) -> list[DenyRule]:
    if not path.exists():
        return []
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    rules = []
    for item in data.get("denylist") or []:
        rules.append(
            DenyRule(
                source_type=item.get("source_type"),
                source_id_contains=item.get("source_id_contains"),
                note=str(item.get("note") or ""),
            )
        )
    return rules


def golden_query_texts(cases: list[dict[str, Any]]) -> list[str]:
    """所有金样 query 原文（用于 content 子串污染检测）。"""
    return [str(c["query"]).strip() for c in cases if c.get("query")]


def is_denylisted(chunk: RetrievedChunk, rules: list[DenyRule]) -> bool:
    for r in rules:
        if r.source_type and chunk.source_type != r.source_type:
            continue
        if r.source_id_contains and r.source_id_contains not in chunk.source_id:
            continue
        if r.source_type or r.source_id_contains:
            return True
    return False


def contains_golden_query(content: str, queries: list[str]) -> bool:
    """content 是否含任一金样原文（契约#13：自引用污染）。"""
    if not content:
        return False
    # 过短子串易误杀
    return any(len(q) >= 12 and q in content for q in queries)


def apply_hygiene(
    chunks: list[RetrievedChunk],
    queries: list[str],
    rules: list[DenyRule],
) -> tuple[list[RetrievedChunk], list[RetrievedChunk]]:
    """断言前卫生过滤。返回 (kept, removed)。

    任一金样原文出现在 content 中即剔除（契约#13：污染源正是写入金样原文的文档）。
    """
    kept: list[RetrievedChunk] = []
    removed: list[RetrievedChunk] = []
    for c in chunks:
        if is_denylisted(c, rules) or contains_golden_query(c.content, queries):
            removed.append(c)
        else:
            kept.append(c)
    return kept, removed


def hit_expect(chunks: list[RetrievedChunk], expect_hit: dict | None) -> bool:
    if not expect_hit:
        return False
    sid = str(expect_hit.get("source_id", ""))
    st = expect_hit.get("source_type")
    return any(c.source_id == sid and (st is None or c.source_type == st) for c in chunks)


def best_relevance_value(grades_by_id: dict[int, str], chunks: list[RetrievedChunk]) -> str | None:
    if not chunks:
        return None
    vals = [grades_by_id.get(c.id, "irrelevant") for c in chunks]
    return max(vals, key=lambda v: _RANK.get(v, 0))


def best_on_expect(
    grades_by_id: dict[int, str],
    chunks: list[RetrievedChunk],
    expect_hit: dict | None,
) -> str | None:
    if not expect_hit:
        return None
    sid = str(expect_hit.get("source_id", ""))
    st = expect_hit.get("source_type")
    matched = [
        grades_by_id.get(c.id, "irrelevant")
        for c in chunks
        if c.source_id == sid and (st is None or c.source_type == st)
    ]
    if not matched:
        return None
    return max(matched, key=lambda v: _RANK.get(v, 0))


def assert_case(
    case: dict[str, Any],
    clean_top: list[RetrievedChunk],
    grades_by_id: dict[int, str],
    gate_action: str,
) -> CaseResult:
    """按 yaml assert 字段判定 pass/fail。"""
    spec = case.get("assert") or {}
    quadrant = str(case.get("quadrant") or "")
    expect_hit = case.get("expect_hit")
    fails: list[str] = []

    recall_v = min_v = cite_v = refuse_v = None
    best = best_relevance_value(grades_by_id, clean_top)

    if quadrant == "negative" or spec.get("must_refuse"):
        max_rel = str(spec.get("max_relevance") or "weak")
        if best is not None and _RANK.get(best, 0) > _RANK.get(max_rel, 1):
            fails.append(f"max_relevance: got {best} > {max_rel}")
            refuse_v = "fail"
        else:
            refuse_v = "pass"
        if spec.get("must_refuse"):
            if gate_action != "refuse":
                fails.append(f"must_refuse: gate_action={gate_action}")
                refuse_v = "fail"
            else:
                refuse_v = "pass" if refuse_v != "fail" else "fail"
    else:
        # recall@k
        k = int(spec.get("recall_at") or 5)
        pool = clean_top[:k]
        ok_recall = hit_expect(pool, expect_hit)
        recall_v = "pass" if ok_recall else "fail"
        if not ok_recall:
            fails.append(f"recall@{k}: {expect_hit} not in top")

        # min_relevance：期望文档上的最高评级
        min_rel = str(spec.get("min_relevance") or "relevant")
        on_hit = best_on_expect(grades_by_id, pool, expect_hit)
        if on_hit is None:
            min_v = "fail"
            fails.append("min_relevance: expect_hit 未召回，无法评级")
        elif _RANK.get(on_hit, 0) < _RANK.get(min_rel, 2):
            min_v = "fail"
            fails.append(f"min_relevance: got {on_hit} < {min_rel}")
        else:
            min_v = "pass"

        # citation_in_hits：可引用的 expect_hit 必须仍在卫生后命中集
        if spec.get("citation_in_hits"):
            ok_cite = hit_expect(pool, expect_hit)
            cite_v = "pass" if ok_cite else "fail"
            if not ok_cite:
                fails.append("citation_in_hits: expect_hit 不在命中集")

        # expect_relevance 地板（契约 Q5：低于预判即 fail）
        expect_rel = case.get("expect_relevance")
        if expect_rel and on_hit is not None and _RANK.get(on_hit, 0) < _RANK.get(
            str(expect_rel), 0
        ):
            fails.append(f"expect_relevance: got {on_hit} < {expect_rel}")

    verdict = "pass" if not fails else "fail"
    return CaseResult(
        id=str(case["id"]),
        quadrant=quadrant,
        top5=[c.anchor for c in clean_top[:GRADE_TOP_N]],
        filtered_out=[],
        recall_at5=recall_v,
        best_relevance=best,
        min_relevance=min_v,
        citation_in_hits=cite_v,
        must_refuse=refuse_v,
        gate_action=gate_action,
        verdict=verdict,
        fail_reasons=fails,
    )


def quadrant_recall_summary(results: list[CaseResult]) -> dict[str, str]:
    by_q: dict[str, list[CaseResult]] = defaultdict(list)
    for r in results:
        if r.recall_at5 is not None:
            by_q[r.quadrant].append(r)
    out: dict[str, str] = {}
    for q, rows in sorted(by_q.items()):
        ok = sum(1 for r in rows if r.recall_at5 == "pass")
        out[q] = f"{ok}/{len(rows)}"
    return out


def grade_stability_rate(runs: list[list[str]]) -> float | None:
    """runs: 每次评级得到的 best 列表；返回完全一致占比。"""
    if not runs or len(runs) < 2:
        return None
    # 按位置：每个 case 的多次 best 是否全同
    n_cases = len(runs[0])
    if any(len(r) != n_cases for r in runs):
        return None
    agree = 0
    for i in range(n_cases):
        vals = {runs[j][i] for j in range(len(runs))}
        if len(vals) == 1:
            agree += 1
    return agree / n_cases if n_cases else None


def build_report(
    results: list[CaseResult],
    *,
    embed_name: str,
    grader_model: str,
    stability: float | None,
    corpus_n: int | None,
    run_id: str | None = None,
    extra_summary: dict[str, Any] | None = None,
) -> dict[str, Any]:
    passed = sum(1 for r in results if r.verdict == "pass")
    neg = [r for r in results if r.quadrant == "negative"]
    neg_ok = sum(1 for r in neg if r.verdict == "pass")
    summary: dict[str, Any] = {
        "pass": f"{passed}/{len(results)}",
        "recall_at5_by_quadrant": quadrant_recall_summary(results),
        "negative_refuse": f"{neg_ok}/{len(neg)}" if neg else "0/0",
        "grade_stability_agree": (
            round(stability, 3) if stability is not None else None
        ),
        # 观测 SPEC 三字段（已签 2026-08-07）
        "measurement_source": "observed",
        "confidence": "low",  # 小样本老实标
        "comparability": "not_comparable",  # 首跑无基线
    }
    if extra_summary:
        summary.update(extra_summary)
    arm = arm_report_meta()
    summary.update(arm)
    report: dict[str, Any] = {
        "run": run_id or f"eval-rag-{datetime.now(UTC).strftime('%Y%m%d-%H%M%S')}-r4",
        "arm": arm["arm"],
        "rerank_enabled": arm["rerank_enabled"],
        "recall_k_each": arm["recall_k_each"],
        "coarse_top_n": arm["coarse_top_n"],
        "embed": embed_name,
        "grader": grader_model,
        "corpus": f"ops_knowledge_chunks(N={corpus_n if corpus_n is not None else '?'})",
        "results": [asdict(r) for r in results],
        "summary": summary,
    }
    if arm.get("rerank_model"):
        report["rerank_model"] = arm["rerank_model"]
    if arm.get("compare_with"):
        report["compare_with"] = arm["compare_with"]
    return report


def write_report(path: Path, report: dict[str, Any]) -> None:
    """原子写入报告（先写临时文件再 replace），每条完成后可安全落盘。"""
    path.parent.mkdir(parents=True, exist_ok=True)
    text = yaml.safe_dump(report, allow_unicode=True, sort_keys=False)
    fd, tmp_name = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
    )
    tmp = Path(tmp_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(text)
            f.flush()
            os.fsync(f.fileno())
        tmp.replace(path)
    except Exception:
        tmp.unlink(missing_ok=True)
        raise


def load_existing_results(path: Path) -> tuple[list[CaseResult], dict[str, Any]]:
    """从已有报告加载 CaseResult 列表与元信息（供 --resume）。"""
    if not path.exists():
        return [], {}
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    results: list[CaseResult] = []
    for row in data.get("results") or []:
        results.append(
            CaseResult(
                id=str(row["id"]),
                quadrant=str(row.get("quadrant") or ""),
                top5=list(row.get("top5") or []),
                filtered_out=list(row.get("filtered_out") or []),
                recall_at5=row.get("recall_at5"),
                best_relevance=row.get("best_relevance"),
                min_relevance=row.get("min_relevance"),
                citation_in_hits=row.get("citation_in_hits"),
                must_refuse=row.get("must_refuse"),
                gate_action=row.get("gate_action"),
                verdict=str(row.get("verdict") or "fail"),
                fail_reasons=list(row.get("fail_reasons") or []),
                semantic_hits=list(row.get("semantic_hits") or []),
                keyword_hits=list(row.get("keyword_hits") or []),
            )
        )
    meta = {
        "run": data.get("run"),
        "embed": data.get("embed"),
        "grader": data.get("grader"),
        "summary": data.get("summary") or {},
    }
    return results, meta


_LOG_CASE_RE = re.compile(
    r"^\[(?P<i>\d+)/(?P<n>\d+)\]\s+(?P<id>\S+)\s+·\s+(?P<quadrant>\S+)\s+…"
)
_LOG_SEM_RE = re.compile(r"^\s*→\s*sem=(?P<v>.+)\s*$")
_LOG_KW_RE = re.compile(r"^\s*→\s*kw\s*=(?P<v>.+)\s*$")
_LOG_VERDICT_RE = re.compile(
    r"^\s*→\s*(?P<flag>PASS|FAIL)\s+"
    r"top5=(?P<top5>.+?)\s+"
    r"best=(?P<best>\S+)\s+"
    r"filtered=(?P<filtered>.+?)\s+"
    r"reasons=(?P<reasons>.+)\s*$"
)


def _literal_list(raw: str) -> list[Any]:
    return list(ast.literal_eval(raw))


def infer_assert_fields(
    *,
    quadrant: str,
    verdict: str,
    reasons: list[str],
) -> dict[str, Any]:
    """从日志 verdict/reasons 推断 assert 字段（gate_action 日志未打印 → null）。"""
    if quadrant == "negative":
        return {
            "recall_at5": None,
            "min_relevance": None,
            "citation_in_hits": None,
            "must_refuse": "pass" if verdict == "pass" else "fail",
            "gate_action": None,
        }
    recall_fail = any(r.startswith("recall@") for r in reasons)
    min_fail = any("min_relevance" in r for r in reasons)
    cite_fail = any("citation_in_hits" in r for r in reasons)
    return {
        "recall_at5": "fail" if recall_fail else "pass",
        "min_relevance": "fail" if min_fail else "pass",
        "citation_in_hits": "fail" if (cite_fail or recall_fail) else "pass",
        "must_refuse": None,
        "gate_action": None,
    }


def parse_eval_log(text: str) -> list[CaseResult]:
    """从 run_eval 终端日志恢复 CaseResult（主评测行；不含稳定性抽查）。"""
    results: list[CaseResult] = []
    cur: dict[str, Any] | None = None
    for line in text.splitlines():
        m = _LOG_CASE_RE.match(line)
        if m:
            cur = {
                "id": m.group("id"),
                "quadrant": m.group("quadrant"),
                "sem": [],
                "kw": [],
            }
            continue
        if cur is None:
            continue
        m = _LOG_SEM_RE.match(line)
        if m:
            cur["sem"] = _literal_list(m.group("v"))
            continue
        m = _LOG_KW_RE.match(line)
        if m:
            cur["kw"] = _literal_list(m.group("v"))
            continue
        m = _LOG_VERDICT_RE.match(line)
        if not m:
            continue
        flag = m.group("flag")
        best_raw = m.group("best")
        best = None if best_raw == "None" else best_raw
        reasons = [str(x) for x in _literal_list(m.group("reasons"))]
        verdict = "pass" if flag == "PASS" else "fail"
        fields = infer_assert_fields(
            quadrant=str(cur["quadrant"]), verdict=verdict, reasons=reasons
        )
        results.append(
            CaseResult(
                id=str(cur["id"]),
                quadrant=str(cur["quadrant"]),
                top5=[str(x) for x in _literal_list(m.group("top5"))],
                filtered_out=[str(x) for x in _literal_list(m.group("filtered"))],
                recall_at5=fields["recall_at5"],
                best_relevance=best,
                min_relevance=fields["min_relevance"],
                citation_in_hits=fields["citation_in_hits"],
                must_refuse=fields["must_refuse"],
                gate_action=fields["gate_action"],
                verdict=verdict,
                fail_reasons=reasons,
                semantic_hits=[str(x) for x in cur["sem"]],
                keyword_hits=[str(x) for x in cur["kw"]],
            )
        )
        cur = None
    return results


async def _corpus_count() -> int | None:
    from sqlalchemy import text

    try:
        async with AsyncSessionLocal() as session:
            n = (await session.execute(text("SELECT count(*) FROM ops_knowledge_chunks"))).scalar()
            return int(n) if n is not None else None
    except Exception:
        return None


async def eval_one(
    case: dict[str, Any],
    *,
    embedder: Embedder,
    provider,
    queries: list[str],
    rules: list[DenyRule],
    model: str,
) -> CaseResult:
    query = str(case["query"])
    qvec = (await asyncio.to_thread(embedder.embed, [query]))[0]
    k_each, coarse_n, use_rerank = recall_knobs()
    async with AsyncSessionLocal() as session:
        recall = await hybrid_recall_detail(
            session, query, qvec, k_each=k_each, top_n=coarse_n
        )
    raw = recall.fused
    sem_hits = [c.anchor for c in recall.semantic]
    kw_hits = [c.anchor for c in recall.keyword]
    # CE：对粗排整池精排保留全序，再卫生过滤取 top-5（与生产「精排后再截断」同序）
    if use_rerank and raw:
        raw = await asyncio.to_thread(rerank_chunks, query, raw, len(raw))
    kept, removed = apply_hygiene(raw, queries, rules)
    clean_top = kept[:GRADE_TOP_N]

    if not clean_top:
        decision = decide([])
        result = assert_case(case, [], {}, decision.action)
        result.filtered_out = [c.anchor for c in removed]
        result.semantic_hits = sem_hits
        result.keyword_hits = kw_hits
        return result

    grades = await grade_chunks(provider, query, clean_top, model=model)
    decision = decide(grades)
    grades_by_id = {g.chunk_id: g.relevance.value for g in grades}
    result = assert_case(case, clean_top, grades_by_id, decision.action)
    result.filtered_out = [c.anchor for c in removed]
    result.semantic_hits = sem_hits
    result.keyword_hits = kw_hits
    return result


async def run_stability(
    sample: list[dict[str, Any]],
    *,
    embedder: Embedder,
    provider,
    queries: list[str],
    rules: list[DenyRule],
    model: str,
    repeats: int = 3,
) -> float | None:
    if not sample or repeats < 2:
        return None
    # 先固定召回（含可选 CE），再对同一 clean_top 重复评级
    k_each, coarse_n, use_rerank = recall_knobs()
    tops: list[list[RetrievedChunk]] = []
    for case in sample:
        query = str(case["query"])
        qvec = (await asyncio.to_thread(embedder.embed, [query]))[0]
        async with AsyncSessionLocal() as session:
            recall = await hybrid_recall_detail(
                session, query, qvec, k_each=k_each, top_n=coarse_n
            )
        raw = recall.fused
        if use_rerank and raw:
            raw = await asyncio.to_thread(rerank_chunks, query, raw, len(raw))
        kept, _ = apply_hygiene(raw, queries, rules)
        tops.append(kept[:GRADE_TOP_N])

    runs: list[list[str]] = []
    for _ in range(repeats):
        bests: list[str] = []
        for case, top in zip(sample, tops, strict=True):
            if not top:
                bests.append("irrelevant")
                continue
            grades = await grade_chunks(provider, str(case["query"]), top, model=model)
            decision = decide(grades)
            bests.append(decision.best.value)
        runs.append(bests)
    return grade_stability_rate(runs)


def pick_stability_sample(cases: list[dict[str, Any]], n: int = 4) -> list[dict[str, Any]]:
    """每象限抽 1 条（最多 n）。"""
    seen: set[str] = set()
    out: list[dict[str, Any]] = []
    for c in cases:
        q = str(c.get("quadrant") or "")
        if q in seen:
            continue
        seen.add(q)
        out.append(c)
        if len(out) >= n:
            break
    return out


async def async_main(args: argparse.Namespace) -> int:
    # --from-log：不调模型，仅从终端日志恢复报告
    if args.from_log:
        if not args.out:
            raise SystemExit("--from-log 须同时指定 --out")
        log_path = Path(args.from_log)
        results = parse_eval_log(log_path.read_text(encoding="utf-8"))
        if not results:
            raise SystemExit(f"日志未解析到任何 case: {log_path}")
        report = build_report(
            results,
            embed_name=args.embed_name or "BAAI/bge-m3",
            grader_model=args.grader_name or os.getenv("RAG_GRADER_MODEL", GRADER_MODEL),
            stability=None,
            corpus_n=args.corpus_n,
            extra_summary={
                "recovered_from_log": str(log_path),
                "gate_action_note": "日志未含 gate_action，已置 null",
            },
        )
        out = Path(args.out)
        write_report(out, report)
        summary = report["summary"]
        print(
            f"从日志恢复 {len(results)} 条 → {out} · "
            f"pass={summary['pass']} recall_by_q={summary['recall_at5_by_quadrant']}"
        )
        failed = sum(1 for r in results if r.verdict == "fail")
        return 1 if failed else 0

    cases = load_golden(Path(args.queries))
    if args.limit:
        cases = cases[: args.limit]
    rules = load_denylist(Path(args.denylist))
    queries = golden_query_texts(load_golden(Path(args.queries)))  # 全量 query 作污染词典

    out_path = Path(args.out) if args.out else None
    results: list[CaseResult] = []
    done_ids: set[str] = set()
    run_id = f"eval-rag-{datetime.now(UTC).strftime('%Y%m%d-%H%M%S')}-r4"
    embed_name = "BAAI/bge-m3"
    model = os.getenv("RAG_GRADER_MODEL", GRADER_MODEL)

    if args.resume:
        if not out_path:
            raise SystemExit("--resume 须同时指定 --out")
        results, meta = load_existing_results(out_path)
        done_ids = {r.id for r in results}
        if meta.get("run"):
            run_id = str(meta["run"])
        if meta.get("embed"):
            embed_name = str(meta["embed"])
        if meta.get("grader"):
            model = str(meta["grader"])
        print(f"resume: 已有 {len(results)} 条 · skip={sorted(done_ids)}", flush=True)

    pending = [c for c in cases if str(c["id"]) not in done_ids]
    if not pending and results:
        print("resume: 无待跑 case，仅重算 summary / 可选稳定性", flush=True)

    # 对齐生产查询路径：默认 SiliconFlow ApiEmbedder（避免本机 ST 冷启动/崩溃）
    embedder = get_query_embedder()
    embed_name = embedder.name
    provider = get_llm_provider(os.getenv("RAG_GRADER_PROVIDER", GRADER_PROVIDER))
    model = os.getenv("RAG_GRADER_MODEL", GRADER_MODEL)
    corpus_n = await _corpus_count()
    arm = arm_report_meta()
    print(
        f"arm={arm['arm']} rerank={arm['rerank_enabled']} "
        f"k_each={arm['recall_k_each']} coarse_top_n={arm['coarse_top_n']} "
        f"embed={embed_name} grader={model}",
        flush=True,
    )

    def _checkpoint(stability: float | None = None, note: str | None = None) -> None:
        if not out_path:
            return
        extra_summary: dict[str, Any] = {"partial": True, "completed": len(results)}
        if note:
            extra_summary["note"] = note
        report = build_report(
            results,
            embed_name=embed_name,
            grader_model=model,
            stability=stability,
            corpus_n=corpus_n,
            run_id=run_id,
            extra_summary=extra_summary,
        )
        write_report(out_path, report)

    total = len(cases)
    for case in pending:
        i = next(j for j, c in enumerate(cases, 1) if c["id"] == case["id"])
        print(f"[{i}/{total}] {case['id']} · {case.get('quadrant')} …", flush=True)
        try:
            r = await eval_one(
                case,
                embedder=embedder,
                provider=provider,
                queries=queries,
                rules=rules,
                model=model,
            )
        except Exception as e:
            _checkpoint(note=f"interrupted_at={case['id']}: {type(e).__name__}: {e}")
            print(f"  → ERROR {type(e).__name__}: {e} · 已 checkpoint → {out_path}", flush=True)
            raise
        flag = "PASS" if r.verdict == "pass" else "FAIL"
        print(
            f"  → sem={r.semantic_hits}\n"
            f"  → kw ={r.keyword_hits}\n"
            f"  → {flag} top5={r.top5} best={r.best_relevance} "
            f"filtered={r.filtered_out} reasons={r.fail_reasons}",
            flush=True,
        )
        results.append(r)
        _checkpoint()

    stability = None
    if args.stability > 0:
        sample = pick_stability_sample(cases, n=args.stability)
        print(f"评级稳定性抽查 ×3 · sample={[c['id'] for c in sample]}", flush=True)
        try:
            stability = await run_stability(
                sample,
                embedder=embedder,
                provider=provider,
                queries=queries,
                rules=rules,
                model=model,
                repeats=3,
            )
            print(f"  → agree={stability}", flush=True)
        except Exception as e:
            print(
                f"  → 稳定性抽查失败（主结果已保留）: {type(e).__name__}: {e}",
                flush=True,
            )
            _checkpoint(note=f"stability_failed: {type(e).__name__}: {e}")

    report = build_report(
        results,
        embed_name=embed_name,
        grader_model=model,
        stability=stability,
        corpus_n=corpus_n,
        run_id=run_id,
        extra_summary={"partial": False, "completed": len(results)},
    )
    text = yaml.safe_dump(report, allow_unicode=True, sort_keys=False)
    if out_path:
        write_report(out_path, report)
        print(f"报告写入 {out_path}")
    else:
        print(text)

    summary = report["summary"]
    print(
        f"SUMMARY pass={summary['pass']} "
        f"recall_by_q={summary['recall_at5_by_quadrant']} "
        f"neg={summary['negative_refuse']} "
        f"stability={summary['grade_stability_agree']} "
        f"SPEC={{source={summary['measurement_source']}, "
        f"confidence={summary['confidence']}, "
        f"comparability={summary['comparability']}}}"
    )
    failed = sum(1 for r in results if r.verdict == "fail")
    return 1 if failed else 0


def main() -> None:
    p = argparse.ArgumentParser(description="R-4 golden eval runner")
    p.add_argument("--queries", default=str(DEFAULT_QUERIES))
    p.add_argument("--denylist", default=str(DEFAULT_DENYLIST))
    p.add_argument("--limit", type=int, default=0, help="只跑前 N 条（冒烟）")
    p.add_argument(
        "--stability",
        type=int,
        default=4,
        help="稳定性抽查象限数（0=跳过）",
    )
    p.add_argument("--out", default="", help="报告 yaml 输出路径（建议必填；逐条落盘）")
    p.add_argument(
        "--resume",
        action="store_true",
        help="跳过 --out 中已有 id，从断点续跑",
    )
    p.add_argument(
        "--from-log",
        default="",
        help="从 run_eval 终端日志恢复报告（不调模型；须配 --out）",
    )
    p.add_argument("--embed-name", default="", help="--from-log 时写入的 embed 字段")
    p.add_argument("--grader-name", default="", help="--from-log 时写入的 grader 字段")
    p.add_argument(
        "--corpus-n",
        type=int,
        default=None,
        help="--from-log 时写入的 corpus N（默认未知）",
    )
    args = p.parse_args()
    raise SystemExit(asyncio.run(async_main(args)))


if __name__ == "__main__":
    main()
