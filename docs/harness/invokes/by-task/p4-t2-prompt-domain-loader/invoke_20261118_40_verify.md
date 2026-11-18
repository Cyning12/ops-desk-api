# invoke · 40 验证 · p4-t2-prompt-domain-loader

> **task_slug**：p4-t2-prompt-domain-loader
> **日期**：2026-11-18
> **授权**：issue Cyning12/ops-desk-workspace#23（m03064/m03796 夜间授权 · 委派书 p4-t2-prompt-domain-loader）

## 内容

1. 全量验证重跑（40 波独立复跑非沿用 30 结果）：pytest 六文件 144 passed · ruff 0.15.21 All checks passed · mypy 五件 Success · lint-imports 12 kept 0 broken · graph-compile.sh done OK。
2. spec-wave verify PASS（人工闸三行 approved · HG-GRAPH-MODULES 图谱两件已随 30 落盘）。
3. task 档 40 收口：验收标准 11 条全 [x]（逐条锚定测试/命令）· ### 自检结论 回填（机制面九条断言 · 19 §3.4 三态对拍 · 域路由 · worker 注入 · 回归面五命令全绿 · 全量 pytest CI 终裁）· 偏差登记两项落档 · 修订记录补 40 波行。
4. spec-wave@3.5.0 task lint PASS（自检结论占位节已回填 · W3 警告消除）。

## 验证台账

| 检查 | 结果 |
|------|------|
| pytest 六文件（真 PG postgresql+asyncpg://ops:ops_password@localhost:5432/opsdesk_test · 五键 blank 前缀） | 144 passed in 0.62s |
| ruff check app tests（/主仓 venv · 0.15.21 CI 钉版） | All checks passed |
| mypy 五件 app 文件 | Success: no issues found in 5 source files |
| lint-imports | Contracts: 12 kept, 0 broken |
| scripts/graph-compile.sh | done OK（freeze OPS_DESK_API_TECH_GRAPH_FREEZE_d8987aec487f27b2_V1） |
| npx spec-wave verify --target . --task docs/tasks/active/task_p4_t2_prompt_domain_loader.md | VERIFY: PASS |
| npx --yes spec-wave@3.5.0 task lint --file docs/tasks/active/task_p4_t2_prompt_domain_loader.md | LINT: PASS |
| 19 §3.4 零 diff 对拍（OPS_DOMAIN off / =ops / =不存在域目录 三态 · 全 11 模板 body 逐字节） | 一致（tests/test_prompt_domain_assets.py 对拍断言绿） |
| allowed_app_files 五件对账（git show --stat 46b3cea） | 五件全在白名单 · 零越界（+测试/图谱/docs 属 allowed_tree_*） |

## 偏差

1. **任务档「目标回归」清单文件名修正**：落卡误写 tests/test_prompt_render.py（不存在）→ 真名 tests/test_prompt_assembly.py；40 波按实修正三处（范围/必读列表/测试策略）并回归跑绿。文档落笔误差修正 · 不涉及范围变化（已登记 task 档偏差登记 2）。
2. 其余偏差承 30 登记两项（current_domain env 回落裁定 · render.py mypy 等体重构）· 无新增。
3. 全量 pytest 未本地全跑（仓纪律：环境性红与 base cfe76b23 同路径基线逐签对照 · CI 终裁）——目标面六文件全绿 · 无差异项待对照。

## 结果

40 验证收口完成 · 验收 11 条全绿 · 进 feat PR（--body-file · 中文 · issue #23）→ CI 四绿 → squash merge。
