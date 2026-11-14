"""lg-rag RunWorker：进程内 asyncio.Task 持有 astream，只 emit→event_store（+fanout）。

Wave B（task_lg_rag_sse_run_worker）：执行生命周期与 HTTP SSE 订阅解耦。
``run_id`` 单飞；断连只取消 subscriber，**不** cancel 本 worker。
MVP 进程内；多副本 DB 租约另立。
"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import AsyncIterator, Callable
from dataclasses import dataclass, field
from typing import Any

from app.llm.usage import reset_run_context, set_run_context
from app.ops.lg_rag.checkpointer import apostgres_saver, use_postgres_checkpointer
from app.ops.tenant_context import reset_current_tenant, set_current_tenant

logger = logging.getLogger(__name__)

# fanout 哨兵：worker 结束（含异常收尾）后通知所有订阅者
_BUS_END: Any = object()


@dataclass
class RunEventBus:
    """进程内 fanout：worker publish → 各 HTTP subscriber 队列。"""

    _queues: list[asyncio.Queue[Any]] = field(default_factory=list)
    _history: list[str] = field(default_factory=list)
    _closed: bool = False

    def subscribe(self) -> asyncio.Queue[Any]:
        q: asyncio.Queue[Any] = asyncio.Queue()
        for frame in self._history:
            q.put_nowait(frame)
        if self._closed:
            q.put_nowait(_BUS_END)
        else:
            self._queues.append(q)
        return q

    def unsubscribe(self, q: asyncio.Queue[Any]) -> None:
        with_context = q in self._queues
        if with_context:
            self._queues.remove(q)

    def publish(self, frame: str) -> None:
        if self._closed:
            return
        self._history.append(frame)
        for q in list(self._queues):
            q.put_nowait(frame)

    def close(self) -> None:
        if self._closed:
            return
        self._closed = True
        for q in list(self._queues):
            q.put_nowait(_BUS_END)
        self._queues.clear()


@dataclass
class _WorkerEntry:
    task: asyncio.Task[None]
    bus: RunEventBus


_workers: dict[str, _WorkerEntry] = {}


def bus_end_sentinel() -> Any:
    return _BUS_END


def get_run_bus(run_id: str) -> RunEventBus | None:
    entry = _workers.get(run_id)
    return entry.bus if entry else None


def is_run_worker_active(run_id: str) -> bool:
    entry = _workers.get(run_id)
    return entry is not None and not entry.task.done()


def get_run_worker_task(run_id: str) -> asyncio.Task[None] | None:
    entry = _workers.get(run_id)
    return entry.task if entry else None


def start_run_worker(
    *,
    query: str,
    mode: str,
    thread_id: str,
    run_id: str,
    astream_fn: Callable[..., AsyncIterator[dict[str, Any]]] | None = None,
    history_turns: list[dict] | None = None,
    user_id: str | None = None,
    checkpointer: Any | None = None,
    tenant_id: str | None = None,
) -> RunEventBus:
    """启动（或复用）``run_id`` 单飞 worker；返回 fanout bus。

    调用方须已分配 ``run_id``。同 ``run_id`` 已有未完成 task → 复用 bus（单飞）。
    """
    existing = _workers.get(run_id)
    if existing is not None and not existing.task.done():
        logger.info("lg-rag run_worker single-flight reuse run_id=%s", run_id)
        return existing.bus

    bus = RunEventBus()

    async def _main() -> None:
        tenant_token = None
        llm_token = None
        if tenant_id is not None:
            tenant_token = set_current_tenant(tenant_id)
        llm_token = set_run_context(run_id=run_id, surface="lg_rag")
        # P0' T4：run 一等实体建行（best-effort；单飞复用已建 → 幂等跳过；
        # 失败不阻断 run —— 状态缺失由 orphan 两段式扫描兜住）
        try:
            from app.ops.lg_rag.run_store import create_run

            await create_run(
                run_id=run_id,
                thread_id=thread_id,
                user_id=user_id,
                tenant_id=tenant_id,
            )
        except Exception:
            logger.exception("lg-rag run entity create failed run_id=%s", run_id)
        try:
            from app.ops.lg_rag.sse_stream import _iter_lg_rag_sse_core

            async def _pump(cp: Any) -> None:
                async for frame in _iter_lg_rag_sse_core(
                    query=query,
                    mode=mode,
                    thread_id=thread_id,
                    run_id=run_id,
                    astream_fn=astream_fn,
                    history_turns=history_turns,
                    user_id=user_id,
                    checkpointer=cp,
                ):
                    bus.publish(frame)

            if checkpointer is None and mode == "supervisor" and use_postgres_checkpointer():
                async with apostgres_saver(setup=True) as saver:
                    await _pump(saver)
            else:
                await _pump(checkpointer)
        except asyncio.CancelledError:
            logger.info("lg-rag run_worker cancelled run_id=%s", run_id)
            raise
        except Exception:
            logger.exception("lg-rag run_worker failed run_id=%s", run_id)
        finally:
            bus.close()
            if llm_token is not None:
                reset_run_context(llm_token)
            if tenant_token is not None:
                reset_current_tenant(tenant_token)

    task = asyncio.create_task(_main(), name=f"lg-rag-run-worker-{run_id}")
    _workers[run_id] = _WorkerEntry(task=task, bus=bus)

    def _on_done(t: asyncio.Task[None]) -> None:
        # 保留 bus 供晚到 subscribe 读 history；下次同 run_id 单飞复用前可覆盖
        # 不调度长 sleep GC（避免测试 teardown「Task was destroyed」噪点）
        del t

    task.add_done_callback(_on_done)
    logger.info("lg-rag run_worker started run_id=%s", run_id)
    return bus


# Wave A 薄补偿：worker 死/超时无终帧 → 补 done{disconnected}（F-A1 · 不赌 ASGI）
# 默认陈旧阈值（秒）；可用 env ``LG_RAG_ORPHAN_STALE_SECONDS`` 覆盖。
_ORPHAN_STALE_DEFAULT_S = 300.0


def _orphan_stale_seconds() -> float:
    import os

    raw = (os.environ.get("LG_RAG_ORPHAN_STALE_SECONDS") or "").strip()
    if not raw:
        return _ORPHAN_STALE_DEFAULT_S
    try:
        return max(0.0, float(raw))
    except ValueError:
        return _ORPHAN_STALE_DEFAULT_S


async def scan_orphan_runs_for_compensation(
    *,
    stale_after_seconds: float | None = None,
    limit: int = 50,
) -> int:
    """扫描 orphan run（无终帧且无活跃 worker）并补 ``done{status:disconnected}``。

    P0' T4 两段式：① 事件表有帧但 runs 无行 → 有界补行；② `ops_lg_rag_runs`
    主扫（status='running' + created_at 预筛 + per-run 末帧精确 stale）。
    使 ``run_stream_closed`` 真 → replay 不再永久 409。**不**依赖 ASGI disconnect。
    真在飞（``is_run_worker_active``）跳过。返回本轮补偿条数。
    """
    import time

    from app.ops.lg_rag.event_store import (
        persist_run_event,
        run_stream_closed,
    )
    from app.ops.lg_rag.run_store import (
        backfill_missing_run_rows,
        list_stale_running_runs,
    )

    stale = (
        _orphan_stale_seconds()
        if stale_after_seconds is None
        else max(0.0, float(stale_after_seconds))
    )
    backfilled = await backfill_missing_run_rows(limit=limit)
    if backfilled:
        logger.info("lg-rag orphan backfill run rows n=%s", backfilled)
    opens = await list_stale_running_runs(stale_after_seconds=int(stale), limit=limit)
    compensated = 0
    for row in opens:
        run_id = row["run_id"]
        if is_run_worker_active(run_id):
            continue
        if await run_stream_closed(run_id):
            continue
        next_seq = int(row.get("max_seq") or 0) + 1
        try:
            await persist_run_event(
                run_id=run_id,
                seq=next_seq,
                user_id=row["user_id"],
                thread_id=row["thread_id"],
                # ts_ms 列为 Integer(int32)；用相对单调秒内偏移，避免 epoch-ms 溢出
                ts_ms=int(time.time()) % 2_000_000_000,
                agent_role="system",
                event_type="done",
                payload={
                    "run_id": run_id,
                    "thread_id": row["thread_id"],
                    "status": "disconnected",
                },
            )
        except Exception:
            logger.exception("lg-rag orphan compensate persist failed run_id=%s", run_id)
            continue
        compensated += 1
        logger.info("lg-rag orphan compensated run_id=%s seq=%s", run_id, next_seq)
    return compensated
