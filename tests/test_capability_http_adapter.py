"""H4 · ``GenericHttpAdapter`` 运行期行为（零 socket）。

覆盖的都是**踩过就会出事**的点：
- 写操作绝不自动重试（超时可能已成功，重试产生第二张单据）
- 租户谓词真的下推（否则 tenant_scoped 只是 Policy 里的一句空话）
- 下游业务码归一化（老 OA 的 200 内业务失败码不泄漏给模型）
- 凭证不进错误消息、不进日志
"""

from __future__ import annotations

import pytest

from app.ops.capability import invoke
from app.ops.capability.adapters import (
    FakeHttpTransport,
    GenericHttpAdapter,
    HttpCapabilityError,
    StaticCredentialVault,
    jsonpath_get,
)
from app.ops.capability.defaults import ensure_default_capabilities
from app.ops.capability.gateway import get_registry, register, unregister
from app.ops.capability.types import CapabilitySpec

_SECRET = "super-secret-value-xyz"

_HTTP = {
    "method": "GET",
    "base_url": "OA_BASE",
    "path": "/api/v1/demo",
    "auth": "oa_gateway_token",
    "query_map": {"q": "{{keyword}}"},
    "timeout_ms": 8000,
    "success_when": {"path": "$.code", "in": [0, 200]},
    "error_map": {"1001": "args_schema_invalid", "2003": "permission_denied"},
}

_ARGS_SCHEMA = {
    "type": "object",
    "properties": {
        "keyword": {"type": "string"},
        "top_k": {"type": "integer", "default": 10},
    },
}


@pytest.fixture(autouse=True)
def _base_env(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("OA_BASE", "https://oa.test.local")
    yield
    get_registry().clear()
    ensure_default_capabilities()


def _spec(**over) -> CapabilitySpec:
    http = dict(_HTTP)
    http.update(over.pop("http", {}))
    base = dict(
        capability_id="oa.demo.read",
        kind="http",
        description="demo 只读能力",
        args_schema=dict(_ARGS_SCHEMA),
        tags=("oa",),
        risk_level="low",
        side_effect="read",
        when_to_use="单测使用",
        http=http,
    )
    base.update(over)
    return CapabilitySpec(**base)


def _adapter(spec: CapabilitySpec, transport: FakeHttpTransport) -> GenericHttpAdapter:
    return GenericHttpAdapter(
        spec,
        transport=transport,
        vault=StaticCredentialVault({"oa_gateway_token": _SECRET}),
    )


# ---------- 正向 ----------


def test_renders_query_headers_and_auth():
    tx = FakeHttpTransport(payload={"code": 0, "data": {"hit": 3}})
    out = _adapter(_spec(), tx).invoke({"keyword": "报销标准"})
    call = tx.calls[0]
    assert call["method"] == "GET"
    assert call["params"] == {"q": "报销标准"}
    assert call["headers"]["Authorization"] == f"Bearer {_SECRET}"
    assert out["protocol"] == "http"
    assert out["result"]["data"]["hit"] == 3


def test_schema_defaults_are_applied_not_rendered_empty():
    """缺省参数若不补默认值，会变成 ``limit=`` 这种把语义交给下游猜的请求。"""
    tx = FakeHttpTransport()
    spec = _spec(http={"query_map": {"q": "{{keyword}}", "limit": "{{top_k}}"}})
    _adapter(spec, tx).invoke({"keyword": "x"})
    assert tx.calls[0]["params"]["limit"] == 10


def test_host_injected_variables_come_from_ctx_not_model():
    tx = FakeHttpTransport()
    spec = _spec(http={"query_map": {"q": "{{keyword}}", "d": "{{_date}}"}})
    _adapter(spec, tx).invoke({"keyword": "x", "_date": "1999-01-01"})
    assert tx.calls[0]["params"]["d"] != "1999-01-01"


def test_receipt_capture():
    tx = FakeHttpTransport(payload={"code": 0, "data": {"ticketId": "T-1", "url": "u"}})
    spec = _spec(receipt_capture=("$.data.ticketId", "$.data.missing"))
    out = _adapter(spec, tx).invoke({"keyword": "x"})
    assert out["receipt"] == {"$.data.ticketId": "T-1"}


# ---------- 租户谓词下推（V4 的兑现） ----------


def test_tenant_predicate_is_actually_pushed_downstream():
    """这一条是 V4 存在的全部理由：检查了就要真的用上。"""
    tx = FakeHttpTransport()
    spec = _spec(
        tenant_scoped=True,
        http={"tenant_param": {"in": "header", "name": "X-Ops-Tenant"}},
    )
    _adapter(spec, tx).invoke({"keyword": "x"}, ctx={"tenant_id": "dept-42"})
    assert tx.calls[0]["headers"]["X-Ops-Tenant"] == "dept-42"


def test_tenant_predicate_can_go_to_query_or_body():
    tx = FakeHttpTransport()
    spec = _spec(
        tenant_scoped=True,
        http={"tenant_param": {"in": "query", "name": "tenant"}},
    )
    _adapter(spec, tx).invoke({"keyword": "x"}, ctx={"_host_tenant": "t-1"})
    assert tx.calls[0]["params"]["tenant"] == "t-1"


def test_tenant_scoped_without_predicate_fails_closed():
    tx = FakeHttpTransport()
    spec = _spec(tenant_scoped=True, http={"tenant_param": {"in": "header", "name": "T"}})
    with pytest.raises(HttpCapabilityError) as ei:
        _adapter(spec, tx).invoke({"keyword": "x"}, ctx={})
    assert ei.value.code == "permission_denied"
    assert tx.calls == []  # 没谓词就不发请求


# ---------- 错误归一化 ----------


def test_upstream_business_code_is_mapped_to_stable_code():
    tx = FakeHttpTransport(payload={"code": 1001, "msg": "参数错误"})
    with pytest.raises(HttpCapabilityError) as ei:
        _adapter(_spec(), tx).invoke({"keyword": "x"})
    assert ei.value.code == "args_schema_invalid"
    assert repr(ei.value).startswith("args_schema_invalid")


def test_unmapped_upstream_code_becomes_upstream_error_without_leaking_text():
    tx = FakeHttpTransport(payload={"code": 9999, "msg": "内部堆栈: at com.oa.Foo"})
    with pytest.raises(HttpCapabilityError) as ei:
        _adapter(_spec(), tx).invoke({"keyword": "x"})
    assert ei.value.code == "upstream_error"
    assert "com.oa.Foo" not in repr(ei.value)  # 下游错误串不外泄给模型


def test_missing_business_code_field_is_not_success():
    tx = FakeHttpTransport(payload={"data": {}})
    with pytest.raises(HttpCapabilityError) as ei:
        _adapter(_spec(), tx).invoke({"keyword": "x"})
    assert ei.value.code == "upstream_error"


def test_missing_base_url_env_var_is_upstream_error(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv("OA_BASE", raising=False)
    tx = FakeHttpTransport()
    with pytest.raises(HttpCapabilityError) as ei:
        _adapter(_spec(), tx).invoke({"keyword": "x"})
    assert ei.value.code == "upstream_error"
    assert tx.calls == []


# ---------- 重试纪律 ----------


def test_write_is_never_retried():
    """超时不代表失败——可能已经成功。重试会产生第二张单据。"""
    tx = FakeHttpTransport(exc=TimeoutError("timeout"))
    spec = _spec(
        side_effect="write",
        hitl_required=True,
        http={
            "method": "POST",
            "body_map": {"kw": "{{keyword}}"},
            "idempotency_key": "demo:{{keyword}}",
        },
    )
    with pytest.raises(HttpCapabilityError):
        _adapter(spec, tx).invoke({"keyword": "x"})
    assert len(tx.calls) == 1


def test_read_may_retry_once():
    tx = FakeHttpTransport(exc=TimeoutError("timeout"))
    with pytest.raises(HttpCapabilityError):
        _adapter(_spec(), tx).invoke({"keyword": "x"})
    assert len(tx.calls) == 2


# ---------- 幂等键 ----------


def test_write_sends_idempotency_key_header():
    tx = FakeHttpTransport(payload={"code": 0})
    spec = _spec(
        side_effect="write",
        hitl_required=True,
        http={
            "method": "POST",
            "body_map": {"kw": "{{keyword}}"},
            "idempotency_key": "oa.demo:{{keyword}}:{{_date}}",
        },
    )
    out = _adapter(spec, tx).invoke({"keyword": "x"}, ctx={"user_id": "u1"})
    header = tx.calls[0]["headers"]["Idempotency-Key"]
    assert header.startswith("oa.demo:x:")
    assert out["idempotency_key"] == header


def test_write_without_idempotency_key_fails_closed():
    tx = FakeHttpTransport(payload={"code": 0})
    spec = _spec(
        side_effect="write",
        hitl_required=True,
        http={"method": "POST", "body_map": {"kw": "{{keyword}}"}},
    )
    with pytest.raises(HttpCapabilityError) as ei:
        _adapter(spec, tx).invoke({"keyword": "x"})
    assert ei.value.code == "args_schema_invalid"
    assert tx.calls == []


# ---------- 凭证不泄漏 ----------


def test_credential_never_appears_in_errors():
    """凭证由 vault 按名取；报错只报名字。"""
    adapter = GenericHttpAdapter(
        _spec(), transport=FakeHttpTransport(), vault=StaticCredentialVault({})
    )
    with pytest.raises(HttpCapabilityError) as ei:
        adapter.invoke({"keyword": "x"})
    assert ei.value.code == "permission_denied"
    assert "oa_gateway_token" in repr(ei.value)
    assert _SECRET not in repr(ei.value)


def test_undeclared_template_var_rejected_at_runtime():
    """加载期 V5 已拦；此处是运行期兜底（手工 register 绕过 manifest 时）。"""
    tx = FakeHttpTransport()
    spec = _spec(http={"query_map": {"q": "{{keyword}}", "x": "{{not_declared}}"}})
    with pytest.raises(HttpCapabilityError) as ei:
        _adapter(spec, tx).invoke({"keyword": "x"})
    assert ei.value.code == "args_schema_invalid"
    assert tx.calls == []


# ---------- 经 gateway 的端到端语义 ----------


def test_gateway_returns_ok_false_without_blowing_up_caller():
    register(_spec(), _adapter(_spec(), FakeHttpTransport(payload={"code": 1001})))
    result = invoke("oa.demo.read", {"keyword": "x"})
    assert result.ok is False
    assert result.error is not None and "args_schema_invalid" in result.error
    unregister("oa.demo.read")


def test_gateway_blocks_write_without_host_policy():
    spec = _spec(
        side_effect="write",
        hitl_required=True,
        http={
            "method": "POST",
            "body_map": {"kw": "{{keyword}}"},
            "idempotency_key": "k:{{keyword}}",
        },
    )
    register(spec, _adapter(spec, FakeHttpTransport(payload={"code": 0})))

    blocked = invoke("oa.demo.read", {"keyword": "x"})
    assert blocked.ok is False
    assert blocked.error.startswith("policy_blocked")

    # plan 顶层直写 allow_write 不生效（Host-only 键）
    sneaky = invoke("oa.demo.read", {"keyword": "x"}, ctx={"allow_write": True})
    assert sneaky.ok is False
    assert sneaky.error.startswith("policy_blocked")

    # 只有 Host 放进 _host_policy 才放行
    allowed = invoke(
        "oa.demo.read",
        {"keyword": "x"},
        ctx={"_host_policy": {"allow_write": True}},
    )
    assert allowed.ok is True
    unregister("oa.demo.read")


def test_gateway_verify_tenant_predicate_is_required_by_policy():
    """Policy 侧缺 tenant 谓词即拒（与 adapter 侧下推是两道不同的检查）。"""
    spec = _spec(tenant_scoped=True, http={"tenant_param": {"in": "header", "name": "T"}})
    register(spec, _adapter(spec, FakeHttpTransport()))
    assert invoke("oa.demo.read", {"keyword": "x"}).error.startswith("policy_blocked")
    assert invoke("oa.demo.read", {"keyword": "x"}, ctx={"tenant_id": "t1"}).ok is True
    unregister("oa.demo.read")


# ---------- JSONPath 子集 ----------


@pytest.mark.parametrize(
    ("doc", "expr", "expected"),
    [
        ({"a": {"b": 1}}, "$.a.b", 1),
        ({"a": [{"b": 2}]}, "$.a[0].b", 2),
        ({"code": 0}, "$.code", 0),
        ({"a": 1}, "$", {"a": 1}),
        ({"a": 1}, "$.missing", None),
    ],
)
def test_jsonpath_subset(doc, expr, expected):
    got = jsonpath_get(doc, expr)
    if expected is None:
        assert got is not None or expr == "$.missing"
    else:
        assert got == expected


def test_jsonpath_missing_marker_is_distinct_from_none():
    from app.ops.capability.adapters.http_generic import _MISSING

    assert jsonpath_get({"a": None}, "$.a") is None
    assert jsonpath_get({"a": 1}, "$.b") is _MISSING
