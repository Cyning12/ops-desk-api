"""HITL 审批申请：存储语义 / 回调签名 / 端点行为。

**为什么"重复决定必须被拒"值得单独测**：路由用 404 / 409 区分
「申请不存在」和「已经决过了」，而这两者的判据只有一处——
``adecide`` 返回 None。换言之存储层的语义直接决定端点的语义。

真联调（memory 模式）抓出来的坑：``InMemoryHitlStore.adecide`` 无条件覆写，
``DbHitlStore`` 却带 ``WHERE status='pending'`` 守卫。两套语义不一致 ⇒
「联调时一切正常、上生产行为变了」，而且这种差异**单测各自都绿**。
"""

from __future__ import annotations

import time

import pytest

from app.ops.hitl import new_request_id
from app.ops.hitl.persistence import (
    MODE_DB,
    MODE_MEMORY,
    MODE_NULL,
    configure_hitl_from_env,
    describe_hitl_persistence,
    get_hitl_store,
    reset_hitl_store,
    set_hitl_store,
)
from app.ops.hitl.signature import (
    ENV_SECRET,
    HEADER_NONCE,
    HEADER_SIGNATURE,
    HEADER_TIMESTAMP,
    SignatureError,
    reset_nonces,
    secret_configured,
    sign,
    verify,
)
from app.ops.hitl.store import (
    DbHitlStore,
    InMemoryHitlStore,
    NullHitlStore,
    STATUS_APPROVED,
    STATUS_PENDING,
    STATUS_REJECTED,
)


@pytest.fixture(autouse=True)
def _isolate():
    """进程内全局状态（store / nonce）必须能显式 reset。"""
    reset_hitl_store()
    reset_nonces()
    yield
    reset_hitl_store()
    reset_nonces()


def _req(**kw) -> dict:
    base = {
        "id": new_request_id(),
        "run_id": "r1",
        "thread_id": "t1",
        "subtask_id": "r1:2",
        "unlock_subtask_id": "r1:1",
        "blocked_by": "prefix_touch_required",
        "status": STATUS_PENDING,
        "created_at": time.time(),
    }
    base.update(kw)
    return base


# ---------------------------------------------------------------------------
# 存储语义
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_memory_store_roundtrip():
    store = InMemoryHitlStore()
    req = _req()
    await store.acreate(req)
    assert (await store.aget(req["id"]))["id"] == req["id"]
    assert [r["id"] for r in await store.alist(status="pending")] == [req["id"]]
    decided = await store.adecide(req["id"], decision=STATUS_APPROVED, by="张三")
    assert decided["status"] == STATUS_APPROVED
    assert decided["decision_by"] == "张三"


@pytest.mark.asyncio
async def test_memory_store_rejects_duplicate_decision():
    """重复决定必须返回 None —— 端点靠它区分 404 / 409。"""
    store = InMemoryHitlStore()
    req = _req()
    await store.acreate(req)
    assert await store.adecide(req["id"], decision=STATUS_APPROVED, by="张三") is not None
    assert await store.adecide(req["id"], decision=STATUS_REJECTED, by="李四") is None
    # 第一次的决定没被第二次覆盖
    assert (await store.aget(req["id"]))["status"] == STATUS_APPROVED
    assert (await store.aget(req["id"]))["decision_by"] == "张三"


@pytest.mark.asyncio
async def test_memory_and_db_stores_share_decide_semantics():
    """两套存储的"只受理 pending"必须是同一条规则。

    内存版靠代码、DB 版靠 SQL；这里把 SQL 钉住，防止哪天有人改了
    ``WHERE`` 条件而内存版没跟着改（反之亦然）。
    """
    assert "status = 'pending'" in DbHitlStore._DECIDE, (
        "DbHitlStore.adecide 丢了 pending 守卫，会与内存版语义分叉"
    )
    # 反向对照：守卫不是"整表 UPDATE"
    assert "WHERE" in DbHitlStore._DECIDE and "RETURNING" in DbHitlStore._DECIDE


@pytest.mark.asyncio
async def test_null_store_marks_unpersisted_instead_of_throwing():
    """不落库必须**说出来**，不能假装申请已提交。

    "申请丢了"和"没人申请过"在观测上长得一模一样，人会一直等。
    """
    store = NullHitlStore()
    created = await store.acreate(_req())
    assert created["persisted"] is False
    assert await store.aget(created["id"]) is None
    assert await store.adecide(created["id"], decision=STATUS_APPROVED, by="oa") is None


@pytest.mark.asyncio
async def test_memory_store_has_upper_bound():
    """按 key 累积的进程内字典必须有上界（与降级缓存同一条纪律）。"""
    store = InMemoryHitlStore()
    for _ in range(InMemoryHitlStore._MAX + 5):
        await store.acreate(_req())
    assert len(store._items) <= InMemoryHitlStore._MAX


# ---------------------------------------------------------------------------
# 持久化装配：显式选，不自动探测
# ---------------------------------------------------------------------------


def test_persistence_modes_selected_explicitly(monkeypatch):
    monkeypatch.setenv("OPS_HITL_PERSISTENCE", "memory")
    assert configure_hitl_from_env() == MODE_MEMORY
    assert isinstance(get_hitl_store(), InMemoryHitlStore)

    monkeypatch.setenv("OPS_HITL_PERSISTENCE", "db")
    assert configure_hitl_from_env() == MODE_DB

    monkeypatch.delenv("OPS_HITL_PERSISTENCE", raising=False)
    assert configure_hitl_from_env() == MODE_NULL
    assert isinstance(get_hitl_store(), NullHitlStore)


def test_unknown_persistence_mode_falls_back_to_null(monkeypatch):
    """识别不了的模式按**不落库**处理，绝不能悄悄换成 memory。"""
    monkeypatch.setenv("OPS_HITL_PERSISTENCE", "redis")
    assert configure_hitl_from_env() == MODE_NULL
    assert isinstance(get_hitl_store(), NullHitlStore)


def test_describe_says_whether_it_persists():
    set_hitl_store(InMemoryHitlStore())
    assert describe_hitl_persistence()["mode"] == MODE_MEMORY
    set_hitl_store(NullHitlStore())
    assert describe_hitl_persistence()["mode"] == MODE_NULL


# ---------------------------------------------------------------------------
# 回调签名
# ---------------------------------------------------------------------------


def _signed(body: bytes, *, secret="s3cr3t", ts=None, nonce="n1"):
    stamp = int(time.time()) if ts is None else ts
    headers = {
        HEADER_TIMESTAMP: str(stamp),
        HEADER_NONCE: nonce,
        HEADER_SIGNATURE: sign(body=body, timestamp=stamp, nonce=nonce, secret=secret),
    }
    return headers


def test_signature_roundtrip(monkeypatch):
    monkeypatch.setenv(ENV_SECRET, "s3cr3t")
    body = b'{"request_id":"a","decision":"approved"}'
    verify(body=body, headers=_signed(body))
    # 反向对照：换个密钥就过不了（否则"任何签名都能过"也能通过上一条）
    with pytest.raises(SignatureError):
        verify(body=body, headers=_signed(body, secret="wrong"))


def test_missing_secret_closes_the_endpoint(monkeypatch):
    """不设密钥 = 不开放。否则回调就是谁都能打的匿名接口。"""
    monkeypatch.delenv(ENV_SECRET, raising=False)
    assert secret_configured() is False
    with pytest.raises(SignatureError):
        verify(body=b"{}", headers=_signed(b"{}"))


def test_tampered_body_is_rejected(monkeypatch):
    monkeypatch.setenv(ENV_SECRET, "s3cr3t")
    body = b'{"request_id":"a","decision":"approved"}'
    headers = _signed(body)
    with pytest.raises(SignatureError):
        verify(body=b'{"request_id":"a","decision":"rejected"}', headers=headers)


def test_nonce_replay_is_rejected(monkeypatch):
    monkeypatch.setenv(ENV_SECRET, "s3cr3t")
    body = b"{}"
    headers = _signed(body)
    verify(body=body, headers=headers)
    with pytest.raises(SignatureError):
        verify(body=body, headers=headers)  # 同一个 nonce 再来一次


def test_stale_timestamp_is_rejected(monkeypatch):
    monkeypatch.setenv(ENV_SECRET, "s3cr3t")
    body = b"{}"
    now = time.time()
    headers = _signed(body, ts=int(now) - 4000)
    with pytest.raises(SignatureError):
        verify(body=body, headers=headers, now=now)


def test_signature_error_never_leaks_expected_value(monkeypatch):
    """报错只说哪一步没过，不泄露期望值——否则异常本身成了校对工具。"""
    monkeypatch.setenv(ENV_SECRET, "s3cr3t")
    body = b"{}"
    headers = _signed(body)
    headers[HEADER_SIGNATURE] = "sha256=deadbeef"
    with pytest.raises(SignatureError) as exc:
        verify(body=body, headers=headers)
    assert "deadbeef" not in str(exc.value)
    assert "s3cr3t" not in str(exc.value)


# ---------------------------------------------------------------------------
# 端点：callback 的 404 / 409 区分
# ---------------------------------------------------------------------------


def _client(monkeypatch, store):
    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    from app.ops.hitl.router import router

    monkeypatch.setenv(ENV_SECRET, "s3cr3t")
    set_hitl_store(store)
    app = FastAPI()
    app.include_router(router, prefix="/api/ops")
    return TestClient(app)


def _post_callback(client, payload: dict, *, secret="s3cr3t", nonce=None):
    import json
    import uuid

    body = json.dumps(payload, ensure_ascii=False).encode()
    ts = int(time.time())
    nonce = nonce or uuid.uuid4().hex
    return client.post(
        "/api/ops/hitl/callback",
        content=body,
        headers={
            "Content-Type": "application/json",
            HEADER_TIMESTAMP: str(ts),
            HEADER_NONCE: nonce,
            HEADER_SIGNATURE: sign(body=body, timestamp=ts, nonce=nonce, secret=secret),
        },
    )


def test_callback_approves_and_returns_receipt(monkeypatch):
    store = InMemoryHitlStore()
    req = _req()
    client = _client(monkeypatch, store)
    with client:
        # 先造一条（走 create_request_manual 需要管理员，这里直接写 store）
        import asyncio

        asyncio.run(store.acreate(req))
        res = _post_callback(
            client,
            {"request_id": req["id"], "decision": "approved",
             "decision_by": "张三", "note": "同意重跑"},
        )
    assert res.status_code == 200
    assert res.json()["request"]["status"] == STATUS_APPROVED
    assert res.json()["request"]["decision_by"] == "张三"


def test_callback_duplicate_is_409_not_404(monkeypatch):
    """重复回调必须和"申请不存在"分开 —— 否则会被当成申请丢了。"""
    store = InMemoryHitlStore()
    req = _req()
    client = _client(monkeypatch, store)
    with client:
        import asyncio

        asyncio.run(store.acreate(req))
        asyncio.run(store.adecide(req["id"], decision=STATUS_APPROVED, by="张三"))
        again = _post_callback(client, {"request_id": req["id"], "decision": "rejected"})
        missing = _post_callback(client, {"request_id": "hitl_nope", "decision": "rejected"})
    assert again.status_code == 409, again.text
    assert missing.status_code == 404, missing.text


def test_callback_unsigned_is_401(monkeypatch):
    store = InMemoryHitlStore()
    client = _client(monkeypatch, store)
    with client:
        res = client.post(
            "/api/ops/hitl/callback",
            json={"request_id": "x", "decision": "approved"},
        )
    assert res.status_code == 401


def test_callback_rejects_unknown_decision(monkeypatch):
    store = InMemoryHitlStore()
    req = _req()
    client = _client(monkeypatch, store)
    with client:
        import asyncio

        asyncio.run(store.acreate(req))
        res = _post_callback(client, {"request_id": req["id"], "decision": "maybe"})
    assert res.status_code == 400
    assert "approved" in res.json()["detail"]


def test_list_requests_requires_signature(monkeypatch):
    store = InMemoryHitlStore()
    client = _client(monkeypatch, store)
    with client:
        assert client.get("/api/ops/hitl/requests").status_code == 401
        ts = int(time.time())
        res = client.get(
            "/api/ops/hitl/requests?status=pending",
            headers={
                HEADER_TIMESTAMP: str(ts),
                HEADER_NONCE: "n-list",
                HEADER_SIGNATURE: sign(body=b"", timestamp=ts, nonce="n-list",
                                       secret="s3cr3t"),
            },
        )
        assert res.status_code == 200
        assert res.json()["count"] == 0
