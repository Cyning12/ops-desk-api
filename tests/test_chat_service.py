"""Tests for chat service event mapping."""
from __future__ import annotations

from app.ops.chat.service import run_chat_stream
from app.ops.chat.state import ChatState


def _make_state() -> ChatState:
    return ChatState(
        query="hello",
        session_id=None,
        run_id="run-1",
        model=None,
        issue_context=[],
        pr_context=[],
        graph_context=None,
        intent="",
        answer="",
        history_turns=[],
        events=[],
    )


class TestRunChatStream:
    async def test_maps_node_events(self, monkeypatch):
        async def fake_astream(state, stream_mode):
            assert stream_mode == "updates"
            yield {
                "detect_intent": {
                    "events": [
                        {"event_type": "thinking", "agent_role": "intent", "payload": {"step": "intent"}}
                    ]
                }
            }
            yield {
                "generate_answer": {
                    "events": [
                        {"event_type": "answer", "agent_role": "answer", "payload": {"content": "hi"}}
                    ]
                }
            }

        monkeypatch.setattr("app.ops.chat.service.graph.astream", fake_astream)

        events = [e async for e in run_chat_stream(_make_state())]

        assert len(events) == 2
        assert events[0] == {
            "event_type": "thinking",
            "agent_role": "intent",
            "payload": {"step": "intent"},
        }
        assert events[1] == {
            "event_type": "answer",
            "agent_role": "answer",
            "payload": {"content": "hi"},
        }

    async def test_uses_node_name_when_agent_role_missing(self, monkeypatch):
        async def fake_astream(state, stream_mode):
            yield {"load_context": {"events": [{"event_type": "tool_result", "payload": {}}]}}

        monkeypatch.setattr("app.ops.chat.service.graph.astream", fake_astream)

        events = [e async for e in run_chat_stream(_make_state())]

        assert events[0]["agent_role"] == "load_context"

    async def test_handles_graph_exception(self, monkeypatch):
        async def fake_astream(state, stream_mode):
            raise RuntimeError("graph exploded")
            yield {}  # makes this an async generator

        monkeypatch.setattr("app.ops.chat.service.graph.astream", fake_astream)

        events = [e async for e in run_chat_stream(_make_state())]

        assert len(events) == 1
        assert events[0]["event_type"] == "error"
        assert "graph exploded" in events[0]["payload"]["message"]

    async def test_skips_non_dict_node_output(self, monkeypatch):
        async def fake_astream(state, stream_mode):
            yield {"detect_intent": None}
            yield {"generate_answer": {"events": [{"event_type": "answer", "payload": {"content": "ok"}}]}}

        monkeypatch.setattr("app.ops.chat.service.graph.astream", fake_astream)

        events = [e async for e in run_chat_stream(_make_state())]

        assert len(events) == 1
        assert events[0]["event_type"] == "answer"

    async def test_skips_non_dict_events(self, monkeypatch):
        async def fake_astream(state, stream_mode):
            yield {"detect_intent": {"events": ["bad-event", {"event_type": "thinking"}]}}

        monkeypatch.setattr("app.ops.chat.service.graph.astream", fake_astream)

        events = [e async for e in run_chat_stream(_make_state())]

        assert len(events) == 1
        assert events[0]["event_type"] == "thinking"
