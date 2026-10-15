# invoke · 00 · R3 裁定 + 再派 30 · lg-rag-sse-disconnect-completion

| 项 | 内容 |
|----|------|
| **时间** | 2026-10-14 |
| **帽** | 00（delegate-only · 未改 `app/`） |
| **触发** | [40 R2](66046aa3-f025-49c4-a251-479f81a91c28) TC5 **仍 FAIL** · `invoke_20261014_40_r2_verify.md` |
| **主样本** | run `f6a9cdd567ae41cc91c8ce3938712083` · 断连后 30s+ 409 · 无 settle 日志 · 图仍续写 seq7–8 |

## 裁定

| ID | 决定 |
|----|------|
| **R3-1** | **再派 30**（仍 **D1=A-only** · **禁 Wave B**） |
| **R3-2** | 判定 R2 `request.is_disconnected` **peek 轮询失败**：Starlette `is_disconnected` 用已 cancel 的 CancelScope 非阻塞 `_receive()`，仅当 `http.disconnect` **已入队**才为 True；live uvicorn 常未入队 → 探针永 False（单元 mock→True 假绿） |
| **R3-3** | 优先修法：**阻塞等待** disconnect 的独立 Task（body 已读后 `await receive()` 直到 `http.disconnect`）与主循环竞速 → cancel anext + `_settle_disconnected`；或证明 `yield`/StreamingResponse 在 ClientDisconnect 时必 aclose 生成器并补齐该路径。**禁止**再只加深 peek 轮询 |
| **R3-4** | 新测不得仅 mock `is_disconnected=True`；须覆盖「peek 永 False / 仅 blocking receive 才沉降」或等价契约 |
| **R3-5** | 修后交 **40 复跑 TC5**；若 R3 后再 FAIL → 00 停派，升级维护者（docs-spike / 接受残留 / 另议） |

## 下一棒

已派子 Agent：**30**（R3 · blocking disconnect watch）

本窗未改实现码 · 已派子 Agent：30
