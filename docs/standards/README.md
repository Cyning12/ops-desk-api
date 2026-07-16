# docs/standards

Ops Desk 后端编码标准。

| 文件 | 层级 | 说明 |
|---|---|---|
| [`CODING_BASELINE_L1_v1_zh.md`](./CODING_BASELINE_L1_v1_zh.md) | L1 | 语言无关编码原则（B-01～B-12） |
| [`CODING_BACKEND_L2_v1_zh.md`](./CODING_BACKEND_L2_v1_zh.md) | L2 | Python / FastAPI / SQLAlchemy 具体规则（P-01～P-15） |

## 使用方式

- 新 task 开始前通读 L1。
- 后端代码审查按 L2 条文逐项检查。
- PR 自检清单见 L1 §4。

## 与 harness 的关系

- L1/L2 是 `docs/harness/prompts/` 中 30-execute-code 等 prompt 的输入上下文。
- 每次代码变更须同步更新 `docs/_tech_graph/`。
