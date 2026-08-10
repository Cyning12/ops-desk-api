"""LangGraph Chat 节点：纯业务函数，只读/写 ChatState，不依赖 FastAPI。

约定：
- 每个节点返回「局部更新 dict」，由 LangGraph merge 进 ChatState
- events 字段带 Annotated[..., add] 累加，供 SSE/WS 流式推送
"""
import re

from sqlalchemy import select

from app.config import settings
from app.db.models import OpsIssue
from app.db.session import AsyncSessionLocal
from app.llm.factory import get_llm_provider
from app.llm.schema import LlmMessage, LlmProviderError, LlmUsage
from app.ops.chat.state import ChatState
from app.ops.rag.prefix import strip_doc_context_prefix
from app.ops.tracing import trace_span, update_current_generation_usage

_SYSTEM_PROMPT = (
    "你是 Ops Desk 助手，帮助用户理解 GitHub 仓库中的 issue、PR 和代码图谱。"
    "回答要简洁、准确，优先基于提供的上下文。"
)


async def intent_node(state: ChatState) -> dict:
    """识别用户意图，写入 state.intent，供条件边路由。

    规则（轻量启发式，非 LLM）：
    - 含 #数字 → issue_qa
    - 含「总览」/overview → overview
    - 其余 → general
    """
    query = state["query"]
    intent = "general"
    if re.search(r"#\d+", query):
        intent = "issue_qa"
    elif "总览" in query or "overview" in query.lower():
        intent = "overview"

    return {
        "intent": intent,
        "events": [
            {
                "event_type": "thinking",
                "agent_role": "intent",
                "payload": {"content": f"识别意图为 {intent}", "step": "intent"},
            }
        ],
    }


def route_by_intent(state: ChatState) -> str:
    """条件边回调：返回下一跳 key（须与 graph.add_conditional_edges 映射一致）。"""
    return state["intent"]


async def _fetch_issue_by_number(number: int) -> dict | None:
    """按 GitHub issue number 查库，返回精简 dict；未找到则 None。"""
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(OpsIssue).where(OpsIssue.number == number))
        issue = result.scalar_one_or_none()
        if issue is None:
            return None
        return {
            "number": issue.number,
            "title": issue.title,
            "body": issue.body or "",
            "state": issue.state,
            "labels": issue.labels or [],
            "module_tag": issue.module_tag,
            "html_url": issue.html_url,
        }


async def load_issue_context_node(state: ChatState) -> dict:
    """从 query 提取 #N，加载 issue 上下文到 state.issue_context。

    仅 issue_qa 路径会到达本节点；查库失败不抛出，以 tool_result 事件上报。
    """
    match = re.search(r"#(\d+)", state["query"])
    issue_number = int(match.group(1)) if match else None
    issue: dict | None = None
    summary = "未识别到 issue 编号"

    if issue_number is not None:
        try:
            issue = await _fetch_issue_by_number(issue_number)
            summary = issue["title"] if issue else "未找到"
        except Exception as exc:  # pragma: no cover - defensive; DB failures are logged by caller
            summary = f"查询失败: {exc}"

    return {
        "issue_context": [issue] if issue else [],
        "events": [
            {
                "event_type": "tool_result",
                "agent_role": "context",
                "payload": {
                    "tool": "load_issue",
                    "ok": issue is not None,
                    "issue_number": issue_number,
                    "summary": summary,
                },
            }
        ],
    }


def _build_messages(state: ChatState) -> list[LlmMessage]:
    """组装 OpenAI 兼容 messages：system + 可选 issue 上下文 + 用户 query。"""
    messages: list[LlmMessage] = [LlmMessage(role="system", content=_SYSTEM_PROMPT)]

    issue_context = state.get("issue_context") or []
    if issue_context:
        issue = issue_context[0]
        # body 截断，避免撑爆上下文窗口
        body = (issue.get("body") or "")[:2000]
        context_text = f"相关 issue #{issue.get('number')}：\n标题：{issue.get('title')}\n{body}"
        messages.append(LlmMessage(role="user", content=context_text))

    # R-3 检索链上下文（general/overview 路径）：命中块 + 引用约束（契约 4c/T13）
    retrieved = state.get("retrieved") or []
    if retrieved:
        parts = []
        for c in retrieved:
            body = strip_doc_context_prefix(c.content)[:1200]
            parts.append(f"### 资料 [{c.source_type} {c.anchor}]\n{body}")
        partial_note = (
            "\n重要：现有证据仅覆盖问题的一部分，回答开头必须注明「仅部分证据」。"
            if state.get("gate_action") == "answer_partial"
            else ""
        )
        messages.append(
            LlmMessage(
                role="user",
                content=(
                    "以下是与问题相关的资料：\n\n"
                    + "\n\n".join(parts)
                    + "\n\n回答规则：仅基于以上资料回答，资料未覆盖的内容不得编造；"
                      "引用来源用 [类型 编号] 标注（如 [issue 2720]、[doc contracts/xx.md]）。"
                    + partial_note
                ),
            )
        )

    messages.append(LlmMessage(role="user", content=state["query"]))
    return messages


async def answer_node(state: ChatState) -> dict:
    """调用 LLM 流式生成最终回答；token/fallback/error 均写入 events。"""
    provider = get_llm_provider()
    model = state.get("model") or settings.ops_llm_model
    messages = _build_messages(state)

    events: list[dict] = [
        {
            "event_type": "thinking",
            "agent_role": "answer",
            "payload": {"content": "准备生成回答...", "step": "answer"},
        }
    ]
    answer_parts: list[str] = []

    try:
        # 手动 generation 观测：自研 provider 不走 LangChain LLM 类，
        # CallbackHandler 抓不到这次调用，需显式包裹（Langfuse 技能基线：LLM 调用必须是 generation）
        with trace_span("answer_llm", run_type="llm", model=model):
            async for chunk in provider.complete_stream(messages, model=model):
                # include_usage 末帧：上报 token 用量到 generation（观测基线）
                if chunk.meta and chunk.meta.get("usage"):
                    update_current_generation_usage(
                        LlmUsage(
                            prompt_tokens=chunk.meta["usage"].get("prompt_tokens") or 0,
                            completion_tokens=chunk.meta["usage"].get("completion_tokens") or 0,
                        )
                    )
                    continue
                # Provider 可能在流中插入 fallback 元事件，与正文 chunk 分流
                if chunk.meta and chunk.meta.get("event_type") == "model.fallback":
                    events.append(
                        {
                            "event_type": "model.fallback",
                            "agent_role": "answer",
                            "payload": chunk.meta,
                        }
                    )
                else:
                    answer_parts.append(chunk.content)
                    events.append(
                        {
                            "event_type": "answer",
                            "agent_role": "answer",
                            "payload": {"content": chunk.content},
                        }
                    )
    except Exception as exc:
        retryable = isinstance(exc, LlmProviderError) and exc.retryable
        events.append(
            {
                "event_type": "error",
                "agent_role": "answer",
                "payload": {"stage": "llm", "message": str(exc), "retryable": retryable},
            }
        )

    return {"answer": "".join(answer_parts), "events": events}
