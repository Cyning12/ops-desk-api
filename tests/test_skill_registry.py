"""H5 · Skill Registry 单测。"""

from __future__ import annotations

from app.ops.prompts import render
from app.ops.skill_registry import load_manifest, match_skills, skill_prompt_slot


def test_load_manifest_from_docs_skills():
    manifest = load_manifest()
    ids = {e.skill_id for e in manifest}
    assert "s-l0-project-map" in ids


def test_match_skills_keyword():
    manifest = load_manifest()
    hits = match_skills("项目地图 onboarding", manifest=manifest, top_k=2)
    assert hits
    assert any("project-map" in h.skill_id for h in hits)


def test_skill_prompt_slot_integration_with_render():
    manifest = load_manifest()
    hits = match_skills("G-L0 架构", manifest=manifest, top_k=1)
    assert hits
    slot_text = skill_prompt_slot(hits[0].skill_id, manifest=manifest)
    text = render(
        "lg_rag.supervisor.system",
        {"catalog_block": "(无)"},
        slots={"skill": slot_text},
    )
    assert "<!-- slot:skill -->" in text
    assert hits[0].skill_id in text or "Skill" in text


def test_match_empty_query():
    assert match_skills("", manifest=[]) == []
