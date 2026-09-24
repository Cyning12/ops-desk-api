"""场景维第二阶段裁剪（Host V1-B · scenario_trim）。

SPEC：docs/spec/host-v1-visibility-scenario-policy/SPEC-host-v1-visibility-scenario-policy_v0.md（signed）。

两阶段管线（R1 审查 B-1 澄清钉死）：最终可见集 = 基线 ∩ 场景维 ∩
requested_scope（三重交集 · 交换律等价 · 只收窄不放宽）。本模块承载
stage 2：Builder 内 基线（baseline_filter · stage 1 · 不改动）→
scenario_trim → **有效可见集**（供 supervisor 规划与委派令牌上界）。

设计纪律（承 SPEC §1 签收锁死）：

1. **Host 权威**：纯代码确定性函数，零 LLM 零 IO 可重放可机验；裁剪键
   只取意图字段（needs_tool / domain / risk_hint）+ intent_fallback
   标记；is_composite / summary **不作裁剪键**（自由文本/复杂度不作
   安全键 · 仅 span 观测）；会话上下文不参与（Q2 裁定）。
2. **安全默认**：宁可无工具——意图不可信（fallback）/ 域不可识别仍要
   工具（歧义）→ 可见集退化为空集；缺 risk_hint 视同 high（收紧）；
   缺 domain 视同 unknown。
3. **三档模式**：LG_RAG_VISIBILITY_SCENARIO_MODE=off|observe|enforce
   默认 off；observe 记 would_strip 不生效；非法值回退 off。
4. **记动作不记内容**：剔除记 capability_id + reason 码 + 计数；
   不记 query/intent 原文；off 零日志。

档位口径（承 SPEC §2 D1）：low=常规检索问答 · medium=跨域聚合/多步操作 ·
high=涉写意图/敏感域/模糊高影响请求。
"""

from __future__ import annotations

import logging
import os
from typing import Any

from app.ops.capability.types import CapabilitySpec

logger = logging.getLogger(__name__)

ENV_SCENARIO_MODE = "LG_RAG_VISIBILITY_SCENARIO_MODE"

# 剔除原因码（稳定词表 · 记码不记内容）
REASON_INTENT_FALLBACK = "intent_fallback"  # S1：意图不可信 → 空集
REASON_NEEDS_TOOL_FALSE = "needs_tool_false"  # S2：不需要工具 → 空集（既有行为承接）
REASON_DOMAIN_UNKNOWN = "domain_unknown"  # S3：域不可识别仍要工具 → 空集
REASON_RISK_HIGH_TIGHTEN = "risk_high_tighten"  # S4：high 意图收紧只留 low

_RISK_HINTS = ("low", "medium", "high")


def scenario_mode() -> str:
    """三档：off|observe|enforce；默认 off（零 diff）；非法值回退 off。"""
    raw = os.environ.get(ENV_SCENARIO_MODE, "").strip().lower()
    return raw if raw in ("off", "observe", "enforce") else "off"


def scenario_trim(
    base_visible: list[CapabilitySpec],
    intent: Any,
    intent_fallback: bool,
) -> tuple[list[CapabilitySpec], list[tuple[str, str]]]:
    """场景维裁剪纯函数：返回 (最终可见集, 剔除项 [(capability_id, reason)])。

    规则表（v1 裁定 · 按序适用）：

    - S1 intent_fallback=True → 空集（意图不可信 · 宁可无工具）；
    - S2 needs_tool=False → 空集（既有行为承接 · 不新增语义）；
    - S3 domain=unknown 且 needs_tool=True → 空集（歧义）；
    - S4 risk_hint=high → 只留 risk_level=low（high 已被基线剔除 · 剔 medium）；
    - S5 risk_hint ∈ {low, medium} → 不追加裁剪（基线即终态）。
    """
    specs = list(base_visible or [])
    if intent_fallback:
        return [], [(s.capability_id, REASON_INTENT_FALLBACK) for s in specs]
    mapping = intent if isinstance(intent, dict) else {}
    needs_tool = mapping.get("needs_tool")
    if needs_tool is False:
        return [], [(s.capability_id, REASON_NEEDS_TOOL_FALSE) for s in specs]
    # 缺 domain 视同 unknown（畸形 intent 安全默认）
    domain = str(mapping.get("domain") or "").strip() or "unknown"
    if domain == "unknown" and needs_tool is True:
        return [], [(s.capability_id, REASON_DOMAIN_UNKNOWN) for s in specs]
    risk_hint = str(mapping.get("risk_hint") or "").strip().lower()
    if risk_hint not in _RISK_HINTS:
        # 缺/畸形 risk_hint 视同 high（安全默认收紧 · 不虚假宽松）
        risk_hint = "high"
    if risk_hint == "high":
        final = [s for s in specs if str(s.risk_level) == "low"]
        stripped = [
            (s.capability_id, REASON_RISK_HIGH_TIGHTEN)
            for s in specs
            if str(s.risk_level) != "low"
        ]
        return final, stripped
    return specs, []


def audit_scenario_stripped(
    stripped: list[tuple[str, str]], *, would_strip: bool = False
) -> None:
    """剔除台账（D3）：logger 结构化行 + span metadata；id+reason 码+计数。

    记动作不记内容：不含 query/intent 原文；off 模式调用方短路（零日志）。
    """
    if not stripped:
        return
    ids = [cid for cid, _ in stripped]
    reasons: dict[str, int] = {}
    for _, reason in stripped:
        reasons[reason] = reasons.get(reason, 0) + 1
    action = "would_strip" if would_strip else "stripped"
    logger.warning(
        "visibility_scenario_%s ids=%s reasons=%s",
        action,
        ids,
        reasons,
    )
    try:
        from app.ops.tracing import update_current_span_metadata

        metadata: dict[str, Any] = {
            "scenario_stripped_count": len(stripped),
            "scenario_stripped_reasons": reasons,
        }
        if would_strip:
            metadata["would_strip"] = True
        update_current_span_metadata(metadata)
    except Exception:  # 观测面故障绝不拖垮主流程
        pass
