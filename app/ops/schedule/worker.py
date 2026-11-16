"""Schedule worker 触发执行器（P3-T3 · issue #23 · 设计真源 14 §1.1-§1.8 · 契约真源 15 §4/§7.1）。

lifespan 周期任务（逐字承 auto_resume.py:273-309 五件套先例：env 解析 + 默认关零创建
+ 模块级句柄幂等复用 + 异常吞掉下周期重试 + shutdown cancel 等收尾）。

- 总闸 OPS_SCHEDULE_ENABLED ∈ {off（默认）, on}（R8 · 15 §7.1）：strip().lower()，
  非法值回退 off + logger.warning；on 才创建 worker task；总闸只管 worker **不闸 REST**
  （off 态 TestClient 零 diff · 既有测试面不动）。
- tick 周期 OPS_SCHEDULE_TICK_SECONDS：默认 30s，非法/越界 [1,3600] 回退 30
  （承 scan_interval_seconds 先例形态 · 静默回退）。
- DB 原子抢占（14 §1.4 · 锚 hitl/store.py:261-277 SKIP LOCKED 先例）：单事务
  SELECT ... FOR UPDATE SKIP LOCKED 领到期行（行锁=租约 · 并发双扫不重领）→
  同事务逐行 INSERT fires(status=claimed) ON CONFLICT (schedule_id, planned_fire_at)
  DO NOTHING（撞行=他方已占·跳过）+ 推进 next_fire_at / fire_count+1 / last_fired_at
  （D1：设计单语句 UPDATE...RETURNING 拆为「锁定 SELECT + 同事务逐行推进」，因
  next_fire_at 按 kind 分别计算 · 原子性等价）。
- fires 状态机（15 §4.1）：claimed→fired（run 创建成功 **写回 run_id 才算**）；
  claimed→failed（thread 外来 R6 / user 悬空 R11 / run 创建失败 · logger.exception 留痕）；
  claimed→skipped（schedule 已 paused/cancelled 或已达 max_fires）。
- 补跑 fire_once（14 §1.5）：每 tick（含启动首轮立即执行）对 next_fire_at≤now 的
  active 行各点一次并推进严格未来；停机跨 N 个 interval 只补一次（推进即收敛）。
- 启动补链（14 §1.5 · R10 · 15 §4.3「补链只信台账」）：lifespan 启动首轮对
  status=claimed AND run_id IS NULL 且超龄（CLAIM_STALE_SECONDS=120）的 fires 行
  按台账重放（承 run_worker.scan_orphan_runs_for_compensation 思路）。
- 触发语义（15 §4）：query = 「[定时任务 · {name}] {instruction}」（前缀仅展示 ·
  **非归因/鉴权依据** · 唯一归因真源=fires 三元组 · R12/SP2）；内部直调
  create_run + start_run_worker（不经 HTTP · 承 router.py:454-487 不 await 先例）；
  user turn 不单独落盘——带前缀 query 经既有管线 done 时 persist_thread_turns 落盘
  （避免重复 turn）；goal 懒创建不调（定时指令不该建 goal）。
- fix-434（issue #434 第一项 · 契约 15 §1.2「thread 不存在 fire 时自建」）：
  fire 前 R6 复核后，thread 行缺失则 _execute_fire 同事务补最小行（已存在不动），
  保证 runs 卡片端点（thread_owner 归聚）在 run done 前及非 done 终态下不 404。
- 预算归因（14 §1.8 · R4）：start_run_worker 显式传 creator 身份
  （user_id/tenant_id 取自 schedule 行）；归因链 usage.run_id → ops_lg_rag_runs.user_id
  （ops_llm_usage 无 user_id 列）锚定 creator。
- 点火审计日志三元组（schedule_id / fire_id / run_id · 15 §4.4 · 进验收）。
"""

from __future__ import annotations

import asyncio
import contextlib
import logging
import os
import uuid as _uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import exists, select

from app.db.models import OpsLgRagThread, OpsSchedule, OpsScheduleFire, OpsUser
from app.db.session import AsyncSessionLocal
from app.ops.schedule.store import compute_next_fire_at

logger = logging.getLogger(__name__)

# 总闸与扫频 env（R8 · 15 §7.1 · 14 §1.1）
ENV_SCHEDULE_ENABLED = "OPS_SCHEDULE_ENABLED"
MODE_OFF = "off"
MODE_ON = "on"
ENV_TICK_SECONDS = "OPS_SCHEDULE_TICK_SECONDS"
DEFAULT_TICK_SECONDS = 30
_TICK_MIN_SECONDS = 1
_TICK_MAX_SECONDS = 3600

#: 单 tick 抢占上限（14 §1.4 钉值）
BATCH_LIMIT = 50

#: 启动补链 claimed 孤儿超龄阈值（秒 · 设计未钉值的实施决策 D2 · 4×默认 tick）
CLAIM_STALE_SECONDS = 120.0

# 后台任务句柄模块级管理：幂等复用 + shutdown 可盘点（承 auto_resume._SCAN_TASK）
_WORKER_TASK: asyncio.Task | None = None


def schedule_worker_enabled() -> str:
    """总闸解析：缺省/非法一律回退 off（fail-closed · R8 · 承 auto_resume_mode 先例）。"""
    raw = os.environ.get(ENV_SCHEDULE_ENABLED, "").strip().lower()
    if not raw:
        return MODE_OFF
    if raw in (MODE_OFF, MODE_ON):
        return raw
    logger.warning("%s=%r 无法识别（仅 off / on），按 off 处理", ENV_SCHEDULE_ENABLED, raw)
    return MODE_OFF


def tick_seconds() -> int:
    """扫频（秒）：默认 30，非法/越界 [1,3600] 回退默认（承 scan_interval_seconds 先例）。"""
    raw = os.environ.get(ENV_TICK_SECONDS, "")
    try:
        value = int(str(raw).strip())
    except (TypeError, ValueError):
        return DEFAULT_TICK_SECONDS
    return value if _TICK_MIN_SECONDS <= value <= _TICK_MAX_SECONDS else DEFAULT_TICK_SECONDS


def _now() -> datetime:
    return datetime.now(UTC)


def _effective_max_fires(schedule: OpsSchedule) -> int | None:
    """max_fires 有效上限：once_at 语义等价 1（15 §1.2 · 不落库）。"""
    if schedule.max_fires is not None:
        return schedule.max_fires
    return 1 if schedule.schedule_kind == "once_at" else None


async def claim_due_schedules(
    *, now: datetime | None = None, batch_limit: int = BATCH_LIMIT
) -> list[str]:
    """抢占到期 schedule（单事务 · SKIP LOCKED 行锁=租约）；返回本轮 claimed 的 fire_id 列表。

    事务内逐行（14 §1.4 同事务纪律）：

    1. INSERT fires(status=claimed) ON CONFLICT DO NOTHING——撞幂等键
       uq(schedule_id, planned_fire_at) = 他方已占 → 回滚该次 SAVEPOINT 跳过（吞错
       写 IntegrityError 会 abort 整个事务，故用嵌套事务逐行容错 · 禁 DROP 式容错）；
    2. 已达 max_fires → fire 立即置 skipped（状态机字面 · 15 §4.1），**不增**
       fire_count，interval/daily 仍推进 next_fire_at（提高 max_fires 即自然恢复）；
    3. 否则推进 next_fire_at（严格未来 · 补跑火一次）/ fire_count+1 / last_fired_at；
       once_at 不推进（无下一时刻可算 · NOT EXISTS 谓词 + 幂等键双保险不再入选）。
    """
    now = now or _now()
    claimed: list[str] = []
    async with AsyncSessionLocal() as db:
        occupied = exists().where(
            OpsScheduleFire.schedule_id == OpsSchedule.schedule_id,
            OpsScheduleFire.planned_fire_at == OpsSchedule.next_fire_at,
        )
        rows = (
            (
                await db.execute(
                    select(OpsSchedule)
                    .where(
                        OpsSchedule.status == "active",
                        OpsSchedule.next_fire_at <= now,
                        ~occupied,
                    )
                    .order_by(OpsSchedule.next_fire_at.asc())
                    .limit(batch_limit)
                    .with_for_update(skip_locked=True)
                )
            )
            .scalars()
            .all()
        )
        for schedule in rows:
            planned = schedule.next_fire_at
            fire = OpsScheduleFire(
                schedule_id=schedule.schedule_id,
                tenant_id=schedule.tenant_id,
                planned_fire_at=planned,
                status="claimed",
            )
            inserted = False
            try:
                async with db.begin_nested():
                    db.add(fire)
                inserted = True
            except Exception:
                # 幂等键撞行 = 他进程已占该计划时刻 → 跳过（禁吞错写 IntegrityError）
                logger.info(
                    "schedule claim conflict skip schedule_id=%s planned_fire_at=%s",
                    schedule.schedule_id,
                    planned.isoformat(),
                )
            if not inserted:
                continue
            max_fires = _effective_max_fires(schedule)
            if max_fires is not None and schedule.fire_count >= max_fires:
                fire.status = "skipped"
                logger.info(
                    "schedule fire skipped max_fires reached schedule_id=%s fire_id=%s",
                    schedule.schedule_id,
                    fire.id,
                )
            else:
                schedule.fire_count += 1
                schedule.last_fired_at = now
            if schedule.schedule_kind != "once_at":
                schedule.next_fire_at = compute_next_fire_at(
                    schedule_kind=schedule.schedule_kind,
                    interval_seconds=schedule.interval_seconds,
                    time_of_day=schedule.time_of_day,
                    tz_name=schedule.timezone,
                    now=now,
                )
            claimed.append(str(fire.id))
        await db.commit()
    return claimed


async def _execute_fire(*, fire_id: str, source: str) -> str:
    """执行单次点火（tick / relink 同源）；返回 fires 终态 fired / failed / skipped。

    顺序（15 §4.2）：复核 schedule 状态 → R11 user 存在校验（悬空→failed +
    schedule 自动 paused）→ R6 thread 归属复核（外来→failed 不投递）→
    create_run 建行 → start_run_worker（不 await · 承 router.py:487 先例）→
    写回 run_id + status=fired + fired_at（**run_id 写回才算 fired** · R10）。
    """
    from app.ops.lg_rag import run_worker as _run_worker
    from app.ops.lg_rag.run_store import create_run

    async with AsyncSessionLocal() as db:
        fire = await db.get(OpsScheduleFire, fire_id)
        if fire is None or fire.status != "claimed":
            return "skipped"
        schedule_id_str = str(fire.schedule_id)
        schedule = await db.get(OpsSchedule, fire.schedule_id)
        if schedule is None or schedule.status != "active":
            fire.status = "skipped"
            await db.commit()
            logger.info(
                "schedule fire skipped schedule inactive schedule_id=%s fire_id=%s",
                fire.schedule_id,
                fire_id,
            )
            return "skipped"
        try:
            user = await db.get(OpsUser, schedule.user_id)
            if user is None:
                # R11（14 §1.2 注）：创建者悬空 → failed + schedule 自动 paused
                fire.status = "failed"
                schedule.status = "paused"
                await db.commit()
                logger.warning(
                    "schedule fire failed dangling user schedule_id=%s fire_id=%s user_id=%s",
                    schedule.schedule_id,
                    fire_id,
                    schedule.user_id,
                )
                return "failed"
            thread = await db.get(OpsLgRagThread, schedule.thread_id)
            if thread is not None and str(thread.user_id) != str(schedule.user_id):
                # R6（14 §1.6）：fire 前复核 thread 归属——外来 thread 不投递
                fire.status = "failed"
                await db.commit()
                logger.warning(
                    "schedule fire failed foreign thread schedule_id=%s fire_id=%s thread_id=%s",
                    schedule.schedule_id,
                    fire_id,
                    schedule.thread_id,
                )
                return "failed"
            if thread is None:
                # fix-434（issue #434 第一项 · 契约 15 §1「thread 不存在 fire 时
                # 自建」）：自建语义前移到点火同事务——补最小行（承
                # thread_store.py:35/:95 先例形态 · 已存在不动）。否则 run 行落库到
                # done persist 之间的窗口、及 waiting_approval/error 等不走 persist
                # 的终态下 thread 行缺失，runs 卡片端点 thread_owner 归聚 404。
                # flush 先行：建行失败（并发 PK 冲突等）在 create_run 前暴露，
                # 走既有 except → rollback + failed（不留半建 run 行）。
                db.add(OpsLgRagThread(id=schedule.thread_id, user_id=schedule.user_id))
                await db.flush()
            run_id = _uuid.uuid4().hex
            fire.run_id = run_id
            created = await create_run(
                run_id=run_id,
                thread_id=schedule.thread_id,
                user_id=str(schedule.user_id),
                tenant_id=schedule.tenant_id,
            )
            if not created:
                raise RuntimeError(f"create_run 建行失败 run_id={run_id}")
            query = f"[定时任务 · {schedule.name}] {schedule.instruction}"
            _run_worker.start_run_worker(
                query=query,
                mode="supervisor",
                thread_id=schedule.thread_id,
                run_id=run_id,
                user_id=str(schedule.user_id),
                tenant_id=schedule.tenant_id,
            )
            fire.status = "fired"
            fire.fired_at = _now()
            await db.commit()
        except Exception:
            await db.rollback()
            async with AsyncSessionLocal() as db2:
                fire2 = await db2.get(OpsScheduleFire, fire_id)
                if fire2 is not None and fire2.status == "claimed":
                    fire2.status = "failed"
                    await db2.commit()
            logger.exception(
                "schedule fire failed schedule_id=%s fire_id=%s",
                schedule_id_str,
                fire_id,
            )
            return "failed"
    logger.info(
        "schedule fired source=%s schedule_id=%s fire_id=%s run_id=%s",
        source,
        schedule.schedule_id,
        fire_id,
        run_id,
    )
    return "fired"


async def run_schedule_tick(
    *, now: datetime | None = None, batch_limit: int = BATCH_LIMIT
) -> dict[str, int]:
    """一轮扫描：抢占到期行 → 逐条执行。返回统计（进测试断言与日志）。

    tick 内单条 fire 失败不影响其余（各 fire 独立会话/事务）；DB 级异常由
    _loop 兜住下周期重试（不炸 lifespan · 14 §11）。
    """
    fire_ids = await claim_due_schedules(now=now, batch_limit=batch_limit)
    stats = {"claimed": len(fire_ids), "fired": 0, "failed": 0, "skipped": 0}
    for fire_id in fire_ids:
        outcome = await _execute_fire(fire_id=fire_id, source="tick")
        stats[outcome] += 1
    return stats


async def relink_stale_claimed_fires(
    *, now: datetime | None = None, stale_after_seconds: float = CLAIM_STALE_SECONDS
) -> dict[str, int]:
    """启动补链（14 §1.5 · R10 · 15 §4.3「补链只信台账」）：重放 claimed 孤儿 fires。

    对象：status=claimed AND run_id IS NULL AND created_at ≤ now - stale_after。
    崩溃窗口（claim 提交后·执行前）遗留的台账行按同 _execute_fire 语义重放
    （补建 run 写回或标 failed · 承 run_worker.scan_orphan 两段式思路）。
    """
    now = now or _now()
    cutoff = now - timedelta(seconds=stale_after_seconds)
    stats = {"relinked": 0, "fired": 0, "failed": 0, "skipped": 0}
    async with AsyncSessionLocal() as db:
        rows = (
            (
                await db.execute(
                    select(OpsScheduleFire.id)
                    .where(
                        OpsScheduleFire.status == "claimed",
                        OpsScheduleFire.run_id.is_(None),
                        OpsScheduleFire.created_at <= cutoff,
                    )
                    .order_by(OpsScheduleFire.planned_fire_at.asc())
                    .limit(BATCH_LIMIT)
                )
            )
            .scalars()
            .all()
        )
    for fire_id in rows:
        outcome = await _execute_fire(fire_id=str(fire_id), source="relink")
        stats["relinked"] += 1
        stats[outcome] += 1
    if stats["relinked"]:
        logger.info("schedule relink stale claimed stats=%s", stats)
    return stats


def start_schedule_worker() -> asyncio.Task:
    """创建（或幂等复用）周期任务；返回 task（承 start_compensation_scanner 五件套）。"""
    global _WORKER_TASK
    if _WORKER_TASK is not None and not _WORKER_TASK.done():
        return _WORKER_TASK

    async def _loop() -> None:
        first = True
        while True:
            try:
                if first:
                    # 启动补链先于首轮抢占（14 §1.5 · lifespan 启动首轮）
                    await relink_stale_claimed_fires()
                    first = False
                await run_schedule_tick()
            except asyncio.CancelledError:
                raise
            except Exception:
                logger.exception("schedule worker 本轮失败（下周期重试）")
            await asyncio.sleep(tick_seconds())

    _WORKER_TASK = asyncio.create_task(_loop())
    logger.info("schedule worker 已启动 interval=%ss", tick_seconds())
    return _WORKER_TASK


async def stop_schedule_worker() -> None:
    """shutdown 收尾：cancel + suppress CancelledError（承 stop_compensation_scanner）。"""
    global _WORKER_TASK
    task = _WORKER_TASK
    _WORKER_TASK = None
    if task is None:
        return
    task.cancel()
    with contextlib.suppress(asyncio.CancelledError):
        await task
