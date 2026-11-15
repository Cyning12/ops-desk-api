# R1 审查 · p1-t1-goal-store（2026-11-15）

## 结论

GO（纯新增模块 · 零接线 · 风险面收敛）。

## 核查项

1. **设计一致性**：范围与 07 §5 T1 行逐字对齐；O-1（人工复活 → patch 允许 paused→active）、O-3（1:1 由 T4 唯一索引执行，本单 catch IntegrityError 重读消化竞态）、R-2（不加 FK）均已反映。
2. **纪律分层**：resolve/get/list 读路径 best-effort 吞错+日志带 thread_id（装配链路纪律，承 run_store.py:5-6）；patch 显式抛 GoalNotFoundError/GoalStateTransitionError 不吞（REST 用户显式动作）。
3. **索引对齐**：ORM __table_args__ 用 DB 既有索引名（idx_ops_goals_tenant_status/idx_ops_goals_thread · idx_ops_lg_rag_runs_status_created/idx_ops_lg_rag_runs_thread），零新迁移，autogenerate 漂移消除。
4. **objective 卫生**：单行化（控制符→空格）+ 截 200（对齐 EPISODE_ITEM_MAX_CHARS · 07 §2.3④）；空串降级不建行。
5. **无 FK 顺序容错**：goal 无 user_id 列，无 seeded_maintainer 依赖，测试自持。

## 风险登记

- R-1：唯一索引未建前并发懒创建可产生双 active——T4 唯一索引收口，本单重读已消化大部分窗口（登记）。
- R-2：ORM 补 __table_args__ 若索引名打错 → autogenerate 差异显形；用 alembic check 心态人工核对迁移文件名。
