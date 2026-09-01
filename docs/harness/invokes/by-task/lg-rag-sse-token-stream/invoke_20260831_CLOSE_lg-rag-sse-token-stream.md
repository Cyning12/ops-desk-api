# Invoke：CLOSE · lg-rag-sse-token-stream

| 字段 | 值 |
|---|---|
| hat | CLOSE |
| task_slug | lg-rag-sse-token-stream |
| date | 2026-08-31 |
| PR | [#105](https://github.com/Cyning12/ops-desk-api/pull/105) MERGED |

归档 → `docs/tasks/done/task_lg_rag_sse_token_stream.md`

- 00 代签 · 维护者 Prompt 授权（`PROMPT_00_t4_close_through_c4_serial` · 串行波次 1）
- 生产：无新 Alembic（复用 `ops_lg_rag_run_events`）；deploy-api 随 master push 自动跑
- web T5 打字机：`PROMPT_web_00_lg_rag_t5_typewriter` 已落盘 `_prompts/`；web-00 须先跑 WAVE_READINESS §1 闸
- 下一棒：T6 `lg-rag-deprecate-chat-stream`（00 串行波次 2）
