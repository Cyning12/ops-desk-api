# Task：lc_evidence_chain · HTTP 薄包装（联调 web）

> **状态**：completed  
> **类型**：功能实现（旁路 HTTP 入口）  
> **上游**：旁路链已合入 master（PR #33）· web 页已按 freeze mock 先行（`ops-desk-web` `task_web_lc_evidence_page`）  
> **关联契约**：`../ops-desk-web/docs/spec/SPEC-web-lc-evidence-page_v1.md` §3.2 · `freeze_id`: `lc-evidence-http-v1`  
> **审查对照**：`docs/harness/reviews/task_lc_evidence_http_audit_R1_20260816.md`（20-task-audit · **pass**）  
> **分支**：`task/lc-evidence-http`  
> **编排**：00 已签闸 → 本窗 30+40+50 → PR → CI 绿合入

---

## Harness 元信息

| 字段 | 值 |
|---|---|
| **task_slug** | `lc-evidence-http` |
| **git_branch** | `task/lc-evidence-http` |
| **test_strategy** | `required` |
| **test_strategy_note** | pytest：mock `ainvoke_evidence_answer`；断言 401 / 422 / 200 `{ok,data}` 且 evidence 含 `snippet`；500 `{ok:false,error}`；不连真 LLM/真库；`git diff` 不改 `app/ops/chat/graph.py` 拓扑 |
| **code_quality_bar** | `L2_backend` |
| **graph_change_layer** | `G-L1` |
| **graph_delta** | `docs/_tech_graph/l1/01_modules.md` |
| **graph_delta_note** | `lc_evidence_chain` 备注补 HTTP `POST /api/ops/lc-evidence/invoke`；跨模块契约消费方补 `api`/web；**不新增**一级模块；**不改** chat graph 边 |
| **wiki_delta** | `n/a` |
| **wiki_delta_note** | 不改 coding_wiki；契约真值在 web SPEC freeze + 本仓 G-L1 |
| **review_hat** | `20` |
| **required_invoke_hats** | `10,30` |
| **invoke_retention_profile** | `default` |
| **thinking_profile** | `shortest` |
| **experience_capture** | `recommended` |
| **freeze_id** | `lc-evidence-http-v1` |
| **orchestration** | 单 task · 薄包装已有 `ainvoke_evidence_answer` · 与 tracing task 分分支 |

### 人工闸

| human_gate_id | status | blocks_hats | 说明 |
|---|---|---|---|
| HG-TASK-DRAFT | approved | 22-R1 | 00 签 2026-08-16：范围锁定薄 HTTP + snippet 序列化；基线 `origin/master`（PR #33） |
| HG-AUDIT-R1 | approved | 30 | 审查 `docs/harness/reviews/task_lc_evidence_http_audit_R1_20260816.md` · 00 代签推进 |
| HG-GRAPH-MODULES | approved | 30 | 真值 `docs/_tech_graph/l1/01_modules.md`（D4-a 已签）；本 task 不新增一级模块 |

---

## 背景与目标

web 「LC Evidence」页提交 `POST /api/ops/lc-evidence/invoke`，本仓尚无该路由，前端按设计展示「旁路 API 不可用」（404）。  
旁路链（retrieve → grade → answer）已可库级 / CLI 调用。本 task 只补 **cookie 鉴权的同步 HTTP 薄包装**，供本机联调。

**完成态**：登录用户 POST 一条 query，得到 `{ok:true, data}`，其中 `data.evidence[].snippet` 为字符串；未登录 401；空 query 422。

---

## 范围

1. 新路由 `POST /api/ops/lc-evidence/invoke`  
   - 建议文件：`app/ops/lc_evidence_chain/router.py`（命中 `api` glob `app/ops/*/router.py`，仍属 `lc_evidence_chain` 包）  
   - 在 `app/ops/router.py` `include_router`  
2. 鉴权：`CurrentUser` / `get_current_user`（与 Chat 相同 session cookie）  
3. 请求体：`{ "query": string }` · `min_length=1` · `max_length=8000`（超限 → FastAPI 422）  
4. 调用现有 `ainvoke_evidence_answer(query)`；**不改** LCEL 拓扑、prompt、grade 业务  
5. 响应外壳（freeze `lc-evidence-http-v1`，变更须升 freeze_id）：  
   - 200：`{ "ok": true, "data": { query, evidence, answer, meta } }`  
   - `gate_action=refuse` 仍是 **200**（成功态），不是 4xx  
   - 500 / 上游 LLM 失败：HTTP 500 + `{ "ok": false, "error": { "code": "lc_evidence_failed", "message": "..." } }`（前端亦兼容 FastAPI `detail`）  
6. **`snippet` 必须进 JSON**：`EvidenceItem.snippet` 现为普通 `@property`，`model_dump()` 不含该键。须专用 response schema 或 `@computed_field`；禁止只 dump `ChainResult`  
7. `data.evidence[]` 字段至少：`id, source_type, source_id, chunk_index, anchor, title, url, snippet, grade`（`grade` 无则为 `null`）  
8. `data.meta` 至少：`hit_count, graded, grade_count, kept_count, gate_action, best_relevance`（缺省用合理默认，保证键存在）  
9. 单测：`tests/test_lc_evidence_http.py`（mock 链；override `get_current_user`；覆盖 401 / 422 / 200+snippet / 500 envelope）  
10. G-L1：`docs/_tech_graph/l1/01_modules.md` 备注 HTTP 入口；跨模块契约消费方补 web/api  
11. `./scripts/graph-compile.sh` 通过

可选（非挡）：`docs/_tech_graph/l1/10_flow_lc_evidence.graph.yaml`

---

## 非范围

- 修改 `app/ops/chat/graph.py` 拓扑或默认挂到 `POST /api/ops/chat/stream`  
- SSE / 流式 / 多轮 session  
- 前端页面（web 仓已交付 mock 页）  
- Langfuse / tracing（另 task `lc-evidence-langfuse-tracing`，分分支；本波不叠）  
- 改 grade/answer 提示词或检索内核  
- 匿名访问  
- 升 freeze_id（本波实现 v1，不改契约字段名）

---

## 依赖

| 项 | 说明 |
|---|---|
| 旁路包 | `app/ops/lc_evidence_chain/`（master · PR #33） |
| 鉴权 | `app/ops/deps.py` · `tests/test_chat_router.py` override 先例 |
| 契约 | `../ops-desk-web/docs/spec/SPEC-web-lc-evidence-page_v1.md` §3.2 · 00 签收注记（snippet / `{ok,data}` / 120s 前端超时） |
| 编码规范 | `docs/standards/CODING_BACKEND_L2_v1_zh.md` |
| 前端 client | `../ops-desk-web/src/api/lcEvidence.ts`（拆包与 snippet 校验） |

---

## 实施步骤（建议 · 30）

1. 定义请求/响应 Pydantic 模型（显式 `snippet`；`meta` 键齐全）。  
2. `router.py`：`POST /invoke` + `CurrentUser` + try/except 包装 500 envelope。  
3. `app/ops/router.py` 挂载 prefix `/lc-evidence`。  
4. pytest mock `ainvoke_evidence_answer`；无 cookie → 401；`query=""` → 422；200 断言 snippet。  
5. G-L1 一行 + `graph-compile.sh`。

---

## 验收标准

- [x] `POST /api/ops/lc-evidence/invoke` 存在；无 session cookie → **401**  
- [x] `query` 缺省 / 空串 / 长度 >8000 → **422**  
- [x] 已登录 + mock 链：HTTP **200**，body `ok===true`，`data.evidence` 每项 `typeof snippet === string`（非空命中时）；含 `anchor`  
- [x] `gate_action=refuse` 的 mock：仍 **200** + `ok===true`  
- [x] mock 链抛错：HTTP **500** 且 body 含 `ok===false` 与 `error.message`（或 FastAPI `detail`，前端两者都认）  
- [x] `git diff`（相对 `origin/master`）**不改** `app/ops/chat/graph.py` 拓扑  
- [x] `ruff check` 相关路径 + `pytest tests/test_lc_evidence_http.py` 绿  
- [x] `docs/_tech_graph/l1/01_modules.md` 已注明 HTTP 入口  
- [x] `./scripts/graph-compile.sh` exit 0  
- [x] （人工）本机 `make dev`：OpenAPI 含路径 + 无 cookie POST → 401（完整 LLM 1 问不挡机械关账）

---

## failure_paths

| 触发 | 行为 | 可重试 | 用户可见 |
|---|---|---|---|
| 未登录 / cookie 无效 | 401 | Y（登录） | 前端跳登录 |
| query 空或过长 | 422 | Y（改表单） | 前端表单提示 |
| 召回为空 / `gate_action=refuse` | 200 + `{ok:true,data}` | Y（换问法） | Meta 拒答 + answer 文案 |
| LLM / 检索抛错 | 500 + `{ok:false,error}` | Y | Alert + 重试 |
| 只 dump ChainResult 漏 snippet | 前端当失败 | N（验收打回） | 联调仍红 |
| 误挂 `/chat/stream` 或改 graph | 验收打回 | N | PR 拒绝 |

---

## 给执行帽必读

1. 本 task  
2. `../ops-desk-web/docs/spec/SPEC-web-lc-evidence-page_v1.md` §3.2 与「00 签收注记」  
3. `../ops-desk-web/src/api/lcEvidence.ts`（拆包、snippet 校验、404 文案）  
4. `app/ops/lc_evidence_chain/chain.py` · `types.py`（`snippet` 属性）  
5. `app/ops/deps.py` · `app/ops/router.py` · `tests/test_chat_router.py`  
6. `docs/standards/CODING_BACKEND_L2_v1_zh.md`

---

## 思考轮

### 思考轮控制

| 字段 | 值 |
|---|---|
| **actual_last_round** | R5 |
| **early_stop** | no |
| **residual_risks** | `snippet` 漏序列化会导致 web 200 仍失败；500 外壳须同时兼容 `error` 与 `detail`；勿与 tracing 分支叠提交 |

### R0
web 联调失败的根因是本仓缺少 `POST /api/ops/lc-evidence/invoke`。

### R1
范围=薄 HTTP + cookie 鉴权 + `{ok,data}` + snippet；非范围=改 graph / SSE / tracing / 前端。

### R2
采用 web freeze 方案 A：包装 `ainvoke_evidence_answer`；专用 response schema，不依赖 `model_dump()` 漏字段。

### R3
401 / 422 / refuse=200 / 500 envelope；禁挂 chat/stream。

### R4
pytest mock 四态 + graph diff 空 + ruff + graph-compile；人工 1 问联调。

### R5
闸未签前禁 30；签收后从本分支实现。

---

### 自检结论

> 10-task 起草自检 · **未**签发 HG-AUDIT-R1 · 30 开工前须闸表 approved。

- [x] 验收 / failure_paths / 非范围 / 依赖齐全
- [x] 思考轮 R0–R5 + 控制表已写
- [x] 10-task invoke 已落档
- [x] HG-TASK-DRAFT approved（00 签 2026-08-16）
- [x] HG-AUDIT-R1 approved（R1 pass · 00 代签）
- [x] HG-GRAPH-MODULES approved（D4-a 真值已存在）
- [x] 基线为 `origin/master`（含 PR #33），不叠 tracing 分支

### 自检结论（执行者）

> 30 实现 + 40 自检 · 2026-08-16 · 分支 `task/lc-evidence-http`

- [x] GATE_VERIFY + `harness verify` PASS（闸表均为 approved）
- [x] `POST /api/ops/lc-evidence/invoke`：cookie 鉴权；专用 schema 含 `snippet`
- [x] pytest `tests/test_lc_evidence_http.py` → **7 passed**
- [x] ruff 相关路径 PASS
- [x] `git diff origin/master -- app/ops/chat/graph.py` 为空
- [x] G-L1 `01_modules.md` 已补 HTTP 入口
- [x] `./scripts/graph-compile.sh` exit 0（未提交 generated_at 噪声）
- [x] 本机 OpenAPI 含 `/api/ops/lc-evidence/invoke`；无 cookie → 401
- [x] 30/40 invoke 已落盘

**40 结论：PASS**

### 自检结论（50）

> Harness 50 · 2026-08-16 · 00 统筹复检 · **PASS**

- [x] 验收表机械项已勾且与实现一致（抽读 `router.py` 序列化 snippet / 500 envelope）
- [x] `git diff origin/master -- app/ops/chat/graph.py` 为空
- [x] ruff PASS · pytest **7 passed**
- [x] freeze `lc-evidence-http-v1`：`{ok,data}` · refuse=200
- [x] invoke 50 已落档

**50 结论：PASS · 可 CLOSE / PR**

### 经验节（执行者）

- 旁路 HTTP 必须专用 response schema：`EvidenceItem.snippet` 是 `@property`，`ChainResult.model_dump()` 不含该键，web 拆包会失败。
- FastAPI 不要把返回类型写成 `dict | JSONResponse`（生成 response model 会报 Invalid args）；成功/失败统一 `JSONResponse`。
- 500 外壳必须是响应**顶层** `{ok:false,error}`，不要只放进 FastAPI `detail`（前端按 envelope 读 `error.message`）。
- Wiki: n/a（本波不改 coding_wiki；契约真值在 G-L1 + web freeze `lc-evidence-http-v1`）

### KPI

| 项 | 分 |
|---|---|
| Task_KPI% | 100 |

## CLOSE

| 项 | 内容 |
|---|---|
| 日期 | 2026-08-16 |
| 定稿 | `POST /api/ops/lc-evidence/invoke` 薄包装；freeze `lc-evidence-http-v1` |
| 归档 | `docs/tasks/done/task_lc_evidence_http.md` |

---

## 修订

| 日期 | 说明 |
|---|---|
| 2026-08-16 | 10-task 首稿：对齐 web freeze `lc-evidence-http-v1`；闸 pending |
| 2026-08-16 | 00 签收 HG-TASK-DRAFT / HG-AUDIT-R1；R1 留痕；派 30 |
| 2026-08-16 | 30+40+50 PASS；关账 |
