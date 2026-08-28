"""本库 Issue/PR lookup · Gateway ainvoke（夹具 PG · 不连外网）。"""

from __future__ import annotations

from datetime import datetime, timedelta

import pytest

from app.db.models import OpsIssue, OpsPullRequest, OpsRepo
from app.db.session import AsyncSessionLocal
from app.ops.capability import ainvoke, invoke
from app.ops.capability.defaults import (
    mock_get_deploy_info,
    mock_get_issue_status,
    utc_now_iso,
)
from app.ops.lg_rag.multi.nodes import tool_exec_node
from tests.conftest import DB_AVAILABLE


def test_mock_and_utc_now_invoke_regression():
    """utc_now_iso / mock 同步 invoke 不破。"""
    issue = invoke("mock_get_issue_status", "查 #128")
    assert issue.ok is True
    assert issue.output == mock_get_issue_status("查 #128")

    deploy = invoke("mock_get_deploy_info", "prod")
    assert deploy.ok is True
    assert deploy.output == mock_get_deploy_info("prod")

    now = invoke("utc_now_iso", "")
    assert now.ok is True
    assert now.output["tool"] == utc_now_iso("")["tool"]
    assert "utc" in now.output


async def test_ainvoke_utc_now_iso_sync_adapter():
    """ainvoke 对同步 utc_now_iso 兼容（不走 PG）。"""
    result = await ainvoke("utc_now_iso", "")
    assert result.ok is True
    assert result.output["tool"] == "utc_now_iso"
    assert "utc" in result.output


@pytest.mark.skipif(not DB_AVAILABLE, reason="PostgreSQL not available")
async def test_ainvoke_get_issue_by_number_hit(clean_sync_data):
    """夹具写入后 ainvoke 命中摘要字段；无 raw_payload。"""
    now = datetime.utcnow()
    long_body = "B" * 600
    async with AsyncSessionLocal() as db:
        repo = OpsRepo(owner="acme", name="lookup", full_name="acme/lookup-issue")
        db.add(repo)
        await db.flush()
        db.add(
            OpsIssue(
                repo_id=repo.id,
                number=128,
                title="登录闪退",
                body=long_body,
                state="open",
                labels=["bug", "ios"],
                html_url="https://github.com/acme/lookup-issue/issues/128",
                created_at=now,
                updated_at=now,
                raw_payload={"secret": "must-not-leak"},
            )
        )
        await db.commit()

    result = await ainvoke("get_issue_by_number", "#128")
    assert result.ok is True
    out = result.output
    assert out["number"] == 128
    assert out["title"] == "登录闪退"
    assert out["state"] == "open"
    assert out["html_url"] == "https://github.com/acme/lookup-issue/issues/128"
    assert out["labels"] == ["bug", "ios"]
    assert out["updated_at"]
    assert out["body"] == "B" * 500
    assert "raw_payload" not in out


@pytest.mark.skipif(not DB_AVAILABLE, reason="PostgreSQL not available")
async def test_ainvoke_get_pr_by_number_hit(clean_sync_data):
    """get_pr_by_number 对称命中；含 ci_status / draft。"""
    now = datetime.utcnow()
    async with AsyncSessionLocal() as db:
        repo = OpsRepo(owner="acme", name="lookup-pr", full_name="acme/lookup-pr")
        db.add(repo)
        await db.flush()
        db.add(
            OpsPullRequest(
                repo_id=repo.id,
                number=42,
                title="Fix crash",
                body="pr-body",
                state="open",
                draft=True,
                ci_status="pending",
                html_url="https://github.com/acme/lookup-pr/pull/42",
                created_at=now,
                updated_at=now,
                raw_payload={"diff": "nope"},
            )
        )
        await db.commit()

    result = await ainvoke("get_pr_by_number", "42")
    assert result.ok is True
    out = result.output
    assert out["number"] == 42
    assert out["title"] == "Fix crash"
    assert out["state"] == "open"
    assert out["draft"] is True
    assert out["ci_status"] == "pending"
    assert out["html_url"] == "https://github.com/acme/lookup-pr/pull/42"
    assert out["body"] == "pr-body"
    assert "raw_payload" not in out
    assert "labels" not in out


@pytest.mark.skipif(not DB_AVAILABLE, reason="PostgreSQL not available")
async def test_ainvoke_issue_not_found_ok_false(clean_sync_data):
    result = await ainvoke("get_issue_by_number", "#99999")
    assert result.ok is False
    assert "issue_not_found" in (result.error or "")


@pytest.mark.skipif(not DB_AVAILABLE, reason="PostgreSQL not available")
async def test_ainvoke_pr_not_found_ok_false(clean_sync_data):
    result = await ainvoke("get_pr_by_number", "99999")
    assert result.ok is False
    assert "pr_not_found" in (result.error or "")


async def test_ainvoke_missing_number_ok_false():
    result = await ainvoke("get_issue_by_number", "没有编号")
    assert result.ok is False
    assert "missing_number" in (result.error or "")
    pr = await ainvoke("get_pr_by_number", "")
    assert pr.ok is False
    assert "missing_number" in (pr.error or "")


@pytest.mark.skipif(not DB_AVAILABLE, reason="PostgreSQL not available")
async def test_multi_repo_same_number_takes_latest(clean_sync_data):
    """同号多 repo：updated_at 最新一条。"""
    older = datetime.utcnow() - timedelta(days=2)
    newer = datetime.utcnow()
    async with AsyncSessionLocal() as db:
        repo_old = OpsRepo(owner="acme", name="old", full_name="acme/lookup-old")
        repo_new = OpsRepo(owner="acme", name="new", full_name="acme/lookup-new")
        db.add_all([repo_old, repo_new])
        await db.flush()
        db.add(
            OpsIssue(
                repo_id=repo_old.id,
                number=7,
                title="旧仓库",
                state="closed",
                created_at=older,
                updated_at=older,
            )
        )
        db.add(
            OpsIssue(
                repo_id=repo_new.id,
                number=7,
                title="新仓库",
                state="open",
                created_at=newer,
                updated_at=newer,
            )
        )
        await db.commit()

    result = await ainvoke("get_issue_by_number", "7")
    assert result.ok is True
    assert result.output["title"] == "新仓库"
    assert result.output["state"] == "open"


@pytest.mark.skipif(not DB_AVAILABLE, reason="PostgreSQL not available")
async def test_tool_exec_lookup_ainvoke_and_error_continues(clean_sync_data):
    """tool_exec 对 lookup 走 ainvoke；未命中记 error 不中断。"""
    now = datetime.utcnow()
    async with AsyncSessionLocal() as db:
        repo = OpsRepo(owner="acme", name="tool-exec", full_name="acme/lookup-tool-exec")
        db.add(repo)
        await db.flush()
        db.add(
            OpsIssue(
                repo_id=repo.id,
                number=128,
                title="tool-exec-hit",
                state="open",
                created_at=now,
                updated_at=now,
            )
        )
        await db.commit()

    hit = await tool_exec_node(
        {
            "subtasks": [
                {
                    "id": "t1",
                    "type": "tool",
                    "input": "#128",
                    "tool": "get_issue_by_number",
                }
            ],
            "subtask_results": [],
        }
    )
    assert hit["subtask_results"][0]["output"]["title"] == "tool-exec-hit"
    assert "error" not in hit["subtask_results"][0]

    miss = await tool_exec_node(
        {
            "subtasks": [
                {
                    "id": "t2",
                    "type": "tool",
                    "input": "#99999",
                    "tool": "get_issue_by_number",
                }
            ],
            "subtask_results": [],
        }
    )
    assert "issue_not_found" in (miss["subtask_results"][0].get("error") or "")
