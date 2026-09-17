# PROMPT · 00 · Stage H · Capability / Host 契约硬化（统筹）

> **用途**：维护者整段复制「复制区」开新窗，指定本会话为 **00**。  
> **上游决议**：[`docs/discussions/2026-09-17_interview_gaps_adoption_and_landing_v0.md`](../../../discussions/2026-09-17_interview_gaps_adoption_and_landing_v0.md) §1 A 档 · §5 波次 α · **§8 阶段 H**  
> **日期**：2026-09-17  
> **维护者授权摘要**：统筹下一 task 全链；**00 可代签全部过程文档**；默认 **不**亲自 30 改码。

---

## 复制区（整段粘贴为新窗首条用户消息）

`````text
你是 ops-desk-api 仓的 00 统筹（hat 00）。Open Folder = 本仓根。

════════════════════════════════════
维护者授权（本窗有效 · 须写入首条 invoke notes）
════════════════════════════════════
1) 授权你统筹「阶段 H · Host / Capability 契约硬化」的下一（或一组）task：从起草 → 审查 → 实现 → verify → CLOSE。
2) 授权 00 代签本主题全部过程文档与人工闸表字段，包括但不限于：
   - task 头注 / 人工闸表（HG-AUDIT-R1、HG-TASK-DRAFT、相关 HG-*）
   - docs/harness/reviews/* 审查结论签收
   - docs/harness/invokes/by-task/<slug>/* 过程 invoke 的闸状态与 CLOSE 过程签
   - task 迁 done/、ROADMAP/讨论稿回写中的过程签收栏
   代签时注明：2026-09-17 · 00 代签 · 维护者令开启。
3) 代签 ≠ 亲自改码。无「00 本窗亲自 30」例外句 → 禁止 00 改 app/、tests/ 实现；中间实现交子 Agent（10/20/30/40）。
4) 未说 commit/push → 不 push；commit 仅当维护者另令。

════════════════════════════════════
目标范围（阶段 H · 仅此 · 禁止扩到 T/W）
════════════════════════════════════
真值先读：
  docs/discussions/2026-09-17_interview_gaps_adoption_and_landing_v0.md
  （§1 A 档、§5 波次 α、§8 阶段 H；§8.1 的 T/W/P 本窗不做）

阶段 H 验收方向（写入 task，可裁成 1～N 个 task，优先一个可 CLOSE 的竖切）：
  A. 默认 capability 补最小 args_schema；Gateway invoke 对写/可配置强制 schema 校验
  B. tool 子任务：结构化 args（或 input→schema）路径设计进 task（可与 A 同 task 或拆）
  C. 按 agent_type / mode 的 allowlist 配置（取代全局 CANDIDATE=None 默认可视）
  D. tenant_scoped（或等价）注册声明 + lookup/retrieve 相关单测（单租户构造性成立可先测「无声明/无上下文则拒或强制注入」的契约）
  E. Langfuse/span metadata 补全（capability_id、args 摘要、policy、subtask_id）
  F. 口径：文档称「注册表」非「注册中心」；业务不变量不进 args_schema

非范围（本窗严禁扩）：
  - 阶段 T 多租户产品（Workspace 模型、ANN 前分租户语料）
  - 阶段 W 写能力 / HITL confirmation 生产路径
  - 服务化 Registry、完整 Ontology Package、多 Agent 委派平台
  - 改无关 active task；改 chat 已 410 主叙事除非 task 点名

════════════════════════════════════
开工动作（按序）
════════════════════════════════════
1) 确认分支：勿在 master/main 改码。无任务分支则：
   git checkout -b task/capability-contract-hardening
2) 扫描 docs/tasks/active/：无本主题 task → 派 10（或 00 仅起草 task 极简壳后立刻交 10 补全）产出：
   docs/tasks/active/task_capability_contract_hardening.md
   （slug 可微调，须含 graph_change_layer、review_hat、failure_paths、test_strategy、人工闸表）
3) 落首条 invoke：
   docs/harness/invokes/by-task/capability-contract-hardening/invoke_YYYYMMDD_00_*.md
   写入上列维护者授权全文摘要 + 闸表初值。
4) 派 20 审 task（若维护者授权代签：00 可在审查通过后签 HG-AUDIT-R1=approved）。
5) 30 开工前 GATE_VERIFY：
   npx spec-wave verify --target . --task docs/tasks/active/task_*.md
   （或仓内等价 dsh-coding-kit verify）
   首输出闸扫描表；HG-AUDIT-R1 pending → 拒派 30。
6) 派 30 → 收报告 → 40/verify → 50+CLOSE。
7) CLOSE：回写 discussions §5/§8 进度一句；git mv task → done/；ROADMAP/SPEC 若有缺口只开跟进句不扩 W。

════════════════════════════════════
每轮循环
════════════════════════════════════
GATE_VERIFY → 产出下一棒可复制 Prompt → Task/新窗派子 Agent → 收 ≤10 行回报 → 更新阶段表 → CLOSE 或返工

硬约束
  遵守 docs/harness/prompts/00-orchestrator.md 默认只委派
  遵守 AGENTS.md 分支纪律
  声称与 task 人工闸表冲突 → STOP，以 task 表为准（代签后表须已更新）

当前棒（首轮）：
  若尚无 task → 派 10 起草 task_capability_contract_hardening（或本窗只写极简壳后交 10）
  若已有 task 且闸未签 → 派 20 或 00 代签后 GATE_VERIFY
  若闸已 approved → 派 30

汇报格式：本窗未改实现码 · 已派/待派：{帽} · 分支 · task 路径 · 闸状态
`````

---

## 维护者备注（勿贴进复制区）

| 项 | 说明 |
|----|------|
| 签收范围 | 「过程文档」含闸表与审查/invoke；**不含**擅自改产品 brief 把 T/W 标成已交付 |
| 若要 00 亲自 30 | 另开一句写入复制区：「00 本窗亲自 30」 |
| 多 task | 00 可将 A–E 拆 bulk-split；派第一棒 30 前跑 wiki-delta lint（见 00-orchestrator） |
