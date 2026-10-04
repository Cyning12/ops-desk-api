# Task：B2 HITL 浏览器决策面（cookie maintainer pending + decide · 复用 resume）（hitl-browser-decide）

> **状态**：`ready`（裁定 D/E 已按「安全推荐」落定；20 R1 **通过**（0 阻塞 · 4 nit 转 30）；三闸维护者已签 approved 2026-09-30（`HG-GRAPH-MODULES` 签「图谱在册」· 端点备注随 30 交付落盘复核）→ **30 可开工**；按 SPEC 与 B1 串行）
> **类型**：**码面**（新增 cookie 端点 · 复用既有 store/resume · 零表结构 · 零 SSE 事件）
> **依据 SPEC**：`docs/spec/chat-history-hitl-ux/SPEC-chat-history-hitl-ux_v0.md`（signed 2026-09-30 · §2 B2 · §4 Q2/Q5 · §5 FP-3/FP-6 · §6 B2）
> **审查承接**：`docs/harness/reviews/spec_chat_history_hitl_ux_audit_R1_20260930.md`（PASS-WITH-NITS · N2 持久化路径本 task test_strategy 显式覆盖）
> **分支**：`task/chat-history-hitl-ux`（SPEC §Harness 元信息 默认后端分支 · B1/B2 串行 · 各自 PR）
> **10 帽**：2026-09-30 · 10-task 拆解（不实现代码 · 不签 HG-AUDIT-R1）

---

## Harness 元信息

| 字段 | 值 |
|---|---|
| **task_slug** | `hitl-browser-decide` |
| **git_branch** | `task/chat-history-hitl-ux` |
| **implement_repo** | `ops-desk-api` |
| **test_strategy** | `required` |
| **test_strategy_note** | 集成测（对齐 `tests/test_hitl.py`/`test_hitl_resume.py` 既有 harness）：401/403、owner 过滤、decide→resume 全链（图替身）、重复决定 409、跨用户 404、`OPS_HITL_PERSISTENCE=db` 下 decide→重建 store（模拟重启）→resume（N2 · `DB_AVAILABLE` 门控）；不连真 OA/真 LLM；OA 签名面零 diff 回归 |
| **code_quality_bar** | `L2_backend` |
| **graph_change_layer** | `G-L1` |
| **graph_delta** | `docs/_tech_graph/l1/01_modules.md` |
| **graph_delta_note** | `hitl`/`api` 行备注新 cookie 端点（`GET /api/ops/hitl/pending` · `POST /api/ops/hitl/requests/{id}/decide`）；OA 签名面端点在册不改；不新增一级模块/表/SSE 事件；`HG-GRAPH-MODULES` 随交付签录 |
| **wiki_delta** | `n/a` |
| **wiki_delta_note** | 无 `docs/coding_wiki/` 页面承载 hitl 端点真值（索引无对应条目）；路由真值以 G-L1 图谱备注为准 |
| **review_hat** | `20` |
| **required_invoke_hats** | `10,30,40` |
| **invoke_retention_profile** | `default` |
| **freeze_id** | 无（零新 SSE 事件 · 复用既有 `hitl.waiting`/`done{status}`） |
| **close_pr_policy** | `required` |
| **kpi_aggregator** | `CLOSE` |
| **orchestration** | 10 拆解 → 00 落定裁定 D/E → 20-task-audit R1 → `HG-AUDIT-R1` 人签 → 30/40 → PR + CI 四绿 → merge → CLOSE |

### 人工闸

| human_gate_id | status | blocks_hats | 说明 |
|---|---|---|---|
| HG-TASK-DRAFT | approved | 20-R1, 30 | 10 初稿经 20 R1 审查闭合 · 维护者签 2026-09-30 |
| HG-AUDIT-R1 | approved | 30 | 20-task-audit R1 通过（0 阻塞 · 4 nit 转 30）· 维护者签 2026-09-30 |
| HG-GRAPH-MODULES | approved | 30 | 维护者签「图谱在册」2026-09-30：现有 G-L1 模块覆盖本次改动面；新端点备注随 30 交付落盘 `01_modules.md` 并交付时复核 |
| HG-PILOT-OPSDESK-GLAYER | n/a | — | 复用既有 G-L1 模块，不涉物理分层试点新增 |

---

## 背景与目标

D2 冒烟实证：run 挂在 `waiting_approval`，后端已发 `hitl.waiting` + `done{status}` 帧，但浏览器永远拿不到待审批列表——`GET /api/ops/hitl/requests` 走 HMAC 签名头（OA 系统面），前端零表现。

一句话目标（SPEC Q2/Q5）：新增**cookie maintainer** 两个端点——`GET /hitl/pending`（当前用户可见的 pending）+ `POST /hitl/requests/{id}/decide`（置已决 · 与 callback 同语义 · 密钥不出服务器）；恢复**复用既有** `POST /requests/{id}/resume`（零改动）；OA 签名面零触碰。

---

## 已定夺（维护者令「冲突部分安全推荐方案进行」· 2026-09-30）

> **落定**：下列裁定采纳「安全推荐」项，原「30 拒开工」阻塞解除。

### 裁定 D · 新端点鉴权依赖口径（已采纳 D1 · 维护者 2026-09-30）

- **现状真读**：既有 `resume`/`get_request` 用 `AdminSyncAuth`（`deps.require_admin_sync`）= Bearer 机读 token **或** cookie maintainer；SPEC B2 验收写「cookie maintainer 可拿 · 非 maintainer 403 · 未登录 401」；owner 过滤需要真实 `OpsUser`（Bearer 路径返回 `None`）。
- **备选**：
  - **D1（采纳）**：新两端点用 `MaintainerUser`（`deps.require_maintainer`）——纯 cookie + `role=='maintainer'`（无 cookie → 401 · 非 maintainer → 403），精确对齐 SPEC + owner 过滤；`resume` 保持 `AdminSyncAuth` **零改动**（其 Bearer 路径不被新端点复用）（维护者令 2026-09-30 采纳）。
  - D2：沿用 `AdminSyncAuth`（允许 Bearer admin token，但拿不到 user 做 owner 过滤 · 与「cookie maintainer」字面不符 · 弃选）。

### 裁定 E · pending 列表归属过滤口径（已采纳 E1 · 维护者 2026-09-30）

- **现状真读**：`ops_hitl_requests` 行**无 `user_id`**；归属只能经 `run_id` → `lg_rag.event_store.run_owner` 反查（`hitl-outbound` 已允许 → `lg_rag`）。
- **备选**：
  - **E1（采纳）**：`pending` 仅返回 `run_owner == 当前用户` 的申请（承 SPEC 设计纪律 #3 归属隔离）；`run_owner` 解析不到（未落事件 / null store）→ 该条**排除 + error 日志**（不 500 · 不泄露）（维护者令 2026-09-30 采纳）。
  - E2：返回所有 pending（多 maintainer 场景可互批，但违归属隔离纪律 · 弃选）。
- **落定**：采纳 E1（维护者令 2026-09-30）→ 30 不再因此阻塞；多 maintainer 不能互批他人 run 为归属隔离设计使然，如有需要另立 task。

---

## 范围（钉死）

| # | 件 | 落点 | 动作 |
|---|---|---|---|
| P1 | pending 列表 | `GET /api/ops/hitl/pending`（`app/ops/hitl/router.py`） | 取 `store.alist(status="pending")` → 按裁定 E 过滤归属 → 字段族：`id` · `run_id` · `thread_id` · `reason` · `blocked_by` · `created_at`；返回 `{items, count}`（对齐既有 `list_requests` 外形） |
| P2 | 置已决 | `POST /api/ops/hitl/requests/{id}/decide` | body `{decision: approved|rejected}`（Pydantic `Literal`）→ 校验存在/归属/pending → 复用 `store.adecide(id, decision, by=当前用户, note)` · **不自动 resume**（客户端第二步调既有 `resume`） |
| P3 | 归属/台账 | 路由层 | 归属经 `run_owner`（裁定 E）；审计 `logger.info` 只记动作锚点（id/decision/by/at）· **不记内容**（SPEC 纪律 #4） |
| P4 | 测试 | `tests/test_hitl_pending_decide.py` | 401/403/owner 过滤/decide 语义/重复 409/跨用户 404/decide→resume 全链/db 重启路径（N2） |

## 非范围（钉死 · 越任一条即停）

- ❌ OA 签名面任何改动：`GET /hitl/requests` · `GET /hitl/runtime` · `POST /hitl/callback` 契约与鉴权不动（`signature.py`/`_require_signed` 零 diff）
- ❌ 改 `resume` 端点语义 / 鉴权（`AdminSyncAuth` 保持原样）
- ❌ `decide` 自动触发 resume（SPEC Q2 钉：两步）
- ❌ 新表 / 迁移 / 改 `HitlStore` 协议（复用 `adecide`）
- ❌ 新 SSE 事件类型 / 改 `hitl.waiting`/`done` 帧 / WS 推送
- ❌ 前端渲染（F2 专项 SPEC 另立 · Q4）
- ❌ 改 `InMemoryHitlStore`/`DbHitlStore` 既有语义（含 `WHERE status='pending'` 守卫）

---

## failure_paths

| 触发 | 行为 | 可重试 | 用户可见 |
|---|---|---|---|
| 未登录（无 cookie） | **401**（`require_maintainer` → `get_current_user`） | 是 | 登录 |
| 非 maintainer 角色 | **403** | 否 | 权限错误 |
| decide 未知 `id` / 他人 run 的申请 | **404** · 不泄露存在性（FP-1 口径） | 否 | 校验错误 |
| decide 重复 / 申请已决 | **409**（与 callback 同语义 · adecide 返回 None） | 否 | 冲突 |
| `decision` 非法值/缺字段 | **422**（Pydantic `Literal`） | 是 | 校验错误 |
| pending 列表 null store / `run_owner` 解析不到 | 返回空列表 / 跳过该条 + error 日志 · **不 500** | 是 | 列表可能空 |
| decide 成功但客户端未调 resume | run 仍挂 `waiting_approval`（文档/响应明示两步） | 是（再调 resume） | 待审批未推进 |
| 进程重启且 `OPS_HITL_PERSISTENCE≠db` | 申请丢（null/memory store）· FP-6 文档面提示（本 SPEC 不改默认值） | 否 | 审批消失 |
| OA 签名面出现 diff | **拒收**（既有测试全绿断言） | 是 | — |
| 30 未签 `HG-AUDIT-R1` 即改码 | **拒开工** | 是 | 须先 20 + 人签 |

---

## 验收标准

- [ ] `GET /hitl/pending`：cookie maintainer 200，仅含 `run_owner==当前用户` 的 pending；字段族齐（`id`/`run_id`/`thread_id`/`reason`/`blocked_by`/`created_at`）
- [ ] 非 maintainer（viewer fixture）→ **403**；未登录 → **401**（对齐 `tests/conftest.py` `override_auth_viewer/maintainer`）
- [ ] 异 owner 的 pending **不出现**在列表（裁定 E1）
- [ ] `POST .../decide` `approved` → 200 · store 行 `status=approved` · `decision_by=当前用户` · `decided_at` 非空；语义等价 callback
- [ ] 重复 decide / 已决申请 → **409**；未知 id → **404**；非法 `decision` → **422**
- [ ] 集成：挂起 run → `decide(approved)` → 既有 `POST .../resume` → 终帧 `done{completed}`（对齐 `tests/test_hitl_resume.py` 图替身）
- [ ] `decide(rejected)` → `resume` → 收工出结论（带「没批」语义 · 不解锁 · 承 resume 既有设计）
- [ ] 越权：他人 run 的 `request_id` → **404**
- [ ] **N2 持久化路径**：`OPS_HITL_PERSISTENCE=db` 下 decide 落库 → 重建 store（模拟重启）→ resume 读到已决（`DB_AVAILABLE` 门控 · 无库则 skip 并留痕）
- [ ] OA 签名面回归：`tests/test_hitl.py` 全绿；`POST /hitl/callback` HMAC 校验与既有行为零 diff；`app/ops/hitl/signature.py` 零 diff
- [ ] `.venv/bin/pytest tests -q --tb=short` 绿
- [ ] `.venv/bin/lint-imports --config .importlinter` 绿
- [ ] `./scripts/graph-compile.sh` exit 0；G-L1 备注落盘 + `HG-GRAPH-MODULES` 签录
- [ ] `npx --yes spec-wave@3.0.1 task lint-wiki-delta --target .` 通过

---

## 依赖

- SPEC：`docs/spec/chat-history-hitl-ux/SPEC-chat-history-hitl-ux_v0.md`（signed · §2 B2 · §4 Q2/Q5 · §5 FP-3/FP-6 · §6 B2）
- SPEC 审查：`docs/harness/reviews/spec_chat_history_hitl_ux_audit_R1_20260930.md`（N2）
- 码面真值：`app/ops/hitl/router.py`（`_require_signed` :54-62 · callback :98-138 · resume :240-330）· `app/ops/hitl/store.py`（`adecide` :41-48/215-228 · pending 守卫）· `app/ops/hitl/resume.py` · `app/ops/deps.py:56-63/86-111`（`require_maintainer`/`require_admin_sync`）· `app/ops/lg_rag/event_store.py:50-69`（`run_owner`）
- 先例：`docs/tasks/done/task_lg_rag_sse_resume.md`（归属 404 语义 · HITL resume 事件接续）；`tests/test_hitl.py` · `tests/test_hitl_resume.py` · `tests/test_hitl_resume_events.py`
- 标准：`docs/standards/CODING_BACKEND_L2_v1_zh.md`

---

## 给执行帽的必读列表

1. 本 task（含「已定夺」裁定 D/E）
2. SPEC §2 B2 · §4 Q2/Q5 · §5 FP-3/FP-6 · §6 B2
3. `app/ops/hitl/router.py`（签名面 / callback / resume 三处边界）
4. `app/ops/hitl/store.py`（`adecide` pending 守卫两实现一致性）· `app/ops/deps.py`（鉴权依赖二选一）
5. `app/ops/lg_rag/event_store.py:50-69`（`run_owner` 归属反查）
6. `tests/test_hitl.py` · `tests/test_hitl_resume.py` · `tests/conftest.py`（fixtures）
7. `docs/standards/CODING_BACKEND_L2_v1_zh.md` · `docs/_tech_graph/l1/01_modules.md`（hitl 行）

---

## 思考轮控制

| 轮 | 结论 | early_stop | reason（early_stop） | residual_risks |
|----|------|------------|----------------------|----------------|
| R0 | SPEC signed + D2 冒烟（挂起前端零表现）+ 代码锚点真读（签名面/AdminSyncAuth/adecide） | no | — | 无 |
| R1 | 范围 P1-P4 钉死；非范围锁 OA 签名面/resume/自动 resume/新表 | no | — | 无 |
| R2 | 方案=新增 cookie 端点（Q5 S1）+ 复用 adecide/resume；不碰 OA 面 | no | — | 无 |
| R3 | FP：401/403/404 不泄露/409 重复/422/owner 解析失败降级/重启丢申请（FP-6） | no | — | 无 |
| R4 | 验收全可 pytest 机断（fixtures + 图替身 + DB_AVAILABLE 门控） | no | — | 无 |
| R5 | 可交 20；裁定 D/E 未落定前 30 不启 | no | — | E1 下多 maintainer 不能互批他人 run（按归属隔离设计 · 如实标注） |

**actual_last_round**：R5 · **early_stop**：no · **residual_risks**：见 R5

### R0 · 问题框定

审批面浏览器不可达（签名面 OA 专用）；协议帧已完备，缺的是可达的查询/决策面。

### R1 · 开工闸

`HG-TASK-DRAFT`/`HG-AUDIT-R1`/`HG-GRAPH-MODULES` 均 pending（10 不代签）。范围静态：新端点 + 复用既有 store/resume。

### R2 · 竖切

P1 pending + P2 decide 两端点；恢复复用 `resume` 零改动；审计只记动作。

### R3 · 失败语义

见 failure_paths：最锋利边界 = 归属 404 不泄露 + 重复决定 409 + OA 面零 diff。

### R4 · 可测性

fixtures（maintainer/viewer）+ 图替身（既有 `test_hitl_resume.py`）可断全链；db 路径 `DB_AVAILABLE` 门控。

### R5 · 交付判定

可交 20-task-audit；裁定 D/E 由 00 落定后 30 才可启。

### 自检结论

（10-task · 2026-09-30）范围 P1–P4 钉死 · 非范围八条 · 验收 14 条可机断 · failure_paths 10 条 · 裁定 D/E 已按维护者令采纳安全推荐（D1/E1）· N2 持久化路径入 test_strategy · 思考轮 R0–R5 齐全 · 未签任何 human_gate · 未改 `app/`/`tests/`。

---

## 修订记录

| 日期 | 说明 |
|---|---|
| 2026-09-30 | 10-task 立稿：拆自 SPEC chat-history-hitl-ux §2 B2；锚点真读后把「cookie maintainer 依赖口径」与「pending 归属过滤」上抛为裁定 D/E；N2 持久化路径钉进 test_strategy |
| 2026-09-30 | 维护者令「冲突部分安全推荐方案进行」→ 裁定 D 采纳 D1（`MaintainerUser`）· 裁定 E 采纳 E1（owner 过滤）；阻塞解除 |
| 2026-09-30 | **20-task-audit R1 通过**（0 阻塞 · 4 nit 转 30 · 审查文 `docs/harness/reviews/task_hitl_browser_decide_audit_R1_20260930.md`）→ 维护者签 `HG-TASK-DRAFT`/`HG-AUDIT-R1` = approved；30 可开工（与 B1 串行） |
