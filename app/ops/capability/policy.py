"""Capability invoke Policy 门（H2 · Host-only 策略键；H4 · 写操作闸）。

对齐 SPEC §3.4：高危默认 blocked；``allow_*`` 等策略键仅 Host（env / ``ctx._host_policy``）
可写，模型 plan 顶层字段**不生效**。

H4 增补：``side_effect ∈ {write, irreversible}`` 亦默认 blocked。
理由：``risk_level`` 与 ``side_effect`` 是两个维度——``medium + write``
（普通提交）在只看 ``risk_level`` 的实现下会被完全放行。写操作的放行
信号只有两个来源：进程环境变量，或 Host 构造的 ``_host_policy.allow_write``
（后者用于「单次人工确认通过」的语义，**只对这一次调用有效**）。
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any

from app.ops.capability.errors import POLICY_BLOCKED, format_error
from app.ops.capability.types import WRITE_SIDE_EFFECTS, CapabilitySpec

# 模型 plan / 用户 ctx 顶层禁止直写（写入亦被忽略）
HOST_ONLY_POLICY_KEYS = frozenset(
    {
        "allow_high_risk",
        "allow_sandbox",
        "allow_cli",
        # H4：写操作放行键。进本集合后，模型 plan 顶层写它不生效，
        # 且 plan_ctx_has_host_only_keys 的单测能覆盖到。
        "allow_write",
        "policy_override",
    }
)

_ENV_ALLOW_HIGH_RISK = "OPS_CAPABILITY_ALLOW_HIGH_RISK"
_ENV_ALLOW_SANDBOX = "OPS_CAPABILITY_ALLOW_SANDBOX"
_ENV_ALLOW_CLI = "OPS_CAPABILITY_ALLOW_CLI"
_ENV_ALLOW_WRITE = "OPS_CAPABILITY_ALLOW_WRITE"


@dataclass(frozen=True)
class PolicyDecision:
    """Policy 判定结果。"""

    allowed: bool
    reason: str | None = None


def _env_bool(name: str) -> bool:
    return os.environ.get(name, "").strip().lower() in ("1", "true", "yes")


def _host_policy(ctx: dict[str, Any] | None) -> dict[str, Any]:
    if not ctx:
        return {}
    raw = ctx.get("_host_policy")
    return raw if isinstance(raw, dict) else {}


def plan_ctx_has_host_only_keys(ctx: dict[str, Any] | None) -> bool:
    """plan/state 是否误写 host-only 键（用于单测 · 这些键不生效）。"""
    if not ctx:
        return False
    return any(k in ctx for k in HOST_ONLY_POLICY_KEYS)


def _tenant_predicate(ctx: dict[str, Any] | None) -> Any:
    """租户谓词：``tenant_id`` 或 Host ``_host_tenant``（非空即视为已注入）。"""
    if not ctx:
        return None
    for key in ("tenant_id", "_host_tenant"):
        value = ctx.get(key)
        if value is not None and str(value).strip():
            return value
    return None


def write_allowed(ctx: dict[str, Any] | None) -> bool:
    """本次调用是否获得写放行（env 或 Host 单次放行）。

    对外暴露给回执层：回执要记「这次写是在放行下执行的」，而不只是「成功了」。
    """
    host = _host_policy(ctx)
    return _env_bool(_ENV_ALLOW_WRITE) or host.get("allow_write") is True


def check_invoke(
    spec: CapabilitySpec,
    *,
    ctx: dict[str, Any] | None = None,
) -> PolicyDecision:
    """``invoke`` / ``provide`` 前统一 Policy 校验。"""
    host = _host_policy(ctx)

    # 闸序：危险程度 → 副作用 → 危险形态 → 输入完整性
    if spec.risk_level == "high" and not (
        _env_bool(_ENV_ALLOW_HIGH_RISK) or host.get("allow_high_risk") is True
    ):
        return PolicyDecision(False, format_error(POLICY_BLOCKED, "high_risk"))

    # H4 写操作闸：与 risk_level **独立**（medium + write 亦默认拒）
    if spec.side_effect in WRITE_SIDE_EFFECTS and not write_allowed(ctx):
        return PolicyDecision(False, format_error(POLICY_BLOCKED, "write_not_confirmed"))

    if spec.kind == "sandbox" and not (
        _env_bool(_ENV_ALLOW_SANDBOX) or host.get("allow_sandbox") is True
    ):
        return PolicyDecision(False, format_error(POLICY_BLOCKED, "sandbox_disabled"))

    if spec.kind == "cli" and not (_env_bool(_ENV_ALLOW_CLI) or host.get("allow_cli") is True):
        return PolicyDecision(False, format_error(POLICY_BLOCKED, "cli_disabled"))

    if getattr(spec, "tenant_scoped", False) and _tenant_predicate(ctx) is None:
        return PolicyDecision(False, format_error(POLICY_BLOCKED, "tenant_scope_missing"))

    return PolicyDecision(True, None)
