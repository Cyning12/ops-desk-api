---
hat: 30
task_slug: ci_specwave_pin_align
date: 2026-10-17
---

# invoke · 30 执行 · ci_specwave_pin_align（CI/脚本 spec-wave 钉版对齐 3.3.0 · chore）

## GATE_VERIFY（30 前闸扫描）

| gate | status | blocks_30 | 判定 |
|------|--------|-----------|------|
| HG-TASK-DRAFT | approved | 20, 30 | ✅ |
| HG-AUDIT-R1 | approved | 30 | ✅ |
| HG-GRAPH-MODULES | approved | — | ✅ |

- `npx spec-wave verify --target . --task docs/tasks/active/task_ci_specwave_pin_align.md` → `VERIFY: PASS`（EXIT=0，2026-10-17 亲跑）。
- worktree：ops-desk-api-worktrees/t-ci-pin · 分支 task/ci-specwave-pin-align（未切分支 · 未动其他 worktree）。

## 改动摘要（S1/S2 · 最小 diff）

| 文件 | 改动 |
|------|------|
| `scripts/graph-compile.sh` | :31 GRAPH_CLI 默认值 `spec-wave@3.0.1` → `spec-wave@3.3.0`；头部 2026-10-11 段后补 2026-10-17 对齐记录 3 行（历史注释原文零改） |
| `.github/workflows/lint-wiki-delta.yml` | :37 执行行 + :41 注释行 `spec-wave@3.0.1` → `spec-wave@3.3.0`；头部 2026-09-23 段后补 2026-10-17 对齐记录 2 行（历史注释原文零改） |

## 证据摘录（亲跑 · 2026-10-17）

### TC-1 钉版一致（grep 断言）

```
$ grep -rn "spec-wave@3" scripts/ .github/
scripts/graph-compile.sh:18:# 2026-10-11：GRAPH_CLI 默认值钉 spec-wave@3.0.1（对齐 package.json 与   ← 历史注释（S2 禁改）
scripts/graph-compile.sh:31:GRAPH_CLI="${GRAPH_CLI:-spec-wave@3.3.0}"                                      ← 执行钉
.github/workflows/lint-wiki-delta.yml:4:# 2026-09-23：kit 钉 spec-wave@3.0.1（...）                        ← 历史注释（S2 禁改）
.github/workflows/lint-wiki-delta.yml:37:        run: npx --yes spec-wave@3.3.0 task lint-wiki-delta --target .   ← 执行钉
.github/workflows/lint-wiki-delta.yml:41:      #   run: npx --yes spec-wave@3.3.0 ... --strict                        ← 注释钉
```

- 执行面 3.0.1 字面清零；`spec-wave@3.3.0` 恰现于 GRAPH_CLI 行 + workflow :37/:41 两处。残留两处 `spec-wave@3.0.1` 均为历史钉法缘由注释，S2 明文「不改历史注释原文」，照登。
- `package.json:6` / `.coding-kit/manifest.json` / `pnpm-lock.yaml` 零 diff（git status 核实）。

### TC-2 本地 graph-compile

- FP-4 防假绿前置：`npx --yes spec-wave@3.3.0 --version` → `3.3.0`（EXIT=0）。
- `./scripts/graph-compile.sh` → EXIT=0；输出首行 `[spec-wave@3.3.0] compiling graph yaml -> md (2 dir(s))`；check 全 OK（9 graphs）；normalize guard `[ok] mermaid normalize check: 9 md file(s)`。
- **图谱 md 产出零 diff**（`git status --porcelain docs/_tech_graph/` 仅 graph.json 命中）。
- **graph.json 漂移照登（非 FP-2 md 漂移）**：compile 后 `docs/_tech_graph/shared/graph.json` 仅 `freeze_id`（20261014→20261017）与 `generated_at` 两字段变化——系本仓 `scripts/graph_yaml_to_json.py:65-69` 以 `datetime.now(UTC)` 生成的日期字段，与 spec-wave 版本无关（3.0.1 下同构）。已 `git checkout --` 恢复，零混入本 PR。

### TC-3 本地 lint-wiki-delta

```
$ npx --yes spec-wave@3.3.0 task lint-wiki-delta --target .
目标: .
scope: all · scanned: 171 · strict: false · missing: 0 · issues: 0
LINT-WIKI-DELTA: PASS   （EXIT=0）
```

### TC-4 CI 实证

- 待 PR 上 `tech-graph` / `lint-wiki-delta` workflow 绿 + run 日志版本字面值核验 → 由 40 帽核验钉入 40 invoke。

### TC-5 回滚预案（FP-1）

- 本 PR 钉版 commit 哈希见 PR 描述（commit 后回填）。回滚命令：
  ```
  git revert <pin-commit>   # 单行字面 diff，复原 GRAPH_CLI 默认与 CI npx 钉版回 3.0.1
  git push origin task/ci-specwave-pin-align   # CI 恢复 3.0.1 钉法即复绿
  ```
- 存量违规归属裁定（20 N-1 照登项）：若 3.3.0 新闸拦下存量违规，按 FP-1 先 revert 复绿，再另立适配 task 处理存量。

### TC-6 零越界

- `git status --porcelain` 改动面恰为：`scripts/graph-compile.sh` · `.github/workflows/lint-wiki-delta.yml` · `docs/tasks/active/task_ci_specwave_pin_align.md` · 本 invoke 目录 · R1 审查文（后三件为 task 档维护随附）。
- 零 `app/` diff → pytest/ruff 构造性恒等，照登：无实证（按 test_strategy_note：触及面全绿即可）。

## 偏差与照登

1. TC-1 字面「无 3.0.1」与 S2「不改历史注释原文」存在张力：历史注释 `graph-compile.sh:18` / `lint-wiki-delta.yml:4` 各含一处 `spec-wave@3.0.1`。30 裁定：执行钉版面清零即满足 TC-1 意图，历史注释保留（S2 优先）；新补对齐记录行刻意不含 `spec-wave@3.0.1` 字面以避免扩大 grep 命中面。
2. graph.json freeze_id/generated_at 日期漂移：恢复未混入（见 TC-2）。是否另立 task 让 freeze_id 脱日期化，超本 task 范围，仅照登。
3. pytest 未亲跑：零 `app/` diff，构造性恒等照登（test_strategy_note 许可）。
