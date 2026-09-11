# Task：spec-wave 2.1.3 收尾清理（cursor rules 裸文本替换 + 根级裸 SPEC 归位）

> **状态**：active  
> **类型**：文档健康度收尾 / harness 过程轨（上一 task 遗留 + 非范围项收编）  
> **前置**：`task_dsh_coding_kit_upgrade_2_1_0` 验收全勾（待 PR/CLOSE）；spec-wave **2.1.3** 已就位（manifest / package / CI 钉版）  
> **分支**：`task/specwave-cleanup-2-1-3`（新分支；base 确认：`task/dsh-coding-kit-2-1-0`——前序 PR #132 未合并 · 30 于 2026-09-11 回填）  
> **执行模式**：Open Folder = **ops-desk-api**；过程轨 + 文档搬迁；不改 `app/` 业务逻辑

---

## Harness 元信息

| 字段 | 值 |
|------|-----|
| **task_slug** | `specwave-cleanup-2-1-3` |
| **git_branch** | `task/specwave-cleanup-2-1-3`（base：`main` 或 `task/dsh-coding-kit-2-1-0`，由 30 定） |
| **implement_repo** | `ops-desk-api` |
| **test_strategy** | `required` |
| **test_strategy_note** | `node_modules/.bin/spec-wave check --target .` 零 WARN；`grep -rn "dsh-coding-kit" .cursor/rules/05-harness-starter.mdc .cursor/rules/05-kit-starter.mdc` 零命中；旧位置引用零命中两条（路径锚定 · 审查 R2 B-3 · 显式豁免 task 自身与 reviews）：(a) `grep -rEn "docs/spec/SPEC-(gha-deploy-api_v1|harness-to-dsh-kit-graph-migrate_v0|inform-graph-backfill_v1|langchain-evidence-chain_v1|lc-evidence-chain-hardening_v1|langfuse-sdk-v4-migration_v1|qdrant-migration_v1|rag-reranker-p0_v1)\.md" docs/ .cursor/ scripts/ experiments/ AGENTS.md --exclude=task_specwave_cleanup_2_1_3.md --exclude-dir=reviews` 零命中；(b) `grep -rEn "(\.\./)+(spec/)?SPEC-(gha-deploy-api_v1|harness-to-dsh-kit-graph-migrate_v0|inform-graph-backfill_v1|langchain-evidence-chain_v1|lc-evidence-chain-hardening_v1|langfuse-sdk-v4-migration_v1|qdrant-migration_v1|rag-reranker-p0_v1)\.md" <同范围同豁免>` 零命中；新位置可达：`test -f docs/spec/<夹>/SPEC-<名>.md` × 8（夹内保留原文件名）；`spec-wave verify --task`；`./scripts/graph-compile.sh` |
| **code_quality_bar** | `not_applicable` |
| **graph_change_layer** | `none` |
| **graph_delta** | `none` |
| **graph_delta_note** | 过程轨；仅 `scripts/graph-compile.sh` 注释内 SPEC 路径随行更新，不改 YAML 源 |
| **wiki_delta** | `none` |
| **wiki_delta_note** | 本波不晋升 coding_wiki；`docs/coding_wiki/context.md` 仅机械更新 SPEC 引用路径 |
| **experience_capture** | `recommended` |
| **kpi_aggregator** | `CLOSE` |
| **invoke_retention_profile** | `minimal` |
| **required_invoke_hats** | `30` |
| **close_pr_policy** | `required` |
| **related_pr** | （待开） |
| **review_hat** | `20` |

### 人工闸

| human_gate_id | status | blocks_hats | 说明 |
|---------------|--------|-------------|------|
| HG-TASK-DRAFT | approved | 20-R1, 30 | 2026-09-11 维护者授权 00 本窗代签（「授权00签收后续文件」） |
| HG-AUDIT-R1 | approved | 30 | 20-task-audit R3 PASS（reviews/task_specwave_cleanup_2_1_3_audit_R3_20260911.md）· 2026-09-11 维护者授权 00 本窗代签（过程轨 · 禁改 app/） |

---

## 背景与目标

spec-wave 2.1.3 改名升级（`task_dsh_coding_kit_upgrade_2_1_0`）遗留两项收尾：

1. **cursor rules 裸文本残留**：`.cursor/rules/05-harness-starter.mdc` 与 `.cursor/rules/05-kit-starter.mdc` 各有 **1 处**（第 19 行 GATE_VERIFY 命令）无 marker 的裸文本 `npx dsh-coding-kit`。`refresh-ide-blocks` 只报告、不刷写无 marker 文件，须手动替换为 `npx spec-wave`。
2. **根级裸 SPEC 归位**：`node_modules/.bin/spec-wave check --target .` 报 WARN——`docs/spec/` 根级 **8 个**裸 `SPEC-*.md`。新规范（`docs/spec/README.md` 公约 + `docs/spec/doc-health/`）：新长期 SPEC 一律放专属夹 `docs/spec/<slug>/`，禁止再新增根级裸 SPEC；历史债表 8 条全部 WARN。

目标：清零 check WARN + 清零 **cursor rules 两处 L19** `dsh-coding-kit` 裸命令残留（其余活文档旧命令面不在本波，见非范围清单），且全仓 SPEC 引用路径零断裂（含 `../spec/SPEC-…`、`../SPEC-…` 相对路径变体）。

## 范围

### A. cursor rules 裸文本替换（2 处）

1. `.cursor/rules/05-harness-starter.mdc` L19：`npx dsh-coding-kit verify ...` → `npx spec-wave verify ...`
2. `.cursor/rules/05-kit-starter.mdc` L19：同上
3. 仅替换该裸命令串；`cyning-harness` marker 块（其他文件）与文件其余内容零触碰

### B. 根级裸 SPEC 归位（8 文件 + 引用同步）

约定（`docs/spec/README.md` + 既有 `inform-graph-backfill/` 先例）：slug = SPEC 名去 `_vN` 版本后缀，目标夹 `docs/spec/<slug>/`。**夹内文件名约定写死**（审查 R2 B-3）：迁入后**保留原文件名** `SPEC-<name>_vN.md`，不改名、不拆分、不留根级 POINTER——循 `docs/spec/agent-infra/` 先例（`SPEC-capability-gateway_v0.md`、`SPEC-structured-output-gateway_v0.md` 现存且全仓 20 处夹内活引用均含裸文件名，属合法形态）。映射如下（**维护者 2026-09-11 已裁定 C-1/C-2/C-3 并写死**，见 `docs/harness/reviews/task_specwave_cleanup_2_1_3_audit_R1_20260911.md`，不再为待定项）：

| 源文件 | 目标位置 |
|--------|----------|
| `docs/spec/SPEC-gha-deploy-api_v1.md` | `docs/spec/gha-deploy-api/SPEC-gha-deploy-api_v1.md`（新夹 · **C-1 裁定**） |
| `docs/spec/SPEC-harness-to-dsh-kit-graph-migrate_v0.md` | `docs/spec/harness-to-dsh-kit-graph-migrate/SPEC-harness-to-dsh-kit-graph-migrate_v0.md`（新夹） |
| `docs/spec/SPEC-inform-graph-backfill_v1.md` | `docs/spec/inform-graph-backfill/SPEC-inform-graph-backfill_v1.md`（**既有夹** · **C-3 裁定**：整文件迁入，不留根级 POINTER） |
| `docs/spec/SPEC-langchain-evidence-chain_v1.md` | `docs/spec/lc-evidence-chain/SPEC-langchain-evidence-chain_v1.md`（**C-2 裁定**：与 hardening 合并夹，夹名定 `lc-evidence-chain`） |
| `docs/spec/SPEC-lc-evidence-chain-hardening_v1.md` | `docs/spec/lc-evidence-chain/SPEC-lc-evidence-chain-hardening_v1.md`（同上 · **C-2 裁定**） |
| `docs/spec/SPEC-langfuse-sdk-v4-migration_v1.md` | `docs/spec/langfuse-sdk-v4-migration/SPEC-langfuse-sdk-v4-migration_v1.md`（新夹） |
| `docs/spec/SPEC-qdrant-migration_v1.md` | `docs/spec/qdrant-migration/SPEC-qdrant-migration_v1.md`（新夹） |
| `docs/spec/SPEC-rag-reranker-p0_v1.md` | `docs/spec/rag-reranker-p0/SPEC-rag-reranker-p0_v1.md`（新夹） |

4. 移动前全仓 grep 建引用清单（已预查约 60+ 处，分布于 `docs/spec/README.md`、`docs/coding_wiki/context.md`、`docs/deployment/`、`docs/guides/`、`docs/_tech_graph/shared/99_mermaid_protocol.md`、`docs/tasks/PRIORITY_DEFERRED.md`、`docs/tasks/done/`、`docs/harness/reviews|invokes|evidence/`、`scripts/graph-compile.sh` 注释、`experiments/rag_compare/`、SPEC 互引/自引）；**相对路径变体**已点名，引用清单须覆盖全部提及形式（含裸文件名）；验收机验锚定**旧位置形式**（绝对 `docs/spec/SPEC-` + 相对 `../spec/SPEC-`/`../SPEC-`，见验收标准，审查 R2 B-3）：`docs/coding_wiki/context.md:37`（`../spec/SPEC-gha-deploy-api_v1.md`）、`docs/deployment/qdrant-migration-narrative.md:7`（`../spec/SPEC-qdrant-migration_v1.md`）、`docs/spec/inform-graph-backfill/README.md:15`（`../SPEC-harness-to-dsh-kit-graph-migrate_v0.md`）
5. 移动后同步更新全部引用；历史档（`tasks/done`、`reviews`、`invokes`、`evidence`）**仅机械路径替换**，不改实质内容；机械替换后仍残留裸文件名（新路径 `docs/spec/<夹>/SPEC-<名>.md` 的文件名部分）属**预期**，验收**不要求裸文件名零命中**（审查 R2 B-3）
6. `docs/spec/README.md` 索引更新：历史债表 8 行移除，专属夹表补齐新夹；**顺手更新** L3 公约行旧名 `dsh-coding-kit` → `spec-wave`（审查 R1 非阻塞项 4，本行已纳入范围）

## 非范围

- 不改 `app/` 业务逻辑
- 不动已完成的 spec-wave 改名 3 个提交（`a3ee873` / `3544de1` / `fcfba7d`）
- 不处理无关脏文件：`uv.lock`（M）、`.agents/`（??）
- 不改 `docs/spec/` 各 SPEC 正文实质内容（仅必要的自引路径行）
- 不改 kit 上游 assets；若下次 sync/upgrade 回灌旧命令 → 仅 FEEDBACK（见 failure_paths）
- 不清零其余活文档 `dsh-coding-kit` 旧命令面（本波仅清 cursor rules 两处 L19 裸文本；审查 R1 非阻塞项 1）：`docs/coding_wiki/README.md:36`、`docs/coding_wiki/topics/wikilinks_export.md:14`、`docs/spec/inform-graph-backfill/README.md:102`、`docs/spec/doc-health/process/agent_close_discipline.md:22-23`、`docs/_tech_graph/shared/99_mermaid_protocol.md:8` 等历史/过程文档留待后续波；`.cursor/commands/kit-*`、`.cursor/skills/*`、`docs/harness/prompts/*` 属 kit 上游资产走 FEEDBACK 轨（`docs/spec/README.md:3` 为例外，已纳入范围 B item 6 顺手更新）
- 占位符/描述行命中豁免（验收 grep 锚定旧位置路径 + 8 个具体文件名而非通配的原因，审查 R1 B-1 / R2 B-3）：`.cursor/skills/harness-10-spec/SKILL.md:51`、`docs/harness/prompts/10-spec-requirements.md:51`（模板占位符 `SPEC-<slug>_v1.md` · kit 资产）、`docs/spec/doc-health/README.md:48`（WARN 行为描述行）——本波不改
- `docs/spec/doc-health/.DS_Store`：已 gitignore，仅留痕不处理（审查 R1 非阻塞项 5）
- 不 `npm publish`；不擅自 `gh pr merge`；不代签任何人工闸

## 验收标准

- [ ] `.cursor/rules/05-harness-starter.mdc` 与 `05-kit-starter.mdc` 各 1 处 `npx dsh-coding-kit` → `npx spec-wave`；`grep -rn "dsh-coding-kit" .cursor/rules/` 零命中
- [ ] 8 个根级 `docs/spec/SPEC-*.md` 全部迁入上表目标夹（`ls docs/spec/SPEC-*.md` 无结果）
- [ ] 全仓引用同步 · **旧位置形式**零命中（路径锚定 · 审查 R2 B-3；**不要求裸文件名零命中**——迁入夹内合法新引用与历史档机械替换后残留的裸文件名均属预期，见范围 B item 5）：
  - (a) 绝对旧位置：`grep -rEn "docs/spec/SPEC-(gha-deploy-api_v1|harness-to-dsh-kit-graph-migrate_v0|inform-graph-backfill_v1|langchain-evidence-chain_v1|lc-evidence-chain-hardening_v1|langfuse-sdk-v4-migration_v1|qdrant-migration_v1|rag-reranker-p0_v1)\.md" docs/ .cursor/ scripts/ experiments/ AGENTS.md --exclude=task_specwave_cleanup_2_1_3.md --exclude-dir=reviews` 零命中
  - (b) 相对旧位置变体（覆盖 `../spec/SPEC-…` 与 `../SPEC-…`）：`grep -rEn "(\.\./)+(spec/)?SPEC-(gha-deploy-api_v1|harness-to-dsh-kit-graph-migrate_v0|inform-graph-backfill_v1|langchain-evidence-chain_v1|lc-evidence-chain-hardening_v1|langfuse-sdk-v4-migration_v1|qdrant-migration_v1|rag-reranker-p0_v1)\.md" docs/ .cursor/ scripts/ experiments/ AGENTS.md --exclude=task_specwave_cleanup_2_1_3.md --exclude-dir=reviews` 零命中
  - 豁免说明（元信息引用 · 审查 R2 B-3 处置项）：`--exclude=task_specwave_cleanup_2_1_3.md` 豁免本 task 自身（映射表源列 / test_strategy_note / failure_paths 中 9 处文件名属元信息引用，执行后不改写历史原文）；`--exclude-dir=reviews` 豁免 `docs/harness/reviews/`（R1/R2 等历史审查文）。新位置形式 `docs/spec/<夹>/SPEC-<名>.md` 与 `../<夹>/SPEC-<名>.md` 不匹配上述锚定模式，天然豁免
  - (c) 新位置可达（夹内保留原文件名 · 循 agent-infra 先例 · 逐文件机验）：`test -f docs/spec/gha-deploy-api/SPEC-gha-deploy-api_v1.md && test -f docs/spec/harness-to-dsh-kit-graph-migrate/SPEC-harness-to-dsh-kit-graph-migrate_v0.md && test -f docs/spec/inform-graph-backfill/SPEC-inform-graph-backfill_v1.md && test -f docs/spec/lc-evidence-chain/SPEC-langchain-evidence-chain_v1.md && test -f docs/spec/lc-evidence-chain/SPEC-lc-evidence-chain-hardening_v1.md && test -f docs/spec/langfuse-sdk-v4-migration/SPEC-langfuse-sdk-v4-migration_v1.md && test -f docs/spec/qdrant-migration/SPEC-qdrant-migration_v1.md && test -f docs/spec/rag-reranker-p0/SPEC-rag-reranker-p0_v1.md && echo ALL-8-OK`
- [ ] 占位符/描述行豁免核对（不改 kit 资产，审查 R1 B-1）：`.cursor/skills/harness-10-spec/SKILL.md:51`、`docs/harness/prompts/10-spec-requirements.md:51`、`docs/spec/doc-health/README.md:48` 保持原样（豁免理由见非范围）
- [ ] `docs/spec/README.md` 历史债表清空、专属夹表补齐、L3 公约行旧名更新为 `spec-wave`
- [ ] `node_modules/.bin/spec-wave check --target .` exit 0 且**零 WARN**
- [ ] `node_modules/.bin/spec-wave verify --target . --task docs/tasks/active/task_specwave_cleanup_2_1_3.md` PASS
- [ ] `./scripts/graph-compile.sh` exit 0
- [ ] FEEDBACK 落盘（`docs/spec/doc-health/feedback/`，含 cursor rules 无 marker 不刷写之摩擦记录）

## failure_paths

| 触发 | 行为 |
|------|------|
| SPEC 移动后引用断裂 | 移动前 grep 建清单 → 移动后逐条改 → 验收两条旧位置 grep 零命中 + 8 文件新位置 `test -f` 可达；发现断裂即回滚该文件重来 |
| 目标夹约定歧义 | C-1（`gha-deploy-api` 新建专属夹）/ C-2（合并夹名定 `lc-evidence-chain`）/ C-3（`inform-graph-backfill` 整文件迁入既有夹 · 不留根级 POINTER）已由维护者 2026-09-11 裁定并写死入映射表，执行时**不再 STOP**；执行中新发现的歧义仍 **STOP 问维护者**，结论回填本 task 映射表 |
| cursor rules 替换误伤 marker 块或其余 `dsh-coding-kit` 字样 | 仅改两文件第 19 行裸命令；替换前 grep 精确定位，替换后 diff 复核；marker 块零触碰 |
| kit 上游 assets 仍含旧命令，下次 sync/upgrade 回灌 | 不挡本波；FEEDBACK kit（`docs/spec/doc-health/feedback/`）记录 |
| 历史档路径改写被维护者要求保留原样 | 剔除该批文件并记录于本 task；活引用仍须零断裂 |
| graph-compile 仅注释/格式 diff | 接受并入库（若有） |
| 兄弟 active task（前序升级 task 未 CLOSE）挡 lint/CLOSE | 本波不与 `--with-wiki-lint` 强绑；阻塞则 STOP 报维护者 |

## 依赖

- 前置 task：[`task_dsh_coding_kit_upgrade_2_1_0.md`](./task_dsh_coding_kit_upgrade_2_1_0.md)（验收全勾 · 待 PR/CLOSE）
- 约定真值：[`docs/spec/README.md`](docs/spec/README.md)（专属夹公约 + 历史债表）· [`docs/spec/doc-health/README.md`](docs/spec/doc-health/README.md)
- WARN 复现：`node_modules/.bin/spec-wave check --target .`（裸 SPEC 8 条）

## 给执行帽（30）必读

1. 本 task 人工闸表（HG-AUDIT-R1=approved 前**拒开工**）
2. `docs/spec/README.md` + `docs/spec/doc-health/README.md`（目标夹约定）
3. `docs/harness/prompts/FRAGMENT_30_gate_verify_v1_zh.md`（GATE_VERIFY）
4. 开工先定 base 分支并回填头部「分支」行

## 思考轮控制

| 轮 | 焦点 | 结论 |
|----|------|------|
| R0 | 收编前 task 遗留 + check WARN 两项；grep 预查引用面（60+ 处）与 cursor rules 残留（2 处） | 范围/映射表/failure_paths 落定 |
| R1 | 目标夹命名约定核对（README 公约 + inform-graph-backfill 先例） | slug=去版本后缀；合并夹歧义入 failure_paths |
| R2 | 历史档（done/reviews/invokes）是否改 | 仅机械路径替换；维护者异议走 failure_path |
| R3 | kit 上游回灌风险 | 不挡本波，FEEDBACK 轨兜底 |
| R4 | 承接 20-task-audit R1 审查（`docs/harness/reviews/task_specwave_cleanup_2_1_3_audit_R1_20260911.md`）：B-1 验收 grep 锚定 8 文件名 + 3 处占位符/描述行豁免；B-2 相对路径变体覆盖（引用清单 + 机验）；维护者裁定 C-1/C-2/C-3 写死入映射表；非阻塞 5 项顺带修订 | 修订落定 · 送 R+1 复审 |
| R5 | 承接 20-task-audit R2 审查（`docs/harness/reviews/task_specwave_cleanup_2_1_3_audit_R2_20260911.md`）：B-3 裸文件名验收迁移正确完成后仍永不零命中（夹内合法新引用 / 历史档机械替换残留 / task 自身 9 处命中三条路径均致 FAIL）→ 验收拆为旧位置锚定两条 grep（绝对 `docs/spec/SPEC-<8名>` + 相对 `(\.\./)+(spec/)?SPEC-<8名>`）+ 8 个新位置 `test -f` 可达性检查；写死夹内保留原文件名（循 agent-infra 先例）；task 自身与 `docs/harness/reviews/` 显式豁免；历史档残留裸文件名属预期 | 修订落定 · 送 R3 复审 |

- **early_stop**：R5 后停 · reason：过程轨收尾，面小、命令可验证、无业务风险；R1 审查阻塞项 B-1/B-2、R2 审查阻塞项 B-3 已修订，裁定项 C-1/C-2/C-3 已回填映射表 · residual_risks：① 豁免的 3 处占位符/描述行使通配 `docs/spec/SPEC-` grep 永不零命中（已锚定 8 文件名规避）；② 迁入夹内合法新引用与历史档机械替换后残留的裸文件名使裸文件名 grep 永不零命中（审查 R2 B-3 · 已改旧位置路径锚定 + task 自身/reviews 显式豁免 + 新位置 `test -f` 可达性兜底规避）；③ 其余活文档旧命令面留待后续波（已入非范围清单）
- 20-task-audit 认为不足 → 退回 10-task 补轮再审 R+1

### 自检结论

| 命令 | 退出码 |
|------|--------|
| `node_modules/.bin/spec-wave task lint --file docs/tasks/active/task_specwave_cleanup_2_1_3.md` | 0（LINT: PASS · 10-task 起草自检） |
| `node_modules/.bin/spec-wave task lint --file docs/tasks/active/task_specwave_cleanup_2_1_3.md`（2026-09-11 · 承接 R1 审查修订后复跑） | 0（LINT: PASS · 10-task 修订自检） |
| `node_modules/.bin/spec-wave task lint --file docs/tasks/active/task_specwave_cleanup_2_1_3.md`（2026-09-11 · 承接 R2 审查 B-3 修订后复跑） | 0（LINT: PASS · 10-task 修订自检；锚定模式实证：新位置形式不命中 (a)/(b)，豁免后基线 (a) 42 命中 / (b) 4 命中，迁移后归零可达成） |
| _（其余 draft 期占位 · 30 执行后回填）_ | — |

### KPI

Task_KPI%: _（draft 期占位 · CLOSE 前回填）_
