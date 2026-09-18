"""阶段 T · 只读租户上下文（F1=C · Fixture 轨）。

session 为真源；若请求带 ``X-Ops-Tenant-Id`` 则必须与 session 一致，否则调用方应 403。
图内 lookup / RAG 通过 ContextVar 读取当前租户（由 HTTP 入口设置）。
"""

from __future__ import annotations

from contextvars import ContextVar, Token

TENANT_A = "ops-desk-pilot"
TENANT_B = "ops-desk-pilot-b"
ALLOWED_TENANTS = frozenset({TENANT_A, TENANT_B})
TENANT_HEADER = "X-Ops-Tenant-Id"

_current: ContextVar[str | None] = ContextVar("ops_tenant_id", default=None)


def current_tenant() -> str | None:
    """请求级租户；CLI / 无 HTTP 时为 None（检索不强制过滤）。"""
    return _current.get()


def current_tenant_or_default() -> str:
    """图内 tool_exec：优先请求租户，否则试点 A。"""
    return _current.get() or TENANT_A


def set_current_tenant(tenant_id: str) -> Token[str | None]:
    return _current.set(tenant_id)


def reset_current_tenant(token: Token[str | None]) -> None:
    _current.reset(token)


def normalize_tenant(raw: str | None) -> str:
    value = (raw or "").strip() or TENANT_A
    if value not in ALLOWED_TENANTS:
        raise ValueError(f"unknown_tenant:{value}")
    return value


def resolve_header_against_session(session_tenant: str | None, header: str | None) -> str:
    """F1=C：session 真源；头缺失则用 session；头存在且不一致 → ValueError（调用方映射 403）。"""
    session = normalize_tenant(session_tenant)
    raw = (header or "").strip()
    if not raw:
        return session
    if raw not in ALLOWED_TENANTS:
        raise ValueError(f"unknown_tenant:{raw}")
    if raw != session:
        raise ValueError("tenant_header_mismatch")
    return session
