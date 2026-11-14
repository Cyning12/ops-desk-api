---
title: task · P0' T2b · chat 概念/文档收尾（W2 api 410 化 + drop 三表）
---

# task · P0' T2b · chat 概念/文档收尾（W2 api 410 化 + drop 三表）

> **状态**：`active`（2026-11-14 过闸开工 · W1 web 侧已关账 PR #103 · a7c8b42）
> **来源**：issue Cyning12/ops-desk-workspace#23 · P0' 收官衍生卡（T2a 偏差登记 · draft → 正式落卡）

## Harness 元信息

| 键 | 值 |
|----|----|
| task_slug | p0prime-t2b-chat-cleanup |
| base | 510516c |
| 关联 issue | Cyning12/ops-desk-workspace#23 |
| 关联 PR | 待回填 |
| 前序 | T2a（PR #369 · ee1941fd）· web W1（PR #103 · a7c8b42 · 前置解除） |
| **wiki_delta** | `n/a` |
| **wiki_delta_note** | 本仓未启用 WikiTrack |

## 人工闸（维护者授权）

- 三闸引用 m00177「签收，开始」：禁止 freeze 帧/schema 触碰 · 禁止跨 task 承载 · 禁止 freeze 概念语义漂移（tenant freeze F1-F6 / lg-rag-sse-v1 词表）。
- 本卡全链路纯收尾：410 墓碑 + 模型/迁移/测试改编，零新功能。

## 背景与目标

T2a 已清 chat 计算栈七件并将 `/chat/stream` 410 化，但两个兼容端点（`/chat/models` · `/chat/sessions/latest`）仍活跃且依赖旧表 `ops_sessions_chat`/`ops_runs`/`ops_run_events`。web 仓 W1 已摘除 session 硬门（唯一活跃消费方清零），本波收口 api 侧：端点 410 墓碑化 + 三表归档 drop。

## 范围

1. `app/ops/chat/router.py`：`/chat/models` 与 `/chat/sessions/latest` 410 墓碑化（镜像 `/chat/stream`：auth 在前 + detail{error,migrate_to,message} + Deprecation/Link 头）。
2. 删 `app/ops/chat/schema.py`（仅被两活跃端点引用）。
3. 删三模型类 `OpsSessionChat`/`OpsRun`/`OpsRunEvent` 与关系（`OpsUser.chat_sessions` 等）。
4. alembic `20261114_drop_legacy_chat_tables.py`（down_revision=20261114_v_audit_unified · drop 顺序 events→runs→sessions_chat · downgrade 重建，参照 20260715_init_ops_desk 建表史）。
5. 测试改编：conftest 清库引用摘除；test_session_summary SoT 断言改写；test_tenant_context/test_chat_router/test_auth 三处 200 断言改 410。
6. 图谱 `01_modules.md` db 行登记 drop + chat 行 410 补齐 + 签收行。
7. 归档导出：prod cynaya.cn 三表导出为运营动作（PR body + 本卡记录操作指引，非本仓代码动作）。

## 非范围

- lg-rag 侧任何改动；freeze 帧/schema；新端点；`history_router.py`（`/api/ops/chat/threads` 为 lg-rag history 路由前缀巧合，非旧 chat 概念）。
- prod 数据导出执行本身（运营侧动作，本卡只给指引）。

## 失败路径

- 迁移失败 → `alembic downgrade` 重建三表（downgrade 已含完整建表 DDL）。
- 端点 410 误伤在役消费 → web W1 已摘除唯一消费方（CI 358 绿背书），iOS 无活跃消费（图谱 TODO 引用除外）。
- 测试改编误删仍在用断言 → 目标套件 + 干净 worktree 全量双验。

## 验收标准

- [x] `/chat/models` 与 `/chat/sessions/latest` 未登录 401、登录 410（detail 含 migrate_to 指向 lg-rag），与 `/chat/stream` 墓碑行为一致
- [x] 迁移 up/down scratch 实证；三表 drop 后 `OpsSessionChat`/`OpsRun`/`OpsRunEvent` 在 app 零引用
- [x] 改编测试全绿（410 断言 + auth 在前语义）；干净 worktree 全量绿（允许既有 ta2 红）
- [x] graph check OK · spec-wave task lint PASS · ruff app tests 绿
- [x] lg-rag-sse-v1 freeze 零 diff；tenant freeze 零触碰

## 必读列表

- `app/ops/chat/router.py`（现役墓碑范式 :34-47）
- `docs/tasks/done/task_p0prime_t2_chat_legacy_cleanup.md`（T2a 裁定 :53）
- `alembic/versions/20260715_init_ops_desk.py:163-192`（三表建表史，downgrade 重建参照）

## 思考轮控制

- R0 调研（已完成 · 勘察记录见 invoke_10）：引用面 models/router/conftest/四测试/alembic 建表史。
- R1 设计审查：见 `docs/harness/reviews/task_p0prime_t2b_chat_cleanup_audit_R1_20261114.md`。
- R2-R5：实施/验证/回归/收尾。
- early_stop reason：纯收尾卡，范围封闭。

## 实现备忘

- web W1（PR #103 · a7c8b42）摘除 session 硬门后，本波把 /chat/models 与 /chat/sessions/latest 410 墓碑化（auth 在前 · Deprecation/Link 头 · migrate_to 指 lg-rag 等价端点）。
- 删除 app/ops/chat/schema.py、OpsSessionChat/OpsRun/OpsRunEvent 三模型类与 OpsUser.chat_sessions 关系；追加发现并删除 app/ops/session/history.py（唯一 import OpsRun 的生产文件 · 实扫零调用方）。
- alembic 20261114_drop_legacy_chat_tables：drop 顺序 events→runs→sessions_chat；downgrade 逐字重建（含 server_default 与 idx_ops_run_events_run_seq/run_type 两表引，初稿漏补教训）。
- 测试改编五件（conftest/session_summary SoT 断言/tenant_context/chat_router/auth），410 断言统一带 detail 三键。
- 验证：目标 56 passed（真 PG）；迁移 up/down/up scratch 库实证；干净 worktree 全量 2093 passed/2 skipped/1 failed（唯一红=既有 ta2，另卡 fix-ta2-hitl-ttl-db-store 修复）。
- CI 首波 lint-wiki-delta 红（task 档缺 wiki_delta 字段）→ 补字段 amend 强推 7b08796f 后四件全绿。

## 测试策略

目标套件：test_chat_router + test_auth + test_tenant_context + test_session_summary（真 PG 本地跑）+ 迁移 up/down scratch。回归：干净 worktree 全量。

## 修订记录

| 日期 | 变更 |
|------|------|
| 2026-11-14 | draft → 正式落卡过闸（W1 前置解除后） |
