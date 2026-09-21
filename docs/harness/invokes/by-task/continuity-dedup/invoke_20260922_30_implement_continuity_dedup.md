# invoke · 30 · continuity-dedup · 实现

| 项 | 内容 |
|----|------|
| **时间** | 2026-09-22 |
| **帽** | 30（实现 · 不签任何 human_gate） |
| **分支** | `task/continuity-dedup`（每次 commit 前 `git branch --show-current` 核验 · 未切 master · 未 push） |
| **task** | `docs/tasks/active/task_continuity_dedup.md`（HG-TASK-DRAFT/HG-AUDIT-R1/HG-GRAPH-MODULES 全 approved · 本帽 `npx spec-wave verify` 复跑 PASS） |
| **SPEC** | `docs/spec/continuity-dedup/SPEC-continuity-dedup_v1.md`（signed） |

## 落地摘要（D1–D3 一次提交 · 纯删除型）

- **D1 · 单真源**：`git rm app/ops/session/continuity.py`（36 行 legacy 整文件删除）；`app/ops/session/__init__.py` 仅移除 `:3` `from app.ops.session.continuity import compress_window` 与 `__all__` 中 `"compress_window"`（docstring 与 history/sse_replay 两行及其余三条 `__all__` **原样**——docstring 一度顺手改了词，发现违反「两行移除」白名单即回改）；`app/ops/lg_rag/continuity.py` **零 diff**（真源不动）；零新增依赖边（`git diff master -- app/` 无新增 import 行 · S1 硬删除，未走 S2 re-export）。
- **D2 · 测试收敛**：`tests/test_session_continuity.py` 删 `:5` import + compress_window 两用例（`test_compress_window_keeps_tail_full` / `test_compress_window_small_noop`）；sse_replay 两用例（`test_replay_events_after_seq` / `test_replay_cursor_and_payload`）与 `:6-10` import **逐字保留**；`tests/test_lg_rag_session_continuity.py` **零改动**（合并后即为真源守护，含 `:22-37` 方向闸）。
- **D3 · 图谱零变更按实判**：`./scripts/graph-compile.sh` exit 0；脚本副作用改写 `shared/graph.json` 的 `generated_at` 时间戳已 `git checkout` 还原（图谱内容零变更 · 不触发回炉补闸条款）。

## 验证（真跑）

| 项 | 结果 |
|----|------|
| 用例数 | 基线 **1178** collected → 删除后 **1176**（差值 == 2 · 恰为被删两用例）✓ |
| `pytest tests` 全量 | **1172 passed, 3 failed, 1 skipped**；3 红 = 基线环境性红（`test_chat_ws`×2 + capability proxy×1），删除前基线真跑同 3 红，与本波无关；复跑中 `test_memory_embedding_backfill::test_reconcile_mismatch_marks_failed` 曾随机序下红一次，单跑/复跑均绿，确认为环境性 flaky（事件循环关闭类），与本波无关 |
| `ruff check app tests` | 基线实测 **57** errors → 本波 **57**（**零新增**；简报所称 67 与本仓当前实测不符，以实测为准） |
| `./scripts/graph-compile.sh` | 绿（exit 0 · mermaid normalize check 9 md OK）· 图谱零变更 |
| grep 零残留三 pattern | `session.continuity` / `session/continuity` / `ops\.session import compress_window` 全仓 `*.py` **零命中** ✓ |
| 真源零 diff | `git diff master -- app/ops/lg_rag/continuity.py` 输出为空 ✓ |
| app/ diff 白名单 | 仅 `session/continuity.py` 删除 + `session/__init__.py` 两行移除 ✓ |

## 变异检验三条（不验收空真规则 · 均已还原复跑绿）

1. **删真源函数**：摘掉 `lg_rag/continuity.py` 中 `compress_window` 定义 → `tests/test_lg_rag_session_continuity.py` collection 即 `ImportError: cannot import name 'compress_window'`（1 error）→ 还原后 15 绿 ✓
2. **忘改 __init__ 炸显式**：`git show master:app/ops/session/__init__.py` 恢复旧版（保留 continuity import）而文件已删 → `pytest tests/test_session_continuity.py` `ModuleNotFoundError: No module named 'app.ops.session.continuity'`（1 error）→ 补回实现态 `__init__.py` 后全绿 ✓
3. **摘 try/except 降级守护**：摘掉真源 `compress_window` 的 try/except（dedent 函数体删 except 块）→ `test_compress_window_failure_truncates_tail` 真挂（`AttributeError` 传播）→ 还原后全绿 ✓

## B1 旧测影响面 17 条逐条处置回填

1. `test_session_continuity.py:5` continuity import → **删除**（随模块消失）✓
2. `:6-10` sse_replay import → **回归**（逐字保留 · 包加载正常）✓
3. `:13` `test_compress_window_keeps_tail_full` → **删除**（对账 lg_rag `:65-73` 同构 + `:81-85` 同参数显式断言，等价或更强）✓
4. `:18` 调用行 → **删除**（随用例）✓
5. `:25` `test_compress_window_small_noop` → **删除**（对账 lg_rag `:76-78` 同断言）✓
6. `:27` 断言行 → **删除**（随用例）✓
7. lg_rag `:14` 真源 import → **回归**（真源零改动 · 全绿）✓
8. lg_rag `:23` 依赖方向闸 → **回归**（S1 零新边 · 闸全绿）✓
9. lg_rag `:65` defaults_and_groups_head → **回归**（对账接收方 · 零改动）✓
10. lg_rag `:67` 调用行 → **回归** ✓
11. lg_rag `:76` short_noop → **回归**（对账接收方）✓
12. lg_rag `:78` 断言行 → **回归** ✓
13. lg_rag `:81` failure_truncates_tail → **回归**（变异检验③钉死守护真实）✓
14. lg_rag `:84` 调用行 → **回归** ✓
15. `session/__init__.py:3` 生产 re-export → **删除**（import + `__all__` 条目）✓
16. 禁令注释/断言（answer_stream/progress_stream/packs + test_prompt_packs）→ **回归**（不动）✓
17. 动态 import 面 → **回归**（无处置 · 无隐藏引用面）✓

处置统计：删除×6 · 回归×11 · 改编×0，与 B1 清单一致。

## commit 列表

1. refactor(session): 删除 continuity 重复实现并收敛测试（D1-D3 · 真源零 diff · 用例 1178→1176 · 变异检验×3 还原）· task continuity-dedup

## 遗留

- 仓外脚本引用属不可扫面（承 SPEC residual ① · 若存在则 ImportError 显式炸，消费方迁移 lg_rag 真源）。
- ruff F822 启用与否未核（承 SPEC residual ②）；`__all__` 残留由 grep 断言 + diff 白名单兜，本波 diff 证实无残留。
- 删除不可逆一步靠 git 历史 + 真源功能超集兜底（承 SPEC residual ③）。
- 简报口径与本仓实测差异两处留痕：ruff 基线简报 67 vs 实测 57（零新增结论不变）；全量 pytest 中 `test_memory_embedding_backfill` 随机序 flaky（与本波无关）。

## 闸纪律

本帽未签任何 human_gate；实现形态 = S1 硬删除（未走 S2 re-export · 零新增依赖边/端点/表/事件类型），图谱零变更裁定与实现一致，未触发回炉补闸条款。
