"""MCP server 配置面（P2b-T1）：``mcp_servers.yaml`` 纯解析 loader（零连接）。

设计真源：workspace 11-p2b-mcp-skill-design.md 终稿 §7-②（键面）/ §10（失败语义）。

本模块**只做解析**：读文件 + `yaml.safe_load` + schema 校验，**零连接、零外网、
零 subprocess**。连接 / 握手 / 工具发现 / 翻译注册属 P2b-T2（lifespan 启动期，
总闸 `OPS_CAPABILITY_MCP_ENABLED` 开时按本 loader 结果建连）。

失败语义（fail-closed）：任何非法输入抛 :class:`McpServersConfigError`
（`ValueError` 子类）——文件缺失、非法 yaml、缺键、未知键、未知 transport、
未知 side_effect 词表、传输互斥键、坏/重复 server_key、protocol_version 不符钉版、
超时非正。T2 runtime 负责 catch 后 warn + MCP 面降级为空（设计 §10），本模块不降级。

键面（每 server）：

- `key`（必填）：kebab-case 无点（`^[a-z0-9]+(?:-[a-z0-9]+)*$`），全文件唯一。
- `transport`（必填）：`stdio` | `http`。
- http：`url` 必填；禁 `command` / `args` / `cwd` / `env_allowlist`。
- stdio：`command` 必填；`args` / `cwd` / `env_allowlist` 可选；禁 `url`。
- `protocol_version`：可选，钉版——默认且仅接受 `2025-06-18`。
- `expected_server`：可选 `{name, version}`（T2 握手后校验）。
- `connect_timeout_s` / `call_timeout_s`：可选正数（bool 拒），默认 10 / 30。
- `default_side_effect`：可选，∈ `{none, read, write, irreversible}`。
- `tool_overrides`：可选 mapping，每工具键 ⊆ `{side_effect, idempotency_key,
  hitl_required, tenant_scoped, risk_level, description_override}`。
- `exclude_tools`：可选 list[str]。
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from app.ops.capability.types import RISK_LEVELS, SIDE_EFFECTS

#: MCP protocol 钉版（设计 §7-②；其它版本一律拒）
MCP_PROTOCOL_VERSION = "2025-06-18"

_ALLOWED_TRANSPORTS = frozenset({"stdio", "http"})
#: side_effect / risk_level 词表直接引用 types 单一真源（capability 包内互引，
#: 不违 import-linter capability-outbound 契约——出边为空指禁出 capability 包）。
_ALLOWED_SIDE_EFFECTS = SIDE_EFFECTS
_ALLOWED_RISK_LEVELS = RISK_LEVELS

_DEFAULT_CONNECT_TIMEOUT_S = 10.0
_DEFAULT_CALL_TIMEOUT_S = 30.0

_SERVER_KEY_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")

_SERVER_KEYS = frozenset(
    {
        "key",
        "transport",
        "url",
        "command",
        "args",
        "cwd",
        "env_allowlist",
        "protocol_version",
        "expected_server",
        "connect_timeout_s",
        "call_timeout_s",
        "default_side_effect",
        "tool_overrides",
        "exclude_tools",
    }
)
_EXPECTED_SERVER_KEYS = frozenset({"name", "version"})
_OVERRIDE_KEYS = frozenset(
    {
        "side_effect",
        "idempotency_key",
        "hitl_required",
        "tenant_scoped",
        "risk_level",
        "description_override",
    }
)
_STDIO_ONLY_KEYS = frozenset({"command", "args", "cwd", "env_allowlist"})


class McpServersConfigError(ValueError):
    """``mcp_servers.yaml`` 解析/校验失败（fail-closed）。"""


@dataclass(frozen=True)
class McpExpectedServer:
    """握手后期望的 server 标识（T2 校验用）。"""

    name: str | None = None
    version: str | None = None


@dataclass(frozen=True)
class McpToolOverride:
    """单工具策略覆写（翻译注册期覆盖 server 上报默认值）。"""

    side_effect: str | None = None
    idempotency_key: str | None = None
    hitl_required: bool | None = None
    tenant_scoped: bool | None = None
    risk_level: str | None = None
    description_override: str | None = None


@dataclass(frozen=True)
class McpServerConfig:
    """单个 MCP server 的解析结果（不可变）。"""

    key: str
    transport: str  # "stdio" | "http"
    url: str | None = None
    command: str | None = None
    args: tuple[str, ...] = ()
    cwd: str | None = None
    env_allowlist: tuple[str, ...] = ()
    protocol_version: str = MCP_PROTOCOL_VERSION
    expected_server: McpExpectedServer | None = None
    connect_timeout_s: float = _DEFAULT_CONNECT_TIMEOUT_S
    call_timeout_s: float = _DEFAULT_CALL_TIMEOUT_S
    default_side_effect: str | None = None
    tool_overrides: dict[str, McpToolOverride] = field(default_factory=dict)
    exclude_tools: tuple[str, ...] = ()


def _err(server: str, msg: str) -> McpServersConfigError:
    return McpServersConfigError(f"mcp_servers.yaml · server[{server}]: {msg}")


def _require_str(value: Any, server: str, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise _err(server, f"{field_name} 必填且须非空字符串")
    return value


def _opt_str(value: Any, server: str, field_name: str) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str) or not value.strip():
        raise _err(server, f"{field_name} 须非空字符串")
    return value


def _opt_str_list(value: Any, server: str, field_name: str) -> tuple[str, ...]:
    if value is None:
        return ()
    if not isinstance(value, list) or any(not isinstance(v, str) or not v for v in value):
        raise _err(server, f"{field_name} 须为非空字符串列表")
    return tuple(value)


def _timeout(value: Any, server: str, field_name: str, default: float) -> float:
    if value is None:
        return default
    if isinstance(value, bool) or not isinstance(value, (int, float)) or value <= 0:
        raise _err(server, f"{field_name} 须为正数（bool 拒）")
    return float(value)


def _side_effect(value: Any, server: str, field_name: str) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str) or value not in _ALLOWED_SIDE_EFFECTS:
        raise _err(
            server,
            f"{field_name} 未知 side_effect 词表值 {value!r}（允许 {sorted(_ALLOWED_SIDE_EFFECTS)}）",
        )
    return value


def _parse_expected_server(raw: Any, server: str) -> McpExpectedServer | None:
    if raw is None:
        return None
    if not isinstance(raw, dict):
        raise _err(server, "expected_server 须为 mapping")
    unknown = set(raw) - _EXPECTED_SERVER_KEYS
    if unknown:
        raise _err(server, f"expected_server 未知键 {sorted(unknown)}")
    return McpExpectedServer(
        name=_opt_str(raw.get("name"), server, "expected_server.name"),
        version=_opt_str(raw.get("version"), server, "expected_server.version"),
    )


def _parse_tool_overrides(raw: Any, server: str) -> dict[str, McpToolOverride]:
    if raw is None:
        return {}
    if not isinstance(raw, dict):
        raise _err(server, "tool_overrides 须为 mapping（tool_name → override）")
    out: dict[str, McpToolOverride] = {}
    for tool_name, ov in raw.items():
        if not isinstance(tool_name, str) or not tool_name:
            raise _err(server, "tool_overrides 工具名须非空字符串")
        if not isinstance(ov, dict):
            raise _err(server, f"tool_overrides[{tool_name}] 须为 mapping")
        unknown = set(ov) - _OVERRIDE_KEYS
        if unknown:
            raise _err(server, f"tool_overrides[{tool_name}] 未知键 {sorted(unknown)}")
        risk = ov.get("risk_level")
        if risk is not None and risk not in _ALLOWED_RISK_LEVELS:
            raise _err(
                server,
                f"tool_overrides[{tool_name}].risk_level 未知词表值 {risk!r}"
                f"（允许 {sorted(_ALLOWED_RISK_LEVELS)}）",
            )
        for bool_key in ("hitl_required", "tenant_scoped"):
            if ov.get(bool_key) is not None and not isinstance(ov[bool_key], bool):
                raise _err(server, f"tool_overrides[{tool_name}].{bool_key} 须为 bool")
        out[tool_name] = McpToolOverride(
            side_effect=_side_effect(
                ov.get("side_effect"), server, f"tool_overrides[{tool_name}].side_effect"
            ),
            idempotency_key=_opt_str(
                ov.get("idempotency_key"), server, f"tool_overrides[{tool_name}].idempotency_key"
            ),
            hitl_required=ov.get("hitl_required"),
            tenant_scoped=ov.get("tenant_scoped"),
            risk_level=risk,
            description_override=_opt_str(
                ov.get("description_override"),
                server,
                f"tool_overrides[{tool_name}].description_override",
            ),
        )
    return out


def _parse_server(raw: Any, index: int) -> McpServerConfig:
    label = f"#{index}"
    if not isinstance(raw, dict):
        raise _err(label, "server 条目须为 mapping")
    key = raw.get("key")
    if isinstance(key, str) and key:
        label = key
    unknown = set(raw) - _SERVER_KEYS
    if unknown:
        raise _err(label, f"未知键 {sorted(unknown)}")
    key = _require_str(key, label, "key")
    if not _SERVER_KEY_RE.match(key):
        raise _err(key, f"key 须 kebab-case 无点（^[a-z0-9]+(?:-[a-z0-9]+)*$），收到 {key!r}")

    transport = _require_str(raw.get("transport"), key, "transport")
    if transport not in _ALLOWED_TRANSPORTS:
        raise _err(key, f"未知 transport {transport!r}（允许 {sorted(_ALLOWED_TRANSPORTS)}）")

    present = {k for k, v in raw.items() if v is not None}
    if transport == "http":
        bad = present & _STDIO_ONLY_KEYS
        if bad:
            raise _err(key, f"transport=http 禁带 stdio 键 {sorted(bad)}")
        url = _require_str(raw.get("url"), key, "url（transport=http 必填）")
        command = None
        args: tuple[str, ...] = ()
        cwd = None
        env_allowlist: tuple[str, ...] = ()
    else:  # stdio
        if "url" in present:
            raise _err(key, "transport=stdio 禁带 url")
        command = _require_str(raw.get("command"), key, "command（transport=stdio 必填）")
        url = None
        args = _opt_str_list(raw.get("args"), key, "args")
        cwd = _opt_str(raw.get("cwd"), key, "cwd")
        env_allowlist = _opt_str_list(raw.get("env_allowlist"), key, "env_allowlist")

    protocol_version = raw.get("protocol_version", MCP_PROTOCOL_VERSION)
    if protocol_version != MCP_PROTOCOL_VERSION:
        raise _err(
            key,
            f"protocol_version 钉版 {MCP_PROTOCOL_VERSION}，收到 {protocol_version!r}",
        )

    return McpServerConfig(
        key=key,
        transport=transport,
        url=url,
        command=command,
        args=args,
        cwd=cwd,
        env_allowlist=env_allowlist,
        protocol_version=protocol_version,
        expected_server=_parse_expected_server(raw.get("expected_server"), key),
        connect_timeout_s=_timeout(
            raw.get("connect_timeout_s"), key, "connect_timeout_s", _DEFAULT_CONNECT_TIMEOUT_S
        ),
        call_timeout_s=_timeout(
            raw.get("call_timeout_s"), key, "call_timeout_s", _DEFAULT_CALL_TIMEOUT_S
        ),
        default_side_effect=_side_effect(raw.get("default_side_effect"), key, "default_side_effect"),
        tool_overrides=_parse_tool_overrides(raw.get("tool_overrides"), key),
        exclude_tools=_opt_str_list(raw.get("exclude_tools"), key, "exclude_tools"),
    )


def parse_mcp_servers(data: Any) -> tuple[McpServerConfig, ...]:
    """解析 ``mcp_servers.yaml`` 的已加载对象（纯函数 · 零 IO）。

    `data` 须为 `{"servers": [...]}` 形态的 mapping；任何非法输入抛
    :class:`McpServersConfigError`（fail-closed）。
    """
    if not isinstance(data, dict):
        raise McpServersConfigError("mcp_servers.yaml 顶层须为 mapping（{servers: [...]}）")
    unknown_top = set(data) - {"servers"}
    if unknown_top:
        raise McpServersConfigError(f"mcp_servers.yaml 顶层未知键 {sorted(unknown_top)}")
    servers = data.get("servers")
    if servers is None:
        servers = []
    if not isinstance(servers, list):
        raise McpServersConfigError("mcp_servers.yaml · servers 须为列表")
    out: list[McpServerConfig] = []
    seen: set[str] = set()
    for i, raw in enumerate(servers):
        cfg = _parse_server(raw, i)
        if cfg.key in seen:
            raise _err(cfg.key, f"server key 重复 {cfg.key!r}")
        seen.add(cfg.key)
        out.append(cfg)
    return tuple(out)


def load_mcp_servers_config(path: str | Path) -> tuple[McpServerConfig, ...]:
    """读文件 + `yaml.safe_load` + :func:`parse_mcp_servers`（零连接）。

    文件缺失 / 非法 yaml / schema 非法均抛 :class:`McpServersConfigError`；
    降级（warn + MCP 面为空）是 T2 runtime 职责（设计 §10），本函数不降级。
    """
    p = Path(path)
    try:
        text = p.read_text(encoding="utf-8")
    except OSError as exc:
        raise McpServersConfigError(f"mcp_servers.yaml 读取失败 {p}: {exc}") from exc
    try:
        data = yaml.safe_load(text)
    except yaml.YAMLError as exc:
        raise McpServersConfigError(f"mcp_servers.yaml 非法 yaml {p}: {exc}") from exc
    return parse_mcp_servers(data)
