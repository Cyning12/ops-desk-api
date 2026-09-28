# Invoke · 00 启动 · host-v1-landing（Agent Host v1.0 长程落地 · 新窗口执行）

> **日期**：2026-09-23  
> **帽**：00（统筹 · 可委派 10-spec/10-task/20/30/40 子帽）  
> **维护者令（原话留痕）**：「签收，并生成对此长程任务的00启动Prompt，新窗口执行，授权00签收所有过程文档，完整落地1.0版本内容」  
> **授权面**：**00 代签/代录本长程全部过程文档**——各波 HG-SPEC-SIGNOFF（10-spec 产物）· HG-TASK-DRAFT · HG-AUDIT-R1（20-task-audit 后）· HG-GRAPH-MODULES（图谱回写）；每处代录必须「维护者令原话 + 日期」留痕（承 memory-facts-p0 / multi-replica-verify 先例）。  
> **规划真值**：`docs/spec/agent-infra/07_host_v1_landing_plan_v0.md`（**signed**）  
> **种子真值**：`docs/spec/agent-infra/08_host_v1_wave_spec_outlines_v0.md`（**signed · 方向**）  
> **执行窗口**：新窗口 · Open Folder = `ops-desk-api/` 仓根

---

## 1. 目标（一句话）

按 07 规划**完整落地 Agent Host v1.0**：五波 V1-A~E 全 CLOSE，达到 07 §4 出口标准八面；每波独立 PR、CI 绿后 merge（承「每次 PR 到 main 通过 CI 后自动 merge」先例）。

## 2. 开工前必读（新窗口按序）

1. `AGENTS.md`（仓纪律 · 新会话启动纪律）
2. `docs/spec/agent-infra/07_host_v1_landing_plan_v0.md`（波次/顺序/出口标准）
3. `docs/spec/agent-infra/08_host_v1_wave_spec_outlines_v0.md`（当前波对应章节 = 10-spec 种子）
4. `docs/discussions/2026-09-23_agent-host-full-framework-outline_v0.md`（v0.2 · 差距与字段级起点 · D3 三层并发）
5. `docs/discussions/2026-09-23_agent-host-multi-service-engineering-architecture_v0.md`（C1–C7 可拆性约束）
6. `docs/_tech_graph/l1/01_modules.md`（主线与遗留约定 · 模块出边）
7. 当前波附加：V1-B 加读 `docs/spec/agent-infra/03_strategy_and_intent_plan_v0.md`；V1-E 加读 `docs/spec/multi-replica-verify/SPEC-multi-replica-verify_v1.md`（signed · 直接执行）

## 3. 波次与顺序纪律（钉死）

```text
V1-A ──► V1-B ──┐
   └────► V1-D ──┼──► V1-E（硬化收尾）
        V1-C ────┘   （C 与 B/D 可并行 · E 必须最后）
```

| 波 | spec_slug | 分支 | 关键开放裁定（10-spec 必答） |
|---|---|---|---|
| V1-A | `host-v1-delegation-token` | `task/host-v1-delegation-token` | Q1 签名机制 · Q2 签发审批口径 · **Q3 委派网关是否立新一级模块**（图谱义务随之） |
| V1-B | `host-v1-visibility-scenario-policy` | `task/host-v1-visibility-scenario-policy` | Q1 风险档粒度 · Q2 场景维输入 · Q3 execution_type 映射 |
| V1-C | `host-v1-llm-factory-closure` | `task/host-v1-llm-factory-closure` | Q1 预算检查点层位 · Q2 缓存适用范围 · Q3 规则档形态 |
| V1-D | `host-v1-episodic-memory-feedback` | `task/host-v1-episodic-memory-feedback` | Q1 episode 粒度 · Q2 聚类选型 · Q3 注入预算上限 |
| V1-E | `host-v1-splittability-hardening` | `task/host-v1-splittability-hardening` | Q1 import 闸工具 · Q2 策略包格式 |

## 4. 单波标准流程（不可跳步）

`10-spec`（以 08 对应章为种子展开 · 开放裁定全部作答 · R0–R5 回填）→ **00 代录 HG-SPEC-SIGNOFF**（原话留痕）→ `10-task` → `20-task-audit` → **00 代录 HG-AUDIT-R1** → `30`（分支改码 · 禁 main/master 直改）→ `40` → **PR + CI 绿 + merge** → 图谱回写（**00 代录 HG-GRAPH-MODULES**）→ task CLOSE 归档 done/ + Hub 补登 → 下一波。

## 5. 跨波公共约束（承 08 §0.1 · 各波 SPEC/task 继承不重演）

1. **Host 权威**：SO/Policy/令牌验签不做成模型可选 tool；策略键不可由 plan 写入。
2. **默认关/观测模式上线**：新闸先观测后拦截；降级必带 `degraded` 标记跟数据走。
3. **审计记动作不记内容**；台账面向大纲 #11 清单（能力调用/HITL/紧急停用/Policy 拦截/裁剪剔除项）。
4. **Tier 语义**：A 波令牌=Tier 1（签发原子闸门 · 版本化 · 并发检测）· D 波状态机=Tier 2（事件可重放 · 确定性折叠）· 追加写入=Tier 3（幂等键）。
5. **零 freeze 动**：不改 lg-rag-sse-v1 / lg-rag-http-v1 / lc-evidence-http-v1；SSE 零新事件类型（必须 → 单列 freeze 升级点回 10-spec）。
6. **图谱回写**随 30 交付；**V1-A Q3 若裁定新一级模块 → 图谱义务升级 + HG-GRAPH-MODULES 行如实登记**。

## 6. 回炉与停止条款

- **形态偏离回炉**：30 实现形态偏离 task 预判（新模块/新表/新事件类型/freeze 变更）→ 停 30，回 10-spec/10-task 补闸 + 图谱如实登记后续做（承 graph_delta_note 条款）。
- **每波 = 可停稳态**：波间允许暂停；任一时刻仓库处于可用状态。
- **阻断上报**：同一阻断条件连续 3 轮无法推进 → 停并上报维护者（列具体条件），不得硬闯。
- **不顺手修**：验证/实扫发现的阻断 bug → 另开 fix task（承 multi-replica-verify 纪律）。

## 7. v1.0 出口标准（全轨验收 · 07 §4 真值复述）

委派全链路携令牌越权拒 · 两阶段裁剪+剔除项可查 · manifest 四字段加载期强制 · 预算闸降级带标记 · 情景记忆零污染断言 · import 闸 CI 绿+双进程报告全绿 · SLI/SLO 四项有数 · 图谱签录链完整。

## 8. 00 行为纪律（新窗口）

- **00 不亲自 30 改码**（承 harness-00-delegate-only）：30 一律委派子 Agent；00 负责拆波、签录、验收、图谱、PR。
- 每波首输出 **GATE_VERIFY 表**（承 `FRAGMENT_30_gate_verify_v1_zh.md`）；闸真值在 task 人工闸表，非聊天字面。
- 过程 invoke 落 `docs/harness/invokes/by-task/<wave-slug>/`（`invoke_retention_profile: default`）。
- 会话锚丢失 → 读本文件 + 07/08 重锚（承 hat-reanchor 纪律）。

---

## 修订

| 日期 | 说明 |
|---|---|
| 2026-09-23 | 00 启动 invoke 初版（维护者令原话留痕 · 07/08 signed 同令代录） |
| 2026-09-24 | **终条（长程令全链路闭合）**：五波 V1-A~E 全 CLOSE（PR #179/#181/#183/#184/#187 · 过程 PR #180/#182/#186/#188/#189）+ dualproc fix #190/#192 + 出口复核 PASS-WITH-GAP → G1 closed（#193/#194）+ 三方验收 #195 PASS · 长程令「签收，并生成对此长程任务的00启动Prompt，新窗口执行，授权00签收所有过程文档，完整落地1.0版本内容」（2026-09-23）**全链路闭合** · 00 代录（维护者令原话：「签收，生成00 Prompt，在新窗口开始D1统筹」2026-09-24）· 后续轨：`host-v1-wrap-up`（D1 文档闭环 · 本终条即其 D1-4） |
