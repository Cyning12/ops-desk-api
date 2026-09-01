# Invoke：CLOSE · lg-rag-deprecate-chat-stream

| 字段 | 值 |
|---|---|
| hat | CLOSE |
| task_slug | lg-rag-deprecate-chat-stream |
| date | 2026-09-01 |
| PR | [#108](https://github.com/Cyning12/ops-desk-api/pull/108) MERGED |

归档 → `docs/tasks/done/task_lg_rag_deprecate_chat_stream.md`

- 00 代签 · 维护者 Prompt 授权（`PROMPT_00_t4_close_through_c4_serial` · 串行波次 2）
- 生产：无 Alembic；deploy 随 master push；`/chat/stream` 即起 410（JSON 迁移指针 + `Deprecation` 头）
- 过程注记：T6 task 过程文档曾随 #107（web-00 WAVE_READINESS 回填）提前入 master · 内容无冲突已核
- web 死代码清扫：`PROMPT_web_00_t6_remove_chat_sse` 已落盘 · iOS 另仓
- 下一棒：C0 `host-comms-boundary-spec`（00 串行波次 3 · docs-only SPEC）
