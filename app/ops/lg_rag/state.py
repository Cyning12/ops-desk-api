"""lg_rag 图状态定义（Phase 1）。

说明书：docs/guides/IMPL_langgraph-lg-rag-phase1_v1.md S2/S3。

Phase 1 采用 langgraph 内建 MessagesState：
- messages 走 add_messages reducer，node 返回「增量」列表即可，
  禁止手写全量覆盖；
- 输入为 HumanMessage(query)，输出为末条 AIMessage(answer)。

Router / rewrite / evaluate 等扩展字段留待 Phase 2/3 再引入，
届时在 LgRagState 上增补（保持向后兼容，新增字段须有默认值）。
"""

from __future__ import annotations

from typing import Annotated

from langgraph.graph import MessagesState


class SubtaskResultBatch(list):
    """带本轮计划 id 的结果批次。

    reducer 只认这个集合：计划外 id 丢弃，已有终态的重复条不覆盖。
    普通 list 不带计划上下文（单测直调 / 无 Host id 的错误条）。
    """

    def __init__(
        self,
        items: list[dict],
        plan_ids: set[str] | frozenset[str] | list[str],
    ) -> None:
        super().__init__(items)
        self.plan_ids = frozenset(str(item) for item in plan_ids)


def merge_supervisor_step_count(existing: int | None, new: int | None) -> int:
    """同批工人各写绝对步数时取较大值，避免 LastValue 并发冲突。"""
    return max(int(existing or 0), int(new or 0))


def merge_budget_flag(existing: bool | None, new: bool | None) -> bool:
    """耗尽旗标只升不降。同批多个工人同时置位时折叠成一次。"""
    return bool(existing) or bool(new)


def _terminal_subtask_id(row: dict) -> str:
    """终态关联键。没有 ``subtask_id`` 或没有 output/error 则不算终态。"""
    sid = str(row.get("subtask_id") or "").strip()
    if not sid:
        return ""
    if "output" not in row and "error" not in row:
        return ""
    return sid


def merge_subtask_results(
    existing: list[dict] | None, new: list[dict] | None
) -> list[dict]:
    """``None`` 清空（Critic 回环）；否则按计划 id 归并。

    带 ``plan_ids`` 的批次：未知 id、缺终态、已终态的重复条都丢弃，不覆盖。
    无计划上下文的普通 list：不覆盖已有终态，其余仍追加（含无 Host id 的错误条）。
    """
    if new is None:
        return []
    items = list(new or [])
    plan_ids = getattr(new, "plan_ids", None)
    out = [row for row in (existing or []) if isinstance(row, dict)]
    seen: set[str] = set()
    for row in out:
        sid = _terminal_subtask_id(row)
        if sid:
            seen.add(sid)
    for row in items:
        if not isinstance(row, dict):
            continue
        sid = str(row.get("subtask_id") or "").strip()
        if plan_ids is not None:
            if not sid or sid not in plan_ids:
                continue
            if sid in seen or _terminal_subtask_id(row) != sid:
                continue
            seen.add(sid)
            out.append(row)
            continue
        if sid and sid in seen:
            continue
        if sid and _terminal_subtask_id(row):
            seen.add(sid)
        out.append(row)
    return out


class LgRagState(MessagesState):
    """lg_rag 图状态。

    messages：内建 add_messages reducer（HumanMessage in → AIMessage out）。
    route（Phase 2）：router_node 写入的意图分流，取值
        "rag" | "direct" | "refuse"；无 reducer，节点写回即覆盖。
        老 checkpoint 无此键：条件边 route_by_route 缺省 "rag"。
    retry_count（Phase 3）：rewrite_node 递增的重试计数；缺省 0。
    current_query（Phase 3）：rewrite 后的查询；rag_node 优先取用，
        缺失时回退末条 HumanMessage。rewrite 熔断时置空以终止回环。
    chain_meta（Phase 3）：rag_node 写回的 ChainResult.meta 质量信号
        子集（gate_action/hit_count/kept_count/best_relevance/grade_count），
        evaluate_node 的数据源；evidence 本体不进 state（黑盒原则）。
        缺失时 evaluate 视为 high（安全默认，防意外回环）。
    subtasks（Phase 4）：supervisor_node 拆解产出的子任务列表
        [{"id","type","input","tool"?}]；无 reducer，节点写回即覆盖。
        老 checkpoint 无此键：仅 supervisor 图入口写入，router/basic 图不受影响。
    subtask_results（Phase 4 / S4）：各子任务结果；自定义 reducer：
        new is None → []（Critic 回环清空）；带 plan_ids 的批次按
        subtask_id 归并（未知 id / 重复终态丢弃）。收齐不看列表长度。
        中间结果不进 messages。
    run_id：本次 lg-rag run 已签发的 id，由入口传入，节点内禁止再造 uuid。
    host_subtask_seq：Host 子任务序号，从 0 起累计，签发时 +1（首个为 1）。
        Critic 回环不重置。与 SSE seq 独立。
    inflight_subtask_ids：当前批次已下发、尚未在 join 收口的计划 id。
    assigned_subtask：Send 载荷。工人只读这一份，不按结果条数取下标。
    allowed_capability_ids（S1）：Strategy Builder 写入的本轮 capability 白名单；
        supervisor 可见集 = list_capabilities(filter) ∩ 本字段；空 list → fallback 单 rag。
        supervisor 图路径强制经 Builder 前置，缺字段视为实现错误。
    allowed_skill_ids（S1 · 可选）：本轮 skill 白名单；首版 Builder 写空 list。
    intent（S2）：Intent 节点写入的细意图 dict（IntentV1）；Builder 读 needs_tool 等。
        失败时为保守 fallback（unknown / 全 False / low / 空摘要）。
    critic_verdict（S4）：critic_node 写入的判定 dict（至少含 outcome）；无 reducer。
    inner_retry_count（S4）：同 catalog 重拆次数；无 reducer；缺省 0；上限 1。
    rebinding_count（S4）：回 Builder 次数；无 reducer；缺省 0；上限 1。
    supervisor_step_count（H-β）：supervisor 图 8 类节点入口计数；无 reducer；缺省 0。
    supervisor_budget_exhausted（H-β）：总步/墙钟耗尽旗标；无 reducer；建议 True 后主闸→aggregate。
    supervisor_started_at（H-β · 可选墙钟）：首次 bump 写入的 monotonic 起点；默认墙钟关闭。
    """

    route: str
    retry_count: int
    current_query: str
    chain_meta: dict
    subtasks: list[dict]
    subtask_results: Annotated[list[dict], merge_subtask_results]
    run_id: str
    host_subtask_seq: int
    inflight_subtask_ids: list[str]
    assigned_subtask: dict
    allowed_capability_ids: list[str]
    allowed_skill_ids: list[str]
    intent: dict
    critic_verdict: dict
    inner_retry_count: int
    rebinding_count: int
    supervisor_step_count: Annotated[int, merge_supervisor_step_count]
    supervisor_budget_exhausted: Annotated[bool, merge_budget_flag]
    supervisor_started_at: float
