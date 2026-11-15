"""本库 Issue/PR 只读 lookup（local_fn · 经 Gateway ainvoke）。

从 payload 解析第一个整数（``#128`` / ``128``）；多 repo 同号取 ``updated_at`` 最新。
未命中或无整数 → 抛受控异常，Gateway 变为 ``ok=False``。
输出摘要字段；**禁止** ``raw_payload``；body 截断 500。
"""

from __future__ import annotations

import re
from datetime import datetime
from typing import Any

from sqlalchemy import func, select

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


async def get_issue_by_number(payload: Any, *, ctx: dict[str, Any] | None = None) -> dict[str, Any]:
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


async def get_pr_by_number(payload: Any, *, ctx: dict[str, Any] | None = None) -> dict[str, Any]:
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


# ---------------------------------------------------------------------------
# P2a-T1：面板列表查询（query_issues / query_pull_requests）
#
# 谓词集对齐面板端点（app/ops/issues.py · app/ops/pulls.py），按同谓词重写
# ORM（不复用端点函数）；返回剔 uuid id、不带 body。
# R1：schema_validate 不校验 enum/min/max → page/page_size 边界与 state
# 词表由 adapter 显式把关，违规抛 LookupError（Gateway → ok=False）。
# ---------------------------------------------------------------------------

_PAGE_SIZE_MAX = 20
_ISSUE_STATES = ("open", "closed")
_PR_STATES = ("open", "closed", "merged")


def _parse_page(payload: Any) -> tuple[int, int]:
    """page/page_size 显式校验（R1）：page≥1 · 1≤page_size≤20。"""
    args = payload if isinstance(payload, dict) else {}
    page = args.get("page", 1)
    page_size = args.get("page_size", 10)
    if isinstance(page, bool) or not isinstance(page, int) or page < 1:
        raise LookupError("invalid_page")
    if (
        isinstance(page_size, bool)
        or not isinstance(page_size, int)
        or not 1 <= page_size <= _PAGE_SIZE_MAX
    ):
        raise LookupError("invalid_page_size")
    return page, page_size


def _trim_issue_item(issue: OpsIssue) -> dict[str, Any]:
    """issue 行 → 面板条目（纯函数 · 剔 uuid id / body）。"""
    return {
        "number": issue.number,
        "title": issue.title,
        "state": issue.state,
        "labels": list(issue.labels or []),
        "module_tag": issue.module_tag,
        "updated_at": _iso(issue.updated_at),
    }


def _trim_pr_item(pr: OpsPullRequest) -> dict[str, Any]:
    """PR 行 → 面板条目（纯函数 · 剔 uuid id / body）。"""
    return {
        "number": pr.number,
        "title": pr.title,
        "state": pr.state,
        "draft": pr.draft,
        "ci_status": pr.ci_status,
        "updated_at": _iso(pr.updated_at),
    }


async def query_issues(payload: Any, *, ctx: dict[str, Any] | None = None) -> dict[str, Any]:
    """分页列出本租户 issues（updated_at 倒序）；谓词对齐面板 issues.py。"""
    tenant = _tenant_from_ctx(ctx)
    page, page_size = _parse_page(payload)
    args = payload if isinstance(payload, dict) else {}
    conds: list[Any] = [OpsIssue.tenant_id == tenant]
    state = args.get("state")
    if state:
        if state not in _ISSUE_STATES:
            raise LookupError("invalid_state")
        conds.append(OpsIssue.state == state)
    label = args.get("label")
    if label:
        conds.append(OpsIssue.labels.contains([label]))
    scan_status = args.get("scan_status")
    if scan_status:
        conds.append(OpsIssue.scan_status == scan_status)
    module = args.get("module")
    if module:
        conds.append(OpsIssue.module_tag == module)
    async with AsyncSessionLocal() as session:
        total = (
            await session.execute(select(func.count(OpsIssue.id)).where(*conds))
        ).scalar_one()
        rows = (
            (
                await session.execute(
                    select(OpsIssue)
                    .where(*conds)
                    .order_by(OpsIssue.updated_at.desc())
                    .offset((page - 1) * page_size)
                    .limit(page_size)
                )
            )
            .scalars()
            .all()
        )
    return {
        "items": [_trim_issue_item(row) for row in rows],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


async def query_pull_requests(payload: Any, *, ctx: dict[str, Any] | None = None) -> dict[str, Any]:
    """分页列出本租户 PR 台账（updated_at 倒序）；谓词对齐面板 pulls.py。

    ci_status 词表仓内不可钉（sync 波恒 null · 无生产写入方）→ string
    放行不过滤词表（与面板端点同口径 · 08 §1.3 裁定）。
    """
    tenant = _tenant_from_ctx(ctx)
    page, page_size = _parse_page(payload)
    args = payload if isinstance(payload, dict) else {}
    conds: list[Any] = [OpsPullRequest.tenant_id == tenant]
    state = args.get("state")
    if state:
        if state not in _PR_STATES:
            raise LookupError("invalid_state")
        conds.append(OpsPullRequest.state == state)
    ci_status = args.get("ci_status")
    if ci_status:
        conds.append(OpsPullRequest.ci_status == ci_status)
    async with AsyncSessionLocal() as session:
        total = (
            await session.execute(select(func.count(OpsPullRequest.id)).where(*conds))
        ).scalar_one()
        rows = (
            (
                await session.execute(
                    select(OpsPullRequest)
                    .where(*conds)
                    .order_by(OpsPullRequest.updated_at.desc())
                    .offset((page - 1) * page_size)
                    .limit(page_size)
                )
            )
            .scalars()
            .all()
        )
    return {
        "items": [_trim_pr_item(row) for row in rows],
        "total": total,
        "page": page,
        "page_size": page_size,
    }
