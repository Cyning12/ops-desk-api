"""Langfuse 环境键与默认值。"""

from __future__ import annotations

import pytest

from app.ops.tracing import (
    DEFAULT_LANGFUSE_ENV,
    ensure_langfuse_environment,
    langfuse_environment,
)


@pytest.fixture(autouse=True)
def _clear_langfuse_env(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv("LANGFUSE_ENV", raising=False)
    monkeypatch.delenv("LANGFUSE_TRACING_ENVIRONMENT", raising=False)


def test_langfuse_env_defaults_to_prod():
    assert langfuse_environment() == DEFAULT_LANGFUSE_ENV
    assert langfuse_environment() == "prod"


def test_langfuse_env_dev(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("LANGFUSE_ENV", "dev")
    assert langfuse_environment() == "dev"


def test_langfuse_env_syncs_official_sdk_key(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("LANGFUSE_ENV", "dev")
    assert ensure_langfuse_environment() == "dev"
    import os

    assert os.environ["LANGFUSE_TRACING_ENVIRONMENT"] == "dev"


def test_langfuse_env_invalid_falls_back_prod(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("LANGFUSE_ENV", "langfuse-prod")  # 官方禁止 langfuse 前缀
    assert langfuse_environment() == "prod"


def test_tracing_status_line_hides_secrets(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("OPS_CHAT_TRACER", "langfuse")
    monkeypatch.setenv("LANGFUSE_PUBLIC_KEY", "pk-lf-secret")
    monkeypatch.setenv("LANGFUSE_SECRET_KEY", "sk-lf-secret")
    monkeypatch.setenv("LANGFUSE_ENV", "dev")
    from app.ops.tracing import tracing_status_line

    line = tracing_status_line()
    assert "pk-lf-secret" not in line
    assert "sk-lf-secret" not in line
    assert "LANGFUSE_ENV=dev" in line
    assert "keys=yes" in line
    assert "tracing=on" in line


def test_quoted_keys_still_count_as_configured(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("LANGFUSE_PUBLIC_KEY", '"pk-lf-x"')
    monkeypatch.setenv("LANGFUSE_SECRET_KEY", '"sk-lf-y"')
    from app.ops.tracing import _langfuse_configured

    assert _langfuse_configured() is True
