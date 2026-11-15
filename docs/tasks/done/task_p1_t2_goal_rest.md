---
title: task · feat · P1-T2 REST goal 面
---

# task · feat · P1-T2 REST goal 面

> **状态**：`closed`（2026-11-15 关账 · wave_tip 19e3f9ba）
> **来源**：issue Cyning12/ops-desk-api#390（维护者派单 · 设计真源 07-p1-goal-design.md commit d19fdaa）

## Harness 元信息

| 键 | 值 |
|----|----|
| **task_slug** | p1-t2-goal-rest |
| base | 44a5b32 |
| 关联 issue | Cyning12/ops-desk-api#390 · Cyning12/ops-desk-workspace#23 |
| 关联 PR | #392（CI 四绿 · squash 19e3f9ba） |
| **wiki_delta** | `n/a` |
| **wiki_delta_note** | 本仓未启用 WikiTrack |

## 人工闸（维护者授权）

- 三闸引用 m00177「签收，开始」：禁止 freeze 帧/schema 触碰 · 禁止跨 task 承载 · 禁止 freeze 概念语义漂移。
- 设计真源 07 §4 外部接口面 / §5 T2 行；m02028「本窗口任务继续」直执行。

## 背景

P1-T1（PR #387）已交付 goal_store 读写模块（分层纪律：读 best-effort / patch 显式抛 GoalNotFoundError→404、GoalStateTransitionError→409）。本单将其暴露为 REST 面，供 web/iOS 目标管理与人工复活（O-1：paused 仅人工 PATCH 复活）。

## 范围

1. 新增 `app/ops/goals/router.py`：
   - `GET /ops/goals?thread_id=...` → list_goals（含终态，前端展示用）。
   - `PATCH /ops/goals/{goal_id}` body `{"status": Literal["active","paused","done","abandoned"]}` → patch_goal_status；词表外由 pydantic Literal 前置 422（不进 store）。
   - 鉴权：CurrentUser（app.ops.deps）；tenant 复用 `resolve_header_against_session` + request.state.ops_tenant_id 先例（lg_rag/router.py:376-384 · hitl/router.py:59-62,755）：头/session 不一致 403、未知租户 422。
   - 错误映射：GoalNotFoundError→404 · GoalStateTransitionError→409。
   - 响应模型 pydantic：goal_id/thread_id/objective/status/created_at/updated_at。
2. `app/ops/router.py` 注册 goals router。
3. 新增 `tests/test_goals_rest.py`：未登录 401 · 词表外 422 · 跨租户 404 · 非法流转 409 · list/patch 200 正路径。

## 非范围

入口接线（lg_rag 懒创建 / hitl.resumed→active）= T4；uq_ops_goals_active_thread 迁移 = T4；注入装配 = T3（并行单）；SSE 帧；web/iOS 端改动。

## 失败路径

- 词表外 status → 422（pydantic，不进 store）。
- 跨租户/不存在 goal_id → 404（store 查询带 tenant_id 谓词，防跨租户探测，不用 403）。
- 非法流转（终态→任意等）→ 409。
- DB 故障 → 500（显式动作不吞错，与 patch 分层纪律一致）。

## 验收标准

- [x] `pytest tests/test_goals_rest.py` 真 PG 全绿（覆盖 401/422/404/409/200 五类）
- [x] 词表外 status 返回 422；跨租户 goal_id 返回 404；未登录 401；非法流转 409
- [x] ruff app tests 绿；graph-compile 绿
- [x] 01_modules.md goals 行登记 + 签收行

### 自检结论

（实施时回填）

## 必读列表

- workspace docs/01-scope/03-general-agent/07-p1-goal-design.md §4/§5
- `app/ops/goals/store.py`（T1 已交付接口）
- `app/ops/lg_rag/router.py:376-384`（tenant 解析先例）
- `app/ops/tenant_context.py:57`（resolve_header_against_session）
- `tests/test_chat_router.py`（client/override_auth fixture 体例）

## 思考轮控制

- R0（勘察）：tenant/auth/store 接口锚点已核（resolve_header_against_session :57 · goal_store 404/409 显式抛错 · fixture 体例）。
- R1（审查）：docs/harness/reviews/task_p1_t2_goal_rest_audit_R1_20261115.md。
- R2–R4：实施中按证补充。
- R5（组织人终裁）：维护者。

## 测试策略

真 PG（conftest opsdesk_test · DB_AVAILABLE skipif 体例）；TestClient + override_auth 假鉴权（test_chat_router.py 先例）；跨租户用直接 ORM 建行。

## 修订记录

- 2026-11-15：落卡过闸。
