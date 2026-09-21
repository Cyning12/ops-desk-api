"""W3 · 按业务域逐批放开新 kind（`allow_tags_any` + 平台基线）。

背景：`http` 这类新 kind 一次性放开，等于把所有对外接入的能力同时交给模型。
改为**按域**放开——域落在 `tags` 上，新增一个域只改 `DOMAIN_ALLOW_TAGS` 一行。

本文件同时守住两条「不放宽」的边界：
- `allow_tags_any` **不放宽** `deny_high_risk` / `deny_write`
- `tags_any`（收窄）与 `allow_tags_any`（放宽）方向相反，不可混用
"""

from __future__ import annotations

from pathlib import Path

import pytest

from app.ops.capability import list_capabilities
from app.ops.capability.baseline import (
    DEFAULT_KINDS,
    DOMAIN_ALLOW_TAGS,
    baseline_filter,
)
from app.ops.capability.defaults import ensure_default_capabilities
from app.ops.capability.gateway import get_registry
from app.ops.capability.manifest import load_capability_manifest
from app.ops.capability.types import CapabilityFilter, CapabilitySpec

_OA_MANIFEST = (
    Path(__file__).resolve().parents[1]
    / "app"
    / "ops"
    / "capability"
    / "manifests"
    / "oa.readonly.v1.yaml"
)

_BUILTIN_IDS = {
    "mock_get_issue_status",
    "mock_get_deploy_info",
    "utc_now_iso",
    "get_issue_by_number",
    "get_pr_by_number",
}
_OA_IDS = {"oa.doc.search", "oa.org.whois", "oa.todo.mine"}

_SCHEMA = {"type": "object", "properties": {}}


def _spec(cid: str, **over) -> CapabilitySpec:
    base = dict(
        capability_id=cid,
        kind="http",
        description="单测",
        args_schema=dict(_SCHEMA),
        tags=("oa",),
        side_effect="read",
        when_to_use="单测",
    )
    base.update(over)
    return CapabilitySpec(**base)


@pytest.fixture(autouse=True)
def _clean():
    yield
    get_registry().clear()
    ensure_default_capabilities()


# ---------------- allow_tags_any 放行 ----------------


def test_domain_tag_exempts_kinds_crop():
    spec = _spec("x.http.read", tags=("oa", "readonly"))
    flt = CapabilityFilter(kinds=frozenset({"local_fn"}), allow_tags_any=frozenset({"oa"}))
    from app.ops.capability.registry import _match_filter

    assert _match_filter(spec, flt) is True


def test_unlisted_tag_does_not_exempt():
    spec = _spec("x.http.read", tags=("crm",))
    flt = CapabilityFilter(kinds=frozenset({"local_fn"}), allow_tags_any=frozenset({"oa"}))
    from app.ops.capability.registry import _match_filter

    assert _match_filter(spec, flt) is False


def test_allow_tags_does_not_waive_deny_high_risk():
    """一个 tag 不能换到全部豁免。"""
    spec = _spec("x.http.danger", tags=("oa",), risk_level="high")
    flt = CapabilityFilter(
        kinds=frozenset({"local_fn"}),
        allow_tags_any=frozenset({"oa"}),
        deny_high_risk=True,
    )
    from app.ops.capability.registry import _match_filter

    assert _match_filter(spec, flt) is False


def test_allow_tags_does_not_waive_deny_write():
    """第一期只读：即使域放行了，写能力也不进模型视野。"""
    spec = _spec("x.http.write", tags=("oa",), side_effect="write")
    flt = CapabilityFilter(
        kinds=frozenset({"local_fn"}),
        allow_tags_any=frozenset({"oa"}),
        deny_write=True,
    )
    from app.ops.capability.registry import _match_filter

    assert _match_filter(spec, flt) is False


def test_tags_any_is_narrowing_not_widening():
    """把域白名单写成 tags_any 会得到空目录——存量 local_fn 没有 oa 标签。"""
    assert get_registry().get("utc_now_iso") is not None
    wrong = list_capabilities(
        filter=CapabilityFilter(
            kinds=frozenset({"local_fn"}), tags_any=frozenset({"oa"})
        )
    )
    assert wrong == []


# ---------------- 基线 ----------------


def test_baseline_keeps_builtin_visible_when_no_extra_manifest():
    """未加载额外清单时，基线行为与改动前一致（零影响）。"""
    ids = {s.capability_id for s in list_capabilities(filter=baseline_filter(node_role="t"))}
    assert _BUILTIN_IDS <= ids
    assert not (ids & _OA_IDS)


def test_baseline_exposes_oa_domain_after_manifest_loaded():
    """① 的目标：加载 OA 清单后，模型可见集里要有 oa.*。"""
    load_capability_manifest(_OA_MANIFEST)
    ids = {s.capability_id for s in list_capabilities(filter=baseline_filter(node_role="t"))}
    assert _OA_IDS <= ids
    assert _BUILTIN_IDS <= ids


def test_builder_and_supervisor_use_the_same_baseline():
    """单一真相：两处各写一份会漂移（一处放开、另一处没放开）。"""
    from app.ops.strategy.builder import BUILDER_CAP_FILTER
    from app.ops.lg_rag.multi.nodes import _SUPERVISOR_CAP_FILTER

    load_capability_manifest(_OA_MANIFEST)
    builder_ids = {
        s.capability_id for s in list_capabilities(filter=BUILDER_CAP_FILTER)
    }
    supervisor_ids = {
        s.capability_id for s in list_capabilities(filter=_SUPERVISOR_CAP_FILTER)
    }
    assert builder_ids == supervisor_ids
    assert _OA_IDS <= builder_ids


def test_baseline_filter_shape_is_stable():
    """基线四项：基础 kind、域放行、剔除高危、剔除写。"""
    flt = baseline_filter(node_role="probe")
    assert flt.kinds == DEFAULT_KINDS
    assert flt.allow_tags_any == DOMAIN_ALLOW_TAGS
    assert flt.deny_high_risk is True
    assert flt.deny_write is True


def test_baseline_crops_high_risk_and_write_end_to_end():
    """端到端：注册一条高危只读 + 一条中危写，基线都不放行。"""
    from app.ops.capability.gateway import register, unregister

    class _A:
        kind = "http"

        def invoke(self, args, *, ctx=None):
            return {}

    register(_spec("oa.danger.read", tags=("oa",), risk_level="high"), _A())
    register(_spec("oa.ticket.create", tags=("oa",), side_effect="write"), _A())
    try:
        ids = {
            s.capability_id
            for s in list_capabilities(filter=baseline_filter(node_role="t"))
        }
        assert "oa.danger.read" not in ids
        assert "oa.ticket.create" not in ids
    finally:
        unregister("oa.danger.read")
        unregister("oa.ticket.create")
