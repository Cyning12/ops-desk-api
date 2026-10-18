"""HITL 批准后自动恢复（T2 · SPEC D5 可配置面 · 触发器 + 行锁认领 + 补偿扫描）。

**为什么这个文件必须存在**：v0 链路只覆盖「手动 resume」半环——decide(approved)
之后必须人再点一次 resume 图才继续跑。本模块把「批准后继续」做成可配置两级面：

- 全局 env ``OPS_HITL_AUTO_RESUME`` ∈ {manual（默认 · 现状零 diff）, auto}，
  **非法值回退 manual**（fail-closed）；
- decide 载荷可选键 ``resume_mode`` ∈ {inherit, immediate, manual}（缺省 inherit），
  有效模式求解：immediate→auto · manual→manual · inherit→全局 env。

**无状态恢复纪律（SPEC 设计纪律 6 · 红线）**：触发器**不载状态**——后台任务句柄
不落盘、进程内不存任何「待恢复」业务态；进程重启零丢失靠**补偿扫描**兜底
（启动时扫一次 + 周期任务），恢复一律从事件表/DB 重建，与手动 resume
**同一条恢复路径**（``router._execute_decided_resume`` · 禁 HTTP 自调 · 禁第二条实现）。

**多副本防重（FP-8）**：真源是 PG 行锁认领（``DbHitlStore.aclaim_approved_for_resume``
· FOR UPDATE SKIP LOCKED · 仓内首个先例），叠加 resume 状态机守卫幂等
（非挂起态重入 = not_interrupted 无副作用）；**无进程内存去重缓存**（行锁即唯一真源）。

**补偿扫描「已批准未恢复」四条件**（裁定四）：status=approved ∧ decided_at 未过 TTL
（与 T1 消费门共用 ``OPS_HITL_APPROVAL_CONSUMPTION_TTL_SECONDS`` 单一旋钮）∧
run 无终态（``event_store.run_is_terminal`` · 实操-E 新增只读查询）∧
同 run 无未决 pending（第四条件防 FP-11 循环：auto resume 后仍被拦必产新 pending
→ 扫描自然跳过）。**扫描不看 decide 来源**（N-1 语义明示）：OA callback 批准的单据
在全局 auto 下不即时触发（OA 面不挂触发器 · R2-N2），但会被补偿扫描**补触发**
（延迟 ≤ 扫描周期）——「OA 面不挂」= 「不即时」而非「全 manual」，fail-safe 方向。

**认领竞态就绪校验（hitl-auto-resume-claim-race · 方向 A）**：nodes.py:1820-1831
「落库先于挂起」使 pending/approved 行可见 ⇏ checkpoint interrupt 元数据可见——
decide 同秒首跑此刻执行必撞 ``ResumeError: stranded_checkpoint``（resume.py:236-248 ·
live D1 实证 transient 窗口 ~30s 自愈）。认领后**执行前**做一次**只读**就绪校验
（``_interrupt_metadata_visible``）：命中 stranded 判定快照（有 pending tasks ·
interrupts 全空）则不执行不报错、留 ``hitl_auto_resume_deferred`` 台账等下轮
（认领不写状态 · 行锁随事务提交已释放 · 扫描自然补触发）——竞态化为「等下轮」，
首跑零 stranded_checkpoint。探针只读（FP-4）：不 resume、不写状态、不替执行
（执行仍唯一走 ``router._execute_decided_resume`` 同源路径）。
"""

from __future__ import annotations

import asyncio
import logging
import os
import time
from typing import Any

logger = logging.getLogger(__name__)

ENV_AUTO_RESUME = "OPS_HITL_AUTO_RESUME"
MODE_MANUAL = "manual"
MODE_AUTO = "auto"

ENV_SCAN_INTERVAL_SECONDS = "OPS_HITL_AUTO_RESUME_SCAN_INTERVAL_SECONDS"
DEFAULT_SCAN_INTERVAL_SECONDS = 60
SCAN_INTERVAL_MIN = 5
SCAN_INTERVAL_MAX = 3600

# decide 载荷可选键白名单（R2-N1：str + 端点手工校验 → 未知值 400 · 禁 Literal 变 422）
RESUME_MODE_INHERIT = "inherit"
RESUME_MODE_IMMEDIATE = "immediate"
RESUME_MODE_MANUAL = "manual"
RESUME_MODES = (RESUME_MODE_INHERIT, RESUME_MODE_IMMEDIATE, RESUME_MODE_MANUAL)

# 后台任务句柄模块级管理：防 GC 回收 + shutdown 可盘点（实操-D · 不载业务状态）
_BACKGROUND_TASKS: set[asyncio.Task] = set()
_SCAN_TASK: asyncio.Task | None = None


def auto_resume_mode() -> str:
    """全局开关：缺省/非法一律回退 ``manual``（fail-closed · 现状语义零 diff）。"""
    raw = os.environ.get(ENV_AUTO_RESUME, "").strip().lower()
    if not raw:
        return MODE_MANUAL
    if raw in (MODE_MANUAL, MODE_AUTO):
        return raw
    logger.error("%s=%r 无法识别（仅 manual / auto），按 manual 处理", ENV_AUTO_RESUME, raw)
    return MODE_MANUAL


def scan_interval_seconds() -> int:
    """补偿扫描周期（秒）：默认 60，非法/越界 [5,3600] 回退默认（承 _env_int 先例形态）。"""
    raw = os.environ.get(ENV_SCAN_INTERVAL_SECONDS, "")
    try:
        value = int(str(raw).strip())
    except (TypeError, ValueError):
        return DEFAULT_SCAN_INTERVAL_SECONDS
    return (
        value if SCAN_INTERVAL_MIN <= value <= SCAN_INTERVAL_MAX else DEFAULT_SCAN_INTERVAL_SECONDS
    )


def resolve_resume_mode(resume_mode: str) -> str:
    """有效模式求解：immediate→auto · manual→manual · inherit→全局 env。

    入参须已过白名单（端点手工校验 · R2-N1）；此处对未知值同样 fail-closed 回 manual。
    """
    if resume_mode == RESUME_MODE_IMMEDIATE:
        return MODE_AUTO
    if resume_mode == RESUME_MODE_INHERIT:
        return auto_resume_mode()
    return MODE_MANUAL


def _approval_ttl_seconds() -> int:
    """批准有效窗口：与 T1 消费门同一 env/默认/域（单一旋钮 · 不另开）。惰性 import 防环。"""
    from app.ops.lg_rag.multi.nodes import _approval_consumption_ttl_seconds

    return _approval_consumption_ttl_seconds()


def _decided_at_ts(raw: Any) -> float | None:
    """decided_at 归一（float | ISO str → 时间戳）：复用 T1 同一真源函数。"""
    from app.ops.lg_rag.multi.nodes import _decided_at_ts as _norm

    return _norm(raw)


def _audit(event: str, *, row: dict[str, Any], resume_mode: str, ttl_seconds: int) -> None:
    """台账三件套（记动作不记内容 · 承 delegation_approval_consumed 同一纪律）。

    只记 request_id / run_id / resume_mode / decision_by / TTL 余量，不记参数原值。
    """
    decided_ts = _decided_at_ts(row.get("decided_at"))
    ttl_remaining = (
        max(0, int(ttl_seconds - (time.time() - decided_ts))) if decided_ts is not None else None
    )
    logger.info(
        "%s request_id=%s run_id=%s resume_mode=%s decision_by=%s ttl_remaining_s=%s",
        event,
        row.get("id"),
        row.get("run_id"),
        resume_mode,
        row.get("decision_by") or "",
        ttl_remaining,
    )


def schedule_auto_resume(row: dict[str, Any], *, resume_mode: str, source: str) -> None:
    """派发进程内 asyncio 后台任务（R2-N2 挂点的执行体 · 派发不阻响应）。

    source ∈ {"decide", "scan"}：台账分别记 `hitl_auto_resume_triggered` /
    `hitl_auto_resume_compensated`。派发失败（无运行中事件循环等）只落日志，
    **不改变 decide 已返回的结果**（实操-F · 语义在先）。触发器只带 request_id
    进任务——不载状态，执行体从 DB/事件表重建（SPEC 设计纪律 6）。
    """
    ttl = _approval_ttl_seconds()
    event = "hitl_auto_resume_triggered" if source == "decide" else "hitl_auto_resume_compensated"
    _audit(event, row=row, resume_mode=resume_mode, ttl_seconds=ttl)
    request_id = str(row.get("id") or "")
    try:
        task = asyncio.create_task(
            _claim_and_execute(request_id, resume_mode=resume_mode, ttl_seconds=ttl)
        )
    except RuntimeError:
        logger.exception("HITL 自动恢复派发失败（无运行中事件循环）request=%s", request_id)
        return
    _BACKGROUND_TASKS.add(task)
    task.add_done_callback(_BACKGROUND_TASKS.discard)


async def _interrupt_metadata_visible(row: dict[str, Any]) -> bool:
    """认领后·执行前的**只读**就绪校验（hitl-auto-resume-claim-race · 方向 A）。

    竞态窗口形态（live D1 实证）：aget_state 有 pending tasks 但 interrupts
    全空——恰为执行侧 stranded_checkpoint 的判定快照（resume.py:236-248）。
    命中该形态返 False → 调用方 defer 等下轮；校验自身失败同样 fail-closed
    返 False（等下轮兜底）。无 pending tasks（含 checkpoint 行未写入）**不判
    未就绪**：非 stranded 形态，交还执行侧按现状语义处理（扫描兜底不变）。
    非 postgres checkpointer 部署无此窗口（执行侧同闸过不了）→ 直返 True。
    """
    from app.ops.lg_rag.checkpointer import apostgres_saver, use_postgres_checkpointer

    if not use_postgres_checkpointer():
        return True
    from app.ops.hitl.resume import _THREAD_ID_MAX, _default_graph_factory

    thread_id = str(row.get("thread_id") or "")[:_THREAD_ID_MAX]  # 同 resume.py:223 截断
    try:
        async with apostgres_saver() as saver:
            graph = _default_graph_factory(checkpointer=saver)
            state = await graph.aget_state({"configurable": {"thread_id": thread_id}})
    except Exception:
        logger.exception("HITL 自动恢复就绪校验失败（fail-closed 等下轮）request=%s", row.get("id"))
        return False
    tasks = getattr(state, "tasks", None) or []
    if not tasks:
        return True  # 非 stranded 竞态形态（无 pending tasks）→ 交还执行侧现状语义
    return any(getattr(t, "interrupts", None) for t in tasks)


async def _claim_and_execute(request_id: str, *, resume_mode: str, ttl_seconds: int) -> None:
    """行锁认领 → 终态判定 → 同源恢复执行；任何失败只落日志（后台任务不改 decide 语义）。"""
    from app.ops.hitl import get_hitl_store

    try:
        row = await get_hitl_store().aclaim_approved_for_resume(request_id, ttl_seconds=ttl_seconds)
    except Exception:
        logger.exception("HITL 自动恢复认领失败 request=%s（等补偿扫描下轮兜底）", request_id)
        return
    if row is None:
        logger.info("HITL 自动恢复认领未命中（并发被领/条件已变）request=%s", request_id)
        return
    _audit("hitl_auto_resume_claimed", row=row, resume_mode=resume_mode, ttl_seconds=ttl_seconds)
    run_id = str(row.get("run_id") or "")
    try:
        from app.ops.lg_rag.event_store import run_is_terminal

        if await run_is_terminal(run_id):
            logger.info("HITL 自动恢复跳过：run 已终态 run=%s request=%s", run_id, request_id)
            return
    except Exception:
        logger.exception("HITL 自动恢复：run 终态判定失败 fail-closed 跳过 run=%s", run_id)
        return
    if not await _interrupt_metadata_visible(row):
        # 认领竞态窗口（方向 A）：interrupt 元数据未就绪 → 不执行不报错，等下轮。
        # 认领不写状态（行锁随事务提交已释放）→ 无需回滚，扫描/补触发自然再认领。
        _audit(
            "hitl_auto_resume_deferred",
            row=row,
            resume_mode=resume_mode,
            ttl_seconds=ttl_seconds,
        )
        return
    try:
        from app.ops.hitl.router import _execute_decided_resume  # 惰性 import 防环

        await _execute_decided_resume(row)
    except Exception:
        # ResumeError 与意外异常同处置：后台任务只落日志，等扫描/TTL 兜底
        logger.exception("HITL 自动恢复执行失败 request=%s", request_id)


async def scan_approved_not_resumed_once(*, limit: int = 200) -> int:
    """补偿扫描一轮（FP-9 崩溃兜底）：补触发「已批准未恢复」单据，返回派发数。

    四条件（裁定四）：status=approved ∧ decided_at 未过 TTL ∧ run 无终态 ∧
    同 run 无未决 pending（第四条件=FP-11 不循环的扫描面配套：auto resume 后
    仍被拦必产新 pending → 跳过等人）。**不看 decide 来源**（N-1：OA 批准单
    在 auto 下由本扫描补触发 · 不即时≠不补）。逐条 fail-closed：单条异常跳过，
    不拖垮整轮。
    """
    from app.ops.hitl import get_hitl_store
    from app.ops.hitl.store import STATUS_APPROVED, STATUS_PENDING
    from app.ops.lg_rag.event_store import run_is_terminal

    store = get_hitl_store()
    ttl = _approval_ttl_seconds()
    rows = await store.alist(status=STATUS_APPROVED, limit=limit)
    if not rows:
        return 0
    pendings = await store.alist(status=STATUS_PENDING, limit=500)
    pending_run_ids = {str(r.get("run_id") or "") for r in pendings}
    dispatched = 0
    now = time.time()
    for row in rows:
        run_id = str(row.get("run_id") or "")
        decided_ts = _decided_at_ts(row.get("decided_at"))
        if decided_ts is None or now - decided_ts > ttl:
            continue
        if run_id in pending_run_ids:
            continue
        try:
            if await run_is_terminal(run_id):
                continue
        except Exception:
            logger.exception("HITL 补偿扫描：run 终态判定失败，本条跳过 run=%s", run_id)
            continue
        schedule_auto_resume(row, resume_mode=RESUME_MODE_INHERIT, source="scan")
        dispatched += 1
    return dispatched


def start_compensation_scanner() -> asyncio.Task:
    """启动补偿扫描周期任务：首轮立即执行（=启动时扫一次），随后按周期循环。

    任务句柄模块级管理（实操-D）；已存活时幂等复用。仅在 auto 模式下由
    lifespan 调用——manual 模式**零创建**（TestClient 8 文件 lifespan 面零 diff）。
    """
    global _SCAN_TASK
    if _SCAN_TASK is not None and not _SCAN_TASK.done():
        return _SCAN_TASK

    async def _loop() -> None:
        while True:
            try:
                await scan_approved_not_resumed_once()
            except asyncio.CancelledError:
                raise
            except Exception:
                logger.exception("HITL 自动恢复补偿扫描本轮失败（下周期重试）")
            await asyncio.sleep(scan_interval_seconds())

    _SCAN_TASK = asyncio.create_task(_loop())
    logger.info("HITL 自动恢复补偿扫描已启动 interval=%ss", scan_interval_seconds())
    return _SCAN_TASK


async def stop_compensation_scanner() -> None:
    """shutdown 纪律：cancel 周期任务并等待收尾（任务泄漏坑 · 实操-D）。"""
    global _SCAN_TASK
    task = _SCAN_TASK
    _SCAN_TASK = None
    if task is None:
        return
    task.cancel()
    import contextlib

    with contextlib.suppress(asyncio.CancelledError):
        await task
