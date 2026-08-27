"""Skill Registry · 元数据索引 + NL 匹配 stub（H5）。"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

_DEFAULT_SKILLS_ROOT = Path(__file__).resolve().parents[3] / "docs" / "skills"


@dataclass(frozen=True)
class SkillEntry:
    skill_id: str
    description: str
    triggers: tuple[str, ...]


def _parse_frontmatter_block(block: str) -> dict[str, str]:
    """轻量 YAML  frontmatter（仅 key: value 行 · 无 PyYAML 依赖）。"""
    out: dict[str, str] = {}
    for line in block.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if ":" not in line:
            continue
        key, val = line.split(":", 1)
        out[key.strip()] = val.strip()
    return out


def _parse_skill_md(path: Path) -> SkillEntry | None:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return None
    parts = text.split("---", 2)
    if len(parts) < 3:
        return None
    meta = _parse_frontmatter_block(parts[1])
    skill_id = meta.get("name") or path.parent.name
    description = meta.get("description") or skill_id
    triggers_raw = meta.get("triggers", "")
    triggers = tuple(t for t in re.split(r"[,;]", triggers_raw) if t.strip())
    return SkillEntry(
        skill_id=str(skill_id),
        description=str(description),
        triggers=triggers,
    )


def load_manifest(*, root: Path | None = None) -> list[SkillEntry]:
    """扫描 ``docs/skills/**/SKILL.md`` 建索引。"""
    base = root or _DEFAULT_SKILLS_ROOT
    if not base.is_dir():
        return []
    entries: list[SkillEntry] = []
    for skill_md in sorted(base.glob("**/SKILL.md")):
        entry = _parse_skill_md(skill_md)
        if entry is not None:
            entries.append(entry)
    return entries


def match_skills(
    query: str,
    manifest: list[SkillEntry] | None = None,
    *,
    top_k: int = 3,
) -> list[SkillEntry]:
    """v0 关键词匹配（description / triggers / id）。"""
    items = manifest if manifest is not None else load_manifest()
    q = (query or "").strip().lower()
    if not q:
        return []

    scored: list[tuple[int, SkillEntry]] = []
    for entry in items:
        score = 0
        blob = " ".join([entry.skill_id, entry.description, *entry.triggers]).lower()
        for token in q.split():
            if len(token) < 2:
                continue
            if token in blob:
                score += 1
        if score > 0:
            scored.append((score, entry))
    scored.sort(key=lambda x: (-x[0], x[1].skill_id))
    return [e for _, e in scored[: max(top_k, 0)]]


def skill_prompt_slot(skill_id: str, *, manifest: list[SkillEntry] | None = None) -> str:
    """匹配后注入 Prompt 的 slot 文本（非完整 SKILL 引擎）。"""
    items = manifest if manifest is not None else load_manifest()
    for entry in items:
        if entry.skill_id == skill_id:
            return f"[Skill {entry.skill_id}] {entry.description}"
    return f"[Skill {skill_id}] (unknown)"
