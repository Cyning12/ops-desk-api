"""HITL 申请存储。

纪律沿用能力层（``app/ops/capability/persistence.py``）：

- **只有异步接口**。编排层写入点是 async 节点；同步路径一律显式失败，
  不允许在事件循环里同步打 PG（P-13）。
- **不自动探测数据库可用性**。悄悄换存储实现会造成"申请时有时无"，
  而这种失效的表现是"人在等一个不存在的审批"，极难排查。
- **没配持久化时必须显式报警**，不能假装申请已经提交了。
"""

from __future__ import annotations

import json
import time
import uuid
from typing import Any, Protocol

STATUS_PENDING = "pending"
STATUS_APPROVED = "approved"
STATUS_REJECTED = "rejected"
STATUS_EXPIRED = "expired"
STATUSES = (STATUS_PENDING, STATUS_APPROVED, STATUS_REJECTED, STATUS_EXPIRED)


def new_request_id() -> str:
    return f"hitl_{uuid.uuid4().hex[:20]}"


class HitlStore(Protocol):
    """只有异步接口——同步路径请显式失败，不要假装成功。"""

    async def acreate(self, request: dict[str, Any]) -> dict[str, Any]: ...

    async def aget(self, request_id: str) -> dict[str, Any] | None: ...

    async def alist(
        self, *, status: str | None = None, limit: int = 50
    ) -> list[dict[str, Any]]: ...

    async def adecide(
        self,
        request_id: str,
        *,
        decision: str,
        by: str,
        note: str = "",
    ) -> dict[str, Any] | None: ...


class InMemoryHitlStore:
    """进程内存储（联调 / 单实例）。重启即丢——**不能用于生产**。"""

    _MAX = 512  # 与降级缓存同一条纪律：按 key 累积的进程内字典必须有上界

    def __init__(self) -> None:
        self._items: dict[str, dict[str, Any]] = {}

    async def acreate(self, request: dict[str, Any]) -> dict[str, Any]:
        if len(self._items) >= self._MAX and request["id"] not in self._items:
            # FIFO 淘汰最老的一条；与降级缓存一样，**淘汰必须可观测**
            oldest = min(self._items.values(), key=lambda r: r["created_at"])
            self._items.pop(oldest["id"], None)
            request = {**request, "_evicted_oldest": oldest["id"]}
        self._items[request["id"]] = dict(request)
        return dict(request)

    async def aget(self, request_id: str) -> dict[str, Any] | None:
        row = self._items.get(request_id)
        return dict(row) if row else None

    async def alist(
        self, *, status: str | None = None, limit: int = 50
    ) -> list[dict[str, Any]]:
        rows = [
            dict(r)
            for r in self._items.values()
            if status is None or r.get("status") == status
        ]
        rows.sort(key=lambda r: r["created_at"])
        return rows[:limit]

    async def adecide(
        self, request_id: str, *, decision: str, by: str, note: str = ""
    ) -> dict[str, Any] | None:
        row = self._items.get(request_id)
        if row is None:
            return None
        # ★ 只受理 pending。**必须与 DbHitlStore 的 `WHERE status='pending'` 一致**
        #   —— 真联调抓出来的：内存版无条件覆写，DB 版挡重复，两套语义不同。
        #   后果是"联调时用 memory 一切正常、上生产换成 db 行为变了"，
        #   而路由 404 / 409 的区分完全依赖这里返回 None。
        if row.get("status") != STATUS_PENDING:
            return None
        row["status"] = decision
        row["decision_by"] = by
        row["decision_note"] = note
        row["decided_at"] = time.time()
        return dict(row)


class NullHitlStore:
    """未配置持久化：**不落库且显式标记**。

    刻意不抛异常——抛了会让整条 run 挂掉，而这只是"审批没地方存"。
    但它必须把 ``persisted=False`` 交回去，让编排层能说出来：
    **申请没提交成功**。沉默地返回 True 才是这里最危险的做法。
    """

    async def acreate(self, request: dict[str, Any]) -> dict[str, Any]:
        return {**request, "persisted": False}

    async def aget(self, request_id: str) -> dict[str, Any] | None:
        return None

    async def alist(
        self, *, status: str | None = None, limit: int = 50
    ) -> list[dict[str, Any]]:
        return []

    async def adecide(
        self, request_id: str, *, decision: str, by: str, note: str = ""
    ) -> dict[str, Any] | None:
        return None


class DbHitlStore:
    """PostgreSQL 版：跨实例、跨重启可查。"""

    _INSERT = (
        "INSERT INTO ops_hitl_requests (id, run_id, thread_id, checkpoint_id, "
        "tenant_id, subtask_id, blocked_by, unlock_subtask_id, reason, detail, "
        "payload, status, created_at, updated_at) "
        "VALUES (:id, :run_id, :thread_id, :checkpoint_id, :tenant_id, "
        ":subtask_id, :blocked_by, :unlock_subtask_id, :reason, :detail, "
        "CAST(:payload AS jsonb), :status, now(), now()) "
        "ON CONFLICT (id) DO NOTHING"
    )
    _SELECT_ONE = (
        "SELECT id, run_id, thread_id, checkpoint_id, tenant_id, subtask_id, "
        "blocked_by, unlock_subtask_id, reason, detail, payload, status, "
        "decision_by, decision_note, decided_at, created_at "
        "FROM ops_hitl_requests WHERE id = :id"
    )
    _SELECT_LIST = (
        "SELECT id, run_id, thread_id, checkpoint_id, tenant_id, subtask_id, "
        "blocked_by, unlock_subtask_id, reason, detail, payload, status, "
        "decision_by, decision_note, decided_at, created_at "
        "FROM ops_hitl_requests "
        "WHERE (:status IS NULL OR status = :status) "
        "ORDER BY created_at ASC LIMIT :limit"
    )
    _DECIDE = (
        "UPDATE ops_hitl_requests SET status = :decision, decision_by = :by, "
        "decision_note = :note, decided_at = now(), updated_at = now() "
        "WHERE id = :id AND status = 'pending' RETURNING id"
    )

    def __init__(self, *, session_factory: Any = None) -> None:
        if session_factory is None:
            from app.db.session import AsyncSessionLocal

            session_factory = AsyncSessionLocal
        self._session_factory = session_factory

    async def acreate(self, request: dict[str, Any]) -> dict[str, Any]:
        from sqlalchemy import text

        params = {
            "id": request["id"],
            "run_id": str(request.get("run_id") or ""),
            "thread_id": str(request.get("thread_id") or ""),
            "checkpoint_id": request.get("checkpoint_id"),
            "tenant_id": str(request.get("tenant_id") or ""),
            "subtask_id": str(request.get("subtask_id") or ""),
            "blocked_by": str(request.get("blocked_by") or ""),
            "unlock_subtask_id": str(request.get("unlock_subtask_id") or ""),
            "reason": str(request.get("reason") or ""),
            "detail": str(request.get("detail") or ""),
            "payload": json.dumps(
                request.get("payload") or {}, ensure_ascii=False, default=str
            ),
            "status": STATUS_PENDING,
        }
        async with self._session_factory() as session, session.begin():
            await session.execute(text(self._INSERT), params)
        return {**request, "status": STATUS_PENDING, "persisted": True}

    async def aget(self, request_id: str) -> dict[str, Any] | None:
        from sqlalchemy import text

        async with self._session_factory() as session:
            rows = await session.execute(text(self._SELECT_ONE), {"id": request_id})
            row = rows.first()
        return _row_to_dict(row)

    async def alist(
        self, *, status: str | None = None, limit: int = 50
    ) -> list[dict[str, Any]]:
        from sqlalchemy import text

        async with self._session_factory() as session:
            rows = await session.execute(
                text(self._SELECT_LIST),
                {"status": status, "limit": max(1, min(int(limit), 200))},
            )
            return [_row_to_dict(r) for r in rows.fetchall()]

    async def adecide(
        self, request_id: str, *, decision: str, by: str, note: str = ""
    ) -> dict[str, Any] | None:
        from sqlalchemy import text

        async with self._session_factory() as session, session.begin():
            res = await session.execute(
                text(self._DECIDE),
                {"id": request_id, "decision": decision, "by": by, "note": note},
            )
            updated = res.first() is not None
        if not updated:
            return None
        return await self.aget(request_id)


def _row_to_dict(row: Any) -> dict[str, Any] | None:
    if row is None:
        return None
    return {
        "id": row[0],
        "run_id": row[1],
        "thread_id": row[2],
        "checkpoint_id": row[3],
        "tenant_id": row[4],
        "subtask_id": row[5],
        "blocked_by": row[6],
        "unlock_subtask_id": row[7],
        "reason": row[8],
        "detail": row[9],
        "payload": row[10] if isinstance(row[10], dict) else {},
        "status": row[11],
        "decision_by": row[12],
        "decision_note": row[13],
        "decided_at": row[14].isoformat() if row[14] is not None else None,
        "created_at": row[15].isoformat() if row[15] is not None else None,
        "persisted": True,
    }
