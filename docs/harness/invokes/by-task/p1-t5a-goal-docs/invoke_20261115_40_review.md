# invoke · 40_review · p1-t5a-goal-docs

- R1 审查：① 契约细节与 router.py/store.py 真源逐条比对（422 pydantic 前置 · 404 防探测 · 409 迁移矩阵 · 401 未登录 · uq WHERE status IN active,paused）；② runbook 观测点含 goal_inject_degraded span 与 turns 无横幅断言（T3/T4 测试锚）；③ 回退口径与 inject.py 运行时读闸一致（无缓存秒级）；④ 图谱 implementedBy 符号名与代码一致
- 结论：GO
