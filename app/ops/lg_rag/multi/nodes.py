"""lg_rag Phase 4 · Multi-Agent 节点（supervisor / 三专业 agent / aggregator）。

说明书：docs/guides/DESIGN_langgraph-lg-rag-phase4-multiagent_v1.md §3–§5。

原则：
- supervisor 首次规划失败/非法 → fail-closed 抛 ``SupervisorPlanError`` 停图（D2；
  灾备 env ``LG_RAG_SUPERVISOR_PLAN_ON_FAIL=single_rag`` 降级单 rag 并打 degraded 标记；
  重规划 ``if locked:`` 例外沿用未解决后缀）；须已有 run_id，否则不派工人；
- 无依赖子任务同批 Send 给多个工人；有 depends_on 的等前驱终态再下发；
- 归并键是 Host subtask_id，不用模型别名，也不用结果列表长度当下标；
- 单个子任务异常 → 该 id 占错误终态，不卡住收齐。
"""

from __future__ import annotations

import copy
import json
import logging
import os
import time
from datetime import UTC, datetime
from typing import Any, Optional

from langchain_core.messages import AIMessage
from langchain_core.runnables import RunnableConfig

# ⚠️ 节点签名里的 ``config`` **必须**写成 ``Optional[RunnableConfig]``：
#   本模块带 ``from __future__ import annotations``，注解会变成**字符串**，
#   而 langgraph 1.x 只接受 ``RunnableConfig`` / ``Optional[RunnableConfig]``
#   两种字面写法 —— 写成 ``RunnableConfig | None`` 它不认，
#   后果不是告警而已：**config 不会被注入**，``_thread_id_of`` 的兜底
#   直接失效 ⇒ 审批申请没有 thread_id ⇒ 批准之后无从恢复。
from langgraph.types import Send, interrupt
from pydantic import ValidationError

from app.llm.factory import get_llm_provider
from app.llm.schema import LlmMessage
from app.ops.capability import ainvoke as capability_ainvoke
from app.ops.capability import delegation as dl
from app.ops.capability import get_registry as _cap_registry
from app.ops.capability import list_capabilities
from app.ops.capability.baseline import baseline_filter
from app.ops.capability.gateway import _args_summary as _cap_args_summary  # 单一实现
from app.ops.capability.types import WRITE_SIDE_EFFECTS, CapabilitySpec
from app.ops.lc_evidence_chain.step_hook import (
    reset_chain_step_hook,
    set_chain_step_hook,
)
from app.ops.lg_rag.answer_stream import complete_answer_streaming
from app.ops.lg_rag.graph import astream_router_agent
from app.ops.lg_rag.multi import step_contract as sc
from app.ops.lg_rag.multi.budget import (
    bump_react_round,
    bump_supervisor_step,
    is_react_round_exhausted,
    is_supervisor_budget_exhausted,
)
from app.ops.lg_rag.nodes import (
    _ROUTER_MODEL,
    _ROUTER_PROVIDER,
    _last_user_text,
)
from app.ops.lg_rag.progress_stream import emit_subtask_running, emit_subtask_step
from app.ops.lg_rag.schemas import ExtractResult, SubtaskItem, SubtasksPlan
from app.ops.lg_rag.state import (
    LgRagState,
    SubtaskResultBatch,
    success_terminal_ids,
    unresolved_suffix_ids,
)
from app.ops.prompts import render
from app.ops.prompts.slots import (
    SlotIsolationError,
    assert_slots_declared,
    declare_slots,
    security_input_isolation_enabled,
    wrap_slot,
)
from app.ops.strategy.builder import effective_scope_from_requested
from app.ops.structured_output import parse_only
from app.ops.tenant_context import current_tenant_or_default
from app.ops.tracing import score_current_trace, trace_span, tracing_enabled

logger = logging.getLogger(__name__)

SUBTASK_TYPES = ("rag", "extract", "tool")
MAX_SUBTASKS = 4  # cap=4，超出截断（DESIGN §3）；与 supervisor 总步预算并存

# 子任务 type → 条件边目标节点
_TYPE_TO_NODE = {
    "rag": "rag_subtask",
    "extract": "info_extract",
    "tool": "tool_exec",
}

# Supervisor planner filter：与 Builder **共用同一份基线**（见 capability.baseline），
# 再 ∩ state.allowed_capability_ids（S1）。
_SUPERVISOR_CAP_FILTER = baseline_filter(node_role="supervisor")

# Mock / lookup 已迁入 Capability Gateway（defaults + lookups）；
# tool_exec_node 主路径 await ainvoke（P-13，禁止在 async 节点同步打 PG）。


def _format_capability_catalog(specs: list[CapabilitySpec]) -> str:
    """赋能目录摘要（id · description · risk · output_fields）供 supervisor system 注入。

    ``output_fields`` 非空时追加产出字段名清单——planner 声明 produces/consumes
    从「猜」变「从清单选」（task lg-rag-capability-output-schema）；
    未声明（空）能力的行与此前**逐字节一致**（验收 1 零 diff 口径）。
    """
    if not specs:
        return "（当前无可用 local_fn 工具）"
    lines = []
    for s in specs:
        # getattr 宽容：旧测以 SimpleNamespace 伪造 spec（无 output_fields 属性）——
        # 缺属性视同未声明，行渲染保持零 diff
        declared = getattr(s, "output_fields", None) or ()
        extra = f"；output_fields=[{', '.join(declared)}]" if declared else ""
        lines.append(f"- {s.capability_id}：{s.description}（risk={s.risk_level}{extra}）")
    return "\n".join(lines)


def _build_supervisor_system(catalog_block: str) -> str:
    return render(
        "lg_rag.supervisor.system",
        {"catalog_block": catalog_block},
    )


def _build_supervisor_suffix_system(
    catalog_block: str,
    prefix_block: str,
    suffix_cap: int,
    preserved_block: str = "",
) -> str:
    """重规划（Q8）：只让模型写后缀，前缀以**只读**形态出现。

    approved-replan-quality：preserved_block 注入保号行执行摘要
    （已批准待重跑步名单），破「LLM 不知晓保号行」盲循环（SPEC §9 序1）。
    """
    return render(
        "lg_rag.supervisor.suffix.system",
        {
            "catalog_block": catalog_block,
            "prefix_block": prefix_block,
            "suffix_cap": str(suffix_cap),
            "preserved_block": preserved_block,
        },
    )


def _resolve_supervisor_visible_caps(
    state: LgRagState,
) -> tuple[list[CapabilitySpec], frozenset[str]]:
    """本轮 supervisor 可见 catalog = filter ∩ state allowlist（S1-c）。"""
    allowlist_raw = state.get("allowed_capability_ids")
    if allowlist_raw is None:
        logger.warning(
            "lg_rag supervisor: allowed_capability_ids 缺失（须经 Builder），fallback 单 rag"
        )
        return [], frozenset()
    allowlist = frozenset(str(cid) for cid in allowlist_raw)
    caps = list_capabilities(filter=_SUPERVISOR_CAP_FILTER)
    if not allowlist:
        return [], frozenset()
    visible = [s for s in caps if s.capability_id in allowlist]
    return visible, frozenset(s.capability_id for s in visible)


def _subtasks_have_valid_tool_ids(subtasks: list[dict], allowed_ids: frozenset[str]) -> bool:
    """type=tool 子任务的 tool 须在本轮可见 id 集内（S1-d · 继承 H1）。"""
    for item in subtasks:
        if str(item.get("type") or "") != "tool":
            continue
        tool_id = str(item.get("tool") or "").strip()
        if not tool_id or tool_id not in allowed_ids:
            return False
    return True


# ---------------------------------------------------------------------------
# 解析与元数据辅助
# ---------------------------------------------------------------------------


def _parse_subtasks(raw: str) -> list[dict] | None:
    """解析 supervisor LLM 输出为子任务列表；非法/为空返回 None（走 fallback）。

    选型：``supervisor_node`` 已 ``complete`` 一次，此处仅 ``parse_only``，
    避免 ``acomplete_structured`` 双重 LLM（延迟敏感；纠偏留给后续波次）。

    逐项规整：缺 id 补 tN；type 不在白名单归为 rag（宁退化）；input 非空
    字符串必填（schema + strip），任一项 input 缺失/空白视整体非法；超过
    cap=4 截断（cap 外项不参与校验，避免误 fallback）。
    """
    outcome = parse_only(raw, schema=SubtasksPlan)
    if not outcome.ok or outcome.data is None:
        return None
    items = outcome.data.subtasks
    subtasks: list[dict] = []
    for i, raw_item in enumerate(items[:MAX_SUBTASKS]):
        try:
            item = SubtaskItem.model_validate(raw_item)
        except ValidationError:
            return None
        text = (item.input or "").strip()
        if not text:
            return None
        subtask_type = (item.type or "").strip()
        if subtask_type not in SUBTASK_TYPES:
            subtask_type = "rag"
        subtask = {
            "id": str(item.id or f"t{i + 1}"),
            "type": subtask_type,
            "input": text,
        }
        if subtask_type == "tool" and item.tool:
            subtask["tool"] = str(item.tool)
        if item.args is not None:
            subtask["args"] = dict(item.args)
        if item.depends_on:
            subtask["depends_on"] = [str(dep) for dep in item.depends_on]
        # Q4 步骤契约：可选声明。没声明就留空 ⇒ 后续不校验（契约不推测）
        produces = sc.normalize_produces(item.produces)
        if produces:
            subtask["produces"] = produces
        consumes = sc.normalize_consumes(item.consumes)
        if consumes:
            subtask["consumes"] = consumes
        subtasks.append(subtask)
    return subtasks or None


def _record_span_metadata(metadata: dict) -> None:
    """决策写入当前 span metadata（DESIGN §6；观测失败不挡主流程）。"""
    if tracing_enabled():
        try:
            from langfuse import get_client

            get_client().update_current_span(metadata=metadata)
        except Exception:
            pass
    # E4：仅 supervisor_fallback=True 写 stab.fallback=1（采样门控在 score 内）
    if metadata.get("supervisor_fallback") is True:
        score_current_trace("stab.fallback", 1)


def _pending_subtask(state: LgRagState) -> dict | None:
    """直调节点的兜底：只在没有 Send 载荷时按下标取一项。同批工人禁止走这里。"""
    subtasks = state.get("subtasks") or []
    results = state.get("subtask_results") or []
    idx = len(results)
    return subtasks[idx] if idx < len(subtasks) else None


def _current_subtask(state: LgRagState) -> dict | None:
    """优先读本工人的 assigned_subtask，避免兄弟任务抢同一个下标。"""
    assigned = state.get("assigned_subtask")
    if isinstance(assigned, dict) and assigned:
        return assigned
    return _pending_subtask(state)


def _run_id_of(state: LgRagState) -> str:
    return str(state.get("run_id") or "").strip()


# ---------------------------------------------------------------------------
# Host V1-A · 委派令牌（签发审批 / 有效 scope / 分发签发）
# ---------------------------------------------------------------------------


def _delegation_active() -> bool:
    """委派令牌面是否启用（off = 现状逐字节零 diff · 默认 off）。"""
    return dl.delegation_mode() != dl.MODE_OFF


ENV_WRITE_REPLAY_GUARD_ENABLED = "LG_RAG_WRITE_REPLAY_GUARD_ENABLED"
_GUARD_TRUTHY = ("1", "true", "yes", "on")
_GUARD_FALSY = ("0", "false", "no", "off")


def _write_replay_guard_enabled() -> bool:
    """write 孪生重放护栏独立开关（delegation-naming-boundary D2 解耦）。

    布尔默认 true=开；非法值回退开（fail-closed 反向）+ warning 留痕。
    解析承 continuity.py session_summary_enabled 先例（_TRUTHY/_FALSY
    词表一致 · strip().lower()），唯默认/回退方向相反（R1 N-d 防误抄）。
    FP-2 唯一 intentional behavior change：delegation off 下护栏由从不
    生效变默认生效。
    """
    raw = (os.getenv(ENV_WRITE_REPLAY_GUARD_ENABLED) or "").strip().lower()
    if not raw:
        return True
    if raw in _GUARD_TRUTHY:
        return True
    if raw in _GUARD_FALSY:
        return False
    logger.warning("invalid LG_RAG_WRITE_REPLAY_GUARD_ENABLED=%r; fallback to true", raw)
    return True


# ---------------------------------------------------------------------------
# Host V1-A · 签发审批消费门（D1：批准 → 可消费的授权）
# ---------------------------------------------------------------------------

ENV_APPROVAL_CONSUMPTION_TTL_SECONDS = "OPS_HITL_APPROVAL_CONSUMPTION_TTL_SECONDS"
DEFAULT_APPROVAL_CONSUMPTION_TTL_SECONDS = 3600
_BLOCKED_BY_DELEGATION_ISSUE = "delegation_issue_hitl_required"
# 阶段 W（api-controlled-write-hitl · HG-STAGE-W-DESIGN 签收）：写执行审批闸
# 拦单类。fail-closed：write 类 capability 无新鲜 approved 单据一律挂起 HITL
# （复用既有 HITL 回路）；``OPS_CAPABILITY_ALLOW_WRITE`` 只过 gateway Policy
# 写闸，**不豁免**本闸——两道闸缺一不可（棒次红线钉死）。
_BLOCKED_BY_CAPABILITY_WRITE = "capability_write_hitl_required"
# 写执行可消费的 approved 单据类：本闸拦单类 + 委派签发审批类（后者签发理由
# 串已声明「非只读」· enforce 链不双审批；其消费语义维持既有三元组口径 ·
# M1 保留一行不动）。
_WRITE_CONSUMABLE_BLOCKED_BY = frozenset(
    {_BLOCKED_BY_DELEGATION_ISSUE, _BLOCKED_BY_CAPABILITY_WRITE}
)
# D2 回填适用类：拦截对象即被拦步自身（空 unlock_subtask_id → 回填 sid 自身，
# resume 不 409 的前提）；prefix_touch_required 类维持空 unlock（TA6 钉死）。
_SELF_UNLOCK_BLOCKED_BY = frozenset(
    {_BLOCKED_BY_DELEGATION_ISSUE, _BLOCKED_BY_CAPABILITY_WRITE}
)


def _approval_consumption_ttl_seconds() -> int:
    """批准消费 TTL（墙钟秒）；默认 3600，非法 / 越界（[1, 86400]）回退默认。

    承 ``delegation._env_int``（delegation.py:105-107）low/high 先例同形态。
    """
    raw = os.environ.get(ENV_APPROVAL_CONSUMPTION_TTL_SECONDS, "")
    try:
        value = int(str(raw).strip())
    except (TypeError, ValueError):
        return DEFAULT_APPROVAL_CONSUMPTION_TTL_SECONDS
    return value if 1 <= value <= 86400 else DEFAULT_APPROVAL_CONSUMPTION_TTL_SECONDS


def _decided_at_ts(raw: Any) -> float | None:
    """``decided_at`` 归一为可比墙钟时间戳；不可归一 → ``None``（fail-closed）。

    输入类型钉死（R1-N1 锚点精度）：**float**（InMemory store.py:98 ``time.time()``）
    | **ISO 8601 str**（Db store 经 ``alist/aget`` 实收 ``_row_to_dict`` :249 输出）。
    SPEC「Db store 为 datetime」指 SQL 层；消费端实收是 ISO 字符串，漏 str 分支
    会让 TTL 比较 TypeError 或误判过期/新鲜。
    """
    if isinstance(raw, bool):
        return None
    if isinstance(raw, (int, float)):
        return float(raw)
    if isinstance(raw, str):
        try:
            dt = datetime.fromisoformat(raw.strip())
        except ValueError:
            return None
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=UTC)
        return dt.timestamp()
    return None


def _match_fresh_approved(
    rows: list[dict],
    *,
    run_id: str,
    subtask_id: str,
    capability_id: str,
    blocked_by: frozenset[str],
) -> tuple[dict, int] | None:
    """approved 单据匹配核心（Q1 三元组 + Q5 读时 TTL · **单一实现禁第二份**）。

    命中 ``(run_id, subtask_id, payload.capability_id)`` 精确匹配且未过期 →
    ``(row, ttl_remaining_seconds)``；否则 ``None``。``blocked_by`` 单据类守卫
    由调用方声明（委派签发门只收委派类；写执行闸收写闸类 + 委派类）。
    fail-closed：旧单据无 payload / 缺 capability_id 键 / ``decided_at`` 不可
    归一 / 过期 → 一律不匹配。**不写回单据状态**（授权效力 = 读取时刻的活状态）。
    """
    now = time.time()
    ttl = _approval_consumption_ttl_seconds()
    for row in rows:
        if str(row.get("blocked_by") or "") not in blocked_by:
            continue  # 单据类型守卫：prefix_touch_required 类一行不动
        if str(row.get("run_id") or "") != run_id:
            continue
        if str(row.get("subtask_id") or "") != subtask_id:
            continue
        payload = row.get("payload")
        if not isinstance(payload, dict):
            continue  # 旧单据无 payload → 不消费（fail-closed）
        if str(payload.get("capability_id") or "") != capability_id:
            continue  # 旧单据缺 capability_id 键 → 不消费（fail-closed）
        decided_ts = _decided_at_ts(row.get("decided_at"))
        if decided_ts is None:
            continue
        remaining = ttl - (now - decided_ts)
        if remaining <= 0:
            continue  # Q5：读时判过期（不写回单据状态）
        return row, int(remaining)
    return None


def _audit_approval_consumed(**fields: Any) -> None:
    """批准消费台账（记动作不记内容）：logger 结构化行 + span metadata。

    只记 request_id / subtask_id / capability_id / decision_by / TTL 余量，
    **不记参数原值**（承 delegation.audit_delegation 同一纪律）。
    """
    safe = {k: v for k, v in fields.items() if v is not None}
    logger.info(
        "delegation_approval_consumed %s",
        json.dumps(safe, ensure_ascii=False, sort_keys=True),
    )
    _record_span_metadata({"delegation_approval_consumed": True, **safe})


async def _approval_consumed(state: LgRagState, *, subtask_id: str, capability_id: str) -> bool:
    """消费匹配的 approved 单据（D1 消费门 · Q1 三元组 + Q5 读时 TTL）。

    命中（``(run_id, subtask_id, capability_id)`` 精确匹配 + 未过期）→ ``True``
    + ``delegation_approval_consumed`` 台账；**fail-closed**：读失败 / 旧单据缺
    ``capability_id`` 键 / 过期 / 类型不符 / 未命中 → 一律 ``False``（维持拦截）。
    只消费 ``blocked_by=delegation_issue_hitl_required`` 类单据；**不写回单据状态**
    （授权效力 = 读取时刻的活状态，非缓存快照）。
    """
    from app.ops.hitl import get_hitl_store

    run_id = _run_id_of(state)
    if not (run_id and subtask_id and capability_id):
        return False
    try:
        rows = await get_hitl_store().alist(status="approved", limit=200)
    except Exception as exc:  # FP-1：消费读失败 fail-closed + warning 台账
        logger.warning(
            "delegation_approval_consumption_read_failed subtask=%s capability=%s err=%r",
            subtask_id,
            capability_id,
            exc,
        )
        return False
    hit = _match_fresh_approved(
        rows,
        run_id=run_id,
        subtask_id=subtask_id,
        capability_id=capability_id,
        blocked_by=frozenset({_BLOCKED_BY_DELEGATION_ISSUE}),  # 单据类型守卫不动
    )
    if hit is None:
        return False
    row, remaining = hit
    _audit_approval_consumed(
        request_id=str(row.get("id") or ""),
        subtask_id=subtask_id,
        capability_id=capability_id,
        decision_by=str(row.get("decision_by") or ""),
        ttl_remaining_seconds=remaining,
    )
    return True


async def _write_execution_approval(
    state: LgRagState, *, subtask_id: str, capability_id: str
) -> dict | None:
    """写执行审批消费（阶段 W · W0/W2/W3）：命中 → 可消费的 approved 单据行。

    调用方凭返回行注入 Host 单次写放行 + ``approval_id`` 审计串链；**fail-closed**
    未命中 → ``None``（维持拦截）：读失败 / 过期 / 三元组不符 / 类型不符 /
    capability_write 类单据 ``tenant_id`` 缺失或与当前租户不一致（W2 跨租户写
    拦死 · 租户以 session 真源下推为准）。委派签发类
    （``delegation_issue_hitl_required``）单据**同入本守卫**（api-w-hitl-tenant-fix ·
    HG-W-TENANT-DESIGN ② 扩列：T-fix-2 打戳后守卫查非空成立；空/跨租户 delegation
    行一律 fail-closed 不消费——守卫真空收口）。

    **delegation 类命中 = 查命中不重复消费**（fix-delegation-resume-approval-id ·
    维护者裁决 2026-11-06 · issue #334 comment `6665660681`）：delegation 类单据的
    审批消费归签发门单点（``_approval_consumed`` · ``delegation_approval_consumed``
    台账即该单据唯一消费记录）；本闸对 delegation 类命中仍走同一 fail-closed 匹配
    + W2 租户守卫 + 返回行（approval_id 注入与三照串链不变），但**不再重复记
    ``capability_write_approval_consumed`` 台账**——修复前 resume 后同一 approval_id
    被签发门 + 写闸双消费，与主路径单消费语义不齐。capability_write 类消费形态
    与主路径逐字节一致。台账记动作不记内容（不落参数原值）。
    """
    from app.ops.hitl import get_hitl_store

    run_id = _run_id_of(state)
    if not (run_id and subtask_id and capability_id):
        return None
    try:
        rows = await get_hitl_store().alist(status="approved", limit=200)
    except Exception as exc:  # 读失败 fail-closed + warning（承 FP-1 形态）
        logger.warning(
            "capability_write_approval_read_failed subtask=%s capability=%s err=%r",
            subtask_id,
            capability_id,
            exc,
        )
        return None
    hit = _match_fresh_approved(
        rows,
        run_id=run_id,
        subtask_id=subtask_id,
        capability_id=capability_id,
        blocked_by=_WRITE_CONSUMABLE_BLOCKED_BY,
    )
    if hit is None:
        return None
    row, remaining = hit
    blocked_by = str(row.get("blocked_by") or "")
    if blocked_by in _WRITE_CONSUMABLE_BLOCKED_BY:
        # W2 · HG-W-TENANT-DESIGN ② 扩列：写闸类 + 委派类单据均须带租户且与
        # 当前租户一致（跨租户/空 tenant 一律 fail-closed 不消费）。
        row_tenant = str(row.get("tenant_id") or "")
        if not row_tenant or row_tenant != current_tenant_or_default():
            return None
    if blocked_by == _BLOCKED_BY_DELEGATION_ISSUE:
        # delegation 类：查命中即放行（消费单点在签发门 · 双消费合一 ·
        # approval_id 审计串链经返回行照常注入 · 零行为变化）。
        return row
    logger.info(
        "capability_write_approval_consumed %s",
        json.dumps(
            {
                "approval_id": str(row.get("id") or ""),
                "blocked_by": str(row.get("blocked_by") or ""),
                "capability_id": capability_id,
                "decision_by": str(row.get("decision_by") or ""),
                "subtask_id": subtask_id,
                "tenant_id": current_tenant_or_default(),
                "ttl_remaining_seconds": remaining,
            },
            ensure_ascii=False,
            sort_keys=True,
        ),
    )
    _record_span_metadata(
        {
            "capability_write_approval_consumed": True,
            "approval_id": str(row.get("id") or ""),
            "subtask_id": subtask_id,
            "capability_id": capability_id,
            "tenant_id": current_tenant_or_default(),
            "ttl_remaining_seconds": remaining,
        }
    )
    return row


def _parse_requested_scope(raw: str) -> Any:
    """从 supervisor LLM 输出取 plan 级 requested_scope（A2）；解析失败 → None（视同未声明）。"""
    outcome = parse_only(raw, schema=SubtasksPlan)
    if not outcome.ok or outcome.data is None:
        return None
    return outcome.data.requested_scope


def _effective_scope(state: LgRagState) -> frozenset[str]:
    """本轮有效 scope：声明∩裁剪已写 state 则用；缺键 = 未声明 = 隐式 allowlist。

    只收窄不放宽：返回值恒为 allowed_capability_ids 的子集（声明∩裁剪在
    supervisor 写入时已完成；这里的 allowlist 兜底同样取自 state）。
    """
    declared = state.get("delegation_scope")
    if isinstance(declared, list):
        return frozenset(str(c) for c in declared)
    return frozenset(str(c) for c in (state.get("allowed_capability_ids") or []))


async def _delegation_issue_block_reason(state: LgRagState, row: dict) -> str | None:
    """签发审批口径（Q2 裁定：只读自动 · 其余 HITL）；需审批 → 原因，自动放行 → None。

    有效 scope 内空集（模型声明收窄把 tool 自己裁掉）**不走 HITL**：不签发，
    tool_exec 直接 ok=False 走既有未知/无授权路径（SPEC §2 D5）。

    D1 消费门：sync 纯判定判出需审批后、返回拦截原因**前**，先消费 HITL store
    匹配的 approved 单据（三元组 + TTL · fail-closed）——命中即放行签发（None），
    未命中 / 读异常维持拦截。消费读在编排层本函数内，``issuance_policy_allows``
    保持纯函数零 IO（capability 包零触）。
    """
    tool = str(row.get("tool") or "").strip()
    if not tool:
        return None
    scope = _effective_scope(state)
    if tool not in scope:
        return None
    entry = _cap_registry().get(tool)
    if entry is None:
        return "委派签发审批：capability 未注册，无法判定审批口径（安全默认交人）"
    ok, why = dl.issuance_policy_allows([entry[0]], effective_scope=scope)
    if ok:
        return None
    sid = str(row.get("subtask_id") or "")
    if await _approval_consumed(state, subtask_id=sid, capability_id=tool):
        return None
    return f"委派签发需人工审批（{why}）"


def _issue_delegation_token(state: LgRagState, subtask: dict) -> dict | None:
    """为待分发 tool 子任务签发令牌（序列化 dict · 随 Send 载荷注入 state）。

    空集不签发（SPEC §2 D5）；缺密钥 / 非法约束 → 拒绝签发（安全默认）。
    同 subtask 重签发 = 新例生效 + 旧 nonce 作废（禁续期 · 签发序号单调）。
    """
    tool = str(subtask.get("tool") or "").strip()
    scope = _effective_scope(state)
    capability_set = {tool} & set(scope) if tool else set()
    sid = str(subtask.get("subtask_id") or "")
    if not capability_set:
        logger.info("delegation 有效 scope 内空集，不签发 subtask=%s tool=%s", sid, tool)
        return None
    token = dl.issue_token(
        capability_set=capability_set,
        subject_binding={
            # tenant 取自 ContextVar（阶段 T · C6）；身份不取模型产出
            "tenant_id": current_tenant_or_default(),
            "user_id": str(state.get("user_id") or ""),
            "run_id": _run_id_of(state),
            "subtask_id": sid,
        },
    )
    if token is None:
        return None
    return dl.token_to_dict(token)


def _missing_run_update(query: str) -> dict:
    return {
        "subtasks": [],
        "inflight_subtask_ids": [],
        "subtask_results": [
            {
                "error": "run_id 缺失，未签发 subtask_id，未派工人",
                "input": query,
            }
        ],
    }


def _error_terminal(item: dict, message: str) -> dict:
    sid = str(item.get("subtask_id") or "")
    row = {
        "id": sid,
        "subtask_id": sid,
        "type": str(item.get("type") or ""),
        "input": str(item.get("input") or ""),
        "error": message,
    }
    if item.get("alias"):
        row["alias"] = str(item["alias"])
    if item.get("tool"):
        row["tool"] = str(item["tool"])
    return row


def _delegation_blocked_terminal(item: dict, issue_reason: str) -> dict:
    """delegation 签发审批拦截 terminal（api-w-hitl-tenant-fix · T-fix-2）。

    blocked_by + hitl_required + **租户戳**（取当前租户上下文 ContextVar）——
    对齐 capability_write 闸既有 stamping 先例（:1881-1925 同形态 · HG-W-TENANT-DESIGN
    ② 守卫扩列后消费端查非空成立的落库前提；裁决③：历史 '' 行不回填，新单不再产
    空租户）。无请求上下文（CLI/扫描）时 ``current_tenant_or_default`` 回落试点 A，
    与 capability_write 闸同口径。
    """
    blocked = _error_terminal(item, issue_reason)
    blocked["blocked_by"] = _BLOCKED_BY_DELEGATION_ISSUE
    blocked["hitl_required"] = True
    blocked["tenant_id"] = current_tenant_or_default()
    return blocked


def _resolve_depends(
    row: dict,
    raw_deps: list,
    id_set: set[str],
    alias_map: dict[str, list[str]],
) -> tuple[list[str], str | None]:
    """把 depends_on 收成已签发 id。非法则整项不派。"""
    if not raw_deps:
        return [], None
    resolved: list[str] = []
    own = row["subtask_id"]
    for dep in raw_deps:
        token = str(dep).strip()
        if not token or token == "__invalid__":
            return [], "depends_on 无法解析，不派工人"
        if token == own or token == row.get("alias"):
            return [], "depends_on 指向自身，不派工人"
        if token in id_set:
            resolved.append(token)
            continue
        targets = alias_map.get(token) or []
        if len(targets) != 1:
            return [], "depends_on 指向计划外或无法解析，不派工人"
        target = targets[0]
        if target == own:
            return [], "depends_on 指向自身，不派工人"
        resolved.append(target)
    return resolved, None


def _cyclic_ids(rows: list[dict]) -> set[str]:
    """depends_on 成环的 subtask_id。前驱方向：项 → 它等待的 id。"""
    graph = {str(row["subtask_id"]): list(row.get("depends_on") or []) for row in rows}
    color = dict.fromkeys(graph, 0)
    cyclic: set[str] = set()

    def walk(node: str, stack: list[str]) -> None:
        color[node] = 1
        stack.append(node)
        for dep in graph.get(node, []):
            if dep not in graph:
                continue
            if color[dep] == 1:
                cyclic.update(stack[stack.index(dep) :])
            elif color[dep] == 0:
                walk(dep, stack)
        stack.pop()
        color[node] = 2

    for node in list(graph):
        if color[node] == 0:
            walk(node, [])
    return cyclic


def _cap_output_fields(tool_id: str) -> tuple[str, ...]:
    """能力声明的产出字段名清单；未注册 / 未声明 → ()（空 = 不裁剪）。"""
    if not tool_id:
        return ()
    entry = _cap_registry().get(tool_id)
    if entry is None:
        return ()
    return tuple(entry[0].output_fields or ())


def _trim_fields_by_output_fields(
    issued: list[dict],
    locked_rows: list[dict],
    *,
    skip: set[str],
) -> list[dict]:
    """计划期裁剪：声明字段 ∉ 相关能力 output_fields（非空时）→ 裁掉并留痕。

    纪律（task lg-rag-capability-output-schema · 承 step_contract「不替模型猜」）：
    只裁字段、不拒整 plan、不改语义；某步 / 某前驱声明**全被裁空 → 视同空 = 不校验**。
    produces 对照本步 tool；consumes_resolved 逐前驱对照前驱 tool。
    """
    by_sid = {str(row["subtask_id"]): row for row in locked_rows + issued}
    trims: list[dict] = []
    for row in issued:
        sid = str(row["subtask_id"])
        if sid in skip:
            continue
        produces = row.get("produces")
        if produces:
            declared = _cap_output_fields(str(row.get("tool") or ""))
            if declared:
                kept = [f for f in produces if f in declared]
                removed = [f for f in produces if f not in declared]
                if removed:
                    trims.append({"subtask_id": sid, "kind": "produces", "removed": removed})
                    if kept:
                        row["produces"] = kept
                    else:
                        row.pop("produces", None)
        consumes = row.get("consumes_resolved")
        if consumes:
            for dep in sorted(consumes):
                pred_tool = str((by_sid.get(dep) or {}).get("tool") or "")
                declared = _cap_output_fields(pred_tool)
                if not declared:
                    continue
                kept = [f for f in consumes[dep] if f in declared]
                removed = [f for f in consumes[dep] if f not in declared]
                if removed:
                    trims.append(
                        {"subtask_id": sid, "kind": "consumes", "dep": dep, "removed": removed}
                    )
                if kept:
                    consumes[dep] = kept
                else:
                    consumes.pop(dep)
            if not consumes:
                row.pop("consumes_resolved", None)
    return trims


def _issue_plan(
    items: list[dict],
    *,
    run_id: str,
    seq: int,
    alias_prefix: str = "t",
    cap: int = MAX_SUBTASKS,
    locked: list[dict] | None = None,
) -> tuple[list[dict], list[dict], int]:
    """先签发 subtask_id，再解析 depends_on / consumes。超出 cap 的项不签发。

    ``locked``（Q8）：不可变前缀。它**不参与签发**（沿用原来的 subtask_id，
    序列不回退、不复用），但参与别名解析——后缀可以依赖前缀、吃前缀的产出。

    ``alias_prefix``：首次规划 ``t``，重规划后缀 ``s``。别名**强制按位置编号**，
    模型写的 id 只用于**内部互相引用**的重映射；前缀别名不参与重映射，
    否则"后缀引用前缀 t1"会被误改成"后缀引用后缀 s1"。
    """
    locked_rows = [dict(row) for row in (locked or [])]
    issued: list[dict] = []
    remap: dict[str, str] = {}
    for offset, item in enumerate(items[:cap]):
        seq += 1
        old_alias = str(item.get("id") or f"{alias_prefix}{offset + 1}")
        alias = f"{alias_prefix}{offset + 1}"
        remap[old_alias] = alias
        sid = f"{run_id}:{seq}"
        stamped = {
            "id": sid,
            "subtask_id": sid,
            "alias": alias,
            "type": str(item.get("type") or "rag"),
            "input": str(item.get("input") or ""),
        }
        if item.get("tool"):
            stamped["tool"] = str(item["tool"])
        if item.get("args") is not None:
            stamped["args"] = dict(item["args"])
        produces = sc.normalize_produces(item.get("produces"))
        if produces:
            stamped["produces"] = produces
        raw_deps = item.get("depends_on") or []
        if not isinstance(raw_deps, list):
            raw_deps = ["__invalid__"]
        stamped["_raw_deps"] = raw_deps
        stamped["_raw_consumes"] = item.get("consumes") or {}
        issued.append(stamped)

    locked_aliases = {str(row.get("alias") or "") for row in locked_rows}

    def _tok(token: str) -> str:
        """前缀别名原样保留；其余走后缀重映射。"""
        if token in locked_aliases:
            return token
        return remap.get(token, token)

    alias_map: dict[str, list[str]] = {}
    for row in locked_rows + issued:
        alias_map.setdefault(str(row["alias"]), []).append(str(row["subtask_id"]))
    id_set = {str(row["subtask_id"]) for row in locked_rows + issued}
    illegal: dict[str, str] = {}
    for row in issued:
        raw_deps = [_tok(str(dep)) for dep in row.pop("_raw_deps")]
        resolved, err = _resolve_depends(row, raw_deps, id_set, alias_map)
        raw_cons = row.pop("_raw_consumes")
        if isinstance(raw_cons, dict):
            consumes = {_tok(str(k)): v for k, v in raw_cons.items()}
            by_sid = sc.resolve_consumes(sc.normalize_consumes(consumes), alias_map)
        else:
            by_sid = {}
        if by_sid:
            row["consumes_resolved"] = by_sid
            # consumes 隐含依赖：吃了谁的产出，就必须等谁跑完
            for sid in sc.consumes_implied_deps(by_sid):
                if sid not in resolved:
                    resolved.append(sid)
        row["depends_on"] = resolved
        if err:
            illegal[str(row["subtask_id"])] = err
    cyclic = _cyclic_ids([row for row in issued if str(row["subtask_id"]) not in illegal])
    for sid in cyclic:
        illegal[sid] = "depends_on 成环，不派工人"
    errors = [
        _error_terminal(row, illegal[str(row["subtask_id"])])
        for row in issued
        if str(row["subtask_id"]) in illegal
    ]
    trims = _trim_fields_by_output_fields(issued, locked_rows, skip=set(illegal))
    if trims:
        _record_span_metadata({"capability_output_fields_trimmed": trims})
    return issued, errors, seq


def _stamp_host_plan(
    state: LgRagState,
    items: list[dict],
    locked: list[dict] | None = None,
    preserved: list[dict] | None = None,
) -> dict:
    """校验后的项换成 Host id；``locked`` 前缀原样保留在最前面。

    ``preserved``（hitl-replan-carry-and-persist-guard 契约二）：HITL 解锁步
    的保号行，置 locked 之后、LLM 新后缀之前；plan_prefix_ids / recoverable_point
    仍仅随 locked。空 preserved 时输出与此前逐字节一致（契约三）。
    """
    run_id = _run_id_of(state)
    if not run_id:
        query = str(items[0].get("input") or "") if items else ""
        return _missing_run_update(query)
    locked_rows = [dict(row) for row in (locked or [])]
    preserved_rows = [dict(row) for row in (preserved or [])]
    seq = int(state.get("host_subtask_seq") or 0)
    cap = max(0, MAX_SUBTASKS - len(locked_rows) - len(preserved_rows))
    alias_prefix = "s" if locked_rows else "t"
    plan, errors, seq = _issue_plan(
        items,
        run_id=run_id,
        seq=seq,
        alias_prefix=alias_prefix,
        cap=cap,
        locked=locked_rows,
    )
    full = locked_rows + preserved_rows + plan
    out: dict = {
        "subtasks": full,
        "host_subtask_seq": seq,
        "inflight_subtask_ids": [],
        # Q8 可恢复点：前缀长度 = 下一个**真正要执行**的步骤下标。
        # 恢复 = 沿用前缀结果 + 从这里继续，不重跑前缀。
        "plan_prefix_ids": [str(row["subtask_id"]) for row in locked_rows],
        "recoverable_point": len(locked_rows),
    }
    if locked_rows or preserved_rows:
        # 重规划**成功**：新后缀已经替代了旧后缀，被替代的步骤连结果一起剪掉。
        # 不剪的话，上一轮那个失败步骤的记录会一直挂在 results 里：
        # critic 见 error 就 retry、aggregator 见 error 就写"部分失败"——
        # 可它早就被新计划取代了（**陈尸不清理会让整条链反复回环**）。
        # 注意只剪"不在新计划里"的：前缀结果必须完整留下。
        out["subtask_results"] = SubtaskResultBatch(
            [], {str(row["subtask_id"]) for row in full}, replace=True
        )
    if errors:
        out["subtask_results"] = SubtaskResultBatch(
            errors, {str(row["subtask_id"]) for row in full}
        )
    return out


def _locked_prefix(state: LgRagState) -> list[dict]:
    """不可变前缀（Q8）：已进入**成功终态**的计划项，按计划顺序。

    失败终态**不进**前缀——它没有需要保护的东西：没有副作用，也没有可取的结果，
    重规划可以重写它。要保护的是"已经产生了结果/副作用"的步骤：
    它们的 ``(tool, args)`` 决定幂等键，改了就是一次新的写（设计 §2.2）。
    """
    prefix_ids = set(success_terminal_ids(_plan_rows(state), state.get("subtask_results")))
    # 已获批准授权重跑的步骤**不再是不可变前缀** —— 这就是"批准"的唯一效果。
    # 摘掉它 ⇒ 可恢复点回退到那一步 ⇒ 下一轮重规划会重新执行它。
    prefix_ids -= {str(sid) for sid in (state.get("hitl_unlocked_ids") or [])}
    return [dict(row) for row in _plan_rows(state) if str(row["subtask_id"]) in prefix_ids]


def _unresolved_suffix(state: LgRagState, locked: list[dict]) -> list[dict]:
    """上一轮计划里**还没解决**的后缀步骤，原样带回（不重新签发 id）。

    未解决 = 没有终态，或终态是 error。成功终态要么已在 ``locked`` 里、
    要么不该出现在这里；两种情形都不重复带。

    **为什么不重新签发**：换 id 就等于换了一个新步骤，旧步骤的失败记录
    变成"计划外"，observe 按 plan_ids 一过滤就看不见了 —— 失败被抹掉。
    """
    locked_ids = {str(row.get("subtask_id") or "") for row in locked or []}
    unresolved = set(
        unresolved_suffix_ids(_plan_rows(state), state.get("subtask_results"), locked_ids)
    )
    return [dict(row) for row in _plan_rows(state) if str(row["subtask_id"]) in unresolved]


def _carry_plan(state: LgRagState, locked: list[dict], carried: list[dict]) -> dict:
    """沿用上一轮计划（前缀 + 未解决后缀），**不重新签发 subtask_id**。

    ``inflight_subtask_ids`` 交给随后的 ``_join_subtasks`` 重算：
    已终态的沿用项不会被再下发（join 见终态即跳过），只是继续保持可见。
    """
    locked_rows = [dict(row) for row in locked or []]
    full = locked_rows + [dict(row) for row in carried or []]
    return {
        "subtasks": full,
        "host_subtask_seq": int(state.get("host_subtask_seq") or 0),
        "inflight_subtask_ids": [],
        "plan_prefix_ids": [str(row["subtask_id"]) for row in locked_rows],
        "recoverable_point": len(locked_rows),
    }


def _unlocked_preserved_rows(state: LgRagState, locked: list[dict]) -> list[dict]:
    """replan 保号集合（hitl-replan-carry-and-persist-guard 契约一）：
    hitl_unlocked_ids ∩ **无任何终态**的计划步骤，原行原 subtask_id 带回。

    approved 步的旧结果已被 _apply_hitl_decision 剪掉 ⇒ 天然无终态；
    FP-8 防御：凡有终态（成功或失败）的 unlocked 步一律**不保号** ——
    带终态回计划会被跳过执行，授权语义被架空。保号行置于 locked 前缀
    之后、LLM 新后缀之前（_stamp_host_plan 负责落位）；LLM 不知晓
    保号行，故新后缀不得 depends_on 保号行（契约允许）。
    """
    unlocked = {str(s) for s in (state.get("hitl_unlocked_ids") or [])}
    if not unlocked:
        return []
    rows = _plan_rows(state)
    plan_ids = {str(row["subtask_id"]) for row in rows}
    terminal = _terminal_index(list(state.get("subtask_results") or []), plan_ids)
    locked_ids = {str(row.get("subtask_id") or "") for row in locked or []}
    return [
        dict(row)
        for row in rows
        if str(row["subtask_id"]) in unlocked
        and str(row["subtask_id"]) not in terminal
        and str(row["subtask_id"]) not in locked_ids
    ]


# 失败摘要行截断上限：比终态摘要（200）宽——纠错回路的关键信息（死因 +
# 前驱可用字段清单）必须活下来，截掉了重规划还是只能猜字段名（run cb2548）。
_FAILURE_LINE_MAX_CHARS = 400

# 带内逃生口指引（task lg-rag-gate-produces-unfulfilled · 实证 run d3a49）：
# 已终态前驱进锁定前缀、_stamp_host_plan 逐字保留 ⇒ 重规划**改不动**它的
# produces 声明（实证：locked 行原样前置，LLM 项一律签发新 id）——唯一合法
# 出路是以修正后的 produces 重发等价**新步**，或只消费实际产出字段。
_REISSUE_PREDECESSOR_REASONS = (sc.BLOCKED_CONTRACT_MISSING, sc.BLOCKED_PREFIX_TOUCH)
_REISSUE_PREDECESSOR_GUIDANCE = (
    "指引：若失败因前驱声明的 produces 字段未兑现——已终态前驱已锁定不可改写："
    "以修正后的 produces 重发前驱步（作为新步、新 subtask_id），"
    "或让后续步只消费前驱实际产出字段；勿照抄原声明。"
)


def _failed_row_line(row: dict, term: dict | None) -> str:
    """失败步行：与锁定行同格式（id / type / input / tool）+ 失败摘要行。

    supervisor-replan-error-feedback（实测 run cb2548）：terminal 含
    error/blocked_by 时追加「→ 失败：{blocked_by}：{error 截断}」——
    模型至少知道这步死了、死因是什么。blocked_by 缺失（工人执行失败等
    无拦截码形态）时退化为「→ 失败：{error}」，不伪造空段。
    """
    alias = str(row.get("alias") or row.get("subtask_id") or "")
    line = f"- {alias}（{row.get('type') or 'rag'}）：{row.get('input') or ''}"
    if row.get("tool"):
        line += f" [tool={row['tool']}]"
    if term and ("error" in term or term.get("blocked_by")):
        error_text = str(term.get("error") or "")
        if len(error_text) > _FAILURE_LINE_MAX_CHARS:
            error_text = error_text[:_FAILURE_LINE_MAX_CHARS] + "…(截断)"
        blocked_by = str(term.get("blocked_by") or "")
        if blocked_by:
            line += f"\n  → 失败：{blocked_by}：{error_text}"
        else:
            line += f"\n  → 失败：{error_text}"
    return line


def _format_prefix_block(
    locked: list[dict],
    terminals: dict[str, dict] | None = None,
    failed: list[dict] | None = None,
) -> str:
    """前缀摘要：只读视图（id / type / input / tool）+ 终态结果摘要。

    approved-replan-quality：带上已完成步的终态 output 摘要（截断防爆），
    破「LLM 不知晓已完成步产出」——需要数据时 consumes 引用即可，
    不为重取产出重复规划同语义步骤（SPEC §9 序1）。

    supervisor-replan-error-feedback：failed（上一轮失败终态步，按计划
    顺序）追加失败摘要段——破「重规划照抄同一错误声明」（run cb2548：
    write 步被契约闸拦，重规划两轮原样照抄同一错误 consumes 声明）。
    失败步**不在锁定前缀内**（失败终态不进 _locked_prefix），单列一段
    避免被模板抬头「已完成且不可更改」误标——它需要被修正后重新规划。
    failed 为空时输出与此前逐字节一致（主路径零 diff 钉死）。
    """
    lines = []
    for row in locked:
        alias = str(row.get("alias") or row.get("subtask_id") or "")
        line = f"- {alias}（{row.get('type') or 'rag'}）：{row.get('input') or ''}"
        if row.get("tool"):
            line += f" [tool={row['tool']}]"
        term = (terminals or {}).get(str(row.get("subtask_id") or ""))
        if term and "output" in term:
            summary = json.dumps(term.get("output"), ensure_ascii=False, default=str)
            if len(summary) > 200:
                summary = summary[:200] + "…(截断)"
            line += f"\n  → 终态结果：{summary}"
        lines.append(line)
    if failed:
        if lines:
            lines.append("")
        lines.append(
            "以下步骤上一轮执行失败（未锁定，需在新后缀中修正声明后重新规划；"
            "失败原因如下，切勿原样照抄上一轮的 consumes/produces 声明）："
        )
        for row in failed:
            term = (terminals or {}).get(str(row.get("subtask_id") or ""))
            lines.append(_failed_row_line(row, term))
        if any(
            str(
                ((terminals or {}).get(str(row.get("subtask_id") or "")) or {}).get(
                    "blocked_by"
                )
                or ""
            )
            in _REISSUE_PREDECESSOR_REASONS
            for row in failed
        ):
            lines.append(_REISSUE_PREDECESSOR_GUIDANCE)
    return "\n".join(lines) or "（无）"


def _format_preserved_block(preserved: list[dict]) -> str:
    """保号行执行摘要（approved-replan-quality）：已批准待重跑步对 LLM 可见。

    SPEC §9 序1 现象①：LLM 不知晓保号行 → 重规划同语义写步孪生 →
    二次审批 / 二次执行。注入名单后 LLM 不得为其重复规划（结构护栏
    _write_replay_guard 在分发层兜底，双保险）。空集合返空串。
    """
    if not preserved:
        return ""
    lines = [
        "以下步骤已获人工批准、正等待重跑（系统保留原编号并将自动执行；"
        "切勿为同一目的再规划新步骤或孪生步骤）："
    ]
    for row in preserved:
        sid = str(row.get("subtask_id") or "")
        line = f"- {sid}（{row.get('type') or 'rag'}）：{row.get('input') or ''}"
        if row.get("tool"):
            line += f" [tool={row['tool']}]"
        lines.append(line)
    return "\n".join(lines)


def _plan_rows(state: LgRagState) -> list[dict]:
    rows = []
    for item in state.get("subtasks") or []:
        if isinstance(item, dict) and str(item.get("subtask_id") or "").strip():
            rows.append(item)
    return rows


def _terminal_index(results: list, plan_ids: set[str]) -> dict[str, dict]:
    found: dict[str, dict] = {}
    for row in results:
        if not isinstance(row, dict):
            continue
        sid = str(row.get("subtask_id") or "").strip()
        if sid not in plan_ids or sid in found:
            continue
        if "output" in row or "error" in row:
            found[sid] = row
    return found


def _guard_write_key(row: dict) -> str | None:
    """write 孪生护栏 canonical 键：仅 side_effect ∈ WRITE_SIDE_EFFECTS 的行。

    canonical = tool + 规范化入参（args 优先，兼容 plan 层 input；sort_keys
    稳定序列化）。未注册 / 非 write / 序列化失败 → None（不护栏，维持原
    路径——护栏是重放优化不是新闸门，签发门/消费门 fail-closed 不变）。
    """
    tool = str(row.get("tool") or "").strip()
    if not tool:
        return None
    entry = _cap_registry().get(tool)
    if not entry:
        return None
    if str(getattr(entry[0], "side_effect", "") or "") not in WRITE_SIDE_EFFECTS:
        return None
    payload = row.get("args")
    if not isinstance(payload, dict):
        payload = row.get("input")
    try:
        canonical = json.dumps(payload, sort_keys=True, ensure_ascii=False, default=str)
    except (TypeError, ValueError):
        return None
    return f"{tool}\x00{canonical}"


def _write_success_call_keys(done: dict[str, dict], by_id: dict[str, dict]) -> dict[str, str]:
    """done 内 write **成功**终态的 canonical → sid 索引。

    error 终态不入索引：失败的已批准写重跑是既有语义，不在护栏面。
    """
    keys: dict[str, str] = {}
    for tsid, term in done.items():
        if "output" not in term or "error" in term:
            continue
        trow = by_id.get(tsid)
        if not trow:
            continue
        key = _guard_write_key(trow)
        if key is not None:
            keys.setdefault(key, tsid)
    return keys


def _write_blocked_call_keys(done: dict[str, dict], by_id: dict[str, dict]) -> dict[str, str]:
    """done 内**在途写单步**（被 capability_write 闸拦下 · hitl_required）的
    canonical → sid 索引（fix-seen-surface-idempotency · issue #335 巡检层
    守卫数据面）。重启后重规划孪生步命中即继承在途终态（不重复派发——
    重复派发 = 重复拉起噪音 + persist 面重复建单风险）。成功终态不入
    （走 replay-guard 成功面）。
    """
    keys: dict[str, str] = {}
    for tsid, term in done.items():
        if str(term.get("blocked_by") or "") != _BLOCKED_BY_CAPABILITY_WRITE:
            continue
        if term.get("hitl_required") is not True:
            continue
        trow = by_id.get(tsid)
        if not trow:
            continue
        key = _guard_write_key(trow)
        if key is not None:
            keys.setdefault(key, tsid)
    return keys


def _write_intent_live_key(*, capability_id: str, write_intent: Any) -> tuple[str, str] | None:
    """写意图幂等键（fix-seen-surface-idempotency · status 位真源）。

    = (capability_id, write_intent.args_summary)——args_summary 由写闸以
    ``_cap_args_summary`` 确定性序列化随单落库（阶段 W 写意图结构钉死），
    同写意图跨 sid 可比。缺 capability_id / write_intent 非 dict → None
    （不入守卫面，维持原精确 sid 路径）。幂等键语义 = status 位（库面 live
    单）∧ seen_surface 位（本轮已带回）双条件（HG-WRITE-TICKET-IDEMPOTENCY-
    DESIGN ② 签认 · 缺一不可：只看 seen 位 = 本缺陷；只看 status 位 =
    不同 args 的合法写被误并）。
    """
    cap = str(capability_id or "").strip()
    if not cap:
        return None
    if not isinstance(write_intent, dict):
        return None
    return (cap, str(write_intent.get("args_summary") or ""))


async def _join_subtasks(state: LgRagState) -> dict:
    """收口上一批：漏带回的 id 写错误终态；预算耗尽则补齐剩余 id，不再开新批。"""
    plan = _plan_rows(state)
    plan_ids = {str(row["subtask_id"]) for row in plan}
    by_id = {str(row["subtask_id"]): row for row in plan}
    done = _terminal_index(list(state.get("subtask_results") or []), plan_ids)
    inflight = [
        str(sid) for sid in (state.get("inflight_subtask_ids") or []) if str(sid) in plan_ids
    ]
    extras: list[dict] = []
    for sid in inflight:
        if sid in done:
            continue
        extras.append(_error_terminal(by_id[sid], "工人未带回匹配的 subtask_id，已写错误终态"))
        done[sid] = extras[-1]
    # 不可变前缀（Q8）：**读声明**，不从"有 output 的终态"反推。
    # 反推会把"本轮刚跑完的前驱"也算成前缀，于是任何缺字段都变成
    # prefix_touch_required —— contract_missing_field 永远走不到（死分支），
    # 而 Q4 要的"别把坏数据喂下去"和 Q8 要的"改历史得交人"被混成一件事。
    prefix_ids = frozenset(str(sid) for sid in (state.get("plan_prefix_ids") or []))
    updates: dict = {}
    if is_supervisor_budget_exhausted(state):
        for row in plan:
            sid = str(row["subtask_id"])
            if sid in done:
                continue
            extras.append(_error_terminal(row, "supervisor 总步预算耗尽，未终态子任务写入错误终态"))
            done[sid] = extras[-1]
        updates["inflight_subtask_ids"] = []
    else:
        ready: list[str] = []
        blocked_meta: dict[str, int] = {}
        # 判定 3 收窄留痕（task lg-rag-gate-produces-unfulfilled · 实证 run
        # d3a49）：produces 未兑现但未被本步 consumes 引用 → 放行，观察写 span
        # （复用既有 _record_span_metadata 通道，不新增事件类型）。
        unfulfilled_obs: list[dict] = []
        # hitl-approved-replan-quality（契约一）：write 成功终态 canonical
        # 索引 + 本批已派发 write 键——孪生步结构护栏数据面。delegation-
        # naming-boundary D2：门控自 _delegation_active() 解耦至独立开关
        # LG_RAG_WRITE_REPLAY_GUARD_ENABLED（默认开 · 关时整段不建索引，
        # 恢复 master 基线零 diff）。
        write_done_keys = (
            _write_success_call_keys(done, by_id) if _write_replay_guard_enabled() else {}
        )
        # fix-seen-surface-idempotency（巡检层守卫 · 决策点① 案 A）：在途写单步
        # （blocked 终态在 checkpoint 面可见）的 canonical 索引——重启后重规划
        # 孪生步命中即继承在途终态，不重复派发。
        write_blocked_keys = (
            _write_blocked_call_keys(done, by_id) if _write_replay_guard_enabled() else {}
        )
        batch_write_keys: dict[str, str] = {}
        for row in plan:
            sid = str(row["subtask_id"])
            if sid in done:
                continue
            deps = [str(dep) for dep in (row.get("depends_on") or [])]
            if not all(dep in done for dep in deps):
                continue
            # ★ 前驱失败即终止（Q4 缺陷二）：error 终态不再算"前驱已完成"。
            #   契约校验也在这里 —— 喂入前判，不合格一次工具都不打。
            reason, detail = sc.gate(row=row, terminals=done, by_id=by_id, prefix_ids=prefix_ids)
            if reason:
                blocked = _error_terminal(row, f"{sc.label_of(reason)}（{detail}）")
                blocked["blocked_by"] = reason
                if sc.needs_hitl(reason):
                    blocked["hitl_required"] = True
                extras.append(blocked)
                # 写进 done ⇒ 依赖它的后继同批级联停（不是等下一轮）
                done[sid] = blocked
                blocked_meta[reason] = blocked_meta.get(reason, 0) + 1
                continue
            for item in sc.unfulfilled_produces(row=row, terminals=done, by_id=by_id):
                unfulfilled_obs.append({"subtask_id": sid, **item})
            # hitl-approved-replan-quality（SPEC §9 序1 · 契约一）：write
            # 孪生步结构护栏——**先于签发检查**：命中异 sid 同 canonical
            # 成功终态即 guard-skip（不派发 · 不消费单据 · 不产孤儿 HITL
            # 单），output 照抄原终态 + replay_of 台账。FP-3：approved
            # unlocked 步自身旧结果已被剪掉（无终态）⇒ 天然不命中自身。
            write_key = None
            if _write_replay_guard_enabled() and str(row.get("type") or "") == "tool":
                write_key = _guard_write_key(row)
                if write_key is not None:
                    orig_sid = write_done_keys.get(write_key)
                    if orig_sid is not None and orig_sid != sid:
                        skipped = _base_result(row)
                        try:
                            skipped["output"] = copy.deepcopy(done[orig_sid].get("output"))
                        except Exception:
                            skipped["output"] = done[orig_sid].get("output")
                        skipped["write_replay_guard_skip"] = True
                        skipped["replay_of"] = orig_sid
                        extras.append(skipped)
                        done[sid] = skipped
                        logger.info(
                            "write_replay_guard_skip %s",
                            json.dumps(
                                {
                                    "subtask_id": sid,
                                    "replay_of": orig_sid,
                                    "capability_id": str(row.get("tool") or ""),
                                },
                                ensure_ascii=False,
                            ),
                        )
                        _record_span_metadata(
                            {
                                "write_replay_guard_skip": True,
                                "subtask_id": sid,
                                "replay_of": orig_sid,
                            }
                        )
                        continue
                    if write_key in batch_write_keys:
                        # 同批双胞胎：首发照派，次发本轮挂起——下一 join
                        # pass 见首发终态再走 guard-skip（同轮重入保证）。
                        continue
                    # fix-seen-surface-idempotency（巡检层守卫）：同写意图的
                    # 在途写单步被重规划孪生时，孪生步**继承在途终态**
                    # （replay_of 溯源 · 不派发不消费）——重复派发即重复拉起
                    # 噪音（写闸 fail-closed 再拦 + persist 面重复建单风险）。
                    orig_blocked = write_blocked_keys.get(write_key)
                    if orig_blocked is not None and orig_blocked != sid:
                        inherited = copy.deepcopy(done[orig_blocked])
                        inherited["subtask_id"] = sid
                        inherited["id"] = sid
                        inherited["replay_of"] = orig_blocked
                        extras.append(inherited)
                        done[sid] = inherited
                        logger.info(
                            "write_ticket_twin_inherited %s",
                            json.dumps(
                                {
                                    "subtask_id": sid,
                                    "replay_of": orig_blocked,
                                    "capability_id": str(row.get("tool") or ""),
                                },
                                ensure_ascii=False,
                                sort_keys=True,
                            ),
                        )
                        continue
            # Host V1-A：委派签发审批（Q2：只读自动 · 其余 HITL_REQUIRED）。
            # off 模式整段短路（现状零 diff）；审批拦截复用既有 HITL 回路留痕。
            if _delegation_active() and str(row.get("type") or "") == "tool":
                issue_reason = await _delegation_issue_block_reason(state, row)
                if issue_reason:
                    blocked = _delegation_blocked_terminal(row, issue_reason)
                    extras.append(blocked)
                    done[sid] = blocked
                    blocked_meta["delegation_issue_hitl_required"] = (
                        blocked_meta.get("delegation_issue_hitl_required", 0) + 1
                    )
                    dl.audit_delegation(
                        dl.AUDIT_TOKEN_ISSUE_HITL_REQUIRED,
                        subtask_id=sid,
                        tool=str(row.get("tool") or ""),
                    )
                    continue
            if write_key is not None:
                batch_write_keys[write_key] = sid  # 确认派发才登记首发
            ready.append(sid)
        updates["inflight_subtask_ids"] = ready
        if blocked_meta:
            _record_span_metadata(
                {
                    "step_contract_blocked": sum(blocked_meta.values()),
                    "step_contract_blocked_by_reason": blocked_meta,
                }
            )
        if unfulfilled_obs:
            _record_span_metadata({"step_contract_produces_unfulfilled": unfulfilled_obs})
    if extras:
        updates["subtask_results"] = SubtaskResultBatch(extras, plan_ids)
    return updates


def _bind_upstream(
    state: LgRagState, subtask: dict
) -> tuple[dict | None, str | None, list[str], list[str]]:
    """按 ``consumes`` 把前驱产出注入本步（Q4 缺陷一：之前根本没串数据）。

    ``type=tool`` → 注入 ``args[字段名]``（**覆盖** planner 写死的占位值）；
    ``type=rag|extract`` → 在 input 尾部追加编排层生成的固定上下文块。
    取哪些字段由模型声明，**怎么注入由代码决定**。
    """
    consumes = subtask.get("consumes_resolved") or {}
    if not consumes:
        return None, None, [], []
    plan = _plan_rows(state)
    terminals = _terminal_index(
        list(state.get("subtask_results") or []),
        {str(row["subtask_id"]) for row in plan},
    )
    sid_to_alias = {
        str(row["subtask_id"]): str(row.get("alias") or row["subtask_id"]) for row in plan
    }
    values = sc.collect_values(
        consumes_by_sid=consumes, terminals=terminals, sid_to_alias=sid_to_alias
    )
    if not values:
        return None, None, [], []
    if str(subtask.get("type") or "") == "tool":
        return (
            sc.bind_args(subtask.get("args"), values),
            None,
            sc.bound_field_names(values),
            [],
        )
    text, included = sc.bind_input(
        str(subtask.get("input") or ""), values, sid_to_alias=sid_to_alias
    )
    return None, text, included, sc.dropped_fields(values, included)


def _worker_state(state: LgRagState, subtask: dict) -> dict:
    task = dict(subtask)
    args, text, bound, dropped = _bind_upstream(state, subtask)
    if args is not None:
        task["args"] = args
    if text is not None:
        task["input"] = text
    if bound:
        task["bound_fields"] = bound
    # 被整块预算挤掉的字段必须说出来——静默少给等于给了一份看起来完整的数据
    if dropped:
        task["bound_dropped_fields"] = dropped
    payload: dict = {
        "messages": list(state.get("messages") or []),
        "assigned_subtask": task,
        "subtasks": list(state.get("subtasks") or []),
        "supervisor_step_count": int(state.get("supervisor_step_count") or 0),
    }
    # Send 载荷即工人所见的全部 state：run_id 必须随载荷下发——写审批消费门
    # ``_write_execution_approval`` 经 ``_run_id_of(state)`` 取值，缺键空串
    # fail-closed ⇒ HITL resume 后重下发永远再拦（fix-worker-state-send-run-id ·
    # 案 A · HG-WORKER-STATE-RUN-ID-DESIGN）。非空才写（镜像下两行可选键先例）：
    # 空 run_id 不写入，防空串键污染工人视野（FP-7）。
    run_id = _run_id_of(state)
    if run_id:
        payload["run_id"] = run_id
    if state.get("supervisor_started_at") is not None:
        payload["supervisor_started_at"] = state["supervisor_started_at"]
    if state.get("supervisor_budget_exhausted") is True:
        payload["supervisor_budget_exhausted"] = True
    return payload


# ---------------------------------------------------------------------------
# Supervisor（DESIGN §3）
# ---------------------------------------------------------------------------


class SupervisorPlanError(RuntimeError):
    """supervisor-first（D2）：首次规划失败（无 locked 前缀）fail-closed 信号。

    触发面：LLM 异常/超时、输出无法解析、plan 含非法 tool id —— 整 plan 作废，
    由 SSE 边界捕获映射为单帧 ``error{stage=supervisor_plan}`` 后收终态（停图）。
    灾备 env ``LG_RAG_SUPERVISOR_PLAN_ON_FAIL=single_rag`` 时不抛，走降级单 rag；
    重规划例外（``if locked:``）沿用未解决后缀，不进入本路径（判据不扩）。
    """


ENV_SUPERVISOR_PLAN_ON_FAIL = "LG_RAG_SUPERVISOR_PLAN_ON_FAIL"


def _supervisor_plan_on_fail() -> str:
    """灾备开关：``error``（默认）| ``single_rag``；非法值回退 ``error``（fail-closed）。"""
    raw = os.environ.get(ENV_SUPERVISOR_PLAN_ON_FAIL, "error").strip().lower()
    if raw in ("error", "single_rag"):
        return raw
    logger.warning(
        "lg_rag supervisor plan_on_fail env 非法值 %r，回退默认 error（fail-closed）",
        raw,
    )
    return "error"


async def supervisor_node(state: LgRagState) -> dict:
    """LLM 拆解复合问题为 ≤4 子任务；首次失败/非法/非法 tool id → fail-closed（D2）。

    可见集 = ``list_capabilities(filter)`` ∩ ``state.allowed_capability_ids``（S1）；
    空 allowlist / 缺字段 → 整 plan fallback 单 rag；``type=tool`` id 须在本轮可见集内。
    选型：complete 一次 + ``parse_only``（见 ``_parse_subtasks``），
    不用 ``acomplete_structured`` 以免本波双重 LLM。
    有非空 run_id 才签发 Host ``subtask_id``；缺失则不派工人、不用模型 id 当关联键。
    """
    bump = bump_supervisor_step(state)
    query = _last_user_text(state["messages"])
    if not _run_id_of(state):
        _record_span_metadata(
            {
                "capability_catalog_count": 0,
                "subtask_count": 0,
                "subtask_types": [],
                "supervisor_fallback": True,
                "structured_output_fallback": True,
                "supervisor_missing_run_id": True,
                "supervisor_raw": "",
            }
        )
        return {**bump, **_missing_run_update(query)}
    # Q8：重规划入口先算不可变前缀。空 ⇒ 首次规划，走原路径。
    locked = _locked_prefix(state)
    # hitl-replan-carry-and-persist-guard：HITL 解锁步保号集合（契约一·P=unlocked∩无终态）。
    preserved = _unlocked_preserved_rows(state, locked)
    caps, allowed_ids = _resolve_supervisor_visible_caps(state)
    if state.get("allowed_capability_ids") is None or not allowed_ids:
        span_meta: dict = {
            "capability_catalog_count": 0,
            "subtask_count": 1,
            "subtask_types": ["rag"],
            "supervisor_fallback": True,
            "structured_output_fallback": True,
            "supervisor_empty_allowlist": True,
            "supervisor_raw": "",
        }
        _record_span_metadata(span_meta)
        # 已有前缀时不退化成"单 rag"：那会把已完成步骤的关联键抹掉
        items = [] if locked else [{"id": "t1", "type": "rag", "input": query}]
        stamped = _stamp_host_plan(state, items, locked=locked, preserved=preserved)
        return {**bump, **stamped}
    catalog_block = _format_capability_catalog(caps)
    if locked or preserved:
        # approved-replan-quality：前缀带终态结果摘要 + 注入保号行名单（去盲）
        # hitl-n1-locked-branch-inject（方案 A）：locked 空 + preserved 非空
        # （hitl 批准单步写形态 · 40 run1 实证）同走 suffix 注入面——locked 空
        # 不蕴涵 preserved 空，else 基础 prompt 会让保号行对 LLM 不可见（N1）。
        # prefix_block 退化为「（无）」字面（_format_prefix_block([]) 已处理）；
        # preserved 空 ⇒ 仍走 else 基础模板，主路径逐字节零 diff（FP-3 钉死）。
        _plan_ids = {str(r["subtask_id"]) for r in _plan_rows(state)}
        _terminals = _terminal_index(list(state.get("subtask_results") or []), _plan_ids)
        # supervisor-replan-error-feedback（run cb2548）：失败终态步（被拦/
        # 工人失败）不进锁定前缀，但它们的死因必须反哺重规划 prompt——
        # 否则模型不知道上一轮哪步死了、为什么死，只能照抄同一错误声明。
        # 无失败步时 _failed 为空 ⇒ prompt 逐字节零 diff（FP 口径沿用
        # preserved_block 先例，由专项测试钉死）。
        _locked_ids = {str(r.get("subtask_id") or "") for r in locked}
        _failed = [
            row
            for row in _plan_rows(state)
            if str(row["subtask_id"]) not in _locked_ids
            and (
                "error" in (_terminals.get(str(row["subtask_id"])) or {})
                or (_terminals.get(str(row["subtask_id"])) or {}).get("blocked_by")
            )
        ]
        system_content = _build_supervisor_suffix_system(
            catalog_block,
            _format_prefix_block(locked, _terminals, failed=_failed),
            max(0, MAX_SUBTASKS - len(locked)),
            preserved_block=_format_preserved_block(preserved),
        )
    else:
        system_content = _build_supervisor_system(catalog_block)
    raw = ""
    subtasks: list[dict] | None = None
    invalid_tool_id = False
    with trace_span("supervisor", run_type="chain"):
        try:
            provider = get_llm_provider(_ROUTER_PROVIDER)
            raw = await provider.complete(
                [
                    LlmMessage(role="system", content=system_content),
                    LlmMessage(role="user", content=query),
                ],
                model=_ROUTER_MODEL,
            )
            subtasks = _parse_subtasks(raw)
            if subtasks is not None and not _subtasks_have_valid_tool_ids(subtasks, allowed_ids):
                invalid_tool_id = True
                logger.warning(
                    "lg_rag supervisor plan 含非法 tool id，fallback 单 rag raw=%r",
                    raw[:200],
                )
                subtasks = None
        except Exception as exc:  # LLM 异常/超时 → 规划失败（默认 fail-closed，见下）
            logger.warning("lg_rag supervisor LLM 失败 run_id=%s err=%r", _run_id_of(state), exc)
    fallback = subtasks is None
    if fallback and raw and not invalid_tool_id:
        logger.warning(
            "lg_rag supervisor 输出非法 run_id=%s raw=%r", _run_id_of(state), raw[:200]
        )
    degraded = False
    if fallback:
        if locked:
            # 前缀已锁定：拿不到后缀就**沿用上一轮未解决的后缀**，
            # 绝不退化成单 rag，也绝不把计划收缩成只剩前缀。
            #
            # 收缩为什么是错的（实测出来的，不是推演）：后缀一空，
            # 那些"还没解决"的步骤就从计划里消失了 —— 它们的失败/未终态记录
            # 随即变成**计划外 id**，observe 按 plan_ids 过滤看不见，
            # aggregator 更看不见，于是结论写成"已覆盖全部子任务"。
            # 失败被静默抹掉，正是外层 ReAct 要防的那一类事。
            #
            # 沿用而不是重签发：**不换 subtask_id**，所以已终态的失败步骤
            # 不会被 join 重新下发（join 见终态即跳过），只是继续保持可见。
            carried = _unresolved_suffix(state, locked)
            logger.warning(
                "lg_rag supervisor 重规划输出非法，沿用前缀 %d 步 + 未解决后缀 %d 步 raw=%r",
                len(locked),
                len(carried),
                raw[:200],
            )
            if carried:
                span_meta = {
                    "capability_catalog_count": len(caps),
                    "subtask_count": len(locked) + len(carried),
                    "supervisor_fallback": True,
                    "structured_output_fallback": True,
                    "supervisor_raw": raw[:200],
                    "plan_prefix_len": len(locked),
                    "replan_suffix_only": True,
                    "replan_carried_unresolved": len(carried),
                }
                _record_span_metadata(span_meta)
                return {**bump, **_carry_plan(state, locked, carried)}
            subtasks = []
            fallback = False
        else:
            # supervisor-first（D2）：首次规划失败（无 locked 前缀）默认 **fail-closed** ——
            # 静默单 rag 会把「规划失败」包装成「成功给出单 rag 计划」，aggregator
            # 冒充成功路径（SPEC failure_paths FP）。抛 SupervisorPlanError 停图，
            # 由 SSE 边界映射单帧 error{stage=supervisor_plan} 收终态。
            # 判据不扩：locked 空 + preserved 非空（HITL 批准待重跑形态）同归 error（FP-1b）。
            if _supervisor_plan_on_fail() != "single_rag":
                fail_meta: dict = {
                    "capability_catalog_count": len(caps),
                    "subtask_count": 0,
                    "subtask_types": [],
                    "supervisor_fallback": True,
                    "structured_output_fallback": True,
                    "supervisor_plan_failed": True,
                    "supervisor_raw": raw[:200],
                    "plan_prefix_len": len(locked),
                }
                if invalid_tool_id:
                    fail_meta["supervisor_invalid_tool_id"] = True
                _record_span_metadata(fail_meta)
                logger.warning(
                    "lg_rag supervisor 首次规划失败，fail-closed 停图 run_id=%s raw=%r",
                    _run_id_of(state),
                    raw[:200],
                )
                raise SupervisorPlanError(
                    "supervisor first plan failed (no locked prefix); "
                    "set LG_RAG_SUPERVISOR_PLAN_ON_FAIL=single_rag to degrade"
                )
            # 灾备：single_rag 降级 —— 全程打 degraded 标记（state + span + SSE 终帧），
            # 不冒充全量成功；delegation_scope 不写入（不扩权）。
            degraded = True
            logger.warning(
                "lg_rag supervisor 首次规划失败，灾备降级单 rag run_id=%s raw=%r",
                _run_id_of(state),
                raw[:200],
            )
            subtasks = [{"id": "t1", "type": "rag", "input": query}]
    stamped = _stamp_host_plan(state, subtasks or [], locked=locked, preserved=preserved)
    if degraded:
        stamped["supervisor_degraded"] = True
    issued = stamped.get("subtasks") or []
    # Host V1-A · A2：声明∩裁剪（只收窄不放宽 · off 模式整段短路零 diff）。
    # 有效 scope 写 state，作签发 capability_set 上界；越界剔除 + 截断留痕。
    # 交集输入 allowed_ids 即 Builder 直出 allowlist（candidates ∩ 基线可见集
    # 直接求交 · scenario 阶段已摘除 2026-10-20），经
    # _resolve_supervisor_visible_caps 传导至此 ⇒ delegation_scope =
    # requested_scope ∩ allowlist（只收窄不放宽 · 委派令牌不越 allowlist）。
    scope_span: dict = {}
    if _delegation_active() and not fallback and subtasks:
        requested_scope = _parse_requested_scope(raw)
        # 已声明 → 声明∩裁剪后写 state；未声明 → 不写键（隐式 allowlist 兼容现状）
        if isinstance(requested_scope, list):
            scope, stripped, truncated = effective_scope_from_requested(
                requested_scope, allowed_ids
            )
            stamped["delegation_scope"] = scope
            scope_span = {
                "delegation_scope_declared": True,
                "delegation_scope_count": len(scope),
            }
            if stripped:
                scope_span["delegation_scope_stripped"] = stripped
            if truncated:
                scope_span["delegation_scope_truncated"] = len(truncated)
    span_meta = {
        "capability_catalog_count": len(caps),
        "subtask_count": len(issued),
        "subtask_types": [s["type"] for s in issued],
        "supervisor_fallback": fallback,
        # 与 supervisor_fallback 并存（SPEC §5）
        "structured_output_fallback": fallback,
        "supervisor_raw": raw[:200],
        # Q8 可恢复点
        "plan_prefix_len": len(locked),
        "recoverable_point": int(stamped.get("recoverable_point") or 0),
    }
    if locked:
        span_meta["replan_suffix_only"] = True
    if degraded:
        span_meta["supervisor_degraded"] = True
    if invalid_tool_id:
        span_meta["supervisor_invalid_tool_id"] = True
    span_meta.update(scope_span)
    _record_span_metadata(span_meta)
    return {**bump, **stamped}


def route_next_subtask(state: LgRagState) -> str | list[Send]:
    """按 inflight 一次下发多个工人；预算耗尽或没有待发 id → **observe**。

    主闸仍是总步 / 旗标 / 墙钟：即使计划未收齐也返回 ``"observe"``，
    不直跳 END、也不直跳 aggregate。收齐由 join 写入 inflight 为空来表达，
    不用结果条数。
    """
    if is_supervisor_budget_exhausted(state):
        return "observe"
    by_id = {str(row["subtask_id"]): row for row in _plan_rows(state)}
    delegation_on = _delegation_active()
    sends: list[Send] = []
    for sid in state.get("inflight_subtask_ids") or []:
        subtask = by_id.get(str(sid))
        if subtask is None:
            continue
        node = _TYPE_TO_NODE.get(str(subtask.get("type") or ""), "rag_subtask")
        payload = _worker_state(state, subtask)
        # Host V1-A：分发路径逐子任务签发（off = 不签发零 diff）；
        # 重发 / replan 走到这里一律重签发新例（旧 nonce 作废 · 禁续期）。
        if delegation_on and node == "tool_exec":
            # Send 载荷即工人所见的全部 state：主体绑定的 run_id 必须随载荷
            # 下发，否则验签侧 ctx.run_id 为空 ⇒ R-f 误拒（非篡改）。
            payload["run_id"] = _run_id_of(state)
            token_payload = _issue_delegation_token(state, subtask)
            if token_payload is not None:
                payload["delegation_token"] = token_payload
        sends.append(Send(node, payload))
    if not sends:
        # ★ 不再直接 aggregate。没有待发步骤 ≠ 这一轮满足了原始问题：
        #   可能是后缀为空、可能全被拦下、可能统统失败。
        #   先交给 observe 做**执行层收口**，由它决定"再来一轮"还是"收工出结论"。
        return "observe"
    return sends


# ---------------------------------------------------------------------------
# 三个专业 Agent（DESIGN §4）
# ---------------------------------------------------------------------------


def _base_result(subtask: dict) -> dict:
    sid = str(subtask.get("subtask_id") or subtask.get("id") or "")
    result = {
        "id": sid,
        "subtask_id": sid,
        "type": str(subtask.get("type") or ""),
        "input": str(subtask.get("input") or ""),
    }
    if subtask.get("alias"):
        result["alias"] = str(subtask["alias"])
    if subtask.get("tool"):
        result["tool"] = str(subtask["tool"])
    if subtask.get("args") is not None:
        result["args"] = dict(subtask["args"])
    return result


def _finish_worker(state: LgRagState, bump: dict, result: dict) -> dict:
    """带回同一 subtask_id；缺 output/error 时补错误终态，避免收齐挂起。"""
    if "output" not in result and "error" not in result:
        result["error"] = "工人返回缺少 output 或 error"
    plan_ids = {str(row["subtask_id"]) for row in _plan_rows(state)}
    return {**bump, "subtask_results": SubtaskResultBatch([result], plan_ids)}


def _step_detail_from_node_output(node_output: object) -> dict | None:
    """router 节点 updates 摘要：只取轻量键，避免塞 messages 全文。"""
    if not isinstance(node_output, dict):
        return None
    out: dict = {}
    for key in ("route", "retry_count", "chain_meta", "quality", "current_query"):
        if key in node_output:
            val = node_output[key]
            if key == "current_query" and isinstance(val, str) and len(val) > 120:
                out[key] = val[:119] + "…"
            else:
                out[key] = val
    return out or {"keys": sorted(node_output.keys())[:12]}


async def rag_subtask_node(state: LgRagState) -> dict:
    """RAG 子任务：内部 astream_router_agent（复用 Phase 2/3）并推送 step 里程碑。

    子图输入隔离：fresh messages 仅含本子任务 input，不污染父历史；
    结果 = 末条 AIMessage + chain_meta 摘要。异常 → 错误结果不中断。
    §10.7：running 起步 + router/evidence step 帧（经 progress sink / chain hook）。
    总步计数只计本节点入口，**不计**内部 router 子图节点。
    """
    bump = bump_supervisor_step(state)
    subtask = _current_subtask(state)
    if subtask is None:  # 防御：dispatch 保证不会发生；追加错误结果保推进
        return {
            **bump,
            "subtask_results": [{"type": "rag", "error": "no pending subtask"}],
        }
    result = _base_result(subtask)
    subtask_id = result["id"]
    subtask_type = result["type"] or "rag"
    # §10.7：重活前发 running 起步帧（无 sink 时为空操作）
    await emit_subtask_running(
        agent_role="rag_subtask",
        subtask_id=subtask_id,
        type=subtask_type,
        input_preview=result["input"],
    )

    async def _chain_hook(step: str, detail: dict | None) -> None:
        await emit_subtask_step(
            agent_role="rag_subtask",
            subtask_id=subtask_id,
            type=subtask_type,
            step=step,
            detail=detail,
        )

    hook_token = set_chain_step_hook(_chain_hook)
    try:
        with trace_span("rag_subtask", run_type="chain"):
            try:
                acc_messages: list = []
                acc_chain_meta: dict = {}
                async for update in astream_router_agent(
                    result["input"],
                    thread_id=str(result.get("subtask_id") or "") or "missing-subtask-id",
                ):
                    if not isinstance(update, dict):
                        continue
                    for node_name, node_output in update.items():
                        await emit_subtask_step(
                            agent_role="rag_subtask",
                            subtask_id=subtask_id,
                            type=subtask_type,
                            step=str(node_name),
                            detail=_step_detail_from_node_output(node_output),
                        )
                        if not isinstance(node_output, dict):
                            continue
                        msgs = node_output.get("messages")
                        if isinstance(msgs, list) and msgs:
                            acc_messages.extend(msgs)
                        if "chain_meta" in node_output and isinstance(
                            node_output.get("chain_meta"), dict
                        ):
                            acc_chain_meta = node_output["chain_meta"] or {}
                answer = ""
                for m in reversed(acc_messages):
                    if getattr(m, "type", None) == "ai":
                        content = m.content
                        answer = content if isinstance(content, str) else str(content)
                        break
                result["output"] = answer
                result["chain_meta"] = acc_chain_meta
            except Exception as exc:
                logger.warning("lg_rag rag 子任务失败 id=%s err=%r", result["id"], exc)
                result["error"] = repr(exc)
    finally:
        reset_chain_step_hook(hook_token)
    return _finish_worker(state, bump, result)


def _empty_extract() -> dict:
    return {"dates": [], "versions": [], "people": []}


async def info_extract_node(state: LgRagState) -> dict:
    """信息抽取子任务：LLM 从输入文本抽 dates/versions/people JSON。

    选型：complete 一次 + ``parse_only``，避免双重 LLM。
    非法 JSON / schema 失败 → 空结构 + warning + structured_output_fallback，
    不中断（DESIGN §8 / SPEC §5）。
    """
    bump = bump_supervisor_step(state)
    subtask = _current_subtask(state)
    if subtask is None:
        return {
            **bump,
            "subtask_results": [{"type": "extract", "error": "no pending subtask"}],
        }
    result = _base_result(subtask)
    # §10.7：重活前发 running 起步帧（无 sink 时为空操作）
    await emit_subtask_running(
        agent_role="info_extract",
        subtask_id=result["id"],
        type=result["type"] or "extract",
        input_preview=result["input"],
    )
    with trace_span("info_extract", run_type="chain"):
        try:
            provider = get_llm_provider(_ROUTER_PROVIDER)
            raw = await provider.complete(
                [
                    LlmMessage(role="system", content=render("lg_rag.extract.system")),
                    LlmMessage(role="user", content=result["input"]),
                ],
                model=_ROUTER_MODEL,
            )
        except Exception as exc:
            logger.warning("lg_rag extract LLM 失败 id=%s err=%r", result["id"], exc)
            result["output"] = _empty_extract()
            result["error"] = repr(exc)
            _record_span_metadata({"structured_output_fallback": True})
            return _finish_worker(state, bump, result)
        outcome = parse_only(raw, schema=ExtractResult)
        if not outcome.ok or outcome.data is None:
            logger.warning("lg_rag extract 输出非法，置空结构 raw=%r", (raw or "")[:200])
            result["output"] = _empty_extract()
            _record_span_metadata({"structured_output_fallback": True})
        else:
            result["output"] = outcome.data.model_dump()
            _record_span_metadata({"structured_output_fallback": False})
    return _finish_worker(state, bump, result)


async def tool_exec_node(state: LgRagState) -> dict:
    """工具子任务：经 Capability Gateway ainvoke；未知 id → 错误结果不中断。

    观测：复用 ``trace_span("tool_exec")``；Gateway 向当前 span 写
    capability_id / kind / ok / error / args 摘要 / policy / subtask_id。

    入参：优先 ``subtask.args``；否则兼容 legacy ``input`` 字符串。
    租户：优先请求 ContextVar（F1=C），否则试点 A。
    """
    bump = bump_supervisor_step(state)
    subtask = _current_subtask(state)
    if subtask is None:
        return {
            **bump,
            "subtask_results": [{"type": "tool", "error": "no pending subtask"}],
        }
    result = _base_result(subtask)
    tool_name = str(subtask.get("tool") or "")
    # B：args 优先；兼容 input（写审批闸的意图摘要需要 → 提到 running 帧之前）
    raw_args = subtask.get("args")
    if isinstance(raw_args, dict):
        call_args: object = raw_args
    else:
        call_args = result["input"]
    # ------------------------------------------------------------------
    # 阶段 W · W0 写执行审批闸（fail-closed · 在 running 帧之前：一步未跑）。
    # write 类 capability 无新鲜 approved 单据 → 挂起 HITL（复用既有 HITL
    # 回路：blocked terminal → _persist_hitl → interrupt）。本闸与 gateway
    # Policy 写闸**正交两道闸**：OPS_CAPABILITY_ALLOW_WRITE 只过 Policy 层，
    # 不豁免本闸（棒次红线「无审批直接写 = fail-closed」钉死）。
    # ------------------------------------------------------------------
    entry = _cap_registry().get(tool_name)
    spec = entry[0] if entry else None
    write_approval: dict | None = None
    if spec is not None and spec.side_effect in WRITE_SIDE_EFFECTS:
        write_approval = await _write_execution_approval(
            state, subtask_id=result["id"], capability_id=tool_name
        )
        if write_approval is None:
            gate_tenant = current_tenant_or_default()
            blocked = _error_terminal(
                subtask, "写操作未获人工审批，已挂起等待 HITL 审批（fail-closed）"
            )
            blocked["blocked_by"] = _BLOCKED_BY_CAPABILITY_WRITE
            blocked["hitl_required"] = True
            blocked["tenant_id"] = gate_tenant
            # 写意图结构钉死：capability_id + tenant_id + args 摘要 + 幂等键模板
            # （随单落库于 payload.write_intent · 复用既有 hitl 载荷最小化）。
            blocked["write_intent"] = {
                "capability_id": tool_name,
                "tenant_id": gate_tenant,
                "args_summary": _cap_args_summary(call_args),
                "idempotency_key": str(getattr(spec, "idempotency_key", "") or ""),
            }
            logger.info(
                "capability_write_hitl_required %s",
                json.dumps(
                    {
                        "capability_id": tool_name,
                        "subtask_id": result["id"],
                        "tenant_id": gate_tenant,
                    },
                    ensure_ascii=False,
                    sort_keys=True,
                ),
            )
            _record_span_metadata(
                {
                    "capability_write_hitl_required": True,
                    "subtask_id": result["id"],
                    "capability_id": tool_name,
                }
            )
            return {"subtask_results": [blocked]}
    # §10.7：重活前发 running 起步帧（无 sink 时为空操作）
    await emit_subtask_running(
        agent_role="tool_exec",
        subtask_id=result["id"],
        type=result["type"] or "tool",
        input_preview=result["input"],
    )
    pilot_tenant = current_tenant_or_default()
    cap_ctx: dict = {
        "tenant_id": pilot_tenant,
        "subtask_id": result["id"],
        # 会话维度：配额按 **run** 记，不是按子任务。
        # 只给 subtask_id 的话，budget 只能退回去剥 run_id:seq ——剥得出来是运气，
        # 剥不出来就退化成"一个子任务一个桶"，配额永远打不满（假门）。
        "run_id": _run_id_of(state),
    }
    # Host V1-A：委派链路注入令牌 + 强制标记（仅模式非 off；off 零 diff）。
    # 无令牌（空集未签发）也标记 required —— enforce 下由验签门按 R-a 拒。
    if _delegation_active():
        cap_ctx["_delegation_required"] = True
        # 委派主体绑定四元组补 user_id（与签发侧同源 · 非模型产出）
        cap_ctx["user_id"] = str(state.get("user_id") or "")
        raw_token = state.get("delegation_token")
        if raw_token:
            cap_ctx["_delegation_token"] = raw_token
    if write_approval is not None:
        # 审批命中（W0 闸放行）：Host 单次写放行（policy.write_allowed 读
        # _host_policy · 只对这一次调用有效）+ approval_id 审计串链（W3 ·
        # gateway.py:1318 预留启用）。单据凭证在编排层消费，不穿透 capability 包。
        cap_ctx["_host_policy"] = {"allow_write": True}
        cap_ctx["approval_id"] = str(write_approval.get("id") or "")
    with trace_span("tool_exec", run_type="tool"):
        cap = await capability_ainvoke(tool_name, call_args, ctx=cap_ctx)
        if not cap.ok:
            logger.warning(
                "lg_rag 工具失败 tool=%r id=%s err=%r",
                tool_name,
                result["id"],
                cap.error,
            )
            result["error"] = cap.error or f"未知工具: {tool_name or '(未指定)'}"
        else:
            output = cap.output
            # security-input-isolation D2 · 工具回执面：on 态自由文本回执在
            # 回注 subtask_results 前走 wrap_slot("tool_result", ...)（边界标记
            # + 不可信声明 + 伪造标记转义）；非 str 结构化 output 保持原结构
            # （下游 consumes 绑定按字段取数，改成文本会破坏编排语义——非范围）。
            # 包装机制自身故障 → 本子任务降级 off 态原文 + input_isolation_degraded
            # 标记（跟数据走，aggregator 见标记整单退 off 态装配）。
            if security_input_isolation_enabled() and isinstance(output, str):
                try:
                    output = str(wrap_slot("tool_result", output))
                except Exception:
                    logger.exception(
                        "input isolation wrap failed tool=%r id=%s; degrade to raw output",
                        tool_name,
                        result["id"],
                    )
                    _record_span_metadata({"input_isolation_degraded": True})
                    result["input_isolation_degraded"] = True
                    output = cap.output
            result["output"] = output
            # ★ 降级必须让**模型**看得见。meta 里的 degraded 标记模型看不到
            # （它只看子任务输出），所以：
            #   1) Gateway 已把 _degraded 提示写进 output（跟着数据走）；
            #   2) 这里再在子任务结果上打一层标，让聚合器/前端也能筛出来。
            # 否则模型会拿着静态兜底或过期缓存当真实结果回答，语气还很确定。
            if cap.meta.get("degraded") is True:
                result["degraded"] = True
                result["degraded_action"] = cap.meta.get("degraded_action")
                logger.warning(
                    "lg_rag 工具降级 tool=%r id=%s action=%s reason=%s",
                    tool_name,
                    result["id"],
                    cap.meta.get("degraded_action"),
                    cap.meta.get("degraded_reason"),
                )
    return _finish_worker(state, bump, result)


# ---------------------------------------------------------------------------
# Observe · 外层 ReAct 的收口（DESIGN 06 §8）
# ---------------------------------------------------------------------------


def _observe(state: LgRagState) -> dict:
    """本轮观察：**只用确定性信号**。

    不在这里让模型判断"够不够"——模型判断放在 ``_satisfied_by_model``，
    而且它只能**触发**新一轮，不能放行（放行永远由这里的确定性信号 + 轮次上限决定）。
    """
    plan = _plan_rows(state)
    plan_ids = {str(row["subtask_id"]) for row in plan}
    results = list(state.get("subtask_results") or [])
    terms = _terminal_index(results, plan_ids)
    failed: list[str] = []
    blocked: list[str] = []
    hitl: list[str] = []
    for sid, term in terms.items():
        if "error" in term:
            failed.append(sid)
            if term.get("blocked_by"):
                blocked.append(sid)
            if term.get("hitl_required") is True:
                hitl.append(sid)
    pending = [str(row["subtask_id"]) for row in plan if row["subtask_id"] not in terms]
    prefix = [str(s) for s in (state.get("plan_prefix_ids") or [])]
    return {
        "round": int(state.get("react_round") or 0),
        "planned": len(plan),
        "done": len(terms),
        "prefix_len": len(prefix),
        "newly_planned": max(0, len(plan) - len(prefix)),
        "failed": sorted(failed),
        "blocked": sorted(blocked),
        "hitl_pending": sorted(hitl),
        "pending": sorted(pending),
        "unsatisfied": bool(failed or pending),
    }


async def _satisfied_by_model(state: LgRagState, obs: dict) -> bool | None:
    """可选的模型侧"够不够"判断；**返回 False 只用来触发新一轮**。

    默认关闭（``LG_RAG_REACT_SATISFACTION``）：默认开着等于让模型给自己打分。
    开了之后它也不能放行——确定性信号说没做完就是没做完，
    模型说"够了"不能让一个失败的步骤消失。
    """
    import os

    if os.environ.get("LG_RAG_REACT_SATISFACTION", "0").strip() != "1":
        return None
    from pydantic import BaseModel

    from app.llm.factory import get_llm_provider
    from app.llm.schema import LlmMessage
    from app.ops.lg_rag.nodes import _last_user_text
    from app.ops.structured_output import parse_only

    class _Verdict(BaseModel):
        satisfied: bool

    query = _last_user_text(state.get("messages") or [])
    payload = json.dumps(obs, ensure_ascii=False, default=str)
    try:
        provider = get_llm_provider(_ROUTER_PROVIDER)
        raw = await provider.complete(
            [
                LlmMessage(
                    role="system",
                    content=(
                        "判断下面这批子任务结果**够不够**回答原始问题。"
                        '只输出 JSON：{"satisfied": true|false}。'
                        "有任何失败、缺失、被拦下的步骤都判 false。"
                    ),
                ),
                LlmMessage(
                    role="user",
                    content=f"原始问题：{query}\n观察：{payload}",
                ),
            ],
            model=_ROUTER_MODEL,
        )
        outcome = parse_only(raw, schema=_Verdict)
        if not outcome.ok or outcome.data is None:
            return None
        return bool(outcome.data.satisfied)
    except Exception as exc:  # 模型不可用 → 不因此放行，也不因此循环
        logger.warning("lg_rag observe 模型侧满足度判断失败，按未知处理 err=%r", exc)
        return None


def _thread_id_of(state: LgRagState, config: RunnableConfig | None = None) -> str:
    """恢复定位用的 thread_id。

    **必须能从 config 兜底**：真实调用时 thread_id 只在 config 里，
    state 里未必有人写。拿不到的话审批申请就是一条没有归属的记录——
    人批完之后无从知道要恢复哪条 run。
    """
    direct = str(state.get("thread_id") or "").strip()
    if direct:
        return direct
    try:
        configurable = (config or {}).get("configurable") or {}
        return str(configurable.get("thread_id") or "").strip()
    except Exception:  # config 形态意外时不因此崩
        return ""


async def _approved_fresh_for_subtask(
    state: LgRagState, *, subtask_id: str, capability_id: str
) -> bool:
    """``_persist_hitl`` 建单前检查（hitl-replan-carry-and-persist-guard 契约四）：

    同 (run_id, subtask_id, capability_id) 存在新鲜 approved 单据 → True
    （跳过建单）。匹配语义镜像 ``_approval_consumed``：blocked_by 守卫 +
    三元组精确匹配 + 缺 capability_id 键不匹配 + ``_decided_at_ts`` 归一 +
    ``_approval_consumption_ttl_seconds`` TTL —— 同一实现复用，禁第二份
    （auto_resume.py 复用先例）。**fail-open**（契约五）：读异常 → False
    （照建单）+ ``hitl_persist_guard_read_failed`` warning 台账（键名钉死）。
    """
    run_id = _run_id_of(state)
    if not (run_id and subtask_id and capability_id):
        return False
    from app.ops.hitl import get_hitl_store

    try:
        rows = await get_hitl_store().alist(status="approved", limit=200)
    except Exception as exc:  # FP-4：fail-open 照建单 + warning（钉死键名）
        logger.warning(
            "hitl_persist_guard_read_failed subtask=%s capability=%s err=%r",
            subtask_id,
            capability_id,
            exc,
        )
        return False
    hit = _match_fresh_approved(
        rows,
        run_id=run_id,
        subtask_id=subtask_id,
        capability_id=capability_id,
        # 契约四：与消费门同一份匹配实现；阶段 W 扩至写闸类单据（新鲜 approved
        # 的 capability_write 单同样抑制重复建单）。
        blocked_by=_WRITE_CONSUMABLE_BLOCKED_BY,
    )
    return hit is not None


async def _persist_hitl(
    state: LgRagState, obs: dict, *, thread_id: str = ""
) -> tuple[list[dict], bool]:
    """把本轮 pending 的拦截落库成审批申请。

    返回 ``(申请列表, 是否有未落库的)``。**未落库必须显式带出来**：
    "申请丢了"和"没人申请过"在观测上长得一模一样，人会一直等一个不存在的审批。
    """
    if not obs["hitl_pending"]:
        return list(state.get("hitl_requests") or []), False
    from app.ops.hitl import get_hitl_store, new_request_id

    store = get_hitl_store()
    plan = {str(row["subtask_id"]): row for row in _plan_rows(state)}
    terms = _terminal_index(list(state.get("subtask_results") or []), set(plan))
    # ⚠️ 去重**不能只看 state**：interrupt 挂起时节点 return 的值不会进 checkpoint，
    #   恢复后重跑 observe 时 ``state["hitl_requests"]`` 是空的（上一轮没写进去）。
    #   于是"恢复一次就重复建一条申请" —— 人会在审批列表里看到两条一模一样的。
    #   真相在 store 里，以 (run_id, subtask_id) 为幂等键。
    already = {
        str(r.get("subtask_id")): r
        for r in (state.get("hitl_requests") or [])
        if isinstance(r, dict)
    }
    run_id = _run_id_of(state)
    store_pending_rows: list[dict] = []
    try:
        store_pending_rows = await store.alist(status="pending", limit=200)
        for row in store_pending_rows:
            if str(row.get("run_id") or "") == run_id:
                already.setdefault(str(row.get("subtask_id") or ""), row)
    except Exception as exc:  # 拉不到就退回只认 state，不因此崩
        logger.warning("HITL 申请去重拉取失败，退回按 state 去重 err=%r", exc)
    # fix-seen-surface-idempotency（issue #335 · 30 授权 comment `6669768156`）：
    # reset seen 面（worker 重启 · hitl_requests 不进 checkpoint）后首轮巡检，
    # 重规划孪生步（同写意图新 sid）绕过上面精确 sid 去重 ⇒ 重复建单（overlap
    # 噪音源）。status 位：库面 live 写单（pending + 未过期 approved 的
    # capability_write 类 · 带 write_intent）按写意图幂等键索引；命中 ⇒ 存量单
    # 迁附当前步并带回（不新建）。与 already（seen_surface 位）合成
    # status ∧ seen_surface 双条件（HG-WRITE-TICKET-IDEMPOTENCY-DESIGN ②）。
    intent_live: dict[tuple[str, str], dict] = {}
    if _write_replay_guard_enabled():
        approved_rows: list[dict] = []
        try:
            approved_rows = await store.alist(status="approved", limit=200)
        except Exception as exc:  # 退回仅 pending 面（approved 面读失败方向与
            # _approved_fresh_for_subtask fail-open 一致：照建单可审，不丢单）
            logger.warning("HITL 写意图守卫 approved 面读取失败，退回仅 pending 面 err=%r", exc)
        ttl = _approval_consumption_ttl_seconds()
        now_ts = time.time()
        for row in [*store_pending_rows, *approved_rows]:
            if str(row.get("run_id") or "") != run_id:
                continue
            if str(row.get("blocked_by") or "") != _BLOCKED_BY_CAPABILITY_WRITE:
                continue
            payload_row = row.get("payload")
            if not isinstance(payload_row, dict):
                continue
            key = _write_intent_live_key(
                capability_id=str(payload_row.get("capability_id") or ""),
                write_intent=payload_row.get("write_intent"),
            )
            if key is None:
                continue
            if str(row.get("status") or "") == "approved":
                decided_ts = _decided_at_ts(row.get("decided_at"))
                if decided_ts is None or now_ts - decided_ts > ttl:
                    continue  # 过期 approved ≠ live（消费门读时判过期同口径）
            intent_live.setdefault(key, row)  # alist 按 created_at 升序：最老优先
    created = list(state.get("hitl_requests") or [])
    unpersisted = False
    for sid in obs["hitl_pending"]:
        if sid in already:
            # 已经有 pending 了 —— 但**要把它带回返回值**，
            # 否则恢复那一次（state 里是空的）前端就看不到在等哪条申请
            if not any(str(r.get("subtask_id")) == sid for r in created):
                created.append(already[sid])
            continue
        term = terms.get(sid) or {}
        # 要解锁的是被它依赖的**已执行**前缀步骤（Q8 §2.4）
        unlock = ""
        for dep in (plan.get(sid) or {}).get("depends_on") or []:
            if str(dep) in set(state.get("plan_prefix_ids") or []):
                unlock = str(dep)
                break
        if not unlock and str(term.get("blocked_by") or "") in _SELF_UNLOCK_BLOCKED_BY:
            # D2 空形态回填（形态守卫 = 拦截对象即被拦步自身的单据类：delegation_issue
            # + 阶段 W capability_write）：无前驱前缀时批准 = 授权（重）下发**被拦
            # 步骤自身**（与消费门配对成环）；prefix_touch_required 类空 unlock
            # 维持现状（router 409 保留 · TA6 钉死）。
            unlock = sid
        # D1 消费键（Q1）：payload jsonb 增记 capability_id（零迁移 · 既有读取兼容）。
        # 真源 = _error_terminal 保留的 tool 字段。30 裁定留痕：tool 为空时**不落键**
        # （不落空串）——消费端缺键 fail-closed 语义不变，两类「缺键」归一同一路径。
        payload = {"observation": {k: obs[k] for k in ("round", "planned", "done")}}
        capability_id = str(term.get("tool") or "").strip()
        if capability_id:
            payload["capability_id"] = capability_id
        write_intent = term.get("write_intent")
        if isinstance(write_intent, dict):
            # 阶段 W：写意图随单落库（capability_id + tenant_id + args 摘要 +
            # 幂等键模板 · 结构由 tests/test_write_approval_gate.py 钉死；
            # 复用既有 payload jsonb 列 · 不扩 hitl 表结构）。
            payload["write_intent"] = write_intent
        # hitl-replan-carry-and-persist-guard 契约四：同 (run_id, subtask_id,
        # capability_id) 已有新鲜 approved 单据 ⇒ 跳过建单（防 resume 重放
        # 孤儿 pending）；命中不产新行也不伪造行（契约八 · interrupt 语义不动）。
        if await _approved_fresh_for_subtask(state, subtask_id=sid, capability_id=capability_id):
            logger.info("hitl_persist_guard_skip subtask=%s run=%s", sid, run_id)
            continue
        # fix-seen-surface-idempotency：status 位命中（库面同写意图 live 单）
        # ⇒ 存量单连接域迁附当前步（批准→解锁→消费链路与新建单逐点同义，
        # 仅少一行重复单据）并带回，**不新建**。守卫面 = capability_write 类 ∧
        # 带 write_intent（决策点② · 双条件位之 status 位）。
        if intent_live and str(term.get("blocked_by") or "") == _BLOCKED_BY_CAPABILITY_WRITE:
            intent_key = _write_intent_live_key(
                capability_id=capability_id, write_intent=write_intent
            )
            existing = intent_live.get(intent_key) if intent_key is not None else None
            if existing is not None and str(existing.get("subtask_id") or "") != sid:
                relocated = await store.arelocate_linkage(
                    str(existing.get("id") or ""),
                    subtask_id=sid,
                    unlock_subtask_id=unlock,
                )
                if relocated is None:
                    # 迁附失败（终态竞迁等）⇒ 保守方向：本轮不新建（宁可下轮
                    # 重建，不可重复建单）；留痕可观测。
                    logger.warning(
                        "hitl_write_intent_relocate_failed subtask=%s run=%s",
                        sid,
                        run_id,
                    )
                    continue
                logger.info(
                    "hitl_write_intent_attached %s",
                    json.dumps(
                        {
                            "request_id": str(relocated.get("id") or ""),
                            "subtask_id": sid,
                            "previous_subtask_id": str(existing.get("subtask_id") or ""),
                        },
                        ensure_ascii=False,
                        sort_keys=True,
                    ),
                )
                if not any(str(r.get("id") or "") == relocated["id"] for r in created):
                    created.append(relocated)
                continue
        request = {
            "id": new_request_id(),
            "run_id": run_id,
            "thread_id": thread_id,
            "checkpoint_id": state.get("hitl_checkpoint_id"),
            # api-w-hitl-tenant-fix（T-fix-2 · 契约「新单不再产 tenant_id=''」全类口径）：
            # terminal 已带戳（capability_write 闸 / _delegation_blocked_terminal）
            # 则原样落库；未带戳的类（prefix_touch 等）回落当前租户上下文——
            # 与 capability_write 闸同一真源函数（current_tenant_or_default），
            # 保证 resume 链「单据 tenant 为唯一真源」对**所有**新单成立。
            "tenant_id": str(term.get("tenant_id") or "") or current_tenant_or_default(),
            "subtask_id": sid,
            "blocked_by": str(term.get("blocked_by") or ""),
            "unlock_subtask_id": unlock,
            "reason": str(term.get("error") or ""),
            "detail": str(term.get("blocked_detail") or ""),
            "payload": payload,
            "status": "pending",
            "created_at": time.time(),
        }
        saved = await store.acreate(request)
        if saved.get("persisted") is False:
            unpersisted = True
            logger.error(
                "HITL 申请**未落库**（持久化未配置）subtask=%s run=%s —— 人在等一个不存在的审批",
                sid,
                request["run_id"],
            )
        created.append(saved)
    return created, unpersisted


def _hitl_interrupt_payload(
    state: LgRagState, obs: dict, requests: list[dict], *, thread_id: str = ""
) -> dict:
    """挂起载荷：告诉外面"这次等的是哪几条申请"。

    会被序列化进 checkpoint 并透给前端，**只放关联标识，不放任何密钥**。
    """
    return {
        "reason": "hitl_waiting",
        "run_id": _run_id_of(state),
        "thread_id": thread_id,
        "checkpoint_id": state.get("hitl_checkpoint_id"),
        "round": int(state.get("react_round") or 0),
        "unpersisted": bool(requests) and all(r.get("persisted") is False for r in requests),
        "requests": [
            {
                "id": str(r.get("id") or ""),
                "subtask_id": str(r.get("subtask_id") or ""),
                "unlock_subtask_id": str(r.get("unlock_subtask_id") or ""),
                "blocked_by": str(r.get("blocked_by") or ""),
                "reason": str(r.get("reason") or ""),
            }
            for r in requests
            if isinstance(r, dict) and r.get("status") == "pending"
        ],
    }


def _apply_hitl_decision(state: LgRagState, obs: dict, resumed: Any) -> dict:
    """把"批准"落成 state 更新：**只授权，不代劳**。

    批准的**唯一**效果是解除锁定 —— 它不会自动改历史，也不会自动继续跑，
    而是把被解锁的那一步从不可变前缀里摘出去，让下一轮重规划重新执行它。

    两件必须一起做的事：
    1. 记进 ``hitl_unlocked_ids`` ⇒ ``_locked_prefix`` 不再把它当前缀
       ⇒ 可恢复点回退到它（这就是"从可恢复点重跑"）；
    2. **剪掉它的旧结果**。不然 ``merge_subtask_results`` 见它已有终态就不覆盖，
       重跑的新结果根本进不来 —— 人会看到"批准了但结果没变"。
    """
    payload = resumed if isinstance(resumed, dict) else {}
    approved = {str(x) for x in (payload.get("approved") or []) if str(x).strip()}
    decided_by = str(payload.get("decided_by") or "")
    obs = dict(obs)
    obs["verdict"] = "replan" if approved else "settle"
    obs["hitl_decision"] = {
        "approved": sorted(approved),
        "rejected": [str(x) for x in (payload.get("rejected") or [])],
        "decided_by": decided_by,
    }

    unlocked = {str(s) for s in (state.get("hitl_unlocked_ids") or [])}
    unlocked |= approved

    updates: dict = {
        "react_observation": obs,
        "hitl_unlocked_ids": sorted(unlocked),
        "hitl_interrupt": {
            "resumed": True,
            "approved": sorted(approved),
            "decided_by": decided_by,
        },
    }
    if approved:
        # 被授权重跑 ⇒ 外层的轮数归零：这是一次**被批准的全新尝试**，
        # 不该被上一轮的轮次预算顺手掐掉。有界性由"人批一次才跑一次"保证。
        updates["react_round"] = 0
        plan_ids = {str(row["subtask_id"]) for row in _plan_rows(state)}
        keep = plan_ids - approved
        updates["subtask_results"] = SubtaskResultBatch([], keep, replace=True)
        logger.info(
            "HITL 已批准，解锁 %d 步并从可恢复点重跑 run=%s unlocked=%s by=%s",
            len(approved),
            _run_id_of(state),
            sorted(approved),
            decided_by or "unknown",
        )
    else:
        logger.info("HITL 未获批准（驳回或无授权），收工 run=%s", _run_id_of(state))
    return updates


# config 注解只认 Optional[RunnableConfig]（见 :27-32 警告块）；noqa 防 ruff UP045/--fix 再咬回 X | None（#274 回归源）。
async def observe_node(state: LgRagState, config: Optional[RunnableConfig] = None) -> dict:  # noqa: UP045
    """外层 ReAct 的"观察 + 判定"：这一轮活干完了没有？

    内层是 plan-and-execute（supervisor 拆 ≤4 步、按依赖并行执行）；
    外层是 ReAct（plan → execute → **observe** → 再 plan …）。

    **为什么必须在 aggregator 之前**：``route_next_subtask`` 原本在没有待发步骤时
    直接跳 aggregate，于是"后缀为空 / 全被拦下 / 统统失败"都会一路走到
    aggregator 生成一份**看起来完整的结论**——中间没有任何针对性校验
    （critic 在 aggregator 之后，而且只看有没有 error）。

    判定顺序（先挡最贵的）：
    1. 有 HITL 挂起 → 收工（**不再开新轮**：人没批之前，再来多少轮都还是同一个拦截）；
    2. 有失败 / 被拦 / 未终态 → 再来一轮（受轮次上限）；
    3. 否则 → 收工。
    """
    bump = bump_supervisor_step(state)
    obs = _observe(state)
    thread_id = _thread_id_of(state, config)
    # 落库**先于**挂起：挂起期间节点 return 的值不进 checkpoint，
    # 但申请必须在外面立刻能拉到 —— 否则人不知道有东西等他批。
    hitl_requests, unpersisted = await _persist_hitl(state, obs, thread_id=thread_id)

    # ---- 等待授权：**真的把图挂起**（不是写个标签继续走）----
    #
    # 为什么必须 interrupt：原来 wait_hitl 只是个字符串，route_after_react
    # 把它按 settle 处理 ⇒ 图照样走到 aggregator 出一份"完整结论"。
    # 用户在界面上看到答复的同时，后台躺着一条 pending 审批 ——
    # 这正是 #3 要防的"看起来完整的答案"，只是换了个入口。
    if obs["hitl_pending"]:
        resumed = interrupt(_hitl_interrupt_payload(state, obs, hitl_requests, thread_id=thread_id))
        # 执行到这里只有两种可能：① 恢复后重跑，interrupt() 返回 resume 值；
        # ② 对端没恢复 ⇒ 上一行已经抛 GraphInterrupt，根本走不到这。
        return {
            **bump,
            **_apply_hitl_decision(state, obs, resumed),
        }

    model_says = await _satisfied_by_model(state, obs)
    obs["model_satisfied"] = model_says

    if obs["unsatisfied"] or model_says is False:
        verdict = (
            "replan"
            if not is_react_round_exhausted(state) and not is_supervisor_budget_exhausted(state)
            else "settle"
        )
    else:
        verdict = "settle"
    obs["verdict"] = verdict
    obs["hitl_unpersisted"] = unpersisted

    _record_span_metadata(
        {
            "react_round": int(state.get("react_round") or 0),
            "react_verdict": verdict,
            "react_unsatisfied": bool(obs["unsatisfied"]),
            "react_hitl_pending": len(obs["hitl_pending"]),
            "react_hitl_unpersisted": unpersisted,
        }
    )
    return {
        **bump,
        **bump_react_round(state),
        "react_observation": obs,
        "hitl_requests": hitl_requests,
    }


def route_after_react(state: LgRagState) -> str:
    """``"replan"`` → supervisor（再来一轮 plan→execute）；否则 → aggregator。"""
    verdict = str((state.get("react_observation") or {}).get("verdict") or "settle")
    return "replan" if verdict == "replan" else "settle"


# ---------------------------------------------------------------------------
# Aggregator（DESIGN §5）
# ---------------------------------------------------------------------------


def _aggregator_plain_messages(query: str, payload: str) -> list[LlmMessage]:
    """off 态装配（现网形态 · 逐字节对拍基准）。"""
    return [
        LlmMessage(role="system", content=render("lg_rag.aggregator.system")),
        LlmMessage(
            role="user",
            content=f"原始问题：{query}\n子任务结果：{payload}",
        ),
    ]


def _aggregator_isolated_messages(
    query: str, results: list[dict], payload: str
) -> list[LlmMessage]:
    """on 态装配（security-input-isolation D2 · 工具回执面收口进槽位）。

    - 原始问题走 `user_query` 槽；工具回执段（tool_exec 已逐条
      `wrap_slot("tool_result", ...)`）在 payload 内自带边界标记；
      指令资产归 `system_instruction`。
    - 装配校验 `assert_slots_declared` 在发往 LLM 前执行：声明了
      `tool_result` 而 payload 无边界标记（绕过 wrap_slot 直拼 / 未声明段）
      → :class:`SlotIsolationError` 显式炸，**请求不发出**（下游零请求）
      + span `input_isolation_rejected`。
    - 机制故障（含上游 tool_exec 已降级的 `input_isolation_degraded` 结果）
      → 整单退 off 态装配 + span `input_isolation_degraded`——机制事故退旧
      路径与内容违例不发出**语义分立**。
    """
    tool_outputs = [
        r
        for r in results
        if isinstance(r, dict)
        and str(r.get("type") or "") == "tool"
        and r.get("output") is not None
    ]
    if any(r.get("input_isolation_degraded") for r in tool_outputs):
        logger.warning("input isolation degraded upstream; aggregator keeps off-state assembly")
        return _aggregator_plain_messages(query, payload)
    try:
        system_msg = LlmMessage(
            role="system",
            content=wrap_slot("system_instruction", render("lg_rag.aggregator.system")),
        )
        user_msg = LlmMessage(
            role="user",
            content=f"原始问题：{wrap_slot('user_query', query)}\n子任务结果：{payload}",
        )
        declared = ["user_query"]
        if tool_outputs:
            declared.append("tool_result")
        declare_slots(user_msg, declared)
        assert_slots_declared([system_msg, user_msg])
        return [system_msg, user_msg]
    except SlotIsolationError:
        _record_span_metadata({"input_isolation_rejected": True})
        logger.warning(
            "aggregator input isolation rejected undeclared content; request not sent",
            exc_info=True,
        )
        raise
    except Exception:
        logger.exception("aggregator input isolation failed; degrade to off-state assembly")
        _record_span_metadata({"input_isolation_degraded": True})
        return _aggregator_plain_messages(query, payload)


async def aggregator_node(state: LgRagState) -> dict:
    """LLM 综合全部 subtask_results → 分节结构化 markdown，追加最终 AIMessage。

    中间结果只在 subtask_results，不进 messages；LLM 失败异常上抛
    （与全站一致，DESIGN §8）。
    """
    bump = bump_supervisor_step(state)
    query = _last_user_text(state["messages"])
    results = state.get("subtask_results") or []
    payload = json.dumps(results, ensure_ascii=False, default=str)
    provider = get_llm_provider(_ROUTER_PROVIDER)
    with trace_span("aggregator", run_type="chain"):
        if security_input_isolation_enabled():
            messages = _aggregator_isolated_messages(query, results, payload)
        else:
            messages = _aggregator_plain_messages(query, payload)
        # T5：SSE 路径经 token sink 逐 chunk 上屏（answer delta 帧）；
        # 无 sink / 流式异常时桥内降级整段 complete（T2 行为）+ 日志。
        text = await complete_answer_streaming(
            provider,
            messages,
            model=_ROUTER_MODEL,
            node="aggregator",
        )
    answer = (text or "").strip()
    if not answer:
        logger.warning("lg_rag aggregator 空输出，回退拼接子任务结果")
        answer = (
            "\n\n".join(
                f"## 子任务 {r.get('id') or i + 1}\n"
                f"{r.get('output') or r.get('error') or '(无输出)'}"
                for i, r in enumerate(results)
            )
            or "（无子任务结果）"
        )
    return {**bump, "messages": [AIMessage(content=answer)]}
