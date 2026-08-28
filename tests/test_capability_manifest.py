"""S3 · capability catalog manifest YAML/JSON 加载。"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from app.ops.capability import invoke, list_capabilities
from app.ops.capability.defaults import (
    _DEFAULT_SPECS,
    ensure_default_capabilities,
    utc_now_iso,
)
from app.ops.capability.gateway import get_registry
from app.ops.capability.manifest import (
    BUILTIN_MANIFEST_PATH,
    ManifestError,
    get_capability_manifest_metadata,
    load_capability_manifest,
    reload_capability_manifest,
)

_BUILTIN_IDS = ("mock_get_issue_status", "mock_get_deploy_info", "utc_now_iso")


@pytest.fixture(autouse=True)
def _restore_defaults():
    yield
    get_registry().clear()
    ensure_default_capabilities()


def _write_yaml(path: Path, body: str) -> Path:
    path.write_text(body, encoding="utf-8")
    return path


def test_builtin_yaml_aligns_with_default_specs():
    """S3-a：builtin 三枚与 utc_now_iso 等 _DEFAULT_SPECS 对齐。"""
    assert BUILTIN_MANIFEST_PATH.is_file()
    get_registry().clear()
    result = load_capability_manifest(BUILTIN_MANIFEST_PATH)
    ids = {s.capability_id for s in list_capabilities()}
    for cid in _BUILTIN_IDS:
        assert cid in ids
    hard_ids = {spec.capability_id for spec, _ in _DEFAULT_SPECS}
    assert set(_BUILTIN_IDS) == hard_ids
    by_id = {s.capability_id: s for s in list_capabilities()}
    for spec, _adapter in _DEFAULT_SPECS:
        loaded = by_id[spec.capability_id]
        assert loaded.kind == spec.kind == "local_fn"
        assert loaded.description == spec.description
        assert loaded.tags == spec.tags
        assert loaded.risk_level == spec.risk_level
    now = invoke("utc_now_iso", "")
    assert now.ok is True
    assert now.output["tool"] == utc_now_iso("")["tool"]
    assert result.version == 1
    assert result.capability_manifest_count == 3


def test_load_yaml_and_json_register_declared_ids(tmp_path: Path):
    """S3-a：fixture YAML/JSON load 后 list_capabilities 含声明 id。"""
    yaml_path = _write_yaml(
        tmp_path / "extra.yaml",
        """
version: 2
capabilities:
  - id: extra_utc
    kind: local_fn
    description: extra from yaml
    tags: [readonly, fixture]
    risk_level: low
    enabled: true
    adapter: local_fn:app.ops.capability.defaults:utc_now_iso
""",
    )
    yaml_result = load_capability_manifest(yaml_path)
    ids = {s.capability_id for s in list_capabilities()}
    assert "extra_utc" in ids
    assert yaml_result.version == 2
    assert "extra_utc" in yaml_result.registered_ids

    json_path = tmp_path / "extra.json"
    json_path.write_text(
        json.dumps(
            {
                "version": 3,
                "capabilities": [
                    {
                        "id": "extra_issue",
                        "kind": "local_fn",
                        "description": "extra from json",
                        "tags": ["mock", "fixture"],
                        "risk_level": "low",
                        "enabled": True,
                        "adapter": (
                            "local_fn:app.ops.capability.defaults:mock_get_issue_status"
                        ),
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    json_result = load_capability_manifest(json_path)
    ids = {s.capability_id for s in list_capabilities()}
    assert "extra_issue" in ids
    assert json_result.version == 3
    assert json_result.capability_manifest_count == 1


def test_illegal_adapter_fails_whole_file_no_partial(tmp_path: Path):
    """S3-a：非法 adapter → 整文件失败，不留下半套。"""
    before = {s.capability_id for s in list_capabilities()}
    path = _write_yaml(
        tmp_path / "bad_adapter.yaml",
        """
version: 1
capabilities:
  - id: would_register
    kind: local_fn
    description: valid-looking
    tags: [fixture]
    enabled: true
    adapter: local_fn:app.ops.capability.defaults:utc_now_iso
  - id: evil
    kind: local_fn
    description: illegal module
    enabled: true
    adapter: local_fn:os:system
""",
    )
    with pytest.raises(ManifestError, match="非法 adapter"):
        load_capability_manifest(path)
    after = {s.capability_id for s in list_capabilities()}
    assert after == before
    assert "would_register" not in after
    assert "evil" not in after


def test_unknown_kind_and_missing_id_fail_whole_file(tmp_path: Path):
    """S3-a：未知 kind / 缺 id → 整文件失败。"""
    before = {s.capability_id for s in list_capabilities()}
    kind_path = _write_yaml(
        tmp_path / "mcp.yaml",
        """
version: 1
capabilities:
  - id: sneaky_ok
    kind: local_fn
    description: ok
    enabled: true
    adapter: local_fn:app.ops.capability.defaults:utc_now_iso
  - id: mcp_probe
    kind: mcp
    description: not allowed
    enabled: true
    adapter: local_fn:app.ops.capability.defaults:utc_now_iso
""",
    )
    with pytest.raises(ManifestError, match="未知 kind"):
        load_capability_manifest(kind_path)
    assert {s.capability_id for s in list_capabilities()} == before
    assert "sneaky_ok" not in {s.capability_id for s in list_capabilities()}

    missing_path = _write_yaml(
        tmp_path / "noid.yaml",
        """
version: 1
capabilities:
  - kind: local_fn
    description: no id
    enabled: true
    adapter: local_fn:app.ops.capability.defaults:utc_now_iso
""",
    )
    with pytest.raises(ManifestError, match="缺 id"):
        load_capability_manifest(missing_path)
    assert {s.capability_id for s in list_capabilities()} == before


def test_non_whitelist_module_and_secret_field_fail(tmp_path: Path):
    """S3-a：非白名单 module / 密钥形字段 → 整文件失败。"""
    before = {s.capability_id for s in list_capabilities()}
    module_path = _write_yaml(
        tmp_path / "gateway.yaml",
        """
version: 1
capabilities:
  - id: via_gateway
    kind: local_fn
    description: wrong module
    enabled: true
    adapter: local_fn:app.ops.capability.gateway:register
""",
    )
    with pytest.raises(ManifestError, match="非法 adapter"):
        load_capability_manifest(module_path)
    assert {s.capability_id for s in list_capabilities()} == before

    secret_path = _write_yaml(
        tmp_path / "secret.yaml",
        """
version: 1
capabilities:
  - id: leaky
    kind: local_fn
    description: has secret
    api_key: should-not-land
    enabled: true
    adapter: local_fn:app.ops.capability.defaults:utc_now_iso
""",
    )
    with pytest.raises(ManifestError, match="禁止密钥形字段"):
        load_capability_manifest(secret_path)
    assert {s.capability_id for s in list_capabilities()} == before


def test_enabled_false_skipped(tmp_path: Path):
    """S3-a：enabled: false 跳过；无密钥字段。"""
    path = _write_yaml(
        tmp_path / "mixed.yaml",
        """
version: 1
capabilities:
  - id: skipped_cap
    kind: local_fn
    description: disabled
    tags: [fixture]
    enabled: false
    adapter: local_fn:app.ops.capability.defaults:utc_now_iso
  - id: live_cap
    kind: local_fn
    description: enabled
    tags: [fixture]
    enabled: true
    adapter: local_fn:app.ops.capability.defaults:utc_now_iso
""",
    )
    result = load_capability_manifest(path)
    ids = {s.capability_id for s in list_capabilities()}
    assert "live_cap" in ids
    assert "skipped_cap" not in ids
    assert "skipped_cap" in result.skipped_disabled
    assert result.capability_manifest_count == 1


def test_ensure_idempotent_yaml_first_missing_file_fallback():
    """S3-a：ensure 幂等（YAML 优先，缺文件回退硬编码）。"""
    ensure_default_capabilities()
    ensure_default_capabilities()
    ids = {s.capability_id for s in list_capabilities()}
    for cid in _BUILTIN_IDS:
        assert cid in ids

    get_registry().clear()
    missing = Path("/nonexistent/ops-desk/builtin.v1.yaml")
    with patch(
        "app.ops.capability.manifest.BUILTIN_MANIFEST_PATH",
        missing,
    ):
        ensure_default_capabilities()
    ids = {s.capability_id for s in list_capabilities()}
    for cid in _BUILTIN_IDS:
        assert cid in ids


def test_s3b_metadata_and_explicit_reload(tmp_path: Path):
    """S3-b：load 暴露 version + count；显式 reload 可测。"""
    path = _write_yaml(
        tmp_path / "v.yaml",
        """
version: 9
capabilities:
  - id: reload_cap
    kind: local_fn
    description: first
    tags: [fixture]
    enabled: true
    adapter: local_fn:app.ops.capability.defaults:utc_now_iso
""",
    )
    loaded = load_capability_manifest(path)
    assert loaded.version == 9
    assert loaded.capability_manifest_count == 1
    meta = get_capability_manifest_metadata()
    assert meta["version"] == 9
    assert meta["capability_manifest_count"] == 1

    path.write_text(
        """
version: 10
capabilities:
  - id: reload_cap
    kind: local_fn
    description: second
    tags: [fixture]
    enabled: true
    adapter: local_fn:app.ops.capability.defaults:utc_now_iso
""",
        encoding="utf-8",
    )
    reloaded = reload_capability_manifest(path)
    assert reloaded.version == 10
    by_id = {s.capability_id: s for s in list_capabilities()}
    assert by_id["reload_cap"].description == "second"
    meta = get_capability_manifest_metadata()
    assert meta["version"] == 10
    assert meta["capability_manifest_count"] == 1


def test_no_http_hook_in_capability_package():
    """S3-b：禁止 HTTP / 每请求钩子（包内无 router 挂载 reload）。"""
    cap_root = Path(__file__).resolve().parents[1] / "app" / "ops" / "capability"
    text = ""
    for py in cap_root.rglob("*.py"):
        text += py.read_text(encoding="utf-8")
    assert "APIRouter" not in text
    assert "@router" not in text
    assert "reload_capability_manifest" in (
        cap_root / "manifest.py"
    ).read_text(encoding="utf-8")
