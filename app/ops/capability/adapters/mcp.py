"""MCP kind 探针 adapter（Capability Gateway · P2）。

**Mock only**：不连真 MCP server / 外网。默认**不**进入
``ensure_default_capabilities``；本地启用见 ``app.ops.capability.probes``。
"""

from __future__ import annotations

from typing import Any


class MockMcpAdapter:
    """MCP 协议罐头探针；``invoke`` 返回固定结构，零网络。"""

    kind = "mcp"

    def invoke(self, args: Any, *, ctx: dict[str, Any] | None = None) -> Any:
        del ctx
        return {
            "protocol": "mcp-mock",
            "kind": self.kind,
            "input": args,
            "result": {"echo": args, "source": "canned"},
        }
