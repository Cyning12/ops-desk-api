"""画像记忆（kind=preference）幻觉偏好红线（否决项 · memory-preference-profile）。

**红线不是准确率。** 任一条被突破**整体不通过**。每条红线两个断言缺一不可：

- **正向**：无偏好记忆 → 注入块无 `[用户偏好]` 节（物理不存在）
- **反向对照**：有 preference 行 → 节必须出现（否则"永不渲染"也是假通过）

清单在 `evals/memory/preference_redline_v1.yaml`；本文件是它的实现，
两者一一对应（P0 守这条）。

热路径零 LLM-as-judge：判定面是**注入模型的上下文结构**（确定性），
不是对模型自由文本的语义裁判；「写入→污染→撤销→消失」三态全链路见
tests/test_memory_service_db.py::test_mutation_wrong_preference_pollutes_then_revoke_by_key_erases。
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock

import pytest
import yaml
from langchain_core.messages import SystemMessage

from app.ops.lg_rag.continuity import (
    MEMORY_FACTS_HEADER,
    MEMORY_PREFERENCES_GUIDE,
    MEMORY_PREFERENCES_HEADER,
    assemble_graph_messages_with_memory,
    render_memory_facts_block,
)

pytestmark = pytest.mark.redline

_INVENTORY = (
    Path(__file__).resolve().parents[2] / "evals" / "memory" / "preference_redline_v1.yaml"
)

#: redline_id → 实现它的测试函数名（装饰器登记，P0 对照用）
IMPLEMENTED: dict[str, str] = {}


def redline(redline_id: str):
    def decorate(fn):
        IMPLEMENTED[redline_id] = fn.__name__
        fn.__doc__ = f"[{redline_id}] {fn.__doc__ or ''}"
        return fn

    return decorate


def _load_inventory() -> dict:
    with _INVENTORY.open(encoding="utf-8") as f:
        return yaml.safe_load(f)


async def _assemble_with_recall(monkeypatch: pytest.MonkeyPatch, question: str, facts):
    """MEMORY_FACTS_ENABLED=true + 桩召回（无 DB），返回注入块 SystemMessage 文本集。"""
    monkeypatch.setenv("MEMORY_FACTS_ENABLED", "true")
    # 钉确定性召回通路（同 test_memory_injection._patch_recall 理由：
    # 宿主 .env 开向量召回 + 网络可用时 recall_with_vector 与桩 dicts 不兼容）
    monkeypatch.delenv("MEMORY_FACTS_VECTOR_RECALL_ENABLED", raising=False)
    monkeypatch.setattr(
        "app.ops.memory.service.recall_active", AsyncMock(return_value=facts)
    )
    out = await assemble_graph_messages_with_memory(
        question, [], tenant_id="redline-tenant", user_id="u-redline"
    )
    return [str(m.content) for m in out if isinstance(m, SystemMessage)]


@redline("P0")
def test_inventory_matches_implementation():
    """清单 ↔ 实现一一对应：多声明 = 假防护，少声明 = 暗改。"""
    inv = _load_inventory()
    declared = {r["id"] for r in inv["redlines"]}
    assert declared == set(IMPLEMENTED), (
        f"清单与实现漂移：declared={sorted(declared)} implemented={sorted(IMPLEMENTED)}"
    )


@redline("P1")
async def test_no_preference_memory_no_preference_section(
    monkeypatch: pytest.MonkeyPatch,
):
    """无记忆用户问偏好类问题（金样 G1–G4）→ 注入上下文零偏好节（物理不存在）。

    反向对照：同一装配路径下有 preference 行 → 节必须出现（防空真）。
    """
    cases = _load_inventory()["golden_cases"]
    assert len(cases) >= 3, "金样太少不足以称金样"
    for case in cases:
        blocks = await _assemble_with_recall(monkeypatch, case["question"], [])
        assert not any(MEMORY_PREFERENCES_HEADER in b for b in blocks), (
            f"[{case['id']}] 无偏好记忆却渲染出偏好节：{case['question']}"
        )
        assert not any(MEMORY_PREFERENCES_GUIDE in b for b in blocks)

    # 反向对照：有 preference 行 → 偏好节出现（证明上面的"无节"不是坏掉的渲染）
    blocks = await _assemble_with_recall(
        monkeypatch,
        cases[0]["question"],
        [{"key": "pref.answer_lang", "value": "中文", "kind": "preference"}],
    )
    assert any(MEMORY_PREFERENCES_HEADER in b for b in blocks)


@redline("P2")
def test_preference_section_guide_anchors():
    """偏好节引导语锚点：「非客观事实」+「无偏好不要假设/编造」语义。

    锚点断言非全文快照（改文案不挂 · 改变量语义必挂）；反向对照：事实节
    （无引导语）天然不含这些锚点——锚点确为偏好节独有语义。
    """
    facts = [{"key": "pref.answer_lang", "value": "中文", "kind": "preference"}]
    block = render_memory_facts_block(facts)
    assert MEMORY_PREFERENCES_HEADER in block
    assert "非客观事实" in block
    assert "无偏好" in block and ("假设" in block or "编造" in block)
    fact_only = render_memory_facts_block(
        [{"key": "project.primary_repo", "value": "cyning/ops-desk"}]
    )
    assert "非客观事实" not in fact_only


@redline("P3")
def test_preference_never_in_facts_section():
    """preference 行不得进 `[已知事实]` 节；反向对照：fact 行正常进事实节。"""
    facts = [
        {"key": "project.primary_repo", "value": "cyning/ops-desk"},
        {"key": "pref.answer_lang", "value": "中文", "kind": "preference"},
    ]
    lines = render_memory_facts_block(facts).split("\n")
    fact_idx = lines.index(MEMORY_FACTS_HEADER)
    pref_idx = lines.index(MEMORY_PREFERENCES_HEADER)
    fact_section = lines[fact_idx:pref_idx]
    pref_section = lines[pref_idx:]
    assert not any(line.startswith("pref.") for line in fact_section)
    assert "project.primary_repo=cyning/ops-desk" in fact_section  # 反向对照
    assert "pref.answer_lang=中文" in pref_section
