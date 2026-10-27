"""S3 · capability catalog manifest YAML/JSON 加载。

H4 更新：契约收紧——``args_schema`` 与 ``when_to_use`` 变为**必填**。
理由：无 ``args_schema`` 的能力进不了 FC 目录（``schemas_for_llm`` 会跳过），
注册它几乎总是笔误；无 ``when_to_use`` 则模型只能靠 id 猜。fixture 随之补齐，
**断言本身未改**。
"""

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

_BUILTIN_IDS = (
    "mock_get_issue_status",
    "mock_get_deploy_info",
    "utc_now_iso",
    "get_issue_by_number",
    "get_pr_by_number",
)

# H4 必填字段的最小声明（fixture 复用；契约本身见 manifest._entry_from_raw）
_MIN_DECL = """    when_to_use: 单测 fixture
    args_schema: {type: object, properties: {}}
"""


@pytest.fixture(autouse=True)
def _restore_defaults():
    yield
    get_registry().clear()
    ensure_default_capabilities()


def _write_yaml(path: Path, body: str) -> Path:
    path.write_text(body, encoding="utf-8")
    return path


def test_builtin_yaml_aligns_with_default_specs():
    """S3-a：builtin 五枚与 utc_now_iso / lookup 等 _DEFAULT_SPECS 对齐。"""
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
        assert loaded.tenant_scoped == spec.tenant_scoped
        assert loaded.args_schema == spec.args_schema
        # H4：YAML 与硬编码回退必须对 side_effect 一致（否则回退路径语义漂移）
        assert loaded.side_effect == spec.side_effect
        # output_fields 字段族对齐（task lg-rag-capability-output-schema）：
        # 主加载面（YAML）与硬编码回退面必须逐字段一致，否则回退路径契约漂移
        assert loaded.output_fields == spec.output_fields
    now = invoke("utc_now_iso", "")
    assert now.ok is True
    assert now.output["tool"] == utc_now_iso("")["tool"]
    assert result.version == 1
    assert result.capability_manifest_count == 5


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
    when_to_use: 单测 fixture
    tags: [readonly, fixture]
    risk_level: low
    enabled: true
    args_schema: {type: object, properties: {}}
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
                        "when_to_use": "单测 fixture",
                        "tags": ["mock", "fixture"],
                        "risk_level": "low",
                        "enabled": True,
                        "args_schema": {"type": "object", "properties": {}},
                        "adapter": ("local_fn:app.ops.capability.defaults:mock_get_issue_status"),
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
    when_to_use: 单测 fixture
    tags: [fixture]
    enabled: true
    args_schema: {type: object, properties: {}}
    adapter: local_fn:app.ops.capability.defaults:utc_now_iso
  - id: evil
    kind: local_fn
    description: illegal module
    when_to_use: 单测 fixture
    enabled: true
    args_schema: {type: object, properties: {}}
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
    when_to_use: 单测 fixture
    enabled: true
    args_schema: {type: object, properties: {}}
    adapter: local_fn:app.ops.capability.defaults:utc_now_iso
  - id: mcp_probe
    kind: mcp
    description: not allowed
    when_to_use: 单测 fixture
    enabled: true
    args_schema: {type: object, properties: {}}
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
    when_to_use: 单测 fixture
    enabled: true
    args_schema: {type: object, properties: {}}
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
    when_to_use: 单测 fixture
    tags: [fixture]
    enabled: false
    args_schema: {type: object, properties: {}}
    adapter: local_fn:app.ops.capability.defaults:utc_now_iso
  - id: live_cap
    kind: local_fn
    description: enabled
    when_to_use: 单测 fixture
    tags: [fixture]
    enabled: true
    args_schema: {type: object, properties: {}}
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
    when_to_use: 单测 fixture
    tags: [fixture]
    enabled: true
    args_schema: {type: object, properties: {}}
    adapter: local_fn:app.ops.capability.defaults:utc_now_iso
""",
    )
    loaded = load_capability_manifest(path)
    assert loaded.version == 9
    assert loaded.capability_manifest_count == 1
    meta = get_capability_manifest_metadata()
    # NIT-3 键集相等补强（task_b2_nit3_admin_items_array 钉死契约 6）：
    # 键集断言在前，防 meta 面被顺手扩/删键而逐键值断言抓不住
    assert set(meta.keys()) == {"version", "capability_manifest_count"}
    assert meta["version"] == 9
    assert meta["capability_manifest_count"] == 1

    path.write_text(
        """
version: 10
capabilities:
  - id: reload_cap
    kind: local_fn
    description: second
    when_to_use: 单测 fixture
    tags: [fixture]
    enabled: true
    args_schema: {type: object, properties: {}}
    adapter: local_fn:app.ops.capability.defaults:utc_now_iso
""",
        encoding="utf-8",
    )
    reloaded = reload_capability_manifest(path)
    assert reloaded.version == 10
    by_id = {s.capability_id: s for s in list_capabilities()}
    assert by_id["reload_cap"].description == "second"
    meta = get_capability_manifest_metadata()
    # NIT-3 键集相等补强（同上）：键集在前 + 原逐键值存续
    assert set(meta.keys()) == {"version", "capability_manifest_count"}
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
    assert "reload_capability_manifest" in (cap_root / "manifest.py").read_text(encoding="utf-8")


def test_lookups_adapter_prefix_allowed(tmp_path: Path):
    """lookups 前缀可注册；其它模块前缀仍整文件失败。"""
    ok_path = _write_yaml(
        tmp_path / "lookups.yaml",
        """
version: 1
capabilities:
  - id: extra_issue_lookup
    kind: local_fn
    description: lookups prefix
    when_to_use: 单测 fixture
    tags: [lookup, fixture]
    risk_level: low
    enabled: true
    args_schema: {type: object, properties: {}}
    adapter: local_fn:app.ops.capability.lookups:get_issue_by_number
""",
    )
    result = load_capability_manifest(ok_path)
    ids = {s.capability_id for s in list_capabilities()}
    assert "extra_issue_lookup" in ids
    assert "extra_issue_lookup" in result.registered_ids

    before = {s.capability_id for s in list_capabilities()}
    bad_path = _write_yaml(
        tmp_path / "session.yaml",
        """
version: 1
capabilities:
  - id: would_register
    kind: local_fn
    description: valid-looking
    when_to_use: 单测 fixture
    enabled: true
    args_schema: {type: object, properties: {}}
    adapter: local_fn:app.ops.capability.lookups:get_issue_by_number
  - id: evil_session
    kind: local_fn
    description: illegal module
    when_to_use: 单测 fixture
    enabled: true
    args_schema: {type: object, properties: {}}
    adapter: local_fn:app.db.session:AsyncSessionLocal
""",
    )
    with pytest.raises(ManifestError, match="非法 adapter"):
        load_capability_manifest(bad_path)
    assert {s.capability_id for s in list_capabilities()} == before
    assert "evil_session" not in before
    assert "would_register" not in {s.capability_id for s in list_capabilities()}


def test_min_decl_snippet_is_valid_yaml():
    """fixture 里那段公共声明本身可解析（防止 helper 与真契约漂移）。"""
    import textwrap

    import yaml

    body = "id: probe\nkind: local_fn\n" + textwrap.dedent(_MIN_DECL)
    data = yaml.safe_load(body)
    assert data["when_to_use"]
    assert data["args_schema"] == {"type": "object", "properties": {}}


# ---------------- V10：结果契约形状（拼错 = 没有契约）----------------


def _write_output_schema_manifest(tmp_path: Path, output_schema_block: str) -> Path:
    body = f"""version: 1
capabilities:
  - id: probe_contract
    kind: local_fn
    description: 契约形状单测
    when_to_use: 单测 fixture
    args_schema: {{type: object, properties: {{}}}}
    adapter: local_fn:app.ops.capability.lookups:get_issue_by_number
    output_schema:
{output_schema_block}
"""
    return _write_yaml(tmp_path / "contract.yaml", body)


# ---------------- V10：结果契约形状（拼错 = 没有契约）----------------


def _write_output_schema_manifest(tmp_path: Path, output_schema_block: str) -> Path:
    body = f"""version: 1
capabilities:
  - id: probe_contract
    kind: local_fn
    description: 契约形状单测
    when_to_use: 单测 fixture
    args_schema: {{type: object, properties: {{}}}}
    adapter: local_fn:app.ops.capability.lookups:get_issue_by_number
    output_schema:
{output_schema_block}
"""
    return _write_yaml(tmp_path / "contract.yaml", body)


@pytest.mark.parametrize(
    "block, why",
    [
        ("      required: []", "required 为空列表 —— 等于声明了一个空契约"),
        ("      required: ['data.ticketId']", "路径不以 $ 开头 —— 取不到，契约静默失效"),
        ("      min_items: {'$.data.items': 'one'}", "min_items 不是整数"),
        ("      requiredx: ['$.data.x']", "拼错字段名"),
    ],
)
def test_output_schema_bad_shape_rejected(tmp_path: Path, block: str, why: str):
    """V10：形状不合法必须在**加载期**炸，不能留到运行期静默不生效。"""
    path = _write_output_schema_manifest(tmp_path, block)
    with pytest.raises(ManifestError, match="V10"):
        load_capability_manifest(path)
    assert "probe_contract" not in {s.capability_id for s in list_capabilities()}


def test_output_schema_valid_shape_loads(tmp_path: Path):
    """合法契约必须能加载进 spec（对照——上面四条不是"一律拒绝"）。"""
    block = """      required: ["$.data.ticketId"]
      min_items: {"$.data.items": 1}
      empty_is_suspicious: true"""
    path = _write_output_schema_manifest(tmp_path, block)
    result = load_capability_manifest(path)
    assert "probe_contract" in set(result.registered_ids)
    spec = next(s for s in list_capabilities() if s.capability_id == "probe_contract")
    assert spec.output_schema == {
        "required": ["$.data.ticketId"],
        "min_items": {"$.data.items": 1},
        "empty_is_suspicious": True,
    }
    unregister_probe = getattr(spec, "capability_id", None)
    assert unregister_probe == "probe_contract"


# ---------------- 失败成因分类（熔断的判定依据）----------------


# ---------------- 失败成因分类（熔断的判定依据）----------------


def test_environmental_failure_classification():
    """只有「下游不响应 / 5xx / 429」算环境类；业务响应与本地装配不算。"""
    from app.ops.capability.errors import (
        CAUSE_BUSINESS,
        CAUSE_HTTP_STATUS,
        CAUSE_LOCAL,
        CAUSE_TRANSPORT,
        is_environmental_failure,
    )

    # 该熔
    assert is_environmental_failure(CAUSE_TRANSPORT) is True
    assert is_environmental_failure(CAUSE_HTTP_STATUS, 500) is True
    assert is_environmental_failure(CAUSE_HTTP_STATUS, 503) is True
    assert is_environmental_failure(CAUSE_HTTP_STATUS, 429) is True

    # 不该熔：下游活着并回答了
    assert is_environmental_failure(CAUSE_HTTP_STATUS, 200) is False
    assert is_environmental_failure(CAUSE_HTTP_STATUS, 404) is False
    assert is_environmental_failure(CAUSE_BUSINESS) is False
    # 不该熔：我们自己没配好（配错一次不能把能力停 60s）
    assert is_environmental_failure(CAUSE_LOCAL) is False
    # 信息不全时不判定 → 宁可少熔
    assert is_environmental_failure(None) is False
    assert is_environmental_failure(CAUSE_HTTP_STATUS, None) is False


def test_http_capability_error_exposes_structured_cause():
    """``cause`` 必须能从异常上读到（熔断层不解析 detail 文案）。"""
    from app.ops.capability.adapters.http_generic import HttpCapabilityError
    from app.ops.capability.errors import CAUSE_TRANSPORT, UPSTREAM_ERROR

    err = HttpCapabilityError(UPSTREAM_ERROR, "请求超时", cause=CAUSE_TRANSPORT)
    assert err.environmental is True
    assert str(err) == "upstream_error: 请求超时"  # 对外口径不变

    biz = HttpCapabilityError(UPSTREAM_ERROR, "HTTP 200")
    assert biz.environmental is False  # 未填 cause → 不熔（宁可少熔）
