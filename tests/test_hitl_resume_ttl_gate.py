"""HITL 手动 resume 链 TTL 闸（W-fix-1 · task_api_w_join_gap_fix · 红测先行）。

四决策钉死（HG-W-FIX-DESIGN · 2026-11-02 维护者签）：

① 过期批准 resume 出口 = **409 + detail 含 `approval_expired`**，
   且响应文案含中文「过期」（命中 web mapping ``/过期|expired/i``）；
③ 作用面 = resume/消费环：**decide 不拒超龄 pending**（「批准不过期」语义不 reopen）；
④ **启用 STATUS_EXPIRED**：resume 遇过期批准 → 置单据 expired 终态 + 返 409。

对称既有闸：自动续跑扫描 ``store.aclaim_approved_for_resume``（store.py:116-117）
已有 TTL 判据；手动链（router.py:520 resume_request）此前零闸（F11/F12 实证）。
TTL 判据同源：``nodes._approval_consumption_ttl_seconds``（单一旋钮 · 禁第二处）。
"""

from __future__ import annotations

import asyncio
import time
from unittest.mock import patch

import pytest

import app.ops.hitl.router as router_mod
from app.ops.hitl.persistence import reset_hitl_store
from app.ops.hitl.store import STATUS_APPROVED, STATUS_REJECTED, InMemoryHitlStore
from tests.test_hitl_resume import (
    _approved_row,
    _client,
    _drain,
)


@pytest.fixture(autouse=True)
def _isolate():
    reset_hitl_store()
    yield
    reset_hitl_store()
    getattr(router_mod, "_RESUME_IN_FLIGHT", {}).clear()


def _decided(store: InMemoryHitlStore, *, age_seconds: float = 0.0, **row_kw) -> dict:
    """造一条 approved 行；age_seconds>0 时把 decided_at 拨回（模拟超龄批准）。"""
    row = _approved_row(**row_kw)
    asyncio.run(store.acreate(row))
    asyncio.run(store.adecide(row["id"], decision=STATUS_APPROVED, by="张三"))
    if age_seconds > 0:
        store._items[row["id"]]["decided_at"] = time.time() - age_seconds
    return row


def _rejected(store: InMemoryHitlStore, *, age_seconds: float = 0.0, **row_kw) -> dict:
    row = _approved_row(**row_kw)
    asyncio.run(store.acreate(row))
    asyncio.run(store.adecide(row["id"], decision=STATUS_REJECTED, by="张三"))
    if age_seconds > 0:
        store._items[row["id"]]["decided_at"] = time.time() - age_seconds
    return row


async def _quick_resume(**kwargs):
    if kwargs.get("preflight_only"):
        return {"preflight": True}
    return {"thread_id": kwargs["thread_id"], "state": {"route": "replan"}}


# ---------------------------------------------------------------------------
# 负样本：超 TTL 批准 resume → 409 approval_expired + 单据置 expired 终态
# ---------------------------------------------------------------------------


def test_expired_approved_resume_returns_409_and_marks_expired(monkeypatch):
    """F11/F12 主负样本：approved 超 TTL（默认 3600s）后手动 resume 必须被拒。

    修复前红：手动链零 TTL 闸，过期批准照样解锁重跑（联调 §5 实证 +178s>90s）。
    """
    store = InMemoryHitlStore()
    row = _decided(store, age_seconds=7200)  # 拨回 2h > 默认 TTL 3600s

    with (
        patch("app.ops.hitl.router.resume_hitl_run", new=_quick_resume),
        _client(monkeypatch, store) as client,
    ):
        res = client.post(f"/api/ops/hitl/requests/{row['id']}/resume")

    assert res.status_code == 409, res.text
    detail = res.json()["detail"]
    assert "approval_expired" in detail, f"detail 须含错误码锚：{detail!r}"
    assert "过期" in detail, f"detail 须含中文「过期」（web mapping /过期|expired/i）：{detail!r}"
    after = asyncio.run(store.aget(row["id"]))
    assert after["status"] == "expired", "决策④：过期拒绝时单据置 expired 终态"


def test_ttl_knob_env_is_single_source(monkeypatch):
    """同源实证：TTL 取值复用 OPS_HITL_APPROVAL_CONSUMPTION_TTL_SECONDS（单一旋钮）。

    联调 A5 复测形态：短窗 90s · approved 后 +178s → 过期出口可达。
    """
    monkeypatch.setenv("OPS_HITL_APPROVAL_CONSUMPTION_TTL_SECONDS", "90")
    store = InMemoryHitlStore()
    row = _decided(store, age_seconds=178)

    with (
        patch("app.ops.hitl.router.resume_hitl_run", new=_quick_resume),
        _client(monkeypatch, store) as client,
    ):
        res = client.post(f"/api/ops/hitl/requests/{row['id']}/resume")

    assert res.status_code == 409, res.text
    assert "approval_expired" in res.json()["detail"]
    assert asyncio.run(store.aget(row["id"]))["status"] == "expired"


def test_missing_decided_at_fails_closed(monkeypatch):
    """decided_at 缺失的 approved 行：无法证明未过期 → fail-closed 视同过期。

    对称 InMemoryHitlStore.aclaim_approved_for_resume「缺 decided_at 视同不可认领」。
    """
    store = InMemoryHitlStore()
    row = _approved_row()
    asyncio.run(store.acreate(row))
    # 绕过 adecide 直接置 approved（无 decided_at）：模拟历史/异常数据形态
    store._items[row["id"]]["status"] = STATUS_APPROVED

    with (
        patch("app.ops.hitl.router.resume_hitl_run", new=_quick_resume),
        _client(monkeypatch, store) as client,
    ):
        res = client.post(f"/api/ops/hitl/requests/{row['id']}/resume")

    assert res.status_code == 409, res.text
    assert "approval_expired" in res.json()["detail"]
    assert asyncio.run(store.aget(row["id"]))["status"] == "expired"


# ---------------------------------------------------------------------------
# 正样本：未过期批准不误拒 · 驳回 resume 不受 TTL 闸 · decide 不拒超龄 pending
# ---------------------------------------------------------------------------


def test_fresh_approved_resume_not_rejected(monkeypatch):
    """不误拒红线（failure_paths）：未过期 approved resume 照常受理秒回 200。"""
    store = InMemoryHitlStore()
    row = _decided(store)  # decided_at = now，远未超 TTL

    with (
        patch("app.ops.hitl.router.resume_hitl_run", new=_quick_resume),
        _client(monkeypatch, store) as client,
    ):
        res = client.post(f"/api/ops/hitl/requests/{row['id']}/resume")
        _drain()

    assert res.status_code == 200, res.text
    assert res.json()["resume"]["status"] == "accepted"
    assert asyncio.run(store.aget(row["id"]))["status"] == STATUS_APPROVED, (
        "正样本不得被误置 expired"
    )


def test_rejected_resume_not_subject_to_ttl_gate(monkeypatch):
    """驳回 resume 是「收工出结论」，不属于执行权恢复 → 不受 TTL 闸约束。

    若误把 rejected 也挡下，驳回的 run 会永远挂在等待授权帧（端点 docstring 钉死
    「驳回也必须能调这个端点」）。
    """
    store = InMemoryHitlStore()
    row = _rejected(store, age_seconds=7200)

    with (
        patch("app.ops.hitl.router.resume_hitl_run", new=_quick_resume),
        _client(monkeypatch, store) as client,
    ):
        res = client.post(f"/api/ops/hitl/requests/{row['id']}/resume")
        _drain()

    assert res.status_code == 200, res.text
    assert res.json()["resume"]["status"] == "accepted"
    assert asyncio.run(store.aget(row["id"]))["status"] == STATUS_REJECTED


def test_decide_on_stale_pending_still_succeeds():
    """钉死③：「批准不过期」——adecide 对超龄 pending 不拒（人随时可以下决定）。

    TTL 闸只长在 resume/消费环；若误把闸加进 adecide，这条红。
    """
    store = InMemoryHitlStore()
    row = _approved_row()
    asyncio.run(store.acreate(row))
    store._items[row["id"]]["created_at"] = time.time() - 7200  # 申请挂了 2h 没人批

    decided = asyncio.run(store.adecide(row["id"], decision=STATUS_APPROVED, by="张三"))
    assert decided is not None, "decide 不得拒超龄 pending（「批准不过期」不 reopen）"
    assert decided["status"] == STATUS_APPROVED
    assert decided["decided_at"], "decide 须刷新 decided_at（执行权窗口自决定时刻起算）"
