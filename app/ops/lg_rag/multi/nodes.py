"""lg_rag Phase 4 · Multi-Agent 节点（supervisor / 三专业 agent / aggregator）。

说明书：docs/guides/DESIGN_langgraph-lg-rag-phase4-multiagent_v1.md §3–§5。

原则：
- supervisor 拆解失败/非法 → fallback 单 rag（须已有 run_id；否则不派工人）；
- 无依赖子任务同批 Send 给多个工人；有 depends_on 的等前驱终态再下发；
- 归并键是 Host subtask_id，不用模型别名，也不用结果列表长度当下标；
- 单个子任务异常 → 该 id 占错误终态，不卡住收齐。
"""

from __future__ import annotations

import json
import logging

from langchain_core.messages import AIMessage
from langgraph.types import Send
from pydantic import ValidationError

from app.llm.factory import get_llm_provider
from app.llm.schema import LlmMessage
from app.ops.capability import CapabilityFilter, list_capabilities
from app.ops.capability import ainvoke as capability_ainvoke
from app.ops.capability.types import CapabilitySpec
from app.ops.lc_evidence_chain.step_hook import (
    reset_chain_step_hook,
    set_chain_step_hook,
)
from app.ops.lg_rag.answer_stream import complete_answer_streaming
from app.ops.lg_rag.graph import astream_router_agent
from app.ops.lg_rag.multi.budget import (
    bump_supervisor_step,
    is_supervisor_budget_exhausted,
)
from app.ops.lg_rag.nodes import (
    _ROUTER_MODEL,
    _ROUTER_PROVIDER,
    _last_user_text,
)
from app.ops.lg_rag.progress_stream import emit_subtask_running, emit_subtask_step
from app.ops.lg_rag.schemas import ExtractResult, SubtaskItem, SubtasksPlan
from app.ops.lg_rag.state import LgRagState, SubtaskResultBatch
from app.ops.prompts import render
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

# Supervisor planner filter：与 Builder 同 Policy 裁剪（S1：再 ∩ state allowlist）
_SUPERVISOR_CAP_FILTER = CapabilityFilter(
    node_role="supervisor",
    kinds=frozenset({"local_fn"}),
    deny_high_risk=True,
)

_EXTRACT_SYSTEM = (
    "你是信息抽取器。从用户给出的文本中抽取结构化信息，只输出 JSON：\n"
    '{"dates": ["..."], "versions": ["..."], "people": ["..."]}\n'
    "- dates：出现的日期/时间点（原文表述）；\n"
    "- versions：出现的版本号（如 v1.2.3、2.0）；\n"
    "- people：出现的人名/负责人。\n"
    "没有的类别给空数组。只输出一个 JSON 对象，不要输出其他文字。"
)

_AGGREGATOR_SYSTEM = (
    "你是 Ops Desk 运维知识库助手的答案综合器（Aggregator）。"
    "用户提出了一个复合问题，各子任务的执行结果以 JSON 形式给出"
    "（含 type/input/output 或 error）。请综合全部子任务结果，"
    "输出结构化 markdown 答案：\n"
    "1. 按子任务分节，每节标注来源"
    "（rag 检索 / 信息抽取 / 工具查询，失败子任务如实说明）；\n"
    "2. 末尾给一节「综合结论」，串联各子任务结果回答原始问题。\n"
    "不要编造子任务结果中没有的事实。"
)

# Mock / lookup 已迁入 Capability Gateway（defaults + lookups）；
# tool_exec_node 主路径 await ainvoke（P-13，禁止在 async 节点同步打 PG）。


def _format_capability_catalog(specs: list[CapabilitySpec]) -> str:
    """赋能目录摘要（id · description · risk）供 supervisor system 注入。"""
    if not specs:
        return "（当前无可用 local_fn 工具）"
    lines = [
        f"- {s.capability_id}：{s.description}（risk={s.risk_level}）"
        for s in specs
    ]
    return "\n".join(lines)


def _build_supervisor_system(catalog_block: str) -> str:
    return render(
        "lg_rag.supervisor.system",
        {"catalog_block": catalog_block},
    )


def _resolve_supervisor_visible_caps(state: LgRagState) -> tuple[list[CapabilitySpec], frozenset[str]]:
    """本轮 supervisor 可见 catalog = filter ∩ state allowlist（S1-c）。"""
    allowlist_raw = state.get("allowed_capability_ids")
    if allowlist_raw is None:
        logger.warning(
            "lg_rag supervisor: allowed_capability_ids 缺失（须经 Builder），"
            "fallback 单 rag"
        )
        return [], frozenset()
    allowlist = frozenset(str(cid) for cid in allowlist_raw)
    caps = list_capabilities(filter=_SUPERVISOR_CAP_FILTER)
    if not allowlist:
        return [], frozenset()
    visible = [s for s in caps if s.capability_id in allowlist]
    return visible, frozenset(s.capability_id for s in visible)


def _subtasks_have_valid_tool_ids(
    subtasks: list[dict], allowed_ids: frozenset[str]
) -> bool:
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


def _issue_plan(
    items: list[dict], *, run_id: str, seq: int
) -> tuple[list[dict], list[dict], int]:
    """先签发 subtask_id，再解析 depends_on。超出 cap 的项不签发。"""
    issued: list[dict] = []
    for offset, item in enumerate(items[:MAX_SUBTASKS]):
        seq += 1
        alias = str(item.get("id") or f"t{offset + 1}")
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
        raw_deps = item.get("depends_on") or []
        if not isinstance(raw_deps, list):
            raw_deps = ["__invalid__"]
        stamped["_raw_deps"] = raw_deps
        issued.append(stamped)

    alias_map: dict[str, list[str]] = {}
    for row in issued:
        alias_map.setdefault(str(row["alias"]), []).append(str(row["subtask_id"]))
    id_set = {str(row["subtask_id"]) for row in issued}
    illegal: dict[str, str] = {}
    for row in issued:
        raw_deps = row.pop("_raw_deps")
        resolved, err = _resolve_depends(row, raw_deps, id_set, alias_map)
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
    return issued, errors, seq


def _stamp_host_plan(state: LgRagState, items: list[dict]) -> dict:
    """校验后的项换成 Host id。run_id 空白则不签发。"""
    run_id = _run_id_of(state)
    if not run_id:
        query = str(items[0].get("input") or "") if items else ""
        return _missing_run_update(query)
    seq = int(state.get("host_subtask_seq") or 0)
    plan, errors, seq = _issue_plan(items, run_id=run_id, seq=seq)
    out: dict = {
        "subtasks": plan,
        "host_subtask_seq": seq,
        "inflight_subtask_ids": [],
    }
    if errors:
        out["subtask_results"] = SubtaskResultBatch(
            errors, {str(row["subtask_id"]) for row in plan}
        )
    return out


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


def _join_subtasks(state: LgRagState) -> dict:
    """收口上一批：漏带回的 id 写错误终态；预算耗尽则补齐剩余 id，不再开新批。"""
    plan = _plan_rows(state)
    plan_ids = {str(row["subtask_id"]) for row in plan}
    by_id = {str(row["subtask_id"]): row for row in plan}
    done = _terminal_index(list(state.get("subtask_results") or []), plan_ids)
    inflight = [
        str(sid)
        for sid in (state.get("inflight_subtask_ids") or [])
        if str(sid) in plan_ids
    ]
    extras: list[dict] = []
    for sid in inflight:
        if sid in done:
            continue
        extras.append(
            _error_terminal(by_id[sid], "工人未带回匹配的 subtask_id，已写错误终态")
        )
        done[sid] = extras[-1]
    updates: dict = {}
    if is_supervisor_budget_exhausted(state):
        for row in plan:
            sid = str(row["subtask_id"])
            if sid in done:
                continue
            extras.append(
                _error_terminal(row, "supervisor 总步预算耗尽，未终态子任务写入错误终态")
            )
            done[sid] = extras[-1]
        updates["inflight_subtask_ids"] = []
    else:
        ready: list[str] = []
        for row in plan:
            sid = str(row["subtask_id"])
            if sid in done:
                continue
            deps = [str(dep) for dep in (row.get("depends_on") or [])]
            if all(dep in done for dep in deps):
                ready.append(sid)
        updates["inflight_subtask_ids"] = ready
    if extras:
        updates["subtask_results"] = SubtaskResultBatch(extras, plan_ids)
    return updates


def _worker_state(state: LgRagState, subtask: dict) -> dict:
    payload: dict = {
        "messages": list(state.get("messages") or []),
        "assigned_subtask": dict(subtask),
        "subtasks": list(state.get("subtasks") or []),
        "supervisor_step_count": int(state.get("supervisor_step_count") or 0),
    }
    if state.get("supervisor_started_at") is not None:
        payload["supervisor_started_at"] = state["supervisor_started_at"]
    if state.get("supervisor_budget_exhausted") is True:
        payload["supervisor_budget_exhausted"] = True
    return payload


# ---------------------------------------------------------------------------
# Supervisor（DESIGN §3）
# ---------------------------------------------------------------------------


async def supervisor_node(state: LgRagState) -> dict:
    """LLM 拆解复合问题为 ≤4 子任务；失败/非法/非法 tool id → fallback 单 rag。

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
        stamped = _stamp_host_plan(
            state, [{"id": "t1", "type": "rag", "input": query}]
        )
        return {**bump, **stamped}
    system_content = _build_supervisor_system(_format_capability_catalog(caps))
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
            if subtasks is not None and not _subtasks_have_valid_tool_ids(
                subtasks, allowed_ids
            ):
                invalid_tool_id = True
                logger.warning(
                    "lg_rag supervisor plan 含非法 tool id，fallback 单 rag raw=%r",
                    raw[:200],
                )
                subtasks = None
        except Exception as exc:  # LLM 异常/超时 → 宁退化不失败
            logger.warning("lg_rag supervisor LLM 失败，fallback 单 rag err=%r", exc)
    fallback = subtasks is None
    if fallback and raw and not invalid_tool_id:
        logger.warning(
            "lg_rag supervisor 输出非法，fallback 单 rag raw=%r", raw[:200]
        )
    if fallback:
        subtasks = [{"id": "t1", "type": "rag", "input": query}]
    stamped = _stamp_host_plan(state, subtasks or [])
    issued = stamped.get("subtasks") or []
    span_meta = {
        "capability_catalog_count": len(caps),
        "subtask_count": len(issued),
        "subtask_types": [s["type"] for s in issued],
        "supervisor_fallback": fallback,
        # 与 supervisor_fallback 并存（SPEC §5）
        "structured_output_fallback": fallback,
        "supervisor_raw": raw[:200],
    }
    if invalid_tool_id:
        span_meta["supervisor_invalid_tool_id"] = True
    _record_span_metadata(span_meta)
    return {**bump, **stamped}


def route_next_subtask(state: LgRagState) -> str | list[Send]:
    """按 inflight 一次下发多个工人；预算耗尽或没有待发 id → aggregate。

    主闸仍是总步 / 旗标 / 墙钟：即使计划未收齐也返回 ``"aggregate"``，
    不直跳 END。收齐由 join 写入 inflight 为空来表达，不用结果条数。
    """
    if is_supervisor_budget_exhausted(state):
        return "aggregate"
    by_id = {str(row["subtask_id"]): row for row in _plan_rows(state)}
    sends: list[Send] = []
    for sid in state.get("inflight_subtask_ids") or []:
        subtask = by_id.get(str(sid))
        if subtask is None:
            continue
        node = _TYPE_TO_NODE.get(str(subtask.get("type") or ""), "rag_subtask")
        sends.append(Send(node, _worker_state(state, subtask)))
    if not sends:
        return "aggregate"
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
                    LlmMessage(role="system", content=_EXTRACT_SYSTEM),
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
    # §10.7：重活前发 running 起步帧（无 sink 时为空操作）
    await emit_subtask_running(
        agent_role="tool_exec",
        subtask_id=result["id"],
        type=result["type"] or "tool",
        input_preview=result["input"],
    )
    # B：args 优先；兼容 input
    raw_args = subtask.get("args")
    if isinstance(raw_args, dict):
        call_args: object = raw_args
    else:
        call_args = result["input"]
    pilot_tenant = current_tenant_or_default()
    cap_ctx: dict = {
        "tenant_id": pilot_tenant,
        "subtask_id": result["id"],
    }
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
            result["output"] = cap.output
    return _finish_worker(state, bump, result)


# ---------------------------------------------------------------------------
# Aggregator（DESIGN §5）
# ---------------------------------------------------------------------------


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
        # T5：SSE 路径经 token sink 逐 chunk 上屏（answer delta 帧）；
        # 无 sink / 流式异常时桥内降级整段 complete（T2 行为）+ 日志。
        text = await complete_answer_streaming(
            provider,
            [
                LlmMessage(role="system", content=_AGGREGATOR_SYSTEM),
                LlmMessage(
                    role="user",
                    content=f"原始问题：{query}\n子任务结果：{payload}",
                ),
            ],
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
