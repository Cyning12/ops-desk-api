"""P4-T2 prompt 模板域机制测试（19 契约 §3.1-§3.4 · task_p4_t2_prompt_domain_loader）。

覆盖锚：域文件命中 / 缺失回退（按模板独立 · 否半份合并）/ 坏域件显式炸
点名路径 / domain 词表拒入（含路径穿越负例）/ resolve_domain 解析回退 +
warning / OPS_DOMAIN on-off 全量 11 模板 body 逐字节对拍（§3.4）/ 白名单
KeyError / get_template 域路由 / worker 注入位。隔离形态承
tests/test_prompt_assets.py:146-151（monkeypatch _ASSETS_DIR + 清缓存）。
"""

from __future__ import annotations

import asyncio
import logging
import uuid
from collections.abc import AsyncIterator
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, patch

import pytest

from app.ops.prompts import domain_context, loader
from app.ops.prompts.domain_context import (
    DEFAULT_DOMAIN,
    current_domain,
    reset_current_domain,
    resolve_domain,
    set_current_domain,
)
from app.ops.prompts.loader import PromptAssetError, clear_asset_cache, load_asset
from app.ops.prompts.render import PromptTemplateNotFoundError, get_template
from app.ops.prompts.templates import _TEMPLATE_IDS, TEMPLATES, get_template_for_domain

_VALID = "---\ntemplate_id: {tid}\nversion: v1\n---\n\n{body}\n"


def _write(path: Path, template_id: str, body: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(_VALID.format(tid=template_id, body=body), encoding="utf-8")


@pytest.fixture
def tmp_assets(tmp_path, monkeypatch):
    monkeypatch.setattr(loader, "_ASSETS_DIR", tmp_path)
    clear_asset_cache()
    yield tmp_path
    clear_asset_cache()


@pytest.fixture(autouse=True)
def _clean_domain_env(monkeypatch):
    """隔离 OPS_DOMAIN 环境变量（本文件全部用例）。"""
    monkeypatch.delenv(domain_context.OPS_DOMAIN_ENV, raising=False)


# ---------- §3.1 · 域目录回退 ----------


def test_domain_hit_returns_domain_asset(tmp_assets):
    _write(tmp_assets / "lg_rag.direct.system.md", "lg_rag.direct.system", "OPS-BODY")
    _write(
        tmp_assets / "oa" / "lg_rag.direct.system.md",
        "lg_rag.direct.system",
        "OA-DOMAIN-BODY",
    )
    assert load_asset("lg_rag.direct.system", "oa") == ("v1", "OA-DOMAIN-BODY")
    assert load_asset("lg_rag.direct.system") == ("v1", "OPS-BODY")


def test_domain_missing_file_falls_back_to_root(tmp_assets):
    _write(tmp_assets / "lg_rag.direct.system.md", "lg_rag.direct.system", "OPS-BODY")
    assert load_asset("lg_rag.direct.system", "oa") == ("v1", "OPS-BODY")


def test_domain_fallback_per_template_no_half_merge(tmp_assets):
    """同域下不同模板各自独立命中/回退（覆盖以模板为单位 · 否半份合并）。"""
    _write(tmp_assets / "lg_rag.direct.system.md", "lg_rag.direct.system", "OPS-DIRECT")
    _write(tmp_assets / "lg_rag.intent.system.md", "lg_rag.intent.system", "OPS-INTENT")
    _write(
        tmp_assets / "oa" / "lg_rag.direct.system.md",
        "lg_rag.direct.system",
        "OA-DIRECT",
    )
    assert load_asset("lg_rag.direct.system", "oa") == ("v1", "OA-DIRECT")
    assert load_asset("lg_rag.intent.system", "oa") == ("v1", "OPS-INTENT")


def test_domain_bad_asset_raises_naming_domain_path(tmp_assets):
    """坏文件不静默：域件存在但形态非法 → PromptAssetError 点名域件路径。"""
    _write(tmp_assets / "lg_rag.direct.system.md", "lg_rag.direct.system", "OPS-BODY")
    bad_dir = tmp_assets / "oa"
    bad_dir.mkdir()
    (bad_dir / "lg_rag.direct.system.md").write_text("no front matter here", encoding="utf-8")
    with pytest.raises(PromptAssetError, match="oa"):
        load_asset("lg_rag.direct.system", "oa")


def test_load_asset_rejects_illegal_domain(tmp_assets):
    for bad in ("../etc", "a/b", "OA", "with space", "dot.name"):
        with pytest.raises(PromptAssetError, match="非法 domain"):
            load_asset("lg_rag.direct.system", bad)


def test_load_asset_domain_path_traversal_stays_inside(tmp_assets):
    """路径穿越负例：词表外 domain 永不触目录拼接（双闸之 loader 面）。"""
    _write(tmp_assets / "lg_rag.direct.system.md", "lg_rag.direct.system", "OPS-BODY")
    with pytest.raises(PromptAssetError, match="非法 domain"):
        load_asset("lg_rag.direct.system", "..")


# ---------- §3.3/§5.1 · domain_context 解析面 ----------


def test_resolve_domain_default_blank_and_none():
    assert resolve_domain(None) == DEFAULT_DOMAIN
    assert resolve_domain("") == DEFAULT_DOMAIN
    assert resolve_domain("   ") == DEFAULT_DOMAIN


def test_resolve_domain_accepts_vocab():
    assert resolve_domain("oa") == "oa"
    assert resolve_domain("domain_2") == "domain_2"


def test_resolve_domain_illegal_falls_back_with_warning(caplog):
    with caplog.at_level(logging.WARNING, logger=domain_context.__name__):
        assert resolve_domain("../evil") == DEFAULT_DOMAIN
    assert any("OPS_DOMAIN 非法值" in r.message for r in caplog.records)


def test_current_domain_env_fallback(monkeypatch):
    """漏设无害化（R-P4-2 强化）：contextvar 未注入时回落 env 解析。"""
    assert current_domain() == DEFAULT_DOMAIN
    monkeypatch.setenv(domain_context.OPS_DOMAIN_ENV, "oa")
    assert current_domain() == "oa"
    monkeypatch.setenv(domain_context.OPS_DOMAIN_ENV, "../illegal")
    assert current_domain() == DEFAULT_DOMAIN


def test_set_and_reset_current_domain():
    token = set_current_domain("oa")
    assert current_domain() == "oa"
    reset_current_domain(token)
    assert current_domain() == DEFAULT_DOMAIN


def test_set_current_domain_rejects_illegal():
    with pytest.raises(ValueError, match="非法 domain"):
        set_current_domain("../evil")


# ---------- §3.2 · 白名单薄封装 ----------


def test_get_template_for_domain_whitelist_keyerror(tmp_assets):
    with pytest.raises(KeyError):
        get_template_for_domain("no.such.template", "oa")


def test_get_template_for_domain_hit_and_fallback(tmp_assets):
    _write(tmp_assets / "lg_rag.direct.system.md", "lg_rag.direct.system", "OPS-DIRECT")
    _write(tmp_assets / "lg_rag.intent.system.md", "lg_rag.intent.system", "OPS-INTENT")
    _write(
        tmp_assets / "oa" / "lg_rag.direct.system.md",
        "lg_rag.direct.system",
        "OA-DOMAIN-BODY",
    )
    hit = get_template_for_domain("lg_rag.direct.system", "oa")
    assert hit == {"version": "v1", "body": "OA-DOMAIN-BODY"}
    fallback = get_template_for_domain("lg_rag.intent.system", "oa")
    assert fallback == {"version": "v1", "body": "OPS-INTENT"}


# ---------- §3.3 · get_template 域路由 ----------


def test_get_template_ops_domain_uses_templates_default_face():
    assert current_domain() == DEFAULT_DOMAIN
    tmpl = get_template("lg_rag.direct.system")
    assert tmpl.body == TEMPLATES["lg_rag.direct.system"]["body"]
    assert tmpl.version == TEMPLATES["lg_rag.direct.system"]["version"]


def test_get_template_domain_hit(tmp_assets):
    _write(tmp_assets / "lg_rag.direct.system.md", "lg_rag.direct.system", "OPS-BODY")
    _write(tmp_assets / "oa" / "lg_rag.direct.system.md", "lg_rag.direct.system", "OA-BODY")
    _write(tmp_assets / "lg_rag.intent.system.md", "lg_rag.intent.system", "OPS-INTENT")
    token = set_current_domain("oa")
    try:
        assert get_template("lg_rag.direct.system").body == "OA-BODY"
        # 域件缺失回退根目录（tmp 隔离面 · 根件为 OPS-INTENT）
        assert get_template("lg_rag.intent.system").body == "OPS-INTENT"
        with pytest.raises(PromptTemplateNotFoundError):
            get_template("no.such.template")
    finally:
        reset_current_domain(token)


# ---------- §3.4 · ops 零 diff 对拍（OPS_DOMAIN on/off 全量 11 模板逐字节一致） ----------


def test_ops_domain_env_on_off_byte_identical(monkeypatch):
    """19 §3.4：OPS_DOMAIN=ops（on）与缺省（off）双跑 11 模板 body 逐字节一致。

    真实资产面（不隔离 _ASSETS_DIR）：经 get_template → current_domain 全链路。
    另钉「域目录不存在恒回退根目录」（与不建 assets/ops/ 双保险同构）。
    """
    off = {tid: get_template(tid).body for tid in _TEMPLATE_IDS}
    monkeypatch.setenv(domain_context.OPS_DOMAIN_ENV, "ops")
    on = {tid: get_template(tid).body for tid in _TEMPLATE_IDS}
    assert on == off
    monkeypatch.setenv(domain_context.OPS_DOMAIN_ENV, "domain_without_assets_dir")
    missing_dir = {tid: get_template(tid).body for tid in _TEMPLATE_IDS}
    assert missing_dir == off


# ---------- §3.3 · worker 注入位（start_run_worker 与 set_current_tenant 同位） ----------


@pytest.mark.asyncio
async def test_run_worker_injects_domain_from_env(monkeypatch):
    from langchain_core.messages import AIMessage

    from app.ops.lg_rag.run_worker import get_run_worker_task, start_run_worker

    monkeypatch.setenv(domain_context.OPS_DOMAIN_ENV, "oa")
    seen: list[str] = []
    gate = asyncio.Event()

    async def _astream(
        query: str, *, thread_id: str = "t", **kw: Any
    ) -> AsyncIterator[dict[str, Any]]:
        seen.append(current_domain())
        gate.set()
        yield {"aggregator": {"messages": [AIMessage(content="ok")]}}

    with (
        patch("app.ops.lg_rag.event_store.persist_run_event", new=AsyncMock()),
        patch("app.ops.lg_rag.sse_stream.persist_thread_turns", new=AsyncMock()),
    ):
        run_id = f"p4t2-{uuid.uuid4().hex[:10]}"
        start_run_worker(
            query="域注入",
            mode="supervisor",
            thread_id="th-p4t2",
            run_id=run_id,
            user_id=str(uuid.uuid4()),
            astream_fn=_astream,
        )
        await asyncio.wait_for(gate.wait(), timeout=2.0)
        task = get_run_worker_task(run_id)
        assert task is not None
        await asyncio.wait_for(task, timeout=2.0)

    assert seen and seen[0] == "oa"
    # worker finally reset 后：测试上下文 contextvar 无注入 → 回落 env 解析
    # （env 仍为 oa 时读 oa · env 清除后归 ops 默认）
    assert current_domain() == "oa"
    monkeypatch.delenv(domain_context.OPS_DOMAIN_ENV)
    assert current_domain() == DEFAULT_DOMAIN
