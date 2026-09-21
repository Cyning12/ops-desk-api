# 审查文：task_llm_layer_hardening · 20-task-audit R1

> **审查帽**：20-task-audit（书面审 · 不实现代码 · 不代签人闸）
> **审查日期**：2026-09-21
> **被审对象**：`docs/tasks/active/task_llm_layer_hardening.md`（状态 draft · 2026-09-21 10-task 落稿）
> **对照基准**：`docs/spec/llm-layer-hardening/SPEC-llm-layer-hardening_v1.md`（signed · HG-SPEC-SIGNOFF=approved 2026-09-21）
> **图谱真值**：`docs/_tech_graph/l1/01_modules.md`（本帽亲读复核）

---

## 一、结论摘要

| 维度 | 结论 |
|------|------|
| **内容审查** | **退回 10-task**（1 项内容阻塞，见 §三-B1） |
| **流程闸 HG-AUDIT-R1** | **pending**（符合预期 · 本帽不签 · 00 依维护者授权待 20 终轮零阻塞后代录） |
| **流程闸 HG-GRAPH-MODULES** | approved（模块表已建置）与真值文件一致 ✓；D5 新签义务留验收标准，处理正确 ✓ |
| **下一棒** | **10-task**（补列 B1 验收项）· **禁止附 30 Prompt** |

---

## 二、核对项清单（逐项）

| # | 核对项 | 结果 | 说明 |
|---|--------|------|------|
| 1 | 范围 vs SPEC §2 | ✅ | D1 重试 / D2 熔断 / D3 路由 / D4 usage 落表 / D5 图谱文档，五块一一对应，无缺无溢 |
| 2 | 非范围 vs SPEC §3 | ✅ | 9 条逐字对齐（新 provider / 结构化输出语义 / 流式协议 / fallback 链内容 / 对账 UI / Redis 共享存储 / embed·rerank 记账 / 价表 / web·ios） |
| 3 | 验收标准断言化、可测 | ✅ | 全否定性断言：重试次数=MAX_ATTEMPTS · sleep 序列上界不假 sleep · 零重试反向断言（调用计数=1）· 熔断零出网断言 · advance 拨时间不真等 60s · 按 run_id 聚合真查表 · 无 0 假账 · 变异检验一条防空真规则 |
| 4 | 验收覆盖 SPEC 四块 | ✅ | D1×5 / D2×5 / D3×4 / D4×5 + 工程×4，与 SPEC §6 逐条一致 |
| 5 | failure_paths | ✅ | 17 行 = SPEC §5 全部 15 行内容行 + 2 行流程行（HG-AUDIT-R1 pending 拒开工 · 无变异检验拒收）；语义无漂移 |
| 6 | R0–R5 思考轮控制表 | ✅ | 表 + 每轮子节齐；early_stop 全 no（reason 列无需填）；actual_last_round=R5 回填闭合；residual_risks 继承 SPEC 三条（重试参数校准 / ContextVar 并发串扰 / 占位价偏差）无遗漏 |
| 7 | test_strategy | ✅ | `required` + note（fake provider/fake httpx · advance hook · 全波次回归 test_llm_providers / test_chat_nodes），与 SPEC 元信息一致 |
| 8 | graph_change_layer | ✅ | `G-L1`；graph_delta 指向 `01_modules.md` `llm` 行备注（依赖出边 +`db`），不新增一级模块——与真值文件结构兼容 |
| 9 | review_hat | ✅ | `20`（默认正确） |
| 10 | 人工闸表 · HG-AUDIT-R1 仍 pending | ✅ | pending · blocks 30 · 「10-task 不代签」声明在案 |
| 11 | 人工闸表 · HG-GRAPH-MODULES 与真值一致 | ✅ | 本帽亲读 `01_modules.md`：bootstrap 签 2026-07-16（人签记录首行）· `llm` 行在模块表（第 32 行）· 2026-09-21 当日签录存在（memory_facts_p1 / memory_facts_p0 / tech_graph_recent_sync 三行）——task 闸表表述属实 |
| 12 | 现状锚点实扫（抽查） | ✅ | `base.py:94` 四段超时 ✓ · `rag_nodes.py:33` GRADER_MODEL ✓ · `model_catalog.py:105` siliconflow 链返回 `[]` ✓ · `circuit.py` exclude/throw_new_error_on_trip/snapshot ✓ · `schema.py` retryable ✓ · pybreaker 在 requirements.txt:17 ✓ · `lg_rag/router.py:231,296` hex run_id ✓ · `chat/streaming.py:58-61` ops_runs ✓ |
| 13 | 行为变更类 task「旧测 grep 影响面」验收项 | ❌ | **缺失 → B1 退回项**（见 §三） |
| 14 | 钉死契约 vs SPEC §1/§2 | ✅ | 25 行契约表与 SPEC 钉死语义一致（重试判据 / 退避算法 / 流式纪律 / 熔断叠序 / 路由解析序 / 新表 schema / 落表语义 / env 纪律 / SSE 零改） |

---

## 三、阻塞项（退回 10-task）

### B1 · 行为变更类 task 缺「旧测 grep 影响面」验收项（内容阻塞）

- **依据**：20-task-audit checklist K7——行为变更类 task（改默认值 / 校验 / 策略门 / fallback 语义）验收标准须含「旧测 grep 影响面」项，缺则退回 10-task 补列。
- **本 task 属行为变更类**：重试默认开（`OPS_LLM_RETRY_ENABLED=true`）、熔断默认开（`OPS_LLM_CB_ENABLED=true`）、grader 模型解析序改造（`RAG_GRADER_MODEL` 并入档覆盖链）——三者均改变既有调用路径的默认行为。
- **现状**：task 已有回归底线（test_strategy_note + 工程验收「`tests/test_llm_providers.py` / `tests/test_chat_nodes.py` / memory 抽取回归」）与「开关关闭 = 现网逐字节一致」反向断言，但**未枚举旧测影响面**——例如 `tests/` 中直接 fake provider / 断言「429 立即 fallback」「失败即抛」的旧测，在重试默认开后可能假绿或误红，30 开工前需要一张明确的 grep 清单。
- **补列要求（10-task）**：在验收标准（建议工程小节）增一项，形如：「grep `tests/` 中直接调用 `complete/complete_stream`、fake `LlmProviderError`、断言 fallback/失败行为的旧测清单落盘（或列于本项），逐条标注「不受默认开重试/熔断影响 / 需随本波更新」，30 以此为准」。属补列，不动既有条目。

---

## 四、非阻塞备注（轻微 · 不代改 · 10-task 补列时可顺带）

1. **闸表表述可更全**：HG-GRAPH-MODULES 行称「最近签录 2026-09-21 hitl/tech-graph-sync」；真值文件 2026-09-21 当日实有三行签录（memory_facts_p1 / memory_facts_p0 / tech_graph_recent_sync）。不影响「模块表已建置 approved」真值一致性，仅表述精度。
2. **锚点归属略含糊**：现状锚点行「siliconflow `get_fallback_chain` 返回 `[]`」——函数实址在 `app/llm/model_catalog.py:101-105`（siliconflow.py 内无此函数），语义正确、归属提示可更准。
3. **与 SPEC §8 的编排差异（演进非冲突）**：SPEC §8 将「图谱 `llm` 行新签」写在 20-task-audit 棒次；task 将其演进为 D5 随 30 落盘（00 代录），并在闸表/验收标准留义务。task 编排更细，仅提示维护者签闸时知悉。
4. **20 invoke 快照义务**：task `required_invoke_hats` 含 `20`，按规 20 棒须落 invoke 快照至 `docs/harness/invokes/by-task/llm-layer-hardening/`（现仅有 10 棒一份）。本帽本轮被指令限定只写 reviews/，该义务提请 00/维护者按仓流程补落。

---

## 五、回填清单（交 10-task）

| # | 小节 | 动作 |
|---|------|------|
| 1 | 验收标准 · 工程 | 补列「旧测 grep 影响面」项（见 §三-B1 补列要求） |
| 2 | 人工闸表（可选） | HG-GRAPH-MODULES 说明补全 2026-09-21 三行签录表述 |
| 3 | 现状锚点（可选） | `get_fallback_chain` 锚点改指 `model_catalog.py:101` |

---

## 六、人工闸状态声明

- `HG-AUDIT-R1` = **pending**（blocks 30）——本轮内容未过，**不进入签闸流程**，本审查文不附签闸清单、**不附 30 Prompt**。
- `HG-GRAPH-MODULES` = approved（模块表已建置，真值已亲核）；本 task D5 的 `llm` 行备注新签义务留在验收标准，随 30 落盘（00 代录）。
- 10-task 补列后交 20-task-audit R2 复审；R2 零阻塞后方进入维护者签闸（00 依授权代录）→ 30。

---

## 修订

| 日期 | 说明 |
|------|------|
| 2026-09-21 | R1：14 项核对 13 过 1 阻（B1 旧测 grep 影响面缺失）→ 退回 10-task；HG-AUDIT-R1 保持 pending；锚点 8 处实扫全过 |
