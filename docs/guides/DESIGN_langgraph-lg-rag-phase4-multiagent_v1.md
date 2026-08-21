# Detailed Design：lg_rag Phase 4 · Multi-Agent（Supervisor 协作）（v1 · 待审）

> **总纲**：`docs/guides/PLAN-langgraph-agent-framework_v1.md` Phase 4（第 6–8 周 · 多智能体协作）  
> **前置资产**：Phase 1（basic）· Phase 2（router 三路，标注集 34 条 100%）· Phase 3（evaluate/rewrite 回环）  
> **状态**：draft · 待维护者审；审后 HG-TASK-DRAFT 方可转 approved  
> **硬约束延续**：不改 `app/ops/chat/graph.py`；不改 `lc_evidence_chain` 内部；不挂 SSE  
> **包约束**：落在 `app/ops/lg_rag/` 内（子包 `multi/`，非平行新包）

---

## 1. 目标与拓扑

**目标**（PLAN 4.1–4.5）：Supervisor 拆解复合问题 → 分派专业 Agent → Aggregator 综合成结构化答案。

```text
START → supervisor_node（LLM 拆解，≤4 子任务）
          → dispatch_loop（条件边：取下一子任务）
              ├─ type=rag     → rag_subtask_node（调 router 图子图）
              ├─ type=extract → info_extract_node（LLM 实体抽取）
              ├─ type=tool    → tool_exec_node（Mock 工具注册表）
              └─ 子任务耗尽    → aggregator_node（LLM 综合）→ END
```

三图并存延续：basic（P1 对照）/ router（P2/P3 主路径）/ **supervisor（P4 新增）**；互不破坏。

## 2. State 扩展

```python
class LgRagState(MessagesState):
    ...                            # Phase 1-3 字段
    subtasks: list[dict]           # Supervisor 产出：[{"id","type","input","tool"?}]
    subtask_results: list[dict]    # 各子任务结果（追加；含 type/input/output/meta）
```

- `subtask_results` 用 `Annotated[list[dict], add]` reducer（对齐 PLAN 草案 logs 语义）。
- dispatch 用索引推进：`len(subtask_results) < len(subtasks)` 即未耗尽（结果与子任务按序一一对应）。
- 老 checkpoint：两字段缺失时 supervisor 图不可入（入口即 supervisor 写入；router/basic 图不受影响）。

## 3. Supervisor（PLAN 4.1）

- LLM 拆解（同档小模型、低温度）：输入用户 query，输出 JSON `{"subtasks": [{"id","type","input","tool"?}]}`；`type ∈ {rag, extract, tool}`；`tool` 仅 tool 型需要（注册表键）。
- **约束**：cap=4（超出截断）；单问/无法拆解 → 单 rag 子任务（**fallback 不失败**，对齐 router 的「宁退化不失败」）。
- 输出非法 → 同上 fallback。
- 拆解决策写 span metadata（子任务数、类型序列、原始输出截断）。

## 4. 三个专业 Agent

| Agent | 实现 | 要点 |
|---|---|---|
| RAG SubGraph（PLAN 4.2） | `rag_subtask_node` 内部 `ainvoke_router_agent(input)`——**复用 Phase 2/3 全能力**（意图分流 + 自纠错）；router 图本身即可独立运行的子图 | 子图输入隔离（fresh messages），不污染父历史；结果 = 末条 AIMessage + chain_meta 摘要 |
| InfoExtract（PLAN 4.3） | `info_extract_node`：LLM 从输入文本抽 `{dates[], versions[], people[]}` JSON；输入 = 子任务指定的文本（v1：原 query 或前序 rag 结果文本） | 输出非法 JSON → 空结构 + warning，不中断 |
| Tool Executor（PLAN 4.4） | `tool_exec_node`：Mock 注册表 `{name: fn}`（如 `mock_get_issue_status` / `mock_get_deploy_info`，返回罐头数据） | 未知工具 → 记录错误结果不中断；接口预留真实工具接入 |

## 5. Aggregator（PLAN 4.5）

- LLM 综合全部 `subtask_results` → 结构化 markdown：按子任务分节 + 来源标注（rag 引用 / 抽取实体 / 工具数据），末尾「综合结论」节。
- 追加最终 AIMessage；中间结果只在 `subtask_results`，不进 messages（避免消息膨胀——吸取 Phase 3 中间答案留存教训）。

## 6. 观测

- `propagate_attributes(trace_name="lg-rag")` 延续；supervisor/dispatch/各 agent/aggregator 均 `trace_span`；子任务序在单 trace 树可见。

## 7. 测试策略

| 层 | 内容 |
|---|---|
| mock 单测 | 拆解→分派→综合全链（mock 3 处 LLM + chain）；cap=4 截断；拆解失败 fallback 单 rag；extract 非法 JSON 容错；未知 tool 容错；空 subtasks 防死循环；三图并存互不回归（21 passed 不破坏） |
| 实跑演示 | 3–5 条复合 query（含 G37 型多问、版本/日期抽取问、可命中 mock 工具的问）：人工核子任务拆分合理性与综合答案覆盖面，结果记 task |

## 8. 失败路径

| 触发 | 行为 | 可重试 |
|---|---|---|
| 拆解 LLM 失败/非法 | fallback 单 rag 子任务 | Y |
| 子任务执行异常 | 记录错误结果，继续后续子任务 | Y |
| extract JSON 非法 | 空结构 + warning | Y |
| 未知 tool | 错误结果记录 | Y |
| aggregator LLM 失败 | 异常上抛（与全站一致） | Y |

## 9. 非范围（Phase 4）

- Send API 并行 fan-out（v1 顺序执行；并行另议）
- HITL / interrupt；Store 长期记忆
- 真实外部 API 工具（Mock 先行）
- SSE / Chat 接入；Chat 图任何改动
- 全量 73 条 Golden（另开 task）；检索层长句零命中修复（已立分析 task）

## 10. 验收标准（草案，以 task 表为准）

- [ ] 复合问题拆解 → 分派 → 综合全链走通（mock + 实跑演示）
- [ ] cap/fallback/容错路径 mock 覆盖；三图 21+ 单测不回归
- [ ] Langfuse 单树可见子任务序
- [ ] `git diff master`：chat/graph.py 与 lc_evidence_chain 零改动
- [ ] G-L1 更新 + graph-compile；ruff 绿

---

## 修订

| 日期 | 说明 |
|---|---|
| 2026-08-21 | 首版（AI 起草 · 待审）：Supervisor 顺序 fan-out v1；rag 子任务复用 router 图；Mock 工具注册表；aggregator 综合 |
