"""Skill Registry（H5 · NL 匹配 stub + Prompt slot）。"""

from app.ops.skill_registry.registry import (
    SkillEntry,
    load_manifest,
    match_skills,
    skill_prompt_slot,
)

__all__ = ["SkillEntry", "load_manifest", "match_skills", "skill_prompt_slot"]
