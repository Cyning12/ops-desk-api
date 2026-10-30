# Task：api-graph-anchor-profile-fix（legacy profile graph_modules_path 不可达修正 · chore）

> **状态**：`draft`（2026-10-30 · 10 落稿 v0.1 · 双闸 pending 待维护者签收 · 拒开工）
> **类型**：仓级 chore（配置单行修正 + 生效实测 + 回归 · 零业务码改动）
> **分支**：`task/api-graph-anchor-profile-fix`（维护者签收后新建）
> **先例**：`docs/tasks/done/task_specwave_upgrade_3_5_0.md`（升级类精简形态 · 遗留②即本 task）；实证锚 `docs/spec/doc-health/feedback/2026-10-30_3.5.0_ops-desk-api_upgrade.md` §2/§6.2

## Harness 元信息

| 字段 | 值 |
|------|-----|
| **task_slug** | `api-graph-anchor-profile-fix` |
| **git_branch** | `task/api-graph-anchor-profile-fix` |
| **implement_repo** | `ops-desk-api` |
| **test_strategy** | `recommended` |
| **test_strategy_note** | 配置单行修正面：以 spec-wave 3.5.0 verify 输出逐字对照 + 目录可达性断言为验收；零 app/ diff 故 pytest 构造性恒等 |
| **code_quality_bar** | `not_applicable`（零业务码改动） |
| **graph_change_layer** | `none` |
| **graph_delta** | `none` |
| **graph_delta_note** | 本 task 只改 profile 指针不改图谱源档；01_struct.md 词表面适配属图谱面新增，另案（见非范围） |
| **wiki_delta** | `none` |
| **wiki_delta_note** | 无 WikiTrack 文档面变更；处置差距照登落本 task 自检结论 |
| **review_hat** | `20`（维护者 2026-10-30 新原则：升级/流程类一律走 20-R1 审查文 · 禁 --allow-no-review） |
| **required_invoke_hats** | `30` |
| **invoke_retention_profile** | `minimal`（工具类零业务面 · 承 task_specwave_upgrade_3_5_0 精简形态先例 · 维护者签收时可裁升 default） |
| **close_pr_policy** | `required`（承仓默认任务分支 + PR 纪律 · 若维护者另令全程本地则改 exempt 并补 exempt_note） |

### 人工闸

| human_gate_id | status | blocks_hats | 说明 |
|---------------|--------|-------------|------|
| HG-TASK-DRAFT | approved | 22-R1, 30 | 2026-10-30 · 10 落稿 v0.1 · 2026-10-30 维护者签收（00 代录 · 授权锚 m00500） |
| HG-AUDIT-R1 | pending | 30 | 待 20-R1 审查文落盘 docs/harness/reviews/ + 维护者签收（新原则 · 禁 --allow-no-review · 20-R1 通过后 00 代录 · 授权锚 m00500） |
| HG-GRAPH-MODULES | n/a | — | 图谱源档零改动（graph_change_layer=none · 仅 profile 指针） |
| HG-PILOT-OPSDESK-GLAYER | n/a | — | 无外部试点面 |

## 1. 背景与目标

- spec-wave 3.5.0 新增 graph_anchor 图谱锚点引用检查（条件触发）：profile 声明 `graph_modules_path` 且解析为**可达目录**才真判定（挂点 node_modules spec-wave lib/cli/verify.js:498+ · 探测 lib/checks/graph-anchor.js probeGraphAnchor）。
- 本仓 legacy `.cyning-harness/profile.json` 声明 `graph_modules_path: "l1/01_modules"`——相对仓根不可达（仓根无 `l1/`）→ probe 恒 `graph_path_unreachable` → verify 输出 INFO 一行 + skipped · exit 不变不挡（升级 task 实证在案 · FEEDBACK §2）。
- **起草期读码修正 FEEDBACK 推测**（graph-anchor.js:30-40）：probe 判可达用 `statSync(graphPath).isDirectory()`——目标必须是**目录**。FEEDBACK §2:22 推测「改指 docs/_tech_graph/l1/01_modules.md」不成立（文件路径仍 unreachable · §6 第 2 项仅回指 §2，推测出处在 §2:22）。正确修正值：`docs/_tech_graph/l1`（目录在案 · 含 01_modules.md 与 10_flow_* 图谱对）。
- **修正后行为预断**（读码 graph-anchor.js：节 RE :43 · extractGraphAnchorModuleVocab :54-57 · 节匹配 :59-61 · judgeGraphAnchor 本体 :214）：judgeGraphAnchor 词表抽取要求 `<dir>/01_struct.md` 含「## 1. 模块边界表」节；本仓 l1/ 无 01_struct.md（模块真值在 01_modules.md「## 模块表（必填）」节）→ `skipped: vocabulary_empty` 仍不挡。即本 task 交付的是「路径不可达 skip → 词表空 skip」的诚实毕业；真判定所需词表面适配另案裁决。
- 目标：profile 指向可达目录 + 生效实测逐字照登 + 存量 task verify 零新增缺口回归。

## 2. 范围

- [ ] S1 `.cyning-harness/profile.json` 的 `graph_modules_path`：`"l1/01_modules"` → `"docs/_tech_graph/l1"`（就地改 legacy profile · 其余字段零改；**不**新建 .coding-kit/profile.json——resolveLayoutFile 读序 .coding-kit 优先于 legacy，新建引入双层 profile 遮蔽面，单源就地改为最小面）
- [ ] S2 生效实测：`npx spec-wave@3.5.0 verify --target . --task <本 task>`（HG-AUDIT-R1 approved + R1 审查文落盘后跑）——输出零 `graph_path_unreachable`；graph_anchor 实际判定（预期 `skipped: vocabulary_empty` 或 enabled 路径真判定结果）逐字照登自检结论
- [ ] S3 存量 task verify 回归：抽跑现存 active task `docs/tasks/active/task_lg_rag_gate_produces_unfulfilled.md` + ≥1 done 档（建议 `docs/tasks/done/task_specwave_upgrade_3_5_0.md`），与修正前输出对照——EXIT 与缺口集合零新增，graph_anchor 相关行差异照登
- [ ] S4 词表面适配差距照登（不实施）：自检结论记录「vocabulary_empty → 真判定」所需适配面（上游契约 `01_struct.md` + 「## 1. 模块边界表」节 + 首列反引号词表 · 本仓真值 01_modules.md「## 模块表（必填）」节 · 双真值风险），供维护者裁决另案

## 3. 非范围

- ❌ 新增 `docs/_tech_graph/l1/01_struct.md` 或改 `docs/_tech_graph/` 任何图谱源档（图谱面新增须 HG-GRAPH-MODULES 闸 · 另案）
- ❌ 新建 `.coding-kit/profile.json` · 删/迁 legacy `.cyning-harness/` 其他内容
- ❌ 存量 task 文 / invoke / reviews 补图谱锚点引用（若 graph_anchor 真判定后存量新红 → 另案 · 不顺手改存量）
- ❌ `--allow-no-graph-anchor` 常规化（仅失败路径临时处置 · waived 留痕）
- ❌ web 仓同题处置（另仓另案 · 互引见「关联」）

## 4. 失败路径（failure_paths）

| 触发条件 | 系统行为 | 可重试 | 用户可见 |
|----------|----------|--------|----------|
| profile JSON 写坏 | probe 报 invalid_json · warn + skip（verify.js:500-502）· exit 不挡但生效失败 | 是 · git checkout 复原重改 | verify warn 照登 · V1 拦 |
| 值误写为文件路径（01_modules.md） | isDirectory()=false → 仍 graph_path_unreachable | 是 · 改目录值重跑 | V2 拦（输出仍含 unreachable） |
| 修正后存量 task 被 graph_anchor 真判定新 BLOCKED（面A/面B 缺锚点） | STOP 回维护者裁决；本 task 不修存量；临时 `--allow-no-graph-anchor` 须 waived 留痕 + 另案 | 是 | verify BLOCKED 点名面A/面B 照登 |
| vocabulary_empty 被误读为「检查已真生效」 | 验收 V2 要求 skipped 原因逐字照登 · 不得措辞拔高 | — | 自检结论措辞审 |
| 顺手建 01_struct.md 补齐词表 | 越图谱面（HG-GRAPH-MODULES 未过）→ 拒 · 回非范围 | — | git diff 图谱面零越界复核 |
| 任意修正后异常需整体回退（通用回退口） | profile 单行 `git checkout` 复原即复归 unreachable skip 原态（对照 web D4 双 profile 一行 revert 先例）· 复原后再行裁决 | 是 | git diff + verify 输出照登 |

## 验收标准（§5）

- [ ] V1 profile 合法且可达：`node -e "const p=require('./.cyning-harness/profile.json');if(p.graph_modules_path!=='docs/_tech_graph/l1')process.exit(1)"` EXIT=0 · 且 `node -e "if(!require('fs').statSync('docs/_tech_graph/l1').isDirectory())process.exit(1)"` EXIT=0
- [ ] V2 `npx spec-wave@3.5.0 verify --target . --task docs/tasks/active/task_api_graph_anchor_profile_fix.md`（闸 approved 后）→ 输出零 `graph_path_unreachable` · graph_anchor 行逐字照登自检
- [ ] V3 回归对照：active task + ≥1 done 档 verify 修正前后 EXIT 与缺口集合零新增（差异行照登）
- [ ] V4 仓级 `npx spec-wave@3.5.0 verify --target .` → reviews 缺口集合恰为既有 5 枚基线（task_api_legacy_reviews_backfill 清零前口径）· 无新增缺口类别 · EXIT=2 照登不掩饰
- [ ] V5 `./scripts/graph-compile.sh` EXIT=0 · 图谱 md 零 diff（禁管道截断取真码 · 承 FEEDBACK §1 SIGPIPE 教训）
- [ ] V6 `npx spec-wave@3.5.0 task lint --file docs/tasks/active/task_api_graph_anchor_profile_fix.md` → LINT: PASS EXIT=0
- [ ] V7 git diff 面 = `.cyning-harness/profile.json` 单行值变更 + 本 task 文/invoke/reviews 留痕 · 零其他

## 6. 给执行帽的必读列表

1. `AGENTS.md`（分支纪律 · 仓内定制块）
2. `docs/tasks/done/task_specwave_upgrade_3_5_0.md`（升级先例 · 遗留②出处）+ `docs/spec/doc-health/feedback/2026-10-30_3.5.0_ops-desk-api_upgrade.md` §2（graph_anchor 实证链）
3. spec-wave 3.5.0 包真值：`lib/checks/graph-anchor.js`（probe/judge 契约）· `lib/cli/verify.js:487-535`（挂点与输出契约）
4. `docs/_tech_graph/l1/01_modules.md`（HG-GRAPH-MODULES 真值 · 本 task 只读）

## 7. 关联

- `docs/tasks/active/task_api_prompts_sync_3_5_0.md`：sync 物化的 FRAGMENT_graph_first_read_v1_zh 生效条件即本 task 修正的 profile 可达目录——两件合并后图谱先读片段方具生效前提（帽条文接入仍属 prompts conflict 人工合并裁决面）。
- `docs/tasks/active/task_api_legacy_reviews_backfill.md`：本 task 执行纪律受其仓规条款约束（升级/流程类禁 --allow-no-review）；仓级 verify 缺口基线互为对照（本 task V4 以 5 缺口为基线 · 清零后口径随其闭环更新）。
- web 仓同题 task（另仓立案 · 另案推进 · 互不惊动）。

> 注（R1 审查 NIT-5 照登）：上述两件关联 task 档在本分支不存在（各在 sibling 分支 task/api-prompts-sync-3-5-0 / task/api-legacy-reviews-backfill 在制 · 未合入 master），本分支视角引用悬空；分支合并后自解。

## 8. 测试策略（Harness）

**test_strategy**: `recommended` —— 配置单行修正面以 verify 输出逐字对照 + 目录可达性 node 断言为证；预期零 `app/` / `tests/` diff，pytest 构造性恒等不强制。

## 思考轮控制（R0–R5）

| 轮 | 结论 | early_stop | reason（early_stop） | residual_risks |
|----|------|------------|----------------------|----------------|
| R0 | 问题框定：profile 路径不可达 → graph_anchor 恒 skip · 交付=可达修正+实测+回归 | no | — | none |
| R1 | 路径契约读码：isDirectory 判定 → 修正值须为目录 docs/_tech_graph/l1（FEEDBACK 文件路径推测不成立） | no | — | none |
| R2 | 修正后行为预断：01_struct.md 缺 → vocabulary_empty skip 仍不挡 · 诚实毕业不拔高 | no | — | 真判定需词表面适配另案 |
| R3 | 范围收敛：单行配置 + 实测 + 回归 · 图谱面/存量锚点/双 profile 全部入非范围 | no | — | none |
| R4 | 闸与粒度：单 task 直通 · 双闸 pending · 新原则走 20-R1 禁豁免旗 | yes | R0–R3 已闭环路径契约/行为预断/范围边界 · 无残余分叉 | 词表适配另案照登 |
| R5 | （未开） | — | early_stop at R4 | — |

**actual_last_round**：R4 · **early_stop**：yes · **residual_risks**：见 R2

### R0 · 问题框定

legacy profile `graph_modules_path: l1/01_modules` 相对仓根不可达 → 3.5.0 graph_anchor 恒 `graph_path_unreachable` skip。本 task 交付：指向可达目录 + 生效实测 + 存量回归，三件套不多不少。

### R1 · 路径契约读码

graph-anchor.js:33 `statSync(graphPath).isDirectory()`——可达性判定只认目录。FEEDBACK §6.2 推测的文件路径值不成立；修正值 `docs/_tech_graph/l1`（目录在案 · 模块表与 flow 图谱同层）。同时定夺不新建 .coding-kit/profile.json（读序优先权会遮蔽 legacy · 双层 profile 是新风险面）。

### R2 · 修正后行为预断

enabled 后 judgeGraphAnchor 词表抽取要 `01_struct.md`「## 1. 模块边界表」节——本仓缺 → `skipped: vocabulary_empty`。验收口径据此钉死：「不再 unreachable + skipped 原因逐字照登」，禁措辞拔高为「检查已生效」。

### R3 · 范围收敛

单行 profile 修正 + S2/S3 实测回归 + S4 差距照登。图谱面新增（01_struct.md）、存量锚点补齐、双层 profile 全部非范围——每条对应一个失败路径防越界。

### R4 · 闸与粒度

单 task 直通；双闸 pending 待维护者签收；承维护者 2026-10-30 新原则走 20-R1 审查文、禁 --allow-no-review（与 task_api_legacy_reviews_backfill 条款一互引）。early_stop at R4。

### R5 ·（未开 · early_stop）

---

### 自检结论（执行者）

（draft 期占位 · close 前由执行帽回填：S1–S4 逐项 + V1–V7 矩阵 + graph_anchor 输出逐字照登 + 词表适配差距记录）

---

## 修订记录

| 日期 | 说明 |
|------|------|
| 2026-10-30 | v0.1 · 10 落稿：升级 task 遗留②立案（legacy profile graph_modules_path 不可达）；读码修正 FEEDBACK 文件路径推测（isDirectory → 目录值 docs/_tech_graph/l1）；双闸 pending 待维护者签收（不代录）；新原则走 20-R1 禁 --allow-no-review |
| 2026-10-30 | v0.2 · 闸代录：HG-TASK-DRAFT pending→approved（00 代录 · 授权锚 m00500 · 维护者令启动后续 task）；HG-AUDIT-R1 等其余闸保持 pending 不动 |
| 2026-10-30 | v0.3 · 10 回填：R1 审查通过零阻塞（docs/harness/reviews/task_api_graph_anchor_profile_fix_audit_R1_20261030.md）· NIT-1~5 全采纳（NIT-1 行号引用勘误：节 RE :43 · 节匹配 :59-61 · judgeGraphAnchor :214 · :54-57=extractGraphAnchorModuleVocab · NIT-2 FEEDBACK 推测改引 §2:22 · NIT-3 验收标准补 §5 编号（lint E3 须「## 验收标准」字面起首 → 落「## 验收标准（§5）」）· NIT-4 failure_paths 补通用回退口「profile 单行 git checkout 复原」对照 web D4 · NIT-5 §7 跨分支悬空照登）· 闸表 HG-AUDIT-R1 行字面校正（20-R1 通过后 00 代录 · 授权锚 m00500） |
