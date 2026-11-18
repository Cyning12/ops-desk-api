# invoke · 10 起草 · p4-t6-run-tree-ddl

> **task_slug**：p4-t6-run-tree-ddl
> **日期**：2026-11-18
> **授权**：issue Cyning12/ops-desk-workspace#23（m03796 夜间预授权 · 委派书 p4-t6-run-tree-ddl）

## 内容

1. 落卡 docs/tasks/active/task_p4_t6_run_tree_ddl.md（体例照 docs/tasks/done/task_p2c_t1_planner_tool_awareness.md）：Harness 元信息表（task_slug/base=cfe76b23/关联 issue/wiki_delta n/a/graph_change_layer G-L1/review_hat 20）· 人工闸表三行 approved · 背景（19 §7.1-§7.4 + §11.4/§11.5 契约锚）· 范围 8 条 · 非范围 6 条 · 失败路径 8 条 · 验收标准 9 条 · 必读列表 · 思考轮控制表 + R0-R5（actual_last_round=R5）· 偏差登记 2 条。
2. 勘察结论入档：契约 19 §7.2 SQL 逐字（三列 + uq 部分唯一 + idx parent · 无 FK 无 DB CHECK）；claim 须新写 ON CONFLICT 路径（14 R10 同事务撞 uq abort 教训 · create_run check-then-insert 不复用）；归属从父行取值（18 §8.2）；投影加性豁免零 diff（19 §11.5）。
3. 关键决策定稿：claim_child_run 返回 (run_id, created) 二元组（created 供 T7 worker 启动判定 · 本波不消费签名预留）；深度硬上限由 claim 层断言承载；图谱登记落 lg_rag 行（无独立 db 行 · 承 p2c-t1/fix-434 先例）。
4. registry entry（status=active · base=cfe76b23 · allowed_app_files=[app/db/models.py, app/ops/lg_rag/run_store.py, app/ops/lg_rag/runs_router.py] · banned_prefixes=[scripts/] 因触 alembic/）。
5. R1 审查文 docs/harness/reviews/task_p4_t6_run_tree_ddl_audit_R1_20261118.md（GO · PASS 机读词 · 仓规条款一遵守）。

## 验证台账

| 检查 | 结果 |
|------|------|
| npx --yes spec-wave@3.5.0 task lint --file docs/tasks/active/task_p4_t6_run_tree_ddl.md | PASS（W3 自检结论占位 draft 期合法 · close 前回填） |
| 真 PG 可达 | pg_isready + psql select 1 实证（postgresql://ops:***@localhost:5432/opsdesk_test） |
| worktree/分支 | .agents/worktrees/p4-t6-run-tree-ddl · branch p4-t6-run-tree-ddl · base cfe76b23（git fetch 核实 master 尖一致） |

## 偏差

2 条（task 档偏差登记 · 契约优先于委派书转述）：① 无独立 db 行 → lg_rag 行登记；② 无 DB 层 CHECK → claim 层断言承载。

## 结果

10 起草完成 · R1 审查文 GO · 进 30 实施。