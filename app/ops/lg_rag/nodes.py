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

import logging
import os
import re

from langchain_core.messages import AIMessage, BaseMessage

from app.llm.factory import get_llm_provider
from app.llm.schema import LlmMessage
from app.ops.lc_evidence_chain.chain import ainvoke_evidence_answer
from app.ops.lg_rag.state import LgRagState
from app.ops.rag.grader import REFUSAL_TEXT
from app.ops.structured_output import parse_only
from app.ops.structured_output.schemas import RouteDecision
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
    '- {"route": "direct"}：与助手自身的闲聊、问候、身份/能力元问题，不需要查知识库；\n'
    '- {"route": "refuse"}：明确要求泄密、违法、或与运维知识库完全无关且不应回答的内容。\n'
    "注意：凡涉及产品/项目功能、用法、配置、故障的问题（包括「有没有某功能」"
    "「怎么做到某事」），一律选 rag，不要选 direct。\n"
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
    """解析 router LLM 输出；Gateway parse_only + 历史宽容路径。

    选型：``_classify_route`` 已 ``complete`` 一次，此处仅 ``parse_only``，
    避免 ``acomplete_structured`` 双重 LLM。

    历史宽容：抽不出合法 ``{"route": ...}`` 时，仍接受文本中出现的
    ``"rag"|"direct"|"refuse"`` 字面量（勿无故收紧致误 fallback 暴增）。
    """
    outcome = parse_only(raw, schema=RouteDecision)
    if outcome.ok and outcome.data is not None:
        return outcome.data.route

    # 非 JSON / 非对象：保留改前 regex 宽容路径
    text = (raw or "").strip()
    m = re.search(r'"(rag|direct|refuse)"', text)
    if m:
        return m.group(1)
    return None


async def _classify_route(query: str) -> tuple[str, str, bool]:
    """LLM 三分类。返回 (route, raw_output, used_fallback)。

    complete 一次 + parse_only（见 ``_parse_route`` 选型注释）。
    """
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
    """router 决策写入当前 span metadata（DESIGN §6 / SPEC §5）。"""
    if not tracing_enabled():
        return
    try:
        from langfuse import get_client

        get_client().update_current_span(
            metadata={
                "route": route,
                "router_fallback": fallback,
                # 与 router_fallback 并存；结构化出口失败/LLM 异常均标 true
                "structured_output_fallback": fallback,
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


_META_KEYS = ("gate_action", "hit_count", "kept_count", "best_relevance", "grade_count")

MAX_RETRIES = int(os.getenv("LG_RAG_MAX_RETRIES", "2"))


async def rag_node(state: LgRagState) -> dict:
    """黑盒 RAG：LCEL evidence chain → 追加一条 AIMessage + 写回 chain_meta。

    messages 走 add_messages reducer，返回「增量」列表即可，
    不要手写全量覆盖。ChainResult 为 Pydantic：用 .answer；
    勿写成 result["answer"]。
    Phase 3：优先取 current_query（rewrite 产物）；写回 chain_meta
    质量信号子集供 evaluate_node 判定（evidence 本体不进 state）。
    """
    query = state.get("current_query") or _last_user_text(state["messages"])
    result = await ainvoke_evidence_answer(query)
    chain_meta = {k: result.meta[k] for k in _META_KEYS if k in result.meta}
    return {
        "messages": [AIMessage(content=result.answer or "")],
        "chain_meta": chain_meta,
    }


def _judge_quality(chain_meta: dict | None) -> str:
    """复用 chain gate 结论的确定性映射（DESIGN §3，零额外 LLM）。"""
    if not chain_meta:
        return "high"  # 安全默认：无信号不回环
    gate = str(chain_meta.get("gate_action") or "")
    if gate == "answer_partial":
        return "medium"
    if gate == "refuse" or not chain_meta.get("kept_count"):
        return "low"
    return "high"


async def evaluate_node(state: LgRagState) -> dict:
    """评估检索质量：high/medium→END；low 且未达熔断→rewrite。"""
    meta = state.get("chain_meta") or {}
    quality = _judge_quality(meta)
    retry_count = state.get("retry_count") or 0
    if tracing_enabled():
        try:
            from langfuse import get_client

            get_client().update_current_span(
                metadata={
                    "quality": quality,
                    "retry_count": retry_count,
                    **{k: meta.get(k) for k in _META_KEYS if k in meta},
                }
            )
        except Exception:  # 观测失败不挡主流程
            pass
    return {}


def route_by_quality(state: LgRagState) -> str:
    """evaluate 后的条件边：low 且 retry_count < MAX_RETRIES → rewrite，否则 END。"""
    quality = _judge_quality(state.get("chain_meta") or {})
    if quality == "low" and (state.get("retry_count") or 0) < MAX_RETRIES:
        return "rewrite"
    return "end"


_REWRITE_SYSTEM = (
    "你是检索查询改写器。用户的问题在运维知识库中没有检索到足够证据。"
    "知识库为 GitHub issue/PR 文档（中英混排），全文包裹的长句检索效果差。"
    "请把问题改写为**核心可检索关键词组合**："
    "保留函数名 / 错误码 / 组件名 / issue 编号等精确词，去掉叙述性包裹，"
    "可中英混合；复合问题保留各侧面的关键词。"
    "只输出关键词组合（单行），不要输出完整句子，不要解释。"
)


async def rewrite_node(state: LgRagState) -> dict:
    """LLM 单查询改写（DESIGN §4）。

    熔断语义：LLM 失败 / 空输出 / 与原 query 相同 → 清空 current_query
    并把 retry_count 顶到上限，route_after_rewrite 随之导向 END。
    """
    original = state.get("current_query") or _last_user_text(state["messages"])
    retry_count = state.get("retry_count") or 0
    provider = get_llm_provider(_ROUTER_PROVIDER)
    with trace_span("rewrite", run_type="chain"):
        try:
            raw = await provider.complete(
                [
                    LlmMessage(role="system", content=_REWRITE_SYSTEM),
                    LlmMessage(role="user", content=original),
                ],
                model=_ROUTER_MODEL,
            )
            new_query = (raw or "").strip().splitlines()[0].strip()
        except Exception as exc:
            logger.warning("lg_rag rewrite LLM 失败，终止回环 err=%r", exc)
            new_query = ""
    if not new_query or new_query == original:
        return {"current_query": "", "retry_count": MAX_RETRIES}
    if tracing_enabled():
        try:
            from langfuse import get_client

            get_client().update_current_span(
                metadata={
                    "rewrite_from": original[:200],
                    "rewrite_to": new_query[:200],
                    "retry_count": retry_count + 1,
                }
            )
        except Exception:
            pass
    return {"current_query": new_query, "retry_count": retry_count + 1}


def route_after_rewrite(state: LgRagState) -> str:
    """rewrite 后的条件边：有新 query → rag 重试；熔断置空 → END。"""
    return "rag" if state.get("current_query") else "end"


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
