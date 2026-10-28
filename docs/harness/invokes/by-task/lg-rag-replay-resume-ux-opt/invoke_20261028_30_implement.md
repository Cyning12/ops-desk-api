# Invoke：30 实现 — lg-rag-replay-resume-ux-opt（2026-10-28）

| 字段 | 值 |
|---|---|
| hat_id | 30 |
| task_slug | `lg-rag-replay-resume-ux-opt` |
| task_paths | `docs/tasks/active/task_lg_rag_replay_resume_ux_opt.md`（v0.3 → 交付回填 v0.4） |
| related_review_or_none | `docs/harness/reviews/task_lg_rag_replay_resume_ux_opt_audit_R1_20261028.md`（PASS + NIT×3 已闭合） |
| git_branch | `task/lg-rag-replay-resume-ux-opt`（base master `0a5d610`） |
| created_utc_or_local | 2026-10-28 |
| notes | 委派子 Agent 执行（禁 push/PR · 完工回报 00）；F1 恢复段在写窗 409 语义化 + F2 replay follow 续流 + F3 红测先行 + F4 回写 |

---

## 人工闸扫描（GATE_VERIFY · 30 重填 · 读 task 表）

| human_gate_id | task表status | 用户/invoke声称 | 一致？ | blocks_30 | 30可开工？ |
|---|---|---|---|---|---|
| HG-TASK-DRAFT | approved | 00 代录（维护者授权 m00236） | Y | N | Y |
| HG-AUDIT-R1 | approved | 00 代录 + R1 文 PASS | Y | Y | Y |
| HG-GRAPH-MODULES | approved | 00 代录 · 不新增一级模块 | Y | N | Y |

reviews：`task_lg_rag_replay_resume_ux_opt_audit_R1_20261028.md` 存在且 PASS？ **是**
pre-30 invoke：10 + 20 已落盘？ **是**
机械：`npx spec-wave verify --target . --task docs/tasks/active/task_lg_rag_replay_resume_ux_opt.md` → **VERIFY: PASS**（exit 0 · 30 开工前实证）

结论：**可进入读码/改码** → 已交付。

## 禁区复核（全程守住）

freeze lg-rag-sse-v1 帧形状零触达 · 零新 event_type · 零新表/迁移；resume 200 JSON / decide / callback / OA / 首段 stream bus / `run_is_terminal` / `run_stream_closed` 旧谓词零 diff；不 push 不开 PR；`docs/arch-browser/dist/site-data.json` 无关脏文件全程未触未提交。

## 交付摘要

| 项 | 结果 |
|---|---|
| 分支 / commits | `task/lg-rag-replay-resume-ux-opt`：`679411f`（docs：task+审查+invoke 10/20）→ `a2684e3`（红测 RED 先行）→ `93ca95e`（F1/F2 实现转绿）→ docs 回写 commit（图谱/05/task v0.4/本 invoke） |
| RED→GREEN | RED：11 failed（AttributeError 同形 `test_lg_rag_sse_resume.py:214` 先例）；GREEN：`tests/test_lg_rag_replay_resume_follow.py` **13/13 PASS**（TC1 谓词矩阵含 stale 回拨 · TC2 409 可区分 detail · TC3 帧序/keepalive/逐字节钉 + HTTP 级 follow=true 不 409 · TC4 上限零伪造帧 + aclose 零残留） |
| F1 | `event_store.run_resume_in_progress`（∃ hitl.resumed seq > 最新 done/error seq · stale 阈 `LG_RAG_RESUME_STALE_SECONDS` 默认 900s=实测 68–289s×3 余量 · 超阈回落放行）+ `LgRagRunResumeInProgressError` + `load_events_after` 第二闸（仅 refuse_in_flight=True） |
| F2 | `ReplayRequest.follow=false` 默认零 diff；follow=true 推存量→轮询增量（`LG_RAG_REPLAY_FOLLOW_POLL_SECONDS` 默认 2.0 floor 1.0）→新收尾帧自然收尾；keepalive comment 不占 seq；上限 `LG_RAG_REPLAY_FOLLOW_MAX_SECONDS` 默认 900s 到点自然结束**零伪造帧**；恢复段在写窗 follow=false → 409+Retry-After:2 可区分 detail |
| 旧测三钉 | `test_lg_rag_write_replay_guard.py`/`test_hitl_auto_resume.py`/`test_multi_replica_dualproc.py` 首跑 67 passed 3 failed → **stash 无改动态复跑同 3 failed** ⇒ 零新增红（`test_tc8_diff_whitelist`=前波次 diff 白名单闸结构性旧红；dualproc 两枚环境性） |
| TC5 全量 | `pytest tests` **1973 passed / 26 failed**（19min）→ 同集合 **base `0a5d610` 码面复跑完全相同 26 红**（同 node id 同签名）⇒ 全量维度零新增红 |
| 质量门 | `ruff check app tests` PASS · `./scripts/graph-compile.sh` EXIT=0 零再生噪音 |
| 图谱/05 回写 | `docs/_tech_graph/l1/01_modules.md` lg_rag 行末追加本 task dated 条（体例承 hitl-resume-replay-contract）；hitl 行判 none（hitl 模块零改动）；`docs/spec/agent-infra/05_lg_rag_transport_and_session_plan_v0.md` §10.3 T4「api 提供」加 dated 注 |
| 经验捕获 | 已落 task「经验捕获」节（五条：补丁三层转义 · mock 钉 patch 点定接线层 · 判红 stash/base 对拍纪律 · 测试 DB 残留污染 · 生成器显式 kwargs 可测性） |

关键路径：
- `app/ops/lg_rag/event_store.py`（+run_resume_in_progress / LgRagRunResumeInProgressError / load_events_after 第二闸）
- `app/ops/lg_rag/router.py`（+ReplayRequest.follow / _iter_replay_follow_sse / 409 映射 / env 面三键）
- `tests/test_lg_rag_replay_resume_follow.py`（TC1–TC4 · 477 行）
- `docs/_tech_graph/l1/01_modules.md` lg_rag 行 · `docs/spec/agent-infra/05_lg_rag_transport_and_session_plan_v0.md` §10.3 · task v0.4

## 遗留风险（交 00/维护者知悉）

1. `test_multi_replica_dualproc.py::test_hitl_cross_instance_resume` 环境性旧红：净库后推进至 :521「resume 后 state 为空（图没真推进）」· 疑 LLM 外网依赖 · base 同签名同点 ⇒ 非本 task 引入。
2. `opsdesk_test.ops_hitl_requests` pending 残留（live 累积 · 已清 109 行）会污染 dualproc 分页断言；后续判红先清库复跑。
3. 恢复段时长优化与 web 侧适配按 D3 另立 task（本 task 非范围第八条）。
4. follow 模式生产参数（轮询 2.0s / 上限 900s）建议 40 live 对照后按实微调。

---

## 补记：B-1 修复（40 退回 · commit 0722f75 · 2026-10-28）

40 独立验收（`invoke_20261028_40_verify.md` · c55b436）退回唯一阻断 B-1：谓词内
`now_utc() - last_created_at`（原 event_store.py:248）在迁移 canonical schema
（timestamptz → asyncpg 返 aware）下抛 TypeError，live 实测 500×2；测试库
create_all naive schema 漂移使 TC1–TC4 全绿成假象。

**修复方案定稿（二选一取 python 侧 tz 归一）**：抽纯函数 `_utc_age_seconds`——
now 侧 `datetime.now(UTC)` aware；DB 值 naive 按 UTC 补 tzinfo（与 now_utc 语义
一致），aware 直用。**不承 :305 SQL 侧 cutoff 的理由**：①本路径需把精确
age_seconds 带回 FP-1 error 日志（运维诊断值），SQL 侧比较拿不到该值；②naive
cutoff 对 timestamptz 列的比较依赖会话 TimeZone coercion，服务端 TZ 非 UTC 时
静默误判——显式归一消除该类隐患。

**回归钉**：`test_utc_age_seconds_handles_naive_and_aware_datetimes`（红测先行：
RED=ImportError → GREEN）直传 naive/aware 双形态覆盖减法路径；测试库 schema
对齐迁移属基建另立 task（经验捕获 7）。

**修后实证**：新测 14/14 PASS · 三钉 68 passed/2 failed 同旧红集零新增 ·
ruff PASS · live（timestamptz dev 库 `opsdesk` · uvicorn :8012 验毕已停）四探针：
在写窗 follow=false → **409 + Retry-After:2 + detail「Resume is writing new
events; retry after it settles.」**；follow=true → 200 不 409；纯挂起 follow=false
→ 200 零 diff；stale 超阈（created_at 回拨 7200s）→ 200 回落放行（修复前该分支
在 canonical schema 下永不可达）。live 副作用已清（合成事件 19 行/铸 session 1 行
删除 · 零 pending hitl 行产生）。

## 签收栏

30 实现交付 · 委派子 Agent 落盘 · 2026-10-28 · 三闸 approved · VERIFY PASS · 禁 push/PR（交 00 收口）
