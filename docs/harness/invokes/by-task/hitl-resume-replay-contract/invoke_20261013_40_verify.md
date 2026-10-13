# Invoke：hitl-resume-replay-contract · 40-verify（2026-10-13）

| 字段 | 值 |
|------|-----|
| **hat_id** | 40-verify |
| **task** | docs/tasks/active/task_hitl_resume_replay_contract.md |
| **分支 / HEAD** | task/hitl-resume-obs-drafts @ fb47c27（30 交付 · 已随 PR #248 squash 合并 · origin/master=acac5e6 · 40 live 实证于同码面） |
| **核验范围** | TC5 live 对照（S2 在飞 replay 409+Retry-After · S3 approve→resume 终帧 latency_ms 实值）+ 工程面复核（TC1–TC4 由 30 全量对拍 + PR #248 CI 独立重跑实证） |
| **live 环境** | 本机 uvicorn 127.0.0.1:8050 · 本地 PG（opsdesk）· .env 六组关键 env 就绪（OPS_DESK_AUTH_MODE=db · OPS_HITL_PERSISTENCE=db · LG_RAG_HTTP_CHECKPOINTER=postgres · LG_RAG_DELEGATION_TOKEN_MODE=enforce · DATABASE_URL · capability env）· 登录 admin/maintainer（scripts/create_initial_user.py 邀请码 · cookie 会话） |

## 启动命令与环境三坑（留痕 · 供复现）

最终启动命令要点：env -u 剥离九个 proxy 变量（http_proxy/https_proxy/all_proxy 大小写 + NO_PROXY/no_proxy + NODE_USE_ENV_PROXY）+ OPS_CHAT_TRACER=off + OPS_CAPABILITY_EXTRA_MANIFESTS=oa.readonly.v1.yaml,testing.v1.yaml（绝对路径逗号分隔）+ OPS_CAPABILITY_ALLOW_WRITE=1 + OPS_CAPABILITY_ALLOW_WRITE_TAGS=testing + OPS_STRATEGY_EXTRA_CANDIDATE_CAPABILITY_IDS=testing.write.echo + uv run uvicorn app.main:app --host 127.0.0.1 --port 8050。完整脚本：attachments/tc5_s3_step1.sh。

| 坑 | 症状 | 解法 |
|----|------|------|
| ① langfuse tracer | OPS_CHAT_TRACER=langfuse + .env LANGFUSE_BASE_URL 值带引号 → langfuse httpx 初始化炸 InvalidURL("Invalid port: ':1]'") 毒化全部 LLM 调用（run 0.5s 即 error 帧沉降 · 在飞窗捕不到） | OPS_CHAT_TRACER=off（但单独不够 · 见②） |
| ② NO_PROXY 裸 ::1（真凶） | shell NO_PROXY=localhost,127.0.0.1,::1,[::1] 含裸 ::1 → httpx URLPattern 解析同炸 port ':1]'（embedder.py 与 siliconflow provider 同面） | 启动命令 env -u 九个 proxy 变量彻底剥离（T-W2 当年 env -i 天然规避 · 本机直接 shell 首次暴露） |
| ③ strategy 候选集不含写能力 | supervisor plan 子任务 tool id 不在 allowed_capability_ids → 空集 fallback 单 rag · 永不触发 delegation issue HITL | OPS_STRATEGY_EXTRA_CANDIDATE_CAPABILITY_IDS=testing.write.echo（app/ops/strategy/config.py:39-71 env 追加口）+ OPS_CAPABILITY_ALLOW_WRITE=1 + OPS_CAPABILITY_ALLOW_WRITE_TAGS=testing（side_effect=write 强制审批 · app/ops/capability/policy.py:38 / baseline.py:40） |

## TC5 契约逐条 live 对照

| # | 观测项（task 验收 TC5） | verdict | 证据（attachments/） |
|---|------------------------|---------|---------------------|
| 1 | **S2 同形态**：run 在飞时 POST /lg-rag/replay → 409 + Retry-After（原 500 消失） | ✅ | 两 run 三打实证：run d0d824d405d842a39a2139c972d12d97 在飞窗（14:12）HTTP **409 + retry-after: 2** + body {"detail":"Run is still in flight; retry after it settles."}（tc5_s3_409.hdr/.body）；孤儿在飞 run 22b65ce24299419baab6539892240b54（客户端掐断 · 永不沉降）13:59 首打 + 14:20 复打同 409（tc5_orphan_409.hdr/.body · fail-closed 语义活样本）；全程 **HTTP 500 未出现** |
| 2 | **S3 同形态**：approve → resume → 终帧 done{status:'resumed'} 观测 latency_ms 实值 | ✅ | run d0d824d4（thread f57737d0b0824f72bac0367522941854）：decide approved（inherit · 不送 resume_mode）→ 200 status=approved resume.required=true（tc5_s3_decide.json）→ resume POST 200 **JSON 面非 SSE**（{ok, replay:{cursor d0d824d4:18, events_persisted:11, persisted:true}} · answer 真实生成 · echo written:false 语义 mock · tc5_s3_resume.sse）→ 全量 replay **18 帧 seq1-18 连续无缺**（tc5_s3_full.sse）：seq7 done{waiting_approval, latency_ms:34122} · seq8 hitl.resumed · **seq18 done{status:'resumed', latency_ms:135574}**（与 T-W2 18 帧形同构 · F-OBS-1 修复 live 实证） |
| 3 | model 键不补钉案 live 对照（FP-1 禁伪造） | ✅ | seq18 done payload 键集 = {events_persisted, latency_ms, run_id, status, thread_id} · **无 model 键**（30 钉案与 live 一致 · 对照测试钉死禁伪造） |
| 4 | 挂起 run replay 零 diff（非范围守界 live 面） | ✅ | waiting_approval 态 replay → **200 · 七帧 seq 连续**（tc5_s3_suspended_replay.sse · 挂起放行语义存续） |
| 5 | 沉降后 replay 零 diff（TC3 live 面） | ✅ | resume 沉降后全量 replay 200 十八帧（同 #2）；completed run e05a9af1bbe848e7ba27e334e868a04f replay → **200 · 一百十二帧 seq 连续**（tc5_completed_replay.sse · completed 形态 done 无 status 键属既有正常形态）；S2 smoke run 69b7639e 沉降 replay 同 200（tc5_s2_settled.sse） |
| 6 | hitl.waiting 帧 reason 语义与 T-W2 同形 | ✅ | seq6 hitl.waiting reason=「委派签发需人工审批（capability testing.write.echo 非只读（side_effect=write））」· RID=hitl_81aea17536024f969e9f（tc5_s3_live.sse 七帧 · seq7 done{waiting_approval, 34122}） |

## 工程面复核（40 口径）

| # | 面 | 结果 |
|---|----|------|
| 1 | PR #248 CI 四件（check · import-linter · lint-wiki-delta · pytest） | **全绿**（CI 对 merged 内容独立重跑 · 构成 TC1–TC4 工程面独立实证 · 非承 30 本机记录） |
| 2 | 30 全量对拍（uv run python -m pytest tests -q · 本地真 PG） | 1803 passed + 5 failed · clean tree stash 对拍同 5 红同名同因 = 既有环境性 · **零新增红**（30 invoke 在案） |
| 3 | npx spec-wave@3.3.0 task lint --file docs/tasks/active/task_hitl_resume_replay_contract.md | **LINT: PASS** EXIT=0（40 亲跑） |
| 4 | npx spec-wave@3.3.0 verify --target . --task docs/tasks/active/task_hitl_resume_replay_contract.md | **VERIFY: PASS** EXIT=0（三闸 approved · 40 亲跑） |

## 观测口径注（照登）

- **resume 端点应答为 JSON 面（非 SSE）**：POST /hitl/requests/{id}/resume 同步执行恢复图后返 {ok, request, resume, answer, replay}；终帧观测面 = 事后 /lg-rag/replay（与 T-W2 取证口径一致 · 非回归）。
- **孤儿在飞 run 22b65ce2 留样**：客户端掐断的 run 永不沉降 · 持续 409——fail-closed 语义的活样本（在飞=有帧无收尾帧 · run_stream_closed 判定面实证）。

## 回执 T-W2 联调链（照登 · 非改码）

- **F-OBS-1 闭环**：resume 终帧 done{status:'resumed'} 现携 latency_ms 实值（live 实证 135574ms）→ 前端徽标「耗时 0ms」根因消除；model 键不提供（FP-1 钉案禁伪造 · web 兜底已落 web PR #61 · 去兜底由 web 仓自裁）。
- **F-OBS-2 闭环**：在飞 replay 由瞬返 500 → **409 Conflict + Retry-After: 2**（两 run 三打实证）；挂起/沉降 replay 零 diff；旧客户端按 Retry-After 退避重试即可（FP-3 缓解按预期成立）。

## 结论

**PASS**——TC5 live 对照六条全实证（409 语义化 + Retry-After · resumed 终帧 latency_ms 实值 · model 不补钉案 · 挂起/沉降零 diff · reason 同形）；TC1–TC5 全勾，task 验收面收口；回执 T-W2 联调链照登（F-OBS-1/F-OBS-2 闭环证据齐备，可交 web 仓回执）。

## 附件清单（attachments/ · 16 件）

tc5_s3_409.hdr/.body（S3 在飞 409）· tc5_orphan_409.hdr/.body（孤儿 run 复打 409）· tc5_s3_live.sse（挂起 live 七帧）· tc5_s3_suspended_replay.sse（挂起 replay 200）· tc5_s3_decide.json · tc5_s3_resume.sse（resume JSON 面）· tc5_s3_full.sse（全量 replay 十八帧 · seq18 终帧）· tc5_completed_replay.sse（completed 一百十二帧）· tc5_s2_live.sse / tc5_s2_stream.hdr / tc5_s2_settled.sse（S2 smoke run 69b7639e 三面）· tc5_sanity.sse（sanity run e05a9af1 流）· tc5_s3_step1.sh / tc5_s3_step2.sh（启动与决策复现脚本）

## 修订

| 日期 | 说明 |
|------|------|
| 2026-10-13 | 40 落稿：TC5 live 对照六条全实证 PASS（附件 16 件 · 环境三坑留痕 · 回执 T-W2 链照登）· task lint PASS / verify PASS EXIT=0 亲跑 |
