"""记忆状态机 service：write / revoke / sweep / recall（P0 候选来源仅显式调用）。

纪律：
- 写入先过闸（`should_write`）；**闸拒 = 不落库**，抛 `GateRejectedError`。
- 同 `(tenant_id, user_id, key)` 已有 active → **同一事务**内置旧行
  `superseded`、新行 `supersedes` 指旧 id；后写赢，旧值留表可审计。
- 失效走状态机（superseded / revoked / expired），**不物理删**。
- 召回只认 `status='active'` 且未过期——**查询路径自带 `expires_at` 过滤**，
  不依赖 sweep 存活（双保险）。
- session 纪律：传入 `session` 时调用方持有事务（本模块只 flush）；
  不传则模块自开 `AsyncSessionLocal` 并自行 commit（对齐 thread_store 先例）。
"""
from __future__ import annotations

import logging
from datetime import datetime

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import OpsMemoryFact, now_utc
from app.db.session import AsyncSessionLocal
from app.ops.memory.gate import FactCandidate, should_write

logger = logging.getLogger(__name__)

STATUS_ACTIVE = "active"
STATUS_SUPERSEDED = "superseded"
STATUS_REVOKED = "revoked"
STATUS_EXPIRED = "expired"


class GateRejectedError(ValueError):
    """写入闸拒绝：携带稳定原因码；**调用方不得静默吞掉**。"""

    def __init__(self, reason_code: str) -> None:
        super().__init__(reason_code)
        self.reason_code = reason_code


async def _write_in_session(session: AsyncSession, candidate: FactCandidate) -> OpsMemoryFact:
    """同一事务内：旧 active 置 superseded → 插入新行（supersedes=旧 id）。"""
    result = await session.execute(
        select(OpsMemoryFact)
        .where(
            OpsMemoryFact.tenant_id == candidate.tenant_id,
            OpsMemoryFact.user_id == candidate.user_id,
            OpsMemoryFact.key == candidate.key,
            OpsMemoryFact.status == STATUS_ACTIVE,
        )
        .order_by(OpsMemoryFact.updated_at.desc(), OpsMemoryFact.created_at.desc())
    )
    existing = list(result.scalars().all())
    fact = OpsMemoryFact(
        tenant_id=candidate.tenant_id,
        user_id=candidate.user_id,
        key=candidate.key,
        value=candidate.value,
        kind=candidate.kind,
        supersedes=str(existing[0].id) if existing else None,
    )
    session.add(fact)
    await session.flush()  # 先拿到新行 id，同事务内改旧行
    for old in existing:
        old.status = STATUS_SUPERSEDED
        old.updated_at = now_utc()
    await session.flush()
    return fact


async def write_fact(
    candidate: FactCandidate,
    *,
    source_run_id: str | None = None,
    source_turn: int | None = None,
    expires_at: datetime | None = None,
    session: AsyncSession | None = None,
) -> OpsMemoryFact:
    """过闸 → 落库；闸拒抛 `GateRejectedError`（不落库）；写故障向上抛（不静默）。"""
    decision = should_write(candidate)
    if not decision.allowed:
        logger.info(
            "memory fact rejected reason=%s key=%s tenant=%s",
            decision.reason_code,
            candidate.key,
            candidate.tenant_id,
        )
        raise GateRejectedError(decision.reason_code)
    candidate = FactCandidate(
        tenant_id=candidate.tenant_id.strip(),
        user_id=candidate.user_id.strip(),
        key=candidate.key.strip(),
        value=candidate.value,
        kind=candidate.kind,
    )
    if session is not None:
        fact = await _write_in_session(session, candidate)
        fact.source_run_id = source_run_id
        fact.source_turn = source_turn
        fact.expires_at = expires_at
        await session.flush()
        return fact
    async with AsyncSessionLocal() as own, own.begin():
        fact = await _write_in_session(own, candidate)
        fact.source_run_id = source_run_id
        fact.source_turn = source_turn
        fact.expires_at = expires_at
    # commit 由 begin() 退出时完成；expire_on_commit=False 保证属性可读
    return fact


async def revoke_by_source(
    source_run_id: str,
    *,
    session: AsyncSession | None = None,
) -> int:
    """按源头批量置 `revoked`（纠错唯一入口）；幂等；审计日志记影响行数。

    只动 `active` 行：superseded 行本就不可见，保留其状态可还原
    "它当时被谁取代"的审计链。已 revoked 的行不动 ⇒ 重复调用影响 0 行。
    """
    stmt = (
        update(OpsMemoryFact)
        .where(
            OpsMemoryFact.source_run_id == source_run_id,
            OpsMemoryFact.status == STATUS_ACTIVE,
        )
        .values(status=STATUS_REVOKED, updated_at=now_utc())
    )
    if session is not None:
        result = await session.execute(stmt)
        count = int(result.rowcount or 0)
    else:
        async with AsyncSessionLocal() as own, own.begin():
            result = await own.execute(stmt)
            count = int(result.rowcount or 0)
    # 审计日志：纠错动作本身必须可追查（含幂等 0 行）
    logger.info(
        "memory revoke_by_source source_run_id=%s affected=%d", source_run_id, count
    )
    return count


async def sweep_expired(
    now: datetime | None = None,
    *,
    session: AsyncSession | None = None,
) -> int:
    """定期任务：`expires_at < now` 的活跃行置 `expired`。

    召回正确性**不依赖**本函数（查询路径自带过期过滤）；sweep 只做显式盘点。
    """
    now = now or now_utc()
    stmt = (
        update(OpsMemoryFact)
        .where(
            OpsMemoryFact.status == STATUS_ACTIVE,
            OpsMemoryFact.expires_at.is_not(None),
            OpsMemoryFact.expires_at < now,
        )
        .values(status=STATUS_EXPIRED, updated_at=now_utc())
    )
    if session is not None:
        result = await session.execute(stmt)
        return int(result.rowcount or 0)
    async with AsyncSessionLocal() as own, own.begin():
        result = await own.execute(stmt)
        return int(result.rowcount or 0)


async def recall_active(
    tenant_id: str,
    user_id: str,
    *,
    limit: int = 8,
    now: datetime | None = None,
    session: AsyncSession | None = None,
) -> list[OpsMemoryFact]:
    """确定性召回（无向量）：`(tenant_id, user_id)` + active + 未过期，
    `updated_at desc` top-N。必带 tenant 谓词（跨 tenant = 空结果）。
    """
    now = now or now_utc()
    stmt = (
        select(OpsMemoryFact)
        .where(
            OpsMemoryFact.tenant_id == tenant_id,
            OpsMemoryFact.user_id == user_id,
            OpsMemoryFact.status == STATUS_ACTIVE,
            (OpsMemoryFact.expires_at.is_(None)) | (OpsMemoryFact.expires_at > now),
        )
        # 确定性排序：updated_at 并列时按 created_at / id 兜底，截断不随机
        .order_by(
            OpsMemoryFact.updated_at.desc(),
            OpsMemoryFact.created_at.desc(),
            OpsMemoryFact.id.desc(),
        )
        .limit(max(0, limit))
    )
    if session is not None:
        result = await session.execute(stmt)
        return list(result.scalars().all())
    async with AsyncSessionLocal() as own:
        result = await own.execute(stmt)
        return list(result.scalars().all())
