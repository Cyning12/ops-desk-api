"""hitl-approval-consumption T1：签发审批消费门（D1）+ unlock 空形态回填（D2）验收。

覆盖（task_hitl_approval_consumption_loop 验收映射 · SPEC v1 A1/A2/A3/A6/FP）：

- **TA1** 消费放行：匹配 approved 单据（三元组 + TTL 新鲜）→ 签发判定返 None
  + delegation_approval_consumed 台账（logger + span metadata 双面 ·
  记动作不记内容）；
- **TA2** 变异式否定组：pending/rejected 不生效 · 超 TTL 不生效（**InMemory
  float + Db ISO str 双 store 各一组** · Db 组必经 alist/aget 真读路径 ·
  实操-B）· 三元组任一不匹配 · 旧单据缺 capability_id fail-closed（实操-C）·
  store 读异常 fail-closed + warning（FP-1）· blocked_by=prefix_touch_required
  同键单拒不消费（单据类型守卫 · FP-4）· TTL env 解析（默认 3600 · 域
  [1,86400] · 非法回退 · FP-2）· decided_at 归一单元组（float|ISO str 钉）；
- **TA3** 单子任务 resume 成环：_persist_hitl unlock=被拦 sid 自身回填 +
  payload 增记 capability_id（单测）；机制段 decide(approved) → resume
  （verdict=replan · 解锁留痕）→ 消费放行 → 令牌签发 → tool_exec 真执行 →
  observe done 收口（done{completed} 机制段 · live HTTP 全链留 40 复跑）；
  prefix_touch_required 类空 unlock 维持（router 409 保留 · FP-4）；
- **TA4-D** 消费命中 ≠ 全链放行：签发判定放行后，无令牌验签门照拒 ·
  Policy 写闸不豁免（审批消费不过 gateway/Policy）；
- **TA5** off 零 diff：消费路径零触达（store 读 spy 零调用 · 无台账 · FP-7）；
- **TA6** decide 落库不动：router.py 409 守卫保留断言（prefix_touch 类空
  unlock 仍 409）；store.py adecide/_DECIDE diff 空由 TA7 工程面 diff 核验承接。

live HTTP/SSE 全链与 git diff 空组（registry/policy/store）留 40 复跑。
"""

from __future__ import annotations

import logging
import time
import uuid
from datetime import UTC, datetime, timedelta

import pytest
from langchain_core.messages import HumanMessage
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph

import app.ops.lg_rag.multi.nodes as nodes
from app.ops.capability import delegation as dl
from app.ops.capability.baseline import ENV_ALLOW_WRITE_TAGS
from app.ops.capability.manifest import MANIFEST_DIR, load_capability_manifest
from app.ops.hitl import new_request_id, reset_hitl_store, set_hitl_store
from app.ops.hitl.resume import resume_hitl_run
from app.ops.hitl.store import (
    STATUS_APPROVED,
    STATUS_PENDING,
    DbHitlStore,
    InMemoryHitlStore,
)
from app.ops.lg_rag.multi.nodes import (
    _approval_consumption_ttl_seconds,
    _decided_at_ts,
    _delegation_issue_block_reason,
    _issue_delegation_token,
    _join_subtasks,
    _observe,
    _persist_hitl,
    observe_node,
    route_after_react,
    tool_exec_node,
)
from app.ops.lg_rag.state import LgRagState
from tests.conftest import DB_AVAILABLE

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


async def test_ta1_approval_consumed_allows_redispatch(cap_env, caplog, monkeypatch):
    """TA1：三元组命中 + TTL 新鲜 → 签发判定返 None + 台账（logger+span 双面）。"""
    run_id = f"run-{uuid.uuid4().hex[:8]}"
    sid = f"{run_id}:1"
    state, row = _mk(run_id, sid)
    await cap_env.acreate(_approved_req(run_id, sid))
    span_calls: list[dict] = []
    monkeypatch.setattr(
        nodes, "_record_span_metadata", lambda md: span_calls.append(md)
    )

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
    # span metadata 面：同一台账动作 + TTL 余量（读时判过期的活状态语义）
    spans = [c for c in span_calls if c.get("delegation_approval_consumed") is True]
    assert len(spans) == 1
    assert spans[0]["subtask_id"] == sid
    assert spans[0]["capability_id"] == _TESTING_CAP
    assert spans[0]["ttl_remaining_seconds"] > 0


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
        {"payload": {"capability_id": "oa.readonly.list"}},  # capability 不匹配
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


@pytest.mark.skipif(not DB_AVAILABLE, reason="PostgreSQL not available")
async def test_ta2_ttl_db_store_real_read_path_iso_str(cap_env, monkeypatch):
    """TA2⑧（实操-B · Db 组）：DbHitlStore 经 alist/aget 真读路径实收 ISO str
    decided_at —— 新鲜放 / 过期拦（禁构造 float 绕过 str 分支）。
    """
    from sqlalchemy import text

    from app.db.session import AsyncSessionLocal

    monkeypatch.setenv("OPS_HITL_APPROVAL_CONSUMPTION_TTL_SECONDS", "3600")
    db_store = DbHitlStore()
    set_hitl_store(db_store)
    prefix = f"hitl_ta2db_{uuid.uuid4().hex[:6]}_"
    fresh_id = f"{prefix}fresh"  # 过期半在下一用例（stale 组）

    async def _cleanup() -> None:
        async with AsyncSessionLocal() as db:
            await db.execute(
                text("DELETE FROM ops_hitl_requests WHERE id LIKE :p"),
                {"p": f"{prefix}%"},
            )
            await db.commit()

    await _cleanup()
    try:
        run_id = f"run-{uuid.uuid4().hex[:8]}"
        sid = f"{run_id}:1"
        state, row = _mk(run_id, sid)
        await db_store.acreate(_approved_req(run_id, sid, id=fresh_id))
        decided = await db_store.adecide(fresh_id, decision=STATUS_APPROVED, by="验收")
        assert decided["status"] == STATUS_APPROVED
        # 钉死真读路径实收类型：_row_to_dict 输出 ISO 8601 str（非 float/datetime）
        assert isinstance(decided["decided_at"], str)
        assert await _delegation_issue_block_reason(state, row) is None
    finally:
        await _cleanup()

@pytest.mark.skipif(not DB_AVAILABLE, reason="PostgreSQL not available")
async def test_ta2_ttl_db_store_expired_not_consumed(cap_env, monkeypatch):
    """TA2⑧ 续（Db 组过期半）：decided_at 拨回 2h（SQL 层真改）→ 超 TTL 不消费。"""
    from sqlalchemy import text

    from app.db.session import AsyncSessionLocal

    monkeypatch.setenv("OPS_HITL_APPROVAL_CONSUMPTION_TTL_SECONDS", "3600")
    db_store = DbHitlStore()
    set_hitl_store(db_store)
    prefix = f"hitl_ta2dbx_{uuid.uuid4().hex[:6]}_"
    rid = f"{prefix}stale"

    async def _cleanup() -> None:
        async with AsyncSessionLocal() as db:
            await db.execute(
                text("DELETE FROM ops_hitl_requests WHERE id LIKE :p"),
                {"p": f"{prefix}%"},
            )
            await db.commit()

    await _cleanup()
    try:
        run_id = f"run-{uuid.uuid4().hex[:8]}"
        sid = f"{run_id}:1"
        state, row = _mk(run_id, sid)
        await db_store.acreate(_approved_req(run_id, sid, id=rid))
        await db_store.adecide(rid, decision=STATUS_APPROVED, by="验收")
        async with AsyncSessionLocal() as db:
            await db.execute(
                text(
                    "UPDATE ops_hitl_requests "
                    "SET decided_at = now() - interval '2 hours' WHERE id = :id"
                ),
                {"id": rid},
            )
            await db.commit()
        # 真读路径复核：拨回已生效且实收 ISO str
        got = await db_store.aget(rid)
        assert isinstance(got["decided_at"], str)
        reason = await _delegation_issue_block_reason(state, row)
        assert reason is not None and "非只读" in reason
    finally:
        await _cleanup()

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


def _observe_graph_factory(*, checkpointer):
    """只含真 observe_node 的最小图（承 test_hitl_resume harness · interrupt 需真实 runnable）。"""
    builder = StateGraph(LgRagState)
    builder.add_node("observe", observe_node)
    builder.add_edge(START, "observe")
    builder.add_conditional_edges(
        "observe", route_after_react, {"replan": END, "settle": END}
    )
    return builder.compile(checkpointer=checkpointer)


async def test_ta3_single_subtask_resume_loop_completes(cap_env, monkeypatch):
    """TA3③（机制段 · decide→resume→done{completed}）：单子任务计划批准→恢复→成环。

    真链：_join_subtasks 拦 → _persist_hitl 落库 → observe 图真挂起 →
    store.adecide(approved) → resume_hitl_run 图真恢复（replan · 解锁留痕）→
    消费门放行签发判定 → 令牌真签发 → tool_exec_node 真执行（罐头回显）→
    _observe done==planned 且 unsatisfied=False（done{completed} 机制段收口）。
    live HTTP/SSE 全链（三 env 组 · 无 shim）留 40 复跑。
    """
    run_id = f"run-{uuid.uuid4().hex[:8]}"
    sid = f"{run_id}:1"
    state, row = _mk(run_id, sid)
    joined = await _join_subtasks(state)
    merged = {
        **state,
        "subtask_results": list(joined["subtask_results"]),
        "inflight_subtask_ids": [],
    }
    obs = _observe(merged)
    created, _ = await _persist_hitl(merged, obs, thread_id="t-ta3-loop")
    req = next(r for r in created if str(r.get("subtask_id")) == sid)
    assert req["unlock_subtask_id"] == sid  # D2 回填是 resume 不 409 的前提

    # 图真挂起：interrupt 载荷带本申请（delegation_issue 类）
    saver = InMemorySaver()
    suspended = None
    async for chunk in _observe_graph_factory(checkpointer=saver).astream(
        merged, {"configurable": {"thread_id": "t-ta3-loop"}}, stream_mode="updates"
    ):
        for intr in chunk.get("__interrupt__") or []:
            suspended = intr.value
    assert suspended is not None, "前置：图没有被挂起"
    assert suspended["reason"] == "hitl_waiting"
    assert any(r["blocked_by"] == _BLOCKED_BY for r in suspended["requests"])

    # decide(approved) → resume 图真恢复（verdict=replan · 解锁留痕）
    decided = await cap_env.adecide(req["id"], decision=STATUS_APPROVED, by="验收")
    assert decided["status"] == STATUS_APPROVED
    out = await resume_hitl_run(
        thread_id="t-ta3-loop",
        approved=[sid],
        decided_by="验收",
        checkpointer=saver,
        graph_factory=_observe_graph_factory,
    )
    final = out["state"]
    assert final["react_observation"]["verdict"] == "replan"
    assert final["hitl_unlocked_ids"] == [sid]

    # 重下发：消费门放行（匹配 approved 单据）→ 令牌真签发 → tool_exec 真执行
    # （Host 写放行 env 与消费门正交：Policy 写闸独立信号 · 不豁免≠不放行）
    monkeypatch.setenv("OPS_CAPABILITY_ALLOW_WRITE", "1")
    post = {**merged, "hitl_unlocked_ids": final["hitl_unlocked_ids"]}
    assert await _delegation_issue_block_reason(post, row) is None
    token = _issue_delegation_token(post, row)
    assert token is not None, "消费命中后令牌签发不得为空"
    exec_out = await tool_exec_node(
        {**post, "assigned_subtask": row, "delegation_token": token}
    )
    result = exec_out["subtask_results"][-1]
    assert result.get("subtask_id") == sid
    assert "error" not in result, f"成环执行失败：{result.get('error')!r}"
    assert "output" in result

    # 收口：终态计入 done 且无未满足项（done{completed} 机制段）
    obs_done = _observe({**post, "subtask_results": [result]})
    assert obs_done["done"] == obs_done["planned"] == 1
    assert obs_done["unsatisfied"] is False

async def test_ta4_consumption_hit_does_not_waive_gateway_or_policy(cap_env):
    """TA4-D（实操-D）：消费命中 ≠ 全链放行——签发判定放行后，无令牌 enforce
    验签门照拒；有令牌但无 Host 写放行信号 → Policy 写闸仍裁。"""
    from app.ops.capability import ainvoke as capability_ainvoke
    from app.ops.tenant_context import current_tenant_or_default

    run_id = f"run-{uuid.uuid4().hex[:8]}"
    sid = f"{run_id}:1"
    state, row = _mk(run_id, sid)
    await cap_env.acreate(_approved_req(run_id, sid))
    # ① 消费命中：delegation 签发判定放行（None）
    assert await _delegation_issue_block_reason(state, row) is None
    base_ctx = {
        "tenant_id": current_tenant_or_default(),
        "user_id": "",
        "run_id": run_id,
        "subtask_id": sid,
        "_delegation_required": True,
    }
    args = {"request_id": "r-1", "note": "x"}
    # ② 无委派令牌：enforce 验签门照拒（消费不过 gateway 验签层）
    cap = await capability_ainvoke(_TESTING_CAP, args, ctx=base_ctx)
    assert cap.ok is False
    # ③ 有令牌但无 Host 写放行：Policy 写闸仍裁（消费不过 Policy 层）
    token = _issue_delegation_token(state, row)
    assert token is not None
    cap2 = await capability_ainvoke(
        _TESTING_CAP, args, ctx={**base_ctx, "_delegation_token": token}
    )
    assert cap2.ok is False
    assert "write_not_confirmed" in (cap2.error or "")


async def test_ta5_off_mode_zero_store_touch(cap_env, monkeypatch, caplog):
    """TA5（FP-7）：delegation off 模式消费路径零触达（store 读 spy 零调用 ·
    无 delegation_approval_consumed 台账）。"""
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
    with caplog.at_level(logging.INFO, logger="app.ops.lg_rag.multi.nodes"):
        joined = await _join_subtasks(state)
    assert calls == []  # off：消费读零触达
    assert not any(
        "delegation_approval_consumed" in r.message for r in caplog.records
    )  # off：无新台账
    assert not any(
        r.get("blocked_by") == _BLOCKED_BY
        for r in joined.get("subtask_results", [])
    )


# --- TA6 decide 落库不动：router 409 守卫保留（prefix_touch 空 unlock）-------


def test_ta6_prefix_touch_empty_unlock_resume_still_409():
    """TA6（FP-4 · router.py:404-411 一行不动）：prefix_touch_required 类
    空 unlock 单据批准后 resume 仍 409（不静默按驳回收工）。"""
    import asyncio

    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    from app.ops.deps import require_admin_sync
    from app.ops.hitl.router import router

    store = InMemoryHitlStore()
    set_hitl_store(store)
    run_id = f"run-{uuid.uuid4().hex[:8]}"
    row = {
        "id": new_request_id(),
        "run_id": run_id,
        "thread_id": "t-ta6",
        "subtask_id": f"{run_id}:1",
        "blocked_by": "prefix_touch_required",
        "unlock_subtask_id": "",  # 空形态维持（D2 形态守卫不回填该类）
        "status": STATUS_PENDING,
        "created_at": time.time(),
    }
    asyncio.run(store.acreate(row))
    asyncio.run(store.adecide(row["id"], decision=STATUS_APPROVED, by="验收"))
    app = FastAPI()
    app.include_router(router, prefix="/api/ops")
    app.dependency_overrides[require_admin_sync] = lambda: None
    try:
        with TestClient(app) as client:
            res = client.post(f"/api/ops/hitl/requests/{row['id']}/resume")
        assert res.status_code == 409
        assert "unlock_subtask_id" in res.json()["detail"]
    finally:
        reset_hitl_store()

