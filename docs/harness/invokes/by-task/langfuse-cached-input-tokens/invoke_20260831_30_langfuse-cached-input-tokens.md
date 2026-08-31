# Invoke：30 · langfuse-cached-input-tokens

| 字段 | 值 |
|---|---|
| hat | 30 |
| task_slug | langfuse-cached-input-tokens |
| date | 2026-08-31 |

## GATE_VERIFY

`VERIFY: PASS`

## 交付

- `LlmUsage.cached_input_tokens` + `from_provider_usage`
- `update_current_generation_usage` → `input` / `output` / `cached-input-tokens`
- Chat stream + `complete()` 共用解析
- 单测 `tests/test_llm_usage_cache.py` + provider cache 用例

## 验证

- ruff 绿 · pytest SiliconFlow + usage_cache 19 passed
