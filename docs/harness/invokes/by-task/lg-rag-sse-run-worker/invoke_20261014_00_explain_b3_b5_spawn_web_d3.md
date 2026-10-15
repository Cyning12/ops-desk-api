# invoke · 00 · B3/B5 说明 + 派 web D3

| 项 | 内容 |
|----|------|
| **时间** | 2026-10-14 |
| **帽** | 00 |
| **维护者令** | 「1、开 web D3 2、你要补的 B3 和 B5 是什么？」 |

## TC-B3 / TC-B5 是什么（api 验收项 · 非 web）

| ID | 含义 | 现状 |
|----|------|------|
| **TC-B3** | 「继续回复」= 同 `thread_id` **新** `/stream`（可选 body `continue_from_run_id`）· **禁止**走 HITL `/resume` · replay **不**再调 LLM | 30 已接线 `continue_from_run_id`；40 有冒烟新 run；**缺**正式单测/HTTP 断言钉「零 resume」 |
| **TC-B5** | Wave A **补偿**：worker 进程死/超时仍无终帧 → 扫描补 `error`/`done{disconnected}` → 解除永久 409（**不**靠 ASGI 断连钩） | `scan_orphan_runs_for_compensation` 仍 TODO；cancel 路径可落 disconnected，**完整补偿扫描未做** |

二者均为 **api 仓薄补**，与 D3 web CTA **无关**。可另派 30 薄棒或 CLOSE 前补；**不阻塞**开 web D3。

## web D3

已派 web 仓 **10-task** 起草：History 半截可见 + terminal 驱动「续看/继续回复」· 对齐 api `continue_from_run_id` / `error.stage`。

本窗未改 api 实现码 · 已派子 Agent：web-10
