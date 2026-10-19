# invoke · CLOSE（2026-10-19）

- **PR**：#284 task/query-coref-rewrite → master · CI 全绿（pytest 1m41s pass · check · import-linter · lint-wiki-delta）· MERGEABLE
- **棒流**：SPEC signed（维护者会话）→ 10-task（lint PASS）→ 20-task-audit R1=pass（阻塞 0 · 锚点 26 处零漂移）→ HG-AUDIT-R1 approved（维护者授权 00 代签）→ 30 红测先行（38 例先红后绿 · TC1–TC12 全过）→ 40 approve（阻塞 0 · 889 行 diff 逐行 + 复跑全绿）→ PR+CI 绿 → CLOSE
- **归档**：task 移 docs/tasks/done/task_query_coref_rewrite.md
- **挂账移交**：40 O1–O4（历史窗 [-6:] 口径差建议经验沉淀 / TC2 形态级证明 / continue 金样链路 / 前置 setup 爆半径零）· 30 residual 4 条（真连 LLM 灰度前金样抽查 / rewrite 档默认 ops_llm_model / 金样仅中文 / .env 泄漏 16 项预存失败另立治理任务）
- **下游棒**：memory-injection-consumer（建议序 2/5 · 另 SPEC/task；Phase B 三结局分支待裁定）
