# invoke · 50 收尾（CLOSE 波）· p4-t6-run-tree-ddl

> **task_slug**：p4-t6-run-tree-ddl
> **日期**：2026-11-18

## 内容

CLOSE 登记：registry entry status active→closed + 钉 wave_tip=142723ee（feat PR #444 squash 合入）；task 档 docs/tasks/active/ → docs/tasks/done/ 迁移。

## 验证台账

| 检查 | 结果 |
|------|------|
| feat PR #444 | MERGED（squash 142723eecef8cac0fd58c6ebf0a2b5d373039d0b · 2026-11-18） |
| CI 四绿（feat PR · rebase 后终裁） | check 14s ✓ · import-linter 12s ✓ · lint-wiki-delta 13s ✓ · pytest 2m50s ✓ |
| 提交后 wave_gate 闭窗复跑 | 28 passed（test_wave_gate_registry + tc8/scenario diff 闸复绿确认 · 脏树期红为结构性） |
| committed 闭窗面 | base cfe76b23..wave_tip 142723ee = feat squash 单提交（14 文件 ⊆ allowed 三集合） |
| 并行冲突处置 | PR #443（p4-t2）先合 → CONFLICTING → rebase origin/master 保留双方 registry entry + 01_modules 双方备注/签收行 → 强推 → CI 四绿（委派书并行铁律） |
| task lint（迁 done 后） | npx --yes spec-wave@3.5.0 task lint --file docs/tasks/done/task_p4_t6_run_tree_ddl.md → 见本 PR CI |
| CLOSE PR CI | 见本 PR checks（终裁） |

## 偏差

- tests/test_lg_rag_runs_readonly_api.py 入改动面（§11.4 加性字段使既有键集精确断言必然更新 · registry 已补登）。
- 无 DB 层 CHECK（19 §7.2 SQL 逐字无 CHECK · 深度硬上限由 claim 层断言承载 · 委派书转述为「承载层」表述差异 · 已登记 task 档）。
- 图谱无独立 db 一级模块行 · 表级登记并入 lg_rag 行备注（承 p3-t3 签收行叙事先例 · 已登记 task 档）。
- 本地存量 opsdesk_test 手工幂等对齐三列两索引（create_all 不管 ALTER · 承 conftest 漂移补丁模式 · CI 全新库零代码面改动）。

## 结果

波次闭合：run 树 DDL（三列+uq 部分唯一索引+parent 索引）· claim_child_run 委派 claim（ON CONFLICT 幂等 · 归属从父行 · depth 断言）· runs 列表投影加性 parent_run_id/depth 已落 master；OPS_RUN_TREE_ENABLED 三件套与委派执行提升归 T7。
