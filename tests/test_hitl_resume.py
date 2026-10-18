"""HITL 恢复：**批准之后图真的继续跑**（不是改一行 status 就完事）。

``observe_node`` 用 ``interrupt()`` 把图挂起，只做完了"停下来"这一半。
这一半没接上的时候，人在审批界面点"同意"，库里 status 变成 approved，
然后**什么都不会发生** —— 图还躺在 checkpoint 里，前端还停在"等待授权"
那一帧。这比不批更糟：它看起来像批了。

所以这里测的是后半件事，且每条都配反向对照：

- 正向：批准 → 解锁 + 重规划（verdict=replan）；
- 反向：驳回 → 不解锁 + 收工（verdict=settle）；
- 反向：没挂起的 thread 不许恢复（否则 Command 会被当成新输入，
  "恢复"实际变成"重开一局"，人以为恢复了）；
- 反向：没开 PG checkpointer 必须显式失败，不许返回 200 假装成功。
"""

from __future__ import annotations

import time
from types import SimpleNamespace
from unittest.mock import patch

import pytest
from langchain_core.messages import HumanMessage
from langgraph.checkpoint.memory import InMemorySaver

from app.ops.hitl import new_request_id
from app.ops.hitl.persistence import reset_hitl_store, set_hitl_store
from app.ops.hitl.resume import (
    ResumeError,
    _default_graph_factory,
    resume_hitl_run,
)
from app.ops.hitl.store import (
    STATUS_APPROVED,
    STATUS_PENDING,
    STATUS_REJECTED,
    InMemoryHitlStore,
)
from tests.conftest import DB_AVAILABLE

_RUN = "runresume"
_T1 = f"{_RUN}:1"
_T2 = f"{_RUN}:2"
_TOOL = "mock_get_issue_status"


@pytest.fixture(autouse=True)
def _isolate():
    reset_hitl_store()
    yield
    reset_hitl_store()


def _plan_row(sid: str, **kw) -> dict:
    row = {
        "id": sid,
        "subtask_id": sid,
        "alias": "t" + sid.rsplit(":", 1)[-1],
        "type": "tool",
        "tool": _TOOL,
        "input": "x",
        "depends_on": [],
    }
    row.update(kw)
    return row


def _ok(sid: str) -> dict:
    return {"subtask_id": sid, "type": "tool", "output": {"assignee": "张三"}}


def _err(sid: str, msg: str = "boom", **kw) -> dict:
    row = {"subtask_id": sid, "type": "tool", "error": msg}
    row.update(kw)
    return row


def _hitl_state(**kw) -> dict:
    """T2 被 ``prefix_touch_required`` 拦住，要解锁的是已执行的 T1。"""
    base = {
        "messages": [HumanMessage(content="复合问题")],
        "run_id": _RUN,
        "thread_id": "t-resume",
        "allowed_capability_ids": [_TOOL],
        "supervisor_step_count": 1,
        "host_subtask_seq": 2,
        "react_round": 0,
        "inflight_subtask_ids": [],
        "subtasks": [_plan_row(_T1), _plan_row(_T2, depends_on=[_T1])],
        "subtask_results": [
            _ok(_T1),
            _err(
                _T2,
                "需要重跑已执行步骤",
                blocked_by="prefix_touch_required",
                hitl_required=True,
            ),
        ],
        "plan_prefix_ids": [_T1],
    }
    base.update(kw)
    return base


def _all_done_state(**kw) -> dict:
    base = {
        "messages": [HumanMessage(content="复合问题")],
        "run_id": _RUN,
        "thread_id": "t-resume",
        "allowed_capability_ids": [_TOOL],
        "supervisor_step_count": 1,
        "host_subtask_seq": 2,
        "react_round": 0,
        "inflight_subtask_ids": [],
        "subtasks": [_plan_row(_T1), _plan_row(_T2, depends_on=[_T1])],
        "subtask_results": [_ok(_T1), _ok(_T2)],
        "plan_prefix_ids": [_T1, _T2],
    }
    base.update(kw)
    return base


def _graph_factory(*, checkpointer):
    """只含 observe 的最小图：``interrupt()`` 需要真实 runnable 上下文。"""
    from langgraph.graph import END, START, StateGraph

    from app.ops.lg_rag.multi.nodes import observe_node, route_after_react
    from app.ops.lg_rag.state import LgRagState

    builder = StateGraph(LgRagState)
    builder.add_node("observe", observe_node)
    builder.add_edge(START, "observe")
    builder.add_conditional_edges("observe", route_after_react, {"replan": END, "settle": END})
    return builder.compile(checkpointer=checkpointer)


async def _suspend(state: dict, saver: InMemorySaver, thread_id: str):
    """跑一次把图挂起；返回挂起载荷（没挂起则为 None）。"""
    graph = _graph_factory(checkpointer=saver)
    payload = None
    async for chunk in graph.astream(
        state,
        {"configurable": {"thread_id": thread_id}},
        stream_mode="updates",
    ):
        for intr in chunk.get("__interrupt__") or []:
            payload = intr.value
    return payload


# ---------------------------------------------------------------------------
# 1 · 批准 ⇒ 图真的继续跑
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_approval_resumes_and_unlocks():
    """正向：批准后 ``Command(resume=...)`` 重新进入 observe → 解锁 + 重规划。"""
    set_hitl_store(InMemoryHitlStore())
    saver = InMemorySaver()
    payload = await _suspend(_hitl_state(), saver, "t-approve")
    assert payload is not None, "前置：图没有被挂起"

    out = await resume_hitl_run(
        thread_id="t-approve",
        approved=[_T1],
        decided_by="张三",
        checkpointer=saver,
        graph_factory=_graph_factory,
    )
    assert out["approved"] == [_T1]
    state = out["state"]
    assert state["hitl_unlocked_ids"] == [_T1], "批准了却被没解锁"
    assert state["react_observation"]["verdict"] == "replan"
    assert state["react_observation"]["hitl_decision"]["decided_by"] == "张三"


@pytest.mark.asyncio
async def test_rejection_resumes_but_settles_control():
    """反向对照：驳回也要能恢复（否则那条 run 永远挂在等待授权那一帧），
    但**不解锁任何东西**，直接收工。"""
    set_hitl_store(InMemoryHitlStore())
    saver = InMemorySaver()
    await _suspend(_hitl_state(), saver, "t-reject")

    out = await resume_hitl_run(
        thread_id="t-reject",
        approved=[],
        rejected=[_T2],
        decided_by="李四",
        checkpointer=saver,
        graph_factory=_graph_factory,
    )
    state = out["state"]
    assert state["hitl_unlocked_ids"] == [], "驳回却解锁了 —— 授权与拒绝不分"
    assert state["react_observation"]["verdict"] == "settle"


# ---------------------------------------------------------------------------
# 2 · 不许"假装恢复"
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_resume_on_finished_thread_is_refused_control():
    """反向对照：thread 已经跑完就不许恢复。

    不检查的话 ``Command(resume=...)`` 会被当成一次**新输入**，
    表现为"从头又跑了一遍" —— 人以为恢复了，实际是重开一局。
    """
    set_hitl_store(InMemoryHitlStore())
    saver = InMemorySaver()
    payload = await _suspend(_all_done_state(), saver, "t-done")
    assert payload is None, "前置：这条 run 没有挂起"

    with pytest.raises(ResumeError) as exc:
        await resume_hitl_run(
            thread_id="t-done",
            approved=[_T1],
            checkpointer=saver,
            graph_factory=_graph_factory,
        )
    assert exc.value.code == "not_interrupted"


@pytest.mark.asyncio
async def test_stranded_checkpoint_is_refused_not_crashed():
    """旧版本格式的 checkpoint：**读到 pending task 但没有 interrupt 元数据**。

    实测（langgraph 0.2 → 1.2 升级）：旧 checkpoint 的 values 和 pending task
    都能读回来，但 ``task.interrupts`` 是空的；硬喂 ``Command(resume=...)``
    会在 pregel 内部炸 ``TypeError: 'Interrupt' object is not subscriptable``。
    所以必须在这里拦成 409 —— **不能让客户端拿到 500**，也不能把它和
    "这轮已经跑完了"混成一个码（两者该给人的提示完全不同）。
    """

    class _FakeGraph:
        def __init__(self, tasks):
            self.tasks = tasks

        async def aget_state(self, _config):
            return SimpleNamespace(tasks=self.tasks, values={}, config=_config)

        async def astream(self, *_a, **_kw):
            raise AssertionError("不许走到恢复：这条 checkpoint 恢复不了")
            yield {}  # pragma: no cover

    stranded = [SimpleNamespace(interrupts=(), name="observe", id="x")]
    with pytest.raises(ResumeError) as exc:
        await resume_hitl_run(
            thread_id="t-stranded",
            approved=[_T1],
            checkpointer=InMemorySaver(),
            graph_factory=lambda *, checkpointer: _FakeGraph(stranded),
        )
    assert exc.value.code == "stranded_checkpoint"
    assert "旧版本" in exc.value.detail or "interrupt" in exc.value.detail


@pytest.mark.asyncio
async def test_resume_without_thread_id_is_refused():
    """申请里没有 thread_id ⇒ 定位不到 checkpoint，显式失败而不是猜。"""
    with pytest.raises(ResumeError) as exc:
        await resume_hitl_run(thread_id="", approved=[_T1])
    assert exc.value.code == "no_thread_id"


@pytest.mark.asyncio
async def test_resume_without_pg_checkpointer_fails_closed(monkeypatch):
    """反向对照：没开 PG 开关必须**报错**，不能返回 200。

    内存 saver 是每请求新建的，跨请求恢复必然找不到挂起点。
    这里返回成功的话，人看到"恢复成功"却什么都没发生 —— 比报错难查得多。
    """
    monkeypatch.delenv("LG_RAG_HTTP_CHECKPOINTER", raising=False)
    with pytest.raises(ResumeError) as exc:
        await resume_hitl_run(thread_id="t-nopg", approved=[_T1])
    assert exc.value.code == "checkpointer_not_configured"


@pytest.mark.asyncio
async def test_empty_decision_is_refused():
    """既没批也没驳 ⇒ 不驱动恢复（空决定喂进去会静默按"驳回"收工）。"""
    with pytest.raises(ResumeError) as exc:
        await resume_hitl_run(thread_id="t-empty", approved=[], rejected=[])
    assert exc.value.code == "no_decision"


@pytest.mark.asyncio
async def test_default_graph_factory_keeps_the_injected_checkpointer():
    """默认工厂必须把 checkpointer 装进图。

    装漏了 ⇒ 恢复用的是**另一个** saver ⇒ 找不到挂起点 ⇒ 静默失败。
    这条是"恢复为什么找不到 checkpoint"的第一现场。
    """
    saver = InMemorySaver()
    graph = _default_graph_factory(checkpointer=saver)
    assert graph.checkpointer is saver


# ---------------------------------------------------------------------------
# 3 · 端点：把驱动结果按语义映射成状态码
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


def _drain(timeout: float = 5.0) -> None:
    """等 resume 后台执行沉降（在飞登记清空）。

    异步化（hitl-resume-async）后，端点秒回、执行在后台任务里；
    TestClient 的 portal loop 在另一线程推进，这里同步轮询即可。
    """
    import app.ops.hitl.router as router_mod

    deadline = time.monotonic() + timeout
    while getattr(router_mod, "_RESUME_IN_FLIGHT", {}) and time.monotonic() < deadline:
        time.sleep(0.02)
    assert not getattr(router_mod, "_RESUME_IN_FLIGHT", {}), "后台恢复未沉降"


def _approved_row(**kw) -> dict:
    base = {
        "id": new_request_id(),
        "run_id": _RUN,
        "thread_id": "t-api",
        "subtask_id": _T2,
        "unlock_subtask_id": _T1,
        "blocked_by": "prefix_touch_required",
        "status": STATUS_PENDING,
        "created_at": time.time(),
    }
    base.update(kw)
    return base


def test_resume_endpoint_drives_the_graph(monkeypatch):
    """批准 → 端点**调驱动器**，不是自己编一个"建议怎么恢复"的字典。

    异步化（hitl-resume-async）：端点秒回「已受理」，驱动结果经后台任务产出 ——
    响应断言受理形，outcome 断言沉降后对捕获值做（TC2b 授权适配）。
    """
    import asyncio

    store = InMemoryHitlStore()
    row = _approved_row()
    asyncio.run(store.acreate(row))
    asyncio.run(store.adecide(row["id"], decision=STATUS_APPROVED, by="张三"))

    seen: dict = {}
    outcomes: list[dict] = []

    async def _fake_resume(**kwargs):
        if kwargs.get("preflight_only"):
            return {"preflight": True}
        seen.update(kwargs)
        outcome = {"thread_id": kwargs["thread_id"], "state": {"route": "replan"}}
        outcomes.append(outcome)
        return outcome

    with (
        patch("app.ops.hitl.router.resume_hitl_run", new=_fake_resume),
        _client(monkeypatch, store) as client,
    ):
        res = client.post(f"/api/ops/hitl/requests/{row['id']}/resume")
        _drain()
    assert res.status_code == 200, res.text
    assert res.json()["resume"]["status"] == "accepted"
    assert seen["thread_id"] == "t-api"
    assert seen["approved"] == [_T1]
    assert seen["decided_by"] == "张三"
    assert outcomes and outcomes[0]["state"]["route"] == "replan"


def test_resume_endpoint_collects_every_approved_in_the_same_run(monkeypatch):
    """一次挂起里批了两条 ⇒ 恢复一次就要两条都生效。

    只带一条的话，图重跑一次又被剩下那条拦住、再挂起 ——
    人要连点两次，每次都以为"这次应该完了"。
    """
    import asyncio

    store = InMemoryHitlStore()
    a = _approved_row(unlock_subtask_id=_T1)
    b = _approved_row(subtask_id=_T2, unlock_subtask_id="runresume:0")
    for r in (a, b):
        asyncio.run(store.acreate(r))
        asyncio.run(store.adecide(r["id"], decision=STATUS_APPROVED, by="张三"))
    # 别的 run 的已批申请不许混进来
    other = _approved_row(id=new_request_id(), run_id="other-run", unlock_subtask_id="other:9")
    asyncio.run(store.acreate(other))
    asyncio.run(store.adecide(other["id"], decision=STATUS_APPROVED, by="张三"))

    seen: dict = {}

    async def _fake_resume(**kwargs):
        seen.update(kwargs)
        return {"state": {}}

    with (
        patch("app.ops.hitl.router.resume_hitl_run", new=_fake_resume),
        _client(monkeypatch, store) as client,
    ):
        res = client.post(f"/api/ops/hitl/requests/{a['id']}/resume")
    assert res.status_code == 200, res.text
    assert set(seen["approved"]) == {_T1, "runresume:0"}
    assert "other:9" not in seen["approved"]


def test_resume_endpoint_refuses_pending(monkeypatch):
    """还没决的申请不许恢复 —— 恢复了也是拿空决定去跑。"""
    import asyncio

    store = InMemoryHitlStore()
    row = _approved_row()
    asyncio.run(store.acreate(row))
    with _client(monkeypatch, store) as client:
        res = client.post(f"/api/ops/hitl/requests/{row['id']}/resume")
    assert res.status_code == 409
    assert STATUS_PENDING in res.json()["detail"]


def test_resume_endpoint_refuses_approved_without_unlock(monkeypatch):
    """已批但拿不到待解锁步骤 ⇒ 必须响。

    不响的话会拿着空 approved 去恢复 ⇒ 实际按"驳回"收工，
    人看到"批了但结果是没做"，而且没有任何报错。
    """
    import asyncio

    store = InMemoryHitlStore()
    row = _approved_row(unlock_subtask_id="")
    asyncio.run(store.acreate(row))
    asyncio.run(store.adecide(row["id"], decision=STATUS_APPROVED, by="张三"))
    with _client(monkeypatch, store) as client:
        res = client.post(f"/api/ops/hitl/requests/{row['id']}/resume")
    assert res.status_code == 409
    assert "unlock_subtask_id" in res.json()["detail"]


def test_resume_endpoint_rejection_also_resumes(monkeypatch):
    """驳回**也要**能调恢复：图正挂在 interrupt 上等人，
    只有批准能恢复的话，驳回之后那条 run 会永远停在等待授权那一帧。"""
    import asyncio

    store = InMemoryHitlStore()
    row = _approved_row()
    asyncio.run(store.acreate(row))
    asyncio.run(store.adecide(row["id"], decision=STATUS_REJECTED, by="李四"))

    seen: dict = {}

    async def _fake_resume(**kwargs):
        seen.update(kwargs)
        return {"state": {}}

    with (
        patch("app.ops.hitl.router.resume_hitl_run", new=_fake_resume),
        _client(monkeypatch, store) as client,
    ):
        res = client.post(f"/api/ops/hitl/requests/{row['id']}/resume")
    assert res.status_code == 200, res.text
    assert seen["approved"] == []
    assert seen["rejected"] == [_T2]


@pytest.mark.parametrize(
    "code,expected",
    [
        ("not_interrupted", 409),
        ("no_thread_id", 409),
        ("checkpointer_not_configured", 503),
        ("resume_failed", 502),
    ],
)
def test_resume_endpoint_maps_driver_errors(monkeypatch, code, expected):
    """驱动器失败码 → HTTP 状态码。一律 200 会让前端以为恢复了。"""
    import asyncio

    store = InMemoryHitlStore()
    row = _approved_row()
    asyncio.run(store.acreate(row))
    asyncio.run(store.adecide(row["id"], decision=STATUS_APPROVED, by="张三"))

    async def _boom(**_kwargs):
        raise ResumeError(code, f"boom-{code}")

    with (
        patch("app.ops.hitl.router.resume_hitl_run", new=_boom),
        _client(monkeypatch, store) as client,
    ):
        res = client.post(f"/api/ops/hitl/requests/{row['id']}/resume")
    assert res.status_code == expected, res.text


def test_resume_endpoint_404_on_unknown_request(monkeypatch):
    store = InMemoryHitlStore()
    with _client(monkeypatch, store) as client:
        res = client.post("/api/ops/hitl/requests/hitl_nope/resume")
    assert res.status_code == 404


def test_resume_driver_is_invocable_with_async_store_only():
    """台账：恢复路径只有异步接口（同步调会显式失败，不静默降级）。"""
    import inspect

    from app.ops.hitl import resume as resume_mod

    assert inspect.iscoroutinefunction(resume_mod.resume_hitl_run)
    assert not hasattr(resume_mod, "resume_hitl_run_sync")


# ---------------------------------------------------------------------------
# 4 · 管路：挂起那一次与恢复这一次必须落在**同一个** saver
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not DB_AVAILABLE, reason="PostgreSQL not available")
async def test_resume_across_two_saver_instances(monkeypatch):
    """跨**两个独立 saver 实例**恢复 —— 这才是生产的真实形状。

    请求 1（SSE）建一个 saver 跑图并挂起；请求 2（人点批准）是**另一个
    HTTP 请求**，建的是另一个 saver。内存 saver 下这条要么靠同一个对象
    蒙对、要么根本测不出来；只有在 PG 下它才是真的在考
    "挂起与恢复是否落在同一个 checkpointer 后端"。

    图用最小 observe 图（supervisor 图要真 LLM 才能跑起来），
    checkpointer 是**真的 AsyncPostgresSaver**。
    """
    import uuid

    from app.ops.lg_rag.checkpointer import apostgres_saver

    monkeypatch.setenv("LG_RAG_HTTP_CHECKPOINTER", "postgres")
    set_hitl_store(InMemoryHitlStore())
    tid = "t-pg-" + uuid.uuid4().hex[:12]

    suspended = None
    async with apostgres_saver(setup=True) as saver:
        graph = _graph_factory(checkpointer=saver)
        async for chunk in graph.astream(
            _hitl_state(),
            {"configurable": {"thread_id": tid}},
            stream_mode="updates",
        ):
            for intr in chunk.get("__interrupt__") or []:
                suspended = intr.value
    assert suspended is not None, "前置：图没有挂起"

    # 另一个 saver 实例（= 另一个请求）；图工厂相同，checkpointer 不同对象
    out = await resume_hitl_run(
        thread_id=tid,
        approved=[_T1],
        decided_by="张三",
        graph_factory=_graph_factory,
    )
    assert out["state"]["hitl_unlocked_ids"] == [_T1]
    assert out["state"]["react_observation"]["verdict"] == "replan"


@pytest.mark.skipif(not DB_AVAILABLE, reason="PostgreSQL not available")
async def test_resume_unknown_thread_under_pg_is_refused(monkeypatch):
    """反向对照：PG 下 thread 没挂起 ⇒ not_interrupted，不是"重开一局"。"""
    monkeypatch.setenv("LG_RAG_HTTP_CHECKPOINTER", "postgres")
    with pytest.raises(ResumeError) as exc:
        await resume_hitl_run(
            thread_id="t-pg-never-existed",
            approved=[_T1],
            graph_factory=_graph_factory,
        )
    assert exc.value.code == "not_interrupted"


async def test_supervisor_astream_entry_keeps_the_checkpointer():
    """SSE 那条路（挂起点产生的地方）必须把 checkpointer 装进图。

    装漏了 ⇒ 图照样跑、照样挂起，但 checkpoint 落在**另一个**（内存）saver 里；
    resume 端点拿着 PG saver 去找，找不到 ⇒ 报 not_interrupted ⇒
    人点"同意"之后什么都没发生。这一类失效单测跑图抓不到，只能卡管路。
    """
    from app.ops.lg_rag.multi.graph import astream_supervisor_agent

    sentinel = InMemorySaver()
    seen: dict = {}

    async def _fake_stream(graph, query, *, thread_id, history_turns=None, run_id=None):
        seen["graph"] = graph
        if False:  # pragma: no cover - 让它是个 async generator
            yield {}

    with patch("app.ops.lg_rag.multi.graph._astream_with_tracing", new=_fake_stream):
        async for _ in astream_supervisor_agent("q", thread_id="t-plumb", checkpointer=sentinel):
            pass
    assert "graph" in seen
    assert seen["graph"].checkpointer is sentinel
