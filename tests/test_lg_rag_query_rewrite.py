"""query-coref-rewrite 守护测试（task_query_coref_rewrite TC1–TC9 机断面）。

钉死（SPEC query-coref-rewrite §2/§5 · task D1–D4）：
- D1 先重写后召回：resolved_query 在两条装配分支（session_summary on/off）
  之前一次算出；末位 HumanMessage 与 recall_with_vector 统一吃它（TC8 调用序）。
- D2 开关 LG_RAG_QUERY_REWRITE_ENABLED 默认关 · 非法值 warning 回退关（TC6）；
  LLM 异常/超时/非法输出 → 静默降级原文 + span 双标记（TC3/TC9）；非法输出
  确定式三规则：strip 空串 / 含换行（拒多行不截首行）/ strip 后 >512 字符。
- D3 落盘 persist_thread_turns 与 run.start payload.query 记原文（TC5）；
  首轮无历史短路零 LLM 调用（TC4）。
- off（未设/falsy/非法值）→ 三模式装配逐元素零 diff + 零 LLM 调用（TC1）。
"""

from __future__ import annotations

import asyncio
import json
import logging
from collections.abc import AsyncIterator
from typing import Any
from unittest.mock import patch

import pytest
from httpx import AsyncClient
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage

from app.llm import model_catalog
from app.llm.schema import BaseProvider
from app.ops.lg_rag import query_rewrite
from app.ops.lg_rag.continuity import (
    assemble_graph_messages,
    assemble_graph_messages_with_memory,
)

#: 两轮历史夹具（user/assistant 交替 · 末轮 assistant 收尾）
_HISTORY = [
    {"role": "user", "content": "支付网关从昨天开始间歇 502"},
    {"role": "assistant", "content": "先查 upstream 证书链与 LB 健康检查。"},
]

#: 金样（TC2）：(history, query, 期望改写) —— 指代/省略/时间锚定各 ≥2 + continue 场景
_GOLDENS: list[tuple[list[dict], str, str]] = [
    # 指代消解 ×2
    (_HISTORY, "它现在恢复了吗", "支付网关间歇 502 现在恢复了吗"),
    (
        [
            {"role": "user", "content": "redis-cluster-03 的内存水位"},
            {"role": "assistant", "content": "已超 85% 阈值。"},
        ],
        "这个节点先扩容还是先做故障转移",
        "redis-cluster-03 先扩容还是先做故障转移",
    ),
    # 省略补全 ×2
    (_HISTORY, "那日志呢", "支付网关间歇 502 的日志怎么查"),
    (
        [
            {"role": "user", "content": "怎么发布订单服务 v2.3"},
            {"role": "assistant", "content": "走金丝雀发布流程。"},
        ],
        "回滚呢",
        "订单服务 v2.3 怎么回滚",
    ),
    # 时间锚定 ×2
    (_HISTORY, "昨天的错误率是多少", "支付网关 2026-10-18 的 502 错误率是多少"),
    (
        [
            {"role": "user", "content": "上周的发布窗口"},
            {"role": "assistant", "content": "周三 22:00-24:00。"},
        ],
        "明天还有窗口吗",
        "2026-10-20 还有发布窗口吗",
    ),
    # continue 场景（续跑 run：历史来自既有 thread，query 含指代）
    (
        [
            {"role": "user", "content": "盘点在途的变更单"},
            {"role": "assistant", "content": "在途 3 张：CHG-101/102/103。"},
            {"role": "user", "content": "CHG-102 到哪一步了"},
            {"role": "assistant", "content": "等待二级审批。"},
        ],
        "那它什么时候能批完",
        "CHG-102 什么时候能批完",
    ),
]


def _shape(messages: list[BaseMessage]) -> list[tuple[str, str]]:
    return [(type(m).__name__, str(m.content)) for m in messages]


@pytest.fixture(autouse=True)
def _quiet_envs(monkeypatch: pytest.MonkeyPatch) -> None:
    """本面测试只验重写轨：邻面开关显式关闭，且不从 .env 继承任何重写档配置。"""
    for name in (
        "LG_RAG_QUERY_REWRITE_ENABLED",
        "OPS_LLM_TIER_REWRITE_MODEL",
        "OPS_LLM_STRATEGY_PACK",
        "MEMORY_FACTS_ENABLED",
        "MEMORY_FACTS_VECTOR_RECALL_ENABLED",
        "MEMORY_EPISODES_ENABLED",
        "SESSION_SUMMARY_ENABLED",
        "LG_RAG_HTTP_CHECKPOINTER",
    ):
        monkeypatch.delenv(name, raising=False)


class _FakeProvider(BaseProvider):
    """计数 fake：complete 记录调用；可配置文本 / 异常 / 延迟；order 钩子录调用序。"""

    def __init__(
        self,
        text: str = "重写后问题",
        *,
        error: Exception | None = None,
        delay: float = 0.0,
        order: list[str] | None = None,
    ):
        self.calls: list[dict] = []
        self._text = text
        self._error = error
        self._delay = delay
        self._order = order

    async def complete(self, messages, model=None):
        self.calls.append({"messages": list(messages), "model": model})
        if self._order is not None:
            self._order.append("rewrite")
        if self._delay:
            await asyncio.sleep(self._delay)
        if self._error is not None:
            raise self._error
        return self._text


def _patch_face(monkeypatch: pytest.MonkeyPatch, provider: _FakeProvider) -> dict:
    """mock 重写面 LLM/span；返回观测 dict（spans 为 update_current_span_metadata 实录）。"""
    obs: dict = {"spans": []}
    monkeypatch.setattr(query_rewrite, "get_llm_provider", lambda: provider)
    monkeypatch.setattr(
        query_rewrite,
        "update_current_span_metadata",
        lambda m: obs["spans"].append(m),
    )
    return obs


class _FakeGraph:
    """astream 捕获 graph 入参 payload（三模式零 diff 对拍用 · 零节点执行）。"""

    def __init__(self, sink: list):
        self._sink = sink

    async def astream(self, payload, config, stream_mode="updates"):
        self._sink.append(payload["messages"])
        if False:
            yield {}


async def _capture_graph_input(
    monkeypatch: pytest.MonkeyPatch, mode: str, query: str, history: list[dict]
) -> list[BaseMessage]:
    """按模式跑 astream 入口，返回装配后实际入图的 messages。"""
    sink: list = []
    fake = _FakeGraph(sink)
    if mode in ("basic", "router"):
        from app.ops.lg_rag import graph as basic_graph

        build_name = "build_basic_agent" if mode == "basic" else "build_router_agent"
        entry = (
            basic_graph.astream_basic_agent if mode == "basic" else basic_graph.astream_router_agent
        )
        monkeypatch.setattr(basic_graph, build_name, lambda **kw: fake)
    else:
        from app.ops.lg_rag.multi import graph as multi_graph

        entry = multi_graph.astream_supervisor_agent
        monkeypatch.setattr(multi_graph, "build_supervisor_agent", lambda **kw: fake)
    async for _ in entry(query, thread_id="th-qr-t1", history_turns=history):
        pass
    assert len(sink) == 1
    return sink[0]


# ---------------- TC1 · 默认关三模式逐元素零 diff ----------------


@pytest.mark.parametrize("mode", ["basic", "router", "supervisor"])
@pytest.mark.parametrize("env_value", [None, "0", "false", "off"])
async def test_tc1_off_three_modes_zero_diff(
    monkeypatch: pytest.MonkeyPatch, mode: str, env_value: str | None
):
    """off（未设/falsy）→ 三模式入图 messages 与纯装配逐元素一致；零 LLM 调用零 span。"""
    if env_value is not None:
        monkeypatch.setenv("LG_RAG_QUERY_REWRITE_ENABLED", env_value)
    provider = _FakeProvider()
    obs = _patch_face(monkeypatch, provider)
    baseline = assemble_graph_messages("它现在恢复了吗", _HISTORY)
    messages = await _capture_graph_input(monkeypatch, mode, "它现在恢复了吗", _HISTORY)
    assert _shape(messages) == _shape(baseline)
    assert provider.calls == []
    assert obs["spans"] == []


# ---------------- TC2 · 开 + 金样：末位 HumanMessage / planner / aggregator 实收 ----------------


@pytest.mark.parametrize(("history", "query", "expected"), _GOLDENS)
async def test_tc2_golden_coref_rewrite(
    monkeypatch: pytest.MonkeyPatch, history: list[dict], query: str, expected: str
):
    """金样三类（指代/省略/时间锚定）+ continue 场景：每请求至多一次 LLM 调用，
    返回值为改写文；user 消息窗含对话历史与最新问题原文。"""
    monkeypatch.setenv("LG_RAG_QUERY_REWRITE_ENABLED", "true")
    provider = _FakeProvider(text=expected)
    obs = _patch_face(monkeypatch, provider)
    out = await query_rewrite.maybe_rewrite_query(query, history)
    assert out == expected
    assert len(provider.calls) == 1
    call = provider.calls[0]
    assert call["messages"][0].role == "system"
    user_msg = call["messages"][-1]
    assert user_msg.role == "user"
    assert query in user_msg.content
    assert obs["spans"] == [
        {
            "query_rewrite_applied": True,
            "query_rewrite_src_len": len(query),
            "query_rewrite_dst_len": len(expected),
        }
    ]


async def test_tc2_assembly_last_human_message_is_rewritten(monkeypatch: pytest.MonkeyPatch):
    """装配面：末位 HumanMessage == 改写文；历史部分与 off 态逐字节一致。"""
    monkeypatch.setenv("LG_RAG_QUERY_REWRITE_ENABLED", "true")
    rewritten = "支付网关间歇 502 现在恢复了吗"
    provider = _FakeProvider(text=rewritten)
    _patch_face(monkeypatch, provider)
    out = await assemble_graph_messages_with_memory(
        "它现在恢复了吗", _HISTORY, thread_id="th-qr-t2"
    )
    baseline = assemble_graph_messages("它现在恢复了吗", _HISTORY)
    assert isinstance(out[-1], HumanMessage)
    assert str(out[-1].content) == rewritten
    assert _shape(out[:-1]) == _shape(baseline[:-1])


async def test_tc2_planner_aggregator_receive_rewritten(monkeypatch: pytest.MonkeyPatch):
    """planner/aggregator 实收改写文：两者均取 messages 末位 HumanMessage

    （supervisor_node 经 _last_user_text 直发 planner user 条；aggregator 经
    _aggregator_plain_messages 拼「原始问题：{query}」行）。
    """
    from app.ops.lg_rag.multi.nodes import _aggregator_plain_messages
    from app.ops.lg_rag.nodes import _last_user_text

    monkeypatch.setenv("LG_RAG_QUERY_REWRITE_ENABLED", "true")
    rewritten = "支付网关间歇 502 现在恢复了吗"
    provider = _FakeProvider(text=rewritten)
    _patch_face(monkeypatch, provider)
    out = await assemble_graph_messages_with_memory(
        "它现在恢复了吗", _HISTORY, thread_id="th-qr-t2b"
    )
    planner_query = _last_user_text(out)
    assert planner_query == rewritten
    agg_messages = _aggregator_plain_messages(planner_query, "子任务结果X")
    assert agg_messages[-1].role == "user"
    assert agg_messages[-1].content == f"原始问题：{rewritten}\n子任务结果：子任务结果X"


# ---------------- TC3 · 失败降级：异常 / 超时 → 原文 + span 双标记 ----------------


async def test_tc3_llm_error_fallback_with_span_marks(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("LG_RAG_QUERY_REWRITE_ENABLED", "true")
    provider = _FakeProvider(error=RuntimeError("llm down"))
    obs = _patch_face(monkeypatch, provider)
    out = await query_rewrite.maybe_rewrite_query("它现在恢复了吗", _HISTORY)
    assert out == "它现在恢复了吗"
    assert len(provider.calls) == 1
    assert obs["spans"] == [{"query_rewrite_applied": False, "query_rewrite_fallback": True}]


async def test_tc3_timeout_fallback_with_span_marks(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("LG_RAG_QUERY_REWRITE_ENABLED", "true")
    monkeypatch.setattr(query_rewrite, "QUERY_REWRITE_TIMEOUT_S", 0.05)
    provider = _FakeProvider(text="迟到的改写", delay=0.5)
    obs = _patch_face(monkeypatch, provider)
    out = await query_rewrite.maybe_rewrite_query("它现在恢复了吗", _HISTORY)
    assert out == "它现在恢复了吗"
    assert len(provider.calls) == 1
    assert obs["spans"] == [{"query_rewrite_applied": False, "query_rewrite_fallback": True}]


async def test_tc3_fallback_assembly_byte_identical_to_off(monkeypatch: pytest.MonkeyPatch):
    """降级时装配输出与 off 态逐字节一致（「走了重写面但降级」与「没走」经 span 区分）。"""
    monkeypatch.setenv("LG_RAG_QUERY_REWRITE_ENABLED", "true")
    provider = _FakeProvider(error=RuntimeError("llm down"))
    obs = _patch_face(monkeypatch, provider)
    baseline = assemble_graph_messages("它现在恢复了吗", _HISTORY)
    out = await assemble_graph_messages_with_memory(
        "它现在恢复了吗", _HISTORY, thread_id="th-qr-t3"
    )
    assert _shape(out) == _shape(baseline)
    assert len(provider.calls) == 1
    assert obs["spans"] == [{"query_rewrite_applied": False, "query_rewrite_fallback": True}]


# ---------------- TC4 · 首轮无历史短路：LLM 调用计数 == 0 ----------------


@pytest.mark.parametrize("history", [None, []])
async def test_tc4_first_turn_no_history_shortcircuit(
    monkeypatch: pytest.MonkeyPatch, history: list[dict] | None
):
    monkeypatch.setenv("LG_RAG_QUERY_REWRITE_ENABLED", "true")
    provider = _FakeProvider()
    obs = _patch_face(monkeypatch, provider)
    out = await query_rewrite.maybe_rewrite_query("首轮问题", history)
    assert out == "首轮问题"
    assert provider.calls == []
    assert obs["spans"] == []


# ---------------- TC5 · 落盘与 run.start 记原文 ----------------


def _parse_sse(body: str) -> list[dict]:
    events: list[dict] = []
    for block in body.split("\n\n"):
        block = block.strip()
        if not block:
            continue
        for line in block.split("\n"):
            if line.startswith("data: "):
                events.append(json.loads(line[len("data: ") :]))
    return events


async def test_tc5_persist_and_run_start_keep_original_query(
    client: AsyncClient, override_auth_maintainer, monkeypatch: pytest.MonkeyPatch
):
    """开关 on 且重写真生效（装配末位==改写文）时：run.start payload.query 与
    persist_thread_turns 落盘仍记原文。"""
    monkeypatch.setenv("LG_RAG_QUERY_REWRITE_ENABLED", "true")
    rewritten = "支付网关间歇 502 现在恢复了吗"
    provider = _FakeProvider(text=rewritten)
    _patch_face(monkeypatch, provider)
    captured: dict = {}
    persisted: list[dict] = []

    async def _fake_persist(thread_id: str, user_id: str, query: str, answer: str) -> None:
        persisted.append({"thread_id": thread_id, "query": query, "answer": answer})

    monkeypatch.setattr("app.ops.lg_rag.sse_stream.persist_thread_turns", _fake_persist)

    async def _fake_stream(
        query: str, *, thread_id: str = "t", **_kwargs: Any
    ) -> AsyncIterator[dict[str, Any]]:
        # 请求路径内真实走装配面：证明本请求重写确实生效
        msgs = await assemble_graph_messages_with_memory(query, _HISTORY, thread_id=thread_id)
        captured["assembled_last"] = str(msgs[-1].content)
        yield {"aggregator": {"messages": [AIMessage(content="最终答案")]}}
        yield {"critic_node": {"critic_verdict": "pass"}}

    with patch("app.ops.lg_rag.multi.graph.astream_supervisor_agent", new=_fake_stream):
        response = await client.post(
            "/api/ops/lg-rag/stream",
            json={"query": "它现在恢复了吗", "thread_id": "th-qr-t5"},
        )
    assert response.status_code == 200
    events = _parse_sse(response.text)
    assert events[0]["event_type"] == "run.start"
    assert events[0]["payload"]["query"] == "它现在恢复了吗"
    assert captured["assembled_last"] == rewritten
    assert len(provider.calls) == 1
    assert persisted and persisted[0]["query"] == "它现在恢复了吗"


# ---------------- TC6 · env 非法值：warning + 回退关 + 零 diff ----------------


async def test_tc6_invalid_env_warns_and_zero_diff(monkeypatch: pytest.MonkeyPatch, caplog):
    monkeypatch.setenv("LG_RAG_QUERY_REWRITE_ENABLED", "enable plz")
    provider = _FakeProvider()
    obs = _patch_face(monkeypatch, provider)
    baseline = assemble_graph_messages("它现在恢复了吗", _HISTORY)
    with caplog.at_level(logging.WARNING, logger="app.ops.lg_rag.query_rewrite"):
        out = await assemble_graph_messages_with_memory(
            "它现在恢复了吗", _HISTORY, thread_id="th-qr-t6"
        )
    assert _shape(out) == _shape(baseline)
    assert "LG_RAG_QUERY_REWRITE_ENABLED" in caplog.text
    assert provider.calls == []
    assert obs["spans"] == []


# ---------------- TC7 · rewrite 档在册（model_catalog 三处同增） ----------------


def test_tc7_rewrite_tier_registered_in_catalog(caplog):
    """TASK_TYPES / TASK_TIER_MODELS / TASK_TIER_FALLBACKS 三处在册；
    解析不走 unknown_task 告警；默认 (None, 'default')；fallback 链空 tuple。"""
    assert "rewrite" in model_catalog.TASK_TYPES
    assert "rewrite" in model_catalog.TASK_TIER_MODELS
    assert model_catalog.TASK_TIER_MODELS["rewrite"] is None
    assert model_catalog.TASK_TIER_FALLBACKS["rewrite"] == ()
    with caplog.at_level(logging.WARNING, logger="app.llm.model_catalog"):
        model, source = model_catalog.resolve_task_model("rewrite")
        chain = model_catalog.resolve_fallback_chain("rewrite")
    assert (model, source) == (None, "default")
    assert chain == ()
    assert "unknown llm task_type" not in caplog.text


def test_tc7_env_tier_override(monkeypatch: pytest.MonkeyPatch):
    """OPS_LLM_TIER_REWRITE_MODEL（已知目录内模型）→ source='env_tier'。"""
    known = model_catalog.resolve_siliconflow_models()[0].id
    monkeypatch.setenv("OPS_LLM_TIER_REWRITE_MODEL", known)
    assert model_catalog.resolve_task_model("rewrite") == (known, "env_tier")


# ---------------- TC8 · 先重写后召回（调用序断言） ----------------


async def test_tc8_rewrite_applied_recall_never_called_dormant(
    monkeypatch: pytest.MonkeyPatch,
):
    """④b 休眠断言：重写仍生效（末位 HumanMessage 实收 resolved_query），
    记忆向量召回**零调用**（注入双开关全开也不触达——消费点已收窄）。

    原 TC8「先重写后召回 rewrite → recall 调用序」断言随 ④b 切割失效；
    ④a 复活时按 docs/tasks/deferred/task_memory_facts_build_4a.md 清单恢复
    （recall 实收 resolved_query ∧ 调用序钉死）。
    """
    from app.ops.memory import service as memory_service

    monkeypatch.setenv("LG_RAG_QUERY_REWRITE_ENABLED", "true")
    monkeypatch.setenv("MEMORY_FACTS_ENABLED", "true")
    monkeypatch.setenv("MEMORY_FACTS_VECTOR_RECALL_ENABLED", "true")
    order: list[str] = []
    rewritten = "支付网关间歇 502 现在恢复了吗"
    provider = _FakeProvider(text=rewritten, order=order)
    _patch_face(monkeypatch, provider)

    async def _fake_recall(tenant_id: str, user_id: str, query: str, *, limit: int):
        order.append("recall")
        raise AssertionError("④b 休眠：向量召回通路不应被触达")

    monkeypatch.setattr(memory_service, "recall_with_vector", _fake_recall)
    out = await assemble_graph_messages_with_memory(
        "它现在恢复了吗",
        _HISTORY,
        tenant_id="tenant-1",
        user_id="user-1",
        thread_id="th-qr-t8",
    )
    assert order == ["rewrite"]  # 重写照常；recall 零触达
    assert str(out[-1].content) == rewritten


# ---------------- TC9 · 非法输出确定式三规则 ----------------


@pytest.mark.parametrize(
    "bad",
    [
        "",  # 空串
        "   \n  ",  # strip 后空
        "第一行\n第二行",  # 含换行（拒多行 · 不截首行）
        "含\r回车",  # 含 CR
        "问" * 513,  # strip 后 >512 字符
    ],
)
async def test_tc9_invalid_output_fallback(monkeypatch: pytest.MonkeyPatch, bad: str):
    monkeypatch.setenv("LG_RAG_QUERY_REWRITE_ENABLED", "true")
    provider = _FakeProvider(text=bad)
    obs = _patch_face(monkeypatch, provider)
    out = await query_rewrite.maybe_rewrite_query("它现在恢复了吗", _HISTORY)
    assert out == "它现在恢复了吗"
    assert obs["spans"] == [{"query_rewrite_applied": False, "query_rewrite_fallback": True}]


async def test_tc9_exactly_512_chars_accepted(monkeypatch: pytest.MonkeyPatch):
    """恰 512 字符接受（边界含等号 · >512 才拒）。"""
    monkeypatch.setenv("LG_RAG_QUERY_REWRITE_ENABLED", "true")
    good = "问" * 512
    provider = _FakeProvider(text=good)
    obs = _patch_face(monkeypatch, provider)
    out = await query_rewrite.maybe_rewrite_query("它现在恢复了吗", _HISTORY)
    assert out == good
    assert obs["spans"] == [
        {
            "query_rewrite_applied": True,
            "query_rewrite_src_len": len("它现在恢复了吗"),
            "query_rewrite_dst_len": 512,
        }
    ]


async def test_tc9_padded_output_stripped_and_accepted(monkeypatch: pytest.MonkeyPatch):
    """合法输出前后空白 strip 后接受（strip 是规范化不是判非法）。"""
    monkeypatch.setenv("LG_RAG_QUERY_REWRITE_ENABLED", "true")
    provider = _FakeProvider(text="  支付网关现在恢复了吗  ")
    _patch_face(monkeypatch, provider)
    out = await query_rewrite.maybe_rewrite_query("它现在恢复了吗", _HISTORY)
    assert out == "支付网关现在恢复了吗"
