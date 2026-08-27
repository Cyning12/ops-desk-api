# Task：dsh-coding-kit 升级 1.8.0（K1–K7 核对 + prompts 手同步）

> **状态**：completed（2026-08-27 · PR #76 MERGED · 本卡为事后 Hub 关账归档）  
> **类型**：基础设施 / harness 过程轨升级（minor）  
> **前置**：manifest `1.7.1`；kit **1.8.0** 已 npm 发版（含 agent-host FEEDBACK K1–K7）  
> **分支**：`task/dsh-coding-kit-1-8-0`（实现）· 本关账文档 `fix/kit-1-8-0-closeout-docs`  
> **执行模式**：Open Folder = **ops-desk-api**；维护者授权签收过程文档

---

## Harness 元信息

| 字段 | 值 |
|------|-----|
| **task_slug** | `dsh-coding-kit-upgrade-1-8-0` |
| **git_branch** | `task/dsh-coding-kit-1-8-0` |
| **implement_repo** | `ops-desk-api` |
| **test_strategy** | `required` |
| **test_strategy_note** | `npx dsh-coding-kit@1.8.0 check`；K1/K2/K3 探针；CI lint-wiki-delta@1.8.0 |
| **code_quality_bar** | `not_applicable` |
| **graph_change_layer** | `none` |
| **graph_delta** | `none` |
| **graph_delta_note** | 过程轨升级；不改业务图谱 |
| **wiki_delta** | `none` |
| **wiki_delta_note** | 本波不晋升 coding_wiki；FEEDBACK 走 evidence + doc-health/feedback |
| **experience_capture** | `recommended` |
| **kpi_aggregator** | `CLOSE` |
| **invoke_retention_profile** | `minimal` |
| **required_invoke_hats** | `30` |
| **close_pr_policy** | `required` |
| **related_pr** | `#76`（升级）· 关账索引本 PR |

### 人工闸

| human_gate_id | status | blocks_hats | 说明 |
|---------------|--------|-------------|------|
| HG-TASK-DRAFT | approved | 22-R1, 30 | 2026-08-27 维护者签收「更新到 1.8.0 + 检查 FEEDBACK」 |
| HG-AUDIT-R1 | approved | 30 | 过程轨 · 不改 app/ · 与升级同窗签收 |

---

## 验收（已完成）

- [x] manifest `1.8.0` · `from_version=1.7.1`
- [x] CI `lint-wiki-delta.yml` 钉 `@1.8.0`
- [x] prompts / TASK_TEMPLATE 自包手同步（upgrade 不 sync）
- [x] agent-host K1–K7 探针全部已修
- [x] FEEDBACK：`docs/harness/evidence/FEEDBACK_dsh_coding_kit_1_8_0_*.md`
- [x] 复发记录：`docs/spec/doc-health/feedback/2026-08-27_1.8.0_upgrade-no-prompt-sync.md`
- [x] PR #76 MERGED

### 自检结论（执行者）

| 命令 | 退出码 |
|------|--------|
| `npx dsh-coding-kit@1.8.0 check --target .` | 0（已是最新） |
| K1 wrong_section 探针 | 报 `wiki_delta_wrong_section` |
| K2 `task lint` E8 | FAIL 缺 wiki_delta |
| K3 `verify --with-wiki-lint` | BLOCKED 兄弟 task + 复跑命令 |

---

## CLOSE

| 项 | 值 |
|----|-----|
| 升级 PR | [#76](https://github.com/Cyning12/ops-desk-api/pull/76) MERGED |
| 核对真值 | [`FEEDBACK_dsh_coding_kit_1_8_0_from_ops_desk_api_20260827.md`](../../harness/evidence/FEEDBACK_dsh_coding_kit_1_8_0_from_ops_desk_api_20260827.md) |
| Hub | 本文件 + `docs/tasks/done/README.md` 行 |

### KPI

- kit 钉 **1.8.0**；K1–K7 产品面关闭；本仓 L1–L4 执行纪律仍 optional。
