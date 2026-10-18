"""策略包加载器（V1-E D4 · llm 档级试点）。

优先级钉死：``env > 策略包 > 代码默认``。
``OPS_LLM_STRATEGY_PACK`` 未设 / 空 → **不加载**（缺省=现状逐字节）。
路径可相对仓根或绝对路径；schema_version 必须为 ``"0"``。
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any

_logger = logging.getLogger(__name__)

ENV_STRATEGY_PACK = "OPS_LLM_STRATEGY_PACK"
_SCHEMA_VERSION = "0"
_SURFACE = "llm_tiers"

# 进程内缓存：路径 → 解析后的 overlay（None=已判定无包）
_CACHE: dict[str, dict[str, Any] | None] = {}


class StrategyPackError(ValueError):
    """策略包形态非法。"""


def clear_strategy_pack_cache() -> None:
    """测试用：清缓存。"""
    _CACHE.clear()


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _load_yaml(path: Path) -> dict[str, Any]:
    try:
        import yaml
    except ImportError as exc:  # pragma: no cover
        raise StrategyPackError("PyYAML 未安装 · 无法加载策略包") from exc
    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise StrategyPackError(f"策略包不可读: {path}") from exc
    if not isinstance(raw, dict):
        raise StrategyPackError(f"策略包根须为 mapping: {path}")
    return raw


def _validate(raw: dict[str, Any], path: Path) -> dict[str, Any]:
    ver = str(raw.get("schema_version", ""))
    if ver != _SCHEMA_VERSION:
        raise StrategyPackError(
            f"策略包 schema_version 须为 {_SCHEMA_VERSION!r} · 得 {ver!r}: {path}"
        )
    surface = str(raw.get("surface", ""))
    if surface != _SURFACE:
        raise StrategyPackError(f"本波仅支持 surface={_SURFACE!r} · 得 {surface!r}: {path}")
    return {
        "task_tier_models": dict(raw.get("task_tier_models") or {}),
        "task_tier_fallbacks": dict(raw.get("task_tier_fallbacks") or {}),
        "model_unit_prices": dict(raw.get("model_unit_prices") or {}),
        "path": str(path),
    }


def load_llm_tier_pack(*, path: str | None = None) -> dict[str, Any] | None:
    """加载 llm 档级策略包；未配置 → None（零 diff）。"""
    raw_path = (path if path is not None else os.getenv(ENV_STRATEGY_PACK) or "").strip()
    if not raw_path:
        return None
    if raw_path in _CACHE:
        return _CACHE[raw_path]
    p = Path(raw_path)
    if not p.is_absolute():
        p = _repo_root() / p
    if not p.is_file():
        _logger.warning("OPS_LLM_STRATEGY_PACK=%r 文件不存在 · 忽略策略包", raw_path)
        _CACHE[raw_path] = None
        return None
    try:
        overlay = _validate(_load_yaml(p), p)
    except StrategyPackError:
        _CACHE[raw_path] = None
        raise
    _CACHE[raw_path] = overlay
    return overlay


def pack_tier_model(task: str) -> str | None | object:
    """策略包档默认；未加载 / 未声明 → sentinel ``_MISSING``。"""
    pack = load_llm_tier_pack()
    if pack is None:
        return _MISSING
    models = pack.get("task_tier_models") or {}
    if task not in models:
        return _MISSING
    return models[task]


def pack_tier_fallbacks(task: str) -> tuple[str, ...] | None:
    """策略包 fallback 链；未加载 / 未声明 → None（沿用代码默认）。"""
    pack = load_llm_tier_pack()
    if pack is None:
        return None
    fb = pack.get("task_tier_fallbacks") or {}
    if task not in fb:
        return None
    raw = fb[task] or []
    return tuple(str(x) for x in raw)


def pack_unit_price(model: str) -> dict[str, float] | None:
    """策略包单价；未加载 / 未声明 → None。"""
    pack = load_llm_tier_pack()
    if pack is None:
        return None
    prices = pack.get("model_unit_prices") or {}
    entry = prices.get(model)
    if not isinstance(entry, dict):
        return None
    try:
        return {"input": float(entry["input"]), "output": float(entry["output"])}
    except (KeyError, TypeError, ValueError):
        return None


class _MissingType:
    __slots__ = ()

    def __repr__(self) -> str:
        return "<MISSING>"


_MISSING = _MissingType()
