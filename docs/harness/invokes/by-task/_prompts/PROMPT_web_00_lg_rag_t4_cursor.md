# 可复制 Prompt · web 00 · T4 断网恢复 / 存 cursor（api 仓产出 · 不改 Vue）

> **给谁**：ops-desk-web **00**（新窗 · 可后置；**不阻塞** api T4）。  
> **Open Folder**：`ops-desk-web/`  
> **api 真值**：`ops-desk-api` · task `lg-rag-sse-resume` · freeze `lg-rag-sse-v1` 扩展 · `POST /lg-rag/replay`  
> **依赖**：建议 web T3（稳定 `thread_id`）先稳再开本波；亦可先对接契约 mock。  
> **api 00 本窗不改 web 码**。

---

## 复制区（整段粘贴）

`````text
你是 ops-desk-web 的 00 统筹。默认只编排，不亲自改 Vue（派 10/30）。

Open Folder
  ops-desk-web 仓根

事实
  - 主 Chat 已走 POST /api/ops/lg-rag/stream（T2 · web #23）
  - web T3 thread_id 可能仍在研发；与本波可串行，不挡 api T4 合入
  - api T4（进行中）：slug lg-rag-sse-resume
      · live SSE data 顶层可选 cursor = "{run_id}:{seq}"
      · POST /api/ops/lg-rag/replay · body {run_id, after_seq} 或 {cursor}
      · 重放 seq > after_seq；同 run_id+seq 客户端去重不重复渲染
      · 断连时服务端仍尽量跑完（无 cancel）；客户端靠 replay 补帧
      · 未知/跨用户 run_id → 404
  - 禁止 C0–C4；禁止 T5 token 打字机进本波；禁止再切回 chat/stream

任务（建议 slug web-lg-rag-sse-t4 或 web-lg-rag-sse-resume）
  - 存最近 run_id / seq / cursor（会话或 local）
  - 断网/刷新后：从 cursor 调 /lg-rag/replay 续看
  - 重复 seq 不重复 append（尤其 answer）
  - 联调：DevTools offline → 恢复后帧不丢、不重复
  - 非范围：api 实现、token delta、删 chat 死代码（T6）

动作
  1. 确认 api T4 契约（05 §10.3 / api task 00 定夺）可读
  2. 起草 web T4 task · 闸 · 派 30
  3. PR 勿 auto-merge；可等 api T4 合入后再联调发版

输出：阶段 · 交付路径 · 下一棒
`````

---

## 维护者备注（勿粘贴）

- api-only 可先合；完整「断线续看」产品体验等本 web task。  
- 与 web T3 并行不互堵；若 thread_id 未稳，可先只验单次 run 的 cursor/replay。
