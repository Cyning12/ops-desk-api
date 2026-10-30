# Task 审查：api-legacy-reviews-backfill（R1 · 20-task-audit）

> **审查对象**：`docs/tasks/active/task_api_legacy_reviews_backfill.md`（分支 `task/api-legacy-reviews-backfill` · HEAD 001a188 · v0.2）
> **审查帽**：20-task-audit（R1 · 书面审查 · 未改 task 实质内容 · 未动闸 · 未 commit · 审查文留 untracked）
> **日期**：2026-10-30 · **审查时仓态**：主 worktree 曾被并行会话切分支（见 O3），实证在隔离 worktree `/tmp/audit-lrb`（同 HEAD 001a188）完成
> **委托令**：00 委派「维护者新原则首单 · 全走审查零豁免 · 禁 --allow-no-review」· 五大重点逐条独立复核（读码实证不转述）

## 结论摘要

- **内容审查：通过（零内容阻塞）** —— 五大重点全部经本帽独立读码/实跑复核，钉案逐条与仓内实证吻合；范围/非范围/验收/failure_paths/思考轮六维闭合。
- **流程闸：HG-AUDIT-R1 = pending（符合预期）** —— 本帽未代签；维护者签闸清单见文末。HG-TASK-DRAFT 已 approved（v0.2 · 00 代录 · 授权锚 m00500）在案。
- **阻塞项：无。非阻塞观察 3 条（O1/O2/O3，供执行帽与维护者参考）。**

## 一、重点①：5 存量 reviews 缺口 = 2×新 R1 + 3×补轮 R2 —— 独立实证吻合

本帽亲跑（分支 HEAD 001a188 · spec-wave 3.5.0）：

```text
$ npx spec-wave@3.5.0 verify --target .
reviews 缺口（failClosed · …）:
  - docs/tasks/done/task_fix_hitl_observe_node_config_injection.md · missing R<n> review
  - docs/tasks/done/task_fix_no_proxy_bracket_ipv6_sanitize.md · missing R<n> review
  - docs/tasks/done/task_lg_rag_capability_output_schema.md · 审查文结论不可机读通过（…_audit_R1_20261027.md · 结论/签收节含否定结论词…）
  - docs/tasks/done/task_query_coref_rewrite.md · 审查文结论不可机读通过（…_audit_R1_20261019.md · 结论/签收节含否定结论词…）
  - docs/tasks/done/task_supervisor_first_fail_closed.md · 审查文结论不可机读通过（…_audit_R1_20261019.md · 无结论/签收节…）
VERIFY: BLOCKED · 仓级 reviews 缺口 5 · EXIT=2
```

逐枚独立复核（非转述 verify 输出）：

| 缺口 | 本帽实证 | 与 task 分解 |
|------|----------|--------------|
| fix-hitl-observe-node-config-injection | `ls docs/harness/reviews/ \| grep hitl_observe` 零命中；done 档在案 | 新 R1 ✓ |
| fix-no-proxy-bracket-ipv6-sanitize | 同上零命中；done 档在案 | 新 R1 ✓ |
| lg-rag-capability-output-schema | 在案 R1（20261027）`## 结论` 节 :92 实含「内容审查：BLOCKED」「内容阻塞未清前不附 30 Prompt」——否定词命中属实 | 补轮 R2 ✓ |
| query-coref-rewrite | 在案 R1（20261019）`## 结论摘要` 节 :13 实含「不构成退回理由」——「退回」命中否定守卫（lookbehind 仅豁免 无需/不/未 前缀，「成退回」不在豁免面） | 补轮 R2 ✓ |
| supervisor-first-fail-closed | 在案 R1（20261019）节标题全枚举（一、六大核对表/二、阻塞项/三、非阻塞/四、HG 建议/五、回填/六、下一棒/维护者签闸/修订记录）——无「结论/签收」起首节属实 | 补轮 R2 ✓ |

交叉印证：`docs/spec/doc-health/feedback/2026-10-30_3.5.0_ops-desk-api_upgrade.md` §5（:35-38）载 master `0a5d610` 以 3.3.0 复跑同一 5 缺口逐字一致、五档均 2026-10-19+ 归档晚于豁免基线 2026-10-11——task §1「存量既有缺口 · 非 3.5.0 引入」属实。

## 二、重点②：补轮 R2 承「不通过→补轮 R+1」纪律 —— 仓内先例在案

- **条文真值**：`docs/harness/prompts/10-task-requirements.md:56` ——「20-task-audit 审思考是否充分；不通过 → **退回 10-task** 补轮后再审 R+1」。
- **在案补轮先例**（reviews/ 实存）：`task_specwave_cleanup_2_1_3_audit_R2/R3_20260911.md`、`task_specwave_verify_baseline_audit_R2_20261011.md`、`task_supervisor_parallel_join_audit_R2_20260919.md`、`task_testing_write_capability_audit_R2_20261009.md`。
- 本帽通读 verify_baseline R2 全文头部：R1 裁定 BLOCKER（B-1）→ R2 增量复核，`## 结论` 节引述 R1 沿革而用词干净（「R1 裁定 BLOCKER」「lint FAIL」均非否定词表形态），为 S1c–S1e 可直接对照的合规范式。
- task S1c–S1e「补轮 R2 · 不得覆盖原 R1」与 failure_paths 第 5 行「前审沿革节」设计，与该纪律及先例一致 ✓。

## 三、重点③：仓规落点 AGENTS.md cyning-harness-local 块 —— 实证成立

- **块结构**：`AGENTS.md:153-159` `<!-- cyning-harness-local:begin/end -->` 块在案，内含仓内定制三条（pre-30 invoke 拒改码 / HG-PILOT·G-L0 关键词 / HG-GRAPH-MODULES 图谱闸路径），块外 :122 产品块自述「勿改本 begin/end 内文（upgrade 会整块替换）」。
- **「upgrade 不改写」实证（非自述转述）**：`.coding-kit/manifest.json` 载 `from_version: 3.3.0 → version: 3.5.0 · upgraded_at: 2026-10-30T01:59:27Z`——本仓昨日刚完成 3.5.0 升级，而 local 块三条仓内定制原样存续（本帽 :153-159 亲读）= 升级后零改写的现时实证。另有多波历史佐证在案：`task_specwave_upgrade_2_4_2.md` F-4 回滚预案+验收 :114「local 块内容零变化」、`task_specwave_upgrade_3_0_0.md:101` 同口径、`task_dsh_coding_kit_upgrade_1_5_1.md:82` / `1_7_1.md:60`「local 块零手恢复」、`feedback/2026-09-18_3.0.0` 验收锚 HASH `0b6df7fc537b22ad` 全程不变。
- **落点排他理由**：`docs/standards/` 实仅 `CODING_BASELINE_L1_v1_zh.md` / `CODING_BACKEND_L2_v1_zh.md` / README——编码规范面，流程闸纪律落彼确实不协调。task R2 定夺成立 ✓。

## 四、重点④：两条款可执行性核对

- **条款一**（升级/流程类 task 禁用 `--allow-no-review` · 一律走 20-R1）：可执行且有机械兜底——`--allow-no-review` 仅作用于 `verify --task` 当次调用，而 done 档归档后由仓级裸 verify failClosed 兜底（`cli/verify.js:134-152`：done 档无机读通过的审查文即回缺口清单）。即「豁免旗绕审」在归档关账面无法藏匿，仓规条款只是把该约束前置到开工面。探测违规靠 invoke 留痕/过程记录（旗标不入库），属流程可执行。
- **条款二**（exempt 扩列须带截止条件/回填义务 · 写入 reason 字段）：基建在案——`checks/exempt.ts`（见 yaml 头注 :2-5）已机械校验四字段 slug/reason/date/authorized_by 缺一即 invalid + authorized_by A1 三元判；既有扩列先例（arch-browser-eng-graph-mermaid :25 reason 长文注记裁定沿革）证明 reason 字段承载长语义可行。增量部分「截止条件/回填义务」是 reason 的语义内容，spec-wave 不做语义机判，由审查/人审面执行——条款写成纪律可执行，但执行帽落 AGENTS.md 时应如实表述为「人审核对项」而非「机断闸」（见 O2）。
- 仓内定制块关键词/闸路径既有条目与两条款无冲突；条款落 begin/end 标记内、其余零改，V4 可机验（git diff 限定块内）✓。

## 五、重点⑤：verify 缺口 5→0 清零机断可行性 —— 源码实证可行

本帽通读 `node_modules/spec-wave/lib/`（3.5.0）单一实现源：

1. **缺口判定**：`cli/verify.js:134-152`（verifyBareReviewsMode）——done 档逐枚 `findLatestReview`：无审查文 → `missing R<n> review`；有则 `evalReviewConclusion(最高轮)` 失败 → 「不可机读通过」。`blocked = gaps.length > 0`（:162），缺口 0 → `VERIFY: PASS（裸 verify · 仓级 reviews 扫描）` EXIT=0（:208-213）。
2. **最高轮语义**：`checks/review-gates.js:127-134`——按 round 升序取末位，**R2 落盘即取代 R1 成为唯一被评估轮**，原 R1 否定结论留档但不再参与判定。「补轮 R2 不清原档而清零缺口」机制成立。
3. **机读契约**：`checks/review-gates.js:162-227`——节标题 `^#{2,3}s*(中文序号)?(结论|签收)` 起首 · 通过词 PASS/ACCEPT/签收/通过/零内容阻塞/零阻塞落节内 · 否定守卫 `REVIEW_NEG_RE`（退回[豁免 无需/不/未 前缀]/不·未通过同句窗/不予·不·未签收/no·not pass/doesn't/fail to pass/not approv*/decline/veto/refuse/中英混入/内容阻塞[豁免 零 前缀]）· 去通过词后实质 ≥20 字符 · 档 M 语义判 SUBJ∧(OBJ∨GATE)。task §2 S1 机读契约照登与源码一致 ✓。
4. **命名口径**：址A 文件名匹配为字面比对（`review-gates.js:113` `stripVer(m[1]) !== base` · 捕获组必参与）——审查文文件名必须带 `task_` 前缀且 slug 段与 done 档 basename（含下划线）逐字一致；task S1a–S1e 所钉命名全部合规 ✓。slug 归一（meta task_slug 优先 · underscores→hyphens）仅作用于豁免条目解析面（`exempt.ts` U1），task 照登口径无误。
5. **操作戒尺（实证导出）**：R2 审查文「前审沿革」须独立成节、**不得并入结论/签收节**——若在该节内引述原 R1 的「BLOCKED/内容阻塞/退回」等字面，将再触 `REVIEW_NEG_RE` 致新轮亦不可机读通过（query_coref R1 正是「不构成退回理由」误伤先例）。verify_baseline R2 的「结论节干净 + 沿革另述」即合规范式。

结论：S1 五枚落盘且各自过机读契约 → 缺口 5→0 · VERIFY: PASS EXIT=0 为可机断验收 ✓。

## 六、通用核对（验收可机断 · failure_paths · 非范围 · 思考轮）

- **验收标准 V1–V7**：V1（文件名/落盘）·V3（verify 输出）·V5（审查文+verify --task）·V6（lint）·V7（git diff 面）均可机断；V2/V4 含人审判断面（核对质量/条文逐字）——对审查交付类 task 属合法形态。
- **failure_paths 5 行**：覆盖实质不通过 STOP 纪律 / 机读不过修格式 / 落点维护者另定 / 并行缺口隔离 / R2 沿革表述——与本 task 风险面契合，可重试性与用户可见口径齐。
- **非范围 5 条**：exempt yaml 零 diff · done 档本体零改 · 基线前历史档不重审 · web 仓另案 · 本 task 自身禁用豁免旗——边界清晰且与 V7 diff 面互锁。
- **思考轮 R0–R5**：控制表齐 · early_stop at R5 理由成立（轮次用尽 · 无残余分叉）· residual_risks 落 R2/R3 照登。lint E8–E10 结构闸 PASS（本帽亲跑）。
- **行为变更类 checklist（K7）**：本 task 零业务码改动（graph_change_layer=none · code_quality_bar=not_applicable），非行为变更类，「旧测 grep 影响面」项不适用。

## 七、复跑钉案（本帽亲跑 · 2026-10-30）

```text
$ npx spec-wave@3.5.0 task lint --file docs/tasks/active/task_api_legacy_reviews_backfill.md
LINT: PASS · task_api_legacy_reviews_backfill.md · EXIT=0

$ npx spec-wave@3.5.0 verify --target . --task docs/tasks/active/task_api_legacy_reviews_backfill.md
HG-TASK-DRAFT approved · HG-AUDIT-R1 pending ❌ 拒 30 · HG-GRAPH-MODULES n/a
VERIFY: BLOCKED · HG-AUDIT-R1 pending · task_api_legacy_reviews_backfill.md · EXIT=2（预期）
```

## 八、阻塞项与回填清单

- **内容阻塞：零** —— 无回填 10-task 项。
- **流程闸：HG-AUDIT-R1 = pending** —— 权属维护者，签闸清单见文末。

## 九、非阻塞观察（供执行帽/维护者参考 · 不构成退回理由）

- **O1（陈旧表述 · 顺手项）**：task 状态行 :3 与 R5 节 :138 仍书「双闸 pending」，v0.2 已代录 HG-TASK-DRAFT=approved；:5「分支…（维护者签收后新建）」分支实已建。闸表本身为真值且正确，执行帽 close 前顺手校正表述即可。
- **O2（条款二表述建议）**：S2 落 AGENTS.md 时建议写明「截止条件/回填义务由人审核对（spec-wave 四字段为机械面 · 语义面不机判）」，免后生误解为机断闸。
- **O3（仓态观察 · 非 task 内容）**：审查期间主 worktree 分支被并行会话切换（task/api-legacy-reviews-backfill → task/api-graph-anchor-profile-fix），疑多审查 agent 并发共用同一 worktree 所致；本帽实证已在隔离 worktree（同 HEAD 001a188）完成，结论不受影响。建议上级对并发审查棒串行化分支操作或各棒用独立 worktree。
- **V3 逐字口径提醒**：PASS 时输出字面为 `VERIFY: PASS（裸 verify · 仓级 reviews 扫描）`（verify.js:210），执行帽照登时取全行。

## 结论与签收

本帽 20-task-audit 对 task_api_legacy_reviews_backfill 的 R1 书面审查**通过（PASS · 零内容阻塞）**：范围/非范围/验收/failure_paths/思考轮/人工闸六维核对闭合；五大重点逐条经独立读码与实跑复核全部属实——仓级 5 缺口分解（2 missing + 3 机读不过）与 verify 实跑逐字吻合，R+1 补轮纪律条文与先例在案，AGENTS.md 仓内定制块落点经 manifest 与多波升级实证，两条款可执行性成立，缺口 5→0 清零经 review-gates.js/verify.js 源码证实可机断。HG-AUDIT-R1 闸维持 pending，签收权属维护者；本帽不代签、不附 30 Prompt。

## 维护者签闸（20 后 · 30 前）

- [ ] 已读 R1 审查结论（本文）
- [ ] 在 task 人工闸表将 HG-AUDIT-R1 改为 approved（维护者 · 日期）
- [ ] commit task 文档或确认已签
- [ ] 再下发 Harness 30 Prompt

30 Agent 将以 task 表为准；pending 时必须拒开工（见 TEMPLATE_30_gate_stop.md）。

## 修订记录

| 日期 | 摘要 |
|------|------|
| 2026-10-30 | R1 落盘：五大重点独立复核全吻合 · 内容零阻塞通过 · HG-AUDIT-R1 pending 待维护者签闸 · O1–O3 非阻塞观察照登 |
