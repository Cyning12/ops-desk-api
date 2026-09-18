"""本库 Issue/PR 只读 lookup（local_fn · 经 Gateway ainvoke）。

从 payload 解析第一个整数（``#128`` / ``128``）；多 repo 同号取 ``updated_at`` 最新。
未命中或无整数 → 抛受控异常，Gateway 变为 ``ok=False``。
输出摘要字段；**禁止** ``raw_payload``；body 截断 500。
"""

from __future__ import annotations

import re
from datetime import datetime
from typing import Any

from sqlalchemy import select

from app.db.models import OpsIssue, OpsPullRequest
from app.db.session import AsyncSessionLocal

_FIRST_INT = re.compile(r"\d+")
_BODY_LIMIT = 500


def _payload_text(payload: Any) -> str:
    if payload is None:
        return ""
    if isinstance(payload, bool):
        return str(payload)
    if isinstance(payload, int):
        return str(payload)
    if isinstance(payload, float) and payload.is_integer():
        return str(int(payload))
    return str(payload)


def _parse_first_int(payload: Any) -> int:
    """解析 payload 中第一个整数；失败则 ValueError（Gateway → ok=False）。"""
    text = _payload_text(payload)
    match = _FIRST_INT.search(text)
    if match is None:
        raise ValueError("missing_number: payload 需包含 issue/PR 号（如 #128）")
    return int(match.group(0))


def _clip_body(body: str | None) -> str | None:
    if body is None:
        return None
    if len(body) <= _BODY_LIMIT:
        return body
    return body[:_BODY_LIMIT]


def _iso(dt: datetime | None) -> str | None:
    if dt is None:
        return None
    return dt.isoformat()


def _tenant_from_ctx(ctx: dict[str, Any] | None) -> str:
    """租户谓词；缺则拒（与 Policy tenant_scoped 对齐）。"""
    if not ctx:
        raise LookupError("tenant_scope_missing")
    raw = ctx.get("tenant_id") or ctx.get("_host_tenant")
    tenant = str(raw or "").strip()
    if not tenant:
        raise LookupError("tenant_scope_missing")
    return tenant


async def get_issue_by_number(
    payload: Any, *, ctx: dict[str, Any] | None = None
) -> dict[str, Any]:
    """按 number + tenant_id 查本库 Issue；跨租户未命中 → LookupError(issue_not_found)。"""
    number = _parse_first_int(payload)
    tenant = _tenant_from_ctx(ctx)
    async with AsyncSessionLocal() as session:
        stmt = (
            select(OpsIssue)
            .where(OpsIssue.number == number, OpsIssue.tenant_id == tenant)
            .order_by(OpsIssue.updated_at.desc())
            .limit(1)
        )
        issue = (await session.execute(stmt)).scalar_one_or_none()
    if issue is None:
        raise LookupError("issue_not_found")
    return {
        "number": issue.number,
        "title": issue.title,
        "state": issue.state,
        "html_url": issue.html_url,
        "updated_at": _iso(issue.updated_at),
        "labels": list(issue.labels or []),
        "body": _clip_body(issue.body),
    }


async def get_pr_by_number(
    payload: Any, *, ctx: dict[str, Any] | None = None
) -> dict[str, Any]:
    """按 number + tenant_id 查本库 PR；跨租户未命中 → LookupError(pr_not_found)。"""
    number = _parse_first_int(payload)
    tenant = _tenant_from_ctx(ctx)
    async with AsyncSessionLocal() as session:
        stmt = (
            select(OpsPullRequest)
            .where(OpsPullRequest.number == number, OpsPullRequest.tenant_id == tenant)
            .order_by(OpsPullRequest.updated_at.desc())
            .limit(1)
        )
        pr = (await session.execute(stmt)).scalar_one_or_none()
    if pr is None:
        raise LookupError("pr_not_found")
    return {
        "number": pr.number,
        "title": pr.title,
        "state": pr.state,
        "html_url": pr.html_url,
        "updated_at": _iso(pr.updated_at),
        "ci_status": pr.ci_status,
        "draft": pr.draft,
        "body": _clip_body(pr.body),
    }
