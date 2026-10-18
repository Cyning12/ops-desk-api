"""Prompt 资产加载器：运行时读 ``app/ops/prompts/assets/<template_id>.md``。

纪律（task prompt-asset-roadmap-p1 · SPEC §2 D2/D3）：
- 缺文件 / front-matter 缺字段 / 空 body / version 非 ``v<N>`` →
  :class:`PromptAssetError` 显式炸，点名路径与 template_id
  （packs.py FRAGMENT 显式炸先例），**禁止静默降级为空串**。
- template_id 白名单来自 registry 键（``templates._TEMPLATE_IDS``）；
  文件名仅允许 ``[a-z0-9_.]``，**不接受外部路径入参**（无路径穿越面）。
- 加载结果 lru_cache 缓存；``clear_asset_cache()`` 供测试 / future reload
  清缓存后重读生效。
"""

from __future__ import annotations

import re
from functools import cache
from pathlib import Path

_ASSETS_DIR = Path(__file__).resolve().parent / "assets"
_ID_RE = re.compile(r"[a-z0-9_]+(\.[a-z0-9_]+)*")
_VERSION_RE = re.compile(r"v\d+")


class PromptAssetError(RuntimeError):
    """prompt 资产缺失或形态非法（路径与 template_id 随消息点名）。"""


def _parse_front_matter(text: str, path: Path) -> tuple[dict[str, str], str]:
    """解析 ``---`` 包裹的 ``key: value`` front-matter，返回 (meta, body)。"""
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        raise PromptAssetError(f"prompt 资产缺 front-matter 起始 ---: {path}")
    meta: dict[str, str] = {}
    end: int | None = None
    for i in range(1, len(lines)):
        line = lines[i]
        if line.strip() == "---":
            end = i
            break
        if not line.strip():
            continue
        key, sep, value = line.partition(":")
        if not sep or not key.strip():
            raise PromptAssetError(f"prompt 资产 front-matter 行非法: {path}: {line!r}")
        meta[key.strip()] = value.strip()
    if end is None:
        raise PromptAssetError(f"prompt 资产缺 front-matter 结束 ---: {path}")
    return meta, "\n".join(lines[end + 1 :]).strip()


@cache
def load_asset(template_id: str) -> tuple[str, str]:
    """读资产文件，返回 ``(version, body)``；缺失/形态非法显式炸。"""
    if not _ID_RE.fullmatch(template_id):
        raise PromptAssetError(f"非法 template_id（拒绝路径入参）: {template_id!r}")
    path = _ASSETS_DIR / f"{template_id}.md"
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise PromptAssetError(
            f"prompt 资产缺失或不可读: {path} (template_id={template_id})"
        ) from exc
    meta, body = _parse_front_matter(text, path)
    for field in ("template_id", "version"):
        if not meta.get(field):
            raise PromptAssetError(
                f"prompt 资产 front-matter 缺字段 {field}: {path} (template_id={template_id})"
            )
    if meta["template_id"] != template_id:
        raise PromptAssetError(
            f"prompt 资产 front-matter template_id 与文件名不符: {path} "
            f"(front-matter={meta['template_id']!r}, file={template_id!r})"
        )
    if not _VERSION_RE.fullmatch(meta["version"]):
        raise PromptAssetError(
            f"prompt 资产 version 非 v<N> 格式: {path} (version={meta['version']!r})"
        )
    if not body:
        raise PromptAssetError(f"prompt 资产 body 为空: {path} (template_id={template_id})")
    return meta["version"], body


def clear_asset_cache() -> None:
    """清加载缓存（测试 / future reload 用；清后重读文件生效）。"""
    load_asset.cache_clear()
