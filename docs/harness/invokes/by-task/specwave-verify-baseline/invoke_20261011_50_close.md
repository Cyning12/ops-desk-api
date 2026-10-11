---
hat: 50
task_slug: specwave-verify-baseline
date: 2026-10-11
---

# invoke · 50+CLOSE · specwave-verify-baseline（仓级 verify 缺口基线收口 · SPEC §9 序3）

## 收口结论

- 链路全通：10-task 落稿（00 代笔 f992fff · 实跑真值 EXIT=2/93 缺口三类分账）→ 20-task-audit R1 BLOCKER（B-1 lint FAIL E3/E4/E5/E8）→ B-1 修订 fe51492 → R2 PASS-WITH-NITS（559d24a · N-4 照登吸收）→ 三闸 approved（维护者授权 m01606/m00255 · 00 代录）→ 30（d704c35 豁免 yaml → 72ab71f 双址规约+task 自检 → db6aa53 30 invoke）→ 40（PASS · V1-V5 全绿 · TC3 反向实证亲跑红绿）。
- PR [#228](https://github.com/Cyning12/ops-desk-api/pull/228)：MERGED 2026-10-11 · squash `5204330`（base master `cae745e`）。
- 归档：task → done/（头部状态 done · 验收 TC1-TC5 勾选 · 修订表 CLOSE 行）；active README 登记表补行；done README Hub harness 域表行+修订记录行补登；CLOSE 文档 `docs/tasks/close/close_specwave_verify_baseline_20261011.md` 落盘。
- 双址过渡：审查文 R1/R2 复制落址A（`docs/harness/reviews/task_specwave_verify_baseline_audit_R{1,2}_20261011.md` · 互参注记）——规约 §二 过渡期口径「新增审查文必须落址A」· 址B 原件不动 · verify 按最高 R 轮消费 R2（PASS-WITH-NITS 机读口径满足）· 先例 B1/B2 同（规约 §一 误报实证 2）。

## 交付摘要

| 项 | 内容 |
|---|---|
| **产出** | `docs/harness/legacy-gate-exempt.yaml`（存量 93 档豁免 · 四字段 · failClosed · reason 统一「存量基线豁免 · 未审」）+ `docs/harness/CONVENTION_review_gate_dual_address_v1_zh.md`（双址规约 v1 · 五节） |
| **验收** | TC1 93 档逐档对账（36 零审查档+39 无结论节+13 否定结论词+5 缺 SUBJ）· TC2 verify EXIT=0 PASS（豁免命中 93 · invalid 0）· TC3 反向实证双棒亲跑（30：临时档单点红→撤档复绿 · 40：藏豁免档→BLOCKED 93→恢复 PASS）· TC4 诚实性机查 · TC5 反回归（pytest 构造性恒等 + 既有档零 diff） |
| **红线** | 零业务码 · 既有 133+ 合规档零 diff · done/ 档本体零改（钉死契约 1/4/5）· 禁伪造审查（契约 2 · 豁免≠审查通过钉规约 §三.2） |

## 钉案登记（详见 CLOSE 文档第四节）

1. 30 invoke 行 76-77「（回填中）」占位语残留——过程留痕不改 · 照登备查。
2. 豁免 ≠ 审查通过：存量 93 在真补审前永不合规 · 绿灯=明示基线豁免产物。
3. 上游根治留后续：verify 仅扫址A（review-gates.ts findLatestReview）· 址B 不入扫描面 → 过渡期复制落址A（本 CLOSE 已立第二例）· 上游支持后规约修订。
4. 管道吞码坑：verify | tail 吞 EXIT=2 报 0 · 40 棒 set -e 中止事故复证 · 凡引 EXIT 重定向取 $?（规约 §四）。
5. D1 落案偏差：倾向 C 混合 → 实际纯豁免（B 案）· 真补审臂未执行 · 留维护者另立 task。

## 质量钉（CLOSE 机械闸复跑）

- 仓级 verify：`npx --yes spec-wave@3.2.0 verify --target . > /tmp/close_verify.txt 2>&1; echo EXIT=$?` → **EXIT=0 · VERIFY: PASS**（挪档 done/ 后零新增缺口 · 址A 复制件供门禁消费）。
- task lint：`npx --yes spec-wave task lint --file docs/tasks/done/task_specwave_verify_baseline.md` → **EXIT=0 · LINT: PASS**（W4 思考轮节 warn=chore 轨合法豁免）。
- graph-compile：本 CLOSE 无图谱变更（task graph_delta=none）· n/a。

## 移交

- active 目录余 `task_repo_logging_init.md`（序2 · PR #227 已合 · 其 CLOSE 另棒处理 · 非本棒面）。
- worktree `t-specwave-verify-baseline` 与 task/close 分支待 CLOSE PR 合并后由 00/维护者清理（本 CLOSE 在该 worktree 内作业无法自清 · CLOSE 文档第六节在案）。
- 仓级 verify 基线收口后：`docs/tasks/done/` 新增归档必须址A 有可机读通过审查文或合法豁免，否则 verify 红（增量门禁预警力已恢复 · TC3 实证）。
