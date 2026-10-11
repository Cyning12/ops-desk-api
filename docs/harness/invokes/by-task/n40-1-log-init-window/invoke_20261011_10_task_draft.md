---
hat: 10
task_slug: n40-1-log-init-window
date: 2026-10-11
---

# invoke · 10-task 起草 · n40-1-log-init-window（logging 初始化窗口收口）

## 落稿摘要

- 上游交接：`docs/harness/invokes/by-task/_prompts/PROMPT_00_spec-campaign-handoff_20261011.md` §2.2 第 2 项（序2 N-40-1 · nit 级）；真值档 `docs/tasks/close/close_repo_logging_init_20261011.md` §四 N-40-1 原文 + §七 后续建议 1（修法候选留本 task 裁定）+ 40 invoke :77/:91 NIT 登记。
- 锚点亲读复核（worktree `t-n40-1-log-init-window` · base master `286d825` 成立）：
  - `app/main.py` 全文 77 行——import 链 `:9-12`（app.config / app.ops.hitl / app.ops.router / app.ops.tracing）先于 `:38` 模块级 `_init_logging()`（定义 `:18-35` · 格式常量 `:14`）。
  - 窗口发射源传递链钉实：`app.ops.router` → `app/ops/lg_rag/multi/nodes.py:36-39` / `app/ops/admin/capability.py:28` 等 `from app.ops.capability import ...` → `app/ops/capability/__init__.py:112` 模块级 `configure_persistence_from_env()` → `persistence.py:65-68` WARNING（裸格式实证首行）· `persistence.py:48` INFO（db 模式被吞）。
- 交付：`docs/tasks/active/task_n40_1_log_init_window.md`——候选 A（main.py 行序上移 · 最小面）/ B（抽 app/ops/logging_config.py · CLOSE 建议形态）开放不锁死，C（发射点挪窝）否决入非范围；钉死契约 7（OPS_LOG_LEVEL 语义/格式/uvicorn 共存/幂等/caplog 面/最小面/零新增）；TC1–TC4（TC1 窗口格式反转红测先行为核心验收）；思考轮 R0–R5 early_stop；三闸 pending 不代签。
- verify：`npx spec-wave verify --target . --task docs/tasks/active/task_n40_1_log_init_window.md > /tmp/verify_n40_1_log_init_window.log 2>&1; echo $?` → **EXIT=2**，仅因新 draft 三闸 pending（HG-TASK-DRAFT / HG-AUDIT-R1 / HG-GRAPH-MODULES 均 ❌ 拒 30）——draft 正确语义，零 lint 解析问题；verify 后 `git status` 零再生噪音。

## 留 20 审要点

- A/B 裁定倾向是否成立（A 最小面行序 vs B 可复用新模块 · 方向 B 触发图谱 G-L2 indexes 判定 + HG-GRAPH-MODULES 代录义务）。
- 窗口发射点全集（capability/__init__.py:112 已钉实为确认发射源；其余 import 链分支第二发射点未全量排查 · 留 30 实证）。
- TC1/TC2 子进程探针纪律（PYTHONPATH=$PWD + 显式 env · 承 CLOSE 偏差 4 sys.path 坑位教训）。
