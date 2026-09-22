# SPEC：L5 模型层硬化（重试 / 熔断 / 分层路由 / 成本归集）（v1）

> **状态**：`signed`（HG-SPEC-SIGNOFF=**approved** · 2026-09-21 · 维护者授权 00 本窗签收全部过程文档 · 原话「授权00签收所有过程文档，接续 llm-layer-hardening」）
> **track**：`feature`（L5 模型层 · 承重墙缺角补齐；含新表 → 带 alembic migration 与图谱同步义务）
> **上游**：`../ops-desk-workspace/docs/08-interview/07_agent-memory-prompt-module-landscape_v1_zh.md` §L5（393–396 行）+ 附录 A L5 行（511 行：「有链无退避抖动 · 缺 LLM 重试/熔断、分层路由、成本按 run 聚合」）
> **格式基准**：`docs/spec/memory-facts-p1/SPEC-memory-facts-p1_v1.md`（signed）
> **下游**：人签 SPEC → 00 出 task → 20-task-audit → HG-AUDIT-R1 → 30 实现
> **Open Folder（实现）**：`ops-desk-api/`

---

## Harness 元信息

| 字段 | 值 |
|---|---|
| **spec_slug** | `llm-layer-hardening` |
| **invoke_slug** | `llm-layer-hardening`（task 阶段） |
| **test_strategy** | `required` |
| **test_strategy_note** | 单测：fake provider / fake httpx 注入各类错误——可重试错误退避重试、不可重试零重试、流中已吐 token 后零重试；熔断三态转换用 advance 式时间拨动 hook 不 sleep；路由分档断言 + 非法档回退；usage 落表按 run_id 聚合 + 落表故障不挡主答；全波次回归 `tests/test_llm_providers.py` `tests/test_chat_nodes.py` |
| **Open Folder（实现）** | `ops-desk-api/` |
| **默认分支** | `task/llm-layer-hardening` |
| **graph_change_layer（建议）** | `G-L1`（`docs/_tech_graph/l1/01_modules.md` `llm` 行备注更新：重试/熔断/路由/usage 账本；**不新增**一级模块；新表 `ops_llm_usage` 入备注） |

### 人工闸（SPEC 阶段）

| human_gate_id | status | 说明 |
|---|---|---|
| **HG-SPEC-SIGNOFF** | **pending** | 维护者签收本 SPEC 后方可 00 出 task / 30 改码（人签，不由 10-spec 代签） |

---

## 1. 背景与目标

### 现状（2026-09-21 实扫）

| 能力 | 状态 | 锚点 |
|---|---|---|
| provider 抽象 + 工厂 | ✅ | `app/llm/factory.py::get_llm_provider`（`siliconflow` / `bailian` 字典）· `app/llm/schema.py::BaseProvider` |
| 显式四段超时 | ✅ | `app/llm/providers/base.py:94` `httpx.Timeout(connect=10, read=180, write=30, pool=5)` |
| fallback 链 | ⚠️ **有链无退避** | `app/llm/providers/bailian.py::complete_stream`（仅 bailian 有链 · 可重试错误**立即**换下一模型 · 无 backoff/jitter）；siliconflow `get_fallback_chain` 返回 `[]` |
| 错误可重试性分类 | ✅（未消费） | `app/llm/schema.py::LlmProviderError(retryable, status_code)`；`base.py::_raise_for_status`：408/429/5xx → `retryable=True`；`httpx.RequestError` → `retryable=True`；4xx 其余 → `False` |
| 结构化输出（parse/repair/validate + correction 重试 ≤3） | ✅ | `app/ops/structured_output/complete.py`（输出语义纠偏，**与传输重试正交**，本 SPEC 不改） |
| 熔断 | ❌ 模型层无 | 先例：`app/ops/capability/circuit.py`（pybreaker · 三态 · exclude 业务错误 · `throw_new_error_on_trip=False` · FallbackStorage） |
| 分层路由 | ⚠️ 仅 grader 单点 | `app/ops/chat/rag_nodes.py:33` `GRADER_MODEL`（env `RAG_GRADER_MODEL` 默认 `Qwen/Qwen3.6-27B`）；answer 走 `settings.ops_llm_model` 单模型；**无任务类型/成本档概念** |
| usage 观测 | ⚠️ 仅 Langfuse（可选、默认关） | `app/ops/tracing.py::update_current_generation_usage`；`base.py::_report_complete_usage`（tracing 关则静默 no-op） |
| 成本归集 | ❌ 离线人工导出 | `evals/agent/cost/export_cost.py` + `price_table_v1.yaml`（占位价）；GUIDE：`docs/spec/agent-infra/eval/GUIDE_token_cost_ledger_v0.md`（Langfuse 非账单 SoT；**禁止 LLM 估费**）；DB 无 usage 表 |

### 痛点

1. **无退避重试**：可重试错误（429/5xx/传输错）要么立即换模型（bailian）、要么直接失败（siliconflow / grader / 抽取）——瞬时故障被放大为 run 失败，或对挣扎中的下游零缓冲连打。
2. **无熔断**：provider 连续故障时每个请求都再付一次完整 read 超时（180s 上限）才知道它还挂着——慢且放大下游负载（capability `circuit.py` 序言已论证同一问题）。
3. **无分层路由**：grader 与生成同档混用靠人肉 env，成本/质量档不可按任务类型声明与演进。
4. **成本黑盒**：usage 只在 Langfuse（可关），DB 无按 run 聚合的账本——「这个 run 花了多少 token/钱」答不出；手册 L5/L8 联动缺口。

### 一句话目标

在 **provider 抽象 / fallback 链 / 结构化输出语义一行不改** 的前提下，给 L5 补四块承重墙：**① 通用重试（指数退避+抖动 · 仅可重试错误类）② provider 级熔断（复用 pybreaker + capability 模式）③ 任务类型分层路由（grader/生成分档）④ usage 按 run_id 聚合落表**，全部默认安全、可关、可观测，且**故障不得返回半成功数据**。

设计纪律（签收时锁死）：

1. **分类靠结构不靠文案**：可重试判定只认 `LlmProviderError.retryable` / `status_code`（对齐 `capability/errors.py::is_environmental_failure` 的结构化 cause 思想），禁止解析错误字符串。
2. **流式纪律**：已开始吐 token 后**禁止**重试/换模型（否则重复正文）；重试与熔断重入只发生在首 content chunk 之前。
3. **观测不挡主答**：usage 落表失败 = log + 计数，不拖垮回答；但**不得静默声称已记账**（状态须可从运行观测读出）。
4. **成本公式不变**：`cost = usage × Host 价表`（占位价 · E5 既有公式沿用）；本 SPEC 只解决 usage 落表与按 run 聚合，不改价表、不做对账 UI。

---

## 2. 范围

### D1 · 通用重试：指数退避 + 抖动（必做）

| 项 | 约定 |
|---|---|
| 判据 | 仅 `LlmProviderError` 且 `retryable=True`（408/429/5xx/传输错/SSE 解析错——`base.py` 既有分类）；其余异常（含 `retryable=False` 的 4xx、`ValueError` 缺 key）**零重试** |
| 算法 | 指数退避 + full jitter：`delay_i = random(0, min(cap, base × 2^i))`；默认 `base=0.5s · cap=8s · max_attempts=3`（env 可调，非法值回退默认 + warning，对齐 `grader_prompt_version` 模式） |
| env | `OPS_LLM_RETRY_ENABLED=true`（默认开）· `OPS_LLM_RETRY_MAX_ATTEMPTS` · `OPS_LLM_RETRY_BASE_DELAY_S` · `OPS_LLM_RETRY_MAX_DELAY_S` |
| 施加面 | `BaseProviderImpl` 的 complete/stream 边界统一包一层（对所有 provider 生效）；**bailian fallback 链内每个候选也走同一重试层**（先同模型退避重试、再换模型），链语义/顺序不变 |
| 流式纪律 | 重试只允许发生在**首 content chunk yield 之前**；已开始产出正文后出错 → 不重试，向上抛，由调用方走既有 error 事件路径（`chat/nodes.py:229-237`） |
| 观测 | span/log 记 `llm_retry{attempt=i, delay=…, provider, model}`；重试耗尽抛**原始** `LlmProviderError`（不包装丢根因） |

### D2 · 熔断：provider 级（必做）

| 项 | 约定 |
|---|---|
| 复用 | `pybreaker`（已在 `requirements.txt`）+ `capability/circuit.py` 已验证模式：`with breaker.calling():`（asyncio 可用）、`exclude` 回调剔除业务错误、`throw_new_error_on_trip=False` 保留根因、测试 hook（reset/trip/advance）不 sleep |
| 粒度 | **provider 级**（`siliconflow` / `bailian` 各一个 breaker）——不按模型熔：同 provider 换模型是 fallback 链自己的职责，双状态机会互相打架 |
| 计失败 | 仅环境类失败计数 = `LlmProviderError.retryable=True`（对齐 `errors.py::is_environmental_failure`「不响应/5xx/429 才算下游不健康」）；业务类（4xx 其余、本地装配错）**不计数** |
| 参数 | 默认 `fail_max=5 · reset_timeout=60s · success_threshold=1`（与 capability 默认一致）；env `OPS_LLM_CB_ENABLED=true` / `OPS_LLM_CB_FAIL_MAX` / `OPS_LLM_CB_RESET_TIMEOUT` |
| 与重试叠序 | 熔断 guard 包在重试层**外**：open 时零出网立即失败；重试在 guard 内发生并计入失败 |
| open 翻译 | 熔断中调用 → 明确的 `circuit_open` 错误（类 `CircuitOpen` 模式），调用方转 error 事件（`retryable=False`）；**不得返回半成功 answer** |
| 观测 | snapshot 函数（对齐 `circuit.py::snapshot`）：state / fail_counter / seconds_until_half_open / blocked_calls，供 /runtime 类观测面挂载；多副本共享存储（Redis）本波沿用进程内，storage 接口留位不实现 |

### D3 · 分层路由：任务类型 → 模型档（必做）

| 项 | 约定 |
|---|---|
| 任务类型 | `answer`（生成档）· `grader`（评级档 · 现 `RAG_GRADER_MODEL` 先例）· `extract`（记忆抽取档）· `structured`（结构化输出节点档）；档位表在 `app/llm/` 侧声明（如 `model_catalog` 扩展 `TASK_TIER_MODELS`） |
| 解析序 | 调用方显式 `model=` > env 档覆盖（`OPS_LLM_TIER_<TASK>_MODEL`）> 档默认 > `settings.ops_llm_model`；非法档/未知 task 回退默认 + warning |
| 兼容 | `RAG_GRADER_MODEL` 既有 env 继续生效（并入 grader 档覆盖链，不破坏现网配置）；不显式分档的调用点行为 = 现网逐字节一致 |
| 调用点改造 | `chat/rag_nodes.py`（grader）· `memory/extract.py`（extract）· `structured_output/complete.py`（structured）· answer 路径，改为声明 task 类型而非裸传模型 |
| 观测 | 路由决策（task → provider/model/档来源）写 span metadata，并随 D4 usage 行落 `task_type` 列 |

### D4 · 成本归集：usage 按 run_id 聚合落表（必做）

| 项 | 约定 |
|---|---|
| 新表 | `ops_llm_usage`：`id` · `run_id text null` · `surface text`（`chat`/`lg_rag`/`background`）· `task_type text` · `provider text` · `model text` · `prompt_tokens int` · `completion_tokens int` · `cached_input_tokens int` · `attempts int` · `created_at`；索引 `(run_id)`、`(surface, created_at)` |
| run_id 口径 | chat = `ops_runs.id`（UUID · `chat/streaming.py:58-61`）；lg_rag = `uuid4().hex`（`lg_rag/router.py:231,296`）；两口径并存故 `run_id` 用 text + `surface` 区分，**不设 FK**；后台抽取带其 `source_run_id` |
| 上下文传递 | run 上下文（run_id/surface/task_type）经 **ContextVar** 由入口点（chat streaming、lg_rag router、memory 抽取、grader 节点）注入；provider 层 `_report_complete_usage` 同点消费——不改 `complete/complete_stream` 签名 |
| 写入点 | `BaseProviderImpl` usage 上报处（现 lazy-import tracing 的同一钩点）追加落表；tracing 关也落表（落表不依赖 Langfuse）；无 usage 末帧 → 无行，**不写 0 假账** |
| 成本 | 表内只存 tokens；`cost_est` 由查询/导出侧 × `price_table_v1.yaml` 计算（占位价 · E5 公式 `input×input价 + cached×cache价 + output×output价` 每 1M）；价表缺行 → `price_missing` 空值，不算假价 |
| 失败语义 | 落表异常 → log + 计数（运行观测可见），**不挡主答**；embed/rerank 无标准 usage 字段 → 本波不记账（GUIDE 已知缺口，非范围） |
| 迁移 | **alembic migration 必交**（upgrade/downgrade 可逆）；`app/db/models.py` 增模型类 |

### D5 · 图谱与文档（必做）

- `docs/_tech_graph/l1/01_modules.md` `llm` 行备注更新（重试退避 / provider 熔断 / 分档路由 / `ops_llm_usage` 账本；依赖出边 + `db`）——**不新增一级模块**，但须维护者签 HG-GRAPH-MODULES 新行（仓规：新增表须同步图谱，G-L1 层表述）
- `app/llm/README.md`（无则建）增四块机制说明 + env 表；新表在图谱数据层备注登记
- `./scripts/graph-compile.sh` 绿

---

## 3. 非范围

- ❌ 新 provider 接入（占位草案原文保留）
- ❌ 改结构化输出语义（parse/repair/validate/correction 重试 ≤3 不动 · 占位草案原文保留）
- ❌ 流式协议改动（SSE 事件类型 / 帧格式 / `model.fallback` 语义不变 · 占位草案原文保留）
- ❌ 改 fallback 链内容 / 顺序 / test_only 过滤（`BAILIAN_FALLBACK_CHAIN` 是现网配置）
- ❌ 成本对账 UI / HTTP 查询端点 / 预算闸（budget 是 capability 层既有机制，不扩展到 LLM）
- ❌ 多副本熔断共享存储（Redis state storage 留位不实现；capability `circuit_storage.py` 为将来先例）
- ❌ embed / rerank 的 usage 记账（无标准 usage 字段，GUIDE §3.2 已知缺口）
- ❌ 价表更新 / 真实商务价格（占位价沿用，手册 L8 联动另行）
- ❌ web / ios

---

## 4. 方案对比（R2）

### 重试层

| 方案 | 做法 | 收益 | 代价 | 裁决 |
|---|---|---|---|---|
| **S1 · 自实现薄重试层（本 SPEC）** | `BaseProviderImpl` 内 ~50 行 helper，消费既有 `LlmProviderError.retryable` | 零新依赖；流式「首 chunk 前才可重试」纪律可精确表达；与熔断/usage 钩点同层 | 需自写退避+jitter（算法 trivial） | **推荐** |
| S2 · 引入 tenacity | `@retry` 装饰 complete/stream | 成熟库 | 仓内无此依赖（`requirements.txt` 无 tenacity）；对 async generator 的「流中禁重试」表达别扭（需额外包一层判定）；为 ~50 行逻辑引依赖不值 | 弃 |

### 熔断层

| 方案 | 做法 | 收益 | 代价 | 裁决 |
|---|---|---|---|---|
| **S1 · 复用 pybreaker + capability 模式（本 SPEC）** | provider 级 breaker；`calling()` + `exclude` + `throw_new_error_on_trip=False` | pybreaker 已在仓且 `circuit.py` 有三个实测结论（Tornado-only 坑 / exclude 用法 / 根因保留）可直接移植；测试 hook（advance 拨时间不 sleep）现成模式 | 需另写一层薄封装翻译 `circuit_open` | **推荐** |
| S2 · 自研三态状态机 | 手写 open/half-open/closed | 无外部语义 | 重造轮子且易错（`circuit.py` 序言：状态机交给 pybreaker 正是为了「不存在状态机漏跑」）；半开探测并发语义自研高风险 | 弃 |

### 成本存储

| 方案 | 做法 | 收益 | 代价 | 裁决 |
|---|---|---|---|---|
| **S1 · 新表 `ops_llm_usage`（本 SPEC）** | ContextVar 传 run 上下文，provider 钩点落表 | 覆盖 chat + lg_rag 两种 run_id 口径（UUID vs hex text · 无共同 FK 可挂）；落表不依赖 Langfuse 开关 | 一次 alembic migration | **推荐** |
| S2 · 复用 `ops_runs` 加列 | run 行上挂 usage 汇总 | 零新表 | `ops_runs` 是 chat 专属（lg_rag run 无此行）；多次 LLM 调用/run（answer+grader+extract）挤一行丢 task 维度 | 弃 |
| S3 · 仅 Langfuse 不落地 | 维持现状 | 零开发 | Langfuse 可关且非账单 SoT（GUIDE 钉死）；「按 run 查成本」仍答不出——正是本 SPEC 要补的洞 | 弃 |

### 路由档存放

| 方案 | 做法 | 收益 | 代价 | 裁决 |
|---|---|---|---|---|
| **S1 · 代码档表 + env 覆盖（本 SPEC）** | `model_catalog` 扩展 `TASK_TIER_MODELS` + `OPS_LLM_TIER_*` | 对齐 `RAG_GRADER_MODEL` / `RAG_GRADER_PROMPT` 既有先例；变更走 PR 可审 | 改档要发版（env 覆盖可热调对冲） | **推荐** |
| S2 · DB 驱动路由表 | 路由配置入库 | 热改 | 新管理面 + 新失败模式（DB 挂 → 选不出模型）；量级不符 | 弃 |

---

## 5. 边界 / 失败路径 / 安全（failure_paths）

| 触发 | 行为 | 可重试 |
|---|---|---|
| 429 / 5xx / 传输错 / SSE 解析错（`retryable=True`） | 指数退避+抖动重试 ≤ max_attempts；bailian 链内先同模型重试再换下一模型 | Y（自动） |
| 4xx 其余 / 缺 API key / `retryable=False` | **零重试**，原样上抛 | — |
| 流中已吐首 content chunk 后出错 | **零重试零换模型**，上抛走 error 事件；已吐正文不重复不拼接（半成功数据以 error 事件显式终结，不得静默当成功 answer 收尾） | — |
| 重试耗尽 | 抛**原始** `LlmProviderError`（不包装丢根因）；调用方走既有 error 事件路径 | — |
| provider 连续 `fail_max` 次环境失败 | breaker open → 后续调用**零出网**立即 `circuit_open` 错误事件；不误伤业务错误（不计数） | Y（reset_timeout 后自动探测） |
| 熔断 open 拦截 | 错误翻译保留根因（`throw_new_error_on_trip=False`）；error 事件 `retryable=False`，**不得返回半成功 answer** | — |
| 业务错误风暴（用户参数错 × N） | `exclude` 判定不计失败，breaker 保持 closed（对齐「用户填错 5 次参数不能把能力停 60s」） | — |
| 重试+熔断叠加等待膨胀 | 单请求总等待有界 = attempts × (max_delay + read timeout)；CI 断言 fake 时钟下重试间隔序列符合界 | — |
| 路由档指向不存在/未配置模型 | 回退档默认 → `settings.ops_llm_model`，log warning（对齐 `grader_prompt_version` 非法值回退模式）；不炸请求 | — |
| usage 落表异常（DB 故障 / migration 未跑） | log + 计数 + snapshot 可见，**不挡主答**；不得静默声称已记账 | Y（下一 run） |
| provider 未回 usage 末帧 | **不写 0 假账**（无行）；观测侧沿用 `usage_missing` 语义 | — |
| 价表缺行（查询/导出侧） | `cost_est` 空 + `price_missing`，不算假价（E5 语义沿用） | — |
| run 上下文缺失（无 ContextVar 的调用点） | usage 行 `run_id=NULL · surface=background`，不阻断记账 | — |
| 新 env 非法值 | 回退默认 + warning（全 env 统一纪律） | — |
| 全部新开关关闭 | 行为 = 现网逐字节一致（重试/熔断可关；路由未声明档 = 现网模型解析序） | — |

安全：本 SPEC 不引入新密钥/凭证面；usage 行只存 token 计数与模型名，**不存** prompt/answer 正文（正文 I/O 仍在 Langfuse 侧、可关、截断 4000 字——`tracing.py` 既有纪律）。

---

## 6. 验收标准

### D1 · 重试

- [ ] fake provider 连续抛 `httpx.RequestError`（→ `retryable=True`）：断言重试次数 = `OPS_LLM_RETRY_MAX_ATTEMPTS`，且 monkeypatch 的 sleep 序列满足 `delay_i ≤ min(cap, base×2^i)`（jitter 下界 ≥0）——**不假 sleep**
- [ ] fake provider 抛 400（`retryable=False`）：断言**零重试**（provider 调用计数 = 1）
- [ ] fake stream 已 yield 一个 content chunk 后抛错：断言零重试，调用方收到 error 事件且无重复正文
- [ ] bailian 链：首个候选可重试失败 → 先退避重试该候选，再发 `model.fallback` 换下一候选（链顺序与事件语义不变）
- [ ] `OPS_LLM_RETRY_ENABLED=false`：行为与现网逐字节一致

### D2 · 熔断

- [ ] fake provider 连续 `fail_max` 次环境失败 → breaker open；随后调用**零出网**（fake httpx 断言无新请求）且 error 事件含 `circuit_open`
- [ ] 用 advance 式 hook 拨动 opened_at（**不真等 60s**）→ 下一次调用放行探测，成功 → closed，失败 → open
- [ ] 业务类错误（`retryable=False`）× fail_max 次：breaker 保持 closed（不计数）
- [ ] 跳闸那一次错误根因保留（非 `CircuitBreakerError` 替换）
- [ ] snapshot 输出 state / fail_counter / seconds_until_half_open / blocked_calls 可断言

### D3 · 路由

- [ ] grader 调用点声明 `task_type=grader` → 命中 grader 档模型；`OPS_LLM_TIER_GRADER_MODEL` 覆盖生效；既有 `RAG_GRADER_MODEL` 配置不破坏（并入覆盖链）
- [ ] answer / extract / structured 各档独立解析；未知 task 或非法档回退默认 + warning
- [ ] 不显式分档的既有调用点：模型解析结果与现网逐字节一致
- [ ] span metadata 含 task → model 决策与档来源

### D4 · 成本归集

- [ ] 一次 chat run（answer + grader 两次 LLM 调用、fake usage 末帧）→ `ops_llm_usage` 两行同 `run_id`、`task_type` 分别为 `answer`/`grader`、tokens 与 fake 值一致；按 `run_id` 聚合查询返回合计
- [ ] lg_rag run（hex run_id）落行 `surface=lg_rag`，与 chat 行可区分查询
- [ ] provider 无 usage 末帧 → 无行（**非 0 假账**）
- [ ] 落表路径抛错（fake session 故障）→ answer 正常返回 + log/计数断言（不挡主答）
- [ ] alembic upgrade/downgrade 可逆（表可增可删）

### 工程

- [ ] ruff + pytest 绿（本波新测 + `tests/test_llm_providers.py` / `tests/test_chat_nodes.py` / memory 抽取回归）
- [ ] 图谱 `llm` 行备注更新 + HG-GRAPH-MODULES 新签 + `graph-compile.sh` 绿
- [ ] 新 env 非法值回退 + warning 全覆盖
- [ ] 变异检验：把重试判据改成「全部错误都重试」一次，确认 D1 的 4xx 零重试断言真会 fail（不验收空真规则）

---

## 7. 思考轮控制（10-spec）

| 轮 | 结论摘要 | 状态 |
|---|---|---|
| R0 | 上游手册 L5（§393-396 + 附录 A 511 行）钉死缺口：有链无退避 · 缺熔断 · 缺路由 · 成本未按 run 聚合；承重墙缺角（静默失败带错数据往下走） | done |
| R1 | 范围 = D1 重试 / D2 熔断 / D3 路由 / D4 成本落表 / D5 图谱文档；非范围 = 新 provider / 结构化输出语义 / 流式协议 / fallback 链内容 / 对账 UI / Redis 共享存储 / embed·rerank 记账 | done |
| R2 | 四组对比各 ≥2：重试选自实现薄层（弃 tenacity：仓内无依赖 + 流式纪律难表达）；熔断选 pybreaker 复用（弃自研状态机）；存储选新表（弃 ops_runs 加列 / 仅 Langfuse）；路由选代码档表+env（弃 DB 驱动） | done |
| R3 | failure_paths 14 条，核心三条：流中禁重试（防重复正文）、业务错误不计熔断（防误熔）、落表故障不挡主答但不静默（可观测）；run_id 双口径（UUID/hex）→ text+surface 无 FK | done |
| R4 | 验收全为可执行否定性断言：重试次数/延迟界、零重试反向断言、熔断三态拨时间不 sleep、按 run_id 聚合、无 0 假账；含变异检验一条 | done |
| R5 | SPEC draft-complete 可交人签 HG-SPEC-SIGNOFF；签后 00 出 task（建议单 task 四块同波，D1–D2 先于 D3–D4 提交） | done |
| early_stop | no | — |
| residual_risks | ① 重试默认参数（base 0.5s/cap 8s/3 次）未经真实流量校准，上线后按观测调；② ContextVar 注入点在 lg_rag supervisor 多节点并发下需 30 阶段逐点核验（并发子任务 run 上下文串扰风险）；③ 占位价表与真实账单偏差仍由手册 L8 另行解决 | 签收时知悉 |

---

## 8. 下一棒

1. **维护者**：审本 SPEC → 签 `HG-SPEC-SIGNOFF=approved`
2. **00**：起草 `docs/tasks/active/task_llm_layer_hardening.md`（范围 D1–D5 · 人工闸表含 HG-GRAPH-MODULES）
3. **20-task-audit**：书面审 → 维护者签 `HG-AUDIT-R1` + 图谱 `llm` 行新签
4. **30**：`task/llm-layer-hardening` 分支实现 D1–D5
5. **40**：验收 → PR（与 memory-facts-p0/p1 同模式）

### 下一棒可复制 Prompt（20-spec-audit 预审 / 00 起草 task）

```text
你是 ops-desk-api 仓（/Users/cyning/Desktop/Ops-desk/ops-desk-api）的 <20-spec-audit ｜ 00>。
SPEC：docs/spec/llm-layer-hardening/SPEC-llm-layer-hardening_v1.md（draft-complete · HG-SPEC-SIGNOFF=pending）。
<20-spec-audit>：书面审范围/非范围/验收/failure_paths 与 R0–R5 思考轮，结论落盘 docs/harness/reviews/，不代签人闸。
<00>：待维护者签 HG-SPEC-SIGNOFF=approved 后，按 SPEC §8 起草 docs/tasks/active/task_llm_layer_hardening.md（D1–D5 · failure_paths 沿用 SPEC §5 · 人工闸表含 HG-GRAPH-MODULES）。
```

---

## 修订

| 日期 | 说明 |
|---|---|
| 2026-09-21 | 占位稿（范围草案 + 锚点 + 验收方向 + 接续指引） |
| 2026-09-21 | 10-spec 补全：实扫 `app/llm/` / `capability/circuit.py` / `errors.py` / `tracing.py` / `evals/agent/cost/` 锚点落地；四块范围断言化验收；R0–R5 回填；方案对比四组；failure_paths 14 条；track 裁定 `feature`；HG-SPEC-SIGNOFF 保持 pending 待人签 |
