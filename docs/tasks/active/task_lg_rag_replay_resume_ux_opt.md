# task（草案 · 人工闸 pending · 拒开工）：lg-rag replay 恢复段在写窗口语义化 + 审批后 SSE 续流（replay follow live-tail）

> **状态**：draft（草案 · HG-TASK-DRAFT / HG-AUDIT-R1 / HG-GRAPH-MODULES 均 **pending** · 30 拒开工）
> **由来**：维护者原话锚（web 仓 00 转发 · m00321）：「给api仓起草一份replay的优化task，同时思考审批通过后也继续为SSE的方式通信的方案，审批后等待中间过长」——两大诉求：①replay 优化；②**审批通过后继续以 SSE 流式通信**的方案（替代轮询 replay），消解「审批后等待中间过长」。上游实证钉案：ops-desk-web invoke `../ops-desk-web/docs/harness/invokes/by-task/web-hitl-approval-overlay-ux/invoke_20261028_30_implement.md`（2026-10-28 · PG 实证 + 根因链）。
> **分支**：task/lg-rag-replay-resume-ux-opt（维护者签收后新建，本窗不建）。
> **锚点核真**：本仓 base master `0a5d610`，全部行号 10 亲读逐字复核（禁信转述）。

## Harness 元信息

| 字段 | 值 |
|------|-----|
| **task_slug** | `lg-rag-replay-resume-ux-opt` |
| **git_branch** | `task/lg-rag-replay-resume-ux-opt` |
| **implement_repo** | `ops-desk-api` |
| **test_strategy** | `required` |
| **test_strategy_note** | 谓词/409/follow 契约测试红测先行（修复前 RED → 修复后 GREEN 时序 git 可查）+ 全量对拍基线 + 40 live 对照复跑 HITL approve→resume 形态 |
| **code_quality_bar** | `L2_backend` |
| **graph_change_layer** | `G-L1`（改 `app/ops/lg_rag/event_store.py` 新谓词 + `app/ops/lg_rag/router.py` replay 端点行为扩展 · 图谱模块行为表述面 · 30 按实判回写） |
| **graph_delta** | 预期 `docs/_tech_graph/l1/01_modules.md` lg_rag / hitl 行备注回写（按实判 · 无模块增删） |
| **graph_delta_note** | 若 30 实证后确认零图谱表述面变化，改填 `none` 并注理由 |
| **wiki_delta** | `n/a` |
| **wiki_delta_note** | 无文档站/WikiTrack 变更（SSE/HTTP 契约面扩展） |
| **review_hat** | `20` |
| **required_invoke_hats** | `10,20,30,40` |
| **invoke_retention_profile** | `default` |
| **experience_capture** | `required` |
| **kpi_aggregator** | `n/a` |
| **orchestration** | 10 落稿 → 20 R1 → 维护者签 → 30（红测先行）→ 40（含 live 对照）→ PR+CI 绿 → CLOSE |
| **freeze_id** | `lg-rag-sse-v1`（**不**新 freeze · **零新 event_type** · SSE 帧 data 形状零变；replay HTTP 面两项演进——请求体增可选 `follow` 键 + 恢复段在写窗 409 语义化——承 `task_lg_rag_sse_resume`「扩展：帧内可选 cursor + replay HTTP」先例，非 silent 扩，回写 05 按实判） |
| **close_pr_policy** | `required` |

### 人工闸

| human_gate_id | status | blocks_hats | 说明 |
|---------------|--------|-------------|------|
| HG-TASK-DRAFT | approved | 20, 30 | 2026-10-28 · 00 代录（维护者长期授权 m00236「授权00签收后续文档」· 承 m00230 先例）· 初稿 F1–F4 + SSE 续流形态定夺（replay opt-in follow live-tail）· 20-R1 审查后 HG-AUDIT-R1 再走签 |
| HG-AUDIT-R1 | approved | 30 | 2026-10-28 · 00 代录（维护者长期授权 m00236「授权00签收后续文档」· 承 m00230 先例）· 20 R1 内容 PASS + NIT×3 已勘误闭合（审查文 docs/harness/reviews/task_lg_rag_replay_resume_ux_opt_audit_R1_20261028.md · 实证钉案 12/12 核真 · F2 follow live-tail 定夺成立 · 跨仓声明与 web 现状一致）· 30 解锁 |
| HG-GRAPH-MODULES | approved | 30 | 2026-10-28 · 00 代录（维护者授权 m00236）· G-L1 无模块增删（行为表述面 · 20 R1 核对认可）· 30 交付按实回写图谱增量 |

---

## 背景与目标

### 需求真值（维护者原话锚 m00321）

「给api仓起草一份replay的优化task，同时思考审批通过后也继续为SSE的方式通信的方案，审批后等待中间过长」——拆解为两诉求：**①replay 优化**；**②审批通过后继续以 SSE 流式通信**（替代轮询 replay 的 chase 形态），消解「审批后等待中间过长」的用户观感。

### 上游实证钉案（web 仓调查结论 · 2026-10-28 · 本地 PG `opsdesk` 只读实证）

- PG 实证 run `38cb1138…`（hitl_825e · 2026-10-28 07:28 批准）：`ops_lg_rag_run_events` **seq 1–19 连续无洞**（全库 max(seq)=count(*) 零反例）；恢复段完整落盘：`hitl.resumed`@10 → node/subtask.progress@11–16 → `answer{final:true}`@17 → critic@18 → `done{status:resumed, latency_ms:289607}`@19。第二数据点 run `1039c1a9…` 同构（恢复段 68s）。
- 前端 chase 预算 = 10 次递增退避（2s 起 ×1.5 封顶 8s）≈ **56s 墙钟** < 恢复段实测 68–289s → chase 必在恢复段写完前耗尽，落「恢复仍在进行，可稍后手动续看」。
- **web 仓前端防御已落地**（空 replay 200 零内容帧不产气泡 + resumeHint + 手动续看 · web task `web-hitl-approval-overlay-ux` D1/D8）；本 task 是**后端语义化与通信方案面**。

### 根因链（本仓亲读核真 · base `0a5d610`）

1. HITL 批准 → `POST /hitl/requests/{id}/resume` 请求内只做守卫 preflight（`app/ops/hitl/router.py:473-489` `_preflight_decided_resume`），随即 `asyncio.create_task` 投递后台执行（`router.py:580-584`）**秒回 200 accepted**（`router.py:587-615`，携 `replay.cursor` = 受理时刻 `last_seq` · `_best_effort_replay_cursor` `router.py:506-517`）。端点 docstring 自承：「同步执行实测 130–310s，超前端 30s 超时」（`router.py:534-537`）。
2. 恢复段后台异步跑 68–289s（实测），过程帧经 `ResumeEventSink`（`app/ops/hitl/resume.py:54-162`）**直写事件表**接同 run_id 续编号；期间无任何 live 推送通道（恢复路径**无 run_worker bus**，bus 仅 `/lg-rag/stream` 首段持有 · `app/ops/lg_rag/run_worker.py:71-80,93-165`）。
3. 恢复段在写窗口内调 replay：`load_events_after(refuse_in_flight=True)`（`app/ops/lg_rag/event_store.py:225-265`）的 409 闸看 `run_stream_closed`（`event_store.py:129-149`）——该谓词**刻意**把 `done{waiting_approval}` 挂起帧算作已收尾（挂起 replay 合法零 diff · F-OBS-2 裁定），故恢复段在写期首段 `done{waiting_approval}` 已存在 ⇒ **不拦 409，合法返回 200 零帧** ⇒ 用户观感「没数据返回/等待过长」（维护者实测「点击续看推进返回空」）。
4. 即 chase 有两次结构性失败：预算 56s < 恢复段 68–289s（时序面）；在写窗 replay 合法空 200 无语义区分（契约面）。

**目标**：(a) replay 在恢复段在写窗口**语义化**（409 + Retry-After · 或 30 实证后裁定的等价语义化形态），不再合法空 200；(b) 落地**审批通过后 SSE 续流**形态（定稿见 D2：replay 端点 opt-in `follow` live-tail），让「批准之后跑完的那段」以单条 SSE 长连接推帧，chase 轮询降级为兜底；(c) 对既有沉降后/挂起 replay 行为**零 diff**。

### 形态决策 D 表（R 轮思考后定稿）

| D | 议题 | 定稿 | 备选与驳回理由 |
|---|------|------|----------------|
| D1 | replay 恢复段在写窗语义化形态 | **409 Conflict + `Retry-After: 2`**（detail 区分恢复段语义，如 `Resume segment is still in flight; retry after it settles.`）；判定面 = 新增事件表真源谓词（建议名 `run_resume_in_progress`）：**∃ `hitl.resumed` 帧 seq > 最新 done/error 收尾帧 seq**（且未过 stale 阈 · FP-1）⇒ 恢复段在写。挂起零 diff：无 `hitl.resumed` 在其后、或其之后已有新收尾帧（含再挂起 `done{waiting_approval}`）⇒ 200 原路径 | 200 + in_progress 标记帧：违反 freeze 零新 event_type 约束且把语义藏进载荷，客户端仍需改解析；409+Retry-After 承 F-OBS-2 已建语义（`router.py:401-409`），web 已有退避处理 |
| D2 | 审批后 SSE 续流形态 | **replay 端点 opt-in `follow` 模式（live-tail）**：`ReplayRequest` 增可选 `follow: bool = false`；follow=true 时先推 `seq > after_seq` 已落盘帧，随后**挂起循环**（DB 轮询事件表 · 间隔 ≥1s env 可调）按 seq 序推新帧，直至见到 `seq > after_seq` 的新收尾帧（done/error）推出后收尾；期间发 SSE keepalive comment（复用 `sse_stream._KEEPALIVE_FRAME` 口径 · comment 不进 data · 承 idle-keepalive freeze 声明）；总时长上限（env · 默认建议 ≥600s 覆盖 289s 实测）到点未收尾 → 流自然结束（**禁伪造帧**），客户端凭末帧 cursor 再 follow/轮询兜底。follow=true 时在飞/在写窗**不再 409**（follow 语义即等待）；follow=false 全行为零 diff | **B1 resume 端点升级 SSE**（驳回）：①只覆盖 manual resume 一条路径——`decide(resume_mode=immediate)`/env auto 自动恢复由 `auto_resume.schedule_auto_resume` 后台触发（`router.py:243-249`），**无 HTTP 连接可升级**；②resume 200 JSON（`resume`/`replay` 块 · `router.py:587-615`）是既有契约，改 SSE = breaking 或须内容协商双形态，复杂度与回归面俱大。**B3 新独立端点**（驳回）：契约面更大且与 replay 功能重叠，opt-in 字段是最小演进。**bus 直推**（驳回）：恢复段 `ResumeEventSink` 直写事件表无 bus，引入进程内 bus 到恢复路径须新做 registry 接线且**多副本不成立**（事件表是唯一跨进程真源 · 承 `task_multi_replica_dualproc` 口径：恢复可在另一副本执行）；DB 轮询 tail 以事件表为真源，多副本天然安全 |
| D3 | 恢复段时长本身优化（68–289s 实测） | **入非范围，另立 task**：时长 = 图重跑被批准步+下游的 LLM 执行时间，优化面（模型/prompt/并行/剪枝）是独立课题；本 task 消「等待不可见/语义不明」，不消「等待本身」 | 并入本 task（驳回）：面过大且与契约面无耦合，违单一职责 |

---

## 范围

- **F1 · 恢复段在写窗谓词 + replay 409 语义化**：`app/ops/lg_rag/event_store.py` 新增只读谓词（建议 `run_resume_in_progress` · D1 判定面 · 含 stale 阈防 FP-1 永久 409）；`load_events_after` 或 replay 端点接线（30 实证裁定接线层 · 既有 `refuse_in_flight` 闸语义零 diff）；`app/ops/lg_rag/router.py` replay 端点命中时 409 + `Retry-After` + 可区分 detail。挂起/沉降/首段在飞三态既有行为零 diff。
- **F2 · replay `follow` live-tail（SSE 续流）**：`ReplayRequest` 增可选 `follow`（缺省 false 字面零 diff）；follow=true 走 D2 定稿形态（推存量 → 挂起轮询推增量 → 新收尾帧后收尾 · keepalive comment · 总时长上限 env）；帧序列化复用 `format_sse_event`（`sse_replay.py:71-83`）与既有 `event_gen` 体例（`router.py:416-418`），SSE 帧 data 形状逐字节同构。
- **F3 · 契约测试（红测先行）**：谓词矩阵单测 + replay 409 状态码断言 + follow 帧序/收尾/上限/断连断言（验收 TC1–TC4）；既有 replay/resume/run_worker 测试钉零新增红。
- **F4 · 留档与回执**：invoke 留档（10/20/30/40）· 图谱备注按实回写 · 经验捕获；40 live 对照后回执 web 仓（chase→follow 适配面交接 · web 侧另立 task）。

## 非范围

- **app/ 代码本 task 起草阶段零改动**（本 PR 纯 docs）；30 改码须 HG-AUDIT-R1 approved 后另棒。
- **resume 端点响应契约**（200 JSON accepted + `replay.cursor` 块 · `router.py:587-615`）零 diff；decide/callback/OA 签名面零 diff；`auto_resume` 触发链零 diff。
- **首段 stream 主链**（`sse_stream.py` / `run_worker.py` / `sse_subscribe.py` bus fanout）零 diff——follow 走 DB 轮询**不复用 bus**（D2 驳回理由④）。
- **`run_is_terminal` / `run_stream_closed` 既有谓词语义不动**（新谓词新增、不改旧；F-OBS-2 409 闸与挂起合法 replay 口径存续）。
- **恢复段时长优化**（D3 · 另立 task）。
- **web 侧适配**（chase 器换 follow / resumeHint 文案 / 手动续看去留）——另立 web task，本 task 仅出契约与回执。
- **前端既有防御去留**（web 空 200 不产气泡已落 · web 仓自裁）。
- **多副本 live 推送**（bus 跨副本）：非本 task 面（follow 以事件表为真源天然多副本安全）。

---

## 失败路径

| 触发条件 | 系统行为 | 可重试 | 用户可见 |
|----------|----------|--------|----------|
| FP-1 恢复段崩溃在写窗口（ResumeError/异常 ⇒ sink 不关不落新收尾帧 · `app/ops/hitl/router.py:447-449` 注释口径） | 谓词恒真 → replay 409 永久化风险；缓解：stale 阈（`hitl.resumed` 或末帧 `created_at` 超 env 阈 ⇒ 视为已沉降回落 200 + error 日志），30 实证定默认阈值。注：orphan 补偿**不覆盖**此形态（`done{waiting_approval}` 已存在 ⇒ `list_open_runs` 排除 · `event_store.py:168-171`），照登不硬修 | 是（超时自动回落） | 极罕见崩溃形态下退化为既有「稍后手动续看」 |
| FP-2 follow 长连接被网关/代理 idle 掐断 | 挂起期发 SSE keepalive comment 防 idle 掐（承 `task_lg_rag_sse_idle_keepalive` freeze 声明：comment 不进 data JSON）；仍被掐 ⇒ 客户端以末帧 cursor 重发 follow（幂等 · seq>after_seq 去重客户端既有） | 是（cursor 重连） | 无（重连透明续推） |
| FP-3 follow 总时长上限到点仍未收尾（恢复段超 env 上限） | 流自然结束（**禁伪造 done/任何帧**）；客户端退避重连或 chase 轮询兜底存续（chase 不删） | 是 | 退化为既有 chase 形态 |
| FP-4 409 语义化误伤挂起 replay 主路径 | TC 钉死：纯挂起（`done{waiting_approval}` 为最新收尾帧、其后无 `hitl.resumed`）与再挂起（`hitl.resumed` 后已有新 `done{waiting_approval}`）两形态 ⇒ 200 零 diff；pytest 断言拦截 | 是（回退 diff） | 无 |
| FP-5 旧客户端不识 follow / 不识恢复段 409 语义 | follow 缺省 false 字面零 diff；409 视同既有在飞 409 按 Retry-After 退避即可（F-OBS-2 已建语义 · web 已具备） | 是 | 无 |
| FP-6 follow DB 轮询频率压力 | 间隔 ≥1s（env 可调）· 单连接单循环 · 恢复段量级分钟、单 run 单连接，负载面小；30 实测留痕 | 是 | 无 |
| FP-7 follow 期间 run 再挂起（`done{waiting_approval}` 新收尾帧） | 收尾帧即流结束条件——推出该帧后正常收尾；后续批准再 follow（语义自洽 · 帧自解释承 `ResumeEventSink` 设计） | 是 | 前端回到「等待授权」帧（既有渲染存续） |
| FP-8 HG-AUDIT-R1 pending 即 30 改码 | 执行 Agent **拒开工**（GATE_VERIFY · task 人工闸表为真值） | 是 | 须先 20 R1 + 维护者签 |

---

## 验收标准

- [ ] **TC1 谓词矩阵（红测先行）**：构造事件序列断言新谓词——(a) 挂起 `done{waiting_approval}`@N 后 `hitl.resumed`@N+1 且无更新收尾帧 ⇒ **真**；(b) 纯挂起（无 `hitl.resumed`）⇒ 假；(c) `hitl.resumed` 后有 `done{resumed}` / 新 `done{waiting_approval}` / `error` ⇒ 假；(d) stale 超阈 ⇒ 假。修复前 RED（谓词不存在 · AttributeError 同形签名，承 `test_lg_rag_sse_resume.py:214` 先例）→ 修复后 GREEN，时序 git 可查。
- [ ] **TC2 replay 409 语义化**：形态 (a) 下 `POST /lg-rag/replay`（follow 缺省）⇒ 409 + `Retry-After` 正整数 + detail 与首段在飞 409 可区分；**三态零 diff**：纯挂起 replay 200、沉降后 replay 200 流式帧序对 master 同输入零 diff、首段在飞（无收尾帧）仍原 409（`tests/test_lg_rag_sse_resume.py` / `tests/test_lg_rag_sse_run_worker.py` TC-B4 钉存续零新增红）。
- [ ] **旧测 grep 影响面**（承 `docs/tasks/done/task_lg_rag_sse_resume.md:102` 先例单列）：`tests/test_lg_rag_write_replay_guard.py` · `tests/test_hitl_auto_resume.py` · `tests/test_multi_replica_dualproc.py` 三钉零新增红（follow/409 语义化对 replay 守卫、auto 恢复链、多副本口径零破坏）；其余面由 TC5 全量对拍兜底。
- [ ] **TC3 follow 帧序契约（红测先行）**：follow=true 自 cursor 起 ⇒ 先推存量帧 → 挂起期 keepalive comment（不进 data）→ 恢复段新帧按 seq 序逐帧追加（含 `hitl.resumed` 首帧自解释）→ 见 `seq > after_seq` 新收尾帧推出后流结束；全部帧 data 形状与 `format_sse_event` 逐字节同构（freeze `lg-rag-sse-v1` 帧形状零 diff · 零新 event_type）。
- [ ] **TC4 follow 上限与断连**：总时长上限到点未收尾 ⇒ 流自然结束且**零伪造帧**（断言末帧非合成 done/error）；客户端断连 ⇒ 仅取消本 follow 循环（无副作用 · 无后台任务残留断言）；follow=true 在写窗/在飞**不返 409**（等待语义存续）。
- [ ] **TC5 反回归全量对拍**：`pytest tests` 全量对拍 master 基线零新增红（环境性红逐枚同名同因照登）；`ruff check app tests` 触及路径零新增；`./scripts/graph-compile.sh` EXIT=0（再生噪音文件一律还原）。
- [ ] **TC6 live 对照（40 帽）**：复跑 HITL approve→resume 同形态（对照 run `38cb1138` 钉案）：恢复段在写窗 replay(follow=false) 实测 409 + Retry-After；follow=true 单连接收全恢复段 `hitl.resumed → … → done{resumed, latency_ms}`（seq 连续无洞）；chase 预算耗尽观感消失；结果如实照登，回执 web 仓（含 web 侧适配交接口径）。

## 依赖

- 上游实证：ops-desk-web invoke `../ops-desk-web/docs/harness/invokes/by-task/web-hitl-approval-overlay-ux/invoke_20261028_30_implement.md`（PG run `38cb1138…` / `1039c1a9…` 钉案 · chase 预算 56s · 根因链四节）。
- 锚点亲读（base master `0a5d610` · 行号逐字复核）：`app/ops/hitl/router.py:473-489`（preflight）· `:506-517`（cursor）· `:520-615`（resume 端点异步受理）· `:425-464`（`_execute_decided_resume` 后台执行体）· `app/ops/hitl/resume.py:54-162`（ResumeEventSink 帧生成面 · :112-122 `hitl.resumed` · :124-137 close done）· `app/ops/lg_rag/router.py:372-428`（replay 端点）· `app/ops/lg_rag/event_store.py:129-149`（run_stream_closed）· `:225-265`（load_events_after/refuse_in_flight）· `app/ops/lg_rag/sse_replay.py:36-83`（resolve/format）· `app/ops/lg_rag/sse_subscribe.py:23-63` + `run_worker.py:71-165`（bus 对照面）。
- 无代码面阻塞依赖；web 侧不阻塞（前端防御已落 · 本 task 收口后 web 适配另立 task）。

## 给执行帽的必读列表

1. 本 task 全部锚点行（逐一亲读复核 · 禁信转述 · 行号漂移按实校正）：`app/ops/hitl/router.py:411-615` · `app/ops/hitl/resume.py:54-300` · `app/ops/lg_rag/router.py:372-428` · `app/ops/lg_rag/event_store.py:94-265` · `app/ops/lg_rag/sse_replay.py` 全文。
2. `app/ops/lg_rag/sse_stream.py`（`_KEEPALIVE_FRAME` / `_KEEPALIVE_INTERVAL_S` 口径 · follow keepalive 复用面）+ `app/ops/lg_rag/sse_subscribe.py:23-63` + `app/ops/lg_rag/run_worker.py:71-165`（D2 不复用 bus 的决策依据复核）。
3. `docs/standards/CODING_BACKEND_L2_v1_zh.md`（涉码 task）。
4. freeze/契约先例：`docs/tasks/done/task_lg_rag_sse_resume.md`（replay HTTP 面扩展先例）· `docs/tasks/done/task_hitl_resume_replay_contract.md`（409+Retry-After 语义化与红测先行体例）· `docs/tasks/done/task_lg_rag_sse_idle_keepalive.md`（keepalive comment freeze 声明）· `docs/tasks/done/task_hitl_resume_async.md`（异步受理由来）。
5. 既有测试钉：`tests/test_lg_rag_sse_resume.py`（replay 契约钉族）· `tests/test_lg_rag_sse_run_worker.py`（TC-B4/B5 在飞/orphan 钉）· `tests/test_hitl_resume_async.py` / `tests/test_hitl_resume_events.py`（恢复段帧钉）。

## 跨仓协调（ops-desk-web 影响面 + 冻结契约声明）

- **现消费者**：web chase 器（10 次 × 2s 起 ×1.5 封顶 8s ≈ 56s 墙钟预算）是 replay 既有唯一消费者；resumeHint / 手动续看 / 空 200 不产气泡防御已随 web task `web-hitl-approval-overlay-ux` 落地。
- **本 task 上线后的 web 影响**：①follow=false 面——仅恢复段在写窗从「合法空 200」变「409 + Retry-After」，web 已有在飞 409 退避处理（F-OBS-2 联调链已建）与空 200 防御，双路径兼容、**不强制 web 同步改**；②follow 面——web 侧以 follow 单连接替代 chase（chase 降级为兜底）+ resumeHint 文案调整，**另立 web task**（建议衔接本 task 40 live 对照回执后立项）。
- **冻结契约声明**：freeze `lg-rag-sse-v1` **帧形状冻结面零触达**——SSE 帧 data 形状（run_id/seq/ts_ms/agent_role/event_type/payload/cursor）零变、零新 event_type、keepalive 为 SSE comment 不进 data；演进仅限 replay HTTP 面两项（请求体可选 `follow` 键 + 恢复段在写窗 409 语义化），承 `task_lg_rag_sse_resume`「扩展：帧内可选 cursor + replay HTTP · 不 silent 扩 · 回写 05」先例，本 task 以本节为**契约演进声明**，30 按实判回写 05/图谱。

## 思考轮控制

| 轮 | 结论 | early_stop | reason（early_stop） | residual_risks |
|---|------|-----------|----------------------|----------------|
| R0 | 问题框定：维护者两诉求（replay 优化 + 审批后 SSE 续流）· 上游钉案 replay 五段链实证「时序窗口非丢数据」· 本仓锚点亲读核真（base `0a5d610`） | false | — | 无 |
| R1 | 证据收集：根因链四环钉死（异步受理秒回 200 / 恢复段 68–289s 直写事件表无 bus / run_stream_closed 刻意放行挂起 ⇒ 在写窗合法空 200 / chase 56s 必耗尽）；router.py:473-489 docstring 自承同步 130–310s | false | — | 恢复段时长分布仅两数据点（68s/289s） |
| R2 | 方案生成：D 表三决议——D1 409+Retry-After（新谓词事件表真源）/ D2 replay opt-in follow live-tail（驳回 resume 升级 SSE、新端点、bus 直推三备选 · 理由见 D 表）/ D3 时长优化入非范围 | false | — | follow 轮询间隔/时长上限默认值留 30 实证 |
| R3 | 反例与边界：挂起/再挂起 replay 零 diff 钉死（FP-4/TC2）· 崩溃在写窗 stale 阈防永久 409（FP-1 · orphan 补偿不覆盖照登）· 禁伪造帧（FP-3/TC4）· follow 多副本以事件表为真源（D2 ④）· freeze 帧形状冻结面零触达 | false | — | stale 阈默认值为设计参数（30 实证裁定） |
| R4 | 验收/可测性：TC1 谓词矩阵 + TC2 状态码 + TC3 follow 帧序 + TC4 上限/断连 + TC5 全量对拍 + TC6 live 对照 · 全可机断（TC6 为 live 实证照登口径承前例） | false | — | TC6 依赖 live 环境（承前例照登口径） |
| R5 | 收口：范围 F1–F4 / 非范围八条 / 失败路径八行 / 验收六条 / 依赖三条 / 必读五项 / 跨仓协调节齐备；三闸 pending 不代签；graph_change_layer=G-L1 预判 | true | 根因链四环全钉案 · 锚点全亲读核真 · 形态三备选显式驳回留痕 · 设计参数（阈值/间隔/上限）显式留 30 · 再轮无新增信息 | 恢复段崩溃永久 409 形态以 stale 阈缓解而非根治（FP-1 照登）· graph_delta 为预判 |

**actual_last_round**：R5（early_stop）

### R0 · 问题框定

维护者原话锚（m00321 · web 仓 00 转发）两大诉求：①replay 优化；②审批通过后继续以 SSE 流式通信替代轮询，消「审批后等待中间过长」。上游 web 仓 invoke（2026-10-28）已钉案：PG 实证 run `38cb1138` seq 1–19 连续无洞、恢复段完整落盘（`hitl.resumed`@10 → `done{resumed, latency_ms:289607}`@19），「没数据返回」= **时序窗口 + 契约语义缺口，非丢数据**；修复面归属后端（web 前端防御 D1 已落 · 禁改姐妹仓）。10 亲读本仓 base `0a5d610` 核真全部引用锚点。

### R1 · 证据收集

根因链四环（逐环亲读）：①resume 端点异步受理——`router.py:473-489` preflight 守卫 + `:580-584` create_task 投递 + `:587-615` 秒回 200 携 `replay.cursor`（受理时刻 `last_seq` · `:506-517`），docstring `:534-537` 自承「同步执行实测 130–310s，超前端 30s 超时」；②恢复段 `ResumeEventSink`（`resume.py:54-162`）直写事件表接同 run_id 续编号，**无 bus**（`run_worker.py:71-80` registry 仅 `/lg-rag/stream` 首段 `start_run_worker` 注册）⇒ 恢复过程无 live 推送通道；③`run_stream_closed`（`event_store.py:129-149`）刻意把 `done{waiting_approval}` 算收尾（挂起 replay 合法零 diff · F-OBS-2 裁定留痕）⇒ 恢复段在写窗 `refuse_in_flight` 闸不拦 ⇒ replay 合法 200 零帧；④web chase 预算 ≈56s < 恢复段实测 68–289s ⇒ 必耗尽。

### R2 · 方案生成

D1（在写窗语义化）：409+Retry-After 承 F-OBS-2 已建语义与 web 退避处理，优于 200+标记帧（违 freeze 零新 event_type · 语义藏载荷仍需客户端改解析）；判定面新谓词以**事件表为真源**（红线承 `run_is_terminal`：禁读进程内存态 · `_RESUME_IN_FLIGHT` 是 request_id 键的进程内单飞登记，多副本不成立，不能作判定面）。D2（SSE 续流）：replay opt-in `follow` live-tail——覆盖 manual resume 与 decide(auto) 两条恢复路径（resume 端点升级 SSE 只覆盖 manual · auto 无连接可升级 · `router.py:243-249`），opt-in 字段最小契约演进（resume 200 JSON 契约不动 · 驳回 B1/B3），DB 轮询 tail 以事件表为真源多副本天然安全（驳回 bus 直推：恢复路径无 bus 且跨副本不成立）。D3：恢复段时长优化（68–289s = 图重跑 LLM 执行时间）独立课题，入非范围。

### R3 · 反例与边界

- 挂起 replay 合法零 diff 是既有契约（F-OBS-2 裁定）——新谓词对纯挂起/再挂起两形态必须判假，FP-4/TC2 钉死。
- 恢复段崩溃在写窗（sink 不关 · `router.py:447-449` 注释口径）：谓词恒真 → 409 永久化；orphan 补偿不覆盖（`done{waiting_approval}` 已存在 ⇒ `list_open_runs` 排除 · `event_store.py:168-171`）——stale 阈缓解（超阈回落 200 + error 日志），照登不硬修（FP-1）。
- follow 流**禁伪造帧**：上限到点/断连均自然结束，末帧永远来自事件表（FP-3/TC4 断言）。
- freeze 帧形状冻结面零触达：follow 复用 `format_sse_event` 与既有 event_gen 序列化体例；keepalive 为 comment 不进 data（承 idle-keepalive freeze 声明）。

### R4 · 验收/可测性

TC1 谓词矩阵红测先行（RED 签名 = AttributeError 同形 · 承 `test_lg_rag_sse_resume.py:214` 先例）防恒绿假象；TC2 状态机断 + 三态零 diff；TC3 follow 帧序/收尾/帧形状逐字节同构断言；TC4 上限零伪造帧 + 断连零副作用；TC5 仓级对拍基线；TC6 live 对照复现 run `38cb1138` 形态回执 web。全可机断（TC6 承前例 live 照登口径）。

### R5 · 收口

范围 F1–F4、非范围八条、失败路径八行、验收六条、依赖三条、必读五项、跨仓协调节（web 影响面 + freeze 契约演进声明）齐备；HG-TASK-DRAFT / HG-AUDIT-R1 / HG-GRAPH-MODULES 均 pending 不代签（维护者亲签或授权 00 代录）；graph_change_layer=G-L1 预判（lg_rag/hitl 模块行为表述面 · 30 按实判回写）。lint 形态对齐历 task 实证教训（验收 `- [ ]` 清单 · 思考轮控制表五列 · 闸表四列纯 status）。设计参数（stale 阈 / 轮询间隔 / follow 上限默认值）显式留 30 实证裁定。裁定收口，early_stop at R5。

### 自检结论（10 帽）

结构对齐本仓已合并先例（`task_hitl_resume_replay_contract` · PR #248）；元信息块预填含 wiki_delta / freeze_id / required_invoke_hats；全部本仓锚点行号亲读核真（base `0a5d610`）：`router.py:473-489/:506-517/:534-537/:580-615` · `resume.py:54-162` · `event_store.py:129-149/:225-265` · `sse_replay.py:36-83` · `run_worker.py:71-80,93-165` · `sse_subscribe.py:23-63`。形态决策 D 表三决议留痕（含三备选驳回理由）；跨仓协调节明示 web 影响面与 freeze 冻结面声明。

---

## 修订记录

| 日期 | 说明 |
|------|------|
| 2026-10-28 | v0.2 · 20 R1 落盘 PASS（审查文 `docs/harness/reviews/task_lg_rag_replay_resume_ux_opt_audit_R1_20261028.md`）+ NIT×3 勘误闭合：NIT-1 FP-1 锚点勘正（`resume.py:447-449` → `app/ops/hitl/router.py:447-449`）· NIT-2 思考轮控制表 R1 行锚点勘正（→ `router.py:473-489`）· NIT-3 旧测 grep 影响面单列验收项（三钉 + TC5 兜底）· 闸态不动 |
| 2026-10-28 | v0 · 10 落稿：维护者原话锚 m00321（replay 优化 + 审批后 SSE 续流）· 上游钉案 web invoke 20261028_30（PG run 38cb1138 seq 1–19 无洞 · 恢复段 68/289s · chase 56s 必耗尽 · 在写窗合法空 200）· 本仓锚点亲读核真（base `0a5d610`）· D 表定稿（D1 409+Retry-After 新谓词 · D2 replay opt-in follow live-tail · D3 时长优化入非范围）· F1–F4 范围 · TC1–TC6 验收 · FP-1–FP-8 · R0–R5 思考轮（early_stop at R5）· 三闸 pending 待人签 |
| 2026-10-28 | v0.1 · 00 代录 HG-TASK-DRAFT=approved（维护者授权 m00236）· 派 20-task-audit R1 |
| 2026-10-28 | v0.3 · 00 代录 HG-AUDIT-R1 + HG-GRAPH-MODULES = approved（维护者授权 m00236）· R1 PASS+NIT×3 闭合 · 30 解锁（红测先行 · 全程本地） |
