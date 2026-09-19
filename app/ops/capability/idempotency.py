"""幂等防重存储（W5 · 收尾）。

**目标不是"强幂等"（回放原始结果），而是"同一个幂等键不会在本层发出两次请求"。**
为什么不回放：回放要求把下游原始结果落库（扩大数据边界，可能含薪酬/合同），
而且它**只在你本来就不需要它的时候有用**——第一次结果未知时，恰恰没有结果可回放。
详见工作区《能力注册表落地设计》。

## 状态机

```
        claim(key)
   ┌────────┴────────┐
   │                 │
 无记录          已有记录
   │                 │
建 in_flight      ┌──┴──────────┐
租约 = now+TTL    │             │
   │           status=done   status=in_flight
acquired=True   duplicate    ┌──┴─────────┐
                 不再执行     租约未过期    租约已过期
                             in_flight    接管（重新计时）
                             attempts+1   acquired=True, attempts+1
```

## release 的语义（**这条最容易做错**）

「失败就释放」是错的：**超时不代表没成功**，释放会让重试建出第二张单。

只有在**确知下游没有产生副作用**时才允许释放：

| 情形 | 能否释放 | 理由 |
|---|---|---|
| 请求还没发出去（渲染/凭证/租户/头编码失败） | ✅ 能 | 下游没见过这次请求 |
| 下游明确拒绝（`args_schema_invalid` / `policy_blocked` / `permission_denied`） | ✅ 能 | 被拒 = 无副作用 |
| 超时 / 连接错误 / 未知业务码（`upstream_error`） | ❌ **不能** | 可能已生效，留给租约过期 |
| 成功 | ❌ 不能 | 直接 `complete` |

**失败方向一律 fail-closed**：宁可让该 key 在租约期内被拒，也不冒重复执行的风险。
代价由 `lease_seconds` 界定——这就是为什么**租约必须存在**：
没有它，"先插占位行"的做法会在进程崩溃后把该 key **永久**卡死，而且是静默的。

## 持久化

`IdempotencyStore` 是同步协议，本模块只提供进程内实现。
DB 版（`ops_capability_idempotency` 表，结构已随迁移落盘）是下一步——
顺序上必须**先把异步路径钉死**（`GenericHttpAdapter.ainvoke` 不阻塞事件循环），
否则 DB 版接上去是在错误的地基上。
"""

from __future__ import annotations

import logging
import threading
import time
from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable

logger = logging.getLogger(__name__)

#: 默认租约：超过这个时长仍未 complete 的 in_flight 视为失效，允许接管。
#: 取值要 **> 该能力的 timeout_ms**，否则正常执行中的请求会被误判为卡死。
DEFAULT_LEASE_SECONDS = 120.0

STATUS_IN_FLIGHT = "in_flight"
STATUS_DONE = "done"


@dataclass(frozen=True)
class IdempotencyClaim:
    """一次 claim 的结果。"""

    key: str
    #: 本次是否拿到执行权（只有它为 True 时才该真的发请求）
    acquired: bool
    #: 该键此前**已完成**过 → 不应再执行
    duplicate: bool = False
    #: 该键正在被别的执行者处理（租约未过期）
    in_flight: bool = False
    #: 已完成时的回执 id（供调用方对账/查询）
    receipt_id: str | None = None
    #: 该键的累计尝试次数（含本次）
    attempts: int = 0
    #: 租约已过期、由本次接管（说明上次可能异常中断）
    took_over_stale_lease: bool = False

    @property
    def should_execute(self) -> bool:
        return self.acquired


@runtime_checkable
class IdempotencyStore(Protocol):
    """防重存储协议（同步）。

    ``claim`` 必须是**原子**的（并发下只有一个执行者拿到 ``acquired=True``）。
    """

    def claim(
        self, key: str, *, capability_id: str = "", tenant_id: str = ""
    ) -> IdempotencyClaim: ...

    def complete(self, key: str, *, receipt_id: str = "") -> None: ...

    def release(self, key: str) -> None: ...


class NullIdempotencyStore:
    """不防重——**显式选择，且不静默**（每次写都告警）。

    默认用它，是因为"没有防重"这个事实必须被看见，而不是被假装做到了。
    """

    def claim(
        self, key: str, *, capability_id: str = "", tenant_id: str = ""
    ) -> IdempotencyClaim:
        logger.warning(
            "幂等防重未启用（NullIdempotencyStore）：capability=%s key=%s "
            "—— 重复提交可能产生第二张单据",
            capability_id,
            key,
        )
        return IdempotencyClaim(key=key, acquired=True)

    def complete(self, key: str, *, receipt_id: str = "") -> None:
        return

    def release(self, key: str) -> None:
        return


@dataclass
class _Row:
    status: str
    receipt_id: str | None
    lease_expires_at: float
    attempts: int
    capability_id: str = ""
    tenant_id: str = ""
    created_at: float = field(default_factory=time.monotonic)


class InMemoryIdempotencyStore:
    """进程内防重 + 租约（单实例 / 测试）。

    ⚠️ **多实例下每个进程各一份**——与进程内注册表同一个已知边界。
    跨实例防重需要 DB 版（表结构已落盘）。
    """

    def __init__(self, *, lease_seconds: float = DEFAULT_LEASE_SECONDS) -> None:
        self._rows: dict[str, _Row] = {}
        self._lease = lease_seconds
        self._lock = threading.Lock()

    def claim(
        self, key: str, *, capability_id: str = "", tenant_id: str = ""
    ) -> IdempotencyClaim:
        now = time.monotonic()
        with self._lock:
            row = self._rows.get(key)
            if row is None:
                self._rows[key] = _Row(
                    status=STATUS_IN_FLIGHT,
                    receipt_id=None,
                    lease_expires_at=now + self._lease,
                    attempts=1,
                    capability_id=capability_id,
                    tenant_id=tenant_id,
                )
                return IdempotencyClaim(key=key, acquired=True, attempts=1)

            row.attempts += 1
            if row.status == STATUS_DONE:
                return IdempotencyClaim(
                    key=key,
                    acquired=False,
                    duplicate=True,
                    receipt_id=row.receipt_id,
                    attempts=row.attempts,
                )

            # in_flight：租约过期才允许接管
            if now <= row.lease_expires_at:
                return IdempotencyClaim(
                    key=key, acquired=False, in_flight=True, attempts=row.attempts
                )
            row.lease_expires_at = now + self._lease
            row.capability_id = capability_id or row.capability_id
            row.tenant_id = tenant_id or row.tenant_id
            logger.warning(
                "幂等键租约已过期，本次接管：capability=%s key=%s attempts=%s "
                "—— 上次执行可能异常中断，下游状态需人工确认",
                capability_id,
                key,
                row.attempts,
            )
            return IdempotencyClaim(
                key=key, acquired=True, attempts=row.attempts, took_over_stale_lease=True
            )

    def complete(self, key: str, *, receipt_id: str = "") -> None:
        with self._lock:
            row = self._rows.get(key)
            if row is None:  # pragma: no cover - 防御
                return
            row.status = STATUS_DONE
            row.receipt_id = receipt_id or row.receipt_id
            row.lease_expires_at = float("inf")

    def release(self, key: str) -> None:
        """**只在确知下游无副作用时调用**（见模块 docstring 的表）。"""
        with self._lock:
            self._rows.pop(key, None)

    def snapshot(self) -> dict[str, dict[str, Any]]:
        with self._lock:
            return {
                key: {
                    "status": row.status,
                    "receipt_id": row.receipt_id,
                    "attempts": row.attempts,
                    "capability_id": row.capability_id,
                    "tenant_id": row.tenant_id,
                }
                for key, row in self._rows.items()
            }

    def clear(self) -> None:
        with self._lock:
            self._rows.clear()

    def __len__(self) -> int:
        with self._lock:
            return len(self._rows)


_store: IdempotencyStore = NullIdempotencyStore()


def get_idempotency_store() -> IdempotencyStore:
    return _store


def set_idempotency_store(store: IdempotencyStore | None) -> None:
    """装配/测试用。``None`` → 复位为 ``NullIdempotencyStore``（显式不防重并告警）。"""
    global _store
    _store = store if store is not None else NullIdempotencyStore()


def reset_idempotency_store() -> None:
    set_idempotency_store(None)
