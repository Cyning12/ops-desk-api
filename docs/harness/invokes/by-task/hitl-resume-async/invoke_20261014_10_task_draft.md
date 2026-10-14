# invoke_20261014_10_task_draft — hitl-resume-async · 10-task 起草

| 键 | 值 |
|---|---|
| hat_id | 10 |
| task | `docs/tasks/active/task_hitl_resume_async.md` |
| 分支 | `task/hitl-resume-async`（base `master` 56e4a9f = PR #250 merge · 与当前 HEAD 一致） |
| 日期 | 2026-10-14 |
| 上游 | web 00 跨仓移交令 `../ops-desk-web/docs/harness/invokes/by-task/hitl-resume-async-handoff/invoke_20261014_00_dispatch_api.md` |

## 启动令摘要

- 维护者裁定（web 会话 m00383）：**B 方案 = api 单边异步化 resume**（复用 PR #250 RunWorker 机制形态）；A 方案（web per-request timeout 拉长）不单独做
- JC-F1 实证：resume 同步执行 130–310s · axios 30s 掐断 `net::ERR_ABORTED` · 后端跑完前端误回「待审批」
- §4 契约钉死六项：decide/resume 两步不变 · resume_mode 白名单不变且 immediate=立即调度（非同步跑完）· 驳回也可 resume 收工 · 终帧 `done{status:"resumed", latency_ms:int≥0, 无 model 键}` 逐键不变 · replay 在飞 409 + `Retry-After: 2` 不变 · ResumeError→409/503/502 映射表不变
- §5 契约决策点：resume 响应 `resume` 键变「已受理」形态 · **约束 30：状态码保持 200、键名不删不改 → web 零改动**；若必须动响应面，先回执 web（落点同 handoff 目录 · 写入 task failure_paths/决策记录）
- §6 验收：resume p95<1s（echo live）· 秒回后 replay 立即 409 在飞 → 沉降 200 帧 seq 连续终帧 done{resumed, latency_ms 实值} · 回归 T-W2 S3 链 + TC5 二次 resume 409（菜谱复用 hitl-resume-replay-contract）· pytest HITL/auto-resume 面 + 新增异步单测
- 纪律：分支 task/hitl-resume-async · HG-AUDIT-R1 approved 前 30 拒改码 · 证据落 `docs/harness/invokes/by-task/hitl-resume-async/`
- **维护者授权留痕（00 转达 · 本会话 2026-10-14）**：维护者已授权 00 签收本 task 后续所有文档（含 HG-TASK-DRAFT / HG-AUDIT-R1 / HG-GRAPH-MODULES 闸签）；task 人工闸表各闸说明列已注明「维护者 2026-10-14 授权 00 代签（会话授权 · invoke_10 留痕）」；闸状态仍 pending —— 签署动作由 00 在 20 R1 PASS 后执行，本棒不预签

## 输入真读清单（亲读锚点 · 全核真）

| 输入 | 读取法 | 核真结论 |
|---|---|---|
| 移交令 invoke_20261014_00_dispatch_api.md | 全文 85 行 | §4/§5/§6 逐字吸收进 task 钉死表/决策点/验收 |
| JC-F1 证据（web 40 机验） | `git -C ../ops-desk-web show a2b1b1f:<path>` | invoke_20261013_40_verify.md:43-44 实证 130–310s/30.1s ERR_ABORTED/卡片误回待审批；终帧 done{resumed, latency_ms:306187}（b3b2da40 · jc_tc3v3_replay.sse）与 124348（04417a5b）；replay settled 200 at 107.6s（jc_tc3v3_network.json） |
| `app/ops/hitl/router.py` | 亲读 | resume_request :466-529 · **:494 `await _execute_decided_resume(row)` 同步执行=根因** · 响应键集 {ok,request,resume,replay,ts} :513-533 · 映射表 :495-509（409×5/503×1/502 兜底）· 状态守卫 :487-491 · _execute_decided_resume :418-463 · _open_event_sink :360-396（run_owner 反查 :378 不可省）· _persist_resumed_turns :399-415 · decide :184-269（白名单校验 :207-211 · auto 派发 :246-254） |
| `app/ops/hitl/resume.py` | 亲读 | resume_hitl_run :288 · ResumeEventSink :112-162 · close 终帧 :124-137（latency_ms :135 · 无 model 键）· checkpointer fail-closed :332-339 |
| `app/ops/hitl/auto_resume.py` | 全文 313 行 | schedule_auto_resume :138-158 派发不阻响应 · _claim_and_execute :193-234（PG 行锁认领/run_is_terminal 守卫/就绪校验 defer）· scan_approved_not_resumed_once :237-274 四条件 · 同源纪律 :11-14 · 执行唯一走 router._execute_decided_resume :229-231 |
| `app/ops/lg_rag/run_worker.py`（PR #250） | 全文 245 行 | RunEventBus :25-61 · start_run_worker 单飞 :92-168 · scan_orphan_runs_for_compensation :188-245 · **生产侧周期接线未见于 app/（调用方仅 tests）** |
| `app/ops/lg_rag/event_store.py` | 亲读 | run_stream_closed :132 · refuse_in_flight→409 :246 · list_open_runs :160-163 |
| `app/main.py` | :46-59 | 补偿扫描器仅 MODE_AUTO lifespan 挂（:52-54 · manual 零创建）→ manual 模式崩溃兜底缺口 = 30 裁定面 |
| 姊妹模板 task_hitl_resume_replay_contract.md | 亲读 | 结构/文风/lint PASS 范式（本 task 文件沿用） |
| 40 菜谱 invoke_20261013_40_verify.md（hitl-resume-replay-contract） | 亲读 | 起服三坑 + echo 六 env 组 + tc5_s3_step1.sh/step2.sh（TC8 复用） |
| 姊妹 10 invoke_20261011_10_task_draft.md | 亲读 | 本 invoke 格式范式 |

## R0 思考轮结论

**问题定义闭合**：JC-F1 根因 = `router.py:494` 请求内同步 await 整条恢复链（130–310s）超 axios 30s；B 方案方向 = 请求内保留同步可判定守卫 + asyncio 派发秒回 200 携 replay cursor + 执行唯一走同源 `_execute_decided_resume` + 复用 RunWorker/auto_resume 单飞与补偿扫描形态；三闸 pending 零签、HG-AUDIT-R1 approved 前 30 拒改码。

## 关键裁定

1. **复用不另造轮子**：30 实现方向约束写明 —— 派发参照 auto_resume.schedule_auto_resume 形态，单飞参照 _BACKGROUND_TASKS/_workers，崩溃兜底复用补偿扫描形态（四条件/孤儿扫描）
2. **接线面缺口显式化（30 裁定 · 10 不越权）**：scan_orphan_runs_for_compensation 生产侧无调用方（仅 tests/test_lg_rag_sse_run_worker.py）；auto_resume 扫描器仅 MODE_AUTO lifespan 挂（main.py:52-54）→ manual 模式「投递后崩溃」无周期兜底，task F3/FP-3 标明 30 裁定
3. **响应面零 diff 为钉死约束（D2/D3）**：状态码 200 + 键名不动 → web 零改动；必须动则先回执 web（落点 handoff 目录）
4. **与启动令出入的真值（照登）**：JC 证据不在 web 工作树 —— 已提交于 web 分支 `task/web-api-joint-check` @ a2b1b1f（**未并 web 主线** · NOT-ANCESTOR of web HEAD 8f55d9f），工作树仅存 gitignored `*.log`；task 依赖节已给出 git show 读取法。数值面（130–310s/30s/终帧实值）与启动令一致，无实质冲突
5. **闸面**：HG-TASK-DRAFT/HG-AUDIT-R1/HG-GRAPH-MODULES 全 pending · 维护者授权 00 代签留痕（见上）· 本棒零签

## 产出

| 文件 | 说明 |
|---|---|
| `docs/tasks/active/task_hitl_resume_async.md` | task v0 初稿（背景/根因锚点/范围 F1–F5/非范围/契约钉死六项/决策点 D1–D3/失败路径七条/验收 TC1–TC8/依赖/必读列表/R0–R5 思考轮/人工闸表 pending） |
| 本 invoke | 10 帽起草留痕 |
| `docs/tasks/active/README.md` | 索引表加一行（纯 docs） |

## 门禁实证

- `npx dsh-coding-kit task lint --file docs/tasks/active/task_hitl_resume_async.md` → **PASS · EXIT=0**（首轮 FAIL 三修：状态行改 `> **状态**：active` 格式 · 元信息表改 `| **key** | value |` 粗体键格式 · 补 `### 自检结论（执行者）` 节 · 复跑零 error 零 warning）
- 禁区自查：app/ 与 tests/ 零改动 · 未签任何 human_gate · 未 push · git add 暂存不 commit（00 统提）

## 遗留

1. 20 R1 书面审查（review_hat=20 · 审查文落盘 docs/harness/reviews/）→ 00 代签三闸 → 30 开工
2. 30 裁定面：F2 幂等具体形态（409 vs 幂等 200）· F3 接线面（resume 专属扫描/复用 lg_rag 扫描/其他）· D1「已受理」键值具体形态
3. 40 棒：TC8 live echo p95<1s + 响应面回执 web（落点 handoff 目录）
4. web 证据分支 a2b1b1f 未并主线 —— 若后续 web 主线合并该分支，依赖节读取法可简化为直读工作树

---

## 2026-10-14 · 20 R1 FAIL 退回回填（10-task · 回填后 lint PASS）

- **退回**：docs/harness/reviews/task_hitl_resume_async_audit_R1_20261014.md（20-task-audit · 内容 FAIL=N1 + n1–n4 · HG-AUDIT-R1 仍 pending）
- **N1 回填**：验收新增 TC2b「旧测 grep 影响面」——必破断言 4 处亲读核真（tests/test_hitl_resume.py:362 · tests/test_hitl_pending_decide.py:501/528/661）+ decide 面零 diff 区分（test_hitl_pending_decide.py:367-368 · test_hitl_auto_resume.py:308/417-418/570/909）
- **n1**：ResumeEventSink 锚 :112-162 → :54-162（多处联动：根因锚点/必读列表/TC4/自检结论）
- **n2**：TC7「等 8 文件」→ 实证 10 件列全名（test_hitl*.py 7 件 + lg_rag sse 3 件 · R4 摘要联动）
- **n3**：钉死行5 补 app/ops/lg_rag/router.py:417-421（Retry-After: 2 设置点）
- **n4**：invoke_retention_profile 注明 required_invoke_hats 优先（v2.12）
- **门禁实证**：复跑 npx dsh-coding-kit task lint --file docs/tasks/active/task_hitl_resume_async.md → EXIT=0 PASS
- **工作树异常留痕**：16:57 工作树被切 docs/arch-browser 时本 task 5 件产出被 stash（stash@{0} wip-before-arch-browser）· 00 裁定 A 已切回并 pop 恢复 · 另一线未提交修改 app/main.py 与 docs/discussions/2026-09-24_agent-host_current_architecture_v1_zh.md 非本 task 所有 · 未 git add
- 修订记录：task v0 → v0.1
