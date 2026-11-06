"""fix-planner-args-schema · hat 30（案②修复资产 · issue #339）。

缺陷（issue #339 · 10 档诊断五环锚定）：live 八段真落笔 supervisor planner 产出
string-args（入参 JSON 序列化成字符串写进 input · 无 args 对象）→ gateway
``validate_capability_args`` fail-closed 拒执行（``args_schema_invalid`` · 两轮
一致）→ 阻断全部写能力 40 真落笔验证。

修复语义（HG-PLANNER-ARGS-DESIGN 签认 = 案②修复资产 · 根因环①③一并消除）：
1. 两份 supervisor prompt 资产（system / suffix.system）文档化 ``args``
   结构化对象（type=tool 时 args 为 JSON 对象 · 按目录块 args_schema 填键名/类型）；
2. ``_format_capability_catalog`` 目录块注入各能力 ``args_schema``（信息缺口环③）；
3. gateway fail-closed / ``_parse_subtasks`` 解析面 / SSE 面**零改动**
   （案①拒收语义由 gateway fail-closed 既有承载 · 红线永不放宽）。

负样本（维护者红线 · issue #339 comment `6674979717` 六条件之① ·
经**真规划→派发→执行路径**驱动 · 禁直造 state 直调）：

- **红**：修复前提示词未文档化 args、目录块无 args_schema——遵循提示词的模型
  只认 input 字面 → 产 string-args（issue #339 live 两轮一致形态）→ 真链
  （supervisor_node → _join_subtasks → tool_exec_node → gateway →
  ops_capability_notes）派发执行 → ``args_schema_invalid`` 拦截 · 零落笔；
- **绿**：修复后提示词文档化 args + 目录块注入 args_schema → 同链产对象 args →
  schema 校验通过 · 真落笔执行断言达成（便签行/回执/审批串链）。

planner mock 按「提示词遵循」语义对 system prompt 反应：目录块含
``args_schema=``（修复后形态）→ 产对象 args；否则复现 live 观测 string-args
形态——红→绿由同一端到端测试承载，肉眼可见。

红线对拍（本文件自身约束）：gateway ``args_schema`` fail-closed 永不放宽——
fail-closed 承接组（string-args 强灌 · 与提示词无关）修复前后永绿；
legacy 只读 input 串形态零漂移（常规对拍组）。
"""

from __future__ import annotations

import json
import uuid
from types import SimpleNamespace
from unittest.mock import patch

import pytest
from langchain_core.messages import HumanMessage

from app.db.session import AsyncSessionLocal
from app.ops.capability import delegation as dl
from app.ops.capability.baseline import ENV_ALLOW_WRITE_TAGS, baseline_filter
from app.ops.capability.defaults import ensure_default_capabilities
from app.ops.capability.gateway import get_registry
from app.ops.capability.idempotency import (
    InMemoryIdempotencyStore,
    reset_idempotency_store,
    set_idempotency_store,
)
from app.ops.capability.manifest import MANIFEST_DIR, load_capability_manifest
from app.ops.capability.receipts import (
    InMemoryReceiptSink,
    reset_receipt_sink,
    set_receipt_sink,
)
from app.ops.hitl import reset_hitl_store, set_hitl_store
from app.ops.hitl.store import STATUS_APPROVED, InMemoryHitlStore
from app.ops.lg_rag.multi.nodes import (
    _format_capability_catalog,
    _join_subtasks,
    _observe,
    _persist_hitl,
    supervisor_node,
    tool_exec_node,
)
from app.ops.tenant_context import TENANT_A
from tests.conftest import DB_AVAILABLE

_NEW_MANIFEST = MANIFEST_DIR / "ops.write.v1.yaml"
_NEW_CAP = "ops.write.run_note"
_BLOCKED_BY_WRITE = "capability_write_hitl_required"

_DB_MARK = pytest.mark.skipif(not DB_AVAILABLE, reason="需要 PostgreSQL（opsdesk_test）")

# 测试数据统一前缀：清理与断言都按它过滤，绝不触碰其他行
_PREFIX = "pargs"


# ---------------------------------------------------------------------------
# 环境夹具（承 test_stage_w_write_expand run_note_env 三层显式打开范式）
# ---------------------------------------------------------------------------


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
    """写能力三层显式打开：manifest 显式加载 + 独立写 tag 放行 + 内存幂等/回执。

    **不设** ``OPS_CAPABILITY_ALLOW_WRITE``——Host 单次写放行由审批命中后注入
    （两道闸语义 · 编排层审批闸不被 env 豁免）。
    """
    monkeypatch.setenv(dl.ENV_MODE, "off")
    monkeypatch.delenv("OPS_CAPABILITY_ALLOW_WRITE", raising=False)
    monkeypatch.setenv(ENV_ALLOW_WRITE_TAGS, "run_note")
    # 钉死契约（baseline.py docstring）：`_SUPERVISOR_CAP_FILTER` 模块级常量 import
    # 时固化——env 后设须显式重建 filter（禁止依赖 import 顺序巧合）。
    monkeypatch.setattr(
        "app.ops.lg_rag.multi.nodes._SUPERVISOR_CAP_FILTER",
        baseline_filter(node_role="supervisor"),
    )
    load_capability_manifest(_NEW_MANIFEST)
    hitl_store = InMemoryHitlStore()
    set_hitl_store(hitl_store)  # 先落 store：_persist_hitl 建单面写同一份
    idem_store = InMemoryIdempotencyStore()
    set_idempotency_store(idem_store)
    sink = InMemoryReceiptSink()
    set_receipt_sink(sink)
    yield hitl_store, sink


# ---------------------------------------------------------------------------
# DB 小工具（真 PostgreSQL · opsdesk_test · 承 stage-w 先例）
# ---------------------------------------------------------------------------


async def _clear_notes() -> None:
    from sqlalchemy import text

    async with AsyncSessionLocal() as session, session.begin():
        await session.execute(
            text("DELETE FROM ops_capability_notes WHERE idempotency_key LIKE :p"),
            {"p": f"{_PREFIX}-%"},
        )


async def _fetch_notes(idem_key: str) -> list[dict]:
    from sqlalchemy import text

    async with AsyncSessionLocal() as session:
        rows = await session.execute(
            text(
                "SELECT id, tenant_id, capability_id, run_id, subtask_id, approval_id,"
                " note, created_by, idempotency_key FROM ops_capability_notes"
                " WHERE idempotency_key = :k"
            ),
            {"k": idem_key},
        )
        cols = (
            "id", "tenant_id", "capability_id", "run_id", "subtask_id", "approval_id",
            "note", "created_by", "idempotency_key",
        )
        return [dict(zip(cols, r, strict=True)) for r in rows.all()]


# ---------------------------------------------------------------------------
# 遵循提示词的 planner mock（红→绿载体 · 禁直造 subtasks 直调）
# ---------------------------------------------------------------------------

_NOTE_TEXT = "planner-args 修复验收便签"


def _planner_following_prompt(run_id: str, req_id: str, *, force_string_args: bool = False):
    """按「提示词遵循」语义产 plan 的 mock provider。

    - 目录块含 ``args_schema=``（修复后形态）→ 产**对象 args**（compliant 模型）；
    - 否则复现 issue #339 live 两轮一致形态：入参 JSON 序列化成字符串写进 input；
    - ``force_string_args=True``（fail-closed 承接组）：无视提示词恒产 string-args。
    """

    async def _complete(messages, *, model):
        system = str(messages[0].content)
        structured = (not force_string_args) and "args_schema=" in system
        if structured:
            step = {
                "id": "t1",
                "type": "tool",
                "tool": _NEW_CAP,
                "input": f"给 run {run_id} 写一条备注（幂等键 {req_id}）",
                "args": {"run_id": run_id, "note": _NOTE_TEXT, "request_id": req_id},
            }
        else:
            step = {
                "id": "t1",
                "type": "tool",
                "tool": _NEW_CAP,
                "input": json.dumps(
                    {"run_id": run_id, "note": _NOTE_TEXT, "request_id": req_id},
                    ensure_ascii=False,
                ),
            }
        return json.dumps({"subtasks": [step]}, ensure_ascii=False)

    return SimpleNamespace(complete=_complete)


def _span_cm():
    from unittest.mock import MagicMock

    cm = MagicMock()
    cm.__enter__ = MagicMock(return_value=None)
    cm.__exit__ = MagicMock(return_value=False)
    return cm


# ---------------------------------------------------------------------------
# 真链驱动：规划 → 派发 → 审批 → 重下发执行（承 test_stage_w A1 链范式）
# ---------------------------------------------------------------------------


async def _approve_write_step(run_note_env, merged: dict, sid: str) -> dict:
    """写闸拦 → 真建单 → decide(approved)；返回带审批的 state 与单据 id。"""
    store, _sink = run_note_env
    obs = _observe(merged)
    assert obs["hitl_pending"] == [sid]
    created, unpersisted = await _persist_hitl(merged, obs, thread_id=f"t-{_PREFIX}")
    assert unpersisted is False
    req = next(r for r in created if str(r.get("subtask_id")) == sid)
    assert req["blocked_by"] == _BLOCKED_BY_WRITE
    decided = await store.adecide(req["id"], decision=STATUS_APPROVED, by="验收")
    assert decided["status"] == STATUS_APPROVED
    return req


# ---------------------------------------------------------------------------
# 验收① · 负样本（红→绿 · 真规划→派发→执行路径）
# ---------------------------------------------------------------------------


@_DB_MARK
async def test_planner_args_schema_red_to_green_end_to_end(run_note_env):
    """负样本（维护者红线）：planner 输出 args 通过 schema 校验（端到端）。

    真链：supervisor_node（mock planner 遵循提示词）→ _join_subtasks 派发 →
    tool_exec 写闸拦 → _persist_hitl 真建单 → decide(approved) → 重下发
    tool_exec → gateway args_schema 校验 → 真落笔。

    - **修复前（红）**：提示词未文档化 args + 目录无 args_schema → mock 产
      string-args → ``args_schema_invalid`` fail-closed 拦截 · 便签表零落笔 ·
      本测试绿断言（真落笔）失败 = 红可见；
    - **修复后（绿）**：同链产对象 args → schema 校验通过 · 便签行落值
      （tenant/approval/subtask/幂等键四串链）· 回执 write_confirmed。
    """
    _store, sink = run_note_env
    run_id = f"{_PREFIX}-{uuid.uuid4().hex[:8]}"
    req_id = f"{run_id}-req"

    # ① 真规划（system prompt 走真实装配：catalog = 真注册表 + 真目录块渲染）
    provider = _planner_following_prompt(run_id, req_id)
    with (
        patch("app.ops.lg_rag.multi.nodes.get_llm_provider", return_value=provider),
        patch("app.ops.lg_rag.multi.nodes._record_span_metadata"),
        patch("app.ops.lg_rag.multi.nodes.trace_span", return_value=_span_cm()),
    ):
        planned = await supervisor_node(
            {
                "messages": [HumanMessage(content="给这次 run 留一条备注")],
                "run_id": run_id,
                "user_id": f"u-{_PREFIX}",
                "allowed_capability_ids": [_NEW_CAP],
            }
        )
    rows = planned.get("subtasks") or []
    assert len(rows) == 1
    sid = str(rows[0]["subtask_id"])
    assert rows[0]["tool"] == _NEW_CAP

    # ② 真派发
    merged = {
        "messages": [HumanMessage(content="给这次 run 留一条备注")],
        "run_id": run_id,
        "user_id": f"u-{_PREFIX}",
        "allowed_capability_ids": [_NEW_CAP],
        "subtasks": rows,
        "subtask_results": [],
        "inflight_subtask_ids": [],
        "host_subtask_seq": 1,
    }
    joined = await _join_subtasks(merged)
    assert sid in (joined.get("inflight_subtask_ids") or [])
    row = next(r for r in rows if str(r.get("subtask_id")) == sid)

    # ③ 无审批 → fail-closed 挂起（编排层闸 · adapter 零触达 · 零落笔）
    blocked_out = await tool_exec_node({**merged, "assigned_subtask": row})
    blocked = blocked_out["subtask_results"][-1]
    assert blocked.get("blocked_by") == _BLOCKED_BY_WRITE
    assert blocked.get("hitl_required") is True
    intent = blocked.get("write_intent") or {}
    assert intent.get("capability_id") == _NEW_CAP

    # ④ 真建单 + decide(approved)
    merged = {**merged, "subtask_results": [blocked], "inflight_subtask_ids": []}
    req = await _approve_write_step(run_note_env, merged, sid)

    # ⑤ 重下发：审批命中 → Host 单次写放行 → gateway args_schema 校验 → 真落笔
    exec_out = await tool_exec_node({**merged, "assigned_subtask": row})
    result = exec_out["subtask_results"][-1]
    assert result.get("subtask_id") == sid
    # 绿断言（修复前此处红：args_schema_invalid 拦截 · error 非空 · 零落笔）
    assert "error" not in result, (
        f"负样本未转绿：planner args 未通过 schema 校验（error={result.get('error')!r}）"
    )
    assert result["output"]["written"] is True
    assert result["output"]["tool"] == "ops_write_run_note"  # adapter 回执 tool 键（承 stage-w A1）

    # 真落笔断言：便签行落值（tenant / approval / subtask / 幂等键四串链）
    notes = await _fetch_notes(req_id)
    assert len(notes) == 1
    note = notes[0]
    assert note["tenant_id"] == TENANT_A
    assert note["capability_id"] == _NEW_CAP
    assert note["run_id"] == run_id
    assert note["subtask_id"] == sid
    assert note["approval_id"] == req["id"]
    assert note["idempotency_key"] == req_id
    assert note["note"] == _NOTE_TEXT

    # 回执：write_confirmed 串同一幂等键
    receipts = sink.by_idempotency_key(req_id)
    assert len(receipts) == 1
    assert receipts[0].ok is True
    assert receipts[0].write_confirmed is True


# ---------------------------------------------------------------------------
# 红线对拍 · FP-6 承接组：fail-closed 永不放宽（string-args 强灌 · 永绿）
# ---------------------------------------------------------------------------


@_DB_MARK
async def test_fail_closed_string_args_never_passes(run_note_env):
    """红线：string-args 强灌（与提示词无关）→ args_schema_invalid 拦截 · 零落笔。

    修复前后本组必须**恒绿**——gateway fail-closed 是抓出本缺陷的安全属性，
    「让 string-args 能执行」是伪修复（FP-6）；案①拒收语义由其既有承载。
    """
    _store, _sink = run_note_env
    run_id = f"{_PREFIX}-{uuid.uuid4().hex[:8]}"
    req_id = f"{run_id}-req"

    provider = _planner_following_prompt(run_id, req_id, force_string_args=True)
    with (
        patch("app.ops.lg_rag.multi.nodes.get_llm_provider", return_value=provider),
        patch("app.ops.lg_rag.multi.nodes._record_span_metadata"),
        patch("app.ops.lg_rag.multi.nodes.trace_span", return_value=_span_cm()),
    ):
        planned = await supervisor_node(
            {
                "messages": [HumanMessage(content="给这次 run 留一条备注")],
                "run_id": run_id,
                "user_id": f"u-{_PREFIX}",
                "allowed_capability_ids": [_NEW_CAP],
            }
        )
    rows = planned.get("subtasks") or []
    assert len(rows) == 1
    sid = str(rows[0]["subtask_id"])
    assert "args" not in rows[0], "强灌组 planner 必须产 string-args 形态（无 args 键）"

    merged = {
        "messages": [HumanMessage(content="给这次 run 留一条备注")],
        "run_id": run_id,
        "user_id": f"u-{_PREFIX}",
        "allowed_capability_ids": [_NEW_CAP],
        "subtasks": rows,
        "subtask_results": [],
        "inflight_subtask_ids": [],
        "host_subtask_seq": 1,
    }
    joined = await _join_subtasks(merged)
    assert sid in (joined.get("inflight_subtask_ids") or [])
    row = next(r for r in rows if str(r.get("subtask_id")) == sid)

    blocked_out = await tool_exec_node({**merged, "assigned_subtask": row})
    blocked = blocked_out["subtask_results"][-1]
    assert blocked.get("blocked_by") == _BLOCKED_BY_WRITE

    merged = {**merged, "subtask_results": [blocked], "inflight_subtask_ids": []}
    await _approve_write_step(run_note_env, merged, sid)

    exec_out = await tool_exec_node({**merged, "assigned_subtask": row})
    result = exec_out["subtask_results"][-1]
    # fail-closed 承接：schema 校验拒 string（期望 type=object 实际=str 形态）
    assert "args_schema_invalid" in str(result.get("error") or ""), (
        f"gateway fail-closed 被放宽：string-args 未被拦（result={result!r}）"
    )
    assert await _fetch_notes(req_id) == [], "拦截形态不得落笔"


# ---------------------------------------------------------------------------
# 常规对拍 · legacy 只读 input 串形态零漂移
# ---------------------------------------------------------------------------


async def test_legacy_input_only_read_tool_zero_drift():
    """常规对拍：只读能力 legacy input 串形态（无 args 键）与修复前零漂移。

    真链：supervisor_node（plan 只含 input 字面）→ tool_exec_node 真执行——
    ``utc_now_iso`` args_schema 为 ``[string, object, null]`` 兼容串形 · 直跑成功。
    """
    plan = json.dumps(
        {"subtasks": [{"id": "t1", "type": "tool", "tool": "utc_now_iso", "input": "当前 UTC"}]},
        ensure_ascii=False,
    )
    async def _complete(messages, *, model):
        return plan

    provider = SimpleNamespace(complete=_complete)
    with (
        patch("app.ops.lg_rag.multi.nodes.get_llm_provider", return_value=provider),
        patch("app.ops.lg_rag.multi.nodes._record_span_metadata"),
        patch("app.ops.lg_rag.multi.nodes.trace_span", return_value=_span_cm()),
    ):
        planned = await supervisor_node(
            {
                "messages": [HumanMessage(content="现在几点（UTC）")],
                "run_id": f"{_PREFIX}-{uuid.uuid4().hex[:8]}",
                "user_id": f"u-{_PREFIX}",
                "allowed_capability_ids": ["utc_now_iso"],
            }
        )
    rows = planned.get("subtasks") or []
    assert len(rows) == 1
    assert "args" not in rows[0], "legacy 形态不得被强补 args 键"
    out = await tool_exec_node(
        {
            "messages": [],
            "run_id": f"{_PREFIX}-{uuid.uuid4().hex[:8]}",
            "subtasks": rows,
            "subtask_results": [],
            "inflight_subtask_ids": [],
            "assigned_subtask": rows[0],
        }
    )
    result = out["subtask_results"][-1]
    assert "error" not in result, f"legacy 只读串形态漂移：{result.get('error')!r}"
    assert "utc" in result["output"]


# ---------------------------------------------------------------------------
# 目录块 args_schema 注入（单元面 · 信息缺口环③）
# ---------------------------------------------------------------------------


def test_catalog_injects_args_schema_when_declared():
    """声明 args_schema → 行尾（括号内）注入 JSON Schema；planner 按 schema 填 args。"""
    spec = SimpleNamespace(
        capability_id="ops.write.run_note",
        description="写 run 备注",
        risk_level="medium",
        output_fields=(),
        args_schema={
            "type": "object",
            "properties": {"run_id": {"type": "string"}, "note": {"type": "string"}},
            "required": ["run_id", "note"],
            "additionalProperties": False,
        },
    )
    line = _format_capability_catalog([spec])
    assert 'args_schema={"type": "object"' in line
    assert '"run_id"' in line and '"note"' in line
    assert line.startswith("- ops.write.run_note：写 run 备注（risk=medium；args_schema=")


def test_catalog_args_schema_after_output_fields():
    """output_fields 与 args_schema 同声明时顺序钉死：risk → output_fields → args_schema。"""
    spec = SimpleNamespace(
        capability_id="mock_get_issue_status",
        description="查状态",
        risk_level="low",
        output_fields=("status", "assignee"),
        args_schema={"type": ["string", "object"], "properties": {}, "additionalProperties": True},
    )
    assert _format_capability_catalog([spec]) == (
        "- mock_get_issue_status：查状态（risk=low；output_fields=[status, assignee]；"
        'args_schema={"type": ["string", "object"], "properties": {}, '
        '"additionalProperties": true}）'
    )


def test_catalog_legacy_fake_caps_row_byte_identical():
    """旧测 SimpleNamespace 伪造 spec（无 args_schema 属性）行渲染零 diff。

    承 output_fields 先例 getattr 宽容口径——缺属性视同未声明。
    """
    fake = SimpleNamespace(capability_id="x", description="d", risk_level="low")
    assert _format_capability_catalog([fake]) == "- x：d（risk=low）"


# ---------------------------------------------------------------------------
# 提示词资产面：args 文档化 + 目录块 args_schema 真注入（真装配 · 真注册表）
# ---------------------------------------------------------------------------


async def test_supervisor_prompt_documents_args_and_injects_schema(run_note_env):
    """修复资产落地断言：system prompt 同时满足——

    1. 目录块真注入 ``ops.write.run_note`` 的 args_schema（``run_id``/``note``/
       ``request_id`` 字段名对模型可见 · 信息缺口环③消除）；
    2. 提示词文档化 args 结构化对象（type=tool 产 JSON 对象而非塞 input 串）。
    """
    captured: list[str] = []

    async def _capture(messages, *, model):
        captured.append(str(messages[0].content))
        return json.dumps(
            {"subtasks": [{"id": "t1", "type": "rag", "input": "占位"}]},
            ensure_ascii=False,
        )

    provider = SimpleNamespace(complete=_capture)
    with (
        patch("app.ops.lg_rag.multi.nodes.get_llm_provider", return_value=provider),
        patch("app.ops.lg_rag.multi.nodes._record_span_metadata"),
        patch("app.ops.lg_rag.multi.nodes.trace_span", return_value=_span_cm()),
    ):
        await supervisor_node(
            {
                "messages": [HumanMessage(content="复合问题")],
                "run_id": f"{_PREFIX}-{uuid.uuid4().hex[:8]}",
                "user_id": f"u-{_PREFIX}",
                "allowed_capability_ids": [_NEW_CAP],
            }
        )
    assert captured, "mock 未收到 system prompt"
    system = captured[0]
    # 环③：目录块注入 args_schema（修复前目录只有 id·description·risk → 红）
    assert "args_schema=" in system, "目录块未注入 args_schema（信息缺口环③未消除）"
    assert '"run_id"' in system and '"request_id"' in system
    # 环①：提示词文档化 args 结构化对象（修复前资产未提 args → 红）
    assert "args" in system
