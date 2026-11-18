# invoke · 10 起草 · p4-t7-delegate-child-run

> **task_slug**：p4-t7-delegate-child-run
> **日期**：2026-11-18
> **授权**：issue Cyning12/ops-desk-workspace#23（m03796 夜间预授权 · 委派书 p4-t7-delegate-child-run）

## 内容

1. 落卡 docs/tasks/active/task_p4_t7_delegate_child_run.md（体例照 docs/tasks/done/task_p4_t6_run_tree_ddl.md）：Harness 元信息表（task_slug/base=297363bd/关联 issue/wiki_delta n/a/graph_change_layer G-L1/review_hat 20）· 人工闸表三行 approved · 背景（19 §8-§13 契约锚）· 范围 8 条 · 非范围 7 条 · 失败路径 11 条 · 验收标准 9 条 · 必读列表 · 思考轮控制表 + R0-R5（actual_last_round=R5）· 偏差登记 1 条。
2. 勘察结论入档：契约 19 §8.1 闸开分支（type=tool→claim+spawn+轮询 join · rag/extract 留图内 · plan-JSON 零新 type）；§8.4 三层预算（深度 1 硬上限 + MAX_CHILDREN 默认 8 claim 前 COUNT + MAX_SUBTASKS=4 不动 · 配额键=父根 run_id）；§9 令牌五行表（事件/HITL 单据 run_id=子 · token binding=子 run_id/子任务 id 子侧自发签发 · cap_ctx 预算键=父根 · _approval_consumed 键=(子 run_id, subtask_id, capability_id)）；§10 HITL 三段（waiting_approval 退出不占槽 → resume 按 run 行 depth 分流 → 重跑 _approval_consumed 命中放行 fail-closed）；§11 帧面零新增（run.start 加可选 parent_run_id）；§12 总闸词表 off/on 非法回退 off+warning；§13 失败路径十行表。
3. 关键决策定稿（task 档 R3）：执行体提取 _run_tool_capability 闸链单真源（18 §3.4 · tool_exec_node/execute_delegate_subtask 双调用面共享）；resumed 重跑 seq 续 last_seq（承 ResumeEventSink 纪律 · 防撞 uq_ops_lg_rag_run_events_run_seq）；depth 分流位在 hitl/router._execute_decided_resume/_preflight_decided_resume（19 §10②逐字 · _open_event_sink 前）；run.start 加 delegate_spec 加性键（resume 重跑规格重建 · §11.5 加性豁免）；轮询 1.0s 常量不做 env；建单 pending 去重（同 run_id+subtask_id）；registry banned_prefixes=[alembic/, scripts/]（本波不触 alembic）；GUIDE_env_inventory 不登记（承 p4-t2 OPS_DOMAIN 先例）。
4. registry entry（status=active · base=297363bd · allowed_app_files 七件=[app/ops/hitl/router.py, app/ops/lg_rag/event_store.py, app/ops/lg_rag/multi/graph.py, app/ops/lg_rag/multi/nodes.py, app/ops/lg_rag/run_store.py, app/ops/lg_rag/run_worker.py, app/ops/lg_rag/sse_stream.py] · banned_prefixes=[alembic/, scripts/]）。
5. R1 审查文 docs/harness/reviews/task_p4_t7_delegate_child_run_audit_R1_20261118.md（GO · PASS 机读词 · 仓规条款一遵守）。

## 验证台账

| 检查 | 结果 |
|------|------|
| npx --yes spec-wave@3.5.0 task lint --file docs/tasks/active/task_p4_t7_delegate_child_run.md | 见 invoke_40（draft 期 W3 自检结论占位合法 · close 前回填） |
| 真 PG 可达 | 测试电池实证（postgresql://ops:***@localhost:5432/opsdesk_test · 10 用例全 pass） |
| worktree/分支 | .agents/worktrees/p4-t7-delegate-child-run · branch p4-t7-delegate-child-run · base 297363bd（master 尖 · T6 已合 142723ee） |

## 偏差

1 条（task 档偏差登记）：GUIDE_env_inventory 不登记 env 三件套（承 p4-t2 OPS_DOMAIN 先例 · env 注记入图谱行备注）。

## 结果

10 起草完成 · R1 审查文 GO · 进 30 实施。
