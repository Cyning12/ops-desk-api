# CLOSE 档 · task_api_graph_anchor_profile_fix（2026-10-30）

## 一句话

legacy `.cyning-harness/profile.json` 的 `graph_modules_path` 由不可达的 `l1/01_modules` 修正为可达目录 `docs/_tech_graph/l1`，spec-wave 3.5.0 graph_anchor 检查由 `graph_path_unreachable` 诚实毕业至 `skipped: vocabulary_empty`（词表面适配另案）；V1–V7 全绿 · 40 独立验收 PASS；分支 `task/api-graph-anchor-profile-fix`（六 commit）未 push，**PR 合码 + CI 绿 + 分支清理待维护者裁决**（close_pr_policy=required 偏差 · 承维护者授权 m00085 全程本地直验先例 · 授权锚 m00085/m00500）。

## 需求锚

升级 task `task_specwave_upgrade_3_5_0` 遗留②立案：3.5.0 新增 graph_anchor 图谱锚点引用检查，profile 声明 `graph_modules_path` 且解析为可达目录才真判定；本仓 legacy 值相对仓根不可达 → probe 恒 `graph_path_unreachable` skip。实证锚 `docs/spec/doc-health/feedback/2026-10-30_3.5.0_ops-desk-api_upgrade.md` §2/§6.2。

## 交付

- **S1**：`.cyning-harness/profile.json:5` 单行值变更（其余字段零改 · JSON 合法 · 不新建 .coding-kit/profile.json 避免双层遮蔽）。
- **S2** 生效实测：verify 输出零 `graph_path_unreachable`；graph_anchor 行逐字：`verify: INFO · 图谱锚点引用检查 · 图谱锚点检查未生效（已跳过 · vocabulary_empty · 模块词表抽取失败（01_struct.md 缺失））`。
- **S3** 存量回归：active + done 各一档 verify 修正前后逐字节 diff 为空 · EXIT 与缺口集合零新增。
- **S4** 词表面适配差距照登（不实施）：真判定需上游契约 `<dir>/01_struct.md`「## 1. 模块边界表」节，本仓真值在 `01_modules.md`「## 模块表（必填）」节——图谱面新增须 HG-GRAPH-MODULES 闸，另案。

## 验收链

10 落稿 v0.1 → 00 代录 HG-TASK-DRAFT（授权锚 m00500）→ 20 R1 审查文 `docs/harness/reviews/task_api_graph_anchor_profile_fix_audit_R1_20261030.md` 通过零阻塞（NIT-1~5 全采纳 · v0.3 `3956ad5`）→ 00 代录 HG-AUDIT-R1（v0.4 · `f96419a`）→ 30 交付（`f388ac3` 实现 + `2a455dc` 自检回填）→ 40 独立验收 **PASS**（`5c932b6` · 不信 30 自报逐项亲跑 · f96419a detached worktree 独立取前基线逐字吻合）→ 00 CLOSE（授权锚 m00085/m00500）。

## 证据要点（40 亲跑）

- V1 值断言 + isDirectory 双 EXIT=0；V2 本 task verify EXIT=0 `VERIFY: PASS` 且零 `graph_path_unreachable`。
- V3 存量两 task 前后逐字节 diff 为空；V4 仓级 EXIT=2 照登 · reviews 缺口恰 5 枚基线零新增类别。
- V5 `graph-compile.sh` EXIT=0（真码非管道截断）· `docs/_tech_graph/` porcelain 空；V6 `task lint` PASS EXIT=0。
- V7 diff 面纯净：实现面仅 profile 单行，余为 invoke/task 留痕；维护者脏文件 `docs/arch-browser/dist/site-data.json` 全程未动。
- 波及面复核：现役消费者仅 spec-wave（graph-anchor.js:26 · verify.js:507 · cli-lifecycle.js:193）；`.coding-kit/` 无 profile.json；AGENTS.md 符号引用不联动。

## 遗留移交（另案）

1. 词表面适配：`01_struct.md` 契约 vs `01_modules.md` 真值的双真值风险，图谱面新增须 HG-GRAPH-MODULES 闸，维护者裁决另案。
2. 存量 task 图谱锚点引用补齐：graph_anchor 真判定后若新红，另案不顺手改存量。
3. 双 profile（.coding-kit 读序优先于 legacy）遮蔽面观察。
4. 分支 `task/api-graph-anchor-profile-fix` 六 commit 未 push：PR 合码 + CI 绿 + 分支清理移交维护者终审。
