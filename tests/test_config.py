"""Tests for app configuration behavior."""
from __future__ import annotations

from app.config import Settings
from app.llm.model_catalog import get_default_model


def test_settings_empty_model_falls_back_to_default() -> None:
    """OPS_LLM_MODEL='' (empty string from compose/env) falls back to catalog default."""
    s = Settings(ops_llm_model="")
    assert s.ops_llm_model == get_default_model(s.ops_llm_provider)
    assert s.ops_llm_model != ""
