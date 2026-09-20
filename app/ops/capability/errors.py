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


# ---- 失败成因（熔断的判定依据；**结构化，不解析文案**）----
#
# 为什么需要：``upstream_error`` 一个码里同时混着三种完全不同的东西——
#   传输层故障（下游不响应）  → 该熔
#   HTTP 5xx / 429           → 该熔
#   HTTP 200 + 未识别业务码   → 下游活着且回答了，**不该熔**
#   本地配置缺失（base_url / 凭证 / 存储接口）→ 我们自己没配好，**不该熔**
# 只用 code 判断的话，"用户填错 5 次参数"会把整个能力熔断 60s；
# 用 detail 字符串判断的话，文案一改熔断就静默失效（V7 那类死代码问题）。

#: 传输层：超时 / 连接失败 / DNS / 第三方 transport 抛裸异常
CAUSE_TRANSPORT = "transport"
#: HTTP 状态码层：5xx / 429 计环境类，其余按业务响应处理
CAUSE_HTTP_STATUS = "http_status"
#: 业务层：下游返回了结构化响应（含未识别的业务码）
CAUSE_BUSINESS = "business"
#: 本地装配层：我们这边没配好（缺 base_url / 缺凭证 / 存储接口不匹配 / 模板没声明）
CAUSE_LOCAL = "local"

CAUSES: frozenset[str] = frozenset(
    {CAUSE_TRANSPORT, CAUSE_HTTP_STATUS, CAUSE_BUSINESS, CAUSE_LOCAL}
)

#: 计入熔断的 HTTP 状态码：服务端故障 + 过载限流
TRIP_HTTP_STATUSES: frozenset[int] = frozenset({429})
TRIP_HTTP_STATUS_MIN = 500


def is_environmental_failure(cause: str | None, http_status: int | None = None) -> bool:
    """这次失败是不是"下游不健康"——**熔断只计这一类**。

    判据一句话：**「下游活着并回答了」就不该熔；只有「不响应 / 5xx / 429」才熔。**

    ``cause`` 缺失时（老调用点没填 / 非 HttpCapabilityError）**一律不算环境类**——
    宁可少熔，不可误熔：误熔等于把一个能用的能力停 60s。
    """
    if cause == CAUSE_TRANSPORT:
        return True
    if cause == CAUSE_HTTP_STATUS:
        if http_status is None:
            # 标了状态码层却没给状态码：不敢判定，按业务类处理（少熔）
            return False
        return http_status >= TRIP_HTTP_STATUS_MIN or http_status in TRIP_HTTP_STATUSES
    return False


def error_code_of(message: str) -> str | None:
    """从 ``"code: detail"`` 形状的消息里取回 code；不匹配返回 None。"""
    head = str(message or "").strip().split(":", 1)[0].strip()
    return head if head in STABLE_ERROR_CODES else None


def format_error(code: str, detail: str | None = None) -> str:
    """统一格式化：``code`` 或 ``code: detail``。"""
    base = str(code or "").strip() or UPSTREAM_ERROR
    text = str(detail or "").strip()
    return f"{base}: {text}" if text else base
