# invoke · 50 收口 · p4-t2-prompt-domain-loader

> **task_slug**：p4-t2-prompt-domain-loader
> **日期**：2026-11-18
> **授权**：issue Cyning12/ops-desk-workspace#23（m03064/m03796 夜间授权 · 委派书 p4-t2-prompt-domain-loader）

## 内容

1. feat PR #443（feat(p4-t2): prompt 模板域机制 · --body-file 中文 · ref issue Cyning12/ops-desk-workspace#23）CI 四绿（check 31s · import-linter 11s · lint-wiki-delta 10s · pytest 2m41s 全量终裁 pass）→ squash merge 6b2c7934（2026-11-18T01:06:25Z）。
2. registry entry 收口（docs/harness/audit_gates/registry.yaml:1264-1304）：status active→closed · 钉 wave_tip="6b2c7934"（merge squash commit · base cfe76b23 不动）。
3. task 档迁档：docs/tasks/active/ → docs/tasks/done/task_p4_t2_prompt_domain_loader.md（git mv）· 状态行 active→done（feat PR #443 squash merge 6b2c7934 · CI 四绿）· 修订记录补 CLOSE 行。
4. spec-wave verify + task lint 复跑（done 档路径）。

## 验证台账

| 检查 | 结果 |
|------|------|
| gh pr checks 443（check / import-linter / lint-wiki-delta / pytest） | 四绿 pass |
| gh pr merge 443 --squash --delete-branch | MERGED 2026-11-18T01:06:25Z · mergeCommit 6b2c7934 |
| master fast-forward 核实（git fetch · origin/master=6b2c7934） | 一致 |
| npx spec-wave verify --target . --task docs/tasks/done/task_p4_t2_prompt_domain_loader.md | VERIFY: PASS |
| npx --yes spec-wave@3.5.0 task lint --file docs/tasks/done/task_p4_t2_prompt_domain_loader.md | LINT: PASS |
| registry.yaml entry 机读（status=closed · wave_tip=6b2c7934 · 五件 allowed_app_files 与 feat diff 对账一致） | 一致 |

## 偏差

无新增（承 40 波登记三项：current_domain env 回落裁定 · render.py mypy 等体重构 · 目标回归文件名修正 · 均已在 feat PR 体如实登记）。

## 结果

P4-T2 prompt 模板域机制全波 CLOSE：机制面（loader 目录回退 / templates 薄封装 / domain_context / render 域路由 / worker 注入位 · 不建 assets/ops/）落 master 6b2c7934 · 19 §3.4 零 diff 对拍钉死 · registry closed · task done。后继波：P4-T3 manifest domain 消费 · P4-T4 RAG 域隔离 · P4-T5 oa 域资产（7 覆盖+4 刻意不覆盖）。
