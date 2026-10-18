"""W2 · 可见集求值（visibility）与副作用回执（receipts）。

两个都是「机制」而非「功能」：
- 可见集：第一层 CapabilityFilter 管「这个场景该不该出现」，第二层管「**这个人**能不能看到」。
- 回执：副作用以收据为真，且**失败也要留**——一次「失败」的写可能已经在下游生效。
"""

from __future__ import annotations

from typing import Any

import pytest

from app.ops.capability import (
    InMemoryReceiptSink,
    Principal,
    capability_catalog_snapshot,
    invoke,
    list_capabilities,
    principal_from_ctx,
    schemas_for_llm,
    set_receipt_sink,
)
from app.ops.capability.defaults import ensure_default_capabilities
from app.ops.capability.gateway import get_registry, register, unregister
from app.ops.capability.receipts import (
    NullReceiptSink,
    get_receipt_sink,
    reset_receipt_sink,
)
from app.ops.capability.types import CapabilitySpec
from app.ops.capability.visibility import (
    REASON_CLASSIFICATION,
    REASON_DEPARTMENT,
    REASON_ROLE,
    check_visible,
    evaluate_visibility,
)

_SCHEMA = {"type": "object", "properties": {"q": {"type": "string"}}}


def _spec(cid: str, **over) -> CapabilitySpec:
    base: dict[str, Any] = {
        "capability_id": cid,
        "kind": "local_fn",
        "description": "单测用",
        "args_schema": dict(_SCHEMA),
        "side_effect": "read",
        "when_to_use": "单测",
    }
    base.update(over)
    return CapabilitySpec(**base)


class _EchoAdapter:
    kind = "local_fn"

    def __init__(self, *, raises: BaseException | None = None) -> None:
        self._raises = raises
        self.calls = 0

    def invoke(self, args: Any, *, ctx: dict[str, Any] | None = None) -> Any:
        self.calls += 1
        if self._raises is not None:
            raise self._raises
        return {"ok": True, "args": args}


@pytest.fixture(autouse=True)
def _clean():
    reset_receipt_sink()
    yield
    get_registry().clear()
    reset_receipt_sink()
    ensure_default_capabilities()


# ---------------- 可见集 ----------------


def test_undeclared_visibility_is_visible_and_counted():
    """未声明 → 不受限但留痕。把「该声明没声明」变成可度量项，而不是静默放行。"""
    specs = [_spec("c1"), _spec("c2", visibility={"departments": ["all"]})]
    kept, summary = evaluate_visibility(specs, Principal())
    assert {s.capability_id for s in kept} == {"c1", "c2"}
    assert summary["visibility_undeclared_count"] == 1
    assert summary["visibility_kept_count"] == 2


def test_department_restriction_is_fail_closed_without_identity():
    """声明了限制而主体信息不足 → 不可见。这是本层的核心方向。"""
    spec = _spec("dept_cap", visibility={"departments": ["finance"]})
    visible, reason = check_visible(spec, Principal())
    assert visible is False
    assert reason == REASON_DEPARTMENT


def test_department_match_grants_visibility():
    spec = _spec("dept_cap", visibility={"departments": ["finance", "hr"]})
    ok, _ = check_visible(
        spec, Principal(user_id="u1", departments=frozenset({"hr"}), roles=frozenset({"employee"}))
    )
    assert ok is True


def test_all_wildcard_means_unrestricted():
    spec = _spec("wild", visibility={"departments": ["all"], "roles": ["all"]})
    assert check_visible(spec, Principal())[0] is True


def test_role_restriction():
    spec = _spec("mgr_only", visibility={"roles": ["manager"]})
    assert check_visible(spec, Principal(roles=frozenset({"employee"})))[1] == REASON_ROLE
    ok, _ = check_visible(spec, Principal(roles=frozenset({"employee", "manager"})))
    assert ok is True


def test_classification_is_ordered_not_equality():
    spec = _spec("conf", visibility={"classification_max": "confidential"})
    assert check_visible(spec, Principal(classification_max="internal"))[1] == (
        REASON_CLASSIFICATION
    )
    assert check_visible(spec, Principal(classification_max="confidential"))[0] is True
    # 高于要求当然也可以
    assert check_visible(spec, Principal(classification_max="secret"))[0] is True


def test_project_dimension():
    spec = _spec("proj", visibility={"projects": ["p1"]})
    assert check_visible(spec, Principal(projects=frozenset()))[0] is False
    assert check_visible(spec, Principal(projects=frozenset({"p1"})))[0] is True


def test_gateway_crops_catalog_by_principal():
    register(_spec("pub_cap", visibility={"departments": ["all"]}), _EchoAdapter())
    register(_spec("fin_cap", visibility={"departments": ["finance"]}), _EchoAdapter())

    anon = {s.capability_id for s in list_capabilities()}
    assert "pub_cap" in anon
    assert "fin_cap" not in anon

    fin = {
        s.capability_id
        for s in list_capabilities(
            principal=Principal(user_id="u", departments=frozenset({"finance"}))
        )
    }
    assert {"pub_cap", "fin_cap"} <= fin
    unregister("pub_cap")
    unregister("fin_cap")


def test_llm_tool_list_is_cropped_consistently():
    """裁剪必须发生在**给模型之前**：清单里没有，模型就选不到。"""
    register(_spec("fin_only", visibility={"roles": ["cfo"]}), _EchoAdapter())
    names = {t["function"]["name"] for t in schemas_for_llm()}
    assert "fin_only" not in names
    names2 = {
        t["function"]["name"]
        for t in schemas_for_llm(principal=Principal(roles=frozenset({"cfo"})))
    }
    assert "fin_only" in names2
    unregister("fin_only")


def test_snapshot_explains_why_hidden():
    register(_spec("hidden_cap", visibility={"departments": ["legal"]}), _EchoAdapter())
    _, summary = capability_catalog_snapshot()
    hit = [h for h in summary["visibility_hidden"] if h["capability_id"] == "hidden_cap"]
    assert hit and hit[0]["reason"] == REASON_DEPARTMENT
    assert summary["visibility_principal_anonymous"] is True
    unregister("hidden_cap")


def test_principal_from_ctx_accepts_host_tenant_key():
    p = principal_from_ctx({"_host_tenant": "t-9", "user_id": "u-1"})
    assert p.tenant_id == "t-9"
    assert p.user_id == "u-1"
    assert Principal().is_anonymous() is True


# ---------------- 副作用回执 ----------------


def test_write_records_receipt_on_success():
    sink = InMemoryReceiptSink()
    set_receipt_sink(sink)
    register(
        _spec("w1", side_effect="write", hitl_required=True),
        _EchoAdapter(),
    )
    result = invoke(
        "w1",
        {"q": "x"},
        ctx={"_host_policy": {"allow_write": True}, "user_id": "u1", "tenant_id": "t1"},
    )
    assert result.ok is True
    assert result.meta["receipt_id"]
    assert len(sink) == 1
    r = sink.all()[0]
    assert r.capability_id == "w1"
    assert r.ok is True
    assert r.user_id == "u1"
    assert r.tenant_id == "t1"
    assert r.write_confirmed is True
    unregister("w1")


def test_failed_write_still_records_receipt():
    """一次「失败」的写可能已经在下游生效（超时 / 半成功）——不留就无从对账。"""
    sink = InMemoryReceiptSink()
    set_receipt_sink(sink)
    register(
        _spec("w2", side_effect="write", hitl_required=True),
        _EchoAdapter(raises=TimeoutError("boom")),
    )
    result = invoke("w2", {"q": "x"}, ctx={"_host_policy": {"allow_write": True}})
    assert result.ok is False
    assert len(sink) == 1
    assert sink.all()[0].ok is False
    unregister("w2")


def test_policy_blocked_write_records_nothing():
    """没执行就没有副作用，不该留回执——否则回执表会被"未发生的写"污染。"""
    sink = InMemoryReceiptSink()
    set_receipt_sink(sink)
    register(_spec("w3", side_effect="write", hitl_required=True), _EchoAdapter())
    result = invoke("w3", {"q": "x"})
    assert result.ok is False
    assert result.error.startswith("policy_blocked")
    assert len(sink) == 0
    unregister("w3")


def test_read_without_capture_records_nothing():
    sink = InMemoryReceiptSink()
    set_receipt_sink(sink)
    register(_spec("r1"), _EchoAdapter())
    invoke("r1", {"q": "x"})
    assert len(sink) == 0
    unregister("r1")


def test_read_with_capture_records_receipt():
    sink = InMemoryReceiptSink()
    set_receipt_sink(sink)
    register(_spec("r2", receipt_capture=("$.x",)), _EchoAdapter())
    result = invoke("r2", {"q": "x"})
    assert result.ok is True
    assert len(sink) == 1
    unregister("r2")


def test_sink_failure_does_not_break_the_call():
    class _BrokenSink:
        def record(self, receipt) -> None:
            raise RuntimeError("disk full")

    set_receipt_sink(_BrokenSink())
    register(_spec("w4", side_effect="write", hitl_required=True), _EchoAdapter())
    result = invoke("w4", {"q": "x"}, ctx={"_host_policy": {"allow_write": True}})
    assert result.ok is True  # 回执失败不该让业务失败
    unregister("w4")


def test_default_sink_is_null_and_does_not_crash(caplog):
    assert isinstance(get_receipt_sink(), NullReceiptSink)
    register(_spec("w5", side_effect="write", hitl_required=True), _EchoAdapter())
    result = invoke("w5", {"q": "x"}, ctx={"_host_policy": {"allow_write": True}})
    assert result.ok is True
    # NullSink 不静默：写能力没地方落回执是配置问题，要看得见
    assert "回执未落库" in caplog.text
    unregister("w5")


# ---------------- 稳定错误码 ----------------


def test_unknown_id_uses_stable_code_prefix_with_human_detail():
    result = invoke("nope.does.not.exist", {})
    assert result.error.startswith("unknown_id:")
    assert "未知工具" in result.error  # 中文详情保留：模型认码，人读详情


def test_disabled_uses_stable_code_prefix():
    register(_spec("off_cap", enabled=False), _EchoAdapter())
    result = invoke("off_cap", {})
    assert result.error.startswith("disabled:")
    assert result.meta.get("blocked") == "disabled"
    unregister("off_cap")
