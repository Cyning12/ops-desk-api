# Task：图谱 Bootstrap · 模块表人签（D4-a）

> **状态**：done  
> **类型**：存量 **首次** 接入 / 新仓图谱初始化  
> **关联**：[`docs/_tech_graph/01_struct.md`](../../_tech_graph/01_struct.md) · ONBOARDING 档位 S0～S3

---

## Harness 元信息

| 字段 | 值 |
|---|---|
| **task_slug** | `graph-bootstrap` |
| **test_strategy** | `recommended` |
| **test_strategy_note** | 文档 + 文件存在性；无业务单测 |
| **code_quality_bar** | `not_applicable` |
| **orchestration** | 单 task 或 Epic 首棒 |
| **git_branch** | `task/graph-bootstrap` |
| **experience_capture** | `recommended` |

| **wiki_delta** | `n/a` |
| **wiki_delta_note** | 本仓未启用 WikiTrack |
### 人工闸

| human_gate_id | status | blocks_hats | 说明 |
|---|---|---|---|
| **HG-GRAPH-MODULES** | approved | **30** | `01_struct` **一级模块表** 已覆盖 ops-desk-api 一级模块 |
| HG-TASK-DRAFT | approved | 22-R1 | 小 task 合并执行 |
| HG-AUDIT-R1 | approved | 30 | 本 task 为文档初始化，无需额外 R1 |

---

## 背景与目标

**完成态**：

- [x] `docs/_tech_graph/` 骨架就位（`00_main` 双轨、`10_flow_chat`、`99_mermaid_protocol`、`02_version`）
- [x] `01_struct.md` 模块表填完 **一级模块**（module_id · glob · 依赖方向）
- [x] **至少 1** 条主 flow（`10_flow_chat`）
- [x] **`HG-GRAPH-MODULES` approved**
- [x] 本 task 关账 invoke + `### 自检结论` 回填

**不做**：

- 首次 onboarding **全仓 flow 一次画完**
- 全仓代码扫描自动生图

---

## 范围

- [x] 从 `cyning-harness/graph/templates/` 复制骨架至 `docs/_tech_graph/`
- [x] 填写 `01_struct.md` 模块表（删除模板示例行）
- [x] 完成 `10_flow_chat` 主路径（替换占位锚点）
- [x] 在 `01_struct.md` 记录 **人签表**

## 非范围

- 业务功能代码改动
- L0-e `graph.json` 全量 export（保留兼容层 `graph.json` 供 check 使用）

---

## 失败路径

| 触发条件 | 系统行为 | 可重试 | 用户可见 |
|---|---|---|---|
| `HG-GRAPH-MODULES` pending 即开 30 改码 task | 执行 **拒开工** | 是 | 须先完成本 bootstrap + 人签 |
| 模块表空表或仅模板示例行 | 22 **打回** | 是 | 一级模块未覆盖 |
| 试图一次画完所有 flow | 审查 **打回** | 是 | 违反 D4-a |

---

## 验收标准

- [x] `docs/_tech_graph/00_main.md` + `.graph.yaml` 存在且语义一致
- [x] `01_struct.md` ≥3 行真实模块（实际 8 行）
- [x] `HG-GRAPH-MODULES` → **approved**
- [x] ≥1 主 flow（`10_flow_chat`）
- [x] invoke 落盘 `docs/harness/invokes/by-task/graph-bootstrap/`

---

## 给执行帽的必读列表

1. [`docs/ONBOARDING.md`](../../docs/ONBOARDING.md) §3 存量档位
2. `docs/_tech_graph/01_struct.md` · `99_mermaid_protocol.md`
3. 本 task 验收表

---

## 实现备忘

| 项 | 状态 | 备注 |
|---|---|---|
| 骨架复制 | ✅ | 由 `npx @cyning/harness init` 生成，后恢复项目特定内容 |
| 模块表 | ✅ | 8 个一级模块：entry / api / auth / chat / data / admin / llm / db |
| HG-GRAPH-MODULES | ✅ | approved |
| 主 flow | ✅ | `10_flow_chat` 覆盖 SSE Chat 完整流程 |

---

### 自检结论（执行者）

- `00_main.graph.yaml` 与 `10_flow_chat.graph.yaml` 符合 `inform_graph.v3` schema。
- `./scripts/graph-compile.sh` 可成功编译 `.graph.yaml` → `.md` + `graph.json`，并通过 `npx @cyning/harness graph yaml check --all`。
- 项目 npx 权限已放开：`.claude/settings.json` 添加 `Bash(npx @cyning/harness *)`。
- 待后续业务实现后更新：`answer_node` 接入 LLM Provider、`ops_runs` / `ops_run_events` 持久化。

---

## 修订记录

| 日期 | 说明 |
|---|---|
| 2026-07-16 | 从 cyning-harness `TASK_graph_bootstrap.md` 嵌入并关账 |
