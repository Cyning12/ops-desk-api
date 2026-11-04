"""HITL decide 归属反查无帧兜底（fix-hitl-decide-owner-fallback · B+C 签认）。

背景（issue #315）：sync ``POST /api/ops/lg-rag/invoke`` 触发写闸时拦单正常落库，
但 sync invoke **不落 run 事件帧**（事件帧是 SSE RunWorker 路径专属产物），
``_run_owner_of`` → ``event_store.run_owner`` 反查返回 None → decide 404
「申请不存在」，审批链断、单据滞留 pending。

本文件钉死的语义（task_fix_hitl_decide_owner_fallback 钉死契约）：

- **负样本①（维护者红线）**：无帧 run（``run_owner`` → None）且单据
  ``thread_id`` 归属当前 maintainer → decide **不再 404**（200 进入
  ``adecide`` 正常语义 · approved / rejected 均验证）· pending 列表可见。
- **负样本②（不越权）**：无帧 + thread 归属**他人** → decide 仍 404
  （不泄露存在性 · FP-1 口径不破）· 单据保持 pending。
- **负样本③（fail-closed）**：无帧 + thread 行缺失 → decide 仍 404 + error
  日志 · 绝不猜 user_id。
- **正样本零漂移**：有帧 run（``run_owner`` 返真值）→ **绝不走兜底**
  （事件表是第一真源 · thread 反查 mock 断言未被调用）· 行为逐字节不变。
- **降级**：兜底反查本身抛异常 → 404 + error 日志 · 不 500。
"""

from __future__ import annotations

import asyncio
import logging
from unittest.mock import AsyncMock, patch

import pytest

from app.ops.hitl.store import STATUS_APPROVED, STATUS_PENDING, STATUS_REJECTED, InMemoryHitlStore
from tests.conftest import DB_AVAILABLE
from tests.test_hitl_pending_decide import (
    _MAINTAINER,
    _OTHER_USER_ID,
    _client,
    _owner_map,
    _row,
)

_NOFRAMES_RUN = "runnoframes"


@pytest.fixture(autouse=True)
def _isolate():
    from app.ops.hitl.persistence import reset_hitl_store

    reset_hitl_store()
    yield
    reset_hitl_store()


def _thread_owner_map(mapping: dict[str, str | None]):
    """thread_id → user_id 的 thread_owner 替身（None = thread 行缺失）。"""

    async def _fake(thread_id: str):
        return mapping.get(thread_id)

    return _fake


# ---------------------------------------------------------------------------
# 负样本①（维护者红线）：无帧 run + thread 归属本人 → decide 不再 404
# ---------------------------------------------------------------------------


def test_decide_frameless_run_falls_back_to_thread_owner_approved():
    """sync invoke 面写闸单（无事件帧）：decide(approved) 200 不再 404。"""
    store = InMemoryHitlStore()
    row = _row(run_id=_NOFRAMES_RUN, thread_id="t-fallback-ok")
    asyncio.run(store.acreate(row))
    owner = _owner_map({_NOFRAMES_RUN: None})
    thread_owner = _thread_owner_map({"t-fallback-ok": str(_MAINTAINER.id)})

    with (
        patch("app.ops.lg_rag.event_store.run_owner", new=owner),
        patch("app.ops.lg_rag.thread_store.thread_owner", new=thread_owner),
        _client(store, user=_MAINTAINER) as client,
    ):
        res = client.post(
            f"/api/ops/hitl/requests/{row['id']}/decide", json={"decision": "approved"}
        )
    assert res.status_code == 200, res.text
    assert res.json()["request"]["status"] == STATUS_APPROVED
    assert asyncio.run(store.aget(row["id"]))["status"] == STATUS_APPROVED


def test_decide_frameless_run_falls_back_to_thread_owner_rejected():
    """兜底不止放行 approved——rejected 同样可达（adecide 全语义）。"""
    store = InMemoryHitlStore()
    row = _row(run_id=_NOFRAMES_RUN, thread_id="t-fallback-ok")
    asyncio.run(store.acreate(row))
    owner = _owner_map({_NOFRAMES_RUN: None})
    thread_owner = _thread_owner_map({"t-fallback-ok": str(_MAINTAINER.id)})

    with (
        patch("app.ops.lg_rag.event_store.run_owner", new=owner),
        patch("app.ops.lg_rag.thread_store.thread_owner", new=thread_owner),
        _client(store, user=_MAINTAINER) as client,
    ):
        res = client.post(
            f"/api/ops/hitl/requests/{row['id']}/decide", json={"decision": "rejected"}
        )
    assert res.status_code == 200, res.text
    assert res.json()["request"]["status"] == STATUS_REJECTED


def test_pending_lists_frameless_run_via_thread_fallback():
    """pending 列表与 decide 同源受益：无帧单据对 thread 属主可见（decide 前置）。"""
    store = InMemoryHitlStore()
    row = _row(run_id=_NOFRAMES_RUN, thread_id="t-fallback-ok")
    asyncio.run(store.acreate(row))
    owner = _owner_map({_NOFRAMES_RUN: None})
    thread_owner = _thread_owner_map({"t-fallback-ok": str(_MAINTAINER.id)})

    with (
        patch("app.ops.lg_rag.event_store.run_owner", new=owner),
        patch("app.ops.lg_rag.thread_store.thread_owner", new=thread_owner),
        _client(store, user=_MAINTAINER) as client,
    ):
        res = client.get("/api/ops/hitl/pending")
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["count"] == 1
    assert [item["id"] for item in body["items"]] == [row["id"]]


# ---------------------------------------------------------------------------
# 负样本②：无帧 + thread 归属他人 → 仍 404 不越权
# ---------------------------------------------------------------------------


def test_decide_frameless_thread_owned_by_other_still_404():
    store = InMemoryHitlStore()
    row = _row(run_id=_NOFRAMES_RUN, thread_id="t-fallback-other")
    asyncio.run(store.acreate(row))
    owner = _owner_map({_NOFRAMES_RUN: None})
    thread_owner = _thread_owner_map({"t-fallback-other": _OTHER_USER_ID})

    with (
        patch("app.ops.lg_rag.event_store.run_owner", new=owner),
        patch("app.ops.lg_rag.thread_store.thread_owner", new=thread_owner),
        _client(store, user=_MAINTAINER) as client,
    ):
        res = client.post(
            f"/api/ops/hitl/requests/{row['id']}/decide", json={"decision": "approved"}
        )
    assert res.status_code == 404
    # 申请必须原样还在（没被别人决掉）
    assert asyncio.run(store.aget(row["id"]))["status"] == STATUS_PENDING


# ---------------------------------------------------------------------------
# 负样本③：无帧 + thread 行缺失 → 仍 404（fail-closed · error 日志）
# ---------------------------------------------------------------------------


def test_decide_frameless_no_thread_row_still_404_fail_closed(caplog):
    store = InMemoryHitlStore()
    row = _row(run_id=_NOFRAMES_RUN, thread_id="t-fallback-missing")
    asyncio.run(store.acreate(row))
    owner = _owner_map({_NOFRAMES_RUN: None})
    thread_owner = _thread_owner_map({})

    with (
        patch("app.ops.lg_rag.event_store.run_owner", new=owner),
        patch("app.ops.lg_rag.thread_store.thread_owner", new=thread_owner),
        caplog.at_level(logging.ERROR, logger="app.ops.hitl.router"),
        _client(store, user=_MAINTAINER) as client,
    ):
        res = client.post(
            f"/api/ops/hitl/requests/{row['id']}/decide", json={"decision": "approved"}
        )
    assert res.status_code == 404
    assert asyncio.run(store.aget(row["id"]))["status"] == STATUS_PENDING
    assert any(r.levelno >= logging.ERROR for r in caplog.records), "fail-closed 必须留痕"


def test_decide_frameless_thread_lookup_exception_does_not_500(caplog):
    """兜底反查本身抛异常 → 404 降级 + error 日志，不 500。"""

    async def _boom(_thread_id):
        raise RuntimeError("db down")

    store = InMemoryHitlStore()
    row = _row(run_id=_NOFRAMES_RUN, thread_id="t-fallback-boom")
    asyncio.run(store.acreate(row))
    owner = _owner_map({_NOFRAMES_RUN: None})

    with (
        patch("app.ops.lg_rag.event_store.run_owner", new=owner),
        patch("app.ops.lg_rag.thread_store.thread_owner", new=_boom),
        caplog.at_level(logging.ERROR, logger="app.ops.hitl.router"),
        _client(store, user=_MAINTAINER) as client,
    ):
        res = client.post(
            f"/api/ops/hitl/requests/{row['id']}/decide", json={"decision": "approved"}
        )
    assert res.status_code == 404
    assert asyncio.run(store.aget(row["id"]))["status"] == STATUS_PENDING
    assert any(r.levelno >= logging.ERROR for r in caplog.records)


# ---------------------------------------------------------------------------
# 正样本零漂移：有帧 run 绝不走兜底（事件表第一真源）
# ---------------------------------------------------------------------------


def test_decide_framed_run_never_uses_thread_fallback():
    store = InMemoryHitlStore()
    row = _row(thread_id="t-framed")
    asyncio.run(store.acreate(row))
    owner = _owner_map({row["run_id"]: str(_MAINTAINER.id)})
    thread_spy = AsyncMock(return_value=_OTHER_USER_ID)  # 若被调用即越权归属

    with (
        patch("app.ops.lg_rag.event_store.run_owner", new=owner),
        patch("app.ops.lg_rag.thread_store.thread_owner", new=thread_spy),
        _client(store, user=_MAINTAINER) as client,
    ):
        res = client.post(
            f"/api/ops/hitl/requests/{row['id']}/decide", json={"decision": "approved"}
        )
    assert res.status_code == 200, res.text
    assert res.json()["request"]["status"] == STATUS_APPROVED
    thread_spy.assert_not_awaited(), "有帧 run 必须只信事件表，绝不走兜底"


# ---------------------------------------------------------------------------
# DB 面：真 thread_owner 真 OpsLgRagThread 行（无帧 run 全链）
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not DB_AVAILABLE, reason="PostgreSQL not available")
async def test_db_frameless_run_decide_via_real_thread_owner(monkeypatch):
    """真 PG：无帧 run_owner（无事件帧）→ 真 thread_owner 兜底 → decide 200。

    这是维护者红线「sync invoke 触发写闸 → decide 不再 404」的 DB 亲跑版：
    run_owner 走真实现（事件表无帧返 None），thread 行真插，归属反查全链不替身。
    """
    import uuid

    from httpx import ASGITransport, AsyncClient
    from sqlalchemy import text

    from app.db.models import OpsLgRagThread, OpsUser
    from app.db.session import AsyncSessionLocal
    from app.ops.hitl.persistence import configure_hitl_from_env, get_hitl_store, reset_hitl_store

    suffix = uuid.uuid4().hex[:10]
    run_id = f"runnoframes-{suffix}"
    tid = f"t-noframes-{suffix}"
    rid = f"hitl_nf_{suffix}"

    monkeypatch.setenv("OPS_HITL_PERSISTENCE", "db")
    reset_hitl_store()
    assert configure_hitl_from_env() == "db"

    # user 与 thread 无 ORM 关系映射——同事务 flush 顺序不保证 user 先落，
    # 对齐 test_hitl_pending_decide 先例：两次独立提交。
    async with AsyncSessionLocal() as db:
        db.add(OpsUser(id=str(_MAINTAINER.id), username=f"nf-{suffix}", role="maintainer"))
        await db.commit()
    async with AsyncSessionLocal() as db:
        db.add(OpsLgRagThread(id=tid, user_id=str(_MAINTAINER.id)))
        await db.commit()

    from tests.test_hitl_pending_decide import _bare_app

    app = _bare_app(user=_MAINTAINER)
    transport = ASGITransport(app=app)
    try:
        await get_hitl_store().acreate(
            {
                "id": rid,
                "run_id": run_id,
                "thread_id": tid,
                "checkpoint_id": None,
                "tenant_id": "ops-desk-pilot",
                "subtask_id": "s:2",
                "blocked_by": "prefix_touch_required",
                "unlock_subtask_id": "s:1",
                "reason": "需要重跑已执行步骤",
                "detail": "",
                "payload": {},
                "status": STATUS_PENDING,
            }
        )
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            res = await client.post(
                f"/api/ops/hitl/requests/{rid}/decide", json={"decision": "approved"}
            )
        assert res.status_code == 200, res.text
        assert res.json()["request"]["status"] == STATUS_APPROVED
    finally:
        async with AsyncSessionLocal() as db:
            await db.execute(text("DELETE FROM ops_hitl_requests WHERE id = :i"), {"i": rid})
            await db.execute(text("DELETE FROM ops_lg_rag_threads WHERE id = :t"), {"t": tid})
            await db.execute(text("DELETE FROM ops_users WHERE id = :u"), {"u": str(_MAINTAINER.id)})
            await db.commit()
        reset_hitl_store()


@pytest.mark.skipif(not DB_AVAILABLE, reason="PostgreSQL not available")
async def test_db_thread_owner_returns_none_for_missing_thread():
    """真 thread_owner：thread 行缺失 → None（fail-closed 语义的单测面）。"""
    from app.ops.lg_rag.thread_store import thread_owner

    assert await thread_owner("t-definitely-missing") is None
