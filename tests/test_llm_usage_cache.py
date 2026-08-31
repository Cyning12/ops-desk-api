"""LlmUsage 解析 + Langfuse usage_details（含 cached-input-tokens）。"""

from __future__ import annotations

from app.llm.schema import LlmUsage
from app.ops.tracing import update_current_generation_usage


def test_llm_usage_from_provider_prefers_prompt_cache_hit():
    u = LlmUsage.from_provider_usage(
        {
            "prompt_tokens": 100,
            "completion_tokens": 9,
            "prompt_cache_hit_tokens": 70,
            "prompt_tokens_details": {"cached_tokens": 1},  # 应被 hit 字段优先
        }
    )
    assert u is not None
    assert u.prompt_tokens == 100
    assert u.cached_input_tokens == 70
    assert u.completion_tokens == 9


def test_llm_usage_from_provider_details_fallback():
    u = LlmUsage.from_provider_usage(
        {
            "prompt_tokens": 50,
            "completion_tokens": 2,
            "prompt_tokens_details": {"cached_tokens": 40},
        }
    )
    assert u is not None
    assert u.cached_input_tokens == 40


def test_llm_usage_from_provider_no_cache():
    u = LlmUsage.from_provider_usage({"prompt_tokens": 3, "completion_tokens": 4})
    assert u is not None
    assert u.cached_input_tokens == 0


def test_update_generation_usage_exclusive_cache_key(monkeypatch):
    monkeypatch.setattr("app.ops.tracing.tracing_enabled", lambda: True)
    captured: list = []

    class _Client:
        def update_current_generation(self, **kwargs):
            captured.append(kwargs)

    monkeypatch.setattr("langfuse.get_client", lambda: _Client())

    update_current_generation_usage(
        LlmUsage(prompt_tokens=100, completion_tokens=10, cached_input_tokens=80)
    )

    assert len(captured) == 1
    details = captured[0]["usage_details"]
    assert details["input"] == 20  # 100 - 80
    assert details["output"] == 10
    assert details["cached-input-tokens"] == 80
