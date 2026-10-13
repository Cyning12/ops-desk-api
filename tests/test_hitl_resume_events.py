"""恢复段的事件落盘：批准之后的结论要能**回到前端**。

SSE 在 ``interrupt()`` 那一帧就收尾了（``hitl.waiting`` +
``done(status=waiting_approval)``）。批准之后跑完的那段如果只留在 HTTP
响应里，前端就得自己再造一条通道。而 replay 通道本来就存在 —— 只要把这段
**接同一个 run_id 继续编号**写进去即可。

这个文件测的就是"接得对不对"，核心一条是 **seq 必须接着走**：
从 1 重开会让 replay 的 `seq > after_seq` 过滤把恢复段整段丢掉，
而客户端那边看起来只是"replay 返回空"，很难想到是编号重开了。
"""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from app.ops.hitl.persistence import reset_hitl_store, set_hitl_store
from app.ops.hitl.resume import ResumeEventSink
from app.ops.hitl.store import (
    STATUS_APPROVED,
    STATUS_PENDING,
    InMemoryHitlStore,
)

_RUN = "runevt"
_T1 = f"{_RUN}:1"


@pytest.fixture(autouse=True)
def _isolate():
    reset_hitl_store()
    yield
    reset_hitl_store()


@pytest.fixture
def persisted():
    """接住所有 persist_run_event 调用；返回累积列表。"""
    rows: list[dict] = []

    async def _fake(**kw):
        rows.append(kw)

    with patch("app.ops.lg_rag.event_store.persist_run_event", new=_fake):
        yield rows


def _plain_update() -> dict:
    return {"observe": {"react_observation": {"verdict": "replan"}}}


# ---------------------------------------------------------------------------
# 1 · 编号必须接着走（不是从 1 重开）
# ---------------------------------------------------------------------------


async def test_seq_continues_from_start_seq(persisted):
    """正向：从 ``start_seq`` 接着编号。

    从 1 重开 ⇒ replay 的 ``seq > after_seq`` 把恢复段整段过滤掉 ⇒
    前端 replay 返回空，看起来像"没有新事件"。
    """
    sink = ResumeEventSink(run_id="r1", user_id="u1", thread_id="t1", start_seq=7)
    await sink.open(approved=[_T1], decided_by="张三")
    await sink(_plain_update())
    await sink.close()
    assert [r["seq"] for r in persisted] == [8, 9, 10]
    assert all(r["run_id"] == "r1" and r["user_id"] == "u1" for r in persisted)


async def test_start_seq_zero_starts_at_one_control(persisted):
    """反向对照：没传 start_seq 就从 1 开始 —— 不是"永远接着某个数"。"""
    sink = ResumeEventSink(run_id="r1", user_id="u1", thread_id="t1")
    await sink.open(approved=[_T1])
    await sink(_plain_update())
    assert [r["seq"] for r in persisted] == [1, 2]


# ---------------------------------------------------------------------------
# 2 · 这一段的开头与收尾要能自解释
# ---------------------------------------------------------------------------


async def test_opens_with_resumed_and_closes_with_done(persisted):
    """开头 ``hitl.resumed`` + 结尾 ``done(status=resumed)``。

    replay 出来的这段要能自解释，否则客户端看到凭空多出来一串节点帧，
    不知道那是什么。
    """
    sink = ResumeEventSink(run_id="r1", user_id="u1", thread_id="t1")
    await sink.open(approved=[_T1], decided_by="张三")
    await sink(_plain_update())
    await sink.close()

    assert persisted[0]["event_type"] == "hitl.resumed"
    assert persisted[0]["payload"]["approved"] == [_T1]
    assert persisted[0]["payload"]["decided_by"] == "张三"
    assert persisted[-1]["event_type"] == "done"
    assert persisted[-1]["payload"]["status"] == "resumed"
    assert sink.cursor == "r1:3"


async def test_re_interrupt_marks_the_tail_as_waiting(persisted):
    """恢复段**又挂起** ⇒ 发 ``hitl.waiting`` 且 done 标 ``waiting_approval``。

    批准一次不等于后面不会再拦一次。静默收尾会让人以为跑完了，
    而实际后台又躺着一条 pending。
    """
    sink = ResumeEventSink(run_id="r1", user_id="u1", thread_id="t1")
    await sink.open(approved=[_T1])
    await sink({"__interrupt__": (type("I", (), {"value": {"reason": "hitl_waiting",
                                                            "requests": []}})(),)})
    await sink.close()
    kinds = [r["event_type"] for r in persisted]
    assert "hitl.waiting" in kinds
    assert persisted[-1]["payload"]["status"] == "waiting_approval"
    assert sink.re_interrupted is True


async def test_normal_tail_is_not_marked_waiting_control(persisted):
    """反向对照：没再挂起就不许标 waiting_approval —— 否则"一律等待"也绿。"""
    sink = ResumeEventSink(run_id="r1", user_id="u1", thread_id="t1")
    await sink.open(approved=[_T1])
    await sink(_plain_update())
    await sink.close()
    assert persisted[-1]["payload"]["status"] == "resumed"
    assert sink.re_interrupted is False


# ---------------------------------------------------------------------------
# 2b · 终帧观测字段（F-OBS-1：与 live 流 done 对齐 · task hitl_resume_replay_contract）
# ---------------------------------------------------------------------------


async def test_close_done_carries_latency_ms(persisted):
    """F-OBS-1：resume 终帧 done 必须带 latency_ms（int ≥ 0 · 毫秒）。

    缺键时前端 lastDone 徽标只能显示「耗时 0ms」（web 联调 FP-1 实证）。
    口径与 live 流终帧一致：int((time.perf_counter() - started) * 1000)。
    修复前 RED 签名：KeyError 'latency_ms'（缺键，与实证缺口同形）。
    """
    sink = ResumeEventSink(run_id="r1", user_id="u1", thread_id="t1")
    await sink.open(approved=[_T1])
    await sink(_plain_update())
    await sink.close()

    done = persisted[-1]
    assert done["event_type"] == "done"
    latency_ms = done["payload"]["latency_ms"]
    assert isinstance(latency_ms, int)
    assert latency_ms >= 0


async def test_close_done_has_no_model_key_control(persisted):
    """FP-1 裁定钉案（对照用例，应即绿）：resume 终帧**不补** model 键。

    lg-rag 面无 per-run model 真源（live done 亦无 model；chat 的 model 来自
    chat 模块自有 run 记录，非本契约面）——伪造默认值违反 FP-1 禁伪造红线。
    此断言钉死「不硬造」，防后续有人塞配置默认值充数。
    """
    sink = ResumeEventSink(run_id="r1", user_id="u1", thread_id="t1")
    await sink.open(approved=[_T1])
    await sink(_plain_update())
    await sink.close()

    assert "model" not in persisted[-1]["payload"]


async def test_node_updates_use_the_same_frame_shape_as_live(persisted):
    """恢复段的帧形状必须和 live 一致（复用 ``map_node_update``）。

    形状漂移的话前端要写两套渲染逻辑，而且只在"批准过一次"的会话里出现。
    """
    sink = ResumeEventSink(run_id="r1", user_id="u1", thread_id="t1")
    await sink({"rag_subtask": {"subtask_results": [{"subtask_id": _T1, "output": "x"}]}})
    frame = persisted[-1]
    assert frame["event_type"] == "subtask.progress"
    assert frame["agent_role"] == "rag_subtask"
    assert frame["payload"]["status"] == "done"


async def test_internal_channels_are_not_emitted(persisted):
    """``__interrupt__`` 之类的内部 channel 不当成节点帧发。"""
    sink = ResumeEventSink(run_id="r1", user_id="u1", thread_id="t1")
    await sink({"__metadata__": {"x": 1}})
    assert persisted == []


# ---------------------------------------------------------------------------
# 3 · 落盘失败不许把恢复本身弄挂，但**不许静默**
# ---------------------------------------------------------------------------


async def test_persist_failure_is_counted_not_raised():
    """落盘挂了要记 ``failed`` 并继续跑 —— 恢复本身比事件更重要。"""
    async def _boom(**_kw):
        raise RuntimeError("db down")

    with patch("app.ops.lg_rag.event_store.persist_run_event", new=_boom):
        sink = ResumeEventSink(run_id="r1", user_id="u1", thread_id="t1")
        await sink.open(approved=[_T1])
        await sink(_plain_update())
        await sink.close()
    assert sink.failed == 3
    assert sink.persisted == 0


# ---------------------------------------------------------------------------
# 4 · 端点：replay 信息要交回前端，归属没解析到要明说
# ---------------------------------------------------------------------------


def _client(monkeypatch, store):
    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    from app.ops.deps import require_admin_sync
    from app.ops.hitl.router import router

    set_hitl_store(store)
    app = FastAPI()
    app.include_router(router, prefix="/api/ops")
    app.dependency_overrides[require_admin_sync] = lambda: None
    return TestClient(app)


def _row(**kw) -> dict:
    base = {
        "id": "hitl_e2e",
        "run_id": "r1",
        "thread_id": "t-api",
        "subtask_id": f"{_RUN}:2",
        "unlock_subtask_id": _T1,
        "blocked_by": "prefix_touch_required",
        "status": STATUS_PENDING,
        "created_at": 1.0,
    }
    base.update(kw)
    return base


def test_resume_endpoint_returns_replay_cursor(monkeypatch):
    """前端靠这个 cursor 调 replay 才能收到批准后的结论。"""
    import asyncio

    store = InMemoryHitlStore()
    row = _row()
    asyncio.run(store.acreate(row))
    asyncio.run(store.adecide(row["id"], decision=STATUS_APPROVED, by="张三"))

    sink = ResumeEventSink(run_id="r1", user_id="u1", thread_id="t-api", start_seq=3)

    async def _fake_open(_row, _thread_id):
        return sink

    seen: dict = {}

    async def _fake_resume(**kw):
        seen.update(kw)
        sink_arg = kw.get("update_sink")
        if sink_arg is not None:
            await sink_arg({"aggregator": {"messages": []}})
        return {"state": {}, "answer": "批准后的答案", "query": "原始问题"}

    turns = AsyncMock()
    with (
        patch("app.ops.hitl.router._open_event_sink", new=_fake_open),
        patch("app.ops.hitl.router.resume_hitl_run", new=_fake_resume),
        patch("app.ops.lg_rag.event_store.persist_run_event", new=AsyncMock()),
        patch("app.ops.lg_rag.thread_store.persist_thread_turns", new=turns),
        _client(monkeypatch, store) as client,
    ):
        res = client.post(f"/api/ops/hitl/requests/{row['id']}/resume")

    assert res.status_code == 200, res.text
    # 端点必须把 sink 交给驱动器 —— 不交的话恢复段一个事件都不会落，
    # 但响应看起来完全正常（这条就是那个"静默失效"的护栏）
    assert seen.get("update_sink") is sink, "恢复没把 update_sink 传给驱动器"
    replay = res.json()["replay"]
    assert replay["persisted"] is True
    assert replay["run_id"] == "r1"
    assert replay["cursor"] == "r1:6"  # open=4 / aggregator=5 / done=6
    assert replay["events_persisted"] == 3
    # 用户这一轮在"等待授权"时没落历史，恢复后必须补上
    turns.assert_awaited_once_with("t-api", "u1", "原始问题", "批准后的答案")


def test_resume_endpoint_reports_when_events_could_not_persist(monkeypatch):
    """归属解析不到 ⇒ 事件没落 ⇒ 前端 replay 不到。必须**说出来**，
    不能返回一个看起来正常的空 cursor。"""
    import asyncio

    store = InMemoryHitlStore()
    row = _row()
    asyncio.run(store.acreate(row))
    asyncio.run(store.adecide(row["id"], decision=STATUS_APPROVED, by="张三"))

    async def _fake_resume(**_kw):
        return {"state": {}, "answer": "", "query": ""}

    with (
        patch("app.ops.hitl.router._open_event_sink", new=AsyncMock(return_value=None)),
        patch("app.ops.hitl.router.resume_hitl_run", new=_fake_resume),
        _client(monkeypatch, store) as client,
    ):
        res = client.post(f"/api/ops/hitl/requests/{row['id']}/resume")

    assert res.status_code == 200, res.text
    replay = res.json()["replay"]
    assert replay["persisted"] is False
    assert replay["cursor"] == ""
    assert replay["events_persisted"] == 0


# ---------------------------------------------------------------------------
# 5 · 归属反查：取不到就 None（不猜一个 user_id）
# ---------------------------------------------------------------------------


async def test_open_event_sink_resolves_owner_and_seq(monkeypatch):
    from app.ops.hitl.router import _open_event_sink

    async def _owner(run_id):
        return "u1" if run_id == "r1" else None

    async def _last(_run_id):
        return 12

    with (
        patch("app.ops.lg_rag.event_store.run_owner", new=_owner),
        patch("app.ops.lg_rag.event_store.last_seq", new=_last),
    ):
        sink = await _open_event_sink({"id": "x", "run_id": "r1"}, "t1")
    assert sink is not None
    assert sink.user_id == "u1"
    assert sink.seq == 12


async def test_open_event_sink_is_none_when_run_unknown(monkeypatch):
    """反向对照：run 没落过事件帧 ⇒ 查不到归属 ⇒ None（不猜）。"""
    from app.ops.hitl.router import _open_event_sink

    async def _owner(_run_id):
        return None

    with patch("app.ops.lg_rag.event_store.run_owner", new=_owner):
        assert await _open_event_sink({"id": "x", "run_id": "r-gone"}, "t1") is None


async def test_open_event_sink_is_none_without_run_id(monkeypatch):
    """申请行没有 run_id ⇒ 无处可落 ⇒ None。"""
    from app.ops.hitl.router import _open_event_sink

    assert await _open_event_sink({"id": "x", "run_id": ""}, "t1") is None
