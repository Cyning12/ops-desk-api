"""H4 · 多文件 manifest + ``kind=http`` 契约 + 加载期强校验 V1–V8。

原则：**能在加载期发现，就不要留到运行期。**
本文件只测「加载期能不能拦住」；运行期行为见 test_capability_http_adapter.py。
"""

from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from app.ops.capability import list_capabilities, schemas_for_llm
from app.ops.capability.defaults import ensure_default_capabilities
from app.ops.capability.errors import STABLE_ERROR_CODES
from app.ops.capability.gateway import get_registry
from app.ops.capability.manifest import (
    MANIFEST_DIR,
    ManifestError,
    load_capability_manifest,
    load_capability_manifests,
    reload_capability_manifest,
)

pytestmark = pytest.mark.filterwarnings("ignore::UserWarning")

_HTTP_BASE = {
    "method": "GET",
    "base_url": "OA_BASE",
    "path": "/api/v1/demo",
    "auth": "oa_gateway_token",
    "query_map": {"q": "{{keyword}}"},
    "timeout_ms": 8000,
    "success_when": {"path": "$.code", "in": [0, 200]},
    "error_map": {"1001": "args_schema_invalid", "5001": "upstream_error"},
}

_CAP_BASE = {
    "id": "oa.demo.read",
    "kind": "http",
    "description": "demo 只读能力",
    "when_to_use": "单测使用",
    "tags": ["oa"],
    "risk_level": "low",
    "side_effect": "read",
    "enabled": True,
    "tenant_scoped": False,
    "args_schema": {"type": "object", "properties": {"keyword": {"type": "string"}}},
    "http": _HTTP_BASE,
}


@pytest.fixture(autouse=True)
def _restore_defaults():
    yield
    get_registry().clear()
    ensure_default_capabilities()


def _cap(**over) -> dict:
    """构造一条 http 能力；``http_`` 前缀键合并进 http 块。"""
    cap = copy.deepcopy(_CAP_BASE)
    http_over = {
        k[len("http_"):]: v for k, v in over.items() if k.startswith("http_")
    }
    for k, v in over.items():
        if not k.startswith("http_"):
            cap[k] = v
    cap["http"].update(http_over)
    return cap


def _write(tmp_path: Path, name: str, caps: list[dict], version: int = 1) -> Path:
    path = tmp_path / name
    path.write_text(
        json.dumps({"version": version, "capabilities": caps}, ensure_ascii=False),
        encoding="utf-8",
    )
    return path


# ---------- 正向：http 能注册、能被模型看见 ----------


def test_http_kind_registers_without_adapter_field(tmp_path: Path):
    """http 是「内联声明」，不需要 adapter 字段（与 local_fn 形态不同）。"""
    path = _write(tmp_path, "ok.json", [_cap()])
    result = load_capability_manifest(path)
    assert result.registered_ids == ("oa.demo.read",)
    by_id = {s.capability_id: s for s in list_capabilities()}
    spec = by_id["oa.demo.read"]
    assert spec.kind == "http"
    assert spec.side_effect == "read"
    assert spec.http is not None
    assert spec.http["base_url"] == "OA_BASE"


def test_http_capability_is_exposed_to_llm_with_when_to_use(tmp_path: Path):
    """schemas_for_llm 必须带上 description（含 when_to_use 语义），否则模型选不中。"""
    path = _write(tmp_path, "ok.json", [_cap(when_to_use="用户想找制度文件时使用")])
    load_capability_manifest(path)
    tools = schemas_for_llm()
    entry = next(t for t in tools if t["function"]["name"] == "oa.demo.read")
    assert entry["function"]["description"] == "demo 只读能力"
    assert entry["function"]["parameters"]["properties"]["keyword"]


def test_real_oa_readonly_manifest_loads():
    """仓内 OA 只读清单本身必须能过校验（否则等于配了一份死的清单）。"""
    path = MANIFEST_DIR / "oa.readonly.v1.yaml"
    assert path.is_file()
    result = load_capability_manifest(path)
    assert set(result.registered_ids) == {
        "oa.doc.search",
        "oa.org.whois",
        "oa.todo.mine",
    }
    by_id = {s.capability_id: s for s in list_capabilities()}
    # 只读清单里不允许出现任何写能力
    assert all(by_id[c].side_effect == "read" for c in result.registered_ids)
    assert all(not by_id[c].hitl_required for c in result.registered_ids)


# ---------- V1–V8 ----------


def test_v1_write_requires_idempotency_key(tmp_path: Path):
    path = _write(
        tmp_path,
        "v1.json",
        [_cap(side_effect="write", hitl={"required": True})],
    )
    with pytest.raises(ManifestError, match="V1"):
        load_capability_manifest(path)
    assert "oa.demo.read" not in {s.capability_id for s in list_capabilities()}


def test_v2_write_requires_hitl(tmp_path: Path):
    path = _write(
        tmp_path,
        "v2.json",
        [_cap(side_effect="write", http_idempotency_key="{{keyword}}")],
    )
    with pytest.raises(ManifestError, match="V2"):
        load_capability_manifest(path)


def test_v3_high_risk_requires_hitl(tmp_path: Path):
    path = _write(tmp_path, "v3.json", [_cap(risk_level="high")])
    with pytest.raises(ManifestError, match="V3"):
        load_capability_manifest(path)


def test_v4_tenant_scoped_http_requires_tenant_param(tmp_path: Path):
    """否则租户谓词只在 Policy 里被检查、没真的传给下游。"""
    path = _write(tmp_path, "v4.json", [_cap(tenant_scoped=True)])
    with pytest.raises(ManifestError, match="V4"):
        load_capability_manifest(path)


def test_v4_tenant_param_shape_is_validated(tmp_path: Path):
    bad_in = _write(
        tmp_path,
        "v4a.json",
        [_cap(tenant_scoped=True, http_tenant_param={"in": "cookie", "name": "x"})],
    )
    with pytest.raises(ManifestError, match="tenant_param.in 非法"):
        load_capability_manifest(bad_in)

    bad_name = _write(
        tmp_path,
        "v4b.json",
        [_cap(tenant_scoped=True, http_tenant_param={"in": "header", "name": ""})],
    )
    with pytest.raises(ManifestError, match="tenant_param.name"):
        load_capability_manifest(bad_name)


def test_v4_does_not_apply_to_local_fn(tmp_path: Path):
    """回归：local_fn 直接拿 ctx，不存在「下推」——不该被 V4 误伤。"""
    path = _write(
        tmp_path,
        "v4c.json",
        [
            {
                "id": "local_tenant_cap",
                "kind": "local_fn",
                "description": "x",
                "when_to_use": "单测",
                "tags": [],
                "risk_level": "low",
                "side_effect": "read",
                "enabled": True,
                "tenant_scoped": True,
                "args_schema": {"type": "object", "properties": {}},
                "adapter": "local_fn:app.ops.capability.lookups:get_issue_by_number",
            }
        ],
    )
    result = load_capability_manifest(path)
    assert result.registered_ids == ("local_tenant_cap",)


def test_v5_undeclared_template_variable_fails(tmp_path: Path):
    """模板变量写错是配置错误，加载期就该拦——不要留到运行期变成空串。"""
    path = _write(
        tmp_path,
        "v5.json",
        [_cap(http_query_map={"q": "{{keyword}}", "limit": "{{top_k}}"})],
    )
    with pytest.raises(ManifestError, match="模板变量未声明"):
        load_capability_manifest(path)


def test_v5_host_injected_variables_are_allowed(tmp_path: Path):
    path = _write(
        tmp_path,
        "v5b.json",
        [_cap(http_query_map={"q": "{{keyword}}", "on": "{{_date}}"})],
    )
    assert load_capability_manifest(path).registered_ids == ("oa.demo.read",)


def test_v6_error_map_must_use_stable_codes(tmp_path: Path):
    """不允许随手发明第八个错误码。"""
    path = _write(
        tmp_path,
        "v6.json",
        [_cap(http_error_map={"1001": "oa_custom_error"})],
    )
    with pytest.raises(ManifestError, match="稳定错误码"):
        load_capability_manifest(path)


def test_v6_all_seven_codes_are_accepted(tmp_path: Path):
    path = _write(
        tmp_path,
        "v6b.json",
        [_cap(http_error_map={str(i): code for i, code in enumerate(sorted(STABLE_ERROR_CODES))})],
    )
    assert load_capability_manifest(path).registered_ids == ("oa.demo.read",)


def test_v7_http_block_only_allowed_for_http_kind(tmp_path: Path):
    path = _write(
        tmp_path,
        "v7.json",
        [
            {
                "id": "local_with_http",
                "kind": "local_fn",
                "description": "x",
                "when_to_use": "单测",
                "args_schema": {"type": "object", "properties": {}},
                "side_effect": "read",
                "http": copy.deepcopy(_HTTP_BASE),
                "adapter": "local_fn:app.ops.capability.defaults:utc_now_iso",
            }
        ],
    )
    with pytest.raises(ManifestError, match="V7"):
        load_capability_manifest(path)


def test_v7_http_kind_without_http_block_fails(tmp_path: Path):
    cap = _cap()
    del cap["http"]
    with pytest.raises(ManifestError, match="必须有 http 块"):
        load_capability_manifest(_write(tmp_path, "v7b.json", [cap]))


def test_v8_read_must_not_declare_idempotency_key(tmp_path: Path):
    """只读不需要幂等键——写了通常是抄错，早报早改。"""
    path = _write(
        tmp_path,
        "v8.json",
        [_cap(http_idempotency_key="{{keyword}}")],
    )
    with pytest.raises(ManifestError, match="V8"):
        load_capability_manifest(path)


# ---------- 必填字段 ----------


def test_args_schema_is_required(tmp_path: Path):
    """无 args_schema 的能力进不了 FC 目录（schemas_for_llm 会跳过），注册它几乎总是笔误。"""
    cap = _cap()
    del cap["args_schema"]
    with pytest.raises(ManifestError, match="缺 args_schema"):
        load_capability_manifest(_write(tmp_path, "req1.json", [cap]))


def test_when_to_use_is_required(tmp_path: Path):
    cap = _cap()
    del cap["when_to_use"]
    with pytest.raises(ManifestError, match="缺 when_to_use"):
        load_capability_manifest(_write(tmp_path, "req2.json", [cap]))


def test_capability_id_naming_is_enforced(tmp_path: Path):
    with pytest.raises(ManifestError, match="非法 id"):
        load_capability_manifest(_write(tmp_path, "id1.json", [_cap(id="OA.Demo")]))


def test_side_effect_and_risk_level_vocabulary(tmp_path: Path):
    with pytest.raises(ManifestError, match="side_effect 非法"):
        load_capability_manifest(_write(tmp_path, "voc1.json", [_cap(side_effect="update")]))
    with pytest.raises(ManifestError, match="risk_level 非法"):
        load_capability_manifest(_write(tmp_path, "voc2.json", [_cap(risk_level="critical")]))


# ---------- 密钥纪律：收紧而非放宽 ----------


def test_base_url_must_be_env_var_name_not_url(tmp_path: Path):
    """把内网域名/端口写死进仓 = 配置泄漏 + 无法换环境。"""
    path = _write(
        tmp_path,
        "sec1.json",
        [_cap(http_base_url="https://oa.internal.example")],
    )
    with pytest.raises(ManifestError, match="base_url 必须是环境变量名"):
        load_capability_manifest(path)


def test_auth_must_be_credential_name_not_secret_value(tmp_path: Path):
    for bad in ("Bearer sk-abc123", "oa-token", "sk-abcdefghijkl"):
        path = _write(tmp_path, f"sec_{abs(hash(bad))}.json", [_cap(http_auth=bad)])
        with pytest.raises(ManifestError, match="auth"):
            load_capability_manifest(path)


def test_secret_shaped_key_inside_http_block_is_rejected(tmp_path: Path):
    cap = _cap()
    cap["http"]["access_token"] = "should-not-land"
    with pytest.raises(ManifestError, match="禁止密钥形字段"):
        load_capability_manifest(_write(tmp_path, "sec2.json", [cap]))


def test_credential_and_token_shaped_keys_are_rejected(tmp_path: Path):
    """``credential_ref`` / ``auth_token_ref`` 这类键名会被拒——声明凭证请用 ``auth``。

    （既有实现只做精确匹配 + password/secret 子串，会放过 ``credential_ref``；
    H4 补成 token/credential 子串匹配，才真正拦得住「看起来像放密钥的字段」。）
    """
    for bad_key in ("credential_ref", "auth_token_ref", "access_token"):
        cap = _cap()
        cap["http"][bad_key] = "oa_gateway_token"
        with pytest.raises(ManifestError, match="禁止密钥形字段"):
            load_capability_manifest(_write(tmp_path, f"sec_{bad_key}.json", [cap]))


def test_plain_auth_key_is_accepted(tmp_path: Path):
    """``auth`` 不在拒绝列表里，也不含敏感子串——这是声明凭证的正确字段名。"""
    assert load_capability_manifest(_write(tmp_path, "sec_ok.json", [_cap()])).registered_ids == (
        "oa.demo.read",
    )


# ---------- 多文件：失败域隔离 ----------


def test_multi_file_failure_isolation(tmp_path: Path):
    """坏一份不带崩别的——这是拆文件的首要理由。"""
    good = _write(tmp_path, "good.json", [_cap()])
    bad = _write(tmp_path, "bad.json", [_cap(id="oa.demo.bad", risk_level="high")])
    result = load_capability_manifests([good, bad])
    assert not result.ok
    assert len(result.loaded) == 1
    assert result.loaded[0].registered_ids == ("oa.demo.read",)
    assert len(result.failed) == 1
    assert str(bad) in result.failed[0][0]
    assert "oa.demo.read" in {s.capability_id for s in list_capabilities()}


def test_cross_file_duplicate_id_is_reported(tmp_path: Path):
    """避免「先后顺序决定谁生效」的隐性行为。"""
    a = _write(tmp_path, "a.json", [_cap()])
    b = _write(tmp_path, "b.json", [_cap(description="重复 id")])
    result = load_capability_manifests([a, b])
    assert len(result.loaded) == 1
    assert "跨文件重复 id" in result.failed[0][1]


def test_reload_only_unregisters_its_own_file_ids(tmp_path: Path):
    """回归：按文件记 id 集合——否则 reload A 会把 B 的能力悄悄注销掉。"""
    a = _write(tmp_path, "a.json", [_cap()])
    b = _write(tmp_path, "b.json", [_cap(id="oa.demo.other")])
    load_capability_manifests([a, b])
    assert {"oa.demo.read", "oa.demo.other"} <= {
        s.capability_id for s in list_capabilities()
    }

    # a 里删掉 oa.demo.read，换成两条新的
    a.write_text(
        json.dumps(
            {
                "version": 2,
                "capabilities": [
                    _cap(id="oa.demo.new1"),
                    _cap(id="oa.demo.new2"),
                ],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    reload_capability_manifest(a)
    ids = {s.capability_id for s in list_capabilities()}
    assert "oa.demo.read" not in ids  # 本文件删掉的能力必须注销（否则永久残留）
    assert {"oa.demo.new1", "oa.demo.new2"} <= ids
    assert "oa.demo.other" in ids  # 别的文件不受影响
