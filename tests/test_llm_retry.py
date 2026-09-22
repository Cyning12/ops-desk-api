"""llm-layer-hardening D1：通用重试（指数退避+抖动 · 仅 retryable 错误类）。

纪律对拍（task 钉死契约）：
- 仅 LlmProviderError(retryable=True) 重试；4xx / 缺 key 零重试（分类靠结构不靠文案）
- 流中已吐首 content chunk 后零重试零换模型（防重复正文）
- 重试耗尽抛原始错误；OPS_LLM_RETRY_ENABLED=false = 现网逐字节一致
- 退避序列 monkeypatch sleep 断言上界，不假 sleep
"""
from __future__ import annotations

import logging

import httpx
import pytest

from app.llm.providers.siliconflow import SiliconFlowProvider
from app.llm.retry import DEFAULT_MAX_ATTEMPTS, retry_config
from app.llm.schema import LlmChunk, LlmMessage, LlmProviderError


@pytest.fixture
def retry_delays(monkeypatch):
    """假时钟：记录退避序列，不真 sleep。"""
    delays: list[float] = []

    async def _fake_sleep(delay: float) -> None:
        delays.append(delay)

    monkeypatch.setattr("app.llm.retry.sleep", _fake_sleep)
    return delays


class _FailingClient:
    """每次 __aenter__ 抛传输错（retryable=True）；记录实例化次数。"""

    created: int = 0

    def __init__(self, *args, **kwargs):
        type(self).created += 1

    async def __aenter__(self):
        raise httpx.ConnectError("connection refused")

    async def __aexit__(self, *args):
        pass


class _BadRequestClient:
    """固定回 400（retryable=False）。"""

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        pass

    def stream(self, *args, **kwargs):
        return _BadRequestResp()

    @property
    def calls(self):
        return type(self).created


class _BadRequestResp:
    status_code = 400

    async def aread(self):
        return b"bad request"

    async def aiter_lines(self):
        return
        yield

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        pass


class TestRetryableBackoff:
    async def test_request_error_retries_to_max_attempts(self, monkeypatch, retry_delays):
        """连续传输错：调用次数 == OPS_LLM_RETRY_MAX_ATTEMPTS，延迟序列符合界。"""
        monkeypatch.setenv("OPS_LLM_RETRY_MAX_ATTEMPTS", "4")
        _FailingClient.created = 0
        monkeypatch.setattr(httpx, "AsyncClient", lambda *a, **k: _FailingClient())

        provider = SiliconFlowProvider(api_key="test-key")
        with pytest.raises(LlmProviderError) as exc_info:
            async for _ in provider.complete_stream([LlmMessage(role="user", content="hi")]):
                pass

        assert exc_info.value.retryable is True
        assert _FailingClient.created == 4  # 总尝试 = max_attempts（含首次）
        assert len(retry_delays) == 3
        for i, d in enumerate(retry_delays):
            assert 0.0 <= d <= min(8.0, 0.5 * (2**i))

    async def test_4xx_zero_retry(self, monkeypatch, retry_delays):
        """400（retryable=False）零重试：调用计数 == 1（变异检验锚点）。"""
        calls = 0

        def _factory(*a, **k):
            nonlocal calls
            calls += 1
            return _BadRequestClient()

        monkeypatch.setattr(httpx, "AsyncClient", _factory)
        provider = SiliconFlowProvider(api_key="test-key")
        with pytest.raises(LlmProviderError) as exc_info:
            async for _ in provider.complete_stream([LlmMessage(role="user", content="hi")]):
                pass

        assert exc_info.value.retryable is False
        assert exc_info.value.status_code == 400
        assert calls == 1  # 零重试
        assert retry_delays == []  # 零退避

    async def test_missing_key_zero_retry(self, monkeypatch, retry_delays):
        """缺 API key（ValueError）零重试，原样上抛。"""
        monkeypatch.setattr("app.llm.providers.siliconflow.settings.siliconflow_api_key", None)
        provider = SiliconFlowProvider(api_key=None)
        with pytest.raises(ValueError, match="SiliconFlow API key is not configured"):
            async for _ in provider.complete_stream([LlmMessage(role="user", content="hi")]):
                pass
        assert retry_delays == []

    async def test_retry_exhaustion_raises_original_error(self, monkeypatch, retry_delays):
        """重试耗尽抛原始 LlmProviderError（不包装丢根因）。"""
        _FailingClient.created = 0
        monkeypatch.setattr(httpx, "AsyncClient", lambda *a, **k: _FailingClient())
        provider = SiliconFlowProvider(api_key="test-key")
        with pytest.raises(LlmProviderError, match="connection refused") as exc_info:
            async for _ in provider.complete_stream([LlmMessage(role="user", content="hi")]):
                pass
        assert exc_info.value.retryable is True
        assert exc_info.value.status_code is None  # 原始传输错，无包装

    async def test_retry_disabled_byte_identical(self, monkeypatch, retry_delays):
        """OPS_LLM_RETRY_ENABLED=false：行为与现网逐字节一致（单次即抛）。"""
        monkeypatch.setenv("OPS_LLM_RETRY_ENABLED", "false")
        _FailingClient.created = 0
        monkeypatch.setattr(httpx, "AsyncClient", lambda *a, **k: _FailingClient())
        provider = SiliconFlowProvider(api_key="test-key")
        with pytest.raises(LlmProviderError) as exc_info:
            async for _ in provider.complete_stream([LlmMessage(role="user", content="hi")]):
                pass
        assert exc_info.value.retryable is True
        assert _FailingClient.created == 1  # 零重试 = 现网
        assert retry_delays == []


class TestStreamRetryDiscipline:
    async def test_no_retry_after_first_content_chunk(self, monkeypatch, retry_delays):
        """已吐首 content chunk 后出错：零重试，已吐正文不重复不拼接。"""
        from app.llm.providers.base import BaseProviderImpl
        from app.ops.chat.nodes import answer_node
        from app.ops.chat.state import ChatState

        calls = 0

        class _StreamThenFail(BaseProviderImpl):
            async def complete_stream(self, messages, model=None):
                nonlocal calls
                calls += 1
                yield LlmChunk(content="Hello")
                raise LlmProviderError("mid-stream boom", retryable=True)

        monkeypatch.setattr("app.ops.chat.nodes.get_llm_provider", lambda: _StreamThenFail())
        monkeypatch.setattr("app.ops.chat.nodes.settings.ops_llm_model", "test-model")

        state = ChatState(
            query="hi", session_id=None, run_id="run-stream-1", model=None,
            issue_context=[], pr_context=[], graph_context=None, intent="",
            answer="", history_turns=[], events=[],
        )
        result = await answer_node(state)

        assert calls == 1  # 零重试（已吐首 chunk）
        assert retry_delays == []
        assert result["answer"] == "Hello"  # 已吐正文不重复
        answer_events = [e for e in result["events"] if e["event_type"] == "answer"]
        assert len(answer_events) == 1
        err = result["events"][-1]
        assert err["event_type"] == "error"
        assert err["payload"]["retryable"] is True

    async def test_retry_only_before_first_chunk(self, monkeypatch, retry_delays):
        """首 chunk 前的失败可重试：第二次尝试成功后正文只出自成功流。"""
        from app.llm.providers.base import BaseProviderImpl

        calls = 0

        class _FailOnceThenOK(BaseProviderImpl):
            async def complete_stream(self, messages, model=None):
                nonlocal calls
                calls += 1
                if calls == 1:
                    raise LlmProviderError("503", retryable=True, status_code=503)
                yield LlmChunk(content="ok")

        provider = _FailOnceThenOK()
        chunks = [
            c async for c in provider.complete_stream([LlmMessage(role="user", content="hi")])
        ]
        assert calls == 2
        assert [c.content for c in chunks] == ["ok"]
        assert len(retry_delays) == 1


class TestRetryEnv:
    @pytest.mark.parametrize(
        "env_name, bad",
        [
            ("OPS_LLM_RETRY_ENABLED", "maybe"),
            ("OPS_LLM_RETRY_MAX_ATTEMPTS", "abc"),
            ("OPS_LLM_RETRY_MAX_ATTEMPTS", "0"),
            ("OPS_LLM_RETRY_BASE_DELAY_S", "-1"),
            ("OPS_LLM_RETRY_MAX_DELAY_S", "xyz"),
        ],
    )
    def test_invalid_env_falls_back_with_warning(self, monkeypatch, caplog, env_name, bad):
        """非法 env 回退默认 + warning（全 env 统一纪律）。"""
        monkeypatch.setenv(env_name, bad)
        with caplog.at_level(logging.WARNING, logger="app.llm.retry"):
            cfg = retry_config()
        assert cfg.enabled is True
        assert cfg.max_attempts == DEFAULT_MAX_ATTEMPTS
        assert cfg.base_delay_s == 0.5
        assert cfg.max_delay_s == 8.0
        assert any("invalid" in r.message and env_name in r.message for r in caplog.records)

    def test_valid_env_applied(self, monkeypatch):
        monkeypatch.setenv("OPS_LLM_RETRY_MAX_ATTEMPTS", "5")
        monkeypatch.setenv("OPS_LLM_RETRY_BASE_DELAY_S", "1.5")
        monkeypatch.setenv("OPS_LLM_RETRY_MAX_DELAY_S", "20")
        cfg = retry_config()
        assert (cfg.max_attempts, cfg.base_delay_s, cfg.max_delay_s) == (5, 1.5, 20.0)
