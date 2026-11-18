# invoke · 40 验证 · p4-t3-manifest-domain-tags

> **task_slug**：p4-t3-manifest-domain-tags
> **日期**：2026-11-18
> **授权**：issue Cyning12/ops-desk-workspace#23（m03064/m03796 夜间授权 · 委派书 p4-t3-manifest-domain-tags）

## 内容

1. 全量验证重跑（40 波独立复跑非沿用 30 结果 · 五键 blank 前缀按 task 档测试策略 OPS_HITL_PERSISTENCE= OPS_CAPABILITY_ALLOW_WRITE= OPS_CAPABILITY_ALLOW_WRITE_TAGS= OPS_CAPABILITY_PERSISTENCE= OPS_CAPABILITY_EXTRA_MANIFESTS=）：目标三文件 45 passed · capability 电池 673 passed/5 failed · ruff 0.15.21 All checks passed · mypy manifest.py 2 errors（与 master 同 2）· lint-imports 12 kept 0 broken · graph-compile.sh done OK。
2. 电池零新增对账：capability 电池 5 failed 与干净 master 主 checkout 同路径基线**同 5 个**（comm 双向空集 · 顺序依赖既有 · 单跑均过）；worktree 673 = master 659 + 14（新文件用例数）。
3. 全量 pytest 本地对照结论（30 波登记 · 40 波复核有效）：solo 36 vs 32 · 差 5 全为 test_multi_replica_dualproc.py，实证孤儿 pytest 进程（pid 3801）与 dualproc 端口/DB 交叉污染——杀进程后双侧重跑该文件均 9 passed；31 个共有失败为本地环境性既有（CI pgvector:pg16 service 终裁）。
4. task 档 40 收口：验收标准 10 条全 [x]（逐条锚定测试用例/命令）· 自检结论回填（机制面九条断言 + 回归面 + lint 面 + CI 终裁口径）· 修订记录补 40 波行。
5. spec-wave@3.5.0 task lint PASS（自检结论占位已回填 · W3 警告消除）· spec-wave verify PASS（人工闸三行 approved · 图谱锚点检查 vocabulary_empty 跳过为既有常态）。

## 验证台账

| 检查 | 结果 |
|------|------|
| pytest 目标三文件 test_capability_manifest_domain.py + test_capability_manifest.py + test_capability_domain_allowlist.py（真 PG postgresql+asyncpg://ops:ops_password@localhost:5432/opsdesk_test · 五键 blank 前缀） | 45 passed in 0.58s |
| pytest -k capability 电池（同上前缀） | 673 passed / 5 failed——与干净 master 基线同 5 个（comm 双向空集）· 零新增 |
| ruff check app tests（/主仓 venv · 0.15.21 CI 钉版） | All checks passed |
| ruff format --check（本波两件） | 2 files already formatted（仓 81 件未 format 为既有面 · master 同 81） |
| mypy app/ops/capability/manifest.py | 2 errors = master 同 2（yaml stubs + untyped def :954→:1023 行号位移 · 零新增） |
| lint-imports | Contracts: 12 kept, 0 broken |
| scripts/graph-compile.sh | done OK |
| npx spec-wave verify --target . --task docs/tasks/active/task_p4_t3_manifest_domain_tags.md | VERIFY: PASS |
| npx --yes spec-wave@3.5.0 task lint --file docs/tasks/active/task_p4_t3_manifest_domain_tags.md | LINT: PASS |
| git 守卫两文件（post-commit 在途面清空） | tests/test_wave_gate_registry.py + tests/test_lg_rag_write_replay_guard.py 22 passed |
| allowed_app_files 单件对账（git show --stat 769f7126） | app/ops/capability/manifest.py 单件在白名单 · 零越界（测试/图谱/docs 属 allowed_tree_*） |

## 偏差

1. 承 30 登记：base 修正 370a137a → 297363bd（task 档偏差登记 1 · R0 裁定）· 无新增。
2. 全量 pytest 未本地复跑全绿（仓纪律：环境性红与 base 297363bd 同路径基线逐签对照 · CI 终裁）——目标面与 capability 电池对照零差异项。

## 结果

40 验证收口完成 · 验收 10 条全绿 · 进 feat PR（--body-file · 中文 · issue #23）→ CI 四绿 → squash merge。
