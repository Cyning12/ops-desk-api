# Invoke：20 书面审查 R1 — lg-rag-replay-resume-ux-opt（2026-10-28）

> **task**：`docs/tasks/active/task_lg_rag_replay_resume_ux_opt.md`（v0.1 · HG-TASK-DRAFT=approved 00 代录 · HG-AUDIT-R1/HG-GRAPH-MODULES pending）
> **帽**：20-task-audit（书面审查 · 只审不改 · 不落 30 Prompt）
> **required_invoke_hats**=10,20,30,40 含 20 ⇒ 本 invoke 快照强制落盘
> **审查文**：`docs/harness/reviews/task_lg_rag_replay_resume_ux_opt_audit_R1_20261028.md`

## 执行实录

1. skill `harness-20-task-audit` + `docs/harness/prompts/20-task-audit.md` 加载；AGENTS.md 闸纪律确认（本窗不切分支、不改码、不代签；既有脏文件 site-data.json 未触）。
2. **实证钉案 12/12 亲读核真**（base master `0a5d610`）：hitl/router.py:473-489 preflight（:478 同步 130–310s 自承）· :506-517 cursor · :534-537 端点 docstring · :580-584 create_task · :587-615 200 JSON replay.cursor · :243-249 auto_resume 后台触发 · :467-470 _RESUME_IN_FLIGHT 进程内单飞；hitl/resume.py:54-162 ResumeEventSink 直写事件表无 bus（:88 persist_run_event · :112-122 hitl.resumed · :124-137 close done）；lg_rag/event_store.py:94-126 run_is_terminal · :129-149 run_stream_closed 放行挂起 · :168-171 list_open_runs orphan 排除 · :225-265 refuse_in_flight 409；lg_rag/router.py:96-101 ReplayRequest · :372-428 replay 端点（:401-409 F-OBS-2 409+Retry-After · :416-418 event_gen）；sse_replay.py:71-83 format_sse_event 七键；sse_stream.py:74-75 keepalive comment；sse_subscribe.py:23-63；run_worker.py:71-80,93-165 registry 仅首段。
3. **D2 三驳回核实**：B1（auto 无连接可升级 + resume 200 JSON 契约）/ B3（契约面最小化）/ bus 直推（恢复路径无 bus + 多副本不成立 · tests/test_multi_replica_dualproc.py 佐证）——三驳回全部成立；follow=false 字面零 diff 可验收；env ≥600s vs 289s 实测 >2× 余量合理；禁伪造帧经 TC4 机断防得住。
4. **F1 谓词**：∃ hitl.resumed seq > 最新 done/error seq SQL 可行（同构先例 run_is_terminal）；stale 阈明示留 30 定稿；挂起/再挂起/沉降/首段在飞四态零 diff 逻辑自洽。
5. **freeze**：lg-rag-sse-v1 帧形状零触达 + 零新 event_type 声明属实；演进声明承 task_lg_rag_sse_resume.md:32 先例格式。
6. **红测先例**：tests/test_lg_rag_sse_resume.py:214 RED=AttributeError 同形逐字符核实。
7. **跨仓**：抽读 web invoke_20261028_30_implement.md 全文（PG 38cb1138 seq1-19 无洞 · 68/289s · chase 56s）+ 抽读 web src/stores/chat.ts（:1028/:1111/:1173 409 退避 · :1204-1268 sawInk 空泡回收 · :1069 resumeHint）——「web 已有 409 退避与空 200 防御双兼容」声明与 web 仓现状一致。
8. **旧测影响面独立 grep**：tests/ 26 文件命中 replay/resume；task 点名钉族在面内，TC5 全量对拍兜底；未按先例单列 grep 影响面验收项 → NIT-3。
9. **思考轮 R0–R5**：控制表五列齐备 · 回填闭合 · early_stop at R5 理由成立；graph_delta G-L1 预判无模块增删核对认可（01_modules.md lg_rag/hitl 行存续）。
10. **lint/verify 复跑**：`npx spec-wave task lint` EXIT=0 PASS；`verify --task` EXIT=2 BLOCKED 仅因两闸 pending（预期流程态）。

## 结论

**内容 PASS + 3 NIT（非阻塞）· 零内容阻塞；流程闸 HG-AUDIT-R1 / HG-GRAPH-MODULES pending 待维护者签。**

- NIT-1：FP-1 锚点文件名误植 `resume.py:447-449` → 实 `router.py:447-449`（resume.py 仅 384 行）
- NIT-2：思考轮控制表 R1 行 `resume.py:473-489` → 实 `router.py:473-489`
- NIT-3：旧测 grep 影响面未按 task_lg_rag_sse_resume.md:102 先例单列验收项（建议补列或注明 TC5 兜底）

**核验边界声明**：维护者原话锚 m00321 在 web 仓父窗，本帽无法亲读，以 00 单转述为准；task 两诉求拆解与转述一致。

HG-AUDIT-R1 pending ⇒ 本棒不附 30 Prompt；签闸清单见审查文文末。
