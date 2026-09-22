# Task：bugfix · 测试基线红清理（chat_ws×2 + capability proxy×1 + backfill flaky）

> **状态**：`done`（2026-09-22 · 五棒全通（bugfix 轨）· 40 PASS A1–A6 双态 · PR #169 CI 全绿合并 master（9a46f48）· CLOSE 归档）  
> **类型**：**bugfix**（双轨：可跳 SPEC · 各 40 invoke 观察项 ≈ mini-SPEC）  
> **依据**：`docs/harness/invokes/by-task/llm-layer-hardening/invoke_20260921_40_verify_llm_layer_hardening.md`（3 红 + master 同错复现）· `invoke_20260921_50_close_llm_layer_hardening.md`（「另开 fix task」指令）· `docs/harness/invokes/by-task/security-input-isolation/invoke_20260922_50_close_security_input_isolation.md`（3 红 + backfill flaky · fix 候选清单）· `docs/harness/invokes/by-task/memory-compliance-delete/invoke_20260922_40_verify_memory_compliance_delete.md`（3 红同款）· `docs/harness/invokes/by-task/tenant-readonly-predicate/invoke_20260918_40_verify_tenant-readonly-predicate.md`（PG 表缺失 hydrate 失败首记）· 本 task 10 帽复现 invoke：`docs/harness/invokes/by-task/test-baseline-reds/`  
> **分支**：`fix/test-baseline-reds`（base：`master`）

---

## Harness 元信息

| 字段 | 值 |
|------|-----|
| **task_slug** | `test-baseline-reds` |
| **git_branch** | `fix/test-baseline-reds` |
| **implement_repo** | `ops-desk-api` |
| **test_strategy** | `required` |
| **test_strategy_note** | 三条缺陷各有「修复前红 → 修复后绿」断言；flaky 用例全量连跑 3 次零复发 + 单测 20 连跑全绿；全量 `pytest tests` 回归零新增红；不连外网（修复方向即去除外部依赖） |
| **code_quality_bar** | `L2_backend` |
| **graph_change_layer** | `none` |
| **graph_delta** | `n/a` |
| **graph_delta_note** | bugfix · 只改 tests/（含 conftest）· app/ 与图谱零改动 · HG-GRAPH-MODULES 以 `none` 代录 |
| **wiki_delta** | `n/a` |
| **wiki_delta_note** | 依据=40 invoke 观察项（mini-SPEC）· 无 wiki 条目变更 |
| **review_hat** | `20` |
| **required_invoke_hats** | `10,20,30,40` |
| **invoke_retention_profile** | `default` |
| **experience_capture** | `recommended` |
| **kpi_aggregator** | `CLOSE` |
| **orchestration** | 10 落稿 → 20 R1 → 00 代录 → 30 → 40 → CLOSE |
| **freeze_id** | 无 |

### 人工闸

| human_gate_id | status | blocks_hats | 说明 |
|---------------|--------|-------------|------|
| HG-TASK-DRAFT | approved | 20-R1, 30 | 2026-09-22 · 00 验收 10-task 稿通过（维护者授权 00 代录 · 承队列授权令延续） |
| HG-AUDIT-R1 | approved | 30 | 2026-09-22 · 20-task-audit R1 PASS 零阻塞零退回（`docs/harness/reviews/task_test_baseline_reds_audit_R1_20260922.md` · 三根因亲跑复核一致 · CI 假绿核验属实）· 维护者授权 00 代录签收 |
| HG-GRAPH-MODULES | approved | 30 | 2026-09-22 00 代录 · `graph_change_layer=none`（bugfix · 只改 tests/ · 实扫无图谱改动） |
| HG-PILOT-OPSDESK-GLAYER | n/a | — | 非物理分层试点 task |

---

## 背景与目标

测试基线存在 3 条环境性红 + 1 条随机 flaky，自 2026-09-18 起被多个 task 的 40 核验反复记录为「基线环境性 · 非本波问题」并放行，`llm-layer-hardening` 50 与 `security-input-isolation` 50 均指令「另开 fix task 清理」。本 task 即该 fix task。

**10 帽真跑复现结果**（2026-09-22 · 本机 · 真 PG `opsdesk_test` · 分支 `fix/test-baseline-reds`）：

| 缺陷 | 复现 | 现象 |
|------|------|------|
| D1 `tests/test_chat_ws.py` ×2 | `pytest tests/test_chat_ws.py` → 2 failed / 4 passed | 实得事件流含 `error`/`tool_result`，与断言序列不符；伴随 portal-loop teardown 噪音（`RuntimeError: Event loop is closed`） |
| D2 `test_urllib_transport_honors_explicit_capability_proxy` | `pytest tests/test_capability_http_adapter.py -k proxy` → 1 failed / 1 passed | `Failed: DID NOT RAISE HttpCapabilityError` |
| D3 `test_reconcile_mismatch_marks_failed` | 单测连跑 20 次 → **8 failed / 12 passed**（≈40% 翻车率） | 断言 `embedded==2` 实得 3 · `status=="failed"` 实得 `pass` |

**一句话目标**：把三条缺陷各修复为**确定性绿**（环境隔离/打桩 + 竞态确定性化），禁止 skip/xfail 式掩盖；只改 `tests/`（含 `tests/conftest.py`），`app/` 零改动。

---

## 现状锚点（只读 · 30 必读 · 10 已扫）

### D1 · chat_ws ×2（`test_ws_message_streams_events` · `test_ws_second_message_while_active_rejected`）

四层叠加根因（10 已逐层实证，证据见 `docs/harness/invokes/by-task/test-baseline-reds/`）：

| 层 | 锚点 | 实证 |
|----|------|------|
| L1 断言过期（主根因） | `tests/test_chat_ws.py:160` 期望 `[run.start, thinking, thinking, answer, answer, done]` | 期望写于 2026-07-18（`ecdbc9e`）；2026-08-10 `b04715f`（R-3）把 general/overview 改线 `retrieve→grade→gate`（`app/ops/chat/graph.py:45-46`），现行图必多 `tool_result` 事件。补好环境后实得 index 2 = `tool_result` ≠ `thinking` —— **即使环境全修，断言仍不匹配现行拓扑** |
| L2 宿主代理 env 污染 | 宿主 `NO_PROXY/no_proxy=localhost,127.0.0.1,::1,[::1]` 含裸 IPv6 `::1` → httpx(trust_env=True) 建 Client 抛 `InvalidURL: Invalid port: ':1]'`（`app/ops/rag/embedder.py:92` httpx.post 触发） | 实证：宿主 env 下 `httpx.Client()` 即炸；`env -u *_proxy` 净化后恢复。CI runner 无此 env |
| L3 测试库 schema 漂移 | `ops_knowledge_chunks` 由 `alembic/versions/20260808_rag_chunks.py:35` 裸 SQL 建（**无 ORM 模型**）→ conftest `create_all`（`tests/conftest.py:155`）不含 → retrieve 混合召回 SQL（`app/ops/rag/retrieve.py:30-35`）炸 `UndefinedTableError` | 实证：`pg_tables` 查询无此表（26 表）；手工补表后该层消失。tenant-readonly-predicate 40（2026-09-18）已首记此现象 |
| L4 CI 假绿 | `.github/workflows/pytest.yml:26` `DATABASE_URL` 指向 localhost:5432 但 workflow **无 postgres service** → `DB_AVAILABLE=False` → DB 用例全 skip | 「CI 绿」实为 skip 绿，三缺陷从未在 CI 真跑过 |
| （噪音）portal-loop teardown | `tests/test_chat_ws.py:64-75` `_portal_engine` dispose | 失败后的跨 loop dispose 噪音（`Event loop is closed`），非根因；L1–L3 修复后须顺带确认噪音消失 |

### D2 · capability proxy（`test_urllib_transport_honors_explicit_capability_proxy`）

| 层 | 锚点 | 实证 |
|----|------|------|
| macOS 系统级 loopback 代理旁路 | `urllib.request.proxy_bypass("127.0.0.1")` 在 darwin 恒 `True`（系统「忽略代理设置」列表默认含 127.0.0.1/localhost）→ `ProxyHandler.proxy_open` 被短路，显式 `OPS_CAPABILITY_HTTP_PROXY`（`app/ops/capability/adapters/http_generic.py:306-313`）实际未用 → DID NOT RAISE | 实证：本机 probe 返回 `True`；Linux CI 无此旁路 → 绿。同文件 `test_urllib_transport_bypasses_ambient_http_proxy` 因断言语义相反而碰巧不受此影响 |

### D3 · backfill flaky（`test_reconcile_mismatch_marks_failed`）

| 层 | 锚点 | 实证 |
|----|------|------|
| keyset 水位 × 随机 uuid 竞态 | 回填扫描 `scripts/memory_embedding_backfill.py:215-222` `id > last_id ORDER BY id ASC`；测试并发注入行用 `uuid.uuid4()`（`tests/test_memory_embedding_backfill.py:559`） | 注入时机在首页 embed 期间（首页扫描已完成）；注入行 uuid **落在水位后**（≈50% 概率）则被下一页扫到并嵌入 → `embedded==3, remaining==0, status=pass` 断言翻车；落在水位前 → 预期路径。20 连跑实测 8 红 ≈40% |

---

## 钉死契约（30 不得静默改义）

| 项 | 钉死 |
|----|------|
| **禁止掩盖** | 不得用 `skip`/`skipif`/`xfail`/「本地跳过」消解三条缺陷；修复后三条在**有 PG 的本地环境确定性绿** |
| **改动边界** | 只改 `tests/`（含 `tests/conftest.py`）；`app/`、`scripts/`、`alembic/`、`.github/` **零 diff** |
| **D1 修复语义** | 断言序列对齐**现行图拓扑**（R-3 检索链 · 含 `tool_result`），不回退图拓扑；检索链外部依赖（embedder HTTP / grader LLM / 语料数据）在 WS 用例内**打桩确定化**（monkeypatch rag_nodes 侧 `get_llm_provider`/embedder/hybrid_recall 之一组，30 选最小面），使事件序列与外部世界无关 |
| **D1 环境隔离** | conftest 增加：① 代理 env 净化（对齐 `tests/conftest.py:23` `OPS_CHAT_TRACER` setdefault 先例；删除或改写 `*_proxy` 系列中的裸 IPv6 条目，须在 import app 之前生效）；② `_create_test_schema` 补 `ops_knowledge_chunks` 建表 DDL（与既有 ALTER 补丁同模式 · 幂等 `IF NOT EXISTS` · 逐字对齐 migration `20260808_rag_chunks` 的列定义，含 `CREATE EXTENSION IF NOT EXISTS vector`；sparse_embedding 等后续迁移列按需核对） |
| **D2 修复语义** | 测试内 monkeypatch `urllib.request.proxy_bypass`（返回 False）做 OS 隔离，使「显式代理必被使用」断言与宿主 OS 无关；**不改** `_capability_opener` 生产语义（空 dict 默认不走代理不变） |
| **D3 修复语义** | 并发注入行用**确定性小 id**（小于两个种子行 id，如 `UUID(int=1)` 或由种子行 `min(id)` 推导），保证恒落在 keyset 水位前 → `embedded==2 / remaining==1 / status=failed` 恒成立；不改 `run_backfill` 生产分页逻辑 |
| **顺带核验** | D1 修复后 `_portal_engine` teardown 噪音（Event loop is closed）应消失；若仍在，30 须定位并注记（不阻塞） |

---

## 范围

- [ ] **F1 · D1 修复**：WS 两例断言对齐现行图拓扑 + 检索链打桩确定化 + conftest 代理 env 净化 + `ops_knowledge_chunks` 建表补丁
- [ ] **F2 · D2 修复**：proxy 用例打桩 `proxy_bypass`（OS 隔离）
- [ ] **F3 · D3 修复**：flaky 用例并发注入行确定性小 id（确定性同步点）
- [ ] **F4 · 注记**：CI 无 PG → DB 用例 skip 的「假绿」缺口写入 `tests/README` 或 conftest docstring（**不修 CI**，另议）；schema 漂移补丁理由注释落码

### 非范围

- 改 CI workflow（加 postgres service 另 task 议）；重建测试库为 migration schema（仓级议题 · tz-fix 已注记同类）
- 改生产码任何语义（httpx trust_env / urllib opener / 图拓扑 / keyset 分页）
- chat WS 功能增强；其它 flaky 狩猎（本 task 只修已观察到的三条）
- 30 顺手重构测试文件

---

## failure_paths

| 触发条件 | 系统行为 | 可重试 | 用户可见 |
|----------|----------|--------|----------|
| HG-AUDIT-R1 待签即 30 | **拒开工** | 是 | 是 |
| 用 skip/xfail 掩盖任一缺陷 | 审查拒收（钉死契约） | 是 | 否 |
| 改 app//scripts//alembic//.github/ | `git diff` 检出 → 40 拒收（改动边界钉死） | 是 | 否 |
| D1 断言回退图拓扑或删 tool_result 期望 | 40 拒收（须对齐现行拓扑） | 是 | 否 |
| D3 修成「重试到绿」/sleep 等待 | 40 拒收（须确定性同步点） | 是 | 否 |
| conftest env 净化误伤 integration marker 用例 | `pytest -m integration` 路径注记 + 40 复核 | 是 | 否 |
| 修复后全量 pytest 新增红 | 回归失败 → 30 返工 | 是 | 否 |

---

## B1 · 旧测影响面（10 已实扫落盘）

| 面 | 实扫结果 |
|----|----------|
| TestClient/websocket 使用面 | `tests/test_chat_ws.py`（WS 6 例）· `tests/test_hitl.py` / `test_hitl_resume.py` / `test_hitl_resume_events.py`（TestClient HTTP）· `tests/dualproc_server.py`（工具）。conftest 变更须保这 5 处全绿 |
| 代理 env 使用面 | `tests/test_capability_http_adapter.py`（2 proxy 例）· `tests/eval/test_capability_redlines.py`（引用 `OPS_CAPABILITY_HTTP_PROXY`）；env 净化对 marker=`integration` 真连用例的影响须 30 注记（CI 默认不跑 integration） |
| run_backfill 使用面 | 仅 `tests/test_memory_embedding_backfill.py`（15 例 · autouse `_clean` 全表清）；D3 只动 `test_reconcile_mismatch_marks_failed` 一例的注入 id，其余 14 例零 diff 期望 |
| conftest 共有面 | `_create_test_schema` 建表补丁影响全部 DB 用例（session scope）：新增表为空表，对既有断言零影响（无用例 SELECT 该表计数）；`opsdesk_test` 26 表现状已实核 |
| SSE 对照 | `tests/test_chat_router.py` 四例已改 410 断言（不经图），与 WS 用例无共享夹具路径，预期零影响 |

---

## 验收标准

- [ ] 人工闸：HG-AUDIT-R1 approved 后方可勾选下列码项
- [ ] **A1（D1 前红→后绿）**：修复前 `pytest tests/test_chat_ws.py` = 2 failed / 4 passed（10 已录基线）；修复后同环境 `pytest tests/test_chat_ws.py` = **6 passed**，且无 `Event loop is closed` teardown 噪音（或噪音已注记）
- [ ] **A2（D2 前红→后绿）**：修复前 `pytest tests/test_capability_http_adapter.py -k proxy` = 1 failed / 1 passed；修复后 = **2 passed**，且 monkeypatch 不打桩时不依赖宿主 OS 旁路列表语义
- [ ] **A3（D3 flaky 零复发）**：修复前单测 20 连跑 ≈40% 红（10 已录 8/20）；修复后 ① 单测 `test_reconcile_mismatch_marks_failed` **20 连跑全绿** ② 全量 `pytest tests` **连跑 3 次零复发**（该例三跑皆绿）
- [ ] **A4（双环境同绿）**：本地真 PG 环境三条确定性绿 + CI `pytest` workflow 不新增红（CI DB skip 现状已按 F4 注记；CI 绿不视为真跑的证据）
- [ ] **A5（全量回归）**：`pytest tests` 全量绿（零 failed；修复前基线 3 红 + flaky 皆消），B1 表内 5 处 TestClient 文件 + memory 全量（≥99 条基线）+ lg_rag/session 回归全绿
- [ ] **A6（改动边界）**：`git diff --stat` 仅 `tests/` 路径；`app/` `scripts/` `alembic/` `.github/` 零 diff
- [ ] `ruff check tests` 触及路径绿
- [ ] `npx spec-wave task lint --file docs/tasks/active/task_test_baseline_reds.md` PASS

---

## 依赖

| 依赖 | 说明 |
|------|------|
| 依据（mini-SPEC） | 40 观察项四份（见文首依据行）+ 本 task 10 帽复现 invoke `docs/harness/invokes/by-task/test-baseline-reds/` |
| 被修测试 | `tests/test_chat_ws.py` · `tests/test_capability_http_adapter.py` · `tests/test_memory_embedding_backfill.py` · `tests/conftest.py` |
| 对照真值（只读） | `app/ops/chat/graph.py`（现行拓扑）· `app/ops/rag/retrieve.py` / `embedder.py` · `app/ops/capability/adapters/http_generic.py` · `scripts/memory_embedding_backfill.py` · `alembic/versions/20260808_rag_chunks.py`（DDL 对齐源） |
| 编码规范 | `docs/standards/CODING_BACKEND_L2_v1_zh.md` |

---

## 给执行帽的必读列表

1. `AGENTS.md` · 2. 本 task（钉死契约 + B1）· 3. `docs/harness/invokes/by-task/test-baseline-reds/` 十份复现/定位 invoke · 4. `docs/standards/CODING_BACKEND_L2_v1_zh.md` · 5. `tests/conftest.py` 全文 · 6. `app/ops/chat/graph.py` + `app/ops/chat/rag_nodes.py`（现行事件语义）· 7. `FRAGMENT_30_gate_verify_v1_zh.md`

---

## 思考轮控制

| 轮 | 结论 | early_stop | reason（early_stop） | residual_risks |
|----|------|------------|----------------------|----------------|
| R0 | bugfix · 三条缺陷已由 40 观察项记录、10 帽全部真跑复现并定位到层 | no | — | none |
| R1 | 范围=三缺陷修复+注记；改动边界钉死 tests/ | no | — | 无 |
| R2 | 修复方向逐条裁定（打桩/环境隔离/确定性 id）；禁止掩盖条款钉死 | no | — | D1 打桩面选择（rag_nodes provider vs hybrid_recall）留 30 最小面裁量 |
| R3 | D1 四层根因交叉验证（补表+净化 env 后实得 tool_result → 断言过期坐实为主根因） | yes | 三层缺陷根因全部实证闭环 · 修复方向唯一且无方案分叉值得展开 | CI 假绿缺口只注记不修（非范围 · 另 task 议） |
| R4 | （未开） | — | early_stop at R3 | — |
| R5 | （未开） | — | early_stop at R3 | — |

**actual_last_round**：R3 · **early_stop**：yes · **residual_risks**：见 R3

### R0 · 问题框定
三条缺陷在 llm-layer-hardening 40/50、security-input-isolation 50、memory-compliance-delete 40、tenant-readonly-predicate 40 五处 invoke 有记录，且有「另开 fix task」明确指令；无需重开需求分析。

### R1 · 范围钉死
只修已观察三条；改动边界 tests/；CI 改造、测试库重建、生产语义变更全部非范围。

### R2 · 方案裁定
D1=断言对齐现行拓扑+检索链打桩+conftest 双补丁（env 净化/建表）；D2=proxy_bypass 打桩；D3=确定性小 id。每条都排除了「skip 掩盖」与「改生产码」两条岔路。

### R3 · 交叉验证
对 D1 做反向实证：手工补 `ops_knowledge_chunks` + 净化代理 env 后重跑，实得事件流 index 2 = `tool_result` —— 证明环境层全修后断言仍不匹配，断言过期（R-3 改线遗留）为不可省略的主根因，防止 30 只修环境层而收不了尾。验证后已 drop 表恢复红基线。

### R4 ·（未开 · early_stop）

本轮不展开；三条根因已实证闭环。

### R5 ·（未开 · early_stop）

本轮不展开。

---

### 自检结论（执行者）

> **40 核验：PASS（2026-09-22 · 零阻塞）**。A1–A6 全过：全量 pytest 双态（宿主 env 现状 / 净 env delenv 场景）+ 三连跑均 1367 passed / 0 failed；origin/master worktree 对照亲跑前红（D1 2f/4p · D2 1f/1p · D3 3f/10）与「httpx InvalidURL 假绿」（净 env 下 7 红逐字复现）均成立；flaky 20 连跑零复发；D1 变异复做真挂已还原；diff 仅 tests/ · ruff 零新增 · graph-compile 绿。证据：`docs/harness/invokes/by-task/test-baseline-reds/invoke_20260922_40_verify.md`。观察项 1 条（capability 文件单文件独立跑 4 红为 master 同源预存顺序依赖 · 非本 task 范围 · 另议）。

---

## 修订

| 日期 | 说明 |
|------|------|
| 2026-09-22 | 10-task 落稿（bugfix 双轨 · 三缺陷真跑复现+读码定位 · early_stop at R3）· HG-TASK-DRAFT / HG-AUDIT-R1 待签 → 30 拒开工 |
| 2026-09-22 | 40 核验 PASS（A1–A6 全过 · 双态全量 1367/0 ×3 · master 对照前红+假绿复现 · 变异复做）· 自检结论回填 |
| 2026-09-22 | **50+CLOSE**：PR [#169](https://github.com/Cyning12/ops-desk-api/pull/169) CI 全绿 merge master（`9a46f48`）· 归档 done/ · 全量 pytest 1367/0 failed 双态三连跑 · 遗留：CI 假绿（无 PG 服务 DB 用例全 skip）另 task 议 · capability 单文件独立跑 4 红（顺序依赖×宿主 env）另 task 议 · 测试库 schema 漂移根治属仓级议题 |
