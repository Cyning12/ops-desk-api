# invoke_20261117_30_implement

## 内容

实施：tests/test_lg_rag_sse_run_worker.py 同 family 归属闸竞态缺口两件统一修法——抽模块级 helper `_wait_run_owner_visible(event_store, run_id)`（40×50ms 有界轮询 run_owner 可见 · 逐字承 TC-B4 先例 b61c1227 同参 · 耗尽 fail-loud 不兜底），三处调用面统一：
1. test_tc_b1_replay_after_disconnect_includes_tail（issue #432 目标用例 · 在飞 409 断言前插入等待）；
2. test_tc_b4_in_flight_refuse_zero_diff（先例内联循环机械抽取为 helper 调用 · 零行为变化）；
3. test_tc_b5_active_worker_not_compensated（同形抢跑点 · 在飞 409 断言前插入等待）。

## 结果

- git diff 自证：+19/-8 · 仅 tests/test_lg_rag_sse_run_worker.py 单文件 · 零 app/ 改动 · 零断言弱化（等待仅前置时序，断言语义零触）。
- ruff check app tests：All checks passed。
- 目标用例真 PG 单跑首过（0.14s · 非 skip · DB_AVAILABLE 真跑）。

## 偏差记录

无（生产侧容忍窗备选经 R1 取舍论证否决 · 裁定测试侧承先例 · 见审查文核查项 3）。
