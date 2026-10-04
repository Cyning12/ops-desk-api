# Invoke：30（含 40）· hitl-browser-decide

---

## 元信息表

| 字段 | 值 |
|------|-----|
| hat_id | 30（含 40） |
| task_slug | `hitl-browser-decide` |
| task_paths | `docs/tasks/active/task_hitl_browser_decide.md` |
| related_review_or_none | `docs/harness/reviews/task_hitl_browser_decide_audit_R1_20260930.md`（R1 通过 · 0 阻塞 · 4 nit 转 30） |
| git_branch | `task/chat-history-hitl-ux`（叠在 B1 commit `9904f81` 之上 · B1 交付物零回退） |
| created_utc_or_local | 2026-09-30 |
| notes | 00 派工（web 子 Agent）；裁定 D1/E1 已定夺（维护者 2026-09-30）；不 push、不开 PR |

---

## 可复制 Prompt 快照（00 派工原文要点）

> 你是 **30 实现帽**（兼 40 验证），工作目录 ops-desk-api，分支 `task/chat-history-hitl-ux`（已在该分支，勿切分支、勿动 main）。分支上已有 B1 交付 commit `9904f81`（chat-history-api），B2 改动**叠在其上**，不得回退/改动 B1 交付物。
>
> 授权前提：task 表人工闸 **HG-TASK-DRAFT / HG-AUDIT-R1 / HG-GRAPH-MODULES 均已 approved（维护者 2026-09-30）**，`npx spec-wave verify` PASS。30 授权成立。
>
> 裁定摘要：
> - **D1**：新两端点用 `MaintainerUser`（`deps.require_maintainer`）——纯 cookie + `role=='maintainer'`（无 cookie → 401 · 非 maintainer → 403）；既有 `resume` 保持 `AdminSyncAuth` **零改动**
> - **E1**：`pending` 仅返回 `run_owner == 当前用户` 的申请（经 `run_id` → `lg_rag.event_store.run_owner` 反查）；`run_owner` 解析不到 → 该条排除 + error 日志（不 500 · 不泄露）
>
> 范围 P1–P4：`GET /api/ops/hitl/pending`（字段族 `id`/`run_id`/`thread_id`/`reason`/`blocked_by`/`created_at` · `{items, count}`）；`POST /api/ops/hitl/requests/{id}/decide`（Pydantic `Literal` · 复用 `store.adecide` · **不自动 resume**）；审计只记动作锚点；`tests/test_hitl_pending_decide.py`（401/403/owner 过滤/decide 语义/重复 409/跨用户 404/decide→resume 全链图替身/`OPS_HITL_PERSISTENCE=db` decide→重建 store→resume · N2 · DB_AVAILABLE 门控）。
>
> 20 R1 四 nit：N1 补 `test_hitl_resume_events.py`/`test_lg_rag_sse_hitl.py` 回归；N2 owner 解析不到补独立机断；N3 `/hitl/runtime` 回归点名跑绿；N4 `created_at` 断言「非空」而非具体类型。
>
> 非范围红线：❌ OA 签名面任何改动（`signature.py`/`_require_signed` 零 diff）❌ 改 resume 语义/鉴权 ❌ decide 自动 resume ❌ 新表/迁移/改 `HitlStore` 协议 ❌ 新 SSE 事件/改帧 ❌ 前端渲染 ❌ 改 InMemory/Db store 既有语义 ❌ 改动 B1 交付物。
>
> 交付验收命令（全绿才可报完成）：① `.venv/bin/pytest tests -q --tb=short` ② `.venv/bin/lint-imports --config .importlinter` ③ `./scripts/graph-compile.sh` ④ `npx --yes spec-wave@3.0.1 task lint-wiki-delta --target .` ⑤ `ruff check app tests`（触及文件全绿 · 不新增）⑥ `git diff` 自查（signature 零 diff · callback 零 diff · B1 零回退）。
>
> 提交纪律：commit 到 `task/chat-history-hitl-ux`（不 push、不开 PR）；中文摘要 commit message；invoke 快照落 `docs/harness/invokes/by-task/hitl-browser-decide/`。

（完整原文见 00 会话 `_prompts/PROMPT_web_00_chat_history_hitl_ux.md` 派工消息。）

---

## GATE_VERIFY（30 首输出闸扫描）

| human_gate_id | task表status | blocks_30 | 30可开工？ |
|---|---|---|---|
| HG-TASK-DRAFT | approved | 20-R1, 30 | ✅ |
| HG-AUDIT-R1 | approved | 30 | ✅ |
| HG-GRAPH-MODULES | approved | — | ✅（「图谱在册」· 端点备注随本交付落盘复核） |
| HG-PILOT-OPSDESK-GLAYER | n/a | — | — |

`npx spec-wave verify --target . --task docs/tasks/active/task_hitl_browser_decide.md`：**VERIFY: PASS** → 30 开工。

---

## 交付摘要（30/40 执行后）

### 改动文件清单

| 文件 | 动作 | 说明 |
|---|---|---|
| `app/ops/hitl/router.py` | 扩展（P1/P2/P3） | 新增 `GET /hitl/pending`（`MaintainerUser` · E1 归属过滤 · `_run_owner_of` 反查 · 解析不到排除+error 日志 · alist 故障降级空列表）+ `POST /hitl/requests/{id}/decide`（`_DecidePayload` Pydantic `Literal` → 422 · 归属 404 不泄露 · 复用 `adecide` → 重复 409 · 响应带 `resume` 第二步提示 · **不自动 resume**）+ 模块 docstring 端点表；**diff 仅 +141/-2（-2 为 import 行拓宽）· callback/`_require_signed`/resume 区域零触碰** |
| `tests/test_hitl_pending_decide.py` | 新增（P4 · N1–N4） | 20 用例：401×2/403×2 · owner 过滤+字段族 · owner 解析不到（None/异常/alist 故障）三降级 · null store 空列表 · decide 语义+审计锚点 · 不自动 resume（spy）· 未知 404/跨用户 404/归属不可判 404 · 重复 409 · 非法 422 · decide→resume 全链图替身（approved→replan 解锁 / rejected→settle 收工）· `/hitl/runtime` 回归（N3）· **db 持久化全链**（N2 · 真 PG decide→重建 store 模拟重启→resume） |
| `docs/_tech_graph/l1/01_modules.md` | 备注（图谱 H6 对应件） | `hitl`/`api` 行备注新 cookie 端点（裁定 D1/E1）+ HG-GRAPH-MODULES 签录行（2026-09-30）；OA 签名面端点在册不改 |
| `docs/_tech_graph/shared/graph.json` | 重生成 | graph-compile 产物（仅 generated_at 时间戳） |
| `docs/harness/invokes/by-task/hitl-browser-decide/invoke_20260930_30_40_hitl-browser-decide.md` | 新增 | 本文件 |

### 六条验收命令结果

| # | 命令 | exit | 结果 |
|---|---|---|---|
| 1 | `.venv/bin/pytest tests -q --tb=short` | **0** | **1647 passed, 1 skipped**（含新增 20 用例；B1 交付时存量的 `test_import_from_supabase.py` 3 errors = 本机 PG `ops` 角色无 CREATEDB 权限——本次经本机 superuser `ALTER ROLE ops CREATEDB` 修复本地环境后**真绿**，clean tree 复跑已证与代码无关） |
| 2 | `.venv/bin/lint-imports --config .importlinter` | 0 | 12 kept, 0 broken（hitl→db/lg_rag 既有边复用 · `router→deps` 既有 ignore） |
| 3 | `./scripts/graph-compile.sh` | 0 | done（warning 为既有 tech 词汇登记档提示 · 不咬 exit） |
| 4 | `npx --yes spec-wave@3.0.1 task lint-wiki-delta --target .` | 0 | PASS（scanned 147 · issues 0） |
| 5 | `ruff check app tests` | 1（存量） | 本次触及文件 **All checks passed**；全仓 66 条存量 = clean tree 基线 66（**零新增**；B1 时点 55 → 现 66 的差异为 miniconda ruff 0.9.10 与 B1 时点环境口径差，非本交付引入）；存量全部位于非本 task 文件 |
| 6 | `git diff` 自查 | — | `app/ops/hitl/signature.py` **零 diff**；router.py diff 仅新增（-2 行均为 import 拓宽 · callback HMAC 行为零 diff）；B1 的 11 文件中 **app/+tests/ 零 diff**（仅 `01_modules.md`/`graph.json` 按图谱回写叠加 · B1 行未动） |

### 验收 14 条逐条对照

| # | 验收 | 结论 | 证据 |
|---|---|---|---|
| 1 | `GET /hitl/pending` cookie maintainer 200 · 仅 own pending · 字段族齐 | ✅ | `test_pending_lists_only_own_runs_with_field_family`（own+other 两 run · 字段集恰 6 键 · created_at 非空 N4） |
| 2 | 非 maintainer 403 · 未登录 401 | ✅ | `test_pending_requires_login_401`/`_viewer_is_403` + decide 同两条（对齐 conftest override 口径 · `@wraps` 兼容 `require_admin_sync` 位置调用） |
| 3 | 异 owner pending 不出现（E1） | ✅ | 同 #1（`run-other` 归属他人被排除 · count=1） |
| 4 | decide approved → 200 · status=approved · decision_by=当前用户 · decided_at 非空 | ✅ | `test_decide_approved_marks_decided_and_audits`（响应+store 双断言 · 审计锚点 id/decision/by 在 INFO 日志） |
| 5 | 重复/已决 409 · 未知 404 · 非法 422 | ✅ | `test_decide_duplicate_is_409`（首决不被覆盖）· `test_decide_unknown_id_404` · `test_decide_invalid_decision_is_422`（含缺字段） |
| 6 | 集成：挂起 → decide(approved) → 既有 resume → 图跑完（图替身） | ✅ | `test_decide_approved_then_resume_drives_the_graph`（最小 observe 图真挂起真恢复 · `hitl_unlocked_ids==[T1]` · verdict=replan；对齐 `test_hitl_resume.py` harness 的图替身口径） |
| 7 | decide(rejected) → resume → 收工出结论（不解锁） | ✅ | `test_decide_rejected_then_resume_settles`（verdict=settle · `hitl_unlocked_ids==[]`） |
| 8 | 越权：他人 run 的 request_id → 404 | ✅ | `test_decide_other_users_run_is_404_not_leaked`（申请原样 pending · 不泄露）；归属不可判同 404 `test_decide_unresolvable_owner_is_404_with_error_log` |
| 9 | N2 持久化：db 下 decide 落库 → 重建 store（模拟重启）→ resume 读到已决 | ✅ | `test_db_decide_survives_store_rebuild_then_resume`（**真 PG 真跑**：`OPS_HITL_PERSISTENCE=db` 装配 · 事件表归属帧 FK 真用户 · PG checkpointer 挂起 · HTTP decide → reset+reconfigure=重启 → aget 已决 → resume verdict=replan；本机 DB_AVAILABLE=true 未 skip） |
| 10 | OA 签名面回归：`test_hitl.py` 全绿 · callback HMAC 零 diff · `signature.py` 零 diff | ✅ | 点名回归 `test_hitl.py`+`test_hitl_resume.py`+`test_hitl_resume_events.py`+`test_lg_rag_sse_hitl.py`+`test_chat_history_api.py` 共 **90 passed**；`git diff app/ops/hitl/signature.py` = 空；router diff 无 callback 区改动 |
| 11 | `.venv/bin/pytest tests -q --tb=short` 绿 | ✅ | 1647 passed, 1 skipped · exit 0 |
| 12 | `.venv/bin/lint-imports --config .importlinter` 绿 | ✅ | 12 kept, 0 broken |
| 13 | graph-compile exit 0 · G-L1 备注落盘 · HG-GRAPH-MODULES 签录 | ✅ | exit 0；`01_modules.md` hitl/api 行备注 + 签录行 |
| 14 | lint-wiki-delta 通过 | ✅ | PASS（issues 0） |

### 20 R1 四 nit 对照

| nit | 结论 | 证据 |
|---|---|---|
| N1 补 `test_hitl_resume_events.py`/`test_lg_rag_sse_hitl.py` 回归 | ✅ | 点名回归 5 文件 90 passed（含这两件 + `test_hitl.py`/`test_hitl_resume.py`/`test_chat_history_api.py`） |
| N2 owner 解析不到 → 排除+error 日志+不 500 独立机断 | ✅ | `test_pending_excludes_unresolvable_owner_with_error_log`（None）+ `test_pending_owner_lookup_exception_does_not_500`（异常）+ `test_pending_alist_failure_degrades_to_empty_list`（alist 故障）+ decide 侧 404 变体；caplog 断言 error 级日志 |
| N3 `/hitl/runtime` 回归点名跑绿 | ✅ | `test_hitl_runtime_endpoint_intact`（AdminSyncAuth cookie 路径 200 · mode/persists/callback_secret_configured 字段在） |
| N4 `created_at` 断言「非空」而非具体类型 | ✅ | 内存用例与 db 用例均只断 truthy（注释注明 InMemory=float / Db=ISO 字符串） |

### 非范围红线自查

- OA 签名面（`GET /hitl/requests` · `GET /hitl/runtime` · `POST /hitl/callback` · `signature.py`/`_require_signed`）：❌ 未越（signature.py 零 diff · router diff 仅新增段 · test_hitl.py 全绿）
- 改 `resume` 语义/鉴权：❌ 未越（resume 区域零 diff · `test_hitl_resume*.py` 全绿）
- decide 自动 resume：❌ 未越（spy 断言 `resume_hitl_run` 零调用 · 响应明示两步）
- 新表/迁移/改 `HitlStore` 协议：❌ 未越（复用 `alist`/`aget`/`adecide`）
- 新 SSE 事件/改 `hitl.waiting`/`done` 帧/WS：❌ 未越（零 SSE 面 diff）
- 前端渲染：❌ 未越
- 改 InMemory/Db store 既有语义（含 pending 守卫）：❌ 未越（store.py 零 diff）
- 改动 B1 交付物（11 文件）：❌ 未越（app/+tests/ 零 diff · 图谱两件为叠加回写且 B1 行未动）

### 遗留风险 / 偏差

1. **本地环境变更留痕**：为让全量 pytest 真绿，经本机 PG superuser 执行 `ALTER ROLE ops CREATEDB`（修 `test_import_from_supabase.py` scratch 建库权限 · 该 3 errors 在 B1 交付时为存量环境问题并已同样声明）。此为**本机环境修复、非仓内改动**；CI 无 postgres service 时该文件整文件 skip（conftest F4 已注记）。
2. ruff 全仓 66 条存量（= clean tree 基线 · 零新增），全部位于非本 task 文件；本次触及文件 ruff 全绿。
3. decide 归属判定依赖 `run_owner`（事件表有帧才可判）；run 未落过事件帧的申请对所有人都不可见/不可决（E1 设计使然 · 错误日志可观测），多 maintainer 不能互批他人 run（task R5 已如实标注）。
4. db 全链用例依赖本机 PG（`DB_AVAILABLE` 门控）；CI 无库时 skip 留痕（conftest 会打出 skip 原因，非静默）。

**结论：可进 PR 环节**（不 push、不开 PR 已由本帽遵守 · 00 统筹后续）。
