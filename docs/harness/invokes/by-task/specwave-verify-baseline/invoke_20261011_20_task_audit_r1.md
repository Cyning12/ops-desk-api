---
hat: 20
task_slug: specwave-verify-baseline
date: 2026-10-11
---

# invoke · 20+task-audit R1 · specwave-verify-baseline（仓级 verify 缺口基线 chore）

## 审查摘要

- 审查文：`docs/audits/task-review/20261011_specwave-verify-baseline_r1.md`（新规约址 · R1 书面审 · 未改 task · 未代签闸 · 未切分支）。
- **裁定：BLOCKER 退修订**——内容面全正向（实跑复核 93=36+5+39+13 对账 ✓ · D1 倾向 C 成立 · 豁免机制原生支持实证闭环 `docs/harness/legacy-gate-exempt.yaml` failClosed 四字段 · 钉死契约 5 全可机验 · TC1-TC5 可证伪），但 task lint 亲跑 **EXIT=2 FAIL**（E3 缺 ## 验收标准节/E4 缺 failure_paths 节/E5 缺自检结论节/E8 缺 wiki_delta 行）→ B-1 退 10 修订，修订量小。
- N-1（done/ 154 vs 155 微偏）· N-2（豁免原生支持已闭环 · 30 免探）· N-3（D2 规约档名留 30 钉）照登不闸。
- 三闸（HG-TASK-DRAFT/HG-AUDIT-R1/HG-GRAPH-MODULES）维持 pending · 未代签。
- 实证留痕：verify 输出 /tmp/verify_baseline_r1.txt · lint 输出 /tmp/lint_r1.txt（verify TRUE_EXIT=2 重定向取码 ✓ 管道吞码坑未踩）。

## 过程

1. 读 task f992fff 全文 + 既有 audits/invoke 规约先例（20261010_hitl-auto-resume-claim-race_r1.md）。
2. 实跑复核：重定向取真 EXIT=2 · 明细 93 行 · 分类计数 36/5/(39+13) 与 task 分账一致 · 抽查 missing 档成立。
3. 豁免机制探查：verify 头行明示原生 yaml 口 + CLI --help 宽开关面 · 仓内清单档未建。
4. lint 亲跑 EXIT=2 FAIL → 裁定 BLOCKER。
5. 骨架先行 commit ee66dce → 填案 commit（本档与审查文同 commit）。
