# Agent Host v1.0 · 五波 SPEC 大纲拆解（v0 · draft · 长程落地流程方向）

> **层级**：L0 规划配套（07 的下游 · 每波 10-spec 的**种子稿**）  
> **状态**：`signed`（2026-09-23 · 00 代录 · 维护者令「签收……授权00签收所有过程文档，完整落地1.0版本内容」· **方向签收**：各波正式 SPEC 仍以独立 HG-SPEC-SIGNOFF 为准（由 00 按本授权代录）· 初稿维护者令「针对 1.0 进行 spec 的详细大纲拆解……细节交由后续每一个 10-spec 再次完善」）  
> **上游**：[`07_host_v1_landing_plan_v0.md`](./07_host_v1_landing_plan_v0.md)（draft · 待 HG-SPEC-SIGNOFF）· 功能面大纲 v0.2 · 工程架构方案（`docs/discussions/2026-09-23_*`）  
> **性质声明**：本文是**大纲**不是 SPEC——每波开工时由 10-spec 以对应章节为种子展开为完整 SPEC（`docs/spec/host-v1-<wave>/SPEC-..._v0.md`），走标准流程（10-spec → HG-SPEC-SIGNOFF → 10-task → 20-task-audit → HG-AUDIT-R1 → 30 → 40 → PR → 图谱回写）。**本文不授权任何 30 改码**。

---

## 0. 波次总览与元信息预判

| 波 | spec_slug（建议） | 一句话目标 | 依赖 | graph_change_layer 预判 | freeze 预判 |
|---|---|---|---|---|---|
| **V1-A** | `host-v1-delegation-token` | 委派授权产物化：令牌六字段 + 签发审批 + 全链路验签 | —（最先） | **可能新一级模块**（SPEC 裁定）· 至少 lg_rag/capability 行备注 | 无（图内化 · 不动 HTTP/SSE 契约） |
| **V1-B** | `host-v1-visibility-scenario-policy` | 可见集两阶段 + manifest 可撤销性四字段加载期强制 | V1-A · 03 轨风险档对齐 | capability/strategy 行备注 · manifest schema 版本 | manifest 格式演进（向后兼容） |
| **V1-C** | `host-v1-llm-factory-closure` | LLM 工厂闭环：预算硬闸 + 推理缓存 + 声明式降级 | 无硬依赖 · 可与 B 并行 | llm 行备注 · 无新模块预判 | 无 |
| **V1-D** | `host-v1-episodic-memory-feedback` | 情景记忆（闸/库分离）+ 失败模式库→规则回写 | V1-A 后 | memory 行备注 · **可能新表**（alembic 义务 SPEC 判） | 无 |
| **V1-E** | `host-v1-splittability-hardening` | multi-replica-verify 实施 + import 机械闸 + registry 抽象 + 策略收敛 | A–D 全落地 | 预期无（验证轨先例）· 按实判 | 无 |

### 跨波公共约束（各波 SPEC 必须继承，不重演论证）

1. **Host 权威**：SO/Policy/令牌验签不可做成模型可选 tool；策略键不可由 plan 写入（承 02 轨）。
2. **默认关/观测模式上线**：新闸先观测后拦截（承 SESSION_SUMMARY/MEMORY_FACTS 先例）；降级必带 `degraded` 标记。
3. **审计记动作不记内容**（承 memory purge 先例）；审计台账面向 #11 清单靠拢。
4. **Tier 语义设计输入**（大纲 v0.2 D3）：A 波令牌=Tier 1（签发原子闸门 · 版本化）· D 波状态机=Tier 2（事件可重放 · 确定性折叠）· 追加类写入=Tier 3（幂等键）。
5. **零 freeze 动**：不改 lg-rag-sse-v1 / lg-rag-http-v1 / lc-evidence-http-v1；SSE 零新事件类型（若必须 → 单列 freeze 升级点）。
6. **图谱回写**随 30 交付；人签记录新行留 00 代录位。

---

## 1. V1-A · delegation-token（委派授权产物化）

### 1.1 背景与目标

委派网关是 34 模块对照中**唯一的新安全面**（v0.1 测评点 5）：supervisor→工人分发已有 step_contract 校验点（consumes/produces · prefix_touch_required→hitl_required），但**没有授权产物**——工人的能力调用权来自图内位置而非可核验的凭据。一句话目标：委派时签发**令牌**（六字段：能力集/TTL/一次性/参数约束/主体绑定/签名），工人执行能力前验签，签发本身走高危审批；**图内化，无网络面**。

### 1.2 范围（交付块拆解 · D 块为 10-spec 展开单位）

| 块 | 内容大纲 |
|---|---|
| D1 令牌模型 | 六字段 dataclass：`capability_set` / `ttl` / `one_shot` / `param_constraints` / `subject_binding`（tenant+user+run+subtask）/ `signature`；不可变；版本字段 |
| D2 签发点 | subtask_join/observe 分发路径签发；签发审批策略（安全域自动 vs HITL——**开放裁定 · 见 §1.5 Q2**）；Tier 1 语义（版本化 · 并发签发检测） |
| D3 验签点 | `tool_exec` 进 capability `_prepare_call` 闸链**之前**插验签门；无令牌/越集/过期/重用/参数越约束/主体不符 → 拒（`ok=False` 不拖垮整图 · 承 v0 失败语义） |
| D4 审计 | 签发/验签通过/拒绝进台账（记动作不记内容 · 参数字段哈希化） |
| D5 requested_scope | supervisor plan 输出携带声明式 scope（A2）；Builder 从隐式 allowlist 升级为「声明∩裁剪」 |
| D6 测试 | 六类拒绝断言 + 全链路携令牌断言 + 审批留痕断言 + 篡改断言（改字段→签名失效） |

### 1.3 非范围

跨服务验签 / JWT 公钥体系 / 网络面令牌传递（v2.0）· 用户态认证令牌 · 动态 StateGraph · 改既有 freeze 契约。

### 1.4 failure_paths（预判 · 10-spec 补强）

| 路径 | 处置方向 |
|---|---|
| ReAct replan 重发子任务与一次性语义冲突 | SPEC 定：replan 重新签发（新 one_shot 例）还是令牌续期——**须正面回答** |
| 令牌入 checkpoint（interrupt/resume 恢复后令牌是否仍有效） | TTL 锚定墙钟 vs run 逻辑时钟 · SPEC 裁定 |
| 验签性能（每 capability 调用一次） | 纯本地对称验签 · 微秒级 · 禁查库 |
| 签名密钥管理 | 进程内密钥起步（env 注入 · 轮换=重启）；**禁硬编码** |

### 1.5 验收标准大纲 + 开放裁定（留 10-spec）

验收：六类拒绝全部断言化 · 全链路携令牌 · 签发审批留痕可查 · 篡改即失效 · 图谱回写完成。  
**开放裁定**：Q1 签名机制选型（HS256 对称 vs  Ed25519——图内场景对称足够？）· Q2 签发审批默认口径（哪些 scope 组合触发 HITL · 安全域自动放行的边界）· Q3 委派网关是否立**新一级模块**（图谱义务随之定）。

### 1.6 R0–R5 思考轮预判

R0 令牌是授权产物不是认证 · R1 图内化为本波边界 · R2 签名机制/签发点位置两案对比 · R3 一次性与 replan/断点恢复冲突 · R4 六类拒绝可机验 · R5 新模块裁定后人签。

---

## 2. V1-B · visibility-scenario-policy（可见集两阶段 + 可撤销性声明）

### 2.1 背景与目标

Builder allowlist（Registry∩Policy）只是**身份维**单阶段；测评点 3/4 要求：场景维二次裁剪（安全默认「宁可无工具」· 剔除项进台账）+ manifest 可撤销性四字段（`reversible`/`execution_type`/`max_reversal_latency`/`requires_stop_support` · 缺失→默认 HITL · 加载期强制）。

### 2.2 范围

| 块 | 内容大纲 |
|---|---|
| D1 意图风险档 | IntentV1 增 `risk_level` 字段（**先对齐 03 策略轨现行 schema** · U2）；档位数与口径 SPEC 定 |
| D2 场景维裁剪 | 身份维（请求前）→ 基础可见集 → 场景维（意图+风险档驱动）→ 最终可见集；安全默认：裁剪歧义/异常 → 退化成无工具也不放行 |
| D3 剔除项审计 | 被裁掉的能力 id + 裁剪原因进台账（#11 审计清单第一项落地） |
| D4 manifest 四字段 | schema 化 + 加载期强制校验（CI 静态 + 运行时兜底）；缺失 → 该能力默认 HITL_REQUIRED；向后兼容（既有 manifest 无字段 → 默认而非报错） |
| D5 测试 | 两阶段裁剪矩阵断言 · 安全默认断言 · 四字段缺失默认断言 · 剔除台账断言 |

### 2.3 非范围

HITL 三档执行侧全体系（本波只做 **manifest 声明面**与默认兜底 · 执行侧消费在后续波）· 动态 StateGraph · 跨进程可见集下发。

### 2.4 failure_paths（预判）

| 路径 | 处置方向 |
|---|---|
| 意图风险档误判导致过度裁剪 | 安全默认方向正确（宁缺毋滥）· 误判进台账可复盘 |
| 03 轨风险档演进冲突 | 以 03 现行 schema 为准延展 · 冲突回 10-spec |
| 四字段缺失存量 manifest 批量默认 HITL 致可用性降 | 灰度：先告警后强制（承观测模式先例） |
| 裁剪耗时 | 纯代码 · 目标 <10ms（承工程方案 P2 出口） |

### 2.5 验收标准大纲 + 开放裁定

验收：两阶段裁剪矩阵 · 安全默认生效 · 剔除项台账可查 · 四字段加载期强制。  
**开放裁定**：Q1 风险档粒度（3 档 low/mid/high？）· Q2 场景维输入除意图外是否含会话上下文 · Q3 `execution_type` 三值与既有 capability 危险度标注的映射关系。

### 2.6 R0–R5 预判

R0 裁剪是治理不是功能 · R1 身份维已有 · R2 风险档来源两案（intent 内嵌 vs 独立分类器）· R3 过度裁剪方向 · R4 矩阵可机验 · R5 与 03 轨边界确认后人签。

---

## 3. V1-C · llm-factory-closure（预算 + 缓存 + 声明式降级）

### 3.1 背景与目标

usage 账本是记账不是预算（测评点 2 判准）；推理缓存缺失；降级是同档重试+熔断无跨档链。一句话：预算硬闸（默认观测）+ 耗尽降级路径（小模型档→规则/缓存）+ 推理缓存（plan/参数模板）+ 档级 fallback 声明进 `model_catalog`。

### 3.2 范围

| 块 | 内容大纲 |
|---|---|
| D1 预算声明与检查点 | 会话/任务级预算声明；调用前预估 + 调用后记账（usage 账本复用）；**默认观测模式**（只记不拦）→ 灰度开拦截 |
| D2 耗尽降级链 | 预算耗尽 → 小模型档 → 规则引擎/缓存；**防假降级**（U3 · 声明才降级 · 必带 `degraded` 标记跟数据走 · 承 fallback.py 铁律） |
| D3 推理缓存 | 对象=高频意图 plan 模板 + 高频能力参数模板；键=intent/capability+参数哈希；失效随模型/prompt 版本 bump；命中率观测进 span |
| D4 声明式降级 | 档级 fallback 声明进 `model_catalog.TASK_TIER_MODELS`（大→小→规则）；不散落调用点 |
| D5 指标 | Cost per Successful Task 定义 + 产出面（Langfuse span 聚合） |
| D6 测试 | 预算检查点断言 · 降级标记断言（ok=True 也可能降级 · 通断同看标记）· 缓存命中/失效断言 · 版本 bump 失效断言 |

### 3.3 非范围

跨 provider 计费对账 · 缓存跨进程共享（进程内起步）· 预算跨租户统筹（先会话/任务两级）。

### 3.4 failure_paths（预判）

| 路径 | 处置方向 |
|---|---|
| 预估成本与实际偏差大（流式 token 不可预知） | 调用后记账为准 · 预估算保守下限 · 超限在下一次调用前拦截 |
| 缓存命中陈旧 plan（能力目录已变） | 缓存键含 catalog 版本/可见集哈希 · SPEC 定 |
| 降级链末端（规则也失败） | `ok=False` + degraded 标记 · 不伪造成功 |
| 观测→拦截灰度误伤 | 拦截开关按 surface 粒度 · 默认关 |

### 3.5 验收标准大纲 + 开放裁定

验收：预算两级生效 · 耗尽降级带标记 · 缓存命中可观测 · 降级声明集中 · Cost per Successful Task 有数。  
**开放裁定**：Q1 预算检查点在 llm 层还是 capability 层（双检查点？）· Q2 缓存对流式 answer 是否适用（预判：只缓存 plan/参数，不缓存终答）· Q3 规则引擎档的具体形态（固定文案 vs 模板）。

### 3.6 R0–R5 预判

R0 账本是起点不是终点 · R1 进程内为本波边界 · R2 检查点位置两案 · R3 假降级防线 · R4 全链路标记可机验 · R5 观测模式灰度口径确认后人签。

---

## 4. V1-D · episodic-memory-feedback（情景记忆 + 失败模式库）

### 4.1 背景与目标

事实/偏好记忆已 stable（闸 + 状态机 + 融合召回）；测评与大纲组 D 缺：**情景记忆**（成功/失败模式 · 供规划参考）与**失败模式库→规则回写**。铁律：**与事实记忆闸/库物理分离 · 零互写**（U4）。

### 4.2 范围

| 块 | 内容大纲 |
|---|---|
| D1 episode schema | 任务类型 / 上下文指纹 / plan 摘要 / 工具序列 / 结果与成败标签 / run 归因（tenant+run_id） |
| D2 独立写入闸 | `should_write_episode` 判据（与 `should_write` 分立 · 物理不同函数不同表） |
| D3 召回注入 | 规划时召回相似成功 episode（注入面与事实记忆**分节** · 承 `[已知事实]`/`[用户偏好]` 先例增 `[相似经验]`） |
| D4 失败模式聚类 | 离线任务：run_events + subtask_results 聚类 → 模式库（指纹规则 vs embedding 聚类 · SPEC 选型） |
| D5 规则回写 | 高频模式 → redlines/manifest **建议**（**人工确认后生效** · 禁全自动） |
| D6 测试 | 零互写断言（事实表/episode 表）· 召回分节断言 · 聚类报告断言 · 回写建议未确认不生效断言 |

### 4.3 非范围

D3 跨进程同步（v2.0）· 自动规则回写 · 实时聚类（离线批处理起步）· 用户可见的记忆管理面。

### 4.4 failure_paths（预判）

| 路径 | 处置方向 |
|---|---|
| episode 污染（错误经验被召回放大） | 成败标签 + 来源权重 + `revoke_by_source` 承事实记忆先例 |
| 聚类噪声（低频偶发被当模式） | 频次阈值 + 人工确认闸 |
| 隐私/租户隔离 | tenant 谓词承阶段 T 纪律 · 跨租户零召回断言 |
| 新表 alembic | SPEC §2 判定义务 · off 态不读不写 drop 安全（承 session_summaries 先例） |

### 4.5 验收标准大纲 + 开放裁定

验收：零互写 · 召回分节 · 聚类报告产出 · 建议未确认零生效 · 默认关零 diff。  
**开放裁定**：Q1 episode 粒度（run 级 vs subtask 级）· Q2 聚类选型（指纹规则起步？）· Q3 注入 token 预算占比上限。

### 4.6 R0–R5 预判

R0 经验≠事实 · R1 闸/库分离为边界 · R2 粒度与聚类两案 · R3 污染放大防线 · R4 零互写可机验 · R5 alembic 义务确认后人签。

---

## 5. V1-E · splittability-hardening（可拆性硬化 · 收尾）

### 5.1 背景与目标

工程方案 C1/C5/C7 + signed `multi-replica-verify`：功能稳定后做可拆性硬化——**这是 v1.0 与 v2.0 的分界线**：做完本波，上楼只是换传输层。

### 5.2 范围

| 块 | 内容大纲 |
|---|---|
| D1 multi-replica-verify 实施 | 按 signed SPEC 直接执行：双进程 pytest 集成测 + compose runbook + 状态边界清单（产物=验证证据 · 预期零生产码） |
| D2 import 机械闸 | 模块依赖出边 CI 化（import-linter 或自实现 · 真值=`01_modules.md` 出边列） |
| D3 registry 接口抽象 | capability registry 读写分离接口化（读侧缓存抽象 · 写侧注册中心客户端接口 · 本地实现为默认） |
| D4 策略收敛 | env 散落盘点 → 策略包声明式（版本化 · 承 prompts 资产化先例） |
| D5 问题修复 | 验证发现的阻断 bug → **另开 fix task**（承 SPEC 不顺手修纪律） |

### 5.3 非范围

实际多副本生产部署 · 服务拆分 · 注册中心实现（接口先行，实现在 v2.0）。

### 5.4 failure_paths（预判）

| 路径 | 处置方向 |
|---|---|
| 双进程验证发现状态泄漏 | 另开 fix task · 本波记录边界清单 |
| import 闸误报（既有合理越界） | 白名单机制 + 逐条消账 · 图谱出边同步修正 |
| registry 抽象改动面大 | 只抽接口不改语义 · 对拍测试零 diff |

### 5.5 验收标准大纲 + 开放裁定

验收：双进程报告全绿 · import 闸 CI 绿 · registry 接口可替换 · 策略包盘点完成。  
**开放裁定**：Q1 import 闸工具选型（import-linter vs 自实现 ruff 插件）· Q2 策略包格式与 env 回退关系。

### 5.6 R0–R5 预判

R0 硬化不是重构 · R1 signed SPEC 为直接输入 · R2 闸工具两案 · R3 对拍零 diff 防线 · R4 报告即验收 · R5 v1.0 出口清单全表复核后人签。

---

## 6. 使用方式（10-spec 种子→完整 SPEC 的展开规则）

1. 每波开工：10-spec 复制对应章节为 `docs/spec/host-v1-<wave>/SPEC-host-v1-<wave>_v0.md`，展开 §x.2 的 D 块为正式范围条目、§x.5 开放裁定为 R2 方案对比（≥2 案 · 推荐 · 弃选）、failure_paths 补全。
2. **开放裁定（Q1–Qn）是 10-spec 的必答题**，不许带入 task。
3. 顺序纪律承 07：A 先行 · C 可与 B 并行 · E 收尾；每波 HG-SPEC-SIGNOFF 人签后才拆 task。
4. 本大纲与实际 SPEC 冲突时**以 signed SPEC 为准**（大纲是方向不是契约）。

## 7. 关联

- 规划：[`07_host_v1_landing_plan_v0.md`](./07_host_v1_landing_plan_v0.md)（波次/顺序/出口标准真值）
- 功能面：`../../discussions/2026-09-23_agent-host-full-framework-outline_v0.md`（v0.2 · D3 三层并发）
- 工程面：`../../discussions/2026-09-23_agent-host-multi-service-engineering-architecture_v0.md`（C1–C7 · V1-E 输入）
- 前置 SPEC：`../multi-replica-verify/`（signed · V1-E D1 直接执行）· `03_strategy_and_intent_plan_v0.md`（V1-B 风险档对齐）
