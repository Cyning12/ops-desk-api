# SPEC：多轮指代消解 · 装配层查询重写（v0 · 默认关）

> **状态**：`signed`（HG-SPEC-SIGNOFF=**approved** · 2026-10-19 维护者会话签收 · 20-spec-audit R1 pass）
> **track**：`feature`（历史感知的 query 重写，注入 continuity 装配层；不新增路由 / 表 / SSE event_type）
> **上游**：2026-10-19 supervisor 全流程架构审核会话（m00021 用户观察①：「supervisor 的 query 没做指代消解，多轮必然出现问题」——审核坐实，且比预想更彻底：planner 连历史都看不到）
> **建议序**：**1/5**（query-coref-rewrite → memory-injection-consumer → scenario-stage-rewire → delegation-naming-boundary → tech-graph-flow-resync）
> **现状锚点**：
> - planner 取词 `query=_last_user_text(state["messages"])`（`app/ops/lg_rag/multi/nodes.py:1106`），prompt 仅 `system(catalog)+user(query)` 两条（`multi/nodes.py:1163-1170`），**不带历史**；
> - aggregator 同样只吃原文 query+子任务结果（`multi/nodes.py:2107`、`_aggregator_plain_messages :2035-2043`）；
> - 装配层只做窗口压缩不改写：`compress_window`（`app/ops/lg_rag/continuity.py:44-79`，max_full_turns=6 / group_size=2），`_assemble_messages_from_compressed`（:82-98）末位追加 `HumanMessage(query)` 原文；
> - 全链路唯一文本变形是 `continue_from_run_id` 草稿拼接（`app/ops/lg_rag/router.py:339-342`，非语义改写）；
> - 代码内确有查询重写但只在 router 子图内部回环：`rewrite_node`（`app/ops/lg_rag/nodes.py:203-240`，写 `state.current_query`，对象是子任务检索问句）。
> **下游**：20-spec-audit / HG-SPEC-SIGNOFF → 00 出 task → 20-task-audit → HG-AUDIT-R1 → 30
> **Open Folder（实现）**：`ops-desk-api/`

---

## Harness 元信息

| 字段 | 值 |
|---|---|
| **spec_slug** | `query-coref-rewrite` |
| **invoke_slug** | `query-coref-rewrite` |
| **test_strategy** | `required` |
| **test_strategy_note** | 金样多轮会话（指代/省略/时间锚定三类）断言改写结果 · 默认关零 diff（消息序列逐元素相等）· 改写失败降级原文（不阻塞主链路）· 落盘与 run.start 仍为原文 · `mode=basic/router/supervisor` 三模式同开关生效 · 开关非法值回退关 |
| **默认分支** | `task/query-coref-rewrite` |
| **graph_change_layer** | `none` 预期（不增路由/表/event_type；`docs/_tech_graph/l1/01_modules.md` lg_rag 行备注补一句新开关即可，不走 G-L* 结构变更） |
| **freeze_id** | 对照 `lg-rag-sse-v1` / `lg-rag-http-v1`：SSE 帧与请求体零变化（改写只发生在图输入装配内）。若 30 需要把改写结果透出到 SSE（本波明确不做）→ 回本 SPEC 升 freeze |

### 人工闸（SPEC 阶段）

| human_gate_id | status | 说明 |
|---|---|---|
| **HG-SPEC-SIGNOFF** | approved（2026-10-19 维护者） | 维护者会话签收；审查文 `spec_query-coref-rewrite_audit_R1_20261019`（pass · N1–N3 移交 task 吸收） |

---

## 1. 背景与目标

多轮对话下用户 query 大量依赖上下文（「那个 PR 合了吗」「刚才说的表加个索引」）。当前 supervisor 链路：

1. 装配层把历史压缩后装进 `state.messages`，但 **planner 的 prompt 只有 catalog + 原文 query 两条消息**——历史在手却不给规划器；
2. rag 工人子图输入隔离（`astream_router_agent(result["input"], ...)`，`multi/nodes.py:1432-1435` 不传 history），检索问句= planner 拆出的子任务 input，指代未消解则检索必然跑偏；
3. aggregator 同样不看历史。

审核结论：**supervisor 链路没有任何指代消解，也没有面向 planner 的查询重写；用户 query 原文全程不改写。** 多轮场景必然拆解失败或幻觉编号。

### 一句话目标

在 **continuity 装配层**（末位 `HumanMessage(query)` 追加之前）插入可选的「历史感知 query 重写」步骤：用压缩后历史 + 原文 query 产出**自足问句**（self-contained query），下游 planner / rag 检索 / aggregator 全部吃重写结果；**env 默认关**，开启后改写失败一律降级原文。

---

## 2. 范围

单 task。

### D1 · 重写插入点：continuity 装配层

| 项 | 约定 |
|---|---|
| 位置 | `assemble_graph_messages_with_memory`（`continuity.py:546-602` → impl :401-514）内，`_assemble_messages_from_compressed`（:82-98）末位追加之前 |
| 输入 | 压缩后历史 turns + 原文 query（此刻是**全链路唯一两者皆备的单点**） |
| 输出 | `resolved_query`：自足问句；若历史为空或重写判定「无需消解」→ 原样返回（零 LLM 调用短路允许，见 D3） |
| 生效面 | `graph.py:_astream_with_tracing`（:199-205）三模式（basic/router/supervisor）统一生效——三者都经此装配 |
| 先例 | 仿 `SESSION_SUMMARY_ENABLED`（session-summary-fallback 已实施 · 默认关）零 diff 接入模式 |

### D2 · 开关与降级

| 项 | 约定 |
|---|---|
| env | `LG_RAG_QUERY_REWRITE_ENABLED`（**默认 0=关**；非法值回退关） |
| 模型档 | 走 `resolve_task_model('rewrite')` 档（复用 tier 路由；档未配时回落 `_ROUTER_MODEL` 同档，不新造档位语义之外的特例） |
| 降级 | 重写 LLM 异常 / 超时 / 输出为空 / 输出非法（长度超界或明显非问句）→ **静默降级原文 query**，span 记 `query_rewrite_fallback=true`；**禁止**因重写失败让主链路失败 |
| 预算 | 重写调用经 LLM 工厂切面（预算/熔断/缓存照常生效）；`OPS_LLM_INFER_CACHE_ENABLED` 下 task_type=structured 可缓存 |

### D3 · 消耗面与审计口径

| 项 | 约定 |
|---|---|
| 消耗方 | 装配层末位 `HumanMessage(resolved_query)`——planner、aggregator、rag 工人自动吃到（无需改各自取词代码） |
| 落盘 | `persist_thread_turns`（`thread_store.py:63-90`）与 `run.start` payload.query（`sse_stream.py:334-341`）**仍记原文**；改写结果只进 prompt 不落盘（避免双真源口径漂移） |
| 可观测 | span/log 记 `query_rewrite_applied`（bool）+ 原文/改写后长度；**不**记改写全文进日志（与「审计记动作不记内容」纪律一致） |
| 与 continue_from_run_id 关系 | 草稿拼接（`router.py:339-342`）发生在 worker 上游、进装配层之前；重写看到的是拼接后文本——本波**不改**该拼接逻辑，只在 SPEC 记录此顺序事实 |

---

## 3. 非范围

- ❌ 改 planner / aggregator / rag 工人的取词逻辑（消耗面靠装配层输出天然覆盖）
- ❌ 把重写结果落盘或透出到 SSE / history API（口径：原文是唯一持久真源）
- ❌ 改 router 子图内部 `rewrite_node`（质量回环改写，对象不同，各司其职）
- ❌ 改 `continue_from_run_id` 草稿拼接语义
- ❌ 默认开启；❌ 多轮重写（每请求至多一次重写调用）
- ❌ 引入检索式指代库 / 实体库（本波纯 LLM 重写，无新依赖）

---

## 4. 方案对比（R2 落盘）

| 方案 | 内容 | 裁定 |
|---|---|---|
| A supervisor_node 内重写 | planner 取 query 处自带历史调 LLM 重写 | **弃**。只惠及 planner，rag 检索与 aggregator 仍吃原文；且与其他模式行为分裂 |
| B planner prompt 直接带历史 | 不重写，把压缩历史塞进 planner prompt | **弃**（本波）。prompt 膨胀且 rag 检索问句仍是原文指代；可作后续「planner 上下文增强」另案 |
| C 本 SPEC：装配层统一重写 | 唯一两者皆备单点，三模式生效 | **采纳** |
| D 前置独立 coref 节点 | 图内新增节点 | **弃**。新增图拓扑/状态字段，成本与收益不成比例；装配层已是天然位置 |

---

## 5. failure_paths

| ID | 路径 | 期望 |
|---|---|---|
| FP-1 | 开关默认（关） | 消息序列与改前逐元素相等（零 diff 断言） |
| FP-2 | 开关开 + 首轮无历史 | 短路返回原文；允许零 LLM 调用 |
| FP-3 | 开关开 + 重写 LLM 异常/超时/空输出 | 降级原文，主链路继续；span `query_rewrite_fallback=true` |
| FP-4 | 开关开 + 指代 query（金样） | 末位 HumanMessage 为自足问句；planner 收到改写后文本 |
| FP-5 | env 非法值 | 行为同关 |
| FP-6 | 落盘与 run.start | 仍记原文 query（双写两表口径不漂移） |
| FP-7 | `mode=basic/router` | 同开关生效；既有测试无行为差（默认关保证） |

---

## 6. 验收

- [ ] 默认关：三模式消息装配逐元素零 diff
- [ ] 开 + 金样多轮（指代/省略/时间锚定各 ≥2 条）：末位 HumanMessage 为自足问句，planner/aggregator 实际收到
- [ ] 开 + 重写失败注入：降级原文，主链路产出不受影响，span 有 fallback 标记
- [ ] 首轮无历史：零额外 LLM 调用
- [ ] `persist_thread_turns` 与 `run.start` payload 记原文
- [ ] pytest 覆盖 FP-1~FP-7 为绿；不新增 SSE event_type / 路由 / 表

---

## 7. 风险

| 风险 | 缓解 |
|---|---|
| 重写引入语义漂移（改错意思） | 默认关；金样断言；失败降级原文；重写 prompt 约束「只消解指代与省略，不增删意图」 |
| 每请求多一次 LLM 延迟 | 首轮短路；同档小模型；缓存可命中；开关制 |
| 与 `continue_from_run_id` 拼接文本交互意外 | 本波不改拼接；金样含一条 continue 场景 |
| 改写落盘口径被误改 | FP-6 否决 + 验收断言 |

回滚：env 关掉即恢复；代码面开关短路在装配层单点。

---

## 8. 思考轮控制

| 轮 | 结论 | early_stop | reason | residual_risks |
|---|---|---|---|---|
| R0 | 用户观察①坐实：无指代消解且 planner 不见历史 | no | | |
| R1 | 范围=装配层重写单点 + 开关 + 降级 + 审计口径；消耗面/落盘/router 回环非范围 | no | | |
| R2 | 采纳 C（装配层）；弃 A（节点内）、B（prompt 带史）、D（新图节点） | no | | planner 带历史是否后续仍需（另案） |
| R3 | 失败一律降级原文；不记改写全文；continue 拼接顺序事实记录 | no | | 重写语义漂移靠金样挡 |
| R4 | 假 LLM 可测全部 FP；金样三类 | no | | 金样覆盖率靠后续 golden-eval 加强 |
| R5 | draft 可交 20-spec-audit；不可当已签收 | no | 人签未发生 | HG-SPEC-SIGNOFF=pending |

`actual_last_round`：R5

### R0
审核会话证据链：`multi/nodes.py:1106` 取原文、:1163-1170 两条消息、aggregator :2035-2043 同样不吃历史、continuity :82-98 原文追加。

### R1
角色：多轮运维问答。成功=指代 query 被正确拆解与检索；失败=重写坏也不伤主链路。

### R2
见 §4。装配层是唯一「历史+原文皆备」且三模式共用的单点。

### R3
安全：不改鉴权/闸链；重写失败面全部收敛到「用原文」。

### R4
`test_strategy=required`，假 LLM 注入即可，不打真模型。

### R5
本文件不授权改 `app/`。下一棒：20-spec-audit 或维护者人签，然后 00 起草 task。

---

## 9. 修订记录

| 日期 | 说明 |
|---|---|
| 2026-10-19 | v0 draft：supervisor 全流程审核发现①落盘（指代消解缺失 · 装配层插入 · 默认关） |
| 2026-10-19 | HG-SPEC-SIGNOFF=approved（维护者会话签收 · R1 pass · N1–N3 移交 task）；交 00 起草 task |
