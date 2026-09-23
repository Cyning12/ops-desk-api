# Agent Host v1.0 · 大版本落地规划（v0 · draft）

> **层级**：L0 规划（接 02 编号序列 · 02 轨 H1–H5 的继任者）  
> **状态**：`draft`（2026-09-23 · **待 HG-SPEC-SIGNOFF 维护者签收** · 本文不授权任何 30 改码）  
> **上游**：[`../../discussions/2026-09-23_agent-host-full-framework-outline_v0.md`](../../discussions/2026-09-23_agent-host-full-framework-outline_v0.md)（功能面 34 模块对照 **v0.1** · 三方测评六点已补强）· [`../../discussions/2026-09-23_agent-host-multi-service-engineering-architecture_v0.md`](../../discussions/2026-09-23_agent-host-multi-service-engineering-architecture_v0.md)（工程面 P0–P3 / C1–C7 / M0–M5）  
> **前置轨**：[`02_agent_host_plan_v0.md`](./02_agent_host_plan_v0.md)（**completed** · H1–H5 CLOSE）· [`../multi-replica-verify/SPEC-multi-replica-verify_v1.md`](../multi-replica-verify/SPEC-multi-replica-verify_v1.md)（**signed** · V1-E 直接前置）· [`06_host_comms_boundary_spec_v0.md`](./06_host_comms_boundary_spec_v0.md)（signed）  
> **Open Folder**：`ops-desk-api/`

---

## Harness 元信息

| 字段 | 值 |
|---|---|
| **plan_slug** | `host-v1-landing-plan` |
| **test_strategy** | 按子波次定（各波 SPEC 自填） |
| **graph_change_layer（建议）** | 多为 `G-L1` 行备注；**V1-A 可能触发新一级模块裁定**（委派网关独立 or 入既有行 · SPEC 阶段定） |
| **freeze_id** | 无新 freeze 预期；若波次动 SSE 帧/HTTP 契约须单列 freeze |
| **默认分支（建议）** | `task/host-v1-<wave-slug>` |

### 人工闸（SPEC 阶段）

| human_gate_id | status | 说明 |
|---|---|---|
| **HG-SPEC-SIGNOFF** | **pending** | 待维护者签收本规划；签收后 00 方可拆 V1-A task |

---

## 1. 反思：当前大纲能否支撑大版本落地

**结论：可以，但「大版本」必须正确定义——Host v1.0 = 功能面 M0 四组缺口 + 工程面 M1 可拆性硬化；明确不含多服务拆分（那是 v2.0，触发条件驱动）。**

### 1.1 三支柱已立

| 支柱 | 证据 |
|---|---|
| **基座 stable** | v0.1 大纲 34 模块中 8 项「已有」（执行网关六道闸 / SO 校验 / 主 Agent / 子 Agent / 结果反馈 / 结果回写 / 降级容错 / 能力提供方等价物）；「雏形」项全部有代码落点，不是从零 |
| **文档链闭合** | v0.1 大纲（差距清单 + 字段级起点）→ 工程架构方案（C1–C7 可拆性约束 + 部署形态）→ 本规划（波次与顺序）→ signed 前置（multi-replica-verify 实证方案）——从「想什么」到「怎么验」无断点 |
| **过程轨与主线清洁** | spec-wave 3.0.1 + task/闸/verify 纪律；主线已裁定、legacy/dormant 已隔离（不被旧面拖累）；图谱追平至 2026-09-23 |

### 1.2 诚实的不确定性（各波 SPEC 阶段必须正面回答）

| # | 不确定性 | 所在波 |
|---|---|---|
| U1 | 委派令牌签发是**新安全面**：签发审批（HITL or 安全域）的触发口径、验签性能、令牌撤销语义 | V1-A |
| U2 | 场景维裁剪依赖**意图风险分级口径**——IntentV1 目前无风险档，需与 03 策略轨对齐演进 | V1-B |
| U3 | 预算硬闸的降级语义须防「假降级」（承 `fallback.py` 声明才降级 / 必带 `degraded` 标记铁律） | V1-C |
| U4 | 情景记忆与既有事实记忆的**闸/库分离**设计（should_write 判据不同 · 污染隔离） | V1-D |
| U5 | 波次多人签密：5 波 × （HG-SPEC-SIGNOFF + HG-AUDIT-R1），维护者带宽是真实约束——每波都是可停稳态，允许波间暂停 | 全轨 |

### 1.3 与在轨 SPEC 的关系（不混改）

- **03 策略轨（active）**：V1-B 的意图风险档与其 Intent schema 演进**对齐不重开**；若 03 先落地风险档，V1-B 直接消费。
- **04 测评轨（active）**：V1.0 出口标准的 SLI/SLO 四项指标定义与其观测面对齐。
- **05 传输/会话轨（active）**：SSE 主线已稳定；v1.0 各波**不改传输契约**（除非单列 freeze）。
- **multi-replica-verify（signed · 未实施）**：V1-E 的第一件事，不提前不推迟。

---

## 2. v1.0 范围 / 非范围

**范围（M0 四组 + M1 硬化）**：委派令牌图内化 · requested_scope 显式化 · 场景维可见集裁剪 · manifest 可撤销性四字段 · 预算硬闸 · 推理缓存 · 声明式降级链 · 情景记忆 · 失败模式库 · import 机械闸 · registry 接口抽象 · 双进程实证。

**非范围**：多服务拆分（v2.0 · 触发条件见工程方案 §7）· D3 记忆跨进程同步（不建）· microVM 沙箱 · chat legacy 面 · 完整 Skill 引擎 · 动态 StateGraph compile · 模型可选「校验 tool」（Host 权威不动摇）。

---

## 3. 执行波次总表（v1.0 = 5 波）

| 序 | 波次 ID | 内容（字段级起点见 v0.1 大纲 §6） | 建议 task slug | 依赖 | 图谱义务预判 |
|---|---|---|---|---|---|
| **V1-A** | `delegation-token` | **A1 委派令牌图内化**：六字段（能力集/TTL/一次性/参数约束/主体绑定/签名）· 签发走 HITL/安全域审批 · subtask_id 绑定验签 + **A2 requested_scope 显式化**（plan 输出携带声明式 scope） | `host-v1-delegation-token` | —（最先） | **可能新一级模块**（委派网关独立 or 入 `lg_rag`/`capability` 行 · SPEC 裁定）；人签预留 |
| **V1-B** | `visibility-scenario-policy` | **B1 场景维裁剪**（意图风险档驱动第二阶段 · 安全默认「宁可无工具」· 剔除项进审计台账）+ **B2 manifest 可撤销性四字段**（`reversible`/`execution_type`/`max_reversal_latency`/`requires_stop_support` · 缺→默认 HITL · 加载期校验） | `host-v1-visibility-scenario-policy` | V1-A（scope 声明是裁剪输入）· 03 轨风险档对齐（U2） | capability/strategy 行备注 · manifest schema 版本 |
| **V1-C** | `llm-factory-closure` | **C1 预算硬闸**（会话/任务级 · 耗尽降级路径小模型档→规则/缓存 · 防假降级 U3 · Cost per Successful Task 指标）+ **C2 推理缓存**（plan/参数模板 · 参数哈希键 · 版本 bump 失效）+ **C3 声明式降级**（档级 fallback 进 model_catalog） | `host-v1-llm-factory-closure` | 无硬依赖（usage 账本已有）· **可与 V1-B 并行** | llm 行备注 · 无新模块预判 |
| **V1-D** | `episodic-memory-feedback` | **D1 情景记忆**（成功/失败模式 · 与事实记忆闸/库分离 U4）+ **D2 失败模式库 → 规则回写**（聚类管线 → redlines/manifest 半自动回路）；**D3 明确不建** | `host-v1-episodic-memory-feedback` | V1-A 后（模式沉淀需 run 上下文归因） | memory 行备注 · 可能新表（SPEC 判 alembic 义务） |
| **V1-E** | `splittability-hardening` | **multi-replica-verify 实施**（signed SPEC 直接执行）+ **C5 import 机械闸**（模块出边 = 未来服务边界 · CI）+ **C1 registry 接口抽象**（读写分离可替换实现）+ **C7 策略收敛** | `host-v1-splittability-hardening` | V1-A~D 全落地（功能稳定后硬化）· signed SPEC 已备 | 预期无（验证轨先例）· 按实判 |

### 3.1 顺序纪律（承 02 轨「顺序钉死」先例）

```text
V1-A ──► V1-B ──┐
   └────► V1-D ──┼──► V1-E（硬化收尾）
        V1-C ────┘   （C 与 B/D 可并行 · E 必须最后）
```

- **A 必先行**：令牌是 B 的裁剪输入、D 的归因载体。
- **C 可并行**：LLM 工厂闭环与业务面无耦合，可插 B/D 间隙。
- **E 必收尾**：可拆性硬化在功能稳定后做，否则接口抽象追不上功能变动。
- **每波结束 = 可停稳态**：允许波间暂停（U5），不强求连续推进。

### 3.2 单波标准流程（不可跳步）

`10-spec` → `HG-SPEC-SIGNOFF`（维护者）→ `10-task` → `20-task-audit` → `HG-AUDIT-R1` → `30` → `40` → PR → 图谱回写（HG-GRAPH-MODULES）→ CLOSE 归档。

---

## 4. v1.0 出口标准（全轨验收清单）

| 面 | 出口判据 |
|---|---|
| 委派链路 | supervisor→工人全链路携令牌；无令牌/越权/过期→拒绝且断言化；签发审批留痕 |
| 可见集 | 两阶段裁剪上线；安全默认生效；剔除项进审计台账可查 |
| manifest | 可撤销性四字段 schema 化；缺失→默认 HITL；加载期强制校验 |
| LLM 工厂 | 预算硬闸生效；耗尽降级必带 `degraded` 标记；缓存命中率可观测；降级链声明式 |
| 记忆 | 情景记忆独立闸/库（零事实记忆污染断言）；失败模式聚类报告产出 |
| 工程 | import 机械闸 CI 绿；双进程共享 PG 验证报告全绿；registry 接口可替换实现 |
| 指标 | SLI/SLO 候选四项（端到端 P99 / 任务完成率 / 能力命中率 / Cost per Successful Task）有定义、有数、有看板 |
| 图谱 | 01_modules 全回写；HG-GRAPH-MODULES 签录链完整 |

---

## 5. 风险与对冲

| 风险 | 对冲 |
|---|---|
| 令牌面做重（过早跨服务化） | V1-A 明确**图内化**：subtask_id 绑定 · 无网络面；跨服务验签留 v2.0 |
| 意图风险档与 03 轨冲突演进 | V1-B SPEC 阶段先对齐 03 现行 schema；冲突则以 03 为准延展 |
| 预算硬闸误伤主线 | 默认**观测模式**上线（只记账不拦截）→ 灰度后开拦截（承 SESSION_SUMMARY/MEMORY_FACTS 默认关先例） |
| 情景记忆污染事实记忆 | 闸/库物理分离 + 零互写断言（U4） |
| 波间停顿烂尾 | 每波出口 = 可用稳态；规划文随时可凭出口清单复盘续推 |

---

## 6. 关联

- 功能面：`../../discussions/2026-09-23_agent-host-full-framework-outline_v0.md`（v0.1 · 差距与字段级起点）
- 工程面：`../../discussions/2026-09-23_agent-host-multi-service-engineering-architecture_v0.md`（v1.0 = 其 M0+M1 · v2.0 = M2+）
- 前置：`../multi-replica-verify/`（signed · V1-E）· `02_agent_host_plan_v0.md`（completed）· `06_host_comms_boundary_spec_v0.md`（signed）
- 在轨对齐：`03_strategy_and_intent_plan_v0.md` · `04_eval_and_observability_plan_v0.md` · `05_lg_rag_transport_and_session_plan_v0.md`
- 图谱：`docs/_tech_graph/l1/01_modules.md`（模块出边 = 服务边界真值）
