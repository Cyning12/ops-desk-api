---
hat: 10-spec
spec_slug: dialogue-full-view
date: 2026-10-11
---

# invoke · 10+spec 起草 · dialogue-full-view（B 面 · 全量展示+SSE 导出+mermaid 拓扑）

## 落稿摘要

- 首棒（子 Agent 4c99f183）长读卡滞 · interrupt 留痕（零落盘 · 与序1 骨架棒不同）· **00 代笔**（授权 m01606）。
- 上游实读：终局文档 docs/guides/DESIGN_agent_contribution_endgame_v0_zh.md :93-94（#15 折叠层级/#16 mermaid 中间档逐字并入）· handoff :41 B 面口径 · 分仓纪律承 A 面/chat-history-hitl-ux 先例。
- 锚点亲读：lg_rag/router.py:222/:289/:332 三端点 · sse_stream.py:201 node.progress 帧 · 帧型六枚（node.progress/hitl.waiting/error/done/query/answer · D4 钉 30 全量复核）· multi/graph.py:86-96 十节点清单。
- 交付：docs/spec/dialogue-full-view/SPEC-dialogue-full-view_v0.md——D1 导出形态三案（倾向 C 混合）· D2 折叠三层级原则 · D3 拓扑源二案（倾向 B 后端端点图演进单源）· D4 帧枚举完备性 · Q1-Q5 · 设计纪律 5（只读面/帧契约回兼容）· 拆 task 规划 B-E1/B-E2/B-F1 · HG-SPEC-SIGNOFF pending。

## 留 20 审要点

- D1/D3 倾向是否成立 · Q 块是否漏关键裁定 · 帧型清单 grep 口径完备性（D4 是否足以兜底）· 拓扑正确性「与 graph.py 1:1 机断」断言形态。
