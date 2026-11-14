---
title: task · P0' T2b · chat 概念/文档收尾
---

# task · P0' T2b · chat 概念/文档收尾

> **状态**：`draft`（P0' 收官衍生落卡 · 待排期过闸）
> **来源**：issue Cyning12/ops-desk-workspace#23 · P0' 波次偏差登记

## Harness 元信息

| 键 | 值 |
|----|----|
| task_slug | p0prime-t2b-chat-concept-cleanup |
| 关联 issue | Cyning12/ops-desk-workspace#23 |

## 背景

T2（裁定 A3：摘 WS 路由→删旧码→归档 drop 三表→410 墓碑）以 a 波合并（PR #369 · ee1941fd）：chat 计算栈七件清除完成，但概念表 `ChatState`/`SseEvent` 行标注、`10_flow_chat.md`/`11_flow_sync_to_chat.md` 头部退役注记、归档 drop 三表（`ops_chat_sessions`/`ops_chat_messages`/`ops_chat_checkpoints`）的迁移与 410 墓碑端点收尾未随 a 波带走——本卡收口。

## 范围（草案）

1. 归档迁移：drop 旧 chat 三表（production cynaya.cn 数据导出确认后执行）。
2. 410 墓碑：旧 `/api/ops/chat/*` 端点返回 410 + 指向 lg-rag 的迁移说明（若 T2a 已部分落地则核对补齐）。
3. 图谱收尾：概念表 `ChatState`/`SseEvent` 行删除或归档标注定稿；flow 文档退役注记复核。

## 非范围

- lg-rag 侧任何改动；新功能。

## 验收（草案）

- [ ] 迁移 up/down scratch 实证；prod 导出确认记录
- [ ] 410 墓碑行为测试
- [ ] graph check OK；lint PASS

