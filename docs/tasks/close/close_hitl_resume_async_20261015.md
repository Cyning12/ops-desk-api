# CLOSE：hitl-resume-async（POST /hitl/requests/{id}/resume 异步化 · JC-F1 B 方案 · 复用 RunWorker/auto_resume）（2026-10-15）

> **task**：[../done/task_hitl_resume_async.md](../done/task_hitl_resume_async.md)（已归档 done/ · 状态行 CLOSED 回写）
> **类型**：性能/契约缺口收口（JC-F1 · web 00 跨仓移交 B 方案 · api 单边异步化 · 跨仓联合 CLOSE）
> **关账日期**：2026-10-15 · 帽位：CLOSE（50 · 维护者令「web 完成后一起 close」· 授权链：维护者 2026-10-14 会话授权「授权00签收后续所有文档」· 00 代录签收过程文档）

---

## 一 · 任务信息

| 项 | 值 |
|----|----|
| task_slug | `hitl_resume_async` |
| 依据 | web 00 移交令 `../ops-desk-web/docs/harness/invokes/by-task/hitl-resume-async-handoff/invoke_20261014_00_dispatch_api.md`（维护者裁定 B 方案）· JC-F1 40 机验实证（web 分支 `task/web-api-joint-check` @ a2b1b1f）· 本仓锚点亲读核真（base `master` 56e4a9f） |
| 背景 | web 联调实证：resume 端点**同步执行**整个图恢复 130–310s，axios 全局 30s（web `src/api/http.ts:50`）掐断 `net::ERR_ABORTED`，后端跑完前端卡片误回「待审批」——状态假相。根因 `app/ops/hitl/router.py:494` 请求内同步 `await _execute_decided_resume(row)` |
| 目标 | `POST /api/ops/hitl/requests/{id}/resume` 秒回 200（投递异步执行后即返回）携 replay cursor；恢复执行异步进行，事件照常落盘，前端经 replay 追帧 |
| 分支 | `task/hitl-resume-async`（base `master` 56e4a9f） |
| 帽链 | 10-task（v0 → v0.1 吸收 R1 退回 → v0.2 吸收维护者裁定 a）→ 20-task-audit R1 **FAIL**（N1 阻塞+4nits）→ R2 **PASS** → 三闸 approved（00 代签 · 维护者 2026-10-14 会话授权）→ 30 红测先行（交付 commit `e9e6845`）→ 40 live 机验（`388e923` · 8 PASS + TC8-3a 维护者裁定 a）→ PR #252 → **CLOSE（本档 · web 复验 PASS 后联合关账）** |

## 二 · 交付

| 环节 | 实证 |
|------|------|
| PR | [#252](https://github.com/Cyning12/ops-desk-api/pull/252) · **MERGED 2026-10-15T01:25:56Z · squash commit `0e5f6b1`**（分支 4 commits：`3be6dd3` 文档+闸 → `3f0aadb` 审查文命名/机读修复 → `e9e6845` 30 实现 → `388e923` 40 机验+task v0.2 · CI 4/4 绿：check/import-linter/lint-wiki-delta/pytest） |
| 码面 | `app/ops/hitl/resume.py`（`_resume_with`/`resume_hitl_run` 增 `preflight_only` 尾参 · preflight 短路在两道快照检查后 astream 前 · PG 路径 `setup=not preflight_only`）· `app/ops/hitl/router.py`（抽 `_collect_decisions_or_raise` · 新增 `_preflight_decided_resume` / `_RESUME_IN_FLIGHT` 单飞字典 / `_run_resume_in_background` / `_best_effort_replay_cursor` · `resume_request` 改写：404/状态守卫不变 → 在飞 409 → 占位 None 防 TOCTOU → preflight（ResumeError→409/503/502 映射表逐字不变）→ `asyncio.create_task` → 响应已受理形） |
| 响应面 D1/D2 | `resume={status:"accepted", thread_id, approved, rejected, decided_by}` · `replay={run_id, cursor:best-effort, events_persisted:0, events_failed:0, persisted:bool(run_id), re_interrupted:false}` · **状态码 200 · 顶层键 `{ok,request,resume,replay,ts}` 不删不改 → web 零改动**（web 复验实证成立） |
| 契约钉死六项 | 逐项落地零回归：decide/resume 两步不变 · `resume_mode` 白名单未知值 400（immediate=立即**调度**异步）· 驳回可 resume 收工 · 终帧 `done{status:'resumed', latency_ms:int≥0, 无 model 键}` 逐键不变 · replay 在飞 409+Retry-After:2 语义面不变（口径修正见 §四.1）· ResumeError 映射表不变 |
| 测试面 | 新建 `tests/test_hitl_resume_async.py` 6 测（红测先行 RED→GREEN：响应先于执行完成返回 / 在飞 409 / 幂等重投递 / preflight 拒已完成 / 崩溃兜底 / cursor 形态）· TC2b 旧测 4 处断言适配（`test_hitl_resume.py` · `test_hitl_pending_decide.py` ×3：fake 捕获 outcome + `_drain`/`_adrain` 沉降后断言）· `test_hitl_resume_events.py` 单点适配 2 处 · `test_hitl_auto_resume.py` 单路径钉 ==1→==2（preflight 与后台执行同一驱动器非第三实现）· **decide 面 5 处消费点零 diff** |
| 图谱 | `docs/_tech_graph/l1/01_modules.md` hitl 行备注回写（异步化形态/preflight/单飞/F3 裁定）· `shared/graph.json` 再生成 · graph-compile 绿 |
| invokes | `docs/harness/invokes/by-task/hitl-resume-async/`（10_task_draft / 20_task_audit / 30_implement / 40_verify + attachments 105 件全量证据）· 本 CLOSE 补 50 于同目录 |
| 审查文 | 址A 原件 `docs/harness/reviews/task_hitl_resume_async_audit_R1_20261014.md`（FAIL）/ `_R2_20261014.md`（PASS）· **址B 复制件 `docs/audits/task-review/20261014_hitl-resume-async_r1.md` / `_r2.md` 随本 CLOSE 落**（双址规约 §二 过渡期口径 · 址A 原件不动） |
| 跨仓回执 | api 30 回执 `../ops-desk-web/.../hitl-resume-async-handoff/invoke_20261014_30_api_receipt.md`（响应面终态 + 语义迁移一点）· api 00 复验启动令 `invoke_20261015_00_dispatch_web_reverify.md` · **web 40 复验回执 `invoke_20261015_40_web_reverify_receipt.md`（TC1–TC7 全 PASS · JC-F1 跨仓闭环）** |
| **CLOSE 增量** | task 档归档 done/（状态行 CLOSED + 修订记录 CLOSED 行）· 址B 复制件两件落盘 · active README 登记表补登（active 行→归档行）· 本档 + 50 invoke 落盘 |

## 三 · 核验结论（验收终态摘要 · TC1–TC8 + web 复验 TC1–TC7）

### api 40 live 机验（40 invoke · echo 场景 · 全可机断）

| 验收项 | 结果 | 实证 |
|--------|------|------|
| TC1 红测先行 | ✅ | RED 6 测全红（「resume 端点仍同步等执行 2.01s」· KeyError 'status' · 在飞第二发 200≠409 · RuntimeError 同步传播 · TypeError preflight_only ×2）→ GREEN 6 passed |
| TC2 契约零回归对拍 | ✅ | ResumeError 映射表测全绿（409/503/502 逐档）· resume_mode 白名单 400 · 状态守卫 409 · 驳回收工链绿 |
| TC2b 旧测影响面 | ✅ | 4 处必破断言逐点适配 · decide 面 5 处零 diff 实证绿 |
| TC3 终帧逐键 | ✅ | sink 面既有断言覆盖零 diff · live 逐键见 TC8 |
| TC4 落盘链零 diff | ✅ | 沉降后 sink.persisted==3（open/aggregator/done seq 连续）· turns 断言命中 `_persist_resumed_turns` |
| TC5 幂等防重 | ✅ | 在飞二次 resume=409「恢复正在执行中」· 沉降后=409「没有挂起的 interrupt」（preflight not_interrupted 双钉） |
| TC6 崩溃兜底 | ✅ | 后台执行抛异常 → finally pop 在飞登记 → 重调 resume 幂等重投递成功 |
| TC7 pytest 全量 | ✅ | HITL/auto-resume 11 件面 **212 绿 1 红**（`test_db_store_alist_really_executes_on_asyncpg` 经 master worktree 对拍**基线同红**=环境因）· ruff 本线文件全绿 · 全量 7 failed/1815 passed 红集与 master 基线完全同集 |
| TC8 live 机验 | ✅ | **resume p95=46.6ms**（8 样本 37.9–46.6ms << 1s · 对照同步旧时代 130–310s）· 秒回 200 响应形全对 · 沉降后 18 帧 seq1-18 连续 · 终帧逐键 `done{resumed, latency_ms:180804 int, 无 model}` · hitl.resumed 恰 1 枚 · T-W2 S3 回归 · TC5 双形态 409 · 驳回收工 · 白名单 `"turbo"`→400 · immediate decide 17.7ms 秒回+后台 ~102s `done{resumed}` · 孤儿 run 服务端仍推进（RunWorker 解耦实证）· **3a 维护者裁定 (a) 收口（见 §四.1）** |

### web 40 复验回执（JC-F1 跨仓闭环 · web 零改码实证）

回执 `../ops-desk-web/docs/harness/invokes/by-task/hitl-resume-async-handoff/invoke_20261015_40_web_reverify_receipt.md`（详证 web 仓 `web-hitl-resume-async-reverify/invoke_20261015_40_verify.md` + attachments 19 件）：

| 验收项 | 结果 | 关键数值 |
|--------|------|------|
| TC1 resume<1s 零 ERR_ABORTED | ✅ | decide 17.93ms · **resume 34.77ms 200** · ERR_ABORTED=0（对照旧 30.1s 掐断） |
| TC2 卡片零误回「待审批」 | ✅ | 253ms 转 decided · 45s 采样窗 RETURN_TO_WAITING=false · pageerror/console=0 |
| TC3 replay seq+终帧+徽标 | ✅ | 18 帧 seq1-18 连续 · hitl.resumed 恰 1（seq8）· 终帧 `done{resumed, latency_ms=152757 int, 无 model}` · 徽标「完成 · 耗时 152757ms」**逐位一致** |
| TC4 在飞窗两形态 | ✅ | 命中裁定 (a)：replay 200 部分帧（9 帧 seq1-9 · retryAfter=null）· 前端零异常 |
| TC5 弱消费复查 | ✅ | 顶层键恰 `{ok,request,resume,replay,ts}` · resume.status=accepted · replay.persisted=true · events_persisted/failed=0 · re_interrupted=false · `hitl.ts:76` `resume: unknown` 零改动 · persisted 无消费分支 |
| TC6 驳回+immediate 回归 | ✅ | 驳回：decide 7.76ms → resume 24.71ms accepted → 终帧 `done{waiting_approval, 136850}`（收工口径）· immediate：required=false+auto_triggered → 前端不链第二步（RESUME_CALLED=false）→ 终帧 `done{resumed, 249579 int}` |
| TC7 质量门+回执 | ✅ | lint EXIT=0 · test 263/263 零失败 · build EXIT=0 · 10/20/40 invoke 齐 |

JC-F1 断链三环闭环实证：api 同步 130–310s（已根除 · 实测毫秒级）→ axios 30s 掐断（触发前提消失 · 全窗零 ERR_ABORTED）→ catch→waiting 假相（45s 窗全程未触发）。

**CLOSE 质量钉复跑（本帽 · 归档后仓态 · 重定向取真码）**：

- 改动前基线（master 2a5878c 干净 worktree）：`npx --yes spec-wave verify --target . > /tmp/verify_close_baseline_hitl.log 2>&1; echo EXIT=$?` → **EXIT=0 · VERIFY: PASS**。
- 归档后复跑（本 CLOSE worktree）：`npx --yes spec-wave verify --target . --task docs/tasks/done/task_hitl_resume_async.md > /tmp/verify_close_hitl.log 2>&1; echo EXIT=$?` → **EXIT=0 · VERIFY: PASS**（本 task 址A R1/R2 审查文在案供门禁消费 · 挪档 done/ 后自身零缺口 · 无 specwave_330 式豁免扩列需要）。
- `npx --yes spec-wave task lint --file docs/tasks/done/task_hitl_resume_async.md` → **EXIT=0 · LINT: PASS**。

## 四 · 偏差与 nit（如实照登）

1. **TC8-3a 表述矛盾 · 维护者裁定 (a) 收口（零码改）**：task v0 钉死表行5 称「resume 投递后 replay 在飞窗打 409 属正确行为」——40 实证**在飞窗 replay 返回 200 部分帧**：根因 `run_stream_closed`（`app/ops/lg_rag/event_store.py:132-152`）对任何 done/error 帧即判收尾，挂起 run 已持 `done{waiting_approval}` 收尾帧 → 在飞窗 replay 必 200；**同步旧时代同窗口同路径同为 200**（契约零回归 · 属 task 表述矛盾非码回归）。维护者 2026-10-14 裁定 (a)：修 task 表述零码改签收——v0.2 落成「replay 在飞 409 仅限无收尾帧 live run · resume 在飞窗 200 部分帧为既有语义」· web 复验 TC4 实测命中 200 部分帧形态前端零异常。若产品日后确要在飞窗 409，须把 resume 在飞注册接进 lg_rag 读路径判定面，**另立 task**。
2. **语义迁移（web 回执已声明 · 复验 TC5 实证零影响）**：`run_owner` 归属反查失败的「明说」从响应面（旧 `replay.persisted==false`）迁到后台执行——受理响应 `persisted` 恒 `bool(run_id)`，失败信号改由 api 侧 error 日志+事件流缺席承担。web 侧 `persisted` 无消费分支（复验实证），零改码成立。
3. **F3 崩溃兜底不新造扫描器（30 裁定）**：进程内单飞字典随进程消失无残留；重调 resume 幂等重投递（preflight not_interrupted 防重跑）；auto 模式既有 `scan_approved_not_resumed_once` 周期兜底（`main.py:52-54` 仅 `OPS_HITL_AUTO_RESUME=auto` 时挂 lifespan · manual 模式无周期兜底为已知面）· **replay 永久悬 409 的孤儿补偿周期接线归 `task_lg_rag_sse_disconnect_completion` 另案**。
4. **`test_hitl_auto_resume.py:761` 钉计数 ==1→==2**：preflight 探针与后台执行体调**同一驱动器** `resume_hitl_run`（非第二恢复实现 · 禁第三实现的钉语义存续）——计数修正非语义放宽，注释已改写。
5. **环境坑留痕（api 侧复跑须知 · 承 web 回执末节 + 40 invoke）**：postgresql@18 须 `pg_ctl -D /opt/homebrew/var/postgresql@18 start`（brew services 会被 smart shutdown 杀）· api `auth/me` 500=连接池毒化须重启 api · 测试须 `.venv/bin/python -m pytest`（裸 python 命中 venv 外环境炸 asyncpg）· 本机 `ops_hitl_requests` 残留行曾致 pending 列表 LIMIT 50 挤爆假象（已清）。
6. **跨线共享工作树事件（留痕）**：10/20 帽期间另一线曾将主工作树切至 `docs/arch-browser` 并把本线暂存件收进 stash（00 裁定 pop 恢复零损失）；本 CLOSE 全程在独立 worktree `/tmp/close-hitl-resume-async` 操作，主工作树别线未提交件零触碰。

## 五 · 签录（闸态表与审查文链）

| 闸 / 环节 | 状态 | 文档 / 实证 |
|-----------|------|------------|
| HG-TASK-DRAFT | **approved** | 2026-10-14 00 代签（维护者会话授权「授权00签收后续所有文档」）· 初稿经 20 R1 FAIL 回填 → R2 PASS |
| HG-AUDIT-R1 | **approved** | 2026-10-14 00 代签（同授权链）· R 轮真值 = 址A R1（FAIL）→ R2（PASS · N1+n1–n4 全核销） |
| HG-GRAPH-MODULES | **approved** | 2026-10-14 00 代签（同授权链）· 20 R1 核对 G-L1 预判相容 · 30 按实判回写已落（`l1/01_modules.md` hitl 行备注） |
| HG-PILOT-OPSDESK-GLAYER | n/a | 无外部试点面 |
| 20 R1/R2 审查 | **R1 FAIL → R2 PASS** | 址A 原件 `docs/harness/reviews/task_hitl_resume_async_audit_R1_20261014.md` / `_R2_20261014.md` · 址B 复制件 `docs/audits/task-review/20261014_hitl-resume-async_r1.md` / `_r2.md`（本 CLOSE 落 · 址A 原件不动） |
| invokes | — | `by-task/hitl-resume-async/`（10/20/30/40/50 + attachments 105 件） |
| 合并 | **MERGED** | PR [#252](https://github.com/Cyning12/ops-desk-api/pull/252) · squash `0e5f6b1` · 2026-10-15T01:25:56Z · CI 4/4 绿 |
| 跨仓联合 | **PASS** | web 复验回执 TC1–TC7 全 PASS（`invoke_20261015_40_web_reverify_receipt.md`）· JC-F1 断链三环闭环 · web 零改码实证 |

## 六 · 资源清理

- **本 CLOSE 不删任何东西**：分支 `task/hitl-resume-async`（本地/远端）与本 CLOSE 分支 `docs/close-hitl-resume-async`、worktree `/tmp/close-hitl-resume-async` **移交 00/维护者统一清理**——CLOSE PR 未合并前 close 分支在役；**CLOSE PR 合并后**：`git worktree remove` + 删除分支（task 分支已 squash 合入 master `0e5f6b1` · 删除安全 · 远端一并清）。
- 先例对照：b2_nit3 / specwave_330 各 CLOSE 均将 worktree/分支清理移交 00（active README 登记表在案）· 本件同口径。

## 七 · 维护者验收 checklist 与后续建议

### 维护者验收 checklist（00 代录 · 授权链同上 · 需人重新验收项）

- [ ] **resume 秒回抽验（live）**：master 起服（菜谱 `docs/harness/invokes/by-task/hitl-resume-async/invoke_20261014_40_verify.md` · 起服三坑+echo 六 env 组）· decide(approved) → resume 实测 <1s 返回 200 · 响应形 `resume.status=="accepted"` · 顶层键 `{ok,request,resume,replay,ts}`。
- [ ] **沉降追帧抽验**：沉降后 replay 帧 seq 连续 · 终帧 `done{status:'resumed', latency_ms:int≥0, 无 model 键}` 逐键 · hitl.resumed 恰 1 枚。
- [ ] **幂等双形态抽验**：在飞二次 resume=409「恢复正在执行中」· 沉降后二次=409「没有挂起的 interrupt」。
- [ ] **web 复验回执抽验**：web 仓 `hitl-resume-async-handoff/invoke_20261015_40_web_reverify_receipt.md` TC1–TC7 全 PASS 与 attachments 19 件（截图/HAR/全量帧）抽查一致。
- [ ] **TC8-3a 裁定 (a) 认知确认**：replay 在飞 409 仅限无收尾帧 live run · resume 在飞窗 200 部分帧为既有语义（同步旧时代同形）——维护者 2026-10-14 已裁定，本 checklist 复述备查；若日后要在飞窗 409 需另立 task 改 lg_rag 读路径。

### 后续建议

1. **F3 孤儿周期接线（另案在册）**：replay 永久悬 409 的孤儿补偿周期接线归 `task_lg_rag_sse_disconnect_completion`（co-CLOSE 关联在案）· manual 模式无周期兜底面同案处置。
2. **测试卫生小项（可选）**：`test_db_store_alist_really_executes_on_asyncpg` 环境性红（master 基线同红）可并入仓级测试基线收口 task 统一处置。
3. **web 侧无跟进义务**：复验实证零改码（`resume: unknown` 弱消费 · persisted 无消费分支）——B 方案对 web 完全透明，无 web 跟随 task。

## 八 · 修订记录

| 日期 | 说明 |
|------|------|
| 2026-10-15 | CLOSE 落稿（50 close 棒 · worktree `/tmp/close-hitl-resume-async` · 分支 `docs/close-hitl-resume-async` · base master `2a5878c`）：九节沿仓内先例（b2_nit3 / specwave_330 CLOSE 文档）· 验收终态承 40 invoke TC1–TC8 实证 + web 复验回执 TC1–TC7 全录 · 维护者令「web 完成后一起 close」联合关账 · 质量钉复跑（verify 改动前基线 EXIT=0 PASS → 归档后 EXIT=0 PASS · task lint done/ 档 PASS · 重定向取真码）· 址B 复制件两件落盘（址A 原件不动 · 双址规约 §二）· 维护者 checklist 00 代录（授权链：维护者 2026-10-14 会话授权）· TC8-3a 裁定 (a) / 语义迁移 / F3 另案 / 环境坑 / 跨线工作树事件如实照登 |

## 九 · 附录

### 关键路径

| 类别 | 路径 |
|------|------|
| task（已归档） | `docs/tasks/done/task_hitl_resume_async.md`（状态行 CLOSED） |
| CLOSE 档 | `docs/tasks/close/close_hitl_resume_async_20261015.md`（本档） |
| 交付码面 | `app/ops/hitl/router.py`（resume_request 异步化 + preflight + 单飞）· `app/ops/hitl/resume.py`（preflight_only 透传）· `tests/test_hitl_resume_async.py`（新建 6 测）· `tests/test_hitl_resume.py` / `test_hitl_pending_decide.py` / `test_hitl_resume_events.py` / `test_hitl_auto_resume.py`（TC2b 适配） |
| 审查文（址A 原件） | `docs/harness/reviews/task_hitl_resume_async_audit_R1_20261014.md` · `_R2_20261014.md` |
| 审查文（址B 复制件） | `docs/audits/task-review/20261014_hitl-resume-async_r1.md` · `_r2.md`（本 CLOSE 落） |
| invokes | `docs/harness/invokes/by-task/hitl-resume-async/`（10/20/30/40/50 + attachments 105 件） |
| 跨仓回执链 | `../ops-desk-web/docs/harness/invokes/by-task/hitl-resume-async-handoff/`（00_dispatch_api / 30_api_receipt / 00_dispatch_web_reverify / 40_web_reverify_receipt 四件） |
| 双址规约 | `docs/harness/CONVENTION_review_gate_dual_address_v1_zh.md`（§二 过渡期口径） |

### CLOSE 复跑命令留痕

```bash
npx --yes spec-wave verify --target . > /tmp/verify_close_baseline_hitl.log 2>&1; echo "EXIT=$?"   # 改动前基线 EXIT=0 · VERIFY: PASS
npx --yes spec-wave verify --target . --task docs/tasks/done/task_hitl_resume_async.md > /tmp/verify_close_hitl.log 2>&1; echo "EXIT=$?"   # 归档后 EXIT=0 · VERIFY: PASS
npx --yes spec-wave task lint --file docs/tasks/done/task_hitl_resume_async.md                    # EXIT=0 · LINT: PASS
```
