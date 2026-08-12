"""RAG_FTS_CONFIG：关键词路 regconfig 可配置（默认 simple；影子 A 臂 chinese）。"""
from __future__ import annotations

import pytest

from app.ops.rag.retrieve import _fts_config, _keyword_query


@pytest.fixture(autouse=True)
def _clear_fts_env(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv("RAG_FTS_CONFIG", raising=False)
    monkeypatch.delenv("RAG_KW_EXPAND", raising=False)


def test_fts_config_default_simple():
    assert _fts_config() == "simple"


def test_fts_config_chinese(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("RAG_FTS_CONFIG", "chinese")
    assert _fts_config() == "chinese"


def test_fts_config_invalid_fallback(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("RAG_FTS_CONFIG", "chinese';drop")
    assert _fts_config() == "simple"


def test_keyword_query_default_uses_simple():
    sql, param = _keyword_query("自动压缩")
    assert param == "自动压缩"
    text_sql = str(sql)
    assert "plainto_tsquery('simple'::regconfig" in text_sql
    assert "chinese" not in text_sql


def test_keyword_query_chinese_regconfig(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("RAG_FTS_CONFIG", "chinese")
    sql, param = _keyword_query("自动压缩")
    assert param == "自动压缩"
    text_sql = str(sql)
    assert "plainto_tsquery('chinese'::regconfig" in text_sql
    assert "plainto_tsquery('simple'::regconfig" not in text_sql


def test_keyword_query_expanded_honors_fts_config(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("RAG_FTS_CONFIG", "chinese")
    monkeypatch.setenv("RAG_KW_EXPAND", "true")
    sql, param = _keyword_query("自动压缩被取消")
    text_sql = str(sql)
    assert "to_tsquery('chinese'::regconfig" in text_sql
    assert param  # glossary 展开非空
