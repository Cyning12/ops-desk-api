# SPEC 审查：query-coref-rewrite（R1）

> **审查帽**：20-spec-audit（书面审 · 不改 SPEC 实质内容）
> **被审文件**：`docs/spec/query-coref-rewrite/SPEC-query-coref-rewrite_v0.md`（draft · HG-SPEC-SIGNOFF=pending）
> **审查日期**：2026-10-19
> **审查方式**：通读 SPEC 全文 + read/grep 实测全部代码锚点（不接受 SPEC 自述）

## 结论：**pass（通过）**

建议维护者签收 HG-SPEC-SIGNOFF；签收后下一棒 = 00 起草 task（默认分支 `task/query-coref-rewrite`）。3 条非阻塞观察供 10-task 参考，不构成退回理由。

---

## 1. 锚点抽查（read/grep 实测 · 14 处全部一致，0 漂移）

| # | SPEC 引用 | 实测结果 |
|---|---|---|
| 1 | `app/ops/lg_rag/multi/nodes.py:1106` planner 取词 `query=_last_user_text(state["messages"])` | ✅ 一致（:1106 在 `supervisor_node` 内，原样命中） |
| 2 | `multi/nodes.py:1163-1170` prompt 仅 system(catalog)+user(query) 两条 | ✅ 一致（:1163-1170 `provider.complete([LlmMessage(system), LlmMessage(user, query)], model=_ROUTER_MODEL)`，确为两条、无历史） |
| 3 | `multi/nodes.py:2107` aggregator 同样吃原文 | ✅ 一致（:2107 `query = _last_user_text(state["messages"])` 在 `aggregator_node`） |
| 4 | `multi/nodes.py:2035-2043` `_aggregator_plain_messages` | ✅ 一致（def :2035，body 至 :2043，user 消息 = `原始问题：{query}\n子任务结果：{payload}`） |
| 5 | `app/ops/lg_rag/continuity.py:44-79` `compress_window`（max_full_turns=6 / group_size=2） | ✅ 一致（def :44-79；常量 `DEFAULT_MAX_FULL_TURNS=6` :40、`DEFAULT_GROUP_SIZE=2` :41） |
| 6 | `continuity.py:82-98` `_assemble_messages_from_compressed` 末位追加 `HumanMessage(query)` 原文 | ✅ 一致（:97 `messages.append(HumanMessage(content=query))`） |
| 7 | `app/ops/lg_rag/router.py:339-342` `continue_from_run_id` 草稿拼接（非语义改写） | ✅ 一致（:339-342 `query = f"{body.query}\n\n[继续回复·既有草稿]\n{partial}"`） |
| 8 | `app/ops/lg_rag/nodes.py:203-240` `rewrite_node` 写 `state.current_query`（router 子图内部回环） | ✅ 一致（def :203，:240 `return {"current_query": new_query, ...}`；对象为子任务检索问句） |
| 9 | `multi/nodes.py:1432-1435` `astream_router_agent(result["input"], ...)` 不传 history | ✅ 一致（:1432-1435 仅传 `result["input"]` + `thread_id`，无 history 参数） |
| 10 | `graph.py:_astream_with_tracing` :199-205 三模式统一经装配 | ✅ 一致（:199-205 `assemble_graph_messages_with_memory(query, history_turns, ...)`） |
| 11 | `continuity.py:546-602` `assemble_graph_messages_with_memory`（包装面） | ✅ 一致（def :546，body 至 :602，含 security-input-isolation 槽位归因面） |
| 12 | `continuity.py:401-514` `_assemble_graph_messages_with_memory_impl` | ✅ 一致（def :401，下一顶层 def 在 :520，区间 401-514 精确） |
| 13 | `thread_store.py:63-90` `persist_thread_turns` | ✅ 一致（def :63，body 至 :90，user turn 记原文 `content=query` :82） |
| 14 | `sse_stream.py:334-341` `run.start` payload.query | ✅ 一致（:334-341 emit "run.start"，payload 含 `"query": query` :340） |

**统计：一致 14 / 漂移 0。**

## 2. 核对表

| 维度 | 判定 | 依据 |
|---|---|---|
| 范围（D1-D3） | ✅ 闭合 | 插入点（continuity 装配层末位追加之前）、开关（`LG_RAG_QUERY_REWRITE_ENABLED` 默认关）、降级（失败一律回原文）、审计口径（落盘/run.start 仍记原文）四要素齐备且互相自洽 |
| 非范围 | ✅ 钉死 | 不改 planner/aggregator/rag 取词、不透出 SSE/不落盘改写、不动 router 回环 `rewrite_node`、不动 continue 拼接、不默认开、无新依赖——6 条均明确可判 |
| 验收可机器化 | ✅ | 默认关逐元素零 diff（对拍断言）；金样三类（指代/省略/时间锚定各 ≥2）；失败注入降级 + span `query_rewrite_fallback=true`；首轮零 LLM 调用（调用计数断言）；FP-6 落盘原文；假 LLM 可全覆盖，不打真模型（R4 一致） |
| failure_paths | ✅ 完备 | FP-1~FP-7 覆盖：默认关零 diff / 首轮短路 / LLM 异常超时空输出降级 / 金样正向 / env 非法值 / 落盘口径 / basic+router 模式同开关。与验收清单一一对应 |
| 思考轮 R0-R5 | ✅ 闭合 | `actual_last_round=R5`；R2 方案对比 A/B/C/D 裁定落盘（§4）；R3 安全面（失败收敛到原文）与 R5（draft 不授权改 app/）均已回填；residual_risks 如实挂账（planner 带历史另案、金样覆盖靠 golden-eval 加强、人签未发生） |
| freeze 口径 | ✅ | 对照 `lg-rag-sse-v1`/`lg-rag-http-v1`：SSE 帧与请求体零变化；改写透出 SSE 需回 SPEC 升 freeze——闸门表述正确 |
| graph_change_layer | ✅ | `none` 预期合理（不增路由/表/event_type；图谱仅 lg_rag 行备注补开关一句） |

## 3. 阻塞项

无。

## 4. 非阻塞观察（供 00 / 10-task 参考，不改 SPEC 实质）

1. **N1 · `rewrite` 档尚未存在于模型目录**：SPEC D2「走 `resolve_task_model('rewrite')` 档」——实测 `app/llm/model_catalog.py:123-132` `TASK_TIER_MODELS` 现有键仅 `answer/grader/extract/structured/summary`；未知 task_type 会走 :156-158 `unknown_task` 告警分支。故 task 需在 `TASK_TIER_MODELS` 增 `"rewrite": None` 键（仿 summary 档 :128-131 先例，默认 None 不落档、回落 `_ROUTER_MODEL` 同档，与 SPEC D2 语义一致）。属实现面小改，SPEC 未点名该文件但 D2 已蕴含，graph_change_layer=none 不受影响。
2. **N2 · 重写与记忆召回的先后顺序未钉死**：impl 内记忆向量召回 `recall_with_vector(..., query, ...)`（`continuity.py:454-457`）吃的是 `query` 变量。若重写发生在召回之前，召回问句也会被改写（可能有益）；之后则召回仍用原文。SPEC 未规定，留 task 决策并在验收里钉一条。
3. **N3 · 「明显非问句」判定需具体化**：D2 降级条件含「输出非法（长度超界或明显非问句）」，其中「明显非问句」是启发式表述。假 LLM 注入下验收仍可机器化（注入既定非法样例），但 task 应把判定规则写成确定式（如长度上限数值 + 首行/空白规则），避免 30 自由发挥。

## 5. HG-SPEC-SIGNOFF 建议

**建议签收**（本帽不代签 · 仅维护者可签）。SPEC draft 与代码现状 14/14 锚点一致，范围/非范围/验收/failure_paths/R0–R5 五维闭合，默认关零 diff 的接入模式有 `SESSION_SUMMARY_ENABLED` 成例（`continuity.py:147-162`）可仿，风险面全部收敛到「失败用原文」。

## 6. 下一棒

HG-SPEC-SIGNOFF=approved 后：00 起草 task（`task/query-coref-rewrite`）→ 20-task-audit → HG-AUDIT-R1 → 30。本审查不构成任何 `app/` 改动授权。

---

## 修订记录

| 日期 | 说明 |
|---|---|
| 2026-10-19 | R1：14 锚点实测全一致，判定 pass，附 3 条非阻塞观察（N1 rewrite 档 / N2 召回顺序 / N3 非问句判定） |
