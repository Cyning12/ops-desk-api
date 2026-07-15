"""Chat SSE endpoint."""
import time
import uuid

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse

from app.config import settings
from app.ops.chat.schema import ChatModelsResponse, ChatStreamRequest
from app.ops.chat.service import run_chat_stream
from app.ops.chat.sse import make_sse_event
from app.ops.chat.state import ChatState

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/stream")
async def chat_stream(request: Request) -> StreamingResponse:
    """Stream chat response via Server-Sent Events."""
    body = await request.json()
    req = ChatStreamRequest(**body)
    run_id = str(uuid.uuid4())

    state = ChatState(
        query=req.message,
        session_id=req.session_id,
        run_id=run_id,
        issue_context=[],
        pr_context=[],
        graph_context=None,
        intent="",
        answer="",
        events=[],
    )

    async def event_generator():
        seq = 0
        started_at = time.perf_counter()

        def emit(event_type: str, agent_role: str, payload: dict) -> str:
            nonlocal seq
            seq += 1
            return make_sse_event(run_id, seq, started_at, event_type, agent_role, payload)

        yield emit("run.start", "system", {"run_id": run_id})

        try:
            async for _event in run_chat_stream(state):
                # TODO: map LangGraph events to SSE events
                pass

            yield emit(
                "done",
                "system",
                {
                    "latency_ms": int((time.perf_counter() - started_at) * 1000),
                    "model": req.model or settings.ops_llm_model,
                },
            )
        except Exception as e:
            yield emit("error", "system", {"stage": "chat", "message": str(e), "retryable": False})

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )


@router.get("/models", response_model=ChatModelsResponse)
async def list_models() -> ChatModelsResponse:
    """Return available chat models."""
    # TODO: read from model_catalog
    return ChatModelsResponse(
        provider=settings.ops_llm_provider,
        default_model=settings.ops_llm_model,
        models=[],
    )
