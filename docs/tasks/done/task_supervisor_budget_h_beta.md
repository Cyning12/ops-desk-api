# Task：阶段 H · 波次 β · supervisor 总预算

> **状态**：`completed`（2026-09-17 · 00 CLOSE PASS · 待维护者 commit/PR）  
> **上游**：`docs/discussions/2026-09-17_interview_gaps_adoption_and_landing_v0.md` §5 波次 β 项 6 · §8 阶段 H  
> **分支**：`task/supervisor-budget-h-beta`  
> **类型**：feature / 编排预算  
> **无关**：禁止扩阶段 T/W/P；禁止改 SSE freeze / `chat/graph.py`；禁止服务化 Registry。  
> **00 注**：2026-09-17 · 00 代签过程闸授权开启 · 本窗只落壳与编排 · 默认不亲自 30  
> **10 注**：2026-09-17 · 钉死总步默认 / 计数点位 / 耗尽→aggregate / 墙钟降级 / 与既有 4·1+1 共存

---

## Harness 元信息

| 字段 | 值 |
|------|-----|
| **task_slug** | `supervisor-budget-h-beta` |
| **git_branch** | `task/supervisor-budget-h-beta` |
| **implement_repo** | `ops-desk-api` |
| **test_strategy** | `required` |
| **test_strategy_note** | 先单测预算耗尽路径（`route_next_subtask` / 可选 `route_after_critic`）再改图/节点；不连真外网 / 不连真 Langfuse 云 |
| **code_quality_bar** | `L2_backend` |
| **graph_change_layer** | `G-L1` |
| **graph_delta** | `docs/_tech_graph/l1/01_modules.md`（lg_rag 备注）· 可选 `10_flow_*` 一句 |
| **graph_delta_note** | **不新增**一级模块；仅备注 supervisor 总预算 / 耗尽→aggregate |
| **wiki_delta** | `n/a` |
| **wiki_delta_note** | 口径「注册表」若触及文档保持否定「注册中心」；推行纪律可一句挂 coding_wiki（可选） |
| **review_hat** | `20` |
| **required_invoke_hats** | `10,20,30,40` |
| **invoke_retention_profile** | `default` |
| **orchestration** | Cursor Task 链 · 00 统筹 |
| **semi_auto** | `false` |
| **audit_profile** | `full` |
| **freeze_id** | 无 |
| **experience_capture** | `recommended` |
| **kpi_aggregator** | `CLOSE` |

### 人工闸

| human_gate_id | status | blocks_hats | 说明 |
|---------------|--------|-------------|------|
| HG-TASK-DRAFT | approved | 22-R1, 30 | 2026-09-17 · 00 代签 · 维护者令开启 · 10 补全 + 20 PASS-with-nits |
| HG-AUDIT-R1 | approved | 30 | 2026-09-17 · 00 代签 · 维护者令开启 · 审查文 `docs/harness/reviews/task_supervisor_budget_h_beta_audit_R1_20260917.md` |
| HG-GRAPH-MODULES | approved | 30 | 2026-09-17 · 00 代签 · 维护者令开启 · 仅 G-L1 备注、不新增一级模块（30 改图谱后回写 `01_modules.md` 签收行） |

---

## 背景与目标

波次 α 已 CLOSE（契约硬化）。β 要补 **supervisor 总预算**（讨论稿 §5 项 6 / Q4「并发子任务预算会计」）：现有 `MAX_SUBTASKS=4` 与 critic `MAX_INNER_RETRIES`/`MAX_REBINDING`（各 1）只约束局部；缺「总步数」耗尽后强制收束（**耗尽→aggregate**，防幻觉循环；保留部分结果综合，**不**直跳 END）。

本 task 一竖切：定义预算字段与默认值 → 图内计数/检查 → 耗尽行为单测 → 文档/图谱备注。产品仍只读单租户；**不**做多租户/写/HITL。

---

## 现状锚点（只读 · 10 实扫 · 30 必读）

| 主题 | 路径 · 锚点 | 现状缺口 |
|------|-------------|----------|
| 子任务上限 | `app/ops/lg_rag/multi/nodes.py` L48 `MAX_SUBTASKS = 4`；`_parse_subtasks` L156 `items[:MAX_SUBTASKS]` | 仅截断子任务数，非总步/墙钟 |
| dispatch 耗尽 | 同文件 `route_next_subtask` L277–286：`_pending_subtask is None` → `"aggregate"` | 子任务列表耗尽，非全局预算；尚无 step 守卫 |
| 三 agent 回边 | `app/ops/lg_rag/multi/graph.py` L41–47 `_DISPATCH_MAP`；L77–79 supervisor/agent → `route_next_subtask` | 可在此路由加「总步耗尽 → aggregate」 |
| Critic 预算 | `app/ops/strategy/critic.py` L14–15 `MAX_INNER_RETRIES=1` · `MAX_REBINDING=1`；`decide_critic_verdict` L34–42 超限 → `"end"`；`_REASON_BUDGET` L20 | 仅 retry/rebind 回数；超限走 END（非 aggregate） |
| Critic 边 | `graph.py` L49–55 `_CRITIC_MAP`：pass/end→END；retry→supervisor；rebind→strategy_builder | 全局耗尽后须禁止再 retry/rebind |
| 状态 | `app/ops/lg_rag/state.py` `LgRagState`：有 `inner_retry_count` / `rebinding_count`；**无**总步/墙钟字段 | 须增 `supervisor_step_count`（及可选耗尽旗标） |
| 既有单测 | `tests/test_lg_rag_multi.py`（含 `test_empty_subtasks_dispatch_goes_aggregate`）· `tests/test_critic_rebind.py` · `tests/test_lg_rag_supervisor_capability_catalog.py` | 回归面；本波扩预算耗尽测 |

拓扑真值（`graph.py` 模块 docstring）：

```text
START → intent_node → strategy_builder → supervisor → dispatch
  ├─ rag / extract / tool → 回 dispatch
  └─ 耗尽/空 → aggregator → critic_node
       ├─ pass / end → END
       ├─ retry_planner → supervisor
       └─ rebind → strategy_builder
```

---

## 10 钉死契约（00/30 不得静默改义）

| 项 | 钉死 |
|----|------|
| **总步默认值** | **`32`** · 常量名建议 `MAX_SUPERVISOR_STEPS` · env 建议 `LG_RAG_SUPERVISOR_MAX_STEPS`（缺省 `"32"`；非法/≤0 时 30 须安全回退到 32，禁静默「无限」） |
| **为何 32** | 覆盖既有 4·1+1 最坏路径约 ~22 次 supervisor 图节点访问 + 缓冲，避免误伤金样；仍远低于「幻觉空转」无界 |
| **计数范围** | **仅** supervisor `StateGraph` 节点入口递增：`intent_node` · `strategy_builder` · `supervisor` · `rag_subtask` · `info_extract` · `tool_exec` · `aggregator` · `critic_node`。**不计** `rag_subtask` 内部 router 子图节点 |
| **递增时机** | 各上列节点执行时 +1（共享 helper 或等价）；计数写入 state 键建议 `supervisor_step_count`（无 reducer · 缺省 0） |
| **检查点位** | **主闸**：`route_next_subtask`——若 `supervisor_step_count >= MAX_SUPERVISOR_STEPS`（或耗尽旗标已置），**即使仍有 pending 子任务** 也返回 `"aggregate"`。**辅闸**：`route_after_critic` / `decide_critic_verdict`——若全局已耗尽，禁止 `retry_planner`/`rebind`，强制 `"end"` |
| **耗尽边目标** | **`aggregate`（→ `aggregator` 节点）**，**禁止**耗尽时直跳 `END`（保留部分结果综合） |
| **耗尽语义** | 可写 `supervisor_budget_exhausted=True`（建议）；未跑完的子任务**不**伪造结果；aggregator 综合已有 `subtask_results`（与既有 error 部分结果姿态一致） |
| **墙钟** | **本竖切降级为「仅总步」硬门**。墙钟 **非验收硬门**：允许 30 薄实现 env `LG_RAG_SUPERVISOR_MAX_WALL_SECONDS`（默认 **`0`=关闭**）+ 可选 state `supervisor_started_at`；若开启且超时，**同耗尽姿态→aggregate**。未实现墙钟不算本 task 失败 |
| **与 MAX_SUBTASKS=4** | **并存**：解析期仍截断 ≤4；总步是跨节点全局上限，不替代 cap |
| **与 critic 1+1** | **并存 + 优先级**：全局总步/墙钟耗尽 **优先于** 局部 retry/rebind 额度——已耗尽则不得再进 supervisor/Builder 回环；未耗尽时 critic `MAX_INNER_RETRIES`/`MAX_REBINDING` 语义不变 |
| **优先级一句** | **任一**（总步耗尽 · 墙钟超时（若开）· critic 局部额度耗尽）即收束；总步/墙钟收束点是 **aggregate**，critic 局部额度耗尽收束点仍是 **END**（既有） |

---

## 范围（同 task 竖切）

- [x] **B1 · 总步数预算（硬门）**：`MAX_SUPERVISOR_STEPS` / `LG_RAG_SUPERVISOR_MAX_STEPS` 默认 32；state `supervisor_step_count`；上列节点递增；`route_next_subtask` 耗尽→`"aggregate"`；建议耗尽旗标
- [x] **B2 · 墙钟（可选薄 · 非硬门）**：默认关闭；若实现则超时同→aggregate；须可单测（注入 fake clock / 极小阈值）
- [x] **B3 · 与既有预算共存**：不破坏 `MAX_SUBTASKS=4` / critic 1+1；辅闸阻止耗尽后再 retry/rebind；文档/注释写清优先级
- [x] **B4 · 单测**：① 人为压低 `MAX_SUPERVISOR_STEPS`（或直接垫高 `supervisor_step_count`）→ `route_next_subtask` 断言 `"aggregate"`；② 未耗尽路径回归绿（`test_lg_rag_multi` / critic 测）；③ 若做辅闸：耗尽后 critic 不得 retry/rebind
- [x] **B5 · 图谱/口径（薄）**：G-L1 `01_modules.md` lg_rag 备注一句；触及文档保持「进程内注册表」；讨论稿 §5 项 7–8 零码可顺手一句，**非**硬门

**竖切结论**：B1+B3+B4 **同 task 必交**；B2 可选；B5 薄备注。

---

## 非范围

- 阶段 T / W / P（多租户产品 / 写·HITL / 服务化 Registry·本体平台）
- 改 SSE freeze、idle keepalive 契约、chat 410 叙事
- 改 `app/ops/chat/graph.py`（**零 diff**）
- 完整多 Agent attenuation / 跨 run confirmation
- 服务化 Registry / 本体包
- 把 router 子图内节点计入 supervisor 总步
- 耗尽直跳 END（跳过 aggregator）

### 跟进（非本 task 验收）

- 墙钟硬门化（若 β 后观测需要）
- 讨论稿 §5 项 7–8 文档口径专竖切（若本波零码未做）

---

## 失败路径（failure_paths）

| 触发条件 | 系统行为 | 可重试 | 用户可见 |
|----------|----------|--------|----------|
| `HG-AUDIT-R1` pending 即 30 改码 | 执行 Agent **拒开工** | 是 | 须先 20 + 闸签 |
| 总步 ≥ `MAX_SUPERVISOR_STEPS` | `route_next_subtask` → `"aggregate"` · 图不垮 · 建议置 `supervisor_budget_exhausted` | 否（本 run） | 是（部分综合答案；可经 span/metadata） |
| 墙钟超时（若开启） | 同总步耗尽姿态 → aggregate | 否（本 run） | 是 |
| 全局已耗尽仍触 critic | 禁止 retry/rebind · 强制 `"end"` | 否 | 是（以已综合答案结束） |
| critic 局部 1+1 耗尽（全局未耗尽） | 既有：outcome=`end` → END | 否 | 是 |
| `MAX_SUBTASKS` 截断 | 既有：plan 超 4 截断，非 fallback | 否 | 间接（少子任务） |
| 误扩 T/W/P 或改 SSE freeze / `chat/graph.py` | 审查/verify **拒收** | 是（回滚） | 否（内部） |
| 默认预算过小打爆金样 | 20/40 拒收或回调默认（须改 task/钉死表，禁静默改 32→更小） | 是 | 否（内部） |
| env 非法导致「无限步」 | 实现须回退默认 32；审查拒收无上限路径 | 是 | 否 |

---

## 验收标准

- [x] 存在可配置 supervisor 总步预算：常量/env 默认 **32**（名见钉死表）
- [x] state 含 `supervisor_step_count`（及建议 `supervisor_budget_exhausted`）；计数点位符合钉死表（不计 router 子图）
- [x] 耗尽时 `route_next_subtask` → `"aggregate"`（**非** END）；有单测可断言
- [x] 全局耗尽后 critic **不得**再 `retry_planner`/`rebind`（辅闸或等价）；有单测或与既有 `test_critic_rebind` 扩断言
- [x] `MAX_SUBTASKS=4` 与 critic `MAX_INNER_RETRIES`/`MAX_REBINDING`=1 行为不无故破坏
- [x] **旧测 grep 影响面**：`tests/test_lg_rag_multi.py` · `tests/test_critic_rebind.py` · `tests/test_lg_rag_supervisor_capability_catalog.py` 回归绿（默认 32 下既有路径不得被误杀）
- [x] `pytest tests/test_lg_rag_multi.py tests/test_critic_rebind.py tests/test_lg_rag_supervisor_capability_catalog.py -q` 绿（30 可按新增测文件扩列表）
- [x] `ruff check app/ops/lg_rag/multi app/ops/lg_rag/state.py app/ops/strategy/critic.py tests`（触及路径）绿
- [x] 若改图/G-L1 备注：`./scripts/graph-compile.sh` 绿
- [x] `npx --yes spec-wave task lint-wiki-delta --target .` 通过
- [x] `chat/graph.py` 零 diff；不新增 G-L1 一级模块；未扩 T/W/P；未改 SSE freeze
- [x] 墙钟：未实现可勾「降级跳过」；若实现则默认 0=关且超时→aggregate 有测

---

## 依赖

- 上游决议：`docs/discussions/2026-09-17_interview_gaps_adoption_and_landing_v0.md`（§5 β 项 6 · §8 H）
- α 归档对照：`docs/tasks/done/task_capability_contract_hardening.md`（非范围：β 预算曾挂账）
- 编码规范：`docs/standards/CODING_BACKEND_L2_v1_zh.md`
- 图谱：`docs/_tech_graph/l1/01_modules.md`
- 设计参考：`docs/guides/DESIGN_langgraph-lg-rag-phase4-multiagent_v1.md`（§1 拓扑 · §3 supervisor）
- 闸片段：`docs/harness/prompts/FRAGMENT_30_gate_verify_v1_zh.md`

---

## 给执行帽的必读列表

1. `AGENTS.md`
2. 本 task（全文 · 尤其「10 钉死契约」与非范围）
3. `docs/discussions/2026-09-17_interview_gaps_adoption_and_landing_v0.md` §5 β 项 6 · §8 H（**勿做** T/W/P）
4. `docs/standards/CODING_BACKEND_L2_v1_zh.md`
5. 代码锚点：`app/ops/lg_rag/multi/graph.py` · `app/ops/lg_rag/multi/nodes.py` · `app/ops/strategy/critic.py` · `app/ops/lg_rag/state.py`
6. 既有测：`tests/test_lg_rag_multi.py` · `tests/test_critic_rebind.py`
7. α 归档：`docs/tasks/done/task_capability_contract_hardening.md`
8. 过程 invoke：`docs/harness/invokes/by-task/supervisor-budget-h-beta/`
9. `docs/harness/prompts/FRAGMENT_30_gate_verify_v1_zh.md`（30 首输出闸扫描）

---

## 思考轮控制

| 轮 | 结论 | early_stop | reason（early_stop） | residual_risks |
|----|------|------------|----------------------|----------------|
| R0 | β = supervisor 总预算收束，非平台 Registry / 非 T/W | no | — | none |
| R1 | 优先总步硬门；墙钟本竖切降级可选 | no | — | 墙钟若后补需同姿态 |
| R2 | 耗尽边钉 **aggregate**（非 END）；保留部分综合 | no | — | none |
| R3 | 默认 32；计 supervisor 图节点、不计 router 子图；主闸在 `route_next_subtask` | no | — | 默认过紧误伤金样 |
| R4 | 与 4·1+1 并存；全局耗尽优先禁 critic 回环；停轮 | yes | 钉死表齐；代码锚点已实扫；R5 无新增决策面 | 默认 32 若金样仍紧由 20/40 回调 task；30 须防 env≤0 变无限 |
| R5 | （未开） | — | early_stop at R4 | — |

**actual_last_round**：R4 · **early_stop**：yes · **reason（early_stop）**：钉死表与代码锚点已齐；再开 R5 无新增决策面 · **residual_risks**：见 R4 行

### R0 · 问题框定

波次 β 项 6 = 补 supervisor **总预算**与耗尽收束；产品仍是 lg_rag 单图编排，不是服务化 Registry / 多 Agent 平台。阶段 T/W/P 明确不进本竖切。

### R1 · 总步 vs 墙钟

讨论稿写「步数/墙钟」；壳 B2 标可选。本竖切 **总步硬门**、**墙钟降级**（默认关、非验收硬门），避免 fake clock / 注入面拖垮 30，同时保留同姿态扩展点。

### R2 · 耗尽边

直跳 END 会跳过 aggregator，部分子任务结果无法综合。钉 **耗尽→aggregate**（与讨论稿 Q4 / 壳倾向一致）；critic 局部额度耗尽仍走既有 END。

### R3 · 默认与计数

`MAX_SUBTASKS=4` + critic 1+1 最坏约 ~22 次 supervisor 图节点访问 → 默认 **32** 留缓冲。只计本图节点入口，**不计** `rag_subtask` 内 router 子图（否则一步 RAG 可吃光预算）。主闸落 `route_next_subtask`。

### R4 · 共存与停轮

全局耗尽 **优先于** critic 回环额度（辅闸禁 retry/rebind）；未耗尽时 4·1+1 语义不变。钉死表齐、锚点已扫 → early_stop。

### R5

（提前停 · 未开）

---

## 实现备忘（子 Agent 回填）

| 项 | 状态 | 备注 |
|----|------|------|
| 10 补全 | ✅ | 2026-09-17 · 钉死 32 / aggregate / 墙钟降级 / 4·1+1 优先级 |
| 20 审查 | ✅ | 2026-09-17 · PASS-with-nits · 审查文 audit_R1_20260917 · 00 代签闸 |
| 30 实现 | ✅ | 2026-09-17 · B1+B2+B3+B4+B5 · 交 40 |
| 40 verify | ✅ | 2026-09-17 · 门禁全绿 · 无小修 · 交 50+CLOSE |

### 30 建议落点（非强制实现细节）

1. `state.py`：增 `supervisor_step_count: int`；建议 `supervisor_budget_exhausted: bool`
2. `nodes.py`：常量 + env；agent/supervisor/aggregator 入口 bump；`route_next_subtask` 读计数
3. `critic.py`：辅闸读全局耗尽旗标/计数
4. `intent_node` / `strategy_builder_node`：同图路径须 bump（在各自模块或薄包装——**勿**为 bump 去改 `chat/graph.py`）
5. 单测优先纯函数级（route）再考虑整图 mock

---

### 自检结论

| 检查 | 结果 |
|------|------|
| `npx --yes spec-wave@2.4.2 task lint --file docs/tasks/active/task_supervisor_budget_h_beta.md` | **PASS**（2026-09-17 · 10） |

### 自检结论（执行者）

| 检查 | 结果 |
|------|------|
| GATE_VERIFY + `spec-wave verify` | **PASS**（闸三行 approved） |
| pytest（budget + multi + critic + catalog） | **41 passed** |
| ruff（触及路径） | **PASS** |
| `./scripts/graph-compile.sh` | **PASS** |
| `lint-wiki-delta` | **PASS** |
| `chat/graph.py` | **零 diff** |
| 结论 | **30 PASS · 交 40** |

### 自检结论（40 verify）

| 检查 | 结果 |
|------|------|
| `spec-wave verify` | **PASS**（闸三行 approved · exit 0） |
| pytest（budget + multi + critic + catalog） | **41 passed**（exit 0） |
| ruff（触及路径） | **PASS**（exit 0） |
| `./scripts/graph-compile.sh` | **PASS**（exit 0） |
| `lint-wiki-delta` | **PASS**（exit 0） |
| `chat/graph.py` | **零 diff** |
| B1–B5 / failure_paths 抽查 | **全 ✅** · 无小修 |
| 结论 | **40 PASS · 交 50+CLOSE** |

### KPI（00）

Task_KPI%: 100 · D1 范围钉死（总步 32 · 耗尽→aggregate · 墙钟降级 · 与 4·1+1 共存 · 禁扩 T/W/P）· D2 闸齐（HG-TASK-DRAFT / HG-AUDIT-R1 / HG-GRAPH-MODULES 00 代签 · R1 PASS-with-nits）· D3 过程档齐（invoke 00/10/20/30/40 + 40 reverify + R1 审查文）· D4 图谱 G-L1 lg_rag 备注薄（无新一级模块）· D5 Hub/KPI 补登 + 交 commit/PR

### 经验总结

1. **总步硬门优先于墙钟**：默认关墙钟可先落地防幻觉循环，避免 fake clock 拖垮竖切。
2. **耗尽→aggregate 而非 END**：保留部分子任务结果综合，与既有 dispatch 空列表姿态一致。
3. **只计本图节点入口**：不计 `rag_subtask` 内 router 子图，否则一步 RAG 可吃光预算。

---

## 修订记录

| 日期 | 说明 |
|------|------|
| 2026-09-17 | 00 开壳 · 分支 `task/supervisor-budget-h-beta` · 冒烟 PASS 后维护者令开启 · 00 代签过程闸授权 · 交 10 |
| 2026-09-17 | 10 补全 · 钉死默认 32 / 计数点位 / 耗尽→aggregate / 墙钟降级 / 与 4·1+1 共存 · 交 20-task-audit |
| 2026-09-17 | 20 PASS-with-nits · 00 代签 HG-TASK-DRAFT / HG-AUDIT-R1 / HG-GRAPH-MODULES · 交 30 |
| 2026-09-17 | 30 实现 B1–B5 · 主闸 aggregate / 辅闸 end / 墙钟默认关 · 交 40 |
| 2026-09-17 | 40 verify PASS · pytest 41 / ruff / graph-compile / spec-wave verify+wiki · chat 零 diff · 交 50+CLOSE |
| 2026-09-17 | 00 50+CLOSE：讨论稿 §5/§8 回写 · SPEC 跟进句 · task → `docs/tasks/done/` · **未 commit** |
| 2026-09-18 | 00：40 reverify PASS · 补 KPI/Hub · 维护者令完成 CLOSE 含 commit/PR |

---

## CLOSE

| 项 | 内容 |
|----|------|
| 日期 | 2026-09-18（过程关账 2026-09-17 · 本轮补机读缺口 + 出 PR） |
| 签注 | 2026-09-17 · 00 代签 · 维护者令开启；2026-09-18 · 维护者令完成到 CLOSE（含 commit/PR） |
| 定稿 | 阶段 H β：supervisor 总步默认 32 · 耗尽→aggregate · 辅闸禁回环 · 墙钟默认关 |
| 证据 | 40 PASS · 40 reverify PASS（2026-09-18）· pytest 41 · verify PASS · graph-compile 绿 · `chat/graph.py` 零 diff |
| 归档 | `docs/tasks/done/task_supervisor_budget_h_beta.md` |
| Hub | engineering 域补登 |
| 跟进（不扩 W） | 阶段 T（第二租户数据前置）；完整墙钟硬门若产品需要可另开 |
| Git | commit `6911483` · 已 push；**排除**无关 `uv.lock` / `.agents/` |
| PR | [#141](https://github.com/Cyning12/ops-desk-api/pull/141)（~~待合入~~ **已 MERGED 2026-09-18** · merge commit `4896701`；修订注记 2026-10-30：原「待合入」为陈旧表述，按 `git log 4896701` 实证更正） |
