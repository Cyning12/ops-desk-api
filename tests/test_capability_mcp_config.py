"""P2b-T1 · mcp_servers.yaml 配置面解析单测（纯解析 · 零连接）。

覆盖：happy path（stdio+http+默认值）、fail-closed 拒载面（非法 yaml / 缺键 /
未知 transport / 未知 side_effect 词表 / 传输互斥键 / 未知键 / 坏 server_key /
重复 key / protocol_version 不符钉版 / override 未知键 / exclude_tools 非 list /
超时非正 / 缺文件），及模块零网络 import 断言。
"""

from __future__ import annotations

import pytest

from app.ops.capability.mcp_config import (
    MCP_PROTOCOL_VERSION,
    McpServersConfigError,
    load_mcp_servers_config,
    parse_mcp_servers,
)

# --- happy path ---


def test_parse_happy_stdio_and_http_with_defaults():
    cfg = parse_mcp_servers(
        {
            "servers": [
                {"key": "fs", "transport": "stdio", "command": "npx",
                 "args": ["-y", "@mcp/fs"], "cwd": "/tmp", "env_allowlist": ["HOME"]},
                {"key": "remote-svc", "transport": "http", "url": "http://127.0.0.1:9000/mcp"},
            ]
        }
    )
    assert len(cfg) == 2
    stdio, http = cfg
    assert stdio.key == "fs"
    assert stdio.transport == "stdio"
    assert stdio.command == "npx"
    assert stdio.args == ("-y", "@mcp/fs")
    assert stdio.cwd == "/tmp"
    assert stdio.env_allowlist == ("HOME",)
    assert stdio.url is None
    # 默认值钉版
    assert stdio.protocol_version == MCP_PROTOCOL_VERSION == "2025-06-18"
    assert stdio.connect_timeout_s == 10.0
    assert stdio.call_timeout_s == 30.0
    assert stdio.default_side_effect is None
    assert stdio.tool_overrides == {}
    assert stdio.exclude_tools == ()
    assert http.key == "remote-svc"
    assert http.url == "http://127.0.0.1:9000/mcp"
    assert http.command is None
    assert http.args == ()


def test_parse_full_optional_fields():
    cfg = parse_mcp_servers(
        {
            "servers": [
                {
                    "key": "github",
                    "transport": "http",
                    "url": "https://mcp.example.com/sse",
                    "protocol_version": "2025-06-18",
                    "expected_server": {"name": "github-mcp", "version": "1.2.3"},
                    "connect_timeout_s": 5,
                    "call_timeout_s": 45.5,
                    "default_side_effect": "read",
                    "tool_overrides": {
                        "create_issue": {
                            "side_effect": "write",
                            "idempotency_key": "issue-{title}",
                            "hitl_required": True,
                            "tenant_scoped": True,
                            "risk_level": "medium",
                            "description_override": "建 issue（写操作 · 需 HITL）",
                        }
                    },
                    "exclude_tools": ["delete_repo"],
                }
            ]
        }
    )
    (srv,) = cfg
    assert srv.expected_server is not None
    assert srv.expected_server.name == "github-mcp"
    assert srv.expected_server.version == "1.2.3"
    assert srv.connect_timeout_s == 5.0
    assert srv.call_timeout_s == 45.5
    assert srv.default_side_effect == "read"
    ov = srv.tool_overrides["create_issue"]
    assert ov.side_effect == "write"
    assert ov.idempotency_key == "issue-{title}"
    assert ov.hitl_required is True
    assert ov.tenant_scoped is True
    assert ov.risk_level == "medium"
    assert ov.description_override == "建 issue（写操作 · 需 HITL）"
    assert srv.exclude_tools == ("delete_repo",)


def test_parse_empty_servers_list_ok():
    assert parse_mcp_servers({"servers": []}) == ()


def test_load_from_file(tmp_path):
    p = tmp_path / "mcp_servers.yaml"
    p.write_text(
        "servers:\n"
        "  - key: fs\n"
        "    transport: stdio\n"
        "    command: npx\n",
        encoding="utf-8",
    )
    cfg = load_mcp_servers_config(p)
    assert [s.key for s in cfg] == ["fs"]


# --- fail-closed 拒载面 ---


def test_reject_invalid_yaml(tmp_path):
    p = tmp_path / "bad.yaml"
    p.write_text("servers: [\n  - key: unclosed", encoding="utf-8")
    with pytest.raises(McpServersConfigError, match="非法 yaml"):
        load_mcp_servers_config(p)


def test_reject_missing_file(tmp_path):
    with pytest.raises(McpServersConfigError, match="读取失败"):
        load_mcp_servers_config(tmp_path / "nonexistent.yaml")


def test_reject_top_level_not_mapping():
    with pytest.raises(McpServersConfigError, match="顶层须为 mapping"):
        parse_mcp_servers(["servers"])


def test_reject_top_level_unknown_key():
    with pytest.raises(McpServersConfigError, match="顶层未知键"):
        parse_mcp_servers({"servers": [], "extra": 1})


def test_reject_servers_not_list():
    with pytest.raises(McpServersConfigError, match="servers 须为列表"):
        parse_mcp_servers({"servers": {}})


def test_reject_missing_key():
    with pytest.raises(McpServersConfigError, match="key 必填"):
        parse_mcp_servers({"servers": [{"transport": "http", "url": "http://x"}]})


def test_reject_missing_transport():
    with pytest.raises(McpServersConfigError, match="transport 必填"):
        parse_mcp_servers({"servers": [{"key": "fs", "command": "npx"}]})


def test_reject_unknown_transport():
    with pytest.raises(McpServersConfigError, match="未知 transport"):
        parse_mcp_servers({"servers": [{"key": "fs", "transport": "grpc"}]})


def test_reject_unknown_side_effect():
    with pytest.raises(McpServersConfigError, match="未知 side_effect 词表值"):
        parse_mcp_servers(
            {"servers": [{"key": "fs", "transport": "stdio", "command": "x",
                          "default_side_effect": "delete"}]}
        )


def test_reject_http_missing_url():
    with pytest.raises(McpServersConfigError, match="url（transport=http 必填）"):
        parse_mcp_servers({"servers": [{"key": "svc", "transport": "http"}]})


def test_reject_stdio_missing_command():
    with pytest.raises(McpServersConfigError, match="command（transport=stdio 必填）"):
        parse_mcp_servers({"servers": [{"key": "fs", "transport": "stdio"}]})


def test_reject_http_with_stdio_keys():
    for extra in ({"command": "x"}, {"args": ["a"]}, {"cwd": "/t"}, {"env_allowlist": ["H"]}):
        with pytest.raises(McpServersConfigError, match="禁带 stdio 键"):
            parse_mcp_servers(
                {"servers": [{"key": "svc", "transport": "http",
                              "url": "http://x", **extra}]}
            )


def test_reject_stdio_with_url():
    with pytest.raises(McpServersConfigError, match="禁带 url"):
        parse_mcp_servers(
            {"servers": [{"key": "fs", "transport": "stdio", "command": "x",
                          "url": "http://x"}]}
        )


def test_reject_unknown_server_key():
    with pytest.raises(McpServersConfigError, match="未知键"):
        parse_mcp_servers(
            {"servers": [{"key": "fs", "transport": "stdio", "command": "x",
                          "mystery": 1}]}
        )


def test_reject_bad_server_key():
    for bad in ("FS", "my.server", "-lead", "tail-", "double--dash", "with_underscore"):
        with pytest.raises(McpServersConfigError, match="kebab-case 无点"):
            parse_mcp_servers(
                {"servers": [{"key": bad, "transport": "stdio", "command": "x"}]}
            )


def test_reject_duplicate_server_key():
    with pytest.raises(McpServersConfigError, match="server key 重复"):
        parse_mcp_servers(
            {"servers": [
                {"key": "fs", "transport": "stdio", "command": "a"},
                {"key": "fs", "transport": "stdio", "command": "b"},
            ]}
        )


def test_reject_protocol_version_mismatch():
    with pytest.raises(McpServersConfigError, match="protocol_version 钉版"):
        parse_mcp_servers(
            {"servers": [{"key": "fs", "transport": "stdio", "command": "x",
                          "protocol_version": "2024-11-05"}]}
        )


def test_reject_override_unknown_key():
    with pytest.raises(McpServersConfigError, match=r"tool_overrides\[t\] 未知键"):
        parse_mcp_servers(
            {"servers": [{"key": "fs", "transport": "stdio", "command": "x",
                          "tool_overrides": {"t": {"bogus": 1}}}]}
        )


def test_reject_override_unknown_side_effect():
    with pytest.raises(McpServersConfigError, match="未知 side_effect 词表值"):
        parse_mcp_servers(
            {"servers": [{"key": "fs", "transport": "stdio", "command": "x",
                          "tool_overrides": {"t": {"side_effect": "nuke"}}}]}
        )


def test_reject_override_unknown_risk_level():
    with pytest.raises(McpServersConfigError, match="risk_level 未知词表值"):
        parse_mcp_servers(
            {"servers": [{"key": "fs", "transport": "stdio", "command": "x",
                          "tool_overrides": {"t": {"risk_level": "extreme"}}}]}
        )


def test_reject_override_non_bool_flags():
    with pytest.raises(McpServersConfigError, match="hitl_required 须为 bool"):
        parse_mcp_servers(
            {"servers": [{"key": "fs", "transport": "stdio", "command": "x",
                          "tool_overrides": {"t": {"hitl_required": "yes"}}}]}
        )


def test_reject_exclude_tools_not_list():
    with pytest.raises(McpServersConfigError, match="exclude_tools 须为非空字符串列表"):
        parse_mcp_servers(
            {"servers": [{"key": "fs", "transport": "stdio", "command": "x",
                          "exclude_tools": "not-a-list"}]}
        )


def test_reject_timeout_non_positive_or_bool():
    for bad in (0, -1, True, "10"):
        with pytest.raises(McpServersConfigError, match="须为正数"):
            parse_mcp_servers(
                {"servers": [{"key": "fs", "transport": "stdio", "command": "x",
                              "connect_timeout_s": bad}]}
            )


def test_reject_expected_server_unknown_key():
    with pytest.raises(McpServersConfigError, match="expected_server 未知键"):
        parse_mcp_servers(
            {"servers": [{"key": "fs", "transport": "stdio", "command": "x",
                          "expected_server": {"name": "n", "extra": 1}}]}
        )


# --- 零连接结构断言 ---


def test_module_imports_no_network_stack():
    """mcp_config 仅 stdlib+yaml+types：源内无网络/进程栈 import（零连接）。"""
    import ast
    from pathlib import Path

    import app.ops.capability.mcp_config as mod

    banned = {"httpx", "socket", "urllib", "subprocess", "requests", "aiohttp", "http"}
    tree = ast.parse(Path(mod.__file__).read_text(encoding="utf-8"))
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(a.name.split(".")[0] for a in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module.split(".")[0])
    assert not (banned & imported), f"网络/进程栈被 import: {banned & imported}"
