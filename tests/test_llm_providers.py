"""Tests for LLM providers."""
from __future__ import annotations

import httpx
import pytest

from app.llm.providers.bailian import BailianProvider
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

    async def test_complete_reports_usage_when_tracing_on(self, monkeypatch):
        lines = [
            'data: {"choices":[{"delta":{"content":"One"}}]}',
            'data: {"choices":[{"delta":{"content":"Two"}}]}',
            'data: {"choices":[],"usage":{"prompt_tokens":11,"completion_tokens":7}}',
            "data: [DONE]",
        ]
        monkeypatch.setattr(httpx, "AsyncClient", _fake_client_factory(200, lines))
        monkeypatch.setattr("app.ops.tracing.tracing_enabled", lambda: True)
        captured: list = []
        monkeypatch.setattr(
            "app.ops.tracing.update_current_generation_usage",
            lambda usage: captured.append(usage),
        )

        provider = SiliconFlowProvider(api_key="test-key")
        answer = await provider.complete([LlmMessage(role="user", content="hi")])

        assert answer == "OneTwo"
        assert len(captured) == 1
        assert captured[0].prompt_tokens == 11
        assert captured[0].completion_tokens == 7

    async def test_complete_reports_io_when_tracing_on(self, monkeypatch):
        lines = [
            'data: {"choices":[{"delta":{"content":"Out"}}]}',
            'data: {"choices":[],"usage":{"prompt_tokens":1,"completion_tokens":1}}',
            "data: [DONE]",
        ]
        monkeypatch.setattr(httpx, "AsyncClient", _fake_client_factory(200, lines))
        monkeypatch.setattr("app.ops.tracing.tracing_enabled", lambda: True)
        monkeypatch.setattr(
            "app.ops.tracing.update_current_generation_usage", lambda usage: None
        )
        io_captured: list = []

        def _capture_io(*, input=None, output=None, truncate=None):
            io_captured.append({"input": input, "output": output})

        monkeypatch.setattr(
            "app.ops.tracing.update_current_generation_io",
            _capture_io,
        )

        provider = SiliconFlowProvider(api_key="test-key")
        answer = await provider.complete([LlmMessage(role="user", content="hi")])

        assert answer == "Out"
        assert len(io_captured) == 1
        assert "user: hi" in (io_captured[0]["input"] or "")
        assert io_captured[0]["output"] == "Out"

    async def test_complete_usage_silent_when_tracing_off(self, monkeypatch):
        lines = [
            'data: {"choices":[{"delta":{"content":"One"}}]}',
            'data: {"choices":[{"delta":{"content":"Two"}}]}',
            'data: {"choices":[],"usage":{"prompt_tokens":11,"completion_tokens":7}}',
            "data: [DONE]",
        ]
        monkeypatch.setattr(httpx, "AsyncClient", _fake_client_factory(200, lines))
        monkeypatch.setattr("app.ops.tracing.tracing_enabled", lambda: False)
        captured: list = []
        monkeypatch.setattr(
            "app.ops.tracing.update_current_generation_usage",
            lambda usage: captured.append(usage),
        )
        io_captured: list = []
        monkeypatch.setattr(
            "app.ops.tracing.update_current_generation_io",
            lambda **kwargs: io_captured.append(kwargs),
        )

        provider = SiliconFlowProvider(api_key="test-key")
        answer = await provider.complete([LlmMessage(role="user", content="hi")])

        assert answer == "OneTwo"
        assert captured == []
        assert io_captured == []

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

        assert captured["body"]["model"] == "deepseek-ai/DeepSeek-V4-Flash"


class TestBailianProvider:
    @pytest.fixture
    def mock_bailian_stream(self, monkeypatch):
        """Replace _stream_openai_compatible to control fallback chain behavior."""

        def _make(responses_by_model: dict[str, list[LlmChunk] | Exception]) -> None:
            call_log: list[str] = []

            async def fake_stream(*, base_url: str, api_key: str, model: str, messages):
                call_log.append(model)
                result = responses_by_model.get(model)
                if isinstance(result, Exception):
                    raise result
                if result is None:
                    raise LlmProviderError(f"unexpected model: {model}", retryable=False)
                for chunk in result:
                    yield chunk

            monkeypatch.setattr(
                BailianProvider,
                "_stream_openai_compatible",
                staticmethod(fake_stream),
            )
            return call_log

        return _make

    async def test_complete_stream_ok(self, mock_bailian_stream):
        mock_bailian_stream({"deepseek-v4-pro": [LlmChunk(content="ok")]})
        provider = BailianProvider(api_key="test-key")

        chunks = [
            chunk
            async for chunk in provider.complete_stream([LlmMessage(role="user", content="hi")])
        ]

        assert [c.content for c in chunks] == ["ok"]

    async def test_fallback_emits_event(self, mock_bailian_stream):
        mock_bailian_stream({
            "deepseek-v4-pro": LlmProviderError("503", retryable=True, status_code=503),
            "deepseek-v4-flash": [LlmChunk(content="fallback ok")],
        })
        provider = BailianProvider(api_key="test-key")

        chunks = [
            chunk
            async for chunk in provider.complete_stream([LlmMessage(role="user", content="hi")])
        ]

        assert len(chunks) == 2
        assert chunks[0].meta is not None
        assert chunks[0].meta["event_type"] == "model.fallback"
        assert chunks[0].meta["from_model"] == "deepseek-v4-pro"
        assert chunks[0].meta["to_model"] == "deepseek-v4-flash"
        assert chunks[1].content == "fallback ok"

    async def test_fallback_chain_exhausted(self, mock_bailian_stream):
        mock_bailian_stream({
            "deepseek-v4-pro": LlmProviderError("503", retryable=True, status_code=503),
            "deepseek-v4-flash": LlmProviderError("503", retryable=True, status_code=503),
            "qwen3.7-plus": LlmProviderError("503", retryable=True, status_code=503),
        })
        provider = BailianProvider(api_key="test-key")

        with pytest.raises(LlmProviderError) as exc_info:
            async for _ in provider.complete_stream([LlmMessage(role="user", content="hi")]):
                pass

        assert exc_info.value.retryable is False
        assert "exhausted" in str(exc_info.value)

    async def test_non_retryable_stops_fallback(self, mock_bailian_stream):
        mock_bailian_stream({
            "deepseek-v4-pro": LlmProviderError("401", retryable=False, status_code=401),
            "deepseek-v4-flash": [LlmChunk(content="should not reach")],
        })
        provider = BailianProvider(api_key="test-key")

        with pytest.raises(LlmProviderError) as exc_info:
            async for _ in provider.complete_stream([LlmMessage(role="user", content="hi")]):
                pass

        assert exc_info.value.retryable is False
        assert exc_info.value.status_code == 401

    async def test_test_only_models_filtered(self, mock_bailian_stream):
        call_log = mock_bailian_stream({
            "deepseek-v4-pro": LlmProviderError("503", retryable=True, status_code=503),
            "deepseek-v4-flash": [LlmChunk(content="ok")],
        })
        provider = BailianProvider(api_key="test-key")

        async for _ in provider.complete_stream([LlmMessage(role="user", content="hi")]):
            pass

        # test_only models (kimi-k2.7-code, GLM-5.2) must not be attempted
        assert "kimi/kimi-k2.7-code" not in call_log
        assert "ZHIPU/GLM-5.2" not in call_log

    async def test_explicit_model_skips_fallback(self, mock_bailian_stream):
        call_log = mock_bailian_stream({
            "qwen-plus": [LlmChunk(content="explicit")],
        })
        provider = BailianProvider(api_key="test-key")

        chunks = [
            chunk
            async for chunk in provider.complete_stream(
                [LlmMessage(role="user", content="hi")],
                model="qwen-plus",
            )
        ]

        assert [c.content for c in chunks] == ["explicit"]
        assert call_log == ["qwen-plus"]

    async def test_missing_api_key(self, monkeypatch):
        monkeypatch.setattr("app.llm.providers.bailian.settings.bailian_api_key", None)
        provider = BailianProvider(api_key=None)
        with pytest.raises(ValueError, match="Bailian API key is not configured"):
            async for _ in provider.complete_stream([LlmMessage(role="user", content="hi")]):
                pass

    async def test_complete_aggregates_stream(self, mock_bailian_stream):
        mock_bailian_stream({
            "deepseek-v4-pro": [LlmChunk(content="One"), LlmChunk(content="Two")],
        })
        provider = BailianProvider(api_key="test-key")

        answer = await provider.complete([LlmMessage(role="user", content="hi")])

        assert answer == "OneTwo"

    async def test_complete_reports_usage(self, mock_bailian_stream, monkeypatch):
        mock_bailian_stream({
            "deepseek-v4-pro": [
                LlmChunk(content="One"),
                LlmChunk(content="Two"),
                LlmChunk(
                    content="",
                    meta={"usage": {"prompt_tokens": 3, "completion_tokens": 4}},
                ),
            ],
        })
        captured: list = []
        monkeypatch.setattr("app.ops.tracing.tracing_enabled", lambda: True)
        monkeypatch.setattr(
            "app.ops.tracing.update_current_generation_usage",
            lambda usage: captured.append(usage),
        )
        provider = BailianProvider(api_key="test-key")

        answer = await provider.complete([LlmMessage(role="user", content="hi")])

        assert answer == "OneTwo"
        assert len(captured) == 1
        assert captured[0].prompt_tokens == 3
        assert captured[0].completion_tokens == 4

    async def test_complete_skips_fallback_meta(self, mock_bailian_stream):
        mock_bailian_stream({
            "deepseek-v4-pro": LlmProviderError("503", retryable=True, status_code=503),
            "deepseek-v4-flash": [LlmChunk(content="fallback ok")],
        })
        provider = BailianProvider(api_key="test-key")

        answer = await provider.complete([LlmMessage(role="user", content="hi")])

        assert answer == "fallback ok"
