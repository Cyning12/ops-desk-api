# Agent Host · 当前架构（对照大纲）索引

> **日期**：2026-09-24  
> **目标真值**：[完整框架大纲 v0.2](../2026-09-23_agent-host-full-framework-outline_v0.md)  
> **总览（当前总架构 + 缺失）**：[00_overview_current_vs_target_v1_zh.md](./00_overview_current_vs_target_v1_zh.md)  
> **扩展策略（名实 · 高 ROI 能力）**：[../2026-09-24_agent-host_extension_strategy_v1_zh.md](../2026-09-24_agent-host_extension_strategy_v1_zh.md)  
> **工程演进**：[多服务工程方案](../2026-09-23_agent-host-multi-service-engineering-architecture_v0.md)  
> **交互浏览**：[../../arch-browser/README.md](../../arch-browser/README.md)（HTML 衍生视图 · 本目录 MD 仍为真值）

## 模块详构（34 = 大纲编号）

| # | 模块 | 层 | 状态 | 详构 |
|---|---|---|---|---|
| 1 | 能力注册与同步 | 控制面 | 部分 | [M01](./modules/M01_capability-registry.md) |
| 2 | 加载期强制 | 控制面 | 部分 | [M02](./modules/M02_load-time-enforce.md) |
| 3 | 可见集裁剪 · 两阶段 | 控制面 | 已落地 | [M03](./modules/M03_visibility-trim.md) |
| 4 | Prompt 管理 | 控制面 | 部分 | [M04](./modules/M04_prompt-mgmt.md) |
| 5 | SO 校验 | 控制面 | 已落地 | [M05](./modules/M05_so-gateway.md) |
| 6 | 委派网关 · 令牌 | 控制面 | 已落地 | [M06](./modules/M06_delegation-gateway.md) |
| 7 | 执行网关 · 六道门 | 控制面 | 已落地 | [M07](./modules/M07_exec-gateway.md) |
| 8 | Policy 硬闸 | 控制面 | 部分 | [M08](./modules/M08_policy-gate.md) |
| 9 | 记忆管理 · 分层 | 控制面 | 部分 | [M09](./modules/M09_memory-layered.md) |
| 10 | 评估与验证 | 控制面 | 部分 | [M10](./modules/M10_eval-verify.md) |
| 11 | 可观测性 | 控制面 | 部分 | [M11](./modules/M11_observability.md) |
| 12 | 成本控制 | 控制面 | 已落地 | [M12](./modules/M12_cost-control.md) |
| 13 | 沙箱隔离 | 控制面 | 不适用 | [M13](./modules/M13_sandbox.md) |
| 14 | 安全策略 · HITL | 控制面 | 部分 | [M14](./modules/M14_hitl-security.md) |
| 15 | 意图解析 | 执行面 | 已落地 | [M15](./modules/M15_intent.md) |
| 16 | 安全护栏检测 | 执行面 | 部分 | [M16](./modules/M16_safety-guard.md) |
| 17 | 主 Agent · Orchestrator | 执行面 | 已落地 | [M17](./modules/M17_orchestrator.md) |
| 18 | 子 Agent · Specialist | 执行面 | 已落地 | [M18](./modules/M18_specialist.md) |
| 19 | 结果反馈（执行面） | 执行面 | 已落地 | [M19](./modules/M19_result-feedback-llm.md) |
| 20 | 模型注册与版本 | LLM工厂 | 部分 | [M20](./modules/M20_model-registry.md) |
| 21 | 模型路由 | LLM工厂 | 部分 | [M21](./modules/M21_model-routing.md) |
| 22 | 降级与容错 | LLM工厂 | 已落地 | [M22](./modules/M22_degrade-resilience.md) |
| 23 | 推理缓存 | LLM工厂 | 已落地 | [M23](./modules/M23_infer-cache.md) |
| 24 | Token 预算与配额 | LLM工厂 | 已落地 | [M24](./modules/M24_token-budget.md) |
| 25 | 模型评测 A/B | LLM工厂 | 部分 | [M25](./modules/M25_model-eval-ab.md) |
| 26 | 模型安全 | LLM工厂 | 部分 | [M26](./modules/M26_model-safety.md) |
| 27 | 垂域 · 车控 | 能力提供方 | 不适用 | [M27](./modules/M27_domain-vehicle.md) |
| 28 | 垂域 · 座舱 | 能力提供方 | 不适用 | [M28](./modules/M28_domain-cabin.md) |
| 29 | 垂域 · 导航 | 能力提供方 | 不适用 | [M29](./modules/M29_domain-nav.md) |
| 30 | 本域能力统一接入 | 能力提供方 | 已落地 | [M30](./modules/M30_capability-providers.md) |
| 31 | 结果回写 | 反馈闭环 | 已落地 | [M31](./modules/M31_result-persist.md) |
| 32 | 成功案例→记忆 | 反馈闭环 | 部分 | [M32](./modules/M32_success-to-memory.md) |
| 33 | 失败案例→失败模式库 | 反馈闭环 | 已落地 | [M33](./modules/M33_failure-patterns.md) |
| 34 | 高频模式→新规则 | 反馈闭环 | 部分 | [M34](./modules/M34_pattern-to-rules.md) |

## 状态统计（v1.0 后）

- 已落地：15  · 部分/雏形：15  · 缺失：0  · 不适用：4

