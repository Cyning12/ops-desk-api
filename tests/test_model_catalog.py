"""model_catalog：SILICONFLOW_MODELS env + 默认兜底。"""

from __future__ import annotations

from app.llm.model_catalog import (
    get_default_model,
    get_models_for_provider,
    parse_siliconflow_models_env,
    resolve_siliconflow_models,
)


def test_default_siliconflow_catalog_starts_with_flash(monkeypatch):
    monkeypatch.delenv("SILICONFLOW_MODELS", raising=False)
    assert get_default_model("siliconflow") == "deepseek-ai/DeepSeek-V4-Flash"
    ids = [m["id"] for m in get_models_for_provider("siliconflow")]
    assert ids[0] == "deepseek-ai/DeepSeek-V4-Flash"
    assert "Qwen/Qwen3.6-27B" in ids


def test_siliconflow_models_env_overrides(monkeypatch):
    monkeypatch.setenv(
        "SILICONFLOW_MODELS",
        "Qwen/Qwen3.6-27B|Qwen Grader,deepseek-ai/DeepSeek-V4-Flash",
    )
    models = resolve_siliconflow_models()
    assert models[0].id == "Qwen/Qwen3.6-27B"
    assert models[0].name == "Qwen Grader"
    assert get_default_model("siliconflow") == "Qwen/Qwen3.6-27B"


def test_siliconflow_models_env_empty_falls_back(monkeypatch):
    monkeypatch.setenv("SILICONFLOW_MODELS", "  ,  ")
    assert parse_siliconflow_models_env("  ,  ") is None
    monkeypatch.setenv("SILICONFLOW_MODELS", "")
    assert get_default_model("siliconflow") == "deepseek-ai/DeepSeek-V4-Flash"
