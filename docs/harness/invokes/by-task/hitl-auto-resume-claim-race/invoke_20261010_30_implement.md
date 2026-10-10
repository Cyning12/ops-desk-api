---
hat: 30
task_slug: hitl-auto-resume-claim-race
date: 2026-10-10
---

# Invoke：30 实现 hitl-auto-resume-claim-race（auto_resume 认领竞态 · decide 同秒首跑连续 stranded_checkpoint）

> **帽**：Harness 30-implement（实现） · **task**：`docs/tasks/active/task_hitl_auto_resume_claim_race.md`
> **分支**：`task/hitl-auto-resume-claim-race`（base = master `1117286` · 前序 7022e20 起草 / b7639ce 20 审）
> **纪律**：先复现再定方案（钉死契约 5 · N-3）· 最小面（钉死契约 4）· 手动 409 零 diff（钉死契约 2）· commit 拆 feat/test/docs · 只 add 自产文件

## 时序证据（红测先于实现 · 钉死契约 5 / N-3）

1. **23:33 前后**（本帽 session 内）：TC1/TC2 注入式红测落盘 `tests/test_hitl_auto_resume.py` 尾部（`_RaceWindow` 窗口替身 · seam=`auto_resume._interrupt_metadata_visible` raising=False 注入，修复前 seam 不存在则注入悬置、红在断言层）。此刻 git log HEAD=`2f91f67`（三闸代录），`app/ops/hitl/auto_resume.py` 零 diff。
2. **2026-10-10 23:42:54 +0800** 修复前红跑出：`pytest tests/test_hitl_auto_resume.py -k 'tc1_claim_race_window or tc2_auto_decide_chain'` → **2 failed / 39 deselected**，失败机制与 live D1 逐字同形：
   - TC1 红：`AssertionError: HITL 自动恢复执行失败 request=hitl_…`（ERROR 日志 auto_resume.py:182，exc=ResumeError stranded_checkpoint「窗口内：tasks 有 · interrupts 空」）+ 窗口内已执行（`attempted` 非空）。
   - TC2 红：decide 同秒首跑撞窗口 → ERROR 日志 + stranded_checkpoint，随后补偿扫描 `hitl_auto_resume_compensated` 重试轮才恢复 —— 即 D1「首跑 6 连撞 → 补偿扫描 ~30s 自愈」的注入式复刻。
3. **实现 commit 严格在后**：test `79b6485`（红测 · 单独检出时两枚红）→ feat `51e17ca`（实现）→ docs（本文件 + 图谱回写）——红测记录先于实现 commit，无先修后测。

## 根因实证（F2 前半）

- **机制链**：nodes.py:1820-1831「落库先于挂起」——HITL pending 行先落库可见，图挂起（checkpoint interrupt 元数据）后完成；故「行可见 ⇏ interrupt 元数据可见」。decide 同秒首跑认领后执行，aget_state 读到「有 pending tasks · interrupts 全空」快照 → resume.py:236-248 抛 `ResumeError: stranded_checkpoint`（raise 在 resume.py:244）。
- **live D1 实证**（验收文档项 6 · f57b4ae:docs/acceptance/20261010_hitl-consumption-loop_local_acceptance.md）：auto 首次认领起连续 6 次 `stranded_checkpoint`（17:00:51 与 decide 同秒），补偿扫描每 5s 重试，约 30s 后（17:01:23）恢复成功直达终链——**窗口 transient 钉案**（同码面自愈）；对照项 4 手动链（分钟级间隔）从未触发。
- **PG 探针**（langgraph 1.2.11 · langgraph-checkpoint-postgres 3.1.2 · 真 AsyncPostgresSaver 跨连接新连接模拟 resume 侧 aget_state）：interrupt 帧吐出后 interrupt 元数据跨连接即刻可见 → 平坦图 pregel/aput 层无可见性窗口，窗口=**落库→挂起间隙**（应用层时序），非 checkpoint 存储层缺陷。
- **注入式复现**（时序证据 2）：TC1/TC2 修复前红与 D1 逐字同形（ERROR「HITL 自动恢复执行失败」+ ResumeError stranded_checkpoint + 补偿扫描重试轮自愈）→ 根因钉在认领-执行间隙的元数据可见性窗口，非 resume.py 分类错误（手动 409 语义不动）。
- **副发现（测试环境事实）**：仓根 `.env` 经 app/config.py:11 `load_dotenv` 使 `LG_RAG_HTTP_CHECKPOINTER=postgres` 在 pytest 全进程生效——就绪校验窄形态判定（无 pending tasks 不判未就绪）使 B1 七文件零改动原样绿（InMemorySaver 挂起态在真 PG 不可见 → tasks 空 → 交还执行侧）。

## 方案裁定（F2 后半 · A/B/C/D 择一）

**选案 A：认领后·执行前只读就绪校验（竞态化为「等下轮」）**。

- **A 采纳理由**：窗口 transient 且下轮（补偿扫描/补触发）天然存在——不就绪时 defer 零成本；探针只读契合无状态恢复纪律（FP-4 · 钉死契约 1）；认领不写状态（store.py FOR UPDATE SKIP LOCKED 锁随事务提交释放）→ defer 无需回滚；零新表/迁移/SSE 事件/env（钉死契约 7）。
- **B（grace delay）排除**：窗口绑「挂起完成」时序非墙钟——固定延迟不可靠（短了仍撞窗 · 长了每认领白付延迟）；task 自判同结论。
- **C（执行体内有界退避重试）排除**：放大失败面（FP-3）——窗口内仍刷 ERROR「HITL 自动恢复执行失败」（TC2 要求清零）；执行体内重试把竞态处置藏进唯一恢复路径，混淆 manual/auto 语义。
- **D（根因侧：落库/挂起时序或 store 认领写态）**：钉死契约 4 超面禁动（nodes.py/store.py diff 空）。
- **窄形态判定**：仅「有 pending tasks ∧ interrupts 全空」（= stranded 判定快照）判未就绪；无 pending tasks（checkpoint 行未写入的 not_interrupted 子窗口）交还执行侧现状语义（扫描兜底不变）——留转 40 观测。

## 实现面（F3 · 钉死契约 4 最小面核对）

- **改动文件**：`app/ops/hitl/auto_resume.py`（feat `51e17ca`：+模块 docstring 竞态校验段 · +`_interrupt_metadata_visible(row)` 只读探针 · +`_claim_and_execute` defer 分支）· `tests/test_hitl_auto_resume.py`（test `79b6485`：+158 行 TC1/TC2 + `_RaceWindow`/`_assert_zero_stranded_logs`）· docs（本 invoke + 图谱回写）。
- **最小面核对**：`git status` 实证 nodes.py / store.py / router.py / T1 消费门 / T4 guard **diff 全空**；resume.py **零改动**（不重分类 · 手动 409 对外语义零 diff · tests/test_hitl_resume.py:230-259 原样绿实证）。
- **新台账键钉名（钉死契约 6）**：`hitl_auto_resume_deferred`（格式同三件套 `%s request_id=%s run_id=%s resume_mode=%s decision_by=%s ttl_remaining_s=%s` · 记动作不记内容）。
- **N-2 图谱回写**：docs/_tech_graph/l1/01_modules.md:39 hitl 行备注已补「hitl-auto-resume-claim-race（方向 A）就绪校验 + 台账 +`hitl_auto_resume_deferred`」，graph-compile 复跑 EXIT=0（graph.json generated_at 再生噪音已 checkout 还原）。
- **既有源码机断存续**：`test_trigger_carries_no_state_and_no_http_self_call`（模块级可变态白名单 {logger,_BACKGROUND_TASKS,_SCAN_TASK} · 源码无 httpx）与 `test_single_resume_path_in_router`（router 内 `await resume_hitl_run(` 唯一）原样绿——无状态纪律与单一恢复路径未被修复侵蚀。

## TC 逐项

| TC | 口径 | 结果 | 证据 |
|---|---|---|---|
| TC1 | 注入式竞态窗口复现（修复前红 → 修复后绿） | ✅ | 修复前红 23:42:54（2 failed · D1 同形签名）→ 修复后绿（`test_tc1_claim_race_window_defers_until_metadata_visible` PASSED：窗口内零执行+probes==1+deferred 台账×1 → flip 后直达×1） |
| TC2 | 修复后 auto decide-同秒链零 stranded_checkpoint | ✅ | `test_tc2_auto_decide_chain_zero_stranded_in_race_window` PASSED：全链 HTTP decide(auto) 首跑撞窗口 → deferred（窗口内图仍挂起零执行）→ 补偿扫描补触发直达恢复（hitl_unlocked_ids==[_T1]）；caplog/台账零「HITL 自动恢复执行失败」· 零 stranded_checkpoint · triggered/deferred/compensated/claimed 链齐 |
| TC3 | live 实证 auto 首跑无重试直达 | 留 40 | 30 不测 live（委派分工）；断言口径见留转 40 清单 1 |
| TC4 | 反回归（39 枚原样绿 + B1 七文件 + 全量基线 4 红零新增） | ✅ | B1 七文件 174 passed（含 test_hitl_resume.py:230-259 stranded→409 原样绿 · auto_resume 39 枚零改动绿）；全量 pytest 1764 passed + 4 failed = 基线钉案（capability_lookups×3 + lg_rag_multi×1）零新增红 |
| TC5 | 工程面（ruff / graph-compile / 再生噪音还原 / task lint） | ✅ | ruff 触及路径 All checks passed；graph-compile EXIT=0；uv.lock（nvidia marker 重写）与 graph.json（generated_at）再生噪音均 checkout 还原；`npx spec-wave task lint --file` PASS（W3 占位 warning=10 起草期既有不咬） |

## 过程留痕

- 2026-10-10 30 骨架先行落盘（本文件）。
- 23:33 前后 TC1/TC2 红测落盘 → 23:42:54 修复前红（2 failed）→ uv.lock 再生噪音还原 → 方向 A 实现 → TC1/TC2 绿 → 首轮 B1 4 红（probe 宽判定撞 .env PG 闸）→ 窄化判定（无 pending tasks 交还执行侧）→ B1 174 全绿 → 全量基线零新增 → N-2 回写 → test `79b6485` → feat `51e17ca` → docs（本 commit）。

## 留转 40 清单

1. **TC3 live 实证**（TC3 整项留 40）：六 env 组 + `OPS_HITL_AUTO_RESUME=auto` + `OPS_HITL_AUTO_RESUME_SCAN_INTERVAL_SECONDS=5` 起 live，decide 同秒 → 台账链预期 `triggered→claimed→（窗口命中则 deferred→compensated→claimed）→恢复完成`；**deferred 是方向 A 机制本体，非失败重试轮**——TC3 断言口径=零 stranded_checkpoint ERROR，若 live 窗口未命中则直达亦合规。
2. **not_interrupted 子窗口**：checkpoint 行未写入（tasks 空）时探针不判未就绪，保持现状语义（执行失败落日志+扫描兜底）——窄判定刻意为之；若 live 实证该子窗口可观测（首跑 not_interrupted），另起 task 议扩面（本 task 钉死契约 4 禁动）。
3. **真·永久 stranded 单在 auto 下**：每轮 deferred（INFO 台账）直至 TTL 耗尽——观测靠 `hitl_auto_resume_deferred`（FP-7）；manual 409 语义零 diff 未动（钉死契约 2）。
4. **探针成本**：每次 auto 认领多开一次 `apostgres_saver` 连接 + 一次 aget_state（认领低频可接受）；生产若观测连接压力再议。
5. **环境事实留档**：仓根 .env（维护者 live 调试）经 app/config.py:11 load_dotenv 使 PG 闸在 pytest 全进程 ON——后续 hitl 测试作者须知此前提；工作树未跟踪 jar 未动勿 add。

## 修订

| 日期 | 说明 |
|------|------|
| 2026-10-10 | 30 骨架先行落盘 |
| 2026-10-10 | 30 逐项回填完毕（TC1/TC2/TC4/TC5 全绿 · TC3 留 40）· test 79b6485 / feat 51e17ca |
