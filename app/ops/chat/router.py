"""Chat SSE endpoint."""
from __future__ import annotations

import asyncio
import logging
import time
import uuid
from collections.abc import AsyncGenerator

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db.models import OpsRun, OpsRunEvent, OpsSessionChat, OpsUser
from app.db.session import AsyncSessionLocal
from app.llm.model_catalog import get_default_model, get_models_for_provider
from app.ops.chat.schema import ChatModelsResponse, ChatStreamRequest
from app.ops.chat.service import run_chat_stream
from app.ops.chat.sse import make_sse_event
from app.ops.chat.state import ChatState
from app.ops.deps import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["chat"])

# Flush events to DB every N buffered events to keep memory bounded.
_FLUSH_BATCH_SIZE = 10
# Max wait seconds for final background flush before closing the stream.
_FINAL_FLUSH_TIMEOUT = 5.0


async def _resolve_chat_session(
    db: AsyncSession,
    session_id: str | None,
    user_id: str,
    title: str,
) -> str:
    """Validate existing chat session or create a new one."""
    if session_id:
        result = await db.execute(
            select(OpsSessionChat).where(OpsSessionChat.id == session_id)
        )
        chat_session = result.scalar_one_or_none()
        if chat_session is None or str(chat_session.user_id) != user_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Chat session not found",
            )
        return session_id

    chat_session = OpsSessionChat(user_id=user_id, title=title[:100])
    db.add(chat_session)
    await db.flush()
    return str(chat_session.id)


async def _persist_run_events(run_id: str, events: list[dict]) -> None:
    """Persist archived events and update the parent run record."""
    if not events:
        return

    async with AsyncSessionLocal() as db:
        try:
            has_error = any(e.get("event_type") == "error" for e in events)
            answer = "".join(
                e.get("payload", {}).get("content", "")
                for e in events
                if e.get("event_type") == "answer"
            )
            last_ts_ms = events[-1].get("ts_ms", 0)

            result = await db.execute(select(OpsRun).where(OpsRun.id == run_id))
            run = result.scalar_one_or_none()
            if run is not None:
                run.status = "error" if has_error else "completed"
                run.latency_ms = last_ts_ms
                run.answer = answer

            db_events = [
                OpsRunEvent(
                    run_id=run_id,
                    seq=e["seq"],
                    ts_ms=e["ts_ms"],
                    agent_role=e["agent_role"],
                    event_type=e["event_type"],
                    payload=e.get("payload", {}),
                )
                for e in events
            ]
            db.add_all(db_events)
            await db.commit()
        except Exception:
            await db.rollback()
            logger.exception("Failed to persist chat run events", extra={"run_id": run_id})


@router.post("/stream")
async def chat_stream(
    request: Request,
    user: OpsUser = Depends(get_current_user),
) -> StreamingResponse:
    """Stream chat response via Server-Sent Events."""
    body = await request.json()
    req = ChatStreamRequest(**body)
    run_id = str(uuid.uuid4())

    # Setup chat session and run record outside the SSE generator.
    async with AsyncSessionLocal() as setup_session:
        chat_session_id = await _resolve_chat_session(
            setup_session,
            req.session_id,
            user.id,
            req.message,
        )

        run = OpsRun(
            id=run_id,
            session_id=chat_session_id,
            query=req.message,
            status="running",
            model=req.model or settings.ops_llm_model,
        )
        setup_session.add(run)
        await setup_session.commit()

    state = ChatState(
        query=req.message,
        session_id=chat_session_id,
        run_id=run_id,
        model=req.model,
        issue_context=[],
        pr_context=[],
        graph_context=None,
        intent="",
        answer="",
        events=[],
    )

    async def event_generator() -> AsyncGenerator[str, None]:
        seq = 0
        started_at = time.perf_counter()
        all_events: list[dict] = []
        buffer: list[dict] = []
        flush_task: asyncio.Task | None = None

        def emit(event_type: str, agent_role: str, payload: dict) -> str:
            nonlocal seq
            seq += 1
            event = {
                "run_id": run_id,
                "seq": seq,
                "ts_ms": int((time.perf_counter() - started_at) * 1000),
                "agent_role": agent_role,
                "event_type": event_type,
                "payload": payload,
            }
            all_events.append(event)
            buffer.append(event)
            return make_sse_event(run_id, seq, started_at, event_type, agent_role, payload)

        async def flush() -> None:
            to_persist = buffer[:]
            buffer.clear()
            if not to_persist:
                return
            async with AsyncSessionLocal() as db:
                try:
                    db_events = [
                        OpsRunEvent(
                            run_id=run_id,
                            seq=e["seq"],
                            ts_ms=e["ts_ms"],
                            agent_role=e["agent_role"],
                            event_type=e["event_type"],
                            payload=e.get("payload", {}),
                        )
                        for e in to_persist
                    ]
                    db.add_all(db_events)
                    await db.commit()
                except Exception:
                    await db.rollback()
                    logger.exception(
                        "Failed to flush chat run events",
                        extra={"run_id": run_id, "count": len(to_persist)},
                    )

        def schedule_flush() -> None:
            nonlocal flush_task
            if flush_task is None or flush_task.done():
                flush_task = asyncio.create_task(flush())

        try:
            yield emit("run.start", "system", {"run_id": run_id})

            async for ev in run_chat_stream(state):
                yield emit(ev["event_type"], ev["agent_role"], ev["payload"])
                if len(buffer) >= _FLUSH_BATCH_SIZE:
                    schedule_flush()

            yield emit(
                "done",
                "system",
                {
                    "latency_ms": int((time.perf_counter() - started_at) * 1000),
                    "model": run.model,
                },
            )
        except Exception as e:
            logger.exception("Chat stream failed", extra={"run_id": run_id})
            yield emit(
                "error",
                "system",
                {"stage": "chat", "message": str(e), "retryable": False},
            )
        finally:
            if flush_task is not None and not flush_task.done():
                try:
                    await asyncio.wait_for(flush_task, timeout=_FINAL_FLUSH_TIMEOUT)
                except Exception:
                    logger.exception(
                        "Final background flush did not complete",
                        extra={"run_id": run_id},
                    )
            if buffer:
                await flush()
            await _persist_run_events(run_id, all_events)

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
    provider = settings.ops_llm_provider
    return ChatModelsResponse(
        provider=provider,
        default_model=get_default_model(provider),
        models=get_models_for_provider(provider),
    )
