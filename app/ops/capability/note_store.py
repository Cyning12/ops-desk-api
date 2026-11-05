"""受控写便签落笔面（stage-w-write-expand · Q1=S1 仓内落笔型写）。

``ops.write.run_note`` 的 DB IO 集中在本模块（``defaults.py::ops_write_run_note``
经延迟 import 调用，保持 defaults 罐头函数面纯净）。延迟 import ``app.db``
对齐 ``idempotency.py`` / ``receipts.py`` 先例（能力内核顶层零 DB 依赖；
import-linter 白名单同例登记）。

防重语义（FP-4 重放不双写）：
``INSERT ... ON CONFLICT (tenant_id, idempotency_key) DO NOTHING RETURNING id``——
同键重放时不双写；``RETURNING`` 为空如实取回已有行 id（duplicate 形状由
调用方组装）。
"""

from __future__ import annotations

from typing import Any

_INSERT_NOTE = """
INSERT INTO ops_capability_notes
    (id, capability_id, tenant_id, run_id, subtask_id, approval_id,
     note, created_by, idempotency_key, created_at)
VALUES
    (CAST(:id AS uuid), :capability_id, :tenant_id, :run_id, :subtask_id, :approval_id,
     :note, :created_by, :key, now())
ON CONFLICT (tenant_id, idempotency_key) DO NOTHING
RETURNING CAST(id AS text)
"""

_SELECT_NOTE_ID = """
SELECT CAST(id AS text) FROM ops_capability_notes
WHERE tenant_id = :tenant AND idempotency_key = :key
"""


async def insert_note(params: dict[str, Any]) -> tuple[str | None, str | None]:
    """落笔便签；返回 ``(note_id, duplicate_of)``——``note_id is None`` 表示命中
    唯一约束（同 (tenant, key) 已有行），此时 ``duplicate_of`` 为已有行 id。"""
    from sqlalchemy import text

    from app.db.session import AsyncSessionLocal

    async with AsyncSessionLocal() as session, session.begin():
        inserted = await session.execute(text(_INSERT_NOTE), params)
        note_id = inserted.scalar()
        if note_id is not None:
            return str(note_id), None
        row = await session.execute(
            text(_SELECT_NOTE_ID),
            {"tenant": params["tenant_id"], "key": params["key"]},
        )
        return None, str(row.scalar() or "")
