# Task：阶段 H · Host / Capability 契约硬化（波次 α）

> **状态**：`completed`（2026-09-17 · 00 CLOSE PASS · 待维护者 commit/PR）  
> **上游**：`docs/discussions/2026-09-17_interview_gaps_adoption_and_landing_v0.md` §1 A 档 · §5 波次 α · §8 阶段 H  
> **分支**：`task/capability-contract-hardening`  
> **类型**：feature / Host 契约硬化  
> **无关**：勿与其他 active task 混改；禁止扩阶段 T/W/P；禁止改 `chat/graph.py` 拓扑与 chat 410 主叙事（除非本验收点名）。  
> **00 注**：2026-09-17 · 本窗开工落壳 · 维护者令开启 · 10 补全后送 20

---

## Harness 元信息

| 字段 | 值 |
|------|-----|
| **task_slug** | `capability-contract-hardening` |
| **git_branch** | `task/capability-contract-hardening` |
| **implement_repo** | `ops-desk-api` |
| **test_strategy** | `required` |
| **test_strategy_note** | 先补/扩单测再改实现；覆盖 schema 校验、agent_type/mode allowlist、tenant_scoped 拒缺上下文、观测 metadata；不连真外网 / 不连真 Langfuse 云 |
| **code_quality_bar** | `L2_backend` |
| **graph_change_layer** | `G-L1` |
| **graph_delta** | `docs/_tech_graph/l1/01_modules.md` · `docs/_tech_graph/l1/10_flow_capability.md` · `docs/_tech_graph/l1/10_flow_capability.graph.yaml`（可选一句） |
| **graph_delta_note** | 仅 `capability` / `lg_rag` /（若触及）strategy 行**备注**；**不新增**一级模块；不增 implementedBy |
| **wiki_delta** | `n/a` |
| **wiki_delta_note** | 本 task 不迁 coding_wiki；口径「注册表」与业务不变量纪律落 capability 文档/模块注释/CODING 一句即可 |
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
| HG-TASK-DRAFT | approved | 22-R1, 30 | 2026-09-17 · 00 代签 · 维护者令开启 · 10 补全 + 20 PASS |
| HG-AUDIT-R1 | approved | 30 | 2026-09-17 · 00 代签 · 维护者令开启 · 审查文 `docs/harness/reviews/task_capability_contract_hardening_audit_R1_20260917.md` |
| HG-GRAPH-MODULES | approved | 30 | 2026-09-17 · 00 代签 · 维护者令开启 · 仅 G-L1 备注、不新增一级模块（30 改图谱后回写 `01_modules.md` 签收行） |

---

## 背景与目标

面试 A 档与阶段 H 要求：现网 Capability 面已有 Registry + Gateway + Policy + Strategy Builder allowlist，但默认 local_fn **多数无 `args_schema`**、`invoke` **不做参数校验**、候选可见集仍可 `CANDIDATE_CAPABILITY_IDS=None`（全量可见）、lookup **无 `tenant_scoped` 机制化声明**、span metadata 缺 args/policy/subtask 串链字段。

本 task **一竖切 CLOSE**（A–F 同 task）：补最小契约 → Gateway 校验 → 按 agent_type/mode 配置 allowlist → `tenant_scoped` + 单测 → 观测补全 → 口径 F。产品仍为只读单租户；为阶段 T/W 留字段与失败姿态，**不实现**多租户产品与写/HITL。

---

## 现状锚点（只读定位 · 30 必读）

| 主题 | 真实路径 | 现状缺口 |
|------|----------|----------|
| 契约类型 | `app/ops/capability/types.py` | `CapabilitySpec` 有 `args_schema`；**无** `tenant_scoped` |
| 默认注册 | `app/ops/capability/defaults.py` · `app/ops/capability/manifests/builtin.v1.yaml` | 五枚默认 local_fn **均无** `args_schema` |
| Manifest | `app/ops/capability/manifest.py` | 需能加载 schema / `tenant_scoped`（若 YAML 增字段） |
| Gateway | `app/ops/capability/gateway.py` | `invoke`/`ainvoke` 过 Policy；**无** args JSON Schema 校验；span 仅 `capability_id`/`kind`/`ok`/`error`/`risk_level`/`policy_blocked` |
| Policy | `app/ops/capability/policy.py` | high/sandbox/cli 门；**无**租户谓词 |
| Lookup | `app/ops/capability/lookups.py` | `get_issue_by_number` / `get_pr_by_number` 自由文本 payload；无租户 ctx |
| 候选可见集 | `app/ops/strategy/config.py` · `app/ops/strategy/builder.py` | `CANDIDATE_CAPABILITY_IDS=None` → 全量可见 catalog |
| Filter 占位 | `app/ops/capability/types.py` `CapabilityFilter.node_role` | 占位；本波用 **agent_type/mode → allowlist 配置** 窄落地，不上完整授权服务 |
| tool 子任务 | `app/ops/lg_rag/schemas/subtasks.py` · `app/ops/lg_rag/multi/nodes.py` `tool_exec_node` | `SubtaskItem.input: str` 自由文本；`ainvoke(tool, input)` |
| 观测 | `app/ops/capability/gateway.py` `_write_span_metadata` · `app/ops/tracing.py` | 缺 args 摘要、`subtask_id`、policy 决策串 |
| 既有单测 | `tests/test_capability_gateway.py` · `test_capability_lookups.py` · `test_capability_policy.py` · `test_capability_manifest.py` · `test_strategy_builder.py` · `test_lg_rag_supervisor_capability_catalog.py` | 回归面；本波扩测 |

归档对照：`docs/tasks/done/task_capability_gateway_p*.md` · `task_capability_policy_sandbox.md` · `task_ops_pg_lookup_capabilities.md` · `task_lg_rag_supervisor_capability_catalog.md` · `task_strategy_builder_allowlist.md`。

---

## 范围（A–F · 默认同 task 竖切）

- [x] **A · args_schema + invoke 校验**
  - 默认能力（至少：`get_issue_by_number` · `get_pr_by_number` · `utc_now_iso`；建议 mock 亦补最小 schema）在 `defaults.py` + `builtin.v1.yaml` 补 **最小 JSON Schema**
  - Gateway `invoke`/`ainvoke`：有 `args_schema` 时校验；不合规则 `ok=False` + 明确 error（如 `args_schema_invalid`）
  - 校验开关：默认对「已声明 schema」开启；预留强制模式（env / Host `_host_policy`）；**写能力强制**写进注释/ROADMAP（本仓尚无写能力实现）
  - **禁止**把业务不变量（涨跌幅规则等）写进 `args_schema`（见 F）
- [x] **B · tool 子任务结构化 args**
  - `SubtaskItem` 增加可选 `args: dict | None`（或等价）；`tool_exec_node` **优先**传 `args`，否则兼容旧 `input` 字符串（映射/包装策略在实现备忘钉死，须单测）
  - supervisor 结构化出口与 prompt 提示：鼓励对 lookup 产出可校验 args；非法 args → Gateway 拒，不抛垮图
- [x] **C · agent_type / mode → allowlist**
  - 取代「裸 `CANDIDATE_CAPABILITY_IDS=None` = 默认可视全量」：Host 配置 **按 agent_type 或 mode** 的显式 allowlist（落点建议 `app/ops/strategy/config.py` 或邻接配置模块）
  - Builder 读该配置写 `allowed_capability_ids`；未知 key → 安全默认（空或最小只读集，**禁止**静默全开）；单测覆盖
- [x] **D · tenant_scoped**
  - `CapabilitySpec`（+ YAML）增加 `tenant_scoped: bool`（默认 `False`）
  - 默认 lookup（`get_issue_by_number` / `get_pr_by_number`）标 `True`
  - Gateway/Policy：`tenant_scoped=True` 且 ctx **无**租户谓词（建议键 `tenant_id` 或 Host `_host_tenant`）→ **拒**（`policy_blocked: tenant_scope_missing`）
  - 现网构造性单租户：lg_rag / Host 调用方可注入固定试点租户 id；**不**建 Workspace 模型（阶段 T）
  - 单测：无租户谓词拒；有谓词可过（夹具/mock）
- [x] **E · Langfuse / span metadata**
  - 扩展 Gateway（及 tool_exec 可写）metadata：`capability_id`（已有）、**args 摘要**（截断/哈希，禁全量密钥）、**policy** 决策摘要、`subtask_id`（tool_exec 传入 ctx）
  - 写路径预留 `approval_id` 字段名（可空；本波不实现 HITL）
- [x] **F · 口径与纪律**
  - 文档/图谱备注/模块 docstring：称 **进程内注册表**，**禁止**暗示已上线「注册中心 / 跨进程发现服务」
  - 编码纪律：Gateway 只做 schema/Policy；业务不变量不进 `args_schema`（`docs/standards/CODING_BACKEND_L2_v1_zh.md` 补一句或 capability 包注释指针）

**竖切结论**：A–F **同 task** 交付；若 20/30 发现 B（子任务 schema）与 A 强耦合导致风险过大，可跟进拆 `task_capability_tool_args_v2`，但 **默认不拆**。

---

## 非范围（严禁扩）

- 阶段 **T**：多租户产品（Principal↔Workspace、ANN 前分租户语料、跨租户负样本金样）
- 阶段 **W**：写能力 / HITL confirmation 生产路径 / 沙箱写池
- 阶段 **P**：服务化 Registry、完整 Ontology Package、多 Agent 委派平台、attenuation 真子 Agent
- 波次 **β**：supervisor 总步数/墙钟预算与耗尽 aggregate —— **默认非范围**；跟进见文末
- 改无关 active task；改 chat 已 410 主叙事（除非本验收点名）
- 新增 G-L1 一级模块；引入 Agently；动态 `StateGraph.compile`
- 改 `chat/graph.py` 拓扑

### 跟进（非本 task 验收）

- 波次 β · supervisor 预算（讨论稿 §5 项 6）
- 阶段 T/W 串行（§8.1）；本波仅字段与 fail-closed 姿态预埋
- CapabilitySpec 可选治理字段（version/owner 等 · B 档 ROADMAP）

---

## 10 钉死契约（00/30 不得静默改义）

| 项 | 钉死 |
|----|------|
| A 无 schema | 无 `args_schema` → **不**做参数 schema 校验（保持可调用）；`schemas_for_llm` 仍跳过（P1 既有） |
| A 有 schema | 校验失败 → `ok=False`，不抛垮调用方 |
| B 兼容 | 仅有 `input` 无 `args` → 允许（legacy）；有 `args` → 以 `args` 为主入 Gateway |
| C 默认 | 禁止 `None`=全开为生产默认；须显式 map/list；测试可 patch |
| D 缺租户 | `tenant_scoped` 能力缺 ctx 租户谓词 → **拒**（非静默放行） |
| F 用词 | 对外/仓内文档「注册表」；审查拒收「已上线注册中心」表述 |

---

## 失败路径（failure_paths）

| 触发条件 | 系统行为 | 可重试 | 用户可见 |
|----------|----------|--------|----------|
| `HG-AUDIT-R1` pending 即 30 改码 | 执行 Agent **拒开工** | 是 | 须先 20 + 闸签 |
| invoke args 不符 `args_schema` | Gateway `ok=False` · error 含 schema 校验含义 | 视调用方改 args | 是（结构化错误进 subtask_results） |
| 能力不在 agent_type/mode allowlist | Builder 不写入 / supervisor 不可见；非法 tool → 既有 fallback 单 rag | 否（改 Host 配置） | 是（无该 tool / fallback） |
| `tenant_scoped` 能力缺租户上下文 | Policy/Gateway 拒 · `tenant_scope_missing` | 是（补 ctx） | 是 |
| 未知 capability_id | 既有：`ok=False`，图不垮 | 否 | 是 |
| Policy high/sandbox/cli 挡 | 既有 `policy_blocked` | 视 Host env | 是 |
| 实现误扩 T/W/P 或改 chat 拓扑 | 审查/verify **拒收** | 是（回滚） | 否（内部） |
| 文档声称「注册中心」已上线 | 文档/审查拒收 · 口径纠正 | 是 | 口径纠正 |
| 业务不变量塞进 `args_schema` | 20/40 审查拒收 | 是 | 否（内部） |

---

## 验收标准

- [x] **A**：默认 lookup（+ `utc_now_iso`）注册含最小 `args_schema`；不合规 args → `ainvoke`/`invoke` `ok=False`；单测在 `tests/test_capability_gateway.py`（或邻接新测）
- [x] **B**：`SubtaskItem` 支持可选结构化 `args`；`tool_exec_node` 优先 `args`、兼容 `input`；至少 1 条节点级单测
- [x] **C**：存在 agent_type/mode → allowlist 配置面；`CANDIDATE_CAPABILITY_IDS=None` 不再作为生产「全开」语义（或显式废弃路径有注释+测）；`tests/test_strategy_builder.py` 覆盖
- [x] **D**：`tenant_scoped` 字段落地；lookup 声明为 True；无租户谓词拒；有谓词可过；`tests/test_capability_lookups.py` 与/或 `tests/test_capability_policy.py` 覆盖
- [x] **E**：span metadata 含 args 摘要、policy 摘要、`subtask_id`（tool 路径）；单测可断言 metadata 写入（mock tracing 即可）
- [x] **F**：触及文档/图谱备注无「已上线注册中心」误称；CODING 或 capability 注释含「业务不变量不进 args_schema」
- [x] `pytest tests/test_capability_gateway.py tests/test_capability_lookups.py tests/test_capability_policy.py tests/test_capability_manifest.py tests/test_strategy_builder.py tests/test_lg_rag_supervisor_capability_catalog.py -q` 绿（30 可按新增文件扩列表）
- [x] `ruff check app/ops/capability app/ops/strategy app/ops/lg_rag/multi app/ops/lg_rag/schemas tests`（触及路径）绿
- [x] `./scripts/graph-compile.sh` 绿（若改 G-L1 备注/flow）
- [x] `npx --yes spec-wave task lint-wiki-delta --target .` 通过
- [x] `chat/graph.py` 零 diff；不新增 G-L1 一级模块；`HG-GRAPH-MODULES` 本 task 行已签（关账前）

---

## 依赖

- 上游决议：`docs/discussions/2026-09-17_interview_gaps_adoption_and_landing_v0.md`
- SPEC（既有）：`docs/spec/agent-infra/capability/SPEC-capability-gateway_v0.md`
- 编码规范：`docs/standards/CODING_BACKEND_L2_v1_zh.md`
- 图谱：`docs/_tech_graph/l1/01_modules.md` · `10_flow_capability.*`
- 闸片段：`docs/harness/prompts/FRAGMENT_30_gate_verify_v1_zh.md`

---

## 给执行帽的必读列表

1. `AGENTS.md`
2. 本 task（全文 · 尤其「10 钉死契约」与非范围）
3. `docs/discussions/2026-09-17_interview_gaps_adoption_and_landing_v0.md`（§1 A · §5 α · §8 H；**勿做** §8.1 T/W/P）
4. `docs/standards/CODING_BACKEND_L2_v1_zh.md`
5. `docs/_tech_graph/l1/01_modules.md` · `docs/_tech_graph/l1/10_flow_capability.md`
6. 代码锚点：`app/ops/capability/{types,gateway,policy,defaults,manifest,lookups}.py` · `manifests/builtin.v1.yaml` · `app/ops/strategy/{config,builder}.py` · `app/ops/lg_rag/schemas/subtasks.py` · `app/ops/lg_rag/multi/nodes.py`
7. 归档：`docs/tasks/done/task_capability_gateway_p0.md` … `p3.md` · `task_capability_policy_sandbox.md` · `task_ops_pg_lookup_capabilities.md` · `task_lg_rag_supervisor_capability_catalog.md` · `task_strategy_builder_allowlist.md`
8. 过程 invoke：`docs/harness/invokes/by-task/capability-contract-hardening/`
9. `docs/harness/prompts/FRAGMENT_30_gate_verify_v1_zh.md`（30 首输出闸扫描）

---

## 思考轮控制

| 轮 | 结论 | early_stop | reason（early_stop） | residual_risks |
|----|------|------------|----------------------|----------------|
| R0 | 框定阶段 H α = 契约空洞硬化，非平台 Registry | no | — | none |
| R1 | A–F 同竖切；T/W/P 与 β 预算非范围 | no | — | none |
| R2 | 有 schema 才校验；args 优先、input 兼容 | no | — | B 兼容拖长 30 风险 |
| R3 | tenant_scoped 缺 ctx 则拒；构造性单租户注入 | no | — | none |
| R4 | 观测补字段 + 口径「注册表」；停轮 | yes | 上游已钉 A–F 与 H→T→W；代码锚点已扫清；R5 无新增决策面 | B 兼容若爆可跟进拆棒；C 安全默认（空 vs 最小只读）须 30 钉死 |
| R5 | （未开） | — | early_stop at R4 | — |

**actual_last_round**：R4 · **early_stop**：yes · **reason（early_stop）**：上游讨论稿已钉 A–F 与 H→T→W 序；代码锚点已扫清；再开 R5 无新增决策面 · **residual_risks**：见 R4 行

### R0 · 问题框定

阶段 H 波次 α = 契约空洞（无 schema / 无校验 / 全局可见 / 无租户声明 / 观测弱）与面试伤疤同构；目标是 **可 CLOSE 竖切**，不是平台 Registry。

### R1 · 竖切边界

A–F 同 task：共享 `CapabilitySpec`/Gateway/Builder 触点，拆棒增加闸成本。β 预算与 T/W/P **明确非范围**。

### R2 · 兼容与破坏面

默认能力今日无 schema 且 tool 走自由 `input`；必须 **有 schema 才校验** + **args 优先、input 兼容**，避免一刀切打爆现网 supervisor 金样。

### R3 · 租户姿态

无 Workspace 产品时仍要机制化：`tenant_scoped` + 缺 ctx 则拒；Host 注入构造性单租户。避免「文档说要过滤、代码自觉」。

### R4 · 观测与口径

metadata 补 args 摘要 / policy / `subtask_id` 成本低、面试扣分点明确；F 零码/少码改词与纪律，防止简历与图谱继续写「注册中心」。

### R5

（提前停 · 未开）

---

## 实现备忘（子 Agent 回填）

| 项 | 状态 | 备注 |
|----|------|------|
| 10 补全 task | ✅ | 2026-09-17 · `task lint` PASS |
| 20 审查 | ✅ | 2026-09-17 · audit R1 PASS · 00 代签 |
| 30 实现 | ✅ | 2026-09-17 · A–F 竖切 · 见 invoke_30 |
| 40 verify | ✅ | 2026-09-17 · PASS · 见 invoke_40；B 补无 PG 节点测 |

### 30 钉死备忘

- **B 兼容**：`tool_exec` 有 `args: dict` → 原样入 Gateway；否则用 `input` 字符串（legacy）。
- **C 安全默认**：未知 `agent_type`/`mode` → `[]`（fail-closed）；`CANDIDATE_CAPABILITY_IDS is not None` 仍可显式覆盖（测试）；`build_allowlist_from_candidates(None)` 不再全开。
- **D 试点租户**：`tool_exec` 注入 `tenant_id=OPS_PILOT_TENANT_ID|ops-desk-pilot`；直接 Gateway 调用须自带 `tenant_id`/`_host_tenant`。
- **A 校验**：最小自研校验器（无 jsonschema 依赖）；`OPS_CAPABILITY_FORCE_ARGS_SCHEMA` / `_host_policy.force_args_schema` 预留。

### 建议实现序（非强制）

1. types + manifest/YAML 字段（`args_schema` / `tenant_scoped`）  
2. Gateway 校验 + Policy 租户门 + span  
3. defaults/builtin 补 schema 与 lookup `tenant_scoped`  
4. strategy config allowlist map + Builder  
5. SubtaskItem `args` + tool_exec  
6. 文档口径 F + G-L1 备注  

---

### 自检结论（执行者）

**40 PASS** · A–F 与 failure_paths 抽查达标 · `spec-wave verify` PASS · pytest **76 passed / 8 skipped**（30 声明集合；40 补 B 无 PG 节点测）· ruff 绿 · graph-compile 绿 · lint-wiki-delta PASS · `chat/graph.py` 零 diff · 未 commit/push · 未 CLOSE。交 **50+CLOSE**（注意：`schema_validate.py` 仍 untracked，commit 须纳入）。

---

## 修订记录

| 日期 | 说明 |
|------|------|
| 2026-09-17 | 00 极简壳 · 分支 `task/capability-contract-hardening` · 维护者令开启 · 交 10 |
| 2026-09-17 | 10-task 补全：A–F 验收 · failure_paths · R0–R4 early_stop · 真实代码锚点 · 送 20 |
| 2026-09-17 | 20-task-audit PASS · 00 代签 HG-TASK-DRAFT / HG-AUDIT-R1 / HG-GRAPH-MODULES · 维护者令开启 |
| 2026-09-17 | 30 实现 A–F · invoke_30 · 交 40 |
| 2026-09-17 | 40 verify PASS · 补 B 无 PG 测 · invoke_40 · 交 50+CLOSE |
| 2026-09-17 | 00 50+CLOSE：讨论稿 §5/§8 回写 · SPEC 跟进句 · `git mv` → `docs/tasks/done/` · 过程签 2026-09-17 · 00 代签 · 维护者令开启 · **未 commit** |

---

## CLOSE

| 项 | 内容 |
|----|------|
| 日期 | 2026-09-17 |
| 签注 | 2026-09-17 · 00 代签 · 维护者令开启 |
| 定稿 | 阶段 H α：args_schema + invoke 校验 · allowlist · tenant_scoped · span metadata · 口径「注册表」 |
| 证据 | 40 PASS · pytest 76 passed / 8 skipped · verify PASS · graph-compile 绿 |
| 归档 | `docs/tasks/done/task_capability_contract_hardening.md` |
| 跟进（不扩 W） | β supervisor 预算；阶段 T；完整 JSON Schema 库可选；commit 须纳入 `schema_validate.py` |
| Git | **未 commit / 未 push**（待维护者另令） |
| PR | 待开 |
