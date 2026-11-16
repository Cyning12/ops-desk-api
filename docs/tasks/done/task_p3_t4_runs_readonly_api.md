---
title: task · feat · P3-T4 runs 只读端点——threads/{id}/runs 列表 + runs/{id}/events 白名单帧流
---

# task · feat · P3-T4 runs 只读端点——threads/{id}/runs 列表 + runs/{id}/events 白名单帧流

> **状态**：`done`（2026-11-16 落卡 → 同日 feat PR #418 squash merge d9700b87 · CLOSE 关账）
> **来源**：issue Cyning12/ops-desk-workspace#23（m03064/m03283 夜间授权 · 契约真源 workspace 15-p3-contracts.md v1 终稿 §3/§4/§0 冻结词表 · commit 62af6ea；操作真源 lead 委派书 m00002）

## Harness 元信息

| 键 | 值 |
|----|----|
| **task_slug** | p3-t4-runs-readonly-api |
| base | f1d0dd28 |
| 关联 issue | Cyning12/ops-desk-workspace#23 |
| 关联 PR | （feat PR 待开 · 关账波 PR 随 CLOSE 波回填） |
| **wiki_delta** | `n/a` |
| **wiki_delta_note** | 本仓未启用 WikiTrack；本波为 lg_rag runs 只读端点 |
| graph_change_layer | G-L1（01_modules.md lg_rag 行备注 + HG-GRAPH-MODULES 签收行） |
| review_hat | 20（R1 审查文 docs/harness/reviews/task_p3_t4_runs_readonly_api_audit_R1_20261116.md · GO） |

### 人工闸

| human_gate_id | status | blocks_hats | 说明 |
|---------------|--------|-------------|------|
| HG-TASK-DRAFT | approved | 30 | approved 2026-11-16 · 授权 issue #23 m03064/m03283（夜间授权）+ 15 契约终稿 §3 + lead 委派书 m00002 为唯一范围真源 |
| HG-AUDIT-R1 | approved | 30 | approved 2026-11-16 · 同上授权 + R1 审查文 docs/harness/reviews/task_p3_t4_runs_readonly_api_audit_R1_20261116.md（GO） |
| HG-GRAPH-MODULES | approved | 30 | approved 2026-11-16 · 同上授权（新路由属既有 lg_rag 模块行内备注义务，无新一级模块/表/SSE 事件类型）· lg_rag 行备注随 30 交付回填 |

## 背景

P3（Scheduler + runs 只读 API）第 4 单。T2（scheduler 本体）并行在途，`ops_schedules`/`ops_schedule_fires` 表尚未落地。本单交付两个**只读**端点（契约 §3）：

- `GET /api/ops/lg-rag/threads/{thread_id}/runs`：thread 属主卡片的 runs 列表（keyset 分页），含 schedule 归因投影。
- `GET /api/ops/lg-rag/runs/{run_id}/events`：单 run 的事件帧流（白名单过滤 + 500 帧截断 + after_seq 续拉）。

契约 §3.3 已核实：现落库 `event_type` 词表恰等于 §0 冻结词表 8 值，白名单是**前置防泄层**（未来内部帧类型落库时零改动拦截），非词表修补。

## 范围

1. **`app/ops/lg_rag/run_store.py` 增量**：
   - `list_thread_runs_page(...)`：thread_id + user_id 谓词，keyset（created_at desc, run_id desc），limit ≤50；投影 run_id/thread_id/status（六词表原值直出）/created_at/finished_at。
   - `fetch_run_start_queries(run_ids)`：批量反查各 run 的 run.start 帧 payload.query（单次 IN 查询防 N+1）。
   - `fetch_schedule_attributions(run_ids)`：raw SQL 契约钉名 `ops_schedule_fires JOIN ops_schedules` 批量反查 {schedule_id, name, fire_id}（IN 单次查询）；表未落地（T2 未合）→ try/except UndefinedTable → 空归因 + logger.warning（表在即生效零改动）。
2. **`app/ops/lg_rag/event_store.py` 增量**：
   - `list_run_events_page(run_id, *, after_seq, limit)`：`event_type IN 8 值白名单` **SQL 层过滤**，按 seq 升序取 limit+1 判定截断。归属校验复用既有 `assert_run_owned`。
3. **新增 `app/ops/lg_rag/runs_router.py`**（prefix=/lg-rag · 承 history_router 体例：鉴权 CurrentUser/ORM OpsUser 经 `app.ops.lg_rag.router` 间接取，零 .importlinter 改动）：
   - `GET /threads/{thread_id}/runs`：`thread_store.thread_owner` != 当前用户 → 404 detail="Thread not found"；limit Query 默认 20、上限 50（超限 422）；cursor max_length=512（复用 history.encode/decode_cursor · {ts,rid} 键）；query_summary = run.start payload.query 截 80（[:79]+"…" 承 history.py 风格）；schedule_attribution 无归因 → null。响应 `{"ok":true,"data":{"runs":[...],"next_cursor":...}}`。
   - `GET /runs/{run_id}/events`：`assert_run_owned` 前置（跨用户/未知 → 404 detail="Run not found"）；after_seq Query 默认 0 ge=0；单次最多 500 帧，超出 → truncated:true + next_after_seq=末帧 seq；事件对象仅 {seq, event_type, payload, created_at} 四字段。响应 `{"ok":true,"data":{"run_id","events":[...],"truncated","next_after_seq"}}`。
4. **`app/ops/router.py`**：include_router 注册 runs_router（承 lg_rag_router 既有面，无路径冲突）。
5. **测试 `tests/test_lg_rag_runs_readonly_api.py`**（真 PG）：双用户 404 矩阵、白名单过滤断言（词表外 event_type 行不落响应）、分页/截断/after_seq 续拉、空 run/空 thread、schedule 归因路径（raw SQL 临时建表覆盖后 drop · 不碰 alembic）。
6. **图谱**：`docs/_tech_graph/l1/01_modules.md` lg_rag 行备注（新增 runs_router 端点面）+ HG-GRAPH-MODULES 签收行。

## 非范围

- `ops_schedules`/`ops_schedule_fires` DDL 与 ORM 模型（T2 范围）；本波只读契约钉名反查，不建表、不碰 alembic。
- SSE /stream /replay 写路径、event_type 词表扩缩、status 六词表修补。
- schedules CRUD 端点（T2/T3 范围）、runs 写路径（T5 范围）。
- 前端/iOS 任何改动。

## 失败路径

1. 跨用户/未知 thread 请求 runs 列表 → 404（不泄存在性）。
2. 跨用户/未知 run 请求 events → 404（assert_run_owned 既有语义）。
3. 词表外 event_type 帧（未来内部帧）→ SQL 层过滤不落响应、不进应用内存。
4. fires 表未落地 → schedule_attribution 全 null + warning，端点不炸。
5. 恶意 cursor（非 base64/非 JSON/缺键/超长）→ 422。
6. limit>50 或 <1 → 422；after_seq<0 → 422。
7. run 零事件 → 200 空列表（不 404）；thread 零 runs → 200 空列表。
8. query 超 80 字 → 截断 [:79]+"…"；run.start 无 query 键 → query_summary null。

## 验收标准

- [x] 两端点上线且挂 `/api/ops/lg-rag` 前缀，响应壳 `{"ok":true,"data":...}`
- [x] 双用户 404 矩阵测试通过（thread/run × owner/stranger/unknown）
- [x] 白名单过滤断言通过：词表外 event_type 行落库后不落响应
- [x] keyset 分页正确（跨页无重无漏）；limit=51 → 422；坏 cursor → 422
- [x] 505 帧 → 500 帧 + truncated:true + next_after_seq；after_seq 续拉取余 5 帧 truncated:false
- [x] 空 run events 200 空列表；空 thread runs 200 空列表
- [x] query_summary 截 80 断言；schedule 归因路径（临时表）断言 {schedule_id,name,fire_id}
- [x] `pytest tests` 真 PG 全绿（五键 blank 前缀）；`ruff check app tests` 绿；import-linter 绿
- [x] registry entry active base=f1d0dd28；`npx --yes spec-wave@3.5.0 task lint --file` PASS
- [x] CI 四绿（pytest/check/import-linter/lint-wiki-delta）→ squash merge → CLOSE 波钉 wave_tip

### 自检结论

- 13 用例真 PG 全绿（`pytest tests/test_lg_rag_runs_readonly_api.py` 13 passed · 五键 blank 前缀）：验收 1-7 条全机断覆盖。
- `ruff check`（改动五件）All checks passed；`lint-imports` 12 kept 0 broken（零 .importlinter 改动）。
- 全套 `pytest tests`（2288→2300 passed）：本地 23 红与干净 HEAD 基线逐签一致（环境性 multi_replica_dualproc/strategy_builder 顺序依赖 + 脏树期 TC8/wave_gate_registry 结构性红 · 提交后复绿），CI 四绿终裁。
- registry entry active + spec-wave verify PASS（三人工闸 approved）+ task lint PASS（2026-11-16 10 阶段）。
- 图谱 01_modules.md lg_rag 行备注 + HG-GRAPH-MODULES 签收行已回写（30 阶段）。

## 必读列表

- workspace `docs/05-plan/15-p3-contracts.md` v1 终稿（§3 两端点契约 · §0 冻结词表 · §4.1 fires 表 · §4.4 归因真源）commit 62af6ea
- `app/ops/lg_rag/event_store.py`（assert_run_owned:350 · LgRagRunNotFoundError:24 · list_thread_activity_page:436 keyset 先例）
- `app/ops/lg_rag/run_store.py`（OpsLgRagRun 读写面）
- `app/ops/lg_rag/thread_store.py`（thread_owner）
- `app/ops/lg_rag/history.py`（TITLE_MAX_CHARS=80 · encode/decode_cursor · make_runs_cursor 先例）
- `app/ops/lg_rag/history_router.py`（import 纪律 · 404 detail · 响应壳体例）
- `app/db/models.py:258/:280`（OpsLgRagRunEvent/OpsLgRagRun）
- `tests/test_chat_history_api.py`（测试体例真源）

## 思考轮

| 轮 | 议题 | 状态 |
|----|------|------|
| R0 | 范围对账（委派书 vs 契约 §3/§4） | done |
| R1 | 失败路径推演（404 矩阵/白名单防泄/截断/422 面） | done |
| R2 | 非范围边界（T2 fires 表/T3 schedules CRUD/T5 写路径） | done |
| R3 | 关键决策记录（白名单 SQL 层/thread 归属真源/归因容错反查/零 import-linter 改动） | done |
| R4 | 体例对账（p2b-t3 模板/registry/invokes/审查文） | done |
| R5 | 收尾复核（验收 checklist 全锚定） | done |

| 轮 | 结论 | early_stop |
|----|------|-----------|
| R0 | 委派两端点与契约 §3.1/§3.2 逐字段对齐，零冲突 | false |
| R1 | 失败路径 8 条可机判，核心=白名单 SQL 层+fires 缺位降级 | false |
| R2 | 非范围=T2 DDL/T3 CRUD/T5 写路径/SSE/词表修补 | false |
| R3 | 五项关键决策落定（见 R3 小节） | false |
| R4 | 体例全承 p2b-t3 模板 | false |
| R5 | 验收 10 条全锚定，可进 30 | false |

actual_last_round: R5

### R0 · 范围对账

委派两端点与契约 §3.1/§3.2 逐字段对齐：投影字段、keyset 键、limit 上限 50（R-P3-8）、cursor 512、500 帧截断、四字段事件对象、响应壳形状全部有契约锚。归因真源=fires 台账三元组（§4.4），query 前缀文本非归因依据。

### R1 · 失败路径推演

见「失败路径」8 条；核心：白名单必须 SQL 层（否则截断形状侧漏内部帧存在性）；fires 表缺位必须降级 null 不炸端点（T2 并行波时序）。

### R2 · 非范围边界

fires/schedules DDL 是 T2 的表，本波 CREATE 即越权 → raw SQL 契约钉名 + UndefinedTable 容错；测试临时建表仅覆盖反查路径，drop 收尾不留痕，不碰 alembic（banned_prefixes）。

### R3 · 关键决策记录

- **白名单过滤落点=SQL 层**（WHERE event_type IN 8 值）：500 帧截断须按白名单后帧计数（响应层过滤会页内欠载且内部帧存在性可经截断形状侧漏）；非白名单 payload 不进应用内存=防泄最小面。
- **thread 归属真源=thread_store.thread_owner（thread SoT ops_lg_rag_threads）**：契约 §3.1 用词与 §1.7 schedule 归属同源；空 thread（零事件）应 200 空列表而非 404（事件表真源零帧 None→404 会误伤）。
- **schedule_attribution 容错批量反查**：run_ids IN 单次 raw SQL（防 N+1）；try/except UndefinedTable → 空归因+warning；表随 T2 落地即生效零改动（R-P3-T4-1）。
- **query_summary 截断**承 history.py 风格 len>80 → [:79]+"…"。
- **零 .importlinter 改动**：runs_router 不直 import app.db/app.ops.deps，全走 store 层 + app.ops.lg_rag.router 间接取鉴权。

### R4 · 体例对账

task 档照 task_p2b_t3_mcp_translator.md 模板；registry entry 字段全（base=f1d0dd28 · allowed_app_files 四件 · banned alembic/+scripts/）；invokes by-task/p3-t4-runs-readonly-api/{10,30,40,50}；R1 审查文落盘。

### R5 · 收尾复核

验收 10 条逐条有实现锚/测试锚；测试纪律（真 PG · 五键 blank · CI 终裁）承委派书。

## 实现备忘

### 偏差登记

- 无契约偏差。实现备忘：契约 §3.2 白名单 8 值含 `hitl.resumed`（既有 freeze 测试词表 7 值无此帧系 SSE start-frame 对拍口径，非冲突）。

### 限制登记

- **R-P3-T4-1（fires 表缺位）**：schedule_attribution 反查依赖 `ops_schedule_fires`/`ops_schedules`（T2 范围，本波在途未合）。实现为容错降级：表不存在 → 归因全 null + warning；表在即生效。测试以 raw SQL 临时建表覆盖归因路径后 drop。

### 目录文件清单

- `app/ops/lg_rag/runs_router.py`（新 · 两端点 · prefix=/lg-rag · 鉴权经 app.ops.lg_rag.router 间接取）
- `app/ops/lg_rag/run_store.py`（尾增 P3-T4 节：`list_thread_runs_page`/`fetch_run_start_queries`/`fetch_schedule_attributions` + `_ATTRIBUTION_SQL` raw SQL 契约钉名）
- `app/ops/lg_rag/event_store.py`（尾增 `RUN_EVENTS_ALLOWED_TYPES` 8 值 + `list_run_events_page`）
- `app/ops/router.py`（include_router(lg_rag_runs_router)）
- `tests/test_lg_rag_runs_readonly_api.py`（新 · 13 用例）
- `docs/_tech_graph/l1/01_modules.md`（lg_rag 行备注 + HG-GRAPH-MODULES 签收行）
- `docs/harness/reviews/task_p3_t4_runs_readonly_api_audit_R1_20261116.md`（R1 审查文）
- `docs/harness/audit_gates/registry.yaml`（entry active）
- `docs/harness/invokes/by-task/p3-t4-runs-readonly-api/`（10/30/40/50）

## 测试策略

真 PG `postgresql+asyncpg://ops:ops_password@localhost:5432/opsdesk_test`；五键 blank 前缀（OPS_HITL_PERSISTENCE= OPS_CAPABILITY_ALLOW_WRITE= OPS_CAPABILITY_ALLOW_WRITE_TAGS= OPS_CAPABILITY_PERSISTENCE= OPS_CAPABILITY_EXTRA_MANIFESTS=）；新增 `tests/test_lg_rag_runs_readonly_api.py`（体例承 test_chat_history_api.py：造 OpsUser 行满足 FK · 按 id 前缀清场）；CI 四绿终裁。

## 修订记录

| 日期 | 修订 |
|------|------|
| 2026-11-16 | 落卡（夜间自动执行波 · 授权 issue #23 m03064/m03283） |
| 2026-11-16 | 30 实现 + 图谱回写 + 自检回填（13 用例真 PG 绿 · ruff/import-linter 绿） |
| 2026-11-16 | 40 验收 + feat PR #418 CI 四绿 → squash merge d9700b87 · 50 CLOSE 关账（迁 done · registry closed 钉 wave_tip） |
