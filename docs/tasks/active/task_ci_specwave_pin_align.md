# Task：ci-specwave-pin-align（仓卫生 · CI/脚本 spec-wave 钉版对齐 3.3.0 · chore）

> **状态**：active（30 已交付 · 待 PR CI 实证（TC-4 由 40 核验）· 2026-10-17 维护者授权 00 代录签收（m00238「授权00签收后续文档，开始下面的任务」· 20 R1 书面审经授权豁免）
> **类型**：仓卫生 / 工具链钉版对齐（chore · 零 `app/` 改动 · `graph_change_layer=none`）
> **依据**：`docs/tasks/close/close_specwave_330_graph_update_20261011.md` §「CI 钉版不一致」照录 + 后续工作建议第 1 条（「另立小 task 统一升 3.3.0」）· `docs/tasks/done/task_specwave_330_graph_update.md`（PR #242 已合）
> **分支建议**：`task/ci-specwave-pin-align`（base master 最新）

## Harness 元信息

| 字段 | 值 |
|------|-----|
| **task_slug** | `ci_specwave_pin_align` |
| **git_branch** | `task/ci-specwave-pin-align` |
| **implement_repo** | `ops-desk-api` |
| **test_strategy** | `required` |
| **test_strategy_note** | 纯工具链钉版面：grep 断言钉版字面一致 + 本地 graph-compile / lint-wiki-delta 在 3.3.0 下绿 + PR CI（tech-graph / lint-wiki-delta）绿实证；零 `app/` diff 故 pytest 构造性恒等（触及面全绿即可） |
| **code_quality_bar** | `L2_backend` |
| **graph_change_layer** | `none`（30 实判：仅改 scripts/ 与 .github/workflows/ 钉版字面；若 3.3.0 下编译产出图谱 md diff → 越界，见 FP-2） |
| **graph_delta** | 无 |
| **graph_delta_note** | 本 task 不改图谱源；3.3.0 compile 若产生既有 md 漂移，不混入本 PR，另立案 |
| **wiki_delta** | `n/a` |
| **wiki_delta_note** | 钉版事实回写 CLOSE 文档后续工作清单即可，无 wiki 面 |
| **review_hat** | `20` |
| **required_invoke_hats** | `10,20,30,40` |
| **invoke_retention_profile** | `default` |
| **experience_capture** | `recommended` |
| **kpi_aggregator** | `n/a` |
| **orchestration** | 10 落稿 → 20-task-audit R1 → 维护者签闸 → 30（钉版 + 本地实证）→ 40（PR CI 绿核验）→ PR → CLOSE |
| **freeze_id** | 无 |

### 人工闸

| human_gate_id | status | blocks_hats | 说明 |
|---------------|--------|-------------|------|
| HG-TASK-DRAFT | approved | 20, 30 | 2026-10-17 维护者授权 00 代录（m00238） |
| HG-AUDIT-R1 | approved | 30 | 2026-10-17 维护者授权 00 代录（m00238 · 20 R1 书面审豁免） |
| HG-GRAPH-MODULES | approved | 30 | 2026-10-17 代录：全局真值 approved（docs/_tech_graph/l1/01_modules.md:63）· `graph_change_layer=none` |

---

## 背景与目标

### 实证面（10 亲读 · 2026-10-17）

仓内已于 2026-10-11 升 spec-wave **3.3.0**（task `specwave_330_graph_update` · PR #242 · squash `92a8526`），但钉版不一致面仍在：

| 位置 | 现状钉版 | 证据 |
|------|----------|------|
| `scripts/graph-compile.sh:28` | `GRAPH_CLI="${GRAPH_CLI:-spec-wave@3.0.1}"` | 10 亲读；同文件 :18-22 注释亦载 3.0.1 钉法缘由 |
| `.github/workflows/lint-wiki-delta.yml:35` | `npx --yes spec-wave@3.0.1 task lint-wiki-delta --target .` | 10 亲读；:39 注释行（--strict 备选）同钉 3.0.1 |
| `package.json:6` | `"spec-wave": "3.3.0"`（devDependencies 精确钉） | 10 亲读 |
| `.coding-kit/manifest.json` | `"version": "3.3.0"` · `"from_version": "3.0.1"` | 10 亲读 |
| `pnpm-lock.yaml` | `spec-wave@3.3.0` 锁 | 见 `docs/tasks/done/task_arch_browser_eng_graph_mermaid.md` TC-4 |
| `.github/workflows/tech-graph.yml:33` | 调 `./scripts/graph-compile.sh`（钉版随脚本内 GRAPH_CLI） | 10 亲读：workflow 无独立钉版字面 |

### 风险照录（来自 CLOSE 文档，禁擅改史实）

`close_specwave_330_graph_update_20261011.md` §「CI 钉版不一致」：本地/CI 的 graph-compile 与 lint-wiki-delta 闸实际跑在 3.0.1 上；**3.2 W1 形状闸（implementedBy object）与 3.3 ast check 在 3.0.1 下不存在**——两处钉 3.0.1 时不会拦形状闸缺口，亦不会产生升级提示。CLOSE 已明示「是否刻意待维护者确认，禁擅改」，并建议「若确认为遗漏，另立小 task 统一升 3.3.0」。本 task 即该另立小 task。

### 目标

统一钉版到 **3.3.0**（与 `package.json` / `.coding-kit/manifest.json` / `pnpm-lock.yaml` 对齐；若 30 前亲读发现 3.3.0 已非目标，须先回 10 钉案再动手）；同步更新两处文件的相关注释；本地 + CI 双侧绿实证；回滚策略落盘。

---

## 范围

- [x] **S1 · 钉版统一**（30 · 2026-10-17 ✔）：`scripts/graph-compile.sh:28` GRAPH_CLI 默认值 `spec-wave@3.0.1` → `spec-wave@3.3.0`；`.github/workflows/lint-wiki-delta.yml:35` 与 :39（注释行）`spec-wave@3.0.1` → `spec-wave@3.3.0`。
- [x] **S2 · 注释同步**（30 ✔ · 历史注释原文零改）：`graph-compile.sh` 头部 2026-10-11 段（:18-22）与 `lint-wiki-delta.yml` 头部 2026-09-23 段（:4-5）补一行对齐记录（日期 + 本 task slug + 缘由一句话）；**不改**历史注释原文。
- [x] **S3 · 本地实证**（30 ✔ · 证据见 30 invoke）：`./scripts/graph-compile.sh` EXIT=0 且日志首行含 `[spec-wave@3.3.0]`；`npx --yes spec-wave@3.3.0 task lint-wiki-delta --target .` 输出含 `LINT-WIKI-DELTA: PASS`。
- [ ] **S4 · CI 实证**：PR 上 `tech-graph` 与 `lint-wiki-delta` 两个 workflow 绿；run 日志摘录证明实际加载 3.3.0（钉入 40 invoke）。
- [x] **S5 · 零 diff 纪律**（30 ✔ · graph.json 日期漂移已恢复未混入）：`git diff --stat` 仅触上述两文件（+ 本 task 文件与 invoke）；图谱产出 / pnpm-lock / 其他文件零卷入。

## 非范围

- ❌ spec-wave **功能升级**（>3.3.0 追踪、新命令面启用如 `graph ast check` 默认开）
- ❌ verify / lint / 形状闸**规则变更**；`--strict` 开关启用
- ❌ 图谱档（`docs/_tech_graph/**`）内容适配改动——3.3.0 下若产出漂移另立案（FP-2）
- ❌ `package.json` / `package-lock.json` / `pnpm-lock.yaml` / `.coding-kit/manifest.json` 改动（已是 3.3.0）
- ❌ 其他 workflow（deploy-api / import-linter / pytest / ops_sync_kimi_code）改动
- ❌ 本起草阶段零任何文件改动（仅落盘本 task）

---

## failure_paths

| 触发条件 | 系统行为 | 可重试 | 用户可见 |
|----------|----------|--------|----------|
| FP-1 钉版 bump 后 CI 红（tech-graph 或 lint-wiki-delta 在 3.3.0 下失败） | **不 merge**；先定位是钉版引入还是存量违规被新闸拦住；**回滚策略**：`git revert` 钉版 commit（单行字面 diff），CI 恢复 3.0.1 钉法即复绿，再另立适配 task 处理存量 | 是（revert 即可重试） | PR 红 / merge blocked |
| FP-2 3.3.0 下 compile 产出图谱 md 与仓内漂移 | 不混入本 PR；恢复产出、另立图谱适配 task；本 task 仅钉版 | 是 | graph diff 污染 PR |
| FP-3 HG-AUDIT-R1 / HG-GRAPH-MODULES pending 即 30 | GATE_VERIFY **拒开工**（`npx spec-wave verify --task` BLOCKED） | 是 | — |
| FP-4 CI runner npx 缓存导致实际仍跑 3.0.1 | 40 核验 run 日志版本字面值；不符则钉 `npm cache` / 显式 `npx --yes spec-wave@3.3.0 --version` 前置步断言 | 是 | CI 假绿 |
| FP-5 维护者裁定目标版本 ≠ 3.3.0（如刻意保留 3.0.1） | STOP 回 10 改写钉案或 CLOSE 为 won't-do；禁 30 自行拍板 | 是 | task 返工 |
| FP-6 顺手改历史注释原文 / 无关文件 | 拒收；diff 白名单仅 S1/S2 两文件 | 是 | PR 噪声 |

---

## 验收标准

- [x] **TC-1（钉版一致）**（30 ✔ · 执行面 3.0.1 清零；历史注释 2 处保留系 S2 明文，照登）：`grep -rn "spec-wave@3" scripts/ .github/` 输出中 **无 3.0.1 字面**，`spec-wave@3.3.0` 恰现于 `scripts/graph-compile.sh` GRAPH_CLI 行、`lint-wiki-delta.yml` 两处（:35 + :39 注释行）；`package.json:6` / manifest 保持 3.3.0 零 diff。
- [x] **TC-2（本地 graph-compile）**（30 ✔ · EXIT=0 · 首行 [spec-wave@3.3.0] · 图谱 md 零 diff）：`./scripts/graph-compile.sh` EXIT=0；输出首行含 `[spec-wave@3.3.0] compiling`；`git status` 图谱产出 **零 diff**（若有 diff 转 FP-2，禁勾选本项）。
- [x] **TC-3（本地 lint-wiki-delta）**（30 ✔ · LINT-WIKI-DELTA: PASS · EXIT=0）：`npx --yes spec-wave@3.3.0 task lint-wiki-delta --target .` 输出含 `LINT-WIKI-DELTA: PASS`。
- [ ] **TC-4（CI 绿实证）**：PR 检查 `tech-graph`、`lint-wiki-delta` 均绿；40 invoke 贴 run 链接 + 日志摘录证明 3.3.0 实载（FP-4 防假绿）。
- [x] **TC-5（回滚预案）**（30 ✔ · revert 命令载 30 invoke 与 PR 描述）：30 invoke 或 PR 描述载明 FP-1 回滚命令（`git revert <pin-commit>` 单行字面 diff 复原 3.0.1）与本 PR commit 哈希。
- [x] **TC-6（零越界）**（30 ✔ · diff 白名单内 · pytest 构造性恒等照登）：`git diff --stat master...HEAD` 仅含 `scripts/graph-compile.sh`、`.github/workflows/lint-wiki-delta.yml`、`docs/tasks/active/task_ci_specwave_pin_align.md`、invoke 档；pytest/ruff 存量零新增红（本 task 零 `app/` diff）。

## 依赖

- 不一致面照录与授权来源：`docs/tasks/close/close_specwave_330_graph_update_20261011.md`（§「CI 钉版不一致」+ 后续工作建议第 1 条）
- 升级史：`docs/tasks/done/task_specwave_330_graph_update.md`（PR #242 · 3.0.1→3.3.0 图谱适配已 done）
- pnpm-lock 3.3.0 锁证据：`docs/tasks/done/task_arch_browser_eng_graph_mermaid.md` TC-4
- 改动对象：`scripts/graph-compile.sh` · `.github/workflows/lint-wiki-delta.yml` · `.github/workflows/tech-graph.yml`（只读确认调用链）
- 钉版现状：`package.json` · `.coding-kit/manifest.json` · `pnpm-lock.yaml`（只读）
- 3.0.1 钉法缘由（漂移史）：`scripts/graph-compile.sh:18-22` 注释 + `docs/tasks/active/README.md` 2026-10-11 行（5e07040）

## 给执行帽的必读列表

1. 本 task 全文（含 FP-1 回滚纪律 · FP-5 钉案裁定闸）。
2. `docs/tasks/close/close_specwave_330_graph_update_20261011.md` §「CI 钉版不一致」（禁擅改史实的原始口径）。
3. `scripts/graph-compile.sh` 全文（GRAPH_CLI 回退口语义保留）。
4. `.github/workflows/lint-wiki-delta.yml` + `tech-graph.yml`（调用链与缓存注释）。
5. `docs/harness/prompts/FRAGMENT_30_gate_verify_v1_zh.md`（30 前闸扫描）。

## 思考轮控制

| 轮 | 结论 | early_stop | reason（early_stop） | residual_risks |
|---|---|---|---|---|
| R0 | 框定：仓内 3.3.0 已生效而 CI/脚本闸跑 3.0.1，形状闸（3.2 W1 / 3.3 ast）形同虚设；CLOSE 已建议另立小 task | false | — | 维护者或刻意保留 3.0.1（FP-5） |
| R1 | 证据：亲读 graph-compile.sh:28 / lint-wiki-delta.yml:35,39 / package.json:6 / manifest / tech-graph.yml 调用链；不一致面=恰好两处 + 注释 | false | — | 行号漂移（30 按实校正） |
| R2 | 方案：单行字面钉版 ×2 文件 + 注释补行；不动 GRAPH_CLI 回退口与 workflow 结构 | false | — | CI npx 缓存假绿（FP-4） |
| R3 | 反例：3.3.0 下图谱漂移不混入（FP-2）；目标版本异议回 10（FP-5）；回滚=revert 单 commit（FP-1） | false | — | 存量违规被新闸拦住时的归属裁定 |
| R4 | 验收：TC-1 grep 断言 / TC-2、3 本地绿 / TC-4 CI 绿实证 / TC-5 回滚落盘 / TC-6 diff 白名单 | false | — | 无 |
| R5 | 收口：草稿交 20；闸 pending 待维护者签；禁 30 | true | 改动面极小且唯一 · 证据锚点齐备 · 再轮无新信息 | 见 R0/R3 |

**actual_last_round**：R5（early_stop）

### R0 · 问题框定

钉版分裂：声明面（package/manifest/lock）=3.3.0，执行面（graph-compile 默认 + lint-wiki-delta CI）=3.0.1。后果不是功能红，而是新形状闸不被执行——静默降级。CLOSE 文档已定性为「待维护者确认是否刻意」，本 task 按「确认为遗漏」路径起草，同时留 FP-5 裁定口。

### R1 · 证据收集

2026-10-17 亲读六处：graph-compile.sh（:28 钉 3.0.1 · :18-22 钉法缘由注释）、lint-wiki-delta.yml（:35 执行钉 · :39 注释钉）、package.json:6（3.3.0）、manifest（3.3.0 · from 3.0.1）、tech-graph.yml（:33 调脚本无独立钉）、pnpm-lock（3.3.0 · 转引 TC-4）。其余 spec-wave@3 字面命中均为历史文档（reviews / done tasks / CLOSE），非执行面，不改。

### R2 · 方案生成

最小 diff：两文件钉版字面 3.0.1→3.3.0（共三处：GRAPH_CLI 默认值、CI run 行、CI 注释行），头部注释各补一行对齐记录。GRAPH_CLI 环境变量回退口保留（SPEC §6.2 契约）。

### R3 · 反例与边界

回滚必须一键（revert 钉版 commit）；图谱漂移不借本 task 夹带；「刻意保留 3.0.1」是合法裁定 → 本 task 可整体 won't-do，30 无权拍板目标版本。

### R4 · 验收/可测性

TC-1 纯文本断言；TC-2/TC-3 本地命令输出断言；TC-4 以 CI run 日志版本字面值防 npx 缓存假绿；TC-6 diff 白名单防噪声。

### R5 · 收口

草稿交 20-task-audit；人工闸全 pending 待维护者签；禁 30；未 commit。

### 自检结论（执行者）

**30（2026-10-17）**：钉版对齐完成，本地实证全绿。

- GATE_VERIFY：`npx spec-wave verify --task` PASS（三闸 approved · 维护者授权 00 代录 m00238 照登）。
- 改动：`scripts/graph-compile.sh` GRAPH_CLI 默认值 + `.github/workflows/lint-wiki-delta.yml` :37/:41 共三处 `spec-wave@3.0.1` → `3.3.0`；两文件头部各补 2026-10-17 对齐记录（历史注释原文零改）。
- 实证：TC-1 grep 执行面清零 ✔（历史注释 2 处含 3.0.1 系 S2 明文保留，照登）；TC-2 `./scripts/graph-compile.sh` EXIT=0 · 首行 `[spec-wave@3.3.0]` · 图谱 md 零 diff ✔（graph.json 仅 freeze_id/generated_at 日期漂移，系 graph_yaml_to_json.py:65-69 `datetime.now(UTC)` 所致、与版本无关，已恢复未混入）；TC-3 `LINT-WIKI-DELTA: PASS` ✔；FP-4 防假绿：`npx --yes spec-wave@3.3.0 --version` → `3.3.0` ✔。
- TC-4 CI 实证待 PR（40 核验）；TC-5 revert 预案落 30 invoke + PR 描述；TC-6 diff 白名单内 · 零 `app/` diff · pytest 构造性恒等照登。
- 证据全文：`docs/harness/invokes/by-task/ci-specwave-pin-align/invoke_20261017_30_pin_align.md`。

## 修订记录

| 日期 | 说明 |
|------|------|
| 2026-10-17 | 10-task 初稿落盘（帽 10 · 闸 pending 待维护者签 · 禁 30 · 未 commit） |
| 2026-10-17 | 20 R1 书面审签收（址A · 审查文 docs/harness/reviews/task_ci_specwave_pin_align_audit_R1_20261017.md）· 维护者授权 00 代录三闸 approved（m00238） |
| 2026-10-17 | 30 交付：钉版 3.0.1→3.3.0 两处文件三处字面 + 注释对齐记录 · 本地 TC-1/2/3 绿 · FP-4 版本断言 ✔ · graph.json 日期漂移恢复未混入 · 状态行更新 |
