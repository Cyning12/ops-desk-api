# invoke_20261117_40_verify

## 内容

验证（真 PG postgresql+asyncpg://ops:ops_password@localhost:5432/opsdesk_test · 五键 blank 前缀）：① 目标用例连续 10 轮；② 全文件回归；③ 全量 pytest；④ ruff；⑤ wave_gate_registry。

## 结果

- 目标用例 test_tc_b1_replay_after_disconnect_includes_tail 连续 10 轮：10/10 passed 零红（0.13-0.14s/轮 · 真跑非 skip）。
- 全文件 tests/test_lg_rag_sse_run_worker.py：7 passed。
- 全量 pytest tests：2441 passed / 3 skipped / 1 failed（73.01s）——唯一红=tests/test_wave_gate_registry.py 脏树期结构性红（closed entry p1-t5a-goal-docs banned tests/ 在途咬 · 提交后在途面清空即绿 · 仓内常态已登记于派单）。
- ruff check app tests：All checks passed。
- wave_gate_registry 提交后复跑：2 passed（在途面清空实证）。
- CI（无 .env）终裁：PR #435 四绿——check 15s · import-linter 10s · lint-wiki-delta 12s · pytest 2m43s pass（真 PG service · 目标用例含跑）。

## 偏差记录

无。
