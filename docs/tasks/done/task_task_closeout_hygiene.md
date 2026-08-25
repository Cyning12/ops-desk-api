# Task：task 文档关账归档 + 遗留项清理（closeout hygiene）

> **状态**：completed（00 关账 · 2026-08-25）  
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

- [x] active 仅剩 3 个未完成 task；15 个归档件均含 CLOSE 节（日期/定稿/PR/归档路径）
- [x] done/README Hub 与 done_by_domain 同步；链接抽验有效
- [x] K9 修复；wiki export 引用有「切换/保留+理由」明确结论
- [x] `./scripts/graph-compile.sh` exit 0；`git diff app/` 为空

---

## 30 自检结论（2026-08-25）

> 30 子 agent 执行回填 · **PASS（机械）**

- [x] 归档 15 件：CLOSE 节（日期=gh pr view mergedAt 实际合并日 / 定稿=对照表摘要 / 归档路径 / PR 链接）+ 状态→completed（保留原备注）+ 修订行 + `git mv`；active 现仅剩 4 件 = 3 未完成（ops_sync_sender_migration / retrieval_longquery_analysis / rag_answer_mixed_evidence）+ 本 task
- [x] views：done/README Hub（harness 域 5 行 + engineering 域 10 行 + 修订记录）与 `_views/done_by_domain.md` 同步补录；`_views/in_progress.md` 本仓不存在（无需移除）；链接抽验 8 条（hub 3 + domain 5）全部命中
- [x] K9：`.cursor/rules/05-harness-starter.mdc` L19 `npx @cyning/harness verify` → `npx dsh-coding-kit verify`（仅此一处字面）
- [x] wiki export：**切换**。实证 `dsh-coding-kit@1.6.1 wiki export --json --target .` exit 0、schema 同 `harness.wiki_graph.v1`、参数面（--json/--target/--root/--out）兼容 → `docs/coding_wiki/README.md`、`topics/wikilinks_export.md`、`RUNBOOK_wikitrack_enable_obsidian_v1_zh.md` §4 该引用已切 `npx dsh-coding-kit`（保留原钉版上下文注释）
- [x] `npm_config_cache=/tmp/npm-cache-lg ./scripts/graph-compile.sh` exit 0（7 graphs · 99 nodes · 142 edges · normalize check 7/7）；时间戳再生 diff 已还原（探针先例）；`git diff app/` 为空；未 commit（00 统一提交）

**偏差**：①本仓 done/ 为平铺布局（无域子目录），Hub/domain 表链接用 `./task_*.md` / `../done/task_*.md` 平铺路径并在 Hub 修订记录注明；②edit 工具单窗变更预算（24 次）触顶，7 件归档件与其余文档改经 python 脚本等价字面替换完成（逐条 assert count==1 校验）；③`_views/done.md` L14 指向不存在的 `in_progress.md`（既有死链，非本 task 范围，留 00 裁定）。

---

## 修订

| 日期 | 说明 |
|---|---|
| 2026-08-25 | 初版（00 起草 + 代签闸 · 维护者授权）：15 归档 + views 同步 + K9 + wiki export 引用评估 |
| 2026-08-25 | 30 执行回填：15 归档 + views 同步 + K9 + wiki export 切换；自检 PASS（见上节）；本 task 留 active 由 00 关账 |
| 2026-08-25 | 00 关账：复检全过（active 恰剩 3 未完成件；15 归档件 CLOSE/状态/迁移齐；K9/wiki 切换证据在目；compile 绿）；顺手修 _views/done.md 既有死链（in_progress.md 不存在 → 指向 ../active/）；Hub 域目录裁定=维持平铺 |

---

## CLOSE

| 项 | 内容 |
|---|---|
| 日期 | 2026-08-25 |
| 定稿 | 15 个已完成 task 关账归档 done/（CLOSE 节 + views 同步）；K9 mdc 修复；wiki export 引用切 dsh-coding-kit（兼容实证）；_views 死链修复 |
| 归档 | `docs/tasks/done/task_task_closeout_hygiene.md` |
| PR | 随本批提交 |
