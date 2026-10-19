---
hat: 10-task
task_slug: rag_golden_eval_live_run
date: 2026-10-19
---

# invoke · 10-task 起草 · rag_golden_eval_live_run（R-4 结案真跑：现集 73 条 golden 全量真跑 + 结案报告 + R-5 Demo 证据表回填）

## 落稿摘要

- 起草帽：10-task 子 Agent（00 委派 · 2026-10-19）。
- 移交口径（亲读实证）：上游 task_rag_golden_eval_r4_r5 已 CLOSE（PR #262 · CLOSE 档 close_rag_golden_eval_r4_r5_20261017.md）——评测资产全闭环（summarize_r4.py 394 行 + 12 测 + r4_final_TEMPLATE.md + demo_evidence_TEMPLATE.md + 契约核对零漂移），唯一未闭环 = **TC-R4-5 结案真跑**（HG-EVAL-LIVE-RUN pending 移交）；本 task 只做真跑回填单增量，资产零重写，禁重复立项。
- 10 亲跑实证锚点（2026-10-19）：
  - 现集 73 条四象限亲跑计数：zh2en=26 / zh2zh=20 / en2en=16 / negative=11（⚠️ ≠ 旧过程稿 71 条，FP-9 旧稿禁冒充结案钉死）。
  - 知识库活态：PG ops_knowledge_chunks=8648 == Qdrant ops_knowledge points_count=8648（dim=1024 Cosine green · 双容器 Up 2 days healthy · 承 PR #276 三对照 match）。
  - SILICONFLOW_API_KEY 在 .env 存在非空（grep 计数=1 · 值不落档）。
  - reports/r4*.yaml 18 份过程稿（pre-G72/G73 旧集 71 条 · 无结案效力）；run_eval.py / summarize_r4.py docstring 用法亲读（--limit/--resume/--out · ZH2EN_THRESHOLD=1/3 未舍入三态）。
  - 降级先例亲读（close_local_rag_knowledge_rebuild_20261018.md §三）：ApiEmbedder 无批切 → 分批 --limit 75 步递增 248s；NO_PROXY 含 [::1] → env -u 清洗。
- 落码与否建议：**零落码**——全链复用既有管线（run_eval.py 全量真跑 → summarize_r4.py 聚合 → 双模板回填），无新码无新测试；实证须改码即 STOP 另立 task 补 30 棒+图谱闸评估（FP-6）。故 required_invoke_hats=10,40 · review_hat=20 · graph_change_layer=none。
- 闸设计：四闸全 pending（HG-TASK-DRAFT / HG-AUDIT-R1 / HG-EVAL-LIVE-RUN / HG-GRAPH-MODULES）未代签；HG-EVAL-LIVE-RUN 为本 task 核心闸（本地库 + 真 LLM key + 配额消耗授权 · 维护者 2026-10-19 会话「全做」选定推进 · 00 签闸时统一代录）；HG-PROD-READONLY-ACCESS 关联照登不消解（本 task 零涉生产）。
- 纪律面：不假绿（FP-2 部分完成如实记）· 门槛未达如实 NOT_MET 不改默认（FP-4）· LLM key 失效阻塞登记（FP-5）· 小样本 Wilson CI 老实标（FP-7）· 契约漂移只上抛（FP-8）。
- 交付：docs/tasks/active/task_rag_golden_eval_live_run.md（TC-LR-1..6 · FP-1..10 · R0–R5 early_stop）· npx --yes spec-wave task lint → **LINT: PASS**（首轮 E5 缺自检结论节 → 补 draft 占位节 → 复跑 PASS）。

## 留 20 审要点

- 零落码裁定是否成立（F1–F4 是否全部可复用既有管线 · FP-6 STOP 边界是否够硬）。
- FP-9 旧过程稿禁冒充与 zh2en 分母口径（现集 73 · 按实际报告取数）是否钉死。
- 分批降级预案（--limit + --resume）与冒烟 /tmp 先例是否足以覆盖配额/超时面。
- TC-LR-3 机断旁证（12+13 测复跑）在零 diff 硬约束下的证明力是否充分。
