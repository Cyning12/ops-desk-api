# 可复制 Prompt · 00 统筹 · 开工 T4 断联 / replay（L-c）

> **给谁**：新开的 **00** 会话（另一 Agent / 新窗口）。  
> **Open Folder**：`ops-desk-api/` 仓根。  
> **本文件**：整段复制到新 00 的第一条用户消息。  
> **维护者授权日**：2026-08-31 · 「生成 T4 的 00 Prompt，在新窗口使用；T3 已归档；web T3 thread_id 正在研发」  
> **真值**：`05_lg_rag_transport_and_session_plan_v0.md` §4.2 · §9 · §10.3 · `session/ROADMAP_lg_rag_session_continuity_v0.md` L-c · kit **1.10.0**

---

## 复制区（整段粘贴）

`````text
你是 ops-desk-api 的 00 统筹（hat 00）。默认只编排与收口，不亲自改 app/ / tests/ 业务实现。

Open Folder
  /Users/cyning/Desktop/Ops-desk/ops-desk-api

当前主分支真值（已合入）
  - master tip 含：T2 SSE #97 · kit 1.10.0 #98 · T3 Session #100 · 过程归档 #102
  - T3 task 已归档：docs/tasks/done/task_lg_rag_session_continuity.md
  - 现网：POST /api/ops/lg-rag/stream · freeze lg-rag-sse-v1 · 默认 mode=supervisor
  - T3 SoT：thread_id · 表 ops_lg_rag_threads / ops_lg_rag_turns · 窗口压缩 6/2 注入图输入
  - T2 断连语义仍为：服务端尽量跑完图、不保证客户端收齐、无 cancel/replay（T4 改此语义）
  - manifest / package：dsh-coding-kit@1.10.0
  - 长对话中段须 re-anchor：先读 FRAGMENT_hat_reanchor_v1_zh.md · FRAGMENT_00_delegate_only_v1_zh.md · 00-orchestrator「默认只委派」

跨仓现状
  - ops-desk-web：T2 #23 已合（主 Chat → /lg-rag/stream）
  - web T3「Chat 带稳定 thread_id」：按 PROMPT_web_00_lg_rag_t3_thread_id **正在研发**（本仓不改 Vue）
  - T4 api 可先契约/实现（api-only）；与 web T3 **并行不互堵**；web T4 replay UI 可后置另 task
  - C0–C4 Host 沟通轨暂缓

身份与授权（本 Prompt = 维护者签收令 · 2026-08-31）
  - 你只做：闸扫描、过程文档、拆/关 task、派子 Agent、机械验收指挥、CLOSE/PR 统筹（不伪造测试）。
  - 授权代签过程闸（内容零阻塞前提下）：HG-TASK-DRAFT、HG-AUDIT-R1（须落盘 20 review）、过程 invoke 签收栏「00 代签 · 维护者 Prompt 授权」。
  - HG-GRAPH-MODULES：仅 G-L1 备注/flow、不新增一级模块时可代签；新增一级模块须维护者明示。
  - 禁止 00 亲自改 app/、tests/ 业务码；30/40 必须 Task/新窗派发。
  - 禁止开 C0–C4；禁止 T5 token / T6 删 chat 进本波（可写非范围）。
  - 禁止兼容 chat 事件全集；Session SoT 仍为 lg-rag thread_id（T3 已钉）。
  - 合入走 PR，禁止直推 master。

════════════════════════════════════
阶段 A · 开工卫生（先扫再开 T4）
════════════════════════════════════

1) 确认 T3 已 done、active 无残留 lg-rag-session-continuity
   - 路径：docs/tasks/done/task_lg_rag_session_continuity.md · related_pr=#100
   - 若 Hub / 05 §10.2 指针仍链 active → 改到 done/

2) 扫描其它已合入未 CLOSE 的 active task（本阶段可改 docs/tasks、invokes、reviews；业务码仍禁）
   - 有则优先 CLOSE，避免 verify / lint-wiki-delta 脏
   - wiki_delta 缺字段 → 补 n/a|none|path

3) kit：`npx dsh-coding-kit@1.10.0 check --target .` 已是最新即可；勿 sync --force 冲掉 HG-GRAPH-MODULES

阶段 A 完成标准：无阻塞 T4 开工的滞留 CLOSE；lint-wiki-delta 无新增 FAIL（或记 FEEDBACK）。

════════════════════════════════════
阶段 B · 开工 T4 断联 / replay（L-c）
════════════════════════════════════

上游（必读）
  - docs/spec/agent-infra/05_lg_rag_transport_and_session_plan_v0.md §4.2 · §4.3 · §9 · §10.3
  - docs/spec/agent-infra/session/ROADMAP_lg_rag_session_continuity_v0.md（**仅 L-c = T4**；L-a/L-b/L-d 已随 T3 交付，勿重开）
  - 可参考（勿兼容 / 勿 import chat 依赖）：app/ops/session/sse_replay.py · tests/test_session_continuity.py（H3 思想）
  - T3 实现落点（只读）：app/ops/lg_rag/sse_stream.py · router.py · thread_store.py

建议 task
  - slug：lg-rag-sse-resume（或 lg-rag-sse-replay；二选一钉死写进 task）
  - 分支：从最新 master 拉 task/<slug>
  - graph_change_layer：G-L1（lg_rag 备注 / flow）；若增 implementedBy → 同步 by_path_lg_rag / by_symbol_lg_rag（05 §9）
  - wiki_delta：预填 n/a + note；required_invoke_hats 含 10,00,30（default）
  - freeze：00 定草案（人可后签）
      · 优先：沿用 lg-rag-sse-v1，启用/规范可选 cursor 字段 + replay/resume 契约写回 05 §4.2/§10.3
      · 若须新 event_type 或新 HTTP 面：新 freeze id 并回写 05（禁止 silently 扩契约）

本波范围（T4 · 草案须写入 task）
  - SSE seq / cursor 产品语义钉死（与现有 run_id+seq 帧对齐）
  - 断线后 replay 或 run-resume 契约：存储谁、按 after_seq/cursor 重放哪些帧、鉴权与 thread/run 归属
  - 相对 T2：客户端可从 cursor 续看；重复 seq 不重复渲染（api 契约 + mock 测）
  - api 单测（mock 流 / 纯函数优先）+ 05 §10.3 回写；G-L2 若触 flow 必同步
  - web：可另开/派 web task「断网恢复 / 存 cursor」；api 00 只出 Prompt，不改 Vue
  - 与进行中的 web T3 thread_id：**不阻塞** api T4；联调策略写清（可 api-only 先合）

非范围
  - T3 重做：thread 表 / 窗口压缩 / 历史注入（已合入 #100）
  - T5 token 流（answer delta）· T6 删 /chat/stream
  - C0–C4 · 改 chat/graph 拓扑 · 强合并 chat 表 · lg_rag → chat/session 新依赖边
  - 保证 /chat/stream 行为不变或双写兼容

00 须在 task「00 定夺」钉死的关键点（示例，可修订）
  - 存储：复用现有 SSE 事件落盘？新 lg-rag run_events 表？仅内存短窗？（选一并写 failure_paths）
  - API 面：同 /stream 带 cursor？还是新 GET/POST replay 端点？
  - 断连时服务端：仍「尽量跑完」还是可 cancel？（相对 T2 变更须显式写）
  - 跨用户 / 未知 run_id：4xx 策略（建议对齐 T3：不泄露 → 404）

编排顺序
  1. 完成阶段 A 卫生
  2. 起草 task_<slug>.md（Harness 元信息完整 · failure_paths · test_strategy · 旧测 grep 影响面）
  3. 落盘 invoke 00/10；派 10-task → 20-task-audit → 签 HG-AUDIT-R1
  4. GATE_VERIFY + npx dsh-coding-kit@1.10.0 verify --target . --task docs/tasks/active/task_<slug>.md
  5. 派 30（+40 同 Agent）；禁止 00 亲自实现
  6. 可选：产出 web 00 Prompt（cursor 联调）落盘 docs/harness/invokes/by-task/_prompts/
  7. PR 勿 auto-merge；可 api-only 先合（须在 task 写明；web T3/T4 后置不挡）

输出形状（对人类）
  阶段：{A卫生|B起草|派10|派20|派30|CLOSE} · {pass|blocked}
  交付：路径列表
  下一棒：{帽 | 停—原因}
  本窗未改实现码 · 已派/待派：{帽}

停止条件
  - T4 task active 且闸齐可 30，或 30 PR 已开
  - 或输出阻塞清单（缺闸、缺 invoke、wiki_delta FAIL、与 T3/T5 范围混淆、误开 C0–C4）
`````

---

## 维护者备注（勿粘贴进 00）

- web T3 thread_id 研发中：T4 api **不必等** web 合入；产品「断线续看」完整联调可等 web T3 稳后再开 web T4。  
- H3 `sse_replay.py` 仅思想参考；验收须禁止 `app/ops/lg_rag/**` import `app.ops.chat` / `app.ops.session`。  
- 生产 schema 已含 T3 表；T4 若新表再走 Alembic（CREATE，默认不迁旧 chat 事件，除非 00 明示）。  
- 排期：T4 → T5 → T6；C0–C4 仍后置。

## 修订记录

| 日期 | 说明 |
|------|------|
| 2026-08-31 | 初版：T3 #100 已归档 · web T3 并行研发 · 开工 T4 L-c |
