# CLOSE：hitl-auto-resume-claim-race（2026-10-10）

> **task**：[`../done/task_hitl_auto_resume_claim_race.md`](../done/task_hitl_auto_resume_claim_race.md)（已归档 done/）
> **类型**：验收偏差收口（bugfix 性质 · 实证驱动 · T2 交付物的 live 偏差修正）
> **关账日期**：2026-10-10 · 帽位：CLOSE

---

## 一 · task 目标

auto 模式 decide 同秒即时认领路径**零 `stranded_checkpoint`**，auto 首跑无重试直达恢复成功；手动 resume 语义与既有测试面零 diff。源偏差=T2 验收 D1：decide 成功与台账 `hitl_auto_resume_triggered` 同秒（17:00:51），auto 首次认领起**连续 6 次** `ResumeError: stranded_checkpoint`（resume.py:244），补偿扫描（5s 周期）≈30s 后（17:01:23）自愈；手动 resume（分钟级人批延迟）从未触发。

## 二 · 根因实证

- **机制链（落库先于挂起）**：`app/ops/lg_rag/multi/nodes.py:1820-1822` 注释明示「落库先于挂起」——`_persist_hitl`（nodes.py:1610-1706）先把 pending 行写库，`interrupt()` 在 :1831 才抛 GraphInterrupt；LangGraph checkpoint（含 interrupt 元数据）落库在其后。故「pending 行可见（GET pending / auto 认领可查）**⇏** checkpoint interrupt 元数据可见」——两者时序差即竞态窗口。
- **窗口 transient 钉案**：auto 流 decide 同秒认领（router.py:242-254 → `schedule_auto_resume` → `_claim_and_execute` → `_execute_decided_resume` → `resume_hitl_run` → `aget_state`）读到「有 pending tasks · interrupts 全空」快照 → 命中 resume.py:236-248 `stranded_checkpoint`；同码面自愈（~30s 后 checkpoint 元数据可见）证明该 code 存在 **transient 形态**——resume.py:41-51 注释原钉「旧版本格式残留 · 永远恢复不了 → 409」的分类语义须留档重审（手动 409 对外语义不动 · 钉死契约 2）。
- **PG 探针**（langgraph 1.2.11 · langgraph-checkpoint-postgres 3.1.2 · 真 AsyncPostgresSaver 跨连接新连接模拟 resume 侧 aget_state）：interrupt 帧吐出后元数据跨连接即刻可见 → 平坦图 pregel/aput 层无可见性窗口；窗口=**落库→挂起间隙**（应用层时序），非 checkpoint 存储层缺陷。

## 三 · 选案 A 与 B/C/D 排除依据

**选案 A：认领后·执行前只读就绪校验（竞态化为「等下轮」）**——`_interrupt_metadata_visible(row)` 只读探针命中 stranded 判定快照（有 pending tasks · interrupts 全空）→ defer 等下轮补偿扫描，台账 `hitl_auto_resume_deferred`（记动作不记内容）；认领不写状态（FOR UPDATE SKIP LOCKED 锁随事务提交释放）→ defer 无需回滚；执行仍 `_execute_decided_resume` 同源（无状态恢复纪律 · FP-4）；零新表/迁移/SSE 事件/env。

- **B（grace delay）排除**：窗口绑「挂起完成」时序非墙钟——固定延迟不可靠（短了仍撞窗 · 长了每认领白付延迟）。
- **C（执行体内有界退避重试）排除**：放大失败面（FP-3）——窗口内仍刷 ERROR「HITL 自动恢复执行失败」（TC2 要求清零）；执行体内重试把竞态处置藏进唯一恢复路径，混淆 manual/auto 语义。
- **D（根因侧时序/store 认领写态）排除**：钉死契约 4 超面禁动（nodes.py/store.py diff 空实证）。

## 四 · 合并链

| 环节 | 实证 |
|------|------|
| 交付链 | `7022e20` 10 起草 → `b7639ce` 20 R1 审查文 → `2f91f67` 三闸代录 → `79b6485` **红测先行**（TC1/TC2 修复前 2 failed · D1 同形签名）→ `51e17ca` feat 方向 A 实现 → `ac7f635` 30 invoke + 图谱 hitl 行回写 → `2714092` 40 核验 invoke + task 自检回填 |
| PR | [#224](https://github.com/Cyning12/ops-desk-api/pull/224) · **MERGED · merge commit `11fb7e6`**（2026-10-10 · CI 绿） |
| 改动面 | `app/ops/hitl/auto_resume.py` +52（docstring 竞态校验段 + `_interrupt_metadata_visible` 只读探针 + `_claim_and_execute` defer 分支）· `tests/test_hitl_auto_resume.py` +158（TC1/TC2 + `_RaceWindow`/`_assert_zero_stranded_logs`）· 图谱 l1/01_modules.md:39 hitl 行备注 · 文档面；nodes.py/store.py/router.py/resume.py/T1 消费门/T4 guard diff 全空 · tests/test_hitl_resume.py diff 0 行（手动 409 语义存续） |
| 反回归 | B1 七文件 174 passed · 全量 pytest 1764 passed + 4 failed = 仓级基线钉案（capability_lookups×3 + lg_rag_multi×1 环境性 · .env PG 闸全进程渗入同源）零新增红 · ruff 触及面零新增 · graph-compile EXIT=0 |

## 五 · 40 核验结论与 live 实证

**40 核验七项全 PASS（独立复跑 · 不采信 30 自报）**，详见 [40 invoke](../../harness/invokes/by-task/hitl-auto-resume-claim-race/invoke_20261010_40_verify.md)：

- **红测时序证据**：git log 实证 79b6485（test）先于 51e17ca（feat）严格有序；detached worktree 单独检出 79b6485 复跑 2 failed（D1 同形签名）→ 无先修后测。
- **断言强度亲读非假绿**：TC1 窗口内零执行断言（`assert not attempted`）+ probes==1 + flip 后直达×1 + claimed×2/deferred×1 台账链 + 零 stranded caplog；TC2 真 HTTP decide(auto) + 真挂起 + 四键台账齐。
- **TC3 live 实证**（隔离库 opsdesk_tc3 · :8060 · 六 env 组 + auto + 5s 扫描）：台账链 `triggered×1 → claimed×1（直达执行）→ (compensated→claimed→deferred)×5 → approval_consumed×1 → token_issued×1 → token_verified×1 → HITL 恢复完成×1`——**零 stranded_checkpoint（grep count=0）· 零「HITL 自动恢复执行失败」· 恰好一次执行**。deferred×5 = 恢复在窗期（LLM 轮 ~25s）补偿扫描五轮重认领被探针（tasks 有 · interrupts 空）挡下不执行——**方向 A 机制本体 live 实证**，恰好挡住 5 次重复恢复（修复前 live D1 同场景即 6 连撞 stranded 的签名）；decide-同秒原始窗口本次未命中（误端点耽搁 44s · 如实登记），首认领直达亦合规。
- **留转 2-5 裁定**：not_interrupted 子窗口 live 未观测（维持窄判定不扩面）· 永久 stranded 观测路径（deferred 台账 ttl_remaining_s 3598→3578 逐轮递减留痕至 TTL）实证成立（FP-7）· 探针成本低频可接受 · PG 闸环境事实照登。

## 六 · 闸与审查文链

| 环节 | 文档 |
|------|------|
| 10 落稿 | `7022e20` · [10 invoke](../../harness/invokes/by-task/hitl-auto-resume-claim-race/invoke_20261010_10_task_draft.md) |
| 20 R1 审查 | `b7639ce` · [`docs/audits/task-review/20261010_hitl-auto-resume-claim-race_r1.md`](../../audits/task-review/20261010_hitl-auto-resume-claim-race_r1.md)（**PASS-WITH-NITS** · 零内容阻塞 · N-1~N-3 非阻塞：断言窗实延至 :260 / 台账键图谱回写义务 / 红测时序证据要求——40 核验第 7 项照登全过）· 码面锚点 8 处全亲读核真 |
| 人工闸 | HG-TASK-DRAFT / HG-AUDIT-R1 / HG-GRAPH-MODULES 三闸 approved（维护者授权 · 00 代录 2026-10-10 · `2f91f67`）· HG-PILOT-OPSDESK-GLAYER n/a |
| invokes | [`docs/harness/invokes/by-task/hitl-auto-resume-claim-race/`](../../harness/invokes/by-task/hitl-auto-resume-claim-race/)（10 落稿 / 20 审查 / 30 实现 / 40 核验 / 50 收口） |
| 上游偏差源 | `docs/acceptance/20261010_hitl-consumption-loop_local_acceptance.md` D1+项6（分支 `acceptance/20261010-hitl-consumption-loop` @ `f57b4ae`）· T2 task `docs/tasks/done/task_hitl_approval_consumption_auto_resume.md` |

## 七 · 验收图谱回写类

**已回写并入 PR #224**：`docs/_tech_graph/l1/01_modules.md:39` hitl 行备注已补「**hitl-auto-resume-claim-race（2026-10-10 · 方向 A）**：auto 认领后·执行前只读就绪校验 `_interrupt_metadata_visible`（命中 stranded 判定快照 → defer 等下轮 · 手动 409 对外语义零 diff）；台账 +`hitl_auto_resume_deferred`」——40 核验第 7 项 N-2 实证在册；graph-compile EXIT=0（graph.json generated_at 再生噪音 checkout 还原）。无独立验收文档面；wiki_delta=n/a。

## 八 · 学习要点

1. **红测先于实现的时序证据是 bugfix 类 task 的最强防线**：TC1/TC2 注入式红测落盘（`_RaceWindow` 窗口替身 · seam 注入）→ 修复前红跑（2 failed · 与 live D1 逐字同形签名）→ 实现 commit 严格在后（git log 父链有序 + detached worktree 单独检出红测 commit 复跑实证）——40 独立核验以 worktree 复跑为准，不采信 30 自报。
2. **`.env → load_dotenv` 使 PG 闸在 pytest 全进程 ON**（app/config.py:11）：仓根维护者调试用 .env 使 `LG_RAG_HTTP_CHECKPOINTER=postgres` / `LG_RAG_DELEGATION_TOKEN_MODE=enforce` 渗入测试进程——首轮 B1 4 红即探针宽判定撞真 PG 所致，窄化判定（无 pending tasks 交还执行侧）后零改动原样绿；基线 4 红同源自此。**测试作者须知此前提**。
3. **`saver.setup()` 新库首跑 idle-in-transaction 卡点**：全新库首跑 AsyncPostgresSaver.setup() 的 CREATE INDEX CONCURRENTLY 被本服务自身 login 期 idle-in-transaction 会话阻塞 3m30s → pg_terminate_backend（隔离库自身连接）后通——新库首跑须无长事务阻塞，live 核验启动器应含此排查路径。
4. **`logging.basicConfig` 缺失致裸 uvicorn 无台账**：TC3 起 :8060 服务时裸 uvicorn 不带 app 台账输出，须启动器显式 logging.basicConfig(INFO) 台账方可见——台账链断言（triggered/claimed/deferred/consumed/token）依赖此前提。

## 九 · 改进建议

1. **裸 uvicorn 台账可观测性（建议后续仓级 task）**：把 logging.basicConfig 初始化收进 `app/main.py`（或 lifespan 早期），使任意启动方式（裸 uvicorn / 启动器 / compose）台账口径一致——当前 live 核验必须依赖自写启动器才能看到 `hitl_auto_resume_*` 台账链，仓级收口后 40/验收脚本可省一层封装。
2. **仓级 verify 缺口基线**：`npx spec-wave verify` EXIT=2 BLOCKED（done/ 遗留档 reviews 缺口 · 仓级基线 · 主仓同）——照登不新增；建议另立 chore task 批量补登或 verify 配置标 baseline（承上一 CLOSE 同钉案）。
3. **not_interrupted 子窗口**：窄判定（tasks 空不判未就绪）本 task 刻意维持；若他日 live 首跑该子窗口可观测（首跑 not_interrupted 而非 stranded），另起 task 议扩面（本 task 钉死契约 4 禁动 nodes.py/store.py）。
4. **stranded_checkpoint 分类语义重审**：resume.py:41-51 注释钉「旧版本格式残留 · 永远恢复不了 → 409」，本竞态实证 transient 形态存在；手动对外 409 语义存续不动，但注释/分类语义建议随下次触及 resume.py 的 task 顺手修正表述。
