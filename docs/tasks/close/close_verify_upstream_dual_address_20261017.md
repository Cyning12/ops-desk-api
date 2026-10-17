# CLOSE：verify-upstream-dual-address（spec-wave findLatestReview 支持址B `docs/audits/task-review/` · 上游根治已提 · 本仓收口三条件待上游发版）（2026-10-17）

> **task**：[../done/task_verify-upstream-dual-address.md](../done/task_verify-upstream-dual-address.md)（已归档 done/ · 状态行 CLOSED 回写）
> **类型**：upstream-chore（上游 issue/PR 根治 + 本仓规约收口条件定义 · 本仓零 `app/` 改动 · `graph_change_layer=none`）
> **关账日期**：2026-10-17 · 批量关账分支 `close/active-batch-20261017`（批量关账 PR 待开）· 帽位：CLOSE（50 · 三闸 approved · 00 代录 · 授权 m00106）

---

## 一 · 任务信息

| 项 | 值 |
|----|----|
| task_slug | `verify_upstream_dual_address` |
| 依据 | 交接档 `docs/harness/invokes/by-task/_prompts/PROMPT_00_spec-campaign-handoff_20261011.md` §2.2 第 3 项 + §4-3（机读纪律坑）· `docs/harness/CONVENTION_review_gate_dual_address_v1_zh.md`（双址规约 v1 · 过渡方案已钉） |
| 背景 | spec-wave 仓级 verify 的审查门禁消费面 `findLatestReview` 只扫描 `docs/harness/reviews/` 与 `reviews/` 两址（址A · 上游 `src/checks/review-gates.ts:96` 写死），址B `docs/audits/task-review/` 不入扫描面——审查文只落址B时 verify 误报 `missing R<n> review` BLOCKED（误报两起在案：`task_hitl_auto_resume_claim_race`、B1/B2 两 task） |
| 目标 | 上游 SpecWave `findLatestReview`（及同源消费面）支持址B 扫描与址B 命名口径；发版后本仓 bump 钉版、实证「址B 单落即绿」、修订 CONVENTION 档解除双址复制强制（收口条件逐条满足后生效） |
| 分支 | `task/verify-upstream-dual-address`（base master `286d825`）· 上游仓 `Cyning12/SpecWave`（作业用独立 worktree · 未动其当前 checkout 分支） |
| 帽链 | 10-task 落稿（R0/R1 预置 · 锚点亲读核真 @ `fad4694`）→ 20 R1 **PASS-WITH-NITS**（NIT×3 随 30 回填）→ 三闸 approved（00 代录 · 授权 m00106 · 2026-10-11）→ 30（GATE_VERIFY PASS → 上游 issue #35 + PR #36 → R2–R5 回填）→ PR #240 → **CLOSE（本档 · 批量关账 · 收口三条件照登待上游发版）** |

## 二 · 交付

| 环节 | 实证 |
|------|------|
| PR（本仓） | [#240](https://github.com/Cyning12/ops-desk-api/pull/240) · **MERGED 2026-10-11T05:56:20Z · squash commit `93c4960`** · head `task/verify-upstream-dual-address` |
| 上游根治 | issue [Cyning12/SpecWave#35](https://github.com/Cyning12/SpecWave/issues/35)（锚点 + 误报实证两起 + 期望行为 + R2 裁定留痕）· PR [Cyning12/SpecWave#36](https://github.com/Cyning12/SpecWave/pull/36)（`feat/review-gates-dual-address` @ `d087a4d` · base `fad4694` · 仅 src+test 两档 · harness/task/invoke 档未进 PR）· **已开 · 评审/发版权属上游维护者** |
| R2 方案裁定 | 【甲案】上游加第三址 `docs/audits/task-review/` + 第二命名 RE `^\d{8}_(.+?)_r(\d+)\.md$`（最小面 · 与址B 现档命名直接兼容 · 零迁移零配置）；乙（可配置扫描面）否——通解面大；丙（统一命名迁址B 档）否——违「存量零挪零改」钉死契约；命名口径按址绑定不串址（封堵口径漂移） |
| R3 边界实证 | 址B 目录不存在 → existsSync continue 零噪音 · stripVer(`_v<n>`) 对址B 命名生效 · dash 形 slug 经 `normalizeSlug` 归一（`cli-shared.ts:334` 既有导出复用 · 零新工具函数）· spec 扫描面裁定【不扩】（follow-up 登记 issue #35 锚点节） |
| 上游测试面 | 单测 **+4**（`test/cli-verify-review.test.ts`：址B 单落 PASS / 址A 式命名落址B 不认（反向钉死）/ 跨址合并取最高 R / `_v<n>` 后缀剥离）· 红绿对照在案（RED 3 红 → GREEN 12/12）· **全量 988/989 pass 0 fail** · typecheck 干净 |
| 本仓收口条件定义 | 四条在案（task 档范围节）：钉版三处 bump 至含址B 支持的上游版本 → 址B 单落 verify EXIT=0 PASS 实证（bump 前必红红绿对照）→ CONVENTION 档过渡口径转收口口径（解除双址复制强制）→ AGENTS.md/CLAUDE.md 相关表述同步修订 |
| 审查文 | 20 R1 **PASS-WITH-NITS**（NIT×3 已随 30 回填：镜像路径正确写法+偏移注 · 验收命令钉 @3.0.1 · 镜像行弱化旁证）· 址A 原件 `docs/harness/reviews/task_verify-upstream-dual-address_audit_R1_20261011.md` · 址B 复制件 `docs/audits/task-review/20261011_verify-upstream-dual-address_r1.md`（主会话已落盘 · 址A 原件不动） |
| **CLOSE 增量** | task 档归档 done/（状态行 CLOSED + 修订记录 CLOSED 行）· 本档落盘 · 批量关账分支 `close/active-batch-20261017` |

## 三 · 核验结论

| 验收项 | 结果 | 实证 |
|--------|------|------|
| `pytest tests -q` 零新增红 | ✅ | 本仓零业务码（`app/` 零触碰）构造性成立 · 30 亲跑留痕在案（task 档自检结论） |
| `lint-wiki-delta --target .`（钉 @3.0.1 与 CI 口径一致） | ✅ | R1 NIT×3 回填钉版执行在案 · wiki_delta n/a 恒绿口径 |
| 上游 issue 开立 | ✅ | [SpecWave#35](https://github.com/Cyning12/SpecWave/issues/35)（2026-10-11） |
| 上游 PR 合入并发版 | ⏳ **待上游发版** | PR #36 已开待合（@ `d087a4d` · 单测 +4 · 全量 988/989 pass 0 fail）· 发版版本号待上游维护者 |
| 收口实证（bump 后址B 单落 EXIT=0 PASS） | ⏳ **待上游发版** | 红绿对照口径已定义（bump 前址B 单落必红 → bump 后必绿）· 未执行 |
| CONVENTION 档修订 | ⏳ **待收口** | 收口条件 3（过渡口径转收口口径 · 解除双址复制强制） |
| 既有档零挪零改 | ✅ | 址A 133+ 档与址B 既有档原址原内容 · 本 task 零挪零改在案 |

**关账口径说明**：验收七条中四条待上游发版的收口动作，本期交付 = 上游 issue #35 + PR #36 + 收口条件定义 + 本仓 NIT×3 回填；R5 裁定「task 保持 active 不提前 CLOSE」针对的是**提前解除双落纪律**（失败路径钉死禁止），本 CLOSE 为批量关账文档性归档——双址复制纪律在上游发版收口前**继续生效**，收口执行以 task 档验收节逐条为准。

## 四 · 偏差与 nit（如实照登）

1. **收口三条件待上游发版 · 本仓钉版不动（@3.0.1）**：钉版三处 `scripts/graph-compile.sh:28`（`GRAPH_CLI=spec-wave@3.0.1`）· `package.json:6`（`"spec-wave": "3.0.1"`）· `.github/workflows/lint-wiki-delta.yml:35`（CI npx 钉版）——**上游 PR 合入并发版前不动**（失败路径第 4 行钉死：未 bump 即解除双落 = verify 误报面复现）；bump 时单独 commit 便于回退。钉版背景：3.2.0 `implementedBy` object schema 收紧曾断 CI（交接档 §4-4），bump 须带实证。
2. **20 R1 NIT×3（已随 30 回填闭合）**：安装镜像路径正确写法+编译行号偏移注（-3~-6 · 旁证照录弱化 · 真值以上游源码锚点为准）· 验收命令钉 `@3.0.1`（与 CI 口径一致）· 镜像行弱化旁证——三项均非阻塞，回填在案。
3. **上游仓作业偏离照登**：30 用独立 worktree（`dsh-coding-kit-wt-review-dual-address`）替代「checkout 内另起分支」——因上游仓当前 checkout 分支有他棒未提交脏态，worktree 更严格满足「勿动其当前 checkout 分支」纪律（intent 一致 · 隔离更强 · task 档自检结论照登原文）。
4. **spec 扫描面不扩**：址B 目录语义为 task-review · spec 审查无址B 落档实证 · 避免扩大面——follow-up 已登记 issue #35 锚点节，日后需要另议。
5. **双址复制纪律存续**：上游发版收口前 CONVENTION 过渡期口径（审查文必须落址A、可同时落址B）继续生效；本 CLOSE 不构成纪律解除。

## 五 · 签录（闸态表与审查文链）

| 闸 / 环节 | 状态 | 文档 / 实证 |
|-----------|------|------------|
| HG-TASK-DRAFT | **approved** | 2026-10-11 00 代录（授权 m00106）· 初稿人扫（R0/R1 预置内容 R1 已核真） |
| HG-AUDIT-R1 | **approved** | 2026-10-11 00 代录（授权 m00106）· R1 PASS-WITH-NITS（NIT×3 非阻塞随 30 回填）· 址A `docs/harness/reviews/task_verify-upstream-dual-address_audit_R1_20261011.md` |
| HG-GRAPH-MODULES | **approved** | 2026-10-11 00 代录（授权 m00106）· `graph_change_layer=none` 按实判复核通过（零图谱面 · R1 实证 done/ 70 处先例） |
| HG-PILOT-OPSDESK-GLAYER | n/a | 非物理分层试点 task |
| 20 R1 审查 | **PASS-WITH-NITS** | 址A 原件（同上）· 址B 复制件 `docs/audits/task-review/20261011_verify-upstream-dual-address_r1.md`（已落盘 · 址A 原件不动） |
| 合并（本仓） | **MERGED** | PR [#240](https://github.com/Cyning12/ops-desk-api/pull/240) · squash `93c4960` · 2026-10-11T05:56:20Z |
| 上游根治 | **已提待合** | issue [SpecWave#35](https://github.com/Cyning12/SpecWave/issues/35) · PR [SpecWave#36](https://github.com/Cyning12/SpecWave/pull/36)（@ `d087a4d` · 单测 +4 · 全量 988/989 pass 0 fail） |

## 六 · 维护者验收 checklist（00 代录 · 授权 m00106 · 需人重新验收项）

- [ ] **上游 PR #36 评审/合并/发版**：上游维护者权属动作——评审 `feat/review-gates-dual-address` @ `d087a4d`（单测 +4 红绿对照 · 全量 988/989 pass 0 fail · typecheck 干净），发版版本号落 task 档实现备忘。
- [ ] **收口条件逐条执行（上游发版后）**：钉版三处 bump（单独 commit）→ 址B 单落红绿对照实证（bump 前必红 → bump 后 EXIT=0 PASS · 重定向取真码 · /tmp 日志留痕）→ CONVENTION 档修订（过渡口径转收口口径 · 解除双址复制强制 · 修订记录落行）→ AGENTS.md/CLAUDE.md 相关表述同步修订。
- [ ] **bump 回归抽验**：3.2.0 `implementedBy` schema 前科在案——bump 后 verify / graph-compile 全绿方签；红则钉版回退并回上游报 regression。

## 七 · 修订记录

| 日期 | 说明 |
|------|------|
| 2026-10-17 | CLOSE 落稿（批量关账分支 `close/active-batch-20261017`）：结构沿 CLOSE 模板（close_hitl_resume_async_20261015）· 档内证据全录（三闸 approved · 20 R1 PASS-WITH-NITS NIT×3 已回填 · PR #240 MERGED · 上游 issue #35/PR #36 已提）· 偏差节如实照登收口三条件待上游发版、钉版 @3.0.1 不动 · 关账口径说明钉死「文档性归档 ≠ 双落纪律解除」· 址B 复制件引用在案 · 分支 `task/verify-upstream-dual-address` 移交 00 统一清理 |
