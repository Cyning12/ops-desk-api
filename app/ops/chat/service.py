"""Chat service glue between graph and persistence."""
from app.ops.chat.graph import graph
from app.ops.chat.state import ChatState


async def run_chat_stream(state: ChatState):
    """Async generator over graph events formatted as SSE."""
    # TODO: create ops_runs record, persist events in background
    async for event in graph.astream_events(state, version="v2"):
        yield event
