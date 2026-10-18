"""幂等防重存储（W5 · 收尾；W6 · 持久化）。

**目标不是"强幂等"（回放原始结果），而是"同一个幂等键不会在本层发出两次请求"。**
为什么不回放：回放要求把下游原始结果落库（扩大数据边界，可能含薪酬/合同），
而且它**只在你本来就不需要它的时候有用**——第一次结果未知时，恰恰没有结果可回放。
详见工作区 `docs/07-design/00_capability-registry-design_v1_zh.md`。

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
只有在**确知下游没有产生副作用**时才允许释放（见 `RELEASE_SAFE_ERROR_CODES`，在 adapter 里）：

| 情形 | 能否释放 | 理由 |
|---|---|---|
| 请求还没发出去（渲染/凭证/租户/头编码失败） | ✅ | 下游没见过这次请求 |
| 下游明确拒绝（`args_schema_invalid` / `policy_blocked` / `permission_denied`） | ✅ | 被拒 = 无副作用 |
| 超时 / 连接错误 / 未知业务码（`upstream_error`） | ❌ **不能** | 可能已生效，留给租约 |
| 成功 | ❌ | 直接 `complete` |

**失败方向一律 fail-closed**：宁可让该 key 在租约期内被拒，也不冒重复执行的风险。
代价由 `lease_seconds` 界定——这就是为什么**租约必须存在**：
没有它，"先插占位行"的做法会在进程崩溃后把该 key **永久**卡死，而且是静默的。

## 两个实现

| 实现 | 作用域 | 用于 |
|---|---|---|
| `InMemoryIdempotencyStore` | **进程内**（多实例各一份 → 跨实例防重无效） | 单实例 / 测试 |
| `DbIdempotencyStore` | **跨实例**（`(tenant_id, idempotency_key)` 唯一约束） | 生产 |

两者的键作用域一致：**租户内唯一**。跨租户互不影响。

DB 版把**租约判定交给数据库时钟**（`now()`）而不是应用进程时钟——
多实例部署下各机器时钟有偏差，用本地时钟判租约必然出错。
"""

from __future__ import annotations

import asyncio
import logging
import threading
import time
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
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
    """同步防重存储。``claim`` 必须**原子**（并发下只有一个执行者拿到 ``acquired=True``）。"""

    def claim(
        self, key: str, *, capability_id: str = "", tenant_id: str = ""
    ) -> IdempotencyClaim: ...

    def complete(self, key: str, *, receipt_id: str = "", tenant_id: str = "") -> None: ...

    def release(self, key: str, *, tenant_id: str = "") -> None: ...


@runtime_checkable
class AsyncIdempotencyStore(Protocol):
    """异步防重存储（DB 版实现它）。"""

    async def aclaim(
        self, key: str, *, capability_id: str = "", tenant_id: str = ""
    ) -> IdempotencyClaim: ...

    async def acomplete(self, key: str, *, receipt_id: str = "", tenant_id: str = "") -> None: ...

    async def arelease(self, key: str, *, tenant_id: str = "") -> None: ...


class NullIdempotencyStore:
    """不防重——**显式选择，且不静默**（每次写都告警）。

    默认用它，是因为"没有防重"这个事实必须被看见，而不是被假装做到了。
    实现了同步 + 异步两套，便于在任何路径上做默认值。
    """

    def claim(self, key: str, *, capability_id: str = "", tenant_id: str = "") -> IdempotencyClaim:
        logger.warning(
            "幂等防重未启用（NullIdempotencyStore）：capability=%s key=%s "
            "—— 重复提交可能产生第二张单据",
            capability_id,
            key,
        )
        return IdempotencyClaim(key=key, acquired=True)

    def complete(self, key: str, *, receipt_id: str = "", tenant_id: str = "") -> None:
        return

    def release(self, key: str, *, tenant_id: str = "") -> None:
        return

    async def aclaim(
        self, key: str, *, capability_id: str = "", tenant_id: str = ""
    ) -> IdempotencyClaim:
        return self.claim(key, capability_id=capability_id, tenant_id=tenant_id)

    async def acomplete(self, key: str, *, receipt_id: str = "", tenant_id: str = "") -> None:
        return

    async def arelease(self, key: str, *, tenant_id: str = "") -> None:
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

    ⚠️ **多实例下每个进程各一份** → 跨实例防重无效。生产用 `DbIdempotencyStore`。
    """

    def __init__(self, *, lease_seconds: float = DEFAULT_LEASE_SECONDS) -> None:
        self._rows: dict[tuple[str, str], _Row] = {}
        self._lease = lease_seconds
        self._lock = threading.Lock()

    def claim(self, key: str, *, capability_id: str = "", tenant_id: str = "") -> IdempotencyClaim:
        now = time.monotonic()
        with self._lock:
            row = self._rows.get((tenant_id, key))
            if row is None:
                self._rows[(tenant_id, key)] = _Row(
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
            if now <= row.lease_expires_at:
                return IdempotencyClaim(
                    key=key, acquired=False, in_flight=True, attempts=row.attempts
                )
            row.lease_expires_at = now + self._lease
            row.capability_id = capability_id or row.capability_id
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

    def complete(self, key: str, *, receipt_id: str = "", tenant_id: str = "") -> None:
        with self._lock:
            row = self._rows.get((tenant_id, key))
            if row is None:  # pragma: no cover - 防御
                return
            row.status = STATUS_DONE
            row.receipt_id = receipt_id or row.receipt_id
            row.lease_expires_at = float("inf")

    def release(self, key: str, *, tenant_id: str = "") -> None:
        """**只在确知下游无副作用时调用**（见模块 docstring 的表）。"""
        with self._lock:
            self._rows.pop((tenant_id, key), None)

    # 异步门面：包成 to_thread，避免阻塞事件循环
    async def aclaim(
        self, key: str, *, capability_id: str = "", tenant_id: str = ""
    ) -> IdempotencyClaim:
        return await asyncio.to_thread(
            self.claim, key, capability_id=capability_id, tenant_id=tenant_id
        )

    async def acomplete(self, key: str, *, receipt_id: str = "", tenant_id: str = "") -> None:
        await asyncio.to_thread(self.complete, key, receipt_id=receipt_id, tenant_id=tenant_id)

    async def arelease(self, key: str, *, tenant_id: str = "") -> None:
        await asyncio.to_thread(self.release, key, tenant_id=tenant_id)

    def snapshot(self) -> dict[str, dict[str, Any]]:
        with self._lock:
            return {
                f"{tenant}:{key}": {
                    "status": row.status,
                    "receipt_id": row.receipt_id,
                    "attempts": row.attempts,
                    "capability_id": row.capability_id,
                    "tenant_id": row.tenant_id,
                }
                for (tenant, key), row in self._rows.items()
            }

    def clear(self) -> None:
        with self._lock:
            self._rows.clear()

    def __len__(self) -> int:
        with self._lock:
            return len(self._rows)


# ---- SQL：租约判定交给数据库时钟（多实例下各机器时钟有偏差，本地时钟判必然出错）----

_INSERT_IF_ABSENT = """
INSERT INTO ops_capability_idempotency
    (id, tenant_id, idempotency_key, capability_id, status, lease_expires_at,
     attempts, created_at, updated_at)
VALUES
    (CAST(:id AS uuid), :tenant, :key, :cap, 'in_flight',
     now() + make_interval(secs => :ttl), 1, now(), now())
ON CONFLICT (tenant_id, idempotency_key) DO NOTHING
RETURNING id
"""

_TAKEOVER_IF_STALE = """
UPDATE ops_capability_idempotency
SET status = 'in_flight',
    lease_expires_at = now() + make_interval(secs => :ttl),
    attempts = attempts + 1,
    capability_id = COALESCE(NULLIF(:cap, ''), capability_id),
    updated_at = now()
WHERE tenant_id = :tenant
  AND idempotency_key = :key
  AND status = 'in_flight'
  AND (lease_expires_at IS NULL OR lease_expires_at < now())
RETURNING attempts
"""

_BUMP_AND_READ = """
UPDATE ops_capability_idempotency
SET attempts = attempts + 1, updated_at = now()
WHERE tenant_id = :tenant AND idempotency_key = :key
RETURNING status, receipt_id, attempts
"""

_COMPLETE = """
UPDATE ops_capability_idempotency
SET status = 'done',
    receipt_id = COALESCE(:receipt, receipt_id),
    lease_expires_at = NULL,
    updated_at = now()
WHERE tenant_id = :tenant AND idempotency_key = :key
"""

_RELEASE = """
DELETE FROM ops_capability_idempotency
WHERE tenant_id = :tenant AND idempotency_key = :key
"""


class DbIdempotencyStore:
    """PostgreSQL 版防重存储——**跨实例生效**（生产用）。

    三次尝试全在一个事务里，`claim` 是原子的：

    1. `INSERT ... ON CONFLICT DO NOTHING` 无记录则抢到执行权
    2. 若已有记录且 `in_flight` 且**租约已过期**（按 DB 时钟）→ 接管
    3. 否则读回状态：`done` → duplicate；`in_flight` → 拒绝（并累加 attempts）
    """

    def __init__(
        self,
        *,
        session_factory: Any = None,
        lease_seconds: float = DEFAULT_LEASE_SECONDS,
    ) -> None:
        if session_factory is None:
            # 延迟 import：能力内核默认零 DB 依赖，只有真用 DB 版才拉起来
            from app.db.session import AsyncSessionLocal

            session_factory = AsyncSessionLocal
        self._session_factory = session_factory
        self._lease = float(lease_seconds)

    async def aclaim(
        self, key: str, *, capability_id: str = "", tenant_id: str = ""
    ) -> IdempotencyClaim:
        params = {
            "id": str(uuid.uuid4()),
            "tenant": tenant_id,
            "key": key,
            "cap": capability_id,
            "ttl": self._lease,
        }
        async with self._session_factory() as session, session.begin():
            inserted = await session.execute(_text(_INSERT_IF_ABSENT), params)
            if inserted.first() is not None:
                return IdempotencyClaim(key=key, acquired=True, attempts=1)

            taken = await session.execute(_text(_TAKEOVER_IF_STALE), params)
            row = taken.first()
            if row is not None:
                logger.warning(
                    "幂等键租约已过期，本次接管：capability=%s key=%s attempts=%s "
                    "—— 上次执行可能异常中断，下游状态需人工确认",
                    capability_id,
                    key,
                    row[0],
                )
                return IdempotencyClaim(
                    key=key,
                    acquired=True,
                    attempts=int(row[0]),
                    took_over_stale_lease=True,
                )

            seen = await session.execute(_text(_BUMP_AND_READ), params)
            got = seen.first()
        if got is None:  # pragma: no cover - 竞态兜底：行被并发 release 掉了
            return await self.aclaim(key, capability_id=capability_id, tenant_id=tenant_id)
        status, receipt_id, attempts = got[0], got[1], int(got[2])
        if status == STATUS_DONE:
            return IdempotencyClaim(
                key=key,
                acquired=False,
                duplicate=True,
                receipt_id=receipt_id,
                attempts=attempts,
            )
        return IdempotencyClaim(key=key, acquired=False, in_flight=True, attempts=attempts)

    async def acomplete(self, key: str, *, receipt_id: str = "", tenant_id: str = "") -> None:
        async with self._session_factory() as session, session.begin():
            await session.execute(
                _text(_COMPLETE),
                {"tenant": tenant_id, "key": key, "receipt": receipt_id or None},
            )

    async def arelease(self, key: str, *, tenant_id: str = "") -> None:
        async with self._session_factory() as session, session.begin():
            await session.execute(_text(_RELEASE), {"tenant": tenant_id, "key": key})

    async def asnapshot(
        self, *, tenant_id: str = "", stuck_only: bool = False, limit: int = 200
    ) -> list[dict[str, Any]]:
        """运维/测试用：列出防重行。

        ``stuck_only=True`` 只返回**租约已过期的 `in_flight`**——那些是"发出去了但
        不知道结果"的写操作，需要人工去下游确认。**这一步只发现，不自动重试**：
        要不要重试取决于下游到底有没有生效，那是人或专门的查询能力才能判断的。
        """
        clauses = []
        params: dict[str, Any] = {"limit": max(1, min(int(limit), 1000))}
        if tenant_id:
            clauses.append("tenant_id = :tenant")
            params["tenant"] = tenant_id
        if stuck_only:
            clauses.append("status = 'in_flight'")
            clauses.append("lease_expires_at IS NOT NULL AND lease_expires_at < now()")
        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        stmt = (
            "SELECT idempotency_key, tenant_id, capability_id, status, attempts, "
            "receipt_id, lease_expires_at, updated_at "
            f"FROM ops_capability_idempotency {where} "
            "ORDER BY updated_at DESC LIMIT :limit"
        )
        async with self._session_factory() as session:
            rows = await session.execute(_text(stmt), params)
            return [
                {
                    "idempotency_key": r[0],
                    "tenant_id": r[1],
                    "capability_id": r[2],
                    "status": r[3],
                    "attempts": int(r[4]),
                    "receipt_id": r[5],
                    "lease_expires_at": r[6].isoformat() if r[6] else None,
                    "updated_at": r[7].isoformat() if r[7] else None,
                    # 卡住的行要给出对账线索，而不只是一个 id
                    "needs_reconcile": r[3] == STATUS_IN_FLIGHT,
                }
                for r in rows
            ]


def _text(sql: str) -> Any:
    from sqlalchemy import text

    return text(sql)


def lease_seconds_to_deadline(seconds: float) -> datetime:
    """仅用于文档/调试展示：把租约时长换成墙上时钟期限（判定不依赖它）。"""
    return datetime.now(UTC) + timedelta(seconds=seconds)


_store: IdempotencyStore | AsyncIdempotencyStore = NullIdempotencyStore()


def get_idempotency_store() -> Any:
    return _store


def set_idempotency_store(store: Any = None) -> None:
    """装配/测试用。``None`` → 复位为 ``NullIdempotencyStore``（显式不防重并告警）。"""
    global _store
    _store = store if store is not None else NullIdempotencyStore()


def reset_idempotency_store() -> None:
    set_idempotency_store(None)
