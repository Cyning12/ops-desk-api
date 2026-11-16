# invoke_20261117_10_task_draft

## 内容

10 帽起草：task 档落盘 docs/tasks/active/task_fix_432_replay_owner_race.md（背景=master 偶发红 TC-B1 replay 用例抛 LgRagRunNotFoundError · TC-B4 同 family 归属闸竞态）；范围=tests/test_lg_rag_sse_run_worker.py 同形抢跑缺口两件（TC-B1 :165 · TC-B5-active :532）统一测试侧有界等待；验收五条；红线=零断言弱化/零 app 改动。

## 结果

- 先例锚点：b61c1227（TC-B4 有界等待 40×50ms · 随 d002e4f0 合入 · #384 波）。
- 机制锚点：app/ops/lg_rag/event_store.py:381 assert_run_owned 先于 :382 在飞闸；:354 run_owner 反查事件表，行未可见即抛 NotFound。
- 覆盖缺口排查：全 tests/ grep load_events_after——resume/follow/orphan 各用例均直接 persist_run_event（awaited 提交）落库无 bus 竞态面；仅 run_worker 文件两件缺口。
- registry entry 落登记（status=active · base=396f7fed · banned app//alembic//scripts/）。

## 偏差记录

无。
