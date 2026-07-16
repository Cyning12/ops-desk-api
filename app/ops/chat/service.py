"""Chat service glue between graph and persistence."""
from collections.abc import AsyncIterator

from app.ops.chat.graph import graph
from app.ops.chat.state import ChatState


async def run_chat_stream(state: ChatState) -> AsyncIterator[dict]:
    """Async generator over graph events formatted for SSE emission."""
    try:
        async for node_update in graph.astream(state, stream_mode="updates"):
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
