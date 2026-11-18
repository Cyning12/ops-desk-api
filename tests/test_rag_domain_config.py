"""P4-T4 RAG 域配置面（19 契约 §4 · fail-closed 域隔离）。

覆盖：collection 按域三级回退矩阵全格 · ops 零 diff 对拍 · domain=None 两通路
（contextvar 注入 / OPS_DOMAIN env）· rag 子任务域闸（非 ops 未配置 ⇒
「本域未配置检索」且 astream_router_agent 零调用 · ops/已配置域放行）·
glossary 按域文件回退 + 按域缓存隔离 · 影子写 None-skip（零 DLQ）。
"""

from __future__ import annotations

import os

import pytest
from langchain_core.messages import AIMessage

from app.ops.lg_rag.multi.nodes import rag_subtask_node
from app.ops.prompts import domain_context
from app.ops.rag import backend as rag_backend
from app.ops.rag import glossary as rag_glossary
from app.ops.rag import shadow_write as rag_shadow

_ENV_KEYS = (
    "QDRANT_COLLECTION_OPS",
    "QDRANT_COLLECTION_OA",
    "QDRANT_COLLECTION_ZZ",
    "QDRANT_COLLECTION",
    "OPS_DOMAIN",
)


@pytest.fixture(autouse=True)
def _reset_env_and_cache(monkeypatch: pytest.MonkeyPatch):
    for key in _ENV_KEYS:
        monkeypatch.delenv(key, raising=False)
    rag_glossary._TABLES.clear()
    yield
    rag_glossary._TABLES.clear()


def _base_qdrant_collection() -> str:
    """base 版 qdrant_collection() 语义复刻（零 diff 对拍真源）。"""
    return (os.getenv("QDRANT_COLLECTION") or "ops_knowledge").strip() or "ops_knowledge"


# ---------------------------------------------------------------- collection 矩阵


@pytest.mark.parametrize(
    ("env", "expected"),
    [
        ({}, "ops_knowledge"),
        ({"QDRANT_COLLECTION": "custom"}, "custom"),
        ({"QDRANT_COLLECTION": "  padded  "}, "padded"),
        ({"QDRANT_COLLECTION_OPS": "ops2"}, "ops2"),
        ({"QDRANT_COLLECTION_OPS": "ops2", "QDRANT_COLLECTION": "custom"}, "ops2"),
        ({"QDRANT_COLLECTION_OPS": "  "}, "ops_knowledge"),  # 空白视同未配置
        ({"QDRANT_COLLECTION": "  "}, "ops_knowledge"),
        ({"QDRANT_COLLECTION_OPS": " ", "QDRANT_COLLECTION": "custom"}, "custom"),
    ],
)
def test_ops_chain_matrix(monkeypatch: pytest.MonkeyPatch, env, expected):
    for key, value in env.items():
        monkeypatch.setenv(key, value)
    assert rag_backend.qdrant_collection("ops") == expected
    # domain=None（缺省域 · 未注入未设 OPS_DOMAIN ⇒ ops）同值
    assert rag_backend.qdrant_collection() == expected


@pytest.mark.parametrize(
    "env",
    [
        {},
        {"QDRANT_COLLECTION": "custom"},
        {"QDRANT_COLLECTION": "  padded  "},
        {"QDRANT_COLLECTION": " "},
        {"QDRANT_COLLECTION_OPS": " "},  # OPS 键空白=未设 ⇒ 与 base 逐值一致
        {"QDRANT_COLLECTION": ""},
    ],
)
def test_ops_zero_diff_vs_base(monkeypatch: pytest.MonkeyPatch, env):
    """QDRANT_COLLECTION_OPS 未设（含空白）时 ops 链与 base 行为逐值一致。"""
    for key, value in env.items():
        monkeypatch.setenv(key, value)
    assert rag_backend.qdrant_collection("ops") == _base_qdrant_collection()
    assert rag_backend.qdrant_collection() == _base_qdrant_collection()


@pytest.mark.parametrize(
    ("env", "expected"),
    [
        ({"QDRANT_COLLECTION_OA": "oa_kb"}, "oa_kb"),
        ({}, None),
        ({"QDRANT_COLLECTION": "custom"}, None),  # 不回落全局键
        ({"QDRANT_COLLECTION_OPS": "ops2"}, None),  # 不回落 ops 键
        ({"QDRANT_COLLECTION_OA": "  "}, None),  # 空白视同未配置
    ],
)
def test_non_ops_chain_fail_closed(monkeypatch: pytest.MonkeyPatch, env, expected):
    for key, value in env.items():
        monkeypatch.setenv(key, value)
    assert rag_backend.qdrant_collection("oa") == expected


def test_domain_none_resolution_contextvar(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("QDRANT_COLLECTION_OA", "oa_kb")
    token = domain_context.set_current_domain("oa")
    try:
        assert rag_backend.qdrant_collection() == "oa_kb"
        assert rag_backend.qdrant_collection(None) == "oa_kb"
    finally:
        domain_context.reset_current_domain(token)
    # reset 后回落缺省域 ops
    assert rag_backend.qdrant_collection() == "ops_knowledge"


def test_domain_none_resolution_env(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("OPS_DOMAIN", "oa")
    monkeypatch.setenv("QDRANT_COLLECTION_OA", "oa_kb")
    assert rag_backend.qdrant_collection() == "oa_kb"


def test_domain_resolution_failure_falls_back_ops(monkeypatch: pytest.MonkeyPatch, caplog):
    """importlib 运行期解析失败 ⇒ 回落 ops + logger.exception（零 diff 面优先）。"""
    import sys

    # sys.modules 置 None ⇒ import_module 抛 ImportError（不触碰全局 importlib）
    monkeypatch.setitem(sys.modules, "app.ops.prompts.domain_context", None)
    with caplog.at_level("ERROR", logger="app.ops.rag.backend"):
        assert rag_backend._current_domain() == "ops"
    assert "fallback to ops" in caplog.text


# ---------------------------------------------------------------- rag 子任务域闸


def _state() -> dict:
    return {
        "run_id": "run-p4t4",
        "assigned_subtask": {
            "subtask_id": "st1",
            "id": "st1",
            "type": "rag",
            "input": "测试问题",
        },
        "subtasks": [
            {"subtask_id": "st1", "id": "st1", "type": "rag", "input": "测试问题"}
        ],
        "subtask_results": [],
    }


async def _rag_gen(query, thread_id=None):
    yield {
        "rag_node": {
            "messages": [AIMessage(content="检索答案")],
            "chain_meta": {"path": "rag"},
        }
    }


@pytest.mark.asyncio
async def test_gate_fail_closed_oa_unconfigured(monkeypatch: pytest.MonkeyPatch):
    """domain=oa 且无 QDRANT_COLLECTION_OA ⇒ 本域未配置检索 · 后端调用零发生。"""
    calls: list = []

    async def _spy(*a, **k):
        calls.append((a, k))
        yield {}

    monkeypatch.setattr("app.ops.lg_rag.multi.nodes.astream_router_agent", _spy)
    token = domain_context.set_current_domain("oa")
    try:
        out = await rag_subtask_node(_state())
    finally:
        domain_context.reset_current_domain(token)
    assert calls == [], "未配置域不得触达检索后端"
    row = out["subtask_results"][0]
    assert row["output"] == "本域未配置检索"
    assert "error" not in row


@pytest.mark.asyncio
async def test_gate_fail_closed_env_domain_oa(monkeypatch: pytest.MonkeyPatch):
    """OPS_DOMAIN=oa（env 通路 · 未注入）同样 fail-closed。"""
    monkeypatch.setenv("OPS_DOMAIN", "oa")
    calls: list = []

    async def _spy(*a, **k):
        calls.append((a, k))
        yield {}

    monkeypatch.setattr("app.ops.lg_rag.multi.nodes.astream_router_agent", _spy)
    out = await rag_subtask_node(_state())
    assert calls == []
    assert out["subtask_results"][0]["output"] == "本域未配置检索"


@pytest.mark.asyncio
async def test_gate_passes_oa_configured(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("QDRANT_COLLECTION_OA", "oa_kb")
    monkeypatch.setattr("app.ops.lg_rag.multi.nodes.astream_router_agent", _rag_gen)
    token = domain_context.set_current_domain("oa")
    try:
        out = await rag_subtask_node(_state())
    finally:
        domain_context.reset_current_domain(token)
    row = out["subtask_results"][0]
    assert row["output"] == "检索答案"
    assert row["chain_meta"] == {"path": "rag"}


@pytest.mark.asyncio
async def test_gate_passes_ops_default(monkeypatch: pytest.MonkeyPatch):
    """缺省域 ops：闸恒放行（既有行为零 diff）。"""
    monkeypatch.setattr("app.ops.lg_rag.multi.nodes.astream_router_agent", _rag_gen)
    out = await rag_subtask_node(_state())
    row = out["subtask_results"][0]
    assert row["output"] == "检索答案"
    assert row["chain_meta"] == {"path": "rag"}


# ---------------------------------------------------------------- glossary 按域回退


def test_glossary_fallback_same_as_ops():
    ops = rag_glossary.expand_query_for_fts("自动压缩被取消", domain="ops")
    oa = rag_glossary.expand_query_for_fts("自动压缩被取消", domain="oa")
    assert ops is not None
    assert oa == ops  # glossary.oa.yaml 不存在 ⇒ 回退默认件逐字节等


def test_glossary_domain_file_honored(monkeypatch: pytest.MonkeyPatch, tmp_path):
    domain_yaml = tmp_path / "glossary.zz.yaml"
    domain_yaml.write_text("压缩: [ziponly]\n", encoding="utf-8")
    monkeypatch.setattr(
        rag_glossary,
        "_glossary_path",
        lambda d: domain_yaml if d == "zz" else rag_glossary._GLOSSARY_PATH,
    )
    out = rag_glossary.expand_query_for_fts("压缩", domain="zz")
    assert out == "( 压缩 | ziponly )"
    # 其他域不受域件影响
    assert rag_glossary.expand_query_for_fts("压缩", domain="ops") != out


def test_glossary_cache_isolated_by_domain():
    first = rag_glossary.expand_query_for_fts("自动压缩", domain="ops")
    assert set(rag_glossary._TABLES) == {"ops"}
    second = rag_glossary.expand_query_for_fts("自动压缩", domain="oa")
    assert set(rag_glossary._TABLES) == {"ops", "oa"}  # 按域 keyed · 互不串扰
    assert first == second  # 同默认件


def test_glossary_domain_none_uses_current_domain():
    token = domain_context.set_current_domain("oa")
    try:
        out = rag_glossary.expand_query_for_fts("自动压缩")
    finally:
        domain_context.reset_current_domain(token)
    assert set(rag_glossary._TABLES) == {"oa"}
    assert out == rag_glossary.expand_query_for_fts("自动压缩", domain="oa")


# ---------------------------------------------------------------- 影子写 fail-closed


def test_shadow_upsert_skip_when_unconfigured(monkeypatch: pytest.MonkeyPatch, caplog):
    dlq: list = []
    monkeypatch.setattr(rag_shadow, "qdrant_collection", lambda *a, **k: None)
    monkeypatch.setattr(rag_shadow, "_write_dlq", lambda *a, **k: dlq.append(a))
    with caplog.at_level("WARNING", logger="app.ops.rag.shadow_write"):
        rag_shadow._shadow_upsert_safe(
            [rag_shadow.ShadowPoint(point_id=1, vector=[0.1], payload={})]
        )
    assert dlq == []  # 零 DLQ 噪声
    assert "本域未配置检索" in caplog.text


def test_shadow_delete_skip_when_unconfigured(monkeypatch: pytest.MonkeyPatch, caplog):
    dlq: list = []
    monkeypatch.setattr(rag_shadow, "qdrant_collection", lambda *a, **k: None)
    monkeypatch.setattr(rag_shadow, "_write_dlq", lambda *a, **k: dlq.append(a))
    with caplog.at_level("WARNING", logger="app.ops.rag.shadow_write"):
        rag_shadow._shadow_delete_safe([1, 2])
    assert dlq == []
    assert "本域未配置检索" in caplog.text
