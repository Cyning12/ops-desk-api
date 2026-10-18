"""Tests for LLM providers."""

from __future__ import annotations

import httpx
import pytest

from app.llm.providers.bailian import BailianProvider
from app.llm.providers.siliconflow import SiliconFlowProvider
from app.llm.schema import LlmChunk, LlmMessage, LlmProviderError


@pytest.fixture
def retry_delays(monkeypatch):
    """假时钟（llm-layer-hardening 清单 #2/#3/#4 改编）：记录退避序列，不真 sleep。

    默认开重试后可重试错误会先退避至 max_attempts 再抛/换模型；monkeypatch
    app.llm.retry.sleep 断言延迟上界，避免 CI 真等。
    """
    delays: list[float] = []

    async def _fake_sleep(delay: float) -> None:
        delays.append(delay)

    monkeypatch.setattr("app.llm.retry.sleep", _fake_sleep)
    return delays


class _FakeStreamResponse:
    def __init__(self, status_code: int, lines: list[str]) -> None:
        self.status_code = status_code
        self.lines = list(lines)
        self.aread_calls = 0

    async def aread(self) -> bytes:
        # 真流式路径不得在成功响应上 aread() 整包；若误调则清空 lines 以暴露回归
        self.aread_calls += 1
        if self.status_code < 400:
            self.lines.clear()
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
        self.last_response: _FakeStreamResponse | None = None

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        pass

    def stream(self, *args, **kwargs):
        self.last_response = _FakeStreamResponse(self.status_code, self.lines)
        return self.last_response


def _fake_client_factory(status_code: int, lines: list[str]):
    clients: list[_FakeClient] = []

    def _factory(*args, **kwargs):
        client = _FakeClient(status_code, lines)
        clients.append(client)
        return client

    _factory.clients = clients  # type: ignore[attr-defined]
    return _factory


class TestSiliconFlowProvider:
    async def test_complete_stream_ok(self, monkeypatch):
        lines = [
            'data: {"choices":[{"delta":{"content":"Hello"}}]}',
            'data: {"choices":[{"delta":{"content":" world"}}]}',
            "data: [DONE]",
        ]
        factory = _fake_client_factory(200, lines)
        monkeypatch.setattr(httpx, "AsyncClient", factory)

        provider = SiliconFlowProvider(api_key="test-key")
        chunks = [
            chunk
            async for chunk in provider.complete_stream([LlmMessage(role="user", content="hi")])
        ]

        assert [c.content for c in chunks] == ["Hello", " world"]
        assert all(isinstance(c, LlmChunk) for c in chunks)
        # 成功流不得 aread() 整包（假响应若误调会清空 lines → chunks 为空）
        assert factory.clients[-1].last_response is not None
        assert factory.clients[-1].last_response.aread_calls == 0

    async def test_complete_stream_rejects_aread_buffering(self, monkeypatch):
        """回归：成功路径若调用 aread()，假响应会清空 lines → 不得仍声称流式成功。"""
        lines = [
            'data: {"choices":[{"delta":{"content":"X"}}]}',
            "data: [DONE]",
        ]
        factory = _fake_client_factory(200, lines)
        monkeypatch.setattr(httpx, "AsyncClient", factory)
        provider = SiliconFlowProvider(api_key="test-key")
        chunks = [
            c async for c in provider.complete_stream([LlmMessage(role="user", content="hi")])
        ]
        assert [c.content for c in chunks] == ["X"]
        assert factory.clients[-1].last_response.aread_calls == 0

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
        assert captured[0].cached_input_tokens == 0

    async def test_complete_reports_cached_tokens(self, monkeypatch):
        lines = [
            'data: {"choices":[{"delta":{"content":"x"}}]}',
            (
                'data: {"choices":[],"usage":{"prompt_tokens":100,"completion_tokens":5,'
                '"prompt_cache_hit_tokens":80,"prompt_cache_miss_tokens":20,'
                '"prompt_tokens_details":{"cached_tokens":80}}}'
            ),
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
        await provider.complete([LlmMessage(role="user", content="hi")])

        assert len(captured) == 1
        assert captured[0].prompt_tokens == 100
        assert captured[0].cached_input_tokens == 80
        assert captured[0].completion_tokens == 5

    async def test_complete_reports_io_when_tracing_on(self, monkeypatch):
        lines = [
            'data: {"choices":[{"delta":{"content":"Out"}}]}',
            'data: {"choices":[],"usage":{"prompt_tokens":1,"completion_tokens":1}}',
            "data: [DONE]",
        ]
        monkeypatch.setattr(httpx, "AsyncClient", _fake_client_factory(200, lines))
        monkeypatch.setattr("app.ops.tracing.tracing_enabled", lambda: True)
        monkeypatch.setattr("app.ops.tracing.update_current_generation_usage", lambda usage: None)
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
            async for chunk in provider.complete_stream([LlmMessage(role="user", content="hi")])
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
    async def test_retryable_errors(self, status_code, monkeypatch, retry_delays):
        lines = []
        factory = _fake_client_factory(status_code, lines)
        monkeypatch.setattr(httpx, "AsyncClient", factory)

        provider = SiliconFlowProvider(api_key="test-key")
        with pytest.raises(LlmProviderError) as exc_info:
            async for _ in provider.complete_stream([LlmMessage(role="user", content="hi")]):
                pass

        # 错误分类断言保留；默认开重试后先退避至 max_attempts(=3) 再抛
        assert exc_info.value.retryable is True
        assert exc_info.value.status_code == status_code
        assert len(factory.clients) == 3
        # 退避序列上界：delay_i <= min(cap=8, base=0.5*2^i)，jitter 下界 >= 0
        assert len(retry_delays) == 2
        assert all(0.0 <= d <= min(8.0, 0.5 * (2**i)) for i, d in enumerate(retry_delays))

    async def test_sse_parse_error_retryable(self, monkeypatch, retry_delays):
        lines = ["data: not-json"]
        factory = _fake_client_factory(200, lines)
        monkeypatch.setattr(httpx, "AsyncClient", factory)

        provider = SiliconFlowProvider(api_key="test-key")
        with pytest.raises(LlmProviderError) as exc_info:
            async for _ in provider.complete_stream([LlmMessage(role="user", content="hi")]):
                pass

        assert exc_info.value.retryable is True
        # SSE 解析错可重试：默认退避至 max_attempts(=3) 再抛
        assert len(factory.clients) == 3
        assert len(retry_delays) == 2

    async def test_request_error_retryable(self, monkeypatch, retry_delays):
        created = []

        class _FailingClient:
            def __init__(self, *args, **kwargs):
                created.append(1)

            async def __aenter__(self):
                raise httpx.ConnectError("connection refused")

            async def __aexit__(self, *args):
                pass

        monkeypatch.setattr(httpx, "AsyncClient", lambda *args, **kwargs: _FailingClient())

        provider = SiliconFlowProvider(api_key="test-key")
        with pytest.raises(LlmProviderError) as exc_info:
            async for _ in provider.complete_stream([LlmMessage(role="user", content="hi")]):
                pass

        # 分类断言保留；传输错默认退避重试至 max_attempts(=3) 再抛
        assert exc_info.value.retryable is True
        assert "connection refused" in str(exc_info.value)
        assert len(created) == 3
        assert len(retry_delays) == 2

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
                return _FakeStreamResponse(
                    200, ['data: {"choices":[{"delta":{"content":"ok"}}]}', "data: [DONE]"]
                )

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

    async def test_fallback_emits_event(self, mock_bailian_stream, retry_delays):
        # 改编（清单 #3）：默认开重试后首候选先同模型退避至耗尽（max_attempts=3），
        # 再发 model.fallback 换下一候选；事件语义/链序不变
        call_log = mock_bailian_stream(
            {
                "deepseek-v4-pro": LlmProviderError("503", retryable=True, status_code=503),
                "deepseek-v4-flash": [LlmChunk(content="fallback ok")],
            }
        )
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
        # 首候选退避重试 3 次后才换模型（链内每候选走同一重试层）
        assert call_log == ["deepseek-v4-pro"] * 3 + ["deepseek-v4-flash"]
        assert len(retry_delays) == 2

    async def test_fallback_chain_exhausted(self, mock_bailian_stream, monkeypatch, retry_delays):
        # 改编（清单 #4）：拉高 fail_max 隔离重试语义（9 次环境失败会真熔断，
        # 熔断行为由 tests/test_llm_circuit.py 专测覆盖）；终态断言保留
        monkeypatch.setenv("OPS_LLM_CB_FAIL_MAX", "99")
        call_log = mock_bailian_stream(
            {
                "deepseek-v4-pro": LlmProviderError("503", retryable=True, status_code=503),
                "deepseek-v4-flash": LlmProviderError("503", retryable=True, status_code=503),
                "qwen3.7-plus": LlmProviderError("503", retryable=True, status_code=503),
            }
        )
        provider = BailianProvider(api_key="test-key")

        with pytest.raises(LlmProviderError) as exc_info:
            async for _ in provider.complete_stream([LlmMessage(role="user", content="hi")]):
                pass

        assert exc_info.value.retryable is False
        assert "exhausted" in str(exc_info.value)
        # 每候选先退避重试至耗尽：共 3 候选 × max_attempts(=3) 次出网
        assert call_log == (
            ["deepseek-v4-pro"] * 3 + ["deepseek-v4-flash"] * 3 + ["qwen3.7-plus"] * 3
        )

    async def test_non_retryable_stops_fallback(self, mock_bailian_stream):
        mock_bailian_stream(
            {
                "deepseek-v4-pro": LlmProviderError("401", retryable=False, status_code=401),
                "deepseek-v4-flash": [LlmChunk(content="should not reach")],
            }
        )
        provider = BailianProvider(api_key="test-key")

        with pytest.raises(LlmProviderError) as exc_info:
            async for _ in provider.complete_stream([LlmMessage(role="user", content="hi")]):
                pass

        assert exc_info.value.retryable is False
        assert exc_info.value.status_code == 401

    async def test_test_only_models_filtered(self, mock_bailian_stream):
        call_log = mock_bailian_stream(
            {
                "deepseek-v4-pro": LlmProviderError("503", retryable=True, status_code=503),
                "deepseek-v4-flash": [LlmChunk(content="ok")],
            }
        )
        provider = BailianProvider(api_key="test-key")

        async for _ in provider.complete_stream([LlmMessage(role="user", content="hi")]):
            pass

        # test_only models (kimi-k2.7-code, GLM-5.2) must not be attempted
        assert "kimi/kimi-k2.7-code" not in call_log
        assert "ZHIPU/GLM-5.2" not in call_log

    async def test_explicit_model_skips_fallback(self, mock_bailian_stream):
        call_log = mock_bailian_stream(
            {
                "qwen-plus": [LlmChunk(content="explicit")],
            }
        )
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
        mock_bailian_stream(
            {
                "deepseek-v4-pro": [LlmChunk(content="One"), LlmChunk(content="Two")],
            }
        )
        provider = BailianProvider(api_key="test-key")

        answer = await provider.complete([LlmMessage(role="user", content="hi")])

        assert answer == "OneTwo"

    async def test_complete_reports_usage(self, mock_bailian_stream, monkeypatch):
        mock_bailian_stream(
            {
                "deepseek-v4-pro": [
                    LlmChunk(content="One"),
                    LlmChunk(content="Two"),
                    LlmChunk(
                        content="",
                        meta={"usage": {"prompt_tokens": 3, "completion_tokens": 4}},
                    ),
                ],
            }
        )
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
        mock_bailian_stream(
            {
                "deepseek-v4-pro": LlmProviderError("503", retryable=True, status_code=503),
                "deepseek-v4-flash": [LlmChunk(content="fallback ok")],
            }
        )
        provider = BailianProvider(api_key="test-key")

        answer = await provider.complete([LlmMessage(role="user", content="hi")])

        assert answer == "fallback ok"
