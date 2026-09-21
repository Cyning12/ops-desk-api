# invoke · 40 · memory-facts-p0 · 独立核验

| 项 | 内容 |
|----|------|
| **时间** | 2026-09-21 |
| **帽** | 40（子 Agent 独立核验 · 未复信 30 报告） |
| **结论** | **40 PASS**（A–H 八项核验全过 · 11/11 验收映射 PASS · 无阻塞不退回） |

## 关键证据

- diff 面全部落在声明面 + 00 文档面；SSE 仅 +4 行透传；无新依赖
- 六条否定断言齐备；变异检验先断言污染进注入块、revoke 后断言消失（非假通过）
- 默认关零 diff 对比 (消息类型, 全文内容) 全列表
- 全量 3 失败经 master worktree 同 env 复跑证实既有（30 漏报 capability proxy 1 条，性质相同非阻塞）
- alembic 往返 0/0；graph-compile 0；task lint PASS

## 已知未测项

① span memory_facts_injected 无专门单测（代码路径在）；② 30 漏报 1 条既有失败；③ 提交/PR 后续流程
