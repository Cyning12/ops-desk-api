# Task：L5 模型层硬化（重试 / 熔断 / 分层路由 / 成本归集）

> **状态**：`signed`（2026-09-21 · 20-task-audit R2 PASS-with-notes 零阻塞 · HG-AUDIT-R1=approved（维护者授权 00 代录）· 可 30）  
> **类型**：feature / L5 模型层 · 承重墙缺角补齐（含新表 → 带 alembic migration 与图谱同步义务）  
> **上游 SPEC**：`docs/spec/llm-layer-hardening/SPEC-llm-layer-hardening_v1.md`（**signed** · HG-SPEC-SIGNOFF=approved 2026-09-21）  
> **分支**：`task/llm-layer-hardening`（**禁止 master 直改**）  
> **10 注**：2026-09-21 · 维护者授权「00 签收所有过程文档，接续 llm-layer-hardening」· HG-AUDIT-R1 由 00 在该授权下于 20 审后代录，**本帽不签**

---

## Harness 元信息

| 字段 | 值 |
|------|-----|
| **task_slug** | `llm-layer-hardening` |
| **git_branch** | `task/llm-layer-hardening` |
| **implement_repo** | `ops-desk-api` |
| **test_strategy** | `required` |
| **test_strategy_note** | 单测：fake provider / fake httpx 注入各类错误——可重试错误退避重试、不可重试零重试、流中已吐 token 后零重试；熔断三态转换用 advance 式时间拨动 hook 不 sleep；路由分档断言 + 非法档回退；usage 落表按 run_id 聚合 + 落表故障不挡主答；全波次回归 `tests/test_llm_providers.py` `tests/test_chat_nodes.py` |
| **code_quality_bar** | `L2_backend` |
| **graph_change_layer** | `G-L1` |
| **graph_delta** | `docs/_tech_graph/l1/01_modules.md`（`llm` 行备注：重试退避 / provider 熔断 / 分档路由 / `ops_llm_usage` 账本 · 依赖出边 +`db`） |
| **graph_delta_note** | **不新增**一级模块；`llm` 行备注更新 + 新表登记须维护者签 HG-GRAPH-MODULES 新行（00 代录，随 30 交付落盘） |
| **wiki_delta** | `n/a` |
| **wiki_delta_note** | 契约真值在 SPEC `llm-layer-hardening` |
| **review_hat** | `20` |
| **required_invoke_hats** | `10,20,30,40` |
| **invoke_retention_profile** | `default` |
| **experience_capture** | `recommended` |
| **kpi_aggregator** | `CLOSE` |
| **orchestration** | 10 落稿 → 20-task-audit → 维护者授权 00 代录闸 → 30（建议 D1–D2 先于 D3–D4 提交）→ 40 → CLOSE |
| **freeze_id** | 无（不改 `lg-rag-sse-v1` / `lg-rag-http-v1` / `lc-evidence-http-v1`） |

### 人工闸

| human_gate_id | status | blocks_hats | 说明 |
|---------------|--------|-------------|------|
| HG-TASK-DRAFT | **approved** | 20-R1, 30 | 2026-09-21 · 00 验收 10-task 稿（含 R1 退回修订 B1）通过 · 维护者本窗授权 00 签收过程文档（原话「授权00签收所有过程文档，接续 llm-layer-hardening」） |
| HG-AUDIT-R1 | **approved** | **30** | 2026-09-21 · 20-task-audit R2 终轮 PASS-with-notes 零阻塞（`docs/harness/reviews/task_llm_layer_hardening_audit_R2_20260921.md`）· 维护者本窗授权 00 代录签收 |
| HG-GRAPH-MODULES | **approved** | **30** | 2026-09-21 核验 `docs/_tech_graph/l1/01_modules.md`：模块表已建置（bootstrap 签 2026-07-16 · `llm` 行在表 · 2026-09-21 当日三行签录：memory_facts_p1 / memory_facts_p0 / tech_graph_recent_sync）；**注意**：本 task D5 的 `llm` 行备注更新仍须维护者签新行（00 代录），义务留在验收标准 |
| HG-PILOT-OPSDESK-GLAYER | n/a | 物理分层试点改码 | 本 task 不涉物理分层试点 |

---

## 背景与目标

L5 模型层现状（SPEC §1 实扫）：provider 抽象 + 四段超时 + 错误可重试性分类已备，但 **有链无退避**（bailian 可重试错误立即换模型、siliconflow 无链）、**无熔断**（下游挂起每请求再付一次 180s read 超时上限）、**无分层路由**（grader 靠人肉 env）、**成本黑盒**（usage 仅在可关的 Langfuse，DB 无按 run 聚合账本）。

一句话目标（SPEC 锁死）：在 **provider 抽象 / fallback 链 / 结构化输出语义一行不改** 的前提下，给 L5 补四块承重墙——**① 通用重试（指数退避+抖动 · 仅可重试错误类）② provider 级熔断（复用 pybreaker + capability 模式）③ 任务类型分层路由 ④ usage 按 run_id 聚合落表**，全部默认安全、可关、可观测，且 **故障不得返回半成功数据**。

设计纪律（30 不得违反）：

1. **分类靠结构不靠文案**：可重试判定只认 `LlmProviderError.retryable` / `status_code`，禁止解析错误字符串。
2. **流式纪律**：已开始吐 token 后 **禁止** 重试/换模型；重试与熔断重入只发生在首 content chunk 之前。
3. **观测不挡主答**：usage 落表失败 = log + 计数，不拖垮回答；但不得静默声称已记账。
4. **成本公式不变**：`cost = usage × Host 价表`（占位价 · E5 公式沿用）；本 task 只解决 usage 落表与按 run 聚合。

---

## 现状锚点（只读 · 30 必读 · 10 已扫 · 承 SPEC §1）

| 主题 | 路径 · 锚点 | 现状缺口 |
|------|-------------|----------|
| provider 抽象/工厂 | `app/llm/factory.py::get_llm_provider` · `app/llm/schema.py::BaseProvider` | 抽象已备，本波不改 |
| 超时 | `app/llm/providers/base.py:94` `httpx.Timeout(connect=10, read=180, write=30, pool=5)` | 已备 |
| fallback 链 | `app/llm/providers/bailian.py::complete_stream` · `app/llm/model_catalog.py:101-105::get_fallback_chain` | **有链无退避**；`get_fallback_chain("siliconflow")` 返回 `[]`（函数实址在 `model_catalog.py`，siliconflow.py 内无此函数） |
| 错误分类 | `app/llm/schema.py::LlmProviderError(retryable, status_code)` · `base.py::_raise_for_status` | 分类已备未消费（408/429/5xx/传输错 → retryable=True） |
| 结构化输出 | `app/ops/structured_output/complete.py`（correction 重试 ≤3） | 语义纠偏与传输重试正交，**本波不改** |
| 熔断先例 | `app/ops/capability/circuit.py`（pybreaker · 三态 · exclude 业务错误 · `throw_new_error_on_trip=False`） | 模型层无熔断，模式可移植 |
| 路由先例 | `app/ops/chat/rag_nodes.py:33` `GRADER_MODEL`（env `RAG_GRADER_MODEL`） | 仅 grader 单点，无任务类型/成本档 |
| usage 观测 | `app/ops/tracing.py::update_current_generation_usage` · `base.py::_report_complete_usage` | 仅 Langfuse（可关），DB 无表 |
| 成本公式 | `evals/agent/cost/export_cost.py` + `price_table_v1.yaml`（占位价）· GUIDE `docs/spec/agent-infra/eval/GUIDE_token_cost_ledger_v0.md` | Langfuse 非账单 SoT · 禁止 LLM 估费 |
| run_id 口径 | chat = `ops_runs.id` UUID（`chat/streaming.py:58-61`）；lg_rag = `uuid4().hex`（`lg_rag/router.py:231,296`） | 双口径并存 → text + surface · 无 FK |
| P1 测试基线 | `tests/test_llm_providers.py` · `tests/test_chat_nodes.py` | **全绿是本波回归底线** |

---

## 钉死契约（自 SPEC §1/§2 锁死；30 不得静默改义）

| 项 | 钉死 |
|----|------|
| **重试判据** | 仅 `LlmProviderError` 且 `retryable=True`；其余异常（含 `retryable=False` 的 4xx、缺 key `ValueError`）**零重试** |
| **退避算法** | `delay_i = random(0, min(cap, base × 2^i))`；默认 `base=0.5s · cap=8s · max_attempts=3`；env 可调，非法值回退默认 + warning |
| **重试 env** | `OPS_LLM_RETRY_ENABLED=true`（默认开）· `OPS_LLM_RETRY_MAX_ATTEMPTS` · `OPS_LLM_RETRY_BASE_DELAY_S` · `OPS_LLM_RETRY_MAX_DELAY_S` |
| **施加面** | `BaseProviderImpl` complete/stream 边界统一包一层；bailian 链内每个候选走同一重试层（先同模型退避重试、再换模型）；链语义/顺序/test_only 过滤不变 |
| **流式纪律** | 重试只允许在首 content chunk yield 之前；已吐正文后出错 → 零重试零换模型，上抛走既有 error 事件（`chat/nodes.py:229-237`） |
| **重试耗尽** | 抛**原始** `LlmProviderError`（不包装丢根因）；span/log 记 `llm_retry{attempt, delay, provider, model}` |
| **熔断复用** | pybreaker（已在 requirements.txt）+ capability `circuit.py` 模式：`calling()` · `exclude` 剔除业务错误 · `throw_new_error_on_trip=False` · 测试 hook（reset/trip/advance）不 sleep |
| **熔断粒度** | **provider 级**（siliconflow / bailian 各一个 breaker）；不按模型熔 |
| **熔断计数** | 仅环境类失败计数 = `retryable=True`；业务类（4xx 其余、本地装配错）不计数 |
| **熔断参数** | 默认 `fail_max=5 · reset_timeout=60s · success_threshold=1`；env `OPS_LLM_CB_ENABLED=true` / `OPS_LLM_CB_FAIL_MAX` / `OPS_LLM_CB_RESET_TIMEOUT` |
| **叠序** | 熔断 guard 包在重试层**外**：open 时零出网立即失败；重试在 guard 内发生并计入失败 |
| **open 翻译** | `circuit_open` 错误（类 `CircuitOpen` 模式）→ error 事件 `retryable=False`；**不得返回半成功 answer** |
| **熔断观测** | snapshot（state / fail_counter / seconds_until_half_open / blocked_calls）供 /runtime 类观测面；Redis 共享存储留位不实现 |
| **路由任务类型** | `answer` / `grader` / `extract` / `structured`；档位表在 `app/llm/` 侧声明（`model_catalog` 扩展 `TASK_TIER_MODELS`） |
| **路由解析序** | 显式 `model=` > env 档覆盖 `OPS_LLM_TIER_<TASK>_MODEL` > 档默认 > `settings.ops_llm_model`；非法档/未知 task 回退默认 + warning |
| **路由兼容** | `RAG_GRADER_MODEL` 并入 grader 档覆盖链不破坏现网；不显式分档的调用点 = 现网逐字节一致 |
| **调用点改造** | `chat/rag_nodes.py`（grader）· `memory/extract.py`（extract）· `structured_output/complete.py`（structured）· answer 路径，声明 task 类型而非裸传模型 |
| **新表** | `ops_llm_usage`：`id` · `run_id text null` · `surface text` · `task_type text` · `provider text` · `model text` · `prompt_tokens int` · `completion_tokens int` · `cached_input_tokens int` · `attempts int` · `created_at`；索引 `(run_id)`、`(surface, created_at)` |
| **run_id 口径** | chat=UUID / lg_rag=hex 并存 → `run_id` 用 text + `surface` 区分，**不设 FK**；后台抽取带 `source_run_id` |
| **上下文传递** | run 上下文经 **ContextVar** 由入口点注入；provider 层 `_report_complete_usage` 同点消费——**不改 `complete/complete_stream` 签名** |
| **落表语义** | tracing 关也落表；无 usage 末帧 → 无行（**不写 0 假账**）；落表异常 → log + 计数，不挡主答，不静默声称已记账 |
| **成本** | 表内只存 tokens；`cost_est` 由查询/导出侧 × `price_table_v1.yaml`（占位价 · E5 公式）；价表缺行 → `price_missing` 空值 |
| **安全** | usage 行只存 token 计数与模型名，**不存** prompt/answer 正文；无新密钥/凭证面 |
| **env 纪律** | 全部新 env 非法值回退默认 + warning；全部新开关关闭 = 现网逐字节一致 |
| **SSE/HTTP** | 零改事件类型/帧格式/`model.fallback` 语义；无新对外端点 |

---

## 范围（同 task 竖切）

- [ ] **D1 · 通用重试**：`BaseProviderImpl` 边界统一重试层（指数退避 + full jitter · 仅 `retryable=True`）· bailian 链内逐候选接入 · 流式首 chunk 前限定 · 4 个 env + 非法回退
- [ ] **D2 · provider 级熔断**：pybreaker 复用 capability 模式 · 仅环境失败计数 · guard 包重试层外 · `circuit_open` 翻译保根因 · snapshot 观测 · 3 个 env
- [ ] **D3 · 分层路由**：`TASK_TIER_MODELS` 档表 + 解析序 + `RAG_GRADER_MODEL` 兼容 · 四个调用点改造（grader / extract / structured / answer）· 路由决策写 span metadata + usage 行 `task_type`
- [ ] **D4 · usage 落表**：`ops_llm_usage` 模型类 + alembic migration（upgrade/downgrade 可逆）· ContextVar 注入（chat streaming / lg_rag router / memory 抽取 / grader 节点）· provider 钩点落表 · 不挡主答
- [ ] **D5 · 图谱与文档**：`01_modules.md` `llm` 行备注更新 + HG-GRAPH-MODULES 新行（00 代录）· `app/llm/README.md`（无则建）四块机制 + env 表 · `graph-compile.sh` 绿

**竖切结论**：D1–D5 同 task 必交；建议 D1–D2 先于 D3–D4 提交（SPEC R5）；D5 随 30 一并。

### 非范围

- ❌ 新 provider 接入
- ❌ 改结构化输出语义（parse/repair/validate/correction 重试 ≤3 不动）
- ❌ 流式协议改动（SSE 事件类型 / 帧格式 / `model.fallback` 语义不变）
- ❌ 改 fallback 链内容 / 顺序 / test_only 过滤（`BAILIAN_FALLBACK_CHAIN` 是现网配置）
- ❌ 成本对账 UI / HTTP 查询端点 / 预算闸（budget 是 capability 层既有机制，不扩展到 LLM）
- ❌ 多副本熔断共享存储（Redis state storage 留位不实现）
- ❌ embed / rerank 的 usage 记账（无标准 usage 字段，GUIDE §3.2 已知缺口）
- ❌ 价表更新 / 真实商务价格（占位价沿用，手册 L8 联动另行）
- ❌ web / ios

---

## failure_paths

| 触发条件 | 系统行为 | 可重试 | 用户可见 |
|----------|----------|--------|----------|
| `HG-AUDIT-R1` pending 即 30 | **拒开工** | 是 | 是 |
| 429 / 5xx / 传输错 / SSE 解析错（`retryable=True`） | 指数退避+抖动重试 ≤ max_attempts；bailian 链内先同模型重试再换下一模型 | Y（自动） | 否 |
| 4xx 其余 / 缺 API key / `retryable=False` | **零重试**，原样上抛 | — | 否 |
| 流中已吐首 content chunk 后出错 | **零重试零换模型**，上抛走 error 事件；已吐正文不重复不拼接（半成功数据以 error 事件显式终结） | — | 是（error 事件） |
| 重试耗尽 | 抛**原始** `LlmProviderError`（不包装丢根因）；走既有 error 事件路径 | — | 是（error 事件） |
| provider 连续 `fail_max` 次环境失败 | breaker open → 后续调用**零出网**立即 `circuit_open` 错误事件；业务错误不计数 | Y（reset_timeout 后自动探测） | 是（error 事件） |
| 熔断 open 拦截 | 错误翻译保留根因（`throw_new_error_on_trip=False`）；`retryable=False`，不得返回半成功 answer | — | 是（error 事件） |
| 业务错误风暴（用户参数错 × N） | `exclude` 判定不计失败，breaker 保持 closed | — | 否 |
| 重试+熔断叠加等待膨胀 | 单请求总等待有界 = attempts × (max_delay + read timeout)；CI 断言 fake 时钟下重试间隔序列符合界 | — | 否 |
| 路由档指向不存在/未配置模型 | 回退档默认 → `settings.ops_llm_model`，log warning；不炸请求 | — | 否 |
| usage 落表异常（DB 故障 / migration 未跑） | log + 计数 + snapshot 可见，**不挡主答**；不得静默声称已记账 | Y（下一 run） | 否 |
| provider 未回 usage 末帧 | **不写 0 假账**（无行）；观测侧沿用 `usage_missing` 语义 | — | 否 |
| 价表缺行（查询/导出侧） | `cost_est` 空 + `price_missing`，不算假价（E5 语义沿用） | — | 否 |
| run 上下文缺失（无 ContextVar 的调用点） | usage 行 `run_id=NULL · surface=background`，不阻断记账 | — | 否 |
| 新 env 非法值 | 回退默认 + warning（全 env 统一纪律） | — | 否 |
| 全部新开关关闭 | 行为 = 现网逐字节一致 | — | 否 |
| 无变异检验却宣称重试判据有效 | 40/verify 拒收 | 是 | 否 |
| 30 开工前旧测影响面清单未落盘或逐条无处置 | 验收「工程 · 闸前置」项不满足 → 拒收（B1 · 20-task-audit R1 退回项） | 是 | 否 |

---

## 验收标准

- [ ] 人工闸：`HG-AUDIT-R1` approved 后方可勾选下列码项（HG-GRAPH-MODULES 模块表已建置 approved；D5 新签行随 30 落盘）

### D1 · 重试（映射 SPEC §6-D1）

- [ ] fake provider 连续抛 `httpx.RequestError`（→ `retryable=True`）：断言重试次数 = `OPS_LLM_RETRY_MAX_ATTEMPTS`，且 monkeypatch 的 sleep 序列满足 `delay_i ≤ min(cap, base×2^i)`（jitter 下界 ≥0）——**不假 sleep**
- [ ] fake provider 抛 400（`retryable=False`）：断言**零重试**（provider 调用计数 = 1）
- [ ] fake stream 已 yield 一个 content chunk 后抛错：断言零重试，调用方收到 error 事件且无重复正文
- [ ] bailian 链：首个候选可重试失败 → 先退避重试该候选，再发 `model.fallback` 换下一候选（链顺序与事件语义不变）
- [ ] `OPS_LLM_RETRY_ENABLED=false`：行为与现网逐字节一致

### D2 · 熔断（映射 SPEC §6-D2）

- [ ] fake provider 连续 `fail_max` 次环境失败 → breaker open；随后调用**零出网**（fake httpx 断言无新请求）且 error 事件含 `circuit_open`
- [ ] 用 advance 式 hook 拨动 opened_at（**不真等 60s**）→ 下一次调用放行探测，成功 → closed，失败 → open
- [ ] 业务类错误（`retryable=False`）× fail_max 次：breaker 保持 closed（不计数）
- [ ] 跳闸那一次错误根因保留（非 `CircuitBreakerError` 替换）
- [ ] snapshot 输出 state / fail_counter / seconds_until_half_open / blocked_calls 可断言

### D3 · 路由（映射 SPEC §6-D3）

- [ ] grader 调用点声明 `task_type=grader` → 命中 grader 档模型；`OPS_LLM_TIER_GRADER_MODEL` 覆盖生效；既有 `RAG_GRADER_MODEL` 配置不破坏（并入覆盖链）
- [ ] answer / extract / structured 各档独立解析；未知 task 或非法档回退默认 + warning
- [ ] 不显式分档的既有调用点：模型解析结果与现网逐字节一致
- [ ] span metadata 含 task → model 决策与档来源

### D4 · 成本归集（映射 SPEC §6-D4）

- [ ] 一次 chat run（answer + grader 两次 LLM 调用、fake usage 末帧）→ `ops_llm_usage` 两行同 `run_id`、`task_type` 分别为 `answer`/`grader`、tokens 与 fake 值一致；按 `run_id` 聚合查询返回合计
- [ ] lg_rag run（hex run_id）落行 `surface=lg_rag`，与 chat 行可区分查询
- [ ] provider 无 usage 末帧 → 无行（**非 0 假账**）
- [ ] 落表路径抛错（fake session 故障）→ answer 正常返回 + log/计数断言（不挡主答）
- [ ] alembic upgrade/downgrade 可逆（表可增可删）

### 工程（映射 SPEC §6-工程）

- [ ] **闸前置**：30 开工前旧测影响面清单已落盘且逐条有处置（回归/改编/删除理由）——清单见下「旧测影响面清单（B1）」，30 逐条执行处置并在提交说明逐条回填
- [ ] ruff + pytest 绿（本波新测 + `tests/test_llm_providers.py` / `tests/test_chat_nodes.py` / memory 抽取回归）
- [ ] 图谱 `llm` 行备注更新 + HG-GRAPH-MODULES 新签（00 代录）+ `graph-compile.sh` 绿
- [ ] 新 env 非法值回退 + warning 全覆盖
- [ ] 变异检验：把重试判据改成「全部错误都重试」一次，确认 D1 的 4xx 零重试断言真会 fail（不验收空真规则）

### 旧测影响面清单（B1 · 2026-09-21 10-task 实扫落盘 · 20-task-audit R1 退回项补列）

> 扫描口径（真跑）：`grep tests/` `complete_stream|\.complete(` · `LlmProviderError|retryable` · `get_llm_provider|FakeProvider|fake_provider` · `fallback|429|model\.fallback`；全仓 `grep get_fallback_chain` / `RAG_GRADER_MODEL`。行为变更源三处：重试默认开（`OPS_LLM_RETRY_ENABLED=true`）· 熔断默认开（`OPS_LLM_CB_ENABLED=true`）· grader 解析序改造（`RAG_GRADER_MODEL` 并入档覆盖链）。处置三态：**回归**（不受影响，全波次重跑确认）/ **改编**（随本波更新，理由在格内）/ **删除**（须附理由，本清单无）。

| # | 锚点 | 旧测/调用点现状 | 默认开重试/熔断后影响 | 处置 |
|---|------|----------------|----------------------|------|
| 1 | `tests/test_llm_providers.py::test_4xx_non_retryable`（253）· `test_missing_api_key`（246） | 4xx / 缺 key 即抛，断言 retryable=False / ValueError | 零重试判据保护 → 不受影响（既成 D1 零重试反向覆盖） | 回归 |
| 2 | `tests/test_llm_providers.py::test_retryable_errors`（265 · 429/500/503）· `test_sse_parse_error_retryable`（278）· `test_request_error_retryable`（289） | 可重试错误即抛并断言 retryable=True | 默认开重试后先退避至 max_attempts 再抛：终态断言仍成立，但真 sleep 拖慢、fake client 调用次数变 | **改编**：monkeypatch sleep/假时钟（或测内设 `OPS_LLM_RETRY_MAX_ATTEMPTS=1` 保旧语义）；错误分类断言保留 |
| 3 | `tests/test_llm_providers.py::test_fallback_emits_event`（374） | 首候选 503 → 立即 `model.fallback` 换 deepseek-v4-flash | 默认开重试后首候选先同模型退避重试至耗尽再换模型：call_log 中 `deepseek-v4-pro` 出现 max_attempts 次，事件语义/链序不变 | **改编**：假时钟下断言「重试耗尽 → fallback 事件仍恰一次 · from/to 不变」；链语义不断言调用次数=1 |
| 4 | `tests/test_llm_providers.py::test_fallback_chain_exhausted`（393） | 三候选全 503 → 抛 retryable=False「exhausted」 | 每候选先重试（共 3×max_attempts 次出网）终态不变 | **改编**：假时钟；终态断言（exhausted · retryable=False）保留 |
| 5 | `test_non_retryable_stops_fallback`（408）· `test_test_only_models_filtered`（422）· `test_explicit_model_skips_fallback`（436）· `test_complete_skips_fallback_meta`（496） | 401 即停链 / test_only 过滤 / 显式 model 跳过链 | 链语义、过滤、显式跳过均不涉重试触发 → 不受影响 | 回归 |
| 6 | `tests/test_chat_nodes.py::test_answer_node_handles_error`（191-208） | FailingProvider（**继承 BaseProviderImpl**）抛 retryable=True → error 事件 retryable=True | 重试层在 BaseProviderImpl 边界 → 默认开后 error 事件前经历 max_attempts 次重试；终态断言不变但真 sleep 拖慢 | **改编**：monkeypatch sleep/假时钟；终态断言（error · retryable=True）保留 |
| 7 | `tests/test_chat_nodes.py`（147/165 成功路径）· `tests/test_chat_ws.py`（23/46 FakeProvider 继承 BaseProviderImpl · 成功流） | 成功路径流式 | 成功不触发重试/熔断计数 → 不受影响 | 回归 |
| 8 | `tests/test_memory_extract_p1.py::test_extract_provider_error_zero_writes`（383-401） | 断言 `provider.calls == 1`（「不重试风暴」契约）；FakeProvider 继承 `BaseProvider` **非** BaseProviderImpl | 重试层不套 BaseProvider 抽象 → 理论上不受影响；但须防 30 误把重试层套上抽象层导致该测误红 | 回归（默认开下必须仍绿；红 = 30 施加面错了） |
| 9 | `tests/test_lg_rag_sse_token_stream.py`（45 `_FakeProvider(BaseProvider)`）· `test_lg_rag_retry.py`（17）· `test_lg_rag_router.py`（100/114）· `test_lg_rag_multi.py`（179/198） | patch `get_llm_provider` 的节点级异常 fallback（宁退化不失败） | 节点级 fallback 由节点自己实现，与传输重试正交 → 不受影响 | 回归 |
| 10 | 熔断全局态（新增 · 无旧测） | provider 级 breaker 为进程内单例 | 测试间串扰风险：上一测 trip 的 breaker 会污染下一测 | **改编（新测工程项）**：conftest 增 autouse reset fixture，对齐 `tests/conftest.py:194-203` capability `fallback.reset()` 先例；旧测回归确认无串扰 |
| 11 | `RAG_GRADER_MODEL` 消费点：`app/ops/chat/rag_nodes.py:32-33` · `app/ops/lg_rag/nodes.py:38` · `app/ops/lc_evidence_chain/grader.py:24,29` · `evals/golden/run_eval.py:38,656,685,708` | env 直读默认值 | tests/ 下 grep **零命中**（无旧测直接断言该 env）→ 无旧测改编；解析序改造须保既有 env 生效 | 回归（D3 新增兼容断言覆盖，见 D3 验收第 1 条） |
| 12 | usage 落表钩点：`app/llm/providers/base.py:31-34` `complete` 聚合路径触 `_report_complete_usage` 同点落表 | 旧测继承 BaseProviderImpl 的 fake 经 `complete()` 时会触钩点 | 无 ContextVar 时 `run_id=NULL · surface=background` 不阻断；落表异常不挡主答 | 回归（确认旧测在无 DB/未 migration 环境下不红；红 = 违反「不挡主答」契约） |

---

## 依赖

| 依赖 | 说明 |
|------|------|
| SPEC | `docs/spec/llm-layer-hardening/SPEC-llm-layer-hardening_v1.md`（signed · HG-SPEC-SIGNOFF=approved 2026-09-21） |
| 上游设计 | `../ops-desk-workspace/docs/08-interview/07_agent-memory-prompt-module-landscape_v1_zh.md` §L5（393–396 行）+ 附录 A L5 行（511 行） |
| 熔断先例 | `app/ops/capability/circuit.py` · `app/ops/capability/errors.py::is_environmental_failure`（pybreaker 三态 · exclude · 根因保留 · advance 测试 hook） |
| 成本 GUIDE | `docs/spec/agent-infra/eval/GUIDE_token_cost_ledger_v0.md` + `evals/agent/cost/price_table_v1.yaml`（占位价 · Langfuse 非账单 SoT） |
| 编码规范 | `docs/standards/CODING_BACKEND_L2_v1_zh.md` |
| 图谱 | `docs/_tech_graph/l1/01_modules.md`（HG-GRAPH-MODULES 真值） |
| 同模式先例 | `docs/tasks/done/task_memory_facts_p1.md`（含新表 + 图谱同步 + 00 代录闸的闭环模式） |

---

## 给执行帽的必读列表

1. `AGENTS.md`
2. 本 task（钉死契约 · 闸 · 非范围）
3. SPEC `docs/spec/llm-layer-hardening/SPEC-llm-layer-hardening_v1.md`
4. `docs/standards/CODING_BACKEND_L2_v1_zh.md`
5. 代码：`app/llm/**`（factory / schema / providers/base / bailian）· `app/ops/capability/circuit.py` + `errors.py` · `app/ops/tracing.py` · `app/ops/chat/rag_nodes.py` · `app/ops/chat/streaming.py` · `app/ops/memory/extract.py` · `app/ops/structured_output/complete.py` · `app/ops/lg_rag/router.py` · `evals/agent/cost/`
6. `docs/harness/prompts/FRAGMENT_30_gate_verify_v1_zh.md`

---

## 思考轮控制

| 轮 | 结论 | early_stop | reason（early_stop） | residual_risks |
|----|------|------------|----------------------|----------------|
| R0 | L5 四缺口钉死（有链无退避 / 无熔断 / 无路由 / 成本黑盒）；SPEC signed | no | — | none |
| R1 | 30 硬阻塞于 HG-AUDIT-R1（pending · 00 代录）；HG-GRAPH-MODULES 模块表已建置 approved（2026-09-21 核验 01_modules.md），D5 新签义务留验收 | no | — | 无 |
| R2 | D1–D5 同 task 竖切，建议 D1–D2 先于 D3–D4 提交；方案对比继承 SPEC R2 四组裁决（自实现薄重试层 / pybreaker 复用 / 新表 / 代码档表+env） | no | — | 无 |
| R3 | 失败语义四条钉死：流中禁重试（防重复正文）· 业务错误不计熔断（防误熔）· 落表故障不挡主答但不静默 · 无 0 假账；run_id 双口径 text+surface 无 FK | no | — | 无 |
| R4 | 验收全否定性断言：重试次数/延迟界 · 零重试反向断言 · 熔断三态拨时间不 sleep · 按 run_id 聚合 · 含变异检验一条 | no | — | 重试默认参数（0.5s/8s/3 次）未经真实流量校准（继承 SPEC residual ①） |
| R5 | 可交 20-task-audit；HG-AUDIT-R1 待人签 | no | — | ContextVar 注入点在 lg_rag supervisor 多节点并发下需 30 逐点核验（继承 SPEC residual ②）；占位价表偏差由手册 L8 另行（继承 SPEC residual ③） |

**actual_last_round**：R5 · **early_stop**：no · **residual_risks**：见 R4/R5

### R0 · 问题框定

上游手册 L5 钉死四个承重墙缺角；SPEC 已签收，本 task 不重开范围辩论，只做可执行化拆解。

### R1 · 开工闸

HG-AUDIT-R1 pending 期间拒 30；HG-GRAPH-MODULES 模块表已建置（2026-09-21 真读 `01_modules.md` 核验：bootstrap 2026-07-16 签 · `llm` 行在表 · 签录链完整），本 task 的 `llm` 行备注新签义务留在 D5 与验收标准，不由本帽预签。

### R2 · 竖切

D1–D5 同 task：四块共用 provider 边界钩点（重试层 / 熔断 guard / usage 落表同层），拆开会出现半截态；提交序建议 D1–D2（传输韧性）先于 D3–D4（路由与账本），每步可独立回归。方案对比不重演，直接继承 SPEC R2 裁决。

### R3 · 失败语义

流中已吐正文后任何重试/换模型都会产生重复正文——钉死「首 chunk 前限定」；业务错误计入熔断会误熔（用户填错 5 次参数不能把 provider 停 60s）；落表故障不挡主答但须可观测（log+计数+snapshot），不得静默声称已记账；无 usage 末帧不写 0 假账。

### R4 · 可测性

fake provider / fake httpx 消解外网不确定性；sleep 序列 monkeypatch 断言上界不假 sleep；熔断三态用 advance 式 hook 拨时间不真等 60s；usage 聚合按 run_id 真查表断言；变异检验一条防空真规则。

### R5 · 交接就绪

思考充分可交 20-task-audit；残余风险三条继承 SPEC 签收知悉项（重试参数校准 / ContextVar 并发串扰 / 占位价偏差）。

---

### 自检结论（执行者）

> **40 核验（2026-09-21 · 独立真跑，非轻信 30 自称）**：**PASS-with-warnings · 验收 24/24**。
> 证据全文：`docs/harness/invokes/by-task/llm-layer-hardening/invoke_20260921_40_verify_llm_layer_hardening.md`。要点：
> - `pytest tests`：1137 passed · 1 skipped · 3 failed；3 失败经 **master worktree 对照同错复现**（WS portal-loop ×2 + capability proxy ×1，环境性基线既有，与本波无关，高置信）。
> - `ruff check app tests`：57 errors = master 基线 57，零新增。
> - alembic 往返本帽在 dev 库真跑：upgrade/downgrade/re-upgrade 全过，表结构与钉死契约逐列一致，终态回 head，dev 数据零触碰。
> - `graph-compile.sh` exit 0；`01_modules.md` llm/db 行 + HG-GRAPH-MODULES 新行（00 代录 approved）在位。
> - 关键断言抽查（重试界/零重试/流式纪律/熔断三态/路由分档/usage 按 run_id 聚合/落表故障不挡主答/无末帧不落行）全部真实存在且断言非空；旧测 12 条处置 diff 实核落地。
> - 变异检验本帽亲自复做：删 `not exc.retryable` 判据 → `test_4xx_zero_retry` 真 fail（`assert 3 == 1`）→ 还原复跑全绿、工作树净。
> - 注意项（非阻塞）：3 条基线红仍存（建议独立 fix 分支）；重试默认参数未校准等三条承 SPEC residual。

---

## 修订

| 日期 | 说明 |
|------|------|
| 2026-09-21 | 10-task 落稿 · R0–R5 全轮无 early_stop · HG-AUDIT-R1=pending → 30 拒开工 · HG-GRAPH-MODULES 模块表已建置 approved（核验 `01_modules.md`）· D5 新签义务留 30 |
| 2026-09-21 | **闸签收**：HG-TASK-DRAFT=approved（00 验收 10-task 稿）· HG-AUDIT-R1=approved（R2 零阻塞 · 维护者本窗授权 00 代录，原话留痕于 SPEC 状态行与本表 10 注）· 30 放行 |
| 2026-09-21 | **R1 退回修订（B1 已补）**：实扫落盘「旧测影响面清单」12 条（grep 口径在节首）+ 工程「闸前置」验收断言 + failure_paths 一行；顺带采纳审查文非阻塞备注 1（闸表补全 2026-09-21 三行签录表述）· 2（`get_fallback_chain` 锚点实址修正为 `model_catalog.py:101-105`）· 4（20 invoke 快照由本帽代录至 invokes 目录，原义务属 20 棒）；备注 3（SPEC §8 编排差异）知悉无需改 · HG-AUDIT-R1 保持 pending（本帽不签） |
| 2026-09-21 | **40 核验**：PASS-with-warnings · 验收 24/24（逐条证据见 invoke `invoke_20260921_40_verify_llm_layer_hardening.md`）· 3 失败经 master worktree 对照证为基线环境性 · 变异检验亲自复做有效并还原 · 本帽未签任何 human_gate、未 CLOSE |
