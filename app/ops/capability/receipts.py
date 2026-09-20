"""副作用回执（W2 · side_effect_receipts）。

**副作用以收据为真**：模型的自然语言总结不算，下游返回的载荷也不算——
只有落下来的回执算。所以写能力（``side_effect ∈ {write, irreversible}``）
无论成败都要留一张。

为什么失败也要留：**一次"失败"的写操作可能已经在下游生效了**
（超时、连接中断、下游返回业务失败但事务已提交）。不留回执，事后无法对账，
也就无法回答「到底写没写进去」——这正是写操作不自动重试的同一个原因。

落库接缝：``ReceiptSink`` 协议 + 进程内实现。DB sink（``side_effect_receipts``
表 + alembic 迁移）是下一波次的独立交付；此处先把**记录点与字段**钉死，
免得表建好了却发现该记的东西没记。
"""

from __future__ import annotations

import asyncio
import json
import logging
import threading
import uuid
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from typing import Any, Protocol, runtime_checkable

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class Receipt:
    """一次写操作的副作用凭据。"""

    receipt_id: str
    capability_id: str
    side_effect: str
    ok: bool
    created_at: str
    user_id: str = ""
    tenant_id: str = ""
    subtask_id: str = ""
    idempotency_key: str | None = None
    # 从下游响应按 receipt.capture 抓到的关键字段（如 ticketId / url）
    captured: dict[str, Any] = field(default_factory=dict)
    error: str | None = None
    # True 表示这次调用**在审批放行下**执行（见 policy.allow_write）
    write_confirmed: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@runtime_checkable
class ReceiptSink(Protocol):
    def record(self, receipt: Receipt) -> None: ...


@runtime_checkable
class AsyncReceiptSink(Protocol):
    """异步 sink（DB 版实现它）。"""

    async def arecord(self, receipt: Receipt) -> None: ...


class NullReceiptSink:
    """默认 sink：不落库，但**不静默**——写能力没地方落回执是配置问题，要看得见。"""

    def record(self, receipt: Receipt) -> None:  # pragma: no cover - 由单测断言
        logger.warning(
            "副作用回执未落库（未配置 ReceiptSink）: capability=%s ok=%s key=%s",
            receipt.capability_id,
            receipt.ok,
            receipt.idempotency_key,
        )

    async def arecord(self, receipt: Receipt) -> None:
        self.record(receipt)


class InMemoryReceiptSink:
    """进程内 sink（测试 / 单实例）；线程安全。"""

    def __init__(self, *, limit: int = 1000) -> None:
        self._items: list[Receipt] = []
        self._limit = limit
        self._lock = threading.Lock()

    def record(self, receipt: Receipt) -> None:
        with self._lock:
            self._items.append(receipt)
            if len(self._items) > self._limit:
                del self._items[: len(self._items) - self._limit]

    def all(self) -> list[Receipt]:
        with self._lock:
            return list(self._items)

    def by_idempotency_key(self, key: str) -> list[Receipt]:
        with self._lock:
            return [r for r in self._items if r.idempotency_key == key]

    def clear(self) -> None:
        with self._lock:
            self._items.clear()

    def __len__(self) -> int:
        with self._lock:
            return len(self._items)


_sink: ReceiptSink = NullReceiptSink()


def get_receipt_sink() -> ReceiptSink:
    return _sink


def set_receipt_sink(sink: ReceiptSink | None) -> None:
    """替换 sink（启动装配 / 测试）。``None`` → 复位为 ``NullReceiptSink``。"""
    global _sink
    _sink = sink if sink is not None else NullReceiptSink()


def reset_receipt_sink() -> None:
    set_receipt_sink(None)


def new_receipt_id() -> str:
    return uuid.uuid4().hex[:16]


def build_receipt(
    *,
    capability_id: str,
    side_effect: str,
    ok: bool,
    ctx: dict[str, Any] | None,
    idempotency_key: str | None = None,
    captured: dict[str, Any] | None = None,
    error: str | None = None,
    write_confirmed: bool = False,
) -> Receipt:
    c = ctx or {}
    return Receipt(
        receipt_id=new_receipt_id(),
        capability_id=capability_id,
        side_effect=side_effect,
        ok=ok,
        created_at=datetime.now(UTC).isoformat(),
        user_id=str(c.get("user_id") or c.get("_host_user_id") or ""),
        tenant_id=str(c.get("tenant_id") or c.get("_host_tenant") or ""),
        subtask_id=str(c.get("subtask_id") or ""),
        idempotency_key=idempotency_key,
        captured=dict(captured or {}),
        error=error,
        write_confirmed=write_confirmed,
    )


def record_receipt(receipt: Receipt) -> None:
    """落回执；sink 抛异常**不得**影响调用方（回执失败不该让业务失败）。"""
    try:
        get_receipt_sink().record(receipt)
    except Exception:  # pragma: no cover - 防御
        logger.exception("副作用回执落库失败: %s", receipt.capability_id)


async def arecord_receipt(receipt: Receipt) -> None:
    """异步落回执（异步路径用）。

    sink 有 ``arecord`` 就 await 它（DB 版）；否则把同步实现丢线程——
    **不要直接在事件循环里调同步 sink**，那正是我们刚修掉的阻塞问题。
    """
    sink = get_receipt_sink()
    try:
        arecord = getattr(sink, "arecord", None)
        if callable(arecord):
            await arecord(receipt)
            return
        await asyncio.to_thread(sink.record, receipt)
    except Exception:  # pragma: no cover - 防御
        logger.exception("副作用回执落库失败: %s", receipt.capability_id)


# ---- DB sink（跨实例可见）----

_INSERT = """
INSERT INTO ops_capability_receipts
    (id, receipt_id, capability_id, side_effect, ok, write_confirmed,
     user_id, tenant_id, subtask_id, idempotency_key, captured, error, created_at)
VALUES
    (CAST(:id AS uuid), :receipt_id, :capability_id, :side_effect, :ok,
     :write_confirmed, :user_id, :tenant_id, :subtask_id, :key,
     CAST(:captured AS jsonb), :error, now())
"""


class DbReceiptSink:
    """PostgreSQL 版回执 sink——副作用凭据要**跨实例、跨重启**可查。"""

    def __init__(self, *, session_factory: Any = None) -> None:
        if session_factory is None:
            from app.db.session import AsyncSessionLocal

            session_factory = AsyncSessionLocal
        self._session_factory = session_factory

    async def arecord(self, receipt: Receipt) -> None:
        from sqlalchemy import text

        params = {
            "id": str(uuid.uuid4()),
            "receipt_id": receipt.receipt_id,
            "capability_id": receipt.capability_id,
            "side_effect": receipt.side_effect,
            "ok": receipt.ok,
            "write_confirmed": receipt.write_confirmed,
            "user_id": receipt.user_id,
            "tenant_id": receipt.tenant_id,
            "subtask_id": receipt.subtask_id,
            "key": receipt.idempotency_key,
            "captured": json.dumps(receipt.captured, ensure_ascii=False, default=str),
            "error": receipt.error,
        }
        async with self._session_factory() as session:
            async with session.begin():
                await session.execute(text(_INSERT), params)

    def record(self, receipt: Receipt) -> None:
        raise RuntimeError(
            "DbReceiptSink 只提供异步落库：请走异步路径（arecord），"
            "不要在事件循环里同步调用——那会阻塞事件循环"
        )

    async def arecent(
        self,
        *,
        tenant_id: str = "",
        capability_id: str = "",
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        """最近的回执（观测端点 / 对账用）。**只读，不改任何状态。**"""
        from sqlalchemy import text

        clauses = []
        params: dict[str, Any] = {"limit": max(1, min(int(limit), 500))}
        if tenant_id:
            clauses.append("tenant_id = :tenant")
            params["tenant"] = tenant_id
        if capability_id:
            clauses.append("capability_id = :cap")
            params["cap"] = capability_id
        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        stmt = (
            "SELECT receipt_id, capability_id, side_effect, ok, write_confirmed, "
            "user_id, tenant_id, subtask_id, idempotency_key, captured, error, created_at "
            f"FROM ops_capability_receipts {where} ORDER BY created_at DESC LIMIT :limit"
        )
        async with self._session_factory() as session:
            rows = await session.execute(text(stmt), params)
            return [
                {
                    "receipt_id": r[0],
                    "capability_id": r[1],
                    "side_effect": r[2],
                    "ok": r[3],
                    "write_confirmed": r[4],
                    "user_id": r[5],
                    "tenant_id": r[6],
                    "subtask_id": r[7],
                    "idempotency_key": r[8],
                    "captured": r[9],
                    "error": r[10],
                    "created_at": r[11].isoformat() if r[11] else None,
                }
                for r in rows
            ]
