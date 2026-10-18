"""下游熔断（P1 · 八问 Q3）。

为什么要有
----------
下游连续故障时，**每一次调用都要再付一次完整超时**才知道它还挂着。三个后果：
慢（一步 8s）、**放大下游负载**（下游已经在挣扎还继续打）、
重试纪律失效（GET 会重试一次，等于打两遍）。

熔断回答的是"**这个下游现在还打得通吗**"，与写放行/审批（"该不该做"）正交。

三态（命名按业界标准；中文直觉容易读反）
--------------------------------------
- **closed** = 电路闭合 = **正常放行**
- **open** = 电路断开 = **熔断中，不放行**
- **half-open** = 恢复探测中，**瞬时**状态——只在"这一次探测进行中"存在，
  探测结束立刻落回 open 或 closed。

准确的行为（转换由调用驱动，不需要定时器，也就不存在"状态机漏跑"）：:

    open 且 now - opened_at >= 60s
        → 下一次调用放行一次（此刻标记 half-open）
        → 成功 → closed（恢复）
        → 失败 → open（opened_at 刷新，再等 60s）

怎么用 pybreaker（三个实测结论，别踩）
------------------------------------
1. ``call_async`` 是 **Tornado-only**（源码 ``@gen.coroutine``），不能用于 asyncio。
   asyncio 用 ``with breaker.calling(): result = await ...``（已验证可用）。
2. 它只在**抛异常**时计失败，所以要用 ``exclude`` 把"不算下游故障"的异常挑出去
   （见 :func:`_is_business_error`）；**成功**则由 ``calling()`` 正常退出自动记。
3. ``throw_new_error_on_trip=False``：否则跳闸那次会把真实根因换成
   ``CircuitBreakerError``，等于把错误原因吞了。

状态机**完全交给 pybreaker**：本模块不自己翻状态，只做两件它不管的事——
把 open 翻译成我们的错误口径、以及写能力不参与探测。
"""

from __future__ import annotations

import contextlib
import os
import threading
from collections.abc import Iterator
from datetime import UTC, datetime, timedelta
from typing import Any

import pybreaker

from app.ops.capability import circuit_storage
from app.ops.capability.circuit_storage import FallbackStorage
from app.ops.capability.errors import (
    UPSTREAM_ERROR,
    is_environmental_failure,
)
from app.ops.capability.types import WRITE_SIDE_EFFECTS

_ENV_ENABLED = "OPS_CAPABILITY_CB_ENABLED"
_ENV_FAIL_MAX = "OPS_CAPABILITY_CB_FAIL_MAX"
_ENV_RESET_TIMEOUT = "OPS_CAPABILITY_CB_RESET_TIMEOUT"
_ENV_SUCCESS_THRESHOLD = "OPS_CAPABILITY_CB_SUCCESS_THRESHOLD"
_ENV_SCOPE = "OPS_CAPABILITY_CB_SCOPE"
_ENV_HALFOPEN_WRITES = "OPS_CAPABILITY_CB_HALFOPEN_WRITES"

DEFAULT_FAIL_MAX = 5
#: 恢复时长（秒）——按需求指定
DEFAULT_RESET_TIMEOUT = 60
DEFAULT_SUCCESS_THRESHOLD = 1

SCOPE_CAPABILITY = "capability"
SCOPE_HOST = "host"

_LOCK = threading.Lock()
_BREAKERS: dict[str, pybreaker.CircuitBreaker] = {}
_BLOCKED_CALLS = 0


class CircuitOpen(Exception):  # noqa: N818 - 公开异常名，改名属 API 语义变更（另立 task）
    """熔断中，这次调用没有出门。

    带 ``detail``（含状态与剩余秒数），由 gateway 转成 ``upstream_error``。
    """

    def __init__(self, detail: str) -> None:
        self.detail = detail
        super().__init__(detail)


def _is_business_error(exc: BaseException) -> bool:
    """这次异常**不算**下游故障（业务响应 / 本地装配）→ 不计入熔断。

    判据（见 ``errors.is_environmental_failure``）：只有「不响应 / 5xx / 429」算故障。
    其余一律不算——**用户填错 5 次参数不能把整个能力停 60s**。
    """
    cause = getattr(exc, "cause", None)
    status = getattr(exc, "http_status", None)
    return not is_environmental_failure(cause, status)


def enabled() -> bool:
    return os.environ.get(_ENV_ENABLED, "1").strip().lower() not in ("0", "false", "no")


def _int_env(name: str, default: int) -> int:
    raw = os.environ.get(name, "").strip()
    if not raw:
        return default
    try:
        n = int(raw)
    except ValueError:
        return default
    return n if n > 0 else default


def _bool_env(name: str, default: bool) -> bool:
    raw = os.environ.get(name, "").strip().lower()
    if not raw:
        return default
    return raw in ("1", "true", "yes")


def limits() -> dict[str, Any]:
    return {
        "fail_max": _int_env(_ENV_FAIL_MAX, DEFAULT_FAIL_MAX),
        "reset_timeout": _int_env(_ENV_RESET_TIMEOUT, DEFAULT_RESET_TIMEOUT),
        "success_threshold": _int_env(_ENV_SUCCESS_THRESHOLD, DEFAULT_SUCCESS_THRESHOLD),
        "scope": os.environ.get(_ENV_SCOPE, "").strip().lower() or SCOPE_CAPABILITY,
        # 默认**否**：写探测失败的代价不对等（占幂等租约、留失败回执、
        # 让人去查"这张单到底建没建"）。让读能力先把路探开。
        "half_open_writes": _bool_env(_ENV_HALFOPEN_WRITES, False),
    }


def circuit_name(spec: Any) -> str:
    """breaker 的 key：默认**每个能力一个**（scope=capability）。

    scope=host 时才按 base_url 的 host 聚合。默认不这么做——同 host 的两个接口
    一个挂一个好是常态，按 host 熔会**误伤**健康的那个，
    把局部故障放大成整体不可用，正是熔断本该避免的事。
    """
    cid = str(getattr(spec, "capability_id", "") or "unknown")
    if limits()["scope"] != SCOPE_HOST:
        return cid
    http = getattr(spec, "http", None) or {}
    base_name = str(http.get("base_url") or "").strip()
    base = os.environ.get(base_name, "").strip()
    host = base.split("//", 1)[-1].split("/", 1)[0] if base else ""
    return f"host:{host or cid}"


def breaker_for(spec: Any) -> pybreaker.CircuitBreaker:
    """取（或建）这个能力对应的 breaker。进程内单例，跨调用存活。"""
    name = circuit_name(spec)
    lim = limits()
    with _LOCK:
        cb = _BREAKERS.get(name)
        if cb is None:
            cb = pybreaker.CircuitBreaker(
                fail_max=lim["fail_max"],
                reset_timeout=lim["reset_timeout"],
                success_threshold=lim["success_threshold"],
                # ★ 业务类异常不计入熔断（callable 形式：异常类型不够判定时用）
                exclude=[_is_business_error],
                name=name,
                # ★ 跳闸那次保留原始错误，别把根因换成 CircuitBreakerError
                throw_new_error_on_trip=False,
                state_storage=FallbackStorage(name),
            )
            _BREAKERS[name] = cb
        # 阈值可被 env 改：每次取用时同步，免得"改个配置要重启"
        cb.fail_max = lim["fail_max"]
        cb.reset_timeout = lim["reset_timeout"]
        cb.success_threshold = lim["success_threshold"]
        return cb


def _opened_at(cb: pybreaker.CircuitBreaker) -> datetime | None:
    # pybreaker 没有公开的 opened_at getter，观测必须读它（否则算不出剩余时间）
    opened = cb._state_storage.opened_at  # noqa: SLF001
    if opened is not None and opened.tzinfo is None:
        return opened.replace(tzinfo=UTC)
    return opened


def _elapsed_since_open(cb: pybreaker.CircuitBreaker) -> float | None:
    opened = _opened_at(cb)
    if opened is None:
        return None
    return (datetime.now(UTC) - opened).total_seconds()


def _remaining(cb: pybreaker.CircuitBreaker) -> float:
    elapsed = _elapsed_since_open(cb)
    if elapsed is None:
        return 0.0
    return max(0.0, float(limits()["reset_timeout"]) - elapsed)


def check(spec: Any) -> str | None:
    """**执行前**检查。放行返回 ``None``；拦截返回给调用方的 detail。

    这里只管 pybreaker 不管的一件事：**写能力不参与半开探测**。
    其余（open 直接拦、到点放行探测）由 :func:`guard` 里 ``calling()`` 驱动。
    """
    if not enabled():
        return None
    cb = breaker_for(spec)
    state = cb.current_state
    if state == pybreaker.STATE_CLOSED:
        return None

    is_write = str(getattr(spec, "side_effect", "") or "") in WRITE_SIDE_EFFECTS
    if not is_write or limits()["half_open_writes"]:
        return None  # 读能力（或显式允许写探测）→ 交给 calling() 决定
    # 写能力：只要不在 closed，一律不放行（可探测期也不探）
    return f"circuit_open: {cb.name} state={state} 剩余 {_remaining(cb):.0f}s 写能力不参与探测"


@contextlib.contextmanager
def guard(spec: Any) -> Iterator[None]:
    """包住**真实执行**：状态机交给 pybreaker，open 时翻译成 :class:`CircuitOpen`。

    用法（同步/异步都行，``await`` 写在 with 体内）::

        with circuit.guard(spec):
            output = await adapter.ainvoke(args, ctx=ctx)

    块内抛出的异常：
    - 环境类（超时/5xx/429）→ pybreaker 计一次失败，异常照常往外抛
    - 业务类 → 被 ``exclude`` 挑掉，不计数，异常照常往外抛
    - 熔断中 → 抛 :class:`CircuitOpen`（调用方转成 ``upstream_error``）
    """
    if not enabled():
        yield
        return
    cb = breaker_for(spec)
    try:
        with cb.calling():
            yield
    except pybreaker.CircuitBreakerError:
        global _BLOCKED_CALLS
        with _LOCK:
            _BLOCKED_CALLS += 1
        raise CircuitOpen(
            f"circuit_open: {cb.name} state={cb.current_state} 剩余 {_remaining(cb):.0f}s"
        ) from None


def error_detail(exc: CircuitOpen) -> str:
    """给模型的稳定错误串（``upstream_error`` + detail）。"""
    from app.ops.capability.errors import format_error  # 局部导入：避免与 errors 循环

    return format_error(UPSTREAM_ERROR, exc.detail)


def reset(*, name: str | None = None) -> None:
    """清空 breaker（``name=None`` 清全部）。

    测试**必须**在每个用例前调一次：这是进程内全局状态，与注册表、配额同源。
    """
    with _LOCK:
        if name is None:
            for cb in _BREAKERS.values():
                cb.close()
            _BREAKERS.clear()
        else:
            cb = _BREAKERS.pop(name, None)
            if cb is not None:
                cb.close()


def trip(spec: Any) -> None:
    """测试/运维用：手动把某个能力熔断（模拟连续失败）。"""
    breaker_for(spec).open()


def advance(spec_or_name: Any, seconds: float) -> None:
    """测试用：把 opened_at 往前拨，**不 sleep**（否则测 60s 恢复要真等）。"""
    name = spec_or_name if isinstance(spec_or_name, str) else circuit_name(spec_or_name)
    cb = _BREAKERS.get(name)
    if cb is None:
        return
    cb._state_storage.opened_at = datetime.now(UTC) - timedelta(seconds=seconds)  # noqa: SLF001


def snapshot() -> dict[str, Any]:
    """/runtime 观测用。"""
    lim = limits()
    shared = circuit_storage.is_shared()
    with _LOCK:
        items = []
        for name, cb in _BREAKERS.items():
            state = cb.current_state
            elapsed = _elapsed_since_open(cb)
            # ★ 已可探测的 open 要标出来：pybreaker 自己不会提前翻 half-open，
            #   只回显 current_state 会出现"显示 open、实际下一次就放行"。
            #   显示和行为不一致会诱导人去手动干预一个正在自愈的系统。
            ready = (
                state == pybreaker.STATE_OPEN
                and elapsed is not None
                and elapsed >= float(lim["reset_timeout"])
            )
            items.append(
                {
                    "name": name,
                    "state": state,
                    "ready_to_probe": ready,
                    "seconds_until_half_open": (
                        max(0.0, float(lim["reset_timeout"]) - elapsed)
                        if elapsed is not None
                        else None
                    ),
                    "fail_counter": cb.fail_counter,
                    "fail_max": cb.fail_max,
                    "reset_timeout": cb.reset_timeout,
                }
            )
        blocked = _BLOCKED_CALLS
    backend = circuit_storage.backend_name()
    return {
        "enabled": enabled(),
        "limits": lim,
        "backend": backend,
        "scope": "shared" if shared else "process-local",
        # 配了 Redis 但没用上 = 降级运行，必须显式说出来，不假装是分布式的
        "degraded": backend == circuit_storage.BACKEND_REDIS and not shared,
        "redis_error": circuit_storage.last_redis_error(),
        "blocked_calls": blocked,
        "breakers": sorted(items, key=lambda x: x["name"]),
    }
