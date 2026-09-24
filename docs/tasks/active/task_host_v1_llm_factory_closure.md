# Task：Agent Host V1-C · LLM 工厂闭环（预算硬闸 llm/budget.py + 耗尽降级链带 degraded 标记 + 推理缓存 plan/参数 + 档级 fallback 进 model_catalog + Cost per Successful Task）（host-v1-llm-factory-closure）

> **状态**：`active`（2026-09-23 · 20-task-audit R1 **PASS-WITH-NITS**（零阻塞 · N1–N3 已微修留痕）· HG-AUDIT-R1=**approved** 00 代录 · 30 可委派开工）  
> **类型**：feature（LLM 工厂闭环 · **零 alembic 义务**（usage 复用 `ops_llm_usage` 既有表 · SPEC §3 锁死）· **有图谱义务按实判**（llm 行备注 + 人签新行 00 代录位 · 无新模块预判））  
> **上游 SPEC**：`docs/spec/host-v1-llm-factory-closure/SPEC-host-v1-llm-factory-closure_v0.md`（**signed** · HG-SPEC-SIGNOFF=approved 2026-09-23 · 00 代录 · Q1 llm 层单检查点 / Q2 只缓存 plan·参数 / Q3 固定文案模板档签收锁死）  
> **并行说明**：本波与 V1-B 并行推进（07 §3.1 授权 · 文件面零交叠——B 触 strategy/capability/lg_rag · 本波仅 app/llm）  
> **分支**：`task/host-v1-llm-factory-closure`（**禁止 master/main 直改 · 30 由 00 委派子 Agent 执行**）  
> **10 注**：2026-09-23 · 本棒由 00 亲起（无初稿时起草第一步 · 承 harness-00-delegate-only 例外条款）；HG-AUDIT-R1 落稿时待签（10 帽不签）

---

## Harness 元信息

| 字段 | 值 |
|------|-----|
| **task_slug** | `host-v1-llm-factory-closure` |
| **git_branch** | `task/host-v1-llm-factory-closure` |
| **implement_repo** | `ops-desk-api` |
| **test_strategy** | `required` |
| **test_strategy_note** | 预算两级检查点断言（预估保守下限/记账为准/超限下一次调用前拦截）· 降级标记断言（ok=True 也可能 degraded · 链末端 ok=False+degraded 不伪造成功）· 缓存命中/失效断言（版本 bump · catalog 哈希 · 终答不缓存）· 声明式降级集中守护断言 · Cost per Successful Task 聚合口径断言（缺单价 unknown 不伪造 0）· off 零 diff |
| **code_quality_bar** | `L2_backend` |
| **graph_change_layer** | `G-L1` 行备注（`llm` 行：预算闸 budget.py + 推理缓存 infer_cache + 档级降级链 TASK_TIER_FALLBACKS + Cost per Successful Task 指标面；**不新增一级模块**；HG-GRAPH-MODULES 随 30 交付 00 代录） |
| **graph_delta** | `docs/_tech_graph/l1/01_modules.md`（llm 行备注 + 人签新行 · 零新一级模块 · 零新跨模块边） |
| **graph_delta_note** | **回炉补闸条款**：若 30 实现形态偏离本预判（新增一级模块 · 新增表/列触发 alembic · 新增 SSE 事件类型 · 新增 HTTP 路由 · 改 freeze 契约 · 改 provider 契约 · 改 usage 末帧落账纪律），不得沿用本裁定——退回 10-spec/10-task 补闸 + `docs/_tech_graph/` 如实登记后续做 |
| **wiki_delta** | `n/a` |
| **wiki_delta_note** | 契约真值在 SPEC `host-v1-llm-factory-closure`；budget/infer_cache/model_catalog docstring 同步属范围项非 wiki |
| **review_hat** | `20` |
| **required_invoke_hats** | `10,20,30,40` |
| **invoke_retention_profile** | `default` |
| **experience_capture** | `recommended` |
| **kpi_aggregator** | `CLOSE` |
| **orchestration** | 单 task 直通：10 落稿 → 20-task-audit → HG-AUDIT-R1（00 代录）→ 30（00 委派子 Agent · 实现序：D4 catalog 链声明 → D1 budget.py → D2 降级链接线 → D3 infer_cache → D5 指标面 → D6 断言收口）→ 40 → PR+CI 绿+merge → 图谱回写（00 代录）→ CLOSE |
| **freeze_id** | 无（不改 lg-rag-sse-v1 / lg-rag-http-v1 / lc-evidence-http-v1 · SSE 零新事件类型 · 零新路由 · 零新表） |

### 人工闸

| human_gate_id | status | blocks_hats | 说明 |
|---------------|--------|-------------|------|
| HG-TASK-DRAFT | approved | 20-R1, 30 | 2026-09-23 · 00 代录（维护者令原话：「签收，并生成对此长程任务的00启动Prompt，新窗口执行，授权00签收所有过程文档，完整落地1.0版本内容」+ 本窗令「继续，完成后自行进行下一波，无特殊情况无需停下等待接收命令」） |
| HG-AUDIT-R1 | **approved** | **30** | 2026-09-23 · **00 代录**（维护者令原话：「签收，并生成对此长程任务的00启动Prompt，新窗口执行，授权00签收所有过程文档，完整落地1.0版本内容」+ 本窗令「授权00可以签收所有过程文档」「继续，完成后自行进行下一波，无特殊情况无需停下等待接收命令」）；依据：20-task-audit R1 **PASS-WITH-NITS** 零阻塞（`docs/harness/reviews/task_host_v1_llm_factory_closure_audit_R1_20260923.md` · 白名单 vs 钉死落点一致性核验通过——吸收 V1-B FAIL 教训）；N1–N3 已微修留痕（修订记录） |
| HG-GRAPH-MODULES | approved | **30** | 2026-09-23 真读 `docs/_tech_graph/l1/01_modules.md`：模块表已建置（签录链完整至 2026-09-23 V1-A 回写行）；`llm` 行在表；图谱新签义务（llm 行备注 + 人签新行 00 代录位）**随 30 交付落盘**；不新增一级模块 |
| HG-PILOT-OPSDESK-GLAYER | n/a | 物理分层试点改码 | 本 task 不涉物理分层试点改码 |

---

## 背景与目标

现状（SPEC §1 锁死 · 本帽复核一致）：`ops_llm_usage` 是账本不是预算（`usage.py` run 级聚合 · ContextVar run 上下文）；降级=同档重试+熔断无跨档链（`providers/base.py` + `circuit.py`）；推理缓存缺失；`model_catalog.TASK_TIER_MODELS` 有分档无 fallback 声明。

一句话目标（SPEC 锁死）：预算硬闸（默认观测 · 调用前预估+调用后记账 · 超限下一次调用前拦截）+ 耗尽降级链（小模型档→规则/缓存 · 必带 degraded 标记）+ 推理缓存（plan/参数 · 版本入键）+ 档级 fallback 声明进 model_catalog + Cost per Successful Task 指标定义。

设计纪律（30 不得违反 · 承 SPEC §1 签收锁死）：

1. **默认观测**：`OPS_LLM_BUDGET_MODE=off|observe|enforce` 默认 off · `OPS_LLM_INFER_CACHE_ENABLED=false` 默认关；非法值回退默认。
2. **防假降级（U3）**：声明才降级（catalog 集中）· `degraded` 标记跟数据走（ok=True 也可能降级）· 链末端 ok=False+degraded 不伪造成功。
3. **进程内边界**：缓存进程内 TTL/LRU · 预算会话/任务两级进程内计数（重启归零如实定性）· 不跨进程不跨租户。
4. **账本纪律**：无末帧不写 0 假账 · 落表故障不挡主答 · 预估是保守下限不是承诺 · 缺单价 unknown 不伪造 0。
5. **零 freeze 动**：不改 freeze 契约 · SSE 零新事件 · 零新路由 · 零新表 · provider 契约零改。

---

## 现状锚点（只读 · 30 必读 · 10 已扫）

| 主题 | 路径 · 锚点 | 现状 |
|------|-------------|------|
| usage 账本（**D1 复用面**） | `app/llm/usage.py` · `providers/base.py:136-152` | ContextVar run 上下文 · 末帧落账 · 无帧不落 · 不写 0 假账 · 落表故障不挡主答 |
| 分档路由（**D4 落点**） | `app/llm/model_catalog.py:118-177` | TASK_TYPES 五档 · TASK_TIER_MODELS · 解析序 explicit>env 档>档默认>现网默认 · 非法回退+warning（:157-167） |
| 防假降级铁律（**D2 承袭对象**） | `app/ops/capability/fallback.py:23-38` | B1 写能力永不降级 · B2 显式标记 · B3 链条有界 · B4 只有不可用才降级；ACTION_STATIC 静态兜底先例（:81） |
| 进程内配额/锁先例 | `app/ops/capability/budget.py` · `circuit.py` | 会话配额/kill switch · pybreaker 模式 · 锁形态 |
| 调用点（**检查点接线面 · R1 审查 N2 描述修正**） | `app/llm/factory.py`（provider 注册表 · 19 行薄面）· `providers/base.py:31-52`（`__init_subclass__` 统一入口真值 · usage hook 同层 :136-152） | complete/stream 统一入口在 base.py 子类注册面 · 检查点/缓存接线双落点 |
| 命名冲突扫 | grep `TASK_TIER_FALLBACKS\|check_budget\|infer_cache\|BudgetVerdict\|resolve_fallback_chain` 于 app | **零命中**（2026-09-23 本帽真跑）；app/llm/ 无 budget.py（capability/budget.py 不同包不冲突） |
| 测试基线 | `.venv/bin/python -m pytest tests --collect-only -q` | **1420 collected**（2026-09-23 本帽真跑） |
| alembic 义务 | 无 | usage 复用既有表 · 零新表零列；迁移 diff 为空入验收断言 |

---

## 钉死契约（自 SPEC §2/§4/§5 锁死；30 不得静默改义）

| 项 | 钉死 |
|----|------|
| **预算声明（D1）** | `OPS_LLM_BUDGET_SESSION_TOKENS`/`OPS_LLM_BUDGET_TASK_TOKENS` 默认 0=不限制 · 非法/负值回退 0；任务级键=TASK_TYPES 五档 |
| **检查点（Q1 裁定）** | 新文件 `app/llm/budget.py` 纯函数面 `check_budget(task_type, *, ctx) -> BudgetVerdict`；调用前保守下限预估（档级 P50 样本/固定下限常量）· 调用后 usage 真实记账覆盖；**超限在下一次调用前拦截**不截进行中流 |
| **模式（D1）** | `OPS_LLM_BUDGET_MODE=off\|observe\|enforce` 默认 off · `OPS_LLM_BUDGET_ENFORCE_TASKS` task 白名单（默认空=全观测）· 非法回退 off |
| **耗尽降级（D2）** | 链序=预算耗尽→小模型档（catalog 声明）→规则/缓存档；`degraded=true`+`degrade_reason=budget_exhausted`+`degrade_chain` 跟数据走；链末端 ok=False+degraded；无声明档=明确失败（承 ACTION_NONE） |
| **推理缓存（D3 · Q2 裁定）** | 只缓存结构化产物（intent/plan 档 structured 输出 + 高频能力参数模板）· **终答 answer 不缓存**；键=task_type+模型档+prompt 版本+输入哈希（plan 类另含 catalog 版本/可见集哈希）；进程内 LRU（默认 256）+TTL（默认 3600s 非法回退）；`OPS_LLM_INFER_CACHE_ENABLED=false` 默认关 |
| **声明式降级（D4）** | `model_catalog` 增 `TASK_TIER_FALLBACKS: dict[str, tuple[str,...]]` + `resolve_fallback_chain(task_type)` 纯函数（非法档过滤+warning）；规则档词表 `rule:<name>`；**调用点零硬编码降级模型**（守护断言） |
| **链校验（FP-8）** | catalog 链声明校验：去环 + 链长≤3（承 B3） |
| **指标（D5）** | Cost per Successful Task = Σ(成功 run LLM cost)/成功任务数；单价表入 catalog（估算口径注明非对账）；缺单价 → `unknown` 不伪造 0；产出面=Langfuse span 聚合不建新看板 |
| **图谱** | llm 行备注 + HG-GRAPH-MODULES 人签新行（**00 代录位**）；`./scripts/graph-compile.sh` 绿；零新一级模块 |

---

## 范围（单 task 直通 · SPEC §2 D1–D6）

- [ ] **D4 · catalog 链声明（必做 · 先行）**：`TASK_TIER_FALLBACKS` + `resolve_fallback_chain` + 链校验（去环/≤3）+ 档级单价表
- [ ] **D1 · 预算检查点（必做）**：`app/llm/budget.py` 新文件（声明 env/预估下限/verdict/进程内计数器+锁）+ 调用点接线（complete/stream 前）
- [ ] **D2 · 耗尽降级链（必做 · 防假降级）**：预算 verdict → 链解析 → degraded 标记跟数据走 → 链末端不伪造成功
- [ ] **D3 · 推理缓存（必做 · 默认关）**：进程内 LRU+TTL · 版本入键（模型/prompt/catalog）· 命中观测 · 终答不缓存
- [ ] **D5 · 指标面（必做）**：Cost per Successful Task 定义 + span 聚合产出 + 缺单价 unknown
- [ ] **D6 · 测试与图谱（必做 · 否决面）**：SPEC §2 D6 五组断言全落 + llm 行备注 + HG-GRAPH-MODULES 人签新行（00 代录）+ graph-compile 绿

**竖切结论**：D4→D1→D2→D3→D5→D6 同 task 一次提交；预算不配降级链 = 拦截即死（耗尽=拒答无出口）；降级不配标记 = 假降级（U3 铁律违反）；缓存不配版本入键 = 陈旧 plan 静默命中。耦合面可控（两个新文件 + catalog 扩展 + 调用点接线 + 测试/图谱）。

### 非范围

承 SPEC §3（锁死 · 越任一条即回炉）：跨 provider 计费对账 · 缓存跨进程共享 · 预算跨租户统筹 · 流式终答缓存 · 规则引擎 DSL · 改 provider/freeze 契约 · 新 SSE 事件/路由/表 · 中途截断流。

---

## failure_paths

| 触发条件 | 系统行为 | 可重试 | 用户可见 |
|----------|----------|--------|----------|
| `HG-AUDIT-R1` 未签即 30 | **拒开工** | 是 | 是 |
| B1 旧测影响面未逐条处置即 30 交付 | **拒收**（闸前置） | 是 | 是 |
| 验收缺预算检查点/降级标记/链末端/缓存失效/集中守护/指标口径/off 零 diff/变异检验任一 | **拒收**（防空真规则） | 是 | 是 |
| **预估与实际偏差大**（SPEC FP-1 · 流式 token 不可预知） | 调用后记账为准；预估=保守下限；超限下一次调用前拦截不截流 | 是 | 否 |
| **缓存命中陈旧 plan**（SPEC FP-2 · 目录已变） | plan 键含 catalog 版本/可见集哈希 → 目录变自然失效；模型/prompt 版本入键 | 是 | 否 |
| **降级链末端**（SPEC FP-3） | ok=False + degraded 标记 · 不伪造成功 | 是 | 是（明确失败终态 · 既有形态） |
| **观测→拦截灰度误伤**（SPEC FP-4） | 三档 + task 白名单（默认空=全观测）；enforce 前观察期报告 | 是 | 否 |
| **重启预算计数器归零**（SPEC FP-5） | 如实定性：进程内预算是热路径保护非持久配额；持久对账由 usage 表+指标面兜底；不伪造超额 | — | 否 |
| **缓存击穿**（SPEC FP-6 · 并发同键 miss） | 进程内锁 singleflight（承 capability 锁先例）；v1 接受并发 miss 如实定性 | 是 | 否 |
| **单价表缺失档**（SPEC FP-7） | cost 标 unknown 不伪造 0（承不写 0 假账铁律） | — | 否 |
| **降级链成环/过长**（SPEC FP-8） | catalog 加载期校验去环+链长≤3；非法链 warning+过滤不炸请求（承 :157-167 回退纪律） | — | 否 |

---

## 验收标准

- [ ] 人工闸：HG-AUDIT-R1 approved 后方可勾选下列码项（图谱新签义务随 30 交付落盘 00 代录；**30 偏离预判 → 回炉补闸条款生效**）

### D1 · 预算检查点（映射 SPEC §6-1）

- [ ] 会话/任务两级声明解析（默认 0=不限 · 非法回退 0 · 任务级五档键）
- [ ] 调用前预估保守下限断言（预估≤实际不拦截正常调用）；调用后真实记账覆盖断言
- [ ] 三档断言：off 零行为 · observe would_block 不拦 · enforce 超限**下一次调用前**拦截（进行中流不截断）

### D2 · 耗尽降级链（映射 SPEC §6-2/3）

- [ ] 耗尽 → 小模型档：结果带 `degraded=true`+`degrade_reason=budget_exhausted`+`degrade_chain`（ok=True 也可能降级 · 断言）
- [ ] 链末端（规则档也失败/无声明）→ ok=False+degraded · 不伪造成功（断言）
- [ ] 无声明档 → 明确失败（承 ACTION_NONE 默认 · 断言）

### D3 · 推理缓存（映射 SPEC §6-4）

- [ ] 命中跳过 LLM（mock 计数断言）；命中率 span 观测
- [ ] 失效断言：模型档变更 · prompt 版本 bump · catalog 版本/可见集哈希变 → 自然 miss
- [ ] 终答 answer 不缓存断言；默认关零 diff

### D4 · 声明式降级（映射 SPEC §6-5）

- [ ] `resolve_fallback_chain` 链解析断言（非法档过滤+warning）；链去环+≤3 校验断言
- [ ] 集中性守护断言：调用点零硬编码降级模型（grep 守护测试）

### D5 · 指标（映射 SPEC §6-6）

- [ ] Cost per Successful Task 聚合口径断言（mock usage/span 聚合）；缺单价档 → unknown 不伪造 0

### D6 · 图谱 / 工程（映射 SPEC §6-7/8/9 · §6-10 PR merge 由 orchestration 承载 · R1 审查 N3）

- [ ] 零 alembic（迁移 diff 为空断言）；llm 行备注 + HG-GRAPH-MODULES 人签新行（00 代录）；`./scripts/graph-compile.sh` 绿
- [ ] 全量 `pytest tests` 绿（基线 **1420 collected** · 无既有用例删除 · 新增数如实入 40）；`ruff check app tests` 净增 0
- [ ] 生产路径 diff 白名单：`git diff master -- app/` 只含 llm/budget.py 新增 + llm/infer_cache.py 新增 + llm/model_catalog.py（链+单价表）+ llm/factory.py 与 providers/base.py（检查点/缓存接线 · 最小侵入）+ 测试/图谱/文档

### 变异检验（不验收空真规则）

- [ ] ① **标记可检**：临时摘除 degraded 标记 → 降级标记断言必挂；恢复后全绿
- [ ] ② **缓存可检**：临时摘除 prompt 版本入键 → 版本 bump 失效断言必挂；恢复后全绿
- [ ] ③ **拦截可检**：临时检查点恒放行 → enforce 拦截断言必挂；恢复后全绿

### 旧测影响面清单（B1 · 2026-09-23 10-task 实扫落盘）

> 扫描口径（真跑）：`ls tests/ | grep -iE 'llm|usage|catalog|provider|budget|cache|fallback|circuit|model'`（命中 9 文件归并 5 组）· 命名冲突扫零命中 · 基线 1420 collected

| # | 锚点 | 本波影响 | 处置 |
|---|------|----------|------|
| 1 | `tests/test_model_catalog.py` · `test_llm_routing.py` | 分档路由守护；TASK_TIER_FALLBACKS 纯增量（resolve_task_model 既有解析序零改）→ 零改动全绿 | 回归（零改动） |
| 2 | `tests/test_llm_usage.py` · `test_llm_usage_cache.py` | usage 账本守护；末帧落账纪律零改 · 预算计数器独立面 → 零改动全绿 | 回归（零改动） |
| 3 | `tests/test_llm_circuit.py` · `test_llm_retry.py` · `test_llm_providers.py` | provider 韧性守护；检查点/缓存默认 off → 零 diff 全绿 | 回归（零改动） |
| 4 | `tests/test_supervisor_budget.py` · `test_lg_rag_supervisor_capability_catalog.py` | supervisor 预算/catalog 守护；本波 llm 层预算与 supervisor 步预算正交 → 零改动全绿 | 回归（零改动） |
| 5 | 新增义务：`tests/test_llm_budget.py`（检查点/降级链/标记/链末端/变异检验①③）+ `tests/test_llm_infer_cache.py`（命中/失效/终答不缓存/守护/变异检验②）+ 指标聚合断言（可并入 test_llm_budget.py） | — | 新增（用例数如实入 40 记录） |
| 6 | alembic 链 | 本波**无迁移义务**（usage 复用既有表 · SPEC §3 锁死） | 无（迁移 diff 为空断言入 D6） |

---

## 依赖

| 依赖 | 说明 |
|------|------|
| SPEC | `docs/spec/host-v1-llm-factory-closure/SPEC-host-v1-llm-factory-closure_v0.md`（signed · Q1/Q2/Q3 裁定锁死） |
| 规划/种子 | `docs/spec/agent-infra/07_host_v1_landing_plan_v0.md` · `08_host_v1_wave_spec_outlines_v0.md` §3（双 signed） |
| 既有面 | `docs/tasks/done/task_llm_layer_hardening.md`（usage/分档/熔断 · 本波直接上游） |
| 编码规范 | `docs/standards/CODING_BACKEND_L2_v1_zh.md` |
| 图谱 | `docs/_tech_graph/l1/01_modules.md`（2026-09-23 真读核验 · llm 行 · 签录链至 V1-A 回写行） |
| 改造对象 | `app/llm/budget.py`（新增）· `app/llm/infer_cache.py`（新增）· `app/llm/model_catalog.py`（:118-177 链+单价表）· `app/llm/factory.py` · `app/llm/providers/base.py`（接线 · 最小侵入） |
| 先例 · 防假降级 | `app/ops/capability/fallback.py:23-38`（B1–B4 铁律 · ACTION_STATIC :81） |
| 先例 · 回退纪律 | `app/llm/model_catalog.py:157-167`（非法档 warning+回退不炸请求） |
| 先例 · 进程内配额/锁 | `app/ops/capability/budget.py` · `app/ops/capability/circuit.py` |
| 先例 · 三档模式 | `app/ops/capability/delegation.py`（V1-A off/observe/enforce 形态） |
| 测试锚点 | B1 清单 5 组 |
| 格式基准 | `docs/tasks/done/task_host_v1_delegation_token.md`（V1-A · 五棒全通 · 格式对齐此） |

---

## 给执行帽的必读列表

1. `AGENTS.md`（新会话启动纪律 · 分支纪律 · GATE_VERIFY）
2. 本 task（钉死契约 · 闸 · 非范围 · B1）
3. SPEC `docs/spec/host-v1-llm-factory-closure/SPEC-host-v1-llm-factory-closure_v0.md`（§2 D1–D6 / §3 非范围 / §4 Q1–Q3 / §5 FP-1~FP-8 / §6 验收）
4. `docs/standards/CODING_BACKEND_L2_v1_zh.md`
5. 代码：`app/llm/usage.py` · `app/llm/model_catalog.py`（:118-177）· `app/llm/providers/base.py`（:136-152）· `app/llm/factory.py` · `app/ops/capability/fallback.py`（:23-38 B1–B4）· `app/ops/capability/budget.py`
6. 先例：`tests/test_llm_routing.py`（catalog 断言范式）· `tests/test_llm_usage.py`（账本断言范式）· `tests/test_capability_delegation.py`（V1-A 三档断言范式）
7. `docs/harness/prompts/FRAGMENT_30_gate_verify_v1_zh.md`

---

## 思考轮控制

| 轮 | 结论 | early_stop | reason（early_stop） | residual_risks |
|----|------|------------|----------------------|----------------|
| R0 | SPEC signed（HG-SPEC-SIGNOFF=approved 2026-09-23 00 代录）；范围 D1–D6 承 SPEC §2 不重开；本帽实扫复核：usage 末帧纪律 · catalog 解析序 · fallback B1–B4 · 命名零冲突（app/llm 无 budget.py）· 基线 1420 | no | — | 无 |
| R1 | 开工闸：HG-TASK-DRAFT approved（00 代录 · 双令留痕）· HG-AUDIT-R1 **pending**（blocks 30 → **30 拒开工**）· HG-GRAPH-MODULES=approved（真读核验 · llm 行在表 · 图谱新签义务随 30 落盘） | no | — | 无 |
| R2 | 竖切：D4→D1→D2→D3→D5→D6 同 task 一次提交；方案对比继承 SPEC §4 三组裁定（Q1 单检查点弃双层 · Q2 结构化产物弃终答 · Q3 静态文案弃 DSL），不重演 | no | — | 无 |
| R3 | failure_paths **11 条** = SPEC FP-1~FP-8 翻四列 + 过程三；最锋利边界=防假降级（U3 链末端不伪造成功）与重启归零诚实定性（FP-5 不虚假承诺持久预算） | no | — | ① 进程内预算非持久配额（FP-5 定性）② enforce 灰度依赖观察期报告质量 ③ 单价表是估算口径非对账 |
| R4 | 验收 **16 条**全否定性断言化逐块映射 SPEC §6（人工闸 1 / D1×3 / D2×3 / D3×3 / D4×2 / D5×1 / D6×3 = 16 · R1 审查 N1 计数修正 · 另变异检验×3 不计入）；B1 实扫 5+1 组三态齐全（回归×4 · 新增×1 · 迁移无×1） | no | — | 无 |
| R5 | 可交 20-task-audit；与 SPEC 实质差异为零（锚点/B1/基线数/闸行留痕过程化落地）；HG-AUDIT-R1 落稿时待签 | no | — | 见 R3 |

**actual_last_round**：R5 · **early_stop**：no · **residual_risks**：见 R3/R5

### R0 · 问题框定

SPEC 已签收（Q1 单检查点 + Q2 只缓存结构化产物 + Q3 静态文案档锁死），本 task 只做可执行化拆解：usage 是账本不是预算（测评点 2）· 无跨档降级链 · 无推理缓存——三缺口均有既有面可承（usage ContextVar / catalog 解析序 / fallback 铁律）。当前分支 master——**30 必须切 `task/host-v1-llm-factory-closure`**；与 V1-B 并行但文件面零交叠（B 不触 app/llm）。

### R1 · 开工闸

HG-TASK-DRAFT approved（00 代录 · 双令原话留痕）；HG-AUDIT-R1 **pending**（30 拒开工）；HG-GRAPH-MODULES **真读** `01_modules.md` 核验：模块表已建置 · 签录链完整至 V1-A 回写行 · llm 行在表 · 图谱义务=llm 行备注+人签新行随 30 落盘。

### R2 · 竖切

D1–D6 是不可拆语义单元：预算不配降级链 = 拦截即死（耗尽无出口）；降级不配标记 = 假降级（U3）；缓存不配版本入键 = 陈旧命中。实现序：D4 catalog 链声明（纯数据/函数底座先行）→ D1 budget.py → D2 降级接线 → D3 缓存 → D5 指标 → D6 断言收口。

### R3 · 失败语义

SPEC §5 八条全收翻四列加过程三共十一条。防假降级是全波铁律：链末端 ok=False+degraded 不伪造成功；重启归零如实定性（进程内=热路径保护 · 持久对账走 usage 表）；单价表缺失 unknown 不伪造 0（承不写 0 假账）。

### R4 · 可测性

验收 16 条全部可执行：预估下限 vs 真实记账双断言（防空真「预估=承诺」误读）· degraded 标记是变异检验式（摘除→必挂）· 缓存失效三触发（模型/prompt/catalog 哈希）· 集中性 grep 守护 · off 零 diff 由 1420 基线零改动证明。变异检验三条（标记/缓存键/拦截各配「破坏→必挂→恢复」）。

### R5 · 交付判定

可交 20-task-audit：与 SPEC 实质差异为零；HG-AUDIT-R1 落稿时待签；残余风险三条承 R3 如实携带。

### 自检结论

本稿：范围/非范围/验收/failure_paths 逐块映射 SPEC（§2→D1–D6 · §3→非范围 · §5→failure_paths+过程三 · §6→验收 16 条）；钉死契约自 SPEC §2/§4/§5 锁死；B1 实扫 5+1 组三态齐全；闸表四行诚实；思考轮 R0–R5 回填齐全无跳轮。

---

## 修订记录

| 日期 | 摘要 |
|------|------|
| 2026-09-23 | 10-task 落稿（SPEC signed 后 · 00 亲起）：锚点逐个复核（usage 末帧纪律 · catalog :118-177 · fallback :23-38 · capability budget/circuit 先例）· 命名冲突扫零命中 · pytest 基线 1420 真跑 · B1 5+1 组落盘 · HG-TASK-DRAFT 00 代录 approved（双令留痕）· HG-AUDIT-R1 pending 待 20-task-audit |
| 2026-09-23 | 20-task-audit R1 **PASS-WITH-NITS**（零阻塞 · 审查文 `docs/harness/reviews/task_host_v1_llm_factory_closure_audit_R1_20260923.md`）；N1 计数 15→16 · N2 factory.py 锚点描述修正（统一入口=base.py:31-52 __init_subclass__）· N3 D6 标题 §6-10 映射注明；**00 代录 HG-AUDIT-R1=approved**（维护者令原话+本窗双令留痕）· 30 可委派开工（分支 `task/host-v1-llm-factory-closure` · 与 V1-B 并行零文件交叠） |
