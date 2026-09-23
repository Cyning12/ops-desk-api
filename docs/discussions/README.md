# 方案讨论归档（Discussions）

本目录存放**非 task 执行产物**的架构/方案讨论小结，供后续 task 起草与实现参考。

## 使用约定

| 项 | 约定 |
|---|---|
| 命名 | `YYYY-MM-DD_<主题短名>.md` |
| 状态 | 讨论稿，**非** freeze 契约；落地以 `docs/tasks/active/` + DESIGN/IMPL 为准 |
| 内容 | 结论、边界、对照表、Mermaid；可链到 Agently 等外部仓路径 |
| 索引 | 每篇文末维护「关联 task / 图谱 / 代码入口」 |

## 归档列表

| 日期 | 文件 | 主题 |
|---|---|---|
| 2026-08-26 | [2026-08-26_lg-rag-agent-capability-architecture.md](./2026-08-26_lg-rag-agent-capability-architecture.md) | lg_rag 质量闸 / 多智能体 / 能力网关 / output-control 对照 → [agent-infra SPEC](../spec/agent-infra/) |
| 2026-08-26 | [2026-08-26_agent-host-architecture-phase-summary.md](./2026-08-26_agent-host-architecture-phase-summary.md) | **阶段性总结** + 架构图例 → [`02_agent_host_plan_v0`](../spec/agent-infra/02_agent_host_plan_v0.md) |
| 2026-09-23 | [2026-09-23_agent-host-full-framework-outline_v0.md](./2026-09-23_agent-host-full-framework-outline_v0.md) | **Agent Host 完整框架大纲**：主线裁定（复杂 Agent 进化）· 五层 34 模块对照（已有/雏形/缺失/不适用）· 三道防线映射 · 废弃/休眠清单 · 大模块方向（不落地）→ [`01_modules.md`](../_tech_graph/l1/01_modules.md) |
