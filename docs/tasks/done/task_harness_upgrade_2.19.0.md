# Task：Harness 升级至 2.19.0（api）· lint-wiki-delta

> **状态**：completed  
> **类型**：基础设施（过程轨 upgrade + 文档对齐）  
> **关联**：npm `@cyning/harness@2.19.0` · `task lint-wiki-delta` · 姊妹 `harness-upgrade-2-18-migrate` / `wikitrack-enable-p0`  
> **合入**：PR #22（同波）

---

## Harness 元信息

| 字段 | 值 |
|---|---|
| **task_slug** | `harness-upgrade-2.19.0` |
| **git_branch** | `task/harness-upgrade-2-18-migrate` |
| **graph_change_layer** | `none` |
| **graph_delta** | `none` |
| **graph_delta_note** | 仅过程轨 / 文档钉；不改业务图谱 |
| **wiki_delta** | `docs/harness/RUNBOOK_wikitrack_enable_obsidian_v1_zh.md` |
| **wiki_delta_note** | RUNBOOK 钉 2.19.0 + lint-wiki-delta；coding_wiki 读序版本指针 |
| **review_hat** | `20` |
| **thinking_profile** | `shortest` |
| **invoke_retention_profile** | `minimal` |
| **required_invoke_hats** | `30` |
| **experience_capture** | `recommended` |
| **test_strategy** | `recommended` |
| **test_strategy_note** | `upgrade --yes`；`check`；`task lint-wiki-delta --scope all` exit 0；`wiki export`；`verify --task` |
| **code_quality_bar** | `not_applicable` |
| **orchestration** | 延伸自 2.18.x 同波；与 migrate / wikitrack-p0 一并 CLOSE |

### 人工闸

| human_gate_id | status | blocks_hats | 说明 |
|---|---|---|---|
| **HG-GRAPH-MODULES** | approved | **30** | 00 代签：仅过程轨 |
| HG-TASK-DRAFT | approved | 22-R1 | 维护者：升 2.19.0 + 文档对齐 + 同波关账 |
| **HG-AUDIT-R1** | approved | **30** | 00 代签：无业务 API |

---

## 背景与目标

2.19.0 交付 **`task lint-wiki-delta`**（缺字段扫描 · exit 2）与 USER_GUIDE 扫描建议替换；本仓已在 2.18.x 补齐字段，本 task 钉版本并文档对齐。

**完成态**：

- [x] manifest → `2.19.0`
- [x] overlay 恢复
- [x] `lint-wiki-delta --scope all` → PASS · missing=0
- [x] RUNBOOK / coding_wiki 钉 2.19.0
- [x] check / export / verify
- [x] 与姊妹 task 一并 CLOSE

**不做**：削弱 close 硬闸；默认 `--allow-wiki-gap`；自动 `topics/` 迁目录（upgrade 不代做）

---

## 失败路径

| 触发 | 行为 | 可重试 |
|---|---|---|
| lint-wiki-delta missing>0 | 补字段后再关 | 是 |
| upgrade 冲 overlay | 恢复 | 是 |

---

## 验收标准

- [x] manifest 2.19.0 · check 已是最新
- [x] lint-wiki-delta PASS
- [x] RUNBOOK 含 lint-wiki-delta 与 vault=`coding_wiki/`

---

### 自检结论（执行者）

| 项 | 内容 |
|---|---|
| **日期** | 2026-07-28 |
| **manifest** | `2.19.0`（from 2.18.2） |
| **lint-wiki-delta** | scanned=23 · missing=0 · PASS |
| **check / export / verify** | 见 invoke |

### 经验节（执行者）

- upgrade 后必 diff AGENTS/FRAGMENT overlay。
- `task close` 的 `--target` 是**归档目标路径**，不是仓根；关账勿传 `--target .`。
- Obsidian vault 只开 `docs/coding_wiki/`，避免 docs/ 过程轨孤点。

### KPI

| 项 | 分 |
|---|---|
| Task_KPI% | 100 |

## CLOSE

| 项 | 内容 |
|---|---|
| **日期** | 2026-07-28 |
| **PR** | [#22](https://github.com/Cyning12/ops-desk-api/pull/22)（同波 · ~~待合入~~ **已 MERGED 2026-07-28** · merge commit `0cb5524`；修订注记 2026-10-30：原「待合入」为陈旧表述，按磁盘实态更正） |
| **manifest** | `2.19.0` |
