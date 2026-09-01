# coding_wiki · volatile

> **层**：volatile · **当前 active task** 专属；关账后清空或归档要点

## 相关页

- 稳定层：[[stable]]
- 项目层：[[context]]

## 本波 active

- `lg-rag-sse-delta-realtime`（**实现** · HG-AUDIT-R1 approved · 2026-09-01）：`emit` 后台 persist，不阻塞 SSE yield。真值：05 §10.4.1 + `app/ops/lg_rag/sse_stream.py`  
- `lg-rag-sse-delta-realtime-spec`（docs-only · HG-SPEC-SIGNOFF approved）：契约落盘；待 docs PR/CLOSE

## 执行帽速链

- Active tasks：`../tasks/active/`
- WikiTrack RUNBOOK：[`../harness/RUNBOOK_wikitrack_enable_obsidian_v1_zh.md`](../harness/RUNBOOK_wikitrack_enable_obsidian_v1_zh.md)

## 关账后

- 可复用条目 → 晋升 [[context]] / [[stable]]（仍只写指针，不双份正文）
- 本表清空，避免下一 task 读到 stale volatile
