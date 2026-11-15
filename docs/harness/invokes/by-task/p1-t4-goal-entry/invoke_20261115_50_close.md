# invoke · 50_close · p1-t4-goal-entry

- 时刻：2026-11-15 · 关账（wave_tip 9f309ba3 · PR #397 CI 首波四绿）
- 关账人：本窗口（维护者 m02028「本窗口任务继续」授权）

## 验证台账

| 项 | 证据 |
|----|------|
| 目标测试 | tests/test_goal_entry_wiring.py 4 件真 PG 绿（闸 off 零触达 · 闸 on 懒创建 3 轮复用 · 并发 10 路单行 · turns 无横幅） |
| 回归 | goal/sse/slots/continuity/memory/isolation/run_worker/run_store/chat_router 八套件 158 passed 1 skipped |
| 迁移 | scratch 库 up→1/down→0/up→1 实证 |
| CI | PR #397 首波四绿（pytest 2m19s） |
| 合并尖全量 | 干净 worktree（9f309ba3）**2120 passed / 2 skipped / 0 failed**（47.9s） |
| wave gate | 合并尖本地 2 passed |

## 偏差登记（四件 · 详见 invoke_30）

1. **alembic revision id ≤32 字符**（varchar(32) 硬限）——35 字符初版 upgrade 炸 StringDataRightTruncationError，改名 20261115_uq_goals_active_thread。索引名不受限不动。
2. **create_all 不给既有表补索引**——本地 opsdesk_test 的 ops_goals 是 T5 期 create_all 所建，T1/T4 后加的 ORM Index 均缺席 → 并发用例首跑 5 行假证。DROP TABLE 重建后实证通过。CI 全新库无此问题；本地库演进须注意此坑。
3. FK 先例承 test_chat_history_api.py:117——override_auth 固定 id 用户须 seed_auth_user fixture 补行。
4. 测试套件文件名勘误（test_lg_rag_session_continuity.py 等）。

## 结论

P1-T4 验收 6 条全过。07 §5 序列 T1→(T2∥T3)→T4 全闭环；T5（文档批 + 端侧最小面）依赖就绪。P1 功能链完整：懒创建（T4）→ 注入（T3）→ REST 人工流转（T2）→ DB 1:1 执行面（T4）。
