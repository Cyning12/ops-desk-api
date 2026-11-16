"""skill_loader 注入证据测试（P2b-T4 · 11 §9.2 a-d + R9b schema 对拍）。

a) off：supervisor system 与 loader 零调用（skills 目录有货也逐字节一致）；
b) on：「## 可用技能（摘要）」节挂 supervisor system 尾，整节 ≤ max_chars；
c) on + skill_ref：工人 prompt 注入技能全文（skill_content trusted 槽逐字节）；
d) on + 未知 skill_ref：span warn（skill_ref_unknown）fail-open 零注入不炸 plan；
R9b：SubtaskItem（off）无 skill_ref 字段/extra ignore 丢键；SubtaskItemSkillRef
（on）收取声明——off 态 JSON schema 逐字节不变。

全部 mock LLM（SimpleNamespace provider · 承 test_lg_rag_supervisor_capability_catalog.py 先例），
不连真外网；env 直读无缓存（monkeypatch.setenv 即时生效 · 承 goals/inject.py 体例）。
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from langchain_core.messages import HumanMessage

from app.ops.capability import list_capabilities
from app.ops.lg_rag.multi import nodes
from app.ops.lg_rag.multi.nodes import (
    _parse_subtasks,
    _worker_state,
    supervisor_node,
)
from app.ops.lg_rag.schemas.subtasks import SubtaskItem, SubtaskItemSkillRef
from app.ops.skill_registry import (
    CATALOG_GUIDE,
    CATALOG_HEADER,
    ENV_ENABLED,
    ENV_ROOT,
    reset_skills_cache,
    skill_catalog_max_chars,
)
from app.ops.strategy import BUILDER_CAP_FILTER

_SKILL_MD = """---
name: panel-data-guide
description: 面板数据解读指南
when_to_use: 需要解读面板指标时
---

# 面板数据解读指南

唯一标记句SKILLFULLBODY。
"""

_PLAN_RAG = json.dumps(
    {"subtasks": [{"id": "t1", "type": "rag", "input": "查部署"}]},
    ensure_ascii=False,
)
_PLAN_SKILL = json.dumps(
    {
        "subtasks": [
            {
                "id": "t1",
                "type": "rag",
                "input": "解读面板",
                "skill_ref": "panel-data-guide",
            }
        ]
    },
    ensure_ascii=False,
)


@pytest.fixture(autouse=True)
def _reset_cache():
    reset_skills_cache()
    yield
    reset_skills_cache()


def _seed_root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    pkg = tmp_path / "panel-data-guide"
    pkg.mkdir()
    (pkg / "SKILL.md").write_text(_SKILL_MD, encoding="utf-8")
    monkeypatch.setenv(ENV_ROOT, str(tmp_path))
    return tmp_path


def _loader_on(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(ENV_ENABLED, "yes")


def _loader_off(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv(ENV_ENABLED, raising=False)


def _span_cm():
    cm = MagicMock()
    cm.__enter__ = MagicMock(return_value=None)
    cm.__exit__ = MagicMock(return_value=False)
    return cm


def _allowlist() -> list[str]:
    return [s.capability_id for s in list_capabilities(filter=BUILDER_CAP_FILTER)]


async def _capture_supervisor_system(plan: str) -> str:
    """跑一次 supervisor_node（mock LLM 固定 plan），回传发给 LLM 的 system 文本。"""
    captured: list[list] = []

    async def _complete(messages, *, model):
        captured.append(messages)
        return plan

    provider = SimpleNamespace(complete=_complete)
    with (
        patch("app.ops.lg_rag.multi.nodes.get_llm_provider", return_value=provider),
        patch("app.ops.lg_rag.multi.nodes._record_span_metadata"),
        patch("app.ops.lg_rag.multi.nodes.trace_span", return_value=_span_cm()),
    ):
        await supervisor_node(
            {
                "messages": [HumanMessage(content="复合问题")],
                "allowed_capability_ids": _allowlist(),
                "run_id": "catrun",
            }
        )
    assert captured, "supervisor 未调 LLM"
    return captured[0][0].content


# ---------------- §9.2-a · off：loader 零调用 + 逐字节一致 ----------------


@pytest.mark.asyncio
async def test_off_supervisor_system_byte_identical_loader_zero_calls(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    """off 态：skills 目录有货也不读——两次 env 变化（有货/无根）system 逐字节一致，
    且 nodes 侧 format_skill_catalog / get_skill 零调用。"""
    _loader_off(monkeypatch)
    _seed_root(tmp_path, monkeypatch)  # 目录有货
    spy_catalog = MagicMock(side_effect=AssertionError("off 态禁调 format_skill_catalog"))
    spy_get = MagicMock(side_effect=AssertionError("off 态禁调 get_skill"))
    with (
        patch.object(nodes, "format_skill_catalog", spy_catalog),
        patch.object(nodes, "get_skill", spy_get),
    ):
        system_with_skills = await _capture_supervisor_system(_PLAN_RAG)
    spy_catalog.assert_not_called()
    spy_get.assert_not_called()
    assert CATALOG_HEADER not in system_with_skills
    # 逐字节对照：根目录指向不存在路径，off 态输出须一字不差
    monkeypatch.setenv(ENV_ROOT, str(tmp_path / "no-such-root"))
    system_without_root = await _capture_supervisor_system(_PLAN_RAG)
    assert system_with_skills == system_without_root


# ---------------- §9.2-b · on：catalog 节挂尾 + 预算 ----------------


@pytest.mark.asyncio
async def test_on_supervisor_system_contains_skill_catalog_within_budget(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    _loader_on(monkeypatch)
    _seed_root(tmp_path, monkeypatch)
    system = await _capture_supervisor_system(_PLAN_RAG)
    assert CATALOG_HEADER in system
    assert "- panel-data-guide：面板数据解读指南（何时用：需要解读面板指标时）" in system
    assert CATALOG_GUIDE in system
    # 整节 ≤ OPS_SKILL_CATALOG_MAX_CHARS（默认 4000）
    section = system[system.index(CATALOG_HEADER):]
    assert len(section) <= skill_catalog_max_chars()
    # 技能全文不泄进 catalog（摘要面与全文本面分离 · §6.3/§6.4）
    assert "唯一标记句SKILLFULLBODY" not in system


# ---------------- §9.2-c · on + skill_ref：全文注入工人 prompt ----------------


@pytest.mark.asyncio
async def test_on_supervisor_plan_skill_ref_end_to_end(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    """on：plan 声明 skill_ref → supervisor 收取 → _worker_state 注入全文。"""
    _loader_on(monkeypatch)
    _seed_root(tmp_path, monkeypatch)
    captured_out: list[dict] = []
    provider = SimpleNamespace(complete=AsyncMock(return_value=_PLAN_SKILL))
    with (
        patch("app.ops.lg_rag.multi.nodes.get_llm_provider", return_value=provider),
        patch("app.ops.lg_rag.multi.nodes._record_span_metadata"),
        patch("app.ops.lg_rag.multi.nodes.trace_span", return_value=_span_cm()),
    ):
        out = await supervisor_node(
            {
                "messages": [HumanMessage(content="复合问题")],
                "allowed_capability_ids": _allowlist(),
                "run_id": "catrun",
            }
        )
    captured_out.append(out)
    subtask = captured_out[0]["subtasks"][0]
    assert subtask["skill_ref"] == "panel-data-guide"
    worker = _worker_state({"messages": [], "subtasks": [subtask]}, subtask)
    injected = worker["assigned_subtask"]["input"]
    assert injected.startswith("解读面板")
    assert "唯一标记句SKILLFULLBODY" in injected
    # skill_content trusted 槽 = 逐字节原样（含 frontmatter 全文 · §6.2）
    assert injected == "解读面板" + chr(10) * 2 + _SKILL_MD


# ---------------- §9.2-d · on + 未知 skill_ref：fail-open + span ----------------


def test_on_worker_state_unknown_skill_ref_fail_open(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, caplog
):
    _loader_on(monkeypatch)
    _seed_root(tmp_path, monkeypatch)
    recorded: list[dict] = []
    subtask = {
        "id": "t1",
        "type": "rag",
        "input": "解读面板",
        "skill_ref": "no-such-skill",
    }
    with (
        caplog.at_level(logging.WARNING),
        patch(
            "app.ops.lg_rag.multi.nodes._record_span_metadata",
            side_effect=lambda m: recorded.append(m),
        ),
    ):
        worker = _worker_state({"messages": [], "subtasks": [subtask]}, subtask)
    # fail-open：零注入、input 原样、不炸
    assert worker["assigned_subtask"]["input"] == "解读面板"
    assert {"skill_ref_unknown": "no-such-skill"} in recorded
    assert "skill_ref 未知" in caplog.text


# ---------------- R9b · schema 对拍（off 逐字节 / on 收取） ----------------


def test_r9b_off_parse_drops_skill_ref(monkeypatch: pytest.MonkeyPatch):
    """off：SubtaskItem extra=ignore 丢 skill_ref 键——subtask dict 零新键。"""
    _loader_off(monkeypatch)
    subtasks = _parse_subtasks(_PLAN_SKILL)
    assert subtasks is not None and len(subtasks) == 1
    assert "skill_ref" not in subtasks[0]
    # off 态 schema 面无 skill_ref 字段（JSON schema 逐字节不变）
    assert "skill_ref" not in SubtaskItem.model_fields
    assert "skill_ref" not in SubtaskItem.model_json_schema().get("properties", {})


def test_r9b_on_parse_captures_skill_ref(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    """on：SubtaskItemSkillRef 收取声明；loader 状态不影响解析层。"""
    _loader_on(monkeypatch)
    _seed_root(tmp_path, monkeypatch)
    subtasks = _parse_subtasks(_PLAN_SKILL)
    assert subtasks is not None
    assert subtasks[0]["skill_ref"] == "panel-data-guide"
    assert "skill_ref" in SubtaskItemSkillRef.model_fields


def test_off_worker_state_skill_ref_key_loader_zero_calls(monkeypatch: pytest.MonkeyPatch):
    """off：subtask dict 即使带 skill_ref 键（旁路）也 loader 零调用零注入。"""
    _loader_off(monkeypatch)
    spy_get = MagicMock(side_effect=AssertionError("off 态禁调 get_skill"))
    subtask = {
        "id": "t1",
        "type": "rag",
        "input": "解读面板",
        "skill_ref": "panel-data-guide",
    }
    with patch.object(nodes, "get_skill", spy_get):
        worker = _worker_state({"messages": [], "subtasks": [subtask]}, subtask)
    spy_get.assert_not_called()
    assert worker["assigned_subtask"]["input"] == "解读面板"
