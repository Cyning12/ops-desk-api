"""Host V1-B · manifest 可撤销性四字段（D4）。

覆盖（task 验收 D4 映射）：
- 四字段类型/词表加载期校验：非法 → ManifestError 整文件失败；
- 矛盾声明拒：side_effect=irreversible + reversible=true → ManifestError
  （变异检验②的靶断言）；execution_type=process 无 stop 支持 → ManifestError；
- 缺字段不报错（manifest 向后兼容演进）；
- 缺失默认 HITL 三档：off 无行为 · observe 台账 reversibility_undeclared
  would_default_hitl · enforce 派生 hitl_required=True · 显式声明不派生（FP-7）；
- builtin.v1.yaml 四字段全覆盖（enforce 升级路径零误伤）。
"""

from __future__ import annotations

import copy
import json
import logging
from pathlib import Path

import pytest

from app.ops.capability.manifest import (
    BUILTIN_MANIFEST_PATH,
    ENV_REVERSIBILITY_MODE,
    ManifestError,
    _parse_and_validate,
    _validate_reversibility,
)
from app.ops.capability.types import CapabilitySpec

_LOCAL_BASE = {
    "id": "test_rev.cap",
    "kind": "local_fn",
    "description": "可撤销性探针",
    "when_to_use": "单测使用",
    "tags": ["test"],
    "risk_level": "low",
    "side_effect": "read",
    "enabled": True,
    "tenant_scoped": False,
    "args_schema": {"type": ["string", "object"], "properties": {}},
    "adapter": "local_fn:app.ops.capability.defaults:utc_now_iso",
}

_HTTP_IRREVERSIBLE = {
    "id": "test_rev.http_write",
    "kind": "http",
    "description": "http 不可逆写探针",
    "when_to_use": "单测使用",
    "tags": ["oa"],
    "risk_level": "medium",
    "side_effect": "irreversible",
    "enabled": True,
    "tenant_scoped": False,
    "visibility": {"departments": ["all"]},
    "hitl": {"required": True},
    "args_schema": {"type": "object", "properties": {"keyword": {"type": "string"}}},
    "http": {
        "method": "POST",
        "base_url": "OA_BASE",
        "path": "/api/v1/demo",
        "auth": "oa_gateway_token",
        "idempotency_key": "keyword",
        "success_when": {"path": "$.code", "in": [0, 200]},
        "error_map": {"1001": "args_schema_invalid", "5001": "upstream_error"},
    },
}


def _write(tmp_path: Path, caps: list[dict]) -> Path:
    path = tmp_path / "rev.test.json"
    path.write_text(
        json.dumps({"version": 1, "capabilities": caps}, ensure_ascii=False),
        encoding="utf-8",
    )
    return path


def _load(tmp_path: Path, caps: list[dict]):
    return _parse_and_validate(_write(tmp_path, caps))


# ---------------------------------------------------------------------------
# 四字段类型/词表校验（非法 → ManifestError 整文件失败）
# ---------------------------------------------------------------------------


def test_valid_four_fields_load(tmp_path):
    cap = {**_LOCAL_BASE, "reversible": True, "execution_type": "instant",
           "max_reversal_latency": 0, "requires_stop_support": False}
    _, pending = _load(tmp_path, [cap])
    spec = pending[0].spec
    assert spec.reversible is True
    assert spec.execution_type == "instant"
    assert spec.max_reversal_latency == 0
    assert spec.requires_stop_support is False


@pytest.mark.parametrize(
    "field,value,match",
    [
        ("reversible", 1, "reversible 必须是 bool"),
        ("reversible", "yes-str", "reversible 必须是 bool"),
        ("execution_type", "bogus", "execution_type 非法"),
        ("execution_type", "", "execution_type 非法"),
        ("max_reversal_latency", -1, "max_reversal_latency 必须是非负 int"),
        ("max_reversal_latency", "10", "max_reversal_latency 必须是非负 int"),
        ("max_reversal_latency", True, "max_reversal_latency 必须是非负 int"),
        ("requires_stop_support", "yes-str", "requires_stop_support 必须是 bool"),
    ],
)
def test_invalid_field_values_rejected(tmp_path, field, value, match):
    cap = {**_LOCAL_BASE, field: value}
    with pytest.raises(ManifestError, match=match):
        _load(tmp_path, [cap])


def test_execution_type_vocabulary_all_accepted(tmp_path):
    for et in ("instant", "target", "process"):
        cap = {**_LOCAL_BASE, "id": f"test_rev.{et}", "execution_type": et}
        if et == "process":
            cap["requires_stop_support"] = True
        _, pending = _load(tmp_path, [cap])
        assert pending[0].spec.execution_type == et


def test_missing_fields_not_an_error(tmp_path):
    """缺字段不报错（向后兼容）；四字段全 None = 未声明。"""
    _, pending = _load(tmp_path, [dict(_LOCAL_BASE)])
    spec = pending[0].spec
    assert spec.reversible is None
    assert spec.execution_type is None
    assert spec.max_reversal_latency is None
    assert spec.requires_stop_support is None
    assert spec.hitl_required is False


# ---------------------------------------------------------------------------
# 跨字段硬规则（矛盾声明拒 · process 无 stop 拒）
# ---------------------------------------------------------------------------


def test_contradiction_irreversible_plus_reversible_rejected_spec_level():
    spec = CapabilitySpec(
        capability_id="x", kind="local_fn", description="d",
        side_effect="irreversible", reversible=True, hitl_required=True,
    )
    with pytest.raises(ManifestError, match="矛盾声明"):
        _validate_reversibility(spec, loc="t")


def test_contradiction_rejected_manifest_level(tmp_path):
    """端到端：合法 http 不可逆写能力 + reversible: true → 矛盾校验拒（整文件失败）。"""
    cap = copy.deepcopy(_HTTP_IRREVERSIBLE)
    cap["reversible"] = True
    with pytest.raises(ManifestError, match="矛盾声明"):
        _load(tmp_path, [cap])


def test_process_without_stop_support_rejected(tmp_path):
    cap = {**_LOCAL_BASE, "execution_type": "process"}
    with pytest.raises(ManifestError, match="requires_stop_support"):
        _load(tmp_path, [cap])
    cap2 = {**_LOCAL_BASE, "execution_type": "process", "requires_stop_support": False}
    with pytest.raises(ManifestError, match="requires_stop_support"):
        _load(tmp_path, [cap2])


def test_target_with_reversible_false_loads_with_no_hard_error(tmp_path):
    """Q3：target + reversible=false 只观测不拒（契约不推测 · 非硬规则）。"""
    cap = {**_LOCAL_BASE, "execution_type": "target", "reversible": False}
    _, pending = _load(tmp_path, [cap])
    assert pending[0].spec.execution_type == "target"


# ---------------------------------------------------------------------------
# 缺失默认 HITL 三档（off / observe / enforce · 声明优先 FP-7）
# ---------------------------------------------------------------------------


def test_mode_off_no_behavior(monkeypatch, tmp_path, caplog):
    monkeypatch.setenv(ENV_REVERSIBILITY_MODE, "off")
    with caplog.at_level(logging.WARNING, logger="app.ops.capability.manifest"):
        _, pending = _load(tmp_path, [dict(_LOCAL_BASE)])
    assert pending[0].spec.hitl_required is False
    assert "reversibility_undeclared" not in caplog.text


def test_mode_invalid_falls_back_off(monkeypatch, tmp_path, caplog):
    monkeypatch.setenv(ENV_REVERSIBILITY_MODE, "bogus")
    with caplog.at_level(logging.WARNING, logger="app.ops.capability.manifest"):
        _, pending = _load(tmp_path, [dict(_LOCAL_BASE)])
    assert pending[0].spec.hitl_required is False
    assert "reversibility_undeclared" not in caplog.text


def test_mode_observe_audit_only(monkeypatch, tmp_path, caplog):
    monkeypatch.setenv(ENV_REVERSIBILITY_MODE, "observe")
    with caplog.at_level(logging.WARNING, logger="app.ops.capability.manifest"):
        _, pending = _load(tmp_path, [dict(_LOCAL_BASE)])
    assert pending[0].spec.hitl_required is False  # observe 不派生
    assert "reversibility_undeclared" in caplog.text
    assert "would_default_hitl" in caplog.text
    assert _LOCAL_BASE["id"] in caplog.text


def test_mode_enforce_derives_hitl_required(monkeypatch, tmp_path, caplog):
    monkeypatch.setenv(ENV_REVERSIBILITY_MODE, "enforce")
    with caplog.at_level(logging.WARNING, logger="app.ops.capability.manifest"):
        _, pending = _load(tmp_path, [dict(_LOCAL_BASE)])
    assert pending[0].spec.hitl_required is True
    assert "reversibility_undeclared" in caplog.text


def test_mode_enforce_explicit_declaration_not_derived(monkeypatch, tmp_path):
    """声明优先（FP-7）：显式声明合法（部分字段即可）→ 不派生。"""
    monkeypatch.setenv(ENV_REVERSIBILITY_MODE, "enforce")
    cap = {**_LOCAL_BASE, "execution_type": "instant"}
    _, pending = _load(tmp_path, [cap])
    assert pending[0].spec.hitl_required is False
    cap2 = {**_LOCAL_BASE, "id": "test_rev.cap2", "reversible": False}
    _, pending2 = _load(tmp_path, [cap2])
    assert pending2[0].spec.hitl_required is False


# ---------------------------------------------------------------------------
# builtin.v1.yaml 四字段全覆盖（enforce 升级路径零误伤）
# ---------------------------------------------------------------------------


def test_builtin_manifest_four_fields_fully_declared():
    _, pending = _parse_and_validate(BUILTIN_MANIFEST_PATH)
    assert pending, "builtin manifest 为空"
    for entry in pending:
        spec = entry.spec
        assert spec.reversible is not None, spec.capability_id
        assert spec.execution_type is not None, spec.capability_id
        assert spec.max_reversal_latency is not None, spec.capability_id
        assert spec.requires_stop_support is not None, spec.capability_id
