"""Capability catalog manifest 加载（S3 · Host 路径）。

YAML/JSON → ``register``；Builder **不**解析本模块。
仅 ``kind=local_fn``；adapter 仅
``local_fn:app.ops.capability.defaults:<attr>`` 与
``local_fn:app.ops.capability.lookups:<attr>``。
非法条目 → **整文件失败**（校验完成前不 register）。
禁止每请求 / HTTP 钩子；显式 ``reload_capability_manifest`` 供测试/运维。
"""

from __future__ import annotations

import importlib
import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.ops.capability.adapters.local_fn import LocalFnAdapter
from app.ops.capability.gateway import get_registry, register, unregister
from app.ops.capability.types import CapabilitySpec
from app.ops.tracing import update_current_span_metadata

logger = logging.getLogger(__name__)

BUILTIN_MANIFEST_PATH = (
    Path(__file__).resolve().parent / "manifests" / "builtin.v1.yaml"
)

ALLOWED_KIND = "local_fn"
ADAPTER_PREFIX_DEFAULTS = "local_fn:app.ops.capability.defaults:"
ADAPTER_PREFIX_LOOKUPS = "local_fn:app.ops.capability.lookups:"
ADAPTER_PREFIXES = (ADAPTER_PREFIX_DEFAULTS, ADAPTER_PREFIX_LOOKUPS)
ADAPTER_PREFIX = ADAPTER_PREFIX_DEFAULTS  # 兼容旧名：defaults 前缀
_PREFIX_TO_MODULE = {
    ADAPTER_PREFIX_DEFAULTS: "app.ops.capability.defaults",
    ADAPTER_PREFIX_LOOKUPS: "app.ops.capability.lookups",
}

# 密钥形字段：loader 拒绝进仓形状；亦不读 env 密钥。
_SECRET_KEYS = frozenset(
    {
        "api_key",
        "apikey",
        "secret",
        "password",
        "token",
        "access_token",
        "auth_token",
        "credential",
        "credentials",
        "private_key",
        "secret_key",
    }
)

_LAST_META: dict[str, Any] = {
    "version": None,
    "capability_manifest_count": 0,
}


class ManifestError(ValueError):
    """整文件失败：非法 manifest（不半套注册）。"""


@dataclass(frozen=True)
class ManifestLoadResult:
    """一次成功 load/reload 的观测结果。"""

    version: int | str | None
    capability_manifest_count: int
    registered_ids: tuple[str, ...]
    skipped_existing: tuple[str, ...]
    skipped_disabled: tuple[str, ...]
    path: str


@dataclass(frozen=True)
class _PendingEntry:
    spec: CapabilitySpec
    adapter: LocalFnAdapter


def get_capability_manifest_metadata() -> dict[str, Any]:
    """模块级 metadata：最近一次成功 load/reload 的 version + count。"""
    return dict(_LAST_META)


def load_capability_manifest(path: str | Path) -> ManifestLoadResult:
    """解析 YAML/JSON 并 register；已存在 id 跳过（幂等）。非法 → 整文件失败。"""
    target = Path(path)
    version, pending = _parse_and_validate(target)
    return _commit(target, version, pending, replace=False)


def reload_capability_manifest(
    path: str | Path | None = None,
) -> ManifestLoadResult:
    """显式重载（测试/运维）。先校验再 unregister 本文件 id，再 register。

    **不是** HTTP 钩子，也禁止在请求路径调用。
    """
    target = Path(path) if path is not None else BUILTIN_MANIFEST_PATH
    version, pending = _parse_and_validate(target)
    for entry in pending:
        unregister(entry.spec.capability_id)
    return _commit(target, version, pending, replace=True)


def _commit(
    target: Path,
    version: int | str | None,
    pending: list[_PendingEntry],
    *,
    replace: bool,
) -> ManifestLoadResult:
    registry = get_registry()
    registered: list[str] = []
    skipped_existing: list[str] = []
    skipped_disabled: list[str] = []
    enabled_count = 0
    for entry in pending:
        cid = entry.spec.capability_id
        if not entry.spec.enabled:
            skipped_disabled.append(cid)
            continue
        enabled_count += 1
        if not replace and registry.get(cid) is not None:
            skipped_existing.append(cid)
            logger.debug("manifest skip already registered: %s", cid)
            continue
        register(entry.spec, entry.adapter)
        registered.append(cid)

    _LAST_META["version"] = version
    _LAST_META["capability_manifest_count"] = enabled_count
    update_current_span_metadata(
        {
            "capability_manifest_version": version,
            "capability_manifest_count": enabled_count,
        }
    )
    return ManifestLoadResult(
        version=version,
        capability_manifest_count=enabled_count,
        registered_ids=tuple(registered),
        skipped_existing=tuple(skipped_existing),
        skipped_disabled=tuple(skipped_disabled),
        path=str(target),
    )


def _parse_and_validate(
    path: Path,
) -> tuple[int | str | None, list[_PendingEntry]]:
    """读盘 + 全量校验；失败时 **零** register。"""
    if not path.is_file():
        raise ManifestError(f"manifest 文件不存在: {path}")
    text = path.read_text(encoding="utf-8")
    data = _decode(path, text)
    if not isinstance(data, dict):
        raise ManifestError(f"manifest 根必须是 mapping: {path}")
    _reject_secret_keys(data, where="root")

    raw_caps = data.get("capabilities")
    if not isinstance(raw_caps, list):
        raise ManifestError(f"manifest.capabilities 必须是 list: {path}")

    pending: list[_PendingEntry] = []
    seen: set[str] = set()
    for idx, raw in enumerate(raw_caps):
        loc = f"capabilities[{idx}]"
        if not isinstance(raw, dict):
            raise ManifestError(f"{loc} 必须是 mapping: {path}")
        _reject_secret_keys(raw, where=loc)
        entry = _entry_from_raw(raw, loc=loc)
        cid = entry.spec.capability_id
        if cid in seen:
            raise ManifestError(f"{loc} 重复 id: {cid}")
        seen.add(cid)
        pending.append(entry)
    return data.get("version"), pending


def _decode(path: Path, text: str) -> Any:
    suffix = path.suffix.lower()
    if suffix == ".json":
        try:
            return json.loads(text)
        except json.JSONDecodeError as exc:
            raise ManifestError(f"JSON 解析失败: {path}: {exc}") from exc
    try:
        import yaml
    except ImportError as exc:  # pragma: no cover
        raise ManifestError("需要 PyYAML：yaml.safe_load") from exc
    try:
        return yaml.safe_load(text)
    except yaml.YAMLError as exc:
        raise ManifestError(f"YAML 解析失败: {path}: {exc}") from exc


def _reject_secret_keys(mapping: dict[str, Any], *, where: str) -> None:
    for key in mapping:
        normalized = str(key).strip().lower().replace("-", "_")
        if normalized in _SECRET_KEYS or "password" in normalized or "secret" in normalized:
            raise ManifestError(f"{where} 禁止密钥形字段: {key}")


def _entry_from_raw(raw: dict[str, Any], *, loc: str) -> _PendingEntry:
    cid = str(raw.get("id") or "").strip()
    if not cid:
        raise ManifestError(f"{loc} 缺 id")
    kind = str(raw.get("kind") or "").strip()
    if kind != ALLOWED_KIND:
        raise ManifestError(f"{loc} 未知 kind（仅 {ALLOWED_KIND}）: {kind or '(空)'}")
    adapter_ref = str(raw.get("adapter") or "").strip()
    fn = _resolve_local_fn_adapter(adapter_ref, loc=loc)
    tags_raw = raw.get("tags") or []
    if not isinstance(tags_raw, list):
        raise ManifestError(f"{loc} tags 必须是 list")
    tags = tuple(str(t) for t in tags_raw)
    enabled = bool(raw.get("enabled", True))
    args_schema = raw.get("args_schema")
    if args_schema is not None and not isinstance(args_schema, dict):
        raise ManifestError(f"{loc} args_schema 必须是 mapping")
    tenant_scoped = bool(raw.get("tenant_scoped", False))
    spec = CapabilitySpec(
        capability_id=cid,
        kind=kind,
        description=str(raw.get("description") or ""),
        args_schema=args_schema,
        tags=tags,
        risk_level=str(raw.get("risk_level") or "low"),
        enabled=enabled,
        tenant_scoped=tenant_scoped,
    )
    return _PendingEntry(spec=spec, adapter=LocalFnAdapter(fn))


def _resolve_local_fn_adapter(ref: str, *, loc: str):
    """仅允许 defaults / lookups 模块上的公开可调用属性；禁止任意 import / eval。"""
    matched: tuple[str, str] | None = None
    for prefix, mod_name in _PREFIX_TO_MODULE.items():
        if ref.startswith(prefix):
            matched = (prefix, mod_name)
            break
    if matched is None:
        raise ManifestError(f"{loc} 非法 adapter: {ref or '(空)'}")
    prefix, mod_name = matched
    attr = ref[len(prefix) :]
    if not attr.isidentifier() or attr.startswith("_"):
        raise ManifestError(f"{loc} 非法 adapter attr: {attr or '(空)'}")
    # 延迟 import 目标模块，避免与 defaults.ensure 循环依赖
    mod = importlib.import_module(mod_name)
    fn = getattr(mod, attr, None)
    if not callable(fn):
        raise ManifestError(f"{loc} adapter 属性不可调用或不存在: {attr}")
    return fn
