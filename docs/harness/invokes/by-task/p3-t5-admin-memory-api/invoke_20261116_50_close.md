# invoke_50 · close（p3-t5-admin-memory-api）

## 内容

- PR Cyning12/ops-desk-api#422 squash merge 完成（merge commit
  0ab54c7b · CI 四 job 全绿：check / import-linter / lint-wiki-delta /
  pytest 全过）。
- 本 invoke：task 档 active → done；registry entry status=closed +
  wave_tip=0ab54c7b。
- 交付物：`app/ops/admin/memory.py` 三端点（GET /admin/memory/facts
  keyset 分页浏览 · POST /admin/memory/facts/{key}/revoke 幂等复用
  revoke_by_key 语义 · GET /admin/memory/episodes 只读 · AdminSyncAuth
  跨租户运维面 R7 · 响应壳 {"ok","data"} · 投影无 embedding ·
  cursor 本地复刻保 .importlinter 零改动 · 零 router.py 改动）+
  tests/test_admin_memory_api.py 23 用例 + 图谱 01_modules.md admin 行
  备注与签收行。

## 过程要点

- 五项裁定与 task R3/R1 审查文一致：{key} 钉名（15 §5.3 schema 真源）
  · tenant 范围 revoke 不改 service 签名（admin 层同形 UPDATE）·
  cursor 本地复刻（admin-outbound forbidden 含 lg_rag）· 零 router.py
  改动（承既有注册面）· episodes 直读 ORM。
- 并行波次无 PR CONFLICTING；未触发 rebase。
- 本地目标测试 23+9 全绿；CI（无 .env）终裁全绿。

## 验证台账

| 项 | 结果 |
|---|---|
| CI check / import-linter / lint-wiki-delta / pytest（PR #422） | 全 pass |
| 目标 23 用例 + purge 回归 9 用例（真 PG opsdesk_test） | 绿 |
| ruff check app tests | 绿 |
| lint-imports | 12 kept, 0 broken（零新出边） |
| spec-wave verify（task 档三闸） | PASS |
| registry yaml safe_load | PASS（26 entries） |

## 结果

P3-T5 close。清理：删除 task/p3-t5-admin-memory-api 与 close 分支 +
worktree + scratch（本波无 scratch DB）。
