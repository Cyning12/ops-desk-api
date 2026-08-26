# done/ · 已完成任务导航（Hub）

> **用途**：日常浏览 **只打开本文件**；`_views/done.md` 为薄指针。  
> **真值**：各 task 文件头部 `状态` + 本目录（或域子目录）物理位置。  
> **落盘约定**：业务仓 `docs/tasks/done/` · 工作区 Harness `docs/harness/tasks/done/`（路径替换下方 `{tasks_root}`）。

---

## 域目录（domain）

| 域 slug | 目录 | 典型前缀 / 规则 |
|---------|------|-----------------|
| `harness` | `done/harness/` | `task_harness_*`（非产品里程碑） |
| `cyning-harness` | `done/cyning-harness/` | `task_harness_cyning_harness_*` · `task_harness_m2_cyning_*` |
| `engineering` | `done/engineering/` | `task_engineering_*` |
| `governance` | `done/governance/` | `task_governance_*` · `task_gov_*` |
| `chatbi` | `done/chatbi/` | `task_chatbi_*` |
| `standards` | `done/standards/` | `task_standards_*` |
| `epics` | `done/epics/` | Epic / MANIFEST 母单 · CLOSE 卡 |

**推断**：关账时按文件名前缀落入域目录；歧义时 task 元信息填 **`domain`** 字段。

---

## harness

| 关账日 | task | freeze_id / 摘要 |
|--------|------|------------------|
| 2026-08-24 | [`task_dsh_coding_kit_upgrade_1_5_1.md`](./task_dsh_coding_kit_upgrade_1_5_1.md) | kit 1.5.1 过程轨升级 · PR #47 |
| 2026-08-24 | [`task_dsh_kit_graph_migrate_probe.md`](./task_dsh_kit_graph_migrate_probe.md) | 迁移探针：不切命令面 + FEEDBACK · PR #47 |
| 2026-08-25 | [`task_dsh_coding_kit_upgrade_1_5_2.md`](./task_dsh_coding_kit_upgrade_1_5_2.md) | kit 1.5.2（K1/K4 被 DEF-028/029 修复） · PR #48 |
| 2026-08-25 | [`task_dsh_coding_kit_upgrade_1_6_1.md`](./task_dsh_coding_kit_upgrade_1_6_1.md) | kit 1.6.1（反哺项全关闭） · PR #50 |
| 2026-08-25 | [`task_dsh_kit_graph_command_switch.md`](./task_dsh_kit_graph_command_switch.md) | 命令面正式切换 · PR #51 |

---

## cyning-harness（产品里程碑）

| 关账日 | task | tag / 摘要 |
|--------|------|------------|
| YYYY-MM-DD | [`cyning-harness/task_<slug>_v1.md`](./cyning-harness/task_<slug>_v1.md) | … |

---

## engineering

| 关账日 | task | 摘要 |
|--------|------|------|
| 2026-08-22 | [`task_lg_rag_phase1.md`](./task_lg_rag_phase1.md) | PLAN Phase 1（basic 图/checkpointer/Langfuse） · PR #45 |
| 2026-08-22 | [`task_lg_rag_phase2.md`](./task_lg_rag_phase2.md) | Phase 2 Router 三路（50 PASS 8/8） · PR #45 |
| 2026-08-22 | [`task_lg_rag_phase3.md`](./task_lg_rag_phase3.md) | Phase 3 自纠错回环（验收裁定通过） · PR #45 |
| 2026-08-22 | [`task_lg_rag_phase4.md`](./task_lg_rag_phase4.md) | Phase 4 Multi-Agent Supervisor（50 PASS） · PR #45 |
| 2026-08-26 | [`task_structured_output_gateway_p0.md`](./task_structured_output_gateway_p0.md) | Structured Output Gateway P0（parse_only） · PR #58 |
| 2026-08-26 | [`task_structured_output_gateway_p1.md`](./task_structured_output_gateway_p1.md) | Structured Output Gateway P1（complete_structured） · PR #58 |
| 2026-08-26 | [`task_structured_output_gateway_p2.md`](./task_structured_output_gateway_p2.md) | Structured Output Gateway P2（lg_rag 接入） · PR #58 |
| 2026-08-26 | [`task_structured_output_gateway_p3.md`](./task_structured_output_gateway_p3.md) | Structured Output Gateway P3（ensure/validate） · PR #58 |
| 2026-08-24 | [`task_inform_graph_backfill_w1_g0_chat.md`](./task_inform_graph_backfill_w1_g0_chat.md) | 图谱 W1（G-L0 + chat 追平） · PR #46 |
| 2026-08-24 | [`task_inform_graph_backfill_w2_bypass_flows.md`](./task_inform_graph_backfill_w2_bypass_flows.md) | 图谱 W2（旁路 flows，graphs 4→6） · PR #47 |
| 2026-08-25 | [`task_inform_graph_backfill_w3_chat_g2.md`](./task_inform_graph_backfill_w3_chat_g2.md) | W3 chat G-L2 indexes · PR #49 |
| 2026-08-25 | [`task_inform_graph_backfill_w4_rag_flow.md`](./task_inform_graph_backfill_w4_rag_flow.md) | W4 10_flow_rag（graphs 6→7） · PR #49 |
| 2026-08-25 | [`task_inform_graph_backfill_w5_coverage.md`](./task_inform_graph_backfill_w5_coverage.md) | W5 anchors + coverage warn · PR #49 |
| 2026-08-25 | [`task_inform_graph_backfill_w6_modules_trim.md`](./task_inform_graph_backfill_w6_modules_trim.md) | W6 模块表瘦身 · PR #49 |

---

## epics（母单 · MANIFEST）

| 关账日 | Epic / CLOSE | 子 task 索引 |
|--------|--------------|--------------|
| YYYY-MM-DD | [`epics/epic_<slug>.md`](./epics/epic_<slug>.md) | 见母单 §编排主表 |

---

## 关账维护（checklist）

1. `git mv {tasks_root}/active/<file>.md {tasks_root}/done/<domain>/`  
2. 头部 `> **状态**：done（YYYY-MM-DD 验收通过）`  
3. **本 Hub** 对应域表 **追加一行**（日期 · 链接 · freeze_id 一行摘要）  
4. **禁止**向 `_views/done.md` 追加长列表（保持 ≤15 行薄指针）  
5. 可选：同步 `_views/done_by_domain.md` 分组表  

---

## 修订记录

| 日期 | 摘要 |
|------|------|
| YYYY-MM-DD | 初版 Hub（cyning-harness 模板嵌入） |
| 2026-08-25 | 补录 15 件归档（task_task_closeout_hygiene）：harness 域 5 件 + engineering 域 10 件；本仓 done/ 为平铺布局，链接用 ./task_*.md |

## 给维护者

`done`、`domain`、`Hub`、`_views`、`freeze_id`、`Epic`
