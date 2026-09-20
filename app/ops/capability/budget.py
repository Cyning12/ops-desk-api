"""会话配额 + kill switch（P0-2 · 失控兜底）。

为什么要有
----------
已有的预算管的是 **supervisor 的步数**（``lg_rag/multi/budget.py``，32 步 / 墙钟），
它回答不了：**一个会话里打了多少次工具调用、尤其多少次写**。
幻觉的典型形态不是"步数超限"，而是**在一步里反复打同一个写能力**——
步数预算看不见这个，而代价是重复建单。

所以这里补两个闸：

1. **per-session 配额**：调用总数 + **写操作数**（两个上限，后者更贵）。
2. **kill switch**：按能力 id / 前缀 / ``write:*`` 紧急停用。

失败口径落在**既有七个码**里（错误码词表"七个、不增"）：
- kill switch → ``disabled: kill_switch ...``
- 配额耗尽 → ``policy_blocked: budget_exhausted ...``
两者都属于 NO_RETRY，模型不该"再试一次"。

边界
----
计数是**进程内**的（与进程内注册表、metrics 同源）。多实例下各进程各一份，
这是已知边界——要跨实例就走 DB，但那会把"泄流"变成"分布式计数"，
当前阶段不值得。``/runtime`` 会把这份边界**显式说出来**，不假装是全局的。

kill switch 只支持**全局**（不按租户分）：紧急开关的第一要求是"一按就全停"，
按租户分会把"我到底停干净了没有"变成一个需要推理的问题。
"""

from __future__ import annotations

import os
import threading
from typing import Any

from app.ops.capability.errors import DISABLED, POLICY_BLOCKED, format_error
from app.ops.capability.types import WRITE_SIDE_EFFECTS

#: 每个会话允许的**调用总数**（0 = 不限）
_ENV_MAX_CALLS = "OPS_CAPABILITY_MAX_CALLS_PER_SESSION"
#: 每个会话允许的**写操作次数**（0 = 不限）。这是最该被卡住的一个数字。
_ENV_MAX_WRITES = "OPS_CAPABILITY_MAX_WRITES_PER_SESSION"
#: 紧急停用：逗号分隔，支持 ``oa.ticket.create`` / ``oa.*`` / ``write:*`` / ``*``
_ENV_KILL_SWITCH = "OPS_CAPABILITY_KILL_SWITCH"

#: 默认值刻意选"**真实有上限**但不会误伤现有流程"的量级：
#: 失控是几十上百次，而正常会话（含联调冒烟）远低于此。
DEFAULT_MAX_CALLS = 64
DEFAULT_MAX_WRITES = 8

_LOCK = threading.Lock()
#: session_key → {"calls": n, "writes": n}
_SESSIONS: dict[str, dict[str, int]] = {}
_BLOCKED_CALLS = 0
_BLOCKED_WRITES = 0
_EVICTED_SESSIONS = 0

#: 追踪的会话数必须有**上界**：key 是 run_id，长跑进程里会一直累积，
#: 无界字典 = 缓慢的内存泄漏。超界按**插入顺序**淘汰最老的（dict 保序）。
#: 代价：被淘汰的会话配额归零（等于换个桶重新数）。这是已知边界，
#: 且在下面 :func:`snapshot` 里**显式报出来**，不假装没发生过。
MAX_TRACKED_SESSIONS = 512


def _int_env(name: str, default: int) -> int:
    raw = os.environ.get(name, "").strip()
    if not raw:
        return default
    try:
        n = int(raw)
    except ValueError:
        return default
    return n if n >= 0 else default


def limits() -> dict[str, int]:
    return {
        "max_calls": _int_env(_ENV_MAX_CALLS, DEFAULT_MAX_CALLS),
        "max_writes": _int_env(_ENV_MAX_WRITES, DEFAULT_MAX_WRITES),
    }


def kill_switch_patterns() -> tuple[str, ...]:
    raw = os.environ.get(_ENV_KILL_SWITCH, "").strip()
    return tuple(p.strip() for p in raw.split(",") if p.strip())


def _run_of_subtask(subtask_id: str) -> str:
    """``run_id:seq`` → ``run_id``；不是这种形态返回 ``""``。

    Host 签发的 subtask_id 形如 ``{run_id}:{seq}``（见 ``lg_rag/multi/nodes``）。
    只认"尾段是纯数字"的形态，避免把任意冒号串误当成 run。
    """
    head, sep, tail = subtask_id.rpartition(":")
    if sep and tail.isdigit():
        return head
    return ""


def session_key(ctx: dict[str, Any] | None) -> str:
    """会话维度：``session_id`` → ``run_id`` → subtask 推回 ``run_id`` → ``租户:用户``。

    **``subtask_id`` 不能当会话维度**（这是写第一版时踩的坑）：子任务是
    ``run_id:seq``，一个子任务基本就打一次工具，按它分桶 ⇒ 每个桶最多 1 次，
    配额**永远打不满**——那是一道"看起来有闸"的假门，比没有更危险。
    所以这里先剥出 run 段；剥不出来才往下退。

    拿不到任何标识时返回 ``""``（一个共享桶）——**不因此放行**：
    匿名调用照样计数，否则"不传 ctx"就成了绕过配额的捷径。
    """
    ctx = ctx or {}
    for key in ("session_id", "_session_id", "run_id", "_run_id"):
        value = ctx.get(key)
        if value:
            return str(value)
    for key in ("subtask_id", "_subtask_id"):
        value = ctx.get(key)
        if not value:
            continue
        sid = str(value)
        run = _run_of_subtask(sid)
        if run:
            return run
    tenant = str(ctx.get("tenant_id") or ctx.get("_host_tenant") or "")
    user = str(ctx.get("user_id") or ctx.get("_user_id") or "")
    if tenant or user:
        return f"{tenant}:{user}"
    return ""


def _matches_kill_switch(cid: str, side_effect: str) -> str | None:
    """返回命中的开关模式；未命中返回 None。"""
    for pattern in kill_switch_patterns():
        if pattern == "*":
            return pattern
        if pattern == "write:*" and side_effect in WRITE_SIDE_EFFECTS:
            return pattern
        if pattern.endswith("*"):
            if cid.startswith(pattern[:-1]):
                return pattern
        elif pattern == cid:
            return pattern
    return None


def is_killed(spec: Any) -> str | None:
    """能力是否被紧急停用；返回命中的模式（未停用返回 None）。"""
    return _matches_kill_switch(
        str(getattr(spec, "capability_id", "") or ""),
        str(getattr(spec, "side_effect", "") or ""),
    )


def check(spec: Any, *, ctx: dict[str, Any] | None) -> str | None:
    """执行前检查。放行返回 ``None``；拦截返回**稳定错误码串**。"""
    killed = is_killed(spec)
    if killed is not None:
        return format_error(DISABLED, f"kill_switch={killed}")

    max_calls, max_writes = limits()["max_calls"], limits()["max_writes"]
    if not max_calls and not max_writes:
        return None

    key = session_key(ctx)
    is_write = str(getattr(spec, "side_effect", "") or "") in WRITE_SIDE_EFFECTS
    with _LOCK:
        used = _SESSIONS.get(key, {"calls": 0, "writes": 0})
        if max_writes and is_write and used["writes"] >= max_writes:
            global _BLOCKED_WRITES
            _BLOCKED_WRITES += 1
            return format_error(
                POLICY_BLOCKED,
                f"budget_exhausted: writes={used['writes']}/{max_writes} session={key or '(匿名)'}",
            )
        if max_calls and used["calls"] >= max_calls:
            global _BLOCKED_CALLS
            _BLOCKED_CALLS += 1
            return format_error(
                POLICY_BLOCKED,
                f"budget_exhausted: calls={used['calls']}/{max_calls} session={key or '(匿名)'}",
            )
    return None


def count(spec: Any, *, ctx: dict[str, Any] | None) -> None:
    """**已放行、即将真正执行**时计数。

    被 Policy / 配额 / kill switch 拦下的不计——否则"反复尝试但都被拒"
    会把配额打满，反而让一次正常的调用也被误伤。
    """
    key = session_key(ctx)
    is_write = str(getattr(spec, "side_effect", "") or "") in WRITE_SIDE_EFFECTS
    with _LOCK:
        bucket = _SESSIONS.get(key)
        if bucket is None:
            # 先淘汰再插入，保证字典长度有界
            while len(_SESSIONS) >= MAX_TRACKED_SESSIONS:
                _SESSIONS.pop(next(iter(_SESSIONS)), None)
                global _EVICTED_SESSIONS
                _EVICTED_SESSIONS += 1
            bucket = {"calls": 0, "writes": 0}
            _SESSIONS[key] = bucket
        bucket["calls"] += 1
        if is_write:
            bucket["writes"] += 1


def reset(*, key: str | None = None) -> None:
    """清空计数（``key=None`` 清全部）。

    测试**必须**在每个用例前调一次：这是进程内全局状态，和注册表、metrics 同源。
    不 reset 的话前一个用例打过的调用会累计到下一个用例——而所有不传 ctx 的调用
    共用匿名桶 ``""``，跑满 64 次之后后面全被拦，"看起来像功能坏了"。
    """
    global _BLOCKED_CALLS, _BLOCKED_WRITES
    with _LOCK:
        if key is not None:
            _SESSIONS.pop(key, None)
            return
        _SESSIONS.clear()
        # 拦截计数也是进程内的，一并清——否则跨用例累积出来的
        # blocked_calls 会让"拦了几次"这种断言变成顺序依赖。
        _BLOCKED_CALLS = 0
        _BLOCKED_WRITES = 0


def snapshot() -> dict[str, Any]:
    """/runtime 观测用。**显式标出进程内边界**，不假装是全局计数。"""
    with _LOCK:
        sessions = {k: dict(v) for k, v in _SESSIONS.items()}
        blocked_calls = _BLOCKED_CALLS
        blocked_writes = _BLOCKED_WRITES
        evicted = _EVICTED_SESSIONS
    lim = limits()
    return {
        "limits": lim,
        "kill_switch": list(kill_switch_patterns()),
        "kill_switch_active": bool(kill_switch_patterns()),
        "sessions": sessions,
        "blocked_calls": blocked_calls,
        "blocked_writes": blocked_writes,
        "tracked_sessions": len(sessions),
        "max_tracked_sessions": MAX_TRACKED_SESSIONS,
        "evicted_sessions": evicted,
        # 已知边界：多实例各进程各一份
        "scope": "process-local",
    }
