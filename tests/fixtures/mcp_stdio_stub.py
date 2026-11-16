#!/usr/bin/env python3
"""P2b-T2 e2e 用零依赖 MCP stdio 桩 server（换行 JSON-RPC 行帧 · 仅 stdlib）。

行为面（环境变量注入 · 经 StdioTransport env_allowlist 白名单传入）
-------------------------------------------------------------------
- MCP_STUB_PROTOCOL_VERSION：initialize 应答的 protocolVersion（默认 2025-06-18）。
- MCP_STUB_SERVER_NAME：serverInfo.name（默认 opsdesk-mcp-stub）。
- MCP_STUB_MODE：`ok`（默认）正常握手；`bad_json` 首帧回非 JSON 行（负例用）。

实现面：逐行读 stdin JSON-RPC 帧：
- initialize → result(protocolVersion/serverInfo/capabilities)
- notifications/*（无 id）→ 忽略不回帧
- ping → {}
- tools/list → 固定两枚工具（echo / sum）
- tools/call → echo 回显 text / sum 求和
- server→client 方向测试由 client 侧 FakeTransport 覆盖，桩不主动发请求。
"""

from __future__ import annotations

import json
import os
import sys

PROTOCOL_VERSION = os.environ.get("MCP_STUB_PROTOCOL_VERSION", "2025-06-18")
SERVER_NAME = os.environ.get("MCP_STUB_SERVER_NAME", "opsdesk-mcp-stub")
MODE = os.environ.get("MCP_STUB_MODE", "ok")

TOOLS = [
    {
        "name": "echo",
        "description": "回显 text 参数",
        "inputSchema": {
            "type": "object",
            "properties": {"text": {"type": "string"}},
        },
    },
    {
        "name": "sum",
        "description": "两数求和",
        "inputSchema": {
            "type": "object",
            "properties": {"a": {"type": "number"}, "b": {"type": "number"}},
        },
    },
]


def _result(msg_id, result) -> None:
    sys.stdout.write(json.dumps({"jsonrpc": "2.0", "id": msg_id, "result": result}) + "\n")
    sys.stdout.flush()


def _error(msg_id, code: int, message: str) -> None:
    sys.stdout.write(
        json.dumps({"jsonrpc": "2.0", "id": msg_id, "error": {"code": code, "message": message}})
        + "\n"
    )
    sys.stdout.flush()


def _handle(msg) -> None:
    if not isinstance(msg, dict):
        return
    method = msg.get("method")
    msg_id = msg.get("id")
    if method is None:
        return
    if msg_id is None:
        return  # 通知：不回帧
    if method == "initialize":
        _result(
            msg_id,
            {
                "protocolVersion": PROTOCOL_VERSION,
                "capabilities": {"tools": {"listChanged": False}},
                "serverInfo": {"name": SERVER_NAME, "version": "0.0.1"},
            },
        )
    elif method == "ping":
        _result(msg_id, {})
    elif method == "tools/list":
        _result(msg_id, {"tools": TOOLS})
    elif method == "tools/call":
        params = msg.get("params") or {}
        name = params.get("name")
        args = params.get("arguments") or {}
        if name == "echo":
            text = str(args.get("text", ""))
            _result(msg_id, {"content": [{"type": "text", "text": text}], "isError": False})
        elif name == "sum":
            total = float(args.get("a", 0)) + float(args.get("b", 0))
            _result(msg_id, {"content": [{"type": "text", "text": str(total)}], "isError": False})
        else:
            _error(msg_id, -32602, f"unknown tool: {name}")
    else:
        _error(msg_id, -32601, f"method not found: {method}")


def main() -> int:
    first = True
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        if first and MODE == "bad_json":
            sys.stdout.write("this is not json\n")
            sys.stdout.flush()
            return 0  # 立即退出，模拟损坏 server
        first = False
        try:
            msg = json.loads(line)
        except json.JSONDecodeError:
            continue
        _handle(msg)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
