"""P2b-T2 · MCP 会话层异常族。

熔断计数口径（circuit.guard · errors.is_environmental_failure）：
- ``McpTransportError`` / ``McpTimeoutError`` 带 ``cause=CAUSE_TRANSPORT`` → 环境类，计熔断；
- 其余（握手失败 / 身份不匹配 / 协议违例）无 ``cause`` → 业务类，不计熔断
  （「下游活着并回答了」不熔 · errors.py:81 钉案）。
"""

from __future__ import annotations

from app.ops.capability.errors import CAUSE_HTTP_STATUS, CAUSE_TRANSPORT


class McpError(Exception):
    """MCP 面异常基类。"""


class McpTransportError(McpError):
    """传输层失败：子进程拉起失败 / 连接不通 / 写读帧失败 / 子进程中途退出 / HTTP 错误态。

    ``cause`` 默认 ``CAUSE_TRANSPORT``（环境类 → 计熔断）；HTTP 非 2xx 应答时置
    ``CAUSE_HTTP_STATUS`` + ``http_status``（5xx/429 才计 · errors.py:88-92）。
    """

    def __init__(
        self,
        message: str,
        *,
        cause: str = CAUSE_TRANSPORT,
        http_status: int | None = None,
    ) -> None:
        self.cause = cause
        self.http_status = http_status
        super().__init__(message)


class McpTimeoutError(McpTransportError):
    """请求超时（initialize / ping / tools/* 任一 · 继承 transport cause 计熔断）。"""


class McpProtocolError(McpError):
    """对端违反 JSON-RPC / MCP 帧纪律（非 JSON 帧 / HTTP 应答非 json 非 SSE 等）。"""


class McpHandshakeError(McpError):
    """initialize 握手失败：版本链耗尽 / 应答版本不在支持集 / ping 门未过。"""


class McpIdentityMismatchError(McpHandshakeError):
    """expected_server 校验失败（serverInfo.name 非精确相等）→ 拒连 + span reason=identity_mismatch。"""


__all__ = [
    "CAUSE_HTTP_STATUS",
    "McpError",
    "McpHandshakeError",
    "McpIdentityMismatchError",
    "McpProtocolError",
    "McpTimeoutError",
    "McpTransportError",
]
