# 审查文：task_llm_layer_hardening · 20-task-audit R2（终轮复审）

> **审查帽**：20-task-audit（书面审 · 不实现代码 · 不代签人闸）
> **审查日期**：2026-09-21
> **被审对象**：`docs/tasks/active/task_llm_layer_hardening.md`（draft · 2026-09-21 R1 退回修订版）
> **对照基准**：`docs/spec/llm-layer-hardening/SPEC-llm-layer-hardening_v1.md`（signed · HG-SPEC-SIGNOFF=approved 2026-09-21）
> **前轮审查**：`docs/harness/reviews/task_llm_layer_hardening_audit_R1_20260921.md`（退回 · 阻塞项 B1）
> **图谱真值**：`docs/_tech_graph/l1/01_modules.md`（本帽亲读复核）
> **本轮指令边界**：只写 reviews/ 下文件 · 不改 task 实质内容

---

## 一、结论摘要

| 维度 | 结论 |
|------|------|
| **内容审查** | **PASS-with-notes（零内容阻塞 · B1 闭合）** · 本轮为终轮，**签收 / 关闭** |
| **流程闸 HG-AUDIT-R1** | **pending**（符合预期 · 本帽不签 · 00 依维护者授权于本审查文落盘后签 task 表） |
| **流程闸 HG-GRAPH-MODULES** | approved（模块表已建置）与真值文件一致 ✓；闸表 2026-09-21 三行签录表述已补全 ✓；D5 新签义务留验收标准 ✓ |
| **下一棒** | **维护者签闸**（00 依授权代录 HG-AUDIT-R1=approved）→ 30 · 闸签前**禁止**下发 30 Prompt |

---

## 二、B1 闭合判定（R1 唯一阻塞项）

**判定：闭合。** 双重要求均满足：

### ① 清单是否实扫所得 —— 是（本帽逐项亲扫复核）

10-task 新增「旧测影响面清单（B1）」小节（task 202-219 行），12 条清单全部带锚点、影响分析、三态处置（回归/改编/删除）。本帽对全部锚点做了实扫核验：

| # | 清单锚点 | 核验结果 |
|---|---------|---------|
| 1 | `test_llm_providers.py::test_missing_api_key`(246) · `test_4xx_non_retryable`(253) | ✅ 行号精确；缺 key→ValueError / 401→retryable=False 断言属实 |
| 2 | `test_retryable_errors`(265→实 266，装饰行 265) · `test_sse_parse_error_retryable`(278) · `test_request_error_retryable`(289) | ✅ 三测均为「可重试错误即抛」旧语义；改编处置（假时钟 / MAX_ATTEMPTS=1）对症 |
| 3 | `test_fallback_emits_event`(374) | ✅ 实扫确认 deepseek-v4-pro 503 → `model.fallback` 换 deepseek-v4-flash，from/to 断言与清单描述逐字一致 |
| 4 | `test_fallback_chain_exhausted`(393) | ✅ 三候选全 503 → retryable=False「exhausted」，与清单描述一致 |
| 5 | `test_non_retryable_stops_fallback`(408) · `test_test_only_models_filtered`(422) · `test_explicit_model_skips_fallback`(436) · `test_complete_skips_fallback_meta`(496) | ✅ 四测行号全中，均不涉重试触发，「回归」处置正确 |
| 6 | `test_chat_nodes.py::test_answer_node_handles_error`(191-208) | ✅ FailingProvider 继承 `BaseProviderImpl`（195 行）抛 retryable=True；改编处置（假时钟）对症 |
| 7 | `test_chat_nodes.py`(147/165 成功路径) · `test_chat_ws.py`(23/46) | ✅ 147/165 为两成功路径测；chat_ws `FakeProvider(BaseProviderImpl)` 在 23 行（fixture 实址 45-53，±1 行偏差见备注 N1） |
| 8 | `test_memory_extract_p1.py::test_extract_provider_error_zero_writes`(383-401) | ✅ `@_DB_SKIP` 383 · def 384 · `provider.calls == 1` 在 400；FakeProvider（42 行）亲核**继承 `BaseProvider` 非 BaseProviderImpl**——清单关键论断属实 |
| 9 | `test_lg_rag_sse_token_stream.py`(45) · `test_lg_rag_retry.py`(17) · `test_lg_rag_router.py`(100/114) · `test_lg_rag_multi.py`(179/198) | ✅ 五处全中：45=`_FakeProvider(BaseProvider)` · 17=`_PROVIDER_PATCH=get_llm_provider` · 100/114=router 异常/非法输出 fallback · 179/198=decompose 非法/异常 fallback——「节点级 fallback 与传输重试正交」定性正确 |
| 10 | 熔断全局态 · conftest 先例 | ✅ `tests/conftest.py:194-203` 亲核：`circuit_reset()`（196/199）+ `fallback.reset()`（203）autouse 先例在案，比清单所述更全 |
| 11 | `RAG_GRADER_MODEL` 消费点 + tests/ 零命中 | ✅ 全仓 grep 亲扫：rag_nodes.py:32-33 ✓ · lg_rag/nodes.py:38 ✓ · lc_evidence_chain/grader.py:24 ✓（29 行为 GRADER_MODEL 常量消费）· run_eval.py:656/685/708 ✓（38 行为 import 消费）；**tests/ 下零命中属实**（命中仅 experiments/ 两份 README 与 docs/，非测试断言） |
| 12 | usage 钩点 `base.py:31-34` | ✅ `_complete_from_stream` 聚合 complete_stream 并触 `_report_complete_usage`（43-44 行）属实 |

### ② 断言是否可测 —— 是

- 工程验收新增**闸前置**项（task 196 行）：「30 开工前旧测影响面清单已落盘且逐条有处置（回归/改编/删除理由）……30 逐条执行处置并在提交说明逐条回填」——可机械核验（清单在案 ✓ · 处置列非空 ✓ · 提交说明回填可由 40/verify 抽查）。
- failure_paths 新增一行（task 155 行）：「30 开工前旧测影响面清单未落盘或逐条无处置 → 拒收（B1）」——与闸前置项互为表里，流程语义清晰。
- 处置三态定义（回归/改编/删除）在节首明确定义，删除须附理由——闭环。

---

## 三、修订漂移全量重核（对照 SPEC）

| # | 核对项 | 结果 | 说明 |
|---|--------|------|------|
| 1 | 范围 vs SPEC §2 | ✅ | D1–D5 五块较 R1 **零改动**，与 SPEC 一一对应 |
| 2 | 非范围 vs SPEC §3 | ✅ | 9 条逐字未动 |
| 3 | failure_paths vs SPEC §5 | ✅ | 现 18 行 = SPEC 15 行内容行 + 3 行流程行（HG-AUDIT-R1 pending 拒开工 · 无变异检验拒收 · **新增 B1 旧测清单拒收**）；新增行属流程行，SPEC 内容行语义无漂移 |
| 4 | 验收 D1–D4 vs SPEC §6 | ✅ | 逐条未动；工程小节仅 +1 闸前置项（B1 要求），其余 4 条未动 |
| 5 | 钉死契约 | ✅ | 25 行未动；B1 清单 #8「防 30 误把重试层套上抽象层」与契约「施加面 = BaseProviderImpl 边界」一致，无新语义 |
| 6 | R0–R5 思考轮 | ✅ | 控制表与各轮子节未动；early_stop 全 no；actual_last_round=R5；residual_risks 三条继承 SPEC 无遗漏 |
| 7 | 新增内容是否越界 | ✅ | B1 清单 12 条全部为 tests/ 影响面枚举 + conftest 工程项（#10），属测试工程细化，未引入新功能面/新依赖/新 env，不构成范围蔓延 |
| 8 | 闸表 · HG-AUDIT-R1 仍 pending | ✅ | pending · blocks 30 · 「10-task 不代签」在案 |
| 9 | 闸表 · HG-GRAPH-MODULES 与真值一致 | ✅ | 本帽亲读 `01_modules.md`：bootstrap 签 2026-07-16（55 行）· `llm` 行在模块表（32 行）· 2026-09-21 当日三行签录 = memory_facts_p1（85）/ memory_facts_p0（86）/ tech_graph_recent_sync（87）——task 闸表修订后表述与真值逐条一致 ✓ |
| 10 | R1 非阻塞备注采纳情况 | ✅ | 备注 1（闸表三行签录补全）已采纳 · 备注 2（`get_fallback_chain` 锚点改指 `model_catalog.py:101-105`，亲核实址 101-105 返回 `[]` ✓）已采纳 · 备注 3（SPEC §8 编排差异）知悉不改，合理 · 备注 4（20 invoke 快照）已由 10-task 代录 `invoke_20260921_20_task_audit_llm_layer_hardening.md`（原义务属 20 棒，修订记录已声明，本帽知悉） |

**结论：修订未引入新漂移。**

---

## 四、非阻塞备注（轻微 · 不代改 · 30 执行时知悉即可）

1. **N1 · 行号 ±1 偏差**：清单 #2 `test_retryable_errors` 实址 266（265 为 parametrize 装饰行）；清单 #7 chat_ws fixture 实址 45-53（清单写 46）。行级偏差，不影响处置正确性，30 按测试名定位即可。
2. **N2 · 清单 #1 覆盖可更全**：`test_missing_api_key` 在 bailian 侧有同名测（`test_llm_providers.py:453`）未单列——同语义同处置（回归），30 执行回归时自然覆盖，不阻塞。
3. **N3 · chat_ws 另有 SlowProvider（32 行）** 继承 BaseProviderImpl（取消语义测），属清单 #7「成功路径不触发重试/熔断」隐含覆盖范围，不阻塞。

---

## 五、人工闸状态声明

- `HG-AUDIT-R1` = **pending**（blocks 30）——本轮内容零阻塞，进入签闸流程；本帽不代签，00 依维护者授权签 task 表。
- `HG-GRAPH-MODULES` = approved（模块表已建置，真值已亲核）；本 task D5 的 `llm` 行备注新签义务留在验收标准，随 30 落盘（00 代录）。

---

## 维护者签闸（20 后 · 30 前）

- [ ] 已读 R1 审查结论（退回 B1）与 R2 审查结论（B1 闭合 · PASS-with-notes）
- [ ] 在 task 人工闸表将 HG-AUDIT-R1 改为 approved（维护者授权 00 代录 · 日期）
- [ ] commit task 文档或确认已签
- [ ] 再下发 Harness 30 Prompt

30 Agent 将以 task 表为准；pending 时必须拒开工（见 TEMPLATE_30_gate_stop.md）。

---

## 修订

| 日期 | 说明 |
|------|------|
| 2026-09-21 | R2（终轮）：B1 双核验闭合（12 条清单锚点全量亲扫属实 · 闸前置断言可测）；范围/非范围/failure_paths/思考轮全量重核零漂移；HG-GRAPH-MODULES 与真值一致；3 条 ±1 行级非阻塞备注 → **签收 / 关闭**，交维护者签闸 |
