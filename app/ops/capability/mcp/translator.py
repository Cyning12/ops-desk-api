"""P2b-T3 · MCP 翻译器：tools/list → manifest 原生条目直挂 Gateway 七层闸链。

硬约束落点（设计终稿 §0.1 / §3 / §4 / §7-① + 委派书）：

- **R5b 同源**：产出 raw dict 直调 ``manifest._entry_from_raw``（V1-V13 同源校验，
  禁止旁路构造）；注册经 ``manifest._commit`` 伪 source ``mcp://<server_key>``（R4），
  shutdown 摘除按 ``manifest._FILE_IDS`` 同表追踪。
- **命名**：``mcp__{server_key}__{tool_name}``；段净化 kebab→下划线、collapse ``_+``
  保证段内绝无 ``__``（切分唯一解、防 server key/tool name 相互注入 · §4-F）；
  段声明校验 ``^[a-z][a-z0-9_]{0,63}$``。**冲突即拒该 server 整批** + span 告警
  （委派加严口径，不静默跳过）。
- **M1 side_effect 必填缺省拒载**（R1）：override > server default_side_effect >
  ``readOnlyHint=true`` → read；否则拒载（宁可误拒）+ span 原因。
  ``readOnlyHint=false`` 与配置 read 冲突 → 拒载（§7-④）；
  ``destructiveHint=true`` → side_effect 抬 irreversible + risk 抬 high
  （设计 §7-④ 与委派 §5-⑦ 两稿并集 · 冲突向保守）。
- **M2 inputSchema 递归清洗**（R2）：白名单键保留 + ``$ref``/``$defs``/``anyOf``/
  ``oneOf``/``allOf``/``not`` 剥壳为可校验子集（记录剥壳点合成节级引导语进
  description）；每层 properties 密钥形键扫描（复用 ``manifest._reject_secret_keys``）；
  字符串值毒扫（slots 伪造标记字面 + 指令性措辞 → 拒载）+ 逐字段截断。
- **M3 when_to_use 强制合成**（manifest.py:537-539 必填缺口的同源解法）：
  description_override > description 摘要 > 名称兜底，保证非空。
- **outputSchema → output_fields 键名清单**（R-D3'：不合成 output_schema 契约）。
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from typing import Any

from app.ops.capability import manifest as _manifest
from app.ops.capability.gateway import get_registry
from app.ops.capability.gateway import unregister as _gateway_unregister
from app.ops.capability.mcp_config import McpServerConfig
from app.ops.capability.types import WRITE_SIDE_EFFECTS
from app.ops.tracing import update_current_span_metadata

logger = logging.getLogger(__name__)

__all__ = [
    "McpEntryRejectedError",
    "McpToolRejection",
    "McpTranslationResult",
    "capability_id_for",
    "register_connected",
    "register_server_tools",
    "unregister_server",
    "unregister_server_safely",
]

MCP_KIND = "mcp"
_ID_PREFIX = "mcp"
_ID_SEP = "__"

_SEGMENT_RE = re.compile(r"^[a-z][a-z0-9_]{0,63}$")
_NON_SEGMENT_CHARS = re.compile(r"[^a-z0-9_]+")
_COLLAPSE_UNDERSCORES = re.compile(r"_+")

# slots 伪造标记字面：复制自 app/ops/lg_rag/prompts/slots.py ``_FORGE_ESCAPES`` 左列。
# capability 层禁引 prompts（零新跨模块边），本地拷贝须与其保持同步。
_FORGE_MARKERS = (
    "</slot:",
    "<slot:",
    "[已知事实]",
    "[用户偏好]",
    "[当前目标]",
    "[相似经验]",
)

# 指令性措辞（小写子串匹配；中文项不受 lower 影响）
_INSTRUCTIONAL_MARKERS = (
    "ignore previous",
    "ignore all",
    "disregard previous",
    "disregard all",
    "system prompt",
    "you are now",
    "do not follow",
    "忽略以上",
    "忽略之前",
    "忽略先前",
    "忽略上文",
    "系统提示词",
    "你现在是",
)

_MAX_DESCRIPTION_CHARS = 1000
_MAX_WHEN_TO_USE_CHARS = 200
_MAX_SCHEMA_TEXT_CHARS = 500
_MAX_OUTPUT_FIELDS = 16
_MAX_NOTE_PATHS = 5

# M2 清洗白名单：仅这些 schema 键保留（其余静默丢弃；剥壳键记录 notes）
_SCHEMA_KEEP_KEYS = frozenset(
    {
        "type",
        "properties",
        "required",
        "items",
        "enum",
        "const",
        "default",
        "description",
        "title",
        "additionalProperties",
        "format",
        "minimum",
        "maximum",
        "exclusiveMinimum",
        "exclusiveMaximum",
        "minLength",
        "maxLength",
        "minItems",
        "maxItems",
        "uniqueItems",
        "pattern",
    }
)
# 剥壳键：组合壳/引用，剥掉并记 notes（节级引导语素材）
_SCHEMA_SHELL_KEYS = frozenset(
    {"$ref", "$defs", "defs", "definitions", "anyOf", "oneOf", "allOf", "not"}
)


class McpEntryRejectedError(ValueError):
    """单条目翻译拒载（原因即 message；调用方落 warn + span）。"""


@dataclass(frozen=True)
class McpToolRejection:
    """单条 tools/list 条目的拒载记录。"""

    tool_name: str
    reason: str


@dataclass(frozen=True)
class McpTranslationResult:
    """单 server 翻译批次结果（span/日志/task 档汇报素材）。"""

    server_key: str
    registered_ids: tuple[str, ...] = ()
    rejected: tuple[McpToolRejection, ...] = ()
    excluded: tuple[str, ...] = ()
    fatal: str | None = None  # 非 None = 整批拒载（命名冲突）


# ---------------------------------------------------------------------------
# 命名（§4-F 防注入 · 委派口径 mcp__{server_key}__{tool_name}）
# ---------------------------------------------------------------------------


def _sanitize_segment(value: str) -> str | None:
    """净化为合法 id 段：lower + 非 ``[a-z0-9_]`` → ``_`` + collapse + strip + 截 64。

    collapse ``_+`` → 段内绝无 ``__``（与 ``__`` 切分唯一解、防相互注入）。
    无法通过段声明校验 ``^[a-z][a-z0-9_]{0,63}$`` → None。
    """

    cleaned = _NON_SEGMENT_CHARS.sub("_", value.strip().lower())
    cleaned = _COLLAPSE_UNDERSCORES.sub("_", cleaned).strip("_")[:64]
    if not cleaned or _SEGMENT_RE.match(cleaned) is None:
        return None
    return cleaned


def capability_id_for(server_key: str, tool_name: str) -> str | None:
    """产出 ``mcp__{server_key}__{tool_name}``；任一段非法 → None。"""

    server_seg = _sanitize_segment(server_key)
    tool_seg = _sanitize_segment(tool_name)
    if server_seg is None or tool_seg is None:
        return None
    return f"{_ID_PREFIX}{_ID_SEP}{server_seg}{_ID_SEP}{tool_seg}"


# ---------------------------------------------------------------------------
# 毒扫（R2：密钥形 + 指令性 + slots 伪造标记）
# ---------------------------------------------------------------------------


def _reject_poison_text(value: str, *, where: str) -> None:
    for marker in _FORGE_MARKERS:
        if marker in value:
            raise McpEntryRejectedError(f"{where}: 命中 slots 伪造标记字面 {marker!r} → 拒载")
    lowered = value.lower()
    for marker in _INSTRUCTIONAL_MARKERS:
        if marker in lowered:
            raise McpEntryRejectedError(f"{where}: 命中指令性措辞 {marker!r} → 拒载")


def _truncate(value: str, limit: int) -> str:
    return value if len(value) <= limit else value[:limit]


# ---------------------------------------------------------------------------
# M2 · inputSchema 递归清洗（$ref/$defs/anyOf/oneOf/allOf 剥壳为可校验子集）
# ---------------------------------------------------------------------------


def _clean_schema_node(node: Any, *, where: str, notes: list[str]) -> dict:
    if not isinstance(node, dict):
        return {}
    out: dict[str, Any] = {}
    for key, value in node.items():
        k = str(key)
        if k in _SCHEMA_SHELL_KEYS:
            notes.append(where or "$")
            continue
        if k not in _SCHEMA_KEEP_KEYS:
            continue
        if k == "properties" and isinstance(value, dict):
            _manifest._reject_secret_keys(value, where=f"{where}.properties")
            out[k] = {
                str(pk): _clean_schema_node(pv, where=f"{where}.{pk}", notes=notes)
                for pk, pv in value.items()
            }
        elif k in ("items", "additionalProperties") and isinstance(value, dict):
            out[k] = _clean_schema_node(value, where=f"{where}.{k}", notes=notes)
        elif isinstance(value, str):
            _reject_poison_text(value, where=f"{where}.{k}")
            out[k] = _truncate(value, _MAX_SCHEMA_TEXT_CHARS)
        elif isinstance(value, list) and k in ("enum", "required"):
            cleaned_list: list[Any] = []
            for item in value:
                if isinstance(item, str):
                    _reject_poison_text(item, where=f"{where}.{k}")
                    cleaned_list.append(_truncate(item, _MAX_SCHEMA_TEXT_CHARS))
                else:
                    cleaned_list.append(item)
            out[k] = cleaned_list
        else:
            out[k] = value
    return out


def _clean_input_schema(schema: Any, *, where: str) -> tuple[dict, list[str]]:
    """清洗 inputSchema → (可校验子集, 剥壳点 notes)。schema 缺失 → 空 object。"""

    if schema is None:
        return {"type": "object", "properties": {}}, []
    if not isinstance(schema, dict):
        raise McpEntryRejectedError(f"{where}: inputSchema 非 mapping → 拒载")
    _manifest._reject_secret_keys(schema, where=where)
    notes: list[str] = []
    cleaned = _clean_schema_node(schema, where=where, notes=notes)
    cleaned.setdefault("type", "object")
    return cleaned, notes


def _append_simplification_note(description: str, notes: list[str]) -> str:
    """M2 节级引导语：剥壳发生过 → 合成提示写入条目 description。"""

    if not notes:
        return description
    uniq = sorted(set(notes))[:_MAX_NOTE_PATHS]
    note = "（复杂参数已简化：" + "、".join(uniq) + " 等处的 $ref/组合壳已剥离为可校验子集）"
    return f"{description}{note}" if description else note


# ---------------------------------------------------------------------------
# 单条目翻译
# ---------------------------------------------------------------------------


def _translate_tool(config: McpServerConfig, tool: Any) -> dict | None:
    """tools/list 单条目 → manifest raw dict；exclude → None；拒载 → raise。"""

    where = f"mcp server={config.key}"
    if not isinstance(tool, dict):
        raise McpEntryRejectedError(f"{where}: tools/list 条目非 mapping → 拒载")
    name = str(tool.get("name") or "").strip()
    if not name:
        raise McpEntryRejectedError(f"{where}: tools/list 条目缺 name → 拒载")
    if name in config.exclude_tools:
        return None

    cid = capability_id_for(config.key, name)
    if cid is None:
        raise McpEntryRejectedError(
            f"{where}: 命名段净化失败（server={config.key!r} tool={name!r}，"
            "须 ^[a-z][a-z0-9_]{0,63}$）→ 拒载"
        )

    override = config.tool_overrides.get(name)

    # title→description 映射；毒扫仅针对 server 供稿（override 为运营侧可信）
    description = ""
    if override is not None and override.description_override:
        description = override.description_override
    else:
        raw_desc = tool.get("description")
        title = tool.get("title")
        source = raw_desc if isinstance(raw_desc, str) and raw_desc.strip() else title
        if isinstance(source, str) and source.strip():
            _reject_poison_text(source, where=f"{where} tool={name} description")
            description = _truncate(source.strip(), _MAX_DESCRIPTION_CHARS)

    try:
        cleaned_schema, notes = _clean_input_schema(
            tool.get("inputSchema"), where=f"{where} tool={name}"
        )
    except _manifest.ManifestError as exc:
        # 密钥形字段扫描（manifest 同源 _reject_secret_keys）→ 单条拒载不炸批
        raise McpEntryRejectedError(
            f"{where} tool={name}: schema 密钥形字段拒载：{exc}"
        ) from exc
    description = _append_simplification_note(description, notes)

    annotations = tool.get("annotations")
    if not isinstance(annotations, dict):
        annotations = {}

    # M1 / §7-④ / 委派 §5-⑦：side_effect + risk 保守向解析
    side_effect = (
        override.side_effect if override is not None and override.side_effect else None
    ) or config.default_side_effect
    read_only = annotations.get("readOnlyHint")
    if side_effect is None and read_only is True:
        side_effect = "read"
    if side_effect is None:
        raise McpEntryRejectedError(
            f"{where} tool={name}: M1 side_effect 缺省"
            "（无 override/default_side_effect 且 readOnlyHint≠true）→ 拒载"
        )
    if read_only is False and side_effect == "read":
        raise McpEntryRejectedError(
            f"{where} tool={name}: readOnlyHint=false 与配置 side_effect=read 冲突 → 拒载"
        )
    risk_level = (
        override.risk_level if override is not None and override.risk_level else None
    ) or "low"
    if annotations.get("destructiveHint") is True:
        # 两稿并集（冲突向保守）：抬 irreversible + risk=high（V3 联动 hitl）
        side_effect = "irreversible"
        risk_level = "high"

    if override is not None and override.hitl_required is not None:
        hitl_required = override.hitl_required
    else:
        hitl_required = side_effect in WRITE_SIDE_EFFECTS or risk_level == "high"
    if override is not None and override.tenant_scoped is not None:
        tenant_scoped = override.tenant_scoped
    else:
        tenant_scoped = side_effect in WRITE_SIDE_EFFECTS  # V13 默认满足

    # M3 · when_to_use 强制合成（manifest.py:537-539 必填缺口）
    wtu_src = description.strip()
    when_to_use = (
        _truncate(wtu_src, _MAX_WHEN_TO_USE_CHARS)
        if wtu_src
        else f"调用 MCP 工具 {name}（server={config.key}）"
    )

    # R-D3' · outputSchema 只取 output_fields 键名（不合成契约）
    output_fields: list[str] = []
    out_schema = tool.get("outputSchema")
    if isinstance(out_schema, dict):
        props = out_schema.get("properties")
        if isinstance(props, dict):
            output_fields = [
                str(k) for k in list(props)[:_MAX_OUTPUT_FIELDS] if str(k).strip()
            ]

    raw: dict[str, Any] = {
        "id": cid,
        "kind": MCP_KIND,
        "description": description,
        "args_schema": cleaned_schema,
        "tags": ["mcp", _sanitize_segment(config.key) or "mcp"],
        "risk_level": risk_level,
        "side_effect": side_effect,
        "when_to_use": when_to_use,
        "tenant_scoped": tenant_scoped,
        "hitl": {"required": hitl_required},
        "mcp": {"server_key": config.key, "tool_name": name},
    }
    if override is not None and override.idempotency_key:
        raw["idempotency_key"] = override.idempotency_key
    if output_fields:
        raw["output_fields"] = output_fields
    return raw


# ---------------------------------------------------------------------------
# 批级注册 / 摘除
# ---------------------------------------------------------------------------


def _batch_conflict_reason(server_key: str, ids: list[str]) -> str | None:
    """命名冲突检测：批内 dup 或与 registry 现存冲突 → 原因串（整批拒载）。

    本 server 自身批次已注册的 id（``_FILE_IDS['mcp://<key>']`` 在册）不算冲突——
    重复注册走 ``_commit(replace=True)`` 幂等替换（shutdown→重启 同进程循环）。
    """

    seen: set[str] = set()
    dups: set[str] = set()
    for cid in ids:
        if cid in seen:
            dups.add(cid)
        seen.add(cid)
    if dups:
        return f"批内命名冲突：{sorted(dups)}"
    own = set(_manifest._FILE_IDS.get(f"mcp://{server_key}", ()))
    registry = get_registry()
    clash = [
        cid for cid in ids if cid not in own and registry.get(cid) is not None
    ]
    if clash:
        return f"与已注册能力冲突：{clash}"
    return None


def register_server_tools(
    config: McpServerConfig, tools: Any, *, replace: bool = True
) -> McpTranslationResult:
    """单 server tools/list → 翻译 → 同源校验 → 注册进 Gateway registry。

    命名冲突即拒该 server **整批** + span 告警（不静默跳过）；
    单条目翻译/校验失败 → 单条拒载 + warn（§10 失败路径）。
    """

    raws: list[dict] = []
    rejected: list[McpToolRejection] = []
    excluded: list[str] = []
    for tool in tools or ():
        tool_name = str(tool.get("name") or "?") if isinstance(tool, dict) else "?"
        try:
            raw = _translate_tool(config, tool)
        except McpEntryRejectedError as exc:
            rejected.append(McpToolRejection(tool_name, str(exc)))
            logger.warning(
                "mcp 翻译拒载 server=%s tool=%s 原因=%s",
                config.key,
                tool_name,
                exc,
            )
            continue
        if raw is None:
            excluded.append(tool_name)
            continue
        raws.append(raw)

    ids = [str(r["id"]) for r in raws]
    fatal = _batch_conflict_reason(config.key, ids)
    if fatal is not None:
        for raw in raws:
            rejected.append(
                McpToolRejection(str(raw["mcp"]["tool_name"]), f"整批拒载：{fatal}")
            )
        update_current_span_metadata(
            {
                "mcp_translator_batch_rejected": config.key,
                "mcp_translator_batch_reason": fatal,
            }
        )
        logger.warning("mcp server=%s 命名冲突整批拒载：%s", config.key, fatal)
        return McpTranslationResult(
            server_key=config.key,
            rejected=tuple(rejected),
            excluded=tuple(excluded),
            fatal=fatal,
        )

    pending = []
    for raw in raws:
        try:
            pending.append(
                _manifest._entry_from_raw(raw, loc=f"mcp://{config.key}:{raw['id']}")
            )
        except _manifest.ManifestError as exc:
            tool_name = str(raw["mcp"]["tool_name"])
            rejected.append(
                McpToolRejection(tool_name, f"V1-V13 同源校验拒载：{exc}")
            )
            logger.warning(
                "mcp 条目校验拒载 server=%s tool=%s 原因=%s",
                config.key,
                tool_name,
                exc,
            )

    if replace:
        # 幂等重注册（照 reload_capability_manifest 先例）：先摘除自身批次旧条目
        for old_cid in _manifest._FILE_IDS.get(f"mcp://{config.key}", ()):
            _gateway_unregister(old_cid)
    result = _manifest._commit(f"mcp://{config.key}", None, pending, replace=replace)
    update_current_span_metadata(
        {
            "mcp_translator_server": config.key,
            "mcp_translator_registered": len(result.registered_ids),
            "mcp_translator_rejected": len(rejected),
            "mcp_translator_excluded": len(excluded),
        }
    )
    logger.info(
        "mcp server=%s 注册 %d 条、拒载 %d 条、排除 %d 条",
        config.key,
        len(result.registered_ids),
        len(rejected),
        len(excluded),
    )
    return McpTranslationResult(
        server_key=config.key,
        registered_ids=tuple(result.registered_ids),
        rejected=tuple(rejected),
        excluded=tuple(excluded),
    )


def unregister_server(server_key: str) -> int:
    """R5c：按 ``_FILE_IDS['mcp://<key>']`` 摘除该 server 全部条目。"""

    ids = _manifest._FILE_IDS.pop(f"mcp://{server_key}", ())
    count = 0
    for cid in ids:
        if _gateway_unregister(cid):
            count += 1
    if ids:
        logger.info("mcp server=%s 摘除 %d/%d 条目", server_key, count, len(ids))
    return count


def unregister_server_safely(server_key: str) -> None:
    """unregister_hook 包装：异常仅 warn（manager 侧亦有守卫，双保险）。"""

    try:
        unregister_server(server_key)
    except Exception:  # noqa: BLE001 —— shutdown 路径禁炸
        logger.warning("mcp server=%s 摘除条目失败", server_key, exc_info=True)


def register_connected(
    manager: Any, configs_by_key: dict[str, McpServerConfig]
) -> tuple[McpTranslationResult, ...]:
    """启动期编排（裁定 D：内存注册不落盘）：遍历已连接 server 逐批注册。

    tools/list 为空 → info 跳过（不炸启动 · §10）。
    """

    results: list[McpTranslationResult] = []
    for key in manager.connected_keys():
        session = manager.get_session(key)
        config = configs_by_key.get(key)
        if session is None or config is None:
            continue
        tools = session.tools
        if not tools:
            logger.info("mcp server=%s tools/list 为空，跳过注册（不炸启动）", key)
            continue
        results.append(register_server_tools(config, tools))
    return tuple(results)
