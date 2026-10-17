# CLOSE：hitl-resume-replay-contract（HITL resume 终帧 latency_ms + 在飞 replay 409+Retry-After · F-OBS-1/2）（2026-10-17）

> **task**：[../done/task_hitl_resume_replay_contract.md](../done/task_hitl_resume_replay_contract.md)（已归档 done/ · 状态行 CLOSED 回写）
> **类型**：契约缺口收口（ops-desk-web 联调链 T-W2 FP-1 报回 · web PR #61 · 纯后端 SSE/HTTP 契约面）
> **关账日期**：2026-10-17 · 帽位：CLOSE（批量关账分支 `close/active-batch-20261017` · 关账 PR 待开）

---

## 一 · 任务信息

| 项 | 值 |
|----|----|
| task_slug | `hitl_resume_replay_contract` |
| 依据 | ops-desk-web 联调链 T-W2 FP-1 纪律报回（2026-10-11 · web PR #61）· 本仓锚点亲读核真（base master `92a8526`） |
| 背景 | 联调实证两观察项：**F-OBS-1** resume 终帧 `done{status:'resumed'}` 缺 `latency_ms`/`model`（S3 replay seq18 · 前端徽标恒显「耗时 0ms」）；**F-OBS-2** run 在飞时 `POST /lg-rag/replay` 瞬返 500（S2 run `640d68970a564fbb8459d8d40cb1c5f6` · replay 端点仅捕 `LgRagRunNotFoundError`，其余异常逃逸） |
| 目标 | (1) 终帧 done payload 补齐 `latency_ms`（必）与 `model`（可取得则补 · 不可得钉案）；(2) 在飞 replay 语义化 409+Retry-After，500 仅存于真实内部错误；沉降后行为零 diff |
| 范围 | F1 终帧增键 · F2 在飞 replay 语义化 · F3 契约测试红测先行 · F4 invoke/图谱/经验捕获 |
| 分支 | `task/hitl-resume-obs-drafts`（base master `92a8526`） |
| 帽链 | 10-task（R0–R5 early_stop）→ 20-task-audit R1 **PASS**（O1–O3 非阻塞观察项）→ 三闸 approved → 30 红测先行（RED `a30b3d3` → GREEN `e4a54d9` · 图谱回写 `61094bf`）→ 40 live 对照 PASS（附件 16 件）→ PR #248 MERGED → **CLOSE（本档 · 批量关账）** |

## 二 · 交付

| 环节 | 实证 |
|------|------|
| PR | [#248](https://github.com/Cyning12/ops-desk-api/pull/248) · **MERGED 2026-10-13T03:40:29Z · squash commit `acac5e6`** · head `task/hitl-resume-obs-drafts` · 标题「feat(hitl,lg-rag): HITL resume 终帧 latency_ms + 在飞 replay 409+Retry-After（F-OBS-1/2 · 30 棒）」 |
| 码面 | `app/ops/hitl/resume.py`（`ResumeEventSink.close()` 终帧 done payload 增 `latency_ms` int≥0 · perf_counter 口径对齐 sse_stream.py）· `app/ops/lg_rag/router.py`（replay 在飞形态 409 + `Retry-After: 2` · 判定面新谓词 `run_stream_closed` 刻意不复用 `run_is_terminal` · 未识别异常仍 500 fail-closed） |
| 契约钉 | 终帧 `done{resumed, latency_ms:int≥0, 无 model 键}` · 在飞 replay `409 + Retry-After: 2` 语义化 body · 沉降后 replay 200 流式零 diff · 404/422 既有语义存续 · freeze `lg-rag-sse-v1` 不升（增键为可选键 · 承 subtask_message 先例） |
| FP-1 裁定 | `model` 键**不补**：sse_stream.py 全文零 model 引用 · resume 全链无来源 · 表无列 · 对照测试钉死禁伪造——钉案照登不硬造 |
| 测试面 | 红测先行时序 git 可查：RED `a30b3d3`（5 红签名全预期：KeyError `latency_ms` 与 F-OBS-1 同形 / AttributeError / TypeError×3）→ GREEN `e4a54d9` · 目标两文件 29 passed · router 测 + DB 三态测 · 全量 1803 passed 零新增红（5 既有环境红 clean tree stash 对拍同名同因）· ruff 触碰文件全绿 |
| 图谱 | `docs/_tech_graph/l1/01_modules.md` hitl/lg_rag 行备注按实回写（`61094bf`）· graph-compile EXIT=0（再生噪音已还原） |
| invokes | `docs/harness/invokes/by-task/hitl-resume-replay-contract/`（10/20/30/40 · `invoke_20261013_40_verify.md` + attachments 16 件） |
| 审查文 | 址A 原件 `docs/harness/reviews/task_hitl_resume_replay_contract_audit_R1_20261012.md`（PASS）· 址B 复制件 `docs/audits/task-review/20261012_hitl-resume-replay-contract_r1.md`（主会话落盘 · 双址规约口径） |
| **CLOSE 增量** | task 档归档 done/（状态行 CLOSED + 修订记录 CLOSED 行）· 本档落盘于批量关账分支 `close/active-batch-20261017` |

## 三 · 核验结论（验收终态摘要 · TC1–TC5 全勾）

| 验收项 | 结果 | 实证 |
|--------|------|------|
| TC1 终帧字段契约（红测先行） | ✅ | RED `a30b3d3`（`KeyError 'latency_ms'` 与 F-OBS-1 同形签名）→ GREEN `e4a54d9` · 时序 git 可查 · `model` 不补 = FP-1 裁定留痕 30 invoke |
| TC2 在飞 replay 语义化 | ✅ | 409 + `Retry-After: 2` 正整数 · 在飞面整体不再触达读路径故 **500 消失** · router 测 + DB 三态测在案 |
| TC3 沉降后零 diff | ✅ | terminal 放行/挂起放行 DB 测 · `refuse_in_flight` 默认关全仓唯一生产调用方 · 404/422 既有断言零新增红存续 |
| TC4 反回归全量对拍 | ✅ | 全量 **1803 passed** + 5 failed 经 clean tree stash 对拍同 5 红同名同因 = 既有环境性 · 零新增 · ruff 全绿 · graph-compile EXIT=0 |
| TC5 live 对照（40 · 2026-10-13） | ✅ | 在飞 replay **409 + retry-after:2 三打实证**（run `d0d824d4` 在飞窗 + 孤儿在飞 run `22b65ce2` 复打 · 500 消失 · fail-closed 活样本）· S3 全链 **replay 18 帧 seq 连续** · seq18 `done{status:'resumed', latency_ms:135574, 无 model 键}`（与 T-W2 形同构 · FP-1 钉案 live 一致）· 挂起 replay 200 七帧 / completed run 200 一百十二帧零 diff · 附件 16 件落盘 |

F-OBS-1 / F-OBS-2 双缺口闭环：终帧 latency_ms 钉死（前端徽标形态来源补齐）· 在飞 replay 500 根除（语义化 409+Retry-After 客户端可退避）· 回执 T-W2 联调链照登。

CLOSE 质量钉复跑（spec-wave verify / task lint 归档后复跑）：**照登：无实证**（本批 CLOSE 未执行 · 30/40 期间 ruff/graph-compile/pytest 证据见上表）。

## 四 · 偏差与 nit（如实照登）

1. **`model` 键不补（FP-1 裁定 · 非缺口）**：resume 全链无 model 来源 · 禁伪造钉死 · 前端零迁就兜底（web PR #61 已落 0/''）存续 · live 实证终帧无 model 键与钉案一致。
2. **20 R1 非阻塞观察项 O1–O3**：内容零阻塞未退回 · O2（`run_is_terminal` 复用疑问）回复在 30 invoke——判定面刻意用新谓词 `run_stream_closed`，挂起 replay 合法零 diff。
3. **resume 200 为 JSON 面非 SSE**：40 live 照登（响应携 replay cursor `:18` · 追帧走 replay 端点）——既有契约形态，非本 task 变更面。
4. **环境三坑留痕（40）**：langfuse 引号炸 port · NO_PROXY 裸 `::1` 同炸 · strategy 候选 env 追加口 `OPS_STRATEGY_EXTRA_CANDIDATE_CAPABILITY_IDS`——复跑须知照登。
5. **全量 5 既有环境红**：同名同因经 clean tree 对拍实证为基线红，与本 task 无关 · 未顺手收口（非范围）。

## 五 · 签录（闸态表与审查文链）

| 闸 / 环节 | 状态 | 文档 / 实证 |
|-----------|------|------------|
| HG-TASK-DRAFT | **approved** | 00 联调链委派令代录（T-W2 FP-1 报回 · web PR #61 · 2026-10-11） |
| HG-AUDIT-R1 | **approved** | 维护者签 2026-10-13 · 20 R1 落盘 PASS（内容零阻塞 · 锚点 9 行全实证 master `cff3660`） |
| HG-GRAPH-MODULES | **approved** | 维护者签 2026-10-13 · G-L1 预判与 20 R1 核对一致 · 30 按实判回写已落（`61094bf`） |
| 20 R1 审查 | **PASS** | 址A `docs/harness/reviews/task_hitl_resume_replay_contract_audit_R1_20261012.md`（O1–O3 非阻塞）· 址B `docs/audits/task-review/20261012_hitl-resume-replay-contract_r1.md` |
| 合并 | **MERGED** | PR [#248](https://github.com/Cyning12/ops-desk-api/pull/248) · squash `acac5e6` · 2026-10-13T03:40:29Z |

## 六 · 维护者验收 checklist（需人重新验收项）

- [ ] **在飞 replay 抽验（live）**：起服造在飞 run → `POST /lg-rag/replay` 实测 **409 + Retry-After: 2** · 语义化 body · 全程无 500。
- [ ] **终帧字段抽验**：HITL approve→resume → 沉降后 replay 终帧 `done{status:'resumed', latency_ms:int≥0, 无 model 键}` 逐键 · 帧 seq 连续。
- [ ] **沉降后主路径零回归抽验**：completed run replay 200 流式帧序正常 · 未知 run_id 404 · 非法 cursor 422。
- [ ] **40 附件抽查**：`docs/harness/invokes/by-task/hitl-resume-replay-contract/attachments/` 16 件与 TC5 结论一致。

## 七 · 资源清理与修订记录

- **本 CLOSE 不删任何东西**：交付分支 `task/hitl-resume-obs-drafts`（已 squash 合入 master `acac5e6` · 删除安全）移交 00/维护者统一清理；批量关账分支 `close/active-batch-20261017` 在役至关账 PR 合并。
- 无后续跟进义务：web 侧兜底已落（PR #61）· 去留由 web 仓自裁（40 已回执联调链）。

| 日期 | 说明 |
|------|------|
| 2026-10-17 | CLOSE 落稿（批量关账分支 `close/active-batch-20261017`）：验收终态承 30 invoke（RED `a30b3d3` → GREEN `e4a54d9` · 图谱 `61094bf` · 全量 1803 passed 零新增红）+ 40 invoke（TC5 live 对照 PASS · 附件 16 件）实证全录 · F-OBS-1/2 闭环 · FP-1 model 不补裁定照登 · 址B 审查文复制件引用（主会话落盘）· 质量钉复跑照登无实证 |
