"""Critic 规则 stub（S4 · 无 LLM 主路径）。

节点 id 必须是 ``critic_node``：LangGraph 禁止与 state key 同名。
判定写 ``critic_verdict``；回环时清空 subtasks / subtask_results。
rebind 只再跑 Builder，不自动扩权、不绕过 Policy。
"""

from __future__ import annotations

from app.ops.lg_rag.schemas.critic import CriticVerdict
from app.ops.lg_rag.state import LgRagState
from app.ops.tracing import trace_span, tracing_enabled, update_current_span_metadata

MAX_INNER_RETRIES = 1
MAX_REBINDING = 1

_REASON_NO_ERROR = "no_error"
_REASON_EMPTY_ALLOWLIST = "error_empty_allowlist"
_REASON_NONEMPTY_ALLOWLIST = "error_nonempty_allowlist"
_REASON_BUDGET = "budget_exhausted"


def _has_error(results: object) -> bool:
    if not isinstance(results, list):
        return False
    return any(isinstance(r, dict) and "error" in r for r in results)


def _allowlist_empty(state: LgRagState) -> bool:
    allowlist = state.get("allowed_capability_ids")
    return not allowlist


def decide_critic_verdict(state: LgRagState) -> str:
    """纯函数：无 error → pass；error+空 allowlist → rebind；error+非空 → retry_planner；超预算 → end。"""
    if not _has_error(state.get("subtask_results")):
        return "pass"
    inner = int(state.get("inner_retry_count") or 0)
    rebind = int(state.get("rebinding_count") or 0)
    if _allowlist_empty(state):
        return "rebind" if rebind < MAX_REBINDING else "end"
    return "retry_planner" if inner < MAX_INNER_RETRIES else "end"


def _reason_for(outcome: str) -> str:
    if outcome == "pass":
        return _REASON_NO_ERROR
    if outcome == "end":
        return _REASON_BUDGET
    if outcome == "rebind":
        return _REASON_EMPTY_ALLOWLIST
    if outcome == "retry_planner":
        return _REASON_NONEMPTY_ALLOWLIST
    return ""


def route_after_critic(state: LgRagState) -> str:
    """条件边：读节点写回后的 ``critic_verdict.outcome``。"""
    verdict = state.get("critic_verdict") or {}
    outcome = verdict.get("outcome") if isinstance(verdict, dict) else None
    if outcome in ("pass", "retry_planner", "rebind", "end"):
        return str(outcome)
    return "end"


def _record_critic_span(metadata: dict) -> None:
    if not tracing_enabled():
        return
    try:
        from langfuse import get_client

        get_client().update_current_span(metadata=metadata)
    except Exception:
        pass
    update_current_span_metadata(metadata)


async def critic_node(state: LgRagState) -> dict:
    """写 critic_verdict；retry/rebind 时递增计数并清空 subtasks / results。"""
    outcome = decide_critic_verdict(state)
    reason = _reason_for(outcome)
    inner = int(state.get("inner_retry_count") or 0)
    rebind = int(state.get("rebinding_count") or 0)
    update: dict = {
        "critic_verdict": CriticVerdict(outcome=outcome, reason=reason).model_dump(),
        "inner_retry_count": inner,
        "rebinding_count": rebind,
    }
    if outcome == "retry_planner":
        inner += 1
        update["inner_retry_count"] = inner
        update["subtasks"] = []
        update["subtask_results"] = None
    elif outcome == "rebind":
        rebind += 1
        update["rebinding_count"] = rebind
        update["subtasks"] = []
        update["subtask_results"] = None
    span_meta = {
        "critic_outcome": outcome,
        "inner_retry_count": inner,
        "rebinding_count": rebind,
    }
    with trace_span("critic", run_type="chain", **span_meta):
        _record_critic_span(span_meta)
        return update
