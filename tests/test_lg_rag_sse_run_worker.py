"""Wave B · RunWorker + SSE 订阅解耦（task_lg_rag_sse_run_worker）。

TC-B1：订阅中途 aclose → worker 仍前进 → 普通 done → replay 含后半段。
TC-B2：worker 失败 → error{stage:lg_rag.worker_failed} → run_stream_closed。
TC-B3：continue_from_run_id 新 /stream · HITL resume 零调用 · replay 不调 LLM。
TC-B4：真在飞 refuse_in_flight → LgRagRunInFlightError（409 零 diff）。
TC-B5：orphan 无终帧 → scan 补 disconnected → run_stream_closed · 不再永久 409。
"""
from __future__ import annotations

import asyncio
import json
import uuid
from collections.abc import AsyncIterator
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import AsyncClient
from langchain_core.messages import AIMessage

from tests.conftest import DB_AVAILABLE

_DB_REQUIRED = pytest.mark.skipif(not DB_AVAILABLE, reason="requires PostgreSQL")
_STREAM = "/api/ops/lg-rag/stream"
_REPLAY = "/api/ops/lg-rag/replay"


def _parse_sse_events(frames: list[str]) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    for raw in frames:
        for block in raw.split("\n\n"):
            block = block.strip()
            if not block or block.startswith(":"):
                continue
            data_line = None
            for line in block.split("\n"):
                if line.startswith("data: "):
                    data_line = line[len("data: ") :]
            if data_line:
                events.append(json.loads(data_line))
    return events


@pytest.mark.asyncio
async def test_tc_b1_subscriber_aclose_worker_continues_to_done() -> None:
    """TC-B1：订阅 aclose 后 worker 仍跑完 → 普通 done（无 disconnected）。"""
    from app.ops.lg_rag.run_worker import (
        get_run_worker_task,
        is_run_worker_active,
        start_run_worker,
    )
    from app.ops.lg_rag.sse_subscribe import subscribe_run_sse

    run_id = f"b1-{uuid.uuid4().hex[:10]}"
    gate = asyncio.Event()
    persisted: list[dict[str, Any]] = []

    async def _capture(**kwargs: Any) -> None:
        persisted.append(dict(kwargs))

    async def _astream(
        query: str, *, thread_id: str = "t", **kw: Any
    ) -> AsyncIterator[dict[str, Any]]:
        yield {"intent_node": {"intent": {"domain": "kb", "needs_tool": False}}}
        await gate.wait()
        yield {
            "aggregator": {
                "messages": [AIMessage(content="后半段答案")]
            }
        }

    with (
        patch(
            "app.ops.lg_rag.event_store.persist_run_event",
            new=_capture,
        ),
        patch(
            "app.ops.lg_rag.sse_stream.persist_thread_turns",
            new_callable=AsyncMock,
        ),
    ):
        bus = start_run_worker(
            query="断连仍跑完",
            mode="supervisor",
            thread_id="th-b1",
            run_id=run_id,
            user_id="u-b1",
            astream_fn=_astream,
        )
        agen = subscribe_run_sse(run_id, bus=bus)
        saw_progress = False
        try:
            async for raw in agen:
                if "node.progress" in raw or "intent" in raw:
                    saw_progress = True
                    break
            assert saw_progress
        finally:
            await agen.aclose()

        assert is_run_worker_active(run_id), "断连后 worker 须仍在飞"
        gate.set()
        task = get_run_worker_task(run_id)
        assert task is not None
        await asyncio.wait_for(task, timeout=2.0)

    done_list = [p for p in persisted if p.get("event_type") == "done"]
    assert done_list, "worker 须落盘 done"
    assert done_list[-1].get("payload", {}).get("status") != "disconnected"
    assert any(
        p.get("event_type") == "answer"
        and (p.get("payload") or {}).get("content") == "后半段答案"
        for p in persisted
    )


@_DB_REQUIRED
@pytest.mark.asyncio
async def test_tc_b1_replay_after_disconnect_includes_tail(
    seeded_maintainer,
) -> None:
    """TC-B1 DB：断连订阅 → worker done → replay 200 含后半段 answer。"""
    from app.ops.lg_rag import event_store
    from app.ops.lg_rag.run_worker import (
        get_run_worker_task,
        start_run_worker,
    )
    from app.ops.lg_rag.sse_subscribe import subscribe_run_sse

    user_id = str(seeded_maintainer["user"].id)
    run_id = f"b1db-{uuid.uuid4().hex[:10]}"
    gate = asyncio.Event()
    after_seq = 0

    async def _astream(
        query: str, *, thread_id: str = "t", **kw: Any
    ) -> AsyncIterator[dict[str, Any]]:
        yield {"intent_node": {"intent": {"domain": "kb", "needs_tool": False}}}
        await gate.wait()
        yield {
            "aggregator": {
                "messages": [AIMessage(content="replay后半段")]
            }
        }

    with patch(
        "app.ops.lg_rag.sse_stream.persist_thread_turns",
        new_callable=AsyncMock,
    ):
        bus = start_run_worker(
            query="replay补后半",
            mode="supervisor",
            thread_id=f"th-{run_id}",
            run_id=run_id,
            user_id=user_id,
            astream_fn=_astream,
        )
        agen = subscribe_run_sse(run_id, bus=bus)
        try:
            async for raw in agen:
                for ev in _parse_sse_events([raw]):
                    after_seq = max(after_seq, int(ev.get("seq") or 0))
                    if ev.get("event_type") == "node.progress":
                        break
                else:
                    continue
                break
        finally:
            await agen.aclose()

        # 在飞时应 409
        with pytest.raises(event_store.LgRagRunInFlightError):
            await event_store.load_events_after(
                run_id, user_id, 0, refuse_in_flight=True
            )

        gate.set()
        task = get_run_worker_task(run_id)
        assert task is not None
        await asyncio.wait_for(task, timeout=3.0)
        await asyncio.sleep(0.05)

    events = await event_store.load_events_after(
        run_id, user_id, after_seq, refuse_in_flight=True
    )
    types = [e["event_type"] for e in events]
    assert "answer" in types
    assert "done" in types
    answer = next(e for e in events if e["event_type"] == "answer")
    assert (answer.get("payload") or {}).get("content") == "replay后半段"
    done = next(e for e in events if e["event_type"] == "done")
    assert (done.get("payload") or {}).get("status") != "disconnected"


@pytest.mark.asyncio
async def test_tc_b2_worker_failure_emits_worker_failed_stage() -> None:
    """TC-B2：astream 抛错 → error.stage == lg_rag.worker_failed。"""
    from app.ops.lg_rag.run_worker import get_run_worker_task, start_run_worker
    from app.ops.lg_rag.sse_subscribe import subscribe_run_sse

    run_id = f"b2-{uuid.uuid4().hex[:10]}"
    persisted: list[dict[str, Any]] = []

    async def _capture(**kwargs: Any) -> None:
        persisted.append(dict(kwargs))

    async def _boom(
        query: str, *, thread_id: str = "t", **kw: Any
    ) -> AsyncIterator[dict[str, Any]]:
        yield {"intent_node": {"intent": {"domain": "kb"}}}
        raise RuntimeError("injected worker failure")
        yield  # pragma: no cover

    with (
        patch(
            "app.ops.lg_rag.event_store.persist_run_event",
            new=_capture,
        ),
        patch(
            "app.ops.lg_rag.sse_stream.persist_thread_turns",
            new_callable=AsyncMock,
        ),
    ):
        bus = start_run_worker(
            query="失败",
            mode="supervisor",
            thread_id="th-b2",
            run_id=run_id,
            user_id="u-b2",
            astream_fn=_boom,
        )
        frames: list[str] = []
        async for raw in subscribe_run_sse(run_id, bus=bus):
            if not raw.startswith(":"):
                frames.append(raw)
        task = get_run_worker_task(run_id)
        if task is not None and not task.done():
            await asyncio.wait_for(task, timeout=2.0)

    errors = [p for p in persisted if p.get("event_type") == "error"]
    assert errors
    assert errors[-1].get("payload", {}).get("stage") == "lg_rag.worker_failed"


@_DB_REQUIRED
@pytest.mark.asyncio
async def test_tc_b4_in_flight_refuse_zero_diff(seeded_maintainer) -> None:
    """TC-B4：worker 仍写入中 → refuse_in_flight 抛 LgRagRunInFlightError。"""
    from app.ops.lg_rag import event_store
    from app.ops.lg_rag.run_worker import (
        get_run_worker_task,
        start_run_worker,
    )
    from app.ops.lg_rag.sse_subscribe import subscribe_run_sse

    user_id = str(seeded_maintainer["user"].id)
    run_id = f"b4-{uuid.uuid4().hex[:10]}"
    hang = asyncio.Event()

    async def _hang(
        query: str, *, thread_id: str = "t", **kw: Any
    ) -> AsyncIterator[dict[str, Any]]:
        yield {"intent_node": {"intent": {"domain": "kb"}}}
        await hang.wait()

    with patch(
        "app.ops.lg_rag.sse_stream.persist_thread_turns",
        new_callable=AsyncMock,
    ):
        bus = start_run_worker(
            query="在飞409",
            mode="supervisor",
            thread_id=f"th-{run_id}",
            run_id=run_id,
            user_id=user_id,
            astream_fn=_hang,
        )
        agen = subscribe_run_sse(run_id, bus=bus)
        try:
            async for raw in agen:
                if "node.progress" in raw:
                    break
            await asyncio.sleep(0.05)
            with pytest.raises(event_store.LgRagRunInFlightError):
                await event_store.load_events_after(
                    run_id, user_id, 0, refuse_in_flight=True
                )
        finally:
            await agen.aclose()
            # 结束 worker 防泄漏
            hang.set()
            task = get_run_worker_task(run_id)
            if task is not None:
                await asyncio.wait_for(task, timeout=2.0)


# ---------------------------------------------------------------------------
# TC-B3 · continue_from_run_id = 新 run · 零 HITL resume · replay ≠ LLM
# ---------------------------------------------------------------------------


@_DB_REQUIRED
@pytest.mark.asyncio
async def test_tc_b3_continue_from_new_stream_zero_resume(
    client: AsyncClient,
    seeded_maintainer,
) -> None:
    """TC-B3：带 continue_from_run_id 同 thread 新 /stream 绿；resume 零调用；
    replay 只读落盘帧、不触发新 LLM/astream。
    """
    from functools import wraps

    from app.main import app as fastapi_app
    from app.ops.deps import get_current_user
    from app.ops.lg_rag import event_store

    user = seeded_maintainer["user"]
    user_id = str(user.id)

    @wraps(get_current_user)
    async def _fake_user(*args: Any, **kwargs: Any):
        return user

    fastapi_app.dependency_overrides[get_current_user] = _fake_user
    try:
        old_run = f"b3old-{uuid.uuid4().hex[:10]}"
        thread_id = f"th-b3-{uuid.uuid4().hex[:8]}"
        partial = "半截草稿答案"
        # ts_ms 为 Integer(int32)；测例用小整数，勿用 epoch-ms
        await event_store.persist_run_event(
            run_id=old_run,
            seq=1,
            user_id=user_id,
            thread_id=thread_id,
            ts_ms=1,
            agent_role="system",
            event_type="run.start",
            payload={
                "run_id": old_run,
                "thread_id": thread_id,
                "mode": "supervisor",
            },
        )
        await event_store.persist_run_event(
            run_id=old_run,
            seq=2,
            user_id=user_id,
            thread_id=thread_id,
            ts_ms=2,
            agent_role="aggregator",
            event_type="answer",
            payload={"content": partial},
        )
        await event_store.persist_run_event(
            run_id=old_run,
            seq=3,
            user_id=user_id,
            thread_id=thread_id,
            ts_ms=3,
            agent_role="system",
            event_type="error",
            payload={"stage": "lg_rag.worker_failed", "message": "注入失败"},
        )

        captured_queries: list[str] = []
        llm_calls = {"n": 0}

        async def _astream(
            query: str, *, thread_id: str = "t", **kw: Any
        ) -> AsyncIterator[dict[str, Any]]:
            llm_calls["n"] += 1
            captured_queries.append(query)
            yield {
                "aggregator": {
                    "messages": [AIMessage(content="继续后的新答案")]
                }
            }

        resume_spy = MagicMock()

        with (
            patch(
                "app.ops.lg_rag.multi.graph.astream_supervisor_agent",
                new=_astream,
            ),
            patch(
                "app.ops.lg_rag.sse_stream.persist_thread_turns",
                new_callable=AsyncMock,
            ),
            patch(
                "app.ops.hitl.resume.resume_hitl_run",
                new=resume_spy,
            ),
            patch(
                "app.ops.hitl.router.resume_hitl_run",
                new=resume_spy,
            ),
        ):
            resp = await client.post(
                _STREAM,
                json={
                    "query": "请继续",
                    "thread_id": thread_id,
                    "continue_from_run_id": old_run,
                    "mode": "supervisor",
                },
            )
            assert resp.status_code == 200, resp.text
            new_run = resp.headers.get("X-Ops-Lg-Rag-Run-Id") or ""
            assert new_run and new_run != old_run
            assert resp.headers.get("X-Ops-Lg-Rag-Thread-Id") == thread_id
            assert captured_queries, "新 stream 须调 astream"
            assert partial in captured_queries[0]
            assert (
                "继续回复" in captured_queries[0]
                or "既有草稿" in captured_queries[0]
            )
            assert llm_calls["n"] >= 1
            assert resume_spy.call_count == 0

            # replay 旧失败 run：只读落盘，不得再调 astream / resume
            llm_before_replay = llm_calls["n"]
            replay = await client.post(
                _REPLAY, json={"run_id": old_run, "after_seq": 0}
            )
            assert replay.status_code == 200, replay.text
            assert llm_calls["n"] == llm_before_replay, "replay 不得触发新 LLM"
            assert resume_spy.call_count == 0
            body = replay.text
            assert "lg_rag.worker_failed" in body or "error" in body
    finally:
        fastapi_app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# TC-B5 · orphan 补偿扫描（红测先行语义：无终帧→scan→closed→replay 200）
# ---------------------------------------------------------------------------


@_DB_REQUIRED
@pytest.mark.asyncio
async def test_tc_b5_orphan_scan_compensates_terminal_clears_409(
    seeded_maintainer,
) -> None:
    """TC-B5：模拟 worker 死掉无终帧 → scan 补 disconnected → closed 真 →
    refuse_in_flight 不再 409。不依赖 ASGI disconnect。
    """
    from app.ops.lg_rag import event_store
    from app.ops.lg_rag.run_worker import (
        is_run_worker_active,
        scan_orphan_runs_for_compensation,
    )

    user_id = str(seeded_maintainer["user"].id)
    run_id = f"b5orp-{uuid.uuid4().hex[:10]}"
    thread_id = f"th-b5-{uuid.uuid4().hex[:8]}"
    await event_store.persist_run_event(
        run_id=run_id,
        seq=1,
        user_id=user_id,
        thread_id=thread_id,
        ts_ms=10,
        agent_role="system",
        event_type="run.start",
        payload={"run_id": run_id, "thread_id": thread_id},
    )
    await event_store.persist_run_event(
        run_id=run_id,
        seq=2,
        user_id=user_id,
        thread_id=thread_id,
        ts_ms=11,
        agent_role="aggregator",
        event_type="answer",
        payload={"content": "半截"},
    )

    assert await event_store.run_stream_closed(run_id) is False
    assert not is_run_worker_active(run_id)
    with pytest.raises(event_store.LgRagRunInFlightError):
        await event_store.load_events_after(
            run_id, user_id, 0, refuse_in_flight=True
        )

    n = await scan_orphan_runs_for_compensation(
        stale_after_seconds=0, limit=200
    )
    assert n >= 1

    assert await event_store.run_stream_closed(run_id) is True
    events = await event_store.load_events_after(
        run_id, user_id, 0, refuse_in_flight=True
    )
    types = [e["event_type"] for e in events]
    assert "done" in types
    done = next(e for e in events if e["event_type"] == "done")
    assert (done.get("payload") or {}).get("status") == "disconnected"

    # 幂等：已 closed 的 orphan 不再重复补偿
    n2 = await scan_orphan_runs_for_compensation(
        stale_after_seconds=0, limit=200
    )
    # 本 run 不应再被计入；允许扫描到其它测试孤儿
    events2 = await event_store.load_events_after(
        run_id, user_id, 0, refuse_in_flight=True
    )
    done_count = sum(1 for e in events2 if e["event_type"] == "done")
    assert done_count == 1
    del n2  # 他测孤儿可并存；本 run 终帧唯一即够


@_DB_REQUIRED
@pytest.mark.asyncio
async def test_tc_b5_active_worker_not_compensated(seeded_maintainer) -> None:
    """TC-B5 反例：真在飞 worker 不得被 orphan 扫描误伤。"""
    from app.ops.lg_rag import event_store
    from app.ops.lg_rag.run_worker import (
        get_run_worker_task,
        is_run_worker_active,
        scan_orphan_runs_for_compensation,
        start_run_worker,
    )
    from app.ops.lg_rag.sse_subscribe import subscribe_run_sse

    user_id = str(seeded_maintainer["user"].id)
    run_id = f"b5act-{uuid.uuid4().hex[:10]}"
    hang = asyncio.Event()

    async def _hang(
        query: str, *, thread_id: str = "t", **kw: Any
    ) -> AsyncIterator[dict[str, Any]]:
        yield {"intent_node": {"intent": {"domain": "kb"}}}
        await hang.wait()

    with patch(
        "app.ops.lg_rag.sse_stream.persist_thread_turns",
        new_callable=AsyncMock,
    ):
        bus = start_run_worker(
            query="真在飞勿补偿",
            mode="supervisor",
            thread_id=f"th-{run_id}",
            run_id=run_id,
            user_id=user_id,
            astream_fn=_hang,
        )
        agen = subscribe_run_sse(run_id, bus=bus)
        try:
            async for raw in agen:
                if "node.progress" in raw:
                    break
            await asyncio.sleep(0.05)
            assert is_run_worker_active(run_id)
            assert await event_store.run_stream_closed(run_id) is False
            await scan_orphan_runs_for_compensation(
                stale_after_seconds=0, limit=200
            )
            assert await event_store.run_stream_closed(run_id) is False
            with pytest.raises(event_store.LgRagRunInFlightError):
                await event_store.load_events_after(
                    run_id, user_id, 0, refuse_in_flight=True
                )
        finally:
            await agen.aclose()
            hang.set()
            task = get_run_worker_task(run_id)
            if task is not None:
                await asyncio.wait_for(task, timeout=2.0)
