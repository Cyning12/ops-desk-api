"""Chat service glue between graph and persistence."""
from collections.abc import AsyncIterator
from contextlib import nullcontext

from app.ops.chat.graph import graph
from app.ops.chat.state import ChatState
from app.ops.tracing import ensure_langfuse_environment, trace_span, tracing_enabled


def _trace_config(state: ChatState) -> dict | None:
    """Langfuse LangChain 集成：官方 CallbackHandler 自动产出图/节点 span。

    session/tags 经 config metadata 传递（官方字段名 langfuse_*）；
    未开启 tracing 时返回 None，零依赖零成本。
    """
    if not tracing_enabled():
        return None
    ensure_langfuse_environment()
    from langfuse.langchain import CallbackHandler  # 延迟导入：SDK 为可选依赖

    metadata: dict = {"langfuse_tags": ["ops-chat"]}
    if state.get("session_id"):
        metadata["langfuse_session_id"] = state["session_id"]
    return {
        "callbacks": [CallbackHandler()],
        "metadata": metadata,
        "run_name": "ops-chat",
    }


async def run_chat_stream(state: ChatState) -> AsyncIterator[dict]:
    """Async generator over graph events formatted for SSE emission."""
    try:
        # 仅在 tracing 开启时传 config（保持无追踪路径调用签名不变）
        astream_kwargs: dict = {"stream_mode": "updates"}
        if config := _trace_config(state):
            astream_kwargs["config"] = config
        # 根 span：手工 grade_llm / answer_llm 才能挂到同一调用链（否则各成单节点 trace）
        span_cm = (
            trace_span("ops-chat", run_type="chain", tags=["ops-chat"])
            if tracing_enabled()
            else nullcontext()
        )
        with span_cm:
            async for node_update in graph.astream(state, **astream_kwargs):
                for node_name, node_output in node_update.items():
                    if not isinstance(node_output, dict):
                        continue
                    for event in node_output.get("events", []) or []:
                        if not isinstance(event, dict):
                            continue
                        yield {
                            "event_type": event.get("event_type", "unknown"),
                            "agent_role": event.get("agent_role", node_name),
                            "payload": event.get("payload", {}),
                        }
    except Exception as exc:
        yield {
            "event_type": "error",
            "agent_role": "system",
            "payload": {"stage": "graph", "message": str(exc), "retryable": False},
        }
