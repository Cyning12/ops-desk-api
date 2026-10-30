# CLOSE 档 · task_api_prompts_sync_3_5_0（2026-10-30）

## 一句话

spec-wave 3.5.0 包内 prompts 同步全程零 --force 完成：add 1 物化 `docs/harness/prompts/FRAGMENT_graph_first_read_v1_zh.md`（sha256 与包内一致）+ conflict 8 全枚人工合并（7 枚对齐上游零 diff · 30-execute-code 保留本地 `_tech_graph/` 读序项为唯一残留 conflict 明示保留）· apply EXIT=1 预期语义照登；S1–S5 / V1–V7 全绿 · 40 独立验收 PASS；分支 `task/api-prompts-sync-3-5-0`（六 commit）未 push，**PR 合码 + CI 绿 + 分支清理待维护者裁决**（close_pr_policy=required 偏差 · 承维护者授权 m00085 全程本地直验先例 · 授权锚 m00085/m00500）。

## 需求锚

升级 task `task_specwave_upgrade_3_5_0` 遗留①立案：upgrade 向导提示 manifest 已升级但 prompts 未自动同步（出处 `docs/spec/doc-health/feedback/2026-10-30_3.5.0_ops-desk-api_upgrade.md` §6.1）；处置先例 web 仓 commit e70a2b0（conflict 全保留零 --force）。

## 交付

- **S1** dry-run 复跑：skip4/add1/conflict8 与起草基线逐字一致零漂移。
- **S2** conflict 8 逐枚 diff 审阅 + 台账：8 枚全判「上游实质新增被本地旧版遮蔽」（本仓零 cyning-harness-local 定制块 · R1 实证）→ 全部人工合并；7 枚与上游零 diff，30-execute-code 保留本地 `_tech_graph/` 硬编码项 + 吸收上游条件条款并存（残留 conflict 1 · 明示保留）。
- **S3** apply（零 --force）：EXIT=1（conflict 未覆盖提示 · cli-sync-prompts.js:156-157 预期语义 · 照登非失败）· written 1 = FRAGMENT_graph_first_read_v1_zh.md · skip 11（合并 7 枚转 skip）。
- **S4** 回归：graph-compile EXIT=0（9 graphs / 142 nodes / 207 edges）图谱零 diff · task lint PASS · 存量 verify 抽跑前后逐字一致。
- **S5** 生效面照登：web conflict 9 全保留 vs 本仓 8 全合并的差异根因（本仓零定制块）；**物化 ≠ 接入**——FRAGMENT_graph_first_read 生效前提 = profile 可达目录（task_api_graph_anchor_profile_fix 面）+ 帽条文引用（本 task 合并面已完成）。

## 验收链

10 落稿 v0.1 → 00 代录 HG-TASK-DRAFT（授权锚 m00500）→ 20 R1 审查文 `docs/harness/reviews/task_api_prompts_sync_3_5_0_audit_R1_20261030.md` 通过零阻塞（NIT N1–N4 全采纳 · v0.3 `1ebce84`）→ 00 代录 HG-AUDIT-R1（v0.4 · `2b6d2c0`）→ 30 交付（`c6bb1c3` 实现 + `ec1f774` 自检回填）→ 40 独立验收 **PASS**（`4fae535` · 不信 30 自报逐项亲跑 · conflict 8 全枚对拍 · worktree 基线法对照存量 verify 逐字一致）→ 00 CLOSE（授权锚 m00085/m00500）。

## 证据要点（40 亲跑）

- diff 面：c6bb1c3 = 9 文件 +50/-2 全在白名单面内 · 零 app/ 零其他；零 --force 内容级佐证 = 30-execute-code 本地项存续（--force 必灭失）+ 7 枚对齐上游零 diff。
- FRAGMENT sha256 `3739570a6a40b2f41110a061e1dfdb0864bd596db3371c67569584da29f3f565` 两侧一致；apply 后 dry-run 收敛 skip 12 / add 0 / conflict 1 · EXIT=0。
- V5 graph-compile EXIT=0 图谱 md 零 diff；V6 task lint PASS EXIT=0；V7 存量 verify（2b6d2c0 vs HEAD · 双侧 BLOCKED EXIT=2）逐字一致零行为变化。
- 维护者脏文件 `docs/arch-browser/dist/site-data.json` 全程未动。

## 遗留移交（另案）

1. 残留 conflict 1：30-execute-code 本地 `_tech_graph/` 读序项明示保留（本仓图谱实体目录 · 与包内 1 行差异）。
2. FRAGMENT_graph_first_read 物化 ≠ 接入：profile 可达目录前提在 task_api_graph_anchor_profile_fix（当前 vocabulary_empty 仍未真判定 · 词表适配另案）。
3. web 与本仓 conflict 处置路线差异（全保留 vs 全合并）根因照登，纪律同为零 --force。
4. §7 跨分支引用悬空随 sibling 分支合并自解；分支 `task/api-prompts-sync-3-5-0` 六 commit 未 push，PR 合码 + CI 绿 + 分支清理移交维护者终审。
