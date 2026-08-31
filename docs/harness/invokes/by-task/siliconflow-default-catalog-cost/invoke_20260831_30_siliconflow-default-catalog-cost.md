# Invoke：30 · siliconflow-default-catalog-cost

| 字段 | 值 |
|---|---|
| hat | 30 |
| task_slug | siliconflow-default-catalog-cost |
| git_branch | task/siliconflow-default-catalog-cost |
| date | 2026-08-31 |

## GATE_VERIFY

| human_gate_id | task表status | blocks_30 | 30可开工？ |
|---|---|---|---|
| HG-TASK-DRAFT | approved | N | Y |
| HG-AUDIT-R1 | approved | Y | Y |
| HG-GRAPH-MODULES | approved | N | Y |

`npx dsh-coding-kit verify` → **PASS**

## 交付

- `SILICONFLOW_MODELS` env（逗号 / `id|名`）+ `_DEFAULT_SILICONFLOW_MODELS` 兜底；默认 Flash
- grader / lg_rag router 默认 `siliconflow` + `Qwen/Qwen3.6-27B`
- Host 价表保留核对数值与 bailian；缺字段补 0；export 计入 cache
- 单测：`tests/test_model_catalog.py` + cost / chat / provider 断言更新

## 验证

- `ruff check` 触及文件：绿
- `pytest` eval_cost / model_catalog / TestListModels / test_default_model / test_config：绿
