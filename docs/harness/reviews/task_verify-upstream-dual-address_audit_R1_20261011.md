# Task 审查（R1）：verify-upstream-dual-address

> **帽子**：20-task-audit · **轮次**：R1 · **日期**：2026-10-11
> **被审对象**：`docs/tasks/active/task_verify-upstream-dual-address.md`（draft · commit d2e19cb · 分支 task/verify-upstream-dual-address · worktree t-verify-upstream-dual-address）
> **对照真值**：`docs/harness/CONVENTION_review_gate_dual_address_v1_zh.md` v1 全文 · `docs/harness/invokes/by-task/_prompts/PROMPT_00_spec-campaign-handoff_20261011.md` §2.2-3/§4-3/§4-4 · 上游 Cyning12/SpecWave @ `fad4694` `src/checks/review-gates.ts`（亲读复核）
> **落址**：址A `docs/harness/reviews/`（双址规约过渡期硬步骤 · 命名 `task_<slug>_audit_R<n>_YYYYMMDD.md` 机读口径合规）

---

## 结论与签收

**结论：PASS-WITH-NITS · 零内容阻塞**（内容面审查通过 · 三条 NIT 登记在案 · 属措辞/口径级）。

本棒对该 task 草稿完成书面审查与复核：上游源码锚点（Cyning12/SpecWave @ `fad4694` · `src/checks/review-gates.ts:96/:99/:116-119/:46`）逐行核对属实；址B 命名不同构发现抽样核真（`docs/audits/task-review/` 9/9 档全为 `YYYYMMDD_<slug>_r<n>.md`）；钉版三处、闸表契约（`task lint` EXIT=0 PASS）、失败路径三案覆盖、`graph_change_layer=none` 先例一致性、R2 三案开放性全部通过。三条 NIT（镜像路径写法 · lint-wiki-delta 验收命令钉版口径 · worktree 无 node_modules 镜像弱化为旁证）不影响 task 可执行性，留执行链注意。

流程闸分列：**HG-TASK-DRAFT / HG-AUDIT-R1 / HG-GRAPH-MODULES 均 pending**（待维护者签 task 表 · 本棒审查不代签 human_gate · 30 开工授权以 task 表 approved 为真值）。

---

## 核对项明细（逐项实证）

| # | 核对项 | 结果 | 证据 |
|---|--------|------|------|
| 1 | 址B 命名不同构发现 | ✅ 属实 | 抽样 `docs/audits/task-review/` 全部 9 档：`20261010_hitl-auto-resume-claim-race_r1.md` 等，100% 为 `YYYYMMDD_<slug>_r<n>.md`——无 `task_` 前缀、日期前缀、小写 `_r<n>`，与址A RE `^(task_.+?)_audit_R(\d+)_.*\.md$` 不同构成立 |
| 2 | 上游锚点 :96 扫描面 | ✅ 亲读复核 | `fad4694` 在案（2026-10-11 · Merge PR #34）；当前 checkout HEAD `fe454f0`（分支 task/specwave-3-3-graph-ast）与 `fad4694` 对该文件 **零 diff**，锚点在 `fad4694` 精确成立：:96 `const dirs = [path.join(target, 'docs/harness/reviews'), path.join(target, 'reviews')]` 址B 不在内 |
| 3 | 上游锚点 :99 命名 RE | ✅ 亲读复核 | :99 `const RE = /^(task_.+?)_audit_R(\d+)_.*\.md$/i` 不收址B 命名口径 |
| 4 | 上游锚点 :116-119 / :46 | ✅ 亲读复核 | :117-119 `findReview` = `findLatestReview` 布尔投影同源（注释 :116 自述单一实现源）；:46 spec 扫描 `findSpecReview` dirs 同构双址写死 |
| 5 | 钉版三处 | ✅ 逐处核真 | `scripts/graph-compile.sh:28` `GRAPH_CLI="${GRAPH_CLI:-spec-wave@3.0.1}"` · `package.json:6` `"spec-wave": "3.0.1"` · `.github/workflows/lint-wiki-delta.yml:35` `npx --yes spec-wave@3.0.1 task lint-wiki-delta` |
| 6 | R2 甲乙丙三案开放性 | ✅ 开放得当 | 非范围钉「上游实现方案不在本 task 锁死（R2 思考轮裁定后落 issue/PR）」；R2 种子列甲（第三址+第二 RE · 最小面）/乙（可配置通解 · 面大）/丙（统一命名迁档 · 倾向否·理由=违存量零挪零改契约）——丙的倾向带明示理由且最终裁定留 R2，并要求含址A/址B 同名冲突取舍，开放性达标 |
| 7 | 失败路径三案覆盖 | ✅ 全覆盖 | wontfix（行1 · 双址纪律长期维持无回归）· 上游收址B 不收命名口径（行2 · 收口条件 2 不成立 · 规约维持双落）· bump 回归（行3 · 钉版回退 + 回上游报 regression）；另含提前解除双落（行4 · 与 CONVENTION §二-2 口径一致）与未签闸拒开工（行5）两条 |
| 8 | graph_change_layer=none 先例一致性 | ✅ | `docs/tasks/done/` 70 处 `graph_change_layer.*none` 先例（10 invoke 记 51 处·实测更多）；`graph_delta_note` 按实判（钉版 bump + 规约档修订不触 `docs/_tech_graph/` 模块语义）成立；HG-GRAPH-MODULES 仍 pending 待人签「在册·无图谱变更」口径与先例一致 |
| 9 | 闸表契约（4 列 · status 纯 pending） | ✅ 机检通过 | `npx --yes spec-wave@3.0.1 task lint --file docs/tasks/active/task_verify-upstream-dual-address.md` → EXIT=0 `PASS`；闸表 4 列 human_gate_id\|status\|blocks_hats\|说明 · status 纯 `pending`/`n/a` 无粗体括注 · 节名无编号 · wiki_delta 必填齐 |
| 10 | 验收标准可机断性 | ✅ | verify 实证用重定向取 `$?` 真码口径（符 CONVENTION §四 D3）；红绿对照（bump 前址B 单落必红 → bump 后必绿）双向可机判；上游 issue URL / PR 号 / 版本号落实现备忘；既有档零挪零改用 git diff 零判；wontfix 等外部不确定面已由失败路径兜底 |

## 非阻塞发现（NIT · 不阻塞执行链）

- **N1（措辞级）**：task:55 镜像路径写作 `node_modules/spec-wave@3.0.1/lib/checks/review-gates.js:89-114`——实际安装目录为 `node_modules/spec-wave/`（npm 布局无 `@版本` 段；主仓实证 v3.0.1 在装 · 编译产物 `lib/checks/review-gates.js` 函数体确在 :89-114 · dirs :90 · RE :93，与 TS 源码行偏移 3-6 行，「行号与源码对齐」表述偏宽）。`@3.0.1` 应读作版本注记非字面路径；执行链按 `node_modules/spec-wave/` 实读即可，不影响结论。
- **N2（口径级）**：验收第 2 条 `npx --yes spec-wave task lint-wiki-delta --target .` 未钉版，与 CI 钉 `spec-wave@3.0.1`（`.github/workflows/lint-wiki-delta.yml:35`）不一致。交接档 §4-4 口径为「仓级 verify 用最新（3.2.0 豁免机制）· CI 面钉 3.0.1」，lint-wiki-delta 属 CI 面——建议收口执行时对该命令对齐钉版或在实现备忘注明所用版本，避免 `npx --yes spec-wave` 拉到未来新版引入口径漂移。
- **N3（信息级）**：本 worktree 无 `node_modules/`，镜像锚点复核在主仓 checkout（`~/Desktop/Ops-desk/ops-desk-api`）完成；上游锚点已在源码层直接复核通过，镜像行弱化为旁证，非独立真值源。

## 阻塞项

**内容阻塞：零。** 流程闸 pending 见「结论与签收」节分列，属维护者签闸面，非内容缺陷。

## 回填清单

无（零内容阻塞 · 无需退回 10-task 修订）。

---

## 维护者签闸（20 后 · 30 前）

- [ ] 已读 R1 审查结论
- [ ] 在 task 人工闸表将 HG-AUDIT-R1 改为 approved（维护者 · 日期）
- [ ] commit task 文档或确认已签
- [ ] 再下发 Harness 30 Prompt

30 Agent 将以 task 表为准；pending 时必须拒开工（见 TEMPLATE_30_gate_stop.md）。

---

## 修订记录

| 日期 | 说明 |
|------|------|
| 2026-10-11 | 20 R1 审查落址A：结论 PASS-WITH-NITS · 零内容阻塞 · 十项核对全过（上游锚点亲读复核 @ fad4694 · 址B 命名 9/9 抽样 · 钉版三处 · task lint PASS）· NIT 三条登记 · 三闸 pending 待维护者签 |
