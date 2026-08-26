"""lg_rag Phase 4 · Multi-Agent 节点（supervisor / 三专业 agent / aggregator）。

说明书：docs/guides/DESIGN_langgraph-lg-rag-phase4-multiagent_v1.md §3–§5。

原则：
- supervisor 拆解失败/非法 → fallback 单 rag 子任务（宁退化不失败）；
- 子任务按序执行，结果追加到 subtask_results（不进 messages）；
- 单个子任务异常 → 记录错误结果并继续后续子任务；
- dispatch 以 len(subtask_results) 作推进索引，每个 agent 节点必追加
  恰好一条结果（含错误结果），保证索引单调推进、无死循环。
"""

from __future__ import annotations

import json
import logging

from langchain_core.messages import AIMessage
from pydantic import ValidationError

from app.llm.factory import get_llm_provider
from app.llm.schema import LlmMessage
from app.ops.capability import invoke as capability_invoke
from app.ops.lg_rag.graph import ainvoke_router_agent
from app.ops.lg_rag.nodes import (
    _ROUTER_MODEL,
    _ROUTER_PROVIDER,
    _last_user_text,
)
from app.ops.lg_rag.state import LgRagState
from app.ops.structured_output import parse_only
from app.ops.structured_output.schemas import ExtractResult, SubtaskItem, SubtasksPlan
from app.ops.tracing import trace_span, tracing_enabled

logger = logging.getLogger(__name__)

SUBTASK_TYPES = ("rag", "extract", "tool")
MAX_SUBTASKS = 4  # cap=4，超出截断（DESIGN §3）

# 子任务 type → 条件边目标节点
_TYPE_TO_NODE = {
    "rag": "rag_subtask",
    "extract": "info_extract",
    "tool": "tool_exec",
}

_SUPERVISOR_SYSTEM = (
    "你是 Ops Desk 运维知识库助手的任务拆解器（Supervisor）。"
    "把用户的复合问题拆解为若干个子任务，只输出 JSON：\n"
    '{"subtasks": [{"id": "t1", "type": "rag|extract|tool", "input": "...", "tool": "..."}]}\n'
    "- type=rag：需要查运维知识库的问题，input 为该子问题的完整问句；\n"
    "- type=extract：需要从文本中抽取日期/版本号/人物，input 为待抽取文本；\n"
    "- type=tool：需要调用工具查询，tool 为工具名"
    "（可用：mock_get_issue_status / mock_get_deploy_info），input 为工具入参描述；\n"
    "- 子任务最多 4 个，按执行顺序排列；单一简单问题就只给一个 rag 子任务。\n"
    "只输出一个 JSON 对象，不要输出其他文字。"
)

_EXTRACT_SYSTEM = (
    "你是信息抽取器。从用户给出的文本中抽取结构化信息，只输出 JSON：\n"
    '{"dates": ["..."], "versions": ["..."], "people": ["..."]}\n'
    "- dates：出现的日期/时间点（原文表述）；\n"
    "- versions：出现的版本号（如 v1.2.3、2.0）；\n"
    "- people：出现的人名/负责人。\n"
    "没有的类别给空数组。只输出一个 JSON 对象，不要输出其他文字。"
)

_AGGREGATOR_SYSTEM = (
    "你是 Ops Desk 运维知识库助手的答案综合器（Aggregator）。"
    "用户提出了一个复合问题，各子任务的执行结果以 JSON 形式给出"
    "（含 type/input/output 或 error）。请综合全部子任务结果，"
    "输出结构化 markdown 答案：\n"
    "1. 按子任务分节，每节标注来源"
    "（rag 检索 / 信息抽取 / 工具查询，失败子任务如实说明）；\n"
    "2. 末尾给一节「综合结论」，串联各子任务结果回答原始问题。\n"
    "不要编造子任务结果中没有的事实。"
)

# Mock 工具已迁入 Capability Gateway（app.ops.capability.defaults）；
# tool_exec_node 主路径改调 capability_invoke，不再维护裸 MOCK_TOOLS 字典。


# ---------------------------------------------------------------------------
# 解析与元数据辅助
# ---------------------------------------------------------------------------


def _parse_subtasks(raw: str) -> list[dict] | None:
    """解析 supervisor LLM 输出为子任务列表；非法/为空返回 None（走 fallback）。

    选型：``supervisor_node`` 已 ``complete`` 一次，此处仅 ``parse_only``，
    避免 ``acomplete_structured`` 双重 LLM（延迟敏感；纠偏留给后续波次）。

    逐项规整：缺 id 补 tN；type 不在白名单归为 rag（宁退化）；input 非空
    字符串必填（schema + strip），任一项 input 缺失/空白视整体非法；超过
    cap=4 截断（cap 外项不参与校验，避免误 fallback）。
    """
    outcome = parse_only(raw, schema=SubtasksPlan)
    if not outcome.ok or outcome.data is None:
        return None
    items = outcome.data.subtasks
    subtasks: list[dict] = []
    for i, raw_item in enumerate(items[:MAX_SUBTASKS]):
        try:
            item = SubtaskItem.model_validate(raw_item)
        except ValidationError:
            return None
        text = (item.input or "").strip()
        if not text:
            return None
        subtask_type = (item.type or "").strip()
        if subtask_type not in SUBTASK_TYPES:
            subtask_type = "rag"
        subtask = {
            "id": str(item.id or f"t{i + 1}"),
            "type": subtask_type,
            "input": text,
        }
        if subtask_type == "tool" and item.tool:
            subtask["tool"] = str(item.tool)
        subtasks.append(subtask)
    return subtasks or None


def _record_span_metadata(metadata: dict) -> None:
    """决策写入当前 span metadata（DESIGN §6；观测失败不挡主流程）。"""
    if not tracing_enabled():
        return
    try:
        from langfuse import get_client

        get_client().update_current_span(metadata=metadata)
    except Exception:
        pass


def _pending_subtask(state: LgRagState) -> dict | None:
    """按推进索引取当前待执行子任务（结果与子任务按序一一对应）。"""
    subtasks = state.get("subtasks") or []
    results = state.get("subtask_results") or []
    idx = len(results)
    return subtasks[idx] if idx < len(subtasks) else None


# ---------------------------------------------------------------------------
# Supervisor（DESIGN §3）
# ---------------------------------------------------------------------------


async def supervisor_node(state: LgRagState) -> dict:
    """LLM 拆解复合问题为 ≤4 子任务；失败/非法 → fallback 单 rag 子任务。

    选型：complete 一次 + ``parse_only``（见 ``_parse_subtasks``），
    不用 ``acomplete_structured`` 以免本波双重 LLM。
    """
    query = _last_user_text(state["messages"])
    raw = ""
    subtasks: list[dict] | None = None
    with trace_span("supervisor", run_type="chain"):
        try:
            provider = get_llm_provider(_ROUTER_PROVIDER)
            raw = await provider.complete(
                [
                    LlmMessage(role="system", content=_SUPERVISOR_SYSTEM),
                    LlmMessage(role="user", content=query),
                ],
                model=_ROUTER_MODEL,
            )
            subtasks = _parse_subtasks(raw)
        except Exception as exc:  # LLM 异常/超时 → 宁退化不失败
            logger.warning("lg_rag supervisor LLM 失败，fallback 单 rag err=%r", exc)
    fallback = subtasks is None
    if fallback:
        if raw:
            logger.warning(
                "lg_rag supervisor 输出非法，fallback 单 rag raw=%r", raw[:200]
            )
        subtasks = [{"id": "t1", "type": "rag", "input": query}]
    _record_span_metadata(
        {
            "subtask_count": len(subtasks),
            "subtask_types": [s["type"] for s in subtasks],
            "supervisor_fallback": fallback,
            # 与 supervisor_fallback 并存（SPEC §5）
            "structured_output_fallback": fallback,
            "supervisor_raw": raw[:200],
        }
    )
    return {"subtasks": subtasks}


def route_next_subtask(state: LgRagState) -> str:
    """dispatch 条件边：取下一子任务按 type 分派；耗尽/空 subtasks → aggregate。

    防死循环：len(subtask_results) >= len(subtasks) 即耗尽（含空列表），
    且每个 agent 节点必追加恰好一条结果，索引单调推进。
    """
    subtask = _pending_subtask(state)
    if subtask is None:
        return "aggregate"
    return _TYPE_TO_NODE.get(str(subtask.get("type") or ""), "rag_subtask")


# ---------------------------------------------------------------------------
# 三个专业 Agent（DESIGN §4）
# ---------------------------------------------------------------------------


def _base_result(subtask: dict) -> dict:
    return {
        "id": str(subtask.get("id") or ""),
        "type": str(subtask.get("type") or ""),
        "input": str(subtask.get("input") or ""),
    }


async def rag_subtask_node(state: LgRagState) -> dict:
    """RAG 子任务：内部调 ainvoke_router_agent（复用 Phase 2/3 全能力）。

    子图输入隔离：fresh messages 仅含本子任务 input，不污染父历史；
    结果 = 末条 AIMessage + chain_meta 摘要。异常 → 错误结果不中断。
    """
    subtask = _pending_subtask(state)
    if subtask is None:  # 防御：dispatch 保证不会发生；追加错误结果保推进
        return {"subtask_results": [{"type": "rag", "error": "no pending subtask"}]}
    result = _base_result(subtask)
    with trace_span("rag_subtask", run_type="chain"):
        try:
            out = await ainvoke_router_agent(
                result["input"],
                thread_id=f"lg-rag-subtask-{result['id'] or 'x'}",
            )
            answer = ""
            for m in reversed(out.get("messages") or []):
                if getattr(m, "type", None) == "ai":
                    content = m.content
                    answer = content if isinstance(content, str) else str(content)
                    break
            result["output"] = answer
            result["chain_meta"] = out.get("chain_meta") or {}
        except Exception as exc:
            logger.warning("lg_rag rag 子任务失败 id=%s err=%r", result["id"], exc)
            result["error"] = repr(exc)
    return {"subtask_results": [result]}


def _empty_extract() -> dict:
    return {"dates": [], "versions": [], "people": []}


async def info_extract_node(state: LgRagState) -> dict:
    """信息抽取子任务：LLM 从输入文本抽 dates/versions/people JSON。

    选型：complete 一次 + ``parse_only``，避免双重 LLM。
    非法 JSON / schema 失败 → 空结构 + warning + structured_output_fallback，
    不中断（DESIGN §8 / SPEC §5）。
    """
    subtask = _pending_subtask(state)
    if subtask is None:
        return {"subtask_results": [{"type": "extract", "error": "no pending subtask"}]}
    result = _base_result(subtask)
    with trace_span("info_extract", run_type="chain"):
        try:
            provider = get_llm_provider(_ROUTER_PROVIDER)
            raw = await provider.complete(
                [
                    LlmMessage(role="system", content=_EXTRACT_SYSTEM),
                    LlmMessage(role="user", content=result["input"]),
                ],
                model=_ROUTER_MODEL,
            )
        except Exception as exc:
            logger.warning("lg_rag extract LLM 失败 id=%s err=%r", result["id"], exc)
            result["output"] = _empty_extract()
            result["error"] = repr(exc)
            _record_span_metadata({"structured_output_fallback": True})
            return {"subtask_results": [result]}
        outcome = parse_only(raw, schema=ExtractResult)
        if not outcome.ok or outcome.data is None:
            logger.warning("lg_rag extract 输出非法，置空结构 raw=%r", (raw or "")[:200])
            result["output"] = _empty_extract()
            _record_span_metadata({"structured_output_fallback": True})
        else:
            result["output"] = outcome.data.model_dump()
            _record_span_metadata({"structured_output_fallback": False})
    return {"subtask_results": [result]}


async def tool_exec_node(state: LgRagState) -> dict:
    """工具子任务：经 Capability Gateway invoke；未知 id → 错误结果不中断。

    观测：复用 ``trace_span("tool_exec")``；Gateway 向当前 span 写
    capability_id / kind / ok / error 截断（SPEC §5），不另开根 span。
    """
    subtask = _pending_subtask(state)
    if subtask is None:
        return {"subtask_results": [{"type": "tool", "error": "no pending subtask"}]}
    result = _base_result(subtask)
    tool_name = str(subtask.get("tool") or "")
    with trace_span("tool_exec", run_type="tool"):
        cap = capability_invoke(tool_name, result["input"])
        if not cap.ok:
            logger.warning(
                "lg_rag 工具失败 tool=%r id=%s err=%r",
                tool_name,
                result["id"],
                cap.error,
            )
            result["error"] = cap.error or f"未知工具: {tool_name or '(未指定)'}"
        else:
            result["output"] = cap.output
    return {"subtask_results": [result]}


# ---------------------------------------------------------------------------
# Aggregator（DESIGN §5）
# ---------------------------------------------------------------------------


async def aggregator_node(state: LgRagState) -> dict:
    """LLM 综合全部 subtask_results → 分节结构化 markdown，追加最终 AIMessage。

    中间结果只在 subtask_results，不进 messages；LLM 失败异常上抛
    （与全站一致，DESIGN §8）。
    """
    query = _last_user_text(state["messages"])
    results = state.get("subtask_results") or []
    payload = json.dumps(results, ensure_ascii=False, default=str)
    provider = get_llm_provider(_ROUTER_PROVIDER)
    with trace_span("aggregator", run_type="chain"):
        text = await provider.complete(
            [
                LlmMessage(role="system", content=_AGGREGATOR_SYSTEM),
                LlmMessage(
                    role="user",
                    content=f"原始问题：{query}\n子任务结果：{payload}",
                ),
            ],
            model=_ROUTER_MODEL,
        )
    answer = (text or "").strip()
    if not answer:
        logger.warning("lg_rag aggregator 空输出，回退拼接子任务结果")
        answer = (
            "\n\n".join(
                f"## 子任务 {r.get('id') or i + 1}\n"
                f"{r.get('output') or r.get('error') or '(无输出)'}"
                for i, r in enumerate(results)
            )
            or "（无子任务结果）"
        )
    return {"messages": [AIMessage(content=answer)]}
