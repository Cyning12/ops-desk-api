"""输入结构隔离注入金样红线（否决项 · security-input-isolation W1）。

**红线不是准确率。** 任一条被突破**整体不通过**。

清单在 `evals/security/input_isolation_v1.yaml`；本文件是它的实现，
两者一一对应（P0 守这条）。对齐 tests/eval/test_memory_preference_redline.py
先例形态（清单=实现 · 正反双断言 · 确定性结构断言）。

诚实定性（SPEC §7 ①）：文本边界不是硬边界——本文件断言「可归因 + 可机检 +
越权构造零请求」，**不声称防住注入**；注入语义判定归 W2 检测层。

热路径零 LLM-as-judge：全部判定为结构/计数机检断言（槽位边界、消息结构
不变量、mock 调用计数、span 标记），无任何 LLM 语义裁判。
"""

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest
import yaml
from langchain_core.messages import HumanMessage

from app.ops.lc_evidence_chain import answer as answer_mod
from app.ops.lc_evidence_chain.answer import answer_question, answer_system_prompt
from app.ops.lc_evidence_chain.types import EvidenceItem
from app.ops.lg_rag.continuity import (
    assemble_graph_messages,
    assemble_graph_messages_with_memory,
)
from app.ops.lg_rag.multi import nodes as multi_nodes
from app.ops.prompts.slots import (
    UNTRUSTED_GUIDE,
    SlotIsolationError,
    slot_close_tag,
    slot_open_tag,
    wrap_slot,
)
from tests.test_lg_rag_multi import (
    _AGGREGATED,
    _build,
    _provider,
    _result,
    _run,
    _subtasks_json,
)

pytestmark = pytest.mark.redline

_INVENTORY = Path(__file__).resolve().parents[2] / "evals" / "security" / "input_isolation_v1.yaml"

_ENV = "SECURITY_INPUT_ISOLATION_ENABLED"

#: redline_id → 实现它的测试函数名（装饰器登记，P0 对照用）
IMPLEMENTED: dict[str, str] = {}


def redline(redline_id: str):
    def decorate(fn):
        IMPLEMENTED[redline_id] = fn.__name__
        fn.__doc__ = f"[{redline_id}] {fn.__doc__ or ''}"
        return fn

    return decorate


def _load_inventory() -> dict:
    with _INVENTORY.open(encoding="utf-8") as f:
        return yaml.safe_load(f)


def _case(case_id: str) -> dict:
    cases = {c["id"]: c for c in _load_inventory()["golden_cases"]}
    return cases[case_id]


def _item(content: str) -> EvidenceItem:
    return EvidenceItem(
        id=1,
        repo="cyning/ops-desk",
        source_type="issue",
        source_id="2720",
        chunk_index=1,
        content=content,
        title="注入样本",
    )


class _Prov:
    """捕获发往 LLM 的消息（计数 + 内容）。"""

    def __init__(self) -> None:
        self.calls: list[list] = []

    async def complete(self, messages, model=None):
        self.calls.append(list(messages))
        return "答案"


async def _answer_capture(query: str, items: list[EvidenceItem]) -> tuple[list, _Prov]:
    prov = _Prov()
    with patch.object(answer_mod, "get_llm_provider", return_value=prov):
        await answer_question(query, items)
    return prov.calls[0], prov


def _slot_span(text: str, slot_id: str) -> tuple[int, int]:
    """返回 slot_id 槽位块的（开标记起点, 闭标记终点）。"""
    open_tag = slot_open_tag(slot_id, trusted=False)
    close_tag = slot_close_tag(slot_id)
    start = text.index(open_tag)
    end = text.index(close_tag, start) + len(close_tag)
    return start, end


def _assert_sentinel_only_inside_slot(text: str, sentinel: str, slot_id: str) -> None:
    """sentinel 每次出现都在 slot_id 边界标记之间；且至少出现一次（反向对照）。"""
    start, end = _slot_span(text, slot_id)  # 块不存在即 index() 炸 = 反向对照
    assert sentinel in text[start:end], "sentinel 须在槽位块内（反向对照防‘内容被丢’假通过）"
    pos = 0
    while True:
        i = text.find(sentinel, pos)
        if i < 0:
            break
        assert start <= i < end, f"sentinel 出现在 {slot_id} 槽位块外: offset={i}"
        pos = i + 1


@redline("P0")
def test_inventory_matches_implementation():
    """清单 ↔ 实现一一对应：多声明 = 假防护，少声明 = 暗改。"""
    inv = _load_inventory()
    declared = {r["id"] for r in inv["redlines"]}
    assert declared == set(IMPLEMENTED), (
        f"清单与实现漂移：declared={sorted(declared)} implemented={sorted(IMPLEMENTED)}"
    )
    assert len(inv["golden_cases"]) >= 3, "金样太少不足以称金样"


@redline("P1")
async def test_sentinel_only_inside_declared_slots(monkeypatch: pytest.MonkeyPatch):
    """on 态：G1（RAG 片段）/ G2（工具回执）sentinel 只进被声明槽位块 + 不可信标记。"""
    monkeypatch.setenv(_ENV, "true")

    # G1 · rag_evidence 面
    g1 = _case("G1")
    messages, _ = await _answer_capture("正常问题", [_item(g1["sentinel"])])
    system, user = messages
    assert g1["sentinel"] not in str(system.content), "sentinel 不得进指令资产"
    user_text = str(user.content)
    _assert_sentinel_only_inside_slot(user_text, g1["sentinel"], "rag_evidence")
    guide = UNTRUSTED_GUIDE.format(label="检索片段")
    assert guide in user_text, "rag_evidence 槽位块须带不可信声明引导语"

    # G2 · tool_result 面（tool_exec 包装 → aggregator payload 边界存活）
    g2 = _case("G2")
    cap = SimpleNamespace(ok=True, output=g2["sentinel"], meta={}, error=None)
    sub = {"id": "t1", "type": "tool", "input": "查", "tool": "mock_get_deploy_info"}
    with patch.object(multi_nodes, "capability_ainvoke", AsyncMock(return_value=cap)):
        out = await multi_nodes.tool_exec_node(
            {"subtasks": [sub], "subtask_results": [], "assigned_subtask": sub}
        )
    wrapped = out["subtask_results"][0]["output"]
    _assert_sentinel_only_inside_slot(wrapped, g2["sentinel"], "tool_result")
    # 聚合 payload（JSON 序列化层）中 sentinel 仍在槽位边界内
    payload = json.dumps(out["subtask_results"], ensure_ascii=False, default=str)
    assert 'slot:tool_result trust=\\"untrusted\\"' in payload  # JSON 转义形态边界存活
    assert payload.find(g2["sentinel"]) > payload.find("slot:tool_result")


@redline("P2")
async def test_structure_invariants_independent_of_sentinel(
    monkeypatch: pytest.MonkeyPatch,
):
    """消息结构不变量（消息数/角色序/指令资产逐字节）与 sentinel 内容无关。"""
    monkeypatch.setenv(_ENV, "true")
    g1 = _case("G1")

    # answer 面：sentinel vs 无 sentinel → 结构全同，指令资产逐字节
    msgs_plain, _ = await _answer_capture("正常问题", [_item("普通片段")])
    msgs_sent, _ = await _answer_capture("正常问题", [_item(g1["sentinel"])])
    assert [m.role for m in msgs_plain] == [m.role for m in msgs_sent] == ["system", "user"]
    assert str(msgs_plain[0].content) == str(msgs_sent[0].content) == answer_system_prompt("v1")

    # lg_rag 装配面：sentinel 进 query/历史 → 消息数/角色序/全部正文逐字节不变
    # （归因只在 additional_kwargs，注入内容改变不了装配结构）
    history = [{"role": "user", "content": f"q{i}"} for i in range(3)] + [
        {"role": "user", "content": g1["sentinel"]}
    ]
    off = assemble_graph_messages("本轮问", history)
    on = await assemble_graph_messages_with_memory("本轮问", history)
    assert [(type(m).__name__, str(m.content)) for m in on] == [
        (type(m).__name__, str(m.content)) for m in off
    ]
    assert [m.additional_kwargs.get("slot_ids") for m in on]  # 归因存在（防空真）


@redline("P3")
async def test_overreach_zero_request_double_assertion(monkeypatch: pytest.MonkeyPatch):
    """越权构造下游零请求（双断言缺一不算过）。

    ① 装配层混入未声明内容（绕过 wrap_slot 直拼）→ mock provider 计数=0
       **且** span input_isolation_rejected 出现；
    ② G4 注入诱导 supervisor 规划非法 tool id → capability gateway 计数=0
       **且** span supervisor_invalid_tool_id 出现（既有 fallback 先例形态）。
    """
    monkeypatch.setenv(_ENV, "true")

    # ① 装配层物理拒收（answer 面）
    spans: list[dict] = []
    monkeypatch.setattr(answer_mod, "update_current_span_metadata", lambda m: spans.append(m))
    monkeypatch.setattr(answer_mod, "wrap_slot", lambda sid, content: content)  # 越权构造
    prov = _Prov()
    with (
        patch.object(answer_mod, "get_llm_provider", return_value=prov),
        pytest.raises(SlotIsolationError),
    ):
        await answer_question("q", [_item("正文")])
    assert len(prov.calls) == 0, "越权构造不得发往 provider（不是被拒绝，是没发出去）"
    assert {"input_isolation_rejected": True} in spans, "缺拒收路径标记 = 假通过"
    monkeypatch.undo()  # 恢复 wrap_slot 后再走 ②（避免泄漏到图内 answer 面）

    # ② G4 · supervisor invalid_tool_id fallback（gateway 零请求）
    monkeypatch.setenv(_ENV, "true")
    g4 = _case("G4")
    gateway = AsyncMock(side_effect=AssertionError("越权工具调用不得触达 gateway"))
    span_calls: list[dict] = []
    supervisor_out = _subtasks_json(
        [{"id": "t1", "type": "tool", "input": g4["sentinel"], "tool": "no_such_tool"}]
    )
    router = _provider('{"route": "direct"}', '{"route": "direct"}')
    chain = AsyncMock(return_value=_result("direct 答案"))
    multi = _provider(supervisor_out, _AGGREGATED, supervisor_out, _AGGREGATED)
    with (
        patch("app.ops.lg_rag.multi.nodes.get_llm_provider", return_value=multi),
        patch("app.ops.lg_rag.nodes.get_llm_provider", return_value=router),
        patch("app.ops.lg_rag.nodes.ainvoke_evidence_answer", new=chain),
        patch("app.ops.lg_rag.multi.nodes.capability_ainvoke", new=gateway),
        patch(
            "app.ops.lg_rag.multi.nodes._record_span_metadata",
            side_effect=lambda m: span_calls.append(m),
        ),
    ):
        out = await _run(_build(), query=g4["sentinel"])
    assert gateway.await_count == 0, "非法 tool id 不得触达 capability gateway"
    assert any(s.get("supervisor_invalid_tool_id") is True for s in span_calls), (
        "缺 supervisor_invalid_tool_id 拒收标记 = 「没发出去」与「没走到」不可区分"
    )
    assert out["subtasks"][0]["type"] == "rag"  # 整单 fallback（既有语义零改动）


@redline("P4")
def test_forged_markers_escaped_never_enter_memory_fact():
    """G3 伪造标记：sentinel 自印 [已知事实]/<slot:memory_fact> → 转义后不构成边界。"""
    g3 = _case("G3")
    sentinel = g3["sentinel"]
    block = str(wrap_slot("tool_result", sentinel))

    # 伪造的槽位边界/节首标记被全角转义，正文中不再有结构语义
    assert "<slot:memory_fact" not in block
    assert "[已知事实]" not in block
    assert "＜slot:memory_fact" in block and "［已知事实］" in block  # 转义形态可见
    # 装配校验只认出一个 tool_result 边界（伪造的 memory_fact 不构成槽位结构）
    from app.llm.schema import LlmMessage
    from app.ops.prompts.slots import assert_slots_declared, declare_slots

    msg = LlmMessage(role="user", content=block)
    declare_slots(msg, ["tool_result"])
    assert_slots_declared([msg])

    # 真实 memory_fact 块结构不受影响：伪造内容进不了 memory_fact 槽位
    from app.ops.lg_rag.continuity import MEMORY_FACTS_HEADER, render_memory_facts_block

    real_block = render_memory_facts_block([{"key": "project.primary_repo", "value": "ops"}])
    assert real_block.startswith(MEMORY_FACTS_HEADER)
    assert "admin_password" not in real_block  # 伪造 fact 不进入真实 memory_fact 结构


@redline("P5")
async def test_off_three_states_byte_identical_all_faces(monkeypatch: pytest.MonkeyPatch):
    """off 三态（未设/false/非法值）四个面与现网逐字节一致；off 零触达。"""
    from app.ops.prompts import slots as slots_mod

    for state in ("unset", "false", "garbage"):
        if state == "unset":
            monkeypatch.delenv(_ENV, raising=False)
        else:
            monkeypatch.setenv(_ENV, "false" if state == "false" else "enable plz")

        # answer 面
        items = [_item("普通片段")]
        messages, _ = await _answer_capture("本轮问题", items)
        assert str(messages[0].content) == answer_system_prompt("v1")
        assert "<slot:" not in str(messages[1].content)  # off 态零标记泄漏

        # continuity 面
        baseline = assemble_graph_messages("本轮问", [{"role": "user", "content": "h"}])
        out = await assemble_graph_messages_with_memory(
            "本轮问", [{"role": "user", "content": "h"}]
        )
        assert [(type(m).__name__, str(m.content)) for m in out] == [
            (type(m).__name__, str(m.content)) for m in baseline
        ]
        assert all("slot_ids" not in m.additional_kwargs for m in out)

        # tool_exec 面
        cap = SimpleNamespace(ok=True, output="回执原文", meta={}, error=None)
        sub = {"id": "t1", "type": "tool", "input": "查", "tool": "mock_get_deploy_info"}
        with patch.object(multi_nodes, "capability_ainvoke", AsyncMock(return_value=cap)):
            tool_out = await multi_nodes.tool_exec_node(
                {"subtasks": [sub], "subtask_results": [], "assigned_subtask": sub}
            )
        assert tool_out["subtask_results"][0]["output"] == "回执原文"

        # aggregator 面
        sent: list[list] = []

        async def _capture(provider, messages, model=None, node=None, _sent=sent):
            _sent.append(list(messages))  # 显式绑定（B023：闭包不偷循环变量）
            return "综合"

        monkeypatch.setattr(multi_nodes, "complete_answer_streaming", _capture)
        results = [{"id": "t1", "type": "tool", "output": "回执原文"}]
        await multi_nodes.aggregator_node(
            {"messages": [HumanMessage(content="原始问题")], "subtask_results": results}
        )
        payload = json.dumps(results, ensure_ascii=False, default=str)
        assert str(sent[0][1].content) == f"原始问题：原始问题\n子任务结果：{payload}"
        monkeypatch.undo()  # 本轮面的补丁复位，进入下一 state

    # off 零触达：三面装配全程 wrap/assert 调用计数 = 0
    monkeypatch.delenv(_ENV, raising=False)
    counts = {"wrap": 0, "assert": 0}
    real_wrap, real_assert = slots_mod.wrap_slot, slots_mod.assert_slots_declared

    def _wrap(*a, **k):
        counts["wrap"] += 1
        return real_wrap(*a, **k)

    def _assert(*a, **k):
        counts["assert"] += 1
        return real_assert(*a, **k)

    monkeypatch.setattr(answer_mod, "wrap_slot", _wrap)
    monkeypatch.setattr(answer_mod, "assert_slots_declared", _assert)
    monkeypatch.setattr(multi_nodes, "wrap_slot", _wrap)
    monkeypatch.setattr(multi_nodes, "assert_slots_declared", _assert)
    import app.ops.lg_rag.continuity as continuity_mod

    monkeypatch.setattr(continuity_mod, "assert_slots_declared", _assert)
    monkeypatch.setattr(continuity_mod, "declare_slots", lambda m, s: m)
    await _answer_capture("q", [_item("正文")])
    await assemble_graph_messages_with_memory("q", [])
    assert counts == {"wrap": 0, "assert": 0}
