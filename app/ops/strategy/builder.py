"""Strategy Builder 节点（S1-b · 规则/配置 · 无 LLM）。

写 ``allowed_capability_ids`` ⊆ Registry ∩ Policy 可见；非法 id 剔除 + span。
"""

from __future__ import annotations

import logging
from typing import Any

from app.ops.capability import list_capabilities
from app.ops.capability.baseline import baseline_filter
from app.ops.capability.types import CapabilityFilter, CapabilitySpec
from app.ops.lg_rag.multi.budget import bump_supervisor_step
from app.ops.lg_rag.state import LgRagState
from app.ops.strategy.config import get_candidate_capability_ids
from app.ops.tracing import trace_span, tracing_enabled, update_current_span_metadata

logger = logging.getLogger(__name__)

# 与 supervisor **共用同一份基线**（见 capability.baseline）：
# local_fn 全可见 + 按域放行的新 kind（如 oa 的 http）+ 剔除 high risk + 剔除写能力。
BUILDER_CAP_FILTER = baseline_filter(node_role="strategy_builder")


def get_policy_visible_catalog(
    *, cap_filter: CapabilityFilter | None = None
) -> list[CapabilitySpec]:
    """Registry ∩ Policy 可见 catalog（Builder / supervisor 共用 filter 语义）。"""
    return list_capabilities(filter=cap_filter or BUILDER_CAP_FILTER)


def get_policy_visible_ids(
    *, cap_filter: CapabilityFilter | None = None
) -> frozenset[str]:
    return frozenset(s.capability_id for s in get_policy_visible_catalog(cap_filter=cap_filter))


def build_allowlist_from_candidates(
    candidates: list[str] | None,
    *,
    visible_ids: frozenset[str] | None = None,
) -> tuple[list[str], list[str]]:
    """从候选 id 构建 allowlist；返回 ``(allowed, stripped)``。

    ``candidates is None``：**已废弃**生产语义（旧「全开」）；现等同空列表。
    生产路径须经 ``get_candidate_capability_ids``（永不 None）。
    """
    visible = visible_ids if visible_ids is not None else get_policy_visible_ids()
    if candidates is None:
        # 废弃：禁止 None=全开；安全默认空
        return [], []
    allowed = [cid for cid in candidates if cid in visible]
    stripped = [cid for cid in candidates if cid not in visible]
    if stripped:
        logger.warning(
            "strategy_builder 剔除非法/不可见 capability id: %s",
            stripped,
        )
    return allowed, stripped


# A2 声明集上限（承 step_contract MAX_FIELDS 纪律 · SPEC FP-7）：超出截断+审计
MAX_SCOPE_IDS = 64


def effective_scope_from_requested(
    requested_scope: Any,
    allowlist: list[str] | frozenset[str] | set[str],
) -> tuple[list[str], list[str], list[str]]:
    """「声明∩裁剪」（Host V1-A · A2）：有效 scope = 声明 ∩ allowlist。

    返回 (scope, stripped, truncated)：

    - 未声明（None / 非 list）→ **兼容现状**：隐式 allowlist 原样返回
      （stripped / truncated 为空；承 subtasks cap 外宽容纪律，
      非 list 视同未声明）；
    - 已声明 → 逐项清洗（去空白去重保序），越 allowlist 的 id **剔除**
      （stripped · 审计 scope_stripped · 只收窄不放宽）；
    - 声明超 MAX_SCOPE_IDS → 截断（truncated 为被截掉的 id · 审计）。
    """
    allowed_set = {str(cid) for cid in allowlist}
    if not isinstance(requested_scope, list):
        return list(allowlist), [], []
    declared: list[str] = []
    for item in requested_scope:
        token = str(item or "").strip()
        if token and token not in declared:
            declared.append(token)
    truncated = declared[MAX_SCOPE_IDS:]
    declared = declared[:MAX_SCOPE_IDS]
    scope = [cid for cid in declared if cid in allowed_set]
    stripped = [cid for cid in declared if cid not in allowed_set]
    if stripped:
        logger.warning(
            "strategy_builder scope_stripped：声明越出 allowlist 的 capability id 已剔除: %s",
            stripped,
        )
    if truncated:
        logger.warning(
            "strategy_builder scope_truncated：声明超 MAX_SCOPE_IDS=%d 已截断: %s",
            MAX_SCOPE_IDS,
            truncated,
        )
    return scope, stripped, truncated


def _record_builder_span(metadata: dict) -> None:
    if not tracing_enabled():
        return
    try:
        from langfuse import get_client

        get_client().update_current_span(metadata=metadata)
    except Exception:
        pass
    update_current_span_metadata(metadata)


async def strategy_builder_node(state: LgRagState) -> dict:
    """写本轮 ``allowed_capability_ids``（及空 ``allowed_skill_ids``）。

    S2：读 ``state.intent``。
    - ``needs_tool is False`` → 空 capability allowlist（supervisor fallback 单 rag）
    - ``needs_tool is True`` 或缺 intent → 仍 ⊆ Registry∩Policy（S1 求交）
    - ``needs_skill`` 本波仍写空 ``allowed_skill_ids``
    - ``risk_hint`` 不得绕过 Policy（始终 deny_high_risk）
    """
    bump = bump_supervisor_step(state)
    with trace_span("strategy_builder", run_type="chain"):
        visible = get_policy_visible_catalog()
        visible_ids = frozenset(s.capability_id for s in visible)
        intent = state.get("intent") or {}
        needs_tool = intent.get("needs_tool")
        if needs_tool is False:
            allowed, stripped = [], []
        else:
            # 按 agent_type / mode 显式 allowlist；未知 key → []（非全开）
            agent_type = None
            if isinstance(intent, dict):
                raw_at = intent.get("agent_type")
                if raw_at is not None:
                    agent_type = str(raw_at)
            mode = state.get("mode")
            mode_s = str(mode) if mode is not None else None
            candidates = get_candidate_capability_ids(
                agent_type=agent_type, mode=mode_s or "supervisor"
            )
            allowed, stripped = build_allowlist_from_candidates(
                candidates, visible_ids=visible_ids
            )
        span_meta: dict = {
            "module": "strategy_builder",
            "strategy_builder_catalog_count": len(visible),
            "strategy_builder_allowed_count": len(allowed),
        }
        if stripped:
            span_meta["strategy_builder_stripped_ids"] = stripped
        if intent:
            span_meta["intent_needs_tool"] = needs_tool
            span_meta["intent_risk_hint"] = intent.get("risk_hint")
        _record_builder_span(span_meta)
        return {
            **bump,
            "allowed_capability_ids": allowed,
            "allowed_skill_ids": [],
        }
