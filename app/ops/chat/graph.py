"""LangGraph StateGraph 编译：装配 Chat 节点与边，供 service 侧 graph.astream 消费。

拓扑（简化）：
  START → detect_intent
            ├─ issue_qa  → load_context → generate_answer → END
            └─ general / overview → retrieve → grade ─┬─ refuse → refuse_answer → END
                                                    └─ answer/answer_partial → generate_answer → END
"""

from langgraph.graph import END, START, StateGraph

from app.ops.chat.nodes import (
    answer_node,
    intent_node,
    load_issue_context_node,
    route_by_intent,
)
from app.ops.chat.rag_nodes import (
    grade_node,
    refuse_node,
    retrieve_node,
    route_by_gate,
)
from app.ops.chat.state import ChatState

# 以 ChatState 为共享状态；各节点返回的 dict 会 merge 回 state
builder = StateGraph(ChatState)

# 注册节点（名称供边引用；实现见 nodes.py）
builder.add_node("detect_intent", intent_node)
builder.add_node("load_context", load_issue_context_node)
builder.add_node("generate_answer", answer_node)
builder.add_node("retrieve", retrieve_node)
builder.add_node("grade", grade_node)
builder.add_node("refuse_answer", refuse_node)

# 固定边：入口始终先做意图识别
builder.add_edge(START, "detect_intent")

# 条件边：route_by_intent 返回 intent 字符串，映射到下一节点名
builder.add_conditional_edges(
    "detect_intent",
    route_by_intent,
    {
        "issue_qa": "load_context",  # 含 #编号 → 先查 issue 再回答
        "general": "retrieve",  # 知识候选 → 检索链（2026-08-10 人定）
        "overview": "retrieve",
    },
)
builder.add_edge("load_context", "generate_answer")
builder.add_edge("retrieve", "grade")
builder.add_conditional_edges(
    "grade",
    route_by_gate,
    {
        "refuse": "refuse_answer",
        "generate_answer": "generate_answer",
    },
)
builder.add_edge("refuse_answer", END)
builder.add_edge("generate_answer", END)

# 编译为可执行图；模块级单例，由 service 导入使用
graph = builder.compile()
