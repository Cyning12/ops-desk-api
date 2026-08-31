# 可复制 Prompt · web 00 · T3 带稳定 thread_id（api 仓产出 · 不改 Vue）

> **给谁**：ops-desk-web **00**（新窗）。  
> **Open Folder**：`ops-desk-web/`  
> **api 00 本窗不改 web 码**。web T2 已 CLOSE：`docs/tasks/done/task_web_lg_rag_sse_t2.md` · PR #23。  
> 可选卫生：该 done task 仍链 api `tasks/active/task_lg_rag_sse_stream_updates.md` → 改为 `ops-desk-api/docs/tasks/done/task_lg_rag_sse_stream_updates.md`。

---

## 复制区（整段粘贴）

`````text
你是 ops-desk-web 的 00 统筹。默认只编排，不亲自改 Vue（派 10/30）。

Open Folder
  ops-desk-web 仓根

事实
  - 主 Chat 已走 POST /api/ops/lg-rag/stream（T2 · web #23 MERGED · 已 done）
  - api T3 开工：slug lg-rag-session-continuity · freeze 仍 lg-rag-sse-v1
  - SoT = thread_id（lg-rag）；禁止当 chat session_id 用
  - api 允许 api-only 先合；web 后置不挡 api PR
  - 禁止 C0–C4；禁止 T4 replay / T5 token

任务（建议 slug web-lg-rag-sse-t3）
  - Chat 发送稳定 thread_id（同会话续问同一 id；新会话新 id）
  - 刷新/重进：恢复或明确新开策略（写进 task）
  - 可选展示 session 元数据
  - 联调：同 thread 续问有上下文 · 新 thread 隔离
  - 非范围：replay UI、打字机 token、再切回 chat/stream

动作
  1. 可选：修正 done T2 对 api task 的过时 active 指针
  2. 起草 web T3 task · 闸 · 派 30
  3. 合入勿 auto-merge 直至与 api T3 联调策略写清

输出：阶段 · 交付路径 · 下一棒
`````
