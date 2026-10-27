"""capability output_fields（task lg-rag-capability-output-schema）。

planner 契约声明从「猜」变「从清单选」：CapabilitySpec.output_fields 声明产出
字段名清单；catalog 注入让 planner 看得见；计划期裁剪把不在清单里的声明字段
裁掉（只裁字段、不拒整 plan；全裁空 → 视同空 = 不校验）。

验收映射：

- **验收 1（catalog 追加渲染）**：声明行含 output_fields 清单；未声明（空）
  能力的行与现状**逐字节一致**；
- **验收 2（计划期裁剪 + span 留痕）**：_issue_plan 出口修剪 produces /
  consumes_resolved，trims 经 _record_span_metadata 留痕；
- **验收 3（运行期注册表对拍 · R1 B1'）**：ensure_default_capabilities() 后
  运行期注册表（builtin.v1.yaml 主加载面）+ defaults 硬编码回退面 +
  testing.v1.yaml 三面 output_fields 与 adapter 实际返回 keys 逐一对齐。
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from app.ops.capability import ainvoke
from app.ops.capability.defaults import (
    _DEFAULT_SPECS,
    ensure_default_capabilities,
)
from app.ops.capability.gateway import get_registry
from app.ops.capability.manifest import (
    MANIFEST_DIR,
    ManifestError,
    load_capability_manifest,
)
from app.ops.capability.types import CapabilitySpec
from app.ops.lg_rag.multi import nodes
from tests.conftest import DB_AVAILABLE

_TESTING_MANIFEST = MANIFEST_DIR / "testing.v1.yaml"
_TENANT_CTX = {"tenant_id": "ops-desk-pilot"}


@pytest.fixture(autouse=True)
def _restore_defaults():
    yield
    get_registry().clear()
    ensure_default_capabilities()


def _write_json(tmp_path: Path, name: str, caps: list[dict]) -> Path:
    path = tmp_path / name
    path.write_text(
        json.dumps({"version": 1, "capabilities": caps}, ensure_ascii=False),
        encoding="utf-8",
    )
    return path


def _probe_cap(**overrides) -> dict:
    cap = {
        "id": "probe.of",
        "kind": "local_fn",
        "description": "output_fields 解析单测",
        "when_to_use": "单测 fixture",
        "args_schema": {"type": "object", "properties": {}},
        "adapter": "local_fn:app.ops.capability.defaults:utc_now_iso",
    }
    cap.update(overrides)
    return cap


# ---------------------------------------------------------------------------
# loader：output_fields 解析与校验（list[str] · 空/缺省 = ()）
# ---------------------------------------------------------------------------


def test_manifest_output_fields_parse(tmp_path: Path):
    """合法 list[str] → tuple；缺省 → ()；空白项剔除。"""
    path = _write_json(
        tmp_path,
        "ok.json",
        [
            _probe_cap(id="probe.of_declared", output_fields=["a", " b ", ""]),
            _probe_cap(id="probe.of_absent"),
        ],
    )
    load_capability_manifest(path)
    declared = get_registry().get("probe.of_declared")
    absent = get_registry().get("probe.of_absent")
    assert declared is not None and absent is not None
    assert declared[0].output_fields == ("a", "b")
    assert absent[0].output_fields == ()


def test_manifest_output_fields_non_list_rejected(tmp_path: Path):
    """非 list → ManifestError（整文件失败，不留半套）。"""
    path = _write_json(tmp_path, "bad.json", [_probe_cap(output_fields="status")])
    with pytest.raises(ManifestError, match="output_fields 必须是 list"):
        load_capability_manifest(path)
    assert get_registry().get("probe.of") is None


def test_capability_spec_output_fields_default_empty():
    """未声明 = ()（不校验语义 · 承 step_contract 不替模型猜）。"""
    spec = CapabilitySpec(capability_id="x", kind="local_fn", description="d")
    assert spec.output_fields == ()


# ---------------------------------------------------------------------------
# 验收 1 · catalog 渲染：声明行追加清单；空声明行逐字节零 diff
# ---------------------------------------------------------------------------


def test_catalog_empty_declaration_row_byte_identical():
    """未声明（空）能力的行与旧格式逐字节一致（验收 1 零 diff 口径）。"""
    spec = CapabilitySpec(capability_id="x", kind="local_fn", description="d", risk_level="low")
    assert nodes._format_capability_catalog([spec]) == "- x：d（risk=low）"


def test_catalog_renders_output_fields_when_declared():
    """声明非空 → 行尾（括号内）追加 output_fields 清单，planner 从清单选。"""
    spec = CapabilitySpec(
        capability_id="mock_get_issue_status",
        kind="local_fn",
        description="查状态",
        risk_level="low",
        output_fields=("status", "assignee"),
    )
    assert nodes._format_capability_catalog([spec]) == (
        "- mock_get_issue_status：查状态（risk=low；output_fields=[status, assignee]）"
    )


# ---------------------------------------------------------------------------
# 验收 2 · 计划期裁剪：只裁字段、不拒整 plan；全裁空 → 视同空；span 留痕
# ---------------------------------------------------------------------------


def _two_step_plan() -> list[dict]:
    return [
        {
            "id": "t1",
            "type": "tool",
            "tool": "mock_get_issue_status",
            "input": "甲",
            "produces": ["assignee", "bogus"],
        },
        {
            "id": "t2",
            "type": "tool",
            "tool": "mock_get_issue_status",
            "input": "乙",
            "depends_on": ["t1"],
            "consumes": {"t1": ["assignee", "ghost"]},
        },
    ]


def test_issue_plan_trims_undeclared_fields_and_records_trace():
    """声明字段 ∉ output_fields（非空时）→ 裁掉 + trims 留痕；不拒整 plan。"""
    ensure_default_capabilities()
    recorded: list[dict] = []
    with patch.object(nodes, "_record_span_metadata", lambda meta: recorded.append(meta)):
        plan, errors, _seq = nodes._issue_plan(_two_step_plan(), run_id="r", seq=0)
    assert errors == []
    t1, t2 = plan
    assert t1["produces"] == ["assignee"]
    assert t2["consumes_resolved"] == {t1["subtask_id"]: ["assignee"]}
    assert recorded == [
        {
            "capability_output_fields_trimmed": [
                {"subtask_id": t1["subtask_id"], "kind": "produces", "removed": ["bogus"]},
                {
                    "subtask_id": t2["subtask_id"],
                    "kind": "consumes",
                    "dep": t1["subtask_id"],
                    "removed": ["ghost"],
                },
            ]
        }
    ]


def test_issue_plan_all_trimmed_treated_as_empty():
    """某步 / 某前驱声明全被裁空 → 视同空 = 不校验（R1 N4 · 不替模型猜）。"""
    ensure_default_capabilities()
    recorded: list[dict] = []
    with patch.object(nodes, "_record_span_metadata", lambda meta: recorded.append(meta)):
        plan, errors, _seq = nodes._issue_plan(
            [
                {
                    "id": "t1",
                    "type": "tool",
                    "tool": "mock_get_issue_status",
                    "input": "甲",
                    "produces": ["bogus"],
                },
                {
                    "id": "t2",
                    "type": "tool",
                    "tool": "mock_get_issue_status",
                    "input": "乙",
                    "depends_on": ["t1"],
                    "consumes": {"t1": ["ghost"]},
                },
            ],
            run_id="r",
            seq=0,
        )
    assert errors == []
    assert "produces" not in plan[0]
    assert "consumes_resolved" not in plan[1]
    trims = recorded[0]["capability_output_fields_trimmed"]
    assert {t["kind"] for t in trims} == {"produces", "consumes"}


def test_issue_plan_all_declared_fields_pass_zero_diff():
    """声明全在清单内 → 原样通过零 diff、零留痕（验收 2 正向支）。"""
    ensure_default_capabilities()
    recorded: list[dict] = []
    with patch.object(nodes, "_record_span_metadata", lambda meta: recorded.append(meta)):
        plan, errors, _seq = nodes._issue_plan(
            [
                {
                    "id": "t1",
                    "type": "tool",
                    "tool": "mock_get_issue_status",
                    "input": "甲",
                    "produces": ["assignee", "status"],
                },
                {
                    "id": "t2",
                    "type": "tool",
                    "tool": "mock_get_issue_status",
                    "input": "乙",
                    "depends_on": ["t1"],
                    "consumes": {"t1": ["assignee"]},
                },
            ],
            run_id="r",
            seq=0,
        )
    assert errors == []
    assert plan[0]["produces"] == ["assignee", "status"]
    assert plan[1]["consumes_resolved"] == {plan[0]["subtask_id"]: ["assignee"]}
    assert recorded == []


def test_issue_plan_unregistered_tool_no_trim():
    """未注册 / 未声明（空 output_fields）→ 原样放行，零裁剪零留痕。"""
    ensure_default_capabilities()
    recorded: list[dict] = []
    with patch.object(nodes, "_record_span_metadata", lambda meta: recorded.append(meta)):
        plan, errors, _seq = nodes._issue_plan(
            [
                {
                    "id": "t1",
                    "type": "tool",
                    "tool": "unregistered_tool",
                    "input": "甲",
                    "produces": ["whatever"],
                },
                {
                    "id": "t2",
                    "type": "tool",
                    "tool": "unregistered_tool",
                    "input": "乙",
                    "depends_on": ["t1"],
                    "consumes": {"t1": ["whatever"]},
                },
            ],
            run_id="r",
            seq=0,
        )
    assert errors == []
    assert plan[0]["produces"] == ["whatever"]
    t1_sid = plan[0]["subtask_id"]
    assert plan[1]["consumes_resolved"] == {t1_sid: ["whatever"]}
    assert recorded == []


# ---------------------------------------------------------------------------
# 验收 3 · 运行期注册表对拍：spec.output_fields == adapter 实际返回 keys
# ---------------------------------------------------------------------------


async def test_registry_output_fields_align_with_adapter_returns():
    """builtin.v1.yaml 主加载面 + testing.v1.yaml：声明清单与真实返回键集相等。"""
    ensure_default_capabilities()
    load_capability_manifest(_TESTING_MANIFEST)
    registry = get_registry()

    cases = [
        ("mock_get_issue_status", {"issue": "#128"}),
        ("mock_get_deploy_info", {"env": "prod"}),
        ("utc_now_iso", {}),
        ("testing.write.echo", {"request_id": "r-1", "note": "demo"}),
    ]
    for cid, args in cases:
        entry = registry.get(cid)
        assert entry is not None, cid
        spec, adapter = entry
        assert spec.output_fields, f"{cid} 未声明 output_fields"
        out = await adapter.ainvoke(args)
        assert isinstance(out, dict)
        assert set(out.keys()) == set(spec.output_fields), (
            f"{cid}: 声明 {sorted(spec.output_fields)} vs 实际 {sorted(out.keys())}"
        )


@pytest.mark.skipif(not DB_AVAILABLE, reason="PostgreSQL not available")
async def test_lookup_output_fields_align_with_adapter_returns(clean_sync_data):
    """lookup 两枚（tenant_scoped · 走 PG 夹具）：返回键集 == 声明清单。"""
    from datetime import datetime

    from app.db.models import OpsIssue, OpsPullRequest, OpsRepo
    from app.db.session import AsyncSessionLocal

    ensure_default_capabilities()
    now = datetime.utcnow()
    async with AsyncSessionLocal() as db:
        repo = OpsRepo(owner="acme", name="of-align", full_name="acme/of-align")
        db.add(repo)
        await db.flush()
        db.add(
            OpsIssue(
                repo_id=repo.id,
                number=128,
                title="登录闪退",
                body="b",
                state="open",
                labels=["bug"],
                html_url="https://github.com/acme/of-align/issues/128",
                created_at=now,
                updated_at=now,
            )
        )
        db.add(
            OpsPullRequest(
                repo_id=repo.id,
                number=42,
                title="Fix",
                body="p",
                state="open",
                draft=False,
                ci_status="success",
                html_url="https://github.com/acme/of-align/pull/42",
                created_at=now,
                updated_at=now,
            )
        )
        await db.commit()

    registry = get_registry()
    for cid, args in (
        ("get_issue_by_number", "#128"),
        ("get_pr_by_number", "42"),
    ):
        entry = registry.get(cid)
        assert entry is not None, cid
        spec = entry[0]
        assert spec.output_fields, f"{cid} 未声明 output_fields"
        result = await ainvoke(cid, args, ctx=_TENANT_CTX)
        assert result.ok is True
        assert set(result.output.keys()) == set(spec.output_fields), (
            f"{cid}: 声明 {sorted(spec.output_fields)} vs 实际 {sorted(result.output.keys())}"
        )


def test_default_specs_all_declare_output_fields():
    """defaults 硬编码回退面：五枚 _DEFAULT_SPECS 全部声明非空 output_fields。"""
    for spec, _adapter in _DEFAULT_SPECS:
        assert spec.output_fields, f"{spec.capability_id} 回退面未声明 output_fields"
