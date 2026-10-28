# Invoke：40 独立验收 — lg-rag-replay-resume-ux-opt（2026-10-28）

| 字段 | 值 |
|---|---|
| hat_id | 40（独立验收 · 与 30 不同人 · 实现帽 d6756599 不在场） |
| task_slug | `lg-rag-replay-resume-ux-opt` |
| task_paths | `docs/tasks/active/task_lg_rag_replay_resume_ux_opt.md`（验收真值 v0.4） |
| related_review_or_none | `docs/harness/reviews/task_lg_rag_replay_resume_ux_opt_audit_R1_20261028.md` |
| git_branch | `task/lg-rag-replay-resume-ux-opt`（base `0a5d610` · 受验 HEAD `b11c401` · commits 679411f/a2684e3/93ca95e/b11c401） |
| created_utc_or_local | 2026-10-28 |
| notes | 逐项实证验收（非口头）；测试库 `opsdesk_test` · live 库 `opsdesk`（uvicorn :8011 · HEAD 码） |

---

## 总结论

**退回（FAIL）**——8 项验收面中 7 项 PASS，**验收面 1（F1）live 实证发现阻断性缺陷 B-1**：恢复段在写窗 `replay(follow=false)` 实测 **500**（应为 409+Retry-After:2），根因为新增谓词内 naive/aware datetime 减法，在迁移 canonical schema（timestamptz）下必崩；测试库 schema 漂移（naive timestamp）使 TC1–TC4 全绿成为假象。F2 follow 续流 live 全语义 PASS。修 B-1 后即可复验（范围小、钉案齐）。

---

## 逐项验收结论

| # | 验收面 | 结论 | 实证 |
|---|---|---|---|
| 1a | F1 谓词+409 语义化四态零 diff（测试面） | PASS | HEAD `opsdesk_test` 13/13 PASS（0.43s）· TC1 矩阵/TC2 409 可区分均绿 |
| 1b | F1 live（TC6 · 40 帽） | **FAIL → B-1** | 写窗 `follow=false` → 500 ×2 次复现（traceback 见下） |
| 1c | F2 follow live-tail 全语义 | PASS | 测试 13/13 + live 单连接 18.1s 收全恢复段（见下） |
| 1d | F3 契约测试 TC1–TC4 存在且通过 | PASS | `tests/test_lg_rag_replay_resume_follow.py` 478 行 13 测全绿 |
| 1e | F4 留档+图谱 | PASS | b11c401：图谱 lg_rag 行 dated 条 + 05 §10.3 dated 注 + invoke_30 + task v0.4 含经验捕获五条 |
| 2 | 红测先行真实性 | PASS | a2684e3 纯测试 commit（+477 行零 app/ 改动）；worktree 复跑 11 failed/2 passed：9 枚 AttributeError（`run_resume_in_progress`/`LgRagRunResumeInProgressError`/`_iter_replay_follow_sse` 不存在）+ 2 枚行为差（:370/:394 follow 被忽略），与 30 声称同签名 |
| 3 | 零新增红独立复核 | PASS | 三钉 HEAD 68p/**2f** vs base 37p+31p/**2f** 同两 node（`test_tc8_diff_whitelist` 结构性旧红 + `test_hitl_cross_instance_resume` 环境性；清库后 dualproc 污染消失，佐证遗留风险 2）；全量 HEAD 26f/1973p vs base（同 .env）26f/1960p，**26 枚 node id 集合完全一致**（diff 为空）· base 少 13 passed 恰为新测试文件 |
| 4 | 冻结面 diff 实证 | PASS | `git diff 0a5d610..HEAD` 仅触 `app/ops/lg_rag/event_store.py`+`router.py`（纯新增）+新测试+docs；hitl/sse_stream/sse_subscribe/run_worker/sse_replay/alembic 零触达；零新 event_type 字面量；零新表/迁移；帧形状 `_format_replay_sse_frame` 与旧 event_gen 逐字节同构（TC3 钉）；live decide 200 + 挂起/沉降 replay 帧与 base 语义零 diff |
| 5 | stale 阈定稿审查 | PASS（带备注） | 900s 理由成文（task v0.4：实测恢复段 68–289s ×3 余量）；TC1(d) created_at 回拨 7200s+形参覆盖真测崩溃场景——**备注**：B-1 未修前 stale 回落路径在 canonical schema 下不可达（崩在前一行减法），修复后 TC1(d) 语义仍有效 |
| 6 | 旧钉静默改动扫描 | PASS | tests/ 仅新增 1 文件零改旧钉；93ca95e 对测试唯一改动=poll_calls 期望 3→4（钉更准未削弱） |
| 7 | 脏文件边界 | PASS | `docs/arch-browser/dist/site-data.json` 未被任何 commit 带入（`git log --name-only` 核=0） |
| 8 | invoke/图谱/经验捕获在 b11c401 | PASS | 四件齐（见 1e） |

---

## B-1 钉案（退回唯一阻断项）

**现象**：HITL approve + resume 后、恢复段在写窗内，`POST /api/ops/lg-rag/replay` `follow=false` 实测 **500 Internal Server Error ×2**（19:52:34 前后两次；应 409 + Retry-After:2 + detail 「Resume is writing new events; retry after it settles.」）。比 base 更糟：base 同场景返 200 空帧（UX 差但非 5xx）。

**traceback（uvicorn :8011 · HEAD b11c401 原文）**：
```
File ".../app/ops/lg_rag/router.py", line 530, in replay_lg_rag
File ".../app/ops/lg_rag/event_store.py", line 356, in load_events_after
File ".../app/ops/lg_rag/event_store.py", line 248, in run_resume_in_progress
    age_seconds = (now_utc() - last_created_at).total_seconds()
                   ~~~~~~~~~~^~~~~~~~~~~~~~~~~
TypeError: can't subtract offset-naive and offset-aware datetimes
```

**根因链（实证）**：
1. `app/db/models.py:27` `now_utc() = datetime.utcnow()` → **offset-naive**。
2. 迁移 `alembic/versions/20260831_lg_rag_run_events.py:32`：`created_at timestamptz NOT NULL DEFAULT now()` → canonical schema 为 **timestamptz**，asyncpg 返回 **offset-aware**（实测 dev 库 `opsdesk` = `timestamp with time zone`）。
3. `opsdesk_test` 实测为 `timestamp without time zone`（conftest create_all 按模型 naive 建表 · 与迁移漂移）→ naive−naive 不崩 → **TC1–TC4 全绿是测试库 schema 漂移掩盖的假象**；任何迁移建库（含生产形态）F1 主路径必崩。
4. 触发条件=「∃ hitl.resumed seq > 最新收尾帧 seq」即达 :248 减法——恰为恢复段在写窗形态，F1 的核心目标场景；且同行使 stale 回落分支（TC1(d) 语义）在 canonical schema 下永不可达。
5. `event_store.py:305` 既有先例是 SQL 侧 cutoff 比较（无 python 减法）；**:248 是全仓唯一 python 侧 `now_utc()`−DB datetime 减法**（grep 实证），缺陷由本 task 引入。

**修复方向建议（40 不改码 · 供 30 参考）**：谓词内 tz 归一——DB 值 naive 则 `replace(tzinfo=timezone.utc)`、now 侧用 `datetime.now(timezone.utc)`；或承 :305 先例改 SQL 侧 age 比较。并补一条 aware 列下的回归钉（或修测试库 schema 对齐迁移，基建项可另立）。修后须重跑：TC1–TC4 + 三钉 + 全量对拍 + live 409 实证。

---

## F2 live 实证明细（PASS · 保留证据）

- 环境：uvicorn :8011 跑 HEAD · dev 库 `opsdesk` · 真实挂起单 `hitl_684d695a3d654f31ad14`（run `633dba00e7c14242aeb7c74ceabd9dde` 挂起 `done{waiting_approval}@9`）。
- `POST /hitl/requests/{id}/decide` {approved, resume_mode:manual} → 200；`POST /hitl/requests/{id}/resume` → 秒回 200 `replay.cursor=:9`（冻结面 live 零 diff ✓）。
- `follow=true` 单连接：200 · **18.1s** 收全恢复段 seq 10→19 **连续无洞**：`hitl.resumed@10 → node.progress@11-13 → subtask.progress@14 → node.progress@15-16 → answer{final:true}@17 → critic@18 → done{status:resumed, latency_ms:39360, events_persisted:9}@19`；收尾帧推出后流自然结束；**0 keepalive**（18s<30s 间隔，一致）；**0 伪造帧**；帧七键（run_id/seq/ts_ms/agent_role/event_type/payload/cursor）齐。
- 挂起态预检：`follow=true` 存量含收尾帧立即收尾、与 `follow=false` data 帧逐字节一致；`follow=true` 在写窗不返 409（200 ✓）。
- 沉降后 `follow=false` → 200 十九帧、末帧 `done@19`（零 diff ✓）。

## 过程附记（环境坑 · 供后续 40 复用）

- **.env 决定 23/26 枚环境红**：base 裸 worktree（无 .env）全量仅 3f；拷入 .env 后 26f 且与 HEAD 同 node 集。对拍必须同环境（capability/redline 类测试在有真 key+可通网时断言失败）。
- 判红前已 `TRUNCATE ops_hitl_requests`（opsdesk_test 清 6 行），dualproc 污染消除，与遗留风险 2 一致。
- ruff check app tests PASS · `./scripts/graph-compile.sh` EXIT=0。
- TC6 副作用披露（dev 库 `opsdesk`）：已 approve 单据 `hitl_684d695a3d654f31ad14`（run 已恢复至 `done@19`）；为 admin 铸 session 行（2h 自过期）；uvicorn :8011 验收后已停。

## 质量门

| 门 | 结果 |
|---|---|
| ruff check app tests | PASS |
| graph-compile.sh | EXIT=0 · 零再生噪音 |
| 新测 13/13（HEAD） | PASS |
| 三钉对拍 | PASS（同 2 红同签名） |
| 全量对拍（同 .env） | PASS（26 node 集逐枚一致） |
| TC6 live F1 | **FAIL（B-1）** |
| TC6 live F2 | PASS |

**40 结论：退回 30 修 B-1（单点 · 钉案齐），其余面全部达标，修后复验范围=TC1–TC4+三钉+全量对拍+live 409 实证。**
