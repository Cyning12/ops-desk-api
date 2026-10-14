# invoke · 00 · R2 裁定 + 再派 30 · lg-rag-sse-disconnect-completion

| 项 | 内容 |
|----|------|
| **时间** | 2026-10-14 |
| **帽** | 00（delegate-only · 未改 `app/`） |
| **触发** | [40](89deb338-5033-4b6a-992d-beeb0e56a6d3) TC5 **FAIL** · `invoke_20261014_40_verify.md` |
| **主样本** | run `5c5b4cf0187b4184a9c4be7307a4eab5` · 断连后 120s+ 仍 409 · 无 `done{disconnected}` |

## 裁定

| ID | 决定 |
|----|------|
| **R2-1** | **派 30 补修**（Wave A 收尾可达性）：live ASGI 客户端断开须触达 `_settle_disconnected` |
| **R2-2** | **禁 Wave B**（仍 D1=A-only；不解耦 worker） |
| **R2-3** | 修法优先：`request.is_disconnected` 竞态轮询 / keepalive `send` 失败路径 / 显式 cancel anext——任选可机证；须保留 TC3 真在飞 409 |
| **R2-4** | 单测 `agen.aclose()` 绿不够；30 须加贴近 live 的钩测或文档化复现脚本，修后交 **40 复跑 TC5** |

## 依据（40）

Starlette 1.3.1 ASGI≥2.4 无并行 `listen_for_disconnect`；卡在长 `__anext__` 时可能永不 aclose → settle 死角。单元 aclose ≠ live 断连。

## 下一棒

已派子 Agent：**30**（R2 补钩 · 仍 Wave A）→ 通过后 **40 复验 TC5**

本窗未改实现码 · 已派子 Agent：30
