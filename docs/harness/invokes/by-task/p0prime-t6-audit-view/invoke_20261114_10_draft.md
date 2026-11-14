# Invoke 10 · 任务起草（p0prime-t6-audit-view · 2026-11-14）

- 来源：workspace 06-kickoff-readiness.md 任务卡 T6（:41）+ R4 裁定 P3（:16）。
- 勘察：三源表列面（models.py:433/:540/:710）→ 缺列域清单（receipts 无 run_id；llm_usage 无 tenant_id/user_id；hitl 无 user_id）→ 补值口径入设计裁定表。
- 列映射裁定：公共列 ts/tenant_id/user_id/run_id/domain/action/outcome + source_id；缺列补 NULL/''（从严）；outcome/action 归一词表见 task 单。
- 边界：不做端点/聚合页/物化（P3 钉死）；零源表变更。
