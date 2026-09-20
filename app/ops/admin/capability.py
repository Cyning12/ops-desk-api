"""Capability 观测端点（管理员面）。

**为什么放在包外**：`app/ops/capability/` 内**禁止挂 APIRouter**——能力注册表变更
必须走 Git + 人闸，不允许有"改一下就能热加载"的 HTTP 入口（包内有测试守着这条）。
观测端点不改能力清单，但同样属于**对外接口**，所以放在 `app/ops/admin/` 下，
与 `admin/sync` 同一个鉴权口径（`AdminSyncAuth`）。

**这组端点回答的是"现在活着吗、谁被裁了、有没有卡住的写"**，不是功能接口：

| 端点 | 回答 |
|---|---|
| `GET /runtime` | **持久化配了吗**（没配 = 没有防重，且不报错）、能力总数、清单版本 |
| `GET /catalog` | 模型/某人能看到哪些能力；**被裁掉的是谁、为什么** |
| `GET /receipts` | 写操作的回执（含 `captured` / `write_confirmed`） |
| `GET /idempotency` | 防重行；`stuck_only=true` 列出**卡住的 in_flight** |

> `/runtime` 是这里面最重要的一条：`OPS_CAPABILITY_PERSISTENCE` 没配时**一切照常运行、
> 只是悄悄不防重**——这种人必须能一眼看出来的事，不该靠翻环境变量。
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Query, status

from app.db.models import OpsUser
from app.ops.capability import (
    Principal,
    capability_catalog_snapshot,
    get_capability_manifest_metadata,
    list_capabilities,
)
from app.ops.capability.baseline import baseline_filter
from app.ops.capability.idempotency import DbIdempotencyStore
from app.ops.capability.metrics import snapshot as metrics_snapshot
from app.ops.capability.persistence import describe_persistence
from app.ops.capability.receipts import DbReceiptSink
from app.ops.capability.types import CapabilityFilter
from app.ops.deps import AdminSyncAuth

router = APIRouter(prefix="/admin/capability", tags=["admin"])


def _csv(value: str | None) -> frozenset[str]:
    if not value:
        return frozenset()
    return frozenset(p.strip() for p in value.split(",") if p.strip())


def _principal(
    *,
    user_id: str | None,
    tenant_id: str | None,
    departments: str | None,
    roles: str | None,
    projects: str | None,
    classification_max: str | None,
) -> Principal:
    """按**待观测主体**构造 Principal（管理员用它来复现"某人看到什么"）。

    注意这与运行时不同：运行时 principal 必须由 Host 从会话构造；
    这里显式接受查询参数，是因为**它的用途就是替别人看一眼**。
    """
    return Principal(
        user_id=(user_id or "").strip(),
        tenant_id=(tenant_id or "").strip(),
        departments=_csv(departments),
        roles=_csv(roles),
        projects=_csv(projects),
        classification_max=(classification_max or "").strip()
        or Principal().classification_max,
    )


@router.get("/runtime")
async def runtime(_user: OpsUser | None = AdminSyncAuth) -> dict[str, Any]:
    """运行时自检：**持久化到底配没配**、能力有多少、清单是哪个版本。"""
    specs = list_capabilities()
    persistence = describe_persistence()
    store = persistence["idempotency"]
    return {
        "persistence": persistence,
        "capabilities": {
            "total": len(specs),
            "enabled": sum(1 for s in specs if s.enabled),
            "by_kind": _count_by(specs, "kind"),
            "by_side_effect": _count_by(specs, "side_effect"),
            # 写能力是风险面：单列出来，改清单时能一眼看到它变了没有
            "write_capabilities": [
                s.capability_id
                for s in specs
                if s.side_effect in ("write", "irreversible")
            ],
        },
        "manifest": get_capability_manifest_metadata(),
        "idempotency_store": store["store"],
        "health": _health(persistence),
    }


def _count_by(specs: list[Any], attr: str) -> dict[str, int]:
    out: dict[str, int] = {}
    for spec in specs:
        key = str(getattr(spec, attr, "") or "unknown")
        out[key] = out.get(key, 0) + 1
    return out


def _health(persistence: dict[str, Any]) -> dict[str, Any]:
    """给人看的一句话结论 + 是否可上生产。"""
    if persistence["production_safe"]:
        return {"level": "ok", "message": "持久化已按 db 装配"}
    return {
        "level": "warn",
        "message": str(persistence["note"]),
        "impact": "重复提交可能产生第二张单据；回执重启即丢（或不可查询）",
    }


@router.get("/catalog")
async def catalog(
    _user: OpsUser | None = AdminSyncAuth,
    baseline: bool = Query(True, description="用模型侧的可见集基线（否则不加形态裁剪）"),
    user_id: str | None = None,
    tenant_id: str | None = None,
    departments: str | None = Query(None, description="逗号分隔"),
    roles: str | None = Query(None, description="逗号分隔"),
    projects: str | None = Query(None, description="逗号分隔"),
    classification_max: str | None = None,
) -> dict[str, Any]:
    """可见集 + **被裁掉的是谁、为什么**。

    「为什么他没看到」在没有这个端点时是答不出来的——只能读代码猜。
    """
    cap_filter: CapabilityFilter | None = (
        baseline_filter(node_role="admin_preview") if baseline else None
    )
    principal = _principal(
        user_id=user_id,
        tenant_id=tenant_id,
        departments=departments,
        roles=roles,
        projects=projects,
        classification_max=classification_max,
    )
    visible, summary = capability_catalog_snapshot(
        filter=cap_filter, principal=principal
    )
    return {
        "filter": {
            "baseline": baseline,
            "kinds": sorted(cap_filter.kinds) if cap_filter and cap_filter.kinds else None,
            "allow_tags_any": (
                sorted(cap_filter.allow_tags_any)
                if cap_filter and cap_filter.allow_tags_any
                else None
            ),
            "deny_high_risk": bool(cap_filter and cap_filter.deny_high_risk),
            "deny_write": bool(cap_filter and cap_filter.deny_write),
        },
        "principal": {
            "user_id": principal.user_id,
            "tenant_id": principal.tenant_id,
            "departments": sorted(principal.departments),
            "roles": sorted(principal.roles),
            "classification_max": principal.classification_max,
            "anonymous": principal.is_anonymous(),
        },
        "visible_ids": sorted(s.capability_id for s in visible),
        **summary,
    }


@router.get("/metrics")
async def metrics(_user: OpsUser | None = AdminSyncAuth) -> dict[str, Any]:
    """进程内指标快照。

    **最该被盯的数字是 `write.blocked`**（被 Policy 拦下的写）：
    异常升高 = 有人在反复试不该做的写；恒为 0 = 没人用，**或者写闸根本没装上**
    ——所以必须和 `/runtime` 的持久化/闸门信息一起看。
    """
    return metrics_snapshot()


@router.get("/receipts")
async def receipts(
    _user: OpsUser | None = AdminSyncAuth,
    tenant_id: str | None = None,
    capability_id: str | None = None,
    limit: int = Query(50, ge=1, le=500),
) -> dict[str, Any]:
    """写操作回执（**副作用以收据为真**）。只读，不改任何状态。"""
    sink = DbReceiptSink()
    try:
        rows = await sink.arecent(
            tenant_id=(tenant_id or "").strip(),
            capability_id=(capability_id or "").strip(),
            limit=limit,
        )
    except Exception as exc:  # noqa: BLE001 — 明确报"库不可达"，不吞
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"回执表不可达：{type(exc).__name__}",
        ) from exc
    return {
        "persistence": describe_persistence(),
        "count": len(rows),
        "receipts": rows,
    }


@router.get("/idempotency")
async def idempotency(
    _user: OpsUser | None = AdminSyncAuth,
    tenant_id: str | None = None,
    stuck_only: bool = Query(
        False, description="只列出租约已过期的 in_flight（需人工到下游对账）"
    ),
    limit: int = Query(200, ge=1, le=1000),
) -> dict[str, Any]:
    """防重行。``stuck_only=true`` 是**租约巡检**：列出"发出去了但不知道结果"的写。

    **这一步只发现、不自动重试**——要不要重试取决于下游到底有没有生效，
    那是人或专门的查询能力才能判断的；盲目重试可能建出第二张单。
    """
    store = DbIdempotencyStore()
    try:
        rows = await store.asnapshot(
            tenant_id=(tenant_id or "").strip(), stuck_only=stuck_only, limit=limit
        )
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"防重表不可达：{type(exc).__name__}",
        ) from exc
    return {
        "persistence": describe_persistence(),
        "stuck_only": stuck_only,
        "count": len(rows),
        "needs_reconcile": sum(1 for r in rows if r["needs_reconcile"]),
        "rows": rows,
        "hint": (
            "这些写操作的状态未知：下游可能已生效也可能没有。"
            "请带 idempotency_key 到下游查询确认，**不要直接重试**。"
            if stuck_only and rows
            else None
        ),
    }
