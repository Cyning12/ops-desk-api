"""lg-rag replay 恢复段在写窗 409 + follow live-tail（task_lg_rag_replay_resume_ux_opt · F1/F2）。

红测先行（F3）：修复前 RED 签名 = AttributeError（event_store 尚无
run_resume_in_progress / LgRagRunResumeInProgressError，router 尚无
_iter_replay_follow_sse），承 tests/test_lg_rag_sse_resume.py:214 先例；
修复后 GREEN，时序 git 可查。

覆盖验收：TC1 谓词矩阵（a/b/c/d）· TC2 replay 409 语义化 + 再挂起零 diff ·
TC3 follow 帧序/keepalive/收尾/帧形状逐字节同构 · TC4 上限零伪造帧 + 断连零残留 ·
follow=true 在写窗不返 409 · follow=false 字面零 diff。
"""

from __future__ import annotations

import asyncio
import json
import uuid
from datetime import timedelta
from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient
from sqlalchemy import update

from app.db.models import OpsLgRagRunEvent, now_utc
from app.db.session import AsyncSessionLocal
from app.ops.lg_rag.sse_replay import format_sse_event
from tests.conftest import DB_AVAILABLE

_REPLAY = "/api/ops/lg-rag/replay"

_DB_REQUIRED = pytest.mark.skipif(not DB_AVAILABLE, reason="需要本地 PG（opsdesk_test）真跑事件表")

_SSE_EVENT_KEYS = {"run_id", "seq", "ts_ms", "agent_role", "event_type", "payload", "cursor"}

_IN_FLIGHT_409_DETAIL = "Run is still in flight; retry after it settles."


def _parse_sse(body: str) -> list[dict]:
    events: list[dict] = []
    for block in body.split("\n\n"):
        block = block.strip()
        if not block:
            continue
        data_line = None
        for line in block.split("\n"):
            if line.startswith("data: "):
                data_line = line[len("data: ") :]
        if data_line:
            events.append(json.loads(data_line))
    return events


def _frame(run_id: str, seq: int, event_type: str, payload: dict) -> dict:
    return format_sse_event(
        {
            "run_id": run_id,
            "seq": seq,
            "ts_ms": seq * 10,
            "agent_role": "system",
            "event_type": event_type,
            "payload": payload,
        }
    )


def _expected_sse_frame(ev: dict) -> str:
    """与 router event_gen 体例（router.py 既有行）逐字节同构的期望值。"""
    return f"event: {ev['event_type']}\ndata: {json.dumps(ev, ensure_ascii=False)}\n\n"


async def _persist_frame(
    run_id: str, seq: int, user_id: str, event_type: str, payload: dict
) -> None:
    from app.ops.lg_rag import event_store

    await event_store.persist_run_event(
        run_id=run_id,
        seq=seq,
        user_id=user_id,
        thread_id=f"th-{run_id}",
        ts_ms=seq * 10,
        agent_role="system",
        event_type=event_type,
        payload=payload,
    )


async def _seed_resume_window(run_id: str, user_id: str) -> None:
    """形态 (a)：挂起 done{waiting_approval}@2 后 hitl.resumed@3 且无新收尾帧。"""
    await _persist_frame(run_id, 1, user_id, "run.start", {"status": "started"})
    await _persist_frame(run_id, 2, user_id, "done", {"status": "waiting_approval"})
    await _persist_frame(run_id, 3, user_id, "hitl.resumed", {"mode": "resume"})


# ---------------------------------------------------------------------------
# TC1 · 谓词矩阵（事件表真源 · 修复前 RED：AttributeError 谓词不存在）
# ---------------------------------------------------------------------------


@_DB_REQUIRED
async def test_run_resume_in_progress_matrix(seeded_maintainer) -> None:
    from app.ops.lg_rag import event_store

    user_id = str(seeded_maintainer["user"].id)

    # (a) 恢复段在写窗 ⇒ 真
    run_a = f"resume-inflight-{uuid.uuid4().hex[:8]}"
    await _seed_resume_window(run_a, user_id)
    assert await event_store.run_resume_in_progress(run_a) is True

    # (b) 纯挂起（无 hitl.resumed）⇒ 假（挂起 replay 合法零 diff · FP-4）
    run_b = f"suspended-{uuid.uuid4().hex[:8]}"
    await _persist_frame(run_b, 1, user_id, "run.start", {"status": "started"})
    await _persist_frame(run_b, 2, user_id, "done", {"status": "waiting_approval"})
    assert await event_store.run_resume_in_progress(run_b) is False

    # (c1) hitl.resumed 后 done{resumed} ⇒ 假（沉降）
    run_c1 = f"resumed-done-{uuid.uuid4().hex[:8]}"
    await _seed_resume_window(run_c1, user_id)
    await _persist_frame(run_c1, 4, user_id, "answer", {"content": "好", "final": True})
    await _persist_frame(run_c1, 5, user_id, "done", {"status": "resumed", "latency_ms": 100})
    assert await event_store.run_resume_in_progress(run_c1) is False

    # (c2) hitl.resumed 后新 done{waiting_approval} ⇒ 假（再挂起 · FP-4/FP-7）
    run_c2 = f"resuspended-{uuid.uuid4().hex[:8]}"
    await _seed_resume_window(run_c2, user_id)
    await _persist_frame(run_c2, 4, user_id, "done", {"status": "waiting_approval"})
    assert await event_store.run_resume_in_progress(run_c2) is False

    # (c3) hitl.resumed 后 error ⇒ 假（恢复段失败收尾）
    run_c3 = f"resumed-error-{uuid.uuid4().hex[:8]}"
    await _seed_resume_window(run_c3, user_id)
    await _persist_frame(run_c3, 4, user_id, "error", {"stage": "lg_rag.worker_failed"})
    assert await event_store.run_resume_in_progress(run_c3) is False

    # 首段在飞（有帧无收尾帧、无 hitl.resumed）⇒ 假（在飞走既有 409 语义 · 四态互斥）
    run_d = f"inflight-{uuid.uuid4().hex[:8]}"
    await _persist_frame(run_d, 1, user_id, "run.start", {"status": "started"})
    assert await event_store.run_resume_in_progress(run_d) is False

    # 空 run_id / 未知 run ⇒ 假
    assert await event_store.run_resume_in_progress("") is False
    assert await event_store.run_resume_in_progress(f"unknown-{uuid.uuid4().hex[:8]}") is False


@_DB_REQUIRED
async def test_run_resume_in_progress_stale_relaxes(seeded_maintainer) -> None:
    """(d) stale 超阈 ⇒ 假（FP-1：恢复段崩溃在写窗不永久 409，回落 200 + error 日志）。

    阈值口径：末帧 created_at 超阈视为已沉降；stale_after_seconds 显式传参覆盖
    env 默认（<=0 关闭 stale 判定 · 承 scan_orphan_runs_for_compensation 先例）。
    """
    from app.ops.lg_rag import event_store

    user_id = str(seeded_maintainer["user"].id)
    run_id = f"resume-stale-{uuid.uuid4().hex[:8]}"
    await _seed_resume_window(run_id, user_id)
    assert await event_store.run_resume_in_progress(run_id) is True

    # 回拨全部帧 created_at 超阈 ⇒ 谓词回落 False
    async with AsyncSessionLocal() as db:
        await db.execute(
            update(OpsLgRagRunEvent)
            .where(OpsLgRagRunEvent.run_id == run_id)
            .values(created_at=now_utc() - timedelta(seconds=7200))
        )
        await db.commit()
    assert await event_store.run_resume_in_progress(run_id) is False

    # 显式形参：阈内 ⇒ 真；超阈 ⇒ 假；<=0 关闭 stale 判定 ⇒ 真
    run_p = f"resume-param-{uuid.uuid4().hex[:8]}"
    await _seed_resume_window(run_p, user_id)
    assert await event_store.run_resume_in_progress(run_p, stale_after_seconds=3600.0) is True
    async with AsyncSessionLocal() as db:
        await db.execute(
            update(OpsLgRagRunEvent)
            .where(OpsLgRagRunEvent.run_id == run_p)
            .values(created_at=now_utc() - timedelta(seconds=30))
        )
        await db.commit()
    assert await event_store.run_resume_in_progress(run_p, stale_after_seconds=10.0) is False
    assert await event_store.run_resume_in_progress(run_p, stale_after_seconds=0.0) is True


# ---------------------------------------------------------------------------
# TC2 · replay 409 语义化（detail 与首段在飞可区分 · 三态零 diff）
# ---------------------------------------------------------------------------


async def test_replay_resume_in_progress_409_distinguishable(
    client: AsyncClient, override_auth_maintainer
) -> None:
    """恢复段在写窗 replay（follow 缺省）⇒ 409 + Retry-After 正整数 + detail 可区分。

    修复前 RED 签名：event_store 尚无 LgRagRunResumeInProgressError（AttributeError），
    承 test_lg_rag_sse_resume.py:214 先例；修复后若漏映射则冒穿路由成裸 500。
    """
    from app.ops.lg_rag import event_store

    with patch(
        "app.ops.lg_rag.router.load_events_after",
        new_callable=AsyncMock,
        side_effect=event_store.LgRagRunResumeInProgressError,
    ):
        response = await client.post(_REPLAY, json={"run_id": "run-resume", "after_seq": 0})
    assert response.status_code == 409
    retry_after = response.headers.get("Retry-After")
    assert retry_after is not None, "409 必须带 Retry-After 供客户端退避"
    assert retry_after.isdigit() and int(retry_after) > 0
    detail = response.json()["detail"]
    assert detail != _IN_FLIGHT_409_DETAIL, "恢复段 409 detail 须与首段在飞 409 可区分"
    assert "Resume" in detail


@_DB_REQUIRED
async def test_load_events_refuses_resume_in_progress(seeded_maintainer) -> None:
    """形态 (a) 下 load_events_after(refuse_in_flight=True) 抛 LgRagRunResumeInProgressError；

    缺省 False（follow 轮询/其余调用面）照常返回帧——follow 等待语义的存储层锚点。
    """
    from app.ops.lg_rag import event_store

    user_id = str(seeded_maintainer["user"].id)
    run_id = f"resume-gate-{uuid.uuid4().hex[:8]}"
    await _seed_resume_window(run_id, user_id)

    with pytest.raises(event_store.LgRagRunResumeInProgressError):
        await event_store.load_events_after(run_id, user_id, 0, refuse_in_flight=True)

    events = await event_store.load_events_after(run_id, user_id, 0)
    assert [e["seq"] for e in events] == [1, 2, 3]


@_DB_REQUIRED
async def test_load_events_resuspended_replays_normally(seeded_maintainer) -> None:
    """再挂起（hitl.resumed 后新 done{waiting_approval}）⇒ refuse_in_flight=True 照常返回（FP-4 钉）。"""
    from app.ops.lg_rag import event_store

    user_id = str(seeded_maintainer["user"].id)
    run_id = f"resuspended-replay-{uuid.uuid4().hex[:8]}"
    await _seed_resume_window(run_id, user_id)
    await _persist_frame(run_id, 4, user_id, "done", {"status": "waiting_approval"})

    events = await event_store.load_events_after(run_id, user_id, 0, refuse_in_flight=True)
    assert [e["seq"] for e in events] == [1, 2, 3, 4]


# ---------------------------------------------------------------------------
# TC3 · follow 帧序契约（生成器级快路径 + HTTP 级接线）
# ---------------------------------------------------------------------------


def _collect_follow_frames(frames: list[str]) -> tuple[list[str], list[str]]:
    data_frames = [f for f in frames if f.startswith("event: ")]
    comments = [f for f in frames if f.startswith(": ")]
    return data_frames, comments


async def test_follow_generator_frame_order_keepalive_and_close() -> None:
    """follow=true 自 cursor 起：推存量 → 挂起期 keepalive comment（不进 data）→
    恢复段新帧按 seq 序追加 → 见 seq>after_seq 新收尾帧推出后流结束。
    全部 data 帧与 format_sse_event + event_gen 体例逐字节同构（freeze 帧形状零 diff）。
    """
    from app.ops.lg_rag import router as lg_router

    ev5 = _frame("run-f", 5, "hitl.resumed", {"mode": "resume"})
    ev6 = _frame("run-f", 6, "node.progress", {"node": "observe"})
    ev7 = _frame("run-f", 7, "answer", {"content": "好", "final": True})
    ev8 = _frame("run-f", 8, "done", {"status": "resumed", "latency_ms": 100})
    poll_batches: list[list[dict]] = [[], [], [ev6, ev7], [ev8]]
    poll_calls: list[tuple[int, bool]] = []

    async def fake_load(run_id, user_id, after_seq, *, refuse_in_flight=False):
        poll_calls.append((after_seq, refuse_in_flight))
        return poll_batches.pop(0) if poll_batches else []

    frames: list[str] = []
    with patch.object(lg_router, "load_events_after", new=fake_load):
        async for frame in lg_router._iter_replay_follow_sse(
            run_id="run-f",
            user_id="u1",
            after_seq=4,
            initial_events=[ev5],
            poll_seconds=0.01,
            keepalive_interval_s=0.015,
            max_seconds=5.0,
        ):
            frames.append(frame)

    data_frames, comments = _collect_follow_frames(frames)
    # 帧序：存量 hitl.resumed → 增量按 seq → 收尾帧 done 后流结束
    assert data_frames == [_expected_sse_frame(ev) for ev in [ev5, ev6, ev7, ev8]]
    parsed = [json.loads(f.split("\ndata: ", 1)[1].rstrip("\n")) for f in data_frames]
    assert [e["seq"] for e in parsed] == [5, 6, 7, 8]
    assert parsed[-1]["event_type"] == "done"
    for ev in parsed:
        assert set(ev.keys()) == _SSE_EVENT_KEYS, "帧 data 形状 = format_sse_event 七键（freeze lg-rag-sse-v1）"
    # keepalive：挂起期 SSE comment，不进 data
    assert comments, "挂起轮询期必须发 keepalive comment 防 idle 掐断（FP-2）"
    assert all(c == ": keepalive\n\n" for c in comments)
    # 轮询真源=load_events_after 且 refuse_in_flight 恒 False（follow=等待语义）；cursor 单调推进。
    # 4 次轮询：两次空批（seq 停 5）→ 增量批 [ev6, ev7]（seq 停 5 拉取、推完进 7）→ 收尾批 [ev8]（seq 7 拉取）。
    assert poll_calls == [(5, False), (5, False), (5, False), (7, False)]


async def test_follow_generator_settled_initial_batch_closes_immediately() -> None:
    """初始存量批已含收尾帧（沉降 run follow=true）⇒ 推完即结束，零轮询。"""
    from app.ops.lg_rag import router as lg_router

    ev5 = _frame("run-s", 5, "done", {"status": "resumed", "latency_ms": 100})

    async def fake_load(*_args, **_kwargs):  # pragma: no cover - 被调用即失败
        raise AssertionError("沉降初始批不得触发轮询")

    frames: list[str] = []
    with patch.object(lg_router, "load_events_after", new=fake_load):
        async for frame in lg_router._iter_replay_follow_sse(
            run_id="run-s",
            user_id="u1",
            after_seq=4,
            initial_events=[ev5],
            poll_seconds=0.01,
            keepalive_interval_s=0.015,
            max_seconds=5.0,
        ):
            frames.append(frame)
    assert frames == [_expected_sse_frame(ev5)]


async def test_follow_generator_resuspended_done_closes() -> None:
    """follow 期间 run 再挂起（新 done{waiting_approval}）⇒ 收尾帧即流结束条件（FP-7）。"""
    from app.ops.lg_rag import router as lg_router

    ev5 = _frame("run-rs", 5, "done", {"status": "waiting_approval"})

    async def fake_load(run_id, user_id, after_seq, *, refuse_in_flight=False):
        return [ev5]

    frames: list[str] = []
    with patch.object(lg_router, "load_events_after", new=fake_load):
        async for frame in lg_router._iter_replay_follow_sse(
            run_id="run-rs",
            user_id="u1",
            after_seq=4,
            initial_events=[],
            poll_seconds=0.01,
            keepalive_interval_s=60.0,
            max_seconds=5.0,
        ):
            frames.append(frame)
    assert frames == [_expected_sse_frame(ev5)]


async def test_replay_follow_true_http_streams_settled_run(
    client: AsyncClient, override_auth_maintainer
) -> None:
    """HTTP 级接线：follow=true 沉降 run ⇒ 200 SSE 立即推存量收尾，轮询以 refuse_in_flight=False。"""
    stored = [
        _frame("run-http", 5, "hitl.resumed", {"mode": "resume"}),
        _frame("run-http", 6, "done", {"status": "resumed", "latency_ms": 100}),
    ]
    with patch(
        "app.ops.lg_rag.router.load_events_after",
        new_callable=AsyncMock,
        return_value=stored,
    ) as mock_load:
        response = await client.post(_REPLAY, json={"cursor": "run-http:4", "follow": True})
    assert response.status_code == 200
    assert "text/event-stream" in response.headers["content-type"]
    assert mock_load.await_args.kwargs["refuse_in_flight"] is False
    events = _parse_sse(response.text)
    assert [e["seq"] for e in events] == [5, 6]
    assert events[-1]["event_type"] == "done"


async def test_replay_follow_true_no_409_in_resume_window(
    client: AsyncClient, override_auth_maintainer, monkeypatch
) -> None:
    """follow=true 在恢复段在写窗不返 409（等待语义存续 · TC4 验收项）：存量无收尾帧时
    挂起轮询直至新收尾帧推出后收尾。"""
    monkeypatch.setenv("LG_RAG_REPLAY_FOLLOW_POLL_SECONDS", "1")
    batches = [
        [_frame("run-w", 5, "hitl.resumed", {"mode": "resume"})],
        [_frame("run-w", 6, "done", {"status": "resumed", "latency_ms": 100})],
    ]

    async def fake_load(run_id, user_id, after_seq, *, refuse_in_flight=False):
        return batches.pop(0) if batches else []

    with patch("app.ops.lg_rag.router.load_events_after", new=fake_load):
        response = await client.post(_REPLAY, json={"cursor": "run-w:4", "follow": True})
    assert response.status_code == 200
    events = _parse_sse(response.text)
    assert [e["seq"] for e in events] == [5, 6]
    assert events[-1]["event_type"] == "done"


async def test_replay_follow_default_false_byte_zero_diff(
    client: AsyncClient, override_auth_maintainer
) -> None:
    """follow 缺省 false 字面零 diff：帧字节与既有 event_gen 体例一致，闸仍 refuse_in_flight=True。"""
    stored = [
        _frame("run-x", 2, "answer", {"content": "hi"}),
        _frame("run-x", 3, "done", {"status": "completed"}),
    ]
    with patch(
        "app.ops.lg_rag.router.load_events_after",
        new_callable=AsyncMock,
        return_value=stored,
    ) as mock_load:
        response = await client.post(_REPLAY, json={"run_id": "run-x", "after_seq": 1})
    assert response.status_code == 200
    assert mock_load.await_args.kwargs["refuse_in_flight"] is True
    expected = "".join(_expected_sse_frame(ev) for ev in stored)
    assert response.text == expected, "follow=false 响应字节须与 master 同输入零 diff"
    events = _parse_sse(response.text)
    assert [e["seq"] for e in events] == [2, 3]


# ---------------------------------------------------------------------------
# TC4 · follow 上限与断连（禁伪造帧 · 零残留）
# ---------------------------------------------------------------------------


async def test_follow_generator_max_duration_no_fabricated_frame() -> None:
    """总时长上限到点未收尾 ⇒ 流自然结束且零伪造帧（末帧永远来自事件表 · FP-3）。"""
    from app.ops.lg_rag import router as lg_router

    poll_count = 0

    async def fake_load(run_id, user_id, after_seq, *, refuse_in_flight=False):
        nonlocal poll_count
        poll_count += 1
        return []

    frames: list[str] = []
    with patch.object(lg_router, "load_events_after", new=fake_load):
        async for frame in lg_router._iter_replay_follow_sse(
            run_id="run-cap",
            user_id="u1",
            after_seq=4,
            initial_events=[],
            poll_seconds=0.01,
            keepalive_interval_s=3600.0,  # 禁 keepalive 干扰：本例只断言零帧
            max_seconds=0.05,
        ):
            frames.append(frame)
    assert poll_count >= 1, "上限前须真实轮询过事件表"
    assert frames == [], "上限到点禁伪造 done/error/任何帧（FP-3）"


async def test_follow_generator_disconnect_no_residue() -> None:
    """客户端断连 ⇒ 仅取消本 follow 循环：无副作用、无后台任务残留（TC4 机断）。"""
    from app.ops.lg_rag import router as lg_router

    async def fake_load(run_id, user_id, after_seq, *, refuse_in_flight=False):
        return []

    tasks_before = set(asyncio.all_tasks())
    with patch.object(lg_router, "load_events_after", new=fake_load):
        gen = lg_router._iter_replay_follow_sse(
            run_id="run-disc",
            user_id="u1",
            after_seq=4,
            initial_events=[],
            poll_seconds=0.01,
            keepalive_interval_s=0.005,
            max_seconds=60.0,
        )
        first = await gen.__anext__()
        assert first == ": keepalive\n\n", "断连前挂起期应先发 keepalive comment"
        await gen.aclose()  # 模拟客户端断连：关闭生成器
        with pytest.raises(StopAsyncIteration):
            await gen.__anext__()
    await asyncio.sleep(0.05)
    tasks_after = set(asyncio.all_tasks())
    assert tasks_after <= tasks_before, "follow 循环不得残留后台任务"
