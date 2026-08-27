# FEEDBACK · dsh-coding-kit 1.8.0 · from ops-desk-api（升级 + agent-host K1–K7 修复核对）

> **日期**：2026-08-27  
> **业务仓**：`ops-desk-api`（分支 `task/dsh-coding-kit-1-8-0`）  
> **起点**：manifest `1.7.1` → 目标 `dsh-coding-kit@1.8.0`  
> **对照**：`/tmp/kit-171/package` vs `/tmp/kit-180/package`（`npm pack`）  
> **上游 FEEDBACK**：[`FEEDBACK_agent_host_plan_ci_20260827.md`](./FEEDBACK_agent_host_plan_ci_20260827.md) §3 **K1–K7**  
> **执行**：本窗 · 过程轨升级；未改 `app/`；prompts 自包内 `assets/harness/prompts/` 手同步（upgrade 仍只写 manifest）

---

## 1. 结论（验收）

| 项 | 结果 |
|----|------|
| manifest | **1.8.0**（`from_version=1.7.1` · preset/ide 保留） |
| AGENTS/CLAUDE local 块 | **零改写**（upgrade 不触 IDE 块；refresh dry-run rewrites=0） |
| upgrade 幂等 | **PASS**（二跑 `1.8.0→1.8.0`） |
| prompts 落地 | **手同步**（`00/10-task/20-task-audit/40/FRAGMENT_30_invoke/README` + `templates/TASK_TEMPLATE.md`） |
| CI 钉版本 | `.github/workflows/lint-wiki-delta.yml` → `@1.8.0` |
| severity=block | **无** |
| **K1–K7** | **全部落地**（见 §3；K3 为显式旗标、非 preset 默认） |

**判定**：1.7.1→1.8.0 minor 在本仓成立；agent-host-plan CI FEEDBACK 的 **K1–K7 均已在 1.8.0 产品面修复**（实证 + 包内注释直接标注 K1–K7）。残余摩擦仍是 **upgrade 不 sync prompts**（沿用 1.7.1 FEEDBACK）。

---

## 2. CLI 面探查（1.8.0 对照 1.7.1）

顶层 help 增量（非破坏）：

```diff
-  npx dsh-coding-kit verify [--target PATH] [--task FILE | --spec FILE] [--json]
+  npx dsh-coding-kit verify [...] [--with-wiki-lint]
+  task lint-wiki-delta 诊断码说明含 wiki_delta_wrong_section
+  task close --json（done_snapshot）
+  task lint --file 增 E8 wiki_delta 存在性
```

| 子命令 | 1.7.1 → 1.8.0 | 破坏性？ |
|---|---|---|
| verify | `--with-wiki-lint`（opt-in） | 否 |
| lint-wiki-delta | `wiki_delta_wrong_section` | 否（诊断增强） |
| task lint | E8 缺 `wiki_delta` 行 → FAIL | 否（加严；与 close 对齐） |
| task close | `--json` + `done_snapshot` 打印 | 否 |
| upgrade / check / refresh | 行为同前（upgrade 仍只写 manifest） | 否 |

lib 变更集中：`cli-checks.js` · `cli-task-extra.js` · `cli-shared.js` · `cli.js`；prompts/templates/00/20/40 资产同步改。

---

## 3. FEEDBACK K1–K7 修复核对（实证）

| ID | 原建议 | 1.8.0 状态 | 证据 |
|----|--------|-----------|------|
| **K1** | `wiki_delta_wrong_section` 替代误报 missing | **已修** | 探针：`## Harness` + wiki_delta 行 → `wiki_delta_wrong_section · 须在 ## Harness 元信息`；`cli-task-extra.js` 注释「K1」 |
| **K2** | `task lint` 起草拦缺 wiki_delta | **已修** | 探针：`task lint --file` → `[E8] 缺 wiki_delta 行`；`cli-checks.js` 注释「E8（K2）」 |
| **K3** | `verify --with-wiki-lint` | **已修（opt-in）** | README + help；dogfood：闸绿后扫到兄弟 task missing → BLOCKED + 打印 CI 同命令；**preset 默认开启未做**（包注释：独立决策点） |
| **K4** | 00 bulk-split 后必跑 lint-wiki-delta | **已修（条文）** | `00-orchestrator.md` 默认行为表新增行；`10-task-requirements.md` 批量拆义务 + `--scope` 取舍 |
| **K5** | close 成功打印 done 元信息快照 | **已修** | `task close --yes` 后 stdout `done_snapshot · harness_meta_section`；`--json` 含 `done_snapshot`；禁手写 done 提示 |
| **K6** | 40 / 模板默认全量 CI + lint-wiki-delta | **已修（条文）** | `40-self-check.md`「补齐全量命令」；`TASK_TEMPLATE.md` 验收默认两行 |
| **K7** | 20 审「旧测 grep 影响面」 | **已修（checklist · 非机械闸）** | `20-task-audit.md` + skill；明确不进 `task lint` |

### 3.1 K1 探针命令与输出

```text
npx dsh-coding-kit@1.8.0 task lint-wiki-delta --target <tmpdir>
→ … · wiki_delta_wrong_section · wiki_delta 行写在「## Harness」节 L5 · 须在 `## Harness 元信息` 表格内
LINT-WIKI-DELTA: FAIL · issues 1
```

（对照 agent-host #72：1.7.x 同类文件报 `wiki_delta_missing` → **误报已消除**。）

### 3.2 K3 探针注意

- `--with-wiki-lint` 挂在 **既有硬闸之后**（R1 / pre-30 invoke 等先过才扫 wiki）。  
- `HG-AUDIT-R1 pending` 时 **不会**跑到 wiki_lint（早退）——与「显式旗标、非默认」一致。  
- BLOCKED 时打印：`复跑（与 PR CI 同命令）: npx --yes dsh-coding-kit task lint-wiki-delta --target .`（**未钉 @version**；本仓 CI 钉 `@1.8.0`，文案略有漂移 → 记 **P3**）。

---

## 4. 本仓落地动作

| # | 动作 | 状态 |
|---|------|------|
| U1 | `upgrade --yes` 1.7.1→1.8.0 | **done** |
| U2 | 自包 `cp` 变更 prompts + `TASK_TEMPLATE.md` | **done** |
| U3 | CI `lint-wiki-delta.yml` 钉 `@1.8.0` | **done** |
| U4 | 回写本 FEEDBACK；agent-host FEEDBACK §3 状态表 | **done** |
| L1–L4 | agent-host 本仓执行纪律（全量 pytest 等） | **仍待**（产品侧 K 已修，仓侧采纳另议） |

---

## 5. 剩余缺口与 severity

| ID | 现象 | severity | 说明 |
|----|------|----------|------|
| R-prompt-sync | `upgrade` 仍不复制 `assets/harness/prompts/` | **P2**（沿用 1.7.1） | 本波再次手 `cp`；建议 `sync prompts` 或 upgrade 写入新增/变更提示 |
| R-rerun-pin | verify wiki BLOCKED 复跑命令无 `@1.8.0` | **P3** | 与本仓 CI 钉版本不完全逐字；功能无碍 |
| R-preset-wiki | `--with-wiki-lint` 非 preset 默认 | **info** | 产品有意；本仓可在 AGENTS local / 40 Prompt 写「PR 前加旗标」 |
| — | 根级裸 SPEC WARN ×8 | info | 历史债；非本波 |

**K1–K7：无未修项。**

---

## 6. 环境与命令实录

| # | 命令 | exit | 说明 |
|---|------|------|------|
| 1 | `npx dsh-coding-kit@1.8.0 check --target .` | 0 | 可升级 1.7.1→1.8.0 |
| 2 | `refresh-ide-blocks --dry-run` | 0 | rewrites=0 · 跳过 local |
| 3 | `upgrade --target . --yes` | 0 | manifest 1.8.0 · from=1.7.1 |
| 4 | `upgrade` 二跑 | 0 | 幂等 |
| 5 | K1/K2/K3 探针 | 见 §3 | 行为符合预期 |
| 6 | `cp` kit prompts → `docs/harness/prompts/` | — | upgrade 未写入 |
| 7 | 钉 CI `@1.8.0` | — | lint-wiki-delta.yml |

---

## 7. 修订记录

| 日期 | 说明 |
|------|------|
| 2026-08-27 | 初稿：1.8.0 升级 + agent-host K1–K7 全量核对 |
