"""E4：score_current_trace 抽样门控（mock Langfuse · 不连云）。"""
from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from app.ops import tracing


@pytest.fixture(autouse=True)
def _reset_eval_sample_env(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv("OPS_EVAL_SCORE_SAMPLE_RATE", raising=False)
    # 默认关 tracing，各用例按需打开
    monkeypatch.delenv("OPS_CHAT_TRACER", raising=False)
    monkeypatch.delenv("LANGFUSE_TRACING", raising=False)
    monkeypatch.delenv("LANGFUSE_PUBLIC_KEY", raising=False)
    monkeypatch.delenv("LANGFUSE_SECRET_KEY", raising=False)


def _enable_tracing(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPS_CHAT_TRACER", "langfuse")
    monkeypatch.setenv("LANGFUSE_PUBLIC_KEY", "pk-test")
    monkeypatch.setenv("LANGFUSE_SECRET_KEY", "sk-test")


def test_eval_score_sample_rate_default_zero():
    assert tracing.eval_score_sample_rate() == 0.0


def test_eval_score_sample_rate_invalid_treated_as_zero(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
):
    monkeypatch.setenv("OPS_EVAL_SCORE_SAMPLE_RATE", "nope")
    with caplog.at_level("WARNING"):
        assert tracing.eval_score_sample_rate() == 0.0
    assert any("OPS_EVAL_SCORE_SAMPLE_RATE" in r.message for r in caplog.records)


def test_eval_score_sample_rate_out_of_range(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
):
    monkeypatch.setenv("OPS_EVAL_SCORE_SAMPLE_RATE", "1.5")
    with caplog.at_level("WARNING"):
        assert tracing.eval_score_sample_rate() == 0.0
    assert any("out of [0,1]" in r.message for r in caplog.records)


def test_score_current_trace_noop_when_tracing_off(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("OPS_EVAL_SCORE_SAMPLE_RATE", "1")
    mock_client = MagicMock()
    monkeypatch.setattr(
        "langfuse.get_client", lambda: mock_client, raising=False
    )
    # 未配置 tracer → tracing_enabled False；即便 import 了也不该调 SDK
    tracing.score_current_trace("stab.fallback", 1)
    mock_client.score_current_trace.assert_not_called()


def test_score_current_trace_rate_zero_skips_sdk(monkeypatch: pytest.MonkeyPatch):
    _enable_tracing(monkeypatch)
    monkeypatch.setenv("OPS_EVAL_SCORE_SAMPLE_RATE", "0")
    mock_client = MagicMock()
    monkeypatch.setattr(tracing, "tracing_enabled", lambda: True)

    def _fake_get_client():
        return mock_client

    monkeypatch.setattr(
        "langfuse.get_client",
        _fake_get_client,
    )
    # 直接 patch 导入路径：score 内 from langfuse import get_client
    import langfuse

    monkeypatch.setattr(langfuse, "get_client", _fake_get_client)

    tracing.score_current_trace("stab.fallback", 1)
    mock_client.score_current_trace.assert_not_called()


def test_score_current_trace_rate_one_writes(monkeypatch: pytest.MonkeyPatch):
    _enable_tracing(monkeypatch)
    monkeypatch.setenv("OPS_EVAL_SCORE_SAMPLE_RATE", "1")
    mock_client = MagicMock()
    monkeypatch.setattr(tracing, "tracing_enabled", lambda: True)

    import langfuse

    monkeypatch.setattr(langfuse, "get_client", lambda: mock_client)

    tracing.score_current_trace("stab.fallback", 1)
    mock_client.score_current_trace.assert_called_once_with(
        name="stab.fallback", value=1
    )


def test_score_current_trace_sdk_error_swallowed(monkeypatch: pytest.MonkeyPatch):
    _enable_tracing(monkeypatch)
    monkeypatch.setenv("OPS_EVAL_SCORE_SAMPLE_RATE", "1")
    monkeypatch.setattr(tracing, "tracing_enabled", lambda: True)

    mock_client = MagicMock()
    mock_client.score_current_trace.side_effect = RuntimeError("boom")

    import langfuse

    monkeypatch.setattr(langfuse, "get_client", lambda: mock_client)

    tracing.score_current_trace("stab.fallback", 1)  # 不抛


def test_supervisor_fallback_scores_stab_fallback(monkeypatch: pytest.MonkeyPatch):
    """调用点：supervisor_fallback=True → stab.fallback=1。"""
    from app.ops.lg_rag.multi import nodes

    scored: list[tuple] = []

    def _capture(name: str, value, **kwargs):
        scored.append((name, value, kwargs))

    monkeypatch.setattr(nodes, "score_current_trace", _capture)
    monkeypatch.setattr(nodes, "tracing_enabled", lambda: False)

    nodes._record_span_metadata({"supervisor_fallback": True})
    assert scored == [("stab.fallback", 1, {})]

    scored.clear()
    nodes._record_span_metadata({"supervisor_fallback": False})
    assert scored == []
