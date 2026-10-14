"""Wave A 史实单测 → Wave B 语义对齐（task_lg_rag_sse_run_worker）。

旧 Wave A 期望「aclose → done{disconnected} + cancel 执行」已停赌。
本文件保留文件名以免孤儿引用；断言改为 B：订阅 aclose 不杀 worker。
完整 TC-B1/B2/B4 见 ``test_lg_rag_sse_run_worker.py``。
旧 task ``task_lg_rag_sse_disconnect_completion.md`` 正文**不修订**。
"""
from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from typing import Any
from unittest.mock import AsyncMock, patch

import pytest

from app.ops.lg_rag.run_worker import is_run_worker_active


async def _hanging_astream(
    query: str, *, thread_id: str = "t", **_kwargs: Any
) -> AsyncIterator[dict[str, Any]]:
    yield {"intent_node": {"intent": {"domain": "kb", "needs_tool": False}}}
    await asyncio.Event().wait()


@pytest.mark.asyncio
async def test_subscriber_aclose_does_not_kill_worker() -> None:
    """B 语义：iter/subscribe aclose 后 worker 仍 active（对照旧 A 杀执行）。"""
    from app.ops.lg_rag.sse_stream import iter_lg_rag_sse

    run_id = "disc-b-aclose"
    persisted: list[dict[str, Any]] = []

    async def _capture_persist(**kwargs: Any) -> None:
        persisted.append(dict(kwargs))

    agen = iter_lg_rag_sse(
        query="断连不杀 worker",
        mode="supervisor",
        thread_id="th-disconnect-b",
        run_id=run_id,
        user_id="u-disconnect-b",
        astream_fn=_hanging_astream,
    )
    with (
        patch(
            "app.ops.lg_rag.event_store.persist_run_event",
            new=_capture_persist,
        ),
        patch(
            "app.ops.lg_rag.sse_stream.persist_thread_turns",
            new_callable=AsyncMock,
        ),
    ):
        saw_progress = False
        try:
            async for raw in agen:
                if "node.progress" in raw or "intent" in raw:
                    saw_progress = True
                    break
            assert saw_progress
        finally:
            await agen.aclose()
        await asyncio.sleep(0.05)

    assert is_run_worker_active(run_id)
    # 订阅断连不得强制落盘 disconnected（worker 仍在飞）
    done_list = [p for p in persisted if p.get("event_type") == "done"]
    assert not any(
        (p.get("payload") or {}).get("status") == "disconnected"
        for p in done_list
    )
    # 收尾挂起的 worker，避免泄漏
    task = __import__(
        "app.ops.lg_rag.run_worker", fromlist=["get_run_worker_task"]
    ).get_run_worker_task(run_id)
    if task is not None and not task.done():
        task.cancel()
        with __import__("contextlib").suppress(asyncio.CancelledError):
            await task
