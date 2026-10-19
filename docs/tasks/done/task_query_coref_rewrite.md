# Task：query-coref-rewrite（多轮指代消解 · 装配层查询重写 · 默认关）

> **状态**：draft（2026-10-19 10-task 落稿 · 待 20-task-audit R1 → 维护者签 HG-AUDIT-R1 → 30）
> **类型**：feature（历史感知 query 重写注入 continuity 装配层；**不**新增路由 / 表 / 一级模块 / SSE `event_type`）
> **依据**：SPEC `docs/spec/query-coref-rewrite/SPEC-query-coref-rewrite_v0.md`（signed · HG-SPEC-SIGNOFF=approved 2026-10-19 维护者会话签收）· 20-spec-audit R1 审查 `docs/harness/reviews/spec_query-coref-rewrite_audit_R1_20261019.md`（**pass** · N1–N3 非阻塞观察移交本 task 吸收）
> **建议序**：1/5（query-coref-rewrite → memory-injection-consumer → scenario-stage-rewire → delegation-naming-boundary → tech-graph-flow-resync）
> **分支**：`task/query-coref-rewrite`（**未切**：当前工作分支为文档线 `docs/spec-followups-2026-10-19`，30 开工前按本文件自 master 切出）

## Harness 元信息

| 字段 | 值 |
|------|-----|
| **task_slug** | `query-coref-rewrite` |
| **git_branch** | `task/query-coref-rewrite` |
| **implement_repo** | `ops-desk-api` |
| **spec** | `docs/spec/query-coref-rewrite/SPEC-query-coref-rewrite_v0.md`（signed） |
| **test_strategy** | `required` |
| **test_strategy_note** | 承 SPEC 元信息：金样多轮会话（指代/省略/时间锚定三类各 ≥2 条）断言改写结果 · 默认关零 diff（消息序列逐元素相等）· 改写失败降级原文（不阻塞主链路）· 落盘与 run.start 仍为原文 · `mode=basic/router/supervisor` 三模式同开关生效 · 开关非法值回退关。增补（R1 审查 N1–N3）：rewrite 档键在册断言（无 unknown_task 告警）· 重写先于记忆向量召回的调用序断言 · 非法输出确定式三规则注入对拍。假 LLM 注入即可机断，**不打真模型** |
| **code_quality_bar** | `L2_backend` |
| **graph_change_layer** | `none`（不增路由/表/一级模块/SSE `event_type`；仅 `docs/_tech_graph/l1/01_modules.md` `lg_rag` 行备注补一句新开关）。若 30 实判越出 none → 回 SPEC 判 G-L*，**禁** silent 扩 |
| **graph_delta** | `docs/_tech_graph/l1/01_modules.md` `lg_rag` 行备注回写 `LG_RAG_QUERY_REWRITE_ENABLED`（装配层查询重写 · 默认关） |
| **graph_delta_note** | 无模块增删仅行备注；偏离回炉补闸 |
| **wiki_delta** | `n/a`（30 实判，可选 volatile 短注） |
| **wiki_delta_note** | 契约真值以 SPEC 为准；本 task 不新增契约面 |
| **review_hat** | `20` |
| **required_invoke_hats** | `10,20,30,40` |
| **invoke_retention_profile** | `default` |
| **experience_capture** | `required` |
| **kpi_aggregator** | `n/a` |
| **orchestration** | 10 落稿（本文件）→ 20-task-audit R1 → 维护者签 HG-AUDIT-R1 → 30（红测先行）→ 40 → PR+CI 绿 → CLOSE → **下游棒**：memory-injection-consumer（建议序 2/5 · 另 SPEC/task） |
| **freeze_id** | 对照 `lg-rag-sse-v1` / `lg-rag-http-v1`：SSE 帧与请求体零变化（改写只发生在图输入装配内）。若 30 需要把改写结果透出到 SSE（本波明确不做）→ 回本 SPEC 升 freeze，**禁** silent 扩 |

### 人工闸

| human_gate_id | status | blocks_hats | 说明 |
|---------------|--------|-------------|------|
| HG-SPEC-SIGNOFF | approved | 10, 20 | 2026-10-19 维护者会话签收 · 见 SPEC 闸表与审查文 R1（pass） |
| **HG-AUDIT-R1** | **approved** | 30 | 2026-10-19 维护者授权 00 代签（会话原话「授权00签收后续文档」，授权范围扩展记录于 docs/harness/invokes/by-task/query-coref-rewrite/）；依据审查文 `docs/harness/reviews/task_query_coref_rewrite_audit_R1_20261019.md`（R1=pass · 阻塞 0 · 锚点 26 处零漂移 · 非阻塞 O1/O2 留 30 吸收） |
| HG-GRAPH-MODULES | approved | 30 | `docs/_tech_graph/l1/01_modules.md` 闸登记表（`lg_rag` 行 :65 起在册）· graph_change_layer=none 预期不再签；30 实判越出 → 回本表补签 |

---

## 背景与目标

### 问题（承 SPEC §1）

多轮对话下用户 query 大量依赖上下文（「那个 PR 合了吗」「刚才说的表加个索引」），而 supervisor 链路**没有任何指代消解**：装配层把历史压缩后装进 `state.messages`，但 planner prompt 只有 catalog + 原文 query 两条消息（`app/ops/lg_rag/multi/nodes.py:1163-1170`），rag 工人子图输入隔离不传 history（`multi/nodes.py:1432-1435`），aggregator 同样只吃原文（`multi/nodes.py:2107`）。多轮场景必然拆解失败或幻觉编号。

### 目标（承 SPEC §1 一句话目标）

在 **continuity 装配层**（末位 `HumanMessage(query)` 追加之前）插入可选的「历史感知 query 重写」步骤：用压缩后历史 + 原文 query 产出**自足问句**，下游 planner / rag 检索 / aggregator 全部吃重写结果；**env 默认关**，开启后改写失败一律降级原文。

---

## 范围

单 task，四块一起做（D1–D3 承 SPEC §2 原样；D4 = R1 审查 N1 增补；任缺一块即 unknown_task 告警或假成功）：

### D1 · 重写插入点：continuity 装配层（承 SPEC D1 + N2 顺序钉死）

- 位置：`assemble_graph_messages_with_memory`（`app/ops/lg_rag/continuity.py:546-602` → impl `:401-514`）内，`_assemble_messages_from_compressed`（`:82-98`）末位追加 `HumanMessage(query)`（`:97`）之前。
- 输入：压缩后历史 turns + 原文 query（全链路唯一两者皆备的单点）。
- 输出：`resolved_query` 自足问句；历史为空或重写判定「无需消解」→ 原样返回（零 LLM 调用短路允许，见 D2）。
- **N2 顺序钉死（10 裁定 · R1 审查观察②吸收）**：**先重写，后记忆召回**。开关开时，`resolved_query` 在 impl 入口（两条装配分支 :428-441 之前）一次性算出；其后 ① 末位 `HumanMessage(resolved_query)`、② 记忆向量召回 `recall_with_vector(..., query, ...)`（`continuity.py:454-457`）统一吃 `resolved_query`。理由：向量召回与 rag 检索同受指代困扰（「那个 PR」作向量问句必然跑偏），单点重写全下游统一口径；召回为瞬时不落盘面，不违 D3「原文是唯一持久真源」审计口径。30 不得以「召回保持原文」为由颠倒顺序。
- 生效面：`graph.py:_astream_with_tracing`（`:199-205`）三模式（basic/router/supervisor）统一生效——三者都经此装配。
- 先例：仿 `SESSION_SUMMARY_ENABLED`（`continuity.py:147-162`）默认关零 diff 接入模式。

### D2 · 开关与降级（承 SPEC D2 + N3 判定规则确定式化）

- env：`LG_RAG_QUERY_REWRITE_ENABLED`（**默认 0=关**；strip/lower 后非法值 → warning + 回退关，仿 `session_summary_enabled` :147-162 先例）。
- 模型档：走 `resolve_task_model('rewrite')` 档（依赖 D4 档键在册）；档未配（`TASK_TIER_MODELS["rewrite"] is None`）→ 返回 `(None, "default")`，调用方沿用现网默认模型解析（等价 SPEC D2「回落同档」语义，不新造档位语义之外的特例）；灰度期 `OPS_LLM_TIER_REWRITE_MODEL` 调档零改码。
- 降级：重写 LLM 异常 / 超时 / 输出非法 → **静默降级原文 query**，span 记 `query_rewrite_fallback=true`；**禁止**因重写失败让主链路失败。
- **N3 非法输出确定式判定规则（10 裁定 · R1 审查观察③吸收，取代 SPEC D2「明显非问句」启发式表述，30 不得另加启发式）**：重写输出满足以下任一即判非法 → 视同重写失败降级原文：
  1. `strip()` 后为**空串**；
  2. 含换行符（`\n` 或 `\r`）——**拒多行**，不取首行截断（避免半截语义）；
  3. `strip()` 后长度 **> 512 字符**（上限数值钉死）。
  不以「是否问号结尾」作判据（中文自足问句可不带问号）。
- 预算：重写调用经 LLM 工厂切面（预算/熔断/缓存照常生效）；`OPS_LLM_INFER_CACHE_ENABLED` 下 task_type=structured 可缓存面与本 task 无关，不为 rewrite 档新扩 `CACHEABLE_TASK_TYPES`。
- 重写 prompt 约束（承 SPEC §7）：「只消解指代与省略，不增删意图」；prompt 文案落点仿仓内 prompt 资产化先例，30 按 `docs/standards/CODING_BACKEND_L2_v1_zh.md` 执行。

### D3 · 消耗面与审计口径（承 SPEC D3 原样）

- 消耗方：装配层末位 `HumanMessage(resolved_query)`——planner、aggregator、rag 工人自动吃到（无需改各自取词代码）。
- 落盘：`persist_thread_turns`（`thread_store.py:63-90`）与 `run.start` payload.query（`sse_stream.py:334-341`）**仍记原文**；改写结果只进 prompt 不落盘（避免双真源口径漂移）。
- 可观测：span/log 记 `query_rewrite_applied`（bool）+ 原文/改写后长度；**不**记改写全文进日志（与「审计记动作不记内容」纪律一致）。
- 与 `continue_from_run_id` 关系：草稿拼接（`router.py:339-342`）发生在 worker 上游、进装配层之前；重写看到的是拼接后文本——本波**不改**该拼接逻辑，仅记录此顺序事实（金样含一条 continue 场景，承 SPEC §7）。

### D4 · `rewrite` 模型档键在册（R1 审查 N1 增补 · 无此项则走 unknown_task 告警分支）

- `app/llm/model_catalog.py:119` `TASK_TYPES` tuple 增 `"rewrite"`（`resolve_fallback_chain` :239 与 `budget.py` :202/:269 任务级计数键同源识别；task_tokens 限额默认 0=不限，行为零 diff 由 30 实证）。
- `app/llm/model_catalog.py:123-132` `TASK_TIER_MODELS` 增 `"rewrite": None` 键（仿 summary 档 :128-131 注释先例：默认 None = 不落档沿用现网默认，灰度期 `OPS_LLM_TIER_REWRITE_MODEL` 调档零改码）。
- `app/llm/model_catalog.py:215-223` `TASK_TIER_FALLBACKS` 增 `"rewrite": ()`（背景档无声明 = 预算耗尽明确失败；工厂层抛错由装配层降级原文兜住，与 summary 档 :222 先例一致）。
- 效果断言：`resolve_task_model('rewrite')` 不再走 :156-158 `unknown_task` 告警分支；档未配时返回 `(None, "default")`（或 env/策略包覆盖时的 `env_tier`/`strategy_pack`）。

## 非范围

承 SPEC §3 六条原样继承：

- ❌ 改 planner / aggregator / rag 工人的取词逻辑（消耗面靠装配层输出天然覆盖）
- ❌ 把重写结果落盘或透出到 SSE / history API（口径：原文是唯一持久真源）
- ❌ 改 router 子图内部 `rewrite_node`（质量回环改写，对象不同，各司其职）
- ❌ 改 `continue_from_run_id` 草稿拼接语义
- ❌ 默认开启；❌ 多轮重写（每请求至多一次重写调用）
- ❌ 引入检索式指代库 / 实体库（本波纯 LLM 重写，无新依赖）

task 级补充：

- ❌ 为 rewrite 档扩 `CACHEABLE_TASK_TYPES` / 档级 fallback 链声明（`TASK_TIER_FALLBACKS["rewrite"]` 恒为空 tuple）
- ❌ 颠倒 N2 钉死的「先重写后召回」顺序（召回吃原文属越出范围）
- ❌ **本起草阶段零 `app/` 改码**（仅 docs；30 开工以 HG-AUDIT-R1=approved 为前提）

---

## 失败路径（failure_paths）

承 SPEC §5 FP-1~FP-7 原样，并增 FP-8~FP-10（R1 审查 N1–N3 吸收）与 FP-11（闸纪律惯例）：

| ID | 触发条件 | 系统行为 | 可重试 | 用户可见 |
|----|----------|----------|--------|----------|
| FP-1 | 开关默认（关） | 消息序列与改前逐元素相等（零 diff 断言） | — | 零 diff |
| FP-2 | 开关开 + 首轮无历史 | 短路返回原文；允许零 LLM 调用（调用计数断言） | — | 正常作答 |
| FP-3 | 开关开 + 重写 LLM 异常/超时 | 降级原文，主链路继续；span `query_rewrite_fallback=true` | 用户重问 | 正常作答（fallback 可机读） |
| FP-4 | 开关开 + 指代 query（金样） | 末位 HumanMessage 为自足问句；planner/aggregator 收到改写后文本 | — | 正常作答 |
| FP-5 | env 非法值 | warning + 行为同关（FP-1） | — | 零 diff |
| FP-6 | 落盘与 run.start | `persist_thread_turns` 与 `run.start` payload.query 仍记原文（双写口径不漂移） | — | history API 原文 |
| FP-7 | `mode=basic/router` | 同开关生效；默认关下既有测试无行为差 | — | 零 diff |
| FP-8（N1） | `TASK_TIER_MODELS` 缺 `rewrite` 档键 | `resolve_task_model('rewrite')` 走 :156-158 `unknown_task` 告警分支——**本 task D4 封堵**：档键在册后 source ∈ {default, env_tier, strategy_pack}，无 unknown_task 告警 | — | 日志告警消失 |
| FP-9（N2） | 重写与记忆向量召回顺序颠倒 | 违反钉死顺序即红：`recall_with_vector`（`continuity.py:454-457`）收到的 query 须等于 `resolved_query`（非原文）；调用序断言重写 LLM 先于召回 | — | — |
| FP-10（N3） | 重写输出非法 | 确定式三规则（空串 / 含换行 / >512 字符）任一命中 → 静默降级原文 + span `query_rewrite_fallback=true`；不取首行截断、不修补 | 用户重问 | 正常作答（fallback 可机读） |
| FP-11 | HG-AUDIT-R1 未签即 30 | GATE_VERIFY 拒开工（闸真值=本表，非聊天/invoke 字面） | 是 | — |

---

## 验收标准

全部可机断（假 LLM 注入 / 夹具 / 零 diff 对拍，**不打真模型**）：

- [ ] **TC1 默认关零 diff**：`LG_RAG_QUERY_REWRITE_ENABLED` 未设/0 下，`mode=basic/router/supervisor` 三模式装配输出消息序列与改前**逐元素相等**（类型+content 对拍）。
- [ ] **TC2 开 + 金样三类**：开关开 + 金样多轮会话（指代/省略/时间锚定各 ≥2 条，含一条 `continue_from_run_id` 拼接场景）注入假重写 LLM 返回钉死自足问句 → 末位 `HumanMessage` content == 改写文；planner（`multi/nodes.py:1163-1170` prompt user 条）与 aggregator（:2035-2043）实际收到改写后文本。
- [ ] **TC3 失败注入降级**：假 LLM 抛错/超时 → 末位 `HumanMessage` 为原文，主链路产出不受影响，span 含 `query_rewrite_fallback=true` 且 `query_rewrite_applied=false`。
- [ ] **TC4 首轮短路**：开关开 + 无历史 → 重写 LLM 调用计数 == 0；末位为原文。
- [ ] **TC5 落盘原文（FP-6）**：开关开且改写生效下，`persist_thread_turns` 入库 turn 与 `run.start` payload.query 均为**原文** query（双写两表口径不漂移）。
- [ ] **TC6 env 非法值（FP-5）**：`LG_RAG_QUERY_REWRITE_ENABLED=yespls` 等非法值 → warning + 行为同关（零 diff 对拍）。
- [ ] **TC7 N1 档键在册（FP-8）**：`resolve_task_model('rewrite')` 返回 source ∈ {`default`, `env_tier`, `strategy_pack`} 且**不**为 `unknown_task`；caplog 无 `unknown llm task_type` 告警；未配档时返回 `(None, "default")`；`OPS_LLM_TIER_REWRITE_MODEL` 设已知目录模型 id 时返回 `(model, "env_tier")`；`TASK_TIER_FALLBACKS["rewrite"] == ()`。
- [ ] **TC8 N2 顺序钉死（FP-9）**：开关开 + 记忆向量召回开（`memory_facts_vector_recall_enabled`）下，桩 `recall_with_vector` 实收 query 参数 == `resolved_query`（假 LLM 钉死改写文，≠原文）；调用序记录断言重写 LLM 调用先于召回。
- [ ] **TC9 N3 非法输出三形态（FP-10）**：假 LLM 分别返回 ①空白串 ②含 `\n` 多行 ③>512 字符长文 → 三种形态均降级原文 + span `query_rewrite_fallback=true`；另注边界：恰 512 字符单行非空输出**接受**（钉死闭区间口径）。
- [ ] **TC10 图谱与契约守护**：不新增 SSE `event_type` / 路由 / 表 / 一级模块；`graph-compile` EXIT=0；`docs/_tech_graph/l1/01_modules.md` `lg_rag` 行备注仅增一句开关说明（graph_change_layer=none 实证）。
- [ ] **TC11 反回归全量**：`pytest` 全量绿（新增覆盖 TC1–TC10）；`ruff check` 触及路径绿；默认关保证下既有用例零行为差。
- [ ] **TC12 旧测影响面（K7 惯例）**：30 红测先行前对下列装配面既有测试逐文件确认处置（行号 30 按实校正），**枚举外既有用例默认保持绿**（误删合法回归即红）：
  - `tests/test_lg_rag_session_continuity.py`（窗口压缩/装配对拍）→ 默认关**保持绿**。
  - `tests/test_session_summary.py`（off 态逐字节对拍先例 · :492-695 对拍簇）→ 默认关**保持绿**；on 态路径与重写共存时逐条核对（两开关独立短路）。
  - `tests/test_memory_injection.py` / `tests/test_memory_episode_recall.py`（装配+记忆注入面）→ 默认关**保持绿**。
  - `tests/test_memory_vector_p1.py` / `tests/test_memory_service_db.py`（`recall_with_vector` 桩入参断言）→ 默认关**保持绿**；若既有用例钉死召回吃原文 query 参数形态，30 逐条核对是否被 N2 顺序钉死影响并标注处置（默认关下 resolved==原文，预期零破）。
  - `tests/test_input_isolation_wiring.py` / `tests/eval/test_input_isolation.py`（:546-602 槽位归因面）→ 默认关**保持绿**。
  - `tests/test_memory_extract_p1.py`（recall 相关桩）→ 默认关**保持绿**。

## 依赖

- base：`task/query-coref-rewrite`（30 开工前自 master 切出；本文件落盘于文档线分支 `docs/spec-followups-2026-10-19`，不切分支）。
- SPEC：`docs/spec/query-coref-rewrite/SPEC-query-coref-rewrite_v0.md`（signed）全文。
- 审查文：`docs/harness/reviews/spec_query-coref-rewrite_audit_R1_20261019.md`（pass · N1–N3 吸收落点见本文件 D1/D2/D4 + FP-8~FP-10 + TC7/TC8/TC9）。
- 锚点（行号录自 R1 审查 14/14 实测 · 10 抽查复核 :147-162/:398-514 · 30 按实校正）：
  - `app/ops/lg_rag/continuity.py:546-602`（`assemble_graph_messages_with_memory` 包装面）· `:401-514`（impl）· `:82-98`（`_assemble_messages_from_compressed` 末位 :97 追加）· `:454-457`（`recall_with_vector` 吃 query）· `:147-162`（`session_summary_enabled` 开关先例）
  - `app/llm/model_catalog.py:119`（`TASK_TYPES`）· `:123-132`（`TASK_TIER_MODELS` · summary 档先例 :128-131）· `:156-158`（unknown_task 告警分支）· `:183-186`（档默认 `None` → `(None, "default")`）· `:215-223`（`TASK_TIER_FALLBACKS`）
  - `app/ops/lg_rag/graph.py:199-205`（`_astream_with_tracing` 三模式统一经装配）
  - `app/ops/lg_rag/multi/nodes.py:1106`（planner 取词）· `:1163-1170`（planner prompt 两条）· `:1432-1435`（rag 工人不传 history）· `:2035-2043/:2107`（aggregator）
  - `app/ops/lg_rag/thread_store.py:63-90`（`persist_thread_turns` 记原文 :82）· `app/ops/lg_rag/sse_stream.py:334-341`（`run.start` payload.query :340）
  - `app/ops/lg_rag/router.py:339-342`（continue 草稿拼接 · 本波不改）
  - `docs/_tech_graph/l1/01_modules.md`（`lg_rag` 行备注回写点 · 闸登记表 :63 起）
- 编码规范：`docs/standards/CODING_BACKEND_L2_v1_zh.md`。

## 给执行帽的必读列表

1. 本 task 全文（含人工闸表 · **HG-AUDIT-R1=pending 未签不得 30**，仅维护者可签，00/AI 不可代签）。
2. SPEC `docs/spec/query-coref-rewrite/SPEC-query-coref-rewrite_v0.md` 全文（§2 D1–D3 · §3 非范围 · §5 FP-1~FP-7 · §6 验收 · §7 风险/回滚）。
3. 审查文 `docs/harness/reviews/spec_query-coref-rewrite_audit_R1_20261019.md`（N1–N3 原文）。
4. 上列锚点文件全文相关段（禁信转述 · 行号按实校正）。
5. `docs/standards/CODING_BACKEND_L2_v1_zh.md`。
6. 开关接入先例：`docs/tasks/done/task_session_summary_fallback.md`（默认关零 diff · off 三态对拍断言钉死）。

## 思考轮控制

| 轮 | 结论 | early_stop | reason（early_stop） | residual_risks |
|---|------|-----------|----------------------|----------------|
| R0 | 问题框定承 SPEC：supervisor 链路无指代消解且 planner 不见历史（R1 审查 14/14 锚点实测一致） | false | — | — |
| R1 | 范围=D1 装配层插入 + D2 开关降级 + D3 审计口径 + D4 档键（N1）；SPEC 六条非范围原样继承 | false | — | N2 顺序 SPEC 未钉（→ 本帽 R2 裁定） |
| R2 | 方案承 SPEC §4 裁定 C；N1–N3 逐条吸收：N1→D4/TC7 · N2→先重写后召回钉死（D1/FP-9/TC8）· N3→确定式三规则（D2/FP-10/TC9） | false | — | 金样覆盖率靠后续 golden-eval 加强（承 SPEC R4） |
| R3 | 反例闭合：失败一律降级原文（不阻塞主链路）· 落盘双真源口径 FP-6 否决 · env 非法回退关 · 非法输出不修补只降级 · 顺序颠倒即红 | false | — | 重写语义漂移靠金样挡（承 SPEC §7） |
| R4 | 验收 TC1–TC12 全部可假 LLM 注入/夹具/零 diff 机断；红测先行；不打真模型 | false | — | continue 拼接场景仅金样一条覆盖 |
| R5 | 草稿可交 20-task-audit；**不可**当已签收 | false | — | **HG-AUDIT-R1=pending**（待 20 审 + 维护者人签 · 签前 30 拒改码） |

**actual_last_round**：R5

### R0 · 问题框定

承 SPEC §8 R0 与 R1 审查 §1：14 处锚点 read/grep 实测全一致，planner/aggregator/rag 三面均无历史无重写，多轮必然失效。

### R1 · 范围收束

承 SPEC §2 D1–D3 + §3 非范围六条原样。D4（N1）为实现面蕴含项：SPEC D2「走 `resolve_task_model('rewrite')` 档」以档键在册为前提，缺键则落 unknown_task 告警（model_catalog.py:156-158），属 task 必须点名的工作项；graph_change_layer=none 不受影响（审查文 N1 原话确认）。

### R2 · 方案与三条观察裁定

- N2 顺序裁定**先重写后召回**：召回问句与 rag 检索同受指代困扰，且 impl 单点一次重写全下游统一；召回非落盘面，不违 D3 审计口径。反面（召回吃原文）会留下「记忆召回仍跑偏」的半吊子状态，与本 task 目标直接冲突。
- N3 判定规则确定式化：空串 / 含换行 / >512 字符三条机器可判，取代「明显非问句」启发式；不以问号结尾作判据（中文问句可不带问号）；不取首行截断（半截语义比降级更糟）。
- N1 档键三处同增（`TASK_TYPES`/`TASK_TIER_MODELS`/`TASK_TIER_FALLBACKS`），fallback 链空 tuple 承 summary 档先例。

### R3 · 反例与边界

失败面全部收敛到「用原文」（承 SPEC R3）；FP-6 落盘口径为否决项；闸纪律 FP-11：HG-AUDIT-R1 未签 30 拒开工。

### R4 · 验收/可测性

`test_strategy=required`；TC1–TC12 均假 LLM 注入/夹具/对拍机断；默认关零 diff 是总保险（FP-1/FP-5/FP-7 三向互锁）。

### R5 · 收口

草稿交 20-task-audit；**HG-AUDIT-R1=pending**，维护者人签前 30 拒改码。本文件不授权改 `app/` / `tests/`。

### 自检结论（10-task · 2026-10-19）

- **范围/非范围互斥**：D1–D4 与非范围九条无重叠；「不改 planner/aggregator/rag 取词」与 D3「消耗面天然覆盖」互锁；「不落盘不透出」与 FP-6/TC5 否决互锁；N2 顺序钉死同时写入范围（D1）与非范围（禁颠倒）。
- **每条验收可机断**：TC1–TC12 全部假 LLM 注入/夹具/零 diff 对拍，无人工判断项；TC9 边界值（恰 512 接受）钉死闭区间口径。
- **N1–N3 逐条可追溯**：N1→D4 + FP-8 + TC7；N2→D1 顺序段 + FP-9 + TC8 + 非范围禁颠倒；N3→D2 判定规则段 + FP-10 + TC9。
- **闸纪律**：HG-AUDIT-R1=**pending** 在表（仅维护者可签 · 00/AI 不可代签）；HG-GRAPH-MODULES 沿用在册 approved（graph_change_layer=none 不再签）；本帽未改 `app/` / `tests/`，未执行 git 分支操作。
- **零 SPEC 扩范围**：非范围六条原样继承；D4 为 SPEC D2 蕴含的实现面工作项（审查文 N1 确认「SPEC 未点名该文件但 D2 已蕴含」）。

---

## 修订记录

| 日期 | 说明 |
|------|------|
| 2026-10-19 | 10-task 草稿：承 SPEC（signed 2026-10-19）D1–D3 + 非范围六条原样；吸收 R1 审查 N1–N3（N1→D4 档键三处 · N2→先重写后召回钉死 · N3→非法输出确定式三规则）；failure_paths FP-1~FP-11；验收 TC1–TC12；HG-AUDIT-R1=pending（仅维护者可签）；分支 `task/query-coref-rewrite` 未切（30 开工前自 master 切） |
