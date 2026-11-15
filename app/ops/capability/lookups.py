"""本库 Issue/PR 只读 lookup（local_fn · 经 Gateway ainvoke）。

从 payload 解析第一个整数（``#128`` / ``128``）；多 repo 同号取 ``updated_at`` 最新。
未命中或无整数 → 抛受控异常，Gateway 变为 ``ok=False``。
输出摘要字段；**禁止** ``raw_payload``；body 截断 500。
"""

from __future__ import annotations

import json
import re
from datetime import datetime, timedelta, timezone
from statistics import median
from typing import Any

from sqlalchemy import func, select

from app.db.models import (
    OpsGraphSnapshot,
    OpsIssue,
    OpsPullRequest,
    OpsScanSnapshot,
    OpsSyncRun,
)
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


# ---------------------------------------------------------------------------
# P2a-T2：面板聚合查询（get_overview / graph_snapshot）
#
# 口径逐键对齐面板端点（app/ops/overview.py:169-180 · app/ops/graph.py），
# 按同谓词重写 ORM（不复用端点函数 · 不引入 capability→api 跨模块边；
# 聚合纯函数镜像 overview.py 同名逻辑）。
# R1：schema_validate 不校验 enum → graph_snapshot 的 view 词表由 adapter
# 显式把关，违规抛 LookupError（Gateway → ok=False）。
# ---------------------------------------------------------------------------

# 窗口常量镜像 app/ops/overview.py（:27-29 · 改动须双处同步）
_CYCLE_REVIEW_WINDOW_DAYS = 90
_TREND_WINDOW_DAYS = 30
# §1.4：scan_snapshot.parsed_summary 序列化超过此长度截断为 {keys,truncated:true}
_PARSED_SUMMARY_LIMIT = 2000
# §1.6：graph_snapshot 视图上限（字符）
_GRAPH_VIEW_LIMITS = {"summary": 4000, "modules": 8000, "full": 12000}
_GRAPH_VIEWS = ("summary", "modules", "full")
MODULE_FILTER_NO_MATCH = "module_filter_no_match"


def _to_naive_utc(value: datetime) -> datetime:
    """aware datetime → naive UTC（镜像 app/ops/admin/service.py:21 同名逻辑）。"""
    if value.tzinfo is None:
        return value
    return value.astimezone(timezone.utc).replace(tzinfo=None)  # noqa: UP017


def _median_days(pairs: list[tuple]) -> dict:
    """(end - start) 天数中位数（镜像 overview.py:32-48 · naive UTC 归一）。"""
    days = []
    for start, end in pairs:
        if start is None or end is None:
            continue
        start = _to_naive_utc(start)
        end = _to_naive_utc(end)
        if end >= start:
            days.append((end - start).total_seconds() / 86400)
    if not days:
        return {"median_days": None, "sample_size": 0}
    return {"median_days": round(median(days), 2), "sample_size": len(days)}


def _build_trend(issue_counts: dict, pr_counts: dict, today: datetime) -> list[dict]:
    """30 天零填 trend（镜像 overview.py:51-64 · 含今天）。"""
    start = (today - timedelta(days=_TREND_WINDOW_DAYS - 1)).date()
    trend = []
    for offset in range(_TREND_WINDOW_DAYS):
        day = start + timedelta(days=offset)
        trend.append(
            {
                "date": day.isoformat(),
                "closed_issues": issue_counts.get(day, 0),
                "merged_prs": pr_counts.get(day, 0),
            }
        )
    return trend


def _json_len(value: Any) -> int:
    """JSON 序列化字符数（ensure_ascii=False · 非序列化值 default=str 兜底）。"""
    return len(json.dumps(value, ensure_ascii=False, default=str))


def _clip_parsed_summary(parsed: Any) -> dict:
    """§1.4：parsed_summary 序列化 >2000 字符 → {keys,truncated:true}（纯函数）。"""
    if _json_len(parsed) <= _PARSED_SUMMARY_LIMIT:
        return parsed
    keys = sorted(parsed.keys()) if isinstance(parsed, dict) else []
    return {"keys": keys, "truncated": True}


def _graph_totals(payload: dict) -> dict:
    """nodes/edges/modules 原始计数（截断后随 truncated:true 一并返回）。"""
    nodes = payload.get("nodes")
    edges = payload.get("edges")
    modules = payload.get("modules")
    return {
        "nodes": len(nodes) if isinstance(nodes, list) else 0,
        "edges": len(edges) if isinstance(edges, list) else 0,
        "modules": len(modules) if isinstance(modules, list | dict) else 0,
    }


def _truncate_graph_payload(payload: dict, limit: int) -> tuple[dict, bool]:
    """按 nodes→edges 顺序截断至序列化 ≤limit（纯函数 · §1.5/§1.6）。

    超限：先裁 nodes 再裁 edges，附原始 totals；极端情况（空 nodes/edges
    仍超限）退化为仅 totals。未超限原样返回（不附 totals）。
    """
    if _json_len(payload) <= limit:
        return payload, False
    totals = _graph_totals(payload)
    out = dict(payload)
    for key in ("nodes", "edges"):
        value = out.get(key)
        if not isinstance(value, list):
            continue
        keep = len(value)
        while keep > 0 and _json_len({**out, "totals": totals}) > limit:
            keep -= 1
            out[key] = value[:keep]
    out["totals"] = totals
    if _json_len(out) > limit:
        out = {"totals": totals}
    return out, True


def _truncate_json_value(value: Any, limit: int) -> tuple[Any, bool]:
    """通用 JSON 值截断（module_matrix 用 · 纯函数）：超限 → {keys,truncated:true}。"""
    if _json_len(value) <= limit:
        return value, False
    keys = sorted(value.keys()) if isinstance(value, dict) else []
    return {"keys": keys, "truncated": True}, True


def _filter_payload_by_module(payload: dict, module: str) -> tuple[dict, str | None]:
    """module 过滤子图（纯函数 · 过滤优先于截断 · §1.5 fail-visible）。

    结构前提：payload["nodes"]/["edges"] 为 list 且每个 node 为含 module 键
    的 dict（kimi-code 外部结构）。键缺失/结构漂移 →
    (原 payload, "module_filter_no_match")，不静默空集。
    """
    nodes = payload.get("nodes")
    edges = payload.get("edges")
    if not isinstance(nodes, list) or not isinstance(edges, list):
        return payload, MODULE_FILTER_NO_MATCH
    if not all(isinstance(n, dict) and "module" in n for n in nodes):
        return payload, MODULE_FILTER_NO_MATCH
    kept = [n for n in nodes if n.get("module") == module]
    kept_ids = {n.get("id") for n in kept}

    def _edge_kept(edge: Any) -> bool:
        if not isinstance(edge, dict):
            return False
        src = edge.get("source", edge.get("from"))
        dst = edge.get("target", edge.get("to"))
        return src in kept_ids and dst in kept_ids

    out = dict(payload)
    out["nodes"] = kept
    out["edges"] = [e for e in edges if _edge_kept(e)]
    return out, None


async def get_overview(payload: Any, *, ctx: dict[str, Any] | None = None) -> dict[str, Any]:
    """聚合总览（口径逐键对齐 app/ops/overview.py:169-180 · §1.4）。

    issue/PR 派生指标接租户谓词；sync_run/scan_snapshot 模型无 tenant_id
    列，属全局 repo 级状态，不在谓词面（W-fix-2 F13 口径 · 与端点一致）。
    """
    tenant = _tenant_from_ctx(ctx)
    now = datetime.utcnow()
    cycle_since = now - timedelta(days=_CYCLE_REVIEW_WINDOW_DAYS)
    trend_since = now - timedelta(days=_TREND_WINDOW_DAYS)
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(OpsPullRequest.created_at, OpsPullRequest.merged_at).where(
                OpsPullRequest.tenant_id == tenant,
                OpsPullRequest.merged_at.is_not(None),
                OpsPullRequest.merged_at >= cycle_since,
            )
        )
        cycle_time = _median_days(list(result.all()))
        result = await session.execute(
            select(OpsPullRequest.created_at, OpsPullRequest.first_review_at).where(
                OpsPullRequest.tenant_id == tenant,
                OpsPullRequest.first_review_at.is_not(None),
                OpsPullRequest.first_review_at >= cycle_since,
            )
        )
        review_time = _median_days(list(result.all()))
        throughput_count = await session.scalar(
            select(func.count(OpsIssue.id)).where(
                OpsIssue.tenant_id == tenant,
                OpsIssue.closed_at.is_not(None),
                OpsIssue.closed_at >= trend_since,
            )
        )
        result = await session.execute(
            select(func.date(OpsIssue.closed_at), func.count())
            .where(
                OpsIssue.tenant_id == tenant,
                OpsIssue.closed_at.is_not(None),
                OpsIssue.closed_at >= trend_since,
            )
            .group_by(func.date(OpsIssue.closed_at))
        )
        issue_counts = dict(result.all())
        result = await session.execute(
            select(func.date(OpsPullRequest.merged_at), func.count())
            .where(
                OpsPullRequest.tenant_id == tenant,
                OpsPullRequest.merged_at.is_not(None),
                OpsPullRequest.merged_at >= trend_since,
            )
            .group_by(func.date(OpsPullRequest.merged_at))
        )
        pr_counts = dict(result.all())
        trend = _build_trend(issue_counts, pr_counts, now)

        sync_run_row = await session.scalar(
            select(OpsSyncRun).order_by(OpsSyncRun.started_at.desc()).limit(1)
        )
        if sync_run_row is None:
            sync_status = "idle"
            sync_run = None
        else:
            sync_status = sync_run_row.status
            summary = sync_run_row.summary or {}
            sync_run = {
                "id": str(sync_run_row.id),
                "started_at": (
                    sync_run_row.started_at.isoformat() if sync_run_row.started_at else None
                ),
                "finished_at": (
                    sync_run_row.finished_at.isoformat() if sync_run_row.finished_at else None
                ),
                "status": sync_run_row.status,
                "records_issue": summary.get("issues"),
                "records_pr": summary.get("pulls"),
            }

        scan_row = await session.scalar(
            select(OpsScanSnapshot).order_by(OpsScanSnapshot.created_at.desc()).limit(1)
        )
        scan_snapshot = None
        if scan_row is not None:
            scan_snapshot = {
                "parsed_summary": _clip_parsed_summary(scan_row.parsed_summary),
                "created_at": scan_row.created_at.isoformat() if scan_row.created_at else None,
            }

    return {
        "cycle_time": cycle_time,
        "review_time": review_time,
        "issue_throughput": {
            "count": throughput_count or 0,
            "period_days": _TREND_WINDOW_DAYS,
        },
        "as_of": now.isoformat() + "Z",
        "sync_status": sync_status,
        "sync_run": sync_run,
        "scan_snapshot": scan_snapshot,
        "trend": trend,
    }


async def graph_snapshot(payload: Any, *, ctx: dict[str, Any] | None = None) -> dict[str, Any]:
    """图谱快照三视图（§1.5/§1.6 · tenant_scoped:false · 全局 repo 口径）。

    统一外壳 {view,scope,repo_id,created_at,summary,module_matrix?,payload?,
    truncated,warning}；过滤优先于截断；view 词表 adapter 显式校验（R1）。
    ctx 照 T1 惯例：不要求不消费（全局数据面 · scope 常量 "global_repo"）。
    """
    args = payload if isinstance(payload, dict) else {}
    view = args.get("view", "summary")
    if view not in _GRAPH_VIEWS:
        raise LookupError("invalid_view")
    module = args.get("module")
    limit = _GRAPH_VIEW_LIMITS[view]
    async with AsyncSessionLocal() as session:
        row = (
            await session.execute(
                select(OpsGraphSnapshot).order_by(OpsGraphSnapshot.created_at.desc()).limit(1)
            )
        ).scalar_one_or_none()

    warning = None
    truncated = False
    if row is None:
        return {
            "view": view,
            "scope": "global_repo",
            "repo_id": None,
            "created_at": None,
            "summary": None,
            "module_matrix": None,
            "payload": None,
            "truncated": False,
            "warning": None,
        }

    graph_payload = row.payload or {}
    module_matrix = row.module_matrix
    if module:
        graph_payload, warning = _filter_payload_by_module(graph_payload, str(module))
    nodes = graph_payload.get("nodes")
    edges = graph_payload.get("edges")
    modules = graph_payload.get("modules")
    summary = {
        "node_count": len(nodes) if isinstance(nodes, list) else 0,
        "edge_count": len(edges) if isinstance(edges, list) else 0,
        "module_count": (
            len(modules)
            if isinstance(modules, list | dict)
            else len(module_matrix)
            if isinstance(module_matrix, dict)
            else 0
        ),
    }

    out_module_matrix = None
    out_payload = None
    if view == "modules":
        out_module_matrix, truncated = _truncate_json_value(module_matrix, limit)
    elif view == "full":
        out_payload, truncated = _truncate_graph_payload(graph_payload, limit)
        out_module_matrix, matrix_truncated = _truncate_json_value(
            module_matrix, _GRAPH_VIEW_LIMITS["modules"]
        )
        truncated = truncated or matrix_truncated

    return {
        "view": view,
        "scope": "global_repo",
        "repo_id": str(row.repo_id),
        "created_at": row.created_at.isoformat() if row.created_at else None,
        "summary": summary,
        "module_matrix": out_module_matrix,
        "payload": out_payload,
        "truncated": truncated,
        "warning": warning,
    }
