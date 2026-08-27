"""H4 · PromptAssembly render 单测。"""

from __future__ import annotations

import pytest

from app.ops.prompts import get_template, render
from app.ops.prompts.render import PromptTemplateNotFoundError


def test_get_template_version():
    tmpl = get_template("lg_rag.supervisor.system")
    assert tmpl.version == "v1"
    assert "Supervisor" in tmpl.body


def test_get_intent_template():
    tmpl = get_template("lg_rag.intent.system")
    assert tmpl.version == "v1"
    assert "Intent" in tmpl.body
    assert "rag/direct/refuse" in tmpl.body


def test_render_supervisor_with_catalog():
    text = render(
        "lg_rag.supervisor.system",
        {"catalog_block": "- mock_get_issue_status：Mock（risk=low）"},
    )
    assert "Capability 目录" in text
    assert "mock_get_issue_status" in text


def test_render_slots_appended():
    text = render(
        "lg_rag.supervisor.system",
        {"catalog_block": "(无)"},
        slots={"skill": "Skill 注入块"},
    )
    assert "<!-- slot:skill -->" in text
    assert "Skill 注入块" in text


def test_render_unknown_template():
    with pytest.raises(PromptTemplateNotFoundError):
        render("nope", {})
