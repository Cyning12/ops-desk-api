"""P2b-T2 · MCP 薄 transport 层 + 会话管理（子包入口）。

零新外部依赖：stdio 走 asyncio 子进程，http 走既有 httpx。import 期零副作用
（不起子进程/不建 client/不读配置——连接全部发生在 McpSessionManager.start()，
由 main.py lifespan 在总闸开启时驱动）。
"""

from app.ops.capability.mcp.errors import (
    McpError,
    McpHandshakeError,
    McpIdentityMismatchError,
    McpProtocolError,
    McpTimeoutError,
    McpTransportError,
)
from app.ops.capability.mcp.manager import (
    McpSessionManager,
    default_transport_factory,
)
from app.ops.capability.mcp.session import (
    SUPPORTED_PROTOCOL_VERSIONS,
    McpSession,
    clamp_timeout_s,
)
from app.ops.capability.mcp.transport import (
    HttpTransport,
    McpTransport,
    StdioTransport,
    filtered_env,
)

__all__ = [
    "SUPPORTED_PROTOCOL_VERSIONS",
    "HttpTransport",
    "McpError",
    "McpHandshakeError",
    "McpIdentityMismatchError",
    "McpProtocolError",
    "McpSession",
    "McpSessionManager",
    "McpTimeoutError",
    "McpTransport",
    "McpTransportError",
    "StdioTransport",
    "clamp_timeout_s",
    "default_transport_factory",
    "filtered_env",
]
