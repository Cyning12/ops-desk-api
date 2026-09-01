# Task Audit R1：lg-rag-sse-token-stream

> **hat_id**：20-task-audit  
> **task**：`docs/tasks/active/task_lg_rag_sse_token_stream.md`（T5 · Token 流）  
> **上游 SPEC**：`docs/spec/agent-infra/05_lg_rag_transport_and_session_plan_v0.md` §4.2 · §9 · §10.4 · `WAVE_READINESS_lg_rag_sse_v0.md` §1  
> **先例**：`docs/harness/reviews/task_lg_rag_sse_resume_audit_R1_20260831.md`（T4 · 同 freeze / 同非 chat 依赖禁区）  
> **日期**：2026-08-31 · 审查人：20-task-audit  
> **10 lint**：PASS（W4 无思考轮节 · SPEC 承载合法）· 本帽复跑 `dsh-coding-kit@1.10.0 task lint` → PASS（exit 0）核实

## 结论摘要

| 维度 | 结论 |
|------|------|
| **内容** | **pass** · 零阻塞 · 不退回 10 · 无「必须退回 00 改钉」级问题 |
| **流程闸** | `HG-AUDIT-R1` **仍 pending**（正确 · 20 不代签）· `HG-TASK-DRAFT` / `HG-GRAPH-MODULES` 已 approved |
| **30 授权** | **未签发** · pending 时禁止附 30 Prompt；真值仍在 task 人工闸表；**可交 00 代签 HG-AUDIT-R1** |

---

## 审查核对（对照 SPEC §4.2/§9/§10.4 · WAVE_READINESS §1 · 现网代码 · 先例）

| 审查点 | 结论 |
|--------|------|
| 范围/非范围互斥且与 05 §10.4 一致 | **未越界**。范围 = aggregator 终答 token→delta 帧 · T2 整段兼容 · 落盘/replay · 文档图谱 · 测试，对齐 §10.4「api 提供：`answer` 多帧 delta（aggregator 等）」。非范围逐条排除 T6 / C0–C4 / 重开 T3·T4 / 改 `chat/graph.py` / 本仓改 Vue / 新增 event_type / 新 freeze id / 新依赖边 / cancel / progress token 化 / 非终答 LLM 上屏 / 32_000 截断语义——与范围互斥无重叠 |
| §10.4 联调项/常见坑落实 | **已钉**。`done` 后停止追加 + 与 `node.progress` 并存不串台 → 00 定夺协议行 + 验收 4（seq 单调帧序断言）；§10.4 常见坑「T2 整段与 T5 delta 混用未分支」→ 00 定夺客户端规则（见 `delta` 追加 · 见 `content` 全量替换）+ failure_paths「混用契约」行（禁止 append） |
| freeze 纪律：扩展 `lg-rag-sse-v1` 而非 silent 扩 event_type | **是 · 不退回 00**。不新增 `event_type`（`answer` 单类型，payload 形态后向兼容扩展：delta 多帧 + 终帧 `final:true`）；旧客户端仅看 `content` 行为不变——与 T4 顶层 `cursor` 扩展先例同构，同 freeze id 扩展合法，本帽**不**坚持拆新 freeze id。回写义务已钩：00 定夺 freeze 行「契约写回 05 §4.2 `answer` 行 + §10.4『api 提供』列」+ 验收条 |
| 兼容协议可验收性 | **可验收**。delta 帧 `{"delta": "<chunk>"}` 按 `seq` 有序拼接；终帧 `{"content": "<full>", "final": true}`（T2 兼容）；验收 1「拼接 == 终帧 `content`（mock 断言）」；test_strategy_note 写明 mock token chunk 流（假 astream 同吐 updates + token）· 不连真 LLM |
| failure_paths 完备 | **完备**（六行）：provider 不支持流式/token 桥异常 → 降级整段（T2 行为）+ 日志；delta 途中图异常 → 已发 delta 保留并尽量落盘 + `error` 帧 + 不补 final；落盘失败不阻断已发 SSE（同 T4）；客户端混用 → 契约钉死全量替换；断连 → 跑完落盘 + replay 补齐 delta；401/404/422 不变 |
| 旧测影响面 + `chat/graph.py` 零 diff | **已列且文件核实存在**：`tests/test_lg_rag_sse_stream.py` · `test_lg_rag_sse_resume.py` · `test_lg_rag_session_continuity.py` · `test_session_continuity.py` 四个路径全在（glob 核实）；`app/ops/chat/graph.py` 零 diff 钩在验收条 |
| graph_delta / G-L2 同步钩（05 §9.3 T5 行） | **已钩**。graph_delta = `l1/10_flow_lg_rag.graph.yaml` + `l1/01_modules.md`（不新增一级模块，`HG-GRAPH-MODULES` 已 approved）；graph_delta_note + 验收条写「stream 符号变更 → G-L2 `by_path_lg_rag`/`by_symbol_lg_rag` 同步」，与 §9.3 T5 行原文一致；两 index 文件存在（glob 核实） |
| wiki_delta n/a 合理性 | **合理**。行为真值在 05 §4.2/§10.4 + 本 task，不晋升 coding_wiki；`lint-wiki-delta` 验收条在（10 自检已 PASS） |
| 思考轮 W4 豁免合法性 | **合法 · 不退回**。本帽复跑 lint → PASS · W4「无思考轮节（SPEC 承载合法豁免）」；思考轮由 05 §4.2/§9/§10.4 + WAVE_READINESS §1 承载；同 T3/T4 先例，20 不把缺节当内容阻塞 |
| 可行性：aggregator 整段现状 | **一致**。`sse_stream.py` `map_node_update`（L107–115）对 aggregator 整段发 `{"content": _truncate(answer, 32_000)}`——T2 整段现状与 task 描述一致；终帧沿用 32_000 截断语义（非范围不改） |
| 可行性：token 来源实证 | **可行**。`aggregator_node`（multi/nodes.py L396）走自定义 `provider.complete`；但 `BaseProvider.complete_stream` 已在接口层存在，SiliconFlow / Bailian 均实现（OpenAI 兼容 `stream=True`），且现 `complete` 本身就是 `_complete_from_stream` 聚合——provider 流式桥接无新依赖、可行性实证。task 不钉死实现选型（`astream(["updates","messages"])` **或** provider 流式桥接），选型风险见非阻塞 1 |
| 可行性：落盘 / replay 形状 | **可行**。`iter_lg_rag_sse` 单 emit 循环 seq 单调（sse_stream.py L139–171），全部帧经 `persist_run_event` 落盘——delta 帧天然随 emit 落盘；`POST /lg-rag/replay`（router.py L262–303）按落盘帧原样重放，形状不变即自然含 delta 帧，无需改 replay 语义（task 非范围亦钉「replay 语义本身不改」） |
| basic 占位空 answer 帧 | **一致**。sse_stream.py L206 占位 `{"content": "", "note": "no_aggregator"}`；00 定夺「basic 无独立终答 LLM → 保持现行为（占位空 answer 帧不变）」——与现网一致 |
| WAVE_READINESS §1 | **一致**。结论行 2026-08-31 api-00「可开工 T5（api 串行）」；task orchestration 行「§1 为 web 闸、不阻塞 api T5 · 可 api-only 先合」与原文备注（web T3/T4 研发中不挡 api T5）一致；web 打字机另 task（00 出 Prompt），本仓不改 Vue |
| 人工闸表与 invoke 留档 | **合规**。required_invoke_hats=`10,00,30`；00/10 invoke 已落盘 `docs/harness/invokes/by-task/lg-rag-sse-token-stream/`（两文件核实）；HG-AUDIT-R1=pending 待本审查落盘后 00 代签 |

其余可执行性：验收含 401/404/422 不变、token 流不可用降级整段、无新依赖边（不 import `app.ops.session`/`app.ops.chat`）、ruff/pytest/graph-compile/lint-wiki-delta 全绿；合入纪律「可 api-only 先合 · 勿 auto-merge」与 05 §11.1 一致。

---

## 阻塞

无。

---

## 非阻塞风险（不退回 10 · 30 知情即可）

1. **`stream_mode=["updates","messages"]` 对自定义 provider 不产 token 事件**：LangGraph messages 模式只表面化 LangChain chat model 的 token；现网 `aggregator_node` 等全部走自定义 `provider.complete`（非 BaseChatModel）。30 现实路径是 **provider 流式桥接**（`complete_stream` 已存在、两 provider 均实现）；task 未钉死选型故不阻塞，若 30 坚持 messages 模式须先验证或改桥接，token 归属过滤（仅 aggregator / direct_answer 的 LLM 调用）同理须按节点归属实现。
2. **aggregator「必做」与降级行读法**：00 定夺覆盖行「aggregator 必做 delta」须与 failure_paths「provider 不支持流式 → 降级整段」合读为「同 provider 流式可得则必做」。现网 SiliconFlow/Bailian 均有 `complete_stream`，预期可必做；运行环境流式不可用时 failure_paths 行接管，30 自检须写明依据。
3. **delta 落盘量增长**：每 token 一帧落盘 `ops_lg_rag_run_events`，行数随终答长度放大。task 未要求聚合/节流（failure_paths 已含落盘失败不阻断）；30 可在不破坏「拼接==终帧」与 seq 单调前提下自选 chunk 粒度（实现自由度内，非契约项）。
4. **direct_answer 降级理由**：router 模式若不同协议须保留整段并把降级理由写进 30 自检（验收 2 已钩，提醒勿漏）。
5. **占位空 answer 帧无 `final` 标记**：basic/router 无 aggregator 时占位帧 `{"content": "", "note": "no_aggregator"}` 保持现行为（00 定夺钉死）；旧客户端兼容，但 web 打字机 task 须知情「遇空 `content` 全量替换为空」这一边角。

---

## 回填清单

无（内容零阻塞 · 不改 task 实质 · **不改**人工闸表 status）。

---

## 签收

**内容签收 · pass**（终轮 R1）。流程闸 `HG-AUDIT-R1` 仍 **pending**（本帽不签发）——**可交 00 代签 HG-AUDIT-R1**；pending 期间禁止下发 30 Prompt。

---

## 维护者签闸（20 后 · 30 前）

- [ ] 已读 R1 审查结论
- [ ] 在 task 人工闸表将 HG-AUDIT-R1 改为 approved（00 代签 · 维护者 Prompt 授权 · 日期）
- [ ] commit task 文档或确认已签
- [ ] 再下发 Harness 30 Prompt

30 Agent 将以 task 表为准；pending 时必须拒开工（见 TEMPLATE_30_gate_stop.md）。
