# Task：P0' T4 run 实体化——ops_lg_rag_runs 一等实体表

> **状态**：in_progress（2026-11-14 起）  
> **类型**：新表 + 迁移 + 写路径挂钩（orphan 扫描改走 runs 表）  
> **关联图谱**：`docs/_tech_graph/l1/01_modules.md`（lg_rag 行备注 + 签收行）  
> **落盘**：`docs/tasks/active/task_p0prime_t4_run_entity.md`；验收后 `git mv` → `docs/tasks/done/`  
> **来源**：ops-desk-workspace `docs/01-scope/03-general-agent/06-kickoff-readiness.md` 任务卡 T4 + 裁定 A1（issue #23 Round 4 · 关键链 T1→T3→T4，T3 已闭环）

---

## Harness 元信息

| 字段 | 值 |
|------|-----|
| **task_slug** | `p0prime-t4-run-entity` |
| **test_strategy** | `required` |
| **test_strategy_note** | status 映射纯函数真值表单测（零 DB）；create/状态流转/stale 扫描/补行 DB 用例——**本地真 PG 实证**（brew postgresql@18 + ops/ops_password + opsdesk_test 已起，CI 无 PG 假绿缺口另记 issue #23）；orphan 补偿既有用例对齐两段式重写 |
| **code_quality_bar** | `recommended` |
| **orchestration** | P0' 任务卡 T4（关键链 T1→T3→T4 · T3 已闭环 1456f3b9/cc622403） |
| **semi_auto** | `false` |
| **audit_profile** | `human_only` |
| **invoke_retention_profile** | `default` |
| **required_invoke_hats** | `10,30,40` |
| **git_branch** | `task/p0prime-t4-run-entity` |
| **graph_change_layer** | `G-L1` |
| **graph_delta** | `note-only` |
| **graph_delta_note** | 不新增一级模块（run_store.py 归 lg_rag 行 `app/ops/lg_rag/**` 覆盖）；`01_modules.md` lg_rag 行备注 + HG-GRAPH-MODULES 签收行 |
| **wiki_delta** | `n/a` |
| **wiki_delta_note** | 本仓未启用 WikiTrack |
| **review_hat** | `20` |
| **close_pr_policy** | `required` |
| **experience_capture** | `recommended` |
| **kpi_rubric** | `KPI_RUBRIC_v1_2` |
| **kpi_aggregator** | `CLOSE` |

### 人工闸

| human_gate_id | status | blocks_hats | 说明 |
|---------------|--------|-------------|------|
| **HG-TASK-DRAFT** | approved | 22-R1, 30 | 维护者授权（issue #23 R4 评论 + 会话 m00177「签收，开始」） |
| **HG-AUDIT-R1** | approved | 30 | 维护者会话签收（m00177「签收，开始」，覆盖 P0' T1–T7 全部任务卡）；R1 审查文 `docs/harness/reviews/task_p0prime_t4_run_entity_audit_R1_20261114.md` |
| **HG-GRAPH-MODULES** | approved | 30 | 仅 lg_rag 行备注追加，不新增一级模块；签收行见 `01_modules.md` |

---

## 背景与目标

run 目前只是 `ops_lg_rag_run_events.run_id` 上的字符串标签，无一等实体：orphan 补偿须**全扫事件表**（`event_store.list_open_runs` closed_ids 排除 + group-by + join），未来 run 列表页/状态机/多副本判定无落点。R4 裁定 A1：新建 `ops_lg_rag_runs`（run_id String(64) PK 与事件表同型零迁移 · tenant_id 必填 · user_id FK · thread_id · status · created_at/finished_at），RunWorker start/finish 写入，`run_events.run_id` 不加 FK（orphan 补偿先扫事件后补 run 行，顺序容错），`uq(run_id,seq)` 不动。

**完成态**：

- [ ] `app/db/models.py` 新增 `OpsLgRagRun`（承既有 lg_rag 三表风格；tenant_id `String(64) NOT NULL DEFAULT ''` 承 ops_capability_notes 先例）。
- [ ] `alembic/versions/20261114_lg_rag_runs.py`：CREATE TABLE + (status, created_at) / (thread_id) 索引；down=DROP TABLE。
- [ ] `app/ops/lg_rag/run_store.py`（新建）：`create_run` / `status_for_event` 纯函数 / 状态更新 / `list_stale_running_runs` / `backfill_missing_run_rows`。
- [ ] `event_store.persist_run_event` 收口：事件提交后 best-effort 状态流转（独立 try 吞错+日志，**绝不反噬事件插入**——现行「落盘失败不阻断 SSE」零 diff）。
- [ ] `run_worker.start_run_worker` `_main` 起始建行（单飞复用不重复建；`user_id` 缺失跳过，与 persist 的 user_id 门一致）；`scan_orphan_runs_for_compensation` 两段式重写。
- [ ] 测试：`tests/test_lg_rag_run_store.py` 新建；`tests/test_lg_rag_sse_run_worker.py` orphan 用例对齐。
- [ ] 图谱备注 + 签收行；registry N3 entry；invoke 10/30/40；R1 审查文。

**设计裁定（30 勘察钉死）**：

1. status 词表镜像 done payload 逐字落列：`running` → `waiting_approval`（非终态）/ `done` / `resumed` / `disconnected` / `error`（四者终态置 finished_at）；`hitl.resumed` 帧 → 回 `running` 清 finished_at。
2. 状态更新唯一挂点 = persist 收口（覆盖主段 sse_stream、恢复段 hitl/resume.py:92、补偿帧 run_worker.py:218 三路写者）。
3. `/invoke` 同步路径无 RunWorker 不落 run 行（A1 范围外，记注）。
4. orphan 扫描两段式：① runs 表主扫 `status='running'` + created_at 预筛 + per-run 末帧精确 stale（有界 ≤limit，保末帧活跃语义防长 run 误伤）+ `is_run_worker_active` 过滤 + `run_stream_closed` 防漂移守卫保留；② events 无 run 行的 open run 反连接出有界补行（tenant_id='' 记注），下轮主扫接管。
5. 已知权衡：终帧事件成功而状态更新失败 → 残留 `running` 由扫描+守卫兜住；反向（状态终态而事件丢失）概率等同现行事件丢失，不硬修。

## 范围

`app/db/models.py` · `alembic/versions/20261114_lg_rag_runs.py`（新建）· `app/ops/lg_rag/run_store.py`（新建）· `app/ops/lg_rag/event_store.py` · `app/ops/lg_rag/run_worker.py` · `tests/test_lg_rag_run_store.py`（新建）· `tests/test_lg_rag_sse_run_worker.py` · `docs/_tech_graph/l1/01_modules.md` · registry/invokes/审查文/本 task 单。

## 非范围

- `ops_goals`（T5 另卡）；checkpointer 语义（T3 已闭环不再动）；run_events 加 FK / uq 变更；/invoke 路径 run 落行；freeze 帧格式任何变更；ops_runs/ops_run_events 旧表（T2b 另卡）。

## 失败路径

| 失败 | 语义 |
|------|------|
| 建行失败（DB 抖动） | best-effort 吞错+日志，run 走补行子路径兜底（A1 顺序容错） |
| 状态更新失败 | 独立 try 吞错+日志，事件插入不受影响；残留 running 由扫描+run_stream_closed 守卫兜住 |
| 迁移 down | DROP TABLE IF EXISTS，幂等 |
| 代码回滚 | 全部挂钩 best-effort，回滚后无残留写失败；事件表路径零 diff |

## 验收标准

- [ ] 迁移 up/down 本地真 PG 实证通过（`alembic upgrade head` / `downgrade -1` 输出随 invoke_40 登记）。
- [ ] 新单测真值表 + DB 用例本地真 PG 全绿。
- [ ] `tests/test_lg_rag_sse_run_worker.py` orphan 用例绿（两段式语义等价：有帧无终帧且无活跃 worker → 补 done{disconnected}）。
- [ ] 干净 worktree（无 .env）全量 pytest 零红；ruff 绿；graph-compile 过；spec-wave task lint PASS。
- [ ] replay/resume 回归件全绿（freeze lg-rag-sse-v1 零帧变更）。
- [ ] registry entry 登记（base=cc62240 · banned_prefixes 空——本波次含 alembic/ 迁移文件）。

## 给执行帽的必读列表

- `docs/tasks/done/task_p0prime_t3_checkpointer_default_on.md`（承继体例 + .env 污染教训）
- `app/ops/lg_rag/event_store.py`（persist 收口 :63-90 · list_open_runs :281-340 · run_stream_closed :161）
- `app/ops/lg_rag/run_worker.py`（start :93-165 · scan_orphan :185-238）
- `app/db/models.py:291-343`（lg_rag 三表风格）· `alembic/versions/20261105_capability_notes.py`（迁移风格）
- workspace `06-kickoff-readiness.md` 卡 T4 + 裁定 A1

## 思考轮控制

| 轮 | 结论 | early_stop |
|----|------|-----------|
| R0 | run 无实体 → orphan 全扫事件表 + 状态机无落点 | 否 |
| R1 | 收口挂载 + 两段式扫描（见设计裁定 6 条） | 否 |
| R2 | 模型/迁移/存储/worker/测试五竖切 | 否 |
| R3 | 全挂钩 best-effort；迁移 down 幂等 | 否 |
| R4 | 纯函数零 DB 单测 + 真 PG DB 用例 + 全量干净环境 | 否 |
| R5 | 验收 6 条过 → 交付 | 否 |

### R0 · 问题框定

run 仅事件表标签，无一等实体；A1 裁定新建 `ops_lg_rag_runs`。

### R1 · 开工闸

三闸 approved（见人工闸表）；设计裁定 6 条钉死挂载点与扫描形态。

### R2 · 竖切

模型 → 迁移 → run_store → event_store 收口 → run_worker 两段式 → 测试。

### R3 · 失败语义

见失败路径表；核心红线：状态更新绝不反噬事件插入。

### R4 · 可测性

status 映射纯函数零 DB；DB 用例本地真 PG 实证（brew postgresql@18 已起）；CI 假绿缺口登记 issue #23。

### R5 · 交付判定

验收 6 条全过 + PR CI 绿 + CLOSE 波次。

### 自检结论

（40 验证回填）

## 实现备忘（子 Agent 回填）

（30 实施回填）

### 自检结论（执行者）

（30/40 回填）

### 经验总结

（50 回填）

## 测试策略（Harness）

见 Harness 元信息 test_strategy_note；新增 DB 用例遵循 conftest 隔离（`opsdesk_test` · create_all 自动含新模型）。

## 修订记录

| 日期 | 修订 |
|------|------|
| 2026-11-14 | 初版落盘（30 勘察后：设计裁定 6 条钉死） |

## 实现备忘（30 回填 · 2026-11-14）

- 偏差 1：`.importlinter` 不在原 allowed 面 —— lg-rag-outbound 契约 forbidden 含 `app.db`，新模块 `run_store.py` 须补 ignore 白名单两条（承 `event_store`/`thread_store` 先例，逐条带理由）；registry allowed_tree_files 同步补 `.importlinter`。
- 偏差 2：本地 brew postgresql@18 已起 + `opsdesk_test` 库就绪 → DB 标记用例本地真跑（此前全 skip）；迁移 up/down/up 于 scratch 库 `opsdesk_t4mig` 真 PG 实证（vector/uuid-ossp 扩展需超级用户预建）。
- 教训：`now_utc` 真值在 `app.db.models:27`（非 app.core.time）；import-linter forbidden 契约对函数内 lazy import 同样生效，先例是 ignore 白名单而非绕开。
