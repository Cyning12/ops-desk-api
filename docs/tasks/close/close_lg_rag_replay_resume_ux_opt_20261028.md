# CLOSE 档 · task_lg_rag_replay_resume_ux_opt（2026-10-28）

## 一句话

lg-rag replay 恢复段在写窗口语义化（409+Retry-After:2）+ 审批后 SSE 续流（replay follow live-tail）本地验收通过归档；分支 `task/lg-rag-replay-resume-ux-opt`（九 commit）未 push，**PR 合码 + CI 绿 + 分支清理待维护者裁决**（close_pr_policy=required 偏差 · 承维护者授权 m00085/m00236 全程本地直验先例）。

## 需求锚

维护者原话（web 仓 00 转述 · m00321）：「给api仓起草一份replay的优化task，同时思考审批通过后也继续为SSE的方式通信的方案，审批后等待中间过长」。

## 交付（F1–F4）

- **F1**：`event_store.run_resume_in_progress` 只读谓词（∃ hitl.resumed seq > 最新收尾帧 seq · 事件表真源）+ `LgRagRunResumeInProgressError`；恢复段在写窗 replay(follow=false) → **409 + Retry-After:2 + 可区分 detail**；stale 阈 env `LG_RAG_RESUME_STALE_SECONDS`=900 防崩溃永久 409；四态零 diff（挂起/再挂起/沉降/首段在飞）。
- **F2**：`ReplayRequest.follow`（默认 false **字面零 diff** · web chase 器全兼容）；follow=true = 推存量 → DB 轮询按 seq 推增量（env 2.0s）→ 见新收尾帧自然收尾；keepalive comment 不占 seq；上限 env 900s 到点自然结束**零伪造帧**；写窗 follow=true 等待不 409。
- **F3**：契约测试 `tests/test_lg_rag_replay_resume_follow.py` 14/14（红测先行 RED=11 failed 同形先例）。
- **F4**：invoke 10/20/30/40 齐备 · 图谱 lg_rag 行回写 · 经验捕获八条。

## 验收链

10 落稿 → 20 R1 内容 PASS+NIT×3 → v0.2 勘误 → 00 代录三闸（m00236）→ 30 交付（679411f/a2684e3/93ca95e/b11c401）→ **40 初验退回 B-1**（event_store.py:248 tz naive−aware TypeError · 测试库 schema 漂移掩盖 · live 500×2）→ 30 修复（0722f75 `_utc_age_seconds` tz 归一 + aware/naive 回归钉 + e9c0faf docs）→ **40 复验 PASS**（041506e · diff 亲读 · RED 独立复证 · live P1 409 愈/P4 stale 可达）→ 00 CLOSE。

## 证据要点

- 新测 14/14 · 三钉零新增红 · 全量 26 failed/1974 passed 与 base `0a5d610` **26 枚 node id 逐枚一致**（环境性旧红 · .env 决定 23/26）。
- 冻结面：lg-rag-sse-v1 零新 event_type/帧形状 · 零新表/迁移 · resume 200 JSON/decide/callback/OA/首段 stream/旧谓词零 diff。
- live：follow 单连接 18.1s 收全恢复段 seq10→19 无洞自然收尾；在写窗 409+retry-after:2；stale 回拨 7200s 回落放行 + FP-1 日志实收。
- ruff 以 CI 钉版 0.15.21 为准 PASS · graph-compile EXIT=0 · spec-wave verify/lint PASS。

## 遗留移交（另立 task 候选）

1. 恢复段时长优化（68–289s 后台异步根因 · hitl/router.py 自承 130–310s）。
2. web 侧 chase→follow 单连接迁移（web 仓另立 · 现 chase 与 follow=false 全兼容不阻塞）。
3. 测试库 schema 与迁移漂移基建（create_all naive vs timestamptz · 本次全绿假象根因）。
4. follow 生产参数（poll 2.0s/上限 900s）按 live 观察微调。
5. 测试库判红纪律：先 TRUNCATE ops_hitl_requests 清 pending 残留再判签名。
