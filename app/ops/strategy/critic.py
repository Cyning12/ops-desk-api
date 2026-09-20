"""Critic 规则 stub（S4 · 无 LLM 主路径）。

节点 id 必须是 ``critic_node``：LangGraph 禁止与 state key 同名。
判定写 ``critic_verdict``；回环时**裁剪** subtasks / subtask_results 到不可变前缀
（Q8：已成功步骤的结果不得被抹掉，否则重规划等于全量重来、前缀无从锁定）。
rebind 只再跑 Builder，不自动扩权、不绕过 Policy。

与 supervisor 总步预算（H-β）优先级：全局耗尽优先于局部
``MAX_INNER_RETRIES`` / ``MAX_REBINDING``——已耗尽则禁止 retry/rebind，强制 ``end``。
"""

from __future__ import annotations

from app.ops.lg_rag.multi.budget import (
    bump_supervisor_step,
    is_supervisor_budget_exhausted,
)
from app.ops.lg_rag.schemas.critic import CriticVerdict
from app.ops.lg_rag.state import (
    LgRagState,
    SubtaskResultBatch,
    success_terminal_ids,
    unresolved_suffix_ids,
)
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
    """纯函数：无 error → pass；error+空 allowlist → rebind；error+非空 → retry_planner；超预算 → end。

    辅闸：全局 supervisor 总步/墙钟已耗尽时，禁止 retry/rebind，强制 ``end``。
    """
    if not _has_error(state.get("subtask_results")):
        return "pass"
    # 全局耗尽优先于局部 1+1 回环额度
    if is_supervisor_budget_exhausted(state):
        return "end"
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
    """条件边：读节点写回后的 ``critic_verdict.outcome``；全局耗尽禁回环。"""
    verdict = state.get("critic_verdict") or {}
    outcome = verdict.get("outcome") if isinstance(verdict, dict) else None
    if outcome in ("retry_planner", "rebind") and is_supervisor_budget_exhausted(state):
        return "end"
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
    bump = bump_supervisor_step(state)
    # 辅闸读含本节点入口计数后的视图（本步 tip-over 也禁回环）
    outcome = decide_critic_verdict({**state, **bump})
    reason = _reason_for(outcome)
    inner = int(state.get("inner_retry_count") or 0)
    rebind = int(state.get("rebinding_count") or 0)
    update: dict = {
        **bump,
        "critic_verdict": CriticVerdict(outcome=outcome, reason=reason).model_dump(),
        "inner_retry_count": inner,
        "rebinding_count": rebind,
    }
    if outcome in ("retry_planner", "rebind"):
        # Q8：只丢"可变后缀"，前缀（已成功步骤）连计划带结果一起留下。
        # 整批清空的话，supervisor 重规划时算不出前缀 ⇒ 已跑过的步骤会被重跑一遍。
        prefix = success_terminal_ids(
            state.get("subtasks"), state.get("subtask_results")
        )
        prefix_set = set(prefix)
        # ★ 未解决的后缀（失败 / 未终态）**必须跟着走**，不能只留前缀。
        #   只留前缀 = 把失败记录一起裁掉：它随即变成"计划外 id"，
        #   observe 按 plan_ids 过滤看不见、aggregator 更看不见，
        #   结论会写成"已覆盖全部子任务"——失败被静默抹掉。
        #   （与 supervisor 重规划的 carry 是同一个洞，两边都得堵。）
        unresolved = set(
            unresolved_suffix_ids(
                state.get("subtasks"), state.get("subtask_results"), prefix_set
            )
        )
        keep = prefix_set | unresolved
        plan_rows = [
            row
            for row in (state.get("subtasks") or [])
            if isinstance(row, dict)
            and str(row.get("subtask_id") or "").strip() in keep
        ]
        update["subtasks"] = plan_rows
        update["subtask_results"] = SubtaskResultBatch([], keep, replace=True)
        update["plan_prefix_ids"] = prefix
        update["recoverable_point"] = len(prefix)
        if outcome == "retry_planner":
            inner += 1
            update["inner_retry_count"] = inner
        else:
            rebind += 1
            update["rebinding_count"] = rebind
    span_meta = {
        "critic_outcome": outcome,
        "inner_retry_count": inner,
        "rebinding_count": rebind,
        "plan_prefix_len": len(update.get("plan_prefix_ids") or []),
    }
    with trace_span("critic", run_type="chain", **span_meta):
        _record_critic_span(span_meta)
        return update
