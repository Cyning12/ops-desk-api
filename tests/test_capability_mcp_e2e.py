"""P2b-T2 · e2e 冒烟：真 stdio 子进程握手（零依赖桩 server）+ 负例三枚 + lifespan 接线。

冒烟面（委派书 m00002 · 登记偏差 D4：无零安装真 server，以最小手工 JSON-RPC stdio 脚本充当）
-------------------------------------------------------------------------------------------
- 真 `asyncio.create_subprocess_exec` 起 `tests/fixtures/mcp_stdio_stub.py`（仅 stdlib）：
  握手 → ping 门 → tools/list → tools/call 全链路；
- env 白名单端到端：MCP_STUB_PROTOCOL_VERSION 仅在 env_allowlist 列名时传入子进程
  （兼证 §5.3 不继承 os.environ：不设白名单时桩回默认钉版）；
- 负例三枚：不存在命令 / http 端口不通 / server 返回非 JSON——均 warn 隔离不炸启动；
- import 零网络 AST 断言：mcp 包仅 transport.py 可 import httpx，全包禁 socket/urllib/requests；
- lifespan：总闸 off 零创建；on+坏路径 warn 降级不炸；on+正常配置 manager 挂上且退出回收。
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.ops.capability.mcp.manager import McpSessionManager
from app.ops.capability.mcp_config import load_mcp_servers_config

FIXTURE = Path(__file__).parent / "fixtures" / "mcp_stdio_stub.py"
REPO_ROOT = Path(__file__).parent.parent
MCP_PKG = REPO_ROOT / "app" / "ops" / "capability" / "mcp"


def _write_yaml(tmp_path: Path, body: str) -> Path:
    path = tmp_path / "mcp_servers.yaml"
    path.write_text(body, encoding="utf-8")
    return path


def _stdio_yaml(**server_overrides) -> str:
    lines = [
        "servers:",
        "  - key: stub",
        "    transport: stdio",
        f"    command: {sys.executable}",
        f"    args: [{FIXTURE}]",
    ]
    for key, value in server_overrides.items():
        lines.append(f"    {key}: {value}")
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------- stdio e2e 冒烟


async def test_stdio_handshake_and_call_tool_e2e(tmp_path) -> None:
    configs = load_mcp_servers_config(_write_yaml(tmp_path, _stdio_yaml()))
    manager = McpSessionManager(configs)
    await manager.start()
    session = manager.get_session("stub")
    assert session is not None
    assert session.negotiated_version == "2025-06-18"
    assert session.server_info["name"] == "opsdesk-mcp-stub"
    assert [t["name"] for t in session.tools] == ["echo", "sum"]
    result = await session.call_tool("echo", {"text": "p2b-t2"}, side_effect="read")
    assert result["content"] == [{"type": "text", "text": "p2b-t2"}]
    await manager.aclose()
    # 子进程已回收（terminate → kill 兜底）
    proc = session.transport._proc
    assert proc is not None and proc.returncode is not None


async def test_stdio_env_allowlist_passes_protocol_version_e2e(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("MCP_STUB_PROTOCOL_VERSION", "2024-11-05")
    # 白名单列名 → 子进程可见 → 握手降级链实证（server 应答 2024-11-05）
    configs = load_mcp_servers_config(
        _write_yaml(tmp_path, _stdio_yaml(env_allowlist="[MCP_STUB_PROTOCOL_VERSION]"))
    )
    manager = McpSessionManager(configs)
    await manager.start()
    session = manager.get_session("stub")
    assert session is not None
    assert session.negotiated_version == "2024-11-05"
    await manager.aclose()


async def test_stdio_env_not_allowlisted_defaults_to_pinned_e2e(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("MCP_STUB_PROTOCOL_VERSION", "2024-11-05")
    # 不设白名单 → 子进程看不到该 env（§5.3 不继承 os.environ）→ 桩回默认钉版
    configs = load_mcp_servers_config(_write_yaml(tmp_path, _stdio_yaml()))
    manager = McpSessionManager(configs)
    await manager.start()
    session = manager.get_session("stub")
    assert session is not None
    assert session.negotiated_version == "2025-06-18"
    await manager.aclose()


async def test_stdio_identity_mismatch_rejected_e2e(tmp_path) -> None:
    configs = load_mcp_servers_config(
        _write_yaml(
            tmp_path,
            _stdio_yaml() + "    expected_server: {name: not-the-stub}\n".replace(
                "servers:", "servers:"
            ),
        )
    )
    manager = McpSessionManager(configs)
    await manager.start()  # 不抛：隔离
    assert manager.get_session("stub") is None
    await manager.aclose()


# ---------------------------------------------------------------- 负例三枚


async def test_negative_nonexistent_command_isolated(tmp_path, caplog) -> None:
    configs = load_mcp_servers_config(
        _write_yaml(tmp_path, _stdio_yaml().replace(sys.executable, "/nonexistent/mcp-server-xyz"))
    )
    manager = McpSessionManager(configs)
    with caplog.at_level("WARNING"):
        await manager.start()  # 不炸启动
    assert manager.get_session("stub") is None
    assert any("建连失败" in r.message for r in caplog.records)
    await manager.aclose()


async def test_negative_http_port_unreachable_isolated(tmp_path, caplog) -> None:
    body = (
        "servers:\n"
        "  - key: bad-http\n"
        "    transport: http\n"
        "    url: http://127.0.0.1:9/mcp\n"  # discard 端口：连接即拒
        "    connect_timeout_s: 2\n"
    )
    configs = load_mcp_servers_config(_write_yaml(tmp_path, body))
    manager = McpSessionManager(configs)
    with caplog.at_level("WARNING"):
        await manager.start()
    assert manager.get_session("bad-http") is None
    assert any("建连失败" in r.message for r in caplog.records)
    await manager.aclose()


async def test_negative_non_json_response_isolated(tmp_path, monkeypatch, caplog) -> None:
    monkeypatch.setenv("MCP_STUB_MODE", "bad_json")
    configs = load_mcp_servers_config(
        _write_yaml(tmp_path, _stdio_yaml(env_allowlist="[MCP_STUB_MODE]"))
    )
    manager = McpSessionManager(configs)
    with caplog.at_level("WARNING"):
        await manager.start()
    assert manager.get_session("stub") is None
    assert any("建连失败" in r.message for r in caplog.records)
    await manager.aclose()


# ---------------------------------------------------------------- import 零网络 AST 断言


def test_mcp_package_has_no_network_imports_except_httpx_in_transport() -> None:
    banned_modules = {"socket", "urllib", "requests", "aiohttp"}
    for path in sorted(MCP_PKG.glob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        imported: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported.add(node.module.split(".")[0])
        assert "subprocess" not in imported, f"{path.name} 禁 subprocess 模块（用 asyncio）"
        assert not (imported & banned_modules), f"{path.name} 禁网络库 {imported & banned_modules}"
        if path.name != "transport.py":
            assert "httpx" not in imported, f"{path.name} 唯 transport.py 可 import httpx"


# ---------------------------------------------------------------- lifespan 接线


def _settings_mcp(monkeypatch, *, enabled: bool, config_path: str | None) -> None:
    from app.config import settings

    monkeypatch.setattr(settings, "ops_capability_mcp_enabled", enabled)
    monkeypatch.setattr(settings, "ops_capability_mcp_servers_config", config_path)


def test_lifespan_gate_off_creates_nothing(monkeypatch) -> None:
    _settings_mcp(monkeypatch, enabled=False, config_path=None)
    with TestClient(app):
        assert not hasattr(app.state, "mcp_sessions")


def test_lifespan_gate_on_bad_config_path_degrades(monkeypatch, caplog) -> None:
    _settings_mcp(monkeypatch, enabled=True, config_path="/nonexistent/mcp_servers.yaml")
    with caplog.at_level("WARNING"), TestClient(app):  # 不炸启动（§10 降级）
        assert not hasattr(app.state, "mcp_sessions")
    assert any("MCP 面降级为空" in r.message for r in caplog.records)


def test_lifespan_gate_on_missing_config_key_degrades(monkeypatch, caplog) -> None:
    _settings_mcp(monkeypatch, enabled=True, config_path=None)
    with caplog.at_level("WARNING"), TestClient(app):
        assert not hasattr(app.state, "mcp_sessions")
    assert any("OPS_CAPABILITY_MCP_SERVERS_CONFIG" in r.message for r in caplog.records)


def test_lifespan_gate_on_connects_and_shutdown_reaps(monkeypatch, tmp_path) -> None:
    config_path = _write_yaml(tmp_path, _stdio_yaml())
    _settings_mcp(monkeypatch, enabled=True, config_path=str(config_path))
    with TestClient(app):
        manager = app.state.mcp_sessions
        assert isinstance(manager, McpSessionManager)
        assert manager.get_session("stub") is not None
        proc = manager.get_session("stub").transport._proc
    # 退出 lifespan 后：session 逆序关闭 + 子进程回收
    assert manager.connected_keys() == ()
    assert proc is not None and proc.returncode is not None


@pytest.mark.parametrize("mode", ["bad_config", "gate_off"])
def test_lifespan_smoke_modes_stable(monkeypatch, mode) -> None:
    # 占位防回归：两降级模式重复进出 lifespan 均无状态泄漏。
    # 注意 app 为模块级单例：前序用例可能在 app.state 留 mcp_sessions——
    # 本断言关心「本趟 lifespan 是否新建」，先清残留再进出。
    for _ in range(2):
        if hasattr(app.state, "mcp_sessions"):
            delattr(app.state, "mcp_sessions")
        if mode == "bad_config":
            _settings_mcp(monkeypatch, enabled=True, config_path="/nonexistent/x.yaml")
        else:
            _settings_mcp(monkeypatch, enabled=False, config_path=None)
        with TestClient(app):
            assert not hasattr(app.state, "mcp_sessions")
