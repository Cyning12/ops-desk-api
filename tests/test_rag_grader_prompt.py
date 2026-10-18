"""grader Prompt 版本切换（v1 基线 / v2 实验）。"""

from __future__ import annotations

from app.ops.rag import grader as grader_mod
from app.ops.rag.grader import (
    GRADER_SYSTEM_V1,
    GRADER_SYSTEM_V2,
    grader_prompt_version,
    grader_system_prompt,
)


def test_default_prompt_is_v1(monkeypatch):
    monkeypatch.delenv("RAG_GRADER_PROMPT", raising=False)
    assert grader_prompt_version() == "v1"
    assert grader_system_prompt() == GRADER_SYSTEM_V1


def test_select_v2(monkeypatch):
    monkeypatch.setenv("RAG_GRADER_PROMPT", "v2")
    assert grader_prompt_version() == "v2"
    assert grader_system_prompt() == GRADER_SYSTEM_V2
    assert "可用证据" in GRADER_SYSTEM_V2
    assert GRADER_SYSTEM_V2 != GRADER_SYSTEM_V1


def test_unknown_falls_back_to_v1(monkeypatch):
    monkeypatch.setenv("RAG_GRADER_PROMPT", "v9")
    assert grader_prompt_version() == "v1"
    assert grader_system_prompt("v9") == GRADER_SYSTEM_V1


def test_compat_alias_is_v1_baseline():
    assert grader_mod._GRADER_SYSTEM == GRADER_SYSTEM_V1
