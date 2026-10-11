# CLOSE：specwave-verify-baseline（2026-10-11）

> **task**：[`../done/task_specwave_verify_baseline.md`](../done/task_specwave_verify_baseline.md)（已归档 done/）
> **类型**：仓级 chore（文档合规 · SPEC §9 序3 · 维护者令 2026-10-11 立项）
> **关账日期**：2026-10-11 · 帽位：CLOSE

---

## 一 · 任务信息

| 项 | 值 |
|----|----|
| task_slug | `specwave-verify-baseline` |
| 依据 | `docs/spec/hitl-approval-consumption/SPEC-hitl-approval-consumption_v1.md` §9 序3（仓级 verify EXIT=2 BLOCKED 92 缺口 · 实跑复核 93）· T1 40 钉案③ |
| 目标 | 仓级 `npx spec-wave verify` EXIT=0 PASS（经明示豁免清单）· 增量门禁恢复预警力 · 存量处置口径诚实（**禁伪造审查**） |
| 帽链 | 10-task（00 代笔落稿 f992fff）→ 20-task-audit R1 BLOCKER（B-1 · lint FAIL E3/E4/E5/E8）→ B-1 修订（fe51492）→ R2 PASS-WITH-NITS（559d24a）→ 三闸 approved（维护者授权 m01606/m00255 · 00 代录）→ 30 实现 → 40 复核 PASS → PR #228 → CLOSE |
| 缺口构成 | 93 = done/ 154 档中的不合规集：36 零审查档（missing R<n> review）+ 39 无结论/签收节 + 13 否定结论词 + 5 缺审查行为陈述（SUBJ）（30 棒 TC1 分账 · 与实跑输出 1:1 对账） |

## 二 · 交付

| 环节 | 实证 |
|------|------|
| PR | [#228](https://github.com/Cyning12/ops-desk-api/pull/228) · **MERGED · squash commit `5204330`**（2026-10-11 · base master `cae745e`） |
| 豁免清单 | `docs/harness/legacy-gate-exempt.yaml`（+383 · **存量 93 档逐枚列入** · spec-wave 原生豁免机制 failClosed · 四字段 slug/reason/date/authorized_by · reason 统一「存量基线豁免 · 未审」· authorized_by 93/93 过 A1 三元判） |
| 双址规约 | `docs/harness/CONVENTION_review_gate_dual_address_v1_zh.md`（+167 · 五节：工具口径实证（verify 仅扫址A 钉死）/ 双址分工裁定（D2 落钉 · 址A=verify 唯一消费址 · 址B=书面审存档址）/ 豁免清单规约 / EXIT 码自证口径（D3）/ TC1 基线全表 93 明细行） |
| diff 面 | 30 棒三 commit（d704c35→72ab71f→db6aa53）= 4 档；全分支对 master 9 档**全在 docs/** · done/ 与 reviews/ 133+ 既有档零触碰 · 零业务码（钉死契约 1/4/5 成立 · 40 V1 实证） |
| invokes | `docs/harness/invokes/by-task/specwave-verify-baseline/`（10 落稿 / 20 R1 / 20 R2 / 30 实现 / 40 复核 · 本 CLOSE 补 50） |
| **CLOSE 增量** | task 归档 done/（状态行/验收勾选/修订记录回填）· 审查文 R1/R2 按规约 §二 过渡期口径**复制落址A**（`docs/harness/reviews/task_specwave_verify_baseline_audit_R{1,2}_20261011.md` · 互参注记 · 址B 原件原址原内容不动）· active/done README 双侧补登 · 本档 |

## 三 · 核验结论（40 PASS · 独立复核不轻信自述）

40 复核五验全绿（详见 [40 invoke](../../harness/invokes/by-task/specwave-verify-baseline/invoke_20261011_40_verify.md) · 全程亲跑留证 /tmp/verify_40_*.txt）：

- **V1 · commit 链/diff 面** ✅：30 三 commit 与自述 1:1 · 全分支 9 档全 docs/ · done/ 与 reviews/ 零触碰 —— 最小面成立。
- **V2 · verify 重跑** ✅：`npx --yes spec-wave@3.2.0 verify --target . > /tmp/verify_40_baseline.txt 2>&1; echo EXIT=$?` → **EXIT=0 · VERIFY: PASS** · 豁免命中 93 · invalid 0；抽验 3 档（inform-graph-backfill-w6-modules-trim 零审查档 · capability-gateway-p3/so-schema-hygiene 无结论节）缺口皆实证 —— 豁免清单非乱列。
- **V3 · TC3 反向实证（增量门禁力证 · 40 亲跑）** ✅：藏豁免档 → **EXIT=2 BLOCKED 缺口 93** → 恢复 → **EXIT=0 PASS** · 工作区零残留 —— 清单一撤全量红复现、清单在位精准转绿，增量预警力完整。（30 棒正实证：临时不合规档 `task_tc3_tmp_noncompliant_probe.md` 单点红逐字指向 → 撤档复绿。）
- **V4 · TC4 诚实性** ✅：93 条目 reason 统一「存量基线豁免 · 未审」· authorized_by 93/93 A1 合规形态 · 「未审」语义钉规约 §三.2 · 契约 2（禁伪造审查）成立。
- **V5 · TC2/TC5 反回归** ✅：lint-wiki-delta EXIT=0 PASS 复跑 · 既有档零 diff · 分支对 master 非 docs/ 改动数=0 → pytest 失败集构造性恒等（同一代码+同一测试 · 40 采信此论证未烧预算双跑）。

**CLOSE 质量钉复跑（本帽 · 归档后仓态）**：

- `npx --yes spec-wave@3.2.0 verify --target . > /tmp/close_verify.txt 2>&1; echo EXIT=$?` → **EXIT=0 · VERIFY: PASS**（重定向取真码 · 挪档 done/ 后本 task 审查文已由址A 复制件供门禁消费 · 零新增缺口）。
- `npx --yes spec-wave task lint --file docs/tasks/done/task_specwave_verify_baseline.md` → **EXIT=0 · LINT: PASS**（done/ 路径复跑 · W4 思考轮节 warn=chore 轨合法豁免 · R1 起同口径）。

## 四 · 偏差与 nit（如实照登）

1. **30 invoke 76-77 占位语残留（nit · 不阻 PASS）**：`invoke_20261011_30_implement.md` 思考轮 8 行 76-77 残留「（回填中）」占位语（TC5a/TC5b 行）——task 档自检结论已如实回填完成态；invoke 为过程留痕 · 40 不改 30 交付档 · 照登备查（40 invoke Nit 节在案）。
2. **诚实声明：豁免 ≠ 审查通过**：93 档豁免语义 = 「未在址A 落可机读通过审查档」（规约 §三.2），覆盖「根本无审查文」与「审查文存在但未达机读口径/未落消费址」两类；**存量 93 在真补审前永不合规**，绿灯是明示基线豁免的产物而非审查结论（钉死契约 2 · 禁伪造审查）。
3. **上游根治留后续**：verify 审查门禁消费面仅扫 `docs/harness/reviews/` 与 `reviews/` 两址（spec-wave `src/checks/review-gates.ts` `findLatestReview` 源码在案）· `docs/audits/task-review/`（址B）完全不入扫描面。本 task 非范围已钉「不改上游 verify 规则」→ 过渡期以「复制审查文落址A」承载（本 CLOSE 对 R1/R2 已执行）；**上游支持址B 扫描后规约届时修订**。
4. **误报先例在案（规约 §一）**：`task_hitl_auto_resume_claim_race.md`（done）审查文只落址B → 列入本 task 基线 93 缺口（missing R<n> review）；B1/B2 两 task 同形 · 已裁定各棒复制审查文回旧址过渡 —— 本 CLOSE 循同例。
5. **管道吞码坑（D3 复证）**：`verify | tail` 吞 EXIT=2 报 0（T1 30 棒前科 · 本 task 实证复现：管道 0 vs 真值 2）；40 棒 TC3 首跑 `set -e` 在 EXIT=2 处中止致恢复语句未执行 —— EXIT 码须显式处理，凡引 verify EXIT 一律重定向取 `$?` 或 pipefail（规约 §四 已钉）。
6. **D1 落案偏差照登**：10 落稿倾向 C 混合（近期补审 + 古早豁免）；经 20 探查豁免机制原生支持后，实际落案为**纯豁免清单**（93 全豁免 · 近期/高价值档真补审臂未执行）——候选开放不锁死留 20 审之裁定结果，非越界；真补审诉求见后续建议。

## 五 · 签录（闸与审查文链）

| 环节 | 文档 / 实证 |
|------|------------|
| 人工闸 | HG-TASK-DRAFT / HG-AUDIT-R1 / HG-GRAPH-MODULES 三闸 **approved**（2026-10-11 · 维护者授权 m01606/m00255 · 00 代录 · task 人工闸表为真值）· HG-PILOT-OPSDESK-GLAYER n/a |
| 20 R1 审查 | 址B 原件 `docs/audits/task-review/20261011_specwave-verify-baseline_r1.md`（BLOCKER 退修订 · B-1 lint FAIL E3/E4/E5/E8 · 豁免机制原生支持实证闭环 · N-1~N-3 照登）· 址A 过渡复制件 `docs/harness/reviews/task_specwave_verify_baseline_audit_R1_20261011.md`（本 CLOSE 落） |
| 20 R2 审查 | 址B 原件 `docs/audits/task-review/20261011_specwave-verify-baseline_r2.md`（**PASS-WITH-NITS** · B-1 四缺落地零越界 · lint EXIT=0 亲跑复证 · N-4 照登已由修订棒吸收）· 址A 过渡复制件 `docs/harness/reviews/task_specwave_verify_baseline_audit_R2_20261011.md`（本 CLOSE 落 · verify 按最高 R 轮消费此件） |
| invokes | `docs/harness/invokes/by-task/specwave-verify-baseline/`：10_task_draft / 20_task_audit_r1 / 20_task_audit_r2 / 30_implement / 40_verify / 50_close（本 CLOSE 落盘） |
| 合并 | PR [#228](https://github.com/Cyning12/ops-desk-api/pull/228) MERGED 2026-10-11 · squash `52043307185fb6125d9a07f68aaaf15e306569a2` |

## 六 · 资源清理

- **已清**：TC3 探针档与 40 藏档零残留（30/40 各自实证 `git status` 干净 · yaml 字节复原 16935B）；本 CLOSE 工作区仅本档所述 diff。
- **待清（留 00/维护者）**：worktree `t-specwave-verify-baseline` 与本地/远端分支 `task/specwave-verify-baseline`、`close/specwave-verify-baseline`——本 CLOSE 在该 worktree 内作业无法自清，且 CLOSE PR 未合并前 close 分支在役；**CLOSE PR 合并后**：`git worktree remove` + 删除两条分支（task 分支已 squash 合入 master `5204330` · 删除安全 · 远端分支一并清）。
- 先例对照：T1/T2 各 CLOSE 亦曾将 worktree/分支清理留 00 处理（active README 登记表在案）· 本件同口径。

## 七 · 后续建议

1. **上游根治（最高优先）**：spec-wave verify 支持址B（`docs/audits/task-review/`）扫描或仓内桥接——落地后撤「复制落址A」过渡口径并修订双址规约；在此之前，**凡审查文只落址B 的 task 归档 done/ 时必须复制落址A**（本 CLOSE 已立第二例，建议写入 50 棒定型流程）。
2. **存量 93 真补审（可选 · 另立 task）**：D1-C 的补审臂未执行——若维护者要求近期/高价值档（如 202609 后 done）真补审，须另立 task 且补录审查文如实标注「存量补录 · 非同期审查」（钉死契约 2 口径）。
3. **豁免清单防腐**：扩列须四字段齐 + PR 人审（task 失败路径表第 4 行）；每新增豁免即侵蚀增量门禁预警力，TC3 反向实证口径（藏档必红）可作为后续抽检模板。
4. **EXIT 码纪律**：凡验收/文档/invoke 引 verify EXIT 一律重定向取 `$?` 或 `set -o pipefail`（规约 §四）· 40 棒 `set -e` 中止事故复证该坑真实存在，建议 30/40 片段库固化取证模板。

## 八 · 修订记录

| 日期 | 说明 |
|------|------|
| 2026-10-11 | CLOSE 落稿（CLOSE 棒 · worktree `t-specwave-verify-baseline` · 分支 `close/specwave-verify-baseline` · base origin/master `5204330`）：九节沿仓内先例 · 质量钉复跑（verify EXIT=0 PASS · task lint PASS）后回填 · 审查文 R1/R2 复制落址A 过渡 |

## 九 · 附录

### 关键路径

| 类别 | 路径 |
|------|------|
| 豁免清单 | `docs/harness/legacy-gate-exempt.yaml`（93 条目 · 16935B） |
| 双址规约 | `docs/harness/CONVENTION_review_gate_dual_address_v1_zh.md` |
| 审查文（址B 原件） | `docs/audits/task-review/20261011_specwave-verify-baseline_r1.md` · `..._r2.md` |
| 审查文（址A 过渡复制件） | `docs/harness/reviews/task_specwave_verify_baseline_audit_R1_20261011.md` · `..._R2_20261011.md` |
| invokes | `docs/harness/invokes/by-task/specwave-verify-baseline/`（10/20r1/20r2/30/40/50） |
| 上游机制真值 | spec-wave `src/checks/exempt.ts`（D-23-W4-EXEMPT-FORMAT · F-W4-04）· `src/checks/review-gates.ts` `findLatestReview` |

### CLOSE 复跑命令留痕

```bash
npx --yes spec-wave@3.2.0 verify --target . > /tmp/close_verify.txt 2>&1; echo "EXIT=$?"   # EXIT=0 · VERIFY: PASS
npx --yes spec-wave task lint --file docs/tasks/done/task_specwave_verify_baseline.md       # EXIT=0 · LINT: PASS
```
