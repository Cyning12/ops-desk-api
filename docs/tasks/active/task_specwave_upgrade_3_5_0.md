# Task：specwave-upgrade-3-5-0（spec-wave 3.3.0→3.5.0 工具链升级 · chore）

> **状态**：`in_progress`（2026-10-30 · 维护者令「更新specwave」· 升级类精简形态）
> **类型**：仓级 chore（工具链钉版升级 · 零业务码改动）
> **分支**：`task/specwave-upgrade-3-5-0`（base = master `0a5d610`）
> **先例**：`docs/tasks/done/task_specwave_330_graph_update.md`（PR #242）· `docs/tasks/done/task_ci_specwave_pin_align.md`（PR #260）

## Harness 元信息

| 字段 | 值 |
|------|-----|
| **task_slug** | `specwave-upgrade-3-5-0` |
| **git_branch** | `task/specwave-upgrade-3-5-0` |
| **implement_repo** | `ops-desk-api` |
| **test_strategy** | `recommended` |
| **test_strategy_note** | 纯工具链钉版面：以 spec-wave 3.5.0 闸命令红绿 + 钉版字面 grep 为验收；预期零 `app/` diff 故 pytest 构造性恒等（触及面 tests/test_capability_harness_cli.py 必跑全绿） |
| **code_quality_bar** | `not_applicable`（零业务码改动；若意外触及 py 文件则 ruff 钉版 .venv/bin/ruff 0.15.21 必跑） |
| **graph_change_layer** | `none` |
| **review_hat** | `20`（升级类精简形态 · 双闸 00 代录 approved · 授权锚 m00236） |
| **graph_delta** | `none` |
| **graph_delta_note** | 本 task 不改图谱源档；3.5.0 compile 若产生既有 md 漂移（日期噪声除外）不混入本 task，另立案 |
| **wiki_delta** | `none` |
| **wiki_delta_note** | 工具链钉版升级无 WikiTrack 文档面变更；FEEDBACK 落 `docs/spec/doc-health/feedback/`（非 coding_wiki 面） |
| **experience_capture** | `recommended` |
| **required_invoke_hats** | `30` |
| **invoke_retention_profile** | `minimal`（升级类精简形态 · 维护者授权 m00236） |
| **kpi_rubric** | `KPI_RUBRIC_v1_2` |
| **kpi_aggregator** | `CLOSE` |
| **close_pr_policy** | `exempt` |
| **close_pr_exempt_note** | 维护者令 2026-10-30：全程本地，允许本地 commit，严禁 push / 开 PR；关账仅本地归档，分支移交维护者裁决 |

### 人工闸

| human_gate_id | status | blocks_hats | 说明 |
|---------------|--------|-------------|------|
| HG-TASK-DRAFT | approved | 22-R1, 30 | 2026-10-30 · 00 代录 · 维护者长期授权锚 m00236「授权00签收后续文档」· 升级类精简 task |
| HG-AUDIT-R1 | approved | 30 | 2026-10-30 · 00 代录 · 维护者长期授权锚 m00236 · 升级类 task 精简形态维护者已授权 |
| HG-GRAPH-MODULES | n/a | — | 图谱零改动（graph_change_layer=none） |
| HG-PILOT-OPSDESK-GLAYER | n/a | — | 无外部试点面 |

## 1. 背景与目标

- 维护者令（2026-10-30）：「更新specwave」——npm 最新版 `spec-wave@3.5.0`（2026-10-21 发布），仓内钉 3.3.0。
- 3.4.0 行为变化：**review-gates 址B 双址扫描**（审查文命名 `YYYYMMDD_<slug>_r<n>.md` · 址A/址B 跨址合并排序）。
- 3.5.0 行为变化：**图谱锚点引用检查（graph_anchor）**——条件触发：`.coding-kit/profile.json` 或 legacy `.cyning-harness/profile.json` 声明 `graph_modules_path` 且路径可达才真判定；本仓 legacy profile 声明 `l1/01_modules`（相对仓根不可达）→ 预实证 `graph_path_unreachable` → verify 输出一行 INFO + skipped，**exit 不变不挡**；另新增豁免旗 `--allow-no-graph-anchor`。
- 两版均 minor，无强制迁移。

## 2. 目标

仓内 spec-wave 全量钉位 3.3.0 → 3.5.0（声明面 + 执行面 + 双 lock）；`npx spec-wave@3.5.0 upgrade --target . --yes` 同步 manifest；3.5.0 下全部仓级闸绿；新闸/行为变化逐条实证照登。

## 3. 范围

- [ ] S1 `package.json:6` `"spec-wave": "3.3.0"` → `"3.5.0"`（精确钉）
- [ ] S2 `package-lock.json` 同步（npm install 重生成）
- [ ] S3 `pnpm-lock.yaml` 同步（pnpm install --lockfile-only；两 lock 并存须都更新）
- [ ] S4 `npx spec-wave@3.5.0 upgrade --target . --yes` → `.coding-kit/manifest.json` 3.3.0 → 3.5.0（legacy `.cyning-harness/` 只读不删）
- [ ] S5 `scripts/graph-compile.sh:31` GRAPH_CLI 默认值 `spec-wave@3.3.0` → `spec-wave@3.5.0` + 头部补 2026-10-30 对齐记录（历史注释原文零改 · GRAPH_CLI 环境变量回退口保留）
- [ ] S6 `.github/workflows/lint-wiki-delta.yml` :37 执行行 + :41 注释行 `spec-wave@3.3.0` → `spec-wave@3.5.0` + 头部补对齐记录（历史注释原文零改）
- [ ] S7 `app/ops/capability/harness_cli.py` `_kit_pin()`：读码确认钉版出处——**env `DSH_CODING_KIT_VERSION` 单源，无硬编码默认值 → 零改动**（结论入自检结论）
- [ ] S8 `tests/test_capability_harness_cli.py:170/:201/:222` 断言 `"spec-wave@3.0.1"`：读测试确认——**env 注入样例断言（monkeypatch.setenv 3.0.1），非默认值断言 → 零改动**（结论入自检结论）
- [ ] S9 FEEDBACK 档 `docs/spec/doc-health/feedback/2026-10-30_3.5.0_ops-desk-api_upgrade.md`（起点 3.3.0 → 终点 3.5.0 · 钉位清单 · 新闸/行为变化实证 · 异常与处置）

## 非范围

- ❌ `app/` 业务码任何改动（S7 实证零改动为预期结论）
- ❌ `.cyning-harness/profile.json` 的 `graph_modules_path` 修正（`l1/01_modules` 相对仓根不可达 → graph_anchor 检查 skip；是否改指 `docs/_tech_graph/l1/01_modules.md` 待维护者裁决另案，本 task 照登不擅改）
- ❌ 历史留痕目录（docs/tasks、docs/harness/reviews、docs/harness/invokes/by-task、docs/audits、reports 等）内 3.3.0/旧钉版字面
- ❌ spec-wave 上游本体改动；push / PR（维护者令：全程本地）
- ❌ 全量 pytest（26 枚环境性旧红在案；仅 tests/test_capability_harness_cli.py 必跑）

## 失败路径

| 触发条件 | 系统行为 | 可重试 | 用户可见 |
|----------|----------|--------|----------|
| upgrade 向导写脏工作树致 S5 误判 | task 档已先 commit（本流程 S0） | 是 | git status 核查后重跑 |
| 3.5.0 graph_anchor 意外 BLOCK 存量 task | 预实证 unreachable→skip 不挡；若意外：`--allow-no-graph-anchor` 照登 + 另立案 | 是 | verify 输出 INFO/BLOCKED 照登 |
| 3.4.0 review-gates 址B 双址扫描影响仓级 verify | 抽跑实证；存量 reviews 缺口按扩列纪律处置，不顺手改存量 | 是 | verify 输出照登 |
| 3.5.0 compile 产出图谱 md 漂移 | 复原不混入本 task，另立案（FP-2 先例） | 是 | git diff 图谱面零越界 |
| lock 重生成引入非 spec-wave 变动 | 仅接受 spec-wave 条目 diff；其他复原 | 是 | git diff lock 面审 |
| 维护者裁定目标版本 ≠ 3.5.0 | STOP 回 10 改钉案；30 无权拍板 | 是 | task 返工 |

## 验收标准

- [ ] V1 `npx --yes spec-wave@3.5.0 check --target .` → manifest 3.5.0 · 「已是最新」无升级提示
- [ ] V2 `npx --yes spec-wave@3.5.0 task lint --file docs/tasks/active/task_specwave_upgrade_3_5_0.md` → LINT: PASS · EXIT=0（3.3.0 下 draft lint PASS 先行实证 · 升级后 3.5.0 复跑）
- [ ] V3 `npx --yes spec-wave@3.5.0 verify --target . --task docs/tasks/active/task_lg_rag_gate_produces_unfulfilled.md`（现存 active task 抽跑）→ 结果照登（闸 pending 则 BLOCKED 属预期语义）
- [ ] V4 `./scripts/graph-compile.sh` → EXIT=0 · 首行 `[spec-wave@3.5.0]` · 图谱 md 零 diff（日期噪声复原）
- [ ] V5 `.venv/bin/pytest tests/test_capability_harness_cli.py -q` → 全绿（harness_cli 相关测试文件必须全绿）
- [ ] V6 grep 钉版一致：`grep -rn "spec-wave@3\.3\.0\|\"spec-wave\": \"3\.3\.0\"" package.json scripts/ .github/ .coding-kit/` → 执行面/声明面 3.3.0 清零（历史注释按 S2 保留照登）
- [ ] V7 `npx --yes spec-wave@3.5.0 task lint-wiki-delta --target .` → LINT-WIKI-DELTA: PASS（与 PR CI `.github/workflows/lint-wiki-delta.yml:37` 钉版逐字一致）
- [ ] V8 FP 防假绿：`npx --yes spec-wave@3.5.0 --version` → `3.5.0`

## 给执行帽的必读列表

1. `AGENTS.md`（分支纪律 · 图谱闸路径）
2. `docs/tasks/done/task_specwave_330_graph_update.md` + `docs/tasks/done/task_ci_specwave_pin_align.md`（升级/钉版先例）
3. spec-wave 3.5.0 包真值：`MIGRATION.md`（3.4.0/3.5.0 行为变化）· `lib/checks/graph-anchor.js`（条件触发契约）· `lib/cli/verify.js:489+`（挂点）
4. web 仓 RUNBOOK 参考：`../ops-desk-web/docs/runbooks/RUNBOOK_harness_upgrade_v1_zh.md` §0 精简形态

## 测试策略（Harness）

**test_strategy**: `recommended` —— 工具链/钉版面以闸命令红绿 + grep 字面为证；预期零代码 diff（`app/` 与 `tests/` 均不动），pytest 构造性恒等；tests/test_capability_harness_cli.py 全绿为触及面兜底闸。

---

### 自检结论（执行者）

（30 回填 · draft 期占位合法）

---

### KPI（00）

（`kpi_aggregator: CLOSE` · 关账回溯填写）

---

### 经验总结

（`experience_capture: recommended` · 关账回填）

---

## 修订记录

| 日期 | 说明 |
|------|------|
| 2026-10-30 | 10 落稿（维护者令「更新specwave」· 升级类精简形态：invoke_retention_profile=minimal · required_invoke_hats=30 · graph_delta/wiki_delta=none+note）；双闸 pending 待 00 代录（授权锚 m00236） |
| 2026-10-30 | 双闸代录 approved（HG-TASK-DRAFT/HG-AUDIT-R1 · 00 代录 · 授权锚 m00236）；按 3.3.0 升级先例扩列 legacy-gate-exempt.yaml 豁免条目（四字段齐 · 无 R1 审查文照登 · 本升级分支 commit 链即人审面） |
