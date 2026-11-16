r"""Skill Registry · 查询面（P2b-T4 真加载器 · 旧 H5 stub API 不保留兼容）。

设计真源：workspace 11-p2b-mcp-skill-design.md 终稿 §6.1/§6.3。

- 加载闸全在 `loader.py`；本模块只做查询与 catalog 摘要合成。
- catalog = 纯文本节（`## 可用技能（摘要）`）追加进 supervisor
  `catalog_block` 字符串（§6.3 · 不动模板资产 · 否 \$skills_block）；
  全文不走 catalog——全文经 `skill_content` trusted 槽注入子任务 prompt
  （§6.4 · 装配面在 `lg_rag/multi/nodes.py::_worker_state`）。
"""

from __future__ import annotations

import logging

from app.ops.skill_registry.loader import (
    SkillDoc,
    get_skills,
    skill_catalog_max_chars,
)

logger = logging.getLogger(__name__)

#: catalog 节首（§6.3 钉死字面 · 测试锚）
CATALOG_HEADER = "## 可用技能（摘要）"
#: 引导行（§6.3：指引 supervisor 在 subtask 声明 skill_ref）
CATALOG_GUIDE = "任务匹配时在 subtask 声明 skill_ref（取值为技能 name），装配面将注入技能全文。"
#: description 单条上限（§6.3 ≤500）
DESCRIPTION_MAX_CHARS = 500


def get_skill(name: str) -> SkillDoc | None:
    """按 name（= plan-JSON skill_ref 取值）取单枚；未知 → None（调用方 fail-open）。"""
    return get_skills().get(name)


def format_skill_catalog(*, max_chars: int | None = None) -> str:
    """合成「## 可用技能（摘要）」节（纯文本 · 供 catalog_block 尾部追加）。

    无可用 skill → 空串（调用方零追加 · off 态逐字节一致由调用方闸保证）；
    整节长度 ≤ `max_chars`（默认 `OPS_SKILL_CATALOG_MAX_CHARS`=4000 ·
    §6.5 合并预算 capability ≤6000 + skill ≤4000 ≤10000），超长截断 + warning。
    """
    limit = max_chars if max_chars is not None else skill_catalog_max_chars()
    skills = get_skills()
    if not skills:
        return ""
    lines = [CATALOG_HEADER, ""]
    for name in sorted(skills):
        doc = skills[name]
        desc = doc.description
        if len(desc) > DESCRIPTION_MAX_CHARS:
            desc = desc[:DESCRIPTION_MAX_CHARS] + "…"
        line = f"- {doc.name}：{desc}"
        if doc.when_to_use:
            line += f"（何时用：{doc.when_to_use}）"
        lines.append(line)
    lines += ["", CATALOG_GUIDE]
    block = "\n".join(lines)
    if len(block) > limit:
        logger.warning(
            "skill_loader: catalog 节 %d 字符超预算 %d — 截断（§6.5 合并预算）",
            len(block),
            limit,
        )
        block = block[:limit]
    return block
