"""Capability invoke Policy 门（H2 · Host-only 策略键）。

对齐 SPEC §3.4：高危默认 blocked；``allow_*`` 等策略键仅 Host（env / ``ctx._host_policy``）
可写，模型 plan 顶层字段**不生效**。
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any

from app.ops.capability.types import CapabilitySpec

# 模型 plan / 用户 ctx 顶层禁止直写（写入亦被忽略）
HOST_ONLY_POLICY_KEYS = frozenset(
    {
        "allow_high_risk",
        "allow_sandbox",
        "allow_cli",
        "policy_override",
    }
)

_ENV_ALLOW_HIGH_RISK = "OPS_CAPABILITY_ALLOW_HIGH_RISK"
_ENV_ALLOW_SANDBOX = "OPS_CAPABILITY_ALLOW_SANDBOX"
_ENV_ALLOW_CLI = "OPS_CAPABILITY_ALLOW_CLI"


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


def check_invoke(
    spec: CapabilitySpec,
    *,
    ctx: dict[str, Any] | None = None,
) -> PolicyDecision:
    """``invoke`` / ``provide`` 前统一 Policy 校验。"""
    host = _host_policy(ctx)

    if spec.risk_level == "high" and not (
        _env_bool(_ENV_ALLOW_HIGH_RISK) or host.get("allow_high_risk") is True
    ):
        return PolicyDecision(False, "policy_blocked: high_risk")

    if spec.kind == "sandbox" and not (
        _env_bool(_ENV_ALLOW_SANDBOX) or host.get("allow_sandbox") is True
    ):
        return PolicyDecision(False, "policy_blocked: sandbox_disabled")

    if spec.kind == "cli" and not (
        _env_bool(_ENV_ALLOW_CLI) or host.get("allow_cli") is True
    ):
        return PolicyDecision(False, "policy_blocked: cli_disabled")

    return PolicyDecision(True, None)
