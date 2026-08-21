"""lg_rag 节点（Phase 1 rag_node + Phase 2 router 三路分流）。

说明书：
- Phase 1：docs/guides/IMPL_langgraph-lg-rag-phase1_v1.md S2
- Phase 2：docs/guides/DESIGN_langgraph-lg-rag-phase2-router_v1.md §4/§5

原则：
- rag_node 只黑盒调用 ainvoke_evidence_answer；
- router 故障 fallback="rag"（宁检索勿错杀）；
- messages 走 add_messages reducer，节点返回增量列表。
"""

from __future__ import annotations

import json
import logging
import os
import re

from langchain_core.messages import AIMessage, BaseMessage

from app.llm.factory import get_llm_provider
from app.llm.schema import LlmMessage
from app.ops.lc_evidence_chain.chain import ainvoke_evidence_answer
from app.ops.lg_rag.state import LgRagState
from app.ops.rag.grader import REFUSAL_TEXT
from app.ops.tracing import trace_span, tracing_enabled

logger = logging.getLogger(__name__)

# 与 grader 同档小模型（DESIGN §4）；可用 LG_RAG_ROUTER_* 独立覆盖
_ROUTER_PROVIDER = os.getenv("LG_RAG_ROUTER_PROVIDER") or os.getenv(
    "RAG_GRADER_PROVIDER", "bailian"
)
_ROUTER_MODEL = os.getenv("LG_RAG_ROUTER_MODEL") or os.getenv(
    "RAG_GRADER_MODEL", "qwen3.7-flash"
)

ROUTES = ("rag", "direct", "refuse")
DEFAULT_ROUTE = "rag"  # fallback：宁检索勿错杀（DESIGN §4）

_ISSUE_NO_RE = re.compile(r"#\d+")

_ROUTER_SYSTEM = (
    "你是 Ops Desk 运维知识库助手的意图分类器。把用户问题分为三类，只输出 JSON：\n"
    '- {"route": "rag"}：与项目/运维/issue/PR/故障相关的技术问题，需要查知识库；\n'
    '- {"route": "direct"}：闲聊、问候、身份/能力等元问题，不需要查知识库；\n'
    '- {"route": "refuse"}：明确要求泄密、违法、或与运维知识库完全无关且不应回答的内容。\n'
    "只输出一个 JSON 对象，不要输出其他文字。"
)

_DIRECT_SYSTEM = (
    "你是 Ops Desk 运维知识库助手。用户在进行闲聊或元问题对话。"
    "用一两句话简短友好地回答，并自然地把话题引回运维知识库可以帮忙的方向。"
    "不要编造项目事实；不知道就说不知道。"
)


def _last_user_text(messages: list[BaseMessage]) -> str:
    for m in reversed(messages):
        if getattr(m, "type", None) == "human" or m.__class__.__name__ == "HumanMessage":
            content = m.content
            return content if isinstance(content, str) else str(content)
    raise ValueError("messages 中无 HumanMessage")


def _parse_route(raw: str) -> str | None:
    """解析 router LLM 输出；宽容提取 JSON，白名单校验。"""
    text = (raw or "").strip()
    value = ""
    try:
        data = json.loads(text)
        if isinstance(data, dict):
            value = str(data.get("route") or "").strip()
    except (json.JSONDecodeError, TypeError):
        m = re.search(r'"(rag|direct|refuse)"', text)
        if m:
            value = m.group(1)
    return value if value in ROUTES else None


async def _classify_route(query: str) -> tuple[str, str, bool]:
    """LLM 三分类。返回 (route, raw_output, used_fallback)。"""
    provider = get_llm_provider(_ROUTER_PROVIDER)
    raw = await provider.complete(
        [
            LlmMessage(role="system", content=_ROUTER_SYSTEM),
            LlmMessage(role="user", content=query),
        ],
        model=_ROUTER_MODEL,
    )
    route = _parse_route(raw)
    if route is None:
        logger.warning(
            "lg_rag router 输出非法，fallback=%s raw=%r", DEFAULT_ROUTE, raw[:200]
        )
        return DEFAULT_ROUTE, raw, True
    return route, raw, False


def _record_route_metadata(*, route: str, raw: str, fallback: bool) -> None:
    """router 决策写入当前 span metadata（DESIGN §6）。"""
    if not tracing_enabled():
        return
    try:
        from langfuse import get_client

        get_client().update_current_span(
            metadata={
                "route": route,
                "router_fallback": fallback,
                "router_raw": raw[:200],
            }
        )
    except Exception:  # SDK 可选；观测失败不挡主流程
        pass


async def router_node(state: LgRagState) -> dict:
    """意图路由：#数字快路径→rag；否则 LLM 三分类；故障 fallback=rag。"""
    query = _last_user_text(state["messages"])
    if _ISSUE_NO_RE.search(query):
        route, raw, fallback = "rag", "rule:#issue-no", False
    else:
        with trace_span("router", run_type="chain"):
            try:
                route, raw, fallback = await _classify_route(query)
            except Exception as exc:  # LLM 异常/超时 → 宁检索勿错杀
                logger.warning(
                    "lg_rag router LLM 失败，fallback=%s err=%r", DEFAULT_ROUTE, exc
                )
                route, raw, fallback = DEFAULT_ROUTE, "", True
    _record_route_metadata(route=route, raw=raw, fallback=fallback)
    return {"route": route}


def route_by_route(state: LgRagState) -> str:
    """条件边回调：老 checkpoint 无 route 键时缺省 rag。"""
    route = state.get("route") or DEFAULT_ROUTE
    return route if route in ROUTES else DEFAULT_ROUTE


async def rag_node(state: LgRagState) -> dict:
    """黑盒 RAG：LCEL evidence chain → 追加一条 AIMessage。

    messages 走 add_messages reducer，返回「增量」列表即可，
    不要手写全量覆盖。ChainResult 为 Pydantic：用 .answer；
    勿写成 result["answer"]。
    """
    query = _last_user_text(state["messages"])
    result = await ainvoke_evidence_answer(query)
    return {"messages": [AIMessage(content=result.answer or "")]}


async def direct_answer_node(state: LgRagState) -> dict:
    """闲聊直答：LLM 一两句话，不检索不读库（DESIGN §5）。"""
    query = _last_user_text(state["messages"])
    provider = get_llm_provider(_ROUTER_PROVIDER)
    with trace_span("direct_answer", run_type="chain"):
        text = await provider.complete(
            [
                LlmMessage(role="system", content=_DIRECT_SYSTEM),
                LlmMessage(role="user", content=query),
            ],
            model=_ROUTER_MODEL,
        )
    answer = (text or "").strip() or "你好，我是 Ops Desk 运维知识库助手，有运维问题可以问我。"
    return {"messages": [AIMessage(content=answer)]}


async def refuse_node(state: LgRagState) -> dict:  # noqa: ARG001
    """越界拒答：固定文案（与 Chat 同源 REFUSAL_TEXT，防文案漂移）。"""
    return {"messages": [AIMessage(content=REFUSAL_TEXT)]}
