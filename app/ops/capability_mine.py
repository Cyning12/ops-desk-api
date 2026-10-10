"""用户态可见能力目录端点 GET /api/ops/capability/mine（SPEC tool-catalog-page §2 B1）。

**落点纪律**：本模块故意落在 app/ops/ 顶层而非 app/ops/capability/ 包内——
包内禁止挂 APIRouter（app/ops/admin/capability.py docstring 钉死 · 有测试守着）。

钉死契约（task_capability_mine_endpoint）：
- principal 必须由会话构造（types.py:57-73 纪律）：user_id/tenant_id/roles 取自
  CurrentUser 与 request.state.ops_tenant_id，禁取自请求参数；
- 可见性求值单源 evaluate_visibility（经 capability_catalog_snapshot），
  路由层零过滤零排序；
- 出站白名单九键（project_capability 投影），admin 面字段与内部装配不出站；
- 只回可见集（防探测）· 空集 200 {"items": [], "count": 0} · 只读零写；
- baseline_filter 不叠加——用户面语义是身份求值（evaluate_visibility 对
  principal 的 fail-closed 判定），而非场景裁剪；baseline 是 admin catalog 的
  场景收窄预设，叠加会造成双真源（裁定依据见 invoke_20261011_30_implement）。
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Request

from app.db.models import OpsUser
from app.ops.capability.gateway import capability_catalog_snapshot
from app.ops.capability.types import CapabilitySpec, Principal
from app.ops.deps import CurrentUser

router = APIRouter(tags=["ops-capability"])

# 与 deps.py:44 同源缺省：dependency_overrides 路径不注入 request.state 时回退
DEFAULT_TENANT_ID = "ops-desk-pilot"


def project_capability(spec: CapabilitySpec) -> dict[str, Any]:
    """出站白名单投影：九键，除此之外的 spec 字段（含内部装配）一律不出站。

    status 为常量 "available"——能出现在可见集里即「当前可用」（承可见性
    求值结果）；禁用/不可用条目根本不进入本端点响应（防探测）。
    """
    return {
        "id": spec.capability_id,
        "kind": spec.kind,
        "description": spec.description,
        "when_to_use": spec.when_to_use,
        "tags": list(spec.tags),
        "risk_level": spec.risk_level,
        "side_effect": spec.side_effect,
        "enabled": spec.enabled,
        "status": "available",
    }


def _principal_from_request(request: Request, user: OpsUser) -> Principal:
    """从会话用户构造 Principal（禁取自请求参数 · roles 单值→frozenset 钉死映射）。"""
    tenant_id = getattr(request.state, "ops_tenant_id", None) or DEFAULT_TENANT_ID
    return Principal(
        user_id=str(user.id),
        tenant_id=tenant_id,
        roles=frozenset({user.role}),
    )


@router.get("/capability/mine")
def capability_mine(request: Request, user: OpsUser = CurrentUser) -> dict[str, Any]:
    """「我的工具箱」：当前登录用户可见能力列表（只读 · 防探测 · 空集 200 如实）。

    任意登录用户可访问（Q3 裁定 CurrentUser 口径）；可见集由
    capability_catalog_snapshot 单源求值，路由层不叠加任何过滤/排序。
    """
    principal = _principal_from_request(request, user)
    visible, _summary = capability_catalog_snapshot(principal=principal)
    items = [project_capability(spec) for spec in visible]
    return {"items": items, "count": len(items)}
