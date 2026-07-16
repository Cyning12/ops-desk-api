"""Tests for chat LangGraph nodes."""
from __future__ import annotations

from app.llm.schema import LlmChunk, LlmMessage
from app.ops.chat.nodes import (
    _build_messages,
    answer_node,
    intent_node,
    load_issue_context_node,
)
from app.ops.chat.state import ChatState


def _make_state(**overrides) -> ChatState:
    defaults = {
        "query": "hello",
        "session_id": None,
        "run_id": "run-1",
        "model": None,
        "issue_context": [],
        "pr_context": [],
        "graph_context": None,
        "intent": "",
        "answer": "",
        "events": [],
    }
    defaults.update(overrides)
    return ChatState(**defaults)  # type: ignore[arg-type]


class TestIntentNode:
    async def test_general_intent(self):
        state = _make_state(query="What is the project about?")
        result = await intent_node(state)

        assert result["intent"] == "general"
        assert result["events"][0]["event_type"] == "thinking"

    async def test_issue_qa_intent(self):
        state = _make_state(query="What is #123 about?")
        result = await intent_node(state)

        assert result["intent"] == "issue_qa"

    async def test_overview_intent(self):
        state = _make_state(query="Show me the overview")
        result = await intent_node(state)

        assert result["intent"] == "overview"


class TestLoadIssueContextNode:
    async def test_no_issue_number(self, monkeypatch):
        monkeypatch.setattr("app.ops.chat.nodes._fetch_issue_by_number", lambda n: None)
        state = _make_state(query="hello")
        result = await load_issue_context_node(state)

        assert result["issue_context"] == []
        event = result["events"][0]
        assert event["event_type"] == "tool_result"
        assert event["payload"]["ok"] is False
        assert event["payload"]["issue_number"] is None

    async def test_issue_found(self, monkeypatch):
        async def fake_fetch(n):
            return {"number": n, "title": "Bug fix", "body": "body"}

        monkeypatch.setattr("app.ops.chat.nodes._fetch_issue_by_number", fake_fetch)
        state = _make_state(query="Tell me about #42")
        result = await load_issue_context_node(state)

        assert result["issue_context"] == [{"number": 42, "title": "Bug fix", "body": "body"}]
        event = result["events"][0]
        assert event["payload"]["ok"] is True
        assert event["payload"]["issue_number"] == 42

    async def test_issue_not_found(self, monkeypatch):
        monkeypatch.setattr("app.ops.chat.nodes._fetch_issue_by_number", lambda n: None)
        state = _make_state(query="Tell me about #99")
        result = await load_issue_context_node(state)

        assert result["issue_context"] == []
        event = result["events"][0]
        assert event["payload"]["ok"] is False
        assert event["payload"]["issue_number"] == 99


class TestBuildMessages:
    def test_includes_system_prompt(self):
        state = _make_state(query="hello")
        messages = _build_messages(state)

        assert messages[0].role == "system"
        assert "Ops Desk" in messages[0].content
        assert messages[-1] == LlmMessage(role="user", content="hello")

    def test_includes_issue_context(self):
        state = _make_state(
            query="summarize",
            issue_context=[{"number": 1, "title": "Bug", "body": "details"}],
        )
        messages = _build_messages(state)

        assert messages[1].role == "user"
        assert "Bug" in messages[1].content
        assert messages[2] == LlmMessage(role="user", content="summarize")

    def test_truncates_long_body(self):
        state = _make_state(
            query="summarize",
            issue_context=[{"number": 1, "title": "Bug", "body": "x" * 5000}],
        )
        messages = _build_messages(state)

        assert len(messages[1].content) < 2500


class TestAnswerNode:
    async def test_answer_node_streams_events(self, monkeypatch):
        from app.llm.providers.base import BaseProviderImpl

        class FakeProvider(BaseProviderImpl):
            async def complete_stream(self, messages, model=None):
                yield LlmChunk(content="Hello")
                yield LlmChunk(content=" world")

        monkeypatch.setattr("app.ops.chat.nodes.get_llm_provider", lambda: FakeProvider())
        monkeypatch.setattr("app.ops.chat.nodes.settings.ops_llm_model", "test-model")

        state = _make_state(query="hi")
        result = await answer_node(state)

        assert result["answer"] == "Hello world"
        event_types = [e["event_type"] for e in result["events"]]
        assert event_types == ["thinking", "answer", "answer"]

    async def test_answer_node_forwards_fallback(self, monkeypatch):
        from app.llm.providers.base import BaseProviderImpl

        class FakeProvider(BaseProviderImpl):
            async def complete_stream(self, messages, model=None):
                yield LlmChunk(
                    content="",
                    meta={
                        "event_type": "model.fallback",
                        "from_model": "a",
                        "to_model": "b",
                        "reason": "quota",
                    },
                )
                yield LlmChunk(content="ok")

        monkeypatch.setattr("app.ops.chat.nodes.get_llm_provider", lambda: FakeProvider())
        monkeypatch.setattr("app.ops.chat.nodes.settings.ops_llm_model", "test-model")

        state = _make_state(query="hi")
        result = await answer_node(state)

        event_types = [e["event_type"] for e in result["events"]]
        assert event_types == ["thinking", "model.fallback", "answer"]
        assert result["events"][1]["payload"]["to_model"] == "b"

    async def test_answer_node_handles_error(self, monkeypatch):
        from app.llm.providers.base import BaseProviderImpl
        from app.llm.schema import LlmProviderError

        class FailingProvider(BaseProviderImpl):
            async def complete_stream(self, messages, model=None):
                raise LlmProviderError("boom", retryable=True)
                yield LlmChunk(content="")  # makes this an async generator

        monkeypatch.setattr("app.ops.chat.nodes.get_llm_provider", lambda: FailingProvider())
        monkeypatch.setattr("app.ops.chat.nodes.settings.ops_llm_model", "test-model")

        state = _make_state(query="hi")
        result = await answer_node(state)

        assert result["answer"] == ""
        assert result["events"][-1]["event_type"] == "error"
        assert result["events"][-1]["payload"]["retryable"] is True
