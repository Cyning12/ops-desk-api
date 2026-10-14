"""HITL resume 异步化：端点**投递即返**，恢复执行在后台跑。

修复前的形状：POST /requests/{id}/resume 在请求内 await 整个图恢复
（echo 场景实测 130–310s），web 侧 axios 30s 超时把请求掐断 —— 后端其实
跑完了，前端卡片却误回「待审批」。这组测试钉住修复后的形状：

- 端点秒回 200，resume.status == "accepted"（执行尚未完成）；
- 响应键位不变：{ok, request, resume, replay, ts}；
- 同一申请在飞期间重复 resume → 409（幂等防重）；
- 后台执行失败 / 进程崩溃后，重新调 resume 可重投递（崩溃恢复不靠扫描器）；
- preflight_only 探针只做守卫检查、不驱动图（请求内 fail-fast 的载体）。
"""

from __future__ import annotations

import asyncio
import threading
import time
from unittest.mock import patch

import pytest
from langgraph.checkpoint.memory import InMemorySaver

import app.ops.hitl.router as router_mod
from app.ops.hitl.persistence import reset_hitl_store
from app.ops.hitl.resume import ResumeError, resume_hitl_run
from app.ops.hitl.store import STATUS_APPROVED, InMemoryHitlStore
from tests.test_hitl_resume import (
    _RUN,
    _T1,
    _approved_row,
    _client,
    _drain,
    _graph_factory,
    _hitl_state,
    _suspend,
)


@pytest.fixture(autouse=True)
def _isolate():
    reset_hitl_store()
    yield
    reset_hitl_store()
    getattr(router_mod, "_RESUME_IN_FLIGHT", {}).clear()


def _decided(store: InMemoryHitlStore, **row_kw) -> dict:
    row = _approved_row(**row_kw)
    asyncio.run(store.acreate(row))
    asyncio.run(store.adecide(row["id"], decision=STATUS_APPROVED, by="张三"))
    return row


# ---------------------------------------------------------------------------
# 1 · 秒回（红测核心：执行被闸门卡住时，响应不许等它）
# ---------------------------------------------------------------------------


def test_resume_returns_before_execution_completes(monkeypatch):
    """执行体慢（被闸门卡住）⇒ 端点仍秒回 200，且响应先于执行完成返回。

    修复前这条红：端点同步等整个图恢复跑完（≥ 闸门放行时间）。
    """
    store = InMemoryHitlStore()
    row = _decided(store)

    gate = threading.Event()
    completed = threading.Event()

    async def _gated(**kwargs):
        if kwargs.get("preflight_only"):
            return {"preflight": True}
        await asyncio.to_thread(gate.wait, 10)
        completed.set()
        return {"thread_id": kwargs["thread_id"], "state": {"route": "replan"}}

    timer = threading.Timer(2.0, gate.set)  # 防死锁：修复前最迟 2s 放行
    with (
        patch("app.ops.hitl.router.resume_hitl_run", new=_gated),
        _client(monkeypatch, store) as client,
    ):
        timer.start()
        try:
            t0 = time.monotonic()
            res = client.post("/api/ops/hitl/requests/" + row["id"] + "/resume")
            elapsed = time.monotonic() - t0
            assert res.status_code == 200, res.text
            assert elapsed < 1.5, f"resume 端点仍同步等执行（{elapsed:.2f}s）"
            assert res.json()["resume"]["status"] == "accepted"
            assert not completed.is_set(), "响应前执行已跑完 —— 仍是同步形态"
        finally:
            gate.set()
            timer.cancel()
        _drain()
        assert completed.is_set(), "后台恢复没有被执行"


# ---------------------------------------------------------------------------
# 2 · D1 响应形：键位不变，resume 键变「已受理」
# ---------------------------------------------------------------------------


def test_resume_response_shape_is_accepted_form(monkeypatch):
    store = InMemoryHitlStore()
    row = _decided(store)

    async def _quick(**kwargs):
        if kwargs.get("preflight_only"):
            return {"preflight": True}
        return {"thread_id": kwargs["thread_id"], "state": {}}

    with (
        patch("app.ops.hitl.router.resume_hitl_run", new=_quick),
        _client(monkeypatch, store) as client,
    ):
        res = client.post("/api/ops/hitl/requests/" + row["id"] + "/resume")
        _drain()
    assert res.status_code == 200, res.text
    body = res.json()
    assert {"ok", "request", "resume", "replay", "ts"} <= set(body), "顶层键位变了"
    resume = body["resume"]
    assert resume["status"] == "accepted"
    assert resume["thread_id"] == "t-api"
    assert resume["approved"] == [_T1]
    assert resume["rejected"] == []
    assert resume["decided_by"] == "张三"
    replay = body["replay"]
    assert replay["run_id"] == _RUN
    assert isinstance(replay["cursor"], str)
    assert replay["events_persisted"] == 0
    assert replay["events_failed"] == 0
    assert replay["re_interrupted"] is False


# ---------------------------------------------------------------------------
# 3 · 幂等防重：同一申请在飞期间重复 resume → 409
# ---------------------------------------------------------------------------


def test_resume_in_flight_duplicate_is_409(monkeypatch):
    store = InMemoryHitlStore()
    row = _decided(store)

    gate = threading.Event()

    async def _gated(**kwargs):
        if kwargs.get("preflight_only"):
            return {"preflight": True}
        await asyncio.to_thread(gate.wait, 10)
        return {"state": {}}

    timer = threading.Timer(2.0, gate.set)
    with (
        patch("app.ops.hitl.router.resume_hitl_run", new=_gated),
        _client(monkeypatch, store) as client,
    ):
        timer.start()
        try:
            first = client.post("/api/ops/hitl/requests/" + row["id"] + "/resume")
            assert first.status_code == 200, first.text
            second = client.post("/api/ops/hitl/requests/" + row["id"] + "/resume")
            assert second.status_code == 409, second.text
            assert "执行中" in second.json()["detail"]
        finally:
            gate.set()
            timer.cancel()
        _drain()


# ---------------------------------------------------------------------------
# 4 · 崩溃恢复：后台执行失败后，重调 resume 可重投递（不靠扫描器）
# ---------------------------------------------------------------------------


def test_resume_after_background_failure_redispatches(monkeypatch):
    store = InMemoryHitlStore()
    row = _decided(store)
    calls: list[bool] = []

    async def _flaky(**kwargs):
        if kwargs.get("preflight_only"):
            return {"preflight": True}
        if not calls:
            calls.append(True)
            raise RuntimeError("模拟后台执行崩溃")
        return {"state": {}}

    with (
        patch("app.ops.hitl.router.resume_hitl_run", new=_flaky),
        _client(monkeypatch, store) as client,
    ):
        first = client.post("/api/ops/hitl/requests/" + row["id"] + "/resume")
        assert first.status_code == 200, first.text
        _drain()
        # 执行已在后台失败并沉降：重调必须能再投递，而不是永远 409 在飞
        second = client.post("/api/ops/hitl/requests/" + row["id"] + "/resume")
        assert second.status_code == 200, second.text
        assert second.json()["resume"]["status"] == "accepted"
        _drain()


# ---------------------------------------------------------------------------
# 5 · preflight_only 探针：只做守卫检查，不驱动图
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_preflight_only_checks_guards_without_streaming():
    """preflight 探针过守卫但不 astream：checkpoint 必须仍停在 interrupt。"""
    saver = InMemorySaver()
    payload = await _suspend(_hitl_state(), saver, "t-preflight")
    assert payload is not None, "前置：图没有被挂起"

    out = await resume_hitl_run(
        thread_id="t-preflight",
        approved=[_T1],
        decided_by="张三",
        checkpointer=saver,
        graph_factory=_graph_factory,
        preflight_only=True,
    )
    assert out["preflight"] is True
    assert out["state"] == {}
    assert out["approved"] == [_T1]
    assert out["decided_by"] == "张三"

    graph = _graph_factory(checkpointer=saver)
    snap = await graph.aget_state({"configurable": {"thread_id": "t-preflight"}})
    assert snap.tasks and snap.tasks[0].interrupts, "preflight 把图驱动了"


@pytest.mark.asyncio
async def test_preflight_refuses_finished_thread():
    """幂等底线：恢复已完成的 thread，preflight 仍打 not_interrupted（409）。"""
    saver = InMemorySaver()
    await _suspend(_hitl_state(), saver, "t-preflight-done")
    await resume_hitl_run(
        thread_id="t-preflight-done",
        approved=[_T1],
        decided_by="张三",
        checkpointer=saver,
        graph_factory=_graph_factory,
    )
    with pytest.raises(ResumeError) as exc:
        await resume_hitl_run(
            thread_id="t-preflight-done",
            approved=[_T1],
            decided_by="张三",
            checkpointer=saver,
            graph_factory=_graph_factory,
            preflight_only=True,
        )
    assert exc.value.code == "not_interrupted"
