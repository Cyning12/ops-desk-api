"""catalog 顶层 manifest 故障可见性 + hidden visibility_reason（task: catalog-manifest-errors-surface）。

TC1 故障注入 → /catalog 顶层两键可观测且既有键零 diff
TC2 零故障基线 → 与 capability_catalog_snapshot 直出逐键对拍（路由零重算）
TC3 visibility_reason 钉源 → 与 visibility.py 词表 + evaluate_visibility 直出一一对应
TC4 失败域隔离 + 故障记录生命周期（reload 成功清除）+ meta 两键零 diff

红测先行：实现未落时本文件必须红。
"""

from __future__ import annotations

from pathlib import Path

import pytest

from app.main import app as fastapi_app
from app.ops.capability import (
    GenericHttpAdapter,
    capability_catalog_snapshot,
    register,
    unregister,
)
from app.ops.capability import manifest as manifest_mod
from app.ops.capability.baseline import baseline_filter
from app.ops.capability.manifest import (
    get_capability_manifest_metadata,
    get_manifest_load_errors,
    load_capability_manifests,
    reload_capability_manifest,
)
from app.ops.capability.types import CapabilitySpec, Principal
from app.ops.capability.visibility import REASON_DEPARTMENT, VISIBILITY_REASON_TEXTS
from app.ops.deps import require_admin_sync

BASE = "/api/ops/admin/capability"

_GOOD_YAML = """
version: 2
capabilities:
  - id: {cap_id}
    kind: local_fn
    description: tc4 fixture
    when_to_use: 单测 fixture
    tags: [readonly, fixture]
    risk_level: low
    enabled: true
    args_schema: {type: object, properties: {}}
    adapter: local_fn:app.ops.capability.defaults:utc_now_iso
"""

# 非法：capabilities 不是 list（manifest.py 校验「manifest.capabilities 必须是 list」）
_BAD_YAML = "version: 2\ncapabilities: {}\n"


@pytest.fixture
def as_admin():
    """走 Bearer 机读路径（覆盖依赖即可，不必真配 token）。"""
    fastapi_app.dependency_overrides[require_admin_sync] = lambda: None
    yield
    fastapi_app.dependency_overrides.pop(require_admin_sync, None)


@pytest.fixture(autouse=True)
def _manifest_error_isolation():
    """FP-1：故障记录是模块级状态——快照/还原，禁跨用例泄漏。"""
    saved = dict(manifest_mod._MANIFEST_LOAD_ERRORS)
    manifest_mod._MANIFEST_LOAD_ERRORS.clear()
    yield
    manifest_mod._MANIFEST_LOAD_ERRORS.clear()
    manifest_mod._MANIFEST_LOAD_ERRORS.update(saved)


def _catalog_expected_keys() -> set[str]:
    """既有键全集 = 路由直出三键 + snapshot summary 键（零 diff 基线钉死 · FP-4）。"""
    _visible, summary = capability_catalog_snapshot(
        filter=baseline_filter(node_role="admin_preview"), principal=Principal()
    )
    return {"filter", "principal", "visible_ids", *summary.keys()}


# ---------------- TC1 故障注入可观测 ----------------


@pytest.mark.asyncio
async def test_tc1_manifest_failure_observable_in_catalog(client, as_admin, tmp_path: Path):
    baseline = (await client.get(f"{BASE}/catalog")).json()

    bad = tmp_path / "broken.yaml"
    bad.write_text(_BAD_YAML, encoding="utf-8")
    result = load_capability_manifests([bad])
    assert not result.ok and len(result.failed) == 1

    body = (await client.get(f"{BASE}/catalog")).json()
    assert body["manifest_errors"] == 1
    assert len(body["manifest_error_details"]) == 1
    detail = body["manifest_error_details"][0]
    assert detail["path"] == str(bad)
    assert "capabilities" in detail["error"]
    # 契约6：不透出内部装配细节
    assert "adapter" not in detail["error"]
    assert "local_fn:" not in detail["error"]
    # 契约1：既有键逐键零 diff
    for key in _catalog_expected_keys():
        assert body[key] == baseline[key], f"既有键 {key} 漂移"


# ---------------- TC2 零故障基线逐键对拍 ----------------


@pytest.mark.asyncio
async def test_tc2_zero_failure_baseline_key_parity(client, as_admin):
    visible, summary = capability_catalog_snapshot(
        filter=baseline_filter(node_role="admin_preview"), principal=Principal()
    )
    body = (await client.get(f"{BASE}/catalog")).json()

    assert body["manifest_errors"] == 0
    assert body["manifest_error_details"] == []
    # 键面：既有键一钥不少，新增仅两键
    assert set(body) == _catalog_expected_keys() | {
        "manifest_errors",
        "manifest_error_details",
    }
    # 逐键对拍：与 snapshot 直出一致（路由零重算 · 契约4 同纪律）
    assert body["visible_ids"] == sorted(s.capability_id for s in visible)
    for key, value in summary.items():
        assert body[key] == value, f"summary 键 {key} 与直出不一致"


# ---------------- TC3 visibility_reason 钉源 ----------------


@pytest.mark.asyncio
async def test_tc3_visibility_reason_pinned_to_source(client, as_admin):
    spec = CapabilitySpec(
        capability_id="tc3.dept.only",
        kind="http",
        description="tc3 fixture",
        when_to_use="单测 fixture",
        tags=("oa",),
        side_effect="read",
        risk_level="low",
        visibility={"departments": ["finance"]},
        http={},
    )
    register(spec, GenericHttpAdapter(spec))
    try:
        body = (await client.get(f"{BASE}/catalog")).json()
        hidden = {h["capability_id"]: h for h in body["visibility_hidden"]}
        entry = hidden["tc3.dept.only"]
        # 既有子键存续（契约1）
        assert entry["reason"] == REASON_DEPARTMENT
        # 新增子键钉源：== visibility.py 词表，禁路由自写文案
        assert entry["visibility_reason"] == VISIBILITY_REASON_TEXTS[REASON_DEPARTMENT]
        # 与 evaluate_visibility 直出逐条一致（路由零重算）
        _visible, summary = capability_catalog_snapshot(
            filter=baseline_filter(node_role="admin_preview"), principal=Principal()
        )
        assert body["visibility_hidden"] == summary["visibility_hidden"]
        # 词表覆盖全部 reason 码（未知码不静默吞）
        assert set(VISIBILITY_REASON_TEXTS) >= {
            "department_mismatch",
            "role_mismatch",
            "project_mismatch",
            "classification_exceeded",
        }
    finally:
        unregister("tc3.dept.only")


# ---------------- TC4 失败域隔离 + 生命周期 + meta 零 diff ----------------


def test_tc4_failure_isolation_lifecycle_and_meta(tmp_path: Path):
    good = tmp_path / "good.yaml"
    bad = tmp_path / "bad.yaml"
    good.write_text(_GOOD_YAML.replace("{cap_id}", "tc4.good.cap"), encoding="utf-8")
    bad.write_text(_BAD_YAML, encoding="utf-8")

    meta_before = get_capability_manifest_metadata()
    result = load_capability_manifests([good, bad])
    try:
        # 失败域隔离存续：好文件照常注册、坏文件整文件失败
        assert not result.ok
        assert [r.registered_ids for r in result.loaded] == [("tc4.good.cap",)]
        assert [p for p, _e in result.failed] == [str(bad)]
        # 故障记录 = failed 集（path→error），与好文件无关
        records = {e["path"]: e["error"] for e in get_manifest_load_errors()}
        assert str(bad) in records and str(good) not in records

        # 生命周期：修好坏文件 → reload 成功 → 该文件记录清除（契约3）
        bad.write_text(_GOOD_YAML.replace("{cap_id}", "tc4.fixed.cap"), encoding="utf-8")
        reload_capability_manifest(bad)
        assert str(bad) not in {e["path"] for e in get_manifest_load_errors()}
    finally:
        unregister("tc4.good.cap")
        unregister("tc4.fixed.cap")

    # meta 面零 diff（钉死契约2：/version+/count 两键，故障不可见）
    meta_after = get_capability_manifest_metadata()
    assert set(meta_after) == {"version", "capability_manifest_count"}
    assert meta_after["version"] != meta_before["version"]  # 加载确实发生
