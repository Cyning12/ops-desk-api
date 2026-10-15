# invoke · 00 · TC5 停派升级维护者 · lg-rag-sse-disconnect-completion

| 项 | 内容 |
|----|------|
| **时间** | 2026-10-14 |
| **帽** | 00（delegate-only · **未再派 30** · 未改 `app/`） |
| **触发** | [40 R3](c84f0856-0974-4ce2-9a7c-26717eff1c4f) TC5 **第三次 live FAIL** · 触发 R3-5 停派 |
| **主样本** | run `426b0a70e37d452aaeb649c2e091e79d` · 20–48s+ 仍 409 · 无 settle 日志 |

## 链摘要

| 轮 | 手法 | 单元 | live TC5 |
|----|------|------|----------|
| 30 → 40 R1 | `GeneratorExit`/`CancelledError` settle | aclose 绿 | FAIL（不 aclose） |
| 30-R2 → 40-R2 | `is_disconnected` peek 轮询 | mock 绿 | FAIL（peek 永 False） |
| 30-R3 → 40-R3 | blocking `request.receive` | mock put disconnect 绿 | FAIL（live 无 `http.disconnect`） |

**不变**：TC3 真在飞 409+Retry-After live **PASS**；pytest 子集 / verify **PASS**；产品面仍等同联调孤儿 409。

## 机理（00 收口判断）

uvicorn/Starlette 在本栈 **客户端中途断开时未必向应用 `receive()` 投递 `http.disconnect`**（或 StreamingResponse 占信道导致 watch 收不到）。应用层 peek/blocking 双路径均无法在 live 触达 `_settle_disconnected`。继续同面微调 **ROI 低**。

## 维护者裁定口

| 选项 | 状态 |
|------|------|
| E1 / E2 / E4 | 未选 |
| **E3 开 Wave B** | **已选（2026-10-14）** · 产品口径见 `invoke_20261014_00_e3_wave_b_plan.md` |

## 纪律

- ASGI disconnect 同面 **停派**（R1–R3 已证伪）。
- E3 方案已落盘；**待维护者确认方案细节后**再派 10 修订 / 重签 D1+图谱闸 / 30-B1。
- 工作树含未提交 30 改码 + 多轮 invoke/附件；**未 commit**。

本窗未改实现码 · **待派：等方案确认** · 阻塞：D1 重签 + task 修订
