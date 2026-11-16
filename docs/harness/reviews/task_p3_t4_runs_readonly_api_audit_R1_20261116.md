# task_p3_t4_runs_readonly_api · R1 审查文（20 帽）

- 时刻：2026-11-16
- 审查人：exec-p3-t4（20 帽 · 夜间授权 issue Cyning12/ops-desk-workspace#23 m03064/m03283 · 00 代签体系）
- 对象：`docs/tasks/active/task_p3_t4_runs_readonly_api.md` v1

## 审查项

1. **范围对账**：task 范围 6 条与 15-p3-contracts.md v1 终稿（commit 62af6ea）
   §3.1 runs 列表（keyset created_at desc,run_id · limit 默认 20 上限 50 R-P3-8
   超限 422 · cursor max_length=512 · 投影 run_id/thread_id/status 六词表原值/
   created_at/finished_at/query_summary 截 80/schedule_attribution 三元组批量
   反查防 N+1）+ §3.2 events（assert_run_owned 404 · 白名单 8 值 · 500 帧截断
   truncated+next_after_seq · after_seq · 事件对象四字段）+ §0 冻结词表 +
   §4.1 fires 表结构 + §4.4 归因真源（fires 台账唯一 · query 前缀文本非依据）
   1:1 落入；委派书 m00002 内联面（双用户 404 矩阵 · 白名单断言 · 分页/截断 ·
   空 run · 图谱行备注+签收行）全部锚定。GO。
2. **非范围**：fires/schedules DDL 与 ORM（T2）· schedules CRUD（T3）· runs
   写路径（T5）· SSE 写路径 · event_type/status 词表修补 · 前端/iOS 均明示
   排除；banned_prefixes=[alembic/, scripts/]。GO。
3. **白名单过滤落点裁定（SQL 层）**：500 帧截断语义须按白名单后帧计数——
   响应层过滤会页内欠载（取 500 滤后不足）且内部帧存在性可经截断形状侧漏；
   SQL 层 WHERE event_type IN 8 值使非白名单 payload 不进应用内存=防泄最小面。
   §3.3 已核实现落库词表恰=freeze 词表，白名单=前置防泄层（未来内部帧零改动
   拦截）非词表修补，裁定与契约意图一致。GO。
4. **thread 归属真源裁定（thread SoT）**：runs 列表归属校验取
   thread_store.thread_owner（ops_lg_rag_threads.user_id）而非事件表真源——
   契约 §3.1 用词与 §1.7 schedule 归属同源；空 thread（零事件）经事件表真源
   会得 None→404 误伤，应 200 空列表。理由成立。GO。
5. **schedule_attribution 容错反查（R-P3-T4-1）**：fires 表随 T2 并行未落地——
   raw SQL 契约钉名 ops_schedule_fires JOIN ops_schedules · run_ids IN 单次
   查询防 N+1 · try/except UndefinedTable → 空归因+warning（表在即生效零改动）；
   测试以 raw SQL 临时建表覆盖归因路径后 drop，不碰 alembic（banned）。裁定
   满足「唯一归因真源=fires 台账」§4.4 且零越权建表。GO。
6. **import-linter 零改动**：runs_router 承 history_router 体例——鉴权
   CurrentUser/ORM OpsUser 经 app.ops.lg_rag.router 间接取，DB 访问全走
   store 层（run_store/event_store 已在 lg-rag-outbound ignore 白名单）；
   新文件不直 import app.db/app.ops.deps → .importlinter 不动。GO。
7. **既有资产复用**：assert_run_owned（event_store.py:350 既有语义跨用户/
   未知 404）· encode/decode_cursor + make_runs_cursor {ts,rid} 先例
   （history.py）· TITLE_MAX_CHARS=80 截断风格 [:79]+"…" · keyset datetime
   直传 SQL 先例（list_thread_activity_page:436）· 响应壳 {"ok","data"} 与
   404 detail 体例（history_router）。零新造轮。GO。
8. **失败路径**：8 条覆盖 404 矩阵/词表外帧过滤/fires 缺位降级/恶意 cursor
   422/limit·after_seq 422/空 run·空 thread 200/query 截断与缺键 null，
   均可机判。GO。
9. **验收可机判**：10 条验收逐条锚到 tests/test_lg_rag_runs_readonly_api.py
   用例或 lint/CI 命令；测试纪律真 PG + 五键 blank 前缀承委派书；脏树期
   wave_gate_registry 红为在途面咬禁改面常态（commit 后转绿 · CI 终裁）。GO。
10. **思考轮**：R0-R5 表 + actual_last_round=R5 + 六小节齐备；R3 记录白名单
    SQL 层/thread 归属真源/归因容错反查/query 截断/零 import-linter 五决策。GO。
11. **registry entry**：status=active · base=f1d0dd28 · allowed_app_files 四件
    （run_store.py/event_store.py/runs_router.py/app/ops/router.py）·
    allowed_tree_files 六件（task active+done/审查文/01_modules/registry/测试
    文件）· allowed_tree_prefixes=invokes 目录 · banned=[alembic/, scripts/] ·
    yaml safe_load 验证通过。GO。
12. **人工闸**：HG-TASK-DRAFT / HG-AUDIT-R1 / HG-GRAPH-MODULES 三行 approved，
    依据 issue #23 m03064/m03283 夜间授权；01_modules.md lg_rag 行备注+签收行
    随 30 交付回填。GO。

## 结论

**GO · 通过（零阻塞项）** —— task v1 可进 30 实施（夜间授权窗口 · 30 台账见 invoke_20261116_30_impl.md · 40 验收台账见 invoke_20261116_40_acceptance.md）。
