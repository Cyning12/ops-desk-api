"""supervisor 图总步 / 可选墙钟预算（阶段 H · 波次 β）。

优先级：全局总步或墙钟耗尽 → 主闸 ``route_next_subtask`` 收束到 ``aggregate``；
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
