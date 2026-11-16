"""Skill Registry（P2b-T4 · SKILL.md 目录包真加载器 + catalog 查询面）。

旧 H5 stub API（SkillEntry/load_manifest/match_skills/skill_prompt_slot）
不保留兼容（§6.2）；加载闸见 `loader.py` 模块 docstring。
"""

from app.ops.skill_registry.loader import (
    DEFAULT_CATALOG_MAX_CHARS,
    ENV_CATALOG_MAX_CHARS,
    ENV_ENABLED,
    ENV_ROOT,
    MAX_SKILL_CHARS,
    SkillDoc,
    get_skills,
    load_skills,
    reset_skills_cache,
    skill_catalog_max_chars,
    skill_loader_enabled,
    skill_loader_root,
)
from app.ops.skill_registry.registry import (
    CATALOG_GUIDE,
    CATALOG_HEADER,
    DESCRIPTION_MAX_CHARS,
    format_skill_catalog,
    get_skill,
)

__all__ = [
    "CATALOG_GUIDE",
    "CATALOG_HEADER",
    "DEFAULT_CATALOG_MAX_CHARS",
    "DESCRIPTION_MAX_CHARS",
    "ENV_CATALOG_MAX_CHARS",
    "ENV_ENABLED",
    "ENV_ROOT",
    "MAX_SKILL_CHARS",
    "SkillDoc",
    "format_skill_catalog",
    "get_skill",
    "get_skills",
    "load_skills",
    "reset_skills_cache",
    "skill_catalog_max_chars",
    "skill_loader_enabled",
    "skill_loader_root",
]
