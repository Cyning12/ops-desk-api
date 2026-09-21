"""Prompt 资产化守护测试（task prompt-asset-roadmap-p1 · D2/D3/锚点断言）。

断言口径（SPEC 设计纪律 4）：**锚点断言替代全文快照**——渲染输出含裸
JSON 示例结构锚点（如 `{"domain"`）且无 `{{` 转义残留；非开发改文案
不挂 CI，改变量名 / 留转义 / 缺键 / 缺文件必挂。
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from app.ops.prompts import get_template, loader, render
from app.ops.prompts.loader import PromptAssetError, clear_asset_cache, load_asset
from app.ops.prompts.templates import TEMPLATES

EXPECTED_IDS = {
    "lg_rag.intent.system": "v1",
    "lg_rag.supervisor.system": "v2",
    "lg_rag.supervisor.suffix.system": "v1",
    "lg_rag.router.system": "v1",
    "lg_rag.direct.system": "v1",
    "lg_rag.rewrite.system": "v1",
    "lg_rag.extract.system": "v1",
    "lg_rag.aggregator.system": "v1",
    "memory.extract.system": "v1",
}

#: 渲染变量锚点（string.Template 语法）；除此之外 body 不得含 `$`
DECLARED_VARIABLES = ("$catalog_block", "$prefix_block", "$suffix_cap")

VARS_SUPERVISOR = {"catalog_block": "- mock_get_issue_status：Mock（risk=low）"}
VARS_SUFFIX = {
    "catalog_block": "- mock_get_issue_status：Mock（risk=low）",
    "prefix_block": "- t1：已完成",
    "suffix_cap": "3",
}


def _render_all() -> dict[str, str]:
    return {
        "lg_rag.intent.system": render("lg_rag.intent.system"),
        "lg_rag.supervisor.system": render("lg_rag.supervisor.system", VARS_SUPERVISOR),
        "lg_rag.supervisor.suffix.system": render(
            "lg_rag.supervisor.suffix.system", VARS_SUFFIX
        ),
        "lg_rag.router.system": render("lg_rag.router.system"),
        "lg_rag.direct.system": render("lg_rag.direct.system"),
        "lg_rag.rewrite.system": render("lg_rag.rewrite.system"),
        "lg_rag.extract.system": render("lg_rag.extract.system"),
        "lg_rag.aggregator.system": render("lg_rag.aggregator.system"),
        "memory.extract.system": render("memory.extract.system"),
    }


# ---------- D2 · registry 覆盖与资产形态 ----------


def test_registry_covers_nine_templates():
    assert set(TEMPLATES) == set(EXPECTED_IDS)


@pytest.mark.parametrize("template_id", sorted(EXPECTED_IDS))
def test_asset_loads_with_version_and_body(template_id: str):
    path = loader._ASSETS_DIR / f"{template_id}.md"
    assert path.is_file(), f"资产文件缺失: {path}"
    version, body = load_asset(template_id)
    assert version == EXPECTED_IDS[template_id]
    assert re.fullmatch(r"v\d+", version)
    assert body.strip()
    assert get_template(template_id).version == version


@pytest.mark.parametrize("template_id", sorted(EXPECTED_IDS))
def test_asset_zero_escape_residue(template_id: str):
    """迁移后 body 零 `{{`/`}}` 转义残留；除声明变量外零 `$` 游离。"""
    _version, body = load_asset(template_id)
    assert "{{" not in body and "}}" not in body
    scrubbed = body
    for var in DECLARED_VARIABLES:
        scrubbed = scrubbed.replace(var, "")
    assert "$" not in scrubbed


# ---------- 锚点断言（非全文快照） ----------


@pytest.mark.parametrize(
    ("template_id", "anchor"),
    [
        ("lg_rag.intent.system", '{"domain"'),
        ("lg_rag.supervisor.system", '{"subtasks"'),
        ("lg_rag.supervisor.suffix.system", '{"subtasks"'),
        ("lg_rag.router.system", '{"route"'),
        ("lg_rag.extract.system", '{"dates"'),
        ("memory.extract.system", '{"facts"'),
    ],
)
def test_rendered_output_structure_anchors(template_id: str, anchor: str):
    text = _render_all()[template_id]
    assert anchor in text, f"{template_id} 渲染输出缺结构锚点 {anchor}"
    assert "{{" not in text, f"{template_id} 渲染输出有转义残留"


def test_render_variables_substituted():
    text = render("lg_rag.supervisor.system", VARS_SUPERVISOR)
    assert "mock_get_issue_status" in text
    assert "$catalog_block" not in text
    text = render("lg_rag.supervisor.suffix.system", VARS_SUFFIX)
    assert "mock_get_issue_status" in text
    assert "- t1：已完成" in text
    assert "最多 3 个" in text
    assert "$prefix_block" not in text and "$suffix_cap" not in text


# ---------- D1 · 缺键显式炸 ----------


def test_render_missing_key_names_template_id():
    with pytest.raises(KeyError, match="lg_rag.supervisor.system"):
        render("lg_rag.supervisor.system", {})


# ---------- D3 · 加载器显式炸形态（tmp_path 隔离 · 不动真资产） ----------


@pytest.fixture
def tmp_assets(tmp_path, monkeypatch):
    monkeypatch.setattr(loader, "_ASSETS_DIR", tmp_path)
    clear_asset_cache()
    yield tmp_path
    clear_asset_cache()


def _write(tmp_path: Path, template_id: str, text: str) -> None:
    (tmp_path / f"{template_id}.md").write_text(text, encoding="utf-8")


def test_loader_missing_file_raises(tmp_assets):
    with pytest.raises(PromptAssetError, match="no.such.template"):
        load_asset("no.such.template")


def test_loader_rejects_path_traversal_id(tmp_assets):
    with pytest.raises(PromptAssetError, match="非法 template_id"):
        load_asset("../etc/passwd")


def test_loader_missing_front_matter_field(tmp_assets):
    _write(tmp_assets, "t.noversion.system", "---\ntemplate_id: t.noversion.system\n---\n\n正文\n")
    with pytest.raises(PromptAssetError, match="缺字段 version"):
        load_asset("t.noversion.system")


def test_loader_template_id_mismatch(tmp_assets):
    _write(tmp_assets, "t.a.system", "---\ntemplate_id: t.b.system\nversion: v1\n---\n\n正文\n")
    with pytest.raises(PromptAssetError, match="与文件名不符"):
        load_asset("t.a.system")


def test_loader_bad_version_format(tmp_assets):
    _write(tmp_assets, "t.badver.system", "---\ntemplate_id: t.badver.system\nversion: '1.0'\n---\n\n正文\n")
    with pytest.raises(PromptAssetError, match="version 非 v<N>"):
        load_asset("t.badver.system")


def test_loader_empty_body_raises(tmp_assets):
    _write(tmp_assets, "t.empty.system", "---\ntemplate_id: t.empty.system\nversion: v1\n---\n\n\n")
    with pytest.raises(PromptAssetError, match="body 为空"):
        load_asset("t.empty.system")


def test_loader_cache_clear_rereads(tmp_assets):
    _write(tmp_assets, "t.cached.system", "---\ntemplate_id: t.cached.system\nversion: v1\n---\n\n旧文案\n")
    assert load_asset("t.cached.system") == ("v1", "旧文案")
    _write(tmp_assets, "t.cached.system", "---\ntemplate_id: t.cached.system\nversion: v2\n---\n\n新文案\n")
    clear_asset_cache()
    assert load_asset("t.cached.system") == ("v2", "新文案")
