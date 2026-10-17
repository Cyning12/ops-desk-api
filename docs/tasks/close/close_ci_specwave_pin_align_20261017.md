# CLOSE：ci-specwave-pin-align（仓卫生 · CI/脚本 spec-wave 钉版对齐 3.3.0 · chore）（2026-10-17）

> **task**：[../done/task_ci_specwave_pin_align.md](../done/task_ci_specwave_pin_align.md)（已归档 done/）
> **类型**：仓卫生 / 工具链钉版对齐（chore · 零 `app/` 改动 · `graph_change_layer=none`）
> **关账日期**：2026-10-17 · 帽位：CLOSE（50 · 三 task 批量关账 · 分支 `close/active-batch-20261017-pm` · 授权链：维护者 2026-10-17 m00238「授权00签收后续文档，开始下面的任务」· 00 代录 · 20 R1 书面审经授权豁免）

---

## 一 · 任务信息

| 项 | 值 |
|----|----|
| task_slug | `ci_specwave_pin_align` |
| 依据 | `docs/tasks/close/close_specwave_330_graph_update_20261011.md` §「CI 钉版不一致」照录 + 后续工作建议第 1 条（「另立小 task 统一升 3.3.0」）· `docs/tasks/done/task_specwave_330_graph_update.md`（PR #242 已合） |
| 背景 | 仓内 2026-10-11 已升 spec-wave **3.3.0**（`package.json:6` / `.coding-kit/manifest.json` / `pnpm-lock.yaml`），但执行面 `scripts/graph-compile.sh` GRAPH_CLI 默认值与 `.github/workflows/lint-wiki-delta.yml` 仍钉 **3.0.1**——**3.2 W1 形状闸（implementedBy object）与 3.3 ast check 在 3.0.1 下不存在**，两处新闸形同虚设（静默降级 · 不拦缺口亦不提示升级） |
| 目标 | 执行面钉版统一 3.3.0（单行字面 diff ×2 文件）+ 注释对齐记录 + 本地/CI 双侧绿实证 + FP-1 回滚预案落盘 |
| 分支 | `task/ci-specwave-pin-align`（worktree `t-ci-pin`） |
| 帽链 | 10-task → 20-task-audit R1 书面审签收（授权豁免 · 址A 落盘）→ 三闸 approved（00 代录 · m00238）→ 30 钉版 + 本地实证（`invoke_20261017_30_pin_align.md`）→ PR #260 → CI 绿实证（TC-4 由本 CLOSE 补录 · 40 轨未走照登）→ **CLOSE（本档）** |

## 二 · 交付

| 环节 | 实证 |
|------|------|
| PR | [#260](https://github.com/Cyning12/ops-desk-api/pull/260) · **MERGED 2026-10-17T05:50:10Z · squash commit `de3c7d7`** |
| 码面 | `scripts/graph-compile.sh`（:31 GRAPH_CLI 默认值 `spec-wave@3.0.1` → `spec-wave@3.3.0` · 头部 2026-10-11 段后补 2026-10-17 对齐记录 3 行 · 历史注释原文零改 · GRAPH_CLI 环境变量回退口保留）· `.github/workflows/lint-wiki-delta.yml`（:37 执行行 + :41 注释行同改 · 头部 2026-09-23 段后补对齐记录 2 行） |
| 本地实证（30） | TC-1 grep 执行面 3.0.1 清零 · TC-2 `./scripts/graph-compile.sh` EXIT=0 · 首行 `[spec-wave@3.3.0] compiling` · 图谱 md 零 diff · TC-3 `LINT-WIKI-DELTA: PASS`（scanned 171 · issues 0）· FP-4 防假绿 `npx --yes spec-wave@3.3.0 --version` → `3.3.0` |
| CI 实证（TC-4 · 本 CLOSE 补录） | PR #260 run 日志实证 **3.3.0 实载**（`npm warn exec … spec-wave@3.3.0` 字面值）· `tech-graph` / `lint-wiki-delta` 两 workflow 绿 |
| 回滚预案（TC-5） | 30 invoke 载 FP-1 回滚命令（`git revert <pin-commit>` 单行字面 diff 复原 3.0.1 · CI 复绿）· 存量违规归属裁定预案在案 |
| invokes | `docs/harness/invokes/by-task/ci-specwave-pin-align/`（10_task_draft / 20_task_audit_r1 / 30_pin_align · 40 缺位照登 · 本批 CLOSE 纪律不另立 50 invoke） |
| 审查文 | 址A `docs/harness/reviews/task_ci_specwave_pin_align_audit_R1_20261017.md`（书面审签收 · 授权豁免） |
| **CLOSE 增量** | task 档归档 done/ · 本档落盘（**本批纪律：仅新增 `docs/tasks/close/close_*.md` · 零 git 操作 · 不改其他任何文件 · 不另立 50 invoke / 址B 复制件**） |

## 三 · 核验结论（验收终态摘要 · TC-1–TC-6 逐项）

| 验收项 | 结果 | 实证 |
|--------|------|------|
| TC-1 钉版一致 | ✅（残留照登） | 执行面 3.0.1 字面清零；`spec-wave@3.3.0` 恰现于 `graph-compile.sh` GRAPH_CLI 行 + `lint-wiki-delta.yml` :37（执行行）/:41（注释行）；`package.json:6` / manifest / pnpm-lock 保持 3.3.0 零 diff。**残留 2 处历史注释保留 3.0.1 字面**（`graph-compile.sh:18` · `lint-wiki-delta.yml:4` · S2 明文「不改历史注释原文」· 30 裁定：执行钉版面清零即满足 TC-1 意图，照登） |
| TC-2 本地 graph-compile | ✅ | EXIT=0 · 输出首行 `[spec-wave@3.3.0] compiling graph yaml -> md (2 dir(s))` · check 全 OK（9 graphs）· mermaid normalize guard OK · **图谱 md 产出零 diff** |
| TC-3 本地 lint-wiki-delta | ✅ | `npx --yes spec-wave@3.3.0 task lint-wiki-delta --target .` → `LINT-WIKI-DELTA: PASS` · EXIT=0（scope: all · scanned: 171 · missing: 0 · issues: 0） |
| TC-4 CI 绿实证 | ✅（本 CLOSE 补录） | PR #260 CI run 日志实证 **3.3.0 实载**（`npm warn exec … spec-wave@3.3.0` 版本字面值核验 · FP-4 防 npx 缓存假绿成立）· `tech-graph` / `lint-wiki-delta` 绿。**40 invoke 缺位照登**：TC-4 原指派 40 核验，40 轨未走，实证由 PR run 日志直接补录入本档 |
| TC-5 回滚预案 | ✅ | FP-1 revert 命令载 30 invoke 与 PR 描述（单行字面 diff 复原 3.0.1） |
| TC-6 零越界 | ✅ | diff 白名单（`scripts/graph-compile.sh` · `lint-wiki-delta.yml` · task/invoke/review 档）· 零 `app/` diff → pytest/ruff 构造性恒等，照登：无实证（test_strategy_note：触及面全绿即可） |

**CLOSE 质量钉复跑（本帽 · 2026-10-17 · 分支 `close/active-batch-20261017-pm` 归档后仓态）**：

- `npx --yes spec-wave verify --target .` → **EXIT=0 · VERIFY: PASS**（裸 verify · 仓级 reviews 扫描 · 4 条存量基线豁免命中留痕：tech-graph-recent-sync / tenant-readonly-predicate / upgrade-harness-2-20-runbook-feedback / wikitrack-enable-p0 · 均 2026-10-11 授权 m01606/m00255 在案）。
- `npx --yes spec-wave task lint --file docs/tasks/done/task_ci_specwave_pin_align.md` → **EXIT=0 · LINT: PASS**。

## 四 · 偏差与 nit（如实照登）

1. **历史注释 2 处保留 `3.0.1` 字面（S2 明文 · 非回归）**：`graph-compile.sh:18` / `lint-wiki-delta.yml:4` 钉法缘由注释原文保留；TC-1 字面「无 3.0.1」与 S2「不改历史注释原文」存在张力，30 裁定执行钉版面清零即满足 TC-1 意图；新补对齐记录行刻意不含 `spec-wave@3.0.1` 字面以避免扩大 grep 命中面。
2. **graph.json 日期漂移另立案照登**：compile 后 `docs/_tech_graph/shared/graph.json` 仅 `freeze_id`（20261014→20261017）与 `generated_at` 两字段变化——系本仓 `scripts/graph_yaml_to_json.py:65-69` 以 `datetime.now(UTC)` 生成的日期字段，与 spec-wave 版本无关（3.0.1 下同构）；已 `git checkout --` 恢复，零混入本 PR。**freeze_id 是否脱日期化另立 task，超本 task 范围，仅照登。**
3. **40 轨未走（TC-4 由 CLOSE 补录）**：task orchestration 原列 40 核验 PR CI；本批交付由 30 → PR 直连，40 invoke 缺位；TC-4 实证（run 日志 3.3.0 字面值）由本 CLOSE 档补录，核验口径与 FP-4 防假绿要求等同（版本字面值断言）。
4. **存量违规归属预案未触发**：20 N-1 照登项——若 3.3.0 新闸拦下存量违规，按 FP-1 先 revert 复绿、再另立适配 task 处理存量；CI 绿实证未触发该路径，预案在案备查。

## 五 · 签录（闸态表与审查文链）

| 闸 / 环节 | 状态 | 文档 / 实证 |
|-----------|------|------------|
| HG-TASK-DRAFT | **approved** | 2026-10-17 维护者授权 00 代录（m00238） |
| HG-AUDIT-R1 | **approved** | 同上（20 R1 书面审经授权豁免） |
| HG-GRAPH-MODULES | **approved** | 同上（全局真值 approved · `docs/_tech_graph/l1/01_modules.md:63` · `graph_change_layer=none`） |
| 20 R1 审查 | **签收（书面审豁免）** | 址A `docs/harness/reviews/task_ci_specwave_pin_align_audit_R1_20261017.md` |
| invokes | — | `by-task/ci-specwave-pin-align/`（10/20/30 · 40 缺位照登） |
| 合并 | **MERGED** | PR [#260](https://github.com/Cyning12/ops-desk-api/pull/260) · squash `de3c7d7` · 2026-10-17T05:50:10Z · CI run 日志 3.3.0 实载 |

## 六 · 资源清理

- **本 CLOSE 不删任何东西**（本批纪律零 git 操作）：分支 `task/ci-specwave-pin-align`（已 squash 合入 master `de3c7d7` · 删除安全 · 远端一并清）、worktree `t-ci-pin`、本批 CLOSE 分支 `close/active-batch-20261017-pm` 移交 00/维护者统一清理（CLOSE PR 未合并前 close 分支在役）。

## 七 · 维护者验收 checklist 与后续建议

### 维护者验收 checklist（00 代录 · 授权链同上 · 需人抽验项）

- [ ] **钉版抽验**：`grep -rn "spec-wave@3" scripts/ .github/` —— 执行面恰三处 3.3.0（graph-compile.sh GRAPH_CLI 行 · lint-wiki-delta.yml :37/:41）；历史注释 2 处 3.0.1 为 S2 明文保留，非漏改。
- [ ] **本地复跑抽验**：`./scripts/graph-compile.sh` 首行含 `[spec-wave@3.3.0]` 且图谱 md 零 diff；`npx --yes spec-wave@3.3.0 task lint-wiki-delta --target .` 输出 `LINT-WIKI-DELTA: PASS`。
- [ ] **CI 实证抽验**：PR #260 run 日志 `npm warn exec … spec-wave@3.3.0` 字面值（FP-4 防假绿口径）。

### 后续建议

1. **graph.json freeze_id 脱日期化（另立案照登）**：`graph_yaml_to_json.py:65-69` `datetime.now(UTC)` 致 freeze_id / generated_at 逐日漂移，是否另立 task 收口由维护者裁定（本 task 非范围已钉）。
2. **3.3+ 新闸启用另立 task**：`graph ast check` 默认开、lint `--strict` 启用等均属本 task 非范围（钉版 ≠ 规则变更），如需启用按另案走 10/20。

## 八 · 修订记录

| 日期 | 说明 |
|------|------|
| 2026-10-17 | CLOSE 落稿（50 close 棒 · 三 task 批量关账 · 分支 `close/active-batch-20261017-pm`）：九节沿仓内先例（close_hitl_resume_async_20261015.md 等）· 验收终态承 30 invoke TC-1/2/3/5/6 实证 + TC-4 由本档补录（PR #260 run 日志 `npm warn exec … spec-wave@3.3.0` 字面值）· 质量钉复跑（verify EXIT=0 PASS · task lint done/ 档 EXIT=0 PASS）· 历史注释 2 处 3.0.1 保留（S2 明文）/ graph.json 日期漂移另立案 / 40 轨缺位如实照登 · 维护者 checklist 00 代录（授权链 m00238） |

## 九 · 附录

### 关键路径

| 类别 | 路径 |
|------|------|
| task（已归档） | `docs/tasks/done/task_ci_specwave_pin_align.md` |
| CLOSE 档 | `docs/tasks/close/close_ci_specwave_pin_align_20261017.md`（本档） |
| 交付码面 | `scripts/graph-compile.sh`（GRAPH_CLI 默认值 3.3.0 + 对齐记录）· `.github/workflows/lint-wiki-delta.yml`（:37 执行行 / :41 注释行 + 对齐记录） |
| 审查文（址A） | `docs/harness/reviews/task_ci_specwave_pin_align_audit_R1_20261017.md` |
| invokes | `docs/harness/invokes/by-task/ci-specwave-pin-align/`（10_task_draft / 20_task_audit_r1 / 30_pin_align） |
| 上游 | `docs/tasks/close/close_specwave_330_graph_update_20261011.md`（§「CI 钉版不一致」）· `docs/tasks/done/task_specwave_330_graph_update.md`（PR #242） |

### CLOSE 复跑命令留痕

```bash
npx --yes spec-wave verify --target . > /tmp/verify_close_batch_pm.log 2>&1; echo "EXIT=$?"   # EXIT=0 · VERIFY: PASS
npx --yes spec-wave task lint --file docs/tasks/done/task_ci_specwave_pin_align.md           # EXIT=0 · LINT: PASS
```
