"""Capability catalog manifest 加载（S3 · Host 路径；H4 · 多文件 + http）。

YAML/JSON → ``register``；Builder **不**解析本模块。
``kind`` 支持 ``local_fn``（引用白名单模块上的函数）与 ``http``（内联声明，
由 ``GenericHttpAdapter`` 解析）。

**一个 loader、多份 manifest、同一个注册表**：
``local_fn`` 随代码发布、``http``（老 OA 等）随业务接入变，两者变更频率、
review 边界、失败域都不同，因此按域拆文件。但 schema、注册表、加载入口
**保持唯一**——只分文件边界，不分格式。

失败语义：
- **单文件整文件失败**：校验完成前不 register（不留半套）。
- **多文件互相隔离**：``load_capability_manifests`` 逐文件 try——坏一份
  不带崩别的（这是拆文件的首要理由）。

禁止每请求 / HTTP 钩子；显式 ``reload_capability_manifest`` 供测试/运维。
**能力清单变更后必须重启或显式 reload，不允许自动热加载**——
热加载意味着「改配置即改权限」，review 就白做了。
"""

from __future__ import annotations

import importlib
import json
import logging
import os
import re
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any

from app.ops.capability import fallback as fallback_mod
from app.ops.capability.adapters.http_generic import (
    HOST_INJECTED_VARS,
    GenericHttpAdapter,
)
from app.ops.capability.adapters.local_fn import LocalFnAdapter
from app.ops.capability.errors import STABLE_ERROR_CODES
from app.ops.capability.gateway import get_registry, register, unregister
from app.ops.capability.types import (
    CLASSIFICATION_LEVELS,
    EXECUTION_TYPES,
    RISK_LEVELS,
    SIDE_EFFECTS,
    WRITE_SIDE_EFFECTS,
    CapabilitySpec,
)
from app.ops.capability.visibility import VISIBILITY_KEYS
from app.ops.tracing import update_current_span_metadata

logger = logging.getLogger(__name__)

MANIFEST_DIR = Path(__file__).resolve().parent / "manifests"
BUILTIN_MANIFEST_PATH = MANIFEST_DIR / "builtin.v1.yaml"

# 显式文件列表（**禁止目录扫描**：往目录丢个文件就生效 = 绕过 review）。
# 额外清单由 env 显式给出；未配置 → 空（默认不动存量）。
DEFAULT_MANIFEST_FILES: tuple[Path, ...] = (BUILTIN_MANIFEST_PATH,)
_ENV_EXTRA_MANIFESTS = "OPS_CAPABILITY_EXTRA_MANIFESTS"

# kind → 适配器形态。kind 是**适配器类型**，不是业务域（业务域放 tags）。
ALLOWED_KINDS: frozenset[str] = frozenset({"local_fn", "http"})
ADAPTER_PREFIX_DEFAULTS = "local_fn:app.ops.capability.defaults:"
ADAPTER_PREFIX_LOOKUPS = "local_fn:app.ops.capability.lookups:"
ADAPTER_PREFIXES = (ADAPTER_PREFIX_DEFAULTS, ADAPTER_PREFIX_LOOKUPS)
ADAPTER_PREFIX = ADAPTER_PREFIX_DEFAULTS  # 兼容旧名：defaults 前缀
_PREFIX_TO_MODULE = {
    ADAPTER_PREFIX_DEFAULTS: "app.ops.capability.defaults",
    ADAPTER_PREFIX_LOOKUPS: "app.ops.capability.lookups",
}

# 能力 id 命名规范：小写字母开头 + 小写字母/数字/下划线，可用点分域（域.对象.动作）。
# 同一份正则同时接受历史扁平 id（如 ``reload_cap``），不强制点分。
_CAPABILITY_ID_RE = re.compile(r"^[a-z][a-z0-9_]*(\.[a-z][a-z0-9_]*)*$")

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

# ---- http 块 ----
_ALLOWED_METHODS = frozenset({"GET", "POST"})
_TENANT_PARAM_IN = frozenset({"query", "body", "header"})
# auth 的值必须是**凭证名**（不是密钥本身）
_AUTH_NAME_RE = re.compile(r"^[a-z][a-z0-9_]{0,63}$")
_AUTH_VALUE_DENY = ("bearer", "sk-", "ghp_", "-----begin", "basic ")
_BASE_URL_NAME_RE = re.compile(r"^[A-Z][A-Z0-9_]{0,63}$")

_LAST_META: dict[str, Any] = {
    "version": None,
    "capability_manifest_count": 0,
}

# 每个文件实际注册了哪些 id（reload 时只注销**本文件**的，避免误伤别的清单）
_FILE_IDS: dict[str, tuple[str, ...]] = {}

# 加载失败集（path → error）：如实反映「当前在册表是怎么来的」。
# load_capability_manifests 逐文件失败即留存；该文件任何一次成功 _commit
# （load/reload）即清除其记录。禁无理由自动清零（契约3 · catalog-manifest-errors-surface）。
_MANIFEST_LOAD_ERRORS: dict[str, str] = {}


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
class MultiManifestLoadResult:
    """多文件加载结果：逐文件成败可见（失败不带崩别的文件）。"""

    loaded: tuple[ManifestLoadResult, ...]
    failed: tuple[tuple[str, str], ...]  # (path, error)

    @property
    def ok(self) -> bool:
        return not self.failed


@dataclass(frozen=True)
class _PendingEntry:
    spec: CapabilitySpec
    adapter: Any


def get_capability_manifest_metadata() -> dict[str, Any]:
    """模块级 metadata：最近一次成功 load/reload 的 version + count。"""
    return dict(_LAST_META)


def get_manifest_load_errors() -> list[dict[str, str]]:
    """当前 manifest 加载失败集（[{path, error}]），按 path 排序（多副本对拍稳定）。

    只读视图：不改内部状态；失败原因原样留存（不透 adapter/local_fn 装配细节，
    校验报错本身就不含这些子串）。
    """
    return [
        {"path": path, "error": _MANIFEST_LOAD_ERRORS[path]}
        for path in sorted(_MANIFEST_LOAD_ERRORS)
    ]


def extra_manifest_paths() -> tuple[Path, ...]:
    """env 显式声明的额外清单（逗号分隔）；未配置 → 空。

    与 ``OPS_CAPABILITY_MCP_ENABLED`` 同一约定：默认关，CI 不加载外部清单。
    """
    raw = os.environ.get(_ENV_EXTRA_MANIFESTS, "")
    parts = [p.strip() for p in raw.split(",") if p.strip()]
    return tuple(Path(p) for p in parts)


def load_extra_manifests_from_env() -> MultiManifestLoadResult | None:
    """启动期钩子：按 env 加载额外清单；未配置返回 None（零影响）。"""
    paths = extra_manifest_paths()
    if not paths:
        return None
    return load_capability_manifests(paths)


def load_capability_manifest(path: str | Path) -> ManifestLoadResult:
    """解析 YAML/JSON 并 register；已存在 id 跳过（幂等）。非法 → 整文件失败。"""
    target = Path(path)
    version, pending = _parse_and_validate(target)
    return _commit(target, version, pending, replace=False)


def load_capability_manifests(
    paths: list[str | Path] | tuple[str | Path, ...],
) -> MultiManifestLoadResult:
    """逐文件加载；**单文件失败不影响其它文件**（失败域隔离）。

    跨文件重复 id：后出现的文件视为失败（避免「先后顺序决定谁生效」的隐性行为）。
    """
    loaded: list[ManifestLoadResult] = []
    failed: list[tuple[str, str]] = []
    claimed: dict[str, str] = {}
    for raw_path in paths:
        target = Path(raw_path)
        try:
            version, pending = _parse_and_validate(target)
            declared = [e.spec.capability_id for e in pending if e.spec.enabled]
            clash = [cid for cid in declared if cid in claimed]
            if clash:
                raise ManifestError(f"跨文件重复 id（已被 {claimed[clash[0]]} 声明）: {clash[0]}")
            for cid in declared:
                claimed[cid] = str(target)
            loaded.append(_commit(target, version, pending, replace=False))
        except ManifestError as exc:
            failed.append((str(target), str(exc)))
            _MANIFEST_LOAD_ERRORS[str(target)] = str(exc)
            logger.error("manifest 加载失败（已跳过该文件）: %s: %s", target, exc)
    return MultiManifestLoadResult(loaded=tuple(loaded), failed=tuple(failed))


def reload_capability_manifest(
    path: str | Path | None = None,
) -> ManifestLoadResult:
    """显式重载（测试/运维）。先校验，再注销**本文件**此前的 id，再 register。

    **不是** HTTP 钩子，也禁止在请求路径调用。
    """
    target = Path(path) if path is not None else BUILTIN_MANIFEST_PATH
    version, pending = _parse_and_validate(target)
    # 关键：按 _FILE_IDS 注销本文件此前注册的 id。
    # 若只注销「本次声明的 id」，则文件里被删掉的旧能力会永久残留。
    for cid in _FILE_IDS.get(str(target), ()):
        unregister(cid)
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

    _FILE_IDS[str(target)] = tuple(registered)
    # 本文件加载成功 → 其历史失败记录失效（契约3：reload 成功清该文件记录）
    _MANIFEST_LOAD_ERRORS.pop(str(target), None)
    _LAST_META["version"] = version
    _LAST_META["capability_manifest_count"] = enabled_count
    update_current_span_metadata(
        {
            "capability_manifest_version": version,
            "capability_manifest_count": enabled_count,
            "capability_manifest_path": str(target),
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


def _validate_output_schema(block: dict[str, Any], *, loc: str) -> None:
    """V10：结果契约形状校验。

    校验意图是**防"契约拼错等于没有契约"**：路径写错、min_items 不是整数、
    required 不是列表——这些在运行期都表现为"契约静默不生效"，最难发现。
    """
    required = block.get("required")
    if required is not None:
        # ``required: []`` 也要拒：声明了 required 却不含任何路径 = 一个什么都不查
        # 的契约，和拼错属于同一类静默失效（看起来有契约，实际没有）。
        # 注意 ``output_schema: {}``（只写 empty_is_suspicious）是**合法**的——
        # 那是"没有必填字段，但空结果可疑"，是一个真实有意义的契约。
        if not isinstance(required, list) or not required:
            raise ManifestError(f"{loc} V10: required 必须是**非空**列表（空列表等于没契约）")
        if not all(isinstance(x, str) and x.strip() for x in required):
            raise ManifestError(f"{loc} V10: required 必须是非空字符串列表")
        for expr in required:
            if not str(expr).lstrip().startswith("$"):
                raise ManifestError(f"{loc} V10: required 路径必须以 $ 开头（当前 {expr!r}）")

    min_items = block.get("min_items")
    if min_items is not None:
        if not isinstance(min_items, dict):
            raise ManifestError(f"{loc} V10: min_items 必须是 mapping（路径 → 条数）")
        for expr, want in min_items.items():
            if not str(expr).lstrip().startswith("$"):
                raise ManifestError(f"{loc} V10: min_items 路径必须以 $ 开头（当前 {expr!r}）")
            try:
                n = int(want)
            except (TypeError, ValueError):
                raise ManifestError(
                    f"{loc} V10: min_items[{expr!r}] 必须是整数（当前 {want!r}）"
                ) from None
            if n < 0:
                raise ManifestError(f"{loc} V10: min_items[{expr!r}] 不得为负")

    unknown = set(block) - {"required", "min_items", "empty_is_suspicious"}
    if unknown:
        raise ManifestError(
            f"{loc} V10: output_schema 未知字段 {sorted(unknown)}（拼错的字段会让契约静默失效）"
        )


def _validate_fallback(block: dict[str, Any], *, loc: str) -> None:
    """V11：降级声明形状校验。

    校验意图与 V10 相同——防「声明拼错等于没有声明」。降级是**静默**改变结果的
    机制（ok=True 但内容不是真的），一个拼错的降级声明比没有降级更危险：
    要么长久不生效（以为有兜底其实没有），要么降级到错误的目标。
    """
    action = str(block.get("action") or fallback_mod.ACTION_NONE).strip()
    if action not in fallback_mod.ACTIONS:
        raise ManifestError(
            f"{loc} V11: action 非法"
            f"（仅 {', '.join(sorted(fallback_mod.ACTIONS))}）: {action or '(空)'}"
        )

    # 字段名是 ``triggers`` 不是 ``on``：YAML 1.1 会把裸键 ``on`` 当布尔 True，
    # 声明会静默变成 ``{True: [...]}`` 而从不被读到。
    triggers = block.get("triggers")
    if triggers is not None:
        if not isinstance(triggers, list) or not triggers:
            raise ManifestError(f"{loc} V11: triggers 必须是非空列表（触发条件）")
        bad = [x for x in triggers if str(x).strip() not in fallback_mod.TRIGGERS]
        if bad:
            raise ManifestError(
                f"{loc} V11: triggers 含未知触发条件 {bad}"
                f"（仅 {', '.join(sorted(fallback_mod.TRIGGERS))}）——"
                "框架不接受业务发明新的「不可用」"
            )

    depth = block.get("max_depth")
    if depth is not None:
        try:
            n = int(depth)
        except (TypeError, ValueError):
            raise ManifestError(f"{loc} V11: max_depth 必须是整数（当前 {depth!r}）") from None
        if n < 1 or n > fallback_mod.MAX_DEPTH_CEILING:
            raise ManifestError(
                f"{loc} V11: max_depth 必须在 1..{fallback_mod.MAX_DEPTH_CEILING}"
                f"（当前 {n}）——链条必须有界（B3）"
            )

    target = block.get("capability_id")
    args_map = block.get("args_map")
    ttl = block.get("ttl_seconds")
    value = block.get("value")

    if action == fallback_mod.ACTION_CAPABILITY:
        if not str(target or "").strip():
            raise ManifestError(f"{loc} V11: action=capability 必须声明 capability_id")
        if not _CAPABILITY_ID_RE.match(str(target).strip()):
            raise ManifestError(
                f"{loc} V11: capability_id 非法（须小写字母开头 + 点分域）: {target}"
            )
        if args_map is not None:
            if not isinstance(args_map, dict) or not args_map:
                raise ManifestError(f"{loc} V11: args_map 必须是非空 mapping")
            if not all(isinstance(k, str) and isinstance(v, str) for k, v in args_map.items()):
                raise ManifestError(f"{loc} V11: args_map 必须是 str→str（目标参数名 ← 源参数名）")
    else:
        if target is not None:
            raise ManifestError(f"{loc} V11: 只有 action=capability 可声明 capability_id")
        if args_map is not None:
            raise ManifestError(f"{loc} V11: 只有 action=capability 可声明 args_map")

    if action == fallback_mod.ACTION_CACHE:
        if ttl is not None:
            try:
                if int(ttl) <= 0:
                    raise ValueError
            except (TypeError, ValueError):
                raise ManifestError(
                    f"{loc} V11: ttl_seconds 必须是正整数（当前 {ttl!r}）"
                ) from None
    elif ttl is not None:
        raise ManifestError(f"{loc} V11: 只有 action=cache 可声明 ttl_seconds")

    if action == fallback_mod.ACTION_STATIC:
        if "value" not in block:
            raise ManifestError(f"{loc} V11: action=static 必须声明 value")
    elif value is not None:
        raise ManifestError(f"{loc} V11: 只有 action=static 可声明 value")

    unknown = set(block) - {
        "triggers",
        "action",
        "capability_id",
        "args_map",
        "max_depth",
        "ttl_seconds",
        "value",
    }
    if unknown:
        raise ManifestError(
            f"{loc} V11: fallback 未知字段 {sorted(unknown)}（拼错的字段会让降级静默失效）"
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
    """拒绝「密钥形字段」的**键名**（不看值）。

    精确匹配 ``_SECRET_KEYS``，并对 ``password`` / ``secret`` / ``token`` /
    ``credential`` 做**子串**匹配——这样 ``credential_ref`` / ``auth_token_ref``
    这类「看起来像放密钥的字段」也会被拦下。HTTP 能力声明凭证请用 ``auth``。
    """
    for key in mapping:
        normalized = str(key).strip().lower().replace("-", "_")
        if normalized in _SECRET_KEYS or any(
            s in normalized for s in ("password", "secret", "token", "credential")
        ):
            raise ManifestError(f"{where} 禁止密钥形字段: {key}")


def _one_of(value: Any, allowed: frozenset[str], *, default: str, loc: str, field: str) -> str:
    text = str(value if value is not None else default).strip()
    if text not in allowed:
        raise ManifestError(
            f"{loc} {field} 非法（仅 {', '.join(sorted(allowed))}）: {text or '(空)'}"
        )
    return text


def _entry_from_raw(raw: dict[str, Any], *, loc: str) -> _PendingEntry:
    cid = str(raw.get("id") or "").strip()
    if not cid:
        raise ManifestError(f"{loc} 缺 id")
    if not _CAPABILITY_ID_RE.match(cid):
        raise ManifestError(
            f"{loc} 非法 id（须小写字母开头 + 小写字母/数字/下划线，可用点分域）: {cid}"
        )
    kind = str(raw.get("kind") or "").strip()
    if kind not in ALLOWED_KINDS:
        raise ManifestError(
            f"{loc} 未知 kind（仅 {', '.join(sorted(ALLOWED_KINDS))}）: {kind or '(空)'}"
        )

    tags_raw = raw.get("tags") or []
    if not isinstance(tags_raw, list):
        raise ManifestError(f"{loc} tags 必须是 list")
    args_schema = raw.get("args_schema")
    if args_schema is not None and not isinstance(args_schema, dict):
        raise ManifestError(f"{loc} args_schema 必须是 mapping")
    if args_schema is None:
        raise ManifestError(f"{loc} 缺 args_schema（无 schema 的能力无法进 FC 目录）")

    # when_to_use 让模型「能选中」。没有它，能力等于只有 id 和一行描述。
    when_to_use = str(raw.get("when_to_use") or "").strip()
    if not when_to_use:
        raise ManifestError(f"{loc} 缺 when_to_use（模型选择依据，不可省）")

    # 结果契约（P0-1）。在**加载期**就把形状钉死：一个拼错的契约等于没有契约，
    # 而"契约没生效"是静默的——调用照常成功，只是不再校验。
    output_schema_raw = raw.get("output_schema")
    if output_schema_raw is not None and not isinstance(output_schema_raw, dict):
        raise ManifestError(f"{loc} V10: output_schema 必须是 mapping")
    if isinstance(output_schema_raw, dict):
        _validate_output_schema(output_schema_raw, loc=f"{loc}.output_schema")

    http_block = raw.get("http")
    if kind != "http" and isinstance(http_block, dict) and http_block:
        # V7：仅 kind=http 可声明 http 块。
        # 必须在**原始数据**上校验——spec.http 对非 http kind 恒为 None，
        # 在 spec 上判会让这条规则变成永远不触发的死代码，而配置被静默忽略。
        raise ManifestError(f"{loc} V7: 仅 kind=http 可声明 http 块（当前 kind={kind}）")
    if kind == "http":
        if not isinstance(http_block, dict):
            raise ManifestError(f"{loc} kind=http 必须有 http 块（mapping）")
        _reject_secret_keys(http_block, where=f"{loc}.http")
        _validate_http_block(http_block, loc=f"{loc}.http", args_schema=args_schema)

    # 顶层 idempotency_key（testing-write-capability · 裁定四）：
    # local_fn write 的合法幂等键声明位（V7 禁 local_fn 声明 http 块）。
    # http 能力仍走 http.idempotency_key；缺省 None=未声明。
    # 校验语义在 V1（write 二选一强制）/ V8（read 对称拦截），此处只解析归一。
    idempotency_key_raw = raw.get("idempotency_key")
    idempotency_key: str | None = None
    if idempotency_key_raw is not None:
        idempotency_key = str(idempotency_key_raw).strip() or None

    hitl_raw = raw.get("hitl") or {}
    if not isinstance(hitl_raw, dict):
        raise ManifestError(f"{loc} hitl 必须是 mapping")
    _reject_secret_keys(hitl_raw, where=f"{loc}.hitl")
    snapshot_raw = hitl_raw.get("snapshot_fields") or []
    if not isinstance(snapshot_raw, list):
        raise ManifestError(f"{loc}.hitl.snapshot_fields 必须是 list")

    receipt_raw = raw.get("receipt") or {}
    if not isinstance(receipt_raw, dict):
        raise ManifestError(f"{loc} receipt 必须是 mapping")
    capture_raw = receipt_raw.get("capture") or []
    if not isinstance(capture_raw, list):
        raise ManifestError(f"{loc}.receipt.capture 必须是 list")

    # 降级声明（P1 · Q3 下半）。默认**不降级**；声明了才降级。
    fallback_raw = raw.get("fallback")
    if fallback_raw is not None:
        if not isinstance(fallback_raw, dict):
            raise ManifestError(f"{loc} fallback 必须是 mapping")
        _reject_secret_keys(fallback_raw, where=f"{loc}.fallback")
        _validate_fallback(fallback_raw, loc=f"{loc}.fallback")

    visibility_raw = raw.get("visibility")
    if visibility_raw is not None:
        if not isinstance(visibility_raw, dict):
            raise ManifestError(f"{loc} visibility 必须是 mapping")
        _reject_secret_keys(visibility_raw, where=f"{loc}.visibility")
        unknown = set(visibility_raw) - VISIBILITY_KEYS
        if unknown:
            raise ManifestError(
                f"{loc}.visibility 未知键"
                f"（仅 {', '.join(sorted(VISIBILITY_KEYS))}）: {sorted(unknown)}"
            )
        cls = str(visibility_raw.get("classification_max") or "").strip().lower()
        if cls and cls not in CLASSIFICATION_LEVELS:
            raise ManifestError(
                f"{loc}.visibility.classification_max 非法"
                f"（仅 {', '.join(CLASSIFICATION_LEVELS)}）: {cls}"
            )
        for dim in ("departments", "roles", "projects"):
            if dim in visibility_raw and not isinstance(visibility_raw[dim], (list, str)):
                raise ManifestError(f"{loc}.visibility.{dim} 必须是 list 或 str")

    # 可撤销性四字段（V1-B）：类型/词表合法才收；非法 → ManifestError 整文件失败
    reversible, execution_type, max_reversal_latency, requires_stop_support = _parse_reversibility(
        raw, loc=loc
    )

    spec = CapabilitySpec(
        capability_id=cid,
        kind=kind,
        description=str(raw.get("description") or ""),
        args_schema=args_schema,
        tags=tuple(str(t) for t in tags_raw),
        risk_level=_one_of(
            raw.get("risk_level"),
            RISK_LEVELS,
            default="low",
            loc=loc,
            field="risk_level",
        ),
        enabled=bool(raw.get("enabled", True)),
        tenant_scoped=bool(raw.get("tenant_scoped", False)),
        side_effect=_one_of(
            raw.get("side_effect"),
            SIDE_EFFECTS,
            default="none",
            loc=loc,
            field="side_effect",
        ),
        when_to_use=when_to_use,
        when_not_to_use=str(raw.get("when_not_to_use") or "").strip(),
        http=dict(http_block) if kind == "http" and isinstance(http_block, dict) else None,
        idempotency_key=idempotency_key,
        hitl_required=bool(hitl_raw.get("required", False)),
        hitl_snapshot_fields=tuple(str(x) for x in snapshot_raw),
        receipt_capture=tuple(str(x) for x in capture_raw),
        # 结果契约（P0-1）：None = 未声明，不做契约校验（见 result_contract 模块 docstring）
        output_schema=(dict(output_schema_raw) if isinstance(output_schema_raw, dict) else None),
        visibility=(dict(visibility_raw) if isinstance(visibility_raw, dict) else None),
        fallback=dict(fallback_raw) if isinstance(fallback_raw, dict) else None,
        # 可撤销性四字段（V1-B）：声明了必须合法；缺字段不报错（向后兼容）
        reversible=reversible,
        execution_type=execution_type,
        max_reversal_latency=max_reversal_latency,
        requires_stop_support=requires_stop_support,
    )
    adapter = _build_adapter(spec, raw=raw, loc=loc)
    _validate_invariants(spec, loc=loc)
    _validate_reversibility(spec, loc=loc)
    spec = _apply_reversibility_default(spec, loc=loc)
    return _PendingEntry(spec=spec, adapter=adapter)


def _build_adapter(spec: CapabilitySpec, *, raw: dict[str, Any], loc: str) -> Any:
    """按 kind 分派。local_fn 引用白名单函数；http 用声明构造（不需要 adapter 字段）。"""
    if spec.kind == "http":
        return GenericHttpAdapter(spec)
    ref = str(raw.get("adapter") or "").strip()
    return LocalFnAdapter(_resolve_local_fn_adapter(ref, loc=loc))


def _validate_http_block(
    http_block: dict[str, Any], *, loc: str, args_schema: dict[str, Any]
) -> None:
    method = str(http_block.get("method") or "").strip().upper()
    if method not in _ALLOWED_METHODS:
        raise ManifestError(
            f"{loc} method 非法（仅 {'/'.join(sorted(_ALLOWED_METHODS))}）: {method or '(空)'}"
        )
    base_url = str(http_block.get("base_url") or "").strip()
    if not base_url:
        raise ManifestError(f"{loc} 缺 base_url")
    if "://" in base_url or not _BASE_URL_NAME_RE.match(base_url):
        # 必须是环境变量名：把内网域名/端口写死进仓 = 配置泄漏 + 无法换环境
        raise ManifestError(
            f"{loc} base_url 必须是环境变量名（大写+下划线），不能是 URL 字面量: {base_url}"
        )
    path = str(http_block.get("path") or "").strip()
    if not path.startswith("/"):
        raise ManifestError(f"{loc} path 必须以 / 开头: {path or '(空)'}")

    auth = str(http_block.get("auth") or "").strip()
    if not auth:
        raise ManifestError(f"{loc} 缺 auth（凭证名）")
    if not _AUTH_NAME_RE.match(auth):
        raise ManifestError(
            f"{loc} auth 必须是凭证名（小写字母开头 + 小写字母/数字/下划线）: {auth!r}"
        )
    lowered = auth.lower()
    if any(s in lowered for s in _AUTH_VALUE_DENY):
        raise ManifestError(f"{loc} auth 疑似直接写入密钥值: {auth!r}")

    if not isinstance(http_block.get("success_when"), dict):
        raise ManifestError(f"{loc} 缺 success_when（mapping）")

    error_map = http_block.get("error_map")
    if not isinstance(error_map, dict) or not error_map:
        raise ManifestError(f"{loc} 缺 error_map（下游业务码 → 稳定错误码）")
    for upstream, stable in error_map.items():
        if str(stable) not in STABLE_ERROR_CODES:
            # 不允许随手发明第八个错误码
            raise ManifestError(
                f"{loc}.error_map 值必须是稳定错误码"
                f"（{', '.join(sorted(STABLE_ERROR_CODES))}）: {upstream} -> {stable}"
            )

    # 模板变量必须落在 args_schema.properties 或 Host 注入集合内。
    # 写错变量名是**配置错误**，加载期就该拦——不要留到运行期变成空串。
    declared = set(args_schema.get("properties") or {})
    allowed = declared | set(HOST_INJECTED_VARS)
    for match in re.finditer(
        r"\{\{(\w+)\}\}", json.dumps(http_block, ensure_ascii=False, default=str)
    ):
        if match.group(1) not in allowed:
            raise ManifestError(
                f"{loc} 模板变量未声明: {{{{{match.group(1)}}}}}"
                f"（须在 args_schema.properties 或以 _ 开头）"
            )


# ---- 可撤销性四字段（V1-B）----
# 缺失默认 HITL 三档灰度（FP-3）：off=无行为 · observe=台账 · enforce=派生
ENV_REVERSIBILITY_MODE = "OPS_CAPABILITY_REVERSIBILITY_MODE"


def _reversibility_mode() -> str:
    """三档：off|observe|enforce；默认 off；非法值回退 off（承 delegation 先例）。"""
    raw = os.environ.get(ENV_REVERSIBILITY_MODE, "").strip().lower()
    return raw if raw in ("off", "observe", "enforce") else "off"


def _parse_reversibility(
    raw: dict[str, Any], *, loc: str
) -> tuple[bool | None, str | None, int | None, bool | None]:
    """解析可撤销性四字段；声明了就必须合法，非法 → ManifestError 整文件失败。

    缺字段不报错（向后兼容 · manifest 演进）；四字段一体声明，
    任一为 None 即「该字段未声明」。
    """
    reversible = raw.get("reversible")
    if reversible is not None and not isinstance(reversible, bool):
        raise ManifestError(f"{loc} reversible 必须是 bool: {reversible!r}")
    execution_type = raw.get("execution_type")
    if execution_type is not None:
        execution_type = str(execution_type).strip()
        if execution_type not in EXECUTION_TYPES:
            raise ManifestError(
                f"{loc} execution_type 非法"
                f"（仅 {'/'.join(sorted(EXECUTION_TYPES))}）: {execution_type or '(空)'}"
            )
    max_reversal_latency = raw.get("max_reversal_latency")
    if max_reversal_latency is not None and (
        not isinstance(max_reversal_latency, int)
        or isinstance(max_reversal_latency, bool)
        or max_reversal_latency < 0
    ):
        raise ManifestError(f"{loc} max_reversal_latency 必须是非负 int: {max_reversal_latency!r}")
    requires_stop_support = raw.get("requires_stop_support")
    if requires_stop_support is not None and not isinstance(requires_stop_support, bool):
        raise ManifestError(f"{loc} requires_stop_support 必须是 bool: {requires_stop_support!r}")
    return reversible, execution_type, max_reversal_latency, requires_stop_support


def _validate_reversibility(spec: CapabilitySpec, *, loc: str) -> None:
    """跨字段一致性硬规则（Q3 裁定）；其余组合只观测不拒（契约不推测）。

    - 矛盾声明拒绝：side_effect=irreversible 且 reversible=true → ManifestError；
    - process 必须声明 stop 支持：execution_type=process 且
      requires_stop_support 非 true → ManifestError。
    """
    if spec.side_effect == "irreversible" and spec.reversible is True:
        raise ManifestError(f"{loc} 矛盾声明：side_effect=irreversible 且 reversible=true")
    if spec.execution_type == "process" and spec.requires_stop_support is not True:
        raise ManifestError(f"{loc} execution_type=process 必须 requires_stop_support: true")


def _reversibility_declared(spec: CapabilitySpec) -> bool:
    """四字段任一有显式声明即视为已声明（声明优先 · FP-7：显式合法 → 不派生）。"""
    return any(
        value is not None
        for value in (
            spec.reversible,
            spec.execution_type,
            spec.max_reversal_latency,
            spec.requires_stop_support,
        )
    )


def _apply_reversibility_default(spec: CapabilitySpec, *, loc: str) -> CapabilitySpec:
    """缺失默认 HITL 三档（FP-3 灰度 · FP-7 声明优先 · 执行侧既有消费不改语义）。

    off=无行为；observe=台账 reversibility_undeclared would_default_hitl 不派生；
    enforce=未声明能力 hitl_required 派生 True（记动作不记内容：只记 id）。
    """
    mode = _reversibility_mode()
    if mode == "off" or _reversibility_declared(spec):
        return spec
    if mode == "observe":
        logger.warning(
            "capability reversibility_undeclared would_default_hitl id=%s loc=%s",
            spec.capability_id,
            loc,
        )
        update_current_span_metadata(
            {
                "reversibility_undeclared": True,
                "would_default_hitl": True,
                "capability_id": spec.capability_id,
            }
        )
        return spec
    logger.warning(
        "capability reversibility_undeclared 派生 hitl_required=True（enforce）id=%s loc=%s",
        spec.capability_id,
        loc,
    )
    return replace(spec, hitl_required=True)


def _validate_invariants(spec: CapabilitySpec, *, loc: str) -> None:
    """加载期强校验（V1–V8）。

    原则：**能在加载期发现，就不要留到运行期。**
    """
    is_write = spec.side_effect in WRITE_SIDE_EFFECTS
    http_block = spec.http or {}
    # 裁定四（testing-write-capability）：幂等键两处声明位——http 块键
    # （http 能力）或顶层 idempotency_key（local_fn write 的合法声明位），
    # 任一非空即满足；**仅 write 强制**，read 不受影响（顶层键缺省 None）。
    idempotency_key = (
        str(http_block.get("idempotency_key") or "").strip()
        or str(spec.idempotency_key or "").strip()
    )

    # V1：写操作必须有幂等键（否则重复提交产生多张单据）
    if is_write and not idempotency_key:
        raise ManifestError(f"{loc} V1: side_effect={spec.side_effect} 必须有 idempotency_key")

    # V2：写操作必须有人工确认（第一期不允许存在「无确认的写能力」）
    if is_write and not spec.hitl_required:
        raise ManifestError(f"{loc} V2: side_effect={spec.side_effect} 必须 hitl.required: true")

    # V3：高危必须有人工确认（高危无确认 = 闸形同虚设）
    if spec.risk_level == "high" and not spec.hitl_required:
        raise ManifestError(f"{loc} V3: risk_level=high 必须 hitl.required: true")

    # V4：tenant_scoped **且 kind=http** 时必须声明租户谓词怎么下推。
    # 否则租户谓词只在 Policy 里被检查、没真的传给下游——检查了但没用上。
    # （local_fn 不适用：进程内适配器直接拿 ctx，不存在「下推」这一步。）
    if spec.tenant_scoped and spec.kind == "http":
        param = http_block.get("tenant_param")
        if not isinstance(param, dict):
            raise ManifestError(f"{loc} V4: tenant_scoped=true 的 http 能力必须有 tenant_param")
        where = str(param.get("in") or "").strip().lower()
        if where not in _TENANT_PARAM_IN:
            raise ManifestError(
                f"{loc} V4: tenant_param.in 非法"
                f"（仅 {'/'.join(sorted(_TENANT_PARAM_IN))}）: {where or '(空)'}"
            )
        if not str(param.get("name") or "").strip():
            raise ManifestError(f"{loc} V4: tenant_param.name 不能为空")

    # V5：模板变量校验见 _validate_http_block（http 专用）

    # V6：error_map 词表校验见 _validate_http_block（http 专用）

    # V7：kind 形态完整性。
    # 注意 http 块的存在性在 ``_entry_from_raw`` 里按**原始数据**校验
    # （spec.http 对非 http kind 恒为 None，此处判不出「多写了 http 块」）。
    if spec.kind == "http" and not http_block:
        raise ManifestError(f"{loc} V7: kind=http 缺 http 块")

    # V8：只读不需要幂等键——写了通常是抄错，早报早改
    # （裁定四对称适配：http 块键与顶层键任一声明都拦，延续「只读不需要幂等键」）
    if not is_write and idempotency_key:
        raise ManifestError(f"{loc} V8: side_effect={spec.side_effect} 不应声明 idempotency_key")

    # V9：对外接入（kind=http）必须显式声明可见范围。
    # 进程内的 local_fn 沿用 CapabilityFilter 语义（未声明即不受限，但留痕）；
    # 而 http 是接别人系统的入口，**不该有「默认全员可见」这种兜底**。
    if spec.kind == "http" and spec.visibility is None:
        raise ManifestError(f"{loc} V9: kind=http 必须声明 visibility（部门 / 角色 / 密级）")

    # V12：写能力**禁止**声明降级（B1）。
    # 单据没建就是没建，不存在"降级成建了一半"。写操作失败必须看得见——
    # 一旦允许降级，就会出现"用户以为提交了、实际没提交"的最坏结果。
    if is_write and fallback_mod.action_of(spec) != fallback_mod.ACTION_NONE:
        raise ManifestError(
            f"{loc} V12: side_effect={spec.side_effect} 禁止声明降级动作"
            f"（当前 action={fallback_mod.action_of(spec)}）——写失败必须明确可见"
        )


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
