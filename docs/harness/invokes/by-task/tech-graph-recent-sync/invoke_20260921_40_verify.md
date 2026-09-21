# invoke · 40 · tech-graph-recent-sync · 2026-09-21

- **hat**：40（验收）
- **结论**：**40 PASS**
- **命令与退出码**：
  - `source .venv/bin/activate && ./scripts/graph-compile.sh` → **0**（9 graphs · 143 nodes / 210 edges · check OK · mermaid normalize ok）
  - `git diff --stat -- app/ tests/ alembic/` → 零 diff
  - `npx spec-wave task lint --file docs/tasks/active/task_tech_graph_recent_sync.md` → **0** PASS
  - `npx spec-wave task lint-wiki-delta --target .` → **0** PASS（scanned=118 · issues=0）
- **锚点抽查**：12 条新陈述 → 代码 file:line 对照表见 task「自检结论」节（gateway `_prepare_call` L258 · circuit L197/L218 · budget L154 · fallback L157 · result_contract L77 · observe_node L1411/L1443 · step_contract.gate L195 · resume_hitl_run L285 · hitl/router L51–333 · admin/capability L45 · alembic 20260920_hitl_requests · redlines 16 条）
- **余项**：历史 line 锚点漂移不扩修（新增一律 symbol 锚点）；无 app/ 改动未跑业务 pytest。
