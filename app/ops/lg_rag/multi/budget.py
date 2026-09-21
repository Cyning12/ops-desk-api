"""supervisor 图总步 / 可选墙钟预算（阶段 H · 波次 β）。

优先级：全局总步或墙钟耗尽 → 主闸 ``route_next_subtask`` 收束到 ``observe``
（**不再直连 aggregator**：没有待发步骤 ≠ 这一轮满足了问题，先让 observe 收口）；
辅闸禁止 critic ``retry_planner`` / ``rebind``。与 ``MAX_SUBTASKS=4``、
critic ``MAX_INNER_RETRIES``/``MAX_REBINDING``=1 **并存**；全局耗尽优先于局部回环额度。

不计 ``rag_subtask`` 内部 router 子图节点。
"""

from __future__ import annotations

import os
import time
from typing import Any

# 文档/钉死默认；运行时以 get_max_supervisor_steps() 为准（读 env）
DEFAULT_MAX_SUPERVISOR_STEPS = 32
MAX_SUPERVISOR_STEPS = DEFAULT_MAX_SUPERVISOR_STEPS

_ENV_MAX_STEPS = "LG_RAG_SUPERVISOR_MAX_STEPS"
_ENV_MAX_WALL = "LG_RAG_SUPERVISOR_MAX_WALL_SECONDS"


# ---- 外层 ReAct 的**轮次**预算（Q8 延伸：与内层"步数"是两个维度）----
#
# 内层 plan-and-execute 的预算是**步数**（一个节点一次）；
# 外层 ReAct 的预算是**轮数**（plan → execute → observe 算一轮）。
# 两者不能互相替代：步数耗尽只是"这轮别再开新节点了"，
# 而"总共允许重规划几次"必须单独封顶，否则一次不满意就永远再来一轮。
DEFAULT_MAX_REACT_ROUNDS = 2
MAX_REACT_ROUNDS = DEFAULT_MAX_REACT_ROUNDS
_ENV_MAX_ROUNDS = "LG_RAG_REACT_MAX_ROUNDS"


def get_max_react_rounds() -> int:
    """读 ``LG_RAG_REACT_MAX_ROUNDS``；缺省 / 非法 / ≤0 → 回退 2（禁无限）。"""
    raw = os.environ.get(_ENV_MAX_ROUNDS, str(DEFAULT_MAX_REACT_ROUNDS))
    try:
        n = int(str(raw).strip())
    except (TypeError, ValueError):
        return DEFAULT_MAX_REACT_ROUNDS
    return n if n > 0 else DEFAULT_MAX_REACT_ROUNDS


def is_react_round_exhausted(state: dict[str, Any]) -> bool:
    """再开一轮就超上限 ⇒ 不再开新轮，直接收口出结论。

    ``react_round`` 记的是**已完成**的轮数：第 1 轮收口时它是 0。
    所以判据是 ``已完成 + 1 >= 上限``，不是 ``已完成 >= 上限``——
    后者会让"上限 2"变成实际跑 3 轮。
    """
    return int(state.get("react_round") or 0) + 1 >= get_max_react_rounds()


def bump_react_round(state: dict[str, Any]) -> dict[str, Any]:
    """observe 收口一轮：轮数 +1。"""
    return {"react_round": int(state.get("react_round") or 0) + 1}


def get_max_supervisor_steps() -> int:
    """读 ``LG_RAG_SUPERVISOR_MAX_STEPS``；缺省 / 非法 / ≤0 → 回退 32（禁无限）。"""
    raw = os.environ.get(_ENV_MAX_STEPS, str(DEFAULT_MAX_SUPERVISOR_STEPS))
    try:
        n = int(str(raw).strip())
    except (TypeError, ValueError):
        return DEFAULT_MAX_SUPERVISOR_STEPS
    if n <= 0:
        return DEFAULT_MAX_SUPERVISOR_STEPS
    return n


def get_max_wall_seconds() -> float:
    """读 ``LG_RAG_SUPERVISOR_MAX_WALL_SECONDS``；缺省 / 非法 / ≤0 → 0（关闭）。"""
    raw = os.environ.get(_ENV_MAX_WALL, "0")
    try:
        n = float(str(raw).strip())
    except (TypeError, ValueError):
        return 0.0
    if n <= 0:
        return 0.0
    return n


def _wall_exceeded(started_at: Any, *, now: float | None = None) -> bool:
    max_wall = get_max_wall_seconds()
    if max_wall <= 0 or started_at is None:
        return False
    try:
        started = float(started_at)
    except (TypeError, ValueError):
        return False
    t = time.monotonic() if now is None else now
    return (t - started) >= max_wall


def is_supervisor_budget_exhausted(
    state: dict[str, Any], *, now: float | None = None
) -> bool:
    """总步 / 耗尽旗标 / 墙钟（若开启）任一触发即视为全局耗尽。"""
    if state.get("supervisor_budget_exhausted") is True:
        return True
    count = int(state.get("supervisor_step_count") or 0)
    if count >= get_max_supervisor_steps():
        return True
    return _wall_exceeded(state.get("supervisor_started_at"), now=now)


def bump_supervisor_step(
    state: dict[str, Any], *, now: float | None = None
) -> dict[str, Any]:
    """节点入口 +1；首次写入 ``supervisor_started_at``；耗尽时置旗。"""
    count = int(state.get("supervisor_step_count") or 0) + 1
    update: dict[str, Any] = {"supervisor_step_count": count}
    started = state.get("supervisor_started_at")
    if started is None:
        started = time.monotonic() if now is None else now
        update["supervisor_started_at"] = started
    exhausted = (
        state.get("supervisor_budget_exhausted") is True
        or count >= get_max_supervisor_steps()
        or _wall_exceeded(started, now=now)
    )
    if exhausted:
        update["supervisor_budget_exhausted"] = True
    return update
