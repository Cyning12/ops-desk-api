"""P2b-T2 · JSON-RPC 2.0 编解码（MCP 子集 · stdio 换行帧与 HTTP 共用）。

只做最小面：request / notification / result / error 四种消息构造 + 三态判别 +
远端 error 应答异常化。batching 不做（11 终稿 §11 非范围）。
"""

from __future__ import annotations

import itertools
from typing import Any

#: JSON-RPC 2.0 规范错误码（§5.1）
PARSE_ERROR = -32700
INVALID_REQUEST = -32600
METHOD_NOT_FOUND = -32601
INTERNAL_ERROR = -32603

_id_counter = itertools.count(1)


def next_id() -> int:
    """单调递增请求 id（进程内唯一即可 · MCP 无跨会话语义）。"""
    return next(_id_counter)


def make_request(req_id: Any, method: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    msg: dict[str, Any] = {"jsonrpc": "2.0", "id": req_id, "method": method}
    if params is not None:
        msg["params"] = params
    return msg


def make_notification(method: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    msg: dict[str, Any] = {"jsonrpc": "2.0", "method": method}
    if params is not None:
        msg["params"] = params
    return msg


def make_result(req_id: Any, result: Any) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": req_id, "result": result}


def make_error(
    req_id: Any, code: int, message: str, data: Any = None
) -> dict[str, Any]:
    err: dict[str, Any] = {"code": code, "message": message}
    if data is not None:
        err["data"] = data
    return {"jsonrpc": "2.0", "id": req_id, "error": err}


def is_request(msg: dict[str, Any]) -> bool:
    """server→client 请求（带 id 带 method · 必须回应，否则对端挂起）。"""
    return "method" in msg and "id" in msg


def is_notification(msg: dict[str, Any]) -> bool:
    """通知（带 method 无 id · 安全忽略，含 notifications/tools/list_changed）。"""
    return "method" in msg and "id" not in msg


def is_response(msg: dict[str, Any]) -> bool:
    """应答（带 id 无 method · result 或 error）。"""
    return "id" in msg and "method" not in msg


class JsonRpcRemoteError(Exception):
    """远端回 JSON-RPC error 应答（code/message/data）。

    无 ``cause`` 属性 → 不计熔断（业务类：server 活着并回答了）。
    """

    def __init__(self, code: int, message: str, data: Any = None) -> None:
        self.code = code
        self.data = data
        super().__init__(f"JSON-RPC error {code}: {message}")


__all__ = [
    "INTERNAL_ERROR",
    "INVALID_REQUEST",
    "METHOD_NOT_FOUND",
    "PARSE_ERROR",
    "JsonRpcRemoteError",
    "is_notification",
    "is_request",
    "is_response",
    "make_error",
    "make_notification",
    "make_request",
    "make_result",
    "next_id",
]
