"""Capability 可见集求值（W2 · F2）。

两层裁剪，**顺序不可颠倒**：

1. ``CapabilityFilter``（按调用上下文：kind / 风险 / 写副作用 / tags）——见 ``registry._match_filter``
2. ``visibility``（按**主体身份**：部门 / 角色 / 项目 / 密级）——本模块

之所以要第二层：第一层是「这个场景该不该出现这类能力」，第二层是
「**这个人**能不能看到这个能力」。上海邮电设计院那种「700+ 份制度分单位
隔离存储、只能检索本单位权限内的文件」靠的就是第二层。

两条纪律：

- **主体由代码构造**（``principal_from_ctx``），不取自模型产出。与租户谓词同源。
- **失败方向**：声明了限制而主体信息不足 → **不可见**（fail-closed）。
  未声明 → 不受限但留痕（``visibility_undeclared``），把「该声明没声明」变成可度量项，
  而不是静默放行。
"""

from __future__ import annotations

from typing import Any

from app.ops.capability.types import (
    CLASSIFICATION_ORDER,
    VISIBILITY_ANY,
    CapabilitySpec,
    Principal,
    classification_rank,
)

# 声明里的键（未知键在加载期被拒，此处只列支持项）
VISIBILITY_KEYS = frozenset(
    {"departments", "roles", "projects", "classification_max"}
)

# 求值不通过的原因（写进审计，便于回答「为什么他没看到」）
REASON_DEPARTMENT = "department_mismatch"
REASON_ROLE = "role_mismatch"
REASON_PROJECT = "project_mismatch"
REASON_CLASSIFICATION = "classification_exceeded"

# reason 码 → 人读文本（单源：路由/出站层禁自写文案 · SPEC 纪律 #3 · 契约4）
VISIBILITY_REASON_TEXTS: dict[str, str] = {
    REASON_DEPARTMENT: "部门不在该能力的可见范围内",
    REASON_ROLE: "角色不在该能力的可见范围内",
    REASON_PROJECT: "项目不在该能力的可见范围内",
    REASON_CLASSIFICATION: "主体密级低于该能力的可见上限",
}


def _as_set(value: Any) -> frozenset[str]:
    if value is None:
        return frozenset()
    if isinstance(value, str):
        return frozenset({value})
    if isinstance(value, (list, tuple, set, frozenset)):
        return frozenset(str(v) for v in value)
    return frozenset()


def principal_from_ctx(ctx: dict[str, Any] | None) -> Principal:
    """从 Host 上下文构造主体。

    键来源与 ``policy._tenant_predicate`` 保持一致（``tenant_id`` / ``_host_tenant``）。
    **模型写进 ctx 的同名键不具备任何效力**——构造点必须在 Host 侧，
    本函数只负责读取，不负责判定来源可信。
    """
    c = ctx or {}
    tenant = c.get("tenant_id") or c.get("_host_tenant") or ""
    return Principal(
        user_id=str(c.get("user_id") or c.get("_host_user_id") or ""),
        tenant_id=str(tenant),
        departments=_as_set(c.get("departments")),
        roles=_as_set(c.get("roles")),
        projects=_as_set(c.get("projects")),
        classification_max=str(
            c.get("classification_max") or Principal().classification_max
        ),
    )


def _dimension_ok(
    rule_value: Any, principal_value: frozenset[str]
) -> bool:
    """一维求交：声明含 ``all`` 或未声明 → 不限；否则需交集非空。"""
    declared = _as_set(rule_value)
    if not declared or VISIBILITY_ANY in declared:
        return True
    return bool(declared & principal_value)


def check_visible(
    spec: CapabilitySpec, principal: Principal
) -> tuple[bool, str | None]:
    """返回 ``(visible, reason)``；``reason`` 仅在不可见时非空。"""
    rule = spec.visibility
    if not isinstance(rule, dict):
        return True, None  # 未声明：不受限（留痕见 evaluate_visibility）

    if not _dimension_ok(rule.get("departments"), principal.departments):
        return False, REASON_DEPARTMENT
    if not _dimension_ok(rule.get("roles"), principal.roles):
        return False, REASON_ROLE
    if not _dimension_ok(rule.get("projects"), principal.projects):
        return False, REASON_PROJECT

    required = str(rule.get("classification_max") or "").strip().lower()
    if required:
        if required not in CLASSIFICATION_ORDER:
            # 加载期已校验；此处 fail-closed，不因配置写错而放行
            return False, REASON_CLASSIFICATION
        if classification_rank(principal.classification_max) < classification_rank(
            required
        ):
            return False, REASON_CLASSIFICATION
    return True, None


def evaluate_visibility(
    specs: list[CapabilitySpec], principal: Principal
) -> tuple[list[CapabilitySpec], dict[str, Any]]:
    """裁剪 + 返回审计摘要（谁被裁、为什么、多少条未声明）。"""
    kept: list[CapabilitySpec] = []
    hidden: list[dict[str, str]] = []
    undeclared = 0
    for spec in specs:
        if spec.visibility is None:
            undeclared += 1
        ok, reason = check_visible(spec, principal)
        if ok:
            kept.append(spec)
        else:
            reason = reason or ""
            hidden.append(
                {
                    "capability_id": spec.capability_id,
                    "reason": reason,
                    # 人读文本单源出于本模块词表（未知码原样返回，不静默吞）
                    "visibility_reason": VISIBILITY_REASON_TEXTS.get(reason, reason),
                }
            )
    summary: dict[str, Any] = {
        "visibility_catalog_count": len(specs),
        "visibility_kept_count": len(kept),
        "visibility_hidden": hidden,
        "visibility_undeclared_count": undeclared,
        # 匿名主体：部门/角色为空，任何声明了限制的能力都会被裁掉
        "visibility_principal_anonymous": principal.is_anonymous(),
    }
    return kept, summary


def filter_visible(
    specs: list[CapabilitySpec], principal: Principal
) -> list[CapabilitySpec]:
    return evaluate_visibility(specs, principal)[0]
