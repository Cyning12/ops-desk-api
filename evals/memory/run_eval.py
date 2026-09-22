#!/usr/bin/env python3
"""记忆金样评测 runner（task memory-golden-eval · eval 轨 · **零生产语义改动**）。

仿 evals/golden/run_eval.py 的 YAML 进出 / 报告结构先例，**不抄其实现**：
RAG 指标（recall@5 / best_relevance）与记忆语义不匹配（SPEC R2-S2 已弃复用）。

双模式：
- ``--backend fake``（默认 · CI 确定性 · 不连外网不连 DB）：进程内
  ``FakeEmbedder``（关键词 → 正交基向量，无随机）+ 罐头抽取（金样自带
  ``fake_facts``）+ 内存事实库；但**真实复用**未改一字的生产件：
  ``gate.should_write``（真闸）、``structured_output.extract_json_object`` +
  ``MemoryFactExtraction``（真解析/schema）、``service._fuse_recall``（真融合）。
- ``--backend live``（维护者真跑）：真实 ``get_query_embedder`` + 真实抽取
  provider + 真 PG。独立 tenant=``memory-eval``，跑后 ``revoke_by_source`` +
  租户行清场。缺 key / 外网不通 / DB 不通 → **退出码 2 显式报错**，
  绝不静默降级冒充 fake（failure_paths 钉死）。

指标（SPEC §2 D2）：抽取 precision / 噪声写入率 / 漏记率 · 复述 top1/top3 ·
supersede 正确率。报告头部**写死** SPEC §2 D5 四条门槛与达成情况（防假绿引用）。

扫参（SPEC §2 D3 · ``--sweep``）：half_life {7,30,90} × sim_floor {0.3,0.5,0.7}
× source_weight_extract {0.6,0.8,1.0} 共 27 组。实现方式：运行时**临时覆盖**
service 模块常量调用真 ``_fuse_recall``（with 块内恢复现场，不改文件、
不改生产默认值）；只出建议，改值另 task 按报告裁决。

用法：
  .venv/bin/python evals/memory/run_eval.py --backend fake --out reports/memory_golden_eval_fake.yaml
  .venv/bin/python evals/memory/run_eval.py --backend fake --sweep
  .venv/bin/python evals/memory/run_eval.py --backend live --limit 6   # 维护者小烟跑

退出码：0 正常；1 金样非法/意外错误；2 live 前置条件不满足（显式失败）。
"""
from __future__ import annotations

import argparse
import asyncio
import contextlib
import json
import logging
import math
import os
import re
import sys
import tempfile
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.db.models import OpsMemoryFact, now_utc  # noqa: E402
from app.ops.memory import service as memory_service  # noqa: E402
from app.ops.memory.extract import MemoryFactExtraction  # noqa: E402
from app.ops.memory.gate import FactCandidate, should_write  # noqa: E402
from app.ops.prompts import get_template  # noqa: E402
from app.ops.structured_output import extract_json_object  # noqa: E402

logger = logging.getLogger("memory_golden_eval")

DEFAULT_GOLDEN = Path(__file__).resolve().parent / "golden_v1.yaml"
DEFAULT_REPORT_DIR = ROOT / "reports"

#: live 真跑独立租户（SPEC §5：隔离 + 跑后清场）
EVAL_TENANT = "memory-eval"
#: 复述用例的干扰事实数：确定性 top-N 挤掉目标，只有向量通路能捞回
PARAPHRASE_DISTRACTORS = 9
#: 复述召回预算（top1/top3 判定口径）
PARAPHRASE_RECALL_LIMIT = 3

CATEGORIES = ("should_remember", "should_not_remember", "supersede", "paraphrase")
MIN_CASE_COUNTS = {
    "should_remember": 12,
    "should_not_remember": 12,
    "supersede": 8,
    "paraphrase": 10,
}

# SPEC §2 D5（签收锁死）· 报告头部写死门槛与达成情况，防"假绿"引用
THRESHOLDS: dict[str, tuple[str, float]] = {
    "extraction_precision": (">=", 0.9),
    "noise_write_rate": ("<=", 0.1),
    "paraphrase_top3": (">=", 0.8),
    "supersede_accuracy": ("==", 1.0),
}
THRESHOLD_NOTE = (
    "门槛来自 SPEC-memory-golden-eval §2 D5（签收锁死）；fake 模式为确定性管线自检，"
    "不构成开开关依据；裁决以 live 真跑报告为准（SPEC §8 维护者复制区）"
)

# SPEC §2 D3 扫参网格（27 组；只出建议不改代码常量）
SWEEP_GRID = {
    "half_life_days": [7.0, 30.0, 90.0],
    "sim_floor": [0.3, 0.5, 0.7],
    "source_weight_extract": [0.6, 0.8, 1.0],
}
#: 扫参推荐内部参考线（对齐 D5 复述门槛；不达标则如实不推荐）
SWEEP_INTERNAL_BAR = 0.8
CURRENT_FUSION_DEFAULTS = {
    "half_life_days": memory_service.HALF_LIFE_DAYS,
    "sim_floor": memory_service.SIM_FLOOR,
    "source_weight_extract": memory_service.SOURCE_WEIGHT_EXTRACTED,
}


class GoldenSchemaError(ValueError):
    """金样 YAML schema 非法（CI 早失败；错误信息聚合全部问题）。"""


class LiveUnavailableError(RuntimeError):
    """live 前置条件不满足：缺 key / 外网不通 / DB 不通（显式失败，不冒充）。"""


# ---------------------------------------------------------------------------
# 金样加载与 schema 校验（E4 单测直接复用）
# ---------------------------------------------------------------------------


def load_golden(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise GoldenSchemaError(f"金样顶层必须是 mapping: {path}")
    return data


def _key_passes_gate(key: object) -> bool:
    """以**真闸**校验 key 合法性（不另造判据）。"""
    if not isinstance(key, str):
        return False
    return should_write(
        FactCandidate(tenant_id="schema", user_id="check", key=key, value="v")
    ).allowed


def _validate_fact_pair(fact: Any, *, where: str, problems: list[str]) -> None:
    if not isinstance(fact, dict) or "key" not in fact or "value" not in fact:
        problems.append(f"{where}: 需要 {{key, value}}")
        return
    if not _key_passes_gate(fact["key"]):
        problems.append(f"{where}: key 不过闸（小写点分层 ≥2 段 · 非易失前缀）: {fact['key']!r}")
    if fact["value"] is None or isinstance(fact["value"], (dict, list)):
        problems.append(f"{where}: value 必须是 JSON 标量且非 null: {fact['value']!r}")


def validate_golden(data: dict[str, Any]) -> list[dict[str, Any]]:
    """金样 schema 校验：四类数量下限 / 必填字段 / key 过真闸。全量聚合问题后一次抛。"""
    problems: list[str] = []
    if data.get("version") != 1:
        problems.append("version 必须为 1")
    cases = data.get("golden")
    if not isinstance(cases, list) or not cases:
        problems.append("golden 必须是非空列表")
        cases = []

    ids: set[str] = set()
    counts: dict[str, int] = dict.fromkeys(CATEGORIES, 0)
    for case in cases:
        cid = str(case.get("id") or "?")
        where = f"case {cid}"
        if cid in ids:
            problems.append(f"{where}: id 重复")
        ids.add(cid)
        cat = case.get("category")
        if cat not in CATEGORIES:
            problems.append(f"{where}: category 非法: {cat!r}")
            continue
        counts[cat] += 1
        if not str(case.get("query") or "").strip():
            problems.append(f"{where}: query 必填")
        fake_facts = case.get("fake_facts") or []
        if not isinstance(fake_facts, list):
            problems.append(f"{where}: fake_facts 必须是列表")
            fake_facts = []
        for i, f in enumerate(fake_facts):
            if not isinstance(f, dict) or "key" not in f or "value" not in f:
                problems.append(f"{where}: fake_facts[{i}] 需要 {{key, value}}")

        if cat in ("should_remember", "should_not_remember", "supersede"):
            if not str(case.get("answer") or "").strip():
                problems.append(f"{where}: answer 必填（抽取文本窗）")
            expect = case.get("expect_facts")
            if not isinstance(expect, list):
                problems.append(f"{where}: expect_facts 必须是列表（可为空 []）")
                expect = []
            for i, f in enumerate(expect):
                _validate_fact_pair(f, where=f"{where} expect_facts[{i}]", problems=problems)
            if cat == "should_remember" and not expect:
                problems.append(f"{where}: 应记用例 expect_facts 不能为空")
            if cat == "should_not_remember" and expect:
                problems.append(f"{where}: 负样本 expect_facts 必须为 []")
            if cat == "supersede":
                setup = case.get("setup_fact")
                _validate_fact_pair(setup, where=f"{where} setup_fact", problems=problems)
                if len(expect) != 1:
                    problems.append(f"{where}: supersede expect_facts 必须恰好 1 条（新值）")
                elif isinstance(setup, dict) and expect[0].get("key") != setup.get("key"):
                    problems.append(f"{where}: supersede 新旧值必须同 key（冲突取代语义）")
        if cat == "paraphrase":
            _validate_fact_pair(case.get("fact"), where=f"{where} fact", problems=problems)
            fact = case.get("fact") or {}
            if case.get("expect_hit_key") != fact.get("key"):
                problems.append(f"{where}: expect_hit_key 必须等于 fact.key")

    for cat, minimum in MIN_CASE_COUNTS.items():
        if counts[cat] < minimum:
            problems.append(f"类别 {cat} 数量 {counts[cat]} < 下限 {minimum}")
    if problems:
        raise GoldenSchemaError("金样 schema 非法：\n" + "\n".join(f"- {p}" for p in problems))
    return cases


# ---------------------------------------------------------------------------
# fake 后端：确定性 embedder（关键词 → 正交基向量 · 无随机 · 不连外网）
# ---------------------------------------------------------------------------

_EMBED_DIM = 64
#: 关键词组 → 维度；金样 PR 用例的事实文本与复述 query 各命中且只命中一组，
#: 余弦相似度即 1.0（CI 确定性）；glossary 组专供干扰项，金样 query 均不命中。
_KEYWORD_GROUPS: tuple[tuple[str, ...], ...] = (
    ("repo", "仓库", "代码仓"),
    ("deploy", "部署"),
    ("时区", "timezone", "shanghai"),
    ("负责人", "owner", "对接人"),
    ("分支", "branch"),
    ("告警", "alert", "monitor", "监控"),
    ("数据库", "database", "postgres", "db"),
    ("缓存", "cache", "redis"),
    ("回滚", "rollback"),
    ("镜像", "image", "docker"),
    ("网关", "gateway"),
    ("队列", "queue"),
    ("发布", "上线"),
    ("密钥", "secret", "vault"),
    ("术语", "glossary", "noise"),
)
_ASCII_KW_RE = {
    kw: re.compile(r"(?<![a-z0-9])" + re.escape(kw) + r"(?![a-z0-9])")
    for group in _KEYWORD_GROUPS
    for kw in group
    if kw.isascii()
}


def _keyword_hit(text_lower: str, keyword: str) -> bool:
    if keyword.isascii():
        return bool(_ASCII_KW_RE[keyword].search(text_lower))
    return keyword in text_lower


class FakeEmbedder:
    """确定性向量：命中关键词组 → 对应基向量叠加后归一化；无命中 → 全零。"""

    name = "fake-keyword-embedder-v1"

    def _vec(self, text_value: str) -> list[float]:
        t = (text_value or "").lower()
        v = [0.0] * _EMBED_DIM
        for dim, group in enumerate(_KEYWORD_GROUPS):
            if any(_keyword_hit(t, kw) for kw in group):
                v[dim] = 1.0
        norm = math.sqrt(sum(x * x for x in v))
        return [x / norm for x in v] if norm else v

    def embed(self, texts: list[str]) -> list[list[float]]:
        return [self._vec(t) for t in texts]


def _cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b, strict=True))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(x * x for x in b))
    if not na or not nb:
        return 0.0
    return dot / (na * nb)


# ---------------------------------------------------------------------------
# fake 后端：内存事实库（真闸 + 真 _fuse_recall；supersede 语义对齐 service）
# ---------------------------------------------------------------------------


class InMemoryFactStore:
    """fake 模式事实库：闸拒=不写入；同 key 后写赢（旧行 superseded）；
    召回 = 确定性 top-N ∪ 向量 top-M → 真 `_fuse_recall`。id 用计数器（全确定）。"""

    def __init__(self, embedder: FakeEmbedder) -> None:
        self._embedder = embedder
        self.facts: list[OpsMemoryFact] = []
        self._seq = 0

    def write(
        self,
        candidate: FactCandidate,
        *,
        source_run_id: str | None = None,
        source_turn: int | None = None,
        updated_at: datetime | None = None,
    ) -> tuple[OpsMemoryFact | None, str]:
        decision = should_write(candidate)
        if not decision.allowed:
            return None, decision.reason_code
        now = updated_at or now_utc()
        old_active = [
            f
            for f in self.facts
            if f.tenant_id == candidate.tenant_id
            and f.user_id == candidate.user_id
            and f.key == candidate.key.strip()
            and f.status == memory_service.STATUS_ACTIVE
        ]
        self._seq += 1
        fact = OpsMemoryFact(
            tenant_id=candidate.tenant_id.strip(),
            user_id=candidate.user_id.strip(),
            key=candidate.key.strip(),
            value=candidate.value,
            kind=candidate.kind,
        )
        fact.id = f"fake-{self._seq:06d}"
        fact.status = memory_service.STATUS_ACTIVE
        fact.source_run_id = source_run_id
        fact.source_turn = source_turn
        fact.supersedes = str(old_active[0].id) if old_active else None
        fact.created_at = now
        fact.updated_at = now
        fact.expires_at = None
        fact.embedding = self._embedder.embed(
            [memory_service._fact_embed_text(fact.key, fact.value)]
        )[0]
        self.facts.append(fact)
        for old in old_active:
            old.status = memory_service.STATUS_SUPERSEDED
            old.updated_at = now
        return fact, ""

    def active(self, tenant_id: str, user_id: str, now: datetime) -> list[OpsMemoryFact]:
        return [
            f
            for f in self.facts
            if f.tenant_id == tenant_id
            and f.user_id == user_id
            and f.status == memory_service.STATUS_ACTIVE
            and (f.expires_at is None or f.expires_at > now)
        ]

    def recall(
        self, tenant_id: str, user_id: str, query: str, *, limit: int, now: datetime
    ) -> list[OpsMemoryFact]:
        """确定性 top-N ∪ 向量 top-M → 真 _fuse_recall（与生产同路径纪律）。"""
        active = self.active(tenant_id, user_id, now)
        deterministic = sorted(
            active, key=lambda f: (f.updated_at, f.created_at, str(f.id)), reverse=True
        )[:limit]
        qvec = self._embedder.embed([query])[0]
        scored = [
            (str(f.id), _cosine(qvec, f.embedding), f) for f in active if f.embedding
        ]
        scored.sort(key=lambda t: (-t[1], t[0]))
        top = scored[:limit]
        sims = {fid: sim for fid, sim, _ in top}
        rows = {fid: f for fid, _, f in top}
        return memory_service._fuse_recall(
            deterministic, sims, rows, limit=limit, now=now
        )


# ---------------------------------------------------------------------------
# 用例结果与指标
# ---------------------------------------------------------------------------


@dataclass
class CaseResult:
    id: str
    category: str
    verdict: str  # pass | fail | error
    detail: str = ""
    written_good: int = 0
    written_noise: int = 0
    extra: dict[str, Any] = field(default_factory=dict)


def _pair_in(pair: tuple[str, Any], expected: list[tuple[str, Any]]) -> bool:
    return any(pair[0] == k and pair[1] == v for k, v in expected)


def run_fake_extraction(
    case: dict[str, Any],
    *,
    store: InMemoryFactStore,
    tenant_id: str,
    user_id: str,
    source_run_id: str,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """罐头 provider（金样 fake_facts）→ 真解析 + 真 schema + 真闸 → 内存库。

    返回 (written, gate_rejected)；闸拒不是写入（对齐生产"拒绝 = 不落库"）。
    """
    payload = json.dumps({"facts": case.get("fake_facts") or []}, ensure_ascii=False)
    obj = extract_json_object(payload) or {}
    data = MemoryFactExtraction.model_validate(obj)
    written: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []
    for item in data.facts:
        candidate = FactCandidate(
            tenant_id=tenant_id, user_id=user_id, key=item.key, value=item.value
        )
        fact, reason = store.write(candidate, source_run_id=source_run_id)
        if fact is None:
            rejected.append({"key": item.key, "reason": reason})
        else:
            written.append({"key": fact.key, "value": fact.value})
    return written, rejected


def _eval_should_remember_fake(
    case: dict[str, Any], store: InMemoryFactStore, run_id: str
) -> CaseResult:
    user = f"eval-{case['id']}"
    rid = f"{run_id}-{case['id']}"
    written, rejected = run_fake_extraction(
        case, store=store, tenant_id=EVAL_TENANT, user_id=user, source_run_id=rid
    )
    expected = [(f["key"], f["value"]) for f in case["expect_facts"]]
    pairs = [(w["key"], w["value"]) for w in written]
    missing = [k for k, v in expected if not _pair_in((k, v), pairs)]
    good = sum(1 for p in pairs if _pair_in(p, expected))
    return CaseResult(
        id=str(case["id"]),
        category="should_remember",
        verdict="pass" if not missing else "fail",
        detail="" if not missing else f"漏记: {missing}",
        written_good=good,
        written_noise=len(pairs) - good,
        extra={"written": written, "gate_rejected": rejected},
    )


def _eval_should_not_remember_fake(
    case: dict[str, Any], store: InMemoryFactStore, run_id: str
) -> CaseResult:
    user = f"eval-{case['id']}"
    rid = f"{run_id}-{case['id']}"
    written, rejected = run_fake_extraction(
        case, store=store, tenant_id=EVAL_TENANT, user_id=user, source_run_id=rid
    )
    return CaseResult(
        id=str(case["id"]),
        category="should_not_remember",
        verdict="pass" if not written else "fail",
        detail="" if not written else f"噪声写入: {[w['key'] for w in written]}",
        written_good=0,
        written_noise=len(written),
        extra={"written": written, "gate_rejected": rejected},
    )


def _eval_supersede_fake(
    case: dict[str, Any], store: InMemoryFactStore, run_id: str
) -> CaseResult:
    user = f"eval-{case['id']}"
    rid = f"{run_id}-{case['id']}"
    setup = case["setup_fact"]
    base = now_utc()
    old_fact, reason = store.write(
        FactCandidate(
            tenant_id=EVAL_TENANT, user_id=user, key=setup["key"], value=setup["value"]
        ),
        updated_at=base - timedelta(days=1),
    )
    if old_fact is None:
        return CaseResult(
            id=str(case["id"]),
            category="supersede",
            verdict="error",
            detail=f"setup_fact 未过闸: {reason}",
        )
    written, rejected = run_fake_extraction(
        case, store=store, tenant_id=EVAL_TENANT, user_id=user, source_run_id=rid
    )
    expected = [(f["key"], f["value"]) for f in case["expect_facts"]]
    pairs = [(w["key"], w["value"]) for w in written]
    wrote_new = all(_pair_in(p, pairs) for p in expected)
    active_rows = [
        f for f in store.active(EVAL_TENANT, user, now_utc()) if f.key == setup["key"]
    ]
    only_new = (
        len(active_rows) == 1 and _pair_in((active_rows[0].key, active_rows[0].value), expected)
    )
    old_superseded = old_fact.status == memory_service.STATUS_SUPERSEDED
    correct = wrote_new and only_new and old_superseded
    fails = []
    if not wrote_new:
        fails.append("新值未写入")
    if not only_new:
        fails.append(f"召回非仅新值: {[(f.key, f.value) for f in active_rows]}")
    if not old_superseded:
        fails.append("旧值未 superseded")
    good = sum(1 for p in pairs if _pair_in(p, expected))
    return CaseResult(
        id=str(case["id"]),
        category="supersede",
        verdict="pass" if correct else "fail",
        detail="; ".join(fails),
        written_good=good,
        written_noise=len(pairs) - good,
        extra={
            "written": written,
            "gate_rejected": rejected,
            "old_status": old_fact.status,
            "recalled": [(f.key, f.value) for f in active_rows],
        },
    )


def _case_slug(case: dict[str, Any]) -> str:
    """用例 id → 合法 key 段（闸只收小写点分层；合成测试 id 可能带连字符）。"""
    return re.sub(r"[^a-z0-9]+", "_", str(case["id"]).lower()).strip("_") or "case"


def _write_paraphrase_fixture_fake(
    case: dict[str, Any], store: InMemoryFactStore, run_id: str, now: datetime
) -> None:
    """目标事实（抽取来源 · 略旧）+ 9 个新鲜显式干扰项（glossary 组）：
    确定性 top-3 只有干扰项，目标只能靠向量通路捞回。"""
    user = f"eval-{case['id']}"
    fact = case["fact"]
    store.write(
        FactCandidate(tenant_id=EVAL_TENANT, user_id=user, key=fact["key"], value=fact["value"]),
        source_run_id=f"{run_id}-{case['id']}",
        updated_at=now - timedelta(hours=1),
    )
    for i in range(PARAPHRASE_DISTRACTORS):
        store.write(
            FactCandidate(
                tenant_id=EVAL_TENANT,
                user_id=user,
                key=f"glossary.term_{_case_slug(case)}_{i:02d}",
                value=f"术语噪声占位 {i}",
            ),
            updated_at=now,
        )


def _eval_paraphrase_fake(
    case: dict[str, Any], store: InMemoryFactStore, run_id: str
) -> CaseResult:
    user = f"eval-{case['id']}"
    now = now_utc()
    _write_paraphrase_fixture_fake(case, store, run_id, now)
    fused = store.recall(
        EVAL_TENANT, user, str(case["query"]), limit=PARAPHRASE_RECALL_LIMIT, now=now
    )
    keys = [f.key for f in fused]
    top1 = bool(keys) and keys[0] == case["expect_hit_key"]
    top3 = case["expect_hit_key"] in keys[:3]
    return CaseResult(
        id=str(case["id"]),
        category="paraphrase",
        verdict="pass" if top3 else "fail",
        detail="" if top3 else f"未命中: top={keys}",
        extra={"top1": top1, "top3": top3, "recalled_keys": keys},
    )


def run_fake_eval(
    cases: list[dict[str, Any]], *, run_id: str
) -> list[CaseResult]:
    """fake 模式端到端：内存库 + 真闸/真解析/真融合；无 DB 无外网，全确定。"""
    embedder = FakeEmbedder()
    store = InMemoryFactStore(embedder)
    results: list[CaseResult] = []
    for case in cases:
        cat = case["category"]
        if cat == "should_remember":
            results.append(_eval_should_remember_fake(case, store, run_id))
        elif cat == "should_not_remember":
            results.append(_eval_should_not_remember_fake(case, store, run_id))
        elif cat == "supersede":
            results.append(_eval_supersede_fake(case, store, run_id))
        elif cat == "paraphrase":
            results.append(_eval_paraphrase_fake(case, store, run_id))
        else:  # pragma: no cover - validate_golden 已拦
            raise GoldenSchemaError(f"未知 category: {cat!r}")
    return results


def _rate(ok: int, total: int) -> float | None:
    return round(ok / total, 4) if total else None


def compute_metrics(results: list[CaseResult]) -> dict[str, Any]:
    """SPEC §2 D2 指标（error 用例不计入分母，单列 errors）。"""
    scored = [r for r in results if r.verdict != "error"]
    sr = [r for r in scored if r.category == "should_remember"]
    ng = [r for r in scored if r.category == "should_not_remember"]
    sp = [r for r in scored if r.category == "supersede"]
    pr = [r for r in scored if r.category == "paraphrase"]
    good = sum(r.written_good for r in scored)
    noise = sum(r.written_noise for r in scored)
    return {
        "extraction_precision": (
            round(good / (good + noise), 4) if (good + noise) else None
        ),
        "noise_write_rate": _rate(sum(1 for r in ng if r.written_noise > 0), len(ng)),
        "miss_rate": _rate(sum(1 for r in sr if r.verdict == "fail"), len(sr)),
        "paraphrase_top1": _rate(sum(1 for r in pr if r.extra.get("top1")), len(pr)),
        "paraphrase_top3": _rate(sum(1 for r in pr if r.extra.get("top3")), len(pr)),
        "supersede_accuracy": _rate(sum(1 for r in sp if r.verdict == "pass"), len(sp)),
        "written_good": good,
        "written_noise": noise,
        "errors": sum(1 for r in results if r.verdict == "error"),
        "cases": len(results),
    }


_THRESHOLD_OPS = {
    ">=": lambda a, b: a >= b,
    "<=": lambda a, b: a <= b,
    "==": lambda a, b: a == b,
}


def evaluate_thresholds(metrics: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """SPEC §2 D5 四条门槛逐条判定；actual=None（样本不足）按未达标计。"""
    out: dict[str, dict[str, Any]] = {}
    for name, (op, bound) in THRESHOLDS.items():
        actual = metrics.get(name)
        met = actual is not None and bool(_THRESHOLD_OPS[op](actual, bound))
        out[name] = {"threshold": f"{op} {bound}", "actual": actual, "met": met}
    return out


# ---------------------------------------------------------------------------
# 扫参（E3）：27 组网格 · 临时覆盖 service 常量调真 _fuse_recall · 只出建议
# ---------------------------------------------------------------------------


@contextlib.contextmanager
def patched_fusion_constants(
    *, half_life_days: float, sim_floor: float, source_weight_extract: float
):
    """运行时临时覆盖 service 融合常量（with 块内恢复现场）。

    零文件改动、零生产默认值改动：只在本进程作用域内影响 `_fuse_recall`
    读取的模块级常量（SPEC §2 D3「以参数覆盖方式调用」的落地）。
    """
    old = (
        memory_service.HALF_LIFE_DAYS,
        memory_service.SIM_FLOOR,
        memory_service.SOURCE_WEIGHT_EXTRACTED,
    )
    memory_service.HALF_LIFE_DAYS = float(half_life_days)
    memory_service.SIM_FLOOR = float(sim_floor)
    memory_service.SOURCE_WEIGHT_EXTRACTED = float(source_weight_extract)
    try:
        yield
    finally:
        (
            memory_service.HALF_LIFE_DAYS,
            memory_service.SIM_FLOOR,
            memory_service.SOURCE_WEIGHT_EXTRACTED,
        ) = old


@dataclass
class _Scenario:
    kind: str  # paraphrase_aged | recency
    target_id: str
    facts: list[OpsMemoryFact]
    vector_sims: dict[str, float]
    deterministic_ids: list[str]


def _mk_sweep_fact(
    *,
    fid: str,
    key: str,
    value: str,
    age_days: float,
    extracted: bool,
    now: datetime,
) -> OpsMemoryFact:
    fact = OpsMemoryFact(
        tenant_id=EVAL_TENANT, user_id="sweep", key=key, value=value, kind="fact"
    )
    fact.id = fid
    fact.status = memory_service.STATUS_ACTIVE
    fact.source_run_id = "sweep-extract-run" if extracted else None
    fact.source_turn = None
    fact.supersedes = None
    ts = now - timedelta(days=age_days)
    fact.created_at = ts
    fact.updated_at = ts
    fact.expires_at = None
    fact.embedding = None
    return fact


def build_sweep_scenarios(
    paraphrase_cases: list[dict[str, Any]], *, now: datetime
) -> list[_Scenario]:
    """复述（陈化 1/30/90 天三档）+ 时效性（旧相关显式 vs 新弱相关抽取）场景。"""
    scenarios: list[_Scenario] = []
    for case in paraphrase_cases:
        slug = str(case["id"]).lower()
        for age in (1.0, 30.0, 90.0):
            target = _mk_sweep_fact(
                fid=f"{slug}-t-{int(age)}",
                key=case["fact"]["key"],
                value=str(case["fact"]["value"]),
                age_days=age,
                extracted=True,
                now=now,
            )
            distractors = [
                _mk_sweep_fact(
                    fid=f"{slug}-d{i}-{int(age)}",
                    key=f"glossary.sweep_{slug}_{i}",
                    value=f"术语噪声 {i}",
                    age_days=0.0,
                    extracted=False,
                    now=now,
                )
                for i in range(5)
            ]
            # 向量 top-M：目标 + 2 个零相似干扰；其余 3 个只走确定性（吃 SIM_FLOOR）
            sims = {
                str(target.id): 1.0,
                str(distractors[0].id): 0.0,
                str(distractors[1].id): 0.0,
            }
            scenarios.append(
                _Scenario(
                    kind="paraphrase_aged",
                    target_id=str(target.id),
                    facts=[target, *distractors],
                    vector_sims=sims,
                    deterministic_ids=[str(d.id) for d in distractors],
                )
            )
    for idx, (age, sim_old, sim_new) in enumerate(
        [(60.0, 0.85, 0.55), (30.0, 0.80, 0.60), (90.0, 0.90, 0.50)]
    ):
        old = _mk_sweep_fact(
            fid=f"rec{idx}-old",
            key="project.recency_relevant",
            value="old-relevant",
            age_days=age,
            extracted=False,
            now=now,
        )
        new = _mk_sweep_fact(
            fid=f"rec{idx}-new",
            key="project.recency_fresh",
            value="fresh-weaker",
            age_days=0.0,
            extracted=True,
            now=now,
        )
        fillers = [
            _mk_sweep_fact(
                fid=f"rec{idx}-f{i}",
                key=f"glossary.recency_{idx}_{i}",
                value=f"术语噪声 {i}",
                age_days=0.0,
                extracted=False,
                now=now,
            )
            for i in range(2)
        ]
        scenarios.append(
            _Scenario(
                kind="recency",
                target_id=str(old.id),
                facts=[old, new, *fillers],
                vector_sims={str(old.id): sim_old, str(new.id): sim_new},
                deterministic_ids=[str(new.id), *(str(f.id) for f in fillers)],
            )
        )
    return scenarios


def _rank_scenario(sc: _Scenario, *, limit: int, now: datetime) -> list[str]:
    rows = {fid: f for f in sc.facts if (fid := str(f.id)) in sc.vector_sims}
    det = [f for f in sc.facts if str(f.id) in sc.deterministic_ids]
    det.sort(key=lambda f: (f.updated_at, f.created_at, str(f.id)), reverse=True)
    fused = memory_service._fuse_recall(
        det[:limit], sc.vector_sims, rows, limit=limit, now=now
    )
    return [str(f.id) for f in fused]


def run_sweep(
    paraphrase_cases: list[dict[str, Any]],
    *,
    now: datetime | None = None,
    limit: int = PARAPHRASE_RECALL_LIMIT,
) -> dict[str, Any]:
    """27 组扫参：每组在复述（陈化）+ 时效性场景上打分，输出推荐组合与理由。"""
    now = now or now_utc()
    scenarios = build_sweep_scenarios(paraphrase_cases, now=now)
    combos: list[dict[str, Any]] = []
    for half_life in SWEEP_GRID["half_life_days"]:
        for sim_floor in SWEEP_GRID["sim_floor"]:
            for weight in SWEEP_GRID["source_weight_extract"]:
                with patched_fusion_constants(
                    half_life_days=half_life,
                    sim_floor=sim_floor,
                    source_weight_extract=weight,
                ):
                    ranked = [
                        (sc, _rank_scenario(sc, limit=limit, now=now))
                        for sc in scenarios
                    ]
                para = [(sc, ids) for sc, ids in ranked if sc.kind == "paraphrase_aged"]
                rec = [(sc, ids) for sc, ids in ranked if sc.kind == "recency"]
                p_top1 = _rate(sum(1 for sc, ids in para if ids[:1] == [sc.target_id]), len(para))
                p_top3 = _rate(sum(1 for sc, ids in para if sc.target_id in ids[:3]), len(para))
                r_top1 = _rate(sum(1 for sc, ids in rec if ids[:1] == [sc.target_id]), len(rec))
                combos.append(
                    {
                        "half_life_days": half_life,
                        "sim_floor": sim_floor,
                        "source_weight_extract": weight,
                        "paraphrase_top1": p_top1,
                        "paraphrase_top3": p_top3,
                        "recency_top1": r_top1,
                        "meets_internal_bar": bool(
                            p_top3 is not None and p_top3 >= SWEEP_INTERNAL_BAR
                        ),
                    }
                )
    ranked_combos = sorted(
        combos,
        key=lambda c: (
            c["paraphrase_top3"] or 0.0,
            c["recency_top1"] or 0.0,
            c["paraphrase_top1"] or 0.0,
        ),
        reverse=True,
    )
    best = ranked_combos[0]

    def _avg(key: str, dim: str, val: float) -> float:
        rows = [c for c in combos if c[dim] == val]
        return round(sum(c[key] or 0.0 for c in rows) / len(rows), 4)

    reasons = [
        "按 half_life 聚合复述 top3 均值: "
        + ", ".join(
            f"{v:g}d={_avg('paraphrase_top3', 'half_life_days', v)}"
            for v in SWEEP_GRID["half_life_days"]
        ),
        "按 sim_floor 聚合复述 top3 均值: "
        + ", ".join(
            f"{v:g}={_avg('paraphrase_top3', 'sim_floor', v)}"
            for v in SWEEP_GRID["sim_floor"]
        ),
        "按 source_weight_extract 聚合时效性 top1 均值: "
        + ", ".join(
            f"{v:g}={_avg('recency_top1', 'source_weight_extract', v)}"
            for v in SWEEP_GRID["source_weight_extract"]
        ),
    ]
    recommendation: dict[str, Any] | None = None
    if best["paraphrase_top3"] is not None and best["paraphrase_top3"] >= SWEEP_INTERNAL_BAR:
        recommendation = {
            "params": {
                "half_life_days": best["half_life_days"],
                "sim_floor": best["sim_floor"],
                "source_weight_extract": best["source_weight_extract"],
            },
            "scores": {
                "paraphrase_top1": best["paraphrase_top1"],
                "paraphrase_top3": best["paraphrase_top3"],
                "recency_top1": best["recency_top1"],
            },
            "reason": (
                "复述 top3 → 时效性 top1 → 复述 top1 字典序最优；"
                "排序键与聚合理由见 reasons"
            ),
        }
    else:
        reasons.append(
            f"全部 27 组复述 top3 低于内部参考线 {SWEEP_INTERNAL_BAR} · 如实不推荐任何组合"
        )
    return {
        "grid": {k: list(v) for k, v in SWEEP_GRID.items()},
        "scenario_count": len(scenarios),
        "combos": combos,
        "recommended": recommendation,
        "current_defaults": dict(CURRENT_FUSION_DEFAULTS),
        "note": "只出建议 · 改值另 task 按报告裁决（SPEC §2 D3）；本扫参未改任何代码常量",
        "reasons": reasons,
    }


# ---------------------------------------------------------------------------
# live 后端（维护者真跑）：真实 embedder + 真实抽取 provider + 真 PG
# ---------------------------------------------------------------------------


def live_preflight():
    """live 前置检查：缺 key / embedder 初始化或探测失败 → LiveUnavailableError。

    显式失败是契约（failure_paths）：绝不静默降级冒充 fake。
    """
    if not (os.getenv("SILICONFLOW_API_KEY") or "").strip():
        raise LiveUnavailableError(
            "live 模式缺少 SILICONFLOW_API_KEY（.env 或环境变量）；"
            "显式失败，不静默降级为 fake"
        )
    from app.ops.rag.embedder import get_query_embedder

    try:
        embedder = get_query_embedder()
    except Exception as exc:
        raise LiveUnavailableError(f"live embedder 初始化失败: {exc}") from exc
    try:
        vectors = embedder.embed(["memory-eval preflight probe"])
    except Exception as exc:
        raise LiveUnavailableError(
            f"live embedder 探测失败（外网不通或模型异常）: {exc}"
        ) from exc
    if not vectors or not vectors[0]:
        raise LiveUnavailableError("live embedder 探测返回空向量（外网不通或模型异常）")
    return embedder


async def _live_db_probe() -> None:
    from sqlalchemy import text

    from app.db.session import AsyncSessionLocal

    try:
        async with AsyncSessionLocal() as session:
            await session.execute(text("SELECT 1"))
    except Exception as exc:
        raise LiveUnavailableError(f"live 模式数据库不可达: {exc}") from exc


async def _live_written_by_source(source_run_id: str) -> list[dict[str, Any]]:
    from sqlalchemy import text

    from app.db.session import AsyncSessionLocal

    async with AsyncSessionLocal() as session:
        rows = await session.execute(
            text(
                "SELECT key, value FROM ops_memory_facts "
                "WHERE source_run_id = :r AND status = 'active'"
            ),
            {"r": source_run_id},
        )
        return [{"key": r.key, "value": r.value} for r in rows.all()]


async def _live_row_status(fact_id: str) -> str | None:
    from sqlalchemy import text

    from app.db.session import AsyncSessionLocal

    async with AsyncSessionLocal() as session:
        rows = await session.execute(
            text("SELECT status FROM ops_memory_facts WHERE id = :i"), {"i": fact_id}
        )
        row = rows.first()
        return str(row[0]) if row else None


async def _live_cleanup(run_ids: list[str]) -> dict[str, int]:
    """SPEC §5 清场：逐 run revoke_by_source（审计）→ 删独立租户残留行。

    硬删仅限专用租户 `memory-eval`：revoke 只动 active 行，superseded/显式
    干扰项靠租户级删除收尾，保证测试库零残留。
    """
    from sqlalchemy import text

    from app.db.session import AsyncSessionLocal
    from app.ops.memory.service import revoke_by_source

    revoked = 0
    for rid in run_ids:
        try:
            revoked += await revoke_by_source(rid)
        except Exception:
            logger.exception("live cleanup revoke failed run_id=%s", rid)
    async with AsyncSessionLocal() as session, session.begin():
        result = await session.execute(
            text("DELETE FROM ops_memory_facts WHERE tenant_id = :t"),
            {"t": EVAL_TENANT},
        )
        deleted = int(result.rowcount or 0)
    logger.info("memory-eval cleanup revoked=%d tenant_rows_deleted=%d", revoked, deleted)
    return {"revoked": revoked, "tenant_rows_deleted": deleted}


async def _eval_extraction_case_live(
    case: dict[str, Any], *, run_id: str, provider: Any
) -> tuple[list[dict[str, Any]], str]:
    """SR/NG 共用：真 run_memory_extraction → 按 source_run_id 查回写入集。"""
    from app.ops.memory.extract import run_memory_extraction

    rid = f"{run_id}-{case['id']}"
    user = f"eval-{case['id']}"
    await run_memory_extraction(
        tenant_id=EVAL_TENANT,
        user_id=user,
        run_id=rid,
        source_turn=1,
        query=str(case["query"]),
        answer=str(case["answer"]),
        _provider=provider,
    )
    return await _live_written_by_source(rid), user


async def _eval_case_live(
    case: dict[str, Any], *, run_id: str, provider: Any, embedder: Any
) -> CaseResult:
    from app.ops.memory.service import recall_active, recall_with_vector, write_fact

    cat = case["category"]
    rid = f"{run_id}-{case['id']}"
    if cat in ("should_remember", "should_not_remember"):
        written, _user = await _eval_extraction_case_live(
            case, run_id=run_id, provider=provider
        )
        if cat == "should_not_remember":
            return CaseResult(
                id=str(case["id"]),
                category=cat,
                verdict="pass" if not written else "fail",
                detail="" if not written else f"噪声写入: {[w['key'] for w in written]}",
                written_noise=len(written),
                extra={"written": written},
            )
        expected = [(f["key"], f["value"]) for f in case["expect_facts"]]
        pairs = [(w["key"], w["value"]) for w in written]
        missing = [k for k, v in expected if not _pair_in((k, v), pairs)]
        good = sum(1 for p in pairs if _pair_in(p, expected))
        return CaseResult(
            id=str(case["id"]),
            category=cat,
            verdict="pass" if not missing else "fail",
            detail="" if not missing else f"漏记: {missing}",
            written_good=good,
            written_noise=len(pairs) - good,
            extra={"written": written},
        )
    if cat == "supersede":
        setup = case["setup_fact"]
        user = f"eval-{case['id']}"
        old_fact = await write_fact(
            FactCandidate(
                tenant_id=EVAL_TENANT,
                user_id=user,
                key=setup["key"],
                value=setup["value"],
            ),
            source_run_id=f"{rid}-setup",
            embedder=embedder,
        )
        written, _ = await _eval_extraction_case_live(
            case, run_id=run_id, provider=provider
        )
        expected = [(f["key"], f["value"]) for f in case["expect_facts"]]
        pairs = [(w["key"], w["value"]) for w in written]
        wrote_new = all(_pair_in(p, pairs) for p in expected)
        recalled = await recall_active(EVAL_TENANT, user, limit=8)
        active_rows = [f for f in recalled if f.key == setup["key"]]
        only_new = len(active_rows) == 1 and _pair_in(
            (active_rows[0].key, active_rows[0].value), expected
        )
        old_status = await _live_row_status(str(old_fact.id))
        correct = wrote_new and only_new and old_status == memory_service.STATUS_SUPERSEDED
        fails = []
        if not wrote_new:
            fails.append("新值未写入")
        if not only_new:
            fails.append(f"召回非仅新值: {[(f.key, f.value) for f in active_rows]}")
        if old_status != memory_service.STATUS_SUPERSEDED:
            fails.append(f"旧值状态: {old_status}")
        good = sum(1 for p in pairs if _pair_in(p, expected))
        return CaseResult(
            id=str(case["id"]),
            category=cat,
            verdict="pass" if correct else "fail",
            detail="; ".join(fails),
            written_good=good,
            written_noise=len(pairs) - good,
            extra={
                "written": written,
                "old_status": old_status,
                "recalled": [(f.key, f.value) for f in active_rows],
            },
        )
    if cat == "paraphrase":
        user = f"eval-{case['id']}"
        fact = case["fact"]
        target = await write_fact(
            FactCandidate(
                tenant_id=EVAL_TENANT, user_id=user, key=fact["key"], value=fact["value"]
            ),
            source_run_id=rid,
            embedder=embedder,
        )
        for i in range(PARAPHRASE_DISTRACTORS):
            await write_fact(
                FactCandidate(
                    tenant_id=EVAL_TENANT,
                    user_id=user,
                    key=f"glossary.term_{_case_slug(case)}_{i:02d}",
                    value=f"术语噪声占位 {i}",
                ),
                embedder=embedder,
            )
        # 钉死目标略旧：确定性 top-N 让给干扰项，逼向量通路出场
        from sqlalchemy import text

        from app.db.session import AsyncSessionLocal

        async with AsyncSessionLocal() as session, session.begin():
            await session.execute(
                text(
                    "UPDATE ops_memory_facts SET updated_at = :ts WHERE id = :i"
                ),
                {"ts": now_utc() - timedelta(hours=1), "i": str(target.id)},
            )
        fused = await recall_with_vector(
            EVAL_TENANT,
            user,
            str(case["query"]),
            limit=PARAPHRASE_RECALL_LIMIT,
            embedder=embedder,
        )
        keys = [f.key for f in fused]
        top1 = bool(keys) and keys[0] == case["expect_hit_key"]
        top3 = case["expect_hit_key"] in keys[:3]
        return CaseResult(
            id=str(case["id"]),
            category=cat,
            verdict="pass" if top3 else "fail",
            detail="" if top3 else f"未命中: top={keys}",
            extra={"top1": top1, "top3": top3, "recalled_keys": keys},
        )
    raise GoldenSchemaError(f"未知 category: {cat!r}")  # pragma: no cover


async def run_live_eval(
    cases: list[dict[str, Any]], *, run_id: str, embedder: Any
) -> tuple[list[CaseResult], list[dict[str, str]], dict[str, int]]:
    """live 模式端到端：真 embedder/provider/PG；单用例失败记 error 不中断；
    finally 里 revoke_by_source + 租户清场（防污染测试库）。"""
    from app.llm.factory import get_llm_provider

    await _live_db_probe()
    # 进程内临时打开双开关（eval 进程私有；不改 .env / 代码默认值）
    os.environ["MEMORY_FACTS_VECTOR_RECALL_ENABLED"] = "true"
    os.environ["MEMORY_FACTS_EXTRACT_ENABLED"] = "true"
    provider = get_llm_provider()
    run_ids: list[str] = []
    results: list[CaseResult] = []
    errors: list[dict[str, str]] = []
    cleanup: dict[str, int] = {"revoked": 0, "tenant_rows_deleted": 0}
    try:
        for case in cases:
            rid = f"{run_id}-{case['id']}"
            run_ids.append(rid)
            if case["category"] == "supersede":
                run_ids.append(f"{rid}-setup")
            try:
                results.append(
                    await _eval_case_live(
                        case, run_id=run_id, provider=provider, embedder=embedder
                    )
                )
            except Exception as exc:  # 单用例失败记 error · 不中断全量（failure_paths）
                logger.exception("live case failed id=%s", case["id"])
                errors.append(
                    {"id": str(case["id"]), "error": f"{type(exc).__name__}: {exc}"}
                )
                results.append(
                    CaseResult(
                        id=str(case["id"]),
                        category=str(case["category"]),
                        verdict="error",
                        detail=f"{type(exc).__name__}: {exc}",
                    )
                )
    finally:
        cleanup = await _live_cleanup(run_ids)
    return results, errors, cleanup


# ---------------------------------------------------------------------------
# 报告（仿 reports/r4*.yaml 形态；头部写死 D5 门槛与达成情况）
# ---------------------------------------------------------------------------


def build_report(
    *,
    run_id: str,
    backend: str,
    golden_path: Path,
    prompt_version: str,
    results: list[CaseResult],
    metrics: dict[str, Any],
    embed_name: str,
    errors: list[dict[str, str]] | None = None,
    cleanup: dict[str, int] | None = None,
    sweep: dict[str, Any] | None = None,
) -> dict[str, Any]:
    thresholds = evaluate_thresholds(metrics)
    by_cat: dict[str, str] = {}
    for cat in CATEGORIES:
        rows = [r for r in results if r.category == cat and r.verdict != "error"]
        by_cat[cat] = f"{sum(1 for r in rows if r.verdict == 'pass')}/{len(rows)}"
    report: dict[str, Any] = {
        "run": run_id,
        "backend": backend,
        "golden": str(golden_path),
        # 报告能看出命中哪版 prompt（task memory-extract-calibration 契约）
        "prompt_version": prompt_version,
        # 头部写死 SPEC §2 D5 门槛与达成情况（防"假绿"引用 · failure_paths）
        "thresholds": thresholds,
        "all_thresholds_met": all(t["met"] for t in thresholds.values()),
        "threshold_note": THRESHOLD_NOTE,
        "tenant": EVAL_TENANT,
        "embed": embed_name,
        "metrics": metrics,
        "summary": {
            "pass_by_category": by_cat,
            # 观测三字段（对齐 r4 报告先例）
            "measurement_source": "observed",
            "confidence": "low",
            "comparability": "not_comparable",
        },
        "errors": errors or [],
        "cleanup": cleanup,
        "results": [asdict(r) for r in results],
    }
    if sweep is not None:
        report["sweep"] = sweep
    return report


def write_report(path: Path, report: dict[str, Any]) -> None:
    """原子写入（先临时文件再 replace；对齐 evals/golden 先例）。"""
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


def default_out_path(backend: str) -> Path:
    stamp = datetime.now().strftime("%Y%m%d")
    return DEFAULT_REPORT_DIR / f"memory_golden_eval_{stamp}_{backend}.yaml"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="记忆金样评测 runner（fake 默认 · live 真跑）")
    parser.add_argument("--backend", choices=["fake", "live"], default="fake")
    parser.add_argument("--golden", type=Path, default=DEFAULT_GOLDEN)
    parser.add_argument("--out", type=Path, default=None)
    parser.add_argument("--limit", type=int, default=0, help="只跑前 N 条用例（冒烟）")
    parser.add_argument("--sweep", action="store_true", help="附带 27 组融合权重扫参")
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    try:
        all_cases = validate_golden(load_golden(args.golden))
    except GoldenSchemaError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    cases = all_cases[: args.limit] if args.limit else all_cases
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    run_id = f"memory-golden-eval-{stamp}-{args.backend}"
    out = args.out or default_out_path(args.backend)

    errors: list[dict[str, str]] = []
    cleanup: dict[str, int] | None = None
    if args.backend == "fake":
        results = run_fake_eval(cases, run_id=run_id)
        embed_name = FakeEmbedder.name
    else:
        try:
            embedder = live_preflight()
            results, errors, cleanup = asyncio.run(
                run_live_eval(cases, run_id=run_id, embedder=embedder)
            )
        except LiveUnavailableError as exc:
            print(f"[live 显式失败 · 退出码 2] {exc}", file=sys.stderr)
            return 2
        embed_name = getattr(embedder, "name", "unknown")

    metrics = compute_metrics(results)
    sweep = None
    if args.sweep:
        para_cases = [c for c in all_cases if c["category"] == "paraphrase"]
        sweep = run_sweep(para_cases)
    report = build_report(
        run_id=run_id,
        backend=args.backend,
        golden_path=args.golden,
        prompt_version=get_template("memory.extract.system").version,
        results=results,
        metrics=metrics,
        embed_name=embed_name,
        errors=errors,
        cleanup=cleanup,
        sweep=sweep,
    )
    write_report(out, report)
    print(f"报告已写入: {out}")
    print(f"指标: {json.dumps(metrics, ensure_ascii=False)}")
    for name, row in report["thresholds"].items():
        flag = "MET" if row["met"] else "NOT-MET"
        print(f"门槛 {name}: {row['threshold']} actual={row['actual']} [{flag}]")
    print(f"all_thresholds_met: {report['all_thresholds_met']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
