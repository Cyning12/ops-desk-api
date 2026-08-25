# Task：dsh-coding-kit 升级 1.6.1（minor 升级 + FEEDBACK 项修复核对）

> **状态**：completed（闸已签 · 00 代签授权；2026-08-25 随 PR #50 关账归档）  
> **类型**：基础设施 / harness 过程轨升级（minor）  
> **前置**：1.5.1 / 1.5.2 升级已入 master；FEEDBACK 反哺 D1–D3 / R6 / K7 / K8 在案  
> **关联**：`docs/harness/evidence/FEEDBACK_dsh_coding_kit_1_5_2_from_ops_desk_api_20260824.md`  
> **分支**：`task/dsh-coding-kit-1-6-1`  
> **执行模式**：00 编排/验收；30 子 agent 执行

---

## Harness 元信息

| 字段 | 值 |
|---|---|
| **task_slug** | `dsh-coding-kit-upgrade-1-6-1` |
| **git_branch** | `task/dsh-coding-kit-1-6-1` |
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
| HG-TASK-DRAFT | approved | 22-R1 | 2026-08-25 00 代签（维护者直接指令「更新 coding-kit 到 1.6.1」+ 本窗授权） |
| HG-AUDIT-R1 | approved | 30 | 2026-08-25 00 代签（升级路径 1.5.1/1.5.2 连续验证过） |

---

## 范围

1. `npm_config_cache=/tmp/npm-cache-lg npx --yes dsh-coding-kit@1.6.1` 按已验证序列升级（check → refresh-ide-blocks → upgrade → 幂等复检）；local 块零手恢复复检。**minor 跳版注意**：先探查 CLI 面有无新增/变更子命令（--help diff 1.5.2 记忆），有破坏性变化须记录并停下报 00。
2. **FEEDBACK 项修复核对**（实读 1.6.1 包源码，证据行号）：D1（export 丢边 label）/ D2（graph_id 命名空间）/ D3（check-export 互认）/ R6（class 按 kind）/ K7（from_version 覆盖）/ K8（freeze_id 日滚动——属本仓产物行为，核对 kit 侧是否提供固定项）；DEF-023 已修三条未回退抽查。
3. 升级有出入 → FEEDBACK 落盘 `docs/harness/evidence/FEEDBACK_dsh_coding_kit_1_6_1_from_ops_desk_api_20260825.md`（无出入修订行注明免落）。

## 非范围

- graph-compile.sh / CI 命令面切换（仍须维护者另签）
- 业务代码、图谱语义

## 验收标准

- [x] manifest 钉 1.6.1；local 块零字节变化（diff 证据 · 见自检 §1/§2）
- [x] verify / graph-compile / pytest 三项跑通（基线一致 · 见自检 §3/§4/§5）
- [x] D1/D2/D3/R6/K7/K8 修复状态结论表（含证据）记入 task 自检；CLI 面变更点记录（见自检 §6/§7）
- [x] 有出入时 FEEDBACK 落盘（`docs/harness/evidence/FEEDBACK_dsh_coding_kit_1_6_1_from_ops_desk_api_20260825.md`）

---

## 自检结论（30 执行 · 2026-08-25）

### 五项自检

| # | 项 | 结果 |
|---|----|------|
| 1 | manifest 钉 1.6.1 | **PASS**（version=1.6.1 · from_version=1.5.2 · preset=fullstack-node-py / ide 保留；幂等二跑 1.6.1→1.6.1 from_version 与 upgraded_at 不变） |
| 2 | local 块零字节变化 | **PASS**（`git diff AGENTS.md CLAUDE.md` 输出为空；refresh --yes rewrites=0 / files_written=0；报告自述「跳过 local 块: 1」） |
| 3 | `verify --task <本task>` | **PASS**（严格态 BLOCKED exit 2 · missing R<n> review = 20 序内预期；`--allow-no-review` 留痕豁免 **PASS exit 0**；10/30 invoke 就位无需 --allow-invoke-gap） |
| 4 | `./scripts/graph-compile.sh` | **PASS** exit 0（harness 面未动；产物 diff 仅 generated_at 时间戳，已 git checkout 还原） |
| 5 | `.venv/bin/pytest tests -q` | **PASS**（3 failed / 242 passed = 既有基线 chat_ws/chat_router 缺表 · 无新增失败） |

### FEEDBACK 项逐项结论（实读 1.6.1 包源码 · 证据行号见 FEEDBACK §3/§4）

| ID | 结论 | kit 修复编号 | 关键证据（1.6.1 行号） |
|----|------|-------------|------------------------|
| D1 export 丢边 label | **已修** | DEF-031 | cli-graph-yaml.js L200-201/206/211/216（mark 各分支 `baseLabel = label`） |
| D2 graph_id 路径命名空间 | **已修** | DEF-032①③ | L281-302 declaredId 写 graphs/nodes/edges；L40-44 校验口径自洽 |
| D3 check-export 不互认 | **已修** | DEF-032② | L548-551 check 与 export 同一声明值真值源 |
| R6 class 按 yaml kind | **已修** | DEF-033 | L401-424 KIND_TO_CLASS（flow/struct/external→phase/doc/infra）+ id 推断兜底 |
| K7 from_version 覆盖 / DEF-028 判据过宽 | **判据过宽已修**（from_version=直接前驱语义不变） | DEF-030 | cli.js L85-89 2.x 词表 / L213-215 收窄；本仓 check 实证「可升级」无误报 |
| K8 freeze_id 日滚动 | **kit 侧有固定项**（常量 TECH_GRAPH_S2_FREEZE_20260519_V2_3 · opts.freezeId 可覆盖）；日滚动系本仓 graph_yaml_to_json.py 行为，沿用 checkout 还原 | — | cli-graph-yaml.js L5/270/318 |
| DEF-023 三条回退抽查 | **未回退** | — | formatAnchorComment L332-338 · 带标签边 L380/387 · 引号+转义 L350-354/363-364 · `grep -- '--"'` 0 命中 |

`lib/cli-graph-yaml.js` 与 1.5.2 diff = **79 行**（1.5.2 波对 1.5.1 为 0 行，本波实质修复落地）。

### CLI 面变更点（1.5.2 → 1.6.1 · 无破坏性变更）

- `verify` 新增 `--spec FILE` 模式（SPEC→00 前审查文存在性闸 · 与 --task 互斥）+ `--allow-no-spec-review` 豁免旗标（`--allow-no-review` 作别名）——顶层 help 唯一 diff
- upgrade / refresh-ide-blocks / check / graph 全子命令面 help 零变更；无参数删除、无语义反转
- lib 增量：cli-checks.js（findSpecReview / shouldSkipSpecAudit / evalSpecReviewsRetention / evalCloseWikiPromotion）；cli-lifecycle.js 接线 spec_reviews_retention 与 close_wiki_promotion 守卫；新增 RELEASING.md
- 行为修正（README.zh-CN L108 自述）：graph export graph_id 改声明值 + 边 label 保留 + class 按 kind——本仓未消费 kit export 输出，无即时影响；graph 命令面切换 probe task 需行为等价回归

### 产物

- FEEDBACK：`docs/harness/evidence/FEEDBACK_dsh_coding_kit_1_6_1_from_ops_desk_api_20260825.md`
- invoke 快照：`docs/harness/invokes/by-task/dsh-coding-kit-upgrade-1-6-1/`（帽 10 + 帽 30）
- manifest：`.cyning-harness/manifest.json`（1.6.1）
- **未 commit · 未 close**（00 统一提交 / 20 R<n> 序内补件）

---

## CLOSE

| 项 | 内容 |
|---|---|
| 日期 | 2026-08-25 |
| 定稿 | kit 1.6.1（反哺项全关闭） |
| 归档 | `docs/tasks/done/task_dsh_coding_kit_upgrade_1_6_1.md` |
| PR | [#50](https://github.com/Cyning12/ops-desk-api/pull/50) MERGED |

---

## 修订

| 日期 | 说明 |
|---|---|
| 2026-08-25 | 初版（00 起草 + 代签闸 · 维护者授权）：1.5.2→1.6.1 minor；附 FEEDBACK 项修复核对 |
| 2026-08-25 | 30 执行回填：升级完成（manifest 1.6.1 · local 块零字节 · 幂等 PASS）；D1/D2/D3/R6/K7 全已修、K8 kit 侧固定项确认、DEF-023 未回退；五项自检全过；FEEDBACK 落盘 |
| 2026-08-25 | 归档（task_task_closeout_hygiene）：CLOSE 节补录 · 状态→completed · git mv 至 docs/tasks/done/（合并日 2026-08-25 · PR #50） |
