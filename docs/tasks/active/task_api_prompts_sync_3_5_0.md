# Task：api-prompts-sync-3-5-0（spec-wave 3.5.0 包内 prompts 同步 · chore）

> **状态**：`in_progress`（2026-10-30 · 30 执行完毕 · S1–S5 / V1–V7 全绿 · 双闸 approved · 待维护者关账裁决）
> **类型**：仓级 chore（harness prompts 同步 · 零业务码改动 · 本地定制零覆盖）
> **分支**：`task/api-prompts-sync-3-5-0`（维护者签收后新建）
> **先例**：web 仓 commit e70a2b0（2026-10-30 · spec-wave 3.3.0→3.5.0 + sync prompts · conflict 9 全部本地保留零 --force · FRAGMENT_graph_first_read_v1_zh.md 新增）；出处 `docs/spec/doc-health/feedback/2026-10-30_3.5.0_ops-desk-api_upgrade.md` §6.1（升级 task 遗留①）

## Harness 元信息

| 字段 | 值 |
|------|-----|
| **task_slug** | `api-prompts-sync-3-5-0` |
| **git_branch** | `task/api-prompts-sync-3-5-0` |
| **implement_repo** | `ops-desk-api` |
| **test_strategy** | `recommended` |
| **test_strategy_note** | 文档资产同步面：以 dry-run/apply 输出逐字照登 + conflict 文件 sha256 前后不变 + graph-compile/lint 回归为验收；零 app/ diff 故 pytest 构造性恒等 |
| **code_quality_bar** | `not_applicable`（零业务码改动） |
| **graph_change_layer** | `none` |
| **graph_delta** | `none` |
| **graph_delta_note** | 本 task 不动图谱源档；FRAGMENT_graph_first_read 物化≠图谱变更 |
| **wiki_delta** | `none` |
| **wiki_delta_note** | prompts 面同步无 WikiTrack 文档面变更；conflict 审阅结论与 web 对照落本 task 自检结论 |
| **review_hat** | `20`（维护者 2026-10-30 新原则：升级/流程类一律走 20-R1 审查文 · 禁 --allow-no-review） |
| **required_invoke_hats** | `30` |
| **invoke_retention_profile** | `minimal`（工具类零业务面 · 承 task_specwave_upgrade_3_5_0 精简形态先例 · 维护者签收时可裁升 default） |
| **close_pr_policy** | `required`（承仓默认任务分支 + PR 纪律 · 若维护者另令全程本地则改 exempt 并补 exempt_note） |

### 人工闸

| human_gate_id | status | blocks_hats | 说明 |
|---------------|--------|-------------|------|
| HG-TASK-DRAFT | approved | 22-R1, 30 | 2026-10-30 · 10 落稿 v0.1 · 2026-10-30 维护者签收（00 代录 · 授权锚 m00500） |
| HG-AUDIT-R1 | approved | 30 | 2026-10-30 · 00 代录 · 授权锚 m00500 · R1 审查文 docs/harness/reviews/task_api_prompts_sync_3_5_0_audit_R1_20261030.md 通过零阻塞（新原则 · 禁 --allow-no-review） |
| HG-GRAPH-MODULES | n/a | — | 图谱源档零改动（graph_change_layer=none） |
| HG-PILOT-OPSDESK-GLAYER | n/a | — | 无外部试点面 |

## 1. 背景与目标

- 2026-10-30 升级 task（`docs/tasks/done/task_specwave_upgrade_3_5_0.md`）遗留①：upgrade 向导提示 manifest 已升级但 prompts 未自动同步（含 `FRAGMENT_hat_reanchor` / `FRAGMENT_00_delegate_only` / 新增 `FRAGMENT_graph_first_read_v1_zh.md`）——`sync prompts` 是否执行待维护者裁决另案，本 task 即该另案。
- sync 语义读码钉案（node_modules spec-wave lib/cli-sync-prompts.js）：白名单 12 prompts + TASK_TEMPLATE.md（:6-21）；dry-run 默认零写入；`--yes` 只写 add 项；**conflict 默认不覆盖 · 仅 --force 覆盖**（:114-115）；apply 后仍有 conflict → EXIT=1 提示「存在 conflict 文件未覆盖」（:156-157，**照登项非失败**）。
- **起草期 dry-run 实测基线**（2026-10-30 · `npx spec-wave@3.5.0 sync prompts --target .` EXIT=0）：skip 4（40-self-check / FRAGMENT_30_gate_verify / FRAGMENT_hat_reanchor / TEMPLATE_30_gate_stop）· **add 1（FRAGMENT_graph_first_read_v1_zh.md）** · **conflict 8**（00-orchestrator / 10-task-requirements / 10-spec-requirements / 20-task-audit / 20-spec-audit / 30-execute-code / FRAGMENT_00_delegate_only / templates/TASK_TEMPLATE.md）。
- 目标：sync 执行 + conflict 逐枚 diff 审阅（仓内本地定制段保留不覆盖）+ graph/lint 回归，全程零 --force（承 web e70a2b0 处置先例）。

## 2. 范围

- [ ] S1 dry-run 复跑照登：`npx spec-wave@3.5.0 sync prompts --target .`（零写入）——skip/add/conflict 三类计数与清单与起草基线对照，漂移逐字照登
- [ ] S2 conflict 8 逐枚 diff 审阅：包内 `assets/harness/prompts|templates` 对照仓内 `docs/harness/...`——逐枚判定差异性质（仓内定制 / 上游实质新增遮蔽 · R1 审查实证：仓内 prompts 零 cyning-harness-local 块 · conflict 8 中 7 枚差异为上游新增「图谱先读」条款被本地旧版遮蔽，执行帽应预期走 failure_paths 第 2 行人工合并路径）；若判出「上游实质新增被本地旧版遮蔽」→ 人工合并入本地定制块（仍零 --force），合并清单与 diff 逐枚照登自检
- [ ] S3 apply：`npx spec-wave@3.5.0 sync prompts --target . --yes`（**零 --force**）→ add 1 物化 `docs/harness/prompts/FRAGMENT_graph_first_read_v1_zh.md`；apply 后 EXIT=1（conflict 未覆盖提示）为预期语义照登
- [ ] S4 回归：`./scripts/graph-compile.sh` EXIT=0 图谱零 diff；`task lint` 本 task PASS；`verify --task docs/tasks/active/task_lg_rag_gate_produces_unfulfilled.md` 抽跑与同步前输出对照（prompts 面改动不应改变 verify 行为 · 差异照登）
- [ ] S5 生效面与 web 对照照登：web e70a2b0 conflict 9 vs 本仓 conflict 8 差异入自检；FRAGMENT_graph_first_read 生效前提照登——该片段条件触发于 profile `graph_modules_path` 可达目录（task_api_graph_anchor_profile_fix 修正面），且本地帽条文（conflict 保留）未引用该片段，**物化 ≠ 接入帽条文**如实记自检

## 3. 非范围

- ❌ `--force` 任何形式使用（含单文件 · 维护者裁定某 conflict 应采上游版时亦手工对齐后重跑 dry-run 转 skip，不走 --force）
- ❌ 改 conflict 8 枚内容（S2 判出实质新增的人工合并除外 · 合并亦保留本地定制段）
- ❌ 白名单外本地附加件（`docs/harness/prompts/FRAGMENT_30_invoke_block_v1_zh.md` / `DAG.md` / `README.md`）任何改动
- ❌ AGENTS.md / CLAUDE.md 的 cyning-harness 块与 IDE skills 拷贝同步（非 sync prompts 面 · 另案）
- ❌ profile `graph_modules_path` 修正（task_api_graph_anchor_profile_fix 地盘）
- ❌ web 仓 prompts 面（e70a2b0 已闭环 · 仅作对照先例）

## 4. 失败路径（failure_paths）

| 触发条件 | 系统行为 | 可重试 | 用户可见 |
|----------|----------|--------|----------|
| apply 后 EXIT=1 | 语义 = conflict 未覆盖提示（cli-sync-prompts.js:156-157）· add 项已写入 · 非失败 | 是 · 照登即过 | 自检结论如实记 EXIT=1 预期语义 |
| S2 判出上游实质新增（如帽条文引用新片段/新闸口径） | 人工合并入本地定制段 · 禁 --force · 合并 diff 逐枚照登 | 是 | S2 结论表 + git diff |
| dry-run 基线漂移（包版本/本地变动致计数 ≠ skip4/add1/conflict8） | 以执行期实测为准照登 · 与起草基线差异入自检 | 是 | dry-run 输出逐字照登 |
| sync 写入越白名单面 | sync 只写白名单 add 项（读码钉案）；git diff 白名单外零越界复核 · 越界即复原 | 是 | git diff 审 |
| FRAGMENT_graph_first_read 被误读为「图谱先读已生效」 | 生效前提 = profile 可达目录（task 1）+ 帽条文引用（conflict 人工合并面）· 本 task 只物化 · S5 照登 | — | 自检措辞审 |

## 验收标准（§5）

- [ ] V1 dry-run 输出逐字照登（skip/add/conflict 三类计数与清单 · 与起草基线对照差异说明）
- [ ] V2 conflict 8 逐枚 diff 结论落自检结论（每枚一行：差异性质 = 仓内定制保留 / 实质新增+人工合并处置）
- [ ] V3 apply 后 `docs/harness/prompts/FRAGMENT_graph_first_read_v1_zh.md` 存在且与包内 `assets/harness/prompts/` 同名件 sha256 一致；apply EXIT=1（conflict 提示）照登
- [ ] V4 conflict 8 枚 apply 前后 sha256 逐枚不变（零 --force 实证 · 或 S2 人工合并枚照登 diff 与其余枚 sha256 不变）
- [ ] V5 `./scripts/graph-compile.sh` EXIT=0 · 图谱 md 零 diff（禁管道截断取真码 · 承 FEEDBACK §1 SIGPIPE 教训）
- [ ] V6 `npx spec-wave@3.5.0 task lint --file docs/tasks/active/task_api_prompts_sync_3_5_0.md` → LINT: PASS EXIT=0
- [ ] V7 `verify --task` 抽跑对照零行为变化照登；git diff 面 = add 1 +（如有）S2 人工合并项 + 本 task 文/invoke/reviews 留痕 · 零其他

## 6. 给执行帽的必读列表

1. `AGENTS.md`（分支纪律 · 仓内定制块）
2. `docs/spec/doc-health/feedback/2026-10-30_3.5.0_ops-desk-api_upgrade.md` §6.1（本 task 出处）+ `docs/tasks/done/task_specwave_upgrade_3_5_0.md`（升级先例）
3. web 仓 commit e70a2b0（处置先例：conflict 全保留零 --force · 新 fragment 物化）
4. spec-wave 3.5.0 包真值：`lib/cli-sync-prompts.js`（白名单/冲突语义/EXIT=1 语义）· `assets/harness/prompts/FRAGMENT_graph_first_read_v1_zh.md`（新增片段全文 · 生效条件伪代码）

## 7. 关联

- `docs/tasks/active/task_api_graph_anchor_profile_fix.md`：FRAGMENT_graph_first_read 生效条件（profile 可达目录）即其修正面——两件合并后图谱先读片段方具生效前提。
- `docs/tasks/active/task_api_legacy_reviews_backfill.md`：本 task 执行纪律受其仓规条款约束（升级/流程类禁 --allow-no-review）。

> 注（R1 审查 N3 照登）：上述两件关联 task 档在本分支不存在（各在 sibling 分支 task/api-graph-anchor-profile-fix / task/api-legacy-reviews-backfill 在制 · 未合入 master），本分支视角引用悬空；双分支合并后自解。

## 8. 测试策略（Harness）

**test_strategy**: `recommended` —— 文档资产同步面以 sync 输出逐字照登 + sha256 对照 + graph-compile/lint 回归为证；预期零 `app/` / `tests/` diff，pytest 构造性恒等不强制。

## 思考轮控制（R0–R5）

| 轮 | 结论 | early_stop | reason（early_stop） | residual_risks |
|----|------|------------|----------------------|----------------|
| R0 | 问题框定：升级遗留① sync prompts 未执行 · 交付=同步+审阅+回归 | no | — | none |
| R1 | sync 语义读码：白名单 12+1 · --yes 只写 add · conflict 默认不覆盖 · apply 后 EXIT=1 为提示非失败 | no | — | none |
| R2 | 处置原则：承 web e70a2b0 —— conflict 全保留零 --force · 实质新增走人工合并 | no | — | S2 判出实质新增的概率存在（合并面照登兜底） |
| R3 | 生效面辨析：物化 ≠ 接入（profile 前提在 task 1 · 帽条文引用在 conflict 合并面）· 措辞禁拔高 | no | — | none |
| R4 | 闸与粒度：单 task 直通 · 双闸 pending · 新原则走 20-R1 禁豁免旗 | yes | R0–R3 已闭环语义/原则/生效面 · 无残余未兜住分叉（R2 残余风险=S2 判出实质新增概率 · 已被 S2 分支/failure_paths 机制兜住照登） | 见 R2 |
| R5 | （未开） | — | early_stop at R4 | — |

**actual_last_round**：R4 · **early_stop**：yes · **residual_risks**：见 R2

### R0 · 问题框定

升级向导提示 prompts 未同步（FEEDBACK §6.1 遗留①）。本 task 交付：sync prompts 执行 + conflict diff 审阅 + 回归，三件套。

### R1 · sync 语义读码

cli-sync-prompts.js：白名单 12 prompts + TASK_TEMPLATE.md；dry-run 零写入；`--yes` 只写 add；conflict 仅 --force 覆盖；apply 后残留 conflict → EXIT=1 提示。起草期 dry-run 基线 skip4/add1/conflict8 已实测钉案。

### R2 · conflict 处置原则

承 web e70a2b0：conflict 全部本地保留、零 --force。本仓 conflict 8 枚预期均为仓内定制（cyning-harness-local 块 · 仓路径钉）；若审阅判出上游实质新增，人工合并入本地定制段而非覆盖。

### R3 · 生效面辨析

新增 FRAGMENT_graph_first_read 的生效条件（片段自带伪代码）：profile 声明 graph_modules_path 且可达目录。本仓前提在 task_api_graph_anchor_profile_fix；且本地帽条文为 conflict 保留版、未引用该片段——「物化 ≠ 接入」必须在自检照登，禁措辞拔高。

### R4 · 闸与粒度

单 task 直通；双闸 pending 待维护者签收；承新原则走 20-R1 审查文、禁 --allow-no-review。early_stop at R4。

### R5 ·（未开 · early_stop）

---

### 自检结论（执行者）

**30 执行回填 · 2026-10-30 · invoke：`docs/harness/invokes/by-task/api-prompts-sync-3-5-0/invoke_20261030_30_execute.md`（minimal）· 实现 commit c6bb1c3**

#### S1 dry-run 复跑（照登）

`npx spec-wave@3.5.0 sync prompts --target .` → EXIT=0 · **skip 4**（40-self-check / FRAGMENT_30_gate_verify / FRAGMENT_hat_reanchor / TEMPLATE_30_gate_stop）· **add 1**（FRAGMENT_graph_first_read_v1_zh.md）· **conflict 8**（00-orchestrator / 10-task-requirements / 10-spec-requirements / 20-task-audit / 20-spec-audit / 30-execute-code / FRAGMENT_00_delegate_only / templates/TASK_TEMPLATE.md）——与起草基线**逐字一致 · 零漂移**。

#### S2 conflict 8 逐枚处置台账

| # | 文件 | 差异性质 | 处置 | 合并条款 |
|---|------|----------|------|----------|
| 1 | prompts/00-orchestrator.md | 上游实质新增被本地旧版遮蔽 | 合并（与上游零 diff） | 「图谱先读」条件条款：profile graph_modules_path 可达 → 派发前确认任务书含图谱先读条款 |
| 2 | prompts/10-task-requirements.md | 同上 | 合并（与上游零 diff） | 图谱先读：task 必读列表含图谱入口 · 涉 01_struct 模块标注图谱锚点 |
| 3 | prompts/10-spec-requirements.md | 同上 | 合并（与上游零 diff） | 图谱先读：SPEC 必读列表含图谱入口 · 涉 01_struct 模块标注图谱锚点 |
| 4 | prompts/20-task-audit.md | 同上 | 合并（与上游零 diff） | 图谱先读：核对图谱锚点引用真实性（grep 级）· 缺引用退回 10 |
| 5 | prompts/20-spec-audit.md | 同上（2 hunk：只做什么 + 输出形状） | 合并（与上游零 diff） | 图谱锚点核对条款 + 输出形状核对表括注「另核图谱锚点引用」 |
| 6 | prompts/30-execute-code.md | 同上（上游将 `_tech_graph/` 硬编码条件化） | **合并 = 保留本地 `_tech_graph/` + 吸收上游条件条款并存**（本仓图谱实体目录 · 与包内仍存 1 行差异 · 复跑 dry-run 唯一残留 conflict · 明示保留） | 图谱先读：profile 可达时开工必读另含图谱入口 |
| 7 | prompts/FRAGMENT_00_delegate_only_v1_zh.md | 同上（+第 4 条 +「图谱先读（必备 · 条件触发）」整节） | 合并（与上游零 diff） | 委派任务书必含图谱先读条款 · 禁止留空占位符派发 |
| 8 | templates/TASK_TEMPLATE.md | 上游实质新增（非图谱条款）：闸表格式说明 | 合并（与上游零 diff） | 「闸表须 4 列 · id 单元格内不要用粗体」说明行 |

仓内零 cyning-harness-local 块（与 R1 审查实证一致）· 全程零 --force。

#### S3 apply（照登）

`sync prompts --target . --yes`（零 --force）→ **EXIT=1**（conflict 1 未覆盖提示 · cli-sync-prompts.js:156-157 预期语义 · 照登项非失败）· written 1 = `docs/harness/prompts/FRAGMENT_graph_first_read_v1_zh.md` · skip 11（S2 合并 7 枚已转 skip）。

#### S4 回归

- `./scripts/graph-compile.sh` → **EXIT=0** · 9 graphs / 142 nodes / 207 edges · check 全 OK · `git status docs/_tech_graph/` 零 diff
- `task lint --file docs/tasks/active/task_api_prompts_sync_3_5_0.md` → **LINT: PASS · EXIT=0**（v0.5 回填后复跑仍 PASS）
- `verify --task docs/tasks/active/task_lg_rag_gate_produces_unfulfilled.md` 抽跑：同步前（stash 法取基线）与同步后输出**逐字一致**（VERIFY: BLOCKED · HG-AUDIT-R1 pending · EXIT=2）· 零行为变化

#### S5 生效面与 web 对照（照登）

- **web 对照**：web e70a2b0 conflict 9 **全部本地保留**（零合并）；本仓 conflict 8 **全部人工合并**（7 枚对齐上游零 diff + 1 枚保留 `_tech_graph/`）· 差异根因：本仓 R1 实证 conflict 差异全为上游实质新增遮蔽、本地零定制块，故走合并路径；处置路线不同但纪律同（零 --force）。
- **物化 ≠ 接入**：FRAGMENT_graph_first_read 生效前提 = profile `graph_modules_path` 可达目录（task_api_graph_anchor_profile_fix 修正面 · 本仓当前 `graph_path_unreachable` · verify INFO skipped 照登）+ 帽条文引用（本 task 已完成合并面）；物化不等于图谱先读已生效，措辞禁拔高。

#### V1–V7 验收矩阵

| 项 | 结论 | 实证 |
|----|------|------|
| V1 dry-run 照登 | ✅ | skip4/add1/conflict8 与基线零漂移（S1） |
| V2 conflict 8 逐枚结论 | ✅ | S2 台账（8 枚全「实质新增+人工合并」） |
| V3 fragment sha256 | ✅ | `3739570a6a40b2f41110a061e1dfdb0864bd596db3371c67569584da29f3f565` 两侧一致；apply EXIT=1 照登 |
| V4 sha256 前后 | ✅ | conflict 8 枚 post-merge 与 post-apply sha256 逐枚不变（apply 零越写；30-execute-code `9c33ac9d…f71f` 系合并保留版） |
| V5 graph-compile | ✅ | EXIT=0 · 图谱 md 零 diff |
| V6 task lint | ✅ | LINT: PASS · EXIT=0 |
| V7 verify 对照 + diff 面 | ✅ | verify 前后逐字一致；git diff 面 = add 1 + S2 合并 8 枚 + 本 task 文/invoke · 零其他（维护者脏文件 site-data.json 全程未动） |

**复跑收敛证据**：apply 后 dry-run → skip 12 / add 0 / conflict 1（30-execute-code · 明示保留 `_tech_graph/`）· EXIT=0。

---

### 验收结论（40 独立验收）

**40 独立验收回填 · 2026-10-30 · invoke：`docs/harness/invokes/by-task/api-prompts-sync-3-5-0/invoke_20261030_40_acceptance.md`（minimal）· 对象：c6bb1c3 + ec1f774（基线 2b6d2c0）· 不信 30 自报逐项亲跑**

**结论：PASS**（建议维护者关账裁决）

| 验收项 | 40 亲跑实证 |
|--------|-------------|
| ① diff 面与量 | c6bb1c3 = 9 文件 +50/-2（prompts 8 + templates/TASK_TEMPLATE 1 · 全在白名单面内）· ec1f774 = task 文 + 30 invoke · 全量 diff 亲读 · 零 app/ 零其他 |
| ② conflict 8 台账 | 实抽全 8 枚（超 ≥3）：7 枚合并件与 node_modules/spec-wave@3.5.0 包内资产逐一 diff **全 ZERO-DIFF**；30-execute-code 恰 1 行差异——本地 `_tech_graph/` 读序项存续 + 上游条件条款并存（残留 conflict 系有意保留 · 属实） |
| ③ V1–V7 复跑 | dry-run 复跑 skip 12 / add 0 / conflict 1 · EXIT=0；FRAGMENT sha256 `3739570a…f565` 两侧一致；白名单外零 diff；graph-compile EXIT=0 图谱零 diff；task lint PASS EXIT=0；存量 verify worktree 基线法（2b6d2c0 vs HEAD）输出逐字一致（双侧 VERIFY: BLOCKED · HG-AUDIT-R1 pending · EXIT=2）；本 task verify PASS EXIT=0（INFO graph_path_unreachable 与 S5 照登一致） |
| ④ 条款质量 | FRAGMENT 生效条件与各帽「条件触发」措辞语义连贯；00/10/20/30 义务一一对应；相对链接目标存在；零虚构图谱指引 |
| ⑤ 30 落账 | invoke minimal 在盘 · 自检与亲跑逐项吻合无拔高 · v0.5 一致 · 遗留四条（残留 conflict 1 / 物化≠接入 / web 对照差异根因 / 跨分支引用悬空）照登合理且均经实证 |

零 --force 内容级佐证：30-execute-code 本地项存续（--force 必灭失）+ 7 枚对齐上游零 diff。维护者脏文件 `docs/arch-browser/dist/site-data.json` 全程未动。

---

## 修订记录

| 日期 | 说明 |
|------|------|
| 2026-10-30 | v0.1 · 10 落稿：升级 task 遗留①立案（sync prompts 未执行）；起草期 dry-run 基线实测（skip4/add1/conflict8）；承 web e70a2b0 零 --force 先例；双闸 pending 待维护者签收（不代录）；新原则走 20-R1 禁 --allow-no-review |
| 2026-10-30 | v0.2 · 闸代录：HG-TASK-DRAFT pending→approved（00 代录 · 授权锚 m00500 · 维护者令启动后续 task）；HG-AUDIT-R1 等其余闸保持 pending 不动 |
| 2026-10-30 | v0.3 · 10 回填：R1 审查通过零阻塞（docs/harness/reviews/task_api_prompts_sync_3_5_0_audit_R1_20261030.md）· NIT N1–N4 全采纳（N1 S2 首句改中性「逐枚判定差异性质」+ 实证照登 · N2 验收标准补 §5 编号（lint E3 须「## 验收标准」字面起首 → 落「## 验收标准（§5）」）· N3 §7 跨分支悬空照登 · N4 R4 early_stop 与 R2 措辞张力调和）· 闸表 HG-AUDIT-R1 行字面校正（20-R1 通过后 00 代录 · 授权锚 m00500） |
| 2026-10-30 | v0.4 · 闸代录：HG-AUDIT-R1 pending→approved（00 代录 · 授权锚 m00500 · R1 审查文 task_api_prompts_sync_3_5_0_audit_R1_20261030.md 通过零阻塞）· 审查文随本提交入库 |
| 2026-10-30 | v0.6 · 40 独立验收：**PASS**（逐项亲跑 · 不信自报）——diff 面 9+2 文件零越界；conflict 8 台账全枚亲核（7 枚与上游零 diff · 30-execute-code 残留系有意保留 `_tech_graph/`）；V1–V7 复跑全绿（dry-run 收敛 skip12/add0/conflict1 · sha256 一致 · graph-compile/lint/verify 全过 · 存量 verify worktree 基线对照逐字一致）；40 invoke minimal 落盘 · 待维护者关账裁决 |
| 2026-10-30 | v0.5 · 30 执行回填：S1–S5 / V1–V7 全绿（实现 commit c6bb1c3 · 30 invoke minimal 落盘）· conflict 8 全部人工合并（7 枚对齐上游零 diff · 30-execute-code 保留 `_tech_graph/` 为唯一残留 conflict 明示保留项）· FRAGMENT_graph_first_read_v1_zh 物化（物化≠接入照登）· 状态 draft→in_progress 待维护者关账裁决 |
