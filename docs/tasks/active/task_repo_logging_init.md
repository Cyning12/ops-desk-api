# Task：repo-logging-init（仓级 logging 初始化 · 裸 uvicorn 台账可观测性收口）

> **状态**：draft（10 落稿 · 20 审与三闸 pending）
> **类型**：仓级基建（可观测性 · SPEC §9 序2 · 维护者令 2026-10-11 立项）
> **依据**：`docs/spec/hitl-approval-consumption/SPEC-hitl-approval-consumption_v1.md` §9 序2 · `docs/tasks/close/close_hitl_auto_resume_claim_race_20261010.md` 第九节改进建议 #1 · `docs/acceptance/20261010_hitl-consumption-loop_local_acceptance.md` 操作便签坑位 1（维护者复跑亲撞）
> **分支**：`task/repo-logging-init`（base = master `cae745e`）

## Harness 元信息

| 字段 | 值 |
|------|-----|
| **task_slug** | `repo-logging-init` |
| **帽链** | 10-task → 20-task-audit → 三闸 → 30 → 40 → PR → CLOSE |
| **人工闸** | HG-TASK-DRAFT / HG-AUDIT-R1 / HG-GRAPH-MODULES = **pending**（00 代录）· HG-PILOT-OPSDESK-GLAYER n/a |
| **图谱预判** | `docs/_tech_graph/l1/01_modules.md` 若有 app/main 或 app 行涉台账表述须回写（30 判） |

## 1. 背景与实证（锚点逐一亲读 · base cae745e 复核成立）

- **app 包内零 logging 初始化**：`app/main.py` 全文 49 行无 logging 配置（:13-26 lifespan 仅挂 tracing/auto_resume）；全仓 `basicConfig|dictConfig|logging.config` 命中仅在 `evals/`、`scripts/`（CLI 自含 · 合理不动）、`alembic/env.py:3`（fileConfig · migrations 自治）——**app/ 服务进程零初始化**（精确口径，SPEC §9「全仓零」指 app 服务面）。
- **55 处 `getLogger(__name__)`**（app/ 下 grep 计数）：各模块只命名 logger，无 handler 无 level——root 无 handler 时 INFO 级全吞。台账键如 `hitl_auto_resume_triggered/claimed/deferred`（app/ops/hitl/auto_resume.py）、`delegation_approval_consumed`、`hitl_persist_guard_skip`（app/ops/lg_rag/multi/nodes.py）全部 logger.info。
- **事故面**：验收 20261010 首轮 run 因 INFO 未开取不到台账行（验收文档 :64 在案）；维护者手动复跑 grep 空（前台 tty 阻塞 → 重定向仍空 → 实锤裸 uvicorn 吞 app INFO）；TC3 live 必须自写启动器带 `logging.basicConfig(level=INFO)`（格式 `%(asctime)s %(name)s %(levelname)s %(message)s`——本 task 口径基准）。

## 2. 目标

任意启动形态（裸 `uvicorn app.main:app` / 自写启动器 / docker compose）下 app INFO 台账开箱可见，三形态口径一致；既有测试面与 logger 调用点零 diff。

## 3. 范围（D 块 · 候选开放不锁死 · 留 20 审）

### D1 · 初始化落点（必做 · 三选一）
- **A**：`app/main.py` 模块级（import 期）`logging.basicConfig(...)`——最简单，uvicorn import app 即生效；须注意 `--reload` 双 import 幂等（basicConfig 天然 no-op 当 root 已有 handler）。
- **B**：lifespan 早期（`log_tracing_startup()` 前）——启动语义最正，但 TestClient 不过模块级 import 路径之外的形态覆盖窄。
- **C**：`logging.config.dictConfig` 配置 dict 抽离（如 app/ops/logging_config.py）——可演进性最强，本 task 最小面下偏重。
- 倾向 A（最小面 · 幂等天然），留 20 审裁定。

### D2 · level 来源（必做 · 二选一）
- **A**：env 口 `OPS_LOG_LEVEL` 默认 INFO（非法值回退 INFO fail-closed · 承 auto_resume env 先例）。
- **B**：钉死 INFO 零 env。倾向 A（运维面价值 · 成本一行），留 20 审。

### D3 · format 口径（必做）
- 对齐验收启动器实证格式：`%(asctime)s %(name)s %(levelname)s %(message)s`——台账 grep 脚本（验收便签）零改。

### D4 · uvicorn logger 共存（必做 · 防回归）
- basicConfig 只配 root handler；`uvicorn.error`/`uvicorn.access` 自带 handler 与 propagate 口径须实证：access log 不吞 · 不双行（root handler + uvicorn handler 重复输出防除）。
- scripts/evals/alembic 既有自含配置零 diff（basicConfig 幂等天然兼容）。

## 4. 钉死契约（红线 · 反回归钉死）

1. **55 处 `getLogger(__name__)` 调用点零 diff**——只加初始化，不动任何 logger 使用面。
2. **零新依赖**（logging  Stdlib）。
3. **pytest 全量零新增红**——环境事实：仓根 .env 经 app/config.py:11 load_dotenv 使 `LG_RAG_HTTP_CHECKPOINTER=postgres` 等渗入 pytest 全进程；本地 4 红=master 基线环境性（capability_lookups×3+lg_rag_multi×1），对拍口径承先例。
4. **TestClient/caplog 测试面零 diff**：basicConfig 加 root handler 不影响 caplog（propagate 链不动）；import 期副作用幂等。
5. **手动/自动 HITL 台账键字面零改**——台账键是验收机读契约。

## 5. 验收标准（TC 组 · 可机验）

- **TC1 单测**：import `app.main` 后 root logger 有且仅有一个本 task handler · level=INFO（或 env 覆盖生效组 · 非法值回退组）。
- **TC2 裸 uvicorn live**：六 env 组起服（无自写启动器）→ 走真挂起→decide→resume 链 → stdout/stderr 日志 grep `hitl_persist_guard_skip|delegation_approval_consumed|token_issued` 三键齐——**本 task 核心验收（原坑位 1 场景反转实证）**。
- **TC3 compose 形态**：`docker compose run` 起服台账同键可见。
- **TC4 共存口径**：uvicorn access log 仍在 · 无重复行（同一事件单行）。
- **TC5 反回归**：全量 pytest 零新增红（master 基线对拍）。

## 6. 非范围

- 结构化日志（JSON）/ 日志落盘轮转 / 日志级别分模块细配——后续演进，本 task 不引。
- scripts/evals/alembic 既有 logging 配置面。
- 任何业务码改动。

## 修订记录

| 日期 | 说明 |
|------|------|
| 2026-10-11 | 10 落稿（**00 代笔** · 首棒长读卡滞 interrupt 留痕 · 授权 m01606 过程文档代签）：SPEC §9 序2 逐字承接 · app/ 零初始化精确口径（55 getLogger · main.py 49 行）· D1-D4 候选开放 · TC1-TC5 · 三闸 pending |
