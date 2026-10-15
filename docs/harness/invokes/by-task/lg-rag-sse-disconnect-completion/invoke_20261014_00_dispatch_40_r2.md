# invoke · 00 · 再派 40 复跑 TC5 · lg-rag-sse-disconnect-completion

| 项 | 内容 |
|----|------|
| **时间** | 2026-10-14 |
| **帽** | 00（delegate-only · 未改实现码） |
| **前置** | [30 R2](c6bf51b7-fd21-4492-9dca-44c1c38f7786) 已补 `request.is_disconnected` 轮询 · `invoke_20261014_30_r2_asgi_disconnect.md` |
| **对照 FAIL** | [40 R1](89deb338-5033-4b6a-992d-beeb0e56a6d3) · run `5c5b4cf0…` 120s+ 409 |

## 下一棒

已派 **40** 复跑 TC5（须用 **R2 码面** 起 uvicorn · 中途 kill · 期望 `done{disconnected}` + replay 200；409 保护区抽检仍须 PASS）

本窗未改实现码 · 已派子 Agent：40
