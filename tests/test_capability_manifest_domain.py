"""P4-T3 · manifest domain 键消费（domain-pack-v1 19 契约 §1/§2 · 上游 commit e453a36 钉死口径）。

loader 行为（app/ops/capability/manifest.py）：
- §1.2 域 id 词表 [a-z0-9_]+——与 capability id 点分词表独立、禁止互拼（R5）；
- §1.3 保留字：撞 allow_tags_any / allow_write_tags_any 现存值
  （含 env OPS_CAPABILITY_ALLOW_WRITE_TAGS）或字面量 mcp → 整文件拒载（R6）；
  oa 是既有合法域，不溯及；
- §2.1 domain → tags 注入：手写 ∪ {domain} 并集去重（手写在前 · domain 兜底追加）；
  键缺失 = 不注入（存量零 diff）；
- §2.2 oa 防双写漂移（R10/N7）：手写面保留 + 注入恒 no-op——逐值一致哨兵；
- §2.3 MCP 翻译条目 domain 真源在 server 配置侧，不经本 loader——但 manifest
  文件内的 kind: mcp 条目与其他条目同受注入（委派书 test plan 第 3 条）。
"""

from __future__ import annotations

from pathlib import Path

import pytest

from app.ops.capability import list_capabilities
from app.ops.capability.baseline import ENV_ALLOW_WRITE_TAGS, baseline_filter
from app.ops.capability.defaults import ensure_default_capabilities
from app.ops.capability.gateway import get_registry
from app.ops.capability.manifest import ManifestError, load_capability_manifest

# 既有真清单（oa 域键 + 手写面 · ops.write 无 domain 键——存量零 diff 哨兵）
_MANIFEST_DIR = Path(__file__).resolve().parents[1] / "app" / "ops" / "capability" / "manifests"
_OA_MANIFEST = _MANIFEST_DIR / "oa.readonly.v1.yaml"
_OPS_WRITE_MANIFEST = _MANIFEST_DIR / "ops.write.v1.yaml"

# oa 手写 tags 逐值钉死（R10/N7：手写面保留 · 注入恒 no-op 的哨兵）
_OA_IDS = {"oa.doc.search", "oa.org.whois", "oa.todo.mine"}
_OA_EXPECTED_TAGS = {
    "oa.doc.search": ("oa", "doc", "readonly"),
    "oa.org.whois": ("oa", "org", "readonly"),
    "oa.todo.mine": ("oa", "todo", "readonly", "personal"),
}
_OPS_WRITE_EXPECTED_TAGS = ("ops", "run_note", "write")

# 最小合法条目（local_fn 承 test_capability_manifest fixture 范式；
# http 块字段对齐 oa.readonly.v1.yaml 与 loader 校验面；mcp 块 server_key/tool_name 必填）
_LOCAL_FN_WITH_TAGS = """  - id: foo.probe_a
    kind: local_fn
    description: 单测 fixture
    when_to_use: 单测 fixture
    tags: [alpha, beta]
    risk_level: low
    side_effect: read
    enabled: true
    args_schema: {type: object, properties: {}}
    adapter: local_fn:app.ops.capability.defaults:utc_now_iso
"""

_LOCAL_FN_NO_TAGS = """  - id: foo.probe_b
    kind: local_fn
    description: 单测 fixture
    when_to_use: 单测 fixture
    risk_level: low
    side_effect: read
    enabled: true
    args_schema: {type: object, properties: {}}
    adapter: local_fn:app.ops.capability.defaults:utc_now_iso
"""

_HTTP_ENTRY = """  - id: foo.probe_http
    kind: http
    description: 单测 fixture（http 块字段对齐 oa.readonly.v1.yaml 校验面）
    when_to_use: 单测 fixture
    tags: [http_alpha]
    risk_level: low
    side_effect: read
    enabled: true
    tenant_scoped: false
    visibility:
      departments: [all]
      roles: [all]
      classification_max: internal
    args_schema: {type: object, properties: {}}
    http:
      method: GET
      base_url: FOO_BASE
      path: /api/v1/probe
      auth: foo_probe_token
      timeout_ms: 5000
      success_when:
        path: "$.code"
        in: [0, 200]
      error_map:
        "5001": upstream_error
"""

_MCP_ENTRY = """  - id: foo.probe_mcp
    kind: mcp
    description: 单测 fixture
    when_to_use: 单测 fixture
    tags: [mcp_alpha]
    risk_level: low
    side_effect: read
    enabled: true
    args_schema: {type: object, properties: {}}
    mcp:
      server_key: demo_srv
      tool_name: probe_thing
"""


@pytest.fixture(autouse=True)
def _restore_defaults():
    yield
    get_registry().clear()
    ensure_default_capabilities()


def _write_yaml(path: Path, body: str) -> Path:
    path.write_text(body, encoding="utf-8")
    return path


def _manifest_yaml(*, domain: str | None, entries: list[str]) -> str:
    lines = ["version: 1"]
    if domain is not None:
        lines.append(f"domain: {domain}")
    lines.append("capabilities:")
    lines.extend(entries)
    return "\n".join(lines) + "\n"


# ---------------- §2.1 domain → tags 注入 ----------------


def test_domain_injected_into_all_capability_tags(tmp_path: Path):
    """§2.1：domain 注入同文件全部条目（local_fn/http/mcp 同源 · 无 tags 键兜底）。"""
    get_registry().clear()
    path = _write_yaml(
        tmp_path / "foo_pack.yaml",
        _manifest_yaml(
            domain="foo_pack",
            entries=[_LOCAL_FN_WITH_TAGS, _LOCAL_FN_NO_TAGS, _HTTP_ENTRY, _MCP_ENTRY],
        ),
    )
    load_capability_manifest(path)
    by_id = {s.capability_id: s for s in list_capabilities()}
    # 手写在前 · domain 兜底追加（并集去重）
    assert by_id["foo.probe_a"].tags == ("alpha", "beta", "foo_pack")
    # 无 tags 键 → 兜底成 [domain]
    assert by_id["foo.probe_b"].tags == ("foo_pack",)
    # http 条目同源注入（GenericHttpAdapter 持 spec 引用——同源见最终 tags）
    assert by_id["foo.probe_http"].tags == ("http_alpha", "foo_pack")
    # 文件内 kind=mcp 条目同受注入（委派书 test plan 第 3 条）
    assert by_id["foo.probe_mcp"].tags == ("mcp_alpha", "foo_pack")


def test_domain_union_dedupe_handwritten_contains_domain(tmp_path: Path):
    """§2.1 并集去重：手写已含 domain → 不追加第二份（oa 恒 no-op 的同族纪律）。"""
    get_registry().clear()
    entry = _LOCAL_FN_WITH_TAGS.replace("tags: [alpha, beta]", "tags: [foo_pack, beta]")
    path = _write_yaml(
        tmp_path / "foo_pack.yaml",
        _manifest_yaml(domain="foo_pack", entries=[entry]),
    )
    load_capability_manifest(path)
    by_id = {s.capability_id: s for s in list_capabilities()}
    assert by_id["foo.probe_a"].tags == ("foo_pack", "beta")


def test_domain_missing_no_injection(tmp_path: Path):
    """§2.1 反向：键缺失 = 不注入（存量零 diff）。"""
    get_registry().clear()
    path = _write_yaml(
        tmp_path / "no_domain.yaml",
        _manifest_yaml(domain=None, entries=[_LOCAL_FN_WITH_TAGS]),
    )
    load_capability_manifest(path)
    by_id = {s.capability_id: s for s in list_capabilities()}
    assert by_id["foo.probe_a"].tags == ("alpha", "beta")


# ---------------- §1.2 域 id 词表 ----------------


@pytest.mark.parametrize("bad", ["Foo_pack", "foo-pack", "foo.pack", ""])
def test_domain_invalid_vocabulary_rejected(tmp_path: Path, bad: str):
    """§1.2：词表 [a-z0-9_]+ 之外（含点号——与 capability id 词表独立禁互拼 R5）拒载。"""
    get_registry().clear()
    path = _write_yaml(
        tmp_path / "bad_domain.yaml",
        _manifest_yaml(domain=f'"{bad}"', entries=[_LOCAL_FN_WITH_TAGS]),
    )
    with pytest.raises(ManifestError, match="domain 非法"):
        load_capability_manifest(path)
    # 整文件拒载 · 不半套注册
    assert "foo.probe_a" not in {s.capability_id for s in list_capabilities()}


def test_domain_non_string_rejected(tmp_path: Path):
    """§1.2：非 str 形态（YAML 标量 5）整文件拒载。"""
    get_registry().clear()
    path = _write_yaml(
        tmp_path / "bad_domain.yaml",
        _manifest_yaml(domain="5", entries=[_LOCAL_FN_WITH_TAGS]),
    )
    with pytest.raises(ManifestError, match="domain 非法"):
        load_capability_manifest(path)


# ---------------- §1.3 保留字 ----------------


def test_domain_reserved_word_mcp_rejected(tmp_path: Path):
    """§1.3 R6：撞 allow_tags_any 现存值 mcp → 整文件拒载 · 不半套注册。"""
    get_registry().clear()
    path = _write_yaml(
        tmp_path / "reserved.yaml",
        _manifest_yaml(domain="mcp", entries=[_LOCAL_FN_WITH_TAGS]),
    )
    with pytest.raises(ManifestError, match="撞保留字"):
        load_capability_manifest(path)
    assert "foo.probe_a" not in {s.capability_id for s in list_capabilities()}


def test_domain_reserved_word_from_env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    """§1.3 R6：env OPS_CAPABILITY_ALLOW_WRITE_TAGS 现存值撞 domain → 拒载；
    env 清掉后同值可载（防 domain 与写放行值同值白捡 deny_write 豁免）。"""
    monkeypatch.setenv(ENV_ALLOW_WRITE_TAGS, "hr, finance")
    get_registry().clear()
    blocked = _write_yaml(
        tmp_path / "hr_pack.yaml",
        _manifest_yaml(domain="hr", entries=[_LOCAL_FN_WITH_TAGS]),
    )
    with pytest.raises(ManifestError, match="撞保留字"):
        load_capability_manifest(blocked)

    monkeypatch.setenv(ENV_ALLOW_WRITE_TAGS, "finance")
    get_registry().clear()
    load_capability_manifest(blocked)
    by_id = {s.capability_id: s for s in list_capabilities()}
    assert by_id["foo.probe_a"].tags == ("alpha", "beta", "hr")


def test_domain_oa_existing_allowed(tmp_path: Path):
    """§1.3 R6 不溯及：oa 是既有合法域——显式豁免不拒载。"""
    get_registry().clear()
    path = _write_yaml(
        tmp_path / "oa_pack.yaml",
        _manifest_yaml(domain="oa", entries=[_LOCAL_FN_NO_TAGS]),
    )
    load_capability_manifest(path)
    by_id = {s.capability_id: s for s in list_capabilities()}
    assert by_id["foo.probe_b"].tags == ("oa",)


# ---------------- §2.2 / 存量零 diff 哨兵 ----------------


def test_oa_manifest_handwritten_tags_preserved():
    """§2.2 R10/N7 哨兵：oa 真清单手写 tags 逐值不动 · 注入恒 no-op。"""
    get_registry().clear()
    load_capability_manifest(_OA_MANIFEST)
    by_id = {s.capability_id: s for s in list_capabilities()}
    assert set(by_id) >= _OA_IDS
    for cid, expected in _OA_EXPECTED_TAGS.items():
        assert by_id[cid].tags == expected


def test_ops_write_manifest_no_domain_zero_injection():
    """存量零 diff 哨兵：ops.write.v1.yaml 无 domain 键 → tags 逐值不动。"""
    get_registry().clear()
    load_capability_manifest(_OPS_WRITE_MANIFEST)
    by_id = {s.capability_id: s for s in list_capabilities()}
    assert by_id["ops.write.run_note"].tags == _OPS_WRITE_EXPECTED_TAGS


def test_baseline_visibility_not_widened_by_domain(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    """委派书第 4 条：新域不被既有消费面意外命中（allowlist 不放宽）。

    - oa（DOMAIN_ALLOW_TAGS 成员）的 http 条目维持可见——既有面不缩水；
    - 新域 hr（非成员 · env 写放行已清）的 http 条目不因注入 tag 白捡可见。
    """
    monkeypatch.delenv(ENV_ALLOW_WRITE_TAGS, raising=False)
    get_registry().clear()
    load_capability_manifest(_OA_MANIFEST)
    visible = {s.capability_id for s in list_capabilities(filter=baseline_filter(node_role="t"))}
    assert visible >= _OA_IDS

    hr_path = _write_yaml(
        tmp_path / "hr_pack.yaml",
        _manifest_yaml(
            domain="hr",
            entries=[_HTTP_ENTRY.replace("foo.probe_http", "hr.probe_http")],
        ),
    )
    load_capability_manifest(hr_path)
    visible_after = {
        s.capability_id for s in list_capabilities(filter=baseline_filter(node_role="t"))
    }
    assert "hr.probe_http" not in visible_after
