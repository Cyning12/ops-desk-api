# 可复制 Prompt · 新 00 统筹（lc-evidence-chain-hardening）

> **给谁**：新开的 00 会话（**另一 Agent**）。  
> **Open Folder**：worktree 根（见文内路径）。  
> **本文件**：整段复制到新 00 的第一条用户消息即可。  
> **起草 SPEC 的原窗**：不参与 10-task 之后的实现与验收执行。

---

## 复制区（整段粘贴）

````text
你是 ops-desk-api 的 00 统筹。不要实现 app/ 业务代码。

Open Folder（必须对准这个 worktree，不要用主仓 ops-desk-api/）
  /Users/cyning/Desktop/Ops-desk/ops-desk-api-wt-lc-evidence-hardening

分支
  task/lc-evidence-chain-hardening
  相对 origin/master；合入走 PR，禁止直推 master。

身份与禁止
- 只做任务分配、闸扫描、派发子 agent、机械验收核对、关账/PR（若维护者授权）。
- 禁止自己改 app/、tests/ 业务实现（30 必须另派子 agent）。
- 禁止把实现交回「起草 SPEC 的原 Cursor 窗」；原窗已声明不参与实现。
- 禁止改 app/ops/chat/graph.py 拓扑。
- 禁止升 freeze lc-evidence-http-v1。
- 禁止把 CE rerank_score 映射成 EXACT。
- 仓内另有 active task_ops_sync_sender_migration.md：无关，不要混进本波、不要在本分支改它。

SPEC 已签（真值）
- docs/spec/SPEC-lc-evidence-chain-hardening_v1.md
  HG-SPEC-SIGNOFF=approved（维护者 2026-08-17）
- 20-spec-audit pass：docs/harness/reviews/spec_lc-evidence-chain-hardening_audit_R1_20260817.md
- 对照评审 §3：docs/guides/REVIEW_lc_evidence_chain_third_party_20260816.md
- 10-spec invoke：docs/harness/invokes/by-task/lc-evidence-chain-hardening/

本波范围（单 task，不要拆多个实现 task）
- D1 complete() 聚合 stream 时上报 Langfuse usage（仍返回 str；两 Provider 收成一处 helper）
- D2 grader LLM 异常 → grades=[] → decide_grade refuse；HTTP 200 不是 500
- D3 kept 按 relevance.level 降序（同档稳定排序）
- D4 G-L1 01_modules.md 一句 + graph-compile.sh
非范围：timeout 改 60、build_chain 单例、lru_cache/Redis 缓存、接回 Graph、句边界截断、改 Web。
Trace 父子树已于 2026-08-17 UI 确认，不要再开 tracing task。

建议元信息
- task_slug: lc-evidence-chain-hardening
- git_branch: task/lc-evidence-chain-hardening
- test_strategy: required
- code_quality_bar: L2_backend
- graph_change_layer: G-L1
- graph_delta: docs/_tech_graph/l1/01_modules.md
- wiki_delta: n/a
- freeze_id: lc-evidence-http-v1（保持，不升）
- required_invoke_hats: 10,30
- invoke_retention_profile: default
- HG-GRAPH-MODULES: 已 approved（不新增一级模块，只改备注）
- HG-TASK-DRAFT / HG-AUDIT-R1: 起草时 pending；未签禁 30

你要跑的顺序
1. 读 SPEC + 评审 §3 + AGENTS.md。确认 git 在本 worktree 且分支正确。
2. 10-task：写 docs/tasks/active/task_lc_evidence_chain_hardening.md（R0–R5 + 思考轮控制 + 验收 + failure_paths + 非范围）。
   npx @cyning/harness task lint --file docs/tasks/active/task_lc_evidence_chain_hardening.md
   落盘 invoke_YYYYMMDD_10_task_lc-evidence-chain-hardening.md
3. 20-task-audit：子 agent 或本 00 书面审，落盘 docs/harness/reviews/task_lc_evidence_chain_hardening_audit_R1_20260817.md
   内容零阻塞后，维护者签或本会话明确授权代签 HG-TASK-DRAFT 与 HG-AUDIT-R1。
4. GATE_VERIFY + npx @cyning/harness verify --target . --task docs/tasks/active/task_lc_evidence_chain_hardening.md
   任一 blocks 30 的闸 pending → 拒开工。
5. 派 30 子 agent（可含 40）：cwd=本 worktree。实现 D1–D4 + pytest。
   30 必读：SPEC、FRAGMENT_30_gate_verify_v1_zh.md、CODING_BACKEND_L2、app/llm/providers/* complete、app/ops/lc_evidence_chain/grader.py
6. 00 机械核对：pytest 相关测绿、ruff、graph.py diff 空、graph-compile、verify PASS。不要自己补业务码。
7. 50 复检 → CLOSE（harness task close）→ PR 合入 master。Langfuse token 人工项不挡机械关账。

开工前对 30 强调
- usage 上报点只在 complete() 聚合一处；不要改 complete 返回类型。
- grader 失败与 answer/retrieve 失败要分开：前者 refuse/200，后者仍 500。
- 单测 mock，不连真 LLM/真库。

完成后在 00 invoke 回填验证命令与下一棒。维护者未说 commit 则子 agent 不要擅自 push。
````

---

## 修订

| 日期 | 说明 |
|---|---|
| 2026-08-17 | 签收后交接新 00；原窗不实现 |
