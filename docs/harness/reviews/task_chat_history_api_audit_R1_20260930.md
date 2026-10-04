# R1 审查 · task_chat_history_api（帽 20-task-audit · B1 会话历史只读 API）

## 元信息

| 项 | 值 |
|---|---|
| **审查帽** | 20-task-audit（任务书面审查 · 不实现代码 · 不代签 human_gate） |
| **日期** | 2026-09-30 |
| **审查对象** | `docs/tasks/active/task_chat_history_api.md`（task_slug=`chat-history-api` · 状态 draft · 类型「码面」） |
| **对照真值** | SPEC `docs/spec/chat-history-hitl-ux/SPEC-chat-history-hitl-ux_v0.md`（signed 2026-09-30 · §2 B1 · §4 Q1/Q6 · §5 FP-1/2/4 · §6 B1）· SPEC 审查 `spec_chat_history_hitl_ux_audit_R1_20260930.md`（PASS-WITH-NITS · N1-N4）· `docs/standards/CODING_BACKEND_L2_v1_zh.md` · `.importlinter` · 代码锚点真读 |
| **审查方式** | 全文真读 + 机跑实证：`npx spec-wave task lint` / `npx spec-wave verify` / `git branch --show-current` / 代码锚点 `read`·`grep` / import-linter 临时副本探针（不改本仓 app/·tests/） |
| **轮次** | R1（HG-AUDIT-R1 仍 `pending` · 本帽只审不签） |
| **维护者已定夺** | 裁定 A1（`run.start` payload 增**可选** `query` 键 · 非新 event_type · 登记 SPEC §1 errata）· 裁定 B1（路由落 `app/ops/lg_rag/history_router.py` APIRouter(prefix="/chat") + 聚合落 `app/ops/lg_rag/history.py` · 路径保持 `/api/ops/chat/threads` · **不得改 .importlinter chat-outbound 契约**） |

---

## 核对项表 · 流程闸（与内容分开列）

| # | 核对项 | 证据 | 判定 |
|---|--------|------|------|
| P1 | HG-TASK-DRAFT 状态 | task 人工闸表 L39 = `pending`（blocks 20-R1, 30）；本棒系维护者直接指派执行 20 审查，故审查照常落盘 · 但 draft 未扫这一事实如实登记 | ⚠ pending（留痕 · 非本帽代签） |
| P2 | HG-AUDIT-R1 状态 | task L40 = `pending`（blocks 30）；机跑 `verify`：`VERIFY: BLOCKED · HG-AUDIT-R1 pending`（exit 2） | ✅ 与真值一致（本帽不签发） |
| P3 | HG-GRAPH-MODULES 状态 | task L41 = `pending`（blocks 30）；verify 同判 `❌ 若 pending 拒 30` | ✅ 与真值一致 |
| P4 | HG-PILOT-OPSDESK-GLAYER | task L42 = `n/a`（复用既有 G-L1 模块 · 不涉物理分层试点新增）；与 H6 仅改 G-L1 备注一致 | ✅ |
| P5 | 分支隔离（禁 master 直改） | 实测 `git branch --show-current` = `task/chat-history-hitl-ux`；与 SPEC §Harness 元信息默认分支一致（L19） | ✅ |
| P6 | `task lint` 机跑（必须 PASS） | `npx --yes spec-wave@3.0.1 task lint --file docs/tasks/active/task_chat_history_api.md` → `LINT: PASS · task_chat_history_api.md` · **exit 0** | ✅ PASS |
| P7 | `verify --task` 机跑（流程态取证） | `npx --yes spec-wave@3.0.1 verify --target . --task docs/tasks/active/task_chat_history_api.md` → `VERIFY: BLOCKED · HG-AUDIT-R1 pending`（exit 2）· 三闸 pending 与 task 表逐行一致 | ✅ 自洽（本审查文落盘后仍待维护者签 P2） |

**流程闸小结**：分支与三闸登记自洽 · task lint PASS。30 授权链未通（HG-TASK-DRAFT / HG-AUDIT-R1 / HG-GRAPH-MODULES 均 pending），符合「20 落盘前不得开工」——本帽不代签。

---

## 核对项表 · 内容

| # | 核对项 | 证据 | 判定 |
|---|--------|------|------|
| C1 | 范围承接 SPEC §2 B1 两端点 | task H1（L86）= `GET /api/ops/chat/threads` 字段族（thread_id/title/last_activity_at/run_count/latest_run_status + cursor/limit 20/100）；H2（L87）= `GET /api/ops/chat/threads/{thread_id}/history` 按 run 升序重建。与 SPEC §2 B1（L64-65）逐字对齐；H3-H6 为聚合纯函数/归属/查询/图谱拆解，均在 B1 子面内，未越出 | ✅ |
| C2 | SPEC §6 B1 四条验收在 task 中均有可机断对应项 | SPEC L167 → task 验收#1（造 2+1 run → 2 thread + 字段族含 waiting_approval）；SPEC L168 → 验收#3（query+answer+subtask+done.status+hitl.waiting requests · seq 序）；SPEC L169 → 验收#5（跨用户 404 不泄露）；SPEC L170 → 验收#6（缺 query 老 run / waiting_approval 降级不阻塞）。**四条全覆盖** | ✅ |
| C3 | 非范围锁死 vs SPEC §3 | task 非范围八条（L95-102）：SSE 新 event/帧语义（除 A1 已批 run.start 可选键）· checkpoint 重建 · 新表/写路径 · 删改重命名 · 前端 · `app/ops/chat/**` · OA/HITL 决策面 · multi 图拓扑——逐条覆盖 SPEC §3 L95-100 | ✅ |
| C4 | 裁定 A1 一致性 + errata 如实登记 | task L50/L56/L63/L95/L130 均写「仅 `run.start` payload 增**可选** `query` 键（非新 event_type）· 其余帧零改动」，与维护者裁定 A1 逐字一致；L56 明写「SPEC §1 纪律 #1 对 run.start payload 增键的豁免登记于此，SPEC 升版时回填 errata」。**但仓内无 errata 机制可承载**（`grep -rn errata docs/` 零命中），仅 task 内注记为「待回填」——可追溯性偏弱（非阻塞 · 见 nit N4） | ✅（附 nit N4） |
| C5 | 裁定 B1 与 import 契约真值 | 实测 `.importlinter`：`chat-outbound` 存在（L243-267 · 明列 `app.ops.chat`/`app.ops.session` 禁 → `app.ops.lg_rag`）；`lg-rag-outbound` 存在（L205-241 · 明列 `app.ops.lg_rag` 禁 → `app.ops.chat`/`app.db`/`app.ops.deps` 等）。B1 路由落 lg_rag **确实不触碰 chat-outbound 契约**，且 `app/ops/chat/**` 零 diff 可成立。**但见 C12-adjacent 的 import 陷阱（nit N1）** | ✅（附 nit N1） |
| C6 | 锚点真实：`run.start` 无 query | 真读 `app/ops/lg_rag/sse_stream.py:343-347`：`yield await emit("run.start", "system", {"run_id": rid, "thread_id": thread_id, "mode": mode})` —— **payload 无 `query` 键**，task L60 断言如实 | ✅ |
| C7 | 锚点真实：`waiting_approval` 不落 turns | 真读 `sse_stream.py:458-473`：`if waiting_approval:` → emit `done{status:"waiting_approval"}` → `_drain_persist()` → `return`；L461 注释逐字「不落 thread turns —— 这一轮没有答案」；`persist_thread_turns` 调用只在 :489-491 的 done 正常路径。task L60 断言如实 | ✅ |
| C8 | 阈值可机断 | answer 截断 `32000`（验收#4 · 标 `answer_truncated=true`）· 分页 20/100（H1 字段 · 验收#2）· 超时 `10s → 504`（验收#7 · 「常量可注入」）。三者皆 pytest 可断；**但默认 20 与上限 100 未单列断言、limit>100 的处置（422 vs clamp）未钉**（非阻塞 · nit N2） | ✅（附 nit N2） |
| C9 | failure_paths 锋利 | 八条（L110-117）：404 不泄露 / 401 / 大 thread 分页+截断+504 / 老 run 降级 / 落盘缺口如实重建不 500 / 422 / SSE 误改拒收 / 未签闸拒开工——均含触发·行为·可重试·用户可见，可执行 | ✅ |
| C10 | test_strategy 可执行 | task L19-20：集成/单测造 `ops_lg_rag_run_events` 行 → threads/history 断言；纯函数优先；不连真 LLM；SSE 帧对拍。与 SPEC §Harness `test_strategy=required` 一致；落地测试文件 `tests/test_chat_history_api.py` 尚不存在（本 task 新建 · 预期） | ✅ |
| C11 | 思考轮 R0–R5 控制表 + 自检闭合 | L163-172：R0-R5 六轮齐全 · `actual_last_round=R5` · `early_stop=no` · 各轮 reason/风险有值；L198-200 自检结论（范围 H1-H6 · 非范围八条 · 验收 13 条 · FP 8 条 · 裁定 A1/B1 · 未签闸 · 未改 app/tests）与正文计数一致。**R5 residual_risks 仍写「裁定 A 若选 A2…」，A1 已采纳后该残留陈旧**（非阻塞 · nit N3） | ✅（附 nit N3） |
| C12 | **行为变更类「旧测 grep 影响面」条款（K7）** | 本 task 触及 frozen SSE 帧 `run.start` payload（A1 增可选 `query` 键）+ 新增路由，属**行为变更类**。全文件 `grep -nE '旧测\|grep\|影响面\|回归'` **零命中**；验收 13 条（L123-135）无「旧测影响面」项——仅泛化「`pytest tests` 全绿」与「`sse_stream.py` 其余 diff 为空」。既有测试确有 run.start 断言面（如 `tests/test_lg_rag_sse_stream.py:101-102` `thread_id`/`mode` · `tests/test_lg_rag_session_continuity.py:166-167` · `tests/test_multi_replica_dualproc.py:420-424` payload 排序对拍），task 未要求 grep 清点、未声明 subset-安全 | ❌ **缺**（阻塞 B1 · 按 K7 退回 10-task） |
| C13 | 验收条目全可机断（除 C12） | 13 条（L123-135）：12 条为造行断言/diff/lint/命令，可机断；第 10 条 pytest 全绿可机断。无主观措辞 | ✅ |

**内容核对计数**：13 项 → ✅ 11 · ⚠ 非阻塞 nit 3 项（N1/N2/N4 等，C4/C5/C8/C11 附）· ❌ 1（C12）。

---

## 阻塞清单

**1 条内容阻塞 · 0 条流程阻塞**（流程三闸 pending 属预期，非缺陷）。

| # | 阻塞 | 证据 | 处置 |
|---|------|------|------|
| **B1** | **行为变更类 task 缺「旧测 grep 影响面」验收/回归项**（skill K7：缺则**退回 10-task** 补列） | task 全文无「旧测/影响面/grep」字样（0 命中）；本 task 改 `run.start` 帧 payload（A1）+ 新增两路由，属行为变更类；既有 run.start 断言面见 `tests/test_lg_rag_sse_stream.py:101-102`、`tests/test_lg_rag_session_continuity.py:166-167`、`tests/test_multi_replica_dualproc.py:420-424`、`tests/test_lg_rag_sse_token_stream.py:183/254`、`tests/test_chat_ws.py:226/275`，task 未要求清点与 subset-安全声明 | **退回 10-task**：在 `## 验收标准` 增「旧测 grep 影响面」项 + 在 `test_strategy_note` 钉回归口径（见回填清单 §1） |

> 说明：新增路由本身不影响旧测；但 A1 改动 frozen SSE 帧是实打实的契约面行为变更，K7 条款正为此设。仅「`pytest tests` 全绿」不足以替代「影响面清点 + subset-安全断言」——后者让 30 在改帧前就知道哪些旧断言受约束。

---

## 非阻塞清单（nits · 不阻本帽执行 · 但建议随 10-task 回填一并处理）

| # | 级别 | 内容 | 建议 |
|---|------|------|------|
| **N1** | 交付陷阱（重要） | 裁定 B1 宣称「零 import-linter 契约改动」，但**本帽机跑实证**：在 `app/` 临时副本中新增 `app/ops/lg_rag/history_router_probe.py` 直接 `from app.ops.deps import CurrentUser` + `from app.db.models import OpsUser`，`lint-imports` 报 `lg_rag 族 … BROKEN`（`history_router_probe -> app.db.models`、`-> app.ops.deps`）；改为经同族 `from app.ops.lg_rag.router import CurrentUser` **间接取**则 `12 kept, 0 broken`。即：B1 零契约改动**可达**，但仅在间接 import 纪律下成立；自然直连 import 会破坏 `lg-rag-outbound` | 10-task 在 `## 验收标准`/`test_strategy_note` 明确 import 纪律（经 `app.ops.lg_rag.router` 间接取 `CurrentUser`/`OpsUser`），或明示授权给 `lg-rag-outbound` 增一条 `ignore_imports` 并如实说明这是契约改动（与裁定 B1「零改动」措辞需二选一对齐）。**注意：维护者裁定仅禁改 chat-outbound，未禁 lg-rag-outbound**，故此点属可解，不要误判为死结 |
| **N2** | 验收精度 | 分页阈值「默认 20 · 上限 100」未单列机断；`limit>100` 处置（422 还是 clamp）未钉 | 验收#2 补：默认 `limit=20` 断言 + 上限行为二选一钉死（建议 422，与 task 既有 422 口径一致） |
| **N3** | 文献陈旧 | R5 控制表 `residual_risks`（L170）仍写「裁定 A 若选 A2，pending run 历史缺 query」，而 A1 已采纳，该残留已不成立；R1（L180）「两处 00 定夺阻塞」亦已被 L54-78「已定夺」解阻 | 10-task 顺手更正 R5/R1 文字，避免读者误判仍存未决项 |
| **N4** | 可追溯性 | task 称 run.start 增键为「对 SPEC §1 errata」，但仓内无 errata 承载机制（`grep errata docs/` 零命中）；现仅 task 内一句「SPEC 升版时回填」 | 给 errata 一个可追溯落点：在 SPEC §修订记录加一行 errata 注记，或落一份独立 errata 便签；避免「待回填」成为悬置 |

---

## 结论：R1 **退回 10-task**

- **流程闸**：分支隔离 ✅（`task/chat-history-hitl-ux`）· `task lint` ✅ PASS（exit 0）· 三闸 pending 如实登记（本帽不签发 HG-AUDIT-R1）。**零流程阻塞**。
- **内容**：范围/非范围/验收/failure_paths/阈值/锚点/思考轮 **大体成立**——SPEC §6 B1 四条验收逐条可机断对应；`run.start` 无 query（sse_stream.py:343-347）与 `waiting_approval` 不落 turns（:458-473）经真读实证属实；裁定 A1/B1 与维护者定夺一致。
- **退回理由（唯一实质阻塞 B1）**：本 task 触及 frozen SSE 帧（`run.start` payload 增键）+ 新增路由，属**行为变更类**，但验收标准与 test_strategy **完全缺失「旧测 grep 影响面」项**（skill K7 明文：缺则退回 10-task 补列）。该缺口无法在 30 阶段安全弥补——30 开工时拿不到旧测影响面清单，改帧即可能在不知情下踩既有断言。
- **下一棒 = 10-task**（回填上表 §1 阻塞项 + 顺手处理 N1-N4），复审为 **R2**。**本帽不指示 30 开工，禁止 30 Prompt。**

---

## 回填清单（退回 10-task · 按 task 小节标题定位）

| # | task 小节 | 回填内容 |
|---|-----------|----------|
| 1 | `## 验收标准` + `test_strategy_note` | 新增「**旧测 grep 影响面**」验收项：清点并列出 `run.start` 既有断言面（至少 `tests/test_lg_rag_sse_stream.py:101-102`、`tests/test_lg_rag_session_continuity.py:166-167`、`tests/test_multi_replica_dualproc.py:420-424`、`tests/test_lg_rag_sse_token_stream.py:183/254`、`tests/test_chat_ws.py:226/275`），声明新增可选 `query` 键为 **subset-安全**（既有断言取子集字段、排序对拍双端一致，不断言 payload 恰好等于三键）；保留整包 `pytest tests` 绿 |
| 2 | `## 已定夺`（裁定 B）· `## 验收标准` | 钉 `history_router.py` 的鉴权 import 纪律：经 `app.ops.lg_rag.router` 间接取 `CurrentUser`/`OpsUser` 以保 `lg-rag-outbound` 零改动；或明示授权增 `ignore_imports` 并同步更正「零 import-linter 契约改动」措辞 |
| 3 | `## 验收标准` H1 分页 | 补 `limit` 默认 20 断言 + `limit>100` 处置（422/clamp 二选一） |
| 4 | `## 思考轮控制` R1/R5 | 更正陈旧残留（A2 假设、两处 00 阻塞）为 A1 已采纳 / 已定夺解阻 |
| 5 | `## 已定夺` / SPEC 侧 | 给 A1 errata 一个可追溯落点（SPEC 修订记录一行或独立便签） |

---

## 修订记录

| 日期 | 摘要 |
|------|------|
| 2026-09-30 | R1 审查落盘：全文真读 + 机跑 `task lint`（PASS/exit 0）· `verify`（BLOCKED/exit 2）· `git branch`（task/chat-history-hitl-ux）· 代码锚点 `sse_stream.py:343-347/458-473` 真读 · `.importlinter` chat-outbound/lg-rag-outbound 核验 · import-linter 临时副本探针实证 B1 零契约改动的成立条件。结论：**退回 10-task**（阻塞 1：行为变更类缺「旧测 grep 影响面」）；非阻塞 nit 4 条。 |

---

## 维护者签闸（20 后 · 30 前）

> ⚠️ **本轮 R1 = 退回 10-task**：下列清单**在 R2 复审转 PASS 后才适用**；请勿在退回轮把 HG-AUDIT-R1 签为 approved（签了会放行一个缺旧测影响面的行为变更 task）。本轮下一棒 = **10-task 回填**。

```text
## 维护者签闸（20 后 · 30 前）

- [ ] 已读 R1 审查结论
- [ ] 在 task 人工闸表将 HG-AUDIT-R1 改为 approved（维护者 · 日期）
- [ ] commit task 文档或确认已签
- [ ] 再下发 Harness 30 Prompt

30 Agent 将以 task 表为准；pending 时必须拒开工（见 TEMPLATE_30_gate_stop.md）。
```
