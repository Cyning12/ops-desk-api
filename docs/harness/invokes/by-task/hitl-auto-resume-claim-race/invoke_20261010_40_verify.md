---
hat: 40
task_slug: hitl-auto-resume-claim-race
date: 2026-10-11
---

# Invoke：40 核验 hitl-auto-resume-claim-race（独立复跑 · TC3 live 实证）

> **帽**：Harness 40-verify（核验） · **task**：`docs/tasks/active/task_hitl_auto_resume_claim_race.md`
> **分支**：`task/hitl-auto-resume-claim-race`（链 7022e20 起草 → b7639ce 20 审 → 2f91f67 三闸代录 → 79b6485 红测 → 51e17ca 实现 → ac7f635 30 invoke）
> **纪律**：独立复跑不采信自报 · 只 add 自产文件 · 不 push 不开 PR · 维护者 :8000 live 与工作树 jar 勿碰 · .env 不触

## 核验逐项结论

| # | 核验项 | 结果 | 证据 |
|---|---|---|---|
| 1 | diff 面最小面核对 | ✅ PASS | `git diff master --stat` 仅 8 文件：app/ops/hitl/auto_resume.py +52 · tests/test_hitl_auto_resume.py +158 · docs/_tech_graph/l1/01_modules.md:39 备注回写 · audit/invoke×3/task 文档。nodes.py/store.py/router.py/resume.py/消费门/guard diff 全空；tests/test_hitl_resume.py **diff 0 行**（:230-259 stranded→409 断言存续 · 钉死契约 2） |
| 2 | 红测时序证据 | ✅ PASS | `git log` 实证 79b6485（test · 23:54:18）先于 51e17ca（feat · 23:54:28）先于 ac7f635（docs），父链 2f91f67→79b6485→51e17ca 严格有序。detached worktree `/tmp/hitl-race-verify-79b6485` 单独检出 79b6485 复跑：`pytest -k 'tc1_claim_race_window or tc2_auto_decide_chain'` → **2 failed / 39 deselected**，失败签名与 live D1 同形（ERROR HITL 自动恢复执行失败 + ResumeError stranded_checkpoint 窗口内：tasks 有 interrupts 空 + compensated 重试轮）。复跑毕 worktree remove --force 清理，主工作树零污染 |
| 3 | TC1/TC2 抽跑 + 断言强度亲读 | ✅ PASS | HEAD 复跑 2 passed。亲读 tests/test_hitl_auto_resume.py:772-927：TC1 窗口内 `assert not attempted`（零执行）+ probes==1 + flip 后直达×1 + claimed×2/deferred×1 台账链断言 + `_assert_zero_stranded_logs`；TC2 真 HTTP decide(auto)+InMemorySaver 真挂起，窗口内 hitl_unlocked_ids 空（图仍挂起零执行）→ flip → scan_approved_not_resumed_once()==1 → hitl_unlocked_ids==[_T1] + triggered/deferred/compensated/claimed 四键齐 + 零 stranded。**deferred 非假绿**（窗口内零执行有独立断言） |
| 4 | TC4 反回归亲跑 | ✅ PASS | B1 七文件 **174 passed**（与 30 自报一致）；全量 pytest **4 failed / 1764 passed / 1 skipped** = 基线钉案（test_capability_lookups×3 + test_lg_rag_multi×1，签名 permission_denied: delegation no_token = .env LG_RAG_DELEGATION_TOKEN_MODE=enforce 全进程渗入的环境性钉案，与 diff 面零交集）**零新增红**。ruff 触及路径 All checks passed（EXIT=0）；graph-compile EXIT=0（graph.json generated_at 再生噪音已 checkout 还原）；task lint 回填后复跑 PASS |
| 5 | TC3 live 实证 | ✅ PASS | 详见下节「TC3 live 实录」。**断言口径达标：零 stranded_checkpoint ERROR（grep count=0）· 零「HITL 自动恢复执行失败」（count=0）· 恢复完成×1 · 恰好一次执行（approval_consumed×1 / token_issued×1 / token_verified×1）· deferred×5 为机制本体实证** |
| 6 | 留转清单 2-5 逐条回应 | ✅ | 见下节「留转清单回应」 |
| 7 | N-1/N-2/N-3 照登核验 | ✅ PASS | N-1：tests/test_hitl_resume.py 断言窗实延至 :260 与 audit 记载一致（照登）。N-2：docs/_tech_graph/l1/01_modules.md:39 hitl 行备注实证含「hitl-auto-resume-claim-race（方向 A）就绪校验 + 台账 + `hitl_auto_resume_deferred`」。N-3：时序证据在案（核验 2 的 git log + worktree 复跑即独立实证） |

## TC3 live 实录（主角）

### 环境

- **env**：六 env 组（LG_RAG_DELEGATION_TOKEN_MODE=enforce / OPS_CAPABILITY_EXTRA_MANIFESTS=testing.v1.yaml / OPS_CAPABILITY_ALLOW_WRITE_TAGS=testing / OPS_STRATEGY_EXTRA_CANDIDATE_CAPABILITY_IDS=testing.write.echo / OPS_HITL_PERSISTENCE=db / OPS_CAPABILITY_ALLOW_WRITE=1）+ `OPS_HITL_AUTO_RESUME=auto` + `OPS_HITL_AUTO_RESUME_SCAN_INTERVAL_SECONDS=5`；代理 env 全 unset。码面真值：OPS_HITL_AUTO_RESUME 合法值=manual/auto（auto_resume.py:39），委派令字面 immediate 系 resume_mode 载荷键值非 env 值——故用 auto。
- **服务**：uvicorn :8060（辟维护者 :8000 手动 live）· 启动器 /tmp/tc3_serve.py（sys.path 钉主仓 + CODE_UNDER_TEST 自证 app/main.py 主仓路径 + logging.basicConfig INFO 台账可见）· 启动日志实证「HITL 自动恢复补偿扫描已启动 interval=5s」。
- **隔离库**：opsdesk_tc3（同 PG 容器 · alembic upgrade head 全迁移）。隔离理由：共享库 opsdesk 有维护者在窗 approved 单 hitl_6178c98f33794b25a6d0（decided_age<TTL），维护者随时 decide 即可被我 5s 扫描认领——不可在共享库开 auto 扫描。
- **登录**：admin（scripts/create_initial_user.py 幂等新建 token）· cookie=/tmp/tc3_jar（非仓内 jar）· runtime={mode:db, store:DbHitlStore, persists:true}。

### 过程时间线（2026-10-11 +0800）

| 时刻 | 事件 |
|---|---|
| 00:12:12 | POST /api/ops/lg-rag/stream（mode=supervisor · query=「请调用工具 testing.write.echo 回显 note=tc3-live-40-verify」· curl -N 保持连接） |
| 00:12–00:16 | **首跑卡点**：全新库首跑 AsyncPostgresSaver.setup() 的 CREATE INDEX CONCURRENTLY 被本服务自身 login 期 idle-in-transaction 会话阻塞 3m30s → pg_terminate_backend（隔离库自身连接 · 零维护者影响）→ setup 通。教训：新库首跑须无长事务阻塞 |
| 00:19:45.350 | pending 单落库：hitl_fcf734403e7544a18f63（run 9c25c5c72399436fb7e74c5c15096dac · blocked_by=delegation_issue_hitl_required） |
| 00:19:47 | SSE 流出 hitl.waiting + done(status=waiting_approval) 帧后流终（checkpoint 随挂起提交） |
| 00:20:03 | 首 decide 误用端点 `/api/ops/hitl/decide` → 404 Not Found（正端点 `/api/ops/hitl/requests/{id}/decide`）——如实登记：致 decide 距挂起 44s 非「同秒」，窗口形态因此不同（下述） |
| 00:20:29.761 | decide approved 成功（persisted=true） |
| 00:20:29.768 | **hitl_auto_resume_triggered**（ttl_remaining_s=3599） |
| 00:20:29.771 | **hitl_auto_resume_claimed**（进程内派发 · 探针可见 → 执行恢复 · 图进入在窗 LLM 轮 ~25s） |
| 00:20:29.832 | hitl_persist_guard_skip |
| 00:20:31/36/41/46/51 | 补偿扫描五轮：**compensated→claimed→deferred** ×5（探针「tasks 有 · interrupts 空」= 恢复在窗快照 → defer 不执行 · ttl_remaining_s 3598→3578 逐轮递减留痕） |
| 00:20:54.446 | **delegation_approval_consumed**（恢复执行抵达消费点 · 恰好一次） |
| 00:20:54.453/462 | delegation token_issued（dt-1-3e60cf2d9c14）→ token_verified |
| 00:20:54.487 | **HITL 恢复完成** request=hitl_fcf734403e7544a18f63 approved=[...:1] replay=...:15 |
| 00:20:51 后 | auto_resume 台账归零（链闭环 · 无游荡重试） |

### 台账链核验（口径达成）

- 链：`triggered×1 → claimed×1（直达执行）→ (compensated→claimed→deferred)×5 → approval_consumed×1 → token_issued×1 → token_verified×1 → HITL 恢复完成×1`。
- **零 stranded_checkpoint（grep count=0）· 零「HITL 自动恢复执行失败」（count=0）**——TC3 断言口径达标。
- **窗口形态如实登记**：本次 decide 距挂起 44s（误端点耽搁），checkpoint 已提交，故 decide-同秒原始窗口未命中、首认领直达；**deferred×5 命中的是「恢复在窗」形态**——恢复执行在窗（LLM 轮 ~25s）期间补偿扫描五轮重认领，探针读得「有 pending tasks · interrupts 全空」→ defer 不执行，**恰好挡住 5 次重复恢复**（修复前 live D1 同场景即重复执行撞 stranded_checkpoint ×6 的签名）。方向 A 机制本体 live 实证，非失败重试轮。
- 噪音定性（非 app 缺陷 · 与 stranded 无关）：opentelemetry「Failed to detach context」×2 = SSE 断连既有噪音；「Exception in ASGI application」= 我自 terminate 的 PG 连接的 SQLAlchemy rollback 善后噪音。
- 后续观测：恢复后 supervisor 二轮 replan 起新单 hitl_4eb7298976124c0c9a8f（subtask :2 · 图自身多轮行为 · 与本 task 机制无关），留 pending 于隔离库，扫描器对未决单不动（实证第四条件）。

## 留转清单回应（30 invoke :62-68 逐条）

2. **not_interrupted 子窗口**：本 live 未观测到（checkpoint 行始终先于扫描认领可见；5 轮 deferred 全部命中「tasks 有 · interrupts 空」形态，无一命中 not_interrupted 子窗口）。维持窄判定不扩面——若他日 live 首跑该子窗口可观测，另起 task 议（本 task 钉死契约 4 禁动）。
3. **真·永久 stranded 在 auto 下**：未造 TTL 耗尽单（3600s 超出本次核验窗口）；但观测口径已实证——`hitl_auto_resume_deferred` INFO 台账逐轮留痕（ttl_remaining_s 3598→3593→3588→3583→3578 递减），永久 stranded 单在 auto 下将以此键每轮留痕直至 TTL，FP-7 观测路径成立。
4. **探针成本**：live 实证每次认领 1 次只读 aget_state（apostgres_saver 连接）；5s 间隔 ×5 轮 PG 零压力迹象（pg_stat_activity 无堆积）。认领低频可接受，照登。
5. **PG 闸环境事实**：实证照登——仓根 .env 经 app/config.py:11 load_dotenv 使 LG_RAG_HTTP_CHECKPOINTER=postgres / LG_RAG_DELEGATION_TOKEN_MODE=enforce 在 pytest 全进程生效（基线 4 红同源）。工作树未跟踪 jar 全程未动未 add。

## 结论

**七项核验全 PASS · 可进 PR 队列。** 红测时序严格在前 · 最小面零外溢 · deferred 非假绿（注入式断言 + live 五轮实证双保险）· 反回归零新增红 · TC3 live 台账链闭环零 stranded。

## 过程留痕

- 2026-10-11 00:00–00:10 文档读毕（task/30 invoke/audit R1）→ 核验 1-4 逐项独立复跑。
- 00:10–00:25 TC3 live：隔离库 + :8060 服务 + 挂起/decide/台账链核验（卡点排查见时间线）。
- 现场清理：自起 uvicorn（:8060）已杀 · /tmp/tc3_* 临时件销毁 · 隔离库 opsdesk_tc3 已 DROP · 维护者 :8000 / jar / .env 未触。

## 修订

| 日期 | 说明 |
|------|------|
| 2026-10-11 | 40 核验落盘：七项全 PASS · TC3 live 实录（deferred×5 机制本体实证 · 零 stranded）· 留转 2-5 逐条回应 · N-1~N-3 照登 · 结论可进 PR 队列 |
