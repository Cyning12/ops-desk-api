# SPEC：Agent Host V1-C · LLM 工厂闭环（预算硬闸 + 推理缓存 + 声明式降级）（llm-factory-closure）（v0）

> **层级**：L1 波次 SPEC（07 L0 规划的 V1-C 波 · 无硬依赖 · 可与 B/D 并行）  
> **状态**：`signed`（HG-SPEC-SIGNOFF=**approved** · 2026-09-23 · **00 代录** · 维护者令原话：「签收，并生成对此长程任务的00启动Prompt，新窗口执行，授权00签收所有过程文档，完整落地1.0版本内容」+ 本窗令「继续，完成后自行进行下一波，无特殊情况无需停下等待接收命令」）  
> **种子**：[`../agent-infra/08_host_v1_wave_spec_outlines_v0.md`](../agent-infra/08_host_v1_wave_spec_outlines_v0.md) §3（signed · 本 SPEC 为其正式展开，冲突以本 SPEC 为准）  
> **上游**：[`../agent-infra/07_host_v1_landing_plan_v0.md`](../agent-infra/07_host_v1_landing_plan_v0.md)（signed）· 大纲 v0.2 #12/#22/#23/#24（成本控制/降级/缓存/预算差距）· `docs/tasks/done/task_llm_layer_hardening.md`（usage 账本/分档路由/熔断重试既有面）  
> **下游**：HG-SPEC-SIGNOFF → 00 出 task → 20-task-audit → HG-AUDIT-R1 → 30（委派子 Agent · 分支 `task/host-v1-llm-factory-closure`）→ 40 → PR+CI 绿+merge → 图谱回写（00 代录）→ CLOSE  
> **Open Folder（实现）**：`ops-desk-api/`

---

## Harness 元信息

| 字段 | 值 |
|---|---|
| **spec_slug** | `host-v1-llm-factory-closure` |
| **invoke_slug** | `host-v1-llm-factory-closure`（task 阶段） |
| **test_strategy** | `required` |
| **test_strategy_note** | 预算两级检查点断言（预估保守下限/调用后记账为准/超限下一次调用前拦截）· 降级标记断言（ok=True 也可能 degraded · 通断同看标记）· 缓存命中/失效断言（版本 bump 失效 · catalog 版本哈希）· 声明式降级链断言（集中 catalog 不散落）· 防假降级断言（末端 ok=False+degraded 不伪造成功）· off 零 diff |
| **默认分支** | `task/host-v1-llm-factory-closure`（自 `master` 分出；**禁止 master/main 直改**） |
| **graph_change_layer** | `G-L1` 行备注（`llm` 行：预算闸+推理缓存+档级降级链 · 无新模块预判；HG-GRAPH-MODULES 随 30 回写 00 代录） |
| **freeze_id** | 无（不改 freeze 契约 · SSE 零新事件类型 · 零新路由 · 零新表——usage 复用 `ops_llm_usage` 既有表） |

### 人工闸（SPEC 阶段）

| human_gate_id | status | 说明 |
|---|---|---|
| **HG-SPEC-SIGNOFF** | **approved**（2026-09-23 · 00 代录） | 维护者双令原话留痕（见状态行）；开放裁定 Q1/Q2/Q3 已答；00 可拆 task |

---

## 1. 背景与目标

### 现状与差距（承大纲 v0.2 #12/#22/#23/#24 + 测评点 2）

`ops_llm_usage` 账本是**记账不是预算**（`app/llm/usage.py` · run 级聚合 task_type 归因）；降级是同档重试+熔断（`BaseProviderImpl` 指数退避+pybreaker）**无跨档链**；推理缓存**缺失**；档级路由已有（`model_catalog.TASK_TIER_MODELS` + `OPS_LLM_TIER_*` env）但无 fallback 声明。

### 关键实证（2026-09-23 本帽真读）

- **usage 面**：`usage.py` 落表 + ContextVar run 上下文注入；`providers/base.py:136-152` 末帧落账 · 无帧不落 · 不写 0 假账 · 落表故障不挡主答——预算检查点可复用同一 ContextVar 与记账面。
- **防假降级铁律**：`capability/fallback.py` B1 写能力永不降级 · B2 降级必须显式标记 `meta.degraded`+来源 · B3 链条有界 · B4 只有下游不可用才降级（:23-38）——LLM 工厂预算降级承同一铁律体系（U3）。
- **分档路由**：`model_catalog.resolve_task_model`（:144-177 · 解析序 explicit > env 档 > 档默认 > 现网默认 · 非法回退+warning）——声明式降级链的自然落点。

### 一句话目标

LLM 工厂闭环：会话/任务级**预算硬闸**（默认观测 · 调用前预估+调用后记账 · 超限下一次调用前拦截）+ 耗尽**降级链**（小模型档→规则/缓存 · 必带 `degraded` 标记）+ **推理缓存**（plan/参数模板 · 版本 bump 失效）+ **档级 fallback 声明进 model_catalog**（不散落调用点）+ Cost per Successful Task 指标定义。

### 设计纪律（跨波公共约束继承 · 签收时锁死）

1. **默认观测上线**：`OPS_LLM_BUDGET_MODE=off|observe|enforce` 默认 off（只记账不拦截）→ 灰度开拦截；缓存 `OPS_LLM_INFER_CACHE_ENABLED=false` 默认关。
2. **防假降级（U3）**：声明才降级（catalog 集中声明）· 必带 `degraded` 标记跟数据走（`ok=True` 也可能降级 · 通断同看标记）· 链末端失败 → `ok=False`+degraded 不伪造成功。
3. **进程内为本波边界**：缓存进程内 TTL · 预算会话/任务两级（ContextVar）· 不跨进程不跨租户。
4. **零 freeze 动**：不改 freeze 契约 · SSE 零新事件 · 零新路由 · 零新表（usage 复用既有表）· provider 契约零改。
5. **账本纪律承袭**：无末帧不写 0 假账 · 落表故障不挡主答 · 预估是保守下限不是承诺。

---

## 2. 范围（D 块展开 · 承 08 §3.2）

### D1 · 预算声明与检查点（必做）

- **预算声明**：会话级 `OPS_LLM_BUDGET_SESSION_TOKENS`（默认 0=不限制）· 任务级 `OPS_LLM_BUDGET_TASK_TOKENS`（默认 0=不限制）；非法/负值回退 0（承 `_env_int` 纪律）；任务级键 = task_type（answer/grader/extract/structured/summary 承 TASK_TYPES）。
- **检查点**（Q1 裁定 · **llm 层单检查点**）：新纯函数面 `app/llm/budget.py`——`check_budget(task_type, *, ctx) -> BudgetVerdict`：① 调用前：会话/任务已记账 + 保守下限预估 vs 声明预算（预估=该档近 N 次调用 P50 token 的保守下限 · 无样本时用档级固定下限常量）；② 调用后：usage 记账复用既有面（真实值为准 · 预估只是下限）。
- **拦截语义**：超限 → **下一次调用前拦截**（流式 token 不可预知 · 不在调用中截断）；enforce 模式拦截走降级链（D2）不直接拒；observe 只记 `would_block`；off 零行为。
- **进程内账本**：会话/任务级计数器（进程内 dict + 锁 · 承 capability budget.py 先例形态）；重启归零如实定性（跨进程预算 v2.0 · 与 usage 持久账本对账由 D5 指标面兜底）。

### D2 · 耗尽降级链（必做 · 防假降级 U3）

- 链序（声明式 · D4）：预算耗尽 → **小模型档**（`TASK_TIER_FALLBACKS[task]` 声明的下一档模型）→ **规则/缓存档**（Q3 裁定：固定文案模板档 + 缓存命中档）。
- **标记铁律**：每次降级 `degraded` 标记跟数据走（结果 meta/span：`degraded=true` + `degrade_reason=budget_exhausted` + `degrade_chain=[tier大, tier小, rule]`）；`ok=True` 也可能降级。
- **链末端**：规则档也失败/无声明 → `ok=False` + degraded 标记 · **不伪造成功**（承 B2/链末端先例）。
- **不降级面**：grader/summary 等背景档预算耗尽 → 明确失败优于降级答非所问？——裁定：**所有档一视同仁走声明链**（无声明 = 明确失败 · 承 fallback ACTION_NONE 默认）；业务档位是否配降级链由 catalog 声明显式决定。

### D3 · 推理缓存（必做 · 默认关）

- **对象**（Q2 裁定）：**只缓存结构化产物**——意图 plan（supervisor SubtasksPlan/intent 档 structured 输出）与高频能力参数模板；**不缓存流式终答 answer**（时效性证据 · 缓存=静默陈旧 · 承 fallback B2 精神）。
- **键**：`task_type + 模型档 id + prompt 模板版本 + 规范化输入哈希`；plan 类另含 **catalog 版本/可见集哈希**（能力目录变 → 旧 plan 失效 · FP 裁定）。
- **失效**：模型档变更 / prompt 版本 bump → 键自然失效（版本入键）；进程内 TTL（`OPS_LLM_INFER_CACHE_TTL_SECONDS` 默认 3600 非法回退）；容量上限（LRU · `OPS_LLM_INFER_CACHE_MAX_ENTRIES` 默认 256）。
- **观测**：命中/未命中/失效进 span metadata（`infer_cache_hit`/`infer_cache_key_prefix` · 不记内容）；命中率由 D5 指标面聚合。

### D4 · 声明式降级（必做）

- `model_catalog` 增 `TASK_TIER_FALLBACKS: dict[str, tuple[str, ...]]`——档级 fallback 链声明（大→小→规则档标记 `rule:<name>`）；`resolve_task_model` 增 `resolve_fallback_chain(task_type)` 纯函数（链解析+非法档过滤+warning · 承 :157-167 回退纪律）。
- **集中不散落**：调用点只问 catalog 要链；禁止在节点/调用点写死降级模型（断言化守护：grep 守护测试或 code review 条款 · 机检面见 D6）。
- 规则档声明：`rule:static_refusal`（固定文案模板 · Q3 裁定）等命名词表入 catalog 注释。

### D5 · 指标（必做）

- **Cost per Successful Task 定义**：`Σ(成功 run 的全部 LLM 调用 cost) / 成功任务数`——cost 由 usage 账本 token × 档级单价表（catalog 增档级单价声明 · 仅估算口径注明非计费对账）；成功任务口径 = supervisor run 终态 done（承 run_events 落盘面）。
- **产出面**：Langfuse span 聚合（预算 verdict / 降级链 / 缓存命中 / 估算成本进 span metadata）；**不建新看板**（承 04 轨观测面 · 本波只保证「有数可查」）。

### D6 · 测试（必做）

1. 预算检查点断言：预估保守下限 · 调用后真实记账覆盖预估 · 超限下一次调用前拦截（enforce）· observe would_block · off 零行为
2. 降级标记断言：耗尽 → 小模型档（degraded 标记+链）· 链末端 ok=False+degraded 不伪造成功 · 无声明明确失败
3. 缓存断言：命中跳过 LLM（mock 计数）· 模型/prompt 版本 bump 失效 · catalog 版本哈希变失效 · 终答不缓存断言 · 关=零 diff
4. 声明式降级断言：链解析（非法档过滤）· 集中性守护（调用点无硬编码降级模型 grep 守护）
5. 指标断言：Cost per Successful Task 聚合口径（mock span 聚合）· 单价表缺失档 → 标注 unknown 不伪造 0

---

## 3. 非范围

- ❌ 跨 provider 计费对账（单价表仅估算口径 · 明示非对账）
- ❌ 缓存跨进程共享（进程内起步 · 重启失效如实定性）
- ❌ 预算跨租户统筹（会话/任务两级 · 跨租户 v2.0）
- ❌ 流式终答缓存（Q2 裁定）
- ❌ 规则引擎 DSL/可编程规则档（Q3 裁定固定文案模板）
- ❌ 改 provider 契约 / 改 freeze / 新 SSE 事件 / 新路由 / 新表
- ❌ 预算拦截中途截断流（超限在下一次调用前拦截 · 不截进行中流）

---

## 4. 开放裁定（必答题 · 全部作答）

### Q1 · 预算检查点层位

| 方案 | 做法 | 裁决 |
|---|---|---|
| **S1 · llm 层单检查点** | `app/llm/budget.py` 于 complete/stream 调用前检查 · usage ContextVar 同源 | **推荐（裁定）**：token 消耗点在 LLM 调用 · 单一口径无漂移；capability 层无法预知 LLM 成本 |
| S2 · llm + capability 双检查点 | 两层各记各拦 | 弃选：双账本口径漂移（capability 层估的是调用次数不是 token）· 一处真值原则（承 baseline「单一真相」先例） |

### Q2 · 缓存对流式 answer 是否适用

| 方案 | 做法 | 裁决 |
|---|---|---|
| **S1 · 只缓存 plan/参数模板（结构化产物）** | 缓存键含 prompt 版本+输入哈希+catalog 版本 | **推荐（裁定）**（承种子预判）：终答含时效性证据 · 缓存终答=静默陈旧（fallback B2 同一条纪律）；plan/参数是结构化低时效面 |
| S2 · 终答也缓存 | answer 档入缓存 | 弃选：违反「降级/缓存必须显式标记且业务声明」铁律的边界——终答缓存无法保证证据时效 |

### Q3 · 规则引擎档的具体形态

| 方案 | 做法 | 裁决 |
|---|---|---|
| **S1 · 固定文案模板档（`rule:<name>` 声明式静态文案）** | catalog 声明文案模板 · 零逻辑 | **推荐（裁定）**：承 fallback `ACTION_STATIC`「返回声明好的静态兜底值」先例——业务声明框架执行 · 框架不猜 |
| S2 · 规则引擎 DSL | 条件→动作可编程规则 | 弃选：v1 过度设计 · 规则即代码引入新审查面 · 与「声明式集中」目标背离 |

---

## 5. failure_paths（承 08 §3.4 · 全部正面裁定）

| # | 路径 | 裁定 |
|---|---|---|
| FP-1 | 预估成本与实际偏差大（流式 token 不可预知） | 调用后记账为准（真实值覆盖）；预估=保守下限（P50 样本/档级常量下限）；超限在**下一次调用前**拦截不截进行中流 |
| FP-2 | 缓存命中陈旧 plan（能力目录已变） | plan 类缓存键含 **catalog 版本/可见集哈希**（目录变→键变→自然失效）；模型/prompt 版本入键 |
| FP-3 | 降级链末端（规则也失败/无声明） | `ok=False` + degraded 标记 · 不伪造成功（承 fallback 链末端先例） |
| FP-4 | 观测→拦截灰度误伤 | `OPS_LLM_BUDGET_MODE` 三档；拦截开关按 task_type 粒度可独立（`OPS_LLM_BUDGET_ENFORCE_TASKS` 白名单 · 默认空=全观测）；enforce 前观察期报告 |
| FP-5 | 进程重启预算计数器归零 | 如实定性：进程内预算是**热路径保护**不是持久配额；持久对账由 usage 表+D5 指标面兜底；重启归零不伪造超额 |
| FP-6 | 缓存击穿（高频同键并发 miss） | 进程内锁单飞（singleflight · 承 capability budget/circuit 锁先例）；v1 可接受并发 miss 各算各的（不引复杂度 · 如实定性） |
| FP-7 | 单价表缺失档成本估算 | 缺单价 → 该档 cost 标 `unknown` 不伪造 0（承「不写 0 假账」铁律） |
| FP-8 | 降级链成环/过长 | catalog 链声明加载期校验：去环+长度上限（承 fallback B3 max_depth 先例 · 链长≤3） |

---

## 6. 验收标准（可机验）

1. 预算两级检查点断言通过（会话/任务级 · 预估下限/记账为准/下一次调用前拦截）
2. 耗尽降级带标记：`degraded=true`+原因+链跟数据走；ok=True 也可能降级断言
3. 链末端 `ok=False`+degraded 不伪造成功；无声明档明确失败
4. 缓存命中跳过 LLM 可观测；版本 bump/catalog 哈希变失效；终答不缓存；默认关零 diff
5. 降级声明集中 model_catalog（调用点零硬编码降级模型 · 守护断言）
6. Cost per Successful Task 有定义有数（span 聚合口径断言 · 缺单价 unknown 不伪造 0）
7. off 模式零 diff（既有基线用例零改动全绿）
8. `pytest tests` 全绿 + `ruff check app tests` 净增 0
9. 图谱回写完成（llm 行备注 + HG-GRAPH-MODULES 00 代录）+ graph-compile 绿
10. PR 到 master 经 CI 绿后 merge

---

## 7. 思考轮回填（R0–R5）

- **R0（读人聊/目标）**：维护者令长程授权；08 §3 种子 + llm-layer-hardening 既有面（usage/分档/熔断）真读毕。
- **R1（范围/非范围）**：进程内为本波边界；D1–D6 承种子展开；跨 provider 对账/跨进程缓存/跨租户预算/终答缓存/规则 DSL 显式排除。
- **R2（方案对比）**：Q1 单检查点（双检查点弃——口径漂移）· Q2 只缓存结构化产物（终答缓存弃——静默陈旧）· Q3 固定文案档（规则 DSL 弃——过度设计）；检查点位置、缓存对象、规则形态各两案以上。
- **R3（边界/失败路径）**：FP-1~FP-8 全裁定；最锋利边界 = 防假降级（U3：链末端不伪造成功 + 标记跟数据走）与重启归零的诚实定性（FP-5 不虚假承诺持久预算）。
- **R4（验收/可测性）**：验收 10 条全可机验；降级标记是变异检验式断言（摘除 degraded 标记 → 断言必挂）。
- **R5（签收就绪）**：观测模式灰度口径确认（三档 + task 白名单）；图谱义务定（llm 行备注 · 无新模块）；可交 00 代录 HG-SPEC-SIGNOFF 后拆 task。

### 思考轮控制

| 轮 | 状态 | 说明 |
|---|---|---|
| R0 | done | 维护者令 + 07/08 §3 + llm 既有面（usage/fallback/catalog）已读 |
| R1 | done | 范围 D1–D6 / 非范围锁死 |
| R2 | done | Q1/Q2/Q3 ≥2 案对比 + 裁定 |
| R3 | done | FP-1~FP-8 裁定 |
| R4 | done | 验收 10 条 + test_strategy=required |
| R5 | done | 签收就绪 → 00 代录 HG-SPEC-SIGNOFF |
| early_stop | no | — |

---

## 8. 关联

- 规划/种子：[`../agent-infra/07_host_v1_landing_plan_v0.md`](../agent-infra/07_host_v1_landing_plan_v0.md) · [`../agent-infra/08_host_v1_wave_spec_outlines_v0.md`](../agent-infra/08_host_v1_wave_spec_outlines_v0.md) §3（双 signed）
- 既有面：`docs/tasks/done/task_llm_layer_hardening.md`（usage 账本/分档路由/熔断）· `docs/spec/agent-infra/04_eval_and_observability_plan_v0.md`（SLI/SLO 对齐 · Cost per Successful Task 候选指标）
- 代码锚点：`app/llm/usage.py` · `app/llm/model_catalog.py`（:118-177 TASK_TIER_MODELS/resolve_task_model）· `app/llm/providers/base.py`（:136-152 末帧落账纪律）· `app/ops/capability/fallback.py`（:23-38 四硬边界 B1–B4）· `app/ops/capability/budget.py`（进程内配额先例）
- 图谱：`docs/_tech_graph/l1/01_modules.md`（llm 行）

## 修订记录

| 日期 | 版本 | 内容 |
|---|---|---|
| 2026-09-23 | v0 | 10-spec 初稿：以 08 §3 种子展开 D1–D6；开放裁定 Q1（llm 层单检查点）/Q2（只缓存 plan/参数 · 不缓存终答）/Q3（固定文案模板档）全部作答；FP-1~FP-8 裁定；R0–R5 回填 |
| 2026-09-23 | v0 | **00 代录 HG-SPEC-SIGNOFF=approved**（维护者双令原话留痕）；下一棒：V1-B CLOSE 后拆 task（C 可与 B/D 并行 · 本窗按 B→C 序推进保闸流清晰） |
