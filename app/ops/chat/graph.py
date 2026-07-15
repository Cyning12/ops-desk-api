"""LangGraph StateGraph compilation."""
from langgraph.graph import END, START, StateGraph

from app.ops.chat.nodes import (
    answer_node,
    intent_node,
    load_issue_context_node,
    route_by_intent,
)
from app.ops.chat.state import ChatState

builder = StateGraph(ChatState)
builder.add_node("detect_intent", intent_node)
builder.add_node("load_context", load_issue_context_node)
builder.add_node("generate_answer", answer_node)

builder.add_edge(START, "detect_intent")
builder.add_conditional_edges(
    "detect_intent",
    route_by_intent,
    {"issue_qa": "load_context", "general": "generate_answer", "overview": "generate_answer"},
)
builder.add_edge("load_context", "generate_answer")
builder.add_edge("generate_answer", END)

graph = builder.compile()
