"""Capability Gateway · 稳定错误码词表（对模型暴露的唯一错误口径）。

设计约束（对齐 GUIDE_capability-registry-v1）：
- **七个，不增**。模型只认这一套；下游（老 OA / ERP / 私有协议）的错误码
  一律在 adapter 内归一化到本词表，不外泄。
- 形状统一 ``code`` 或 ``code: detail``（与既有 gateway / policy 文案兼容）：
  ``policy_blocked: high_risk`` / ``args_schema_invalid: ...``。

为什么要有这一层：下游返回 200 里嵌业务失败码、错误字符串各家不统一、
超时其实已成功——这些差异**必须在 adapter 层被吸收**，否则模型面对的是
一堆无法决策的字符串。
"""

from __future__ import annotations

# ---- 稳定错误码（唯一词表）----
UNKNOWN_ID = "unknown_id"
DISABLED = "disabled"
POLICY_BLOCKED = "policy_blocked"
ARGS_SCHEMA_INVALID = "args_schema_invalid"
DUPLICATE_ID = "duplicate_id"
UPSTREAM_ERROR = "upstream_error"
PERMISSION_DENIED = "permission_denied"

STABLE_ERROR_CODES: frozenset[str] = frozenset(
    {
        UNKNOWN_ID,
        DISABLED,
        POLICY_BLOCKED,
        ARGS_SCHEMA_INVALID,
        DUPLICATE_ID,
        UPSTREAM_ERROR,
        PERMISSION_DENIED,
    }
)

# 模型侧建议动作（供提示词 / 编排层参考；不在本模块强制）
RETRYABLE_CODES: frozenset[str] = frozenset({UPSTREAM_ERROR})
FIX_ARGS_CODES: frozenset[str] = frozenset({ARGS_SCHEMA_INVALID})
NO_RETRY_CODES: frozenset[str] = frozenset(
    {POLICY_BLOCKED, PERMISSION_DENIED, DISABLED, UNKNOWN_ID, DUPLICATE_ID}
)


def is_stable_error_code(code: str) -> bool:
    """是否为词表内的合法错误码（manifest ``error_map`` 校验用）。"""
    return str(code or "").strip() in STABLE_ERROR_CODES


def error_code_of(message: str) -> str | None:
    """从 ``"code: detail"`` 形状的消息里取回 code；不匹配返回 None。"""
    head = str(message or "").strip().split(":", 1)[0].strip()
    return head if head in STABLE_ERROR_CODES else None


def format_error(code: str, detail: str | None = None) -> str:
    """统一格式化：``code`` 或 ``code: detail``。"""
    base = str(code or "").strip() or UPSTREAM_ERROR
    text = str(detail or "").strip()
    return f"{base}: {text}" if text else base
