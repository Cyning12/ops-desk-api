# CLOSE：lg-rag-sse-run-worker ⨯ lg-rag-sse-disconnect-completion（co-CLOSE 合一档 · E3 Wave B RunWorker 与 SSE 解耦）（2026-10-17）

> **task（双 · 同批关账）**：[../done/task_lg_rag_sse_run_worker.md](../done/task_lg_rag_sse_run_worker.md)（新 · Wave B 承接 task · PR #250 收口）· [../done/task_lg_rag_sse_disconnect_completion.md](../done/task_lg_rag_sse_disconnect_completion.md)（旧 · Wave A 尝试 + TC5 停派史 · 正文冻结零修订）
> **类型**：传输架构（进程内 RunWorker + StreamSubscriber · freeze `lg-rag-sse-v1` 行为收口）+ 旧 task 史实关账（co-CLOSE）
> **关账日期**：2026-10-17 · 帽位：CLOSE（批量关账分支 `close/active-batch-20261017` · 关账 PR 待开 · TC-B10 co-CLOSE 验收由本档勾选）

---

## 一 · 任务信息

| 项 | 值 |
|----|----|
| task_slug | `lg_rag_sse_run_worker`（新）· `lg_rag_sse_disconnect_completion`（旧 · co-CLOSE） |
| 依据 | 维护者裁定 **E3 Wave B**（`docs/harness/invokes/by-task/lg-rag-sse-disconnect-completion/invoke_20261014_00_e3_wave_b_plan.md`）· 新 task 生成令（`invoke_20261014_00_e3_new_task_spawn.md`）· 升级留痕 E1–E4（`invoke_20261014_00_escalate_tc5.md`）· base master `9ee928c`（含 F-OBS-2 409 语义） |
| 问题 | 图执行绑死在 HTTP SSE 生成器生命周期：客户端断连 → generator close → cancel 挂起 `__anext__` → 后续帧（含 `done`）不落盘 → History 半截 + replay 永久 409 / 假「续看」（§10.3「断连尽量跑完」条文与实现张力 · 孤儿 run `22b65ce2` / web 联调 TC4 活样本在案） |
| 史实链（如实照登） | 旧 task Wave A（ASGI 钩路线：`is_disconnected` 轮询 → blocking `request.receive` 三抡）**TC5 live×3 FAIL**（R1/R2/R3 · live 均无 settle 落盘 · replay 120s+ 仍 409 · TC3 409 保护区 live 抽检均 PASS）→ 00 停派升级维护者（E1–E4 · `invoke_20261014_00_escalate_tc5.md`）→ 维护者裁定 **E3 Wave B（Worker/Subscriber 拆分）另立新 task** → 新 task 收口、旧 task 正文不再修订 → **本档 co-CLOSE** |
| 产品口径（钉死） | 部分回复可见（History 机读 running + 半截）· Worker 断连后继续跑完落普通 `done` · Worker 失败落 `error{stage:lg_rag.worker_failed}` · 「继续回复」= 同 thread_id 新 `/stream` 新 run（可选 `continue_from_run_id`）· **禁** HITL resume 充当续跑 · **禁** replay 隐式再调 LLM · 不 silent 新 event_type |
| 分支 | 新：`task/lg-rag-sse-run-worker`（base `9ee928c`）· 旧：`task/lg-rag-sse-disconnect-completion`（Wave A 码面**未 commit 未合并** · 零入库） |
| 帽链（新 task） | 10-task（R0–R5 early_stop · D1=A+B 代录授权在案）→ 20 R1 **PASS-WITH-NITS**（N1–N4 · 零内容阻塞）→ 三闸 approved（00 代录 · 维护者「确认并授权重新签 D1」）→ 30（B1 RunWorker+subscribe → B2 薄 → B3/B5 棒）→ 40 live TC-B6 PASS → PR #250 MERGED → **CLOSE（本档 · 与旧 task co-CLOSE）** |

## 二 · 交付

| 环节 | 实证 |
|------|------|
| PR（新 task） | [#250](https://github.com/Cyning12/ops-desk-api/pull/250) · **MERGED 2026-10-14T07:56:02Z · squash commit `56e4a9f`** · head `task/lg-rag-sse-run-worker` · 标题「feat(lg-rag): RunWorker 与 SSE 解耦（E3 Wave B）」 |
| 旧 task 交付 | **零合并交付（无 PR）**——Wave A 三抡码面（断连收尾 `done{disconnected}` + ASGI 钩）全程未 commit · TC5 live×3 FAIL 后废弃 · 正文冻结保留 FAIL 史 |
| 码面（新） | `app/ops/lg_rag/run_worker.py`（新 · RunWorker 进程内 asyncio.Task 持有 astream 只写 event_store · run_id 单飞租约）· StreamSubscriber 拆分（只读推 SSE · HTTP 断连只取消 subscriber 不 cancel worker）· `router.py` `/stream`：鉴权 → 分配 run_id → **先** start worker → **再** StreamingResponse(subscribe) · 失败落 `error{stage:lg_rag.worker_failed}` · 可选 `continue_from_run_id` 新 run 注入 partial 草稿 · 补偿 A 薄做（`list_open_runs` + `scan_orphan_runs_for_compensation` 补 `done{disconnected}` · 活跃 worker 跳过） |
| 裁定表（D1–D3 已签） | 旧 task：**D1=A-only** 裁定留档（2026-10-14 · 后被 E3 升级取代）· 新 task：**D1=A+B（B 主）** · D2=成功普通 `done` / 失败 `error{stage:lg_rag.worker_failed}` / 补偿可 `done{disconnected}` · D3=须同步开 web task |
| 测试面 | 红测先行可查 · `tests/test_lg_rag_sse_run_worker.py` 7 绿（含 TC-B3 HTTP 钉测 `test_tc_b3_continue_from_new_stream_zero_resume`：continue_from 新 run · resume 零调用 · replay 不调 LLM）· 30 触及 pytest 67 绿 → 40 复跑 **pytest 92** · ruff 触及绿 · graph-compile EXIT=0 · `spec-wave verify` PASS |
| 文档/图谱 | `docs/spec/agent-infra/05_lg_rag_transport_and_session_plan_v0.md` §10.3/§4.2 回写 · `docs/_tech_graph/l1/01_modules.md` 新 `run_worker` 模块行 + `l1/10_flow_lg_rag.*`（G-L1 升判 · HG-GRAPH-MODULES 再签后 30）· graph-compile EXIT=0 |
| invokes | 新：`docs/harness/invokes/by-task/lg-rag-sse-run-worker/`（`invoke_20261014_10_task_draft.md` / `_30_implement.md` / `_30_b3_b5.md` / `_40_verify.md` · attachments `tc_b6_*`）· 旧：`docs/harness/invokes/by-task/lg-rag-sse-disconnect-completion/`（`invoke_20261014_00_escalate_tc5.md` · 30/40 r1–r3 invokes · attachments `tc5_r*` FAIL 证据） |
| 审查文 | run_worker 址A `docs/harness/reviews/task_lg_rag_sse_run_worker_audit_R1_20261014.md` → 址B `docs/audits/task-review/20261014_lg-rag-sse-run-worker_r1.md`；disconnect 址A `docs/harness/reviews/task_lg_rag_sse_disconnect_completion_audit_R1_20261013.md` → 址B `docs/audits/task-review/20261013_lg-rag-sse-disconnect-completion_r1.md`（址B 复制件主会话落盘 · 址A 原件不动） |
| **CLOSE 增量** | 两 task 档同批归档 done/（状态行 CLOSED 回写 · 旧 task 修订记录 CLOSED 行照登史实）· 本档落盘于批量关账分支 `close/active-batch-20261017` · TC-B10 co-CLOSE 验收项由本档勾选 |

## 三 · 核验结论（验收终态摘要）

### 新 task（lg_rag_sse_run_worker · TC-B1–B9 全勾 · B10=本档）

| 验收项 | 结果 | 实证 |
|--------|------|------|
| TC-B1 断连仍跑完 | ✅ | 中途关客户端 → worker 仍前进 → DB 最终普通 `done`（无强制 disconnected）→ replay 200 含断点后半段 answer + 终帧 · 红测先行可查 |
| TC-B2 worker 失败 | ✅ | 落盘 `error` 且 `payload.stage==lg_rag.worker_failed` → `run_stream_closed==True` → replay 200 · History `terminal_status=error` + partial answer 仍在 |
| TC-B3 继续回复=新 run | ✅ | `continue_from_run_id` 同 thread_id 新 `/stream` 绿 · **HITL /resume 零调用零 diff** · replay 不触发新 LLM 补算（`test_tc_b3_continue_from_new_stream_zero_resume`） |
| TC-B4 真在飞 409 | ✅ | worker 写入中 replay **409+Retry-After** · 对 master/既有契约零回归（F-OBS-2 语义存续） |
| TC-B5 补偿 A | ✅ | worker 死掉/超时无终帧 → `scan_orphan_runs_for_compensation` 补 `done{disconnected}` → 不再永久 409（**不**依赖 ASGI disconnect 当主证） |
| TC-B6 live 40（旧 TC5 语义替换） | ✅ | 2026-10-14 · 真实 uvicorn :8051 中途断连 → **worker settle → DB terminal → replay 200 后半段 + 普通 done** · 409 抽检 PASS · continue_from 冒烟新 run · run `71d3cdfb…` · attachments `tc_b6_*` |
| TC-B7/B8/B9 | ✅ | §10.3/§4.2 与实现一致 · 图谱+flow 落盘 compile EXIT=0 · 触及路径 pytest/ruff 绿 · HITL 挂起/completed/resume 保护区零新增红 · D3 已提示同步开 web task（30 invoke 在案） |
| TC-B10 co-CLOSE | ✅（本档） | 本档显式双 slug 合一关账 · 旧 task 同批归档 done/ |

### 旧 task（lg_rag_sse_disconnect_completion · 史实照登 · 非验收面）

| 环节 | 终态 |
|------|------|
| TC1–TC4/TC7（Wave A 码面+文档） | 勾选（30 棒 · 红测绿 · §10.3+图谱落盘 · 相关面 73 passed）——但码面**未 commit 未合并**，随 E3 裁定废弃 |
| TC5 live | **FAIL ×3**（R1：无 settle · replay 120s+ 仍 409 → R2 `is_disconnected` 轮询 peek 假绿 live 未翻转 → R3 blocking `request.receive` 竞速 live 仍无 settle · 三抡 uvicorn 均无沉降日志 · DB 止于半截帧）→ 00 停派升级维护者 |
| 裁定 | 维护者选 **E3**（Worker/Subscriber 拆分另立 task）· 旧 task D1=A-only 留档 · 正文冻结不再修订 |

**CLOSE 质量钉复跑**（spec-wave verify / task lint 归档后复跑）：**照登：无实证**（本批 CLOSE 未执行 · 40 期间 verify PASS / pytest 92 / ruff / graph-compile 证据见上表）。

## 四 · 偏差 · nit 与经验钉（如实照登）

1. **经验钉一 · ASGI disconnect 不可作唯一沉降路径**：Wave A 三抡 live 实证——单测 mock 全绿而 live 断连信号始终未触达沉降（peek 轮询与 blocking receive 两形态均否）· 码面绿 ≠ live 绿 · 断连收尾须靠 worker settle + 补偿扫描，不靠请求生命周期钩子。
2. **经验钉二 · Worker/Subscriber 拆分优先（E3 Wave B 成立）**：执行生命周期与 SSE 订阅连接解耦后，断连天然不再杀死执行（HTTP 只取消 subscriber）；TC-B6 live 一次过，对照 Wave A 三抡 FAIL——架构解耦优于协议钩补丁。
3. **经验钉三 · web D3 后续闭环照登**：web 侧「继续回复 / 部分回复 CTA」后续 task `task_web_lg_rag_sse_continue_reply` **40 PASS**（web 仓在案 · api 侧零改动义务已尽）。
4. **旧 task 验收面处置**：TC1–TC4/TC7 勾选项对应码面未入库（零合并交付）——勾选为棒内实证留痕，不代表 master 行为；master 断连收尾语义由新 task（RunWorker settle + 补偿 A）承载。旧 task TC6（Wave B）D1=A-only 不适用 · 其语义由新 task TC-B6 重定义覆盖。
5. **30-R2 peek 假绿教训**：`test_asgi_disconnect_probe_settles_without_aclose` 单测绿而 live 未翻转——disconnect 探测类测试须 live 主证，单测只能作辅证（已写入新 task test_strategy_note）。
6. **多副本双 worker**：MVP 进程内单飞租约 · 多副本 DB 租约方案另立（对照 `task_multi_replica_verify` 边界 · FP-3 在册）。
7. **成本面**：产品默认「断连仍跑完」 · 断连即停+补偿可配（FP-4 显式策略面存续）。

## 五 · 签录（闸态表与审查文链）

| 闸 / 环节 | 状态 | 文档 / 实证 |
|-----------|------|------------|
| 旧 task 三闸 | **approved** | 维护者签 · 00 代录 2026-10-14（授权原话「统筹此任务，授权签收后续过程文档」· `invoke_20261014_00_gate_signoff.md`）· 20 R1 PASS-WITH-NITS（址A `task_lg_rag_sse_disconnect_completion_audit_R1_20261013.md`） |
| 新 task 三闸 | **approved** | 维护者签 · 00 代录 2026-10-14（「确认并授权重新签 D1」+ 过程文档签收权）· 20 R1 PASS-WITH-NITS N1–N4（址A `task_lg_rag_sse_run_worker_audit_R1_20261014.md`）· HG-GRAPH-MODULES 含 G-L1 新 `run_worker` 在册授权（升判再签后 30） |
| 审查文（址B 复制件） | — | `docs/audits/task-review/20261014_lg-rag-sse-run-worker_r1.md` · `docs/audits/task-review/20261013_lg-rag-sse-disconnect-completion_r1.md`（主会话落盘） |
| 升级链 | — | `invoke_20261014_00_escalate_tc5.md`（E1–E4）→ `invoke_20261014_00_e3_wave_b_plan.md` → `invoke_20261014_00_e3_new_task_spawn.md` |
| 合并 | **MERGED** | PR [#250](https://github.com/Cyning12/ops-desk-api/pull/250) · squash `56e4a9f` · 2026-10-14T07:56:02Z（旧 task 无 PR · 零合并交付） |

## 六 · 维护者验收 checklist（需人重新验收项）

- [ ] **断连跑完抽验（live）**：起服 → `/stream` 中途断客户端 → 等 worker settle → DB 普通 `done` · replay 200 补后半段 answer + 终帧（菜谱 `lg-rag-sse-run-worker/invoke_20261014_40_verify.md` · attachments `tc_b6_*`）。
- [ ] **失败路径抽验**：worker 失败 → `error{stage:lg_rag.worker_failed}` 落盘 · `run_stream_closed` 真 · History `terminal_status=error` 机读。
- [ ] **保护区抽验**：真在飞 replay 409+Retry-After · HITL `waiting_approval` 挂起 replay 200 · completed run 帧序零回归 · resume 路径零调用。
- [ ] **continue_from 抽验**：带 `continue_from_run_id` 新 `/stream` 新 run 绿 · replay 不触发 LLM 补算。
- [ ] **史实认知确认**：旧 task Wave A TC5 live×3 FAIL 停派 → E3 升级链（`invoke_20261014_00_escalate_tc5.md`）· 旧 task 正文冻结 · 本档 co-CLOSE 双 slug。
- [ ] **web D3 闭环确认**：web `task_web_lg_rag_sse_continue_reply` 40 PASS 在案（web 仓）。

## 七 · 资源清理与修订记录

- **本 CLOSE 不删任何东西**：分支 `task/lg-rag-sse-run-worker`（已 squash 合入 master `56e4a9f`）与 `task/lg-rag-sse-disconnect-completion`（零合并 · Wave A 码面未入库）移交 00/维护者统一清理；批量关账分支 `close/active-batch-20261017` 在役至关账 PR 合并。

| 日期 | 说明 |
|------|------|
| 2026-10-17 | CLOSE 落稿（co-CLOSE 合一档 · 批量关账分支 `close/active-batch-20261017`）：新 task 验收终态承 30/40 invoke（B1–B6/B3/B5 PASS · TC-B6 live · pytest 92 · verify PASS）实证全录 · 旧 task Wave A TC5 live×3 FAIL 停派升级史实如实照登（E1–E4 → E3 Wave B 另立）· TC-B10 由本档勾选 · 经验钉三条（ASGI disconnect 不可作唯一沉降路径 · Worker/Subscriber 拆分优先 · web D3 40 PASS）入 §四 · 址B 审查文复制件两件引用（主会话落盘）· 质量钉复跑照登无实证 |
