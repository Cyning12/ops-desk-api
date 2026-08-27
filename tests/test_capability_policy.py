"""H2 · Capability Policy 门（mock · 无真 shell）。"""

from __future__ import annotations

import os
from unittest.mock import patch

import pytest

from app.ops.capability import CapabilitySpec, LocalFnAdapter, invoke, register, unregister
from app.ops.capability.defaults import ensure_default_capabilities
from app.ops.capability.gateway import get_registry
from app.ops.capability.policy import (
    HOST_ONLY_POLICY_KEYS,
    PolicyDecision,
    check_invoke,
    plan_ctx_has_host_only_keys,
)
from app.ops.capability.probes import PROBE_SANDBOX_ID, register_p2_probes


@pytest.fixture(autouse=True)
def _restore_registry():
    yield
    get_registry().clear()
    ensure_default_capabilities()


def test_high_risk_default_blocked():
    def _fn(_: str) -> dict:
        return {"ok": True}

    cid = "test_high_risk_fn"
    register(
        CapabilitySpec(
            capability_id=cid,
            kind="local_fn",
            description="高危探针",
            risk_level="high",
            enabled=True,
        ),
        LocalFnAdapter(_fn),
    )
    result = invoke(cid, "x")
    assert result.ok is False
    assert "policy_blocked" in (result.error or "")
    assert result.meta.get("policy_blocked") is True
    unregister(cid)


def test_high_risk_allowed_via_host_policy():
    def _fn(_: str) -> dict:
        return {"ok": True}

    cid = "test_high_risk_host"
    register(
        CapabilitySpec(
            capability_id=cid,
            kind="local_fn",
            description="高危 · host 放行",
            risk_level="high",
            enabled=True,
        ),
        LocalFnAdapter(_fn),
    )
    result = invoke(cid, "x", ctx={"_host_policy": {"allow_high_risk": True}})
    assert result.ok is True
    unregister(cid)


def test_plan_top_level_host_keys_ignored():
    def _fn(_: str) -> dict:
        return {"ok": True}

    cid = "test_high_risk_plan_ignore"
    register(
        CapabilitySpec(
            capability_id=cid,
            kind="local_fn",
            description="plan 不可写 allow_high_risk",
            risk_level="high",
            enabled=True,
        ),
        LocalFnAdapter(_fn),
    )
    ctx = {"allow_high_risk": True}
    assert plan_ctx_has_host_only_keys(ctx)
    result = invoke(cid, "x", ctx=ctx)
    assert result.ok is False
    assert "policy_blocked" in (result.error or "")
    unregister(cid)


def test_check_invoke_low_risk_allowed():
    spec = CapabilitySpec(
        capability_id="low",
        kind="local_fn",
        description="低危",
        risk_level="low",
    )
    assert check_invoke(spec).allowed is True


def test_sandbox_probe_blocked_without_env():
    register_p2_probes(enabled=True)
    result = invoke(PROBE_SANDBOX_ID, "echo")
    assert result.ok is False
    assert "policy_blocked" in (result.error or "")


def test_sandbox_probe_allowed_with_env():
    register_p2_probes(enabled=True)
    with patch.dict(os.environ, {"OPS_CAPABILITY_ALLOW_SANDBOX": "true"}):
        result = invoke(PROBE_SANDBOX_ID, "echo")
    assert result.ok is True


def test_host_only_keys_documented():
    assert "allow_high_risk" in HOST_ONLY_POLICY_KEYS
    assert "policy_override" in HOST_ONLY_POLICY_KEYS


def test_policy_decision_frozen():
    d = PolicyDecision(False, "policy_blocked: high_risk")
    assert d.allowed is False
    assert d.reason == "policy_blocked: high_risk"
