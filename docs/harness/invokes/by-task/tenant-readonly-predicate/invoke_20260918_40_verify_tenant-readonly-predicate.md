# Invoke · 40 verify · tenant-readonly-predicate

> **hat**：40  
> **日期**：2026-09-18  
> **分支**：`task/tenant-readonly-predicate`（已核对 `git branch --show-current`）  
> **task**：`docs/tasks/active/task_tenant_readonly_predicate.md`  
> **上游**：30 PASS · `invoke_20260918_30_implement_tenant-readonly-predicate.md`  
> **禁区**：未扩 T/W/P；未改 SSE freeze / `chat/graph.py`；未 commit/push/PR；未 CLOSE / git mv done；未生产 B 种子；未改 web/ios

---

## 质量门（本帽真跑 · 退出码实录）

工作目录=`/Users/cyning/Desktop/Ops-desk/ops-desk-api`

| 命令 | 退出码 | 结果 |
|------|--------|------|
| `.venv/bin/ruff check app tests` | **1** | 既有 2 条：`tokenizer.py:11` UP035 · `tests/test_rag_chunker.py:7` I001；`git diff --stat` 对该二文件为空 · **非本波** |
| `.venv/bin/ruff check` 本波 app/tests 触及路径（tenant_context / auth / deps / lookups / local_fn / lg_rag router+nodes / rag retrieve+shadow_write+ingest / models / 两测文件 / qdrant index 脚本） | **0** | All checks passed |
| `.venv/bin/pytest tests/test_tenant_context.py tests/test_capability_lookups.py -q --tb=short` | **0** | **19 passed**, 1 warning in 0.32s |
| `.venv/bin/pytest tests -q --tb=short` | **1** | **680 passed, 2 failed, 1 skipped**, 7 warnings in 11.82s |
| `./scripts/graph-compile.sh` | **0** | 9 graphs · 132 nodes · 194 edges · check OK · mermaid normalize ok（既有 branches/triggers warning 不咬 exit） |
| `npx spec-wave verify --target . --task docs/tasks/active/task_tenant_readonly_predicate.md --allow-no-review --allow-invoke-gap` | **0** | VERIFY: PASS（闸均 approved） |
| `npx spec-wave task lint --file docs/tasks/active/task_tenant_readonly_predicate.md` | **0** | LINT: PASS |
| `npx spec-wave task lint-wiki-delta --target .` | **0** | LINT-WIKI-DELTA: PASS（scanned=116 · issues=0） |
| `git diff --stat -- app/ops/chat/graph.py` | **0** | 零 diff（bytes=0） |
| `curl --noproxy '*' http://127.0.0.1:8001/api/ops/auth/me` | **7** | 连接失败 · **8001 未听**（`lsof` 无 LISTEN） |

全量 pytest 失败摘录（**判定与本波无关 · 40 未改码**）：

- `tests/test_chat_ws.py::test_ws_message_streams_events`：旧 chat WS 期望 `thinking/answer/done`，实得 `error`；日志 `relation "ops_knowledge_chunks" does not exist` + event loop closed
- `tests/test_chat_ws.py::test_ws_second_message_while_active_rejected`：同上 PG 表缺失导致 RAG hydrate 失败

非范围：旧 chat WS / SSE freeze / `chat/graph.py`。本波 retrieve 仅在 ContextVar 有租户时过滤；WS 路径未设租户则不过滤。40 不扩修。

---

## 验收标准逐条对照

| # | 验收点 | 结论 | 证据 |
|---|--------|------|------|
| 闸 | `HG-STAGE-T-DATA` · `HG-CONTRACT-FREEZE` · `HG-AUDIT-R1` · `HG-GRAPH-MODULES` 均为 approved | ✅ | task 表 + verify 闸扫描全 approved |
| T0 | Issue/PR `tenant_id` + Qdrant/PG tenant filter 路径；既有行回填 A | ✅ | `models.py` 三表列；迁移 `20260918_tenant_readonly` `ADD COLUMN IF NOT EXISTS` + DEFAULT A；`shadow_write.filter_payload` / ingest metadata；`ensure_payload_indexes.py` |
| T1 | 请求上下文可测注入；不再仅全局 pilot | ✅ | `tenant_context.py` F1=C；`test_header_absent_uses_session` · `test_header_must_match_session` · `test_contextvar_roundtrip`；auth `POST /tenant` · `/me` 回 `tenant_id` |
| T2 | 跨租户 issue/PR 负样本（对外 404 语义） | ✅ | `test_lookup_cross_tenant_misses`（本波 19 条内已跑，未 skip）：A 查 B `#900001` → `ok=False` + `issue_not_found`（与未命中同形，不泄漏）；SQL `tenant_id == tenant` |
| T3 | 跨租户 RAG 负样本 / metadata filter | ✅ | `test_rag_filter_cross_tenant_negative`：A 不见 B chunk；无 `tenant_id` 存量视为 A |
| T4 | 至少 1 条 A→B 自动化断言 | ✅ | 同上 lookup `#900001` A→B |
| ruff / pytest 本波 | 触及路径绿；本波 + lookup 回归绿 | ✅ | 触及 ruff 0；本波 pytest **19 passed** |
| graph-compile | 绿（若改图谱） | ✅ | exit 0 |
| chat 零 diff / 无新一级模块 | `chat/graph.py` 零 diff | ✅ | bytes=0；`01_modules.md` 仅 auth/capability/lg_rag/rag 备注 + 签收行 |
| task lint | PASS | ✅ | LINT: PASS |

**勾选数：验收条全 ✅**（相对 30：无 40→30 小修）。

---

## failure_paths 抽查

| 路径 | 姿态 | 抽查 |
|------|------|------|
| 闸 pending 即 30 | 拒开工 | ✅ 本窗闸均为 approved；verify PASS |
| 缺 `tenant_id` 调 tenant_scoped | `tenant_scope_missing` · 拒 | ✅ `test_lookup_tenant_scoped_missing_ctx_blocked`（本波 19 内） |
| 头与 session 不一致 | 403 | ✅ 单测 `ValueError tenant_header_mismatch`；router `_resolve_request_tenant` mismatch→403（HTTP 40 未复测：8001 未听） |
| 跨租户 lookup/RAG | 拒或空 · 不泄漏 | ✅ lookup `issue_not_found`；RAG 过滤掉 B metadata |
| 误改 SSE event_type | 审查拒收 | ✅ `chat/graph.py` 零 diff |
| 无第二租户 fixture 却宣称验收 | 40 拒收 | ✅ Fixture `TENANT_B` + issue `900001` 自动化断言已跑绿 |

---

## 本机 API / 给 web 00 联调限制

| 项 | 值 |
|----|-----|
| 应对准 | **本仓分支** `task/tenant-readonly-predicate` · base URL **`http://127.0.0.1:8001`** |
| 40 实测 | **8001 未听**（curl 7 · `lsof` 无 LISTEN）· **未** 另起 uvicorn（维护者令：勿串口） |
| Docker `:8000` | 本机 Docker 在听；无 cookie 的 `/api/ops/auth/me` 经 noproxy 得 **401** · **禁止**当作本波代码 |
| 头 | `X-Ops-Tenant-Id` 须与 session 一致，否则 403 |
| 切换 | `POST /api/ops/auth/tenant` 写 session 后再带头 |

---

## 残留风险

1. 全量 pytest 2 fail（旧 chat WS + 缺 `ops_knowledge_chunks`）· 与本波无关 · 合入前若 CI 跑全量可能红（视 CI DB 是否有该表）。
2. `ruff check app tests` 全量 exit 1 · 既有 2 条 · CI `pytest.yml` 中 Ruff 步骤仍注释。
3. alembic 迁移若单独 ruff 会 UP035/UP007（alembic 模板 `typing.Union`）；不在 `app tests` 口径。
4. 生产 B 种子未做；同号跨租户唯一约束本波不改。
5. 8001 未听 → web 联调需维护者/00 自行拉起本分支 uvicorn，勿用 Docker `:8000`。

---

## 结论

**40 PASS** · 本波验收绿 · 全量 2 fail 记环境残留（非本波）· 交 00 等 **web 一起合并** · **未 commit / push / PR / CLOSE**
