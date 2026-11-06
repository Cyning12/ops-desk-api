"""ops-write-catalog-reconcile · hat 30（issue #336 · 设计闸裁决=案③两者）：

``ops.write.*`` 能力**目录对账**常驻测试面——A1 锚点语义（task 档专节为唯一真源）：

- **双口径**：口径① intent 准入（真实闸链实际行为）× 口径② spec 目录
  （能力声明面）同时成立；
- **双向漂移即缺陷**：声明有·行为无 / 行为有·声明无，两方向漂移在本文件
  对账断言下都必须红；
- **对账可机断**：断言锚到具体文件 + 键 / 函数 / 事件名。

验收映射（task_ops_write_catalog_reconcile · D-rec-1~D-rec-3）：

- **族① 一致性机检（打底 · CI 常驻）**：A1 声明基准 ↔
  ``ops.write.v1.yaml`` 真文件 ↔ 加载后 ``CapabilitySpec``/adapter 全字段
  对账；三层显式打开各判据（默认加载面排除 / 写 tag 放行谓词 / mock 特例
  清单不扩容）；漂移矩阵——构造漂移必被拦（loader ManifestError 或
  对账断言红）；
- **族② 端到端实跑（补强 · 真闸链驱动）**：正样本全链
  （闸拦 → pending → decide(approved) → resume → 消费命中 → 真落笔）按
  声明逐条取行为实证；输出契约双向对账（成功路径输出键集 == 声明
  output_fields；重放路径输出键集 ⊆ 声明 output_fields）；
  args_schema 声明的行为层负样本（缺必填 / 多送键 / 类型错 →
  args_schema_invalid · 零落笔）。

红线对拍（本测试文件自身约束）：``app/`` 实现一行不动（对账只经测试面达成 ·
issue #336 红线）；SSE 事件表零 diff（本文件不断言新增任何事件类型）；
fail-closed 判据永不放宽（负样本禁改成放行）。既有 stage-w 16 测为
建设期机制面，本文件为对账面，两族互补不重复造面（幂等 store 丢失
DB 兜底形态等已由 ``test_fp4_idempotent_replay_no_double_write`` 承接）。
"""

from __future__ import annotations

import json
import uuid
from pathlib import Path
from typing import Any

import pytest
import yaml
from langchain_core.messages import HumanMessage
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph
from sqlalchemy import text

import app.ops.lg_rag.multi.nodes as nodes
from app.db.session import AsyncSessionLocal
from app.ops.capability import ainvoke, list_capabilities
from app.ops.capability import delegation as dl
from app.ops.capability.baseline import ENV_ALLOW_WRITE_TAGS, baseline_filter
from app.ops.capability.defaults import ensure_default_capabilities, ops_write_run_note
from app.ops.capability.gateway import get_registry
from app.ops.capability.idempotency import (
    InMemoryIdempotencyStore,
    reset_idempotency_store,
    set_idempotency_store,
)
from app.ops.capability.manifest import (
    DEFAULT_MANIFEST_FILES,
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
from app.ops.hitl.store import STATUS_APPROVED, InMemoryHitlStore
from app.ops.lg_rag.multi.nodes import (
    _observe,
    _persist_hitl,
    observe_node,
    route_after_react,
    tool_exec_node,
)
from app.ops.lg_rag.state import LgRagState
from app.ops.tenant_context import TENANT_A
from tests.conftest import DB_AVAILABLE

_NEW_MANIFEST = MANIFEST_DIR / "ops.write.v1.yaml"
_TESTING_MANIFEST = MANIFEST_DIR / "testing.v1.yaml"
_NEW_CAP = "ops.write.run_note"
_TESTING_CAP = "testing.write.echo"
_BLOCKED_BY_WRITE = "capability_write_hitl_required"

_DB_MARK = pytest.mark.skipif(not DB_AVAILABLE, reason="需要 PostgreSQL（opsdesk_test）")

# 测试数据统一前缀：清理与断言都按它过滤，绝不触碰其他行
_PREFIX = "recon"


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
    """对账环境：manifest 显式加载 + 独立写 tag 放行 + 内存 hitl/幂等/回执。

    与 stage-w 同范式（三层显式打开），对账断言在其上取声明↔行为双口径实证。
    """
    monkeypatch.setenv(dl.ENV_MODE, "off")
    monkeypatch.delenv("OPS_CAPABILITY_ALLOW_WRITE", raising=False)
    monkeypatch.setenv(ENV_ALLOW_WRITE_TAGS, "run_note")
    load_capability_manifest(_NEW_MANIFEST)
    hitl_store = InMemoryHitlStore()
    set_hitl_store(hitl_store)
    set_idempotency_store(InMemoryIdempotencyStore())
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


# ---------------------------------------------------------------------------
# A1 声明基准（口径② · spec 目录）：SPEC v0.1 + HG-OPS-WRITE-COVERAGE-DESIGN
# 签认的声明 of record——对账真值，独立于 manifest 文件本体（文件是声明的
# 实现载体，基准是声明本身；文件漂移 → 对账红）。
# ---------------------------------------------------------------------------

_DECLARED_BASELINE: dict[str, Any] = {
    "capability_id": "ops.write.run_note",
    "kind": "local_fn",
    "description": "写 run 备注/审计便签到本仓 ops_capability_notes（受控写 · 须经 HITL 人工审批）",
    "tags": ("ops", "run_note", "write"),
    "risk_level": "medium",  # deny_high_risk 无豁免口（标 high 永不可见）
    "side_effect": "write",
    "enabled": True,
    "tenant_scoped": True,  # loader V13 强制 · 与 testing.write.echo false 对照
    "hitl_required": True,
    "hitl_snapshot_fields": ("run_id", "note"),
    "idempotency_key": "{{request_id}}",  # 裁定四顶层声明位
    "args_schema": {
        "type": "object",
        "properties": {
            "run_id": {"type": "string", "description": "目标 run 标识（便签归因）"},
            "note": {"type": "string", "description": "备注正文（审计便签内容）"},
            "request_id": {
                "type": "string",
                "description": "幂等键源（租户内唯一 · 重放不双写）",
            },
        },
        "required": ["run_id", "note", "request_id"],
        "additionalProperties": False,
    },
    "output_fields": (
        "tool",
        "written",
        "note_id",
        "run_id",
        "tenant_id",
        "approval_id",
        "idempotency_key",
        "duplicated",
        "duplicate_of",
    ),
    "output_schema": {"required": ["$.tool", "$.written"]},
    "reversible": True,
    "execution_type": "instant",
    "max_reversal_latency": 0,
    "requires_stop_support": False,
    "adapter_fn": ops_write_run_note,  # local_fn 目标函数本体（身份对账）
}


def _reconcile_loaded_spec(spec: Any, adapter: Any) -> None:
    """A1 对账核心：加载后 spec/adapter ↔ 声明基准逐字段断言（漂移即红）。"""
    b = _DECLARED_BASELINE
    assert spec.capability_id == b["capability_id"]
    assert spec.kind == b["kind"]
    assert spec.description == b["description"]
    assert spec.tags == b["tags"]
    assert spec.risk_level == b["risk_level"]
    assert spec.side_effect == b["side_effect"]
    assert spec.enabled is b["enabled"]
    assert spec.tenant_scoped is b["tenant_scoped"]
    assert spec.hitl_required is b["hitl_required"]
    assert spec.hitl_snapshot_fields == b["hitl_snapshot_fields"]
    assert spec.idempotency_key == b["idempotency_key"]
    assert spec.args_schema == b["args_schema"]
    assert spec.output_fields == b["output_fields"]
    assert spec.output_schema == b["output_schema"]
    assert spec.reversible is b["reversible"]
    assert spec.execution_type == b["execution_type"]
    assert spec.max_reversal_latency == b["max_reversal_latency"]
    assert spec.requires_stop_support is b["requires_stop_support"]
    # adapter 身份：local_fn 目标函数 == 声明执行体（行为面锚点）
    assert adapter is not None and getattr(adapter, "_fn", None) is b["adapter_fn"]


# ---------------------------------------------------------------------------
# 族① · 一致性机检（A1 口径②打底 · CI 常驻 · 双向漂移秒红）
# ---------------------------------------------------------------------------


def _load_ops_write() -> tuple[Any, Any]:
    """真文件加载 → (spec, adapter)。"""
    result = load_capability_manifest(_NEW_MANIFEST)
    assert result.registered_ids == (_NEW_CAP,)
    entry = get_registry().get(_NEW_CAP)
    assert entry is not None
    return entry


def test_machine_manifest_file_matches_declaration_baseline():
    """声明有·行为无（声明面）：manifest 文件本体 ↔ A1 声明基准全字段对账。

    文件是声明的实现载体：任何字段漂移（含 args_schema 子键 / output_fields
    清单 / snapshot_fields）在本断言下秒红。
    """
    spec, adapter = _load_ops_write()
    _reconcile_loaded_spec(spec, adapter)


def test_machine_raw_yaml_round_trips_through_loader():
    """机检可机断锚：raw YAML 逐键经 loader 映射无丢失（解析面 ↔ 注册面）。"""
    raw = yaml.safe_load(_NEW_MANIFEST.read_text(encoding="utf-8"))
    (raw_cap,) = raw["capabilities"]
    spec, _adapter = _load_ops_write()
    assert raw_cap["id"] == spec.capability_id
    assert raw_cap["hitl"]["required"] is spec.hitl_required
    assert tuple(raw_cap["hitl"]["snapshot_fields"]) == spec.hitl_snapshot_fields
    assert raw_cap["args_schema"] == spec.args_schema
    assert tuple(raw_cap["output_fields"]) == spec.output_fields
    assert raw_cap["reversible"] is spec.reversible
    assert raw_cap["execution_type"] == spec.execution_type
    assert raw_cap["max_reversal_latency"] == spec.max_reversal_latency
    assert raw_cap["requires_stop_support"] is spec.requires_stop_support
    assert raw_cap["adapter"].startswith("local_fn:app.ops.capability.defaults:")


def test_machine_three_layer_opening_gates():
    """三层显式打开判据对账（加载面/放行面）：
    ① 默认加载面排除（off 零 diff · 不进 DEFAULT_MANIFEST_FILES · 三 env 不设
    → 注册表不含 · builtin 五枚基线）；② 放行谓词 = 独立写 tag run_note。"""
    assert _NEW_MANIFEST not in DEFAULT_MANIFEST_FILES
    assert extra_manifest_paths() == ()
    snap = get_registry().snapshot()
    assert _NEW_CAP not in snap["capability_ids"]
    assert snap["count"] == 5
    # 放行谓词：spec.tags 含 run_note 且不含 testing/mock（复用 mock 谓词即破格）
    spec, _adapter = _load_ops_write()
    assert "run_note" in spec.tags
    assert "testing" not in spec.tags and "mock" not in spec.tags


def test_machine_visibility_gate_matches_declaration(monkeypatch):
    """可见性闸 ↔ 声明对账：加载在场 ≠ 可见——未放行 tag 不可见；放行
    run_note 可见；放行 testing tag 不解锁本能力（独立写 tag 声明）。"""
    _load_ops_write()
    monkeypatch.delenv(ENV_ALLOW_WRITE_TAGS, raising=False)
    ids = {s.capability_id for s in list_capabilities(filter=baseline_filter(node_role="t"))}
    assert _NEW_CAP not in ids
    monkeypatch.setenv(ENV_ALLOW_WRITE_TAGS, "run_note")
    ids = {s.capability_id for s in list_capabilities(filter=baseline_filter(node_role="t"))}
    assert _NEW_CAP in ids
    monkeypatch.setenv(ENV_ALLOW_WRITE_TAGS, "testing")
    ids = {s.capability_id for s in list_capabilities(filter=baseline_filter(node_role="t"))}
    assert _NEW_CAP not in ids


# ---- 漂移矩阵：构造漂移必被拦（loader ManifestError 或对账断言红） ----


def _drift_remove_idempotency_key(raw: dict) -> None:
    raw.pop("idempotency_key", None)


def _drift_hitl_not_required(raw: dict) -> None:
    raw["hitl"]["required"] = False


def _drift_risk_high(raw: dict) -> None:
    raw["risk_level"] = "high"  # deny_high_risk 暴露面漂移


def _drift_tags_lose_run_note(raw: dict) -> None:
    raw["tags"] = ["ops", "write"]


def _drift_adapter_nonexistent(raw: dict) -> None:
    raw["adapter"] = "local_fn:app.ops.capability.defaults:no_such_fn"


def _drift_args_drop_required(raw: dict) -> None:
    raw["args_schema"]["required"] = ["run_id", "note"]


def _drift_args_allow_extra(raw: dict) -> None:
    raw["args_schema"]["additionalProperties"] = True


def _drift_output_fields_drop_written(raw: dict) -> None:
    raw["output_fields"] = [f for f in raw["output_fields"] if f != "written"]


def _drift_snapshot_drop_note(raw: dict) -> None:
    raw["hitl"]["snapshot_fields"] = ["run_id"]


def _drift_side_effect_read(raw: dict) -> None:
    raw["side_effect"] = "read"  # 写闸语义漂移（最危险面）


_DRIFT_CASES = [
    pytest.param(
        _drift_remove_idempotency_key, "idempotency_key 声明位被删", id="no-idempotency-key"
    ),
    pytest.param(_drift_hitl_not_required, "hitl.required 漂移为 false", id="hitl-not-required"),
    pytest.param(_drift_risk_high, "risk_level 漂移为 high", id="risk-high"),
    pytest.param(
        _drift_tags_lose_run_note, "独立写 tag run_note 丢失", id="tags-lose-run-note"
    ),
    pytest.param(
        _drift_adapter_nonexistent, "adapter 目标函数漂移为不存在函数", id="adapter-nonexistent"
    ),
    pytest.param(
        _drift_args_drop_required,
        "args_schema 缺必填 request_id（幂等键源裸奔）",
        id="args-drop-required",
    ),
    pytest.param(
        _drift_args_allow_extra, "args_schema additionalProperties 放宽", id="args-allow-extra"
    ),
    pytest.param(
        _drift_output_fields_drop_written,
        "output_fields 丢 written（结果契约漂移）",
        id="output-drop-written",
    ),
    pytest.param(
        _drift_snapshot_drop_note,
        "hitl snapshot_fields 丢 note（审批快照漂移）",
        id="snapshot-drop-note",
    ),
    pytest.param(_drift_side_effect_read, "side_effect 漂移为 read（写闸逃逸）", id="read-side-effect"),
]


@pytest.mark.parametrize(("mutate", "why"), _DRIFT_CASES)
def test_machine_drift_matrix_caught(tmp_path: Path, mutate, why: str):
    """漂移矩阵（构造漂移即红的常驻形态）：每枚漂移须被 loader 或 A1 对账拦下。

    红语义：若某枚漂移加载成功且 `_reconcile_loaded_spec` 不红 → 对账面破口，
    本测试即红——这就是「双向漂移即缺陷」的机检兜底。
    """
    raw = yaml.safe_load(_NEW_MANIFEST.read_text(encoding="utf-8"))
    (raw_cap,) = raw["capabilities"]
    mutate(raw_cap)
    caught: Exception | None = None
    try:
        load_capability_manifest(_write_json(tmp_path, "drift.json", [raw_cap]))
        entry = get_registry().get(_NEW_CAP)
        assert entry is not None, "漂移后能力未注册（加载面拦截）"
        _reconcile_loaded_spec(*entry)
    except (ManifestError, AssertionError) as exc:  # 漂移被拦 = 对账绿
        caught = exc
    assert caught is not None, f"漂移未被拦：{why}（对账面破口）"


# ---------------------------------------------------------------------------
# 族② · 端到端实跑（A1 口径①补强 · 真闸链驱动 · 补「声明有·行为无」行为层实证）
# ---------------------------------------------------------------------------


def _mk_state(run_id: str, sid: str, req_id: str) -> tuple[dict, dict]:
    """单步写 tool 计划 state + 该步 row（承 stage-w 全链范式）。"""
    state = {
        "messages": [HumanMessage(content="写一条 run 备注")],
        "run_id": run_id,
        "subtasks": [
            {
                "subtask_id": sid,
                "id": sid,
                "type": "tool",
                "input": {"run_id": run_id, "note": "对账便签", "request_id": req_id},
                "args": {"run_id": run_id, "note": "对账便签", "request_id": req_id},
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
    builder = StateGraph(LgRagState)
    builder.add_node("observe", observe_node)
    builder.add_edge(START, "observe")
    builder.add_conditional_edges("observe", route_after_react, {"replan": END, "settle": END})
    return builder.compile(checkpointer=checkpointer)


@_DB_MARK
async def test_e2e_declaration_behavior_map(run_note_env, monkeypatch):
    """声明→行为逐条映射（全链真跑）：每枚声明在真实闸链取到行为实证。

    - hitl.required → 无审批 fail-closed 挂起（blocked_by 钉死 · 零落笔）；
    - snapshot_fields 声明 → 写意图快照含 run_id + note；
    - 全链 → decide(approved) → resume 单路径 → 消费命中 → 真落笔；
    - output_fields 声明 → 成功路径输出键集 == 声明清单（声明有·行为无 +
      行为有·声明无 双方向）；audit 串链（便签行/消费台账/capability span/
      回执 note_id 四处同单）；幂等键声明 → 重放 duplicated · 输出键 ⊆ 声明。
    """
    _hitl, sink = run_note_env
    run_id = f"{_PREFIX}-{uuid.uuid4().hex[:8]}"
    sid = f"{run_id}:1"
    req_id = f"{run_id}-req"
    state, row = _mk_state(run_id, sid, req_id)
    declared_output = set(_DECLARED_BASELINE["output_fields"])

    # ① 声明 hitl.required → 行为：无审批 fail-closed 挂起（adapter 零触达）
    out = await tool_exec_node({**state, "assigned_subtask": row})
    blocked = out["subtask_results"][-1]
    assert blocked.get("blocked_by") == _BLOCKED_BY_WRITE
    assert blocked.get("hitl_required") is True
    assert await _fetch_notes(req_id) == []

    # ② pending 落库：写意图快照 ↔ snapshot_fields 声明对账
    merged = {**state, "subtask_results": [blocked], "inflight_subtask_ids": []}
    obs = _observe(merged)
    assert obs["hitl_pending"] == [sid]
    created, unpersisted = await _persist_hitl(merged, obs, thread_id="t-rec1")
    assert unpersisted is False
    req = next(r for r in created if str(r.get("subtask_id")) == sid)
    intent = req["payload"]["write_intent"]
    assert intent["capability_id"] == _NEW_CAP
    assert intent["idempotency_key"] == "{{request_id}}"
    # snapshot_fields 声明 → 行为：写意图 args 摘要含 run_id + note（快照对账）
    summary = json.loads(intent["args_summary"])
    assert set(_DECLARED_BASELINE["hitl_snapshot_fields"]) <= set(summary.keys())
    assert summary["run_id"] == run_id and summary["note"] == "对账便签"

    # ③ 图真挂起 → decide(approved) → resume 单路径
    saver = InMemorySaver()
    suspended = None
    async for chunk in _observe_graph_factory(checkpointer=saver).astream(
        merged, {"configurable": {"thread_id": "t-rec1"}}, stream_mode="updates"
    ):
        for intr in chunk.get("__interrupt__") or []:
            suspended = intr.value
    assert suspended is not None and suspended["reason"] == "hitl_waiting"
    decided = await _hitl.adecide(req["id"], decision=STATUS_APPROVED, by="对账")
    assert decided["status"] == STATUS_APPROVED
    resumed = await resume_hitl_run(
        thread_id="t-rec1",
        approved=[sid],
        decided_by="对账",
        checkpointer=saver,
        graph_factory=_observe_graph_factory,
    )
    assert resumed["state"]["hitl_unlocked_ids"] == [sid]

    # ④ 重下发：消费命中 → Host 单次放行 + approval_id 注入 → 真落笔
    node_spans: list[dict] = []
    gw_spans: list[dict] = []
    monkeypatch.setattr(nodes, "_record_span_metadata", lambda md: node_spans.append(md))
    monkeypatch.setattr(
        "app.ops.capability.gateway.update_current_span_metadata",
        lambda md: gw_spans.append(md),
    )
    post = {**merged, "hitl_unlocked_ids": resumed["state"]["hitl_unlocked_ids"]}
    exec_out = await tool_exec_node({**post, "assigned_subtask": row})
    result = exec_out["subtask_results"][-1]
    assert "error" not in result, f"批准后重下发失败：{result.get('error')!r}"
    output = result["output"]

    # ⑤ 输出契约双向对账（成功路径）——对账实扫发现两枚登记偏差（A1 漂移实证 ·
    # 30 invoke 照登 · 建议另案对齐声明面，本 task 改码面禁动实现/基准）：
    #   偏差①（行为有·声明无）：adapter 成功路径出键 receipt（抓取载荷），
    #     未在 output_fields 声明；
    #   偏差②（声明有·行为无）：duplicate_of 为重放路径条件出键，成功路径不出。
    adapter_emitted = set(output.keys()) - {"receipt"}
    declared_success = declared_output - {"duplicate_of"}
    assert adapter_emitted == declared_success, (
        f"输出契约漂移：缺 {declared_success - adapter_emitted} · 多 {adapter_emitted - declared_success}"
    )
    assert output["written"] is True and output["duplicated"] is False
    assert "duplicate_of" not in output  # 偏差②：路径条件钉死
    # 偏差①的精确钉死：receipt 抓取载荷与输出面同单同值
    assert output["receipt"] == {
        "note_id": output["note_id"],
        "run_id": run_id,
        "tenant_id": TENANT_A,
    }

    # ⑥ audit 串链声明：便签行 approval_id == 审批单 id；消费台账/span/回执同单
    notes = await _fetch_notes(req_id)
    assert len(notes) == 1
    note = notes[0]
    assert note["approval_id"] == req["id"]
    assert note["tenant_id"] == TENANT_A
    assert note["idempotency_key"] == req_id
    assert str(note["id"]) == output["note_id"]
    consumed = [c for c in node_spans if c.get("capability_write_approval_consumed") is True]
    assert len(consumed) == 1 and consumed[0]["approval_id"] == req["id"]
    gw = [m for m in gw_spans if m.get("capability_id") == _NEW_CAP]
    assert gw and gw[-1]["approval_id"] == req["id"]
    receipts = sink.by_idempotency_key(req_id)
    assert len(receipts) == 1 and receipts[0].ok is True
    assert receipts[0].captured.get("note_id") == output["note_id"]

    # ⑦ 幂等键声明 → 行为：重放 duplicated · 输出键 ⊆ 声明（重放路径含
    # duplicate_of · 不含 note_id/approval_id——偏差②反向钉死）
    replay = await ainvoke(
        _NEW_CAP,
        {"run_id": run_id, "note": "对账便签", "request_id": req_id},
        ctx={"tenant_id": TENANT_A, "_host_policy": {"allow_write": True},
             "approval_id": req["id"]},
    )
    assert replay.ok and replay.output["duplicated"] is True
    replay_keys = set(replay.output.keys())
    assert replay_keys <= declared_output, f"重放路径输出越出声明面：{replay_keys - declared_output}"
    assert "duplicate_of" in replay_keys and "note_id" not in replay_keys
    assert len(await _fetch_notes(req_id)) == 1  # 不双写


@pytest.mark.parametrize(
    ("bad_args", "why"),
    [
        pytest.param(
            {"run_id": "r", "note": "x"}, "缺必填 request_id（幂等键源裸奔）", id="missing-request-id"
        ),
        pytest.param(
            {"run_id": "r", "note": "x", "request_id": "k", "extra": 1},
            "additionalProperties=false 被破",
            id="extra-property",
        ),
        pytest.param(
            {"run_id": 123, "note": "x", "request_id": "k"},
            "run_id 类型错（非 string）",
            id="wrong-type",
        ),
    ],
)
@_DB_MARK
async def test_e2e_args_schema_negatives(run_note_env, bad_args: dict, why: str):
    """args_schema 声明的行为层负样本（A1 口径①）：形态不合 → args_schema_invalid
    fail-closed · 零落笔——放行面（Host 单次写放行 + 租户谓词）俱在也照样拦。"""
    _store, _sink = run_note_env
    req_id = f"{_PREFIX}-{uuid.uuid4().hex[:8]}-req"
    if "request_id" in bad_args:
        bad_args["request_id"] = req_id
    res = await ainvoke(
        _NEW_CAP,
        bad_args,
        ctx={"tenant_id": TENANT_A, "_host_policy": {"allow_write": True}},
    )
    assert res.ok is False
    assert "args_schema_invalid" in (res.error or ""), f"负样本放行：{why}"
    assert res.meta.get("args_schema_invalid") is True
    assert await _fetch_notes(req_id) == []  # fail-closed 零落笔


@_DB_MARK
async def test_e2e_no_approval_zero_write(run_note_env):
    """声明 hitl.required → 行为反向钉死：审批未命中即执行 = 零落笔（FP-2
    fail-closed 不放宽的端到端形态；与 stage-w a2 同语义 · 对账面常驻扎钉）。"""
    _store, _sink = run_note_env
    run_id = f"{_PREFIX}-{uuid.uuid4().hex[:8]}"
    req_id = f"{run_id}-req"
    state, row = _mk_state(run_id, f"{run_id}:1", req_id)
    out = await tool_exec_node({**state, "assigned_subtask": row})
    blocked = out["subtask_results"][-1]
    assert blocked.get("blocked_by") == _BLOCKED_BY_WRITE
    assert await _fetch_notes(req_id) == []
