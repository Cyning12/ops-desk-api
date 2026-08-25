# Task：dsh-coding-kit 1.5.1 graph 迁移探针（预留 SPEC 验证 + FEEDBACK）

> **状态**：completed（闸已签 · 00 代签授权；2026-08-24 随 PR #47 关账归档）  
> **类型**：基础设施 / 图谱工具链 · **验证+对比型（默认不切命令面）**  
> **执行 SPEC**：`docs/spec/SPEC-harness-to-dsh-kit-graph-migrate_v0.md`（预留 · DEF-023）  
> **前置**：`task_dsh_coding_kit_upgrade_1_5_1`（kit 已入库 1.5.1）  
> **分支**：`task/dsh-coding-kit-1-5-1`（与升级同分支累积）  
> **执行模式**：00 编排/验收；30 子 agent 执行

---

## Harness 元信息

| 字段 | 值 |
|---|---|
| **task_slug** | `dsh-kit-graph-migrate-probe` |
| **git_branch** | `task/dsh-coding-kit-1-5-1` |
| **implement_repo** | `ops-desk-api` |
| **test_strategy** | `required` |
| **test_strategy_note** | SPEC §4 验证矩阵 V1–V5 全跑（V3 IDE 预览为人工项）；graph-compile.sh 现状不破坏 |
| **code_quality_bar** | `not_applicable` |
| **graph_change_layer** | `none`（除非切命令面——须维护者另签） |
| **wiki_delta** | `n/a` |
| **review_hat** | `20` |
| **required_invoke_hats** | `10,30` |

### 人工闸

| human_gate_id | status | blocks_hats | 说明 |
|---|---|---|---|
| HG-TASK-DRAFT | approved | 22-R1 | 2026-08-24 00 代签（维护者指令「执行预留 task，对比新版与本地，需要则落 FEEDBACK」） |
| HG-AUDIT-R1 | approved | 30 | 2026-08-24 00 代签（验证型不改默认命令面，风险面小） |

---

## 范围（按 SPEC §2 前置 + §4 矩阵）

1. **前置条件核对**：kit 1.5.1 是否含 DEF-023 修复（changelog / emit 源码对照 `generateMermaid`）。
2. **SPEC §3 备份纪律**：迁移日备份三脚本入 `scripts/legacy/`（即使不切命令面，备份入库供对照）。
3. **§4 矩阵试编译**（临时目录或 env 开关，**不动** `graph-compile.sh` 默认面）：
   - V1：`npx dsh-coding-kit@1.5.1 graph yaml compile --all`（按子目录）exit 0
   - V2：无 normalize 的 kit 产物跑 `graph_mermaid_normalize.py --check` / grep 坏模式
   - V3：IDE 预览（人工项，记录产物差异供维护者勾）
   - V4：`graph yaml check` + graph.json 一致
   - V5：与本仓 normalize 后产物边集合对照（边数一致；id 大小写差异记报告）
4. **判定与产出**（SPEC §4 判定表）：
   - kit 仍差 → **保留 normalize**，落盘 FEEDBACK（`docs/harness/evidence/FEEDBACK_dsh_kit_1_5_1_mermaid_from_ops_desk_api_20260824.md`），内容含 §5 反哺材料（emit 契约规则集 + chat 图 fixture + 差异清单）
   - 全过 → 报告呈维护者签收后才可切命令面（另 task）

## 非范围

- 切换 graph-compile.sh / CI 默认命令面（须维护者签「切命令面」后另 task）
- 改 kit 源码
- 业务代码与图谱语义

## 验收标准

- [x] SPEC §4 矩阵 V1/V2/V4/V5 有实测记录（V3 人工项标注）（实测记录见 FEEDBACK §3：V1 PASS · V2 PASS · V4 PASS 双模式 · V5 PASS 边集合；V3 待维护者勾）
- [x] DEF-023 在 1.5.1 的修复状态有明确结论（含证据：changelog/源码行）（4 条规则 3 修 1 未修；lib/cli-graph-yaml.js L326-405 行号证据见 FEEDBACK §2）
- [x] 迁移日三脚本备份入库 `scripts/legacy/`（`*.20260824.pre-dsh-kit-migrate.bak` ×3 已落盘 untracked，待 00 统一 commit）
- [x] 需要 kit 更新时：FEEDBACK 文档落盘（含反哺规则集与 fixture 对照）（`docs/harness/evidence/FEEDBACK_dsh_kit_1_5_1_mermaid_from_ops_desk_api_20260824.md`：§5 规则集 R1-R6 · §4 chat fixture 对照 · §6 差异 D1-D3）
- [x] `./scripts/graph-compile.sh` 现状（harness + normalize）仍 exit 0（收尾实跑 exit 0，时间戳 diff 已还原）

---

## CLOSE

| 项 | 内容 |
|---|---|
| 日期 | 2026-08-24 |
| 定稿 | 迁移探针：不切命令面 + FEEDBACK |
| 归档 | `docs/tasks/done/task_dsh_kit_graph_migrate_probe.md` |
| PR | [#47](https://github.com/Cyning12/ops-desk-api/pull/47) MERGED |

---

## 修订

| 日期 | 说明 |
|---|---|
| 2026-08-24 | 初版（00 起草 + 代签闸 · 维护者授权）：执行预留迁移 SPEC 的验证矩阵；判定后按需落 FEEDBACK |
| 2026-08-24 | 30 执行回填：V1-V5 实测完成；判定「kit 仍差（class 按 kind 未修 + export 丢 label/graph_id 命名空间差异）」→ 不切命令面、保留 normalize；FEEDBACK 落盘；legacy 备份 ×3 落盘待 00 入库 |
| 2026-08-25 | 归档（task_task_closeout_hygiene）：CLOSE 节补录 · 状态→completed · git mv 至 docs/tasks/done/（合并日 2026-08-24 · PR #47） |
