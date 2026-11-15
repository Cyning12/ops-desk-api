# invoke · 30_implement · p1-t5a-goal-docs

- 实施：① 10_flow_goals.graph.yaml（7 节点：client/goals_list/goals_patch/lg_stream/goal_store/goal_inject/db · 描述含 422/404/409/401 语义 · 迁移矩阵 · uq 索引 · 闸语义）→ graph-compile.sh 编译（spec-wave@3.0.1 · 全量 OK · shared/graph.json 同步）；② RUNBOOK_goal_rollout_v1_zh.md（功能面速览表 · 三步放量 off→灰度→全开 · 回退=删 env 秒级+无数据迁移+REST 面不受闸控 · 07 §6 十条对照锚定测试文件 · 故障排查四症状）；③ 01_modules T2 签收行补 10_flow_goals 链接 + 本波签收行
- 偏差：无（纯文档波 · 零代码）
