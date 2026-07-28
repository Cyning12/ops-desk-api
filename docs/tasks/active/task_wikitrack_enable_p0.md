# Task：WikiTrack P0 启用（入口 + Obsidian + web 复用 RUNBOOK）

> **状态**：in_progress  
> **类型**：基础设施 / 文档（WikiTrack 启用 · 无双份）  
> **关联**：`@cyning/harness@2.18.2` · [`RUNBOOK_wikitrack_enable_obsidian_v1_zh.md`](../harness/RUNBOOK_wikitrack_enable_obsidian_v1_zh.md)  
> **上游**：维护者 00 统筹 · 先升 2.18.2 再落文档

---

## Harness 元信息

| 字段 | 值 |
|---|---|
| **task_slug** | `wikitrack-enable-p0` |
| **git_branch** | `task/harness-upgrade-2-18-migrate` |
| **graph_change_layer** | `none` |
| **graph_delta** | `none` |
| **graph_delta_note** | 不改业务图谱；仅 coding_wiki 入口指针 |
| **wiki_delta** | `docs/coding_wiki` |
| **wiki_delta_note** | 启用 WikiTrack 入口（README/stable/context/volatile）；正文真值仍在原路径 |
| **review_hat** | `20` |
| **thinking_profile** | `shortest` |
| **invoke_retention_profile** | `minimal` |
| **required_invoke_hats** | `00,30` |
| **experience_capture** | `recommended` |
| **test_strategy** | `recommended` |
| **test_strategy_note** | `wiki export --json` 有边；`verify --task`；`check` 2.18.2；无业务 pytest 义务（有则报告） |
| **code_quality_bar** | `not_applicable` |
| **orchestration** | 00 统筹；依赖同分支已升 2.18.2；产出 RUNBOOK 交 web |

### 人工闸

| human_gate_id | status | blocks_hats | 说明 |
|---|---|---|---|
| **HG-GRAPH-MODULES** | approved | **30** | 00 代签：不改模块边界 |
| HG-TASK-DRAFT | approved | 22-R1 | 维护者：落地 WikiTrack + 复用方案交 web |
| **HG-AUDIT-R1** | approved | **30** | 00 代签：仅入口/RUNBOOK；无业务 API |

---

## 背景与目标

空壳 `coding_wiki` 不足以支撑 Obsidian / `wiki_delta=path`。在 **2.18.2** 上启用入口：**单份真值**、相对链 + `[[wikilink]]`，并产出 web 可勾选 RUNBOOK。

**完成态**：

- [x] manifest ≥ 2.18.2
- [x] `docs/coding_wiki` 四文件为真实入口（互链 + 真值相对链）
- [x] `wiki export --json` nodes≥4 且 edges>0
- [x] RUNBOOK 落盘可交 web
- [x] verify / check；invoke 回填

**不做**：复制 standards/图谱正文；Obsidian 插件；web 仓内直接改码（只交方案）

---

## 失败路径

| 触发 | 行为 | 可重试 |
|---|---|---|
| export 空边 | 按 2.18.2 模板补 `[[wikilink]]` | 是 |
| upgrade 冲 overlay | 恢复 AGENTS/FRAGMENT | 是 |
| 误双份正文 | 删副本改指针 | 是 |

---

## 验收标准

- [x] coding_wiki 可读；Obsidian 开 `docs/coding_wiki/` 可导航（勿开上级 `docs/`）
- [x] export 有边；verify PASS
- [x] RUNBOOK 含 web 勾选清单与 api/web 差异表

---

### 自检结论（执行者）

| 项 | 内容 |
|---|---|
| **日期** | 2026-07-28 |
| **manifest** | `2.18.2` |
| **wiki export** | nodes=4 · edges=11 · warnings=0 · exit 0 |
| **verify** | PASS · exit 0 |
| **RUNBOOK** | `docs/harness/RUNBOOK_wikitrack_enable_obsidian_v1_zh.md` |
