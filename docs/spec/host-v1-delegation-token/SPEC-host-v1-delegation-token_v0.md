# SPEC：Agent Host V1-A · 委派令牌（delegation-token · 委派授权产物化）（v0）

> **层级**：L1 波次 SPEC（07 L0 规划的 V1-A 波 · 五波之首）  
> **状态**：`signed`（HG-SPEC-SIGNOFF=**approved** · 2026-09-23 · **00 代录** · 维护者令原话：「签收，并生成对此长程任务的00启动Prompt，新窗口执行，授权00签收所有过程文档，完整落地1.0版本内容」· 承 07/08 同令代录先例）  
> **种子**：[`../agent-infra/08_host_v1_wave_spec_outlines_v0.md`](../agent-infra/08_host_v1_wave_spec_outlines_v0.md) §1（signed · 本 SPEC 为其正式展开，冲突以本 SPEC 为准）  
> **上游**：[`../agent-infra/07_host_v1_landing_plan_v0.md`](../agent-infra/07_host_v1_landing_plan_v0.md)（signed · 波次/顺序/出口标准）· [`../../discussions/2026-09-23_agent-host-full-framework-outline_v0.md`](../../discussions/2026-09-23_agent-host-full-framework-outline_v0.md)（v0.2 · #6 委派网关差距 + A1/A2 字段级起点 + D3 Tier 1 语义）· [`../../discussions/2026-09-23_agent-host-multi-service-engineering-architecture_v0.md`](../../discussions/2026-09-23_agent-host-multi-service-engineering-architecture_v0.md)（C2 委派必带授权产物 · C6 租户进令牌）  
> **下游**：HG-SPEC-SIGNOFF → 00 出 task → 20-task-audit → HG-AUDIT-R1 → 30（委派子 Agent · 分支 `task/host-v1-delegation-token`）→ 40 → PR+CI 绿+merge → 图谱回写（HG-GRAPH-MODULES 00 代录）→ CLOSE  
> **Open Folder（实现）**：`ops-desk-api/`

---

## Harness 元信息

| 字段 | 值 |
|---|---|
| **spec_slug** | `host-v1-delegation-token` |
| **invoke_slug** | `host-v1-delegation-token`（task 阶段） |
| **test_strategy** | `required` |
| **test_strategy_note** | pytest 单测为主（纯函数验签门 + 图节点 fake ctx）；六类拒绝断言 + 全链路携令牌断言 + 审批留痕断言 + 篡改断言 + off 模式零 diff 回归；不开服务、不动 freeze 契约测试 |
| **默认分支** | `task/host-v1-delegation-token`（自 `master` 分出；**禁止 master/main 直改**） |
| **graph_change_layer** | `G-L1` 行备注（**Q3 裁定：不新增一级模块**；`capability` 行 + `lg_rag` 行备注；HG-GRAPH-MODULES 随 30 回写由 00 代录） |
| **freeze_id** | 无（图内化 · 不动 lg-rag-sse-v1 / lg-rag-http-v1 / lc-evidence-http-v1 · SSE 零新事件类型 · 无新 HTTP 路由） |

### 人工闸（SPEC 阶段）

| human_gate_id | status | 说明 |
|---|---|---|
| **HG-SPEC-SIGNOFF** | **approved**（2026-09-23 · 00 代录） | 维护者令原话：「签收，并生成对此长程任务的00启动Prompt，新窗口执行，授权00签收所有过程文档，完整落地1.0版本内容」；开放裁定 Q1/Q2/Q3 已答；00 可拆 task |

---

## 1. 背景与目标

### 现状与差距（承大纲 v0.2 #6）

supervisor→工人分发已有 **step_contract 校验点**（consumes/produces · prefix_touch_required→hitl_required，`app/ops/lg_rag/multi/step_contract.py`）与六道闸执行网关（`capability/gateway.py::_prepare_call`：lookup→enabled→Policy→熔断→配额/kill switch→args_schema），但**没有授权产物**——工人的能力调用权来自图内位置而非可核验的凭据。委派网关是 34 模块对照中**唯一的新安全面**（测评点 5；工程约束 C2：任何主→子委派都签发令牌，即使图内分发）。

### 一句话目标

委派时签发**令牌**（六字段：能力集 / TTL / 一次性 / 参数约束 / 主体绑定 / 签名），工人执行能力前验签，签发本身走高危审批口径；**图内化，无网络面**；叠加 A2 `requested_scope` 显式化（plan 输出携带声明式 scope，Builder 升级为「声明∩裁剪」）。

### 设计纪律（跨波公共约束继承 · 承 08 §0.1，签收时锁死）

1. **Host 权威**：令牌验签不做成模型可选 tool；策略键不可由 plan 写入；`requested_scope` 是声明式输入，**只收窄不放宽**（有效 scope = 声明 ∩ Host 侧裁剪）。
2. **默认关上线**：验签门 env 三档 `off | observe | enforce`，默认 `off`（关闭=现状逐字节零 diff）；灰度路径 observe（只记 would_block 不拦）→ enforce。
3. **审计记动作不记内容**：签发/验签/拒绝进台账（logger + span metadata）；参数字段哈希化，不记原值。
4. **Tier 1 语义**（大纲 v0.2 D3）：令牌签发 = 原子闸门——签发序号单调、令牌版本化、同 subtask 并发/重复签发检测（重签发即作废旧例）；单进程实现预留乐观锁语义，v2.0 上楼零语义改动。
5. **零 freeze 动**：不改任何 freeze 契约；无新 SSE 事件类型；无新 HTTP 路由；无新表（进程内令牌形态，alembic 义务=无）。

---

## 2. 范围（D 块展开 · 承 08 §1.2）

### D1 · 令牌模型（必做）

新内部文件 `app/ops/capability/delegation.py`（入 `capability` 既有模块 · 见 §4 Q3 裁定）：

`DelegationToken`（frozen dataclass · 可序列化进 state/checkpoint · 自包含凭据）：

| 字段 | 类型 | 说明 |
|---|---|---|
| `token_id` | str（uuid4 hex） | 全局唯一 · 审计锚点 |
| `version` | int | 令牌格式版本（v1 起）；`kid` 签名密钥代标识（轮换=重启 · 预留多密钥并存） |
| `capability_set` | frozenset[str] | 允许调用的 capability id 集；**签发时** ⊆ 该子任务有效 scope（见 D5） |
| `ttl_seconds` / `issued_at` / `expires_at` | int / float / float | TTL 锚定**墙钟**（见 §5 FP-2 裁定）；env `LG_RAG_DELEGATION_TOKEN_TTL_SECONDS` 默认 600，非法/越界回退默认（承 step_contract `_env_int` 纪律） |
| `one_shot` | bool + `nonce` str | 一次性语义：nonce 消费登记（进程内 consumed registry · TTL 清理）；默认 `True`（tool_exec 委派一律一次性） |
| `param_constraints` | dict | 参数约束：`{capability_id: {arg_name: 约束}}`；v1 约束子集 = `enum`（允许值枚举）/ `max_len`（字符串上限）/ `pattern`（正则）三种纯代码校验；**未知约束类型 → 拒绝签发**（安全默认，不静默放行） |
| `subject_binding` | dict | `{tenant_id, user_id, run_id, subtask_id}` 四元组；tenant 取自 ctx/ContextVar（承阶段 T · C6），**模型产出不得参与身份构造** |
| `signature` | str | HMAC-SHA256（见 §4 Q1 裁定）：对其余字段的 canonical JSON（排序键 · 紧凑分隔符）签名 |

**不可变**：frozen dataclass，任何字段改动 → 签名失效（篡改断言见 D6）。

### D2 · 签发点（必做）

- **位置**：`subtask_join` 分发路径（`app/ops/lg_rag/multi/graph.py` route_next_subtask 分发前 · 节点实现在 `multi/nodes.py`）：为每个待分发子任务签发令牌，令牌注入该子任务的分发负载（state 内传递 · 工人节点自取）。
- **签发审批口径**（§4 Q2 裁定）：安全域**自动放行边界** = `capability_set` ⊆ 本轮有效 scope（D5）**且**集合内能力全部 `side_effect ∈ {none, read}`（只读）**且**无 sandbox/cli 类（Policy 门类判定复用 `capability/policy.py`）；**其余一律 HITL_REQUIRED**（含写能力 / 越声明 / 沙箱类），复用 `hitl` interrupt/resume 回路，审批留痕落 `ops_hitl_requests`（记动作不记内容）。
- **Tier 1 并发语义**：签发器持进程内单调签发序号；同 `subtask_id` 重签发 → 新例生效、旧例 nonce 作废（supersede 语义，审计记 `token_superseded` 动作）；**禁续期**（见 §5 FP-1）。
- **签发密钥**：env `LG_RAG_DELEGATION_TOKEN_SECRET` 注入；**禁硬编码**；enforce 模式下缺失 → 拒绝签发并告警（安全默认拒，不降级为不签名）。

### D3 · 验签点（必做）

- **位置**：`capability/gateway.py::_prepare_call` 闸链**之前**插验签门（lookup 之前——无有效令牌的调用连注册表都不查）。验签纯函数 `verify_token(token, *, capability_id, args, ctx) -> Verdict` 在 `capability/delegation.py`，零 LLM、零 IO、**禁查库**（HMAC 对称验签微秒级 · 见 §5 FP-3）。
- **触发口径**：ctx 携 `_delegation_required=True` 时强制（委派链路专用 · `tool_exec_node` 注入，承 nodes.py:1050-1091 ctx 装配先例）；非委派调用方（CLI 冒烟 / 测试直连）不携带该标记 → 不受本闸影响（零回归）。
- **六类拒绝**（全部 `ok=False` 返回 `CapabilityResult`，不抛异常、不拖垮整图 · 承 v0 失败语义与 `_blocked_result` 先例——**被拒的调用不落回执**）：

| # | 拒绝类 | 判定 |
|---|---|---|
| R-a | 无令牌 | `_delegation_required` 但 ctx 无令牌 / 反序列化失败 |
| R-b | 越集 | `capability_id ∉ token.capability_set` |
| R-c | 过期 | 墙钟 `now > expires_at` |
| R-d | 重用 | `one_shot` 且 nonce 已消费 |
| R-e | 参数越约束 | `param_constraints` 校验失败 |
| R-f | 主体不符 | ctx（tenant/user/run/subtask）≠ `subject_binding` |
| — | 篡改 | 签名验不过（归入 R-a 拒绝类上报，审计单列 `signature_invalid`） |

- **模式开关**：env `LG_RAG_DELEGATION_TOKEN_MODE=off|observe|enforce`，默认 `off`（零 diff）；`observe` = 走完整验签但只记 `would_block` span/台账不拦；非法值回退 `off`。

### D4 · 审计（必做）

签发（`token_issued` / `token_issue_hitl_required` / `token_superseded`）、验签通过（`token_verified`）、拒绝（`token_rejected:<class>`）进台账：logger 结构化行 + span metadata（承 capability `metrics.py`/`visibility.py` 先例）。**记动作不记内容**：令牌只记 `token_id`/`version`/集合基数/过期时刻；参数约束命中记字段名哈希。面向大纲 #11 审计台账清单（能力调用 / HITL 审批 / Policy 拦截）补「委派令牌」面。

### D5 · requested_scope 显式化（A2 · 必做）

- `lg_rag/schemas/subtasks.py::SubtasksPlan` 增 `requested_scope: list[str] | None`（声明式 capability id 集 · 模型**可声明收窄**，不声明=None）。
- Builder 升级「声明∩裁剪」：`有效 scope = requested_scope ∩ allowlist（Registry∩Policy）`；`requested_scope` 中越 allowlist 的 id **剔除+审计**（承 builder.py stripped 先例，记 `scope_stripped`）；**未声明 → 退化为现状隐式 allowlist**（向后兼容 · observe 期收集声明率，未来是否改默认空留 V1-B 复盘）。
- 有效 scope 写 state，作 D2 签发的 `capability_set` 上界；`tool_exec` 子任务实际令牌集 = 子任务声明 tool ∩ 有效 scope（空集 → 不签发，tool_exec 直接 `ok=False` 走既有未知/无授权路径）。
- **Host 权威**：`requested_scope` 只收窄不放宽；声明不写入任何 Policy 键。

### D6 · 测试（必做）

1. **六类拒绝断言**（R-a~R-f 各一条 + 篡改改字段→签名失效）
2. **全链路携令牌断言**：supervisor 分发 → tool_exec 携令牌 → capability 验签通过（fake adapter）
3. **审批留痕断言**：写能力委派 → `token_issue_hitl_required` 台账可查；只读委派 → 自动签发台账可查
4. **篡改断言**：改 `capability_set`/`expires_at`/`subject_binding` 任一字段 → 验签拒
5. **replan/重发断言**：同 subtask 重发 → 新令牌生效、旧 nonce 作废（拒 R-d）
6. **模式断言**：`off` = 现状零 diff；`observe` = 越权调用放行但 `would_block` 台账可查；`enforce` = 越权拒
7. **requested_scope 断言**：声明∩裁剪矩阵（声明越界剔除 · 未声明兼容现状 · 只收窄不放宽）
8. **冻结回归**：既有 freeze 契约测试零改动通过；SSE 零新事件类型断言（承既有守护测试形态）

---

## 3. 非范围

- ❌ 跨服务验签 / JWT 公钥体系 / 网络面令牌传递（**v2.0**；工程方案 P2 时令牌自包含签名天然上楼，本波预留 `kid`/`version` 即全部义务）
- ❌ 用户态认证令牌（ops_sessions 面不动）
- ❌ 令牌持久化表 / 撤销列表服务（进程内 consumed registry 起步；跨进程撤销 v2.0）
- ❌ 动态 StateGraph compile；模型可选「校验 tool」（Host 权威不动摇）
- ❌ 改既有 freeze 契约 / 新 SSE 事件类型 / 新 HTTP 路由 / 新表（零 alembic 义务）
- ❌ HITL 三档分级体系（PRE_AUTHORIZED/HITL_EXEMPT 属 V1-B manifest 声明面；本波只复用既有 HITL_REQUIRED 等价物作签发审批）
- ❌ 场景维可见集裁剪（V1-B）；情景记忆/失败模式库（V1-D）

---

## 4. 开放裁定（必答题 · 全部作答）

### Q1 · 签名机制选型

| 方案 | 做法 | 收益 | 代价 | 裁决 |
|---|---|---|---|---|
| **S1 · HMAC-SHA256 对称（HS256 类）** | 进程内单密钥 env 注入；canonical JSON 签名；`kid` 标识密钥代 | 微秒级 · 零依赖 · 图内场景签名/验签同进程，对称足够；轮换=重启 | 密钥泄露即可伪造（进程内风险可接受）· 跨服务需换非对称 | **推荐（裁定）** |
| S2 · Ed25519 非对称 | 签发私钥 / 验签公钥 | 跨服务验签不可伪造 | 图内无跨方验签需求 → 过度设计；引入加密依赖；性能更差 | 弃选（v2.0 上楼时再议 · `kid`/`version` 字段已预留算法可换） |

**裁定：S1。** 图内化=签名方与验签方同进程同密钥，对称签名安全模型成立；跨服务验签留 v2.0（工程方案 §9「令牌自包含签名 · 验签零回调 control」与本裁定兼容）。

### Q2 · 签发审批默认口径

| 方案 | 做法 | 收益 | 代价 | 裁决 |
|---|---|---|---|---|
| **S1 · 分级口径：只读自动 · 其余 HITL** | 自动放行边界 = scope 内 ∩ 全只读 ∩ 非沙箱/CLI；写/越界/沙箱 → HITL_REQUIRED | 高危审批覆盖真实风险面（写副作用）；只读委派零摩擦 | 边界判定逻辑须纯代码可测 | **推荐（裁定）** |
| S2 · 全部 HITL | 每次签发都人工批 | 最保守 | supervisor 常规委派全挂起 → 主线不可用 | 弃选 |
| S3 · 全部自动 | 安全域全放行 | 零摩擦 | 签发是高危操作（大纲 A1 原话）→ 裸奔 | 弃选 |

**裁定：S1。** 边界三条件（scope 内 / 全 `side_effect ∈ {none, read}` / 非 sandbox·cli 类）全部纯代码判定、复用 `capability/policy.py` 门类；审批留痕落 `ops_hitl_requests`；上线形态承「默认关/观测模式」——`off` 起步 → `observe` 收集边界误判 → `enforce`。

### Q3 · 委派网关是否立新一级模块

| 方案 | 做法 | 收益 | 代价 | 裁决 |
|---|---|---|---|---|
| **S1 · 不立新模块：签发/验签入 `capability`，分发接线入 `lg_rag`** | `capability/delegation.py`（模型+签发+验签纯函数）+ `lg_rag/multi` 分发接线；图谱两行备注 | 承大纲 §6「能入既有模块就不开新一级模块」；依赖方向顺（`lg_rag → capability` 既有边，零新跨模块边）；v2.0 归属 agent-host-control 时以包内路径整体上楼 | 委派网关无独立图谱行（备注级可见性） | **推荐（裁定）** |
| S2 · 新一级模块 `delegation_gateway` | 独立包 + 图谱新行 | 图谱显式 | 图内化无网络面 → 一级模块是空壳；人为制造新跨模块边；与「P0 期不提前抽象」（工程方案 §9 风险表）冲突 | 弃选 |

**裁定：S1（不新增一级模块）。** 图谱义务随之定：`capability` 行备注（delegation 令牌模型+验签门 · `_prepare_call` 前插）+ `lg_rag` 行备注（subtask_join 签发接线 + requested_scope）；**不新增一级模块 · 不增 implementedBy（G-L2 indexes 不扩）**；HG-GRAPH-MODULES 行随 30 回写由 00 代录如实登记。

---

## 5. failure_paths（承 08 §1.4 · 全部正面裁定）

| # | 路径 | 裁定 |
|---|---|---|
| FP-1 | ReAct replan 重发子任务 vs 一次性语义冲突 | **重发/重plan 一律重新签发新令牌**（新 nonce 新例），旧例 nonce 作废；**禁续期**——一次性是防重放核心，续期等于开口子；签发序号单调 + supersede 审计 |
| FP-2 | 令牌入 checkpoint（interrupt/resume 后是否有效） | 令牌**自包含可序列化**入 state/checkpoint（验签零 IO 不需查库）；TTL 锚定**墙钟**——resume 后过期即拒（R-c），由分发路径重签发；HITL 挂起期间墙钟照走（审批耗时不延长令牌寿命 · 防挂起囤令牌） |
| FP-3 | 验签性能（每 capability 调用一次） | HMAC 对称验签 + 纯代码约束校验，微秒级；**禁查库禁网络**；observe/enforce 均零 IO；单测附朴素计时 smoke（<1ms/次量级声明，不设硬 CI 阈值） |
| FP-4 | 签名密钥管理 | env `LG_RAG_DELEGATION_TOKEN_SECRET` 注入；**禁硬编码**；轮换=重启（`kid` 预留多密钥并存，v2.0）；enforce 缺密钥 → 拒绝签发+告警（安全默认拒） |
| FP-5 | 进程重启丢失 consumed nonce registry（resume 重放被拒） | resume/replan 路径分发前检测 nonce 已消费/令牌失效 → 重签发（FP-1 同款路径）；consumed registry 仅进程内 TTL 缓存，不作持久化承诺 |
| FP-6 | observe 期误判（合法调用被标 would_block） | observe 不拦 + 台账可复盘；进 enforce 前须观察期报告（承观测模式灰度先例） |
| FP-7 | 模型构造超大/畸形 `requested_scope` | Builder 交集天然收敛；声明集上限 `MAX_SCOPE_IDS=64` 截断+审计（承 step_contract MAX_FIELDS 纪律） |

---

## 6. 验收标准（可机验）

1. 六类拒绝（R-a~R-f）+ 篡改全部断言化通过
2. 全链路携令牌断言通过（supervisor→tool_exec→capability 验签通过）
3. 签发审批留痕可查（只读自动 / 写能力 HITL 两条台账路径）
4. replan 重签发断言通过（旧 nonce 作废）
5. `off` 模式零 diff 回归通过；`observe` would_block 可查；`enforce` 越权拒
6. requested_scope 声明∩裁剪矩阵断言通过（越界剔除留痕 · 未声明兼容 · 只收窄不放宽）
7. `pytest tests` 全绿（含既有 freeze 契约守护）；`ruff check app tests` 通过
8. 图谱回写完成：`capability`/`lg_rag` 行备注 + HG-GRAPH-MODULES 00 代录行；`./scripts/graph-compile.sh` 通过
9. PR 到 master 经 CI 绿后 merge（承「PR 过 CI 自动 merge」先例）

---

## 7. 思考轮回填（R0–R5）

- **R0（读人聊/目标）**：维护者令 2026-09-23 立项长程落地；07/08 双 signed 为真值；V1-A 是五波之首（令牌=B 裁剪输入、D 归因载体）。委派网关是 34 模块中唯一新安全面。
- **R1（范围/非范围）**：图内化为本波边界（无网络面/无表/无 freeze 动）；D1–D6 六块承种子展开；跨服务验签/JWT/撤销列表显式留 v2.0。
- **R2（方案对比）**：三个开放裁定全部两案以上对比并作答——Q1 HMAC 对称（Ed25519 弃）· Q2 分级审批（全 HITL/全自动双弃）· Q3 不入新一级模块（独立模块弃）。签名点位置两案（签发入 lg_rag vs 入 capability）随 Q3 裁定为 capability 内聚（依赖方向顺）。
- **R3（边界/失败路径）**：FP-1~FP-7 全部正面裁定；一次性 vs replan 冲突 = 本波最锋利边界，裁定「重签发禁续期」；TTL 墙钟 vs 逻辑时钟裁定墙钟（自包含验签零 IO 成立的前提）。
- **R4（验收/可测性）**：验收 9 条全部可机验（pytest 断言 + graph-compile + CI）；六类拒绝是变异检验式否定断言（改字段→必失效，缺篡改断言则「验签通过」是假通过）。
- **R5（签收就绪）**：开放裁定无遗留（Q1/Q2/Q3 已答）；图谱义务已随 Q3 裁定（两行备注 · 无新一级模块）；可交 00 代录 HG-SPEC-SIGNOFF 后拆 task。

### 思考轮控制

| 轮 | 状态 | 说明 |
|---|---|---|
| R0 | done | 维护者令 + 07/08 + 双讨论稿 + 图谱已读 |
| R1 | done | 范围 D1–D6 / 非范围锁死 |
| R2 | done | Q1/Q2/Q3 ≥2 案对比 + 裁定 |
| R3 | done | FP-1~FP-7 裁定 |
| R4 | done | 验收 9 条 + test_strategy=required |
| R5 | done | 签收就绪 → 00 代录 HG-SPEC-SIGNOFF |
| early_stop | no | — |

---

## 8. 关联

- 规划真值：[`../agent-infra/07_host_v1_landing_plan_v0.md`](../agent-infra/07_host_v1_landing_plan_v0.md)（signed）
- 种子真值：[`../agent-infra/08_host_v1_wave_spec_outlines_v0.md`](../agent-infra/08_host_v1_wave_spec_outlines_v0.md) §1（signed）
- 启动 invoke：[`../../harness/invokes/by-task/host-v1-landing/invoke_20260923_00_host-v1-landing.md`](../../harness/invokes/by-task/host-v1-landing/invoke_20260923_00_host-v1-landing.md)
- 代码锚点：`app/ops/capability/gateway.py::_prepare_call` · `app/ops/lg_rag/multi/graph.py`（subtask_join 分发）· `app/ops/lg_rag/schemas/subtasks.py` · `app/ops/strategy/builder.py` · `app/ops/capability/policy.py`
- 图谱：`docs/_tech_graph/l1/01_modules.md`（capability/lg_rag 行 · 回写义务见 §4 Q3）
- 后续波：V1-B（场景维裁剪消费 requested_scope）· V1-D（run 归因消费令牌主体绑定）

## 修订记录

| 日期 | 版本 | 内容 |
|---|---|---|
| 2026-09-23 | v0 | 10-spec 初稿：以 08 §1 种子展开 D1–D6；开放裁定 Q1（HMAC-SHA256）/Q2（只读自动·其余 HITL）/Q3（不新增一级模块）全部作答；FP-1~FP-7 裁定；R0–R5 回填 |
| 2026-09-23 | v0 | **00 代录 HG-SPEC-SIGNOFF=approved**（维护者令原话留痕见状态行与人工闸表）；下一棒：00 起草 task（`docs/tasks/active/task_host_v1_delegation_token.md`）→ 20-task-audit |
