"""P2b-T3 · MCP 工具适配器（kind=mcp 条目的运行期执行体）。

职责（设计终稿 §7-① 翻译器/适配器分离 · §10 失败路径）：
- 仅支持 ``ainvoke``（异步闸链 ``_call_adapter_async`` 同构，照 ``GenericHttpAdapter`` 先例）；
  sync ``invoke`` fail-closed（raise ``McpSessionUnavailableError``）。
- session 解析：模块级当前 ``McpSessionManager``（lifespan 注入/清除）；未建立 →
  ``McpSessionUnavailableError``（字面 ``mcp_session_unavailable``，fail-closed，不静默降级）。
- 结果成形（R-G12）：``structuredContent`` 优先；否则拼接 ``text`` content 块包装；
  ``isError: true`` → raise ``McpToolError``（error 字面以 ``upstream_error`` 稳定码开头）；
  结果序列化超 64KB → 截断 + ``truncated: true``。

零新依赖（裁定 A）：不引入 MCP SDK；本模块不 import httpx（T2 零网络断言锚扫描全包）。
"""

from __future__ import annotations

import json
from typing import Any

from app.ops.capability.errors import UPSTREAM_ERROR

__all__ = [
    "MCP_RESULT_MAX_CHARS",
    "McpAdapter",
    "McpSessionUnavailableError",
    "McpToolError",
    "clear_session_manager",
    "get_session_manager",
    "set_session_manager",
    "shape_call_result",
]

#: R-G12 · 结果截断阈值（字符数，json.dumps 后测量）
MCP_RESULT_MAX_CHARS = 64 * 1024


class McpSessionUnavailableError(RuntimeError):
    """调用期 session 未建立（§10 fail-closed：ok=False，不降级、不静默）。"""


class McpToolError(RuntimeError):
    """MCP 工具返回 isError=true（R-D7'：→ ok=False + upstream_error 稳定码）。"""


# ---- lifespan 注入的当前 session manager（模块级单例槽位）----
# 启动期 ``register_connected`` 之后由 ``set_session_manager`` 注入；
# shutdown（manager.aclose 之后）由 ``clear_session_manager`` 摘除。
_CURRENT_MANAGER: Any | None = None


def set_session_manager(manager: Any) -> None:
    """lifespan 注入当前 McpSessionManager（duck-typed，避免反向 import）。"""

    global _CURRENT_MANAGER
    _CURRENT_MANAGER = manager


def clear_session_manager() -> None:
    """shutdown 摘除当前 manager（适配器此后一律 mcp_session_unavailable）。"""

    global _CURRENT_MANAGER
    _CURRENT_MANAGER = None


def get_session_manager() -> Any | None:
    """读取当前 manager（未注入 → None → fail-closed）。"""

    return _CURRENT_MANAGER


def _truncate_payload(payload: Any) -> Any:
    """R-G12：序列化超 64KB → 截断 + ``truncated: true``。"""

    try:
        text = json.dumps(payload, ensure_ascii=False, default=str)
    except (TypeError, ValueError):
        text = str(payload)
    if len(text) <= MCP_RESULT_MAX_CHARS:
        return payload
    return {"truncated": True, "text": text[:MCP_RESULT_MAX_CHARS]}


def shape_call_result(result: Any) -> Any:
    """R-G12 · tools/call 结果成形：

    - ``isError: true`` → raise ``McpToolError``（error 字面 ``upstream_error`` 开头）。
    - ``structuredContent`` 优先返回。
    - 否则拼接 text content 块 → ``{"text": ...}`` 包装；两者皆无 → ``{"content": ...}``。
    - 任一路径 64KB 截断 + ``truncated: true``。
    """

    if not isinstance(result, dict):
        return _truncate_payload({"value": result})
    if result.get("isError") is True:
        raise McpToolError(f"{UPSTREAM_ERROR}: MCP 工具返回 isError=true")
    structured = result.get("structuredContent")
    if structured is not None:
        return _truncate_payload(structured)
    content = result.get("content")
    if isinstance(content, list):
        texts = [
            block["text"]
            for block in content
            if isinstance(block, dict)
            and block.get("type") == "text"
            and isinstance(block.get("text"), str)
        ]
        if texts:
            return _truncate_payload({"text": "\n".join(texts)})
    return _truncate_payload({"content": content if content is not None else []})


class McpAdapter:
    """kind=mcp 能力适配器：invoke → McpSession.call_tool（tools/call）。

    构造由 ``manifest._build_adapter`` 的 mcp 分支完成（R5b 同源链路）；
    ``spec`` 为已校验 CapabilitySpec（V1-V13 已过闸）。
    """

    kind = "mcp"

    def __init__(self, spec: Any, *, server_key: str, tool_name: str) -> None:
        self.spec = spec
        self.server_key = server_key
        self.tool_name = tool_name

    def invoke(self, args: dict, *, ctx: Any = None) -> Any:
        """sync 路径 fail-closed：MCP 调用是异步 I/O，禁走同步闸链。"""

        raise McpSessionUnavailableError(
            "mcp_sync_invoke_disabled: MCP 能力仅支持 ainvoke（异步闸链）"
        )

    async def ainvoke(self, args: dict, *, ctx: Any = None) -> Any:
        manager = _CURRENT_MANAGER
        session = manager.get_session(self.server_key) if manager is not None else None
        if session is None:
            raise McpSessionUnavailableError(
                f"mcp_session_unavailable: server={self.server_key}"
            )
        arguments = args if isinstance(args, dict) else {}
        result = await session.call_tool(
            self.tool_name, arguments, side_effect=self.spec.side_effect
        )
        return shape_call_result(result)
