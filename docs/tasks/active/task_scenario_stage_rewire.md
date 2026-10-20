# Task：scenario-stage-rewire（scenario stage 恒短路死代码摘除 · 裁定分支 (a) · 逐值等价）

- **状态**：draft（2026-10-20 10-task 落稿 · 待 20-task-audit R1 → HG-AUDIT-R1 → 30）
- **类型**：cleanup（死代码摘除 · 不新增路由/表/一级模块/SSE event_type · 无契约变更）
- **依据**：`docs/spec/scenario-stage-rewire/SPEC-scenario-stage-rewire_v0.md`（v0.1 · **signed · HG-SPEC-SIGNOFF=approved 2026-10-19 维护者 · 裁定分支 (a) 摘除**）+ `docs/harness/reviews/spec_scenario-stage-rewire_audit_R1_20261019.md`（R1 conditional_pass → v0.1 闭合 → R2 pass）
- **建议序**：3/5（query-coref-rewrite 已合 PR #284 · memory-injection-consumer 已合 PR #285 → **本 task** → delegation-naming-boundary → tech-graph-flow-resync）
- **分支**：本文件落盘于文档线 `docs/task-scenario-stage-rewire`（自 master `51e75c9` 切出）；30 开工分支 `task/scenario-stage-rewire`（30 开工前自 master 另行切出 · 勿与文档线混用）

## Harness 元信息

| 字段 | 值 |
|---|---|
| **task_slug** | `scenario-stage-rewire` |
| **git_branch** | `task/scenario-stage-rewire`（30 开工自 master 切出 · 最新 base 30 按实钉锚） |
| **implement_repo** | ops-desk-api（本仓） |
| **spec** | `docs/spec/scenario-stage-rewire/SPEC-scenario-stage-rewire_v0.md`（v0.1 signed · 裁定 (a)） |
| **test_strategy** | required |
| **test_strategy_note** | 摘除死路径 · 逐值等价回归（摘除前后 allowlist 逐 id 对拍）+ env 失效断言 + dormant 存活断言 + diff 白名单；不打真模型；全量 pytest 绿 |
| **code_quality_bar** | L2_backend |
| **graph_change_layer** | none（预期 · 图谱 G-L1 备注级追加不构成层级变更） |
| **graph_delta** | `docs/_tech_graph/l1/01_modules.md` lg_rag 行（:35）「路径覆盖补记」strategy 段备注追加「scenario 裁剪已摘除（恒短路清理 · 2026-10-20 · 模块 dormant 保留）」；不新增/撤销一级模块 · 零新跨模块边 · 不增 implementedBy |
| **graph_delta_note** | N1 吸收：strategy 无独立一级模块行（薄包先例归属 lg_rag 行），故图谱同步口径 = lg_rag 行 strategy 段备注追加，而非新行；30 实判越出 → 回炉补签 HG-GRAPH-MODULES |
| **wiki_delta** | `docs/guides/GUIDE_env_inventory_v1.md`（:35 LG_RAG_VISIBILITY_SCENARIO_MODE 行备注列追加 deprecated 标注） |
| **wiki_delta_note** | env 键本体保留登记（防历史配置困惑），仅标废弃 |
| **review_hat** | 20 |
| **required_invoke_hats** | 10,20,30,40 |
| **invoke_retention_profile** | default（`docs/harness/invokes/by-task/scenario-stage-rewire/` · 本文件起草即建目录占位） |
| **experience_capture** | required |
| **kpi_aggregator** | n/a |
| **orchestration** | 10 落稿（本文件）→ 20-task-audit R1 → HG-AUDIT-R1（维护者已授权 00 代签后续文档闸 · 落闸动作在 20-task-audit 之后由 00 执行，起草时 pending）→ 30（红测先行 · 摘除实施）→ 40 → PR+CI 绿 → CLOSE → 下游棒：delegation-naming-boundary（建议序 4/5 · 另 SPEC/task） |
| **freeze_id** | 对照 `lg-rag-sse-v1` / `lg-rag-http-v1`：SSE 帧与 HTTP 请求/响应**零变化**（承 SPEC「无契约变更」）；30 实判需动帧 → 回 SPEC 升 freeze，禁 silent 扩 |

### 人工闸

| 闸 | 状态 | 阻塞 | 备注 |
|---|---|---|---|
| HG-SPEC-SIGNOFF | **approved**（2026-10-19 维护者） | 20 书面审 | SPEC v0.1 文末 · 含裁定记录：分支 **(a) 摘除** |
| HG-AUDIT-R1 | **pending** | 30 改码 | 维护者已授权 00 代签后续文档闸 · **落闸动作在 20-task-audit 之后由 00 执行**，起草时一律 pending；**未签不得 30** |
| HG-GRAPH-MODULES | **approved**（在册 · `docs/_tech_graph/l1/01_modules.md` 闸登记表） | 30 改码 | `graph_change_layer=none` 预期不再签；30 实判越出（新行/新边）→ 回炉补签 |

---

## 背景与目标

### 问题（承 SPEC §1）

scenario stage（`app/ops/strategy/scenario.py` + `builder.py` 内 `_apply_scenario_stage`）已**名存实亡**：`scenario.py:71-75` 无 intent 恒短路返回 `(visible, [])`（与 env 档位无关），而唯一 intent 写入方 `app/ops/strategy/intent.py:94` 自 supervisor-first 改造起**从未挂载进任何图**（`multi/graph.py` / `lg_rag/graph.py` 均无 `intent_node`）。死配置（LG_RAG_VISIBILITY_SCENARIO_MODE 三档永无效）、假台账、误导性图谱语义三重代价。

### 目标（承 SPEC §1 一句话目标 · 裁定 (a) 摘除）

删 `builder.py` 内 `_apply_scenario_stage` 调用与死分支，allowlist 语义固定为「candidates ∩ 基线可见集」直接求交（**与现行恒短路输出逐值等价**）；`scenario.py` 模块本体归档保留 + dormant 注释；env 键标 deprecated；图谱/env 台账同步。

## 范围

### D1 摘除面（`app/ops/strategy/builder.py` · 行号 10-task 于 master `51e75c9` 亲读复核，30 按实校正）

- 删 `builder.py:111-128` `_apply_scenario_stage` 函数本体、`:158` 唯一调用点、`:17-20` scenario 三件 import（`audit_scenario_stripped` / `scenario_mode` / `scenario_trim`）
- 删/改写过期注释：`:149` docstring「场景维裁剪（stage 2）在无 intent 时短路不裁」句、`:155-157` 两阶段注释 → 改写为「allowlist = candidates ∩ 基线可见集直接求交（scenario 阶段已摘除 · 2026-10-20）」；`app/ops/lg_rag/multi/nodes.py:1267` 注释「Builder 两阶段（基线→scenario_trim）收窄 allowlist」同步改写（**仅注释行 · 零逻辑变更**）；`multi/graph.py:82-83` 注释已述直接求交口径，不动
- `strategy_builder_node` 摘除后语义固定：`visible = get_policy_visible_catalog()` → `visible_ids` → `build_allowlist_from_candidates(candidates, visible_ids=visible_ids)`（逐值等价现行恒短路输出）

### D2 留尸面（`app/ops/strategy/scenario.py` dormant · 承 SPEC「模块本体不删」）

- 模块本体保留：`scenario_trim` S1–S5 纯函数（:55-96）、`audit_scenario_stripped`（:99-128）、`ENV_SCENARIO_MODE`（:38）、`scenario_mode`（:49-52）均不动
- 文件头追加 dormant 注释：名存实亡状态声明 + 「LG_RAG_VISIBILITY_SCENARIO_MODE 已废弃（2026-10-20）」+ 「无生产消费方」+ 「复用须另立 SPEC」
- 口径裁定（协调 SPEC D1「env 读取处删除」与「模块本体不删」）：**生产消费侧读取调用删除** = `builder.py:118` `scenario_mode()` 调用随 `_apply_scenario_stage` 一并删除；dormant 模块内 `os.environ.get`（:51）定义保留但无生产路径可达

### D3 env 登记

- `docs/guides/GUIDE_env_inventory_v1.md` :35 `LG_RAG_VISIBILITY_SCENARIO_MODE` 行备注列追加「已废弃（scenario 摘除 · 2026-10-20 · 键本体保留防历史配置困惑）」

### D4 图谱（N1 吸收）

- `docs/_tech_graph/l1/01_modules.md` :35 lg_rag 行「路径覆盖补记」strategy 段（host-v1-visibility-scenario-policy V1-B 备注处）追加「scenario 裁剪已摘除（恒短路清理 · 2026-10-20 · task_scenario-stage-rewire · 模块 dormant 保留）」；**不新增/撤销一级模块行**（strategy 薄包先例归属 lg_rag 行）

### D5 旧测处置（`tests/test_strategy_scenario.py` · N2 吸收 · 行号 30 按实校正）

- **删**：:189-256 env 三档与台账六用例（off 零 diff / invalid 回退 / observe would_strip / enforce 生效 / 台账不记内容 / enforce fallback 空集）——全部绑定被删 `_apply_scenario_stage` 与 env 三档行为
- **改写**：:259-270 `test_no_intent_short_circuits_all_modes`（TC6 短路断言）→ 改造为对 `strategy_builder_node` 直出 allowlist 的逐值回归（无 intent state × env 任意值 → allowlist ≡ candidates ∩ 基线可见逐 id 对拍）；:273-300 builder enforce no-intent 用例 → 去 env 耦合保留 allowlist 断言；:308-338 enforce high intent 裁 medium 用例 → 行为已死，改写为「intent 在场亦不裁」断言；:341-378 delegation_scope 用例 → 去 `sc.ENV_SCENARIO_MODE` setenv 耦合，保留 delegation_scope ⊆ allowlist 断言；:34-35 import 行去掉 `_apply_scenario_stage`
- **保留**：`scenario_trim` 纯函数 S1–S5 用例（:76-169）与计时 smoke（:386-395）原样保绿
- **新增**：env 失效断言（env ∈ {未设/off/observe/enforce/bogus} × intent {无/有含 high} → `strategy_builder_node` 输出逐值相等）

### D6 登记不动（N3 吸收 + 留尸口径）

- `app/ops/lg_rag/sse_stream.py:64` `"intent_node": "intent"` 死映射：**不动**（「不增删 SSE event_type」约束下保留正确；freeze `lg-rag-sse-v1` 不升），登记 invoke 引用清单「已知残留 · 不动」
- `app/ops/strategy/intent.py:94` 未挂载写入方：**留尸不摘**（与 SPEC §3「不顺手做其他 strategy 目录清理」互锁），登记 invoke 引用清单
- scenario / `intent_node` / `LG_RAG_VISIBILITY_SCENARIO_MODE` 全仓引用点清单（grep）落 invoke（承 SPEC §7 风险表）

## 非范围（承 SPEC §3 五条原样 + task 级补充）

- ❌ 删 `app/ops/strategy/scenario.py` 模块文件 / 删 IntentV1 schema
- ❌ 恢复 `intent_node` 进 supervisor 图（重接属分支 (b)，需另 SPEC）
- ❌ 改 `get_candidate_capability_ids` / 基线过滤器语义
- ❌ chat 图（410 legacy）任何改动
- ❌ 同 task 内顺手做其他 strategy 目录清理（含 `intent.py` 摘除、`sse_stream.py` 死映射清理）
- ❌ 本起草阶段零 `app/` `tests/` 改码（10-task 只落本文件 + invoke）
- ❌ 摘除面扩大到 SPEC D1 之外（30 不临场发明摘除对象）
- ❌ 删 `scenario.py` 内部函数（本体不删 · 仅文件头注释）

## 失败路径（failure_paths）

| ID | 触发条件 | 系统行为 | 可重试 | 用户可见 |
|---|---|---|---|---|
| FP-1 | 摘除连带破坏可见性基线路径（`get_policy_visible_catalog` / `build_allowlist_from_candidates` / delegation_scope 交集） | 逐值回归断言红：摘除前后 allowlist 逐值不等即 TC2 失败 | 是（git revert 逐值等价回滚语义） | 否（CI 拦截） |
| FP-2 | env 三档任意值 / 残留读取仍影响结果 | env 失效断言红（TC3）；生产路径 grep env 键仅命中 dormant `scenario.py` | 是 | 否 |
| FP-3 | SSE 帧契约被误动（`sse_stream.py` / 帧形 / event_type） | freeze `lg-rag-sse-v1` 不升；`sse_stream.py` 不在 diff 白名单内（TC8 拦截）；既有 SSE 测试绿 | 是 | 否 |
| FP-4 | 图谱不同步（摘除后 01_modules.md 备注未更新） | 备注断言红（TC6）；`graph-compile` EXIT=0 | 是 | 否 |
| FP-5 | 后续有人 import `scenario.py` | 模块仍在可 import（TC4 存活断言 + dormant 注释说明） | 是 | 否 |
| FP-6 | 旧测处置越界（误删合法回归） | K7 惯例：枚举外既有用例默认保持绿，误删即红 | 是 | 否 |
| FP-7 | HG-AUDIT-R1 未签即 30 开工 | GATE_VERIFY 拒开工（承 v2.14+ 拒改码口径） | 是 | 否 |
| FP-8 | 隐藏路径仍依赖 scenario 裁剪语义 | 全仓引用清单落 invoke（TC9）+ 逐值回归兜底 | 是 | 否 |
| FP-9 | 基线锚点不可解析（CI 浅克隆 / fork） | `_resolve_base` 三级探测退化至 merge-base，仍不可得 → `pytest.skip` 带实测 ref 状态（绝不静默 pass/fail） | 是 | 否（skip 可审计） |

## 验收标准

- [ ] **TC1 摘除面机断**：grep 断言 `builder.py` 无 `_apply_scenario_stage` / `scenario_mode` / `scenario_trim` / `audit_scenario_stripped` 残留（import/调用/注释引用全清）；`multi/nodes.py` 无 `scenario_trim` 注释残留。
- [ ] **TC2 逐值回归（承 SPEC FP-1）**：`strategy_builder_node` 在 {无 intent} × {candidates 矩阵} 下 allowlist ≡ candidates ∩ 基线可见（逐 id 对拍，含顺序）；与摘除前恒短路输出逐值相等。
- [ ] **TC3 env 失效（承 SPEC FP-2）**：`LG_RAG_VISIBILITY_SCENARIO_MODE` ∈ {未设/off/observe/enforce/bogus} × intent {无/有含 high} → 输出逐值相等；`app/` 生产路径 grep 该 env 键仅命中 dormant `scenario.py`。
- [ ] **TC4 dormant 存活**：`import app.ops.strategy.scenario` 成功 + `scenario_trim` S1–S5 既有用例保绿 + 文件头 dormant 注释存在（含废弃 env 键名与 2026-10-20 日期）。
- [ ] **TC5 SSE/HTTP 契约零动**：freeze `lg-rag-sse-v1` / `lg-rag-http-v1` 不升；`sse_stream.py`、router 面零 diff（TC8 白名单断言拦截）；既有 SSE/invoke 测试全绿。
- [ ] **TC6 图谱与 env 登记同步**：`01_modules.md` lg_rag 行备注含「scenario 裁剪已摘除」字样断言；`GUIDE_env_inventory_v1.md` `LG_RAG_VISIBILITY_SCENARIO_MODE` 行含 deprecated 标注；`./scripts/graph-compile.sh` EXIT=0。
- [ ] **TC7 旧测处置落实（N2/K7）**：D5 枚举逐项落实（删六项 / 改写四项 / 保留 S1–S5+smoke / 新增 env 失效断言）；枚举外既有用例默认保持绿（误删合法回归即红）。
- [ ] **TC8 diff 白名单（#2 教训 · _resolve_base 式三级探测强制）**：改动面 ⊆ {`app/ops/strategy/builder.py`、`app/ops/strategy/scenario.py`（仅文件头注释）、`app/ops/lg_rag/multi/nodes.py`（仅注释行）、`tests/test_strategy_scenario.py`、`docs/_tech_graph/l1/01_modules.md`、`docs/guides/GUIDE_env_inventory_v1.md`、`docs/harness/invokes/by-task/scenario-stage-rewire/**`、`docs/tasks/active/task_scenario_stage_rewire.md`}；基线锚点解析必须采用三级探测——① `git rev-parse --verify {钉锚}^{commit}` → ② 退化 `merge-base HEAD origin/{GITHUB_BASE_REF 或 master}`（双 ref 试）→ ③ 仍不可得 `pytest.skip` 带实测 ref 状态（绝不静默 pass/fail）；实现照抄 `tests/test_memory_injection_consumer.py:585-609` `_resolve_base` + 三路 diff + untracked 枚举口径。
- [ ] **TC9 引用清单落 invoke**：scenario / `intent_node` / `LG_RAG_VISIBILITY_SCENARIO_MODE` 全仓引用点清单落 `docs/harness/invokes/by-task/scenario-stage-rewire/`，含 `sse_stream.py:64` 与 `intent.py:94`「已知残留 · 不动」登记（承 SPEC §7 风险表）。
- [ ] **TC10 反回归全量**：`pytest tests` 全量绿（摘除后全量对拍）；`ruff check app tests` 触及路径绿；不增 event_type / 路由 / 表。

## 依赖

- base：master `51e75c9`（PR #285 已合）；文档线 `docs/task-scenario-stage-rewire`；30 分支 `task/scenario-stage-rewire`
- SPEC：`docs/spec/scenario-stage-rewire/SPEC-scenario-stage-rewire_v0.md`（v0.1 signed）；审查文：`docs/harness/reviews/spec_scenario-stage-rewire_audit_R1_20261019.md`（R1/R2）
- 代码锚点（10-task 已于 master `51e75c9` 亲读复核 · 行号 30 按实校正）：`builder.py:17-20` import · `:111-128` 函数本体 · `:118` scenario_mode() 调用 · `:149/:155-158` docstring 与调用点；`scenario.py` 全文 128 行（:38 ENV · :49-52 mode · :55-96 trim · :71-75 恒短路 · :99-128 台账）；`intent.py:94`；`sse_stream.py:62-66` _ROLE_ALIAS；`multi/nodes.py:1267` / `multi/graph.py:82-83` 注释
- `_resolve_base` 先例：`tests/test_memory_injection_consumer.py:585-609`（三级探测）+ `:612-627`（diff 白名单断言）
- 编码规范：`docs/standards/CODING_BACKEND_L2_v1_zh.md`
- 结构先例：`docs/tasks/done/task_memory_injection_consumer.md`、`docs/tasks/done/task_query_coref_rewrite.md`

## 给执行帽的必读列表

1. 本 task 全文（含人工闸表 · **HG-AUDIT-R1=pending 未签不得 30**）
2. `docs/spec/scenario-stage-rewire/SPEC-scenario-stage-rewire_v0.md`（裁定 (a) 摘除 · 逐值等价口径）
3. `docs/harness/reviews/spec_scenario-stage-rewire_audit_R1_20261019.md`（N1–N4 移交项）
4. `app/ops/strategy/builder.py`、`app/ops/strategy/scenario.py` 全文亲读（摘除前再复核行号）
5. `tests/test_memory_injection_consumer.py:585-609` `_resolve_base`（TC8 实现蓝本 · 禁临场发明基线解析）
6. `docs/harness/prompts/FRAGMENT_30_gate_verify_v1_zh.md`（30 开工 GATE_VERIFY）

## 思考轮控制

| 轮 | 结论 | early_stop | reason（early_stop） | residual_risks |
|---|---|---|---|---|
| R0 问题框定 | 名存实亡三重代价坐实 · 裁定 (a) 摘除已签 | 否 | — | 无 |
| R1 范围收束 | 摘除面=builder.py 死路径+注释；留尸面=scenario.py dormant+intent.py 不摘+sse 死映射不动 | 否 | — | SPEC D1 与「本体不删」口径张力 → D2 裁定协调 |
| R2 方案与裁定吸收 | N1→D4 图谱 lg_rag 行备注 · N2→D5 旧测处置 · N3→D6 登记不动 · N4→invoke 占位 | 否 | — | 无 |
| R3 反例与边界 | FP-1~FP-9 完备（连带破坏/env 残留/契约/图谱/闸/基线退化） | 否 | — | FP-8 隐藏依赖 → TC9 引用清单兜底 |
| R4 验收可测性 | TC1–TC10 全机断 · TC8 三级探测照抄 _resolve_base · 不打真模型 | 否 | — | CI 浅克隆 → FP-9 可审计 skip |
| R5 收口 | 零 app/ 改码 · 未代签任何闸 · draft 待 20-task-audit | 是 | draft 面已完备，后续轮次由编排推进 | HG-AUDIT-R1 pending 待 00 落签 |

### R0 · 问题框定

恒短路三重坐实承审查文：`scenario.py:71-75` 无 intent 全短路（与 env 档位无关）；唯一写入方 `intent.py:94` 未挂载；上游 supervisor-first task TC6 已落机验。

### R1 · 范围收束

摘除面/留尸面/登记面三面分离：builder.py 死路径摘除（D1）；scenario.py 本体不删 + dormant 注释（D2）；intent.py:94 与 sse_stream.py:64 留尸登记不动（D6）。SPEC D1「env 读取处删除」与「模块本体不删」的口径张力在 D2 显式裁定：生产消费侧读取调用删除，dormant 模块内定义保留。

### R2 · 方案与 N1–N4 裁定吸收

N1（图谱无 strategy 独立行）→ D4：lg_rag 行「路径覆盖补记」strategy 段备注追加，不新行。N2（旧测绑定被删函数）→ D5：删六项/改写四项/保留 S1–S5+smoke/新增 env 失效断言。N3（sse_stream.py:64 死映射）→ D6：不动 + 引用清单登记。N4（invoke 目录缺失）→ 本帽补建占位。

### R3 · 反例与边界

最坏情形枚举：摘除连带破坏可见性基线路径（FP-1 · TC2 逐值回归拦截）；env 残留影响（FP-2 · TC3）；SSE 契约误动（FP-3 · TC5+TC8）；图谱/env 台账不同步（FP-4 · TC6）；误删合法回归（FP-6 · TC7 K7）；闸未签开工（FP-7）；隐藏依赖（FP-8 · TC9）；基线不可解析（FP-9 · TC8 skip 可审计）。

### R4 · 验收可测性

TC1–TC10 全可机断（grep/断言/exit code 级）；TC8 强制 `_resolve_base` 三级探测（吸收 #2 教训：钉锚 → merge-base 退化 → 可审计 skip），实现蓝本钉 `tests/test_memory_injection_consumer.py:585-609`；全程不打真模型。

### R5 · 收口

本帽只落 task 文件 + invoke 占位两处分；零 `app/` `tests/` 改码；未代签任何闸。后续轮次由编排推进：20-task-audit R1 → HG-AUDIT-R1（00 代签）→ 30 → 40 → PR+CI 绿 → CLOSE。

### 自检结论（10-task · 2026-10-20）

- **验收全可机断**：TC1–TC10 均 grep/断言/exit code 级，无人工目测项；TC8 基线解析强制三级探测，禁临场发明。
- **failure_paths 完备**：摘除连带破坏 visibility/verbosity 路径（FP-1/FP-8）、SSE 映射残留与契约（FP-3）、图谱不同步（FP-4）三大父指令点名面全覆盖，另含闸纪律（FP-7）与基线退化（FP-9）。
- **N1–N4 吸收落点齐备**：N1→D4 · N2→D5+TC7 · N3→D6+TC9 · N4→invoke 目录占位。
- **纪律**：未代签任何闸（HG-AUDIT-R1 pending 待 20-task-audit 后 00 落签）；零 `app/` 改码；未改 SPEC。

## 修订记录

- 2026-10-20 v0.1（10-task 落稿 · 自 master `51e75c9` 切出文档线 `docs/task-scenario-stage-rewire`）
