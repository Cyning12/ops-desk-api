# task（草案 · 人工闸 pending · 拒开工）：契约闸 produces 未兑现收窄 + 前缀锁定死锁带内逃生口

> **状态**：HG-AUDIT-R1 已签（2026-10-28 · m00811），可开工。
> **由来**：2026-10-27 复跑实证 run `d3a49527929248cc953b7a5327cae2d0`（635 事件 · 400s · budget_exhausted）：t2 consumes 已收敛 `['title','body']`（全部真实存在），仍被拦 `contract_missing_field`——拦因是闸判定 3「produces 未兑现」，与 consumes 无关。
> **分支**：task/lg-rag-gate-produces-unfulfilled（维护者签收后新建，本窗不建）。

## 根因（已钉案，2026-10-27 run d3a49 事件链实证）

死锁四环：

1. `gate()` 判定 3（`app/ops/lg_rag/multi/step_contract.py:246-257`）：对 `depends_on` **全部**前驱校验其声明 produces 是否兑现，**不管本步 consumes 是否消费缺失字段**。d3a49 中 t1 声明 `['title','body','status']` 未兑现 `status`，t2 只需要 `title/body`，照样拦死。
2. t1 已成功终态 → 锁定/保号区域 → 它的 produces 错误声明**重规划改不动**（重规划能改的只有下游 consumes，而拦因不在 consumes）。
3. B 层 detail（PR #293）已把正确字段清单喂进 prompt——aggregator 甚至照抄进终答——但**修复点（t1 声明）在模型够不到的地方**，且 prompt 没有告诉模型可以重发前驱步。
4. 重规划两轮照抄同一计划 → `budget_exhausted`（seq 634，latency 400385ms），write 从未执行。

安全性论证（收窄不引入风险）：worker 能拿到的数据只有 `collect_values` 按 consumes 显式绑定的字段，且只收产出里真实存在的（`step_contract.py:273-279`）——未被消费的未兑现声明不构成任何实际数据流，拦它没有防御收益，只制造死锁。

## 修复设计（两子项，同一闸文件）

- **B1 · 判定 3 收窄**：produces 未兑现且缺失字段**未被本步 consumes 引用** → 不再 `return BLOCKED`，降级为观察留痕（span/事件，复用既有通道不新增事件类型），放行。consumes 引用了缺失字段的情形本就被判定 2 拦截（语义零回归）。注意纯序依赖（depends_on 无 consumes）同样放行。
- **B2 · 带内逃生口指令**：失败摘要段（`app/ops/lg_rag/multi/nodes.py` `_format_prefix_block` failed 段，PR #293 A 层落点）在 blocked_by=contract_missing_field / prefix_touch_required 场景附明确指引——「前驱声明字段不存在且前驱已终态锁定：以修正后 produces **重发前驱步**（新 subtask_id），勿照抄原声明」。实现期须实证：已终态前驱的行在重规划中是否可改写（保号逻辑 `_stamp_host_plan`），若不可改写则指引只保留「重发新步」口径。

## 非范围

- capability manifest output_schema（**task A** `task_lg_rag_capability_output_schema.md` 的地盘，互为姊妹 task）。
- 前缀不可变语义本身（仍不可变；本 task 只是在不可变前提下给带内逃生口）。
- 判定 1（predecessor_failed）与判定 2（consumes 缺失）语义不动。
- critic verdict / 预算策略不动。

## 验收标准

- [ ] 1. 单测复刻 d3a49 闸场景：前驱终态 output 缺其声明 produces 字段、本步 consumes 全部命中 → `gate()` 放行 + 观察留痕断言（此前返回 contract_missing_field 的用例按新语义适配，属预期内测试变更）。
- [ ] 2. 零回归：consumes 引用缺失字段 → 仍拦（判定 2）；dep 在 prefix → `prefix_touch_required` 分类不变；判定 1 不动。
- [ ] 3. 单测：失败摘要段在上述场景含「重发前驱步」指引文案；无失败步主路径 prompt 逐字节零 diff（承 PR #293 FP 口径）。
- [ ] 4. `.venv/bin/ruff check app tests` 绿（钉版 0.15.21）；`pytest tests` 不引入新红（既有 28 红基线口径）。
- [ ] 5. 40 live：复跑 #2140 query，t2 write 实际执行成功、不再 budget_exhausted（LLM 弹性项，失败须附 run 事件链分析）。

## failure_paths

- 放行后下游「隐式」需要未兑现字段 → 不存在该路径：worker 只见 consumes 绑定值（见根因安全性论证）；缺数据由 worker/aggregator 自然表达，不崩。
- B2 指引文案被模型忽视（照抄惯性）→ 观察留痕可度量（指引出现次数 vs 照抄次数），不阻断主流程；极端情形仍有 budget 闸兜底终局。
- 与 task A 联序：A 让声明不再错，B 让错了救得回；两者独立可合，建议 B 先行（解锁面更直接）。

## Harness 元信息

| 字段 | 值 |
|---|---|
| **task_slug** | `lg-rag-gate-produces-unfulfilled` |
| **git_branch** | `task/lg-rag-gate-produces-unfulfilled` |
| **implement_repo** | `ops-desk-api` |
| **test_strategy** | `required` |
| **test_strategy_note** | 闸语义单测（放行/零回归/指引文案/FP 零 diff）+ 40 live 复跑 d3a49 场景 |
| **code_quality_bar** | `L2_backend` |
| **graph_change_layer** | `none` |
| **graph_delta** | `n/a（观察留痕复用既有 span/事件通道，不新增事件类型）` |
| **wiki_delta** | `n/a` |
| **review_hat** | `20` |
| **required_invoke_hats** | `10,30,40` |
| **invoke_retention_profile** | `default` |
| **close_pr_policy** | `required` |

### 自检结论

结构对齐本仓已合并先例（task_supervisor_replan_error_feedback · PR #293）；元信息块预填含 wiki_delta。与 task A 互指非范围、独立可合；建议实施顺序 B 先于 A（B 直接解死锁，A 源头消猜）。

## 人工闸表

| 闸 | 状态 | 备注 |
|---|---|---|
| HG-AUDIT-R1 | approved | 维护者 2026-10-28 签收（m00811「签收，删除草稿」） |
| HG-GRAPH-MODULES | n/a | 不动图谱分层 |
