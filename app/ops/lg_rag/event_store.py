"""lg-rag SSE 事件落盘 / 按 after_seq 加载（T4 · 不依赖 chat/session）。

chat-history-api（B1）：追加**只读**历史查询面——按 user 列 thread
（GROUP BY 聚合 + keyset 分页）、按 thread 拉全量事件（聚合在
``history.py`` 纯函数层完成）。零新表/迁移/写路径。
"""

from __future__ import annotations

import logging
import os
from datetime import datetime
from typing import Any

from sqlalchemy import and_, func, or_, select

from app.db.models import OpsLgRagRunEvent, now_utc
from app.db.session import AsyncSessionLocal
from app.ops.lg_rag.sse_replay import format_sse_event

logger = logging.getLogger(__name__)


class LgRagRunNotFoundError(Exception):
    """未知或跨用户 run_id；HTTP 映射 404。"""


class LgRagRunInFlightError(Exception):
    """run 仍在流式写入（无收尾帧）；HTTP 映射 409 + Retry-After（F-OBS-2）。"""


class LgRagRunResumeInProgressError(Exception):
    """HITL 恢复段正在写事件表（hitl.resumed 已落、尚无新收尾帧）；HTTP 映射 409 + Retry-After。

    与 LgRagRunInFlightError 刻意区分 detail：首段在飞 = 无收尾帧；恢复段在写窗 =
    已有旧收尾帧（done{waiting_approval}）但其后有 hitl.resumed（task_lg_rag_replay_resume_ux_opt D1）。
    """


_RESUME_STALE_DEFAULT_SECONDS = 900.0
# 定稿理由（30 实证裁定 · FP-1）：恢复段实测 68–289s（2026-10-28 PG 实证
# run 38cb1138… latency_ms=289607 / 1039c1a9… ≈68s · 仅两数据点），取 max 实测
# 约 3 倍余量定默认 900s——正常恢复段远早于此收尾，超阈只命中「崩溃在写窗」
# 残留形态（ResumeError 时 sink 不关不落新收尾帧），回落放行防 replay 409 永久化。


def _resume_stale_seconds() -> float:
    """读 env LG_RAG_RESUME_STALE_SECONDS；缺省/非法/≤0 回退默认（承 run_worker env 体例）。"""
    raw = os.environ.get("LG_RAG_RESUME_STALE_SECONDS", "").strip()
    if not raw:
        return _RESUME_STALE_DEFAULT_SECONDS
    try:
        value = float(raw)
    except ValueError:
        logger.warning("LG_RAG_RESUME_STALE_SECONDS 非法值 %r，回退默认 %.0fs", raw, _RESUME_STALE_DEFAULT_SECONDS)
        return _RESUME_STALE_DEFAULT_SECONDS
    if value <= 0:
        logger.warning("LG_RAG_RESUME_STALE_SECONDS 须 >0（%r），回退默认 %.0fs", raw, _RESUME_STALE_DEFAULT_SECONDS)
        return _RESUME_STALE_DEFAULT_SECONDS
    return value


async def persist_run_event(
    *,
    run_id: str,
    seq: int,
    user_id: str,
    thread_id: str,
    ts_ms: int,
    agent_role: str,
    event_type: str,
    payload: dict[str, Any],
) -> None:
    """尽量落盘一帧；失败由调用方吞掉（不阻断 SSE）。"""
    if not run_id or not user_id:
        return
    async with AsyncSessionLocal() as db:
        db.add(
            OpsLgRagRunEvent(
                run_id=run_id,
                seq=seq,
                user_id=user_id,
                thread_id=thread_id or "",
                ts_ms=ts_ms,
                agent_role=agent_role,
                event_type=event_type,
                payload=payload or {},
            )
        )
        await db.commit()


async def run_owner(run_id: str) -> str | None:
    """该 run 的归属用户；run 不存在（还没落过帧）返回 ``None``。

    为什么需要这个反问：HITL 申请行里只有 ``thread_id`` / ``run_id``，
    **没有 user_id**，而 replay 是按 user_id 做归属校验的。
    恢复段要往**同一个 run_id** 里续写事件，归属只能从已有事件反查 ——
    取不到就宁可不写（写了也读不出来：另一个 user_id 永远 replay 不到），
    并且必须把这个"没写"报出来，不能静默。
    """
    if not run_id:
        return None
    async with AsyncSessionLocal() as db:
        row = (
            await db.execute(
                select(OpsLgRagRunEvent.user_id).where(OpsLgRagRunEvent.run_id == run_id).limit(1)
            )
        ).first()
    return str(row[0]) if row else None


async def last_seq(run_id: str) -> int:
    """该 run 当前最大 seq；恢复段从这里**接着编号**（不是从 1 重开）。"""
    if not run_id:
        return 0
    async with AsyncSessionLocal() as db:
        row = (
            await db.execute(
                select(func.max(OpsLgRagRunEvent.seq)).where(OpsLgRagRunEvent.run_id == run_id)
            )
        ).first()
    return int(row[0] or 0) if row else 0


async def run_is_terminal(run_id: str) -> bool:
    """run 是否已到**终态**（T2 实操-E · 补偿扫描「run 未终态」判定的只读真源）。

    真源裁定（30 留痕）：终态 = 事件表存在终结帧，与 `history.run_terminal_status`
    同口径——
    - `error` 帧 → 终态；
    - `done` 帧且 `payload.status != 'waiting_approval'`（缺省按 completed）→ 终态；
    - `done{waiting_approval}` 是**挂起等待**而非终态（恰是待恢复形态，排除）；
    - 无任何帧 → 非终态。

    红线：禁读进程内存态 · 禁以 checkpoint 存在性近似终态。
    """
    if not run_id:
        return False
    status_expr = func.coalesce(OpsLgRagRunEvent.payload["status"].as_string(), "completed")
    async with AsyncSessionLocal() as db:
        row = (
            await db.execute(
                select(OpsLgRagRunEvent.seq)
                .where(
                    OpsLgRagRunEvent.run_id == run_id,
                    or_(
                        OpsLgRagRunEvent.event_type == "error",
                        and_(
                            OpsLgRagRunEvent.event_type == "done",
                            status_expr != "waiting_approval",
                        ),
                    ),
                )
                .limit(1)
            )
        ).first()
    return row is not None


async def run_stream_closed(run_id: str) -> bool:
    """run 的事件流是否已收尾（存在 done 或 error 帧）。

    与 run_is_terminal 刻意不同口径：done{waiting_approval} 挂起也算收尾
    ——挂起 run 的 replay 是既有合法操作须零 diff，只有正在流式写入（有帧
    无收尾帧）才是 replay 409 判定面（F-OBS-2）。只读，无副作用。
    """
    if not run_id:
        return False
    async with AsyncSessionLocal() as db:
        row = (
            await db.execute(
                select(OpsLgRagRunEvent.seq)
                .where(
                    OpsLgRagRunEvent.run_id == run_id,
                    OpsLgRagRunEvent.event_type.in_(("done", "error")),
                )
                .limit(1)
            )
        ).first()
    return row is not None


async def run_resume_in_progress(
    run_id: str,
    *,
    stale_after_seconds: float | None = None,
) -> bool:
    """HITL 恢复段是否正在写事件表（replay 409 语义化判定面 · task_lg_rag_replay_resume_ux_opt D1）。

    判定面（事件表真源 · 禁读进程内存态，承 run_is_terminal 红线——
    hitl/router.py 的 _RESUME_IN_FLIGHT 是 request_id 键的进程内单飞登记，
    多副本不成立，不能作真源）：
    「∃ hitl.resumed 帧其 seq > 最新 done/error 收尾帧 seq」⇒ 恢复段在写。

    刻意判 False 的形态（与在写窗互斥 · replay 既有行为零 diff · FP-4）：
    纯挂起（无 hitl.resumed）/ 再挂起（hitl.resumed 后新 done{waiting_approval}）/
    沉降（hitl.resumed 后 done{resumed}）/ 恢复段失败（hitl.resumed 后 error）/
    首段在飞（无 hitl.resumed · 走既有在飞 409 语义）。

    stale 阈（FP-1）：恢复段崩溃在写窗（ResumeError 时 sink 不关不落新收尾帧 ·
    app/ops/hitl/router.py:447-449 注释口径）时谓词恒真 → replay 409 永久化；
    末帧 created_at 超阈 ⇒ 视为已沉降回落 False + error 日志照登（orphan 补偿不覆盖
    此形态——done{waiting_approval} 已存在 ⇒ list_open_runs 排除——缓解不硬修）。
    阈值默认见 _RESUME_STALE_DEFAULT_SECONDS 注释；env
    LG_RAG_RESUME_STALE_SECONDS 可调；stale_after_seconds 显式传参覆盖
    （<=0 关闭 stale 判定 · 承 scan_orphan_runs_for_compensation 先例）。
    只读，无副作用。
    """
    if not run_id:
        return False
    if stale_after_seconds is None:
        stale_after_seconds = _resume_stale_seconds()
    closing_sq = (
        select(func.max(OpsLgRagRunEvent.seq))
        .where(
            OpsLgRagRunEvent.run_id == run_id,
            OpsLgRagRunEvent.event_type.in_(("done", "error")),
        )
        .scalar_subquery()
    )
    async with AsyncSessionLocal() as db:
        resumed = (
            await db.execute(
                select(OpsLgRagRunEvent.seq)
                .where(
                    OpsLgRagRunEvent.run_id == run_id,
                    OpsLgRagRunEvent.event_type == "hitl.resumed",
                    OpsLgRagRunEvent.seq > func.coalesce(closing_sq, 0),
                )
                .limit(1)
            )
        ).first()
        if resumed is None:
            return False
        if stale_after_seconds <= 0:
            return True
        last_created_at = (
            await db.execute(
                select(OpsLgRagRunEvent.created_at)
                .where(OpsLgRagRunEvent.run_id == run_id)
                .order_by(OpsLgRagRunEvent.seq.desc())
                .limit(1)
            )
        ).scalar()
    if last_created_at is None:
        return False
    age_seconds = (now_utc() - last_created_at).total_seconds()
    if age_seconds > stale_after_seconds:
        logger.error(
            "lg-rag 恢复段在写窗超 stale 阈（疑似崩溃残留 · FP-1）run_id=%s age=%.1fs threshold=%.1fs ⇒ 谓词回落 False",
            run_id,
            age_seconds,
            stale_after_seconds,
        )
        return False
    return True


async def list_open_runs(
    *,
    stale_after_seconds: float = 0,
    limit: int = 50,
) -> list[dict[str, Any]]:
    """有帧但无 done/error 的 orphan 候选（TC-B5 / F-A1）。

    ``stale_after_seconds>0`` 时仅返回末帧 ``created_at`` 早于 cutoff 的 run。
    只读；是否补偿由 ``scan_orphan_runs_for_compensation`` 再滤活跃 worker。
    """
    from datetime import timedelta

    from app.db.models import now_utc

    if limit <= 0:
        return []
    closed_ids = (
        select(OpsLgRagRunEvent.run_id)
        .where(OpsLgRagRunEvent.event_type.in_(("done", "error")))
        .distinct()
    )
    # 每 run 取末帧行（max seq）上的 user_id/thread_id；禁 min(uuid)
    max_seq_sq = (
        select(
            OpsLgRagRunEvent.run_id.label("rid"),
            func.max(OpsLgRagRunEvent.seq).label("mx"),
        )
        .where(OpsLgRagRunEvent.run_id.notin_(closed_ids))
        .group_by(OpsLgRagRunEvent.run_id)
        .subquery()
    )
    stmt = select(
        OpsLgRagRunEvent.run_id,
        OpsLgRagRunEvent.user_id,
        OpsLgRagRunEvent.thread_id,
        OpsLgRagRunEvent.seq.label("max_seq"),
        OpsLgRagRunEvent.created_at.label("last_activity_at"),
    ).join(
        max_seq_sq,
        and_(
            OpsLgRagRunEvent.run_id == max_seq_sq.c.rid,
            OpsLgRagRunEvent.seq == max_seq_sq.c.mx,
        ),
    )
    if stale_after_seconds > 0:
        cutoff = now_utc() - timedelta(seconds=stale_after_seconds)
        stmt = stmt.where(OpsLgRagRunEvent.created_at < cutoff)
    stmt = stmt.order_by(OpsLgRagRunEvent.created_at.asc()).limit(limit)
    async with AsyncSessionLocal() as db:
        rows = (await db.execute(stmt)).all()
    return [
        {
            "run_id": str(row.run_id),
            "user_id": str(row.user_id),
            "thread_id": str(row.thread_id),
            "last_activity_at": row.last_activity_at,
            "max_seq": int(row.max_seq or 0),
        }
        for row in rows
    ]


async def assert_run_owned(run_id: str, user_id: str) -> None:
    """确认 run 存在且归属当前用户；否则 ``LgRagRunNotFoundError``。"""
    if not run_id or not user_id:
        raise LgRagRunNotFoundError
    owner = await run_owner(run_id)
    if owner is None:
        raise LgRagRunNotFoundError
    if str(owner) != str(user_id):
        raise LgRagRunNotFoundError


async def load_events_after(
    run_id: str,
    user_id: str,
    after_seq: int,
    *,
    refuse_in_flight: bool = False,
) -> list[dict[str, Any]]:
    """归属校验后返回 `seq` > `after_seq` 的已提交帧（live 形状）。

    refuse_in_flight 开启时（replay 面 · F-OBS-2），run 仍在流式写入
    （无收尾帧）则抛 LgRagRunInFlightError——读路径对写入中 run 不稳定
    （live 实证 500），前置拦截语义化为 409 让客户端退避重试；缺省
    False，其余调用面零 diff。

    同开时增第二闸（task_lg_rag_replay_resume_ux_opt D1）：HITL 恢复段在写窗
    （hitl.resumed 已落、尚无新收尾帧 · 判定见 run_resume_in_progress）抛
    LgRagRunResumeInProgressError——该形态下既有在飞闸不拦（done{waiting_approval}
    挂起帧算收尾 · F-OBS-2 刻意口径），若无本闸则 replay 合法 200 零帧无语义区分。
    恢复段在写窗与首段在飞/纯挂起/沉降三态互斥，故既有闸行为零 diff。
    """
    await assert_run_owned(run_id, user_id)
    if refuse_in_flight and not await run_stream_closed(run_id):
        raise LgRagRunInFlightError(run_id)
    if refuse_in_flight and await run_resume_in_progress(run_id):
        raise LgRagRunResumeInProgressError(run_id)
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(OpsLgRagRunEvent)
            .where(
                OpsLgRagRunEvent.run_id == run_id,
                OpsLgRagRunEvent.user_id == user_id,
                OpsLgRagRunEvent.seq > after_seq,
            )
            .order_by(OpsLgRagRunEvent.seq.asc())
        )
        rows = result.scalars().all()
    return [
        format_sse_event(
            {
                "run_id": row.run_id,
                "seq": row.seq,
                "ts_ms": row.ts_ms,
                "agent_role": row.agent_role,
                "event_type": row.event_type,
                "payload": row.payload or {},
            }
        )
        for row in rows
    ]


# ---------------------------------------------------------------------------
# chat-history-api（B1）· 只读历史查询面
# ---------------------------------------------------------------------------


async def thread_owner(thread_id: str) -> str | None:
    """该 thread 的归属用户；无任何已落盘帧返回 ``None``。

    与 ``run_owner`` 同语义：历史面的归属真源 = 事件表 ``user_id`` 列，
    跨用户/未知一律由调用方映射 404（不泄露存在性）。
    """
    if not thread_id:
        return None
    async with AsyncSessionLocal() as db:
        row = (
            await db.execute(
                select(OpsLgRagRunEvent.user_id)
                .where(OpsLgRagRunEvent.thread_id == thread_id)
                .limit(1)
            )
        ).first()
    return str(row[0]) if row else None


async def list_thread_activity_page(
    user_id: str,
    *,
    limit: int,
    after: tuple[datetime, str] | None = None,
) -> list[dict[str, Any]]:
    """当前用户 thread 活动一页（keyset 分页）。

    排序：``last_activity_at``（= 该 thread 末帧 ``created_at``）倒序，
    并列按 ``thread_id`` 升序（稳定键）。``after=(last_activity_at, thread_id)``
    为上一页末条的 keyset 游标。返回 ``[{thread_id, last_activity_at, run_count}]``。
    """
    last_activity = func.max(OpsLgRagRunEvent.created_at)
    stmt = (
        select(
            OpsLgRagRunEvent.thread_id,
            last_activity.label("last_activity_at"),
            func.count(func.distinct(OpsLgRagRunEvent.run_id)).label("run_count"),
        )
        .where(OpsLgRagRunEvent.user_id == user_id)
        .group_by(OpsLgRagRunEvent.thread_id)
    )
    if after is not None:
        after_ts, after_tid = after
        stmt = stmt.having(
            or_(
                last_activity < after_ts,
                and_(
                    last_activity == after_ts,
                    OpsLgRagRunEvent.thread_id > after_tid,
                ),
            )
        )
    stmt = stmt.order_by(last_activity.desc(), OpsLgRagRunEvent.thread_id.asc()).limit(limit)
    async with AsyncSessionLocal() as db:
        rows = (await db.execute(stmt)).all()
    return [
        {
            "thread_id": str(row.thread_id),
            "last_activity_at": row.last_activity_at,
            "run_count": int(row.run_count),
        }
        for row in rows
    ]


async def fetch_events_for_threads(
    user_id: str,
    thread_ids: list[str],
) -> dict[str, list[dict[str, Any]]]:
    """按 thread 分组返回当前用户已落盘事件（``created_at, seq`` 升序原始行）。

    只读；聚合（标题/状态/消息视图）在 ``history.py`` 纯函数层完成，
    这里只负责把行按 ``(created_at, seq)`` 排好——与落盘时序真源一致。
    """
    if not user_id or not thread_ids:
        return {}
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(OpsLgRagRunEvent)
            .where(
                OpsLgRagRunEvent.user_id == user_id,
                OpsLgRagRunEvent.thread_id.in_(list(thread_ids)),
            )
            .order_by(
                OpsLgRagRunEvent.created_at.asc(),
                OpsLgRagRunEvent.seq.asc(),
            )
        )
        rows = result.scalars().all()
    grouped: dict[str, list[dict[str, Any]]] = {tid: [] for tid in thread_ids}
    for row in rows:
        grouped.setdefault(row.thread_id, []).append(
            {
                "run_id": row.run_id,
                "seq": row.seq,
                "user_id": str(row.user_id),
                "thread_id": row.thread_id,
                "ts_ms": row.ts_ms,
                "agent_role": row.agent_role,
                "event_type": row.event_type,
                "payload": row.payload or {},
                "created_at": row.created_at,
            }
        )
    return grouped
