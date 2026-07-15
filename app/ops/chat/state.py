"""ChatState definition for LangGraph."""
from operator import add
from typing import Annotated, TypedDict


class ChatState(TypedDict):
    """LangGraph state for chat."""

    query: str
    session_id: str | None
    run_id: str
    issue_context: list[dict]
    pr_context: list[dict]
    graph_context: dict | None
    intent: str
    answer: str
    events: Annotated[list[dict], add]
