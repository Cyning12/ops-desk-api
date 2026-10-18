"""LLM provider 级熔断（llm-layer-hardening D2 · 复用 capability circuit.py 模式）。

为什么要有
----------
provider 连续故障时，**每一次调用都要再付一次完整 read 超时（180s 上限）**才知道
它还挂着——慢、且放大挣扎中下游的负载。熔断回答的是「这个 provider 现在还打得
通吗」，与重试（瞬时故障缓冲）正交。

三态（与 capability circuit 同源；中文直觉容易读反）
--------------------------------------------------
- **closed** = 正常放行
- **open** = 熔断中，**零出网**立即失败（翻译为 `circuit_open` 错误）
- **half-open** = 恢复探测中（瞬时态，探测结束立刻落回 open 或 closed）

pybreaker 三个实测结论（自 capability/circuit.py 移植，别踩）
------------------------------------------------------------
1. `call_async` 是 **Tornado-only**；asyncio 用 `with breaker.calling():`。
2. 只在**抛异常**时计失败 → 用 `exclude` 把「不算下游故障」的异常挑出去
   （`_is_business_error`：仅 `LlmProviderError(retryable=True)` 计环境失败；
   4xx 业务错 / 缺 key / 流取消 GeneratorExit / CancelledError 一律不计——
   **用户填错 5 次参数不能把 provider 停 60s**）。
3. `throw_new_error_on_trip=False`：跳闸那次保留原始根因，不换成
   `CircuitBreakerError`。

粒度：**provider 级**（siliconflow / bailian 各一个）——不按模型熔：同 provider
换模型是 fallback 链自己的职责，双状态机会互相打架。多副本共享存储（Redis）本波
留位不实现（进程内 storage，与 capability 默认一致）。
"""

from __future__ import annotations

import asyncio
import logging
import os
import threading
from datetime import UTC, datetime, timedelta
from typing import Any

import pybreaker

from app.llm.schema import LlmProviderError

logger = logging.getLogger(__name__)

_ENV_ENABLED = "OPS_LLM_CB_ENABLED"
_ENV_FAIL_MAX = "OPS_LLM_CB_FAIL_MAX"
_ENV_RESET_TIMEOUT = "OPS_LLM_CB_RESET_TIMEOUT"

DEFAULT_FAIL_MAX = 5
DEFAULT_RESET_TIMEOUT = 60

_LOCK = threading.Lock()
_BREAKERS: dict[str, pybreaker.CircuitBreaker] = {}
_BLOCKED_CALLS = 0

_TRUTHY = ("1", "true", "yes", "on")
_FALSY = ("0", "false", "no", "off")


def enabled() -> bool:
    """`OPS_LLM_CB_ENABLED`：默认开；非法值回退开 + warning。"""
    raw = (os.getenv(_ENV_ENABLED) or "").strip().lower()
    if not raw:
        return True
    if raw in _TRUTHY:
        return True
    if raw in _FALSY:
        return False
    logger.warning("invalid %s=%r; fallback to true", _ENV_ENABLED, raw)
    return True


def _int_env(name: str, default: int) -> int:
    raw = (os.getenv(name) or "").strip()
    if not raw:
        return default
    try:
        n = int(raw)
    except ValueError:
        logger.warning("invalid %s=%r; fallback to %s", name, raw, default)
        return default
    if n <= 0:
        logger.warning("invalid %s=%r (<= 0); fallback to %s", name, raw, default)
        return default
    return n


def fail_max() -> int:
    return _int_env(_ENV_FAIL_MAX, DEFAULT_FAIL_MAX)


def reset_timeout() -> int:
    return _int_env(_ENV_RESET_TIMEOUT, DEFAULT_RESET_TIMEOUT)


def _is_business_error(exc: BaseException) -> bool:
    """这次异常**不算** provider 故障 → 不计入熔断。

    判据（对齐 capability errors.is_environmental_failure 的结构化思想，
    **不解析错误文案**）：只有 `LlmProviderError` 且 `retryable=True`
    （408/429/5xx/传输错/SSE 解析错）才算环境类失败。其余——4xx 业务错、
    缺 key `ValueError`、流被取消（GeneratorExit/CancelledError）——一律不算；
    宁可少熔，不可误熔。
    """
    if isinstance(exc, (GeneratorExit, asyncio.CancelledError, StopAsyncIteration)):
        return True
    return not (isinstance(exc, LlmProviderError) and exc.retryable)


def breaker_for(provider: str) -> pybreaker.CircuitBreaker:
    """取（或建）该 provider 的 breaker。进程内单例，跨调用存活。"""
    name = f"llm:{provider}"
    with _LOCK:
        cb = _BREAKERS.get(provider)
        if cb is None:
            cb = pybreaker.CircuitBreaker(
                fail_max=fail_max(),
                reset_timeout=reset_timeout(),
                # ★ 业务类异常不计入熔断（callable 形式）
                exclude=[_is_business_error],
                name=name,
                # ★ 跳闸那次保留原始错误，别把根因换成 CircuitBreakerError
                throw_new_error_on_trip=False,
            )
            _BREAKERS[provider] = cb
        # 阈值可被 env 改：每次取用时同步，免得「改个配置要重启」
        cb.fail_max = fail_max()
        cb.reset_timeout = reset_timeout()
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


def circuit_open_error(provider: str, cb: pybreaker.CircuitBreaker) -> LlmProviderError:
    """open 拦截翻译：`circuit_open` 错误（`retryable=False`），不得返回半成功 answer。

    `throw_new_error_on_trip=False` 保证跳闸那次抛的是原始 `LlmProviderError`；
    本函数只用于「open 状态下根本没出门」的调用。
    """
    global _BLOCKED_CALLS
    with _LOCK:
        _BLOCKED_CALLS += 1
    elapsed = _elapsed_since_open(cb)
    remaining = max(0.0, float(reset_timeout()) - elapsed) if elapsed is not None else 0.0
    return LlmProviderError(
        f"circuit_open: {cb.name} state={cb.current_state} 剩余 {remaining:.0f}s",
        retryable=False,
    )


def is_circuit_open_error(exc: BaseException) -> bool:
    """是否为 open 拦截产生的 CircuitBreakerError（由调用方翻译成 circuit_open）。"""
    return isinstance(exc, pybreaker.CircuitBreakerError)


def reset(*, provider: str | None = None) -> None:
    """清空 breaker（`provider=None` 清全部）。

    测试**必须**在每个用例前调一次：这是进程内全局状态，与 capability 配额同源
    （conftest autouse fixture 已挂）。
    """
    global _BLOCKED_CALLS
    with _LOCK:
        if provider is None:
            for cb in _BREAKERS.values():
                cb.close()
            _BREAKERS.clear()
            _BLOCKED_CALLS = 0
        else:
            cb = _BREAKERS.pop(provider, None)
            if cb is not None:
                cb.close()


def trip(provider: str) -> None:
    """测试/运维用：手动把某个 provider 熔断（模拟连续失败）。"""
    breaker_for(provider).open()


def advance(provider: str, seconds: float) -> None:
    """测试用：把 opened_at 往前拨，**不 sleep**（否则测 60s 恢复要真等）。"""
    cb = _BREAKERS.get(provider)
    if cb is None:
        return
    cb._state_storage.opened_at = datetime.now(UTC) - timedelta(seconds=seconds)  # noqa: SLF001


def snapshot() -> dict[str, Any]:
    """/runtime 类观测面用：state / fail_counter / seconds_until_half_open / blocked_calls。"""
    with _LOCK:
        items = []
        for provider, cb in _BREAKERS.items():
            state = cb.current_state
            elapsed = _elapsed_since_open(cb)
            # ★ 已可探测的 open 要标出来：pybreaker 自己不会提前翻 half-open，
            #   只回显 current_state 会出现「显示 open、实际下一次就放行」。
            ready = (
                state == pybreaker.STATE_OPEN
                and elapsed is not None
                and elapsed >= float(reset_timeout())
            )
            items.append(
                {
                    "provider": provider,
                    "name": cb.name,
                    "state": state,
                    "ready_to_probe": ready,
                    "seconds_until_half_open": (
                        max(0.0, float(reset_timeout()) - elapsed) if elapsed is not None else None
                    ),
                    "fail_counter": cb.fail_counter,
                    "fail_max": cb.fail_max,
                    "reset_timeout": cb.reset_timeout,
                }
            )
        blocked = _BLOCKED_CALLS
    return {
        "enabled": enabled(),
        "fail_max": fail_max(),
        "reset_timeout": reset_timeout(),
        # 多副本共享存储（Redis）留位不实现：本波进程内
        "scope": "process-local",
        "blocked_calls": blocked,
        "breakers": sorted(items, key=lambda x: x["name"]),
    }
