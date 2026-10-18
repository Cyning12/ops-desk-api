"""llm-layer-hardening D2：provider 级熔断（pybreaker 复用 capability 模式）。

纪律对拍（task 钉死契约）：
- 仅环境类失败计数（LlmProviderError retryable=True）；业务错误 ×N 不熔
- open 时零出网立即 circuit_open（retryable=False），不返回半成功 answer
- 跳闸那次保留原始根因（throw_new_error_on_trip=False）
- 三态转换用 advance 式时间拨动 hook，不真等 60s
- snapshot 输出 state / fail_counter / seconds_until_half_open / blocked_calls
"""

from __future__ import annotations

import httpx
import pytest

from app.llm import circuit as llm_circuit
from app.llm.providers.siliconflow import SiliconFlowProvider
from app.llm.schema import LlmMessage, LlmProviderError


@pytest.fixture(autouse=True)
def _fast_breaker(monkeypatch):
    """fail_max=2 · 单请求单尝试（重试与熔断的叠加由 D1/D2 各自覆盖）。"""
    monkeypatch.setenv("OPS_LLM_CB_FAIL_MAX", "2")
    monkeypatch.setenv("OPS_LLM_RETRY_MAX_ATTEMPTS", "1")

    async def _fake_sleep(delay: float) -> None:
        pass

    monkeypatch.setattr("app.llm.retry.sleep", _fake_sleep)


class _ClientFactory:
    """按脚本回响应：503 或 200+一个 content chunk；记录出网次数。"""

    def __init__(self, statuses: list[int]) -> None:
        self.statuses = list(statuses)
        self.network_calls = 0

    def __call__(self, *args, **kwargs):
        self.network_calls += 1
        status = self.statuses.pop(0) if self.statuses else 200
        return _FakeClient(status)


class _FakeClient:
    def __init__(self, status_code: int) -> None:
        self.status_code = status_code

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        pass

    def stream(self, *args, **kwargs):
        return _FakeResp(self.status_code)


class _FakeResp:
    def __init__(self, status_code: int) -> None:
        self.status_code = status_code

    async def aread(self):
        return b"err"

    async def aiter_lines(self):
        if self.status_code == 200:
            yield 'data: {"choices":[{"delta":{"content":"ok"}}]}'
            yield "data: [DONE]"
        return

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        pass


async def _one_call(provider: SiliconFlowProvider) -> list:
    return [c async for c in provider.complete_stream([LlmMessage(role="user", content="hi")])]


class TestCircuitTripAndBlock:
    async def test_env_failures_trip_breaker_then_zero_network(self, monkeypatch):
        """连续 fail_max 次环境失败 → open；随后调用零出网 + circuit_open。"""
        factory = _ClientFactory([503, 503])
        monkeypatch.setattr(httpx, "AsyncClient", factory)
        provider = SiliconFlowProvider(api_key="test-key")

        for _ in range(2):
            with pytest.raises(LlmProviderError):
                await _one_call(provider)
        snap = llm_circuit.snapshot()
        breaker = next(b for b in snap["breakers"] if b["provider"] == "siliconflow")
        assert breaker["state"] == "open"
        assert breaker["fail_counter"] >= 2

        calls_before = factory.network_calls
        with pytest.raises(LlmProviderError) as exc_info:
            await _one_call(provider)
        # 零出网：没有新请求发出
        assert factory.network_calls == calls_before
        # circuit_open 翻译：retryable=False，不得返回半成功 answer
        assert "circuit_open" in str(exc_info.value)
        assert exc_info.value.retryable is False
        assert llm_circuit.snapshot()["blocked_calls"] >= 1

    async def test_trip_call_keeps_root_cause(self, monkeypatch):
        """跳闸那一次抛原始 LlmProviderError（非 CircuitBreakerError 替换）。"""
        factory = _ClientFactory([503, 503])
        monkeypatch.setattr(httpx, "AsyncClient", factory)
        provider = SiliconFlowProvider(api_key="test-key")

        with pytest.raises(LlmProviderError):
            await _one_call(provider)
        with pytest.raises(LlmProviderError) as exc_info:
            await _one_call(provider)
        # 第二次（跳闸那次）仍是原始 503 错误，不是 circuit_open
        assert exc_info.value.status_code == 503
        assert "circuit_open" not in str(exc_info.value)

    async def test_business_errors_never_trip(self, monkeypatch):
        """业务类错误（retryable=False）× fail_max 以上：breaker 保持 closed。"""
        factory = _ClientFactory([401] * 6)
        monkeypatch.setattr(httpx, "AsyncClient", factory)
        provider = SiliconFlowProvider(api_key="test-key")

        for _ in range(6):
            with pytest.raises(LlmProviderError) as exc_info:
                await _one_call(provider)
            assert exc_info.value.status_code == 401  # 每次都真出网、真错

        breaker = next(
            b for b in llm_circuit.snapshot()["breakers"] if b["provider"] == "siliconflow"
        )
        assert breaker["state"] == "closed"
        assert factory.network_calls == 6


class TestCircuitHalfOpen:
    async def test_advance_then_probe_success_closes(self, monkeypatch):
        """拨动 opened_at（不真等 60s）→ 放行探测 → 成功 → closed。"""
        factory = _ClientFactory([503, 503, 200])
        monkeypatch.setattr(httpx, "AsyncClient", factory)
        provider = SiliconFlowProvider(api_key="test-key")

        for _ in range(2):
            with pytest.raises(LlmProviderError):
                await _one_call(provider)
        llm_circuit.advance("siliconflow", 61)  # 拨过 reset_timeout(60s)

        chunks = await _one_call(provider)  # 探测放行
        assert [c.content for c in chunks] == ["ok"]
        breaker = next(
            b for b in llm_circuit.snapshot()["breakers"] if b["provider"] == "siliconflow"
        )
        assert breaker["state"] == "closed"
        assert breaker["fail_counter"] == 0

    async def test_advance_then_probe_failure_reopens(self, monkeypatch):
        """探测失败 → 回到 open（opened_at 刷新）。"""
        factory = _ClientFactory([503, 503, 503])
        monkeypatch.setattr(httpx, "AsyncClient", factory)
        provider = SiliconFlowProvider(api_key="test-key")

        for _ in range(2):
            with pytest.raises(LlmProviderError):
                await _one_call(provider)
        llm_circuit.advance("siliconflow", 61)

        with pytest.raises(LlmProviderError) as exc_info:
            await _one_call(provider)
        assert exc_info.value.status_code == 503  # 探测失败的原始错误
        breaker = next(
            b for b in llm_circuit.snapshot()["breakers"] if b["provider"] == "siliconflow"
        )
        assert breaker["state"] == "open"

    async def test_open_not_yet_elapsed_blocks(self, monkeypatch):
        """open 未到点：blocked（不拨时间 → 不放行）。"""
        factory = _ClientFactory([503, 503])
        monkeypatch.setattr(httpx, "AsyncClient", factory)
        provider = SiliconFlowProvider(api_key="test-key")

        for _ in range(2):
            with pytest.raises(LlmProviderError):
                await _one_call(provider)
        breaker = next(
            b for b in llm_circuit.snapshot()["breakers"] if b["provider"] == "siliconflow"
        )
        assert breaker["seconds_until_half_open"] > 0
        assert breaker["ready_to_probe"] is False


class TestCircuitSnapshotAndEnv:
    def test_snapshot_fields(self):
        llm_circuit.trip("bailian")
        snap = llm_circuit.snapshot()
        assert snap["enabled"] is True
        assert snap["fail_max"] == 2
        assert snap["reset_timeout"] == 60
        assert snap["scope"] == "process-local"
        breaker = next(b for b in snap["breakers"] if b["provider"] == "bailian")
        assert breaker["state"] == "open"
        assert "fail_counter" in breaker
        assert "seconds_until_half_open" in breaker
        assert "blocked_calls" in snap

    def test_invalid_env_falls_back(self, monkeypatch, caplog):
        import logging

        monkeypatch.setenv("OPS_LLM_CB_FAIL_MAX", "abc")
        monkeypatch.setenv("OPS_LLM_CB_RESET_TIMEOUT", "-3")
        monkeypatch.setenv("OPS_LLM_CB_ENABLED", "maybe")
        with caplog.at_level(logging.WARNING, logger="app.llm.circuit"):
            assert llm_circuit.fail_max() == llm_circuit.DEFAULT_FAIL_MAX
            assert llm_circuit.reset_timeout() == llm_circuit.DEFAULT_RESET_TIMEOUT
            assert llm_circuit.enabled() is True
        assert sum("invalid" in r.message for r in caplog.records) >= 3

    async def test_cb_disabled_byte_identical(self, monkeypatch):
        """OPS_LLM_CB_ENABLED=false：不建 breaker 不拦截（现网逐字节一致）。"""
        monkeypatch.setenv("OPS_LLM_CB_ENABLED", "false")
        factory = _ClientFactory([503] * 8)
        monkeypatch.setattr(httpx, "AsyncClient", factory)
        provider = SiliconFlowProvider(api_key="test-key")
        for _ in range(8):
            with pytest.raises(LlmProviderError):
                await _one_call(provider)
        assert factory.network_calls == 8  # 每次都真出网，无熔断拦截
        assert llm_circuit.snapshot()["breakers"] == []
