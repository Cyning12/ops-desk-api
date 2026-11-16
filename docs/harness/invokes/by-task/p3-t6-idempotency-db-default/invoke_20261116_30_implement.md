# invoke_20261116_30_implement · p3-t6-idempotency-db-default

## 实现清单
1. app/ops/capability/persistence.py——:39 默认值翻转（未设/空串 null→db ·
   DbIdempotencyStore + DbReceiptSink 现役转正）· 模块 docstring 改写（翻转 ·
   装配仍是部署动作 · 刻意不做自动探测 = 配置面默认值变更非运行时自适应 ·
   fail-closed + R-P3-10 口径）· 非法值 ERROR 词表补 null · 显式 null WARNING
   新文案「能力层持久化：null（**幂等防重与回执落库均未启用**，不可上生产）」·
   describe note null 分支口径同步（保留「不可上生产」子串）
2. 调用方口径同步：app/ops/capability/__init__.py:102 注释 ·
   app/ops/admin/capability.py :12/:17 docstring（显式 null = 没有防重 · 未设默认 db）
3. 测试：
   - tests/test_capability_persistence_db.py——defaults_to_null→defaults_to_db ·
     新增 test_configure_persistence_env_matrix（env 四分 · R9②）·
     新增 test_configure_persistence_explicit_null_fallback（R9③）·
     新增 test_default_db_store_failure_fails_closed（假 session_factory ·
     ok=False + 传输零调用 · R9③ + R-P3-10）·
     新增 test_default_surface_double_invoke_dedup（默认面防重双调实证）
   - tests/test_log_init_window.py——探针 env ""→"null" · 新 WARNING 钉死 ·
     ERROR 词表钉死 · 新增 test_tc2_window_info_visible_default_unset（未设 →
     INFO「能力层持久化：db（跨实例防重 + 回执落库）」）
4. 文档三面：.env.example:145-147 · GUIDE_env_inventory_v1.md:15 ·
   RUNBOOK_local-acceptance_v1_zh.md:91
5. 图谱：docs/_tech_graph/l1/01_modules.md :34 capability 行 P3-T6 备注段 +
   HG-GRAPH-MODULES 签收表回写行

## 验证台账
- 目标测试（五键 blank 前缀 · 真 PG opsdesk_test）：
  tests/test_capability_persistence_db.py 22 passed ·
  tests/test_log_init_window.py 8 passed ·
  tests/test_admin_capability_observability.py 12 passed（零改实证成立）
- ruff check app tests：All checks passed!（初报 UP037 已 --fix）
- lint-imports：Contracts 12 kept, 0 broken
- 全量 pytest tests：2420 passed · 23 failed → --lf 复跑 21 passed（并发 agent
  共机环境下 flaky · 隔离复跑全绿）· 2 real failure = wave-gate 双闸在途面
  （设计语义：committed 后审计 base..wave_tip ⊆ allowed）→ 提交后复验

## 偏差
- D1（承 10_draft）：契约 15 §7.3/§7.5 口径矛盾不改 15，登记待和解。
- 无新增偏差。

## 结果
进 40。
