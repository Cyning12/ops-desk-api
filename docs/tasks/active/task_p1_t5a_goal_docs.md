---
title: P1-T5a Goal tech_graph REST 契约 + 放量 runbook
---

# Task：P1-T5a Goal tech_graph REST 契约 + 放量 runbook

> **状态**：`in_progress`（2026-11-15 开工）

## Harness 元信息

| 字段 | 值 |
|------|-----|
| **task_slug** | p1-t5a-goal-docs |
| 波次 | P1-T5a（P1 收官波 · api 仓部分） |
| 上游 issue | #399（维护者派单）· #23 母 issue · 设计真源 07-p1-goal-design.md |
| 关联 PR | 待建 |
| **wiki_delta** | docs/_tech_graph/l1/01_modules.md 签收行 + docs/guides/RUNBOOK_goal_rollout_v1_zh.md |

## 人工闸

- [x] H1 维护者授权：m00177「签收，开始」+ m02028「本窗口任务继续」+ m02610「继续」
- [x] H2 设计真源冻结：07-p1-goal-design.md §3/§5/§6（commit d19fdaa）

## 背景与目标

P1 Goal 主线 T1→T4 全闭环（#385/#390/#391/#396）。T5 收官波 api 仓两件：tech_graph REST 契约图谱（goals 两端点+懒创建接线目前仅散落签收行，无独立 flow 图谱）+ GOAL_INJECT_ENABLED 放量 runbook（灰度三步+回退+07 §6 十条验收对照）。

## 范围

1. docs/_tech_graph/l1/10_flow_goals.graph.yaml + 编译产出 10_flow_goals.md（承 10_flow_lg_rag 体例）+ shared/graph.json 同步。
2. docs/guides/RUNBOOK_goal_rollout_v1_zh.md（三步放量 · 回退命令 · 观测点 · 验收对照）。
3. 01_modules.md：T2 签收行补契约链接 + 本波签收行。

## 非范围

- web/iOS 端侧实现（另单）；任何 app//alembic//tests/ 代码改动；GOAL_INJECT_ENABLED 默认翻转（维持 off）。

## 失败路径

- graph-compile 失败 → 检查 yaml schema 对齐既有 flow；lint FAIL → 修体例；CI 红 → 修至绿，不带病合并。

## 验收标准

- [ ] l1/10_flow_goals.{graph.yaml,md} 落盘 · shared/graph.json 同步 · graph-compile 全绿
- [ ] RUNBOOK_goal_rollout_v1_zh.md 含三步放量+回退命令+观测点+07 §6 十条对照
- [ ] 01_modules T2 签收行补链接 + 本波签收行
- [ ] task lint PASS · CI lint-wiki-delta/tech-graph 绿

## 必读列表

- docs/_tech_graph/l1/10_flow_lg_rag.graph.yaml（体例参照）
- app/ops/goals/{router,store,inject}.py（契约真源）
- 07-p1-goal-design.md §6（验收十条）

## 思考轮控制

| 轮次 | 结论 |
|------|------|
| R0 | 图谱体例=flow graph.yaml+编译 md（graph-compile.sh · spec-wave@3.0.1 钉） |
| R1 | 审查：契约细节以 app/ops/goals/*.py 真源为准（422/404/409/401 · 迁移矩阵 · uq 索引） |
| R2 | runbook 复用 hitl_ops 先例结构（guides/ 目录 · frontmatter title/version/status） |
| R3 | 风险：零代码改动波，风险=文档与代码漂移 → 验收对照表锚定测试文件 |
| R4 | 回退=删文档 commit revert（纯文档波） |
| R5 | 完成判定=验收 4 条全勾+CI 绿 |

### 自检结论

（实施时回填）

## 实现备忘

（实施时回填）

## 测试策略

纯文档波：graph-compile.sh 全绿 + npx spec-wave@3.5.0 task lint + CI。

## 修订记录

| 日期 | 内容 |
|------|------|
| 2026-11-15 | 初稿（派单 #399） |
