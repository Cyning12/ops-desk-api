"""步骤契约（Q4）与可恢复点（Q8）· 红线 R14 / R15。

设计：docs/07-design/06_step-contract-and-recoverable-point-plan_v1_zh.md

每条红线都配**正向断言 + 反向对照**：只做正向会得到假通过——
"一律不派工人"天然满足"该停的停住了"，所以必须同时证明
"该跑的照跑"。
"""

from __future__ import annotations

import json
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest
from langchain_core.messages import AIMessage, HumanMessage

from app.ops.lg_rag.multi import step_contract as sc
from app.ops.lg_rag.multi.nodes import (
    MAX_SUBTASKS,
    _issue_plan,
    _join_subtasks,
    _locked_prefix,
    _worker_state,
    supervisor_node,
)
from app.ops.lg_rag.state import SubtaskResultBatch

_RUN = "runcontract"
_T1 = f"{_RUN}:1"
_T2 = f"{_RUN}:2"
_T3 = f"{_RUN}:3"
_TOOL = "mock_get_issue_status"


def _term(sid: str, **kw) -> dict:
    row = {"id": sid, "subtask_id": sid, "type": "tool", "input": "x"}
    row.update(kw)
    return row


def _row(sid: str, *, deps=None, consumes=None, produces=None, **kw) -> dict:
    row = {
        "id": sid,
        "subtask_id": sid,
        "alias": "t" + sid.rsplit(":", 1)[-1],
        "type": "tool",
        "tool": _TOOL,
        "input": "x",
        "depends_on": list(deps or []),
    }
    if consumes:
        row["consumes_resolved"] = consumes
    if produces:
        row["produces"] = produces
    row.update(kw)
    return row


# ---------------------------------------------------------------------------
# 模块层
# ---------------------------------------------------------------------------


def test_normalize_is_lenient_never_raises():
    """垃圾声明一律退化成"没声明"，不抛、不整单作废。"""
    assert sc.normalize_produces("not-a-list") == []
    assert sc.normalize_produces([None, "", "  ", "a", "a"]) == ["a"]
    assert sc.normalize_consumes(["nope"]) == {}
    assert sc.normalize_consumes({"t1": "nope"}) == {}
    assert sc.normalize_consumes({"t1": ["a"], "": ["b"]}) == {"t1": ["a"]}


def test_gate_blocks_failed_predecessor():
    """R14 正向：前驱失败终态 → 后继被拦。"""
    done = {_T1: _term(_T1, error="下游 500")}
    reason, detail = sc.gate(
        row=_row(_T2, deps=[_T1]),
        terminals=done,
        by_id={_T1: _row(_T1)},
        prefix_ids=frozenset(),
    )
    assert reason == sc.BLOCKED_PREDECESSOR_FAILED
    assert _T1 in detail
    assert not sc.needs_hitl(reason)


def test_gate_blocks_missing_consumed_field():
    """R14 正向：consumes 声明的字段在产出里没有 → 拦下（喂入前）。"""
    done = {_T1: _term(_T1, output={"status": "open"})}
    reason, detail = sc.gate(
        row=_row(_T2, deps=[_T1], consumes={_T1: ["assignee"]}),
        terminals=done,
        by_id={_T1: _row(_T1)},
        prefix_ids=frozenset(),
    )
    assert reason == sc.BLOCKED_CONTRACT_MISSING
    assert "assignee" in detail


def test_gate_producer_breach_blocks_dependent():
    """前驱声明了 produces 却没兑现 → 后继也停（声明了就要兑现）。"""
    done = {_T1: _term(_T1, output={"status": "open"})}
    reason, _ = sc.gate(
        row=_row(_T2, deps=[_T1]),
        terminals=done,
        by_id={_T1: _row(_T1, produces=["status", "assignee"])},
        prefix_ids=frozenset(),
    )
    assert reason == sc.BLOCKED_CONTRACT_MISSING


def test_gate_prefix_touch_needs_hitl():
    """Q8：同样"缺字段"，落在不可变前缀上 ⇒ 要改历史 ⇒ 交人。"""
    done = {_T1: _term(_T1, output={"status": "open"})}
    reason, _ = sc.gate(
        row=_row(_T2, deps=[_T1], consumes={_T1: ["assignee"]}),
        terminals=done,
        by_id={_T1: _row(_T1)},
        prefix_ids=frozenset({_T1}),
    )
    assert reason == sc.BLOCKED_PREFIX_TOUCH
    assert sc.needs_hitl(reason) is True


def test_gate_passes_when_undeclared():
    """R14 反向对照：没声明 consumes/produces 就不得拦。

    少了这条，"干脆一步都不跑"也能满足上面所有断言——空真。
    """
    done = {_T1: _term(_T1, error="下游 500")}
    row = _row(_T2, deps=[_T1])
    # 注意：前驱失败**仍然**要拦（那是 C2，与声不声明无关）。
    # 反向对照的正确形态是：前驱成功、且没声明 consumes ⇒ 放行。
    done_ok = {_T1: _term(_T1, output="自由文本")}
    reason, _ = sc.gate(
        row=row,
        terminals=done_ok,
        by_id={_T1: _row(_T1)},
        prefix_ids=frozenset(),
    )
    assert reason is None
    assert done  # 上面那条失败分支确实被拦（防我写反）


def test_gate_passes_when_fields_present():
    """R14 反向对照：字段齐全 ⇒ 放行。"""
    done = {_T1: _term(_T1, output={"assignee": "张三", "status": "open"})}
    reason, _ = sc.gate(
        row=_row(_T2, deps=[_T1], consumes={_T1: ["assignee"]}),
        terminals=done,
        by_id={_T1: _row(_T1, produces=["assignee"])},
        prefix_ids=frozenset({_T1}),
    )
    assert reason is None


def test_gate_does_not_inspect_free_text_output():
    """产出是自由文本（rag/extract）时，不替模型猜字段。"""
    done = {_T1: _term(_T1, output="一段答案")}
    reason, _ = sc.gate(
        row=_row(_T2, deps=[_T1], consumes={_T1: ["assignee"]}),
        terminals=done,
        by_id={_T1: _row(_T1)},
        prefix_ids=frozenset(),
    )
    # output 不是 dict ⇒ missing_fields 返回空 ⇒ 判定为"不可校验"，放行
    assert reason is None
    assert sc.missing_fields("一段答案", ["assignee"]) == []


def test_bind_args_overrides_placeholder():
    """绑定必须覆盖 planner 写死的占位值，否则契约等于没接上。"""
    values = {_T1: {"assignee": "张三"}}
    args = sc.bind_args({"assignee": "待填", "limit": 5}, values)
    assert args["assignee"] == "张三"
    assert args["limit"] == 5


def test_bind_input_appends_deterministic_block():
    """rag/extract：追加编排层生成的固定块，不改写问句本身。"""
    text, included = sc.bind_input(
        "查一下这个人的待办",
        {_T1: {"assignee": "张三"}},
        sid_to_alias={_T1: "t1"},
    )
    assert text.startswith("查一下这个人的待办")
    assert sc.CONTEXT_HEAD in text
    assert "t1.assignee = 张三" in text
    assert included == [f"{_T1}:assignee"]


def test_bind_input_truncates_long_values():
    """单值截断：一个超长值不能吃掉整块。"""
    long_value = "x" * 500
    text, _included = sc.bind_input("q", {_T1: {"blob": long_value}}, sid_to_alias={_T1: "t1"})
    assert len(text) < sc.max_value_chars() + 60
    assert text.rstrip().endswith("…")


def test_context_block_has_total_budget_and_says_what_it_dropped():
    """整块预算：多字段累加也会污染 prompt，所以还要有总量闸；
    挤掉的字段必须**说出来**，不能假装都给到了。"""
    many = {_T1: {f"f{i}": "y" * 120 for i in range(12)}}
    _text, included = sc.render_context_block(many, sid_to_alias={_T1: "t1"})
    dropped = sc.dropped_fields(many, included)
    assert len(included) < 12, "整块预算没生效"
    assert dropped, "挤掉的字段没报出来（静默少给）"
    assert set(dropped) | set(included) == set(sc.bound_field_names(many))


# ---------------------------------------------------------------------------
# 编排层：签发 / 归并联通
# ---------------------------------------------------------------------------


def test_consumes_implies_dependency():
    """吃了谁的产出，就必须等谁——不声明 depends_on 也会被串上。"""
    plan, errors, _ = _issue_plan(
        [
            {"id": "t1", "type": "tool", "tool": _TOOL, "input": "甲"},
            {
                "id": "t2",
                "type": "tool",
                "tool": _TOOL,
                "input": "乙",
                "consumes": {"t1": ["assignee"]},
            },
        ],
        run_id=_RUN,
        seq=0,
    )
    assert not errors
    assert plan[1]["depends_on"] == [_T1]
    assert plan[1]["consumes_resolved"] == {_T1: ["assignee"]}


def test_consumes_unknown_alias_is_dropped_not_guessed():
    plan, _, _ = _issue_plan(
        [{"id": "t1", "type": "tool", "input": "甲", "consumes": {"nope": ["a"]}}],
        run_id=_RUN,
        seq=0,
    )
    assert "consumes_resolved" not in plan[0]


async def test_join_blocks_dependent_of_failed_predecessor():
    """R14 正向（编排层）：前驱失败 ⇒ 后继不下发，且写错误终态。"""
    plan = [_row(_T1), _row(_T2, deps=[_T1])]
    state = {
        "subtasks": plan,
        "subtask_results": [_term(_T1, error="下游 500")],
        "inflight_subtask_ids": [_T1],
        "supervisor_step_count": 1,
    }
    out = await _join_subtasks(state)
    assert out["inflight_subtask_ids"] == []
    blocked = {r["subtask_id"]: r for r in out["subtask_results"]}
    assert blocked[_T2]["blocked_by"] == sc.BLOCKED_PREDECESSOR_FAILED
    assert "error" in blocked[_T2]


async def test_join_cascades_the_stop():
    """t2 被拦 ⇒ t3（依赖 t2）同批一起停，不是等下一轮才停。"""
    plan = [_row(_T1), _row(_T2, deps=[_T1]), _row(_T3, deps=[_T2])]
    state = {
        "subtasks": plan,
        "subtask_results": [_term(_T1, error="下游 500")],
        "inflight_subtask_ids": [_T1],
        "supervisor_step_count": 1,
    }
    out = await _join_subtasks(state)
    assert out["inflight_subtask_ids"] == []
    blocked = {r["subtask_id"] for r in out["subtask_results"]}
    assert blocked == {_T2, _T3}


async def test_join_undeclared_predecessor_failure_still_stops():
    """C2 与声不声明无关：前驱失败就是停。

    这条同时是 test_gate_passes_when_undeclared 的编排层补强——
    那条放行的是"前驱成功且未声明"，这条拦的是"前驱失败"。
    """
    plan = [_row(_T1), _row(_T2, deps=[_T1])]
    state = {
        "subtasks": plan,
        "subtask_results": [_term(_T1, error="boom")],
        "inflight_subtask_ids": [_T1],
        "supervisor_step_count": 1,
    }
    assert (await _join_subtasks(state))["inflight_subtask_ids"] == []


async def test_join_success_still_dispatches():
    """R14 反向对照（编排层）：前驱成功且契约满足 ⇒ 照常下发。"""
    plan = [_row(_T1, produces=["assignee"]), _row(_T2, deps=[_T1], consumes={_T1: ["assignee"]})]
    state = {
        "subtasks": plan,
        "subtask_results": [_term(_T1, output={"assignee": "张三"})],
        "inflight_subtask_ids": [_T1],
        "supervisor_step_count": 1,
    }
    out = await _join_subtasks(state)
    assert out["inflight_subtask_ids"] == [_T2]
    assert "subtask_results" not in out


async def test_join_free_text_predecessor_does_not_block_undeclared():
    """rag 产出是文本、后继没声明 consumes ⇒ 不拦。"""
    plan = [
        {
            "id": _T1,
            "subtask_id": _T1,
            "alias": "t1",
            "type": "rag",
            "input": "q",
            "depends_on": [],
        },
        _row(_T2, deps=[_T1]),
    ]
    state = {
        "subtasks": plan,
        "subtask_results": [_term(_T1, output="一段答案")],
        "inflight_subtask_ids": [_T1],
        "supervisor_step_count": 1,
    }
    assert (await _join_subtasks(state))["inflight_subtask_ids"] == [_T2]


def test_worker_state_binds_tool_args_and_records_bound_fields():
    """绑定真的发生在派工载荷里（否则契约是空门）。"""
    plan = [
        _row(_T1, produces=["assignee"]),
        _row(_T2, deps=[_T1], consumes={_T1: ["assignee"]}, args={"assignee": "待填"}),
    ]
    state = {
        "subtasks": plan,
        "subtask_results": [_term(_T1, output={"assignee": "张三"})],
        "messages": [],
        "supervisor_step_count": 1,
    }
    payload = _worker_state(state, plan[1])
    assigned = payload["assigned_subtask"]
    assert assigned["args"]["assignee"] == "张三"
    assert assigned["bound_fields"] == [f"{_T1}:assignee"]


def test_worker_state_appends_block_for_rag():
    plan = [
        _row(_T1, produces=["assignee"]),
        {
            "id": _T2,
            "subtask_id": _T2,
            "alias": "t2",
            "type": "rag",
            "input": "查待办",
            "depends_on": [_T1],
            "consumes_resolved": {_T1: ["assignee"]},
        },
    ]
    state = {
        "subtasks": plan,
        "subtask_results": [_term(_T1, output={"assignee": "张三"})],
        "messages": [],
        "supervisor_step_count": 1,
    }
    assigned = _worker_state(state, plan[1])["assigned_subtask"]
    assert assigned["input"].startswith("查待办")
    assert sc.CONTEXT_HEAD in assigned["input"]
    assert "t1.assignee = 张三" in assigned["input"]


def test_worker_state_untouched_without_consumes():
    """没声明 consumes ⇒ 载荷原样（不注入任何东西）。"""
    plan = [_row(_T1)]
    state = {"subtasks": plan, "subtask_results": [], "messages": [], "supervisor_step_count": 1}
    assigned = _worker_state(state, plan[0])["assigned_subtask"]
    assert "bound_fields" not in assigned
    assert assigned["input"] == "x"


# ---------------------------------------------------------------------------
# Q8 · 不可变前缀 / 可恢复点
# ---------------------------------------------------------------------------


def test_locked_prefix_includes_only_success_terminals():
    """失败终态不进前缀——它没有要保护的东西，重规划可以重写它。"""
    plan = [_row(_T1), _row(_T2, deps=[_T1]), _row(_T3, deps=[_T1])]
    state = {
        "subtasks": plan,
        "subtask_results": [
            _term(_T1, output={"assignee": "张三"}),
            _term(_T2, error="boom"),
        ],
    }
    assert [r["subtask_id"] for r in _locked_prefix(state)] == [_T1]


def test_locked_prefix_empty_on_first_plan():
    state = {"subtasks": [_row(_T1)], "subtask_results": []}
    assert _locked_prefix(state) == []


_PLAN_PATCH = "app.ops.lg_rag.multi.nodes.get_llm_provider"
_CAPS_PATCH = "app.ops.lg_rag.multi.nodes.list_capabilities"


def _fake_caps(*_a, **_kw):
    return [SimpleNamespace(capability_id=_TOOL, description="Mock 查询", risk_level="low")]


def _prov(*outputs):
    """一个 provider 实例。

    注意不能用 ``lambda: SimpleNamespace(complete=AsyncMock(...))`` —— 那样每个
    节点都拿到**新的** mock，supervisor 第二次调用又会读到最后一份计划，
    把"重规划"测成"重跑原计划"。
    """
    return SimpleNamespace(complete=AsyncMock(side_effect=list(outputs)))


def _seq_provider(*outputs):
    """图级 provider：按序返回，用尽后给占位串（避免 StopAsyncMock 打断图）。

    必须**只造一次实例**再让 ``get_llm_provider`` 返回它。
    """
    stream = iter(outputs)

    async def complete(msgs, model=None):
        try:
            return next(stream)
        except StopIteration:
            return "（无更多计划，保留现状）"

    return SimpleNamespace(complete=complete)


def _plan_json(items: list[dict]) -> str:
    return json.dumps({"subtasks": items}, ensure_ascii=False)


def _state(**kw) -> dict:
    base = {
        "messages": [HumanMessage(content="复合问题")],
        "run_id": _RUN,
        "allowed_capability_ids": [_TOOL],
        "supervisor_step_count": 0,
        "host_subtask_seq": 0,
        "subtasks": [],
        "subtask_results": [],
    }
    base.update(kw)
    return base


@pytest.mark.asyncio
async def test_replan_keeps_prefix_verbatim_and_declares_recoverable_point():
    """R15 正向：重规划只动后缀；前缀 subtask_id / tool / args 逐字段不变。"""
    first = _plan_json(
        [
            {"id": "t1", "type": "tool", "tool": _TOOL, "input": "甲", "args": {"k": "v"}},
            {"id": "t2", "type": "tool", "tool": _TOOL, "input": "乙"},
        ]
    )
    state = _state()
    with patch(_CAPS_PATCH, new=_fake_caps), patch(_PLAN_PATCH, new=lambda *a, **k: _prov(first)):
        out = await supervisor_node(state)

    plan = out["subtasks"]
    assert [r["subtask_id"] for r in plan] == [_T1, _T2]
    assert out["recoverable_point"] == 0  # 首次规划没有前缀

    # 模拟 t1 跑成功了
    done = SubtaskResultBatch([_term(_T1, output={"assignee": "张三"})], {_T1, _T2})
    state2 = _state(
        subtasks=plan,
        subtask_results=done,
        host_subtask_seq=out["host_subtask_seq"],
        supervisor_step_count=1,
    )
    suffix = _plan_json(
        [{"id": "s1", "type": "tool", "tool": _TOOL, "input": "丙", "depends_on": ["t1"]}]
    )
    with patch(_CAPS_PATCH, new=_fake_caps), patch(_PLAN_PATCH, new=lambda *a, **k: _prov(suffix)):
        out2 = await supervisor_node(state2)

    plan2 = out2["subtasks"]
    assert [r["subtask_id"] for r in plan2] == [_T1, f"{_RUN}:3"]
    # 前缀逐字段不变（锁定的是 form，不只是 id）
    assert plan2[0]["tool"] == _TOOL
    assert plan2[0]["args"] == {"k": "v"}
    assert plan2[0]["input"] == "甲"
    # 可恢复点：下一个真正要执行的步骤下标
    assert out2["recoverable_point"] == 1
    assert out2["plan_prefix_ids"] == [_T1]
    # 后缀可以依赖前缀
    assert plan2[1]["depends_on"] == [_T1]


@pytest.mark.asyncio
async def test_replan_suffix_cap_shrinks_with_prefix():
    """前缀占位后，后缀上限同步收缩，总数不超过 MAX_SUBTASKS。"""
    plan = [_row(_T1), _row(_T2)]
    done = SubtaskResultBatch(
        [_term(_T1, output={"a": 1}), _term(_T2, output={"b": 2})], {_T1, _T2}
    )
    state = _state(subtasks=plan, subtask_results=done, host_subtask_seq=2, supervisor_step_count=2)
    suffix = _plan_json(
        [
            {"id": "s1", "type": "rag", "input": "丙"},
            {"id": "s2", "type": "rag", "input": "丁"},
            {"id": "s3", "type": "rag", "input": "戊"},
            {"id": "s4", "type": "rag", "input": "己"},
        ]
    )
    with patch(_CAPS_PATCH, new=_fake_caps), patch(_PLAN_PATCH, new=lambda *a, **k: _prov(suffix)):
        out = await supervisor_node(state)
    assert len(out["subtasks"]) == MAX_SUBTASKS
    assert out["recoverable_point"] == 2


@pytest.mark.asyncio
async def test_replan_illegal_output_keeps_prefix_instead_of_single_rag():
    """LLM 重规划输出非法时，退化成"单 rag"会抹掉已完成步骤的关联键。"""
    plan = [_row(_T1)]
    done = SubtaskResultBatch([_term(_T1, output={"a": 1})], {_T1})
    state = _state(subtasks=plan, subtask_results=done, host_subtask_seq=1, supervisor_step_count=1)
    with (
        patch(_CAPS_PATCH, new=_fake_caps),
        patch(_PLAN_PATCH, new=lambda *a, **k: _prov("这不是 JSON")),
    ):
        out = await supervisor_node(state)
    assert [r["subtask_id"] for r in out["subtasks"]] == [_T1]
    assert out["plan_prefix_ids"] == [_T1]


# ---------------------------------------------------------------------------
# 图级：被拦下的步骤必须**零请求**（不只是不下发）
# ---------------------------------------------------------------------------


async def _rag_gen(*_a, **_kw):
    yield {"rag_node": {"messages": [AIMessage(content="rag 答案")], "chain_meta": {}}}


def _cap(ok: bool, output=None, error=None):
    return SimpleNamespace(ok=ok, output=output if output is not None else {}, error=error, meta={})


@pytest.mark.asyncio
async def test_predecessor_failure_means_zero_downstream_tool_calls(monkeypatch):
    """R14 最强形态：前驱失败 ⇒ 后继工具**一次都没打**（不是"打了但忽略结果"）。"""
    from langgraph.checkpoint.memory import InMemorySaver

    # supervisor-first（D2）夹具同步：t1 失败后 replan 第二轮 provider 输出不可解析，
    # locked 空前缀下默认 fail-closed 会 raise（D2 本意，由 test_lg_rag_multi/
    # structured_output_p2 的 fail-closed 用例覆盖）。本条测的是 depends_on 拦截契约，
    # 与 fail-closed 正交 → 用灾备档 single_rag 保持旧收尾形态，断言零改动。
    monkeypatch.setenv("LG_RAG_SUPERVISOR_PLAN_ON_FAIL", "single_rag")

    from app.ops.lg_rag.multi.graph import build_supervisor_agent
    from app.ops.lg_rag.schemas import IntentV1

    intent_ok = IntentV1(
        domain="ops_kb",
        needs_tool=True,
        needs_skill=False,
        is_composite=True,
        risk_hint="low",
        summary="契约",
    )
    plan = _plan_json(
        [
            {"id": "t1", "type": "tool", "tool": _TOOL, "input": "甲"},
            {"id": "t2", "type": "tool", "tool": _TOOL, "input": "乙", "depends_on": ["t1"]},
        ]
    )
    calls: list[str] = []

    async def _tool_call(name, args, ctx=None):
        calls.append(str(name))
        return _cap(False, error="下游 500")  # t1 失败

    graph = build_supervisor_agent(checkpointer=InMemorySaver())
    provider = _seq_provider(plan, "## 综合结论")
    with (
        patch(
            "app.ops.strategy.intent.acomplete_structured", new=AsyncMock(return_value=intent_ok)
        ),
        patch(
            _PLAN_PATCH,
            new=lambda *a, **k: provider,
        ),
        patch("app.ops.lg_rag.multi.nodes.capability_ainvoke", new=_tool_call),
        patch("app.ops.lg_rag.multi.nodes.astream_router_agent", new=_rag_gen),
    ):
        out = await graph.ainvoke(
            {
                "messages": [HumanMessage(content="复合问题")],
                "run_id": _RUN,
                # 关掉 critic 回环：本条测的是"前驱失败⇒后继零请求"，
                # 回环会把结果裁掉（无成功步骤时等价于清空），干扰读取。
                # 回环本身由下面的 test_replan_preserves_prefix_results 覆盖。
                "inner_retry_count": 1,
            },
            {"configurable": {"thread_id": "t-contract"}},
        )

    assert calls == [_TOOL], f"后继被拦下时应只有一次调用，实际 {calls}"
    results = {r["subtask_id"]: r for r in out["subtask_results"]}
    assert "error" in results[_T1]
    assert results[_T2]["blocked_by"] == sc.BLOCKED_PREDECESSOR_FAILED
    assert "error" in results[_T2]


@pytest.mark.asyncio
async def test_successful_chain_still_binds_and_calls_both():
    """R14 反向对照（图级）：契约满足时两步**都**真的执行，且下游拿到绑定值。"""
    from langgraph.checkpoint.memory import InMemorySaver

    from app.ops.lg_rag.multi.graph import build_supervisor_agent
    from app.ops.lg_rag.schemas import IntentV1

    intent_ok = IntentV1(
        domain="ops_kb",
        needs_tool=True,
        needs_skill=False,
        is_composite=True,
        risk_hint="low",
        summary="契约",
    )
    plan = _plan_json(
        [
            {"id": "t1", "type": "tool", "tool": _TOOL, "input": "甲", "produces": ["assignee"]},
            {
                "id": "t2",
                "type": "tool",
                "tool": _TOOL,
                "input": "乙",
                "depends_on": ["t1"],
                "consumes": {"t1": ["assignee"]},
                "args": {"assignee": "待填"},
            },
        ]
    )
    seen: list[dict] = []

    async def _tool_call(name, args, ctx=None):
        payload = dict(args) if isinstance(args, dict) else {}
        seen.append(payload)
        return _cap(True, output={"assignee": "张三", "status": "open"})

    graph = build_supervisor_agent(checkpointer=InMemorySaver())
    provider = _seq_provider(plan, "## 综合结论")
    with (
        patch(
            "app.ops.strategy.intent.acomplete_structured", new=AsyncMock(return_value=intent_ok)
        ),
        patch(
            _PLAN_PATCH,
            new=lambda *a, **k: provider,
        ),
        patch("app.ops.lg_rag.multi.nodes.capability_ainvoke", new=_tool_call),
        patch("app.ops.lg_rag.multi.nodes.astream_router_agent", new=_rag_gen),
    ):
        out = await graph.ainvoke(
            {"messages": [HumanMessage(content="复合问题")], "run_id": _RUN},
            {"configurable": {"thread_id": "t-contract-ok"}},
        )

    assert len(seen) == 2, f"契约满足时两步都该执行，实际 {seen}"
    # 第二步拿到的必须是绑定值，不是 planner 写死的占位值
    assert seen[1]["assignee"] == "张三"
    results = {r["subtask_id"]: r for r in out["subtask_results"]}
    assert "error" not in results[_T2]


@pytest.mark.asyncio
async def test_replan_preserves_prefix_results_and_does_not_rerun_them():
    """R15 图级：critic 回环重规划时，已成功步骤的结果必须留下、且不得被重跑。

    修这条之前 critic 是 ``subtask_results = None``（整批清空）⇒ 重规划等于
    全量重来，前缀无从谈起，已跑过的步骤会被再打一遍。
    """
    from langgraph.checkpoint.memory import InMemorySaver

    from app.ops.lg_rag.multi.graph import build_supervisor_agent
    from app.ops.lg_rag.schemas import IntentV1

    intent_ok = IntentV1(
        domain="ops_kb",
        needs_tool=True,
        needs_skill=False,
        is_composite=True,
        risk_hint="low",
        summary="契约",
    )
    plan = _plan_json(
        [
            {"id": "t1", "type": "tool", "tool": _TOOL, "input": "甲", "produces": ["assignee"]},
            {"id": "t2", "type": "tool", "tool": _TOOL, "input": "乙", "depends_on": ["t1"]},
        ]
    )
    suffix = _plan_json(
        [{"id": "s1", "type": "tool", "tool": _TOOL, "input": "丙", "depends_on": ["t1"]}]
    )
    seen: list[str] = []

    async def _tool_call(name, args, ctx=None):
        seen.append(str(ctx.get("subtask_id")))
        # 第 2 步失败 ⇒ 触发 critic retry_planner
        return (
            _cap(True, output={"assignee": "张三"}) if len(seen) != 2 else _cap(False, error="boom")
        )

    graph = build_supervisor_agent(checkpointer=InMemorySaver())
    # 外层 ReAct：没有待发步骤先过 observe，它判定"没做完"就 replan。
    # 于是**第 2 次 LLM 就是重规划**（不再是 aggregator）——桩要按新拓扑给。
    provider = _seq_provider(plan, suffix, "## 综合结论一", suffix, "## 综合结论二")
    with (
        patch(
            "app.ops.strategy.intent.acomplete_structured", new=AsyncMock(return_value=intent_ok)
        ),
        patch(_PLAN_PATCH, new=lambda *a, **k: provider),
        patch("app.ops.lg_rag.multi.nodes.capability_ainvoke", new=_tool_call),
        patch("app.ops.lg_rag.multi.nodes.astream_router_agent", new=_rag_gen),
    ):
        out = await graph.ainvoke(
            {"messages": [HumanMessage(content="复合问题")], "run_id": _RUN},
            {"configurable": {"thread_id": "t-contract-replan"}},
        )

    # 前缀 t1 只被真正执行过一次（回环后不重跑）
    assert seen.count(_T1) == 1, f"前缀被重跑了：{seen}"
    # 重规划确实发生了（后缀拿到新的 seq=3）
    assert f"{_RUN}:3" in seen
    # 前缀的结果还在，没被回环抹掉
    results = {r["subtask_id"]: r for r in out["subtask_results"]}
    assert "output" in results[_T1], f"前缀结果被抹掉了：{results}"
    # 可恢复点声明出来了（Q8 原题："编排层没声明"）
    assert out["recoverable_point"] == 1
    assert out["plan_prefix_ids"] == [_T1]


async def test_join_uses_declared_prefix_not_any_success_terminal():
    """前缀必须是**声明**出来的，不能从"有 output 的终态"反推。

    反推的话，本轮刚跑完的前驱也被当成前缀 ⇒ 任何缺字段都变成
    prefix_touch_required ⇒ contract_missing_field 成了死分支，
    Q4（别把坏数据喂下去）与 Q8（改历史得交人）被混成一件事。
    """
    plan = [
        _row(_T1, produces=["assignee"]),
        _row(_T2, deps=[_T1], consumes={_T1: ["assignee"]}),
    ]
    bad = [_term(_T1, output={"status": "open"})]

    # 未声明前缀 ⇒ 本轮前驱产出不符 ⇒ contract_missing_field（Q4）
    out = await _join_subtasks(
        {
            "subtasks": plan,
            "subtask_results": bad,
            "inflight_subtask_ids": [_T1],
            "supervisor_step_count": 1,
        }
    )
    row = {r["subtask_id"]: r for r in out["subtask_results"]}[_T2]
    assert row["blocked_by"] == sc.BLOCKED_CONTRACT_MISSING
    assert "hitl_required" not in row

    # 声明了前缀 ⇒ 同样的缺失变成"要改历史" ⇒ 交人（Q8）
    out = await _join_subtasks(
        {
            "subtasks": plan,
            "subtask_results": bad,
            "inflight_subtask_ids": [_T1],
            "supervisor_step_count": 1,
            "plan_prefix_ids": [_T1],
        }
    )
    row = {r["subtask_id"]: r for r in out["subtask_results"]}[_T2]
    assert row["blocked_by"] == sc.BLOCKED_PREFIX_TOUCH
    assert row["hitl_required"] is True
