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


class NullReceiptSink:
    """默认 sink：不落库，但**不静默**——写能力没地方落回执是配置问题，要看得见。"""

    def record(self, receipt: Receipt) -> None:  # pragma: no cover - 由单测断言
        logger.warning(
            "副作用回执未落库（未配置 ReceiptSink）: capability=%s ok=%s key=%s",
            receipt.capability_id,
            receipt.ok,
            receipt.idempotency_key,
        )


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
