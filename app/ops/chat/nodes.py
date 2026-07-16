"""LangGraph nodes for chat."""
import re

from sqlalchemy import select

from app.config import settings
from app.db.models import OpsIssue
from app.db.session import AsyncSessionLocal
from app.llm.factory import get_llm_provider
from app.llm.schema import LlmProviderError
from app.ops.chat.state import ChatState

_SYSTEM_PROMPT = (
    "你是 Ops Desk 助手，帮助用户理解 GitHub 仓库中的 issue、PR 和代码图谱。"
    "回答要简洁、准确，优先基于提供的上下文。"
)


async def intent_node(state: ChatState) -> dict:
    """Route user intent."""
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
    """Conditional edge routing."""
    return state["intent"]


async def _fetch_issue_by_number(number: int) -> dict | None:
    """Load an issue from the database by its GitHub number."""
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
    """Load issue context by issue number."""
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


def _build_messages(state: ChatState) -> list[dict]:
    """Build OpenAI-compatible messages from state."""
    messages = [{"role": "system", "content": _SYSTEM_PROMPT}]

    issue_context = state.get("issue_context") or []
    if issue_context:
        issue = issue_context[0]
        body = (issue.get("body") or "")[:2000]
        context_text = f"相关 issue #{issue.get('number')}：\n标题：{issue.get('title')}\n{body}"
        messages.append({"role": "user", "content": context_text})

    messages.append({"role": "user", "content": state["query"]})
    return messages


async def answer_node(state: ChatState) -> dict:
    """Generate final answer via LLM."""
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
        async for chunk in provider.complete_stream(messages, model=model):
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
