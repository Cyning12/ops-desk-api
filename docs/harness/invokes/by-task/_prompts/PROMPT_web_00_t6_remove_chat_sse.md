# PROMPT · web 00 · T6 删 chat SSE 死代码

> **产出者**：api 00（串行波次 2 并行交付）· 2026-08-31  
> **执行仓**：`ops-desk-web`（本仓不改 Vue）  
> **前置**：api T6 已合入（`POST /api/ops/chat/stream` → **410 Gone**；task `lg-rag-deprecate-chat-stream`）· web 自 T2 已切 lg-rag 流（05 §10.5「web 已在 T2 切流」）

---

## 背景

api 侧 `/api/ops/chat/stream` 已 410（JSON 迁移指针 + `Deprecation` 头）。web 自 T2 起 Chat 走 `/ops/lg-rag/stream`，chat SSE 客户端已成死代码。

## 建议范围（web task 草稿点）

1. 删 `useOpsChatSse`（死代码）及其专属类型/常量  
2. 移除 chat stream API 常量（`/ops/chat/stream` 路径常量）  
3. grep 清扫 `chat/stream` · `useOpsChatSse` 活引用（含注释引导）  
4. 更新 README（传输主线 = lg-rag SSE）  
5. 联调确认：全站无 chat stream 请求（DevTools Network 勾选）

## 非范围

- 改 api（410 契约已 freeze）· `/chat/models`、`/chat/sessions/latest` 若仍在用 **保留**（api 侧未下线）· iOS

## 状态

api T6 实现中（分支 `task/lg-rag-deprecate-chat-stream`）；api 合入后本 Prompt 可派 web 30。
