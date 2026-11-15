---
title: task · ci · pytest 接入 postgres service 消除 skip 假绿
---

# task · ci · pytest 接入 postgres service 消除 skip 假绿

> **状态**：`closed`（2026-11-15 关账 · wave_tip d002e4f）
> **来源**：issue Cyning12/ops-desk-api#384（维护者派单 · 本窗口直执行）

## Harness 元信息

| 键 | 值 |
|----|----|
| **task_slug** | ci-pytest-pg-service |
| base | 0dfc697 |
| 关联 issue | Cyning12/ops-desk-api#384 |
| 关联 PR | #386（CI 四绿 · squash d002e4f0） |
| **wiki_delta** | `n/a` |
| **wiki_delta_note** | 本仓未启用 WikiTrack |

## 人工闸（维护者授权）

- 三闸引用 m00177「签收，开始」：禁止 freeze 帧/schema 触碰 · 禁止跨 task 承载 · 禁止 freeze 概念语义漂移。
- 本卡为**纯 CI 基础设施**：app/ 零改动、tests/ 用例逻辑零改动（仅允许 conftest.py 注释级同步）。

## 背景

- CI（.github/workflows/pytest.yml）无 postgres service → tests/conftest.py:15 自述「CI 绿对 DB 用例是 skip 绿（假绿）」。本地自 P0' T3 起具备真 PG，全量基线 2091 passed / 2 skipped / 0 failed。
- 假绿实证掩盖过真红：ta2（tests/test_hitl_approval_consumption.py::test_ta2_ttl_db_store_expired_not_consumed）在 CI 长期 skip，本地 PG 起后即红（根因已修 #382）。

## 范围

1. .github/workflows/pytest.yml 增加 postgres service（pgvector/pgvector:pg16 镜像自带 vector 扩展；uuid-ossp 在 contrib）+ 健康检查 + env：DATABASE_URL 与 OPS_TEST_DATABASE_URL（conftest.py:80 TEST_DATABASE_URL_KEY）指向该 service。
2. conftest.py:15 注释级同步（skip 假绿口径在 CI 已消除）。

## 非范围

- app/ 业务代码；tests/ 用例逻辑；其他 workflow；deploy-api.yml；迁移文件（20260715_init_ops_desk.py:23-24 已 CREATE EXTENSION IF NOT EXISTS，service 用户为镜像 superuser 权限足够）。

## 失败路径

- service 健康检查不过 → CI 红，回退本卡。
- DB 用例在 CI 真跑后暴露新红 → 如实登记，不弱化断言，另卡跟进（红线）。

## 验收标准

- [ ] CI pytest job 中 DB 依赖用例真跑且绿（PG 缺失类 skip 归零，其余 skip 逐个有名有姓）
- [ ] 本地协议不回归：无 .env 干净 worktree 全量仍绿
- [ ] workflow 时长较现状膨胀 ≤ +2 分钟
- [ ] ruff / import-linter / graph check 不受影响

## 必读列表

- `.github/workflows/pytest.yml`（现役 CI）
- `tests/conftest.py:76-140`（OPS_TEST_DATABASE_URL 换库协议 + admin 建库机制）
- `alembic/versions/20260715_init_ops_desk.py:23-24`（扩展自举）

### 自检结论

- 验收 1 ✓：CI pytest 真跑 PG——PR #386 末跑 2m10s 绿（1 failed 2091 passed 4 skipped → 修后全绿；DB 用例零 skip，此前 skip-mode 全量跳过）。
- 验收 2 ✓：本地协议不回归——干净 worktree（无 .env · 合并尖 3d6eaecd）全量 2100 passed / 2 skipped / 0 failed。
- 验收 3 ✓：时长膨胀 +34s（skip 态 1m36s → 真跑 2m10s），远低于 +2min 上限。
- 验收 4 ✓：ruff / import-linter / graph check 四件全绿。
- skip 名冊偏差：CI 4 skipped 比本地多 2 件（环境型差异 · 非 PG 缺失类）；CI 日志因 blob 网络未能下载复核，本地 -rs 已核 PG 缺失类归零。

## 思考轮控制

- R0（勘察）：conftest 机制+迁移扩展自举+镜像选型已核。
- R1（审查）：docs/harness/reviews/task_ci_pytest_pg_service_audit_R1_20261115.md。
- R2–R4：实施中按证补充。
- R5（组织人终裁）：维护者。

## 测试策略

- CI 本身即验收场：PR 上 pytest job 的 passed/skipped 计数对比 master 基线。
- 本地干净 worktree 全量回归。

## 修订记录

- 2026-11-15：落卡过闸。
- 2026-11-15：三轮 CI 收敛（2095 errors 扩展缺失 → TC-B4 竞态 1 红 → 全绿）→ PR #386 合并 d002e4f0 → 关账。扩面两件已 registry 登记（TC-B4 测试修复 + template1 扩展步骤）。

## 实现备忘（关账回填）

- service=pgvector/pgvector:pg16（POSTGRES_USER=ops 即镜像 superuser）；健康检查 pg_isready。
- env 双写 DATABASE_URL 与 OPS_TEST_DATABASE_URL（conftest.py:80 协议真源；_assert_test_database 硬断言 _test 结尾）。
- 扩展预建位置=template1 而非目标库：conftest 运行时 CREATE DATABASE 走默认模板，新库自动继承（vector/uuid-ossp 均 per-database 对象）。
- TC-B4 竞态根因：load_events_after 归属闸（event_store.py:381 assert_run_owned→run_owner 反查事件表 :100-117）先于在飞闸；bus.publish 先于事件行对其它会话可见 → CI 调度下抛 LgRagRunNotFoundError。修法=测试侧有界等待（40×50ms）至 run_owner 可见。
