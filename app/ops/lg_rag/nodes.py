"""lg_rag 节点（Phase 1）。

说明书：docs/guides/IMPL_langgraph-lg-rag-phase1_v1.md S2。
原则：只黑盒调用 ainvoke_evidence_answer；
不复制 retrieve SQL / grader / answer prompt。
"""

from __future__ import annotations

from langchain_core.messages import AIMessage, BaseMessage

from app.ops.lc_evidence_chain.chain import ainvoke_evidence_answer
from app.ops.lg_rag.state import LgRagState


def _last_user_text(messages: list[BaseMessage]) -> str:
    for m in reversed(messages):
        if getattr(m, "type", None) == "human" or m.__class__.__name__ == "HumanMessage":
            content = m.content
            return content if isinstance(content, str) else str(content)
    raise ValueError("messages 中无 HumanMessage")


async def rag_node(state: LgRagState) -> dict:
    """黑盒 RAG：LCEL evidence chain → 追加一条 AIMessage。

    messages 走 add_messages reducer，返回「增量」列表即可，
    不要手写全量覆盖。ChainResult 为 Pydantic：用 .answer；
    勿写成 result["answer"]。
    """
    query = _last_user_text(state["messages"])
    result = await ainvoke_evidence_answer(query)
    return {"messages": [AIMessage(content=result.answer or "")]}
