# SPEC：Inform 图谱补齐（ops-desk-api · v1）

> **状态**：`accepted`  
> **track**：`docs/_tech_graph` · 过程资产  
> **类型**：规划 / 分模块补齐真值（**不含**实现 diff）  
> **Open Folder**：`ops-desk-api/`

---

## 一句话

Inform 图谱在 Phase α 后「模块表齐、flow/G-L0/G-L2 缺」的缺口，已拆成 **按层 + 按模块** 可执行 spec；后续每棒认领一包内一个 wave。

---

## 正文真值（分模块）

**入口读序**：[`inform-graph-backfill/README.md`](./inform-graph-backfill/README.md)

| 分区 | 路径 |
|------|------|
| 政策与 wave | `inform-graph-backfill/00_policy_and_boundaries.md` · `01_execution_waves.md` |
| G-L0 / G-L1 / G-L2 | `inform-graph-backfill/layers/` |
| 一级模块 | `inform-graph-backfill/modules/*.md` |
| CI warn | `inform-graph-backfill/ci/coverage_check.md` |
| Skill/task | `inform-graph-backfill/process/skill_and_task_policy.md` |

---

## Harness 元信息（建议）

| 字段 | 值 |
|------|-----|
| **spec_slug** | `inform-graph-backfill` |
| **graph_change_layer** | `mixed`（按 wave 裁剪） |
| **test_strategy** | `recommended` |
| **test_strategy_note** | 每 wave：`./scripts/graph-compile.sh`；W5 加 coverage 脚本 |

### 人工闸（SPEC 阶段）

| human_gate_id | status | 说明 |
|---|---|---|
| HG-SPEC-SIGNOFF | **approved** | 维护者 2026-08-23 签收 v1；W1 可开 30 |

---

## 建议首棒

**W1**：`00_main` 挂 lc/lg 路由 + `10_flow_chat` 追平 RAG 链 — 见 `01_execution_waves.md` §W1。

---

## 修订记录

| 日期 | 说明 |
|------|------|
| 2026-08-23 | v1 初稿落盘 |
| 2026-08-23 | HG-SPEC-SIGNOFF approved；启动 W1 |
