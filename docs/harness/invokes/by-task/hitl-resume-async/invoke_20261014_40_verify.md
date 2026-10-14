# invoke_20261014_40_verify · hitl-resume-async · 40 验收（TC8 live 机验 · echo 场景）

- 帽：40 验收（父会话 00 委派令）· 日期 2026-10-14 · 分支 task/hitl-resume-async（30 实现 commit e9e6845）
- 服务：127.0.0.1:8050（菜谱起服三坑解法：env -u 剥九个 proxy 变量 · OPS_CHAT_TRACER=off · echo 六 env 组）· 验完已杀（见末节）
- 菜谱：docs/harness/invokes/by-task/hitl-resume-replay-contract/invoke_20261013_40_verify.md（tc5_s3_step1.sh/step2.sh 流程复用）
- 证据附件：attachments/（tc8_login.sh · tc8_round.sh · tc8_r1_settle.sh · tc8_r5_resume.sh · tc8_r7_reject.sh · tc8_r8_badmode.sh · tc8.jar · r1–r9 各轮 .hdr/.json/.sse/.timing）

## 一、TC8 逐项 verdict

| # | 观测项 | verdict | 证据 |
|---|--------|---------|------|
| 1 | resume 秒回 + 响应形（顶层键 {ok,request,resume,replay,ts} 不动 · resume.status=="accepted"） | ✅ PASS | r1_resume.json 等 8 轮全 200；resume 键={approved,decided_by,rejected,status,thread_id} · replay 键={cursor,events_failed,events_persisted,persisted,re_interrupted,run_id} |
| 2 | **p95 < 1s**（多样本实测） | ✅ PASS | 8 样本 37.915–46.622ms（含 1 轮 rejected），**p95=46.6ms**（nearest-rank），较同步旧时代 130–310s 降三个数量级 |
| 3a | 秒回后 replay 立即打 = 409 + Retry-After: 2 | ❌ **FAIL（实测 200 部分帧）** | r1 在飞 replay HTTP=200 · 9 帧无终帧（r1_live.sse）；r9 immediate decide 后即刻 replay 同 200。根因分析见「三」 |
| 3b | 沉降后 replay=200 · 帧 seq 连续 · 终帧逐键对拍 | ✅ PASS | r1_full.sse：18 帧 seq 1–18 连续；seq18 done{status:'resumed', latency_ms:180804 **int**, keys={events_persisted,latency_ms,run_id,status,thread_id}, **无 model 键**}；hitl.resumed 帧恰 1 枚（seq8） |
| 4a | 回归 T-W2 S3 链（decide→resume→沉降→终帧） | ✅ PASS | r1 十八帧与菜谱 S3 基准（十八帧 · seq18 done{resumed,135574}）逐键同形 |
| 4b | 回归 TC5 二次 resume 409 | ✅ PASS | 在飞二次 resume=409「该申请的恢复正在执行中，待沉降后再试」（r1_409.body）；**真**沉降后二次 resume=409「thread … 没有挂起的 interrupt —— 要么这轮已经跑完，要么 checkpointer 与挂起时不是同一个」（r1_dup_settled2.json · preflight not_interrupted 语义） |
| 4c | 驳回 resume 收工链 | ✅ PASS（按 task:90「收工=等待态终帧」口径） | r7：decide rejected → resume 200 accepted{rejected:[…:1]} → 图「未获批准收工」→ supervisor 重规划再 interrupt（新申请 hitl_578a9f 子任务 :2）→ seq15 done{waiting_approval, latency_ms:82686 int, 无 model}；新申请未被误消费（GET 实证 status=pending · decision_by=null） |
| 5a | resume_mode 未知值 400 | ✅ PASS | r8：resume_mode="turbo" → **400**「resume_mode 必须是 inherit / immediate / manual」（r8_badmode.json）；同 RID 合法 decide 仍 200（坏 decide 未消费申请） |
| 5b | immediate=立即调度（异步佐证） | ✅ PASS | r9：decide resume_mode=immediate → 17.7ms 秒回 · resume 块 {required:false, auto_triggered:true}；后台执行 ~102s 后 r9_full.sse seq18 done{resumed, latency_ms:102276 int, 无 model} —— decide 毫秒回 + 执行百秒级 = 异步调度实证 |

## 二、原始计时数据（resume 端点 · curl time_total）

| 轮 | decision/mode | DECIDE | RESUME | 备注 |
|----|---------------|--------|--------|------|
| r1 | approved/inherit | 29.236ms | **39.090ms** | 全断言轮 |
| r2 | approved/inherit | — | **43.022ms** | |
| r3 | approved/inherit | — | **41.322ms** | |
| r4 | approved/inherit | — | **44.102ms** | |
| r5 | approved/inherit | — | **37.915ms** | 孤儿 run 接力（客户端被杀后 RunWorker 解耦推进至 waiting_approval · 附证） |
| r6 | approved/inherit | 13.207ms | **40.072ms** | |
| r7 | rejected/inherit | — | **46.622ms** | 驳回链轮 |
| r8 | approved/inherit | bad=400 · good 200 | **44.990ms** | 白名单轮 |
| r9 | approved/immediate | 17.664ms | auto（decide 触发） | immediate 轮 |

**p95 = 46.622ms（8 样本 nearest-rank）· 门槛 1s → PASS**

## 三、FAIL 项 3a 根因分析（不改码 · 供 00 裁定）

**现象**：resume 秒回后、后台执行确在飞期间，replay 返回 **200 部分帧**（r1 在飞 9 帧无终帧 → 沉降后 18 帧），非 task TC8 预期的 409 + Retry-After: 2。

**代码根因**：replay 在飞判定走 `load_events_after(refuse_in_flight=True)`（app/ops/lg_rag/router.py:411）→ `run_stream_closed`（app/ops/lg_rag/event_store.py:132-152）：**存在任何 done/error 帧即判收尾**，其 docstring 明示与 `run_is_terminal` 刻意不同口径——「done{waiting_approval} 挂起也算收尾，挂起 run 的 replay 是既有合法操作须零 diff」。挂起 run 已持 done{waiting_approval}（seq7），故 async resume 在飞期间 replay 必过 200。

**task 内部矛盾**：钉死表行「挂起 replay 200 零 diff · 不变」（task_hitl_resume_async.md:90）与「async resume 在飞期间 replay 立即打=409 属预期」（:92）在给定 `run_stream_closed` 口径下**不能同真**；且同步旧时代同窗口 replay 也是 200 部分帧（同一代码路径）——当前实现属零 diff 保持，**非回归**。

**影响面**：web resume 后 replay 得 200 部分帧（无终帧）属既有语义；JC-F1 的原故障面（resume 请求自身 30s 超时 ERR_ABORTED）已由异步化根除（resume 实测 ~40ms），web 侧跟进 replay 追帧即可见终帧。

**裁定选项**（归 00/维护者，40 不动码）：(a) 修 task TC8 表述：replay 在飞 409 仅限「无收尾帧的 live run」，resume 在飞窗 replay=200 部分帧为既有语义（建议，零码改）；(b) 若产品确要 resume 在飞窗 replay=409，须把 resume 在飞注册接进 replay 判定面（改 app/ops/lg_rag 读路径，超本 task 范围，需另立 task）。

## 四、附证与过程记录

- r5 孤儿接力：客户端 curl 被杀后 run 037556e7 仍推进至 waiting_approval（RunWorker 解耦 · PR #250 行为），接力 decide+resume 37.9ms 秒回成功。
- r7 驳回链二次 resume：首任务完成后 thread 仍 interrupt（新 :2）→ preflight 放行 → 200 重投递（F3 幂等重投递设计内）；空决策不重消费新 pending 申请（hitl_578a9f 实证 pending）。
- pytest 回归属 30 棒已实证（10 件面 152 绿零新增红），本棒不重跑。

## 五、结论

**TC8 总判：1 FAIL（3a · task 表述与既有 replay 语义矛盾 · 非码回归）+ 8 PASS**。建议 00 走裁定选项 (a) 回填 task 表述并签收；若选 (b) 则另立 task。

## 六、收尾

- 服务进程已杀、端口 8050 已净（见末节汇报）
- git add 本线产出（invoke_40 + attachments/），不 commit（归 00 统提）
