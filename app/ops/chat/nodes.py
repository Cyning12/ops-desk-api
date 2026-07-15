"""LangGraph nodes for chat."""
import re

from app.ops.chat.state import ChatState


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


async def load_issue_context_node(state: ChatState) -> dict:
    """Load issue context by issue number."""
    # TODO: query ops_issues from DB
    match = re.search(r"#(\d+)", state["query"])
    issue_number = int(match.group(1)) if match else None
    issue: dict | None = None

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
                    "summary": issue["title"] if issue else "未找到",
                },
            }
        ],
    }


async def answer_node(state: ChatState) -> dict:
    """Generate final answer via LLM."""
    # TODO: integrate provider.complete_stream()
    return {
        "answer": "",
        "events": [
            {
                "event_type": "thinking",
                "agent_role": "answer",
                "payload": {"content": "准备生成回答...", "step": "answer"},
            }
        ],
    }
