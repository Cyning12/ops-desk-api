"""SSE event formatting utilities."""
import json


def make_sse_event(event: dict) -> str:
    """Format a chat run event dict as a single SSE message."""
    return (
        f"event: {event['event_type']}\n"
        f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
    )
