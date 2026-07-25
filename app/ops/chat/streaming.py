"""Shared chat run streaming and persistence helpers for SSE and WS transports."""
from __future__ import annotations

import asyncio
import logging
import time
from collections.abc import AsyncIterator
from contextlib import suppress

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import OpsRun, OpsRunEvent, OpsSessionChat
from app.db.session import AsyncSessionLocal
from app.ops.chat.service import run_chat_stream
from app.ops.chat.state import ChatState

logger = logging.getLogger(__name__)

# Flush events to DB every N buffered events to keep memory bounded.
_FLUSH_BATCH_SIZE = 10
# Max wait seconds for final background flush before closing the stream.
_FINAL_FLUSH_TIMEOUT = 5.0


async def resolve_chat_session(
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
        if chat_session is None or str(chat_session.user_id) != str(user_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Chat session not found",
            )
        return session_id

    chat_session = OpsSessionChat(user_id=user_id, title=title[:100])
    db.add(chat_session)
    await db.flush()
    return str(chat_session.id)


async def create_run_record(
    run_id: str,
    session_id: str,
    query: str,
    model: str,
) -> None:
    """Create the initial ops_runs record for a chat stream."""
    async with AsyncSessionLocal() as db:
        try:
            run = OpsRun(
                id=run_id,
                session_id=session_id,
                query=query,
                status="running",
                model=model,
            )
            db.add(run)
            await db.commit()
        except Exception:
            await db.rollback()
            logger.exception("Failed to create chat run record", extra={"run_id": run_id})
            raise


async def flush_run_events(run_id: str, events: list[dict]) -> None:
    """Persist a batch of run events without updating the parent run record."""
    if not events:
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
                for e in events
            ]
            db.add_all(db_events)
            await db.commit()
        except Exception:
            await db.rollback()
            logger.exception(
                "Failed to flush chat run events",
                extra={"run_id": run_id, "count": len(events)},
            )


async def persist_run_events(
    run_id: str,
    events: list[dict],
    cancelled: bool = False,
) -> None:
    """Update the parent run record from archived events.

    Events themselves are persisted incrementally by `flush_run_events`; this
    helper only finalizes the run summary so we don't duplicate seq numbers.
    """
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
                if has_error:
                    run.status = "error"
                elif cancelled:
                    run.status = "cancelled"
                else:
                    run.status = "completed"
                run.latency_ms = last_ts_ms
                run.answer = answer
                await db.commit()
        except Exception:
            await db.rollback()
            logger.exception("Failed to persist chat run summary", extra={"run_id": run_id})


class ChatEventStreamer:
    """Streams a chat run's events and persists them incrementally.

    Transport-agnostic: the SSE router formats each event as an SSE frame,
    the WS endpoint sends each event as a JSON message. Cancellation is
    cooperative: `request_cancel()` sets a flag checked between graph events,
    and the stream ends with a `run.cancelled` event instead of `done`.
    """

    def __init__(self, state: ChatState, run_id: str, run_model: str) -> None:
        self.state = state
        self.run_id = run_id
        self.run_model = run_model
        self.cancel_requested = False
        self._cancel_event: asyncio.Event | None = None

    def request_cancel(self) -> None:
        """Ask the stream to stop; interrupts an in-flight graph step."""
        self.cancel_requested = True
        if self._cancel_event is not None:
            self._cancel_event.set()

    async def _finalize_run(
        self,
        buffer: list[dict],
        all_events: list[dict],
        flush_task: asyncio.Task | None,
    ) -> None:
        """Flush remaining events and finalize the run record."""
        if flush_task is not None and not flush_task.done():
            try:
                await asyncio.wait_for(flush_task, timeout=_FINAL_FLUSH_TIMEOUT)
            except Exception:
                logger.exception(
                    "Final background flush did not complete",
                    extra={"run_id": self.run_id},
                )
        if buffer:
            await flush_run_events(self.run_id, buffer[:])
            buffer.clear()
        await persist_run_events(
            self.run_id, all_events, cancelled=self.cancel_requested
        )

    async def events(self) -> AsyncIterator[dict]:
        """Yield run events as dicts, flushing them to the DB along the way."""
        seq = 0
        started_at = time.perf_counter()
        all_events: list[dict] = []
        buffer: list[dict] = []
        flush_task: asyncio.Task | None = None

        def emit(event_type: str, agent_role: str, payload: dict) -> dict:
            nonlocal seq
            seq += 1
            event = {
                "run_id": self.run_id,
                "seq": seq,
                "ts_ms": int((time.perf_counter() - started_at) * 1000),
                "agent_role": agent_role,
                "event_type": event_type,
                "payload": payload,
            }
            all_events.append(event)
            buffer.append(event)
            return event

        async def flush() -> None:
            to_persist = buffer[:]
            buffer.clear()
            await flush_run_events(self.run_id, to_persist)

        def schedule_flush() -> None:
            nonlocal flush_task
            if flush_task is None or flush_task.done():
                flush_task = asyncio.create_task(flush())

        try:
            yield emit("run.start", "system", {"run_id": self.run_id})

            # Race each graph event against the cancel signal so a cancel
            # interrupts an in-flight node (e.g. mid-LLM-generation) instead
            # of waiting for the next event boundary. Graph nodes buffer
            # their events until completion, so per-event polling alone would
            # only notice the cancel after the whole answer is generated.
            self._cancel_event = asyncio.Event()
            if self.cancel_requested:
                self._cancel_event.set()
            agen = run_chat_stream(self.state)
            try:
                while True:
                    next_event = asyncio.create_task(agen.__anext__())
                    cancel_wait = asyncio.create_task(self._cancel_event.wait())
                    try:
                        done, _pending = await asyncio.wait(
                            {next_event, cancel_wait},
                            return_when=asyncio.FIRST_COMPLETED,
                        )
                    except asyncio.CancelledError:
                        # Hard cancellation (e.g. client disconnected): stop
                        # both helper tasks so the graph step doesn't leak.
                        next_event.cancel()
                        cancel_wait.cancel()
                        with suppress(BaseException):
                            await next_event
                        with suppress(BaseException):
                            await cancel_wait
                        raise

                    cancel_wait.cancel()
                    with suppress(BaseException):
                        await cancel_wait

                    if self.cancel_requested and next_event not in done:
                        # Cancel won the race: abort the in-flight graph step.
                        next_event.cancel()
                        with suppress(BaseException):
                            await next_event
                        break

                    try:
                        ev = next_event.result()
                    except StopAsyncIteration:
                        break

                    yield emit(ev["event_type"], ev["agent_role"], ev["payload"])
                    if len(buffer) >= _FLUSH_BATCH_SIZE:
                        schedule_flush()
            finally:
                with suppress(BaseException):
                    await agen.aclose()

            if self.cancel_requested:
                yield emit(
                    "run.cancelled",
                    "system",
                    {
                        "run_id": self.run_id,
                        "latency_ms": int((time.perf_counter() - started_at) * 1000),
                    },
                )
            else:
                yield emit(
                    "done",
                    "system",
                    {
                        "latency_ms": int((time.perf_counter() - started_at) * 1000),
                        "model": self.run_model,
                    },
                )
        except asyncio.CancelledError:
            # Hard cancellation (e.g. client disconnected): still persist what
            # we have and mark the run as cancelled.
            self.cancel_requested = True
            raise
        except Exception as e:
            logger.exception("Chat stream failed", extra={"run_id": self.run_id})
            yield emit(
                "error",
                "system",
                {"stage": "chat", "message": str(e), "retryable": False},
            )
        finally:
            # Persistence must survive outer task cancellation (e.g. client
            # disconnected mid-run): run cleanup as a shielded task and keep
            # re-awaiting it if we get cancelled while waiting.
            cleanup = asyncio.create_task(
                self._finalize_run(buffer, all_events, flush_task)
            )
            while not cleanup.done():
                try:
                    await asyncio.shield(cleanup)
                except asyncio.CancelledError:
                    continue
                except Exception:
                    logger.exception(
                        "Chat stream cleanup failed",
                        extra={"run_id": self.run_id},
                    )
                    break
