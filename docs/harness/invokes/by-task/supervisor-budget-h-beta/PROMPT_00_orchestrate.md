# PROMPT · 00 · 阶段 H 波次 β · supervisor 总预算

> **Open Folder**：`ops-desk-api/`  
> **日期**：2026-09-17  
> **上游**：web 冒烟 PASS · workspace 总 00 开棒

---

## 复制区（整段粘贴为新窗首条用户消息）

`````text
你是 ops-desk-api 仓的 00 统筹（hat 00）。Open Folder = 本仓根。

════════════════════════════════════
维护者授权（本窗有效 · 须写入首条 invoke）
════════════════════════════════════
1) 授权你统筹「阶段 H · 波次 β · supervisor 总预算」全链：10 → 20 → 30 → 40 → CLOSE。
2) 授权 00 代签本主题全部过程文档与人工闸，包括：
   - task 人工闸表（HG-TASK-DRAFT / HG-AUDIT-R1 / HG-GRAPH-MODULES 等）
   - docs/harness/reviews/* 审查结论签收
   - docs/harness/invokes/by-task/supervisor-budget-h-beta/*
   - task 迁 done/、讨论稿 §5/§8 回写中的过程签栏
   代签注明：2026-09-17 · 00 代签 · 维护者令开启。
3) 代签 ≠ 亲自改码。无「00 本窗亲自 30」→ 禁止 00 改 app/、tests/；实现交 30。
4) 未说 commit/push → 不 push；commit 仅维护者另令。

════════════════════════════════════
前置
════════════════════════════════════
- H α CLOSE 且已合入 master（PR #138）；web 冒烟 PASS。
- 分支须为：task/supervisor-budget-h-beta（已由总 00 创建则沿用；否则新建）。
- task 壳：docs/tasks/active/task_supervisor_budget_h_beta.md

════════════════════════════════════
目标（仅 β · 讨论稿 §5 项 6）
════════════════════════════════════
supervisor 总预算（总步数 + 可选墙钟）与耗尽后收束（建议 → aggregate）。
可顺手薄做口径文档（项 7–8），非硬门。

非范围：阶段 T/W/P；改 SSE freeze；改 chat/graph.py；服务化 Registry。

════════════════════════════════════
开工序
════════════════════════════════════
1) git branch --show-current 核对 task/supervisor-budget-h-beta
2) 派 10 补全 task（钉死默认数值、计数点、耗尽边、墙钟是否必做）
3) 派 20；通过后 00 代签 HG-*
4) GATE_VERIFY 绿 → 派 30 → 40 → CLOSE
5) CLOSE：回写 discussions §5/§8；git mv → done/；不扩 T

硬约束：遵守 AGENTS.md · 00-orchestrator 默认只委派。

当前棒：派 10 补全 task_supervisor_budget_h_beta（或确认壳已够细则后派 20）。
`````

---

## 维护者备注（勿粘贴）

- 与阶段 T 条件核对并行：β 不阻塞 T 契约测绿项；T 仍缺第二租户数据。
- workspace 总 00 已开壳；本 Prompt 交给 api 仓新窗。
