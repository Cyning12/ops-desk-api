# invoke_40 · acceptance（p3-t4-runs-readonly-api）

## 内容

40 验收：全量测试复跑 + 提交后闸测试复绿实证 + 验收标准逐条核对 + CI 四绿终裁。

## 验证台账

| 项 | 结果 |
|---|---|
| `pytest tests/test_lg_rag_runs_readonly_api.py`（真 PG · 五键 blank） | **13 passed**（0.63s） |
| `pytest tests` 全量（feat commit 2afbb751） | 2300 passed + 23 failed，与干净 HEAD 基线（2288 passed + 同签 23 failed）逐签一致——环境性 multi_replica_dualproc/strategy_builder/lg_rag_multi 顺序与进程依赖 + 脏树期 TC8/wave_gate_registry 结构性红 |
| 闸复绿实证（提交后） | `test_tc8_diff_whitelist` + `test_wave_gate_registry` → **3 passed**（脏树红提交后复绿 · 承前波钉案） |
| `ruff check`（改动五件） | All checks passed |
| `lint-imports` | 12 kept, 0 broken（零 .importlinter 改动） |
| spec-wave task lint | PASS（自检回填后复跑） |
| registry.yaml entry | yaml.safe_load 验证末 entry=p3-t4-runs-readonly-api · status=active · base=f1d0dd28（10 阶段实证） |
| **CI 终裁（PR #418）** | **四绿：pytest 2m36s · check 15s · import-linter 11s · lint-wiki-delta 12s** |

## 验收标准逐条（对账 task 档 10 条）

- [x] 两端点上线且挂 /api/ops/lg-rag 前缀，响应壳 {"ok":true,"data":...}（runs_router.py + app/ops/router.py 注册 · 13 用例响应壳断言）
- [x] 双用户 404 矩阵（test_runs_list_cross_user_404/404_matrix · test_events_cross_user_404/404_matrix · 未登录 401 两锚）
- [x] 白名单过滤：internal.debug/token 落库后不落响应（test_events_whitelist_filters_internal_types）
- [x] keyset 跨页不重不漏 · limit=51 → 422 · 坏 cursor → 422（test_runs_list_pagination_keyset/limit_and_cursor_422）
- [x] 505 帧 → 500 + truncated:true + next_after_seq · 续拉余 5 帧 truncated:false（test_events_truncation_and_after_seq）
- [x] 空 run events 200 空列表（仅词表外帧锚）· 空 thread runs 200 空列表（404_matrix 锚）
- [x] query_summary 截 80 断言 · schedule 归因三元组断言（happy_projection/schedule_attribution 锚）
- [x] pytest 真 PG 13 用例绿 · ruff 绿 · import-linter 绿（全量 23 红与基线同签 · CI 终裁）
- [x] registry entry active base=f1d0dd28 · task lint PASS
- [x] CI 四绿（pytest/check/import-linter/lint-wiki-delta）→ squash merge → CLOSE 波钉 wave_tip（CI 四绿实证 · merge/CLOSE 在 50 波落账）
