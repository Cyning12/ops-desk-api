# invoke · CLOSE（memory-injection-consumer · 2026-10-20）

## 归档
- task 移 docs/tasks/done/task_memory_injection_consumer.md
- PR #285（task/memory-injection-consumer → master）

## 五棒流闭环
- 10-spec → SPEC v0.1（R2 conditional_pass · 阻塞全闭合）
- 维护者签收 HG-SPEC-SIGNOFF=approved（2026-10-19）
- 10-task → 20-task-audit R1=conditional_pass（阻塞 0 · 锚点 30 处全命中）
- HG-AUDIT-R1=approved（维护者授权 00 代签 · m00147 授权链）
- 30 Phase A：spy 矩阵实证三模式 9 消费点全零到达（结局④前提命中）
- HG-PHASE-B-DECISION=approved（维护者亲裁 ④b · m00251）
- 30 Phase B ④b：注入双分支单点 funnel 收窄 + 休眠声明四落点（指向 DEF-005）
- 40=approve（阻塞 0 · 逐行 diff + 复跑 1732/0 全绿）

## CI 事故与修复（记录）
- PR #285 首轮 CI pytest 红：test_phase_b_diff_whitelist 硬编码基线 414270d，CI 浅克隆对象缺失 exit 128
- 30 急修 b881883：_resolve_base() 三级探测（钉锚 414270d → merge-base origin/master 退化 → 可审计 skip），本地钉锚路径与浅克隆两态实测
- 教训入库：含 git 基线锚点的测试必须 CI 浅克隆健壮

## 裁定链（本棒三件）
1. redline P1 反向对照翻休眠断言（00 方案甲 · 护栏收紧 · 恢复指引在 DEF-005 清单）
2. review40 审查文经 _UPSTREAM_SIGN_PATHS 入库（修正 #1 untracked 缺口 · 57f327d）
3. 枚举外连带两件（query_rewrite TC8 dormant 断言、.importlinter 三条移除）落 invoke_20261020_30_phaseB_4b_dormant.md

## 移交
- DEF-005（PRIORITY_DEFERRED）：memory-facts 真实构建（④a）对接文档，开工前遗留问题清单 9 条
