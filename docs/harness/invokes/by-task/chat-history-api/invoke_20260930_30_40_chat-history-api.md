# Invoke：30（含 40）· chat-history-api

---

## 元信息表

| 字段 | 值 |
|------|-----|
| hat_id | 30（含 40） |
| task_slug | `chat-history-api` |
| task_paths | `docs/tasks/active/task_chat_history_api.md` |
| related_review_or_none | `docs/harness/reviews/task_chat_history_api_audit_R2_20260930.md`（R2 通过 · 0 阻塞） |
| git_branch | `task/chat-history-hitl-ux` |
| created_utc_or_local | 2026-09-30 |
| notes | 00 派工（web 子 Agent）；裁定 A1/B1 已定夺；不 push、不开 PR |

---

## 可复制 Prompt 快照（00 派工原文要点）

> 你是 **30 实现帽**（兼 40 验证），工作目录 ops-desk-api，分支 `task/chat-history-hitl-ux`（已在该分支，勿切分支、勿动 main）。
>
> 授权前提：task 表 `docs/tasks/active/task_chat_history_api.md` 人工闸 **HG-TASK-DRAFT / HG-AUDIT-R1 / HG-GRAPH-MODULES 均已 approved（维护者 2026-09-30）**，`npx spec-wave verify` PASS。30 授权成立。
>
> 裁定摘要：
> - **A1**：`run.start` payload 增**可选** `query` 键（非新 event_type · 旧 run 无键按 FP-4 降级）；`sse_stream.py` 除该键外零 diff
> - **B1**：路由落 `app/ops/lg_rag/history_router.py`（`APIRouter(prefix="/chat")`，在 `app/ops/router.py` 注册）；聚合纯函数落 `app/ops/lg_rag/history.py`；路径保持 `/api/ops/chat/threads`、`/api/ops/chat/threads/{thread_id}/history`；**`app/ops/chat/**` 零 diff**
> - **import 纪律**：`history_router.py` 取鉴权/ORM 须经同族 `app.ops.lg_rag.router` 间接取 `CurrentUser`/`OpsUser`；以 `lint-imports` 绿为准
>
> 范围 H1–H6（threads 列表 / thread 完整历史 / 聚合纯函数 / 归属 404 / event_store 只读扩展 / 图谱备注）；failure_paths：聚合超时 10s→504（常量可注入）· 缺 query 降级 · 事件缺口如实重建 · thread_id 非法 422 · 未登录 401。
>
> 测试：新增 `tests/test_chat_history_api.py`（造事件行 · 不连真 LLM）覆盖验收 14 条可机断项 + 旧测 grep 影响面回归（`test_lg_rag_sse_stream.py:101-102` · `test_lg_rag_session_continuity.py:166-167` · `test_multi_replica_dualproc.py:420-424` · `test_lg_rag_sse_token_stream.py:183/254` · `test_chat_ws.py:226/275` 全绿）。
>
> 非范围红线：❌ SSE 新事件类型/改其他帧语义 ❌ checkpoint 重建 ❌ 新表/迁移/写路径 ❌ 历史删除/编辑/标题持久化 ❌ 改 `app/ops/chat/**` ❌ HITL 决策面 ❌ 改 `multi/**`、`chat/graph.py`。
>
> 交付验收命令（全绿才可报完成）：① `.venv/bin/pytest tests -q --tb=short` ② `.venv/bin/lint-imports --config .importlinter` ③ `./scripts/graph-compile.sh` ④ `npx --yes spec-wave@3.0.1 task lint-wiki-delta --target .` ⑤ `ruff check app tests` ⑥ `git diff --stat` 自查（chat 零 diff · sse_stream 仅 query 键）。
>
> 提交纪律：commit 到 `task/chat-history-hitl-ux`（不 push、不开 PR）；commit message 规范中文摘要；invoke 快照落 `docs/harness/invokes/by-task/chat-history-api/`。

（完整原文见 00 会话 `_prompts/PROMPT_web_00_chat_history_hitl_ux.md` 派工消息。）

---

## GATE_VERIFY（30 首输出闸扫描）

| human_gate_id | task表status | blocks_30 | 30可开工？ |
|---|---|---|---|
| HG-TASK-DRAFT | approved | 20-R1, 30 | ✅ |
| HG-AUDIT-R1 | approved | 30 | ✅ |
| HG-GRAPH-MODULES | approved | — | ✅（「图谱在册」· 端点备注随本交付落盘复核） |
| HG-PILOT-OPSDESK-GLAYER | n/a | — | — |

`npx --yes spec-wave@3.0.1 verify --target . --task docs/tasks/active/task_chat_history_api.md`：**VERIFY: PASS** → 30 开工。

---

## 交付摘要（30/40 执行后）

### 改动文件清单

| 文件 | 动作 | 说明 |
|---|---|---|
| `app/ops/lg_rag/history.py` | 新增（H3） | 聚合纯函数：run 分组/终态/answer 聚合（终帧优先→delta 回退→32000 截断）/标题降级/subtask 摘要/hitl 收集/双 cursor 编解码/分页；不碰 DB |
| `app/ops/lg_rag/history_router.py` | 新增（H1/H2/H4） | `APIRouter(prefix="/chat")`：`GET /threads` + `GET /threads/{thread_id}/history`；鉴权经同族 `lg_rag.router` 间接取（N1 钉）；`HISTORY_AGGREGATE_TIMEOUT_S=10.0` 模块常量可注入 → 504 |
| `app/ops/lg_rag/event_store.py` | 扩展（H5） | `thread_owner`（run_owner 同语义）· `list_thread_activity_page`（GROUP BY + keyset）· `fetch_events_for_threads`；零新表/迁移/写路径 |
| `app/ops/lg_rag/sse_stream.py` | 最小改（A1） | `run.start` payload 增可选 `query` 键 + 注释；**其余帧零改动** |
| `app/ops/router.py` | 注册 | include `chat_history_router`；顺带 ruff I001 既有导入排序修正 |
| `tests/test_chat_history_api.py` | 新增 | 25 用例：纯函数 12 + DB 集成 11 + SSE 对拍 2（含 401/404/422/504/FP-4） |
| `docs/_tech_graph/l1/01_modules.md` | 备注（H6） | lg_rag 行 chat-history-api 备注 + HG-GRAPH-MODULES 签录行（2026-09-30） |
| `docs/_tech_graph/l1/10_flow_lg_rag.graph.yaml` → `.md` | 备注（H6） | description 增 B1 端点 + A1 query 键备注；version → 2026-09-30；graph-compile 重生成 |
| `docs/_tech_graph/shared/graph.json` | 重生成 | graph-compile 产物 |

### 六条验收命令结果

| # | 命令 | exit | 结果 |
|---|---|---|---|
| 1 | `.venv/bin/pytest tests -q --tb=short` | 0 | **1624 passed, 1 skipped**；3 errors = `test_import_from_supabase.py` 环境性存量（本机 PG 角色无 CREATEDB 权限 · **clean tree stash 复跑同现** · 与本改动无关） |
| 2 | `.venv/bin/lint-imports --config .importlinter` | 0 | 12 kept, 0 broken |
| 3 | `./scripts/graph-compile.sh` | 0 | done（warning 为既有 tech 词汇登记档提示 · 不咬 exit） |
| 4 | `npx --yes spec-wave@3.0.1 task lint-wiki-delta --target .` | 0 | PASS（scanned 147 · issues 0） |
| 5 | `ruff check app tests` | 1 | 本次改动触及文件 **All checks passed**；总数 55（基线 56 · 本交付 -1：router.py I001 顺手修复）；存量 55 条全部位于非本 task 文件（`multi/nodes.py` 等 · 其中 `multi/**` 是非范围红线不可动），CI ruff 步骤本即注释停用 |
| 6 | `git diff --stat` 自查 | — | `app/ops/chat/**` **零 diff**；`sse_stream.py` diff **仅 `run.start` query 键**（+注释） |

### 验收 14 条逐条对照

| # | 验收 | 结论 | 证据 |
|---|---|---|---|
| 1 | H1 字段族 + waiting_approval + 倒序 | ✅ | `test_threads_list_fields_waiting_approval_and_order`（2 run 同 thread + 1 run 异 thread） |
| 2 | H1 分页默认 20 / >100→422 / cursor 不重不漏 | ✅ | `test_threads_default_limit_20_and_over_100_422`（25 thread 翻页集相等 · 非法 cursor 422 · limit=0 422） |
| 3 | H2 完整重建 + run 升序 + 帧 seq 序 | ✅ | `test_thread_history_full_rebuild_and_run_order`（query/answer/subtasks 序/done.status/hitl requests） |
| 4 | answer 终帧优先 / delta 回退 / 32000 截断 | ✅ | 纯函数 `test_aggregate_answer_*`（边界 32000 不截 · 32001 截）+ API `test_thread_history_answer_truncation_flag` |
| 5 | 跨用户 → 404 | ✅ | `test_thread_history_cross_user_404`（他人 thread · 不 403）；未知 thread `test_thread_history_unknown_thread_404` |
| 6 | 缺 query 老 run 降级不阻塞（FP-4） | ✅ | `test_thread_history_missing_query_degrades_fp4`（标题=run_id 前缀+时间 · 列表不阻塞 · query 如实为 ""） |
| 7 | 超时 10s→504（常量可注入） | ✅ | `test_threads_aggregate_timeout_504` · `test_thread_history_aggregate_timeout_504`（注入 0.05s） |
| 8 | SSE 按 A1：仅 run.start +可选 query · 零新 event_type | ✅ | `test_run_start_carries_optional_query_no_new_event_type`（payload 恰={run_id,thread_id,mode,query} · types ⊆ freeze 集 · 落盘帧同形）；diff 自查仅该键 |
| 9 | `app/ops/chat/**` 零 diff | ✅ | `git diff --stat -- app/ops/chat/` = 空 |
| 10 | pytest 绿（新增测试文件） | ✅ | 1624 passed（新增 25 用例全绿） |
| 11 | 旧测 grep 影响面全绿 · subset-安全 | ✅ | `test_lg_rag_sse_stream.py`(15) · `test_lg_rag_session_continuity.py` · `test_lg_rag_sse_token_stream.py` · `test_chat_ws.py` · `test_multi_replica_dualproc.py`(9 · 跨实例 payload 逐帧对拍含新键双端一致) + resume/hitl/token 相邻面共 **105 用例全绿** |
| 12 | lint-imports 绿（同族间接取） | ✅ | 12 kept, 0 broken（`history_router.py` 经 `app.ops.lg_rag.router` 取 `CurrentUser`/`OpsUser`） |
| 13 | graph-compile exit 0 + G-L1 备注 + 签录 | ✅ | exit 0；`01_modules.md` lg_rag 行备注 + HG-GRAPH-MODULES 签录行；`10_flow_lg_rag` yaml/md 同步 |
| 14 | lint-wiki-delta 通过 | ✅ | PASS（issues 0） |

### 非范围红线自查

- SSE 新事件类型 / 改其他帧语义：❌ 未越（对拍测试锁 freeze 集）
- checkpoint 重建：❌ 未越（真源仅事件表）
- 新表/迁移/写路径：❌ 未越（只读面 · event_store 仅加 SELECT）
- 历史删除/编辑/标题持久化：❌ 未越（标题实时派生）
- 改 `app/ops/chat/**`：❌ 未越（零 diff 实证）
- HITL 决策面（B2）：❌ 未越
- 改 `multi/**` / `chat/graph.py`：❌ 未越

### 遗留风险 / 偏差

1. `test_import_from_supabase.py` 3 errors 为**环境性存量**（本机 PG 角色无 CREATEDB 权限 · clean tree 复跑同现），与本改动无关；CI 无 postgres service 时整文件 skip。
2. `ruff check app tests` 存量 55 条（基线 56）全部在非本 task 文件；其中 `app/ops/lg_rag/multi/nodes.py` 6 条位于**非范围红线**文件不可动。本次改动触及文件 ruff 全绿。CI ruff 步骤本即注释停用，事实质量门 = 不新增 ruff 错误（达成 · 净 -1）。
3. H1 threads 列表对每页 thread 拉全量事件行在纯 Python 聚合（标题/最新态需读帧），page ≤100 有 10s 超时 504 兜底；大事件量 thread 的历史端点同理由 limit 分页 + 32000 截断有界。
4. `waiting_approval` run 的标题取**最早** run 的 query（FP-4 语义）；pending run 自身 query 由 A1 新键覆盖，存量旧 pending run 降级为 run_id 前缀+时间。

**结论：可进 PR 环节**（不 push、不开 PR 已由本帽遵守 · 00 统筹后续）。
