---
title: task · fix · replay 归属闸竞态——bus 发布先于事件行可见（issue #432）
---

# task · fix · replay 归属闸竞态——bus 发布先于事件行可见（issue #432）

> **状态**：`closed`（2026-11-17 关账 · wave_tip 2be501d4）
> **来源**：issue Cyning12/ops-desk-api#432（维护者派单 · 夜间自动执行预授权 issue Cyning12/ops-desk-workspace#23 m03064/m03283/m03694）

## Harness 元信息

| 键 | 值 |
|----|----|
| **task_slug** | fix-432-replay-owner-race |
| base | 396f7fed |
| 关联 issue | Cyning12/ops-desk-api#432 |
| 关联 PR | #435（CI 四绿 · squash 2be501d4） |
| **wiki_delta** | `n/a` |
| **wiki_delta_note** | 本仓未启用 WikiTrack |

### 人工闸（维护者授权）

| human_gate_id | status | blocks_hats | 说明 |
|---------------|--------|-------------|------|
| **HG-TASK-DRAFT** | approved | 22-R1, 30 | 维护者预授权（issue Cyning12/ops-desk-workspace#23 m03064/m03283/m03694 夜间自动执行链） |
| **HG-AUDIT-R1** | approved | 30 | R1 审查文落盘 docs/harness/reviews/task_fix_432_replay_owner_race_audit_R1_20261117.md（GO）· 同一预授权链 |
| **HG-GRAPH-MODULES** | approved | 30 | 不修改图谱（纯测试侧修复 · app/ 零改动） |

- 预授权链：issue Cyning12/ops-desk-workspace#23 m03064/m03283/m03694（夜间自动执行 · 不中途问问题 · 冲突按「最小改动+如实登记偏差」处理）。
- 本卡为**纯测试侧修复**：app/ 零改动、零断言弱化（红线 · 承 #384 波先例裁定）。

## 背景

- master 偶发红：tests/test_lg_rag_sse_run_worker.py::test_tc_b1_replay_after_disconnect_includes_tail 抛 LgRagRunNotFoundError（应为 LgRagRunInFlightError）。
- 根因=TC-B4 同 family 归属闸竞态：load_events_after 的归属闸（app/ops/lg_rag/event_store.py:381 assert_run_owned → :354 run_owner 反查事件表）先于在飞闸；bus.publish 先于事件行提交对其它会话可见 → 归属校验抢跑抛 NotFound。
- 先例：#384 波（b61c1227 · 随 d002e4f0 合入）对 TC-B4 用测试侧有界等待（40×50ms 轮询至 run_owner 可见 · 零断言弱化）——本卡承该修法。

## 范围

1. tests/test_lg_rag_sse_run_worker.py 同 family 覆盖缺口两件统一修法（测试侧有界等待 · 与 TC-B4 先例同形同参）：
   - test_tc_b1_replay_after_disconnect_includes_tail（:165 在飞 409 断言前的归属闸抢跑点 · issue #432 目标用例）；
   - test_tc_b5_active_worker_not_compensated（:532 同形抢跑点 · 同文件 grep 覆盖缺口实证）。
2. 全 tests/ grep 复核：resume/follow/orphan 各用例均为直接 persist_run_event（awaited 提交）落库，无 bus 竞态面——登记复核结论零改动。

## 非范围

- app/ 业务代码（含 event_store 归属闸生产侧改动——R1 论证取舍后裁定测试侧承先例）；alembic 迁移；CI workflow；任何断言弱化；其他测试文件用例逻辑。

## 失败路径

- 有界等待上限（40×50ms=2s）在极端调度下仍不足 → CI 红，如实登记不放大上限不弱化断言，另卡跟进（红线）。
- 同 family 漏判其它抢跑点 → 全文件 grep 轮询/等待覆盖缺口复核兜底（范围 1.2）。

## 验收标准

- [ ] 目标用例 test_tc_b1_replay_after_disconnect_includes_tail 真 PG 连续 10 轮零红
- [ ] tests/test_lg_rag_sse_run_worker.py 全文件绿
- [ ] 全量 pytest 绿（真 PG · 五键 blank 前缀协议）
- [ ] ruff check app tests 绿
- [ ] 零 app/ 改动 · 零断言弱化（diff 自证）

## 必读列表

- `tests/test_lg_rag_sse_run_worker.py`（TC-B1/TC-B4/TC-B5 同 family 用例）
- `app/ops/lg_rag/event_store.py:350-385`（assert_run_owned → run_owner 归属闸先于在飞闸）
- `docs/tasks/done/task_ci_pytest_pg_service.md`（#384 波先例 · TC-B4 修法与关账体例）

### 自检结论

- 验收 1 ✓：目标用例真 PG 连续 10 轮 10/10 passed 零红（0.13-0.14s/轮 · 真跑非 skip）。
- 验收 2 ✓：全文件 7 passed in 0.41s。
- 验收 3 ✓：全量 pytest 2441 passed / 3 skipped（唯一红=脏树期 wave_gate_registry 结构性常态 · 提交后复跑 2 passed 自证）；CI（无 .env 终裁）pytest 2m43s pass。
- 验收 4 ✓：ruff check app tests All checks passed。
- 验收 5 ✓：diff 自证 +19/-8 单文件（tests/test_lg_rag_sse_run_worker.py）· 零 app/ 改动 · 零断言弱化。

## 思考轮控制

| 轮 | 结论 | early_stop | reason（early_stop） | residual_risks |
|---|---|---|---|---|
| R0 | 勘察完成：先例 b61c1227 已读 · 缺口两件定位（TC-B1 :165 · TC-B5-active :532）· 全 tests/ 竞态面排查 | false | — | 极端调度下 2s 上限不足（低概率） |
| R1 | 审查文 docs/harness/reviews/task_fix_432_replay_owner_race_audit_R1_20261117.md（GO · 生产侧取舍论证后裁定测试侧承先例） | false | — | 未来同 family 新用例复犯 |
| R2 | 方案落地：模块级 helper _wait_run_owner_visible 统一三处调用面（TC-B1 插入 · TC-B4 机械抽取 · TC-B5-active 插入）· +19/-8 单文件 | false | — | — |
| R3 | 反例/边界：等待耗尽不兜底（fail-loud 自然抛 NotFound）· 不断言弱化 · TC-B1 :174 末读在 task done 后安全 · orphan/resume/follow 各面 awaited persist 无竞态 | false | — | — |
| R4 | 收敛：ruff 绿 · 目标用例真 PG 10 连跑零红 · 全文件 7 passed · 全量 pytest 见 40 轨 | false | — | — |
| R5 | 组织人终裁：维护者 | false | — | — |

### R0 · 勘察

先例 b61c1227（TC-B4 有界等待 40×50ms · #384 波 · 随 d002e4f0 合入）已读；机制链 event_store.py:381 assert_run_owned → :354 run_owner 反查事件表先于 :382 在飞闸已核；全 tests/ grep load_events_after 调用面，缺口恰两件（TC-B1 :165 · TC-B5-active :532），其余各面均为 awaited persist 落库无 bus 竞态。

### R1 · 审查

docs/harness/reviews/task_fix_432_replay_owner_race_audit_R1_20261117.md（GO）：生产侧容忍窗备选经取舍论证否决（归属闸为跨租户 404 安全闸 · 生产读己所写无此窗口 · 先例 CI 绿史实证），裁定测试侧承先例。

### R2 · 方案

抽模块级 helper 统一修法（避免三处复制 4 行循环）：TC-B1 在飞 409 断言前插入等待；TC-B4 先例内联循环机械抽取为 helper 调用（零行为变化）；TC-B5-active 同形点插入等待。

### R3 · 反例/边界

等待循环只前置时序不改断言语义；耗尽即 fail-loud 不兜底；run_stream_closed 在行不可见时返回 False 恰与断言同向（非失败面）；TC-B1 末次 load 在 worker task 完成后（提交先于 task done）且 owner 已可见，无需再待。

### R4 · 收敛

最小面锁单文件 +19/-8；ruff All checks passed；目标用例真 PG 10 连跑 10/10 零红（0.13-0.14s/轮 · 真跑非 skip）；全文件 7 passed。

### R5 · 收口

组织人终裁：维护者。

## 测试策略

- 真 PG postgresql+asyncpg://ops:ops_password@localhost:5432/opsdesk_test · 五键 blank 前缀（OPS_HITL_PERSISTENCE= OPS_CAPABILITY_ALLOW_WRITE= OPS_CAPABILITY_ALLOW_WRITE_TAGS= OPS_CAPABILITY_PERSISTENCE= OPS_CAPABILITY_EXTRA_MANIFESTS=）。
- 目标用例连续 10 轮 + 全文件 + 全量三层验证；CI（无 .env）为终裁。

## 修订记录

- 2026-11-17：落卡过闸。
- 2026-11-17：30 实施（helper 统一三处调用面）→ 40 验证（10 连跑零红 · 全量绿 · ruff 绿）→ PR #435 CI 四绿 → squash 2be501d4 → 关账。
