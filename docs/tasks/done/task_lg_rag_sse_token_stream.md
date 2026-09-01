# Task：lg-rag T5 · Token 流（终答 answer 多帧 delta）

> **状态**：completed（2026-08-31 CLOSE · PR [#105](https://github.com/Cyning12/ops-desk-api/pull/105) MERGED）  
> **类型**：传输 / SSE token 流  
> **上游**：[`05_lg_rag_transport_and_session_plan_v0.md`](../../spec/agent-infra/05_lg_rag_transport_and_session_plan_v0.md) §4.2 · §9 · §10.4 · [`WAVE_READINESS_lg_rag_sse_v0.md`](../../spec/agent-infra/WAVE_READINESS_lg_rag_sse_v0.md) §1  
> **前置**：T4 CLOSE · [`task_lg_rag_sse_resume`](./task_lg_rag_sse_resume.md) · [#103](https://github.com/Cyning12/ops-desk-api/pull/103)（+ 关账 [#104](https://github.com/Cyning12/ops-desk-api/pull/104)）  
> **分支**：`task/lg-rag-sse-token-stream`  
> **帽子**：00 起草闸；**10** 补全；**20** 审；**30+40** 实现。  
> **无关**：T6 删 `/chat/stream` · C0–C4 · 重开 T3/T4 · 改 `chat/graph.py` 拓扑 · 本仓改 Vue

---

## Harness 元信息

| 字段 | 值 |
|---|---|
| **task_slug** | `lg-rag-sse-token-stream` |
| **git_branch** | `task/lg-rag-sse-token-stream` |
| **implement_repo** | `ops-desk-api` |
| **test_strategy** | `required` |
| **test_strategy_note** | mock token chunk 流（假 astream 同吐 updates + token）；delta 帧序/拼接==终答断言；与 node.progress 并存 seq 单调不串台；replay 含 delta 帧；鉴权 401 / 未知 run_id 404 不变；不连真 LLM |
| **code_quality_bar** | `L2_backend` |
| **graph_change_layer** | `G-L1` |
| **graph_delta** | `docs/_tech_graph/l1/10_flow_lg_rag.graph.yaml` · `docs/_tech_graph/l1/01_modules.md` |
| **graph_delta_note** | `lg_rag` 备注 / flow：`answer` 多帧 delta；不新增一级模块；stream 符号变更 → 同步 G-L2 `by_path_lg_rag` / `by_symbol_lg_rag`（05 §9.3 T5 钩子） |
| **wiki_delta** | `n/a` |
| **wiki_delta_note** | 行为真值在 `05` §4.2/§10.4 + 本 task；不晋升 coding_wiki |
| **review_hat** | `20` |
| **required_invoke_hats** | `10,00,30` |
| **invoke_retention_profile** | `default` |
| **freeze_id** | `lg-rag-sse-v1`（扩展：`answer` 多帧 delta + 终帧 `final` 标记；首帧/增量协议钉死；回写 05 §4.2/§10.4） |
| **close_pr_policy** | `required` |
| **related_pr** | `#105` |
| **kpi_aggregator** | `CLOSE` |
| **orchestration** | T5 仅 answer delta；web 打字机另 task（00 出 Prompt）；可 api-only 先合；WAVE_READINESS §1 为 web 闸、不阻塞 api T5 |

### 人工闸

| human_gate_id | status | blocks_hats | 说明 |
|---|---|---|---|
| HG-TASK-DRAFT | approved | 22-R1 | 2026-08-31 · **00 代签 · 维护者 Prompt 授权** |
| HG-AUDIT-R1 | approved | 30 | 2026-08-31 · **00 代签 · 维护者 Prompt 授权** · 见 `docs/harness/reviews/task_lg_rag_sse_token_stream_audit_R1_20260831.md`（R1 pass · 内容零阻塞） |
| HG-GRAPH-MODULES | approved | — | 不新增一级模块 · **00 代签** · 仅 `lg_rag` 行/flow 备注；stream 符号变更同步 G-L2 indexes |

---

## 00 定夺（草案 · 人可后签）

| 项 | 钉死 |
|---|---|
| **slug** | **`lg-rag-sse-token-stream`** |
| **SoT** | 会话 SoT 仍 T3 **`thread_id`**；续看 SoT 仍 T4 **`run_id` + `seq`/`cursor`**；本波 **不改** |
| **协议（首帧/增量）** | `event_type` **仍 `answer`**，**不新增** event_type：① delta 帧 payload `{"delta": "<chunk>"}`（多帧 · 按 `seq` 有序拼接）② 终帧 payload `{"content": "<full>", "final": true}`（整段 · **T2 兼容**）。客户端规则：**见 `delta` 追加；见 `content` 全量替换；`done` 后停止追加**；禁止把 `content` 帧 append 到 delta 结果（05 §10.4 常见坑） |
| **覆盖** | supervisor **`aggregator` 必做** delta；router `direct_answer` 若同一 provider 流式可得则 **同协议**，否则保留整段并在自检写明降级理由；basic 无独立终答 LLM → 保持现行为（占位空 answer 帧不变） |
| **机制** | 不钉死实现选型：建议 `astream(stream_mode=["updates","messages"])` 或 provider 流式桥接；token 归属 **仅 aggregator / direct_answer 的 LLM 调用**（其他节点 LLM token **不**进 SSE）。**禁止** import `app.ops.session` / `app.ops.chat`；**禁止**新依赖边 |
| **落盘 / replay** | delta 帧与终帧 **同样落盘** `ops_lg_rag_run_events`；`POST /lg-rag/replay` 形状不变（逐帧重放含 delta） |
| **并存不串台** | 全部帧共享单调 `seq`（单 emit 循环保证）；delta 帧不与 `node.progress`/`subtask.progress` 重排 |
| **freeze** | 沿用 **`lg-rag-sse-v1`**（扩展 `answer` 多帧 + `final` 标记；非 silent 扩）；契约写回 05 §4.2 `answer` 行 + §10.4「api 提供」列；若 20 坚持拆新 freeze id → 退回 00 改钉 |
| **合入** | **可 api-only 先合**；与 web T3/T4 **不互堵**。已 MERGED：[#105](https://github.com/Cyning12/ops-desk-api/pull/105)（2026-08-31）。web 打字机另 task（00 已出 Prompt `PROMPT_web_00_lg_rag_t5_typewriter`，本仓不改 Vue） |
| **模块** | 不新增一级模块；`01_modules.md` 只改 `lg_rag` 备注 |

---

## 范围

1. **aggregator 终答 token → SSE delta 帧**：协议见 00 定夺；token 仅归属终答 LLM 调用  
2. **T2 整段兼容**：终帧 `{content, final:true}` 保留；旧客户端仅看 `content` 行为不变  
3. **落盘 / replay**：delta 帧入 `ops_lg_rag_run_events`；replay 逐帧重放  
4. **文档 / 图谱**：05 §4.2 `answer` 行 + §10.4 回写实现句；G-L1 `lg_rag` 备注 / flow；stream 符号变更 → G-L2 indexes（05 §9.3 T5 钩子）  
5. api pytest（mock 流 / 纯函数优先）+ ruff + `./scripts/graph-compile.sh`

## 非范围

- **T6** 删 `/chat/stream` 或 chat 下线窗口 · **C0–C4** Host 沟通轨  
- **重开 T3/T4**（thread 表 / cursor / replay 语义本身不改；仅 replay 重放内容自然含 delta 帧）  
- 本仓改 Vue；web 打字机 UI（另开 web task）  
- 改 `app/ops/chat/graph.py` 拓扑（验收：该文件 **零 diff**）  
- 新增 SSE `event_type`（含 `answer.delta` 等新类型）；拆新 freeze id（除非 20 退回 00 改钉）  
- import `app.ops.session` / `app.ops.chat`；`lg_rag` → `chat`/`session` 新依赖边  
- 服务端 cancel / 中断图执行  
- `node.progress`/`subtask.progress` token 化（仅终答 `answer` delta）  
- intent / critic / rag 等非终答 LLM 调用的 token 上屏  
- 改变 `answer` 整段 32_000 截断上限语义（终帧沿用）

---

## 验收标准

- [x] aggregator LLM token chunk → 多帧 `answer` `{"delta": ...}`；按 `seq` 有序；**拼接 == 终帧 `content`**（mock 断言）  
- [x] router `direct_answer`：同一 provider 流式可得 → 与 aggregator **同协议**（delta + final 帧）；否则保留整段 `answer`，并在 30 自检写明降级理由（00 定夺「覆盖」行）  
- [x] 终帧 `answer` `{"content": ..., "final": true}` 保持 T2 兼容（仅看 `content` 的旧客户端行为不变；mock 断言帧外形）  
- [x] delta 帧与 `node.progress`/`subtask.progress` 并存；全程 `seq` 单调；不串台（帧序断言）  
- [x] delta/终帧落盘 `ops_lg_rag_run_events`；`POST /lg-rag/replay` 重放含 delta 帧、形状与 live 一致  
- [x] 未登录 401 · 未知/跨用户 `run_id` 404 · 非法 body 422 行为 **不变**  
- [x] token 流不可用时 **降级整段 `answer`**（T2 行为）+ 日志；failure_paths 覆盖  
- [x] **旧测 grep 影响面**：`tests/test_lg_rag_sse_stream.py` · `tests/test_lg_rag_sse_resume.py` · `tests/test_lg_rag_session_continuity.py` · `tests/test_session_continuity.py` 绿（可扩展 delta 断言）；`app/ops/chat/graph.py` **零 diff**  
- [x] `app/ops/lg_rag/**` **不** import `app.ops.session` / `app.ops.chat`（无新依赖边）  
- [x] 05 §4.2 `answer` 行 + §10.4 回写实现句；G-L1 备注/flow；G-L2 `by_path_lg_rag`/`by_symbol_lg_rag` 同步（05 §9.3 T5）  
- [x] `ruff check` 触及路径绿；相关 pytest 绿（含上列旧测）；`./scripts/graph-compile.sh` exit 0  
- [x] `npx --yes dsh-coding-kit@1.10.0 task lint-wiki-delta --target .` 通过

---

## failure_paths

| 触发 | 行为 | 可重试 | 用户可见 |
|---|---|---|---|
| provider 不支持流式 / token 桥异常 | **降级整段 `answer` 单帧**（T2 行为）+ 日志 | 是 | 无打字机但有终答 |
| delta 途中图异常 | 已发 delta 保留并尽量落盘；发 `error` 帧；**不补** final 帧 | 视异常 | `event_type=error` |
| 事件落盘失败 | 日志；**不**阻断已发出的 SSE（同 T4） | 是 | replay 可能缺部分帧 |
| 客户端混用 delta+content | 契约钉死：`content` 帧 **全量替换**；禁止 append | — | 文档约束（05 §10.4 常见坑） |
| 断连（live） | 服务端仍尽量跑完并落盘（T2/T4 语义不变） | 是（replay） | replay 补齐 delta |
| 未登录 / 未知 run_id / 非法 body | 401 / 404 / 422（不变） | — | 校验错误 |

---

## 给执行帽的必读列表

1. 本 task（含 **00 定夺**）  
2. `docs/spec/agent-infra/05_lg_rag_transport_and_session_plan_v0.md` §4.2 · §9 · §10.4  
3. `docs/spec/agent-infra/WAVE_READINESS_lg_rag_sse_v0.md` §1（web 闸 · api 不阻塞说明）  
4. 只读参考：`app/ops/lg_rag/sse_stream.py` · `sse_replay.py` · `event_store.py` · `multi/nodes.py`（`aggregator_node`）· `router.py`  
5. `docs/standards/CODING_BACKEND_L2_v1_zh.md`  
6. `docs/_tech_graph/l1/01_modules.md` · `10_flow_lg_rag.*` · `l2/README.md`

---

### 自检结论

> **10-task** · 2026-08-31 · 分支 `task/lg-rag-sse-token-stream` · 思考轮由 SPEC（`05` §4.2/§9/§10.4 + `WAVE_READINESS` §1）承载；本文件 **不**预置 R0–R5（lint W4 合法）。

- [x] slug=`lg-rag-sse-token-stream`；范围 **仅 T5 answer token delta**；非范围钉死 T6/C0–C4/重开 T3·T4/改 `chat/graph.py`/新增 event_type/新 freeze id/新依赖边/cancel/token 化 progress/非终答 LLM 上屏/32_000 截断语义
- [x] 00 定夺保留（未做实质改动）：SoT 不改 · `answer` 单 event_type（delta 多帧 + 终帧 `final` · T2 兼容）· aggregator 必做 / direct_answer 同协议或降级 · 无新依赖边 · 落盘/replay 含 delta · seq 单调不串台 · freeze 扩展 `lg-rag-sse-v1` · 可 api-only 先合 · 不新增一级模块
- [x] 验收含旧测 grep 影响面（`test_lg_rag_sse_stream` · `test_lg_rag_sse_resume` · `test_lg_rag_session_continuity` · `test_session_continuity` 绿 · `chat/graph.py` 零 diff）；补 direct_answer 同协议/降级验收钩
- [x] 验收 / failure_paths / 非范围 / 必读 / `wiki_delta` / invoke 留档字段齐全
- [x] `npx dsh-coding-kit@1.10.0 task lint --file docs/tasks/active/task_lg_rag_sse_token_stream.md` → **PASS**（exit 0 · W4）
- [x] `npx --yes dsh-coding-kit@1.10.0 task lint-wiki-delta --target .` → **PASS**
- [x] HG-AUDIT-R1 **仍 pending**（本帽不签发）· 可交 **20-task-audit**

### 自检结论（执行者 · 30+40 · 2026-08-31）

| 自检命令 | 退出码 | 结果 |
|---|---|---|
| `npx dsh-coding-kit@1.10.0 verify --target . --task docs/tasks/active/task_lg_rag_sse_token_stream.md` | 0 | VERIFY: PASS（三闸 approved） |
| `ruff check app/ops/lg_rag tests/test_lg_rag_sse_token_stream.py`（.venv） | 0 | All checks passed |
| `.venv/bin/pytest tests/test_lg_rag_sse_token_stream.py tests/test_lg_rag_sse_stream.py tests/test_lg_rag_sse_resume.py tests/test_lg_rag_session_continuity.py tests/test_session_continuity.py -q` | 0 | **46 passed**（新增 12 + 旧 34） |
| `./scripts/graph-compile.sh` | 0 | compile + check + normalize 全 OK（9 graphs） |
| `npx --yes dsh-coding-kit@1.10.0 task lint-wiki-delta --target .` | 0 | LINT-WIKI-DELTA: PASS |
| `git diff --stat -- app/ops/chat/graph.py` | 0 | **零 diff**（不在改动清单） |

00 关账复检（2026-08-31）：独立复跑 pytest 五文件 **46 passed** · graph-compile OK · `chat/graph.py` 零 diff · PR #105 CI 三绿后 squash MERGED。

---

## 关账（CLOSE）

| 项 | 值 |
|---|---|
| PR | [#105](https://github.com/Cyning12/ops-desk-api/pull/105) **MERGED** 2026-08-31 |
| 生产 | 无新 Alembic 迁移（复用 T4 `ops_lg_rag_run_events`）；deploy-api 随 master push 自动跑 |
| web | 打字机 Prompt 已落盘 `_prompts/PROMPT_web_00_lg_rag_t5_typewriter.md`；web T5 须 web-00 先跑 WAVE_READINESS §1 闸 |
| 归档 | 2026-08-31 · 00 关账 · 维护者 Prompt 授权 |

### KPI

Task_KPI%: 100 · D1 范围钉死仅 T5 answer delta · D2 闸齐（三代签落盘 + 20 R1 pass）· D3 过程档齐（invoke 10/00/30_40 + R1 审查 + web Prompt）· D4 图谱 G-L1/G-L2 已随 #105 · D5 关账补登 2026-08-31

- **direct_answer 实际处置**：**同协议达成，未降级**。router `direct_answer` 与 aggregator 同一 provider（`_ROUTER_PROVIDER` · SiliconFlow/Bailian 均实现 `complete_stream`），节点经 `complete_answer_streaming(..., node="direct_answer")` 发 delta + 终帧；mock 断言 `test_stream_router_direct_answer_same_protocol` 绿。降级路径由桥内异常兜底（failure_paths 行）而非协议降级。
- **实现机制**：provider 流式桥接（R1 非阻塞 1 选型落地）——`astream(stream_mode="messages")` 对自定义 provider 不产 token，故走 `BaseProvider.complete_stream` + contextvar token sink；sink 在图执行 task context 内 `emit`（seq 单调 + 落盘）后帧入 `asyncio.Queue`，emit 主循环与下一 update 竞速吐帧（打字机实时）；update 边界先吐净残留 delta 再映射 updates 帧。
- **R1 非阻塞 5 条处置**：① 选型=provider 桥接（上）② aggregator「必做」与降级合读——流式可得即必做，桥内降级整段 ③ delta 逐 chunk 落盘量随终答长度放大——接受（task 未要求聚合；chunk 粒度=provider 流原生）④ direct_answer 同协议无降级，理由已写 ⑤ 占位空 answer 帧无 `final` 标记——保持现行为（`test_stream_basic_placeholder_unchanged` 钉死）。
- **已知未测项**：真 LLM 联调（task 钉死不连真 LLM；留给 §11 T5 联调段）；断连中 sink 队列冲刷的生产路径（单测覆盖 mock 断流/异常降级，不覆盖 TCP 断连时序）。

---

## 修订记录

| 日期 | 说明 |
|---|---|
| 2026-08-31 | **00**：T4 CLOSE（#103/#104）后起草 T5；钉 slug=`lg-rag-sse-token-stream`；协议=delta 多帧 + 终帧 `final`（T2 兼容 · 不新增 event_type）；覆盖=aggregator 必做 / direct_answer 同协议或降级；freeze 扩展 `lg-rag-sse-v1` |
| 2026-08-31 | **10-task**：lint PASS（W4 · 思考轮 SPEC 承载）；补 `### 自检结论`；补 direct_answer 同协议/降级验收钩；00 定夺未做实质改动 |
| 2026-08-31 | **20** R1 **pass**（内容零阻塞；非阻塞风险 5 条已录审查文）· **00** 代签 `HG-AUDIT-R1` → approved；可派 30 |
| 2026-08-31 | **30+40**：T5 实现落地——`answer_stream.py` contextvar token sink 桥；sse_stream emit 循环挂 sink + answer delta/终帧 final；aggregator / direct_answer 同协议（未降级）；12 新测 + 46 全绿；ruff / verify / graph-compile / lint-wiki-delta 全 PASS；05 §4.2/§10.4 + G-L1/L2 回写。**不 CLOSE（留给 00）** |
| 2026-08-31 | **00 CLOSE**：PR [#105](https://github.com/Cyning12/ops-desk-api/pull/105) MERGED（CI 三绿）；无新 Alembic（复用 `ops_lg_rag_run_events`）；归档 done/ · Hub 补登 · CLOSE invoke 留档 |
