"""P2a-T2：面板聚合双工具（get_overview / graph_snapshot）双层范式。

- InMemory 层（CI 恒跑）：manifest 全字段钉死（tags/output_schema/nullable
  逐键声明/additionalProperties:false/禁 per-prop description/禁「实时」）、
  tenant_scope_missing 负样本（get_overview）、graph_snapshot view 词表
  adapter 把关（R1：schema_validate 不校验 enum → LookupError → ok=False）、
  截断/过滤纯函数单测（_clip_parsed_summary / _truncate_graph_payload /
  _truncate_json_value / _filter_payload_by_module）。
- 真 PG 层（_DB_MARK · CI service 真跑）：双租户 seed 派生指标隔离 +
  全局段（sync_run/scan_snapshot）跨租户同值、空数据 null 逐键实证、
  parsed_summary >2000 截断标志、graph 三视图与截断标志、
  module 过滤命中与 fail-visible（warning=module_filter_no_match）、
  graph 无 ctx 放行（tenant_scoped:false）。
"""

from __future__ import annotations

from datetime import datetime, timedelta

import pytest

from app.db.models import (
    OpsGraphSnapshot,
    OpsIssue,
    OpsPullRequest,
    OpsRepo,
    OpsScanSnapshot,
    OpsSyncRun,
)
from app.db.session import AsyncSessionLocal
from app.ops.capability import ainvoke, budget, circuit, list_capabilities
from app.ops.capability import delegation as dl
from app.ops.capability.defaults import ensure_default_capabilities
from app.ops.capability.gateway import get_registry
from app.ops.capability.lookups import (
    MODULE_FILTER_NO_MATCH,
    _clip_parsed_summary,
    _filter_payload_by_module,
    _truncate_graph_payload,
    _truncate_json_value,
    get_overview,
    graph_snapshot,
)
from app.ops.capability.manifest import (
    BUILTIN_MANIFEST_PATH,
    load_capability_manifest,
)
from app.ops.tenant_context import TENANT_A, TENANT_B
from tests.conftest import DB_AVAILABLE

_DB_MARK = pytest.mark.skipif(not DB_AVAILABLE, reason="需要 PostgreSQL（opsdesk_test）")

_TENANT_CTX = {"tenant_id": "ops-desk-pilot"}


@pytest.fixture(autouse=True)
def _restore():
    """进程全局态每用例复位（budget/circuit/委派）+ 注册表回默认面。"""
    budget.reset()
    circuit.reset()
    dl.reset_delegation_state()
    ensure_default_capabilities()
    yield
    budget.reset()
    circuit.reset()
    dl.reset_delegation_state()
    get_registry().clear()
    ensure_default_capabilities()


# ---------------------------------------------------------------------------
# manifest 全字段钉死（builtin.v1.yaml ↔ defaults.py 回退面对齐由
# test_capability_manifest.py::test_builtin_yaml_aligns_with_default_specs 守）
# ---------------------------------------------------------------------------


def test_builtin_panel_aggregate_tools_full_fields():
    """P2a-T2：get_overview / graph_snapshot 全字段钉死（§1.4/§1.5/§1.6）。"""
    get_registry().clear()
    load_capability_manifest(BUILTIN_MANIFEST_PATH)
    by_id = {s.capability_id: s for s in list_capabilities()}

    overview = by_id["get_overview"]
    assert overview.kind == "local_fn"
    assert overview.tags == ("panel", "overview", "readonly")
    assert overview.risk_level == "low"
    assert overview.side_effect == "read"
    assert overview.enabled is True
    assert overview.tenant_scoped is True
    assert overview.when_to_use
    assert overview.when_not_to_use == ""
    assert "实时" not in overview.description
    assert overview.output_fields == (
        "cycle_time",
        "review_time",
        "issue_throughput",
        "as_of",
        "sync_status",
        "sync_run",
        "scan_snapshot",
        "trend",
    )
    # 空数据 null 逐键声明（§1.4）
    assert overview.output_schema == {
        "required": [
            "$.cycle_time",
            "$.review_time",
            "$.issue_throughput",
            "$.as_of",
            "$.sync_status",
            "$.trend",
        ],
        "nullable": [
            "$.cycle_time.median_days",
            "$.review_time.median_days",
            "$.sync_run",
            "$.scan_snapshot",
        ],
    }
    # 无参数：空 properties + additionalProperties:false
    assert overview.args_schema == {
        "type": "object",
        "properties": {},
        "additionalProperties": False,
    }

    graph = by_id["graph_snapshot"]
    assert graph.kind == "local_fn"
    assert graph.tags == ("panel", "graph", "readonly")
    assert graph.risk_level == "low"
    assert graph.side_effect == "read"
    assert graph.enabled is True
    assert graph.tenant_scoped is False
    assert graph.when_to_use
    assert graph.when_not_to_use == ""
    assert "实时" not in graph.description
    assert graph.output_fields == (
        "view",
        "scope",
        "repo_id",
        "created_at",
        "summary",
        "module_matrix",
        "payload",
        "truncated",
        "warning",
    )
    assert graph.output_schema == {
        "required": ["$.view", "$.scope", "$.truncated"],
        "nullable": [
            "$.repo_id",
            "$.created_at",
            "$.summary",
            "$.module_matrix",
            "$.payload",
            "$.warning",
        ],
    }
    assert graph.args_schema == {
        "type": "object",
        "properties": {
            "view": {"type": "string", "enum": ["summary", "modules", "full"]},
            "module": {"type": "string"},
        },
        "additionalProperties": False,
    }

    # catalog 体积红线前提：新条目 args_schema 禁 per-prop description
    for spec in (overview, graph):
        for prop in spec.args_schema["properties"].values():
            assert "description" not in prop


# ---------------------------------------------------------------------------
# 闸矩阵 · adapter 拒绝口径 + tenant 负样本（InMemory）
# ---------------------------------------------------------------------------


async def test_gateway_get_overview_tenant_scope_missing_negative():
    """tenant_scoped:get_overview 缺 ctx 租户谓词 → 拒（负样本）。"""
    result = await ainvoke("get_overview", {})
    assert result.ok is False
    assert "tenant_scope_missing" in (result.error or "")


async def test_adapter_get_overview_tenant_scope_missing_direct():
    with pytest.raises(LookupError, match="tenant_scope_missing"):
        await get_overview({}, ctx=None)
    with pytest.raises(LookupError, match="tenant_scope_missing"):
        await get_overview({}, ctx={"tenant_id": "  "})


async def test_gateway_get_overview_additional_properties_rejected():
    """无参数工具：additionalProperties:false 多余键 → args_schema_invalid。"""
    result = await ainvoke("get_overview", {"bogus": 1}, ctx=_TENANT_CTX)
    assert result.ok is False
    assert "args_schema_invalid" in (result.error or "")


async def test_adapter_graph_snapshot_invalid_view_direct():
    """view 词表外 → adapter 抛 LookupError（先于 DB 触达 · InMemory 可跑）。"""
    with pytest.raises(LookupError, match="invalid_view"):
        await graph_snapshot({"view": "bogus"})
    with pytest.raises(LookupError, match="invalid_view"):
        await graph_snapshot({"view": "FULL"})


async def test_gateway_graph_snapshot_invalid_view_ok_false():
    result = await ainvoke("graph_snapshot", {"view": "bogus"})
    assert result.ok is False
    assert "invalid_view" in (result.error or "")


async def test_gateway_graph_snapshot_additional_properties_rejected():
    result = await ainvoke("graph_snapshot", {"bogus": 1})
    assert result.ok is False
    assert "args_schema_invalid" in (result.error or "")


# ---------------------------------------------------------------------------
# 截断 / 过滤纯函数单测（InMemory 恒跑）
# ---------------------------------------------------------------------------


def test_clip_parsed_summary_under_limit_passthrough():
    small = {"health": "ok", "counts": {"issues": 3}}
    assert _clip_parsed_summary(small) == small


def test_clip_parsed_summary_over_limit_keys_truncated():
    big = {"summary": "x" * 3000, "zz_top": 1, "alpha": 2}
    clipped = _clip_parsed_summary(big)
    assert clipped == {"keys": ["alpha", "summary", "zz_top"], "truncated": True}


def test_truncate_json_value_over_and_under_limit():
    small = {"a": 1}
    out, truncated = _truncate_json_value(small, 8000)
    assert out == small
    assert truncated is False

    big = {"b_key": "y" * 9000, "a_key": 1}
    out, truncated = _truncate_json_value(big, 8000)
    assert out == {"keys": ["a_key", "b_key"], "truncated": True}
    assert truncated is True


def test_truncate_graph_payload_nodes_then_edges_order():
    """超限：先裁 nodes 再裁 edges；附原始 totals；truncated=True。"""
    nodes = [
        {"id": f"n{i}", "module": f"m{i % 5}", "label": "x" * 80} for i in range(300)
    ]
    edges = [{"source": "n0", "target": "n1"}]
    payload = {"nodes": nodes, "edges": edges, "modules": ["m0", "m1"]}
    out, truncated = _truncate_graph_payload(payload, 12000)
    assert truncated is True
    assert out["totals"] == {"nodes": 300, "edges": 1, "modules": 2}
    # nodes→edges 顺序：nodes 裁减后已达标 → edges 原样保留
    assert len(out["nodes"]) < 300
    assert out["edges"] == edges
    assert out["modules"] == ["m0", "m1"]


def test_truncate_graph_payload_under_limit_passthrough_no_totals():
    payload = {"nodes": [{"id": "n0"}], "edges": []}
    out, truncated = _truncate_graph_payload(payload, 4000)
    assert out == payload
    assert truncated is False
    assert "totals" not in out


def test_truncate_graph_payload_edges_trimmed_after_nodes_exhausted():
    """nodes 裁空仍超限 → 继续裁 edges（顺序实证）。"""
    nodes = [{"id": "n0", "label": "x" * 100}]
    edges = [{"source": "n0", "target": "n1", "label": "e" * 2000} for _ in range(5)]
    payload = {"nodes": nodes, "edges": edges}
    out, truncated = _truncate_graph_payload(payload, 1200)
    assert truncated is True
    assert out["nodes"] == []
    assert len(out["edges"]) < 5
    assert out["totals"] == {"nodes": 1, "edges": 5, "modules": 0}


def test_filter_payload_by_module_match_keeps_internal_edges():
    payload = {
        "nodes": [
            {"id": "a", "module": "chat"},
            {"id": "b", "module": "sync"},
            {"id": "c", "module": "chat"},
        ],
        "edges": [
            {"source": "a", "target": "c"},
            {"source": "a", "target": "b"},
            {"from": "c", "to": "a"},
        ],
    }
    out, warning = _filter_payload_by_module(payload, "chat")
    assert warning is None
    assert [n["id"] for n in out["nodes"]] == ["a", "c"]
    # 双端均在 kept 集才保留（source/target 与 from/to 两种键形）
    assert len(out["edges"]) == 2


def test_filter_payload_by_module_structural_drift_warns_not_empty():
    """fail-visible：node 缺 module 键 / nodes 非 list → warning + 原样返回。"""
    drift = {"nodes": [{"id": "a"}], "edges": []}
    out, warning = _filter_payload_by_module(drift, "chat")
    assert warning == MODULE_FILTER_NO_MATCH
    assert out == drift

    not_list = {"nodes": "oops", "edges": []}
    out, warning = _filter_payload_by_module(not_list, "chat")
    assert warning == MODULE_FILTER_NO_MATCH
    assert out == not_list


# ---------------------------------------------------------------------------
# 真 PG 层：双租户 seed · 全局口径同值 · 空数据 null · 截断/过滤标志
# ---------------------------------------------------------------------------


async def _seed_overview(*, prefix: str) -> None:
    """repo_a：sync_run + scan_snapshot（全局段）+ A 租户 issue/PR + B 租户两枚 closed。"""
    now = datetime.utcnow()
    async with AsyncSessionLocal() as db:
        repo = OpsRepo(owner="acme", name=f"{prefix}-r", full_name=f"acme/{prefix}-r")
        db.add(repo)
        await db.flush()
        db.add(
            OpsSyncRun(
                repo_id=repo.id,
                sync_type="full",
                status="success",
                started_at=now - timedelta(hours=2),
                finished_at=now - timedelta(hours=1),
                summary={"issues": 11, "pulls": 7},
            )
        )
        db.add(
            OpsScanSnapshot(
                repo_id=repo.id,
                parsed_summary={"health": "ok", "open_issues": 3},
                created_at=now - timedelta(minutes=30),
            )
        )
        # A 租户：1 closed issue（昨天）+ 1 merged PR（created-3d/merged-1d/review-2d）
        db.add(
            OpsIssue(
                repo_id=repo.id,
                number=720000,
                title=f"{prefix}-A-closed",
                state="closed",
                tenant_id=TENANT_A,
                created_at=now - timedelta(days=5),
                updated_at=now - timedelta(days=1),
                closed_at=now - timedelta(days=1),
            )
        )
        db.add(
            OpsIssue(
                repo_id=repo.id,
                number=720001,
                title=f"{prefix}-A-open",
                state="open",
                tenant_id=TENANT_A,
                created_at=now - timedelta(days=2),
                updated_at=now,
            )
        )
        db.add(
            OpsPullRequest(
                repo_id=repo.id,
                number=721000,
                title=f"{prefix}-A-merged",
                state="merged",
                tenant_id=TENANT_A,
                created_at=now - timedelta(days=3),
                updated_at=now - timedelta(days=1),
                merged_at=now - timedelta(days=1),
                first_review_at=now - timedelta(days=2),
            )
        )
        # B 租户：2 closed issues（吞吐与 A 拉开）
        for i in range(2):
            db.add(
                OpsIssue(
                    repo_id=repo.id,
                    number=720100 + i,
                    title=f"{prefix}-B-closed-{i}",
                    state="closed",
                    tenant_id=TENANT_B,
                    created_at=now - timedelta(days=4),
                    updated_at=now - timedelta(days=1),
                    closed_at=now - timedelta(days=1),
                )
            )
        await db.commit()


@_DB_MARK
async def test_get_overview_empty_db_null_declarations(clean_sync_data):
    """空数据：null 逐键实证（sync_status=idle · sync_run/scan_snapshot=None ·
    median_days=None · trend 30 天零填 · as_of 必带）。"""
    result = await ainvoke("get_overview", {}, ctx={"tenant_id": TENANT_A})
    assert result.ok is True
    out = result.output
    assert out["sync_status"] == "idle"
    assert out["sync_run"] is None
    assert out["scan_snapshot"] is None
    assert out["cycle_time"] == {"median_days": None, "sample_size": 0}
    assert out["review_time"] == {"median_days": None, "sample_size": 0}
    assert out["issue_throughput"] == {"count": 0, "period_days": 30}
    assert isinstance(out["as_of"], str) and out["as_of"].endswith("Z")
    assert len(out["trend"]) == 30
    assert all(
        set(day.keys()) == {"date", "closed_issues", "merged_prs"} for day in out["trend"]
    )
    assert sum(day["closed_issues"] for day in out["trend"]) == 0


@_DB_MARK
async def test_get_overview_tenant_metrics_and_global_sections(clean_sync_data):
    """双租户：派生指标各自隔离 · 全局段（sync_run/scan_snapshot）跨租户同值。"""
    await _seed_overview(prefix="p2at2ov")
    res_a = await ainvoke("get_overview", {}, ctx={"tenant_id": TENANT_A})
    res_b = await ainvoke("get_overview", {}, ctx={"tenant_id": TENANT_B})
    assert res_a.ok is True and res_b.ok is True
    out_a, out_b = res_a.output, res_b.output

    # 派生指标隔离
    assert out_a["issue_throughput"]["count"] == 1
    assert out_b["issue_throughput"]["count"] == 2
    assert out_a["cycle_time"] == {"median_days": 2.0, "sample_size": 1}
    assert out_a["review_time"] == {"median_days": 1.0, "sample_size": 1}
    assert out_b["cycle_time"] == {"median_days": None, "sample_size": 0}

    # 全局段同值（无租户列 · W-fix-2 F13 口径）
    assert out_a["sync_status"] == "success" == out_b["sync_status"]
    assert out_a["sync_run"] == out_b["sync_run"]
    assert out_a["sync_run"]["records_issue"] == 11
    assert out_a["sync_run"]["records_pr"] == 7
    assert out_a["scan_snapshot"] == out_b["scan_snapshot"]
    assert out_a["scan_snapshot"]["parsed_summary"] == {
        "health": "ok",
        "open_issues": 3,
    }

    # trend：昨天 1 closed / 1 merged（A 口径）
    yesterday = (datetime.utcnow() - timedelta(days=1)).date().isoformat()
    day = next(d for d in out_a["trend"] if d["date"] == yesterday)
    assert day["closed_issues"] == 1
    assert day["merged_prs"] == 1


@_DB_MARK
async def test_get_overview_scan_summary_clip_over_limit(clean_sync_data):
    """parsed_summary 序列化 >2000 字符 → {keys,truncated:true}（§1.4）。"""
    now = datetime.utcnow()
    async with AsyncSessionLocal() as db:
        repo = OpsRepo(owner="acme", name="p2at2clip-r", full_name="acme/p2at2clip-r")
        db.add(repo)
        await db.flush()
        db.add(
            OpsScanSnapshot(
                repo_id=repo.id,
                parsed_summary={"b_key": "x" * 3000, "a_key": 1},
                created_at=now,
            )
        )
        await db.commit()
    result = await ainvoke("get_overview", {}, ctx={"tenant_id": TENANT_A})
    assert result.ok is True
    parsed = result.output["scan_snapshot"]["parsed_summary"]
    assert parsed == {"keys": ["a_key", "b_key"], "truncated": True}


async def _seed_graph(
    *, prefix: str, payload: dict, module_matrix: dict | None = None
) -> None:
    async with AsyncSessionLocal() as db:
        repo = OpsRepo(owner="acme", name=f"{prefix}-r", full_name=f"acme/{prefix}-r")
        db.add(repo)
        await db.flush()
        db.add(
            OpsGraphSnapshot(
                repo_id=repo.id,
                payload=payload,
                module_matrix=module_matrix,
                created_at=datetime.utcnow(),
            )
        )
        await db.commit()


@_DB_MARK
async def test_graph_snapshot_no_ctx_allowed_and_empty_shell(clean_sync_data):
    """tenant_scoped:false：无 ctx 放行；无快照行 → null 外壳 + truncated=False。"""
    result = await ainvoke("graph_snapshot", {})
    assert result.ok is True
    out = result.output
    assert out["view"] == "summary"
    assert out["scope"] == "global_repo"
    assert out["repo_id"] is None
    assert out["created_at"] is None
    assert out["summary"] is None
    assert out["module_matrix"] is None
    assert out["payload"] is None
    assert out["truncated"] is False
    assert out["warning"] is None


@_DB_MARK
async def test_graph_snapshot_summary_view_counts(clean_sync_data):
    payload = {
        "nodes": [
            {"id": "a", "module": "chat"},
            {"id": "b", "module": "sync"},
        ],
        "edges": [{"source": "a", "target": "b"}],
        "modules": ["chat", "sync"],
    }
    await _seed_graph(prefix="p2at2gs", payload=payload, module_matrix={"chat": {"open": 1}})
    result = await ainvoke("graph_snapshot", {"view": "summary"})
    assert result.ok is True
    out = result.output
    assert out["scope"] == "global_repo"
    assert out["repo_id"]
    assert out["created_at"]
    assert out["summary"] == {"node_count": 2, "edge_count": 1, "module_count": 2}
    assert out["module_matrix"] is None
    assert out["payload"] is None
    assert out["truncated"] is False
    assert out["warning"] is None


@_DB_MARK
async def test_graph_snapshot_modules_view_truncation(clean_sync_data):
    """module_matrix 超 8000 → {keys,truncated:true} + truncated=True（§1.6）。"""
    big_matrix = {f"mod{i:03d}": {"detail": "y" * 100} for i in range(100)}
    await _seed_graph(
        prefix="p2at2gm", payload={"nodes": [], "edges": []}, module_matrix=big_matrix
    )
    result = await ainvoke("graph_snapshot", {"view": "modules"})
    assert result.ok is True
    out = result.output
    assert out["truncated"] is True
    assert out["module_matrix"]["truncated"] is True
    assert sorted(out["module_matrix"]["keys"]) == sorted(big_matrix.keys())
    assert out["payload"] is None


@_DB_MARK
async def test_graph_snapshot_full_view_payload_truncation(clean_sync_data):
    """full 视图：payload 超 12000 → nodes 顺序截断 + totals + truncated=True。"""
    nodes = [
        {"id": f"n{i}", "module": f"m{i % 5}", "label": "x" * 80} for i in range(300)
    ]
    payload = {"nodes": nodes, "edges": [{"source": "n0", "target": "n1"}]}
    await _seed_graph(prefix="p2at2gf", payload=payload)
    result = await ainvoke("graph_snapshot", {"view": "full"})
    assert result.ok is True
    out = result.output
    assert out["truncated"] is True
    assert out["payload"]["totals"] == {"nodes": 300, "edges": 1, "modules": 0}
    assert len(out["payload"]["nodes"]) < 300
    assert out["payload"]["edges"] == [{"source": "n0", "target": "n1"}]


@_DB_MARK
async def test_graph_snapshot_module_filter_match(clean_sync_data):
    """过滤优先于截断：module 命中 → summary 计过滤后子图 · warning=None。"""
    payload = {
        "nodes": [
            {"id": "a", "module": "chat"},
            {"id": "b", "module": "sync"},
            {"id": "c", "module": "chat"},
        ],
        "edges": [
            {"source": "a", "target": "c"},
            {"source": "a", "target": "b"},
        ],
    }
    await _seed_graph(prefix="p2at2mf", payload=payload)
    result = await ainvoke("graph_snapshot", {"module": "chat"})
    assert result.ok is True
    out = result.output
    assert out["summary"]["node_count"] == 2
    assert out["summary"]["edge_count"] == 1
    assert out["warning"] is None


@_DB_MARK
async def test_graph_snapshot_module_filter_no_match_warns(clean_sync_data):
    """fail-visible 实证：node 缺 module 键 → warning=module_filter_no_match +
    未过滤摘要（不静默空集）。"""
    payload = {
        "nodes": [{"id": "a"}, {"id": "b"}],
        "edges": [{"source": "a", "target": "b"}],
    }
    await _seed_graph(prefix="p2at2mn", payload=payload)
    result = await ainvoke("graph_snapshot", {"module": "chat"})
    assert result.ok is True
    out = result.output
    assert out["warning"] == "module_filter_no_match"
    # 未过滤摘要照常返回
    assert out["summary"]["node_count"] == 2
    assert out["summary"]["edge_count"] == 1
