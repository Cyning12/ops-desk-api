# app/llm — LLM Provider 层（L5）

Provider 抽象（`schema.BaseProvider`）+ 工厂（`factory.get_llm_provider`）+
OpenAI 兼容实现（`providers/siliconflow.py` / `providers/bailian.py`）。

## 四块硬化机制（llm-layer-hardening · 2026-09-21）

施加面统一在 `providers/base.py::BaseProviderImpl` 边界（`__init_subclass__` 包装
`complete_stream`；Bailian 例外：fallback 链内**逐候选**走同一 `_resilient_stream`，
先同模型退避重试、再换模型，链语义/顺序/test_only 过滤不变）。

### 1. 通用重试（`retry.py`）

- 判据：仅 `LlmProviderError(retryable=True)`（408/429/5xx/传输错/SSE 解析错）；
  4xx 其余 / 缺 key `ValueError` **零重试**。**分类靠结构不靠文案**。
- 算法：指数退避 + full jitter `delay_i = random(0, min(cap, base × 2^i))`。
- 流式纪律：重试只发生在**首 content chunk yield 之前**；已吐正文后出错
  零重试零换模型，上抛走既有 error 事件（已吐正文不重复不拼接）。
- 耗尽抛**原始** `LlmProviderError`（不包装丢根因）；log 记
  `llm_retry{attempt, delay, provider, model}`。

### 2. provider 级熔断（`circuit.py`）

- pybreaker 复用 `app/ops/capability/circuit.py` 模式：`calling()` 包每次出网、
  `exclude` 剔除业务错误（仅 `retryable=True` 计环境失败）、
  `throw_new_error_on_trip=False` 跳闸保留根因。
- 粒度 provider 级（siliconflow / bailian 各一）；open 时**零出网**立即
  `circuit_open` 错误（`retryable=False`），不返回半成功 answer。
- 观测：`circuit.snapshot()`（state / fail_counter / seconds_until_half_open /
  blocked_calls）；测试 hook `reset() / trip() / advance()`（拨时间不 sleep）。
- 多副本共享存储（Redis）留位不实现（进程内）。

### 3. 任务类型分层路由（`model_catalog.resolve_task_model`）

- 任务类型：`answer` / `grader` / `extract` / `structured`；档表
  `TASK_TIER_MODELS`（`None` = 不落档，回退现网默认）。
- 解析序：显式 `model=` > `OPS_LLM_TIER_<TASK>_MODEL` > 档默认 >
  `settings.ops_llm_model`；非法档/未知 task 回退默认 + warning。
- 兼容：`RAG_GRADER_MODEL` 并入 grader 档覆盖链（不破坏现网）；
  未分档调用点逐字节一致。
- 调用点：`chat/rag_nodes.py`（grader）· `memory/extract.py`（extract）·
  `structured_output/complete.py`（structured）· `chat/nodes.py`（answer）；
  路由决策写 span metadata（`llm_route{task_type, model, source}`）。

### 4. usage 成本归集（`usage.py` + 表 `ops_llm_usage`）

- run 上下文（run_id / surface / task_type）经 **ContextVar** 由入口点注入
  （chat streaming / lg_rag router / memory 抽取 / chat 节点）；provider 边界
  见到 usage 末帧时同点落表——不改 `complete/complete_stream` 签名。
- `run_id` 双口径（chat=UUID / lg_rag=hex）→ text + `surface` 区分，无 FK；
  无上下文调用点 `run_id=NULL · surface=background`。
- **tracing 关也落表**；无 usage 末帧 → 无行（不写 0 假账）；
  落表异常 → log + `persist_failure_count()` 计数，**不挡主答**。
- 成本公式不变：`cost = usage × evals/agent/cost/price_table_v1.yaml`（占位价），
  由查询/导出侧计算；表内不存金额、不存 prompt/answer 正文。

## env 一览

| env | 默认 | 说明 |
|---|---|---|
| `OPS_LLM_RETRY_ENABLED` | true | 重试总开关（false = 现网逐字节一致） |
| `OPS_LLM_RETRY_MAX_ATTEMPTS` | 3 | 总尝试次数（含首次） |
| `OPS_LLM_RETRY_BASE_DELAY_S` | 0.5 | 退避基数（秒） |
| `OPS_LLM_RETRY_MAX_DELAY_S` | 8.0 | 退避上限（秒） |
| `OPS_LLM_CB_ENABLED` | true | 熔断总开关 |
| `OPS_LLM_CB_FAIL_MAX` | 5 | 连续环境失败跳闸阈值 |
| `OPS_LLM_CB_RESET_TIMEOUT` | 60 | open → 半开探测间隔（秒） |
| `OPS_LLM_TIER_ANSWER_MODEL` | — | answer 档覆盖 |
| `OPS_LLM_TIER_GRADER_MODEL` | — | grader 档覆盖（优先于 RAG_GRADER_MODEL） |
| `OPS_LLM_TIER_EXTRACT_MODEL` | — | extract 档覆盖 |
| `OPS_LLM_TIER_STRUCTURED_MODEL` | — | structured 档覆盖 |

全部 env 非法值回退默认 + warning；全部开关关闭 = 现网逐字节一致。
