"""Chat WebSocket endpoint.

Unauthenticated demo transport (interview demo scope): iOS has not adopted
WebSocket yet, so the endpoint resolves the first maintainer as the demo user
instead of verifying a session cookie. Real auth is tracked as a follow-up
task — do not expose this endpoint publicly before that lands.

Client -> server messages:
- ``{"type": "message", "message": "...", "session_id": null, "model": null}``
- ``{"type": "cancel", "run_id": "..."}``

Server -> client messages: the same event dicts as the SSE stream
(``run.start`` / ``thinking`` / ``tool_result`` / ``answer`` /
``run.cancelled`` / ``done`` / ``error``) sent as JSON text frames.
"""
from __future__ import annotations

import asyncio
import json
import logging
import uuid
from contextlib import suppress

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from sqlalchemy import select

from app.config import settings
from app.db.models import OpsUser
from app.db.session import AsyncSessionLocal
from app.ops.chat.state import ChatState
from app.ops.chat.streaming import (
    ChatEventStreamer,
    create_run_record,
    resolve_chat_session,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["chat"])


async def _resolve_demo_user() -> OpsUser | None:
    """Return the first maintainer as the demo user (temporary, no auth)."""
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(OpsUser)
            .where(OpsUser.role == "maintainer")
            .order_by(OpsUser.created_at)
            .limit(1)
        )
        return result.scalar_one_or_none()


def _error_event(stage: str, message: str, run_id: str | None = None) -> dict:
    """Build an out-of-band error event for protocol-level failures."""
    return {
        "run_id": run_id,
        "seq": 0,
        "ts_ms": 0,
        "agent_role": "system",
        "event_type": "error",
        "payload": {"stage": stage, "message": message, "retryable": False},
    }


async def _pump_events(streamer: ChatEventStreamer, websocket: WebSocket) -> None:
    """Forward streamer events to the websocket until done or disconnected."""
    agen = streamer.events()
    try:
        async for event in agen:
            await websocket.send_json(event)
    except (WebSocketDisconnect, RuntimeError):
        # Client went away mid-run; aclose() below still persists the run.
        pass
    finally:
        await agen.aclose()


@router.websocket("/ws")
async def chat_ws(websocket: WebSocket) -> None:
    """Handle a chat websocket connection: one active run at a time.

    Disabled when OPS_CHAT_WS_ENABLED=false: the endpoint is unauthenticated
    by design (demo user), so it must not be reachable on the public internet.
    """
    if not settings.ops_chat_ws_enabled:
        await websocket.close(code=1008)  # policy violation
        return

    await websocket.accept()

    user = await _resolve_demo_user()
    if user is None:
        await websocket.send_json(
            _error_event("ws.user", "no maintainer user available for demo")
        )
        await websocket.close(code=1011)
        return

    active_task: asyncio.Task | None = None
    active_streamer: ChatEventStreamer | None = None
    active_run_id: str | None = None

    try:
        while True:
            raw = await websocket.receive_text()
            try:
                data = json.loads(raw)
            except json.JSONDecodeError:
                await websocket.send_json(
                    _error_event("ws.protocol", "invalid JSON message")
                )
                continue

            msg_type = data.get("type")
            if msg_type == "message":
                if active_task is not None and not active_task.done():
                    # The terminal event (done/run.cancelled) may already be
                    # on its way to the client while the pump task is still
                    # persisting; give it a short grace period before
                    # rejecting as a concurrent run. asyncio.wait (unlike
                    # wait_for) does not cancel the task on timeout.
                    with suppress(BaseException):
                        await asyncio.wait({active_task}, timeout=1)
                if active_task is not None and not active_task.done():
                    await websocket.send_json(
                        _error_event(
                            "ws.protocol", "run already active", active_run_id
                        )
                    )
                    continue

                message = (data.get("message") or "").strip()
                if not message:
                    await websocket.send_json(
                        _error_event("ws.protocol", "message is required")
                    )
                    continue

                run_id = str(uuid.uuid4())
                run_model = data.get("model") or settings.ops_llm_model

                async with AsyncSessionLocal() as setup_session:
                    chat_session_id = await resolve_chat_session(
                        setup_session,
                        data.get("session_id"),
                        str(user.id),
                        message,
                    )
                    await setup_session.commit()
                await create_run_record(run_id, chat_session_id, message, run_model)

                state = ChatState(
                    query=message,
                    session_id=chat_session_id,
                    run_id=run_id,
                    model=data.get("model"),
                    issue_context=[],
                    pr_context=[],
                    graph_context=None,
                    intent="",
                    answer="",
                    events=[],
                )
                active_streamer = ChatEventStreamer(state, run_id, run_model)
                active_run_id = run_id
                active_task = asyncio.create_task(
                    _pump_events(active_streamer, websocket)
                )
            elif msg_type == "cancel":
                cancel_run_id = data.get("run_id")
                if (
                    active_streamer is not None
                    and active_task is not None
                    and not active_task.done()
                    and cancel_run_id == active_run_id
                ):
                    active_streamer.request_cancel()
                else:
                    await websocket.send_json(
                        _error_event(
                            "ws.cancel", "no active run for cancel", cancel_run_id
                        )
                    )
            else:
                await websocket.send_json(
                    _error_event("ws.protocol", f"unknown message type: {msg_type!r}")
                )
    except WebSocketDisconnect:
        logger.info("Chat WS disconnected", extra={"run_id": active_run_id})
    finally:
        if active_streamer is not None:
            active_streamer.request_cancel()
        if active_task is not None and not active_task.done():
            # Give the run a grace period to emit run.cancelled and persist
            # before falling back to hard cancellation.
            with suppress(BaseException):
                await asyncio.wait_for(active_task, timeout=10)
            if not active_task.done():
                active_task.cancel()
                with suppress(BaseException):
                    await active_task
