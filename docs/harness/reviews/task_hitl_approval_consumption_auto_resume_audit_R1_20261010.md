# Task 审查：hitl-approval-consumption-auto-resume（T2 · D5 自动 resume 可配置面 · R1）

> **审查帽**：20-task-audit R1（书面审 · 不实现 · 不改 task 实质）
> **审查对象**：`docs/tasks/active/task_hitl_approval_consumption_auto_resume.md`（draft · 2026-10-10 落稿）
> **对照基准**：SPEC v1（`docs/spec/hitl-approval-consumption/SPEC-hitl-approval-consumption_v1.md` · HG-SPEC-SIGNOFF=approved 2026-10-10 · spec 分支只读）
> **实证 base**：worktree 分支 `task/hitl-approval-consumption`（merge-base=master `4d905e0` ✓）
> **审查人**：Harness 20-task-audit（子 Agent · R1 · 2026-10-10）

---

## 结论摘要

| 维度 | 结论 | 说明 |
|------|------|------|
| **内容** | **PASS**（零内容阻塞 · 三非阻塞注记 N-1~N-3） | R2-N1/N2/N3 三钉全部实证成立；TB1–TB8↔A9/A10 映射闭环；T1 依赖链五处钉死 |
| **流程闸** | HG-TASK-DRAFT / HG-AUDIT-R1 / HG-GRAPH-MODULES 均 pending（属实时序 · 如实登记）+ **T1 未 merge 前置未满足**（T1 本审 FAIL 待 10-task 修复后再签 · 见 T1 审查文） | 见文末签闸清单 |

---

## 核对项

| # | 核对项 | 结论 | 实证 |
|---|--------|------|------|
| 1 | 范围承接：D5 可配置面（Q6 触发器 / Q7 双级配置）· FP-8~FP-11 · A9/A10（+ A5/A6/A7/A8 存续面） | ✅ | 与 SPEC §2 D5 / §4 Q6/Q7 / §5 FP-8~FP-11 / §6 A9/A10 逐块对上 |
| 2 | 非范围完备性 | ✅ | T1 面零改（缺口 GATE_STOP 回 10 不顺手改）· store 既有四方法 + `_DECIDE` diff 空 · OA 触发 · MQ/外部调度器（终局双弃）· UI/SSE · LLM 质量兜底 · 进程内存去重缓存——与 SPEC §3 对齐无漏 |
| 3 | **R2-N1 · 400/422 形态钉实现路径** | ✅ **实证成立 · 裁定正确** | 实读 `router.py:112-116`：`_DecidePayload.decision` 为 `Literal["approved","rejected"]`，docstring 明示「非法值由 Pydantic 直接挡成 **422**」——若 `resume_mode` 用 Literal/Enum，未知值必成 422，违 SPEC FP-10/A10 钉死的 **400**。裁定「`str`（缺省 inherit）+ 端点手工白名单 `HTTPException(400)`」是唯一干净路径；否案③（validator 抛 HTTPException）绕 FastAPI 校验语义，否决理由成立；docstring 注明双字段错误形态差异的要求防误读，到位 |
| 4 | **R2-N2 · 触发器挂点**（router decide 成功分支 · OA callback 不挂） | ✅ **实证成立** | 实读 `decide_request` :175-232：归属守卫 :193-200 → `adecide` :201-206 → 重复 409 :207-215 → 审计 :216-222 → 响应组装 :223-232——挂点「:201-216 成功分支之后、响应组装前」空间实证存在；派发不阻响应语义（实操-F）与该结构兼容。挂 store 层违 A7 diff 空（否决成立）；OA `callback`（:235-275 实读：HMAC 签名面 · 载荷 `dict` 无 `resume_mode` 面 · 同 `adecide` 守卫）不挂触发器的「签名面零 diff + 另立 task」处置成立 |
| 5 | R2-N2 与 D1「按单据不看来源」对称性论证 | ✅ 成立（推论见 N-1） | D1 消费门（T1）读 store 单据不区分 decide 来源（浏览器 decide 与 OA callback 写同一 store）→ 消费面对称；T2 触发器挂点不对称（仅 decide_request）有载荷/签名面实证理由，且补偿扫描四条件不看来源 → 全局面兜底对称性由扫描补齐（N-1 推论 task 未写明，注记之） |
| 6 | **R2-N3 · 行锁仓内无先例 → DbHitlStore 新方法 + InMemory 禁假断言** | ✅ **实证成立** | 20 亲跑 grep：`FOR UPDATE`/`SKIP LOCKED`/`for_update`/`skip_locked` 全 app/ 零命中——「仓内无先例」属实；`DbHitlStore` 既有四方法（:127-228 acreate/aget/alist/adecide）实读在册，新增认领方法 + 既有 diff 空的切法正确；「认领窗口内再查一次判定」防认领后条件已变，机制闭环；InMemory 无锁语义、行锁断言仅 Db 组（真 PG fixture 承 test_hitl_resume.py）+ InMemory 只承载状态机幂等断言——**禁假断言分组边界写进 TB2③**，可机断 |
| 7 | **实操-E · event_store 无 run 终态谓词 → 新增只读查询裁定留痕** | ✅ **实证成立** | 20 亲读 `event_store.py` 全部函数定义：persist_run_event(:26)/run_owner(:56)/last_seq(:78)/assert_run_owned(:93)/load_events_after(:104)/thread_owner(:142)/list_thread_activity_page(:161)/fetch_events_for_threads(:209)——**确无 run 终态谓词**；task 裁定「新增只读查询（事件表 done 帧或等价真源）· 30 留裁定 · 禁读进程内存态 · 禁以 checkpoint 存在性近似终态」处置正确且红线清晰 |
| 8 | 无状态恢复纪律（SPEC 设计纪律 6） | ✅ | 恢复路径同源（resume_request :377-430 恢复段实读：sink→resume_hitl_run→close→turns 依赖仅 row/thread_id）+ 触发器不载状态 + 禁 HTTP 自调 + 行锁即跨副本唯一真源（无进程内存缓存 · 非范围明示）——与 SPEC 红线逐条对上；TB2① grep/审查断言可机断 |
| 9 | lifespan 挂点与 manual 零创建钉 | ✅ | `main.py:12-16` 实读：现仅 `log_tracing_startup()` + `yield`——挂点空间实证；「manual 下扫描任务零创建」+ shutdown cancel + TestClient 8 文件面入 B1/实操-D，旧测不炸的硬条件识别正确 |
| 10 | 配置面 Q7（全局 env 非法回退 manual · 载荷缺键=inherit · 有效模式求解） | ✅ | 与 SPEC Q7 S1 裁定逐字对上；「既有调用不带该键行为同现状零 diff」+ TB6 字面零 diff 快照对拍，可机断 |
| 11 | 单次 decide 一次触发 + 不循环（FP-11） | ✅ | 第四条件「同 run 无未决 pending → 扫描跳过」是防循环的扫描面配套，机制推演闭环；TB5 台账 triggered==1 计数断言可机断 |
| 12 | failure_paths 推演（11 条） | ✅ | FP-8~FP-11 承 SPEC + 实操 A–G 七条来自锚点实读（422 漂移/挂点错位/InMemory 假断言/任务泄漏/终态真源/响应时序/lint），每条有断言或 diff 闸对应 |
| 13 | 思考轮 R0–R5 闭合 | ✅ | 控制表回填齐；early_stop=yes 理由（SPEC 裁定存续 + 四新裁定各有实证排除岔路）成立；R2 residual「run 终态真源无既有谓词 · 30 裁定留 20/40 复核」本审已复核实证（核对项 7） |
| 14 | 行为变更类 task「旧测 grep 影响面」checklist 项（K7） | ✅ | B1 表在册（7 行文件面 + TestClient lifespan 面），预期形态（原样绿/零创建/独立命名新用例）逐行可机断 |
| 15 | 人工闸表 / invoke 目录 / lint 闸 | ✅ | 三闸 pending 如实；`required_invoke_hats=10,20,30,40` 含 20 → 本审 invoke 落盘义务已履行；验收末行含 task lint + lint-wiki-delta |

## 锚点实读抽查

（20 亲读 worktree 分支 `task/hitl-approval-consumption` · merge-base=master `4d905e0` 与 task 声明一致）

| 锚点 | task 声称 | 20 实读结论 |
|------|-----------|-------------|
| `router.py:112-116` | `_DecidePayload` decision Literal → 422 · note 默认空 | ✅ 逐行一致（docstring 明示 422 · R2-N1 前提实证） |
| `router.py:175-232` | decide_request 段划分（守卫/adecide/409/审计/resume 块） | ✅ 逐行一致；「两步钉死 · 不自动 resume」docstring :184-186 实证（第四立案缺口属实） |
| `router.py:235-275` | OA callback 签名面 · 本波不挂触发器 | ✅ 逐行一致（HMAC `_require_signed` :247 · 载荷裸 dict 无 resume_mode 面 · 同 adecide 守卫 · 409 区分重复回调） |
| `router.py:377-430` | resume_request 恢复段（aget 404/409 → 空 unlock 409 → sink → resume_hitl_run → ResumeError 映射 → close+turns） | ✅ 逐行一致（:393-439 段划分精确 · 抽取复用面真实） |
| `router.py:319-374` | `_open_event_sink` + `_persist_resumed_turns` 两件套 | ✅ 实证（归属失败返 None + error 日志语义在案 · 自动路径原样继承可行） |
| `resume.py:285` | `resume_hitl_run(thread_id, approved, rejected, decided_by, update_sink)` 签名 | ✅ 实证（另有 checkpointer/graph_factory 可选参 · 测试注入面既有） |
| `store.py:127-228` | DbHitlStore 既有四方法 · 无行锁先例 | ✅ 四方法实读在册；全 app/ grep FOR UPDATE/SKIP LOCKED 零命中——「仓内无先例」属实 |
| `main.py:12-16` | lifespan 仅 log_tracing_startup + yield | ✅ 逐行一致（补偿扫描挂点空间真实） |
| `event_store.py:26-142` | 只读面无 run 终态谓词 | ✅ 实证（全文件 8 个函数定义逐枚核 · 无终态判定 · 实操-E 成立） |
| `hitl/persistence.py:61-77` | get/set/reset_hitl_store 测试隔离面 | ✅（T1 审查同轮实证 · store 预置装配路径真实） |
| `tests/conftest.py` + TestClient 面 | lifespan 经 TestClient 触发 · manual 零创建为硬条件 | ✅ conftest 实读；实操-D 识别正确（另注：conftest :12-16 有 CI「skip 绿」已知缺口登记 · 与本 task 无关不展开） |

## TB1–TB8 ↔ SPEC A9/A10 映射核对

| task 验收 | SPEC | 核对结论 |
|-----------|------|----------|
| TB1 auto 全链 done{completed}（triggered 台账 + 消费放行 + 终态 · live 留 40） | A9 | ✅ 一致（handoff 验收令「A1 第四段补全实录」承接在案 · 依赖表 handoff 令行对上） |
| TB2 无状态恢复钉死组五子项（只读事件表 grep 断言 · 补偿幂等 · 行锁 Db 组 · 400 非 422 · 非法 env 回退） | A10 | ✅ 全覆盖且分组边界（Db/InMemory）钉死 |
| TB3 防重（并发双 decide 409 + 触发/扫描并发仅一执行 · claimed 计数） | FP-8 | ✅ 一致可机断 |
| TB4 崩溃兜底（未派发/任务丢弃 → 补偿补触发 · compensated 台账 · 真 PG 重启链 fixture） | FP-9 | ✅ 一致 |
| TB5 不循环（auto 后仍拦 → 回挂起 · triggered==1 · 扫描跳过未决 pending） | FP-11 | ✅ 一致 |
| TB6 manual/off 零 diff（resume 块字面快照 · spy 零后台任务 · lifespan 零创建） | A6 本 task 面 | ✅ 一致（D1 消费门面归 T1 TA5，划分正确） |
| TB7 反回归存续（store/registry/policy diff 空 · 手动 resume 抽取前后对拍 · deny 判死测绿） | A5/A7 存续面 | ✅ 一致（「恢复段抽取行为 diff 空 · 对拍」可机断） |
| TB8 工程面（pytest / ruff / graph-compile / 图谱 hitl+lg_rag 两行） | A8 本 task 面 | ✅ 一致（capability/strategy 行归 T1/T3 · main.py 挂点随 hitl 行备注的口径合理） |

## T1 依赖链核对

| 钉点 | 位置 | 结论 |
|------|------|------|
| 头部声明 | :6-7「分支 base=master **须含 T1 merge**」·「依赖 T1 merge 进 master 后方可 30」 | ✅ |
| failure_paths 首行 | 「T1 未 merge 即 30 → 拒开工（GATE_VERIFY 拦）」 | ✅ |
| 验收首条 | 「人工闸全 approved **且 T1 已 merge 进 master** 后方可勾选码项」 | ✅ |
| 依赖表首行 | 「T1（硬依赖 · 串行合并）」+ 机制理由（无消费→恢复后仍再拦 · 无 D2→resume 409） | ✅ 机制依赖论证与 T1 R1 拆分理由互洽 |
| 必读列表 | 第 1 条（GATE_VERIFY · T1 merge 核验）+ 第 10 条（T1 交付形态 done/） | ✅ |
| T1 侧互指 | T1 :7 拆分行 + 依赖表下游行 + 非范围 D5 行 | ✅ 双向一致 |

机制依赖实证复核：T2 TB1 全链的「自动恢复可达 done」确以 T1 消费放行 + unlock 回填为前提（无消费→恢复后 `_delegation_issue_block_reason` 仍拦 · 无 D2→resume 409 ——两条均为 T1 审查已实证的真代码路径）→ **串行合并是机制依赖不是偏好**，成立。

## 阻塞项 / 非阻塞项

### 内容阻塞项：无（PASS）

### 非阻塞注记

- **N-1（OA 批准单的补偿扫描推论未写明）**：补偿扫描四条件（approved ∧ 未过 TTL ∧ run 无终态 ∧ 同 run 无未决 pending）**不看 decide 来源**——OA `callback` 批准的单据在全局 `auto` 模式下虽不即时触发（OA 面不挂触发器），但会被补偿扫描补触发（延迟 ≤ 扫描周期）。即「OA 面本波不挂」的准确语义是「不即时」而非「全 manual」。此为 fail-safe 方向（批准了就会被恢复），无安全洞；建议 10-task 顺手在钉死契约 R2-N2 行或 R2 裁定二补一句明示该语义为预期（不改裁定 · 一行说明），避免 30/40 实测时误报「OA 面竟自动 resume 了」。
- **N-2（命名提示）**：建议认领方法名 `aclaim_approved_for_resume` 与 `capability/idempotency.py` 既有 `aclaim`（幂等认领）不同类同名、语义不同——不同类上可接受，仅提示 30 在 docstring 写明语义差异防误读。
- **N-3（建议值口径）**：扫描周期默认 60s 标为「建议值 · 30 可在域 [5,3600] 内调整并留痕」（R3 residual 已如实登记）——口径正确，维持。

## 回填清单

无（内容 PASS · 零阻塞）。N-1~N-3 为非阻塞注记：N-1 建议 10-task 顺手补一行语义明示（可与 T1 退回修复同批进行 · 不单独阻塞 T2 签收）；N-2/N-3 供 30 参考。

> 注意：T2 内容 PASS ≠ 可开工——30 前置为「三闸 approved **且 T1 已 merge**」。T1 本审 FAIL 待修复重签，T2 的 30 自然排在 T1 闭环之后，与本 task 依赖表一致。

---

## 维护者签闸（20 后 · 30 前）

- [ ] 已读 R1 审查结论
- [ ] 在 task 人工闸表将 HG-AUDIT-R1 改为 approved（维护者 · 日期）
- [ ] commit task 文档或确认已签
- [ ] 再下发 Harness 30 Prompt

30 Agent 将以 task 表为准；pending 时必须拒开工（见 TEMPLATE_30_gate_stop.md）。

---

## 修订

| 日期 | 说明 |
|------|------|
| 2026-10-10 | R1 骨架落盘（骨架先行 · 逐节增量）→ 全文填充：**内容 PASS（零阻塞 · N-1~N-3 注记）· 流程闸 pending 属实时序 + T1 merge 前置未满足** · 锚点 11 组实读 · TB1–TB8↔A9/A10 映射全对上 · T1 依赖链六钉点核齐 |
