"""admin catalog items 全字段数组契约测试（B2 后续 · task_b2_nit3_admin_items_array）。

钉死契约（SPEC tool-catalog-page §2 B2 :75-78 · 本 task 钉死契约 1-5）：

1. **items 覆盖全部在册**：数据源 = 无 filter 全量注册表（registry.list_specs 口径），
   含 disabled / 被裁条目；baseline/kinds/deny_write 等 query 裁剪只影响既有
   ``visible_ids``/summary，对 items 覆盖集零影响。
2. **键集精确 14 键**：``id``/``kind``/``description``/``when_to_use``/``when_not_to_use``/
   ``tags``/``risk_level``/``side_effect``/``enabled``/``tenant_scoped``/``reversible``/
   ``execution_type``/``status``/``visibility_reason``——多一键少一键都红；
   ``adapter``/``args_schema``/``http``/``idempotency_key``/``hitl_*`` 一律不出站（SPEC FP-5）。
3. **status 三态**：``disabled`` ⇔ ``enabled: false``（优先判定）；``denied:<原因码>`` ⇔
   enabled 但 check_visible 裁掉；``visible`` ⇔ 其余。``visibility_reason`` 恒出键，
   仅 denied 条目非空（R1 nit n-1 裁定选①）· 文本单源 VISIBILITY_REASON_TEXTS。
4. **既有键零 diff**：filter/principal/visible_ids/visibility_*/manifest_errors* 存续。
"""

from __future__ import annotations

import pytest

from app.main import app as fastapi_app
from app.ops.capability import (
    GenericHttpAdapter,
    Principal,
    capability_catalog_snapshot,
    evaluate_visibility,
    get_registry,
    register,
    unregister,
)
from app.ops.capability.baseline import baseline_filter
from app.ops.capability.types import CapabilitySpec
from app.ops.deps import require_admin_sync

BASE = "/api/ops/admin/capability"

# SPEC §2 B2 :75 字段族钉案 + status/visibility_reason —— 键集相等机断（多一少一都红）
EXPECTED_ITEM_KEYS = {
    "id",
    "kind",
    "description",
    "when_to_use",
    "when_not_to_use",
    "tags",
    "risk_level",
    "side_effect",
    "enabled",
    "tenant_scoped",
    "reversible",
    "execution_type",
    "status",
    "visibility_reason",
}

EXISTING_TOP_KEYS = {
    "filter",
    "principal",
    "visible_ids",
    "visibility_catalog_count",
    "visibility_kept_count",
    "visibility_hidden",
    "visibility_undeclared_count",
    "visibility_principal_anonymous",
    "manifest_errors",
    "manifest_error_details",
}


@pytest.fixture
def as_admin():
    """走 Bearer 机读路径（覆盖依赖即可，不必真配 token）。"""
    fastapi_app.dependency_overrides[require_admin_sync] = lambda: None
    yield
    fastapi_app.dependency_overrides.pop(require_admin_sync, None)


def _http_probe(capability_id: str, **overrides) -> CapabilitySpec:
    """构造观测探针 spec：tags=("oa",) 豁免 kinds 裁剪，才能走到可见性判定。"""
    base = {
        "capability_id": capability_id,
        "kind": "http",
        "description": f"{capability_id} 探针",
        "args_schema": {"type": "object", "properties": {}},
        "tags": ("oa",),
        "risk_level": "low",
        "side_effect": "read",
        "when_to_use": "单测 fixture",
        "when_not_to_use": "非单测",
        "visibility": {"departments": ["all"]},
        "http": {},
    }
    base.update(overrides)
    return CapabilitySpec(**base)


# ---------------- TC1 · items 全覆盖 + 字段族 ----------------


async def test_tc1_items_cover_full_registry_with_exact_14_keys(client, as_admin):
    """items 长度 == 全量在册数（含 disabled/被裁条目）· 每条目键集精确 14 键。"""
    registry_specs = get_registry().list_specs()
    body = (await client.get(f"{BASE}/catalog")).json()

    items = body["items"]
    assert len(items) == len(registry_specs), (
        f"items 覆盖集应 == 全量在册：{len(items)} vs {len(registry_specs)}"
    )
    assert {i["id"] for i in items} == {s.capability_id for s in registry_specs}
    for item in items:
        assert set(item.keys()) == EXPECTED_ITEM_KEYS, (
            f"条目 {item.get('id')} 键集漂移: "
            f"多 {sorted(set(item.keys()) - EXPECTED_ITEM_KEYS)} · "
            f"少 {sorted(EXPECTED_ITEM_KEYS - set(item.keys()))}"
        )

    # denied 条目 visibility_reason 与 evaluate_visibility 直出对拍（单源 · SPEC 纪律 #3）
    enabled_specs = [s for s in registry_specs if s.enabled]
    _kept, summary = evaluate_visibility(enabled_specs, Principal())
    hidden = {h["capability_id"]: h for h in summary["visibility_hidden"]}
    by_id = {i["id"]: i for i in items}
    for cid, h in hidden.items():
        assert by_id[cid]["status"] == f"denied:{h['reason']}"
        assert by_id[cid]["visibility_reason"] == h["visibility_reason"]

    # 恒出键裁定（R1 nit n-1 选①）：非 denied 条目 visibility_reason 恒为 None
    for item in items:
        if not item["status"].startswith("denied:"):
            assert item["visibility_reason"] is None


# ---------------- TC2 · 既有键零 diff + items 与 query 裁剪正交 ----------------


async def test_tc2_existing_keys_zero_diff_and_items_orthogonal_to_query(client, as_admin):
    body = (await client.get(f"{BASE}/catalog")).json()

    # 既有键逐一在场（SPEC FP-4 · 只增不删）
    missing = EXISTING_TOP_KEYS - set(body.keys())
    assert not missing, f"既有键缺失: {sorted(missing)}"

    # 与可见性单源直出逐键对拍零 diff（路由层零重算）
    visible, summary = capability_catalog_snapshot(
        filter=baseline_filter(node_role="admin_preview"), principal=Principal()
    )
    assert body["visible_ids"] == sorted(s.capability_id for s in visible)
    for key, value in summary.items():
        assert body[key] == value, f"既有键 {key} 与单源直出漂移"

    # baseline/kinds/deny_write/principal 等 query 组合对 items 覆盖集零影响（恒全量在册）
    default_ids = {i["id"] for i in body["items"]}
    for params in (
        {"baseline": "false"},
        {"departments": "finance,hr"},
        {"baseline": "false", "roles": "maintainer", "tenant_id": "t1"},
    ):
        variant = (await client.get(f"{BASE}/catalog", params=params)).json()
        assert {i["id"] for i in variant["items"]} == default_ids, (
            f"query {params} 改变了 items 覆盖集（应恒为全量在册）"
        )


# ---------------- TC3 · status 三态可分辨 ----------------


async def test_tc3_items_status_tri_state(client, as_admin):
    """fixture 注入 disabled + visibility 受限条目 → items 同现三态。

    manifest 加载层跳过 disabled 条目（manifest.py:252-254 skipped_disabled），
    在册 disabled 只能经 register() 直注——与兄弟观测测试同款显式恢复纪律。
    """
    probes = [
        _http_probe("items.probe.disabled", enabled=False),
        _http_probe("items.probe.denied", visibility={"departments": ["finance"]}),
        _http_probe("items.probe.visible"),
    ]
    for spec in probes:
        register(spec, GenericHttpAdapter(spec))
    try:
        body = (await client.get(f"{BASE}/catalog")).json()
        by_id = {i["id"]: i for i in body["items"]}

        disabled = by_id["items.probe.disabled"]
        assert disabled["status"] == "disabled"
        assert disabled["enabled"] is False
        assert disabled["visibility_reason"] is None

        denied = by_id["items.probe.denied"]
        assert denied["status"] == "denied:department_mismatch"
        assert denied["visibility_reason"] == "部门不在该能力的可见范围内"

        visible = by_id["items.probe.visible"]
        assert visible["status"] == "visible"
        assert visible["visibility_reason"] is None

        # disabled 不在 visible_ids（registry.py:120 语义）；denied 对匿名主体亦被裁
        assert "items.probe.disabled" not in body["visible_ids"]
        assert "items.probe.denied" not in body["visible_ids"]
        assert "items.probe.visible" in body["visible_ids"]
    finally:
        for spec in probes:
            unregister(spec.capability_id)


# ---------------- TC4 · 防泄露 ----------------


async def test_tc4_items_no_internal_assembly_leak(client, as_admin):
    """响应体不含 adapter/local_fn:/args_schema 子串（SPEC FP-5 · 纪律 #4）。"""
    spec = _http_probe(
        "items.probe.leak",
        args_schema={
            "type": "object",
            "properties": {"secret_param": {"type": "string"}},
        },
        http={"base_url": "PROBE_BASE_URL", "path": "/probe"},
    )
    register(spec, GenericHttpAdapter(spec))
    try:
        resp = await client.get(f"{BASE}/catalog")
        assert resp.status_code == 200
        text = resp.text
        for needle in ("adapter", "local_fn:", "args_schema", "secret_param", "PROBE_BASE_URL"):
            assert needle not in text, f"响应体泄露内部装配子串: {needle}"
    finally:
        unregister("items.probe.leak")
