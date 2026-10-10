# repo-logging-init 审查（R1 · 20-task-audit）

> **审查对象**：`docs/tasks/active/task_repo_logging_init.md`（commit 73b79e6 · 仓级 logging 初始化 · SPEC §9 序2 · 10 落稿）
> **审查帽**：20-task-audit（R1 书面审查 · 未改 task 实质内容 · 未代签任何 human_gate · 未执行 30 · 未切分支 · 未 commit 码面）
> **日期**：2026-10-11 · **审查时仓态**：worktree `t-repo-logging-init` · 分支 `task/repo-logging-init`（base master `cae745e` · task 文档 commit 73b79e6 在 HEAD~1 链）
> **委托令**：20-task-audit 审查棒——锚点逐一亲读核真 · D1-D4 开放性与倾向理由 · 钉死契约 5 条与 TC1-TC5 可机验性（TC4 断言形态 · TC2 复跑性）· 图谱预判 · 非范围查漏（--reload 形态）

## 结论

**裁定：PASS-WITH-NITS**——内容可执行 · 零内容阻塞 · 锚点 12 组全亲读核真（行号/计数/格式串逐字在案）· D1-D4 候选开放倾向理由成立 · 钉死契约 5 条与 TC1-TC5 均可机验 · 非阻塞观察项 N-1~N-6 列明于 §六 · 三流程闸全 pending 待维护者签（本帽未代签）。

| 维度 | 结论 |
|------|------|
| task **内容**可执行 | ✅ **PASS-WITH-NITS**——背景实证链（SPEC §9 序2 → CLOSE 九节 #1 → 验收坑位 1）三源钉案全在案；目标三形态口径一致可验收；D 块留 20 审裁定姿态正确 |
| **流程闸** HG-TASK-DRAFT / HG-AUDIT-R1 / HG-GRAPH-MODULES | 全 `pending`（00 代录照实 · 本审查文落盘即 HG-AUDIT-R1 前置交付 · 维护者签后方 approved）· HG-PILOT-OPSDESK-GLAYER n/a 预判合理（纯 app/ 内基建 · 无图谱物理分层面） |
| draft 洁净度 | ✓ task 分支仅 73b79e6 一个 task 文档 commit · 工作树无提前实施（本帽仅落审查文与 invoke） |

---

## 一、锚点逐一亲读核真（全亲读 · 如实）

| 锚点（task 声称） | 本帽亲读实证 |
|---|---|
| `app/main.py` 全文 49 行无 logging · lifespan :13-26 仅挂 tracing/auto_resume | ✅ 逐行亲读：全文恰 49 行 · 零 logging import/配置 · lifespan :13-26 仅 `log_tracing_startup()`(:16) 与 auto_resume 补偿扫描挂点(:19-26) |
| `app/config.py:11` load_dotenv 渗 .env | ✅ :11 逐字 `load_dotenv(Path(__file__).resolve().parent.parent / ".env")` |
| 55 处 `getLogger(__name__)`（app/ grep 计数） | ✅ 本帽 grep 复核 ==55（另 1 处非 __name__ 形 · 不计入口径无碍） |
| basicConfig\|dictConfig\|logging.config 命中仅在 evals/ · scripts/ · alembic/env.py:3 | ✅ 逐字复核：evals/memory/run_eval.py:1286 · scripts/{memory_embedding_backfill:445, rag_ingest:56, episode_pattern_mine:262, serve_observe:11} · alembic/env.py:3 fileConfig · **app/ 零命中**——「app 服务进程零初始化」精确口径成立 |
| 台账键 hitl_auto_resume_triggered/claimed/deferred（auto_resume.py）· delegation_approval_consumed · hitl_persist_guard_skip（nodes.py）· 全部 logger.info | ✅ auto_resume.py :147 :207 :222（`_audit` :116-127 内 logger.info :127）· nodes.py :312 logger.info · :1679 logger.info——全 INFO 级在案 |
| SPEC §9 序2「仓级 logging 初始化缺失」 | ✅ SPEC-hitl-approval-consumption_v1.md :264 题字逐字 |
| CLOSE 第九节改进建议 #1 | ✅ close_hitl_auto_resume_claim_race_20261010.md :68 逐字（basicConfig 收进 app/main.py 或 lifespan 早期 · 三形态口径一致——task §2 目标逐字承接） |
| 验收文档 :64 坑位 1 注 | ✅ :64 逐字「因 app INFO 日志未开未取到台账行，重启加 logging.basicConfig(INFO)」 |
| TC3 验收启动器格式 `%(asctime)s %(name)s %(levelname)s %(message)s` | ✅ 验收文档 :134-139 坑位 1 启动器段 :139 格式串逐字一致——D3「对齐验收启动器实证格式」锚真 |
| compose api 形态（TC3） | ✅ docker-compose.yml :79-80 `command: sh -c "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"` 在案 |
| uvicorn logger 共存机理（D4） | ✅ 本帽实证 uvicorn 0.51.0（requirements pin >=0.30,<1）LOGGING_CONFIG：`uvicorn` propagate=False · `uvicorn.access` handlers=[access] propagate=False · `uvicorn.error` 无 handlers 承 `uvicorn` · disable_existing_loggers=False——root 加 handler 后 uvicorn 两 logger 记录止于 `uvicorn`（propagate=False 截断上行）· **不双行**机理成立；task 钉「须实证」而非预判锁死，姿态正确 |
| 图谱 modules.md entry 行 | ✅ docs/_tech_graph/l1/01_modules.md :27 `entry` 行覆 `app/main.py`+config.py · 描述「FastAPI 实例、CORS、环境变量」现无台账表述——图谱预判条件句（若有涉台账表述须回写 · 30 判）成立 |

## 二、D1-D4 候选开放性与倾向理由

- **D1（落点三选一）**：A/B/C 候选开放未锁死 ✓。倾向 A 理由「最小面 · 幂等天然」成立——basicConfig root 已有 handler 时 no-op（stdlib 语义 · 仓内 serve_observe.py 先例佐证同机制）；「--reload 双 import 幂等」注记准确（且 uvicorn --reload 实为 supervisor 重启子进程 · 进程内双 import 风险更低）。B「lifespan 启动语义最正」评价公允 · C「可演进性最强 · 最小面下偏重」取舍合理。
- **D2（level 来源二选一）**：倾向 A（env `OPS_LOG_LEVEL` 默认 INFO · 非法回退 fail-closed）理由成立——承 auto_resume env 先例实证在案（auto_resume.py:76 非法值 logger.error + 回退 manual）。
- **D3（format 口径）**：格式串锚验收 :139 逐字核真 ✓；「台账 grep 脚本零改」成立（grep 按台账键 · format 无关）。
- **D4（uvicorn 共存防回归）**：「access log 不吞 · 不双行须实证」钉法正确——本帽 uvicorn 0.51.0 propagate=False 实证支撑不双行预判（见 §一末行），task 未越断锁死。

## 三、钉死契约可机验性（5 条逐条）

| # | 契约 | 可机验性 |
|---|---|---|
| 1 | 55 处 getLogger 调用点零 diff | ✅ git diff app/ + grep 计数对拍 |
| 2 | 零新依赖 | ✅ requirements.txt diff 空 |
| 3 | pytest 全量零新增红（master 4 红基线环境性对拍） | ✅ 可机验（对拍口径承先例）· 机制锚 config.py:11 真 · 验收 :21 佐证主仓 .env 含 LG_RAG_HTTP_CHECKPOINTER=postgres；**本帽未复跑 pytest**（时限 + 本 worktree 无 .env · load_dotenv 静默 no-op · 复跑须主仓环境）——记 N-5 |
| 4 | TestClient/caplog 测试面零 diff | ✅ 可机验（TC5 兜底）· 论证有缺口：仅及「propagate 链不动」，未论 basicConfig(level=INFO) 抬 root level 致 app INFO 首次进入 caplog 捕获面的副作用（tests/ caplog 使用 305 处）——零 diff 结论须靠 TC5 对拍而非论证自保 · 记 N-2 |
| 5 | 台账键字面零改 | ✅ grep 台账字面钉 |

## 四、TC1-TC5 可机验性

- **TC1**：可机验 ✓ · 断言口径需收紧——pytest 进程 root 自带捕获 handler，「有且仅有一个本 task handler」裸计 `root.handlers` 会误判；建议裸 python 子进程断言或按 handler 归属（formatter/stream）过滤 · 记 N-3。
- **TC2**（核心验收）：可复跑 ✓——六 env 组（验收 :20 逐字在案）· 挂起→decide→resume 链（验收阶段4 步骤在案）· 三键 grep 机断；惟 task 未钉行号锚，复跑须自翻验收文档 · 记 N-4。
- **TC3**：compose api 命令在案（docker-compose.yml:79-80）✓ 可机验。
- **TC4**：「无重复行（同一事件单行）」断言形态**可断**——单请求 access 行 `grep -c`==1 · 同事件台账行计数==1；配合本帽 uvicorn propagate=False 实证，双行防除有机理支撑 ✓。
- **TC5**：master 基线对拍口径明 ✓ 可机验。

## 五、图谱预判与非范围

- **图谱预判**：条件句正确——modules.md :27 entry 行已覆 app/main.py，现无台账表述；30 若加初始化须判是否回写 entry 行描述 · 预判照实（30 判）✓。
- **非范围**：结构化 JSON/落盘轮转/分级细配 + scripts/evals/alembic 自含面 + 业务码——三面挡死 ✓。**--reload 形态**未入验收清单：D1-A 以幂等论证覆盖（reload=supervisor 子进程重启 · 风险更低），属论证覆盖而非实证覆盖 · 可接受 · 记 N-6（建议 30 invoke 留一行说明）。

## 六、NIT 清单（非阻塞 · 照登）

- **N-1**：§1 称 scripts/ 命中为「CLI 自含」——serve_observe.py 实系本地服务启动器（非 CLI · 其 docstring 自述 root WARNING 吞台账问题 + `log_config=None` 自含先例）；实质结论「既有自含配置零 diff · 合理不动」不受影响。
- **N-2**：钉死契约 4 论证缺口（root level 抬高副作用未论 · caplog 305 处使用面）——TC5 对拍兜底，建议 30 补一句论证或以 TC5 结果回写。
- **N-3**：TC1 handler 计数断言须钉识别口径（裸 python 子进程 / 按归属过滤），否则 pytest 进程内误判。
- **N-4**：TC2 复跑锚点可收紧（验收 :20 六 env · :64 坑位注 · 阶段4 链）。
- **N-5**：契约 3 的 4 红基线本帽未复跑（worktree 无 .env）；30/40 对拍须注明执行环境（主仓 .env 在案方复现环境性红）。
- **N-6**：--reload 形态为论证覆盖（D1-A 幂等注记）而非实证覆盖；建议 30 invoke 留一行裁定依据。

---

*审查文骨架先行 commit（32f5d18）后逐节填定稿 · 全部锚点本帽亲读/亲跑实证 · 未改 task 一字。*
