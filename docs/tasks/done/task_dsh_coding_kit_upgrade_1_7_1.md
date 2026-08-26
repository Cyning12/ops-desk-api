# Task：dsh-coding-kit 升级 1.7.1（CLOSE 强绑定 dogfood + 00 条文 + 文档迁移）

> **状态**：completed（闸已签 · 2026-08-26 随 PR #63 关账归档）  
> **类型**：基础设施 / harness 过程轨升级（patch）+ **doc-health 试点文档迁移**  
> **前置**：manifest 现为 `1.6.1`；kit **1.7.1 已 npm 发版**（含 1.7.0 CLOSE 闸 + Starter `00-orchestrator.md`）；本仓已有试点镜像 `docs/spec/doc-health/`  
> **契约真值**：`dsh-coding-kit@1.7.1` CHANGELOG +（可选）本机 `Desktop/Projects/dsh-coding-kit/docs/spec/doc-health/`  
> **分支**：`task/dsh-coding-kit-1-7-1`  
> **执行模式**：Open Folder = **ops-desk-api**；30 执行；FEEDBACK 写回 `docs/spec/doc-health/feedback/`  
> **取代**：原草稿 `task_dsh_coding_kit_upgrade_1_7_0.md`（未执行；靶版本抬到 1.7.1）

---

## Harness 元信息

| 字段 | 值 |
|------|-----|
| **task_slug** | `dsh-coding-kit-upgrade-1-7-1` |
| **git_branch** | `task/dsh-coding-kit-1-7-1` |
| **implement_repo** | `ops-desk-api` |
| **test_strategy** | `required` |
| **test_strategy_note** | 升级后：`npx dsh-coding-kit@1.7.1 check` / `verify --task <本task>`；`./scripts/graph-compile.sh` exit 0；pytest 无新增失败；CLOSE dry-run 实证 `READY`；prompts 含 `00-orchestrator.md` |
| **code_quality_bar** | `not_applicable` |
| **graph_change_layer** | `none` |
| **graph_delta** | `none` |
| **graph_delta_note** | 过程轨升级；不改业务图谱 |
| **wiki_delta** | `none` |
| **wiki_delta_note** | 本波不晋升 coding_wiki；FEEDBACK 走 doc-health/feedback |
| **experience_capture** | `recommended` |
| **kpi_aggregator** | `CLOSE` |
| **invoke_retention_profile** | `default` |
| **required_invoke_hats** | `10,30,40` |
| **close_pr_policy** | `required` |
| **related_pr** | `#63` |

### 人工闸

| human_gate_id | status | blocks_hats | 说明 |
|---------------|--------|-------------|------|
| HG-TASK-DRAFT | approved | 22-R1, 30 | 2026-08-26 00 代签（维护者粘贴 PROMPT_00_30_upgrade_kit_1_7_1 复制区 · 本窗授权「可签过程文档」） |
| HG-AUDIT-R1 | approved | 30 | 2026-08-26 00 代签（轻量 R1：`docs/harness/reviews/task_dsh_coding_kit_upgrade_1_7_1_audit_R1_20260826.md`；过程轨升级 · 不改 app/） |

---

## 背景与目标

把本仓从 **dsh-coding-kit 1.6.1 → 1.7.1**，完成：

1. **1.7.0 行为**：doc-health CLOSE（READY/PASS）、Hub 闸、`check` 裸 SPEC WARN、process/FEEDBACK 轨  
2. **1.7.1 增量**：Starter 入包 `docs/harness/prompts/00-orchestrator.md`（00 默认编排纪律）随 upgrade/sync 落地  

升级摩擦写入 `docs/spec/doc-health/feedback/`，便于反哺 kit。

---

## 范围

### A. 升级（过程轨）

1. 钉依赖 / 用 `npx --yes dsh-coding-kit@1.7.1`（本机可用 `npm_config_cache=/tmp/npm-cache-lg`）按先例序列：`check` → `refresh-ide-blocks`（先 dry-run）→ `upgrade --yes` → 幂等复检。  
2. **local 块零手恢复**：`<!-- cyning-harness-local:begin/end -->` 升级后仍在；被冲则恢复并记 FEEDBACK。  
3. `manifest.version` 钉 **1.7.1**；记录 `from_version`。  
4. 确认 `docs/harness/prompts/00-orchestrator.md` 已出现（含「默认行为」表）；若 sync 未覆盖则按 kit 资产补齐并 FEEDBACK。  
5. 跑通：`verify --task <本task>`（序内缺件可留痕豁免并注明）、`./scripts/graph-compile.sh`、pytest（无新增失败）。

### B. 文档迁移 / dogfood（1.7.0+1.7.1 行为）

6. 更新试点镜像文案与状态：  
   - `docs/spec/doc-health/README.md`：标明 kit **1.7.1 已发版**、SPEC 已签收；读序指向 process/feedback。  
   - `docs/spec/doc-health/process/agent_close_discipline.md`：与 1.7.0+ 对齐（dry-run=`READY`；`--yes`=`PASS`；Hub 必做；PR MERGED / 豁免说明）。  
7. 确认 `docs/spec/README.md` **历史债**表仍在（warn 感知通道）；`npx dsh-coding-kit check` 应对根级裸 `SPEC-*.md` 打出 WARN（记录条数，不要求本波搬迁）。  
8. **CLOSE dogfood（只读/dry-run 优先）**：对本 task 跑一次 `task close`（无 `--yes`）→ 断言输出含 **`CLOSE: READY`** 且 **不含** 完成态 `CLOSE: PASS`；有 Hub 时若缺索引行应 `close_hub_index` BLOCK（可先补 Hub 行再 READY，或记 FEEDBACK）。  
9. 扫描仓内 Prompt/脚本是否仍写「dry-run = CLOSE: PASS」或旧 `@cyning/harness task close` 完成态口径；**可安全改的过程文档**改掉；历史 done/invoke **不**批量改写。  
10. 有出入 → 复制 `docs/spec/doc-health/feedback/_TEMPLATE.md` 为 `2026-08-26_1.7.1_<topic>.md` 并登记 feedback/README 表。

## 非范围

- 不搬迁 `docs/spec/SPEC-*.md` 历史裸文件（仅 WARN / 索引表）  
- 不改 `app/` 业务代码  
- 不切换 graph-compile.sh / CI 命令面（除非升级强制且维护者另授）  
- 不执行 `npm publish`；不擅自 `gh pr merge`（本 task 关账须 PR MERGED 或显式豁免）  
- 不批量清理 active/ 历史堆积（可列观察项进 FEEDBACK）  
- 不强制安装 Agent Skill `harness-00-*`（1.7.1 仅 prompts 入包、Skills 默认不分发）

---

## failure_paths

| 触发 | 行为 | 可重试 |
|------|------|--------|
| upgrade 冲掉 local 块 | 恢复 + FEEDBACK | Y |
| dry-run 仍打 `CLOSE: PASS` | FEEDBACK severity 高；停报 00 | Y |
| Hub 闸误伤无法关账 | 补 Hub 行；或临时 `close_hub_gate: false` / `--allow-no-hub` 并 FEEDBACK | Y |
| PR 未合入挡 close | 先合 PR；或 `close_pr_policy=exempt` + note / `--allow-no-pr-merge` 留痕 | Y |
| 缺 `00-orchestrator.md` | 自 kit 资产补齐 / 记 FEEDBACK | Y |
| npm 缓存权限 | `npm_config_cache=/tmp/...` | Y |

---

## 验收标准

- [x] `.cyning-harness/manifest.json` version=`1.7.1`；local 块保留（diff 证据）  
- [x] `docs/harness/prompts/00-orchestrator.md` 存在且含「默认行为」  
- [x] `check` 输出含裸 SPEC WARN（或记录「0 条」若已无裸文件）；`verify` / graph-compile / pytest 结论写入自检  
- [x] `task close` dry-run → **`CLOSE: READY`**（贴关键 stdout）  
- [x] `docs/spec/doc-health/` README + process 已对齐 1.7.1；FEEDBACK 有则落盘、无则自检写「无出入」  
- [x] 过程文档中误导性「dry-run=PASS」已清理（范围 B.9）；未动业务代码  

---

## 给执行帽的必读列表

1. 本 task  
2. `docs/spec/doc-health/README.md` · `process/agent_close_discipline.md` · `feedback/`  
3. 先例：`docs/tasks/done/task_dsh_coding_kit_upgrade_1_6_1.md`  
4. kit CHANGELOG `[1.7.0]` + `[1.7.1]` 消费者提示  
5. Hub：`docs/tasks/done/README.md`  
6. Prompt：`docs/harness/invokes/by-task/_prompts/PROMPT_00_30_upgrade_kit_1_7_1.md`

---

## 思考轮控制（10 轻量）

| 轮 | 结论 | early_stop |
|----|------|------------|
| R0 | 1.6.1→1.7.1 + doc-health dogfood + 00 条文 | no |
| R1 | 升级 + 文档迁移；非范围=搬裸 SPEC / app | no |
| R2 | 单 task（与 1.5.x/1.6.1 先例一致；吞并未执行的 1.7.0 草稿） | yes · 升级先例充分 |
| R3–R5 | （跳过 · 见 early_stop） | — |

**residual_risks**：Hub 历史漏行导致首次 close 大面积 BLOCK → 依赖补行或闸关；旧 prompts 若 upgrade 未刷须手改。

---

### 自检结论（执行者）

30 执行 · 2026-08-26 · 分支 `task/dsh-coding-kit-1-7-1` · **未动 `app/`**

| # | 项 | 结果 |
|---|----|------|
| 1 | manifest 钉 1.7.1 | **PASS**（version=1.7.1 · from_version=1.6.1 · preset/ide 保留；首次 `upgraded_at=2026-08-26T07:48:18Z`） |
| 2 | local 块 | **PASS**（`git diff AGENTS.md CLAUDE.md` 空；refresh dry-run `skipped_local_blocks=1` / rewrites=0） |
| 3 | `00-orchestrator.md` | **手补 PASS**（upgrade 未落地，自 kit `assets/harness/prompts/` 复制；含「默认行为」表） |
| 4 | `check` 裸 SPEC WARN | **8 条**（与 `docs/spec/README.md` 历史债表一致；不搬迁） |
| 5 | `verify --task <本task>` | **PASS exit 0**（R1 + invoke 10 已就位；无需 `--allow-no-review` / `--allow-invoke-gap`） |
| 6 | `./scripts/graph-compile.sh` | **PASS exit 0**（产物仅 `generated_at` 时间戳，已 `git checkout` 还原） |
| 7 | pytest | **3 failed / 298 passed** = 既有基线 `test_chat_router` / `test_chat_ws` 缺表 · **无新增失败**（1.6.1 波为 3/242） |
| 8 | CLOSE dry-run | 无 `--yes`：`close_pr_merged` BLOCK；`--allow-no-pr-merge` → **`CLOSE: READY · dsh-coding-kit-upgrade-1-7-1`**（stdout 无 `CLOSE: PASS`） |
| 9 | B.9 过程文 | 已用 kit 1.7.1 版替换 `docs/harness/prompts/30-execute-code.md`（原 `@cyning/harness task close` 完成态口径）；未改 `done/` 历史 invoke |

FEEDBACK：`docs/spec/doc-health/feedback/2026-08-26_1.7.1_upgrade-no-prompt-sync.md`

---

### KPI（00）

Task_KPI%: 90

（扣 10：upgrade 未自动落地 00 条文，手补 + FEEDBACK；关账待 PR MERGED。）

---

### 经验总结

- kit 1.7.1 `upgrade` **只写 manifest**，Starter 新增文件不会进入已接入仓；验收须对照包内 `assets/harness/prompts/` 做存在性检查，缺则 `cp` 并开 FEEDBACK。
- CLOSE 1.7.0+：无 `--yes` 只允许写 `CLOSE: READY`；`close_hub_index` 在本仓默认开，dry-run 前就要 Hub 有文件名；`close_pr_merged` 在 PR 未合入时必须 `--allow-no-pr-merge` 或等 MERGED。
- 幂等 `upgrade --yes` 会刷新 `upgraded_at`（`from_version` 保持）；若要比对首次升级时间，先记下再还原。

---

## 修订记录

| 日期 | 摘要 |
|------|------|
| 2026-08-26 | 00 起草 1.7.0 草稿（未执行） |
| 2026-08-26 | 抬靶 **1.7.1**（CLOSE 闸 + Starter 00）；删/取代 1.7.0 task 草稿 |
| 2026-08-26 | 30 回填自检 · 闸代签 · 手补 00 条文 |
