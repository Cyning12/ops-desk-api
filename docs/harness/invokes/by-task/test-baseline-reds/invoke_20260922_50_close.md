---
hat: 50
task_slug: test-baseline-reds
date: 2026-09-22
---

# invoke · 50+CLOSE · test-baseline-reds（bugfix · 测试基线红清零）

## 收口结论
- 五棒全通（bugfix 轨 · 跳 SPEC · 依据=各 40 invoke 观察项 ≈ mini-SPEC）：10-task（三根因真跑实证：chat_ws 断言过期+CI 假绿叠加 · proxy_bypass macOS 短路 · keyset×uuid4 竞态 40% 实测）→ 20-audit（R1 PASS 零返工 · 三根因亲跑复核 · CI 假绿核验属实）→ 双闸签收（00 代录）→ 30（5a5db27 · 只改 tests/ 8 文件 · 含返工实录：purge unmask 7 红钉 delenv）→ 40（PASS · 双态 1367/0×3 · 变异复做 · 假绿实证复现）。
- verify 机读闸拦阻一次：结论节被子标题截断 + 「零退回」不豁免——已修并沉淀口径（退回仅豁免 无需/不/未 前缀 · 结论节内不得有 #{2,3} 子标题截断）。
- PR [#169](https://github.com/Cyning12/ops-desk-api/pull/169)：CI 全绿 → merge master `9a46f48`。
- 归档：task → done/；active README 同步。

## 移交
- **CI 假绿另 task 议**：pytest.yml 无 PG 服务 → DB 用例全 skip → CI 绿 ≠ 真跑证据（F4 注记 · 建议 CI 加 postgres service 或显式标注 skip 面）。
- **capability 单文件独立跑 4 红**：DbIdempotencyStore 同步路径 × 宿主 OPS_CAPABILITY_PERSISTENCE=db 顺序依赖（master 同源预存 · 全量不受影响）另 task 议。
- 测试库 schema 漂移（migration 裸 SQL 无 ORM 模型 → conftest 幂等建表补丁）根治属仓级议题。
- 宿主 env 脆弱面：本波只钉了被 unmask 的 7 例；delenv/钉死模式宜成 conftest 通则。
