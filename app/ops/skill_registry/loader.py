"""Skill 加载器 · SKILL.md 目录包真加载（P2b-T4 · 11 §6.1/§6.5）。

设计真源：workspace 11-p2b-mcp-skill-design.md 终稿 §6.1（加载闸）/§6.5（env
三件套）· §0.1 R9a（全文 ≤20000 字符拒载）。

加载闸（单文件任一条命中 → 拒载/跳过 + warning，不影响其余文件）：

- 仅目录包形态 `skills/<name>/SKILL.md`（根下裸文件不扫）；
- frontmatter `yaml.safe_load`：`name`/`description` 必填，`name` 须
  kebab-case `^[a-z0-9]+(?:-[a-z0-9]+)*$`；
- **伪造标记拒载**（命中 slots 边界/节首标记字面 → 拒载+warn；**拒载优于
  转义**——trusted 槽静默转义改指令语义不可见 · §6.1 裁定）；
- **全文 ≤20000 字符**（R9a · 超限拒载+warn）；
- 坏文件（读取失败/frontmatter 未闭合/YAML 解析失败/缺必填键）→ warn 跳过。

启动加载、重启生效、无热更新（§6.1 裁剪单：无 rank/chokidar/事件总线/多根）。
env 体例承 `app/ops/goals/inject.py:27-46`（os.getenv 直读 · 无缓存 ·
非法值 warning 回退默认）。
"""

from __future__ import annotations

import logging
import os
import re
from dataclasses import dataclass
from pathlib import Path

import yaml

logger = logging.getLogger(__name__)

# env 三件套（承 goals/inject.py 体例 · 直读无缓存）
ENV_ENABLED = "OPS_SKILL_LOADER_ENABLED"
ENV_ROOT = "OPS_SKILL_LOADER_ROOT"
ENV_CATALOG_MAX_CHARS = "OPS_SKILL_CATALOG_MAX_CHARS"

_TRUTHY = ("1", "true", "yes", "on")
_FALSY = ("0", "false", "no", "off")

#: catalog 摘要节预算（§6.5：capability ≤6000 + skill ≤4000 ≤10000）
DEFAULT_CATALOG_MAX_CHARS = 4000
#: R9a：skill 全文硬上限（超限拒载）
MAX_SKILL_CHARS = 20000

_NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")

#: 伪造标记字面（§6.1：slots 边界 + 节首标记 · 命中即拒载）
_FORGED_MARKERS: tuple[str, ...] = (
    "<slot:",
    "</slot:",
    "[已知事实]",
    "[用户偏好]",
    "[当前目标]",
    "[相似经验]",
)

#: 默认 skill 根 = 相对 api 仓根的 ../ops-desk-workspace/skills（§6.5）；
#: 容器内 WORKDIR /app → 解析为 /ops-desk-workspace/skills（compose 只读卷）。
_DEFAULT_ROOT = Path(__file__).resolve().parents[3].parent / "ops-desk-workspace" / "skills"


@dataclass(frozen=True)
class SkillDoc:
    """一枚加载成功的 skill（目录包 `skills/<name>/SKILL.md`）。"""

    name: str  # frontmatter name（kebab-case · 即 plan-JSON skill_ref 取值）
    description: str  # frontmatter description（必填）
    when_to_use: str  # frontmatter when_to_use（可缺省 = ""）
    content: str  # SKILL.md 全文（含 frontmatter · 走 skill_content trusted 槽）
    path: str  # 来源路径（台账/排障）


def skill_loader_enabled() -> bool:
    """`OPS_SKILL_LOADER_ENABLED`（默认 false · 非法值 warning 回退 false）。

    off 态纪律：调用方保证本模块加载面零触达（loader 调用=0 · supervisor
    system 逐字节一致 · §6.5）。
    """
    raw = os.getenv(ENV_ENABLED, "").strip().lower()
    if not raw:
        return False
    if raw in _TRUTHY:
        return True
    if raw in _FALSY:
        return False
    logger.warning("skill_loader: %s=%r 非法，回退 false", ENV_ENABLED, raw)
    return False


def skill_loader_root() -> Path:
    """`OPS_SKILL_LOADER_ROOT`（默认 ../ops-desk-workspace/skills 相对 api 仓根）。"""
    raw = os.getenv(ENV_ROOT, "").strip()
    if raw:
        return Path(raw).expanduser()
    return _DEFAULT_ROOT


def skill_catalog_max_chars() -> int:
    """`OPS_SKILL_CATALOG_MAX_CHARS`（默认 4000 · 非法/≤0 回退 4000）。"""
    raw = os.getenv(ENV_CATALOG_MAX_CHARS, "").strip()
    if not raw:
        return DEFAULT_CATALOG_MAX_CHARS
    try:
        value = int(raw)
    except ValueError:
        value = -1
    if value <= 0:
        logger.warning(
            "skill_loader: %s=%r 非法，回退 %d",
            ENV_CATALOG_MAX_CHARS,
            raw,
            DEFAULT_CATALOG_MAX_CHARS,
        )
        return DEFAULT_CATALOG_MAX_CHARS
    return value


def _parse_skill_md(path: Path) -> SkillDoc | None:
    """单文件加载；返回 None = 拒载/跳过（warning 已记 · 不影响其余文件）。"""
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        logger.warning("skill_loader: 跳过 %s — 读取失败: %s", path, exc)
        return None
    if len(text) > MAX_SKILL_CHARS:
        logger.warning(
            "skill_loader: 拒载 %s — 全文 %d 字符超上限 %d（R9a）",
            path,
            len(text),
            MAX_SKILL_CHARS,
        )
        return None
    for marker in _FORGED_MARKERS:
        if marker in text:
            logger.warning(
                "skill_loader: 拒载 %s — 命中伪造标记 %r（拒载优于转义 · §6.1）",
                path,
                marker,
            )
            return None
    if not text.startswith("---"):
        logger.warning("skill_loader: 跳过 %s — 缺 frontmatter", path)
        return None
    parts = text.split("---", 2)
    if len(parts) < 3:
        logger.warning("skill_loader: 跳过 %s — frontmatter 未闭合", path)
        return None
    try:
        meta = yaml.safe_load(parts[1])
    except yaml.YAMLError as exc:
        logger.warning("skill_loader: 跳过 %s — frontmatter YAML 解析失败: %s", path, exc)
        return None
    if not isinstance(meta, dict):
        logger.warning("skill_loader: 跳过 %s — frontmatter 非键值映射", path)
        return None
    name = meta.get("name")
    description = meta.get("description")
    if not isinstance(name, str) or not name.strip():
        logger.warning("skill_loader: 跳过 %s — frontmatter 缺 name（必填）", path)
        return None
    if not isinstance(description, str) or not description.strip():
        logger.warning("skill_loader: 跳过 %s — frontmatter 缺 description（必填）", path)
        return None
    name = name.strip()
    if not _NAME_RE.match(name):
        logger.warning(
            "skill_loader: 跳过 %s — name=%r 非 kebab-case（^[a-z0-9]+(?:-[a-z0-9]+)*$）",
            path,
            name,
        )
        return None
    when_to_use = meta.get("when_to_use")
    return SkillDoc(
        name=name,
        description=description.strip(),
        when_to_use=str(when_to_use).strip() if when_to_use else "",
        content=text,
        path=str(path),
    )


def load_skills(root: Path | None = None) -> dict[str, SkillDoc]:
    """扫描 `<root>/<name>/SKILL.md` 建索引（仅目录包形态）。

    根目录不存在 → warning + 空表（§10：不炸启动）。坏文件 warn 跳过，
    不影响其余（§6.1）。
    """
    base = root if root is not None else skill_loader_root()
    if not base.is_dir():
        logger.warning("skill_loader: skill 根目录不存在 %s — 空 catalog（不炸启动 · §10）", base)
        return {}
    skills: dict[str, SkillDoc] = {}
    for skill_md in sorted(base.glob("*/SKILL.md")):
        doc = _parse_skill_md(skill_md)
        if doc is None:
            continue
        if doc.name in skills:
            logger.warning(
                "skill_loader: 跳过 %s — name=%r 与 %s 重名",
                skill_md,
                doc.name,
                skills[doc.name].path,
            )
            continue
        skills[doc.name] = doc
    return skills


_CACHE: dict[str, SkillDoc] | None = None


def get_skills() -> dict[str, SkillDoc]:
    """模块单例：进程内加载一次，重启生效（§6.1 无热更新）。"""
    global _CACHE
    if _CACHE is None:
        _CACHE = load_skills()
    return _CACHE


def reset_skills_cache() -> None:
    """清空单例缓存（测试用 · 生产无热更新不重载）。"""
    global _CACHE
    _CACHE = None
