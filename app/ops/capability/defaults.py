"""默认 local_fn 能力：两枚 mock + utc_now_iso + 本库 issue/PR lookup + 面板聚合双工具。

进程内注册表默认条目（非注册中心）。``args_schema`` 仅参数形态；
业务不变量不进 schema。lookup 标 ``tenant_scoped=True``。
"""

from __future__ import annotations

from datetime import UTC
from typing import Any

from app.ops.capability.adapters.local_fn import LocalFnAdapter
from app.ops.capability.gateway import get_registry, register
from app.ops.capability.lookups import (
    get_issue_by_number,
    get_overview,
    get_pr_by_number,
    graph_snapshot,
    query_issues,
    query_pull_requests,
)
from app.ops.capability.types import CapabilitySpec

# 最小 schema：兼容 legacy 字符串 payload + 结构化 object
_SCHEMA_STRING_OR_OBJECT: dict[str, Any] = {
    "type": ["string", "object"],
    "properties": {},
    "additionalProperties": True,
}

_SCHEMA_LOOKUP: dict[str, Any] = {
    "type": ["string", "object"],
    "properties": {
        "number": {
            "type": ["integer", "string"],
            "description": "issue/PR 号",
        },
    },
    "additionalProperties": True,
}

_SCHEMA_UTC: dict[str, Any] = {
    "type": ["string", "object", "null"],
    "properties": {},
    "additionalProperties": True,
}

# P2a-T1：面板列表查询（与 builtin.v1.yaml 逐字段对齐 · 禁 per-prop
# description 守 catalog 体积红线；enum/边界声明在案，执行期由 adapter
# 显式把关——schema_validate 不校验 enum/min/max（R1））
_SCHEMA_QUERY_ISSUES: dict[str, Any] = {
    "type": "object",
    "properties": {
        "state": {"type": "string", "enum": ["open", "closed"]},
        "label": {"type": "string"},
        "scan_status": {"type": "string"},
        "module": {"type": "string"},
        "page": {"type": "integer"},
        "page_size": {"type": "integer"},
    },
    "additionalProperties": False,
}

_SCHEMA_QUERY_PRS: dict[str, Any] = {
    "type": "object",
    "properties": {
        "state": {"type": "string", "enum": ["open", "closed", "merged"]},
        "ci_status": {"type": "string"},
        "page": {"type": "integer"},
        "page_size": {"type": "integer"},
    },
    "additionalProperties": False,
}

_OUTPUT_SCHEMA_PANEL_LIST: dict[str, Any] = {
    "required": ["$.items", "$.total", "$.page", "$.page_size"],
}

# P2a-T2：面板聚合双工具（get_overview / graph_snapshot · 与 builtin.v1.yaml
# 逐字段对齐）。nullable 为逐键空数据声明（契约消费方只读 required，
# nullable 属自由声明键 · result_contract.py:86-93）。
_SCHEMA_GET_OVERVIEW: dict[str, Any] = {
    "type": "object",
    "properties": {},
    "additionalProperties": False,
}

_SCHEMA_GRAPH_SNAPSHOT: dict[str, Any] = {
    "type": "object",
    "properties": {
        "view": {"type": "string", "enum": ["summary", "modules", "full"]},
        "module": {"type": "string"},
    },
    "additionalProperties": False,
}

_OUTPUT_SCHEMA_GET_OVERVIEW: dict[str, Any] = {
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

_OUTPUT_SCHEMA_GRAPH_SNAPSHOT: dict[str, Any] = {
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


def mock_get_issue_status(payload: str) -> dict:
    """罐头数据：issue 状态查询（真实 GitHub API 另议）。"""
    return {
        "tool": "mock_get_issue_status",
        "input": payload,
        "issue": "#128",
        "status": "open",
        "assignee": "cyning",
        "updated_at": "2026-08-20",
    }


def mock_get_deploy_info(payload: str) -> dict:
    """罐头数据：部署信息查询（真实部署平台 API 另议）。"""
    return {
        "tool": "mock_get_deploy_info",
        "input": payload,
        "env": "prod",
        "version": "v2.3.1",
        "deployed_at": "2026-08-19",
        "status": "healthy",
    }


def utc_now_iso(_payload: str) -> dict:
    """只读：返回当前 UTC ISO 时间戳（无副作用 · 不连外网）。"""
    from datetime import datetime

    return {
        "tool": "utc_now_iso",
        "utc": datetime.now(UTC).isoformat(),
        "note": "只读时间查询",
    }


def testing_write_echo(payload: Any) -> dict:
    """测试专用罐头：写操作**语义 mock · 无真实写操作**。

     供 `manifests/testing.v1.yaml` 的 `testing.write.echo` 使用
    （仅 `OPS_CAPABILITY_EXTRA_MANIFESTS` 显式加载 · 不进 `_DEFAULT_SPECS`）。
     纯函数返回罐头 dict：**零 IO · 零 DB · 零外网 · 零文件写 · 零 subprocess**
    （函数体不 import 任何 IO 库，对齐 `utc_now_iso` 范式）。
    """
    return {
        "tool": "testing_write_echo",
        "input": payload,
        "written": False,
        "note": "语义 mock · 无真实写操作（testing-write-capability 测试专用）",
    }


async def _insert_note(params: dict[str, Any]) -> tuple[str | None, str | None]:
    """延迟 import 落笔面（defaults 罐头面顶层不依赖 note_store）。"""
    from app.ops.capability.note_store import insert_note

    return await insert_note(params)


async def ops_write_run_note(payload: Any, *, ctx: dict | None = None) -> dict:
    """受控写落笔：run 备注/审计便签写入 ``ops_capability_notes``（阶段 W 扩写 · Q1=S1）。

    第二条真实窄写能力 ``ops.write.run_note`` 的执行体——与
    ``testing_write_echo`` 语义 mock 相对照：**真实仓内 DB 落笔**。全部 IO 走
    本函数内**延迟 import**（DB IO 集中在 ``note_store.py`` · 对齐
    ``idempotency.py`` / ``receipts.py`` 先例：能力内核顶层零 DB 依赖）。

    防重双保险（FP-4 重放不双写）：
    ① 幂等 store claim（``(tenant_id, request_id)`` 租户内键）——duplicate 直返；
    ② 落笔表 ``(tenant_id, idempotency_key)`` 唯一约束——store 进程丢失 /
       跨实例漂移时 DB 级仍不双写（ON CONFLICT DO NOTHING 如实返回已有行）。

    租户封闭：tenant **只取 ctx**（与 ``Principal`` 同源纪律 · 禁取模型产出）；
    ctx 缺租户谓词时 Policy 层已拒（``tenant_scope_missing``），此处再 fail-closed
    一道（直接调用面不绕闸）。
    """
    import asyncio

    args = payload if isinstance(payload, dict) else {}
    run_id = str(args.get("run_id") or "").strip()
    note = str(args.get("note") or "").strip()
    request_id = str(args.get("request_id") or "").strip()
    if not run_id or not note or not request_id:
        raise ValueError("run_id / note / request_id 必填（落笔参数缺失不落笔）")
    tenant_id = str((ctx or {}).get("tenant_id") or "").strip()
    if not tenant_id:
        raise PermissionError(
            "tenant_scope_missing：写落笔必须携带租户谓词（ctx.tenant_id · 与 Principal 同源）"
        )

    from app.ops.capability.idempotency import get_idempotency_store

    store = get_idempotency_store()
    aclaim = getattr(store, "aclaim", None)
    if callable(aclaim):
        claim = await aclaim(
            request_id, capability_id="ops.write.run_note", tenant_id=tenant_id
        )
    else:
        claim = await asyncio.to_thread(
            store.claim,
            request_id,
            capability_id="ops.write.run_note",
            tenant_id=tenant_id,
        )
    if claim.duplicate:
        # 命中幂等键：不执行。回一个与首次形状一致的载荷，便于调用方对账。
        return {
            "tool": "ops_write_run_note",
            "written": False,
            "duplicated": True,
            "duplicate_of": claim.receipt_id,
            "idempotency_key": request_id,
            "run_id": run_id,
            "tenant_id": tenant_id,
        }
    if not claim.acquired:
        raise RuntimeError(
            f"idempotency_in_flight: 同一幂等键正在执行中 key={request_id} tenant={tenant_id}"
        )

    async def _arelease() -> None:
        arelease = getattr(store, "arelease", None)
        if callable(arelease):
            await arelease(request_id, tenant_id=tenant_id)
        else:
            await asyncio.to_thread(store.release, request_id, tenant_id=tenant_id)

    approval_id = str((ctx or {}).get("approval_id") or "")
    created_by = str((ctx or {}).get("user_id") or "")
    params = {
        "id": str(__import__("uuid").uuid4()),
        "capability_id": "ops.write.run_note",
        "tenant_id": tenant_id,
        "run_id": run_id,
        "subtask_id": str((ctx or {}).get("subtask_id") or ""),
        "approval_id": approval_id,
        "note": note,
        "created_by": created_by,
        "key": request_id,
    }
    try:
        # 唯一约束兜底：同 (tenant, key) 重放不双写，如实取回已有行
        note_id, duplicate_of = await _insert_note(params)
    except Exception:
        # 落笔失败 = 无副作用（单语句原子）→ 释放租约，可安全重试
        await _arelease()
        raise

    if duplicate_of is not None:
        await _arelease()  # 本次 claim 未产生副作用 → 释放（避免把键卡进租约）
        return {
            "tool": "ops_write_run_note",
            "written": False,
            "duplicated": True,
            "duplicate_of": duplicate_of,
            "idempotency_key": request_id,
            "run_id": run_id,
            "tenant_id": tenant_id,
        }

    # 落笔成功：键标完成（回执 id 由 gateway 落完回执后补上 · complete 支持二次调用）
    acomplete = getattr(store, "acomplete", None)
    if callable(acomplete):
        await acomplete(request_id, tenant_id=tenant_id)
    else:
        await asyncio.to_thread(store.complete, request_id, tenant_id=tenant_id)
    return {
        "tool": "ops_write_run_note",
        "written": True,
        "duplicated": False,
        "note_id": str(note_id),
        "run_id": run_id,
        "tenant_id": tenant_id,
        "approval_id": approval_id,
        "idempotency_key": request_id,
        "receipt": {"note_id": str(note_id), "run_id": run_id, "tenant_id": tenant_id},
    }


_DEFAULT_SPECS: list[tuple[CapabilitySpec, LocalFnAdapter]] = [
    (
        CapabilitySpec(
            capability_id="mock_get_issue_status",
            kind="local_fn",
            description="Mock demo：查询 issue 状态（罐头演示数据 · 非真实仓库 · 真实列表用 query_issues）",
            args_schema=dict(_SCHEMA_STRING_OR_OBJECT),
            tags=("mock", "issue"),
            risk_level="low",
            side_effect="read",
            output_fields=("tool", "input", "issue", "status", "assignee", "updated_at"),
        ),
        LocalFnAdapter(mock_get_issue_status),
    ),
    (
        CapabilitySpec(
            capability_id="mock_get_deploy_info",
            kind="local_fn",
            description="Mock demo：查询部署信息（罐头演示数据 · 非真实部署平台 · 仅演示用）",
            args_schema=dict(_SCHEMA_STRING_OR_OBJECT),
            tags=("mock", "deploy"),
            risk_level="low",
            side_effect="read",
            output_fields=("tool", "input", "env", "version", "deployed_at", "status"),
        ),
        LocalFnAdapter(mock_get_deploy_info),
    ),
    (
        CapabilitySpec(
            capability_id="utc_now_iso",
            kind="local_fn",
            description="只读：返回当前 UTC ISO 时间戳",
            args_schema=dict(_SCHEMA_UTC),
            tags=("readonly", "time"),
            risk_level="low",
            side_effect="read",
            output_fields=("tool", "utc", "note"),
        ),
        LocalFnAdapter(utc_now_iso),
    ),
    (
        CapabilitySpec(
            capability_id="get_issue_by_number",
            kind="local_fn",
            description="本库只读：按 number 查 Issue 摘要（无 raw_payload）",
            args_schema=dict(_SCHEMA_LOOKUP),
            tags=("lookup", "issue", "readonly"),
            risk_level="low",
            side_effect="read",
            tenant_scoped=True,
            output_fields=("number", "title", "state", "html_url", "updated_at", "labels", "body"),
        ),
        LocalFnAdapter(get_issue_by_number),
    ),
    (
        CapabilitySpec(
            capability_id="get_pr_by_number",
            kind="local_fn",
            description="本库只读：按 number 查 PR 摘要（无 raw_payload）",
            args_schema=dict(_SCHEMA_LOOKUP),
            tags=("lookup", "pr", "readonly"),
            risk_level="low",
            side_effect="read",
            tenant_scoped=True,
            output_fields=("number", "title", "state", "html_url", "updated_at", "ci_status", "draft", "body"),
        ),
        LocalFnAdapter(get_pr_by_number),
    ),
    (
        CapabilitySpec(
            capability_id="query_issues",
            kind="local_fn",
            description="只读：分页列出本租户 issue 台账（updated_at 倒序）。过滤：state（open|closed）/label（单标签精确）/scan_status/module（=module_tag）；page 从 1 起，page_size 默认 10 上限 20。返回 items[number,title,state,labels,module_tag,updated_at]+total+page+page_size（不含 body 与内部 id）；单条详情用 get_issue_by_number。",
            when_to_use="需要按状态/标签/模块/扫描状态列出 issue 列表或统计数量时",
            args_schema=dict(_SCHEMA_QUERY_ISSUES),
            tags=("panel", "issues", "readonly"),
            risk_level="low",
            side_effect="read",
            tenant_scoped=True,
            output_fields=("items", "total", "page", "page_size"),
            output_schema=dict(_OUTPUT_SCHEMA_PANEL_LIST),
        ),
        LocalFnAdapter(query_issues),
    ),
    (
        CapabilitySpec(
            capability_id="query_pull_requests",
            kind="local_fn",
            description="只读：分页列出本租户 PR 台账（updated_at 倒序）。过滤：state（open|closed|merged）/ci_status（已知值按 GitHub check 惯例 success|failure|pending；当前 sync 波恒 null，过滤可能命中空集）；page 从 1 起，page_size 默认 10 上限 20。返回 items[number,title,state,draft,ci_status,updated_at]+total+page+page_size（不含 body 与内部 id）；单条详情用 get_pr_by_number。",
            when_to_use="需要按状态或 CI 结果列出 PR 列表或统计数量时",
            args_schema=dict(_SCHEMA_QUERY_PRS),
            tags=("panel", "pull_requests", "readonly"),
            risk_level="low",
            side_effect="read",
            tenant_scoped=True,
            output_fields=("items", "total", "page", "page_size"),
            output_schema=dict(_OUTPUT_SCHEMA_PANEL_LIST),
        ),
        LocalFnAdapter(query_pull_requests),
    ),
    (
        CapabilitySpec(
            capability_id="get_overview",
            kind="local_fn",
            description="只读：本租户交付总览聚合（口径对齐面板 overview 端点 · 无参数）。返回 cycle_time/review_time（90 天窗 PR 周期与首评审中位数天数+sample_size，无样本 median_days 为 null）、issue_throughput（30 天关闭数+period_days）、as_of（必带）、sync_status（无同步记录为 idle）、sync_run（最近同步 id/started_at/finished_at/status/records_issue/records_pr，无记录为 null）、scan_snapshot（最近扫描 parsed_summary+created_at，无记录为 null；parsed_summary 序列化超 2000 字符截断为 {keys,truncated:true}）、trend（30 天逐日 closed_issues/merged_prs 零填）。sync_run/scan_snapshot 为全局仓库级状态（无租户列），issue/PR 派生指标按租户过滤。",
            when_to_use="需要交付效率、同步状态、扫描摘要或 30 天趋势的总览数字，或回答「最近整体怎么样」时",
            args_schema=dict(_SCHEMA_GET_OVERVIEW),
            tags=("panel", "overview", "readonly"),
            risk_level="low",
            side_effect="read",
            tenant_scoped=True,
            output_fields=(
                "cycle_time",
                "review_time",
                "issue_throughput",
                "as_of",
                "sync_status",
                "sync_run",
                "scan_snapshot",
                "trend",
            ),
            output_schema=dict(_OUTPUT_SCHEMA_GET_OVERVIEW),
        ),
        LocalFnAdapter(get_overview),
    ),
    (
        CapabilitySpec(
            capability_id="graph_snapshot",
            kind="local_fn",
            description="只读：全局仓库图谱快照三视图（scope 恒为 global_repo · 无租户谓词 · ctx 不要求）。view=summary（默认 · 仅 summary{node_count,edge_count,module_count} · 上限 4000 字符）/modules（附 module_matrix · 上限 8000）/full（附 payload 与 module_matrix · 上限 12000）；module 可选按节点 module 键过滤子图（过滤优先于截断 · 结构不含过滤键时返回 warning=module_filter_no_match 与未过滤摘要，不静默空集）。超限按 nodes→edges 顺序截断并置 truncated=true 且附原始 totals；无快照时 repo_id/created_at/summary 等为 null、truncated=false。",
            when_to_use="需要仓库模块结构、依赖图或模块×问题矩阵的全局视图时",
            args_schema=dict(_SCHEMA_GRAPH_SNAPSHOT),
            tags=("panel", "graph", "readonly"),
            risk_level="low",
            side_effect="read",
            tenant_scoped=False,
            output_fields=(
                "view",
                "scope",
                "repo_id",
                "created_at",
                "summary",
                "module_matrix",
                "payload",
                "truncated",
                "warning",
            ),
            output_schema=dict(_OUTPUT_SCHEMA_GRAPH_SNAPSHOT),
        ),
        LocalFnAdapter(graph_snapshot),
    ),
]


def ensure_default_capabilities() -> None:
    """幂等注册默认 mock；优先 builtin YAML，缺文件回退硬编码。"""
    # 延迟 import：manifest 解析 adapter 时回指本模块
    from app.ops.capability.manifest import (
        BUILTIN_MANIFEST_PATH,
        load_capability_manifest,
    )

    if BUILTIN_MANIFEST_PATH.is_file():
        load_capability_manifest(BUILTIN_MANIFEST_PATH)
        return
    registry = get_registry()
    for spec, adapter in _DEFAULT_SPECS:
        if registry.get(spec.capability_id) is None:
            register(spec, adapter)
