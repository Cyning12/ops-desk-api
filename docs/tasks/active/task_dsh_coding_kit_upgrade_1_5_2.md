# Task：dsh-coding-kit 升级 1.5.2（patch 升级 + FEEDBACK 项修复核对）

> **状态**：active（闸已签 · 00 代签授权）  
> **类型**：基础设施 / harness 过程轨升级（patch）  
> **前置**：`task_dsh_coding_kit_upgrade_1_5_1`（已入 master）；FEEDBACK 已反哺 D1–D3 / R6  
> **关联**：`docs/harness/evidence/FEEDBACK_dsh_kit_1_5_1_mermaid_from_ops_desk_api_20260824.md` §6（D1 export 丢 label / D2 graph_id 命名空间 / D3 check-export 不互认 / R6 class 按 kind）  
> **分支**：`task/dsh-coding-kit-1-5-2`  
> **执行模式**：00 编排/验收；30 子 agent 执行

---

## Harness 元信息

| 字段 | 值 |
|---|---|
| **task_slug** | `dsh-coding-kit-upgrade-1-5-2` |
| **git_branch** | `task/dsh-coding-kit-1-5-2` |
| **implement_repo** | `ops-desk-api` |
| **test_strategy** | `required` |
| **test_strategy_note** | 升级后：`npx dsh-coding-kit verify --target . --task <本task>` 跑通；`./scripts/graph-compile.sh` exit 0；pytest 无新增失败 |
| **code_quality_bar** | `not_applicable` |
| **graph_change_layer** | `none` |
| **wiki_delta** | `n/a` |
| **review_hat** | `20` |
| **required_invoke_hats** | `10,30` |

### 人工闸

| human_gate_id | status | blocks_hats | 说明 |
|---|---|---|---|
| HG-TASK-DRAFT | approved | 22-R1 | 2026-08-24 00 代签（维护者直接指令「更新 dsh_kit 到 1.5.2」+ 本窗授权） |
| HG-AUDIT-R1 | approved | 30 | 2026-08-24 00 代签（patch 升级，1.5.1 路径刚验证过） |

---

## 范围

1. `npm_config_cache=/tmp/npm-cache-lg npx --yes dsh-coding-kit@1.5.2` 按 1.5.1 已验证路径升级（check → refresh-ide-blocks → upgrade → 幂等复检）；local 块零手恢复复检。
2. **FEEDBACK 项修复核对**：实读 1.5.2 包源码，逐项判定 D1 / D2 / D3 / R6（class 按 kind）修复状态（已修/未修/部分 + 证据行号）；若有修复，**不切命令面**（切换仍须维护者另签），只更新结论。
3. 升级有出入 → FEEDBACK 落盘 `docs/harness/evidence/FEEDBACK_dsh_coding_kit_1_5_2_from_ops_desk_api_20260824.md`（无出入则免，修订行注明）。

## 非范围

- graph-compile.sh / CI 命令面切换
- 业务代码、图谱语义

## 验收标准

- [x] manifest 钉 1.5.2；local 块零字节变化（diff 证据：`git diff AGENTS.md CLAUDE.md` 输出为空 · FEEDBACK §6）
- [x] verify / graph-compile / pytest 三项跑通（基线一致）
- [x] D1/D2/D3/R6 修复状态结论表（含证据）记入 task 自检
- [x] 有出入时 FEEDBACK 落盘 → `docs/harness/evidence/FEEDBACK_dsh_coding_kit_1_5_2_from_ops_desk_api_20260824.md`

---

## 自检结论（30 执行 · 2026-08-25）

### 五项自检

| # | 项 | 结果 |
|---|----|------|
| 1 | manifest 钉 1.5.2 | **PASS**（version=1.5.2 · from_version=1.5.1 · preset/ide 保留） |
| 2 | local 块零字节变化 | **PASS**（`git diff AGENTS.md CLAUDE.md` 空；refresh rewrites=0/files_written=0 · 跳过 local 块×1） |
| 3 | `verify --task <本task>` | **PASS**（严格态 BLOCKED exit 2 = 缺 R<n>，20 序内预期；`--allow-no-review` 留痕豁免 PASS exit 0；10/30 invoke 已补齐，无需 --allow-invoke-gap） |
| 4 | `./scripts/graph-compile.sh` | **PASS exit 0**（harness 命令面未动；产物 diff 仅 generated_at/freeze_id 日期戳，已 `git checkout --` 还原） |
| 5 | `.venv/bin/pytest tests -q` | **PASS**（3 failed / 242 passed = 既有基线 chat_ws/chat_router 缺表，无新增） |

### D1/D2/D3/R6 修复核对（实读 1.5.2 包 `lib/cli-graph-yaml.js`；与 1.5.1 包 diff = **0 diff lines**）

| ID | 1.5.2 状态 | 证据行号（1.5.2 包） |
|----|-----------|---------------------|
| D1 export 丢边 label | **未修** | L196-215：mark=`~>`/`?>`/`::…`/`[…]` 仍强制 `baseLabel=''` |
| D2 export graph_id 路径命名空间 | **未修** | L268-279/283-296 仍用 `allGraphIds` 路径 id，不读 `data.graph_id`；L40-41 禁 `/` 依旧 |
| D3 check --all 与自产根 json 不互认 | **未修**（同源 D2） | L527-528 裸 id 过滤不变 |
| R6 class 按 yaml kind | **未修** | L395-397 硬编码 id 白名单（Q/E/U1/U2/RAG/T2S/RPC/FTS · DOC · AUTH/EV_TYPES），不读 `nodes[].kind` |
| DEF-023 已修三条 | **未回退** | formatAnchorComment L326-338 · 带标签边官方形态 L380-381（`--"` 全 lib 零命中）· 引号+entity code L356-358/L344-349 |

**1.5.2 实际增量**：DEF-028（check 跨产品线迁移语义，修 1.5.1 FEEDBACK K1 · lib/cli.js L210-214）+ DEF-029（refresh 无 marker 文件只读检出报告 plain_mentions，修 K4 · lib/cli-refresh-ide-blocks.js）。graph 命令面维持**不切**。

### invoke 快照

`docs/harness/invokes/by-task/dsh-coding-kit-upgrade-1-5-2/`：`invoke_20260825_10_*.md` + `invoke_20260825_30_*.md`（30 补齐）。

---

## 修订

| 日期 | 说明 |
|---|---|
| 2026-08-24 | 初版（00 起草 + 代签闸 · 维护者授权）：1.5.1→1.5.2 patch；附 FEEDBACK 项修复核对 |
| 2026-08-25 | 30 执行回填：升级完成（manifest 1.5.2 · local 块零字节 · 幂等过）；自检五项全 PASS；D1/D2/D3/R6 全未修（证据行号见自检表）；1.5.2 增量=DEF-028/029（修 K1/K4）；升级有出入 → FEEDBACK 已落盘 `FEEDBACK_dsh_coding_kit_1_5_2_from_ops_desk_api_20260824.md`（含新缺口 K7 from_version 判据过宽 / K8 freeze_id 按日滚动）；10/30 invoke 快照补齐 |
