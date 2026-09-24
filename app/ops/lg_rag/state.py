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

    ``replace=True``：把已有结果**裁剪**到 plan_ids（其余丢弃）。
    Q8 用得到——critic 回环重规划时只保留不可变前缀的结果，不再整批清空。
    默认 False（追加语义不变）。
    """

    def __init__(
        self,
        items: list[dict],
        plan_ids: set[str] | frozenset[str] | list[str],
        *,
        replace: bool = False,
    ) -> None:
        super().__init__(items)
        self.plan_ids = frozenset(str(item) for item in plan_ids)
        self.replace = bool(replace)


def success_terminal_ids(
    plan: list[dict] | None, results: list[dict] | None
) -> list[str]:
    """不可变前缀（Q8）：已进入**成功终态**的计划 id，按计划顺序。

    **失败终态不算**——它没有要保护的东西（没有副作用、没有可取的结果），
    重规划可以重写它。要保护的是已经产生结果/副作用的步骤：
    它们的 ``(tool, args)`` 决定幂等键，改了就是一次新的写。

    放在 state 层：critic（strategy 包）与 multi/nodes 都要读，
    而 nodes 已经依赖 critic，反向导入会成环。
    """
    rows = [row for row in (plan or []) if isinstance(row, dict)]
    plan_ids = {
        str(row.get("subtask_id") or "").strip()
        for row in rows
        if str(row.get("subtask_id") or "").strip()
    }
    done: dict[str, dict] = {}
    for row in results or []:
        if not isinstance(row, dict):
            continue
        sid = str(row.get("subtask_id") or "").strip()
        if sid not in plan_ids or sid in done:
            continue
        if "output" in row or "error" in row:
            done[sid] = row
    success = {sid for sid, term in done.items() if "output" in term}
    return [
        str(row["subtask_id"]).strip()
        for row in rows
        if str(row.get("subtask_id") or "").strip() in success
    ]


def unresolved_suffix_ids(
    plan: list[dict] | None,
    results: list[dict] | None,
    prefix_ids: set[str] | frozenset[str] | list[str] | None = None,
) -> list[str]:
    """计划里**还没解决**的步骤 id（按计划顺序）：未终态，或终态是 error。

    与 ``success_terminal_ids`` 互补，两件事都要守：
    - 前缀保护"已经产生了结果/副作用"的步骤 —— 重跑它就是一次新的写；
    - 这里保护"还没解决"的步骤 —— **重规划时它们必须跟着走**。

    为什么必须跟着走（实测，不是推演）：重规划一旦只保留前缀，
    那些失败/未终态的步骤就从计划里消失，它们的记录随即变成**计划外 id**，
    observe 按 plan_ids 过滤看不见、aggregator 更看不见，
    结论会写成"已覆盖全部子任务" —— 失败被静默抹掉。

    放在 state 层：critic（strategy 包）与 multi/nodes 都要读，
    而 nodes 已经依赖 critic，反向导入会成环。
    """
    rows = [row for row in (plan or []) if isinstance(row, dict)]
    known = {
        str(row.get("subtask_id") or "").strip()
        for row in rows
        if str(row.get("subtask_id") or "").strip()
    }
    excluded = {str(sid) for sid in (prefix_ids or [])}
    done: dict[str, dict] = {}
    for row in results or []:
        if not isinstance(row, dict):
            continue
        sid = str(row.get("subtask_id") or "").strip()
        if sid and sid not in done and ("output" in row or "error" in row):
            done[sid] = row
    out: list[str] = []
    for row in rows:
        sid = str(row.get("subtask_id") or "").strip()
        if not sid or sid in excluded or sid in out:
            continue
        term = done.get(sid)
        if term is None or "error" in term:
            out.append(sid)
    return [sid for sid in out if sid in known]


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
    if getattr(new, "replace", False) and plan_ids is not None:
        # 裁剪到 plan_ids：重规划时把"可变后缀"的结果丢掉，前缀的留下
        out = [
            row
            for row in (existing or [])
            if isinstance(row, dict)
            and str(row.get("subtask_id") or "").strip() in plan_ids
        ]
    else:
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
    plan_prefix_ids（Q8）：不可变前缀的 subtask_id 列表（**成功终态**的步骤，按计划顺序）。
        失败终态不在内——它没有要保护的东西，重规划可以重写它。
        protected 的是"已产生结果/副作用"的步骤：其 (tool, args) 决定幂等键。
    recoverable_point（Q8）：= len(前缀)，下一个**真正要执行**的步骤下标。
        恢复 = 沿用前缀结果 + 从这里继续；前缀不重跑（幂等键不变 ⇒ 重放不重做）。
    react_round（Q8 延伸）：外层 ReAct 已完成的**轮数**（plan → execute → observe = 1 轮）。
        与 supervisor_step_count（内层**步数**）是两个维度：步数耗尽只意味着
        "这轮别再开节点了"，而"总共允许重规划几次"必须单独封顶。
    react_observation：observe 写的本轮观察（planned/done/failed/blocked/
        hitl_pending/pending_ids/unsatisfied/verdict）——**执行层收口**的依据。
    hitl_requests：本轮落库的审批申请（含 persisted 标记；没落库必须看得见）。
    hitl_unlocked_ids：**已被批准授权重跑**的步骤 subtask_id。
        写进来之后它们不再算"不可变前缀" —— 可恢复点随之回退到那一步，
        下一轮重规划就会重新执行它。这是"批准"的**唯一**效果：
        它只授权改历史，不自动帮你改，也不自动继续跑。
    hitl_interrupt：图挂起时的载荷（等待授权的申请 / 恢复后的决定）。
        挂起期间节点 return 的值**不会**进 checkpoint，所以这个字段只能由
        恢复那一次写入——观测与前端读它来知道"这次等的是哪条申请"。
    delegation_scope（Host V1-A · A2）：supervisor 写入的本轮**有效 scope**
        （requested_scope ∩ allowlist · 只收窄不放宽）；缺键 = 未声明 =
        兼容现状隐式 allowlist。仅在委派令牌模式非 off 时写入。
    delegation_token（Host V1-A）：subtask_join 分发路径签发的委派令牌
        （序列化 dict · Send 载荷 · tool_exec 自取注入 capability ctx）；
        老 checkpoint 无此键：.get 返回 None → 验签门按 R-a 处理。
    intent_fallback（Host V1-B）：intent_node 写入的意图健康度标记
        （SO/LLM 成功=False · 失败/异常=True）；场景维裁剪 S1 的输入
        （fallback=意图不可信 → 可见集退化为空集 · 安全默认）。
        老 checkpoint 无此键：.get 返回 None → bool(None)=False（现状语义）。
    thread_id / hitl_checkpoint_id：**恢复定位用的关联标识**。
        必须真的在 schema 里——不在的话 StateGraph 会把它们丢掉，
        审批申请里的 thread_id 永远是空，人批完之后无从定位要恢复哪条 run。

    ⚠️ 不能叫 ``checkpoint_id``：那是 LangGraph 的**保留 channel 名**，
       写进 StateGraph 会直接抛 ``Channel names checkpoint_id are reserved``。
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
    plan_prefix_ids: list[str]
    recoverable_point: int
    react_round: int
    react_observation: dict
    hitl_requests: list[dict]
    hitl_unlocked_ids: list[str]
    hitl_interrupt: dict
    delegation_scope: list[str]
    delegation_token: dict
    thread_id: str
    hitl_checkpoint_id: str
    allowed_capability_ids: list[str]
    allowed_skill_ids: list[str]
    intent: dict
    intent_fallback: bool
    critic_verdict: dict
    inner_retry_count: int
    rebinding_count: int
    supervisor_step_count: Annotated[int, merge_supervisor_step_count]
    supervisor_budget_exhausted: Annotated[bool, merge_budget_flag]
    supervisor_started_at: float
