# Task：graph 命令面切换（@cyning/harness → dsh-coding-kit 1.6.1）

> **状态**：active（闸已签 · 含维护者「切命令面」签收）  
> **类型**：基础设施 / 图谱工具链正式迁移  
> **执行 SPEC**：`docs/spec/SPEC-harness-to-dsh-kit-graph-migrate_v0.md`（§2 前置 / §3 备份 / §4 矩阵 / §6 步骤）  
> **前置**：kit 1.6.1 已入 master；DEF-023 + DEF-031/032/033 全修复（D1–D3/R6 关闭）；探针矩阵 V1/V2/V4/V5 历史 PASS  
> **分支**：`task/dsh-kit-graph-command-switch`  
> **执行模式**：00 编排/验收；30 子 agent 执行

---

## Harness 元信息

| 字段 | 值 |
|---|---|
| **task_slug** | `dsh-kit-graph-command-switch` |
| **git_branch** | `task/dsh-kit-graph-command-switch` |
| **implement_repo** | `ops-desk-api` |
| **test_strategy** | `required` |
| **test_strategy_note** | SPEC §4 矩阵 V1–V5 全复跑（kit 1.6.1 无 normalize）；切换后 `./scripts/graph-compile.sh` exit 0 且 CI tech-graph 绿 |
| **code_quality_bar** | `not_applicable` |
| **graph_change_layer** | `none`（命令面切换，图谱语义不变；产物差异须等价回归证明） |
| **wiki_delta** | `n/a` |
| **review_hat** | `20` |
| **required_invoke_hats** | `10,30` |

### 人工闸

| human_gate_id | status | blocks_hats | 说明 |
|---|---|---|---|
| HG-TASK-DRAFT | approved | 22-R1 | 2026-08-25 00 代签（维护者本窗授权） |
| HG-AUDIT-R1 | approved | 30 | 2026-08-25 00 代签（SPEC 前置已满足；回滚路径=§3 备份） |
| HG-CMD-SWITCH | approved | 30 | **2026-08-25 维护者会话直签「切命令面」**（SPEC §2 第 4 条人工闸，对应 1.6.1 全修复事实） |

---

## 范围（SPEC §6 步骤）

1. **§3 迁移日备份**：三脚本 → `scripts/legacy/*.20260825.pre-cmd-switch.bak`（入库）。
2. **§4 矩阵复跑**（kit 1.6.1，无 normalize）：V1 compile exit 0 / V2 emit 无坏模式 / V3 IDE 预览（人工项留材料）/ V4 check+json 一致 / V5 边集合对照。任一不过 → 停手恢复备份写报告。
3. **切换 `graph-compile.sh`**：compile/check 两行 `npx @cyning/harness` → `npx dsh-coding-kit`（可留 `GRAPH_CLI` env 回退口，SPEC §6.2）；**graph.json 生成路径评估**：kit `graph yaml export`（D2/D3 已修）能否替代 `graph_yaml_to_json.py`——做行为等价回归（graph_id 声明值/边 label 保留/下游消费兼容），等价才换，不等价保留本仓脚本并记录。
4. **normalize 处置**：矩阵全过 → 按 SPEC 判定退役或改 no-op 检查开关（推荐：切到 kit emit 后保留 `--check` 纯校验不改写，作为防回退护栏）；`99_mermaid_protocol.md` §0 命令面同步更新。
5. **CI 对齐**：`lint-wiki-delta.yml` 的 `@cyning/harness@2.22.0` 引用 → kit 对应命令（核实 kit 有 `task lint-wiki-delta` 后切换）；tech-graph.yml 走 graph-compile.sh 自动跟随。
6. **AGENTS.md / 相关文档**中仍写 `@cyning/harness` graph 命令处更新（IDE 产品块由 kit refresh 管，仓内其他引用手改）。

## 非范围

- 图谱语义/拓扑改动（产物 diff 只允许时间戳与 emit 风格等价差异，须逐文件解释）
- 业务代码
- normalize 规则再开发

## failure_paths

| 触发 | 行为 | 可重试 |
|---|---|---|
| 矩阵任一项不过 | 停手，恢复 §3 备份，写失败报告 | Y |
| CI tech-graph 切后红 | 回退 graph-compile.sh（GRAPH_CLI env 或 bak），排查 | Y |
| kit export 与本仓 json 不等价 | 保留 graph_yaml_to_json.py，仅切 compile/check 两行 | Y |

## 验收标准

- [ ] §4 矩阵 V1/V2/V4/V5 实测 PASS 记录（V3 材料备）
- [ ] graph-compile.sh 全量走 kit exit 0；`GRAPH_CLI` 回退口或备份可回滚
- [ ] graph.json 生成路径有明确等价性结论（换/留 + 证据）
- [ ] normalize 处置落地（退役/no-op 护栏）+ 99_mermaid_protocol §0 更新
- [ ] CI 全绿（含 lint-wiki-delta 切换后）；产物 diff 逐文件可解释
- [ ] pytest 无新增失败

---

## 修订

| 日期 | 说明 |
|---|---|
| 2026-08-25 | 初版（00 起草 + 代签闸 · 维护者会话直签「切命令面」）：SPEC §6 正式迁移 |
