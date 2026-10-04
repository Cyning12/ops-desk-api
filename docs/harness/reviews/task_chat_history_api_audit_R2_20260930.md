# R2 复审 · task_chat_history_api（帽 20-task-audit · B1 会话历史只读 API）

## 元信息

| 项 | 值 |
|---|---|
| **审查帽** | 20-task-audit（任务书面审查 · 不实现代码 · 不代签 human_gate） |
| **日期** | 2026-09-30 |
| **审查对象** | `docs/tasks/active/task_chat_history_api.md`（task_slug=`chat-history-api` · 状态 draft · 类型「码面」· 承接 R1 退回回填） |
| **对照真值** | SPEC `docs/spec/chat-history-hitl-ux/SPEC-chat-history-hitl-ux_v0.md`（signed 2026-09-30 · §2 B1 · §4 Q1/Q6 · §5 FP-1/2/4 · §6 B1）· SPEC 审查 `spec_chat_history_hitl_ux_audit_R1_20260930.md`（PASS-WITH-NITS · N1-N4）· R1 审查文 `task_chat_history_api_audit_R1_20260930.md` · `.importlinter` · 代码锚点真读 |
| **审查方式** | 全文真读 + 机跑实证：`task lint` / `task lint-wiki-delta` / `verify --task` / `git branch --show-current` / `grep run.start tests/` / 五处旧测锚点逐行 `read` / errata 便签真读 / 代码锚点 `read` |
| **轮次** | **R2 复审**（R1 唯一阻塞 B1 + nit N1-N4 回填复核；HG-AUDIT-R1 仍 `pending` · 本帽只审不签） |
| **R1 结论** | 退回 10-task（阻塞 1：行为变更类缺「旧测 grep 影响面」；非阻塞 nit 4 条） |

---

## 机跑证据（本轮实测 · 原始退出码）

| 命令 | 结果 | 退出码 |
|---|---|---|
| `npx --yes spec-wave@3.0.1 task lint --file docs/tasks/active/task_chat_history_api.md` | `LINT: PASS · task_chat_history_api.md` | **0** |
| `npx --yes spec-wave@3.0.1 task lint-wiki-delta --target .` | `scope: all · scanned: 147 · missing: 0 · issues: 0` → `LINT-WIKI-DELTA: PASS` | **0** |
| `npx --yes spec-wave@3.0.1 verify --target . --task docs/tasks/active/task_chat_history_api.md` | 三闸 pending（HG-TASK-DRAFT / HG-AUDIT-R1 / HG-GRAPH-MODULES）→ `VERIFY: BLOCKED · HG-AUDIT-R1 pending` | **2**（预期） |
| `git branch --show-current` | `task/chat-history-hitl-ux` | **0** |

**代码/文献锚点真读复核（与 task 断言逐条对拍）**

| 锚点 | 真态 | 判定 |
|---|---|---|
| `app/ops/lg_rag/sse_stream.py:343-347` | `yield await emit("run.start","system",{"run_id": rid, "thread_id": thread_id, "mode": mode})` —— payload **无 query** | ✅ 与 task L60 一致 |
| `app/ops/lg_rag/sse_stream.py:458-473` | `if waiting_approval:` → emit `done{status:"waiting_approval"}` → `_drain_persist()` → `return`；注释「不落 thread turns」 | ✅ 与 task L60 一致 |
| `app/ops/lg_rag/event_store.py` | `run_owner`:50 · `assert_run_owned`:87 · `load_events_after`:98（归属校验后按 seq 加载） | ✅ H4/H5 可复用 |
| `.importlinter` | `lg-rag-outbound` L205-241（`app.ops.lg_rag` 禁 → `app.db`/`app.ops.deps` 等；已有 `event_store -> app.db.*`/`router -> app.ops.deps` 白名单）· `chat-outbound` L243-267 | ✅ 裁定 B1 落点不触碰 chat-outbound |
| `docs/spec/chat-history-hitl-ux/ERRATA-chat-history-hitl-ux_v0_20260930.md` | **存在**（25 行）：记 A1 豁免（触及 `run.start` · 可选 `query` · 不新增 event_type · 边界/原因/影响面）· 并轨 SPEC 升版 | ✅ errata 已有落点 |

---

## 核对项表 · 流程闸（与内容分开列）

| # | 核对项 | 证据 | 判定 |
|---|--------|------|------|
| P1 | HG-TASK-DRAFT 状态登记 | task 人工闸表 L39 = `pending`（blocks 20-R1, 30）；与 verify 输出逐行一致 | ✅ 自洽（非本帽代签） |
| P2 | HG-AUDIT-R1 状态登记 | task L40 = `pending`（blocks 30）；机跑 verify → `VERIFY: BLOCKED · HG-AUDIT-R1 pending`（exit 2） | ✅ 与真值一致（本帽不签发） |
| P3 | HG-GRAPH-MODULES 状态登记 | task L41 = `pending`（blocks 30）；verify 同判 `❌ 若 pending 拒 30` | ✅ |
| P4 | HG-PILOT-OPSDESK-GLAYER | task L42 = `n/a`（复用既有 G-L1 模块 · 不涉物理分层试点新增） | ✅ |
| P5 | 分支隔离（禁 master 直改） | 实测 `git branch --show-current` = `task/chat-history-hitl-ux`（exit 0）；与 task L17 / SPEC §Harness 默认分支一致 | ✅ |
| P6 | `task lint` 机跑（必须 PASS） | `LINT: PASS` · **exit 0** | ✅ |
| P7 | `task lint-wiki-delta` 机跑 | `LINT-WIKI-DELTA: PASS` · 147 scanned · 0 missing · 0 issues · **exit 0** | ✅ |
| P8 | `verify --task` 机跑（流程态取证） | 三闸 pending → `BLOCKED`（exit 2）；与 task 表逐行一致 | ✅ 自洽（待维护者签 P2） |
| P9 | 20 invoke 快照义务 | task `required_invoke_hats` = `10,30,40`（**不含 20**）· `review_hat=20`；按 skill，20 invoke 仅 required 集合含 20 时强制 → 本轮免落 invoke 快照 | ✅ n/a |

**流程闸小结**：分支正确 · `task lint` 与 `lint-wiki-delta` 双 PASS · 三闸 pending 登记与 verify 输出自洽。30 授权链未通（HG-TASK-DRAFT / HG-AUDIT-R1 / HG-GRAPH-MODULES 均 pending），符合「20 落盘前不得开工」；本帽不代签。

---

## 核对项表 · 内容（含 R1 回填闭合复核）

| # | 核对项 | 证据 | 判定 |
|---|--------|------|------|
| C1 | 范围承接 SPEC §2 B1 两端点 | task H1 L87 = `GET /api/ops/chat/threads`（thread_id/title/last_activity_at/run_count/latest_run_status + cursor/limit 20/100/422）；H2 L88 = `GET .../{thread_id}/history` 按 run 升序重建；H3-H6 为聚合纯函数/归属/查询/图谱拆解，均在 B1 子面内 | ✅ |
| C2 | SPEC §6 B1 四条验收全部可机断对应 | SPEC L167 → task L124（造 run → 2 thread + 字段族 + waiting_approval）；SPEC L168 → task L126（query+answer+subtask+done.status+hitl.waiting requests · seq 序）；SPEC L169 → task L128（跨用户 404 不泄露）；SPEC L170 → task L129（缺 query 老 run/降级不阻塞）。**四条全覆盖** | ✅ |
| C3 | 非范围锁死 vs SPEC §3 | task L96-103 八条：SSE 新事件/帧语义（除 A1 已批 run.start 可选键）· checkpoint 重建 · 新表/写路径 · 删改重命名 · 前端 · `app/ops/chat/**` · OA/HITL 决策面 · multi 图拓扑——逐条覆盖 SPEC §3 L95-100 | ✅ |
| C4 | 裁定 A1 一致性 + errata 落点 | task L30/L56/L63/L96/L131 均写「仅 `run.start` payload 增**可选** `query` 键（非新 event_type）· 其余帧零改动」；errata 便签已实体落盘并三处引用（L30/L56/L147） | ✅ |
| C5 | 裁定 B1 与 import 契约真值 | `.importlinter` 实测：`chat-outbound` L243-267、`lg-rag-outbound` L205-241；B1 路由落 lg_rag 不触碰 chat-outbound，`app/ops/chat/**` 零 diff 可成立 | ✅ |
| C6 | 锚点真实：`run.start` 无 query | `sse_stream.py:343-347` 真读 payload = `{run_id, thread_id, mode}`，无 query | ✅ |
| C7 | 锚点真实：`waiting_approval` 不落 turns | `sse_stream.py:458-473` 真读：挂起路径 emit done → drain → return，不调 `persist_thread_turns` | ✅ |
| C8 | 阈值可机断（N2 已钉） | answer 截断 `32000`（L127）；分页 `20/100` + `limit>100 → 422`（L87 · L125，**默认 20 断言 + 超限 422 单列**）；超时 `10s → 504` 常量可注入（L130） | ✅ N2 闭合 |
| C9 | failure_paths 锋利 | 八条（L111-118）：404 不泄露 / 401 / 大 thread 分页+截断+504 / 老 run 降级 / 落盘缺口如实重建 / 422 / SSE 误改拒收 / 未签闸拒开工——均含触发·行为·可重试·用户可见 | ✅ |
| C10 | test_strategy 可执行 | L19-20：造 `ops_lg_rag_run_events` 行 → threads/history 断言；纯函数优先；不连真 LLM；SSE 帧对拍（仅 run.start 可选键）；新增 `tests/test_chat_history_api.py`（预期新建） | ✅ |
| C11 | 思考轮 R0–R5 控制表 + 陈旧文字更正（N3） | L168-173 六轮齐全 · `actual_last_round=R5` · `early_stop=no`；**R5 residual_risks 已改为**「无（A1 已采纳：pending run 历史含 query；存量旧 run 无 query 键按 FP-4 降级）」；**R1 开工闸段 L183 已改为**三闸 pending 陈述，原「两处 00 定夺阻塞」已消；全文仅 L64 保留 `A2`（属「备选」对照项，非陈旧残留） | ✅ N3 闭合 |
| **C12** | **行为变更类「旧测 grep 影响面」（K7 · R1 唯一阻塞）** | task **验收 L134** 与 **test_strategy_note L20** 均已含「旧测 grep 影响面」项，列出 5 处 `run.start` 既有断言面并声明新增可选 `query` 键 **subset-安全**（取子集字段 / 排序对拍双端一致 / 不断言 payload 恰等三键）。**逐行真读复核**：`test_lg_rag_sse_stream.py:101-102`（thread_id/mode 子集）、`test_lg_rag_session_continuity.py:166-167`（event_type + thread_id）、`test_multi_replica_dualproc.py:420-424`（live↔replay payload `json.dumps(sort_keys)` 对拍，增键双端对称）、`test_lg_rag_sse_token_stream.py:183`（event_type）/ `:254`（types 列表首项 run.start，仅类型）、`test_chat_ws.py:226`（event_types 列表）/ `:275`（event_types[0]）——**均为子集/对拍断言，subset-safe 成立** | ✅ **B1 闭合** |
| C13 | 验收条目全可机断 | 14 条（L124-137）：造行断言 / diff / lint / graph-compile / lint-wiki-delta 命令均可机断；无主观措辞；与自检 L203「验收 14 条」计数一致 | ✅ |
| C14 | 计数一致性 | 范围 H1-H6（6）· 非范围（8）· failure_paths（8）· 验收（14）· R0-R5（6）与正文/自检声明逐项对齐 | ✅ |

**内容核对计数**：14 项 → ✅ 14 · ❌ 0。R1 阻塞 B1 与 nit N1/N2/N3/N4 **全部闭合**。

---

## R1 回填闭合复核（逐条）

| R1 项 | 要求 | task 落点 | 判定 |
|---|---|---|---|
| **阻塞 B1 / K7** | 验收 + test_strategy_note 增「旧测 grep 影响面」并声明 subset-安全 | `test_strategy_note` L20 + 验收 L134（5 处锚点全列 · subset-安全声明） | ✅ **闭合** |
| **nit N1** | 钉 import 纪律：经 `app.ops.lg_rag.router` 间接取 CurrentUser/OpsUser，或显式 ignore_imports 授权 | 「已定夺」L75「import 纪律（20 R1 N1 实测）」+ 验收 L135（间接取 或 ignore_imports 授权 · `lint-imports` 绿） | ✅ **闭合** |
| **nit N2** | 补分页默认 20 断言 + `limit>100` → 422 | H1 L87「默认 20 · 上限 100 · 超限 422」+ 验收 L125「默认 limit=20；limit>100 → 422；不重不漏」 | ✅ **闭合** |
| **nit N3** | 更正 R5/R1 陈旧文字（A2 假设 / 两处 00 阻塞） | R5 residual_risks L173 改为 A1 已采纳口径；R1 段 L183 改为三闸 pending 陈述；`A2` 仅存于 L64「备选」对照 | ✅ **闭合** |
| **nit N4** | A1 errata 落可追溯落点 | 新建 `docs/spec/chat-history-hitl-ux/ERRATA-chat-history-hitl-ux_v0_20260930.md`（25 行，内容完整）+ task L30/L56/L147 三处引用 | ✅ **闭合** |

---

## 阻塞清单

**0 条内容阻塞 · 0 条流程阻塞**（流程三闸 pending 属预期状态，非缺陷）。

R1 唯一阻塞 B1 已闭合：本 task 触及 frozen `run.start` 帧 payload（A1 可选 `query` 键），属行为变更类；现验收 L134 与 test_strategy_note L20 均已含「旧测 grep 影响面」项，列出 5 处既有 `run.start` 断言面并经逐行真读确认 **subset-安全**，同时保留整包 `pytest tests` 绿（L133）。K7 条款满足。

---

## 非阻塞清单（nits · 不阻 R2 通过 · 供 30/40 参考）

| # | 级别 | 内容 | 建议 |
|---|------|------|------|
| **O1** | 观察（无需回填） | 影响面清单列出 R1 要求的 **5 处锚点（满足「至少」）**；但全 tests `grep run.start` 另返回 `tests/test_lg_rag_sse_resume.py:129`（event_type）· `tests/test_memory_extract_p1.py:269`（event_types 集合含 run.start）· `tests/test_session_continuity.py:14`（fixture payload {}）· `tests/test_lg_rag_sse_stream.py:92`·`tests/test_multi_replica_dualproc.py:401`·`tests/test_chat_ws.py:169/307/312`。经复核上述均为 **event_type-only / fixture / 对拍** 断言，对 payload 增可选键 **subset-safe**，不构成阻塞 | 30 改帧前再跑一次 `grep -rn 'run.start' tests/` 确认；这些点已被验收 L133「`pytest tests` 全绿」覆盖，**无需退回 10-task** |
| **O2** | 提示（无需回填） | 裁定 B1「零 import-linter 契约改动」成立的前提是 `history_router.py` 数据面走同族 `event_store`/`history.py`（`event_store -> app.db.*` 已有白名单），路由层仅经 `app.ops.lg_rag.router` 间接取鉴权；若新文件直连 `app.db.session`/`app.db.models` 仍会破 `lg-rag-outbound` | 验收 L135「`lint-imports` 绿」已是兜底硬闸，30 收敛即可；若需新增 `ignore_imports`，同步更正「零契约改动」措辞 |

> 说明：O1/O2 均**不要求 10-task 回填**，不影响 R2 通过与签闸；仅为 30 交付时的实现提醒。

---

## 结论：R2 **PASS-WITH-NITS**（0 阻塞）

- **流程闸**：分支 `task/chat-history-hitl-ux` ✅ · `task lint` PASS（exit 0）✅ · `task lint-wiki-delta` PASS（exit 0）✅ · verify `BLOCKED`（exit 2，三闸 pending）与 task 表自洽 ✅。**零流程阻塞**；`HG-AUDIT-R1` 仍 `pending`，本帽不签发。
- **内容**：范围/非范围/验收/failure_paths/阈值/锚点/思考轮 **全部成立**；SPEC §6 B1 四条验收逐条可机断对应；`run.start` 无 query（`sse_stream.py:343-347`）与 `waiting_approval` 不落 turns（`:458-473`）经真读属实；裁定 A1/B1 与维护者定夺一致。
- **R1 闭合**：唯一阻塞 B1（K7 旧测影响面）与 4 条 nit（N1 import 纪律 / N2 分页 422 / N3 陈旧文字 / N4 errata 落点）**全部闭合**，逐条有 task 落点与真读证据。
- **残留**：2 条非阻塞观察（O1 影响面清单可再扩 / O2 import 白名单兜底提示），**无需回填、不阻签闸**。
- **下一棒**：维护者签 `HG-AUDIT-R1` → `approved` 后，方可由 30 开工。**本轮不附 30 Prompt**（HG-AUDIT-R1 仍 pending）。

---

## 修订记录

| 日期 | 摘要 |
|------|------|
| 2026-09-30 | R2 复审落盘：全文真读 + 机跑 `task lint`（PASS/exit 0）· `task lint-wiki-delta`（PASS/exit 0）· `verify`（BLOCKED/exit 2）· `git branch`（task/chat-history-hitl-ux）· 五处旧测锚点逐行真读 · errata 便签真读 · 代码锚点 `sse_stream.py:343-347/458-473` + `event_store.py` 复核。结论：**R2 PASS-WITH-NITS**（0 阻塞；R1 阻塞 B1 + nit N1-N4 全部闭合；新增观察 O1/O2 供 30 参考，无需回填）。 |

---

## 维护者签闸（20 后 · 30 前）

> 本轮 R2 已 PASS，下列清单适用；请在 task 人工闸表签 `HG-AUDIT-R1`。

```text
## 维护者签闸（20 后 · 30 前）

- [ ] 已读 R2 审查结论（0 阻塞 · R1 回填全部闭合）
- [ ] 在 task 人工闸表将 HG-AUDIT-R1 改为 approved（维护者 · 日期）
- [ ] commit task 文档或确认已签
- [ ] 再下发 Harness 30 Prompt

30 Agent 将以 task 表为准；pending 时必须拒开工（见 TEMPLATE_30_gate_stop.md）。
```
