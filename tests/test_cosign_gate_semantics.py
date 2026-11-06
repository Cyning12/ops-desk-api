"""同签语义裁决落文 · 机断结构断言（HG-COSIGN-SEMANTICS-DESIGN · issue #333）。

裁决（lead 2026-11-06 · 依据 = PR #351 review 5795679444 + issue #333 comment 6676780590）：
案①幂等为主干（幂等锚五元组 · 同锚重送达 = 同效力不重复记录 · 可记 replay 附注）
+ 覆盖不设默认（append-only · 同锚 + 维护者显式声明替换意图 → 追加新行 · 旧行保留引注）
+ 拒重复不设（补发/重送达是合法通路）
+ 落点 = gate 记录层（Harness 过程资产 · 机断可 grep；消费门内 = 仓外运行时面随 residual_risk 登记）。

负样本（红测先行）：本组断言先红——裁决落文前「同锚重送达的认定规则」在
gate 记录层无可 grep 真源（认定路径无规则 = 重复送达存在被误读为新签的空缺）。
"""

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
FRAGMENT = REPO_ROOT / "docs" / "harness" / "prompts" / "FRAGMENT_00_gate_cosign_semantics_v1_zh.md"
ORCHESTRATOR = REPO_ROOT / "docs" / "harness" / "prompts" / "00-orchestrator.md"
TASK_TEMPLATE = REPO_ROOT / "docs" / "harness" / "templates" / "TASK_TEMPLATE.md"


def test_fragment_exists_with_frontmatter() -> None:
    assert FRAGMENT.is_file(), "同签语义裁决落文缺失（gate 记录层无可机断真源）"
    text = FRAGMENT.read_text(encoding="utf-8")
    assert "name:" in text.split("---")[1], "FRAGMENT frontmatter 缺 name"
    assert "description:" in text.split("---")[1], "FRAGMENT frontmatter 缺 description"


def test_idempotent_anchor_five_tuple() -> None:
    text = FRAGMENT.read_text(encoding="utf-8")
    anchor_section = text.split("## 幂等锚")[1][:400]
    for field in ("维护者", "工单", "闸集", "签认依据", "授权窗口"):
        assert field in anchor_section, f"幂等锚缺字段：{field}"


def test_same_anchor_redelivery_idempotent() -> None:
    text = FRAGMENT.read_text(encoding="utf-8")
    assert "同锚重送达" in text
    assert "同效力" in text
    assert "不重复记录" in text
    assert "replay" in text.lower(), "replay 附注形态未落文"


def test_override_no_default_append_only() -> None:
    text = FRAGMENT.read_text(encoding="utf-8")
    assert "覆盖不设默认" in text
    assert "append-only" in text
    assert "显式声明替换意图" in text
    assert "追加新行" in text
    assert "旧行保留引注" in text, "覆盖须旧行保留引注（审计链只增不改）"


def test_reject_duplicate_not_established() -> None:
    text = FRAGMENT.read_text(encoding="utf-8")
    assert "拒重复不设" in text
    assert "合法通路" in text


def test_landing_point_is_gate_record_layer() -> None:
    text = FRAGMENT.read_text(encoding="utf-8")
    assert "gate 记录层" in text
    assert "消费门内" in text
    assert "residual_risk" in text, "仓外运行时面（消费门内）须随 residual_risk 登记"


def test_orchestrator_reaches_fragment() -> None:
    assert "FRAGMENT_00_gate_cosign_semantics_v1_zh.md" in ORCHESTRATOR.read_text(
        encoding="utf-8"
    ), "00-orchestrator 未引用同签语义 FRAGMENT（认定规则不可达运行时）"


def test_gate_table_four_column_contract_intact() -> None:
    template = TASK_TEMPLATE.read_text(encoding="utf-8")
    assert "| human_gate_id | status | blocks_hats | 说明 |" in template
    assert "| HG-AUDIT-R1 | pending | 30 |" in template
