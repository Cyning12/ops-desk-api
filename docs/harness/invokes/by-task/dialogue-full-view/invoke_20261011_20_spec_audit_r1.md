# invoke · 20-spec-audit R1 书面审 dialogue-full-view SPEC v0（2026-10-11）

> **帽**：20-spec-audit（SPEC 书面审 · 不改 SPEC 实质 · 不代签 HG-SPEC-SIGNOFF）
> **对象**：`docs/spec/dialogue-full-view/SPEC-dialogue-full-view_v0.md`（commit 4094009 · draft · HG-SPEC-SIGNOFF=pending · 00 代笔）
> **审查文**：[`spec_dialogue-full-view_audit_R1_20261011.md`](../../../reviews/spec_dialogue-full-view_audit_R1_20261011.md)
> **结论**：**PASS-WITH-NITS**（锚点 6 项实质全过 · N1-N4 照登移交拆 task）· 建议维护者签 HG-SPEC-SIGNOFF

## 令与纪律执行

- 令：核锚点（终局 :93-94 · handoff :41 · router 三端点 · sse_stream.py:201 · 帧型 grep · graph.py 十节点）· 评 D1/D3 倾向 · 纪律五条 · Q1-Q5 漏项 · 验收机断性；BLOCKER 退修订 / NIT 照登；报告 ≤25 行；commit 不 push/PR。
- 时效：15 分钟 · 骨架先行（4e39ec5 骨架 commit → 本 commit 填裁定）· 只核引用锚点未全仓通读。
- 实证范围：终局 :80-105 · handoff :30-49 · lg_rag/router.py:215-373 · sse_stream.py:83-201,340-350 · sse_replay.py:36-80 · multi/graph.py:60-104 · history.py:28-33 · lg_rag 面 event_type grep（emit/return 字面 + history 常量互证）。

## 关键裁定摘要

- 锚点核真 6 项实质全过；帧型清单行唯一失实（实 7 型 · SPEC 列 query 非 event_type · run.start/subtask.progress 漏列）——**D4 完备性质疑兜住**（subtask 系 30 复核 + 枚举归前端附录）→ N1 不阻签收。
- D1 倾 C / D3 倾 B 理由成立；高亮数据源实证成立（帧顶层 agent_role 载节点名 · sse_stream.py:136/:177）。
- NIT N1-N4 移交 00 拆 task 吸收（帧型行字面 · 高亮验收并 subtask.progress · :33 载荷表述 · 进行中 run 导出快照语义）。

## 闸态

HG-SPEC-SIGNOFF 仍 **pending**，待维护者人签（本帽不代签 · 00 代录口径）。
