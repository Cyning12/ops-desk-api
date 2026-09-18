# task_specwave_upgrade_3_0_0 审查（R1 · 20-task-audit）

> **审查对象**：`docs/tasks/active/task_specwave_upgrade_3_0_0.md`（10-task 起草 · spec-wave 2.4.2 → 3.0.0 major 过程轨升级）
> **审查帽**：20-task-audit（书面审查 · 未改 task 实质内容 · 未代签任何 human_gate · 未执行 30）
> **日期**：2026-09-18 · **审查时仓态**：worktree `/Users/cyning/Desktop/Ops-desk/ops-desk-api-specwave-3-0-0` · 分支 `task/specwave-3-0-0`（base `origin/master`）· 本地仍钉 `spec-wave@2.4.2`
> **开窗授权**：`docs/harness/invokes/by-task/specwave-upgrade-3-0-0/invoke_20260918_00_open_specwave-upgrade-3-0-0.md`（维护者授权 00 代签过程文档；本帽仍不代签）
> **结论**：**PASS-WITH-NOTES**（内容零阻塞 · 非阻塞注记 2 项 · 可请维护者/授权 00 签 `HG-AUDIT-R1`）

---

## 结论摘要

| 维度 | 结论 |
|------|------|
| task **内容**可执行 | ✅ **PASS · 零内容阻塞**——范围/非范围闭合、验收 13 条均可机验且基线实证可达、failure_paths 覆盖 sync 冲突 / verify 结论闸 / 误升 schema v2、思考轮 R0–R5 闭合 |
| **流程闸** HG-TASK-DRAFT | `approved`（2026-09-18 · 00 代签 · 见 open invoke）· 内容审查可进行 |
| **流程闸** HG-AUDIT-R1 | `pending`（blocks 30）· 本审查 PASS 后待维护者或授权 00 签 `approved`；本帽禁止代签 |
| lint 复跑 | `node_modules/.bin/spec-wave task lint --file docs/tasks/active/task_specwave_upgrade_3_0_0.md` → **LINT: PASS** exit 0（2026-09-18 本帽复跑 ✓） |
| 上游实证抽查 | 包内 `MIGRATION.md`「2.4.2 → 3.0.0」定稿节与 task 背景表（默认路径零破坏 · schema v2 可选 · bin 同入口）**一致**（解包 `/tmp/sw-300/package` · version=3.0.0） |

本审查文按结论机读口径书写：「结论」起首节 · 通过词落节内 · 实质内容充足 · 无否定共现。

---

## 审查要点逐项核对

### 1. 范围/非范围完备性 ✅

| 核对点 | 结果 |
|--------|------|
| 钉版（范围 A-1） | ✓ `package.json:6` 实证 `"spec-wave": "2.4.2"`；本地 `node_modules` / `--version` = 2.4.2 |
| manifest（范围 A-2） | ✓ `.coding-kit/manifest.json` 实证 `version=2.4.2` · `from_version=2.1.3`；upgrade 后期望 `version=3.0.0` · `from_version=2.4.2` 与 MIGRATION「写新 · from_version=旧号」语义一致 |
| upgrade 行为 | ✓ 包内最短路径：钉 `spec-wave@3.0.0` → `upgrade --yes` → 字面 →（推荐）refresh；**不删** `.cyning-harness/` —— 与范围 A-2、非范围一致 |
| refresh / sync / skills（B-3/4/5） | ✓ local 块锚定 `git diff AGENTS.md CLAUDE.md` 中 `cyning-harness-local`；冲突策略拒 `--force` + F-3/F-4；skills 不入库口径清晰 |
| CI 三处钉版（C-6） | ✓ `.github/workflows/lint-wiki-delta.yml` 实证 L4/L35/L39 三处 `spec-wave@2.4.2`（`rg -c` = 3） |
| tests 钉版（C-7） | ✓ `tests/test_capability_harness_cli.py` 实证 16 行含 `2.4.2`（env/argv/注入段）；验收用 `grep -n '2\.4\.2'` 零命中可达 |
| harness_cli / GRAPH_CLI（C-8） | ✓ `app/ops/capability/harness_cli.py:109` 已是 `spec-wave@{_kit_pin()}`；`scripts/graph-compile.sh:23` 已是 `GRAPH_CLI:-spec-wave` —— 本波仅验收、不改 `app/` 成立 |
| major 非范围 | ✓ 不强制 schema v2 / `host apply`；F-10 锁定误升；与上游「默认路径什么都不用做」对齐 |
| 非范围闭合 | ✓ 历史档字面豁免、DAG/kit 资产边界、不 publish/merge、授权代签边界均显式 |

### 2. 验收可机验性 ✅（13 条 · 无 B-1/B-3 类不可达成缺陷）

| # | 验收 | 可达性实证 |
|---|------|-----------|
| 1 | package/lock 钉 3.0.0 | ✓ 机械可查 |
| 2 | manifest version/from_version | ✓ 期望值写死 |
| 3 | `--version` = 3.0.0 | ✓ |
| 4 | `check` 零 WARN | ✓ |
| 5 | refresh + local 块零变化 | ✓ 锚定具体文件 diff |
| 6 | `HG-GRAPH-MODULES` 保留命中 | ✓ 现行 `30-execute-code.md:42` 有命中 |
| 7 | CI 计数=3 + 旧钉零命中 | ✓ 现行三处 `@2.4.2`；改后计数断言可达 |
| 8 | `spec-wave@{_kit_pin()}` 命中 1 | ✓ 现行 L109 一处 |
| 9 | pytest PASS + tests 无残留 2.4.2 | ✓ grep 面锚定单文件 |
| 10 | GRAPH_CLI + compile exit 0 | ✓ |
| 11 | `verify --task` PASS | ✓ F-5 处置路径明确；本审查文按机读口径书写 |
| 12 | assets/pins 留痕（偏差不挡） | ✓ 非阻塞型措辞明确 |
| 13 | FEEDBACK 落盘 | ✓ |

### 3. failure_paths 覆盖 ✅

| 审查要点 | 落点 | 评价 |
|---|---|---|
| sync 冲本地补丁 | F-3 | ✓ 与范围 B-4、非范围拒 `--force` 三处口径一致 |
| refresh 改 local 块 | F-4 | ✓ |
| verify 结论机读 BLOCKED | F-5（退回 20 · 禁滥用 `--allow-no-review`） | ✓ |
| tests 字面漂移 | F-6（对齐 C-7 · 禁改语义） | ✓ |
| assets/pins 偏差 | F-8 不挡 | ✓ |
| 误升 schema v2 / 破坏性 host apply | F-10 | ✓ major 边界关键闸 |
| CI 合入纪律 | F-9 | ✓ |

### 4. 上游一致性抽查（`/tmp/sw-300/package` · spec-wave@3.0.0）

| task 背景声明 | 实证 |
|---|---|
| 包为 3.0.0 | ✓ `package.json` version=3.0.0 |
| 最短路径：钉版 → upgrade --yes → 字面 → refresh/skills/sync | ✓ 「SpecWave 最短路径（现行）」步骤 1–4 一致；skills/sync 为推荐刷写，task 收编为必做属加严、可执行 |
| 「2.4.2 → 3.0.0」默认路径零破坏 | ✓ 节标题定稿；①「什么都不用做」：内置宿主行为不变；旧格式表（无 `schema_version`）按 v1 继续可读 |
| schema v2 可选 | ✓ ② 自定义表作者欲用新能力时加 `schema_version: 2` + 根级 `command_sets` 等 |
| 本仓不强制自定义表 / host apply | ✓ 与 MIGRATION 默认路径及非范围/F-10 一致 |
| bin 同入口 | ✓ `bin`: `spec-wave` / `specgate` / `dsh-coding-kit` 同入口；安装终点仍 `spec-wave` |

### 5. 元信息 / 闸表 / 思考轮 / lint ✅

| 核对点 | 结果 |
|--------|------|
| 前置 task | ✓ `docs/tasks/done/task_specwave_upgrade_2_4_2.md` 存在；依赖链接正确 |
| 生产字段 | ✓ `graph_change_layer=none` · `review_hat=20` · `required_invoke_hats=30` · `close_pr_policy=required` 等齐全 |
| 闸表分列 | ✓ HG-TASK-DRAFT=`approved`；HG-AUDIT-R1=`pending`（blocks 30）——内容审查与流程签闸分离正确 |
| 思考轮 | ✓ R0–R5 闭合；early_stop 理由 + residual_risks 三条具体；「20 不足 → 退回 10」回路在案 |
| 自检 lint | ✓ task 自检表已填 LINT: PASS；本帽复跑一致 |
| 行为变更旧测面 | ✓ 本波为过程轨钉版升级（`code_quality_bar=not_applicable`）；tests 字面面已由验收 #9 锚定，无需另列产品语义旧测项 |

---

## 非阻塞注记（2 项 · 不挡签闸）

- **N-1 · 背景表措辞压缩**：增量表「什么都不用做于自定义适配表」把 MIGRATION ① 的「内置宿主行为不变」与「旧格式自定义表零改动继续可读」压成一句；裁定（本仓不强制升 v2）正确。建议 30 以包内 `MIGRATION.md` 该节全文为准，无需改 task 即可执行。
- **N-2 · skills/sync 加严为必做**：上游最短路径将 refresh 列为推荐步 4；task 将 refresh/sync/skills 收编为范围 B 必做，属本仓加严，与目标「跑通推荐刷写」一致，可接受。

---

## 维护者签闸（20 后 · 30 前）

- [ ] 已读 R1 审查结论（PASS-WITH-NOTES · 非阻塞注记 2 项）
- [ ] 在 task 人工闸表将 HG-AUDIT-R1 改为 approved（维护者或开窗授权之 00 代签 · 日期）
- [ ] commit task 文档或确认已签
- [ ] 再下发 Harness 30 Prompt

30 Agent 将以 task 表为准；pending 时必须拒开工（见 TEMPLATE_30_gate_stop.md）。
