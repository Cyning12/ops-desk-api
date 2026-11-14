# R1 审查 · p0prime-t6-audit-view（2026-11-14）

## 结论：PASS（可开工）

## 核对项
1. **范围对裁定**：P3 合格线=单张 view + 公共列 + tenant_id 过滤可用；task 单完成态与之逐字对齐；非范围含端点/聚合页/物化/源表变更——与 P3「不做端点、不做聚合页」一致。
2. **缺列域补值口径**：receipts 无 run_id→NULL（不伪造关联）；llm_usage 无 tenant/user→''（从严，承 data 层 tenant_id='' 先例）；hitl user←COALESCE(decision_by,'')（审批人是最接近操作者的列，pending 时 ''）。不虚构数据。
3. **回退**：CREATE OR REPLACE 幂等；down=DROP VIEW IF EXISTS；view 无读写方。
4. **freeze 合规**：不改 lg-rag-sse-v1 帧；新 DDL（view）含 tenant_id 列（F1-F6 口径）。
5. **风险**：view 随查询走源表无独立索引——单 view 合格线内可接受；三源行数增长后如慢，P3 复评物化（已入非范围，防 scope creep）。
