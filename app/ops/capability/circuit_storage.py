"""熔断状态存储后端（P1/Q3）。

为什么要有这个模块
------------------
熔断状态存在哪，决定了它**是不是跨实例共享的**：

- 存内存：多实例各一份，A 实例熔断了 B 实例照打——故障期被拉长 N 倍。
- 存 Redis：跨实例共享，但 Redis 自己也会挂。

pybreaker 自带 ``CircuitRedisStorage``，但它有两个我们要绕开的点：

1. **同步客户端**：它用的是同步 ``redis`` 客户端，在 asyncio 事件循环里会阻塞。
   （本阶段不真连，接口先留着；真接时要 ``asyncio.to_thread`` 包一层。）
2. **Redis 挂了会 fail-open**：它的 ``fallback_circuit_state`` 是"假设 closed"，
   也就是"Redis 不可用 = 一切正常"。我们要的是**回落到内存 + 显式标注 degraded**
   ——不能因为 Redis 挂了就假装熔断状态还是全局一致的。

三种后端
--------
===============  ==========================================  ==================
backend          触发条件                                    观测里的 scope
===============  ==========================================  ==================
memory           默认（未配置 Redis）                         process-local
redis            配了 URL 且 redis 包可用                     shared
mock-unavailable **本阶段默认**：显式"不可用"                 process-local(degraded)
===============  ==========================================  ==================

``mock-unavailable`` 不是"没接 Redis"，是**故意让 Redis 不可用**——
用来验证回落路径真的会走，而不是等线上 Redis 真挂了才发现回落没写。
"""

from __future__ import annotations

import os
from datetime import UTC, datetime
from typing import Any

from pybreaker import CircuitBreakerStorage, CircuitMemoryStorage

_ENV_BACKEND = "OPS_CAPABILITY_CB_BACKEND"
_ENV_REDIS_URL = "OPS_CAPABILITY_CB_REDIS_URL"

BACKEND_MEMORY = "memory"
BACKEND_REDIS = "redis"
BACKEND_MOCK_UNAVAILABLE = "mock-unavailable"
#: 本阶段默认：**故意**不可用，逼着回落路径被真的走到
DEFAULT_BACKEND = BACKEND_MOCK_UNAVAILABLE

#: 最近一次 Redis 失败原因（观测用；不假装没发生过）
_last_redis_error: str | None = None
_redis_client: Any | None = None
_redis_client_url: str | None = None


def backend_name() -> str:
    raw = os.environ.get(_ENV_BACKEND, "").strip().lower()
    if raw in (BACKEND_MEMORY, BACKEND_REDIS, BACKEND_MOCK_UNAVAILABLE):
        return raw
    return DEFAULT_BACKEND


def last_redis_error() -> str | None:
    return _last_redis_error


def _redis_url() -> str:
    return os.environ.get(_ENV_REDIS_URL, "").strip()


def _try_redis():
    """拿一个可用的 redis 客户端；拿不到返回 ``None`` 并记下原因。

    刻意**不抛**——拿不到就回落内存，这是设计，不是异常。
    """
    global _last_redis_error, _redis_client, _redis_client_url

    url = _redis_url()
    if not url:
        _last_redis_error = "未配置 " + _ENV_REDIS_URL
        return None
    try:
        import redis  # noqa: PLC0415 - 可选依赖，装了才有
    except ImportError:
        _last_redis_error = "未安装 redis（extra: circuit-redis）"
        return None

    if _redis_client is None or _redis_client_url != url:
        try:
            _redis_client = redis.Redis.from_url(url, decode_responses=False)
            _redis_client_url = url
        except Exception as exc:  # noqa: BLE001 - 连接串错了也要回落，不能崩
            _last_redis_error = f"连接串不可用: {type(exc).__name__}"
            _redis_client = None
            return None
    try:
        _redis_client.ping()
    except Exception as exc:  # noqa: BLE001
        _last_redis_error = f"ping 失败: {type(exc).__name__}: {exc}"
        _redis_client = None
        return None
    _last_redis_error = None
    return _redis_client


class FallbackStorage(CircuitBreakerStorage):
    """先 Redis，拿不到就回内存。

    **回落不是"降级到不可用"，是降级到"进程内仍然熔断"**——
    每个实例各自熔断，总比一个都不熔断好。观测里会显式标 degraded，
    不让人误以为还是全局一致的。
    """

    def __init__(self, name: str, *, backend: str | None = None) -> None:
        super().__init__(name)
        self._backend = backend or backend_name()
        self._memory = CircuitMemoryStorage("closed")
        self._redis_storage: Any | None = None
        self._use_redis = False
        if self._backend == BACKEND_REDIS:
            client = _try_redis()
            if client is not None:
                from pybreaker import CircuitRedisStorage  # noqa: PLC0415

                self._redis_storage = CircuitRedisStorage("closed", client, namespace=name)
                self._use_redis = True

    @property
    def effective_backend(self) -> str:
        """实际在用的后端（配置要 redis 但拿不到 → 这里会变成 memory）。"""
        return BACKEND_REDIS if self._use_redis else BACKEND_MEMORY

    @property
    def degraded(self) -> bool:
        """配了 redis 但没用上 = 降级运行中。"""
        return self._backend == BACKEND_REDIS and not self._use_redis

    # ---- CircuitBreakerStorage 接口：统一代理 ----
    @property
    def state(self) -> str:
        if self._use_redis and self._redis_storage is not None:
            try:
                return str(self._redis_storage.state)
            except Exception as exc:  # noqa: BLE001
                _note_redis_error(exc)
                self._use_redis = False
        return str(self._memory.state)

    @state.setter
    def state(self, value: str) -> None:
        if self._use_redis and self._redis_storage is not None:
            try:
                self._redis_storage.state = value
                return
            except Exception as exc:  # noqa: BLE001
                _note_redis_error(exc)
                self._use_redis = False
        self._memory.state = value

    def increment_counter(self) -> None:
        if self._use_redis and self._redis_storage is not None:
            try:
                self._redis_storage.increment_counter()
                return
            except Exception as exc:  # noqa: BLE001
                _note_redis_error(exc)
                self._use_redis = False
        self._memory.increment_counter()

    def reset_counter(self) -> None:
        if self._use_redis and self._redis_storage is not None:
            try:
                self._redis_storage.reset_counter()
                return
            except Exception as exc:  # noqa: BLE001
                _note_redis_error(exc)
                self._use_redis = False
        self._memory.reset_counter()

    def increment_success_counter(self) -> None:
        if self._use_redis and self._redis_storage is not None:
            try:
                self._redis_storage.increment_success_counter()
                return
            except Exception as exc:  # noqa: BLE001
                _note_redis_error(exc)
                self._use_redis = False
        self._memory.increment_success_counter()

    def reset_success_counter(self) -> None:
        if self._use_redis and self._redis_storage is not None:
            try:
                self._redis_storage.reset_success_counter()
                return
            except Exception as exc:  # noqa: BLE001
                _note_redis_error(exc)
                self._use_redis = False
        self._memory.reset_success_counter()

    @property
    def counter(self) -> int:
        if self._use_redis and self._redis_storage is not None:
            try:
                return int(self._redis_storage.counter)
            except Exception as exc:  # noqa: BLE001
                _note_redis_error(exc)
                self._use_redis = False
        return int(self._memory.counter)

    @property
    def success_counter(self) -> int:
        if self._use_redis and self._redis_storage is not None:
            try:
                return int(self._redis_storage.success_counter)
            except Exception as exc:  # noqa: BLE001
                _note_redis_error(exc)
                self._use_redis = False
        return int(self._memory.success_counter)

    @property
    def opened_at(self) -> datetime | None:
        if self._use_redis and self._redis_storage is not None:
            try:
                return self._redis_storage.opened_at
            except Exception as exc:  # noqa: BLE001
                _note_redis_error(exc)
                self._use_redis = False
        return self._memory.opened_at

    @opened_at.setter
    def opened_at(self, value: datetime) -> None:
        if self._use_redis and self._redis_storage is not None:
            try:
                self._redis_storage.opened_at = value
                return
            except Exception as exc:  # noqa: BLE001
                _note_redis_error(exc)
                self._use_redis = False
        self._memory.opened_at = value


def _note_redis_error(exc: BaseException) -> None:
    global _last_redis_error
    _last_redis_error = f"读写失败: {type(exc).__name__}: {exc}"


def is_shared() -> bool:
    """当前配置下熔断状态是否跨实例共享（观测口径用）。"""
    return backend_name() == BACKEND_REDIS and _try_redis() is not None


def reset_for_tests() -> None:
    """测试用：清掉缓存的客户端与错误记录。"""
    global _last_redis_error, _redis_client, _redis_client_url
    _last_redis_error = None
    _redis_client = None
    _redis_client_url = None


def now() -> datetime:
    return datetime.now(UTC)
