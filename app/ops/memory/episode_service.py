"""情景记忆写入面（host-v1-episodic-memory-feedback D2 · U4 零互写）。

纪律：
- **零互写（U4 铁律）**：本模块与事实记忆写面（memory/gate.py ·
  memory/service.py）**物理分立、互不 import**（import 守护断言钉死）；
  episode 只写 ops_memory_episodes，fact 只写事实记忆表（物理分表）
  （双向表计数对拍断言钉死）。
- 写入先过闸（episode_gate.should_write_episode）；**闸拒 = 不落库**，
  抛 EpisodeGateRejectedError。
- 写开关 MEMORY_EPISODES_WRITE_ENABLED 默认 false（非法回退 false）：
  off = 不读不写直接返回 None（双开关独立灰度，召回开关在 continuity）。
- off 态 drop 安全（承 session_summaries 先例）：表不存在时读/写/revoke
  均降级（log + 空结果），不炸调用方。
- 审计记动作不记内容：写/撤销只记 id/run_id/计数，不记 plan 摘要正文。
- session 纪律：传入 session 时调用方持有事务（本模块只 flush）；
  不传则模块自开 AsyncSessionLocal 并自行 commit（承 service.py 先例）。
"""

from __future__ import annotations

import logging
import os

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import OpsMemoryEpisode
from app.db.session import AsyncSessionLocal
from app.ops.memory.episode_gate import (
    EpisodeCandidate,
    should_write_episode,
)

logger = logging.getLogger(__name__)

STATUS_ACTIVE = "active"
STATUS_REVOKED = "revoked"
OUTCOME_SUCCESS = "success"

_TRUTHY = ("1", "true", "yes", "on")
_FALSY = ("0", "false", "no", "off")


class EpisodeGateRejectedError(ValueError):
    """情景记忆写入闸拒绝：携带稳定原因码；**调用方不得静默吞掉**。"""

    def __init__(self, reason_code: str) -> None:
        super().__init__(reason_code)
        self.reason_code = reason_code


def memory_episodes_write_enabled() -> bool:
    """MEMORY_EPISODES_WRITE_ENABLED：默认 false；非法值回退 false + warning。"""
    raw = (os.getenv("MEMORY_EPISODES_WRITE_ENABLED") or "").strip().lower()
    if not raw:
        return False
    if raw in _TRUTHY:
        return True
    if raw in _FALSY:
        return False
    logger.warning("invalid MEMORY_EPISODES_WRITE_ENABLED=%r; fallback to false", raw)
    return False


def _is_missing_table(exc: BaseException) -> bool:
    """表不存在（migration 未跑 / 已 downgrade）→ off 态降级而非炸。"""
    text = f"{type(exc).__name__}: {exc}"
    return "ops_memory_episodes" in text and ("does not exist" in text or "UndefinedTable" in text)


async def write_episode(
    candidate: EpisodeCandidate,
    *,
    session: AsyncSession | None = None,
) -> OpsMemoryEpisode | None:
    """过闸 → 落库；闸拒抛 EpisodeGateRejectedError（不落库）。

    开关 off（默认）→ 不读不写返回 None；表不存在 → 降级返回 None
    （log warning，不炸 run 终态异步面）；其它写故障向上抛（不静默）。
    """
    if not memory_episodes_write_enabled():
        logger.info(
            "memory episode write skipped (MEMORY_EPISODES_WRITE_ENABLED off) run_id=%s",
            candidate.run_id,
        )
        return None
    decision = should_write_episode(candidate)
    if not decision.allowed:
        logger.info(
            "memory episode rejected reason=%s run_id=%s tenant=%s",
            decision.reason_code,
            candidate.run_id,
            candidate.tenant_id,
        )
        raise EpisodeGateRejectedError(decision.reason_code)
    episode = OpsMemoryEpisode(
        tenant_id=candidate.tenant_id.strip(),
        run_id=candidate.run_id.strip(),
        task_domain=(candidate.task_domain or "").strip(),
        context_fingerprint=candidate.context_fingerprint.strip(),
        plan_summary=candidate.plan_summary,
        tool_sequence=list(candidate.tool_sequence),
        outcome=candidate.outcome,
        failure_class=(candidate.failure_class or "").strip() or None,
    )
    try:
        if session is not None:
            session.add(episode)
            await session.flush()
        else:
            async with AsyncSessionLocal() as own, own.begin():
                own.add(episode)
                await own.flush()
    except Exception as exc:
        if _is_missing_table(exc):
            logger.warning(
                "memory episode table missing; write degraded run_id=%s",
                candidate.run_id,
            )
            return None
        raise
    # 审计记动作不记内容（无 plan 摘要 / 工具序列正文）
    logger.info(
        "memory episode written id=%s run_id=%s tenant=%s outcome=%s",
        episode.id,
        episode.run_id,
        episode.tenant_id,
        episode.outcome,
    )
    return episode


async def revoke_by_run(
    run_id: str,
    *,
    session: AsyncSession | None = None,
) -> int:
    """按 run_id 批量置 revoked（episode 纠错唯一入口）；幂等；审计记影响行数。

    只动 active 行 ⇒ 重复调用影响 0 行；revoke 后召回零命中（召回只认
    active），行留表可查（审计对账）。表不存在 → 降级返回 0（off 态安全）。
    """
    stmt = (
        update(OpsMemoryEpisode)
        .where(
            OpsMemoryEpisode.run_id == run_id,
            OpsMemoryEpisode.status == STATUS_ACTIVE,
        )
        .values(status=STATUS_REVOKED)
    )
    try:
        if session is not None:
            result = await session.execute(stmt)
            count = int(result.rowcount or 0)
        else:
            async with AsyncSessionLocal() as own, own.begin():
                result = await own.execute(stmt)
                count = int(result.rowcount or 0)
    except Exception as exc:
        if _is_missing_table(exc):
            logger.warning("memory episode table missing; revoke degraded run_id=%s", run_id)
            return 0
        raise
    # 审计日志：纠错动作本身必须可追查（含幂等 0 行）
    logger.info("memory episode revoke_by_run run_id=%s affected=%d", run_id, count)
    return count


async def recall_success_episodes(
    tenant_id: str,
    context_fingerprint: str,
    *,
    limit: int = 3,
    session: AsyncSession | None = None,
) -> list[OpsMemoryEpisode]:
    """确定性召回（D3）：同 tenant + outcome=success + status=active +
    fingerprint 精确匹配，created_at desc top-N。

    必带 tenant 谓词（跨 tenant = 空结果）；只召回 success（污染放大防线
    第一层 · SPEC FP-1）；并列按 id desc 兜底（截断不随机）。
    表不存在 → 降级空列表（off 态 drop 安全）。
    """
    stmt = (
        select(OpsMemoryEpisode)
        .where(
            OpsMemoryEpisode.tenant_id == tenant_id,
            OpsMemoryEpisode.context_fingerprint == context_fingerprint,
            OpsMemoryEpisode.outcome == OUTCOME_SUCCESS,
            OpsMemoryEpisode.status == STATUS_ACTIVE,
        )
        .order_by(OpsMemoryEpisode.created_at.desc(), OpsMemoryEpisode.id.desc())
        .limit(max(0, limit))
    )
    try:
        if session is not None:
            result = await session.execute(stmt)
            return list(result.scalars().all())
        async with AsyncSessionLocal() as own:
            result = await own.execute(stmt)
            return list(result.scalars().all())
    except Exception as exc:
        if _is_missing_table(exc):
            logger.warning("memory episode table missing; recall degraded to empty")
            return []
        raise
