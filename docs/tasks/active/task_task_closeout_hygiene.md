# Task：task 文档关账归档 + 遗留项清理（closeout hygiene）

> **状态**：active（闸已签 · 00 代签授权）  
> **类型**：过程卫生 / 文档归档 + 小修  
> **背景**：15 个已完成 task 滞留 `docs/tasks/active/`（均已合并 master）；遗留 K9 mdc 旧字面、wiki export 旧引用  
> **分支**：`task/task-closeout-hygiene`  
> **执行模式**：00 编排/验收；30 子 agent 执行

---

## Harness 元信息

| 字段 | 值 |
|---|---|
| **task_slug** | `task-closeout-hygiene` |
| **git_branch** | `task/task-closeout-hygiene` |
| **implement_repo** | `ops-desk-api` |
| **test_strategy** | `required` |
| **test_strategy_note** | `./scripts/graph-compile.sh` exit 0；归档后 active 仅剩 3 个未完成 task；views 链接有效 |
| **code_quality_bar** | `not_applicable` |
| **graph_change_layer** | `none` |
| **wiki_delta** | `n/a`（wiki export 引用更新属文档字面，不动 wiki 语义） |
| **review_hat** | `20` |
| **required_invoke_hats** | `10,30` |

### 人工闸

| human_gate_id | status | blocks_hats | 说明 |
|---|---|---|---|
| HG-TASK-DRAFT | approved | 22-R1 | 2026-08-25 00 代签（维护者指令「处理遗留项，完成的 task 迁移」+ 本窗授权） |
| HG-AUDIT-R1 | approved | 30 | 2026-08-25 00 代签（纯文档归档 + 单行字面修正） |

---

## 范围

1. **归档 15 个已完成 task**（补 CLOSE 节 + 状态行 → completed，`git mv` 到 `docs/tasks/done/`）：
   | task | 对应 PR | 定稿摘要 |
   |---|---|---|
   | task_lg_rag_phase1 | #45 | PLAN Phase 1（basic 图/checkpointer/Langfuse） |
   | task_lg_rag_phase2 | #45 | Phase 2 Router 三路（50 PASS 8/8） |
   | task_lg_rag_phase3 | #45 | Phase 3 自纠错回环（验收裁定通过） |
   | task_lg_rag_phase4 | #45 | Phase 4 Multi-Agent Supervisor（50 PASS） |
   | task_inform_graph_backfill_w1_g0_chat | #46 | 图谱 W1（G-L0 + chat 追平） |
   | task_dsh_coding_kit_upgrade_1_5_1 | #47 | kit 1.5.1 过程轨升级 |
   | task_dsh_kit_graph_migrate_probe | #47 | 迁移探针：不切命令面 + FEEDBACK |
   | task_inform_graph_backfill_w2_bypass_flows | #47 | 图谱 W2（旁路 flows，graphs 4→6） |
   | task_dsh_coding_kit_upgrade_1_5_2 | #48 | kit 1.5.2（K1/K4 被 DEF-028/029 修复） |
   | task_inform_graph_backfill_w3_chat_g2 | #49 | W3 chat G-L2 indexes |
   | task_inform_graph_backfill_w4_rag_flow | #49 | W4 10_flow_rag（graphs 6→7） |
   | task_inform_graph_backfill_w5_coverage | #49 | W5 anchors + coverage warn |
   | task_inform_graph_backfill_w6_modules_trim | #49 | W6 模块表瘦身 |
   | task_dsh_coding_kit_upgrade_1_6_1 | #50 | kit 1.6.1（反哺项全关闭） |
   | task_dsh_kit_graph_command_switch | #51 | 命令面正式切换 |
2. **views 同步**：`docs/tasks/done/README.md`（Hub）与 `_views/done_by_domain.md` 按既有体例补录。
3. **K9**：`.cursor/rules/05-harness-starter.mdc` L19 `npx @cyning/harness verify` → `npx dsh-coding-kit verify`。
4. **wiki export 引用评估**：`docs/coding_wiki/README.md`、`topics/wikilinks_export.md`、`docs/harness/RUNBOOK_wikitrack_enable_obsidian_v1_zh.md` 钉的 `@cyning/harness@2.19.0 wiki export`——核实 kit wiki 子命令参数面兼容后切换（不兼容则保留 + 记录理由）。

## 非范围

- `task_ops_sync_sender_migration` / `task_retrieval_longquery_analysis` / `task_rag_answer_mixed_evidence`（未完成/待审，留 active）
- 历史 done/ 文件与 invokes 中的 dated 字面（不伪造历史）
- 业务代码

## 验收标准

- [ ] active 仅剩 3 个未完成 task；15 个归档件均含 CLOSE 节（日期/定稿/PR/归档路径）
- [ ] done/README Hub 与 done_by_domain 同步；链接抽验有效
- [ ] K9 修复；wiki export 引用有「切换/保留+理由」明确结论
- [ ] `./scripts/graph-compile.sh` exit 0；`git diff app/` 为空

---

## 修订

| 日期 | 说明 |
|---|---|
| 2026-08-25 | 初版（00 起草 + 代签闸 · 维护者授权）：15 归档 + views 同步 + K9 + wiki export 引用评估 |
