# 可复制 Prompt · web 00 · chat-history-hitl-ux（前端 F1/F2 专项立项）

> **给谁**：ops-desk-web **00**（新窗 · 只编排不亲自改 Vue）。  
> **Open Folder**：`ops-desk-web/`  
> **api 契约真值**：`ops-desk-api/docs/spec/chat-history-hitl-ux/SPEC-chat-history-hitl-ux_v0.md`（signed 2026-09-30）· B1 `chat-history-api` / B2 `hitl-browser-decide`（三闸 approved · 30 ready）。  
> **api 00 本窗不改 Vue**。

---

## 复制区（整段粘贴）

`````text
你是 ops-desk-web 的 00 统筹。默认只编排（10-spec / 20-spec-audit / 10-task / 20-task-audit / 30），不亲自改 Vue。

Open Folder
  ops-desk-web 仓根

════════════════════════════════════
上游契约（唯一真值 · 只读 · 勿改 api 仓）
════════════════════════════════════

  ../ops-desk-api/docs/spec/chat-history-hitl-ux/SPEC-chat-history-hitl-ux_v0.md
    · §2 F1/F2 = 前端概要（本波范围依据）
    · §2 B1/B2 = 后端端点契约（前端承接）
    · §6 = 前端验收「以前端专项 SPEC 为准」
    · §3 非范围 · §5 failure_paths 一并读
  ../ops-desk-api/docs/harness/reviews/spec_chat_history_hitl_ux_audit_R1_20260930.md
  ../ops-desk-api/docs/tasks/active/task_chat_history_api.md（B1 · 端点字段族/分页/截断）
  ../ops-desk-api/docs/tasks/active/task_hitl_browser_decide.md（B2 · pending/decide 语义）
  ../ops-desk-api/docs/spec/chat-history-hitl-ux/ERRATA-chat-history-hitl-ux_v0_20260930.md

契约冻结面（本波只承接 · 禁改）
  SSE 零新事件（lg-rag-sse-v1 freeze 内已有）：
    - hitl.waiting（reason + requests[]）
    - done{status:"waiting_approval"}（终态 ≠ 完成）
    - 复用 answer / subtask.progress / run.start（run.start 增可选 query，非新事件）
  REST（cookie 鉴权）：
    B1 GET  /api/ops/chat/threads（thread_id/title/last_activity_at/run_count/latest_run_status + cursor/limit）
    B1 GET  /api/ops/chat/threads/{thread_id}/history（服务端聚合消息视图 query/answer/subtasks/terminal_status/hitl）
    B2 GET  /api/ops/hitl/pending（id/run_id/thread_id/reason/blocked_by/created_at · 仅本人 owner）
    B2 POST /api/ops/hitl/requests/{id}/decide（body {decision: approved|rejected} · 不自动 resume）
    B2 复用 POST /api/ops/hitl/requests/{id}/resume（既有 · 零改动）
  归属：跨用户 404（不泄露存在性）· decide 重复 409 · 非 maintainer 403 / 未登录 401

本仓缺口的真值（须自行核 · 勿臆造）
  src/stores/chat.ts switch 现含 run.start/node.progress/subtask.progress/answer/done/error
    · 无 hitl.waiting 分支（落 default 忽略）
    · case 'done'（约 :621-632）不看 status → waiting_approval 被当完成并 clearActiveRun() 清场
  已有 T4 续看基础：clearActiveRun（约 :461）· replayLgRag（:7）· cursor 提取
  → F2 = 补 hitl.waiting 卡片 + done 按 status 分支
  → F1 = 历史侧栏 + 中断可识别 + 进入 thread 续看

════════════════════════════════════
阶段 A · 立前端专项 SPEC（本波第一步 · 禁跳）
════════════════════════════════════

动作
  1. 在 main 之外建分支：git checkout -b task/chat-history-hitl-ux（禁 main 直改）
  2. 先读本仓 AGENTS.md / CLAUDE.md 与 docs/harness/prompts/（web 自己的真值）
  3. 派 10-spec 起草前端专项 SPEC：docs/spec/<新 slug>/SPEC-<slug>_v0.md
     必含：背景/目标 · 范围（F1 历史+续看 / F2 审批形态）· 非范围 · 验收标准（可机断）· failure_paths · R0–R5 思考轮
     契约面照抄上面的「契约冻结面」；不得新增/改 SSE 事件类型，不得改后端端点语义
     范围与非范围至少覆盖：
       F1：调 B1 threads/history；等待审批 run 徽标可识别；点击进入该 thread 并续看（复用 replay）
       F2：hitl.waiting → 醒目审批卡片（reason + 申请 id + 批准/驳回）→ decide → resume；
           done 按 status 分支：waiting_approval ≠ 完成态（不清场）；completed/failed 维持现行
       非范围：改 api 仓 · 新 SSE 事件 · OA 签名面 · 后端端点语义
  4. 派 20-spec-audit 落盘 docs/harness/reviews/spec_<slug>_audit_R1_*.md
     · 有阻塞 → 退回 10-spec；零阻塞 → SPEC 置待签并停下
  5. 停下等维护者签 HG-SPEC-SIGNOFF（禁代签）；签后才进阶段 B

════════════════════════════════════
阶段 B · 拆前端 task（HG-SPEC-SIGNOFF=approved 后）
════════════════════════════════════

  1. 派 10-task 拆 F1/F2（一个或两个 task · 含 Harness 元信息 + wiki_delta + 人工闸表）
  2. 派 20-task-audit R1 落盘；零阻塞 → 等维护者签 HG-TASK-DRAFT / HG-AUDIT-R1
  3. 签后派 30 实现 → 40 自检 → PR + CI 绿 → merge → CLOSE
     前端 Verify 真值（以本仓 workflow 为准）：pnpm lint → pnpm test → pnpm build

════════════════════════════════════
时序 / 依赖
════════════════════════════════════

  - 后端 B1/B2 三闸 approved、30 ready（端点实现进行中）。前端 SPEC 现在立；实现期若端点未上线，按契约 mock/降级，不得自造字段。
  - 后端 SPEC = 合并契约单源；前端本波只承接，不改契约。
  - 复用既有 T4 active-run / replay，不新造续看机制。

输出形状（对人类）
  阶段：{A-立SPEC|A-审SPEC|B-拆task|B-实现}
  分支：task/chat-history-hitl-ux
  交付：路径列表（SPEC / 审查文 / task）
  闸：HG-SPEC-SIGNOFF = {approved|pending—等维护者}
  下一棒：{20-spec-audit|10-task|20-task-audit|30}
  本窗未改 Vue 实现码 · 已派/待派：{帽}

停止条件
  - 阶段 A：前端专项 SPEC 落盘 + 20-spec-audit 落盘；维护者签 HG-SPEC-SIGNOFF 前不拆 task、不实现
  - 阶段 B：F1/F2 task + R1 审查落盘；未签 HG-AUDIT-R1 不派 30
`````

---

## 维护者备注（勿粘贴）

- 契约单源 = api 仓 SPEC；前端只在 <新 slug> 专项 SPEC 里承接，禁止复制后各自演化。
- F1/F2 合并为一个 SPEC、拆两个 task（或合并）皆可，由 web 00 定夺并落 task。
- api 侧后端合并在分支 `task/chat-history-hitl-ux`；前端可同名。
