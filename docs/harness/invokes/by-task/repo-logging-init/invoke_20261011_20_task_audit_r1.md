---
hat: 20
task_slug: repo-logging-init
date: 2026-10-11
---

# invoke · 20-task-audit R1 · repo-logging-init（仓级 logging 初始化）

## 审查摘要

- 审查对象：docs/tasks/active/task_repo_logging_init.md（commit 73b79e6 · 10 落稿）· 审查文落 docs/audits/task-review/20261011_repo-logging-init_r1.md。
- 纪律执行：骨架先行 commit 32f5d18 → 逐节填定稿；只核 task 实际引用锚点 · 禁全仓通读；未改 task 实质 · 未代签三闸（全 pending 留维护者）。
- 锚点亲读/亲跑 12 组全核真：main.py 49 行零 logging（lifespan :13-26 仅 tracing/auto_resume）· config.py:11 load_dotenv 逐字 · app/ 55 处 getLogger(__name__) grep 复核 · basicConfig|dictConfig|logging.config 命中清单逐字（evals/scripts×4/alembic:3 · app/ 零命中）· 台账键五枚全 INFO 级在案 · SPEC §9 序2（:264）· CLOSE 九节 #1（:68）· 验收 :64 坑位注 + :139 格式串逐字 · compose :79-80 · modules.md :27 entry 行。
- 亲跑实证：uvicorn 0.51.0 LOGGING_CONFIG——`uvicorn`/`uvicorn.access` propagate=False + disable_existing_loggers=False → root 加 handler 不双行机理成立（D4 钉「须实证」姿态正确 · TC4 断言形态可断：grep -c 单行计数）。
- 裁定：**PASS-WITH-NITS**（零 BLOCKER · N-1~N-6 照登：scripts「CLI 自含」措辞微偏（serve_observe.py 实系启动器）· 契约4 caplog 论证缺口（root level 抬高副作用 · 305 处使用面 · TC5 兜底）· TC1 handler 计数须钉识别口径 · TC2 复跑锚点可收紧 · 契约3 四红基线未复跑（worktree 无 .env）· --reload 论证覆盖非实证覆盖）。
- D1/D2 倾向裁断留维护者/30：倾向理由（A 最小面幂等 · env 口承 auto_resume.py:76 先例）审查认定成立，未锁死候选。
