"""Tests for LLM providers."""
from __future__ import annotations

import httpx
import pytest

from app.llm.providers.siliconflow import SiliconFlowProvider
from app.llm.schema import LlmChunk, LlmMessage, LlmProviderError


class _FakeStreamResponse:
    def __init__(self, status_code: int, lines: list[str]) -> None:
        self.status_code = status_code
        self.lines = lines

    async def aread(self) -> bytes:
        return b""

    async def aiter_lines(self):
        for line in self.lines:
            yield line

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        pass


class _FakeClient:
    def __init__(self, status_code: int, lines: list[str]) -> None:
        self.status_code = status_code
        self.lines = lines

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        pass

    def stream(self, *args, **kwargs):
        return _FakeStreamResponse(self.status_code, self.lines)


def _fake_client_factory(status_code: int, lines: list[str]):
    return lambda *args, **kwargs: _FakeClient(status_code, lines)


class TestSiliconFlowProvider:
    async def test_complete_stream_ok(self, monkeypatch):
        lines = [
            'data: {"choices":[{"delta":{"content":"Hello"}}]}',
            'data: {"choices":[{"delta":{"content":" world"}}]}',
            "data: [DONE]",
        ]
        monkeypatch.setattr(httpx, "AsyncClient", _fake_client_factory(200, lines))

        provider = SiliconFlowProvider(api_key="test-key")
        chunks = [
            chunk
            async for chunk in provider.complete_stream(
                [LlmMessage(role="user", content="hi")]
            )
        ]

        assert [c.content for c in chunks] == ["Hello", " world"]
        assert all(isinstance(c, LlmChunk) for c in chunks)

    async def test_complete_aggregates_stream(self, monkeypatch):
        lines = [
            'data: {"choices":[{"delta":{"content":"One"}}]}',
            'data: {"choices":[{"delta":{"content":"Two"}}]}',
            "data: [DONE]",
        ]
        monkeypatch.setattr(httpx, "AsyncClient", _fake_client_factory(200, lines))

        provider = SiliconFlowProvider(api_key="test-key")
        answer = await provider.complete([LlmMessage(role="user", content="hi")])

        assert answer == "OneTwo"

    async def test_complete_stream_ignores_empty_chunks(self, monkeypatch):
        lines = [
            'data: {"choices":[{"delta":{"content":""}}]}',
            'data: {"choices":[{"delta":{}}]}',
            'data: {"choices":[]}',
            'data: {"choices":[{"delta":{"content":"real"}}]}',
            "data: [DONE]",
        ]
        monkeypatch.setattr(httpx, "AsyncClient", _fake_client_factory(200, lines))

        provider = SiliconFlowProvider(api_key="test-key")
        chunks = [
            chunk
            async for chunk in provider.complete_stream(
                [LlmMessage(role="user", content="hi")]
            )
        ]

        assert [c.content for c in chunks] == ["real"]

    async def test_missing_api_key(self, monkeypatch):
        monkeypatch.setattr("app.llm.providers.siliconflow.settings.siliconflow_api_key", None)
        provider = SiliconFlowProvider(api_key=None)
        with pytest.raises(ValueError, match="SiliconFlow API key is not configured"):
            async for _ in provider.complete_stream([LlmMessage(role="user", content="hi")]):
                pass

    async def test_4xx_non_retryable(self, monkeypatch):
        lines = []
        monkeypatch.setattr(httpx, "AsyncClient", _fake_client_factory(401, lines))

        provider = SiliconFlowProvider(api_key="test-key")
        with pytest.raises(LlmProviderError) as exc_info:
            async for _ in provider.complete_stream([LlmMessage(role="user", content="hi")]):
                pass

        assert exc_info.value.retryable is False
        assert exc_info.value.status_code == 401

    @pytest.mark.parametrize("status_code", [429, 500, 503])
    async def test_retryable_errors(self, status_code, monkeypatch):
        lines = []
        monkeypatch.setattr(httpx, "AsyncClient", _fake_client_factory(status_code, lines))

        provider = SiliconFlowProvider(api_key="test-key")
        with pytest.raises(LlmProviderError) as exc_info:
            async for _ in provider.complete_stream([LlmMessage(role="user", content="hi")]):
                pass

        assert exc_info.value.retryable is True
        assert exc_info.value.status_code == status_code

    async def test_sse_parse_error_retryable(self, monkeypatch):
        lines = ["data: not-json"]
        monkeypatch.setattr(httpx, "AsyncClient", _fake_client_factory(200, lines))

        provider = SiliconFlowProvider(api_key="test-key")
        with pytest.raises(LlmProviderError) as exc_info:
            async for _ in provider.complete_stream([LlmMessage(role="user", content="hi")]):
                pass

        assert exc_info.value.retryable is True

    async def test_request_error_retryable(self, monkeypatch):
        class _FailingClient:
            def __init__(self, *args, **kwargs):
                pass

            async def __aenter__(self):
                raise httpx.ConnectError("connection refused")

            async def __aexit__(self, *args):
                pass

        monkeypatch.setattr(httpx, "AsyncClient", lambda *args, **kwargs: _FailingClient())

        provider = SiliconFlowProvider(api_key="test-key")
        with pytest.raises(LlmProviderError) as exc_info:
            async for _ in provider.complete_stream([LlmMessage(role="user", content="hi")]):
                pass

        assert exc_info.value.retryable is True
        assert "connection refused" in str(exc_info.value)

    async def test_default_model(self, monkeypatch):
        captured = {}

        class _CapturingClient:
            def __init__(self, *args, **kwargs):
                pass

            async def __aenter__(self):
                return self

            async def __aexit__(self, *args):
                pass

            def stream(self, method, url, **kwargs):
                captured["body"] = kwargs.get("json")
                return _FakeStreamResponse(200, ['data: {"choices":[{"delta":{"content":"ok"}}]}', "data: [DONE]"])

        monkeypatch.setattr(httpx, "AsyncClient", lambda *args, **kwargs: _CapturingClient())

        provider = SiliconFlowProvider(api_key="test-key")
        async for _ in provider.complete_stream([LlmMessage(role="user", content="hi")]):
            pass

        assert captured["body"]["model"] == "deepseek-ai/DeepSeek-V4-Pro"
