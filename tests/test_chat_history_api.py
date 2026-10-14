"""chat-history-api（B1）· 会话历史只读 API 测试。

覆盖 task 验收 14 条全部可机断项：
- H1 列表字段族 / waiting_approval 识别 / last_activity_at 倒序
- H1 分页：默认 20 · limit>100 → 422 · cursor 不重不漏
- H2 完整重建（query + answer + subtasks + done.status + hitl.waiting）· run 升序 · 帧 seq 序
- answer 聚合：终帧优先 / delta 回退 / 32000 截断标 answer_truncated（N3）
- 跨用户/未知 thread → 404（不 403）；未登录 → 401；thread_id 超长 → 422
- 缺 query 老 run 标题降级不阻塞（FP-4）
- 聚合超时常量可注入 → 504（FP-2）
- SSE 对拍：run.start 仅多可选 query 键 · 零新 event_type（裁定 A1 · freeze lg-rag-sse-v1）

DB 用例造 ``ops_lg_rag_run_events`` 行（不连真 LLM）；聚合层为纯函数直测。
"""
from __future__ import annotations

import asyncio
import json
import uuid
from collections.abc import AsyncIterator
from datetime import datetime, timedelta
from typing import Any
from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient
from langchain_core.messages import AIMessage
from sqlalchemy import delete

from app.db.models import OpsLgRagRunEvent, OpsUser
from app.db.session import AsyncSessionLocal
from app.ops.lg_rag import history
from app.ops.lg_rag.history import (
    ANSWER_MAX_CHARS,
    TITLE_MAX_CHARS,
    HistoryCursorError,
)
from tests.conftest import DB_AVAILABLE

_DB_SKIP = pytest.mark.skipif(not DB_AVAILABLE, reason="PostgreSQL not available")

_THREADS = "/api/ops/chat/threads"
_HISTORY = "/api/ops/chat/threads/{tid}/history"
_STREAM = "/api/ops/lg-rag/stream"

# conftest override_auth_maintainer / override_auth_viewer 固定 id
MAINTAINER_ID = "00000000-0000-0000-0000-000000000001"
VIEWER_ID = "00000000-0000-0000-0000-000000000002"

_BASE_TS = datetime(2026, 9, 30, 12, 0, 0)

# freeze lg-rag-sse-v1 事件类型全集（对拍用：新增 event_type 会在此被捕）
_FREEZE_EVENT_TYPES = {
    "run.start",
    "node.progress",
    "subtask.progress",
    "answer",
    "hitl.waiting",
    "done",
    "error",
}


def _ev(
    run_id: str,
    seq: int,
    user_id: str,
    thread_id: str,
    event_type: str,
    payload: dict[str, Any],
    created_at: datetime,
    *,
    role: str = "system",
) -> OpsLgRagRunEvent:
    return OpsLgRagRunEvent(
        run_id=run_id,
        seq=seq,
        user_id=user_id,
        thread_id=thread_id,
        # ts_ms 列为 int32：run 内相对毫秒即可，不能塞 epoch ms
        ts_ms=int((created_at - _BASE_TS).total_seconds() * 1000),
        agent_role=role,
        event_type=event_type,
        payload=payload,
        created_at=created_at,
    )


def _row(
    run_id: str,
    seq: int,
    event_type: str,
    payload: dict[str, Any],
    created_at: datetime,
    *,
    role: str = "system",
) -> dict[str, Any]:
    """纯函数层事件行 dict（与 event_store.fetch_events_for_threads 同形）。"""
    return {
        "run_id": run_id,
        "seq": seq,
        "user_id": MAINTAINER_ID,
        "thread_id": "th-pure",
        "ts_ms": int((created_at - _BASE_TS).total_seconds() * 1000),
        "agent_role": role,
        "event_type": event_type,
        "payload": payload,
        "created_at": created_at,
    }


@pytest.fixture
async def seed_events():
    """造事件行工厂；按 thread_id 前缀清场（只删本测试造的前缀与用户）。

    ``ops_lg_rag_run_events.user_id`` 有 FK → ``ops_users``：conftest 的
    override 用户（0000...0001/0002）并不真在表里，造事件前须先补用户行。
    """
    prefixes: list[str] = []
    created_users: list[str] = []

    async def _seed(prefix: str, rows: list[OpsLgRagRunEvent]) -> None:
        prefixes.append(prefix)
        async with AsyncSessionLocal() as db:
            for uid in {str(r.user_id) for r in rows}:
                if await db.get(OpsUser, uid) is None:
                    db.add(
                        OpsUser(
                            id=uid,
                            username=f"hist-{uuid.uuid4().hex[:12]}",
                            role="viewer",
                        )
                    )
                    created_users.append(uid)
            await db.flush()  # 先落用户行：无 relationship，UoW 不保证 FK 插入序
            db.add_all(rows)
            await db.commit()

    yield _seed

    async with AsyncSessionLocal() as db:
        for prefix in prefixes:
            await db.execute(
                delete(OpsLgRagRunEvent).where(
                    OpsLgRagRunEvent.thread_id.startswith(prefix)
                )
            )
        for uid in created_users:
            await db.execute(delete(OpsUser).where(OpsUser.id == uid))
        await db.commit()


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


# ---------------------------------------------------------------------------
# H3 纯函数：answer 聚合（终帧优先 / delta 回退 / 32000 截断）
# ---------------------------------------------------------------------------


def test_aggregate_answer_final_frame_wins_over_deltas() -> None:
    run = {
        "run_id": "r1",
        "_first_created_at": _BASE_TS,
        "events": [
            _row("r1", 2, "answer", {"delta": "错"}, _BASE_TS),
            _row("r1", 3, "answer", {"content": "终答", "final": True}, _BASE_TS),
        ],
    }
    answer, truncated = history.aggregate_answer(run)
    assert answer == "终答"
    assert truncated is False


def test_aggregate_answer_delta_fallback_by_seq() -> None:
    run = {
        "run_id": "r1",
        "_first_created_at": _BASE_TS,
        "events": [
            _row("r1", 1, "answer", {"delta": "你好"}, _BASE_TS),
            _row("r1", 2, "answer", {"delta": "世界"}, _BASE_TS),
        ],
    }
    answer, truncated = history.aggregate_answer(run)
    assert answer == "你好世界"
    assert truncated is False


def test_aggregate_answer_truncates_over_32000() -> None:
    run = {
        "run_id": "r1",
        "_first_created_at": _BASE_TS,
        "events": [
            _row(
                "r1",
                1,
                "answer",
                {"content": "x" * (ANSWER_MAX_CHARS + 1), "final": True},
                _BASE_TS,
            ),
        ],
    }
    answer, truncated = history.aggregate_answer(run)
    assert truncated is True
    assert len(answer) == ANSWER_MAX_CHARS
    # 恰好 32000 不截断
    run["events"][0]["payload"]["content"] = "y" * ANSWER_MAX_CHARS
    answer, truncated = history.aggregate_answer(run)
    assert truncated is False
    assert len(answer) == ANSWER_MAX_CHARS


def test_aggregate_answer_no_answer_events() -> None:
    run = {"run_id": "r1", "_first_created_at": _BASE_TS, "events": []}
    assert history.aggregate_answer(run) == ("", False)


# ---------------------------------------------------------------------------
# H3 纯函数：run 分组升序 / 终态 / 标题降级 / subtask / hitl / cursor
# ---------------------------------------------------------------------------


def test_group_events_by_run_orders_by_first_frame() -> None:
    t0, t1 = _BASE_TS, _BASE_TS + timedelta(seconds=10)
    events = [
        # 乱序喂入：r2 的首帧更早 → r2 排前
        _row("r1", 1, "run.start", {"query": "q1"}, t1),
        _row("r2", 2, "done", {}, t0 + timedelta(seconds=1)),
        _row("r2", 1, "run.start", {"query": "q2"}, t0),
        _row("r1", 2, "done", {}, t1 + timedelta(seconds=1)),
    ]
    runs = history.group_events_by_run(events)
    assert [r["run_id"] for r in runs] == ["r2", "r1"]
    # run 内 seq 升序
    assert [e["seq"] for e in runs[0]["events"]] == [1, 2]


def test_run_terminal_status_variants() -> None:
    def _run(*types_payloads: tuple[str, dict]) -> dict[str, Any]:
        return {
            "run_id": "r",
            "_first_created_at": _BASE_TS,
            "events": [
                _row("r", i + 1, et, pl, _BASE_TS)
                for i, (et, pl) in enumerate(types_payloads)
            ],
        }

    assert history.run_terminal_status(_run(("done", {}))) == "completed"
    assert (
        history.run_terminal_status(_run(("done", {"status": "waiting_approval"})))
        == "waiting_approval"
    )
    assert (
        history.run_terminal_status(_run(("done", {"status": "disconnected"})))
        == "disconnected"
    )
    assert history.run_terminal_status(_run(("error", {"message": "x"}))) == "error"
    assert history.run_terminal_status(_run(("answer", {"delta": "d"}))) == "running"


def test_thread_title_from_query_and_truncation() -> None:
    events = [
        _row("r1", 1, "run.start", {"query": "  多   空白   标题  "}, _BASE_TS),
        _row("r1", 2, "done", {}, _BASE_TS),
    ]
    assert history.thread_title(events) == "多 空白 标题"
    long_query = "题" * (TITLE_MAX_CHARS + 10)
    events[0]["payload"]["query"] = long_query
    title = history.thread_title(events)
    assert len(title) == TITLE_MAX_CHARS
    assert title.endswith("…")


def test_thread_title_degrades_without_query_fp4() -> None:
    run_id = "abcdef1234567890"
    events = [
        # 存量旧 run：run.start 无 query 键（裁定 A1 前）
        _row(run_id, 1, "run.start", {"run_id": run_id, "mode": "supervisor"}, _BASE_TS),
        _row(run_id, 2, "done", {}, _BASE_TS),
    ]
    title = history.thread_title(events)
    assert title.startswith(run_id[:8])
    assert _BASE_TS.isoformat() in title
    # 空事件不炸
    assert history.thread_title([]) == ""


def test_summarize_subtasks_and_collect_hitl() -> None:
    run = {
        "run_id": "r1",
        "_first_created_at": _BASE_TS,
        "events": [
            _row(
                "r1",
                1,
                "subtask.progress",
                {"status": "running", "message": "开工"},
                _BASE_TS,
                role="rag_subtask",
            ),
            _row(
                "r1",
                2,
                "subtask.progress",
                {
                    "status": "done",
                    "subtask_result": {"id": "t1"},
                    "answer_preview": "预览",
                    "noise_key": "不透传",
                },
                _BASE_TS,
                role="rag_subtask",
            ),
            _row(
                "r1",
                3,
                "hitl.waiting",
                {"reason": "hitl_waiting", "requests": [{"id": "ap1", "action": "rm"}]},
                _BASE_TS,
            ),
        ],
    }
    subs = history.summarize_subtasks(run)
    assert [s["status"] for s in subs] == ["running", "done"]
    assert subs[0]["agent_role"] == "rag_subtask"
    assert subs[1]["subtask_result"] == {"id": "t1"}
    assert "noise_key" not in subs[1]
    assert history.collect_hitl_requests(run) == [{"id": "ap1", "action": "rm"}]


def test_cursor_roundtrip_and_invalid() -> None:
    cursor = history.make_threads_cursor(_BASE_TS, "th-1")
    assert history.threads_cursor_after(cursor) == (_BASE_TS, "th-1")
    rcursor = history.make_runs_cursor(_BASE_TS, "r-1")
    assert history.runs_cursor_after(rcursor) == (_BASE_TS, "r-1")
    for bad in ("", "  ", "%%%not-b64%%%", history.encode_cursor({"x": 1})):
        with pytest.raises(HistoryCursorError):
            history.threads_cursor_after(bad)


def test_paginate_run_views_no_dup_no_miss() -> None:
    events: list[dict[str, Any]] = []
    for i in range(3):
        ts = _BASE_TS + timedelta(seconds=i * 10)
        events.append(_row(f"r{i}", 1, "run.start", {"query": f"q{i}"}, ts))
        events.append(_row(f"r{i}", 2, "done", {}, ts + timedelta(seconds=1)))
    page1, cursor1 = history.paginate_run_views(events, limit=2)
    assert [v["run_id"] for v in page1] == ["r0", "r1"]
    assert cursor1 is not None
    page2, cursor2 = history.paginate_run_views(events, limit=2, cursor=cursor1)
    assert [v["run_id"] for v in page2] == ["r2"]
    assert cursor2 is None
    assert {v["run_id"] for v in page1 + page2} == {"r0", "r1", "r2"}
    with pytest.raises(HistoryCursorError):
        history.paginate_run_views(events, limit=2, cursor="%%%bad%%%")


def test_latest_run_status_picks_most_recent_run() -> None:
    t0 = _BASE_TS
    events = [
        _row("old", 1, "run.start", {"query": "q"}, t0),
        _row("old", 2, "done", {}, t0 + timedelta(seconds=1)),
        _row("new", 1, "run.start", {"query": "q2"}, t0 + timedelta(seconds=5)),
        _row("new", 2, "done", {"status": "waiting_approval"}, t0 + timedelta(seconds=6)),
    ]
    assert history.latest_run_status(events) == "waiting_approval"


# ---------------------------------------------------------------------------
# H1：threads 列表（DB）
# ---------------------------------------------------------------------------


@_DB_SKIP
async def test_threads_list_fields_waiting_approval_and_order(
    client: AsyncClient, override_auth_maintainer, seed_events
) -> None:
    prefix = f"th-h1-{uuid.uuid4().hex[:8]}"
    tid_a, tid_b = f"{prefix}-a", f"{prefix}-b"
    t0 = _BASE_TS
    rows = [
        # thread A · run r1（completed）
        _ev("r-a1", 1, MAINTAINER_ID, tid_a, "run.start",
            {"run_id": "r-a1", "thread_id": tid_a, "mode": "supervisor", "query": "第一问"},
            t0),
        _ev("r-a1", 2, MAINTAINER_ID, tid_a, "answer",
            {"content": "答一", "final": True}, t0 + timedelta(seconds=1), role="aggregator"),
        _ev("r-a1", 3, MAINTAINER_ID, tid_a, "done",
            {"run_id": "r-a1"}, t0 + timedelta(seconds=2)),
        # thread A · run r2（waiting_approval · 最新活动）
        _ev("r-a2", 1, MAINTAINER_ID, tid_a, "run.start",
            {"run_id": "r-a2", "thread_id": tid_a, "mode": "supervisor", "query": "第二问"},
            t0 + timedelta(seconds=10)),
        _ev("r-a2", 2, MAINTAINER_ID, tid_a, "hitl.waiting",
            {"reason": "hitl_waiting", "requests": [{"id": "ap1"}]},
            t0 + timedelta(seconds=11)),
        _ev("r-a2", 3, MAINTAINER_ID, tid_a, "done",
            {"run_id": "r-a2", "status": "waiting_approval"}, t0 + timedelta(seconds=12)),
        # thread B · run r3（completed · 活动介于 A 两 run 之间）
        _ev("r-b1", 1, MAINTAINER_ID, tid_b, "run.start",
            {"run_id": "r-b1", "thread_id": tid_b, "mode": "basic", "query": "B 问"},
            t0 + timedelta(seconds=5)),
        _ev("r-b1", 2, MAINTAINER_ID, tid_b, "done",
            {"run_id": "r-b1"}, t0 + timedelta(seconds=6)),
    ]
    await seed_events(prefix, rows)

    response = await client.get(_THREADS)
    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is True
    mine = [t for t in body["data"]["threads"] if t["thread_id"].startswith(prefix)]
    assert len(mine) == 2
    # last_activity_at 倒序：A（t0+12s）在 B（t0+6s）前
    assert [t["thread_id"] for t in mine] == [tid_a, tid_b]
    first = mine[0]
    # 字段族齐
    assert set(first) == {
        "thread_id",
        "title",
        "last_activity_at",
        "run_count",
        "latest_run_status",
    }
    assert first["title"] == "第一问"  # 最早 run 的 query 为标题
    assert first["run_count"] == 2
    assert first["latest_run_status"] == "waiting_approval"  # 最新 run 挂起可识别
    assert first["last_activity_at"]  # 非空 ISO
    assert mine[1]["latest_run_status"] == "completed"
    assert mine[1]["run_count"] == 1


@_DB_SKIP
async def test_threads_default_limit_20_and_over_100_422(
    client: AsyncClient, override_auth_viewer, seed_events
) -> None:
    prefix = f"th-h1p-{uuid.uuid4().hex[:8]}"
    rows = []
    for i in range(25):
        tid = f"{prefix}-{i:02d}"
        ts = _BASE_TS + timedelta(minutes=i)
        rows.append(
            _ev(f"r-{i}", 1, VIEWER_ID, tid, "run.start",
                {"run_id": f"r-{i}", "thread_id": tid, "mode": "basic", "query": f"q{i}"},
                ts)
        )
        rows.append(
            _ev(f"r-{i}", 2, VIEWER_ID, tid, "done", {"run_id": f"r-{i}"},
                ts + timedelta(seconds=1))
        )
    await seed_events(prefix, rows)

    # 默认 limit=20
    page1 = await client.get(_THREADS)
    assert page1.status_code == 200
    data1 = page1.json()["data"]
    assert len(data1["threads"]) == 20
    assert data1["next_cursor"] is not None

    # limit>100 → 422；limit<1 → 422
    assert (await client.get(_THREADS, params={"limit": 101})).status_code == 422
    assert (await client.get(_THREADS, params={"limit": 0})).status_code == 422

    # cursor 翻页不重不漏（翻尽为止，只收集本前缀）
    seen: list[str] = []
    cursor = None
    for _ in range(10):
        params: dict[str, Any] = {"limit": 7}
        if cursor:
            params["cursor"] = cursor
        resp = await client.get(_THREADS, params=params)
        assert resp.status_code == 200
        data = resp.json()["data"]
        seen.extend(
            t["thread_id"] for t in data["threads"] if t["thread_id"].startswith(prefix)
        )
        cursor = data["next_cursor"]
        if cursor is None:
            break
    assert len(seen) == 25
    assert len(set(seen)) == 25  # 不重
    assert set(seen) == {f"{prefix}-{i:02d}" for i in range(25)}  # 不漏
    # 倒序：最近活动的 thread 最先拿到
    assert seen[0] == f"{prefix}-24"
    # 非法 cursor → 422
    assert (await client.get(_THREADS, params={"cursor": "%%%bad%%%"})).status_code == 422


# ---------------------------------------------------------------------------
# H2：thread 完整历史（DB）
# ---------------------------------------------------------------------------


@_DB_SKIP
async def test_thread_history_full_rebuild_and_run_order(
    client: AsyncClient, override_auth_maintainer, seed_events
) -> None:
    prefix = f"th-h2-{uuid.uuid4().hex[:8]}"
    tid = f"{prefix}-main"
    t0 = _BASE_TS
    rows = [
        # run r1（先）：delta 回退 answer + subtask 摘要 + done（无 status → completed）
        _ev("r-h2-1", 1, MAINTAINER_ID, tid, "run.start",
            {"run_id": "r-h2-1", "thread_id": tid, "mode": "supervisor", "query": "旧问"},
            t0),
        _ev("r-h2-1", 2, MAINTAINER_ID, tid, "subtask.progress",
            {"status": "running", "message": "检索中"}, t0 + timedelta(seconds=1),
            role="rag_subtask"),
        _ev("r-h2-1", 3, MAINTAINER_ID, tid, "answer", {"delta": "你好"},
            t0 + timedelta(seconds=2), role="aggregator"),
        _ev("r-h2-1", 4, MAINTAINER_ID, tid, "answer", {"delta": "世界"},
            t0 + timedelta(seconds=3), role="aggregator"),
        _ev("r-h2-1", 5, MAINTAINER_ID, tid, "subtask.progress",
            {"status": "done", "subtask_result": {"id": "t1"}, "answer_preview": "你好"},
            t0 + timedelta(seconds=4), role="rag_subtask"),
        _ev("r-h2-1", 6, MAINTAINER_ID, tid, "done", {"run_id": "r-h2-1"},
            t0 + timedelta(seconds=5)),
        # run r2（后）：终帧优先（混 delta）+ hitl.waiting + done(waiting_approval)
        _ev("r-h2-2", 1, MAINTAINER_ID, tid, "run.start",
            {"run_id": "r-h2-2", "thread_id": tid, "mode": "supervisor", "query": "新问"},
            t0 + timedelta(seconds=10)),
        _ev("r-h2-2", 2, MAINTAINER_ID, tid, "answer", {"delta": "残"},
            t0 + timedelta(seconds=11), role="aggregator"),
        _ev("r-h2-2", 3, MAINTAINER_ID, tid, "answer",
            {"content": "终答", "final": True}, t0 + timedelta(seconds=12),
            role="aggregator"),
        _ev("r-h2-2", 4, MAINTAINER_ID, tid, "hitl.waiting",
            {"reason": "hitl_waiting", "requests": [{"id": "ap9", "action": "deploy"}]},
            t0 + timedelta(seconds=13)),
        _ev("r-h2-2", 5, MAINTAINER_ID, tid, "done",
            {"run_id": "r-h2-2", "status": "waiting_approval"},
            t0 + timedelta(seconds=14)),
    ]
    await seed_events(prefix, rows)

    response = await client.get(_HISTORY.format(tid=tid))
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["thread_id"] == tid
    runs = data["runs"]
    assert [r["run_id"] for r in runs] == ["r-h2-1", "r-h2-2"]  # run 首帧时间升序

    r1, r2 = runs
    # r1：delta 按 seq 拼接 · subtask 摘要按 seq 升序 · completed
    assert r1["query"] == "旧问"
    assert r1["answer"] == "你好世界"
    assert r1["answer_truncated"] is False
    assert [s["status"] for s in r1["subtasks"]] == ["running", "done"]
    assert [s["seq"] for s in r1["subtasks"]] == [2, 5]
    assert r1["terminal_status"] == "completed"
    assert r1["hitl"] == []
    assert r1["started_at"]
    # r2：终帧优先于 delta · waiting_approval · hitl requests 透传
    assert r2["query"] == "新问"
    assert r2["answer"] == "终答"
    assert r2["terminal_status"] == "waiting_approval"
    assert r2["hitl"] == [{"id": "ap9", "action": "deploy"}]


@_DB_SKIP
async def test_thread_history_run_pagination_no_dup_no_miss(
    client: AsyncClient, override_auth_maintainer, seed_events
) -> None:
    prefix = f"th-h2p-{uuid.uuid4().hex[:8]}"
    tid = f"{prefix}-main"
    rows = []
    for i in range(3):
        ts = _BASE_TS + timedelta(seconds=i * 10)
        rows.append(
            _ev(f"r-p{i}", 1, MAINTAINER_ID, tid, "run.start",
                {"run_id": f"r-p{i}", "thread_id": tid, "mode": "basic", "query": f"q{i}"},
                ts)
        )
        rows.append(
            _ev(f"r-p{i}", 2, MAINTAINER_ID, tid, "done", {"run_id": f"r-p{i}"},
                ts + timedelta(seconds=1))
        )
    await seed_events(prefix, rows)

    page1 = await client.get(_HISTORY.format(tid=tid), params={"limit": 2})
    assert page1.status_code == 200
    d1 = page1.json()["data"]
    assert [r["run_id"] for r in d1["runs"]] == ["r-p0", "r-p1"]
    assert d1["next_cursor"] is not None

    page2 = await client.get(
        _HISTORY.format(tid=tid), params={"limit": 2, "cursor": d1["next_cursor"]}
    )
    d2 = page2.json()["data"]
    assert [r["run_id"] for r in d2["runs"]] == ["r-p2"]
    assert d2["next_cursor"] is None


@_DB_SKIP
async def test_thread_history_answer_truncation_flag(
    client: AsyncClient, override_auth_maintainer, seed_events
) -> None:
    prefix = f"th-h2t-{uuid.uuid4().hex[:8]}"
    tid = f"{prefix}-main"
    big = "长" * (ANSWER_MAX_CHARS + 100)
    rows = [
        _ev("r-big", 1, MAINTAINER_ID, tid, "run.start",
            {"run_id": "r-big", "thread_id": tid, "mode": "basic", "query": "长答"},
            _BASE_TS),
        _ev("r-big", 2, MAINTAINER_ID, tid, "answer",
            {"content": big, "final": True}, _BASE_TS + timedelta(seconds=1),
            role="aggregator"),
        _ev("r-big", 3, MAINTAINER_ID, tid, "done", {"run_id": "r-big"},
            _BASE_TS + timedelta(seconds=2)),
    ]
    await seed_events(prefix, rows)

    response = await client.get(_HISTORY.format(tid=tid))
    assert response.status_code == 200
    run = response.json()["data"]["runs"][0]
    assert run["answer_truncated"] is True
    assert len(run["answer"]) == ANSWER_MAX_CHARS


# ---------------------------------------------------------------------------
# H4 / failure_paths：404 · 401 · 422 · FP-4 降级 · FP-2 超时 504
# ---------------------------------------------------------------------------


@_DB_SKIP
async def test_thread_history_cross_user_404(
    client: AsyncClient, override_auth_maintainer, seed_events
) -> None:
    prefix = f"th-h4-{uuid.uuid4().hex[:8]}"
    tid = f"{prefix}-other"
    other_user = uuid.uuid4().hex  # 他人 thread（事件表 user_id 真源）
    rows = [
        _ev("r-x", 1, other_user, tid, "run.start",
            {"run_id": "r-x", "thread_id": tid, "mode": "basic", "query": "别人问"},
            _BASE_TS),
        _ev("r-x", 2, other_user, tid, "done", {"run_id": "r-x"},
            _BASE_TS + timedelta(seconds=1)),
    ]
    await seed_events(prefix, rows)

    response = await client.get(_HISTORY.format(tid=tid))
    assert response.status_code == 404  # 不 403 · 不泄露存在性


@_DB_SKIP
async def test_thread_history_unknown_thread_404(
    client: AsyncClient, override_auth_maintainer
) -> None:
    response = await client.get(_HISTORY.format(tid=f"th-none-{uuid.uuid4().hex[:8]}"))
    assert response.status_code == 404


async def test_threads_unauthorized_401(client: AsyncClient) -> None:
    assert (await client.get(_THREADS)).status_code == 401
    assert (await client.get(_HISTORY.format(tid="th-x"))).status_code == 401


async def test_thread_id_too_long_422(
    client: AsyncClient, override_auth_maintainer
) -> None:
    response = await client.get(_HISTORY.format(tid="t" * 256))
    assert response.status_code == 422


@_DB_SKIP
async def test_thread_history_missing_query_degrades_fp4(
    client: AsyncClient, override_auth_maintainer, seed_events
) -> None:
    """存量旧 run（run.start 无 query 键）：标题降级 run_id 前缀+时间，不阻塞。"""
    prefix = f"th-fp4-{uuid.uuid4().hex[:8]}"
    tid = f"{prefix}-old"
    run_id = "0ldrun1234567890"
    rows = [
        _ev(run_id, 1, MAINTAINER_ID, tid, "run.start",
            {"run_id": run_id, "thread_id": tid, "mode": "supervisor"},  # 无 query 键
            _BASE_TS),
        _ev(run_id, 2, MAINTAINER_ID, tid, "answer",
            {"content": "旧答", "final": True}, _BASE_TS + timedelta(seconds=1),
            role="aggregator"),
        _ev(run_id, 3, MAINTAINER_ID, tid, "done", {"run_id": run_id},
            _BASE_TS + timedelta(seconds=2)),
    ]
    await seed_events(prefix, rows)

    list_resp = await client.get(_THREADS)
    assert list_resp.status_code == 200
    mine = [
        t
        for t in list_resp.json()["data"]["threads"]
        if t["thread_id"] == tid
    ]
    assert len(mine) == 1  # 列表不阻塞
    assert mine[0]["title"].startswith(run_id[:8])  # 降级标题

    hist_resp = await client.get(_HISTORY.format(tid=tid))
    assert hist_resp.status_code == 200
    run = hist_resp.json()["data"]["runs"][0]
    assert run["query"] == ""  # 如实重建：缺 query 不伪造
    assert run["answer"] == "旧答"


@_DB_SKIP
async def test_threads_aggregate_timeout_504(
    client: AsyncClient, override_auth_maintainer
) -> None:
    """FP-2：聚合超时常量注入小阈值 → 504。"""

    async def _slow_page(*_a: Any, **_kw: Any) -> list[dict[str, Any]]:
        await asyncio.sleep(5)
        return []

    with (
        patch(
            "app.ops.lg_rag.history_router.HISTORY_AGGREGATE_TIMEOUT_S", 0.05
        ),
        patch(
            "app.ops.lg_rag.history_router.event_store.list_thread_activity_page",
            new=_slow_page,
        ),
    ):
        response = await client.get(_THREADS)
    assert response.status_code == 504


@_DB_SKIP
async def test_thread_history_aggregate_timeout_504(
    client: AsyncClient, override_auth_maintainer, seed_events
) -> None:
    prefix = f"th-to-{uuid.uuid4().hex[:8]}"
    tid = f"{prefix}-main"
    rows = [
        _ev("r-to", 1, MAINTAINER_ID, tid, "run.start",
            {"run_id": "r-to", "thread_id": tid, "mode": "basic", "query": "q"},
            _BASE_TS),
    ]
    await seed_events(prefix, rows)

    async def _slow_fetch(*_a: Any, **_kw: Any) -> dict[str, list[dict[str, Any]]]:
        await asyncio.sleep(5)
        return {}

    with (
        patch(
            "app.ops.lg_rag.history_router.HISTORY_AGGREGATE_TIMEOUT_S", 0.05
        ),
        patch(
            "app.ops.lg_rag.history_router.event_store.fetch_events_for_threads",
            new=_slow_fetch,
        ),
    ):
        response = await client.get(_HISTORY.format(tid=tid))
    assert response.status_code == 504


# ---------------------------------------------------------------------------
# SSE 对拍（裁定 A1 · freeze lg-rag-sse-v1）：run.start 仅多可选 query 键
# ---------------------------------------------------------------------------


async def _fake_supervisor_stream(
    query: str, *, thread_id: str = "t", checkpointer: Any = None, **_kwargs: Any
) -> AsyncIterator[dict[str, Any]]:
    yield {"aggregator": {"messages": [AIMessage(content=f"答:{query}")]}}


async def test_run_start_carries_optional_query_no_new_event_type(
    client: AsyncClient, override_auth_maintainer
) -> None:
    with (
        patch(
            "app.ops.lg_rag.multi.graph.astream_supervisor_agent",
            new=_fake_supervisor_stream,
        ),
        patch(
            "app.ops.lg_rag.sse_stream.persist_thread_turns",
            new_callable=AsyncMock,
        ),
        patch(
            "app.ops.lg_rag.event_store.persist_run_event",
            new_callable=AsyncMock,
        ) as mock_persist,
    ):
        response = await client.post(
            _STREAM, json={"query": "历史问", "thread_id": "th-hist-sse"}
        )
    assert response.status_code == 200
    events = _parse_sse(response.text)
    types = [e["event_type"] for e in events]
    # 零新 event_type：全部落在 freeze 集合内；帧序 run.start → answer → done
    assert set(types) <= _FREEZE_EVENT_TYPES
    assert types == ["run.start", "answer", "done"]

    start = events[0]
    # 既有三键仍在（旧断言 subset-安全锚点）
    assert start["payload"]["thread_id"] == "th-hist-sse"
    assert start["payload"]["mode"] == "supervisor"
    assert start["payload"]["run_id"]
    # A1：仅多一个可选 query 键，值 = 本次 query
    assert set(start["payload"]) == {"run_id", "thread_id", "mode", "query"}
    assert start["payload"]["query"] == "历史问"

    # 落盘帧同形（历史面真源闭环：事件表 run.start 亦携 query）
    first = mock_persist.call_args_list[0]
    assert first.kwargs["event_type"] == "run.start"
    assert first.kwargs["payload"]["query"] == "历史问"
