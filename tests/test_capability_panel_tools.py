"""P2a-T1：面板列表双工具（query_issues / query_pull_requests）闸矩阵 + 双层范式。

- InMemory 层（CI 恒跑）：adapter 拒绝口径（R1 · page/page_size/state 词表 →
  LookupError → ok=False）、additionalProperties 多余键、tenant_scope_missing
  负样本、委派层默认 off、catalog 总长 ≤6000、span payload tenant_id 实证、
  裁剪纯函数钉死。
- 真 PG 层（_DB_MARK · CI service 真跑）：双租户 seed 跨租户空集、分页
  total/page 正确、state 过滤。
"""

from __future__ import annotations

from datetime import datetime, timedelta
from unittest.mock import patch

import pytest

from app.db.models import OpsIssue, OpsPullRequest, OpsRepo
from app.db.session import AsyncSessionLocal
from app.ops.capability import ainvoke, budget, circuit, invoke, list_capabilities
from app.ops.capability import delegation as dl
from app.ops.capability.defaults import ensure_default_capabilities
from app.ops.capability.gateway import get_registry
from app.ops.capability.lookups import (
    _trim_issue_item,
    _trim_pr_item,
    query_issues,
    query_pull_requests,
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
# 裁剪纯函数（剔 uuid id / body · 形状钉死）
# ---------------------------------------------------------------------------


def test_trim_issue_item_shape():
    issue = OpsIssue(
        repo_id="r1",
        number=128,
        title="登录闪退",
        state="open",
        labels=["bug", "ios"],
        module_tag="chat",
        scan_status="done",
        body="secret-body",
    )
    item = _trim_issue_item(issue)
    assert set(item.keys()) == {
        "number",
        "title",
        "state",
        "labels",
        "module_tag",
        "updated_at",
    }
    assert item["number"] == 128
    assert item["labels"] == ["bug", "ios"]
    assert item["module_tag"] == "chat"
    assert "id" not in item
    assert "body" not in item


def test_trim_pr_item_shape():
    pr = OpsPullRequest(
        repo_id="r1",
        number=42,
        title="Fix crash",
        state="open",
        draft=True,
        ci_status="pending",
        body="secret-body",
    )
    item = _trim_pr_item(pr)
    assert set(item.keys()) == {
        "number",
        "title",
        "state",
        "draft",
        "ci_status",
        "updated_at",
    }
    assert item["draft"] is True
    assert item["ci_status"] == "pending"
    assert "id" not in item
    assert "body" not in item


# ---------------------------------------------------------------------------
# 闸矩阵 · adapter 拒绝口径（R1：schema_validate 不校验 enum/min/max →
# 必须是 adapter 抛 LookupError，而非 args_schema_invalid）
# ---------------------------------------------------------------------------


async def test_adapter_rejects_page_size_zero_and_over_max():
    with pytest.raises(LookupError, match="invalid_page_size"):
        await query_issues({"page_size": 0}, ctx=_TENANT_CTX)
    with pytest.raises(LookupError, match="invalid_page_size"):
        await query_issues({"page_size": 21}, ctx=_TENANT_CTX)
    with pytest.raises(LookupError, match="invalid_page_size"):
        await query_pull_requests({"page_size": 0}, ctx=_TENANT_CTX)
    with pytest.raises(LookupError, match="invalid_page_size"):
        await query_pull_requests({"page_size": 21}, ctx=_TENANT_CTX)


async def test_adapter_rejects_page_below_one():
    with pytest.raises(LookupError, match="invalid_page"):
        await query_issues({"page": 0}, ctx=_TENANT_CTX)
    with pytest.raises(LookupError, match="invalid_page"):
        await query_pull_requests({"page": -1}, ctx=_TENANT_CTX)


async def test_adapter_rejects_state_out_of_vocab():
    with pytest.raises(LookupError, match="invalid_state"):
        await query_issues({"state": "archived"}, ctx=_TENANT_CTX)
    with pytest.raises(LookupError, match="invalid_state"):
        await query_pull_requests({"state": "draft"}, ctx=_TENANT_CTX)


async def test_gateway_page_size_over_max_ok_false():
    """经 Gateway：adapter LookupError → ok=False（图不中断）。"""
    result = await ainvoke("query_issues", {"page_size": 21}, ctx=_TENANT_CTX)
    assert result.ok is False
    assert "invalid_page_size" in (result.error or "")
    result = await ainvoke("query_pull_requests", {"page_size": 0}, ctx=_TENANT_CTX)
    assert result.ok is False
    assert "invalid_page_size" in (result.error or "")


async def test_gateway_state_out_of_vocab_ok_false():
    result = await ainvoke("query_issues", {"state": "archived"}, ctx=_TENANT_CTX)
    assert result.ok is False
    assert "invalid_state" in (result.error or "")
    result = await ainvoke("query_pull_requests", {"state": "wip"}, ctx=_TENANT_CTX)
    assert result.ok is False
    assert "invalid_state" in (result.error or "")


async def test_gateway_additional_properties_rejected():
    """additionalProperties:false 多余键 → args_schema_invalid（schema 层拒）。"""
    result = await ainvoke("query_issues", {"bogus": 1}, ctx=_TENANT_CTX)
    assert result.ok is False
    assert "args_schema_invalid" in (result.error or "")
    result = await ainvoke("query_pull_requests", {"label": "x"}, ctx=_TENANT_CTX)
    assert result.ok is False
    assert "args_schema_invalid" in (result.error or "")


async def test_gateway_tenant_scope_missing_negative_x2():
    """tenant_scoped 双工具缺 ctx 租户谓词 → 拒（负样本×2）。"""
    result = await ainvoke("query_issues", {})
    assert result.ok is False
    assert "tenant_scope_missing" in (result.error or "")
    result = await ainvoke("query_pull_requests", {})
    assert result.ok is False
    assert "tenant_scope_missing" in (result.error or "")


async def test_adapter_tenant_scope_missing_direct():
    with pytest.raises(LookupError, match="tenant_scope_missing"):
        await query_issues({}, ctx=None)
    with pytest.raises(LookupError, match="tenant_scope_missing"):
        await query_pull_requests({}, ctx={"tenant_id": "  "})


def test_delegation_layer_default_off(monkeypatch):
    """委派层默认 off（env 未设 · 复位后；防主仓 .env 污染）。"""
    monkeypatch.delenv(dl.ENV_MODE, raising=False)
    assert dl.delegation_mode() == dl.MODE_OFF


# ---------------------------------------------------------------------------
# catalog 总长断言（≤6000 · 08 §5.5 体积红线）
# ---------------------------------------------------------------------------


def test_capability_catalog_total_length_within_budget():
    from app.ops.lg_rag.multi.nodes import _format_capability_catalog

    get_registry().clear()
    ensure_default_capabilities()
    specs = list_capabilities()
    assert len(specs) == 9
    catalog = _format_capability_catalog(specs)
    assert len(catalog) <= 6000


# ---------------------------------------------------------------------------
# span payload tenant_id 实证（R3）
# ---------------------------------------------------------------------------


def test_span_payload_includes_tenant_id():
    with patch("app.ops.capability.gateway.update_current_span_metadata") as upd:
        invoke("utc_now_iso", "", ctx={"tenant_id": "ops-desk-pilot"})
        meta = upd.call_args[0][0]
        assert meta["tenant_id"] == "ops-desk-pilot"


async def test_span_payload_tenant_id_on_new_tool_reject_path():
    """新工具 adapter 拒绝路径同样带 tenant_id 进 span。"""
    with patch("app.ops.capability.gateway.update_current_span_metadata") as upd:
        result = await ainvoke(
            "query_issues", {"page_size": 21}, ctx={"tenant_id": "ops-desk-pilot"}
        )
        assert result.ok is False
        meta = upd.call_args[0][0]
        assert meta["capability_id"] == "query_issues"
        assert meta["ok"] is False
        assert meta["tenant_id"] == "ops-desk-pilot"


def test_span_payload_tenant_id_none_without_ctx():
    with patch("app.ops.capability.gateway.update_current_span_metadata") as upd:
        invoke("utc_now_iso", "")
        meta = upd.call_args[0][0]
        assert "tenant_id" in meta
        assert meta["tenant_id"] is None


# ---------------------------------------------------------------------------
# 真 PG 层：双租户隔离 + 分页 + 过滤
# ---------------------------------------------------------------------------


async def _seed_issues(*, prefix: str) -> None:
    """A 租户 3 枚（2 open · 1 closed · 递旧 updated_at）+ B 租户 1 枚。"""
    now = datetime.utcnow()
    async with AsyncSessionLocal() as db:
        repo_a = OpsRepo(owner="acme", name=f"{prefix}-a", full_name=f"acme/{prefix}-a")
        repo_b = OpsRepo(owner="acme", name=f"{prefix}-b", full_name=f"acme/{prefix}-b")
        db.add_all([repo_a, repo_b])
        await db.flush()
        for i in range(3):
            db.add(
                OpsIssue(
                    repo_id=repo_a.id,
                    number=700000 + i,
                    title=f"{prefix}-A-{i}",
                    state="open" if i < 2 else "closed",
                    labels=["bug"] if i == 0 else [],
                    module_tag="chat" if i == 0 else "sync",
                    tenant_id=TENANT_A,
                    created_at=now - timedelta(days=i + 1),
                    updated_at=now - timedelta(days=i),
                )
            )
        db.add(
            OpsIssue(
                repo_id=repo_b.id,
                number=700100,
                title=f"{prefix}-B-MARKER",
                state="open",
                tenant_id=TENANT_B,
                created_at=now,
                updated_at=now,
            )
        )
        await db.commit()


async def _seed_prs(*, prefix: str) -> None:
    """A 租户 2 枚（open · merged）+ B 租户 1 枚。"""
    now = datetime.utcnow()
    async with AsyncSessionLocal() as db:
        repo_a = OpsRepo(owner="acme", name=f"{prefix}-pa", full_name=f"acme/{prefix}-pa")
        repo_b = OpsRepo(owner="acme", name=f"{prefix}-pb", full_name=f"acme/{prefix}-pb")
        db.add_all([repo_a, repo_b])
        await db.flush()
        db.add(
            OpsPullRequest(
                repo_id=repo_a.id,
                number=710000,
                title=f"{prefix}-A-open",
                state="open",
                draft=False,
                ci_status="success",
                tenant_id=TENANT_A,
                created_at=now - timedelta(days=1),
                updated_at=now,
            )
        )
        db.add(
            OpsPullRequest(
                repo_id=repo_a.id,
                number=710001,
                title=f"{prefix}-A-merged",
                state="merged",
                draft=False,
                ci_status=None,
                tenant_id=TENANT_A,
                created_at=now - timedelta(days=2),
                updated_at=now - timedelta(days=1),
            )
        )
        db.add(
            OpsPullRequest(
                repo_id=repo_b.id,
                number=710100,
                title=f"{prefix}-B-MARKER",
                state="open",
                tenant_id=TENANT_B,
                created_at=now,
                updated_at=now,
            )
        )
        await db.commit()


@_DB_MARK
async def test_query_issues_cross_tenant_empty(clean_sync_data):
    """A 租户查不到 B 租户行（跨租户空集 · total 只计本租户）。"""
    await _seed_issues(prefix="p2at1xi")
    result = await ainvoke("query_issues", {"state": "open"}, ctx={"tenant_id": TENANT_A})
    assert result.ok is True
    out = result.output
    assert out["total"] == 2
    titles = {item["title"] for item in out["items"]}
    assert "p2at1xi-B-MARKER" not in titles

    denied = await ainvoke(
        "query_issues", {"state": "open"}, ctx={"tenant_id": TENANT_B}
    )
    assert denied.ok is True
    assert denied.output["total"] == 1
    assert denied.output["items"][0]["title"] == "p2at1xi-B-MARKER"

    empty = await ainvoke(
        "query_issues", {"state": "closed"}, ctx={"tenant_id": TENANT_B}
    )
    assert empty.ok is True
    assert empty.output["total"] == 0
    assert empty.output["items"] == []


@_DB_MARK
async def test_query_issues_pagination_total_and_page(clean_sync_data):
    """分页 total/page 正确 · updated_at 倒序。"""
    await _seed_issues(prefix="p2at1pg")
    page1 = await ainvoke(
        "query_issues", {"page": 1, "page_size": 2}, ctx={"tenant_id": TENANT_A}
    )
    assert page1.ok is True
    out1 = page1.output
    assert out1["total"] == 3
    assert out1["page"] == 1
    assert out1["page_size"] == 2
    assert len(out1["items"]) == 2
    assert out1["items"][0]["title"] == "p2at1pg-A-0"

    page2 = await ainvoke(
        "query_issues", {"page": 2, "page_size": 2}, ctx={"tenant_id": TENANT_A}
    )
    assert page2.ok is True
    out2 = page2.output
    assert out2["total"] == 3
    assert out2["page"] == 2
    assert len(out2["items"]) == 1
    assert out2["items"][0]["title"] == "p2at1pg-A-2"


@_DB_MARK
async def test_query_issues_filters_label_and_module(clean_sync_data):
    await _seed_issues(prefix="p2at1fl")
    by_label = await ainvoke(
        "query_issues", {"label": "bug"}, ctx={"tenant_id": TENANT_A}
    )
    assert by_label.ok is True
    assert by_label.output["total"] == 1
    assert by_label.output["items"][0]["title"] == "p2at1fl-A-0"

    by_module = await ainvoke(
        "query_issues", {"module": "sync"}, ctx={"tenant_id": TENANT_A}
    )
    assert by_module.ok is True
    assert by_module.output["total"] == 2

    by_state = await ainvoke(
        "query_issues", {"state": "closed"}, ctx={"tenant_id": TENANT_A}
    )
    assert by_state.ok is True
    assert by_state.output["total"] == 1
    assert by_state.output["items"][0]["state"] == "closed"


@_DB_MARK
async def test_query_pull_requests_cross_tenant_and_filters(clean_sync_data):
    """PR 对称：跨租户空集 + state/ci_status 过滤 + draft/ci_status 字段。"""
    await _seed_prs(prefix="p2at1pr")
    result = await ainvoke(
        "query_pull_requests", {}, ctx={"tenant_id": TENANT_A}
    )
    assert result.ok is True
    out = result.output
    assert out["total"] == 2
    titles = {item["title"] for item in out["items"]}
    assert "p2at1pr-B-MARKER" not in titles
    open_item = next(i for i in out["items"] if i["state"] == "open")
    assert open_item["draft"] is False
    assert open_item["ci_status"] == "success"

    merged = await ainvoke(
        "query_pull_requests", {"state": "merged"}, ctx={"tenant_id": TENANT_A}
    )
    assert merged.ok is True
    assert merged.output["total"] == 1
    assert merged.output["items"][0]["title"] == "p2at1pr-A-merged"

    by_ci = await ainvoke(
        "query_pull_requests", {"ci_status": "success"}, ctx={"tenant_id": TENANT_A}
    )
    assert by_ci.ok is True
    assert by_ci.output["total"] == 1

    other = await ainvoke(
        "query_pull_requests", {}, ctx={"tenant_id": TENANT_B}
    )
    assert other.ok is True
    assert other.output["total"] == 1
    assert other.output["items"][0]["title"] == "p2at1pr-B-MARKER"
