"""stage-w-write-expand · hat 30（Q1=S1 仓内落笔型写）：第二条真实窄写能力
``ops.write.run_note`` 端到端接入既有受控写闸链。

验收映射（task_stage_w_write_expand · SPEC v0.1 A1–A8 / FP-1~FP-5）：

- **A2+ 加载期断言（loader V13）**：写能力 ``tenant_scoped: true`` 强制——mock 特例
  清单不扩容（仅 ``testing.write.echo`` · 以 testing/mock tag 为谓词）；
- **A6 字段钉死**：``ops.write.v1.yaml`` 真 loader 加载 · 字段逐条断言
  （``tenant_scoped=true`` / ``hitl.required: true`` / 顶层幂等键声明位 /
  独立写 tag ``run_note`` **不复用 testing tag**）；
- **FP-3 / A2** off 零 diff：默认加载面不含本能力（builtin 五枚基线不变）·
  env 未放行写 tag → baseline 可见集不含（放行 ``testing`` tag 也不可见）；
- **A1 端到端竖切**：闸拦（``capability_write_hitl_required``）→ pending →
  decide(approved) → resume → 重下发消费命中 → 真落笔
  （``ops_capability_notes`` 行落值 tenant/approval_id/subtask_id/幂等键）；
- **A2 负样本**：无审批 fail-closed 零落笔；decide(rejected) 不执行；
  ctx 缺租户谓词 → Policy 拒（``tenant_scope_missing``）；幂等重放不双写
  （内存 store 命中 + 模拟 store 丢失后 DB 唯一约束兜底两形态）；
- **A3 租户下推**：写意图 / 审批行 / 便签行三处 tenant_id 一致；
  同幂等键跨租户互不遮挡（键作用域 = 租户内）；
- **A4 审计串链**：span ``approval_id`` + 回执落值 + 便签行 ``approval_id``
  三处同一张审批单可串；
- **A5 反回归**：resume 单路径无第二实现（源码 grep 断言 · 承
  test_write_approval_gate 先例）；deny 判序零 diff 由既有
  test_capability_testing_write 全组承接（本文件不重复造面）。

红线对拍（本测试文件自身约束）：``registry.py`` / ``policy.py`` /
``lg_rag/multi/nodes.py`` 闸链一行不动（A5 由既有测试守护 + 本文件 grep 断言）。
"""

from __future__ import annotations

import inspect
import json
import uuid
from pathlib import Path

import pytest
from langchain_core.messages import HumanMessage
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph
from sqlalchemy import text

import app.ops.lg_rag.multi.nodes as nodes
from app.db.session import AsyncSessionLocal
from app.ops.capability import ainvoke, list_capabilities
from app.ops.capability import delegation as dl
from app.ops.capability.baseline import ENV_ALLOW_WRITE_TAGS, baseline_filter
from app.ops.capability.defaults import ensure_default_capabilities
from app.ops.capability.gateway import get_registry
from app.ops.capability.idempotency import (
    InMemoryIdempotencyStore,
    reset_idempotency_store,
    set_idempotency_store,
)
from app.ops.capability.manifest import (
    MANIFEST_DIR,
    ManifestError,
    extra_manifest_paths,
    load_capability_manifest,
)
from app.ops.capability.receipts import (
    InMemoryReceiptSink,
    reset_receipt_sink,
    set_receipt_sink,
)
from app.ops.hitl import reset_hitl_store, set_hitl_store
from app.ops.hitl.resume import resume_hitl_run
from app.ops.hitl.store import STATUS_APPROVED, STATUS_REJECTED, InMemoryHitlStore
from app.ops.lg_rag.multi.nodes import (
    _observe,
    _persist_hitl,
    observe_node,
    route_after_react,
    tool_exec_node,
)
from app.ops.lg_rag.state import LgRagState
from app.ops.tenant_context import TENANT_A, TENANT_B
from tests.conftest import DB_AVAILABLE

_NEW_MANIFEST = MANIFEST_DIR / "ops.write.v1.yaml"
_TESTING_MANIFEST = MANIFEST_DIR / "testing.v1.yaml"
_NEW_CAP = "ops.write.run_note"
_TESTING_CAP = "testing.write.echo"
_BLOCKED_BY_WRITE = "capability_write_hitl_required"

_DB_MARK = pytest.mark.skipif(not DB_AVAILABLE, reason="需要 PostgreSQL（opsdesk_test）")

# 测试数据统一前缀：清理与断言都按它过滤，绝不触碰其他行
_PREFIX = "stagew"


@pytest.fixture(autouse=True)
def _restore():
    dl.reset_delegation_state()
    yield
    reset_hitl_store()
    reset_idempotency_store()
    reset_receipt_sink()
    dl.reset_delegation_state()
    get_registry().clear()
    ensure_default_capabilities()


@pytest.fixture(autouse=True)
async def _db_clean():
    if DB_AVAILABLE:
        await _clear_notes()
    yield
    if DB_AVAILABLE:
        await _clear_notes()


@pytest.fixture
def run_note_env(monkeypatch):
    """新能力三层显式打开：manifest 显式加载 + 独立写 tag 放行 + 内存幂等/回执。

    **不设** ``OPS_CAPABILITY_ALLOW_WRITE``——Host 单次写放行由审批命中后注入
    （两道闸语义 · 编排层审批闸不被 env 豁免）。
    """
    monkeypatch.setenv(dl.ENV_MODE, "off")
    monkeypatch.delenv("OPS_CAPABILITY_ALLOW_WRITE", raising=False)
    monkeypatch.setenv(ENV_ALLOW_WRITE_TAGS, "run_note")
    load_capability_manifest(_NEW_MANIFEST)
    hitl_store = InMemoryHitlStore()
    set_hitl_store(hitl_store)  # 先落 store：_persist_hitl 建单面写同一份
    idem_store = InMemoryIdempotencyStore()
    set_idempotency_store(idem_store)
    sink = InMemoryReceiptSink()
    set_receipt_sink(sink)
    yield hitl_store, sink


# ---------------------------------------------------------------------------
# DB 小工具（真 PostgreSQL · opsdesk_test）
# ---------------------------------------------------------------------------


async def _clear_notes() -> None:
    async with AsyncSessionLocal() as session, session.begin():
        await session.execute(
            text("DELETE FROM ops_capability_notes WHERE idempotency_key LIKE :p"),
            {"p": f"{_PREFIX}-%"},
        )


async def _fetch_notes(idem_key: str) -> list[dict]:
    async with AsyncSessionLocal() as session:
        rows = await session.execute(
            text(
                "SELECT id, tenant_id, capability_id, run_id, subtask_id, approval_id,"
                " note, created_by, idempotency_key FROM ops_capability_notes"
                " WHERE idempotency_key = :k"
            ),
            {"k": idem_key},
        )
        cols = ("id", "tenant_id", "capability_id", "run_id", "subtask_id", "approval_id",
                "note", "created_by", "idempotency_key")
        return [dict(zip(cols, r, strict=True)) for r in rows.all()]


def _write_json(tmp_path: Path, name: str, caps: list[dict]) -> Path:
    path = tmp_path / name
    path.write_text(
        json.dumps({"version": 1, "capabilities": caps}, ensure_ascii=False),
        encoding="utf-8",
    )
    return path


def _write_probe(cid: str, **over) -> dict:
    """write 探针条目（V13 用 · 对齐 test_capability_testing_write 形态）。"""
    cap = {
        "id": cid,
        "kind": "local_fn",
        "description": "探针",
        "when_to_use": "单测",
        "args_schema": {"type": "object", "properties": {}},
        "tags": ["probe"],
        "risk_level": "medium",
        "side_effect": "write",
        "hitl": {"required": True},
        "idempotency_key": "{{request_id}}",
        "adapter": "local_fn:app.ops.capability.defaults:utc_now_iso",
    }
    cap.update(over)
    return cap


# ---------------------------------------------------------------------------
# A2+ · loader V13：写能力 tenant_scoped 强制（mock 特例清单不扩容）
# ---------------------------------------------------------------------------


def test_v13_write_requires_tenant_scoped(tmp_path: Path):
    """A2+①：写能力 tenant_scoped 缺省 false 且非 mock 特例 → 整文件 ManifestError。"""
    cap = _write_probe("probe.write_notenant")
    with pytest.raises(ManifestError, match="V13: side_effect=write 必须 tenant_scoped: true"):
        load_capability_manifest(_write_json(tmp_path, "v13.json", [cap]))
    assert "probe.write_notenant" not in {s.capability_id for s in list_capabilities()}


def test_v13_tenant_scoped_write_loads(tmp_path: Path):
    """A2+②：写能力 tenant_scoped: true → 照常加载（新能力的唯一合法出口）。"""
    cap = _write_probe("probe.write_tenant", tenant_scoped=True)
    result = load_capability_manifest(_write_json(tmp_path, "ok.json", [cap]))
    assert "probe.write_tenant" in result.registered_ids


def test_v13_mock_exception_still_loads():
    """A2+③：既有 mock 特例 testing.write.echo（testing/mock tag 谓词命中）零 diff 可加载。"""
    result = load_capability_manifest(_TESTING_MANIFEST)
    assert result.registered_ids == (_TESTING_CAP,)


def test_v13_exception_requires_mock_tag_predicate(tmp_path: Path):
    """A2+④：特例清单不扩容 + 谓词钉死——冒充 testing.write.echo 但无 testing/mock tag → 拦。"""
    cap = _write_probe(_TESTING_CAP, tags=["write"])
    with pytest.raises(ManifestError, match="V13: side_effect=write 必须 tenant_scoped: true"):
        load_capability_manifest(_write_json(tmp_path, "fake.json", [cap]))


# ---------------------------------------------------------------------------
# A6 / FP-3 · 新能力 manifest 字段钉死 + off 零 diff + 可见性
# ---------------------------------------------------------------------------


def test_a6_manifest_fields_pinned():
    """A6：ops.write.v1.yaml 真 loader 加载 · 字段逐条钉死（registry 真值）。"""
    result = load_capability_manifest(_NEW_MANIFEST)
    assert result.registered_ids == (_NEW_CAP,)
    entry = get_registry().get(_NEW_CAP)
    assert entry is not None
    spec, adapter = entry
    assert spec.side_effect == "write"
    assert spec.kind == "local_fn"
    assert spec.tenant_scoped is True  # D2 钉死：与 testing.write.echo false 对照
    assert spec.hitl_required is True  # V2 强制 + SPEC D1 显式声明
    assert spec.idempotency_key == "{{request_id}}"  # 裁定四顶层声明位
    assert spec.risk_level == "medium"  # deny_high_risk 无豁免口（标 high 永不可见）
    assert "run_note" in spec.tags  # 独立写 tag
    assert "testing" not in spec.tags and "mock" not in spec.tags  # 不复用 mock tag
    assert spec.enabled is True
    # 可撤销性四字段齐（字段族对齐 builtin/testing 范式）
    assert spec.reversible is True
    assert spec.execution_type == "instant"
    assert spec.max_reversal_latency == 0
    assert spec.requires_stop_support is False
    assert adapter is not None and callable(getattr(adapter, "ainvoke", None))


def test_fp3_off_zero_diff_default_surface(monkeypatch):
    """FP-3：默认加载面零 diff——三 env 不设 → 注册表不含本能力（builtin 五枚基线）。"""
    monkeypatch.delenv("OPS_CAPABILITY_EXTRA_MANIFESTS", raising=False)
    monkeypatch.delenv(ENV_ALLOW_WRITE_TAGS, raising=False)
    monkeypatch.delenv("LG_RAG_DELEGATION_TOKEN_MODE", raising=False)
    assert extra_manifest_paths() == ()
    snap = get_registry().snapshot()
    assert _NEW_CAP not in snap["capability_ids"]
    assert snap["count"] == 5


def test_visibility_needs_run_note_allow_tag(monkeypatch):
    """加载≠可见：未放行写 tag → baseline 可见集不含；放行 run_note → 含。"""
    load_capability_manifest(_NEW_MANIFEST)
    monkeypatch.delenv(ENV_ALLOW_WRITE_TAGS, raising=False)
    ids = {s.capability_id for s in list_capabilities(filter=baseline_filter(node_role="t"))}
    assert _NEW_CAP not in ids
    monkeypatch.setenv(ENV_ALLOW_WRITE_TAGS, "run_note")
    ids = {s.capability_id for s in list_capabilities(filter=baseline_filter(node_role="t"))}
    assert _NEW_CAP in ids


def test_visibility_testing_tag_does_not_unlock(monkeypatch):
    """SPEC D1：独立写 tag——放行 testing tag **不**使本能力可见（不放行 testing 复用）。"""
    load_capability_manifest(_NEW_MANIFEST)
    load_capability_manifest(_TESTING_MANIFEST)
    monkeypatch.setenv(ENV_ALLOW_WRITE_TAGS, "testing")
    ids = {s.capability_id for s in list_capabilities(filter=baseline_filter(node_role="t"))}
    assert _TESTING_CAP in ids  # 对照：testing tag 放行对既有 mock 生效
    assert _NEW_CAP not in ids  # 本能力不可见（run_note tag 未放行）


# ---------------------------------------------------------------------------
# A1 · 端到端竖切：闸拦 → pending → decide(approved) → resume → 真落笔
# （承 test_write_approval_gate W0/W1/W3 全链范式 · 适配器换真实落笔）
# ---------------------------------------------------------------------------


def _mk_state(run_id: str, sid: str, req_id: str) -> tuple[dict, dict]:
    """单步写 tool 计划 state + 该步 row。"""
    state = {
        "messages": [HumanMessage(content="写一条 run 备注")],
        "run_id": run_id,
        "subtasks": [
            {
                "subtask_id": sid,
                "id": sid,
                "type": "tool",
                "input": {"run_id": run_id, "note": "验收便签", "request_id": req_id},
                "args": {"run_id": run_id, "note": "验收便签", "request_id": req_id},
                "tool": _NEW_CAP,
                "depends_on": [],
            }
        ],
        "subtask_results": [],
        "inflight_subtask_ids": [],
        "allowed_capability_ids": [_NEW_CAP],
    }
    return state, state["subtasks"][0]


def _observe_graph_factory(*, checkpointer):
    """只含真 observe_node 的最小图（承 test_hitl_resume harness）。"""
    builder = StateGraph(LgRagState)
    builder.add_node("observe", observe_node)
    builder.add_edge(START, "observe")
    builder.add_conditional_edges("observe", route_after_react, {"replan": END, "settle": END})
    return builder.compile(checkpointer=checkpointer)


@_DB_MARK
async def test_a1_end_to_end_approve_resume_real_write(run_note_env, monkeypatch):
    """A1+A3+A4 全链：fail-closed 挂起 → pending（写意图钉死）→ 图真挂起 →
    decide(approved) → resume（单一驱动）→ 重下发消费命中 → **真落笔**——
    便签行/回执/span 三处 approval_id 串链 · 三处 tenant_id 一致。"""
    _hitl, sink = run_note_env
    run_id = f"{_PREFIX}-{uuid.uuid4().hex[:8]}"
    sid = f"{run_id}:1"
    req_id = f"{run_id}-req"
    state, row = _mk_state(run_id, sid, req_id)

    # ① 无审批 → fail-closed 挂起（编排层闸 · adapter 零触达 · 零落笔）
    out = await tool_exec_node({**state, "assigned_subtask": row})
    blocked = out["subtask_results"][-1]
    assert blocked.get("blocked_by") == _BLOCKED_BY_WRITE
    assert blocked.get("hitl_required") is True
    assert blocked.get("tenant_id") == TENANT_A  # A3：拦单即带租户
    assert await _fetch_notes(req_id) == []

    # ② pending 落库（写意图结构钉死）
    merged = {**state, "subtask_results": [blocked], "inflight_subtask_ids": []}
    obs = _observe(merged)
    assert obs["hitl_pending"] == [sid]
    created, unpersisted = await _persist_hitl(merged, obs, thread_id="t-s1")
    assert unpersisted is False
    req = next(r for r in created if str(r.get("subtask_id")) == sid)
    assert req["blocked_by"] == _BLOCKED_BY_WRITE
    assert req["unlock_subtask_id"] == sid
    assert req["tenant_id"] == TENANT_A  # A3：审批行带租户
    intent = req["payload"]["write_intent"]
    assert intent["capability_id"] == _NEW_CAP
    assert intent["tenant_id"] == TENANT_A  # A3：写意图带租户
    assert intent["idempotency_key"] == "{{request_id}}"

    # ③ 图真挂起（freeze 形态钉死）→ decide(approved) → resume 单一驱动
    saver = InMemorySaver()
    suspended = None
    async for chunk in _observe_graph_factory(checkpointer=saver).astream(
        merged, {"configurable": {"thread_id": "t-s1"}}, stream_mode="updates"
    ):
        for intr in chunk.get("__interrupt__") or []:
            suspended = intr.value
    assert suspended is not None and suspended["reason"] == "hitl_waiting"

    store = _hitl  # _persist_hitl 已把单落进同一 store（fixture 先设）
    decided = await store.adecide(req["id"], decision=STATUS_APPROVED, by="验收")
    assert decided["status"] == STATUS_APPROVED

    resumed = await resume_hitl_run(
        thread_id="t-s1",
        approved=[sid],
        decided_by="验收",
        checkpointer=saver,
        graph_factory=_observe_graph_factory,
    )
    final = resumed["state"]
    assert final["react_observation"]["verdict"] == "replan"
    assert final["hitl_unlocked_ids"] == [sid]

    # ④ 重下发：消费命中 → Host 单次写放行 + approval_id 注入 → 真落笔
    node_spans: list[dict] = []
    gw_spans: list[dict] = []
    monkeypatch.setattr(nodes, "_record_span_metadata", lambda md: node_spans.append(md))
    monkeypatch.setattr(
        "app.ops.capability.gateway.update_current_span_metadata",
        lambda md: gw_spans.append(md),
    )
    post = {**merged, "hitl_unlocked_ids": final["hitl_unlocked_ids"]}
    exec_out = await tool_exec_node({**post, "assigned_subtask": row})
    result = exec_out["subtask_results"][-1]
    assert result.get("subtask_id") == sid
    assert "error" not in result, f"批准后重下发仍失败：{result.get('error')!r}"
    assert result["output"]["written"] is True
    assert result["output"]["tool"] == "ops_write_run_note"

    # A1 落笔断言：便签行落值（tenant / approval / subtask / 幂等键）
    notes = await _fetch_notes(req_id)
    assert len(notes) == 1
    note = notes[0]
    assert note["tenant_id"] == TENANT_A  # A3：执行行带租户（与拦单/审批行一致）
    assert note["capability_id"] == _NEW_CAP
    assert note["run_id"] == run_id
    assert note["subtask_id"] == sid
    assert note["approval_id"] == req["id"]  # A4：便签行串审批单
    assert note["idempotency_key"] == req_id
    assert note["note"] == "验收便签"

    # A4 审计串链三处：消费台账 / capability span / 回执
    consumed = [c for c in node_spans if c.get("capability_write_approval_consumed") is True]
    assert len(consumed) == 1
    assert consumed[0]["approval_id"] == req["id"]
    gw = [m for m in gw_spans if m.get("capability_id") == _NEW_CAP]
    assert gw and gw[-1]["approval_id"] == req["id"]
    assert gw[-1]["side_effect"] == "write"
    receipts = sink.by_idempotency_key(req_id)
    assert len(receipts) == 1
    assert receipts[0].ok is True
    assert receipts[0].write_confirmed is True  # Host 单次放行下执行
    assert receipts[0].tenant_id == TENANT_A
    assert receipts[0].captured.get("note_id") == str(note["id"])  # UUID 同串链


@_DB_MARK
async def test_a2_no_approval_zero_write(run_note_env):
    """FP-1 负样本：无审批直接执行 → fail-closed 挂起 · 便签表零落笔。"""
    _store, _sink = run_note_env
    run_id = f"{_PREFIX}-{uuid.uuid4().hex[:8]}"
    sid = f"{run_id}:1"
    req_id = f"{run_id}-req"
    state, row = _mk_state(run_id, sid, req_id)

    out = await tool_exec_node({**state, "assigned_subtask": row})
    blocked = out["subtask_results"][-1]
    assert blocked.get("blocked_by") == _BLOCKED_BY_WRITE
    assert blocked.get("hitl_required") is True
    assert await _fetch_notes(req_id) == []


@_DB_MARK
async def test_a2_rejected_settles_without_write(run_note_env):
    """FP-1 反向：decide(rejected) → resume 收工（settle）· 不执行 · 零落笔。"""
    store, _sink = run_note_env
    run_id = f"{_PREFIX}-{uuid.uuid4().hex[:8]}"
    sid = f"{run_id}:1"
    req_id = f"{run_id}-req"
    state, row = _mk_state(run_id, sid, req_id)

    out = await tool_exec_node({**state, "assigned_subtask": row})
    blocked = out["subtask_results"][-1]
    merged = {**state, "subtask_results": [blocked], "inflight_subtask_ids": []}
    obs = _observe(merged)
    created, _ = await _persist_hitl(merged, obs, thread_id="t-s1r")
    req = next(r for r in created if str(r.get("subtask_id")) == sid)

    saver = InMemorySaver()
    async for _chunk in _observe_graph_factory(checkpointer=saver).astream(
        merged, {"configurable": {"thread_id": "t-s1r"}}, stream_mode="updates"
    ):
        pass  # 前置：图完成挂起
    await store.adecide(req["id"], decision=STATUS_REJECTED, by="验收")
    resumed = await resume_hitl_run(
        thread_id="t-s1r",
        approved=[],
        rejected=[sid],
        decided_by="验收",
        checkpointer=saver,
        graph_factory=_observe_graph_factory,
    )
    assert resumed["state"]["react_observation"]["verdict"] == "settle"
    assert await _fetch_notes(req_id) == []  # 驳回不执行 · 零落笔


# ---------------------------------------------------------------------------
# A2 · 租户谓词 / FP-4 幂等重放 / A3 租户隔离（gateway ainvoke 面直测）
# ---------------------------------------------------------------------------


def _invoke_ctx(tenant: str) -> dict:
    return {"tenant_id": tenant, "_host_policy": {"allow_write": True}}


@_DB_MARK
async def test_a2_missing_tenant_predicate_blocked(run_note_env):
    """tenant_scoped 强制：ctx 无租户谓词 → Policy 拒（tenant_scope_missing）· 零落笔。"""
    _store, _sink = run_note_env
    req_id = f"{_PREFIX}-{uuid.uuid4().hex[:8]}-req"
    res = await ainvoke(
        _NEW_CAP,
        {"run_id": f"{_PREFIX}-r", "note": "x", "request_id": req_id},
        ctx={"_host_policy": {"allow_write": True}},  # 无 tenant_id
    )
    assert res.ok is False
    assert "tenant_scope_missing" in (res.error or "")
    assert await _fetch_notes(req_id) == []


@_DB_MARK
async def test_a2_write_without_release_blocked(run_note_env):
    """Policy 写闸正交：有租户但无 Host/env 写放行 → write_not_confirmed · 零落笔。"""
    _store, _sink = run_note_env
    req_id = f"{_PREFIX}-{uuid.uuid4().hex[:8]}-req"
    res = await ainvoke(
        _NEW_CAP,
        {"run_id": f"{_PREFIX}-r", "note": "x", "request_id": req_id},
        ctx={"tenant_id": TENANT_A},  # 无 _host_policy 放行
    )
    assert res.ok is False
    assert "write_not_confirmed" in (res.error or "")
    assert await _fetch_notes(req_id) == []


@_DB_MARK
async def test_fp4_idempotent_replay_no_double_write(run_note_env):
    """FP-4：同幂等键重放不双写——两形态钉死：
    ① 内存 store 命中（duplicate）→ 不执行；
    ② store 换全新实例（模拟重启丢失）→ DB (tenant, key) 唯一约束兜底仍不双写。"""
    _store, _sink = run_note_env
    run_id = f"{_PREFIX}-{uuid.uuid4().hex[:8]}"
    req_id = f"{run_id}-req"
    args = {"run_id": run_id, "note": "重放钉死", "request_id": req_id}
    ctx = _invoke_ctx(TENANT_A)

    first = await ainvoke(_NEW_CAP, args, ctx=ctx)
    assert first.ok and first.output["written"] is True
    assert len(await _fetch_notes(req_id)) == 1

    replay = await ainvoke(_NEW_CAP, args, ctx=ctx)
    assert replay.ok and replay.output["duplicated"] is True
    assert replay.output["written"] is False
    assert len(await _fetch_notes(req_id)) == 1  # 不双写

    set_idempotency_store(InMemoryIdempotencyStore())  # 模拟进程重启 store 丢失
    replay2 = await ainvoke(_NEW_CAP, args, ctx=ctx)
    assert replay2.ok and replay2.output["duplicated"] is True
    assert len(await _fetch_notes(req_id)) == 1  # DB 唯一约束兜底 · 仍一行


@_DB_MARK
async def test_a3_same_key_tenant_isolated(run_note_env):
    """A3：幂等键作用域 = 租户内——同键 A/B 两租户各落一笔，互不遮挡。"""
    _store, _sink = run_note_env
    req_id = f"{_PREFIX}-{uuid.uuid4().hex[:8]}-shared"
    args_a = {"run_id": f"{_PREFIX}-ra", "note": "租户 A 的便签", "request_id": req_id}
    args_b = {"run_id": f"{_PREFIX}-rb", "note": "租户 B 的便签", "request_id": req_id}

    res_a = await ainvoke(_NEW_CAP, args_a, ctx=_invoke_ctx(TENANT_A))
    res_b = await ainvoke(_NEW_CAP, args_b, ctx=_invoke_ctx(TENANT_B))
    assert res_a.ok and res_a.output["written"] is True
    assert res_b.ok and res_b.output["written"] is True  # 跨租户不判 duplicate

    notes = await _fetch_notes(req_id)
    assert len(notes) == 2
    by_tenant = {n["tenant_id"]: n for n in notes}
    assert by_tenant[TENANT_A]["note"] == "租户 A 的便签"
    assert by_tenant[TENANT_B]["note"] == "租户 B 的便签"


# ---------------------------------------------------------------------------
# A5 · 反回归钉死（resume 单路径 · 闸链文件本任务零改动由既有测试全组承接）
# ---------------------------------------------------------------------------


def test_a5_resume_single_path_no_second_impl():
    """A5：恢复单路径无第二实现（源码 grep · 承 test_write_approval_gate 先例）。"""
    import app.ops.hitl.auto_resume as auto_resume
    from app.ops.hitl import router as hitl_router

    ar_src = inspect.getsource(auto_resume)
    assert "from app.ops.hitl.router import _execute_decided_resume" in ar_src
    assert ar_src.count("def _execute_decided_resume") == 0  # 无第二实现
    hr_src = inspect.getsource(hitl_router)
    assert hr_src.count("def _execute_decided_resume") == 1  # 唯一定义点

