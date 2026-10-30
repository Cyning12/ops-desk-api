# 审查文：task_api_prompts_sync_3_5_0 · 20-task-audit R1（2026-10-30）

> **审查帽**：20-task-audit（R1 · 维护者新原则首单：全走审查零豁免 · 禁 --allow-no-review）
> **对象**：分支 `task/api-prompts-sync-3-5-0` · `docs/tasks/active/task_api_prompts_sync_3_5_0.md`（v0.2 · 145 行）
> **方式**：书面审查 · 钉案逐条独立复核（读码/复跑实证 · 不转述）· 不改 task 实质内容 · 闸一律不动 · 本文留 untracked 不 commit

## 结论摘要

| 维度 | 结论 |
|------|------|
| **内容** | **通过**（零内容阻塞 · 4 项 NIT 见下） |
| **流程闸 HG-AUDIT-R1** | **pending**（未动 · 待维护者签 task 表 → approved） |
| task lint | PASS · EXIT=0（审后复跑） |
| verify | BLOCKED · HG-AUDIT-R1 pending · EXIT=2（**预期态**，30 拒开工正确） |

## 钉案独立复核（实证记录）

### ① dry-run 实测基线（skip 4 / add 1 / conflict 8）——属实

独立复跑 `npx spec-wave@3.5.0 sync prompts --target .`（CLI 无 `--dry-run` 旗标，默认即 dry-run；用法行 cli-sync-prompts.js:22-26 实证「默认 dry-run（零写入）」）：

- skip (4)：40-self-check / FRAGMENT_30_gate_verify / FRAGMENT_hat_reanchor / TEMPLATE_30_gate_stop
- add (1)：docs/harness/prompts/FRAGMENT_graph_first_read_v1_zh.md
- conflict (8)：00-orchestrator / 10-task-requirements / 10-spec-requirements / 20-task-audit / 20-spec-audit / 30-execute-code / FRAGMENT_00_delegate_only / templates/TASK_TEMPLATE.md

三类计数与清单**逐项**与 task §1（:41）声称一致，EXIT=0 一致。

### ② apply 后 EXIT=1 语义（:156-157）——属实，确为提示非失败

读码 `node_modules/spec-wave/lib/cli-sync-prompts.js`（包版 3.5.0）：

- :113-115 `const toWrite = [...plan.add]; if (opts.force) toWrite.push(...plan.conflict);` —— `--yes` 只写 add，conflict 仅 `--force` 覆盖（task 引 :114-115，行差 1 行内属实）
- :116-121 写入循环在 fail 之前完成 —— add 项已物化
- :156-157 `if (!result.dryRun && result.conflict.length > 0 && !force) fail('存在 conflict 文件未覆盖（加 --force 显式覆盖，或人工合并后重跑）', 1);` —— EXIT=1 仅触发于 apply 且残留 conflict 且无 --force，**语义为照登提示非失败**，task failure_paths 第 1 行表述准确
- 白名单 :6-21 = 12 prompts + TASK_TEMPLATE.md，与 task §1（:40）一致

### ③ 本地定制段零覆盖保障——机制落在验收标准（V4 + 非范围 + failure_paths），但 S2 预设方向与实证相反（NIT-N1）

保障机制核对：V4「conflict 8 枚 apply 前后 sha256 逐枚不变（零 --force 实证）」+ §3 非范围「❌ --force 任何形式使用」+ failure_paths 第 4 行「git diff 白名单外零越界复核」——零覆盖保障**已落在可机断验收标准**，闭合。

但执行面实证（本审查逐枚 diff 抽查 8 枚 conflict 全部）：

1. 仓内 `docs/harness/prompts/` 与 `templates/` **零 `cyning-harness-local` 块**（grep 零命中；该块仅存于 AGENTS.md/CLAUDE.md，task §3 已正确列为另案非范围）
2. conflict 8 的实际差异主方向是**上游 3.5.0 新增「图谱先读」条件触发条款被本地旧版遮蔽**——8 枚中 7 枚差异均围绕 `FRAGMENT_graph_first_read_v1_zh.md` 引用（00-orchestrator 派发条款 / 10-task / 10-spec 必读与锚点条款 / 20-task-audit / 20-spec-audit 锚点核对条款 / 30-execute-code 开工必读条款 / FRAGMENT_00_delegate_only 整段「图谱先读（必备 · 条件触发）」9 行）；TASK_TEMPLATE 为闸表 4 列注意事项 2 行

即 task failure_paths 第 2 行预埋的「S2 判出上游实质新增（帽条文引用新片段）→ 人工合并」情形**大概率高比例成真**，而非 S2 首句预设的「确认差异 = 仓内定制（cyning-harness-local 块 · 仓路径钉 · 先例增补）」。task 机制（S2 分支 + failure_paths + 非范围例外「S2 判出实质新增的人工合并除外」）已覆盖该路径，R3 亦自认「本地帽条文未引用该片段」——**故不阻塞**，但执行帽应预期走人工合并路径；S2 首句建议改中性表述（见 N1）。

### ④ web 先例 e70a2b0 一致性——属实

- web 仓 commit e70a2b0 message 实证：「spec-wave 3.3.0→3.5.0 三钉对齐 + sync prompts（FRAGMENT_graph_first_read 新增 · **9 本地定制 conflict 保留**）」· diff 含新增 `docs/harness/prompts/FRAGMENT_graph_first_read_v1_zh.md`（+32 行）· 无任何 conflict 文件被覆盖 ✓
- `ops-desk-web/docs/harness/invokes/by-task/web-specwave-upgrade-3-5-0/invoke_20261030_30_implement.md` :14 实证「conflict 9 本地定制全保留 · 零 --force」✓
- 本 task S5 已含「web conflict 9 vs 本仓 conflict 8 差异入自检」对照项 ✓；web 侧升级 task 已有 R1 审查文先例（invoke :19），与本 task 走 20-R1 一致 ✓
- 旁证：web invoke :23 观察「profile graph_modules_path 不可达 → 图谱闸 dormant」与本 task §7 关联 task_api_graph_anchor_profile_fix 的修正面互为印证 ✓

### 出处核实

`docs/spec/doc-health/feedback/2026-10-30_3.5.0_ops-desk-api_upgrade.md` :42 实证遗留①原文（sync prompts 另案）✓；`docs/tasks/done/task_specwave_upgrade_3_5_0.md` 存在 ✓。

## 通用核对

| 项 | 结论 |
|----|------|
| 验收标准可机断性 | V1 计数/清单对照 · V3 sha256 对包内同名件 · V4 sha256 前后不变 · V5 EXIT=0 零 diff（禁管道截断 · 承 SIGPIPE 教训）· V6 lint PASS · V7 verify 对照 + git diff 白面——全部可机断 ✓ |
| failure_paths 完备性 | 5 行覆盖：EXIT=1 语义 / 上游实质新增 / 基线漂移 / 越白名单写 / 措辞拔高误读——完备 ✓ |
| 非范围 | 6 条清晰（--force · conflict 枚内容 · 白名单外件 · AGENTS/CLAUDE 另案 · profile 修正另 task · web 仓）✓ |
| 思考轮 R0–R5 | R0–R4 闭合 · R5 未开 + early_stop at R4 有理由 · residual_risks 落 R2 ✓（N4 张力见下） |
| 行为变更类「旧测 grep 影响面」 | 不适用（零业务码 chore · graph_change_layer=none · 预期零 app/ diff） |
| 闸 | HG-TASK-DRAFT=approved（00 代录 · 授权锚 m00500）· HG-AUDIT-R1=pending —— 本审查**一律未动** ✓ |

## 阻塞清单

**零内容阻塞。**

## NIT 清单（不阻塞 · 建议 10 回填或执行期照登）

- **N1**：S2 首句预设「确认差异 = 仓内定制（cyning-harness-local 块 · 仓路径钉 · 先例增补）」与本审查实证方向相反——本地 prompts 零 local 块，差异主为**上游新增图谱先读条款被本地旧版遮蔽**（8 枚中 7 枚）。建议改中性「逐枚判定差异性质（仓内定制 / 上游实质新增遮蔽）」；执行帽应预期走 failure_paths 第 2 行人工合并路径。
- **N2**：小节编号跳号——「## 验收标准」未编号，§4 之后直接 §6（验收标准应为 §5）。
- **N3**：§7 关联的 `task_api_graph_anchor_profile_fix.md` 与 `task_api_legacy_reviews_backfill.md` 在本分支不存在（各自 sibling 分支未合入 master），本分支视角引用悬空；双分支合并后自解，建议执行期照登即可。
- **N4**：R4 early_stop 理由「无残余分叉」与 R2 residual_risks「S2 判出实质新增的概率存在」略张力；鉴于该分叉已被 S2/failure_paths 机制兜住，仅措辞层面建议如实记。

## 机械闸复核（审后复跑）

- `npx spec-wave task lint --file docs/tasks/active/task_api_prompts_sync_3_5_0.md` → **LINT: PASS · EXIT=0**
- `npx spec-wave verify --target . --task docs/tasks/active/task_api_prompts_sync_3_5_0.md` → **VERIFY: BLOCKED · HG-AUDIT-R1 pending · EXIT=2**（预期态 · 30 拒开工正确）

## 维护者签闸（20 后 · 30 前）

- [ ] 已读 R1 审查结论（本文）
- [ ] 在 task 人工闸表将 HG-AUDIT-R1 改为 approved（维护者 · 日期）
- [ ] commit task 文档或确认已签
- [ ] 再下发 Harness 30 Prompt

30 Agent 将以 task 表为准；pending 时必须拒开工（见 TEMPLATE_30_gate_stop.md）。
