#!/usr/bin/env python3
"""R-4 金样评测 runner（task golden-query-set-v1）。

加载 queries_v1.yaml → 逐条 hybrid_recall → grade_chunks → decide
（复用 app/ops/rag 生产同路径函数，不旁路重写）→ 卫生过滤后断言 → 出报告。

用法：
  .venv/bin/python evals/golden/run_eval.py                  # 全量
  .venv/bin/python evals/golden/run_eval.py --limit 3        # 冒烟
  .venv/bin/python evals/golden/run_eval.py --stability 0    # 跳过评级稳定性抽查
  .venv/bin/python evals/golden/run_eval.py --out reports/r4.yaml
"""
from __future__ import annotations

import argparse
import asyncio
import os
import sys
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
from app.ops.chat.rag_nodes import GRADER_MODEL, GRADER_PROVIDER  # noqa: E402
from app.ops.rag.embedder import SentenceTransformerEmbedder  # noqa: E402
from app.ops.rag.grader import decide, grade_chunks  # noqa: E402
from app.ops.rag.retrieve import RetrievedChunk, hybrid_recall_detail  # noqa: E402

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
) -> dict[str, Any]:
    passed = sum(1 for r in results if r.verdict == "pass")
    neg = [r for r in results if r.quadrant == "negative"]
    neg_ok = sum(1 for r in neg if r.verdict == "pass")
    return {
        "run": f"eval-rag-{datetime.now(UTC).strftime('%Y%m%d-%H%M%S')}-r4",
        "embed": embed_name,
        "grader": grader_model,
        "corpus": f"ops_knowledge_chunks(N={corpus_n if corpus_n is not None else '?'})",
        "results": [asdict(r) for r in results],
        "summary": {
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
        },
    }


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
    embedder: SentenceTransformerEmbedder,
    provider,
    queries: list[str],
    rules: list[DenyRule],
    model: str,
) -> CaseResult:
    query = str(case["query"])
    qvec = (await asyncio.to_thread(embedder.embed, [query]))[0]
    async with AsyncSessionLocal() as session:
        recall = await hybrid_recall_detail(
            session, query, qvec, k_each=10, top_n=RECALL_POOL
        )
    raw = recall.fused
    sem_hits = [c.anchor for c in recall.semantic]
    kw_hits = [c.anchor for c in recall.keyword]
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
    embedder: SentenceTransformerEmbedder,
    provider,
    queries: list[str],
    rules: list[DenyRule],
    model: str,
    repeats: int = 3,
) -> float | None:
    if not sample or repeats < 2:
        return None
    # 先固定召回，再对同一 clean_top 重复评级
    tops: list[list[RetrievedChunk]] = []
    for case in sample:
        query = str(case["query"])
        qvec = (await asyncio.to_thread(embedder.embed, [query]))[0]
        async with AsyncSessionLocal() as session:
            recall = await hybrid_recall_detail(
                session, query, qvec, k_each=10, top_n=RECALL_POOL
            )
        kept, _ = apply_hygiene(recall.fused, queries, rules)
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
    cases = load_golden(Path(args.queries))
    if args.limit:
        cases = cases[: args.limit]
    rules = load_denylist(Path(args.denylist))
    queries = golden_query_texts(load_golden(Path(args.queries)))  # 全量 query 作污染词典

    embedder = SentenceTransformerEmbedder()
    provider = get_llm_provider(os.getenv("RAG_GRADER_PROVIDER", GRADER_PROVIDER))
    model = os.getenv("RAG_GRADER_MODEL", GRADER_MODEL)

    results: list[CaseResult] = []
    for i, case in enumerate(cases, 1):
        print(f"[{i}/{len(cases)}] {case['id']} · {case.get('quadrant')} …", flush=True)
        r = await eval_one(
            case,
            embedder=embedder,
            provider=provider,
            queries=queries,
            rules=rules,
            model=model,
        )
        flag = "PASS" if r.verdict == "pass" else "FAIL"
        print(
            f"  → sem={r.semantic_hits}\n"
            f"  → kw ={r.keyword_hits}\n"
            f"  → {flag} top5={r.top5} best={r.best_relevance} "
            f"filtered={r.filtered_out} reasons={r.fail_reasons}",
            flush=True,
        )
        results.append(r)

    stability = None
    if args.stability > 0:
        sample = pick_stability_sample(cases, n=args.stability)
        print(f"评级稳定性抽查 ×3 · sample={[c['id'] for c in sample]}", flush=True)
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

    report = build_report(
        results,
        embed_name=embedder.name,
        grader_model=model,
        stability=stability,
        corpus_n=await _corpus_count(),
    )
    text = yaml.safe_dump(report, allow_unicode=True, sort_keys=False)
    if args.out:
        out = Path(args.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text, encoding="utf-8")
        print(f"报告写入 {out}")
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
    p.add_argument("--out", default="", help="报告 yaml 输出路径")
    args = p.parse_args()
    raise SystemExit(asyncio.run(async_main(args)))


if __name__ == "__main__":
    main()
