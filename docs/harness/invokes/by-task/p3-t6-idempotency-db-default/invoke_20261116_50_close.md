# invoke_20261116_50_close · p3-t6-idempotency-db-default

## feat PR
- #428 https://github.com/Cyning12/ops-desk-api/pull/428
- CI 四 job 全绿：check 37s · import-linter 10s · lint-wiki-delta 16s · pytest 2m51s
- squash merge sha：d2785471（feat(p3-t6-idempotency-db-default): 幂等转正 DB 默认 null→db）

## 验收台账（task 验收 11 条逐条）
1. [x] persistence.py:39 未设/空串 → db → test_configure_persistence_defaults_to_db
2. [x] env 四分矩阵（显式 db/memory/null/未设→db）→ test_configure_persistence_env_matrix（R9②）
3. [x] 显式 null 回退保留 + WARNING 口径 → test_configure_persistence_explicit_null_fallback（R9③）
4. [x] fail-closed 回归（DB 故障 → ok=False + 传输零调用）→ test_default_db_store_failure_fails_closed（R9③ · R-P3-10）
5. [x] 默认面防重双调实证 → test_default_surface_double_invoke_dedup
6. [x] 非法值 ERROR 词表补 null → test_log_init_window TC1 补组钉死
7. [x] 未设默认 INFO 窗口 → test_tc2_window_info_visible_default_unset
8. [x] docstring 改写（装配是部署动作 / 刻意不做自动探测）→ persistence.py 模块 docstring
9. [x] 观测面零改实证 → test_admin_capability_observability.py 12 passed 零改动
10. [x] 文档三面 + 图谱登记 + HG-GRAPH-MODULES 签收回写 → .env.example:145-147 · GUIDE:15 · RUNBOOK:91 · 01_modules.md:34
11. [x] 风险登记 R-P3-10 + 偏差 D1 → task 档实现备忘

## 机读验证
- ruff check app tests：All checks passed!
- lint-imports：Contracts 12 kept, 0 broken
- wave-gate 双闸：22 passed（committed 面 base..wave_tip ⊆ allowed）
- 全量 pytest（CI 终裁）：绿

## 偏差
- D1（终态）：契约 15 §7.3/§7.5 与 14 终稿口径矛盾——照 14 终稿落地，契约 15 未改，待 lead/00 跨仓和解。

## 结果
波 CLOSE：任务转 done · registry status=closed wave_tip=d2785471。
