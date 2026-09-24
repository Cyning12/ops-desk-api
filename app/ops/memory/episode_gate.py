"""情景记忆写入闸（纯函数 · 无 DB · 无 IO · U4：与事实记忆闸物理分立）。

经验≠事实：事实闸（gate.py::should_write）判「主体绑定的可验证标量」；
本闸判「run 级模式归纳」——不同函数、不同表、不同候选类型，**互不 import**
（import 守护断言钉死）。

五判据（SPEC §2 D2 / task 钉死契约）落成显式可测规则：

| 判据 | 落成规则 | 拒绝原因码 |
|------|----------|------------|
| ① run 归因齐全 | tenant_id / run_id 均非空（episode 必绑定 run） | missing_attribution |
| ② outcome 合法 | outcome ∈ {success, failure, partial} | invalid_outcome |
| ③ 序列上限 | tool_sequence 为 str 列表且 ≤16（承 MAX_FIELDS） | tool_sequence_invalid / tool_sequence_too_long |
| ④ 摘要截断 | plan_summary 为 str 且 ≤200 字符（超长**拒**，非落库后截断） | plan_summary_too_long |
| ⑤ failure 必填合法 | outcome=failure → failure_class 必填且 ∈ 六值词表；任何非空 failure_class 非法值同拒 | failure_class_missing / failure_class_invalid |

**拒绝 = 不落库**（不是"存了不召回"）；原因码稳定可枚举，调用方按码断言。
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field

OUTCOME_SUCCESS = "success"
OUTCOME_FAILURE = "failure"
OUTCOME_PARTIAL = "partial"
#: 成败标签词表（钉死）
ALLOWED_OUTCOMES = frozenset({OUTCOME_SUCCESS, OUTCOME_FAILURE, OUTCOME_PARTIAL})

#: 失败分类词表（六值 · Q2 聚类键 · R1 审查 N3 对齐 SPEC「必填合法」）
ALLOWED_FAILURE_CLASSES = frozenset(
    {
        "capability_blocked",
        "so_failure",
        "budget_exhausted",
        "upstream_error",
        "contract_violation",
        "other",
    }
)

#: 工具序列骨架上限（承 step_contract MAX_FIELDS=16 先例）
MAX_TOOL_SEQUENCE = 16
#: plan 摘要上限（承 MAX_VALUE_CHARS=200 先例；超长拒，不落库后截断）
MAX_PLAN_SUMMARY_CHARS = 200

# 拒绝原因码（稳定可枚举；测试与调用方按码断言，不按文案）
REASON_MISSING_ATTRIBUTION = "missing_attribution"
REASON_INVALID_OUTCOME = "invalid_outcome"
REASON_TOOL_SEQUENCE_INVALID = "tool_sequence_invalid"
REASON_TOOL_SEQUENCE_TOO_LONG = "tool_sequence_too_long"
REASON_PLAN_SUMMARY_TOO_LONG = "plan_summary_too_long"
REASON_FAILURE_CLASS_MISSING = "failure_class_missing"
REASON_FAILURE_CLASS_INVALID = "failure_class_invalid"

REJECT_REASONS = frozenset(
    {
        REASON_MISSING_ATTRIBUTION,
        REASON_INVALID_OUTCOME,
        REASON_TOOL_SEQUENCE_INVALID,
        REASON_TOOL_SEQUENCE_TOO_LONG,
        REASON_PLAN_SUMMARY_TOO_LONG,
        REASON_FAILURE_CLASS_MISSING,
        REASON_FAILURE_CLASS_INVALID,
    }
)


@dataclass(frozen=True)
class EpisodeCandidate:
    """情景记忆写入闸候选（run 级 · 由 run 终态结构化产物显式构造）。

    episode 只从 run 终态结构化产物生成（不经 LLM 抽取 · SPEC FP-7 来源
    分立）；context_fingerprint 由 compute_context_fingerprint 同规则计算。
    """

    tenant_id: str
    run_id: str
    task_domain: str
    context_fingerprint: str
    plan_summary: str
    tool_sequence: list[str] = field(default_factory=list)
    outcome: str = OUTCOME_SUCCESS
    failure_class: str | None = None


@dataclass(frozen=True)
class Decision:
    """闸判定：allowed + 拒绝 reason_code（放行时为空串）。"""

    allowed: bool
    reason_code: str = ""


def should_write_episode(candidate: EpisodeCandidate) -> Decision:
    """情景记忆写入闸纯函数：任一判据不过即拒，**调用方不得落库**。"""
    # ① run 归因齐全：episode 必须绑定 (tenant, run)
    if not (candidate.tenant_id or "").strip() or not (candidate.run_id or "").strip():
        return Decision(False, REASON_MISSING_ATTRIBUTION)
    # ② outcome 词表合法
    if candidate.outcome not in ALLOWED_OUTCOMES:
        return Decision(False, REASON_INVALID_OUTCOME)
    # ③ 工具序列：str 列表且 ≤16
    seq = candidate.tool_sequence
    if not isinstance(seq, list) or any(not isinstance(t, str) for t in seq):
        return Decision(False, REASON_TOOL_SEQUENCE_INVALID)
    if len(seq) > MAX_TOOL_SEQUENCE:
        return Decision(False, REASON_TOOL_SEQUENCE_TOO_LONG)
    # ④ plan 摘要：str 且 ≤200（超长拒 = 不落库；截断是调用方写前义务）
    summary = candidate.plan_summary
    if not isinstance(summary, str) or len(summary) > MAX_PLAN_SUMMARY_CHARS:
        return Decision(False, REASON_PLAN_SUMMARY_TOO_LONG)
    # ⑤ failure 必填合法；任何非空 failure_class 非法值同拒
    failure_class = candidate.failure_class
    if candidate.outcome == OUTCOME_FAILURE and not (failure_class or "").strip():
        return Decision(False, REASON_FAILURE_CLASS_MISSING)
    if (failure_class or "").strip() and failure_class not in ALLOWED_FAILURE_CLASSES:
        return Decision(False, REASON_FAILURE_CLASS_INVALID)
    return Decision(True)


def compute_context_fingerprint(
    task_domain: str,
    intent_features: dict | None = None,
    tool_sequence: list[str] | None = None,
) -> str:
    """上下文指纹（确定性哈希：domain + 意图特征 + 工具序列骨架 · SPEC FP-5 三元）。

    同一规范化输入恒得同一 64 hex（写入与召回同规则计算，聚类键同源）：
    - domain：strip + lower；
    - 意图特征：dict 取标量值（str/int/float/bool/None）按键排序 canonical JSON，
      非标量/非 dict 一律忽略（宁可不召回方向：缺特征 ≠ 报错，得弱指纹）；
    - 工具序列骨架：str 列表保序取前 16（与闸上限同源）。
    """
    domain = (task_domain or "").strip().lower()
    features: dict[str, object] = {}
    if isinstance(intent_features, dict):
        for key in sorted(intent_features):
            value = intent_features[key]
            if value is None or isinstance(value, (str, int, float, bool)):
                features[str(key)] = value
    skeleton = [
        str(t) for t in (tool_sequence or [])[:MAX_TOOL_SEQUENCE] if isinstance(t, str)
    ]
    payload = {"d": domain, "i": features, "t": skeleton}
    canonical = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()
