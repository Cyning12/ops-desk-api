# GUIDE · 策略包 schema v0（llm 档级试点）

> **任务**：`host-v1-splittability-hardening` D4 · 2026-09-24

## 字段

| 字段 | 类型 | 说明 |
|------|------|------|
| `schema_version` | string | 须为 `"0"` |
| `surface` | string | 本波仅 `llm_tiers` |
| `task_tier_models` | map | task → model id 或 null |
| `task_tier_fallbacks` | map | task → list[str] |
| `model_unit_prices` | map | model → `{input,output}` 元/1K |

## 优先级

`explicit` > `OPS_LLM_TIER_*` / `RAG_GRADER_MODEL` > 策略包 > 代码默认

## 缺省

未设 `OPS_LLM_STRATEGY_PACK` → 不加载 → 现状逐字节。

## 样例

见 `app/llm/packs/llm_tiers.v0.yaml`（与代码默认对拍）。
