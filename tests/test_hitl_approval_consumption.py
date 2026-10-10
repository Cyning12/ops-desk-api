"""hitl-approval-consumption T1：签发审批消费门（D1）+ unlock 空形态回填（D2）验收。

覆盖（task_hitl_approval_consumption_loop 验收映射 · SPEC v1 A1/A2/A3/A6/FP）：

- **TA1** 消费放行：匹配 approved 单据（三元组 + TTL 新鲜）→ 签发判定返 None
  + delegation_approval_consumed 台账（记动作不记内容）；
- **TA2** 变异式否定组：pending/rejected 不生效 · 超 TTL 不生效（float 与
  ISO 8601 str 双形态 · 实操-B）· 三元组任一不匹配 · 旧单据缺 capability_id
  fail-closed（实操-C）· store 读异常 fail-closed + warning（FP-1）·
  blocked_by=prefix_touch_required 同键单拒不消费（单据类型守卫 · FP-4）·
  TTL env 解析（默认 3600 · 域 [1,86400] · 非法回退 · FP-2）；
- **TA3** unlock 空形态回填：单子任务 delegation_issue 拦截 →
  unlock_subtask_id=被拦 sid 自身 + payload 增记 capability_id；
  prefix_touch_required 类空 unlock 维持（router 409 保留 · FP-4）；
- **TA5** off 零 diff：消费路径零触达（store 读 spy 零调用 · FP-7）。

live HTTP/SSE 全链与 git diff 空组（registry/policy/store）留 40 复跑。
"""

from __future__ import annotations

import logging
import time
import uuid
from datetime import UTC, datetime, timedelta

import pytest
from langchain_core.messages import HumanMessage

from app.ops.capability import delegation as dl
from app.ops.capability.baseline import ENV_ALLOW_WRITE_TAGS
from app.ops.capability.manifest import MANIFEST_DIR, load_capability_manifest
from app.ops.hitl import reset_hitl_store, set_hitl_store
from app.ops.hitl.store import InMemoryHitlStore
from app.ops.lg_rag.multi.nodes import (
    _approval_consumption_ttl_seconds,
    _decided_at_ts,
    _delegation_issue_block_reason,
    _join_subtasks,
    _observe,
    _persist_hitl,
)

_TESTING_MANIFEST = MANIFEST_DIR / "testing.v1.yaml"
_TESTING_CAP = "testing.write.echo"
_BLOCKED_BY = "delegation_issue_hitl_required"


@pytest.fixture
def cap_env(monkeypatch):
    """enforce + 放行 testing tag + 干净 InMemory store（每用例隔离）。"""
    monkeypatch.setenv(dl.ENV_MODE, "enforce")
    monkeypatch.setenv(dl.ENV_SECRET, "consumption-test-secret")
    monkeypatch.setenv(ENV_ALLOW_WRITE_TAGS, "testing")
    load_capability_manifest(_TESTING_MANIFEST)
    store = InMemoryHitlStore()
    set_hitl_store(store)
    yield store
    reset_hitl_store()


def _mk(run_id: str, sid: str) -> tuple[dict, dict]:
    """单步 tool 计划 state + 该步 row（承 D2 A4④ 范式）。"""
    state = {
        "messages": [HumanMessage(content="演示写操作审批")],
        "run_id": run_id,
        "subtasks": [
            {
                "subtask_id": sid,
                "id": sid,
                "type": "tool",
                "input": {"request_id": "r-1", "note": "demo"},
                "tool": _TESTING_CAP,
                "depends_on": [],
            }
        ],
        "subtask_results": [],
        "inflight_subtask_ids": [],
        "allowed_capability_ids": [_TESTING_CAP],
    }
    return state, state["subtasks"][0]


def _approved_req(run_id: str, sid: str, **over):
    """构造一条 approved 单据行（三元组 + payload 键 · 可被 over 变异）。"""
    req = {
        "id": f"req-{uuid.uuid4().hex[:8]}",
        "run_id": run_id,
        "thread_id": "t-ta",
        "subtask_id": sid,
        "blocked_by": _BLOCKED_BY,
        "unlock_subtask_id": sid,
        "reason": "委派签发需人工审批（测试）",
        "payload": {"capability_id": _TESTING_CAP},
        "status": "approved",
        "decision_by": "验收",
        "decided_at": time.time(),
        "created_at": time.time(),
    }
    req.update(over)
    return req


async def test_ta1_approval_consumed_allows_redispatch(cap_env, caplog):
    """TA1：三元组命中 + TTL 新鲜 → 签发判定返 None + 台账（记动作不记内容）。"""
    run_id = f"run-{uuid.uuid4().hex[:8]}"
    sid = f"{run_id}:1"
    state, row = _mk(run_id, sid)
    await cap_env.acreate(_approved_req(run_id, sid))

    with caplog.at_level(logging.INFO, logger="app.ops.lg_rag.multi.nodes"):
        reason = await _delegation_issue_block_reason(state, row)

    assert reason is None
    hits = [
        r for r in caplog.records if "delegation_approval_consumed" in r.message
    ]
    assert len(hits) == 1
    msg = hits[0].message
    assert sid in msg and _TESTING_CAP in msg and "验收" in msg
    assert "note" not in msg  # 记动作不记内容：参数原值不落台账


# --- TA2 变异式否定组：以下形态全部维持拦截（fail-closed）---------------


@pytest.mark.parametrize("status", ["pending", "rejected"])
async def test_ta2_non_approved_not_consumed(cap_env, status):
    """TA2①：pending / rejected 单据不生效（读时活状态语义）。"""
    run_id = f"run-{uuid.uuid4().hex[:8]}"
    sid = f"{run_id}:1"
    state, row = _mk(run_id, sid)
    await cap_env.acreate(_approved_req(run_id, sid, status=status))
    reason = await _delegation_issue_block_reason(state, row)
    assert reason is not None and "非只读" in reason


@pytest.mark.parametrize(
    "mutate",
    [
        {"run_id": "run-other"},  # run_id 不匹配
        {"subtask_id": "sid-other"},  # subtask_id 不匹配
        {"payload": {"capability_id": "oa.readonly.list"}} ,  # capability 不匹配
        {"payload": {}},  # 旧单据缺 capability_id 键（实操-C fail-closed）
        {"blocked_by": "prefix_touch_required"},  # 单据类型守卫（FP-4）
    ],
    ids=["run_id", "subtask_id", "capability_id", "missing_key", "prefix_touch"],
)
async def test_ta2_triple_mismatch_not_consumed(cap_env, mutate):
    """TA2②：消费键任一不匹配 / 缺键 / 类型不符 → 维持拦截。"""
    run_id = f"run-{uuid.uuid4().hex[:8]}"
    sid = f"{run_id}:1"
    state, row = _mk(run_id, sid)
    req = _approved_req(run_id, sid)
    req.update(mutate)
    await cap_env.acreate(req)
    reason = await _delegation_issue_block_reason(state, row)
    assert reason is not None and "非只读" in reason


async def test_ta2_expired_ttl_float_not_consumed(cap_env, monkeypatch):
    """TA2③：超 TTL 不生效（float decided_at · InMemory 真读路径）。"""
    monkeypatch.setenv("OPS_HITL_APPROVAL_CONSUMPTION_TTL_SECONDS", "60")
    run_id = f"run-{uuid.uuid4().hex[:8]}"
    sid = f"{run_id}:1"
    state, row = _mk(run_id, sid)
    stale = time.time() - 120
    await cap_env.acreate(_approved_req(run_id, sid, decided_at=stale))
    reason = await _delegation_issue_block_reason(state, row)
    assert reason is not None and "非只读" in reason


async def test_ta2_ttl_iso_str_double_form(cap_env, monkeypatch):
    """TA2④（实操-B）：ISO 8601 str decided_at——过期拦 / 新鲜放（归一双形态）。"""
    monkeypatch.setenv("OPS_HITL_APPROVAL_CONSUMPTION_TTL_SECONDS", "3600")
    run_id = f"run-{uuid.uuid4().hex[:8]}"
    sid = f"{run_id}:1"
    state, row = _mk(run_id, sid)
    fresh_iso = datetime.now(UTC).isoformat()
    await cap_env.acreate(_approved_req(run_id, sid, decided_at=fresh_iso))
    assert await _delegation_issue_block_reason(state, row) is None
    run2 = f"run-{uuid.uuid4().hex[:8]}"
    sid2 = f"{run2}:1"
    state2, row2 = _mk(run2, sid2)
    stale_iso = (datetime.now(UTC) - timedelta(hours=2)).isoformat()
    await cap_env.acreate(_approved_req(run2, sid2, decided_at=stale_iso))
    reason = await _delegation_issue_block_reason(state2, row2)
    assert reason is not None and "非只读" in reason


async def test_ta2_store_read_failure_fail_closed(cap_env, monkeypatch, caplog):
    """TA2⑤（FP-1）：消费读 store 异常 → 维持拦截 + warning 台账。"""
    run_id = f"run-{uuid.uuid4().hex[:8]}"
    sid = f"{run_id}:1"
    state, row = _mk(run_id, sid)
    await cap_env.acreate(_approved_req(run_id, sid))

    async def _boom(*a, **k):
        raise RuntimeError("db down")

    monkeypatch.setattr(cap_env, "alist", _boom)
    with caplog.at_level(logging.WARNING, logger="app.ops.lg_rag.multi.nodes"):
        reason = await _delegation_issue_block_reason(state, row)
    assert reason is not None and "非只读" in reason
    assert any(
        "delegation_approval_consumption_read_failed" in r.message
        for r in caplog.records
    )


@pytest.mark.parametrize(
    ("raw", "want"),
    [
        (None, 3600), ("", 3600), ("5", 5), ("86400", 86400),
        ("0", 3600), ("86401", 3600), ("abc", 3600), (" 120 ", 120),
    ],
)
def test_ta2_ttl_env_parse(monkeypatch, raw, want):
    """TA2⑥：TTL env 合法域 [1,86400] · 非法/越界回退默认（承 _env_int 先例）。"""
    if raw is None:
        monkeypatch.delenv("OPS_HITL_APPROVAL_CONSUMPTION_TTL_SECONDS", raising=False)
    else:
        monkeypatch.setenv("OPS_HITL_APPROVAL_CONSUMPTION_TTL_SECONDS", raw)
    assert _approval_consumption_ttl_seconds() == want


@pytest.mark.parametrize(
    ("raw", "ok"),
    [
        (time.time(), True),
        (datetime.now(UTC).isoformat(), True),
        ("2026-10-10T00:00:00+08:00", True),
        ("not-a-date", False),
        (None, False),
        (True, False),  # bool 是 int 子类 · 显式排除
        ([], False),
    ],
)
def test_ta2_decided_at_normalization(raw, ok):
    """TA2⑦：_decided_at_ts 归一 float|ISO str · 不可归一 None（fail-closed）。"""
    assert (_decided_at_ts(raw) is not None) is ok


# --- TA3 unlock 空形态回填（D2 · Q3）与 TA5 off 零触达（FP-7）-----------


async def test_ta3_unlock_refilled_for_delegation_issue(cap_env):
    """TA3①：单子任务 delegation_issue 拦截 → unlock=被拦 sid 自身 + payload 键。

    真链驱动：_join_subtasks（拦）→ _observe → _persist_hitl（落库）。
    """
    run_id = f"run-{uuid.uuid4().hex[:8]}"
    sid = f"{run_id}:1"
    state, _row = _mk(run_id, sid)
    joined = await _join_subtasks(state)
    blocked = [
        r
        for r in joined["subtask_results"]
        if r.get("blocked_by") == _BLOCKED_BY and r.get("hitl_required") is True
    ]
    assert len(blocked) == 1
    merged = {**state, "subtask_results": list(joined["subtask_results"])}
    obs = _observe(merged)
    assert obs["hitl_pending"] == [sid]
    created, unpersisted = await _persist_hitl(merged, obs, thread_id="t-ta3")
    assert unpersisted is False
    req = next(r for r in created if str(r.get("subtask_id")) == sid)
    # D2 回填：无前驱前缀 + delegation_issue 类 → unlock=被拦 sid 自身
    assert req["unlock_subtask_id"] == sid
    # D1 消费键：payload jsonb 增记 capability_id（真源 = term.tool）
    assert req["payload"]["capability_id"] == _TESTING_CAP


async def test_ta3_prefix_touch_unlock_stays_empty(cap_env):
    """TA3②（FP-4）：prefix_touch_required 类空 unlock 维持（409 保留不放宽）。"""
    run_id = f"run-{uuid.uuid4().hex[:8]}"
    sid = f"{run_id}:1"
    state, _row = _mk(run_id, sid)
    term = {
        "subtask_id": sid,
        "id": sid,
        "type": "tool",
        "tool": _TESTING_CAP,
        "blocked_by": "prefix_touch_required",
        "hitl_required": True,
        "error": "改历史需审批（测试）",
    }
    merged = {**state, "subtask_results": [term]}
    obs = _observe(merged)
    assert obs["hitl_pending"] == [sid]
    created, _ = await _persist_hitl(merged, obs, thread_id="t-ta3b")
    req = next(r for r in created if str(r.get("subtask_id")) == sid)
    assert req["blocked_by"] == "prefix_touch_required"
    assert req["unlock_subtask_id"] == ""  # 空 unlock 维持 → router 409 守卫不放宽


async def test_ta5_off_mode_zero_store_touch(cap_env, monkeypatch):
    """TA5（FP-7）：delegation off 模式消费路径零触达（store 读 spy 零调用）。"""
    monkeypatch.setenv(dl.ENV_MODE, "off")
    run_id = f"run-{uuid.uuid4().hex[:8]}"
    sid = f"{run_id}:1"
    state, _row = _mk(run_id, sid)
    calls = []
    orig_alist = cap_env.alist

    async def _spy(*a, **k):
        calls.append(a)
        return await orig_alist(*a, **k)

    monkeypatch.setattr(cap_env, "alist", _spy)
    joined = await _join_subtasks(state)
    assert calls == []  # off：消费读零触达
    assert not any(
        r.get("blocked_by") == _BLOCKED_BY
        for r in joined.get("subtask_results", [])
    )
