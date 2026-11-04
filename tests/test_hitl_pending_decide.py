"""HITL 浏览器决策面：``GET /hitl/pending`` + ``POST /hitl/requests/{id}/decide``。

B2（hitl-browser-decide · 裁定 D1/E1）：浏览器拿不到 HMAC 密钥，OA 签名面
对前端零表现——所以新增 cookie maintainer 两个端点，密钥不出服务器。

这个文件钉住的语义：

- **鉴权（D1）**：纯 cookie + ``role=='maintainer'``——未登录 401 · 非 maintainer 403；
  与 OA 签名面（HMAC）和 ``resume``（AdminSyncAuth，零改动）互不复用。
- **归属（E1）**：申请行没有 user_id，归属经 ``run_id`` → 事件表 ``run_owner``
  反查；异 owner 的 pending 不出现、decide 404（不泄露存在性）；
  归属解析不到 → 排除 / 404 + **error 日志**，绝不 500、绝不猜 user_id。
- **decide 语义**：与 OA callback 同语义（复用 ``adecide`` 的 pending 守卫）——
  重复 409、未知 404、非法 decision 422；**不自动 resume**（两步钉死，
  恢复复用既有 ``POST .../resume``）。
- **全链**：挂起 run → decide → resume → 图真的继续跑（图替身，对齐
  ``tests/test_hitl_resume.py`` harness）；``OPS_HITL_PERSISTENCE=db`` 下
  decide 落库 → 重建 store（模拟重启）→ resume 读到已决（N2 · DB 门控）。

审计纪律：``logger.info`` 只记动作锚点（id/decision/by/at），不记内容。
"""

from __future__ import annotations

import asyncio
import logging
import time
from unittest.mock import AsyncMock, patch

import pytest
from langchain_core.messages import HumanMessage
from langgraph.checkpoint.memory import InMemorySaver

from app.db.models import OpsUser
from app.ops.hitl import new_request_id
from app.ops.hitl.persistence import reset_hitl_store, set_hitl_store
from app.ops.hitl.store import (
    STATUS_APPROVED,
    STATUS_PENDING,
    STATUS_REJECTED,
    InMemoryHitlStore,
    NullHitlStore,
)
from tests.conftest import DB_AVAILABLE
from tests.test_hitl_resume import _drain

_MAINTAINER = OpsUser(
    id="00000000-0000-0000-0000-000000000001", username="admin", role="maintainer"
)
_VIEWER = OpsUser(id="00000000-0000-0000-0000-000000000002", username="viewer", role="viewer")
_OTHER_USER_ID = "00000000-0000-0000-0000-000000000099"

_RUN = "rundecide"
_T1 = f"{_RUN}:1"
_T2 = f"{_RUN}:2"
_TOOL = "mock_get_issue_status"


@pytest.fixture(autouse=True)
def _isolate():
    reset_hitl_store()
    yield
    reset_hitl_store()


# ---------------------------------------------------------------------------
# 测试夹具：cookie 鉴权 override + store 装配 + 图替身
# ---------------------------------------------------------------------------


def _as_user(user):
    """cookie 用户 override：``@wraps`` 让 FastAPI 沿用原签名（request, db），
    ``require_admin_sync`` 的 ``_resolve_cookie_user`` 又会按 ``(request, db)``
    位置参数直调 —— 两种调用形态都兼容。"""
    from functools import wraps

    from app.ops.deps import get_current_user

    @wraps(get_current_user)
    async def _fake(*args, **kwargs):
        return user

    return _fake


def _client(store, *, user=None):
    """裸 FastAPI app + hitl router；``user=None`` 即不带 cookie（未登录）。

    cookie 面端点（pending/decide）经 ``require_maintainer`` → ``get_current_user``，
    resume 经 ``require_admin_sync`` → cookie 路径同样走 ``get_current_user``，
    所以 override 这一个依赖即可同时覆盖两种鉴权。
    """
    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    from app.ops.deps import get_current_user
    from app.ops.hitl.router import router

    set_hitl_store(store)
    app = FastAPI()
    app.include_router(router, prefix="/api/ops")
    if user is not None:
        app.dependency_overrides[get_current_user] = _as_user(user)
    return TestClient(app)


def _bare_app(*, user):
    """DB 用例用：AsyncClient 与测试同一事件循环，避免跨 loop 的 asyncpg 连接。"""
    from fastapi import FastAPI

    from app.ops.deps import get_current_user
    from app.ops.hitl.router import router

    app = FastAPI()
    app.include_router(router, prefix="/api/ops")
    app.dependency_overrides[get_current_user] = _as_user(user)
    return app


def _row(**kw) -> dict:
    base = {
        "id": new_request_id(),
        "run_id": _RUN,
        "thread_id": "t-decide",
        "subtask_id": _T2,
        "unlock_subtask_id": _T1,
        "blocked_by": "prefix_touch_required",
        # api-w-hitl-tenant-fix（裁决①③）：新单须带租户戳，空 tenant fail-closed
        # 拒 resume —— fixture 按 A 补齐（本文件测 decide/resume 状态机，租户默认）。
        "tenant_id": "ops-desk-pilot",
        "reason": "需要重跑已执行步骤",
        "status": STATUS_PENDING,
        "created_at": time.time(),
    }
    base.update(kw)
    return base


def _owner_map(mapping: dict[str, str | None]):
    """run_id → user_id 的 run_owner 替身（None = 归属解析不到）。"""

    async def _fake(run_id: str):
        return mapping.get(run_id)

    return _fake


# --- 图替身（对齐 tests/test_hitl_resume.py 的最小 observe 图）---


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


def _hitl_state(**kw) -> dict:
    """T2 被 ``prefix_touch_required`` 拦住，要解锁的是已执行的 T1。"""
    base = {
        "messages": [HumanMessage(content="复合问题")],
        "run_id": _RUN,
        "thread_id": "t-decide",
        "allowed_capability_ids": [_TOOL],
        "supervisor_step_count": 1,
        "host_subtask_seq": 2,
        "react_round": 0,
        "inflight_subtask_ids": [],
        "subtasks": [_plan_row(_T1), _plan_row(_T2, depends_on=[_T1])],
        "subtask_results": [
            {"subtask_id": _T1, "type": "tool", "output": {"assignee": "张三"}},
            {
                "subtask_id": _T2,
                "type": "tool",
                "error": "需要重跑已执行步骤",
                "blocked_by": "prefix_touch_required",
                "hitl_required": True,
            },
        ],
        "plan_prefix_ids": [_T1],
    }
    base.update(kw)
    return base


def _graph_factory(*, checkpointer):
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
# 1 · 鉴权（裁定 D1）：未登录 401 · 非 maintainer 403
# ---------------------------------------------------------------------------


def test_pending_requires_login_401():
    with _client(InMemoryHitlStore()) as client:
        assert client.get("/api/ops/hitl/pending").status_code == 401


def test_pending_viewer_is_403():
    with _client(InMemoryHitlStore(), user=_VIEWER) as client:
        assert client.get("/api/ops/hitl/pending").status_code == 403


def test_decide_requires_login_401():
    with _client(InMemoryHitlStore()) as client:
        res = client.post("/api/ops/hitl/requests/hitl_x/decide", json={"decision": "approved"})
    assert res.status_code == 401


def test_decide_viewer_is_403():
    with _client(InMemoryHitlStore(), user=_VIEWER) as client:
        res = client.post("/api/ops/hitl/requests/hitl_x/decide", json={"decision": "approved"})
    assert res.status_code == 403


# ---------------------------------------------------------------------------
# 2 · pending 列表：归属过滤（裁定 E1）+ 字段族 + 降级不 500
# ---------------------------------------------------------------------------


def test_pending_lists_only_own_runs_with_field_family():
    """正向：只返回 run_owner == 当前用户的 pending；字段族齐；created_at 非空（N4：
    InMemory 是 float、Db 是 ISO 字符串，两后端类型不同，只断「非空」）。"""
    store = InMemoryHitlStore()
    mine = _row(run_id="run-mine")
    other = _row(run_id="run-other")
    asyncio.run(store.acreate(mine))
    asyncio.run(store.acreate(other))
    owner = _owner_map({"run-mine": str(_MAINTAINER.id), "run-other": _OTHER_USER_ID})

    with (
        patch("app.ops.lg_rag.event_store.run_owner", new=owner),
        _client(store, user=_MAINTAINER) as client,
    ):
        res = client.get("/api/ops/hitl/pending")
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["count"] == 1
    assert [item["id"] for item in body["items"]] == [mine["id"]]
    item = body["items"][0]
    assert set(item.keys()) == {"id", "run_id", "thread_id", "reason", "blocked_by", "created_at"}
    assert item["created_at"], "created_at 必须非空（两后端类型不同，不断具体类型）"


def test_pending_excludes_unresolvable_owner_with_error_log(caplog):
    """N2 机断：run_owner 解析不到 → 该条排除 + error 日志 · 不 500 · 不泄露。"""
    store = InMemoryHitlStore()
    row = _row(run_id="run-ghost")
    asyncio.run(store.acreate(row))
    owner = _owner_map({"run-ghost": None})

    with (
        patch("app.ops.lg_rag.event_store.run_owner", new=owner),
        caplog.at_level(logging.ERROR, logger="app.ops.hitl.router"),
        _client(store, user=_MAINTAINER) as client,
    ):
        res = client.get("/api/ops/hitl/pending")
    assert res.status_code == 200, res.text
    assert res.json() == {"items": [], "count": 0}
    errors = [r for r in caplog.records if r.levelno >= logging.ERROR]
    assert errors, "归属解析不到必须打 error 日志，不能静默吞掉"
    assert any("run-ghost" in r.getMessage() for r in errors)


def test_pending_owner_lookup_exception_does_not_500(caplog):
    """归属反查本身抛异常 → 同样排除 + error 日志，不 500。"""

    async def _boom(_run_id):
        raise RuntimeError("db down")

    store = InMemoryHitlStore()
    asyncio.run(store.acreate(_row(run_id="run-boom")))
    with (
        patch("app.ops.lg_rag.event_store.run_owner", new=_boom),
        caplog.at_level(logging.ERROR, logger="app.ops.hitl.router"),
        _client(store, user=_MAINTAINER) as client,
    ):
        res = client.get("/api/ops/hitl/pending")
    assert res.status_code == 200, res.text
    assert res.json() == {"items": [], "count": 0}
    assert any(r.levelno >= logging.ERROR for r in caplog.records)


def test_pending_null_store_returns_empty_list():
    """null store（未配持久化）→ 空列表，不 500。"""
    with _client(NullHitlStore(), user=_MAINTAINER) as client:
        res = client.get("/api/ops/hitl/pending")
    assert res.status_code == 200, res.text
    assert res.json() == {"items": [], "count": 0}


def test_pending_alist_failure_degrades_to_empty_list(caplog):
    """store.alist 本身故障 → 空列表降级 + 日志，不 500。"""

    class _BrokenStore(NullHitlStore):
        async def alist(self, **_kw):
            raise RuntimeError("db down")

    with (
        caplog.at_level(logging.ERROR, logger="app.ops.hitl.router"),
        _client(_BrokenStore(), user=_MAINTAINER) as client,
    ):
        res = client.get("/api/ops/hitl/pending")
    assert res.status_code == 200, res.text
    assert res.json() == {"items": [], "count": 0}
    assert any(r.levelno >= logging.ERROR for r in caplog.records)


# ---------------------------------------------------------------------------
# 3 · decide：语义 / 边界 / 审计 / 不自动 resume
# ---------------------------------------------------------------------------


def test_decide_approved_marks_decided_and_audits(caplog):
    """decide approved → store 行 status=approved · decision_by=当前用户 ·
    decided_at 非空；审计日志只记动作锚点（与 callback 同语义）。"""
    store = InMemoryHitlStore()
    row = _row()
    asyncio.run(store.acreate(row))
    owner = _owner_map({_RUN: str(_MAINTAINER.id)})

    with (
        patch("app.ops.lg_rag.event_store.run_owner", new=owner),
        caplog.at_level(logging.INFO, logger="app.ops.hitl.router"),
        _client(store, user=_MAINTAINER) as client,
    ):
        res = client.post(
            f"/api/ops/hitl/requests/{row['id']}/decide",
            json={"decision": "approved", "note": "同意重跑"},
        )
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["ok"] is True
    assert body["request"]["status"] == STATUS_APPROVED
    assert body["request"]["decision_by"] == "admin"
    assert body["request"]["decided_at"], "decided_at 必须非空"
    # 两步钉死：响应必须说出「还有第二步 resume」
    assert body["resume"]["required"] is True
    assert body["resume"]["endpoint"].endswith(f"/requests/{row['id']}/resume")
    # 审计锚点：id / decision / by
    infos = [r.getMessage() for r in caplog.records if r.levelno == logging.INFO]
    assert any(row["id"] in m and "approved" in m and "admin" in m for m in infos)
    # store 层同样已决
    saved = asyncio.run(store.aget(row["id"]))
    assert saved["status"] == STATUS_APPROVED
    assert saved["decision_by"] == "admin"


def test_decide_does_not_auto_resume():
    """decide 只置已决，**不触发** resume（SPEC Q2 两步钉死）。"""
    store = InMemoryHitlStore()
    row = _row()
    asyncio.run(store.acreate(row))
    owner = _owner_map({_RUN: str(_MAINTAINER.id)})
    spy = AsyncMock()

    with (
        patch("app.ops.lg_rag.event_store.run_owner", new=owner),
        patch("app.ops.hitl.router.resume_hitl_run", new=spy),
        _client(store, user=_MAINTAINER) as client,
    ):
        res = client.post(
            f"/api/ops/hitl/requests/{row['id']}/decide", json={"decision": "approved"}
        )
    assert res.status_code == 200, res.text
    spy.assert_not_called()


def test_decide_unknown_id_404():
    with _client(InMemoryHitlStore(), user=_MAINTAINER) as client:
        res = client.post("/api/ops/hitl/requests/hitl_nope/decide", json={"decision": "approved"})
    assert res.status_code == 404


def test_decide_other_users_run_is_404_not_leaked():
    """越权：他人 run 的 request_id → 404（不泄露存在性，FP-1 口径）。"""
    store = InMemoryHitlStore()
    row = _row()
    asyncio.run(store.acreate(row))
    owner = _owner_map({_RUN: _OTHER_USER_ID})
    with (
        patch("app.ops.lg_rag.event_store.run_owner", new=owner),
        _client(store, user=_MAINTAINER) as client,
    ):
        res = client.post(
            f"/api/ops/hitl/requests/{row['id']}/decide", json={"decision": "approved"}
        )
    assert res.status_code == 404
    # 申请必须原样还在（没被别人决掉）
    assert asyncio.run(store.aget(row["id"]))["status"] == STATUS_PENDING


def test_decide_unresolvable_owner_is_404_with_error_log(caplog):
    """decide 路径上归属不可判定同样拒（视同非本人）+ error 日志，不 500。"""
    store = InMemoryHitlStore()
    row = _row(run_id="run-ghost")
    asyncio.run(store.acreate(row))
    owner = _owner_map({"run-ghost": None})
    with (
        patch("app.ops.lg_rag.event_store.run_owner", new=owner),
        caplog.at_level(logging.ERROR, logger="app.ops.hitl.router"),
        _client(store, user=_MAINTAINER) as client,
    ):
        res = client.post(
            f"/api/ops/hitl/requests/{row['id']}/decide", json={"decision": "approved"}
        )
    assert res.status_code == 404
    assert asyncio.run(store.aget(row["id"]))["status"] == STATUS_PENDING
    assert any(r.levelno >= logging.ERROR for r in caplog.records)


def test_decide_duplicate_is_409():
    """重复 decide / 已决 → 409（与 callback 同一判据：adecide 返回 None）。"""
    store = InMemoryHitlStore()
    row = _row()
    asyncio.run(store.acreate(row))
    owner = _owner_map({_RUN: str(_MAINTAINER.id)})
    with (
        patch("app.ops.lg_rag.event_store.run_owner", new=owner),
        _client(store, user=_MAINTAINER) as client,
    ):
        first = client.post(
            f"/api/ops/hitl/requests/{row['id']}/decide", json={"decision": "approved"}
        )
        again = client.post(
            f"/api/ops/hitl/requests/{row['id']}/decide", json={"decision": "rejected"}
        )
    assert first.status_code == 200, first.text
    assert again.status_code == 409, again.text
    # 第一次的决定没被第二次覆盖
    saved = asyncio.run(store.aget(row["id"]))
    assert saved["status"] == STATUS_APPROVED
    assert saved["decision_by"] == "admin"


def test_decide_invalid_decision_is_422():
    store = InMemoryHitlStore()
    with _client(store, user=_MAINTAINER) as client:
        bad = client.post("/api/ops/hitl/requests/hitl_x/decide", json={"decision": "maybe"})
        missing = client.post("/api/ops/hitl/requests/hitl_x/decide", json={})
    assert bad.status_code == 422
    assert missing.status_code == 422


# ---------------------------------------------------------------------------
# 4 · decide → resume 全链（图替身，对齐 tests/test_hitl_resume.py harness）
# ---------------------------------------------------------------------------


def _resume_via(saver, outcomes: list | None = None):
    """把端点里的 resume_hitl_run 换成「真驱动器 + 注入内存 saver/图替身」。

    异步化后端点秒回「已受理」：给 outcomes 时把**执行调用**的 outcome 捕获
    下来（preflight 探针调用不记），供 drain 后断言图真的跑完。
    """
    from app.ops.hitl.resume import resume_hitl_run as real

    async def _wrapped(**kw):
        out = await real(checkpointer=saver, graph_factory=_graph_factory, **kw)
        if outcomes is not None and not kw.get("preflight_only"):
            outcomes.append(out)
        return out

    return _wrapped


async def _adrain(timeout: float = 10.0) -> None:
    """异步排干 resume 后台任务（与 AsyncClient 同一 loop，只能让出协程）。"""
    import app.ops.hitl.router as router_mod

    deadline = time.monotonic() + timeout
    while getattr(router_mod, "_RESUME_IN_FLIGHT", {}) and time.monotonic() < deadline:
        await asyncio.sleep(0.02)
    assert not getattr(router_mod, "_RESUME_IN_FLIGHT", {}), "后台恢复未沉降"


def test_decide_approved_then_resume_drives_the_graph():
    """全链正向：挂起 run → decide(approved) → 既有 resume → 解锁 + 重规划。"""
    store = InMemoryHitlStore()
    saver = InMemorySaver()
    payload = asyncio.run(_suspend(_hitl_state(), saver, "t-chain"))
    assert payload is not None, "前置：图没有被挂起"
    row = _row(thread_id="t-chain")
    asyncio.run(store.acreate(row))
    owner = _owner_map({_RUN: str(_MAINTAINER.id)})
    outcomes: list = []

    with (
        patch("app.ops.lg_rag.event_store.run_owner", new=owner),
        patch("app.ops.hitl.router._open_event_sink", new=AsyncMock(return_value=None)),
        patch("app.ops.hitl.router.resume_hitl_run", new=_resume_via(saver, outcomes)),
        _client(store, user=_MAINTAINER) as client,
    ):
        decided = client.post(
            f"/api/ops/hitl/requests/{row['id']}/decide", json={"decision": "approved"}
        )
        assert decided.status_code == 200, decided.text
        resumed = client.post(f"/api/ops/hitl/requests/{row['id']}/resume")
        _drain()
    assert resumed.status_code == 200, resumed.text
    # 异步化（hitl-resume-async）：受理响应只承诺「已受理」，驱动结果在后台 ——
    # 响应断言受理形，outcome 断言沉降后对捕获值做（TC2b 授权适配）。
    assert resumed.json()["resume"]["status"] == "accepted"
    assert outcomes, "后台恢复没有执行"
    state = outcomes[0]["state"]
    assert state["hitl_unlocked_ids"] == [_T1], "批准了却没解锁"
    assert state["react_observation"]["verdict"] == "replan"


def test_decide_rejected_then_resume_settles():
    """全链反向：decide(rejected) → resume → 收工出结论（「没批」语义 · 不解锁）。"""
    store = InMemoryHitlStore()
    saver = InMemorySaver()
    asyncio.run(_suspend(_hitl_state(), saver, "t-chain-rej"))
    row = _row(thread_id="t-chain-rej")
    asyncio.run(store.acreate(row))
    owner = _owner_map({_RUN: str(_MAINTAINER.id)})
    outcomes: list = []

    with (
        patch("app.ops.lg_rag.event_store.run_owner", new=owner),
        patch("app.ops.hitl.router._open_event_sink", new=AsyncMock(return_value=None)),
        patch("app.ops.hitl.router.resume_hitl_run", new=_resume_via(saver, outcomes)),
        _client(store, user=_MAINTAINER) as client,
    ):
        decided = client.post(
            f"/api/ops/hitl/requests/{row['id']}/decide", json={"decision": "rejected"}
        )
        assert decided.status_code == 200, decided.text
        assert decided.json()["request"]["status"] == STATUS_REJECTED
        resumed = client.post(f"/api/ops/hitl/requests/{row['id']}/resume")
        _drain()
    assert resumed.status_code == 200, resumed.text
    # 异步化（hitl-resume-async）：受理响应只承诺「已受理」（TC2b 授权适配）。
    assert resumed.json()["resume"]["status"] == "accepted"
    assert outcomes, "后台恢复没有执行"
    state = outcomes[0]["state"]
    assert state["hitl_unlocked_ids"] == [], "驳回却解锁了 —— 授权与拒绝不分"
    assert state["react_observation"]["verdict"] == "settle"


# ---------------------------------------------------------------------------
# 5 · N3：OA 面 /runtime 回归（本文件点名跑绿）
# ---------------------------------------------------------------------------


def test_hitl_runtime_endpoint_intact():
    """/hitl/runtime（AdminSyncAuth · 观测面）不受新端点影响。"""
    with _client(InMemoryHitlStore(), user=_MAINTAINER) as client:
        res = client.get("/api/ops/hitl/runtime")
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["mode"] == "memory"
    assert body["persists"] is True
    assert "callback_secret_configured" in body


# ---------------------------------------------------------------------------
# 6 · N2 持久化路径：db 下 decide 落库 → 重建 store（模拟重启）→ resume 读到已决
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not DB_AVAILABLE, reason="PostgreSQL not available")
async def test_db_decide_survives_store_rebuild_then_resume(monkeypatch):
    """``OPS_HITL_PERSISTENCE=db`` 全链：decide 落库 → 重建 store（= 进程重启）→
    resume 读到已决并驱动真 PG checkpoint 上的挂起图跑完。

    与内存全链的差别：这条的 store / run_owner / checkpointer 全是**真 PG**，
    「重启」用 reset + 重新 configure 模拟——重启后内存 store 会丢申请，
    db store 必须还在。
    """
    import uuid

    from httpx import ASGITransport, AsyncClient
    from sqlalchemy import text

    from app.db.session import AsyncSessionLocal
    from app.ops.hitl.persistence import configure_hitl_from_env, get_hitl_store
    from app.ops.lg_rag.checkpointer import apostgres_saver
    from app.ops.lg_rag.event_store import persist_run_event

    suffix = uuid.uuid4().hex[:10]
    run_id = f"rundb-{suffix}"
    tid = f"t-db-{suffix}"
    rid = f"hitl_db_{suffix}"

    monkeypatch.setenv("OPS_HITL_PERSISTENCE", "db")
    monkeypatch.setenv("LG_RAG_HTTP_CHECKPOINTER", "postgres")
    reset_hitl_store()
    assert configure_hitl_from_env() == "db"

    # 事件表 user_id 有 FK → ops_users：先落一个真用户行（override 用户用同一 id）
    async with AsyncSessionLocal() as db:
        db.add(OpsUser(id=str(_MAINTAINER.id), username=f"hitl-db-{suffix}", role="maintainer"))
        await db.commit()

    # 归属真源：事件表落一帧（user_id = 当前 maintainer）——E1 反查靠它
    await persist_run_event(
        run_id=run_id,
        seq=1,
        user_id=str(_MAINTAINER.id),
        thread_id=tid,
        ts_ms=0,
        agent_role="system",
        event_type="run.start",
        payload={},
    )

    # 挂起图（真 PG checkpointer）
    async with apostgres_saver(setup=True) as saver:
        graph = _graph_factory(checkpointer=saver)
        suspended = None
        async for chunk in graph.astream(
            _hitl_state(run_id=run_id, thread_id=tid),
            {"configurable": {"thread_id": tid}},
            stream_mode="updates",
        ):
            for intr in chunk.get("__interrupt__") or []:
                suspended = intr.value
    assert suspended is not None, "前置：图没有被挂起"

    await get_hitl_store().acreate(
        {
            "id": rid,
            "run_id": run_id,
            "thread_id": tid,
            "checkpoint_id": None,
            # api-w-hitl-tenant-fix（裁决①③）：空 tenant 现 fail-closed 拒 resume；
            # 本用例测 store rebuild 存活链，tenant 取默认 A（原 '' 为 incidental）。
            "tenant_id": "ops-desk-pilot",
            "subtask_id": _T2,
            "blocked_by": "prefix_touch_required",
            "unlock_subtask_id": _T1,
            "reason": "需要重跑已执行步骤",
            "detail": "",
            "payload": {},
            "status": STATUS_PENDING,
        }
    )

    app = _bare_app(user=_MAINTAINER)
    transport = ASGITransport(app=app)
    try:
        # ① decide（cookie maintainer · 真 db store · 真 run_owner）
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            res = await client.post(
                f"/api/ops/hitl/requests/{rid}/decide", json={"decision": "approved"}
            )
        assert res.status_code == 200, res.text
        assert res.json()["request"]["status"] == STATUS_APPROVED

        # ② 模拟重启：重建 store（新实例），已决必须还在库里
        reset_hitl_store()
        assert configure_hitl_from_env() == "db"
        row = await get_hitl_store().aget(rid)
        assert row is not None, "重启后申请丢了 —— db 持久化失效"
        assert row["status"] == STATUS_APPROVED
        assert row["decision_by"] == "admin"
        assert row["decided_at"], "decided_at 非空（N4：Db 后端是 ISO 字符串，只断非空）"

        # ③ resume（既有端点 · 真 PG checkpointer 找到挂起点 · 图替身避免真 LLM）
        from app.ops.hitl.resume import resume_hitl_run as _real_resume

        outcomes: list = []

        async def _resume_minimal_graph(**kw):
            # checkpointer 不传 → 按 env 走真 PG；只换图工厂（最小 observe 图）
            out = await _real_resume(graph_factory=_graph_factory, **kw)
            if not kw.get("preflight_only"):
                outcomes.append(out)
            return out

        with patch("app.ops.hitl.router.resume_hitl_run", new=_resume_minimal_graph):
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                res2 = await client.post(f"/api/ops/hitl/requests/{rid}/resume")
                await _adrain()
        assert res2.status_code == 200, res2.text
        # 异步化（hitl-resume-async）：受理响应只承诺「已受理」（TC2b 授权适配）。
        assert res2.json()["resume"]["status"] == "accepted"
        assert outcomes, "后台恢复没有执行"
        state = outcomes[0]["state"]
        assert state["hitl_unlocked_ids"] == [_T1]
        assert state["react_observation"]["verdict"] == "replan"
    finally:
        async with AsyncSessionLocal() as db:
            await db.execute(text("DELETE FROM ops_hitl_requests WHERE id = :i"), {"i": rid})
            await db.execute(
                text("DELETE FROM ops_lg_rag_run_events WHERE run_id = :r"), {"r": run_id}
            )
            await db.execute(
                text("DELETE FROM ops_users WHERE id = :u"), {"u": str(_MAINTAINER.id)}
            )
            await db.commit()
