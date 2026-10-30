# task 审查（R1）：lg-rag replay 恢复段在写窗口语义化 + 审批后 SSE 续流（replay follow live-tail）

> **hat**：20-task-audit（书面审查 · 只审不改 · 不代签）
> **对象**：`docs/tasks/active/task_lg_rag_replay_resume_ux_opt.md`（v0.1 · HG-TASK-DRAFT=approved 00 代录 · HG-AUDIT-R1 / HG-GRAPH-MODULES pending）
> **审查日期**：2026-10-28 · **base**：master `0a5d610`（亲读核真 · 与 task 声明 base 一致 ✓）
> **需求真值锚**：维护者原话（m00321 · web 仓父窗转述）「给api仓起草一份replay的优化task，同时思考审批通过后也继续为SSE的方式通信的方案，审批后等待中间过长」——**核验边界声明**：原话锚在 web 仓父窗，本帽无法亲读 m00321 原文，以 00 单转述为准；task 对两诉求（①replay 优化 ②审批后 SSE 续流消等待）的拆解与转述一致，覆盖完整。

---

## 结论摘要

| 维度 | 结论 |
|------|------|
| **内容审查** | **通过 + 3 NIT（非阻塞）** —— 实证钉案全部亲读核真零造假；D1/D2/D3 定稿论证成立；验收六条可机断；思考轮 R0–R5 闭合 |
| **流程闸** | HG-AUDIT-R1 = **pending**（本审查落盘后维护者签）· HG-GRAPH-MODULES = **pending**（G-L1 预判无模块增删 · 核对认可 · 维护者签） |
| **lint / verify** | `npx spec-wave task lint` → **PASS**（EXIT=0）；`verify --task` → EXIT=2 BLOCKED，仅因两闸 pending（预期态 · 非内容失败），闸表读取与 task 字面一致 |
| **30 授权** | 本帽不签发；维护者签 task 表后 30 方可见闸开工 |

---

## 一、实证钉案抽验（全部亲读核真 · base 0a5d610）

| task 声明 | 亲读结果 | 判定 |
|---|---|---|
| `hitl/router.py:473-489` preflight 守卫，docstring 自承同步 130–310s | :473-489 `_preflight_decided_resume` 逐字符；:478「同步执行实测 130–310s，超前端 30s 超时」在 preflight docstring；resume 端点 docstring :534-537 同文 | ✓ |
| `:580-584` create_task 秒回 200 | :580-584 `asyncio.create_task(_run_resume_in_background…)` 逐字符 | ✓ |
| `:587-615` resume 200 JSON `replay.cursor` 契约 | :587-615 返回体含 `resume.status="accepted"` + `replay.cursor`（:604-607）；`_best_effort_replay_cursor` :506-517 受理时刻 `last_seq` | ✓ |
| `:243-249` auto_resume 后台触发（无 HTTP 连接可升级） | :243-249 decide 内 `auto_resume.schedule_auto_resume(...)` 后台派发，decide 返 JSON resume_block——**resume 端点升级 SSE 只覆盖 manual 路径的驳回论据成立** | ✓ |
| `hitl/resume.py:54-162` ResumeEventSink 直写事件表无 bus | :54-162 逐字符；:88 `persist_run_event` 直写；:112-122 `hitl.resumed` 自解释首帧；:124-137 close done（:131 `waiting_approval`/`resumed` 分态） | ✓ |
| `event_store.py:129-149` `run_stream_closed` 放行挂起 | :129-149 逐字符；done/error（含 `done{waiting_approval}`）即算收尾 ⇒ 恢复段在写窗首段挂起帧已存在 ⇒ 不拦 409、合法 200 零帧——根因链第 ③ 环成立 | ✓ |
| `event_store.py:225-265` `refuse_in_flight` 409 | :225-265 逐字符；:240-241 闸抛 `LgRagRunInFlightError` | ✓ |
| `event_store.py:168-171` `list_open_runs` orphan 排除 | :168-171 closed_ids = 任一 done/error ⇒ 挂起 run 被排除出 orphan 候选 ⇒ FP-1「orphan 补偿不覆盖崩溃在写窗」声明属实 | ✓ |
| `run_worker.py:71-80` registry 仅首段 | :71 `_workers` dict、:78-80 `get_run_bus`；:93-165 `start_run_worker` 仅 `/lg-rag/stream` 首段注册，恢复路径全程不触 run_worker（resume.py 无 import） | ✓ |
| `lg_rag/router.py:372-428` replay 端点 + :401-409 F-OBS-2 409+Retry-After | 逐字符（:405-409 409 + `Retry-After: 2` + detail "Run is still in flight"）；:416-418 event_gen 序列化体例 | ✓ |
| `sse_replay.py:71-83` `format_sse_event` 帧形状 | :71-83 逐字符（run_id/seq/ts_ms/agent_role/event_type/payload/cursor 七键） | ✓ |
| keepalive 口径 `sse_stream._KEEPALIVE_FRAME` | `sse_stream.py:74-75`：`_KEEPALIVE_INTERVAL_S=30.0`、`_KEEPALIVE_FRAME=": keepalive\n\n"`（SSE comment 不进 data）——follow 复用面真实存在 | ✓ |
| `_RESUME_IN_FLIGHT` 进程内单飞登记（R2 红线论据） | `router.py:467-470` request_id 键进程内 dict，注释自承「崩溃后登记随进程消失」——不可作判定面、谓词须以事件表为真源的论证成立 | ✓ |

**结论：12/12 钉案亲读核真，零转述造假。**

## 二、F2 SSE 续流形态定夺（D2 = replay opt-in follow live-tail）审查

1. **三驳回理由逐条核实**：
   - **B1 resume 端点升级 SSE（驳回）**：①auto 路径（`router.py:243-249`）由 decide 内后台派发、无专属 HTTP 连接可升级，升级 resume 端点只覆盖 manual——亲读成立；②resume 200 JSON（:587-615）为既有契约，改 SSE = breaking——成立。**驳回成立。**
   - **B3 新独立端点（驳回）**：契约面更大且与 replay 功能重叠，opt-in 字段为最小演进——裁量合理，成立。
   - **bus 直推（驳回）**：恢复路径 ResumeEventSink 直写事件表无 bus（亲读）；引入进程内 bus 到恢复路径须新做 registry 接线，且 `_RESUME_IN_FLIGHT` 式进程内存态多副本不成立（`tests/test_multi_replica_dualproc.py` 存在佐证该口径有钉）；事件表是唯一跨进程真源，DB 轮询 tail 多副本天然安全——**驳回成立。**
2. **follow=false 字面零 diff**：`ReplayRequest`（`lg_rag/router.py:96-101`）现状三键皆 `Field(default=None)` 可选；增 `follow: bool = False` 后旧请求体字面不含该键 ⇒ 反序列化等价，零 diff 声明**可验收**（TC2/TC5 钉死）。
3. **事件表唯一真源 vs 多副本安全**：写面仅 `persist_run_event`（ResumeEventSink 与首段 sink 同表续编号），follow 读面纯 SELECT seq>after_seq——无进程内态依赖，多副本安全论证成立。
4. **总时长上限 env ≥600s vs 实测 289s**：>2× 余量（289s×2≈578s < 600s），且 env 可调、默认值留 30 实证——余量合理、披露充分。
5. **「到点自然结束禁伪造帧」**：FP-3 + TC4「断言末帧非合成 done/error」——follow 循环只推事件表读出的帧，收尾条件 = 见到真收尾帧或上限自然结束，**无合成帧代码路径**，测试可机断（断言末帧来自事件表查询结果）。防得住。

## 三、F1 谓词设计审查

- **SQL 可行性**：∃ `hitl.resumed` seq > 最新 done/error seq —— `event_store.py` 已有同构只读 SQL 先例（`run_is_terminal` :94-126 payload status 表达式 + `run_stream_closed` :129-149）；新谓词纯 SELECT、事件表真源，实现无障碍。✓
- **stale 阈值**：FP-1 明示「30 实证定默认阈值」+ R3 residual_risks 明示「stale 阈默认值为设计参数（30 实证裁定）」——**阈值留 30 定稿且已明示**，符合「可接受但须明示」。✓
- **兼容性声明**：谓词定义（∃ resumed after 最新收尾帧）天然覆盖——纯挂起（无 resumed）⇒ 假；再挂起（resumed 后有新 `done{waiting_approval}`）⇒ 假；沉降（`done{resumed}`）⇒ 假；首段在飞（无收尾帧且无 resumed）⇒ 谓词假、走既有 `run_stream_closed` 原 409。四态逻辑自洽，TC1 (a)-(d) + TC2 三态零 diff 钉死。✓

## 四、冻结契约审查

- freeze `lg-rag-sse-v1` 帧形状七键（`format_sse_event` :75-82）零变、零新 event_type、keepalive 为 comment 不进 data——声明属实（follow 只演进 replay HTTP 面：请求体可选 `follow` 键 + 在写窗 409 语义化）。
- 契约演进声明承 `docs/tasks/done/task_lg_rag_sse_resume.md:32` 先例格式（「扩展：帧内可选 cursor + replay HTTP；不 silent 扩；回写 05」）——格式承袭 ✓，且本 task 跨仓协调节明示「30 按实判回写 05/图谱」。

## 五、范围/非范围/验收/failure_paths 审查

- **验收六条可机断性**：TC1 谓词矩阵（红测先行 · RED=AttributeError 同形）/ TC2 状态码 + 三态零 diff / TC3 follow 帧序逐字节同构 / TC4 上限零伪造帧 + 断连零副作用 / TC5 全量对拍 + ruff + graph-compile / TC6 live 对照照登——TC1–TC5 全机断；TC6 为 live 实证照登口径，承本仓历 task 先例（如 38ada53 live 同场闭合），接受。
- **failure_paths 八行覆盖面**：在写窗崩溃（FP-1)/idle 掐断（FP-2)/上限到点（FP-3)/误伤挂起（FP-4)/旧客户端（FP-5)/轮询压力（FP-6)/再挂起（FP-7)/闸纪律（FP-8)——覆盖面完整。**FP-1 风险披露充分性**：明示 ①谓词恒真→409 永久化风险 ②orphan 补偿不覆盖（`event_store.py:168-171` 机制层面说清为何不覆盖）③stale 阈是缓解非硬修 ④用户可见面退化为既有「稍后手动续看」——照登不硬修的决策留痕完整，披露充分。✓
- **F3 红测先行可执行性**：先例 `tests/test_lg_rag_sse_resume.py:207-228` 亲读——:214「修复前 RED 签名：event_store 尚无 LgRagRunInFlightError（AttributeError）」逐字符，同形可复刻（新谓词不存在 ⇒ AttributeError RED）。✓

## 六、跨仓协调节审查（web 影响面）

- 抽读 `ops-desk-web/docs/harness/invokes/by-task/web-hitl-approval-overlay-ux/invoke_20261028_30_implement.md` 全文：PG run `38cb1138` seq 1–19 无洞、恢复段 289s / `1039c1a9` 68s、chase 预算 ≈56s、根因链四节、D1 空泡防御落地——与 task 转述逐节一致。✓
- **「web 已有 409 退避与空 200 防御双兼容」抽读核实**（`ops-desk-web/src/stores/chat.ts`）：:1028/:1111-1112/:1173 replay 409+Retry-After 按头退避自动重试不弹错误条（FP-H2）存续；:1204-1268 `sawInk`/`CONTENT_INK_EVENT_TYPES` 空流终态回收 + :1069 resumeHint「恢复仍在进行，可稍后手动续看」兜底存续；:984 chase 10 次 56.25s 墙钟钉死——**双兼容声明与 web 仓现状一致**，故 F1 409 语义化不强制 web 同步改的裁量成立。✓
- chase 器兜底存续（FP-3 明示不删）、follow 迁移另立 web task（跨仓协调节②）、40 live 对照回执（TC6）——三件齐备。✓

## 七、旧测影响面（独立 grep 复核）

本帽独立 grep `tests/` replay/resume 相关钉（26 文件命中），重点面：`test_hitl_auto_resume.py`(121) · `test_hitl_resume.py`(57) · `test_hitl_pending_decide.py`(46) · `test_hitl_resume_async.py`(44) · `test_hitl_resume_events.py`(41) · `test_lg_rag_sse_resume.py`(28) · `test_lg_rag_sse_run_worker.py`(26) · `test_lg_rag_write_replay_guard.py`(17) · `test_multi_replica_dualproc.py`(48)。task 已点名前四族（必读 #5 + TC2 钉存续），replay(follow=false) 零 diff 所依赖的既有钉（`test_lg_rag_sse_resume.py` 200 流式帧序钉族 + `test_lg_rag_write_replay_guard.py` 守卫钉）均在面内；TC5 全量对拍零新增红兜底残余面。**实质覆盖成立**；惟先例 `task_lg_rag_sse_resume.md:102` 有「旧测 grep 影响面」单列验收项的体例，本 task 未单列——列 NIT-3（checklist 提醒级，非机械闸，不阻塞）。

## 八、思考轮 R0–R5 + graph_delta + lint/verify

- 控制表五列（轮/结论/early_stop/reason/residual_risks）齐备；R0–R5 逐轮回填闭合；early_stop at R5 理由（根因链四环全钉案 · 锚点全亲读 · 三备选显式驳回 · 设计参数显式留 30 · 再轮无新增信息）成立，残余风险（FP-1 缓解非根治 · graph_delta 预判）如实照登。✓
- `graph_change_layer=G-L1` 预判无模块增删：亲读 `docs/_tech_graph/l1/01_modules.md` lg_rag/hitl 行存续，本 task 仅行为表述面回写（备注级），预判合理；`graph_delta_note` 已留「零变化改填 none」逃生口。✓
- `npx spec-wave task lint` PASS（EXIT=0）；`verify --task` EXIT=2 仅因 HG-AUDIT-R1/HG-GRAPH-MODULES pending（流程态，非内容失败）。✓
- 仓内既有脏文件 `docs/arch-browser/dist/site-data.json` 未触碰；本帽全程零代码零 task 实质改动。✓

---

## 阻塞项

**内容阻塞：零。**

## NIT（非阻塞 · 建议 10-task 顺手勘误，不强制退回）

| # | 位置 | 问题 | 建议修复方向 |
|---|------|------|--------------|
| NIT-1 | failure_paths FP-1 行 | 引 `resume.py:447-449` 为「sink 不关」口径——**文件名误植**：`hitl/resume.py` 全文仅 384 行，该注释实在 `app/ops/hitl/router.py:447`（「# ResumeError 时 sink 不关…」）；R3 节已写对 | FP-1 改引 `router.py:447-449` |
| NIT-2 | 思考轮控制表 R1 行 | 「resume.py:473-489 docstring 自承同步 130–310s」**文件名误植**——preflight 实在 `hitl/router.py:473-489`（:478 含 130–310s 文）；正文 R1 节已写对 | 控制表 R1 行改 `router.py:473-489` |
| NIT-3 | 验收标准 | 未按先例（`task_lg_rag_sse_resume.md:102`）单列「旧测 grep 影响面」验收项；本帽独立 grep 见 `test_lg_rag_write_replay_guard.py`(17) /`test_hitl_auto_resume.py`(121) /`test_multi_replica_dualproc.py`(48) 等未点名 | 于 TC2 或新增验收项补列 grep 影响面清单，或于 TC5 注明「全量对拍即兜底覆盖残余面」 |

## 回填清单（如维护者要求闭合 NIT）

- task 小节「失败路径」FP-1 行：锚点改 `router.py:447-449`
- task 小节「思考轮控制」R1 行：锚点改 `router.py:473-489`
- task 小节「验收标准」：补旧测 grep 影响面单列项（可并 TC2）

---

## 维护者签闸（20 后 · 30 前）

- [ ] 已读 R1 审查结论（内容 PASS + 3 NIT 非阻塞）
- [ ] 在 task 人工闸表将 HG-AUDIT-R1 改为 approved（维护者 · 日期）
- [ ] 在 task 人工闸表将 HG-GRAPH-MODULES 改为 approved（G-L1 预判无模块增删 · 20 核对认可）
- [ ] commit task 文档或确认已签
- [ ] 再下发 Harness 30 Prompt

30 Agent 将以 task 表为准；pending 时必须拒开工（见 TEMPLATE_30_gate_stop.md）。
