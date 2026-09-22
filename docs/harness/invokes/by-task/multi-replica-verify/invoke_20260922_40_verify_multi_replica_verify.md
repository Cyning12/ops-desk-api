# invoke · 40 · multi-replica-verify · 核验（验收 26 条 + 变异复做 + 双轨证据亲核）

| 项 | 内容 |
|----|------|
| **时间** | 2026-09-22 |
| **帽** | 40-verify（核验 30 交付：5a21c43 + 643be11 + 6f4fd2f + dcb15b9） |
| **task** | docs/tasks/active/task_multi_replica_verify.md（signed · 验收 26 条 · B1 10 行） |
| **上游** | docs/spec/multi-replica-verify/SPEC-multi-replica-verify_v1.md（signed · 8236747）· 30 invoke（invoke_20260922_30_implement_multi_replica_verify.md） |
| **分支** | task/multi-replica-verify（每次 commit 前 git branch --show-current 核验 · 禁 master/main · 禁 push · 不签闸 · 不改实现码） |

## 总判定

**PASS · 验收 26/26 通过**（附注 2 项 + 观察项 1 条，均不阻塞 · 见「问题清单」）。30 自称逐条核验**无一虚报**；两处口径瑕疵（清单锚点 1 处偏 2 行 · 「全量复跑绿」在我环境未复现）如实记。

## 核验动作（全真跑留证据）

### 1. 全量 pytest + 基线 3 红对照（亲跑 ×3 + 基线 ×1）

- 分支全量 ×3：**1358 collected（= 1349 基线 + 9 新增 ✅）· 1353 passed · 4 failed · 1 skipped**（25.85s/28.04s/28.17s）。
- 基线对照（git worktree @ **d5234aa** = merge-base = local master · 补同 .env）：**1349 collected ✅ · 同 3 红**（test_capability_http_adapter 代理 + test_chat_ws ×2）· 全量 3 failed/1345 passed/1 skipped。
- 第 4 红 `test_memory_embedding_backfill.py::test_reconcile_mismatch_marks_failed` = **既有 flaky**：单文件 15/15 绿 · 单条 2/2 绿；失败机制读码 = **测试自身时序竞态**（并发插入与 backfill 扫描快照竞速 · 断言 `embedded==2` 实得 3 · 报告 status 仍 pass 侧）；基线全量 1/1 未触发、分支全量 3/3 触发（新增 9 用例改变套件时序/负载所致）；**app/ 零 diff（三点）亲核排除本波引入**。30 自称「全量复跑绿」在我环境 3 跑未复现 —— 如实记观察项（见问题清单①）。

### 2. 双进程测试亲跑 + 断言读码（D2/D4 核心）

- 亲跑 `pytest tests/test_multi_replica_dualproc.py`：**9/9 PASS ×2**（4.65s / 4.63s · 变异还原后复跑同绿）· 两进程起停稳定零超时。
- 归属先断言 FAIL 非 skip ✅：`assert_distinct_instances`（:166-177）用裸 assert（pid/port 对拍），非 skipif；每个跨实例用例首句调用（:366/:381/:404/:430/:454/:540/:640/:676）；变异①实证必挂（见动作 5）。
- resume「图真的续跑」断言链 ✅（test_hitl_cross_instance_resume :511-535）：`state` 非空 + `answer` 非空 + `replay.persisted` + A 侧全程 replay seq 连续 + `hitl.resumed` 存在且 **seq > last_seq_A**（:526-527 接 last_seq 实证）+ `done(status=resumed)` + 全帧同 run_id + 恢复段 answer 终帧非空 —— 不只断 200。
- whoami 归属指纹真值 ✅：`os.getpid()`（dualproc_server.py :198）+ 配置生效自证（`use_postgres_checkpointer()` / describe_hitl_persistence / describe_persistence 全真查询）。
- LLM 替身诚实声明 ✅：三处同源（dualproc_server docstring :10-23 · RUNBOOK · 报告 graph_substitution 字段）；替身只换 `astream_supervisor_agent`/`_default_graph_factory`，PG checkpoint/事件表/DbHitlStore/resume 驱动/配额计数全真（读码确认 :185-186）。

### 3. 部署报告亲读 + 脚本存在性（D1/D4 runbook 轨 · 未重跑 docker 全套 · 承 40 指令裁量）

- `reports/multi_replica_verify/deploy_20260922_095547.yaml` 亲读：**17 条 assertion = 16 ok:true + 1 ok:null（外部 Java 网关 + Eureka 注册 2 实例「未覆盖待补」）** —— 「16/16 PASS + Eureka 如实标注」自称属实 ✅。
- 网关形态三处分开不混 ✅：`gateway_form` 字段 = 降级 LB 双组（nginx rr 无亲和 :8199 · 自研 Python LB cookie-sticky 亲和 :8200）+ 首选外部 Java 网关未覆盖原因（外仓 + 本仓无 Eureka 客户端）；报告 :85 明示「**不得**把本降级形态读作网关验证通过」。
- 字段族齐 ✅：topology / commands / assertions 逐项 / git_sha=7cbbd28 / image_id sha256:33c37d… / recorded_at / cleanup_counts 10 表 / exit_code 0 / verdict pass。
- 脚本存在性 + 可执行性抽查 ✅：multi_replica_{verify.sh,verify.py,lb.py,compose.yml,nginx.conf,Dockerfile,constraints.txt} 7 文件在案；`bash -n` sh 语法 OK · `py_compile` py 语法 OK · 可执行位在。RUNBOOK（docs/guides/RUNBOOK_multi_replica_verify_v1.md）亲读：跑法/网关诚实标注/断言面/替身声明/验证卫生/复跑纪律六节齐全。

### 4. 边界清单亲读 + 锚点抽核（D3）

- GUIDE_process_local_state_boundaries_v1.md 亲读：8 条目判定总表（状态名/锚点/失真形态/既有自首/处置建议/实证六列齐）+ 对照实测定量记录 + 全仓扫描基线（13 行逐条「已盘点/不适用」处置 + fallback 缓存补录条目）+ 跨实例成立面对照表 ✅。
- 锚点抽核 **10 处，9 处精确命中**：registry.py:29-32/38-40 ✅ · budget.py:22-24/51-56/62/246 ✅ · circuit.py:71-72 ✅ · circuit_storage.py:45-47 ✅ · metrics.py:1-13 ✅ · idempotency.py:45-52 ✅ · hitl/persistence.py:28 ✅ · manifest.py:101,107 ✅ · fallback.py:94-96 ✅ · glossary.py:19 ✅ · llm/circuit.py:52-53 ✅。
- **1 处漂移**：条目 1 锚点写 `gateway.py:81`，实扫 `_registry = CapabilityRegistry()` 在 **:79**（偏 2 行 · 行号漂移非语义错 · 见问题清单②）。
- budget 放大实证读码 ✅（:633-668）：上限压 2（BUDGET_MAX_CALLS）· A×2 + B×2 总放行 4 > 2 · **A 侧第 3 次必须 budget_exhausted 拦回**（:665-668 证明上限本身生效非没开闸）；变异③钩子 :654-655 在码。

### 5. 变异检验①复做（40 亲跑）

- `MR_FORCE_SAME_PROCESS=1 pytest tests/test_multi_replica_dualproc.py` → **8 failed / 1 passed**（3.21s）：8 个跨实例用例全挂在归属断言 `assert 92856 != 92856`（两实例同 pid · :176）；唯一 passed = test_resume_without_checkpointer_503（不调归属断言 · 预期内）。与 30 自称「8 failed · 两实例同进程 pid=…」**完全一致** ✅。
- 还原（无 env）复跑 **9/9 全绿** ✅ · `git status` 工作树净 ✅。
- 变异②③ 未由 40 复跑（指令裁量复做 1 条）；钩子读码在案（② MR_B_CHECKPOINTER_OFF :206-212 dotenv 空串对策 · ③ MR_BUDGET_SINGLE :654-655）+ 30 留痕（② 前置配置断言 + B resume 503 必挂 · ③ 总放行 2 ≯ 2 必挂 · 恢复 ×2 全绿）。

### 6. 工程面亲核（ruff / graph-compile / diff / B1）

- `ruff check app tests`：**57 = 基线 57**（基线 worktree 同跑对照）· 零新增 ✅。
- `./scripts/graph-compile.sh`：**exit 0 绿** ✅；再生 `docs/_tech_graph/shared/graph.json` 日期翻滚已 `git checkout` 还原 · 工作树净 ✅。
- app//alembic/ 零 diff 亲核 ✅：`git diff master -- app/ alembic/` = **0 行**（local master = d5234aa = merge-base）；三点 `git diff origin/master...HEAD -- app/ alembic/` = 0 行。**口径说明**：`git diff origin/master`（两点）非空纯因 origin/master 已前进至 07b0eba（memory-fusion-weight-tuning a0ae03d 等 8 commits 不在本支）· 非本波改动。
- diff 白名单亲核 ✅（`git diff --name-status d5234aa...HEAD`）：tests/×2 + scripts/acceptance/×7（全 multi_replica_* 新增 · 既有脚本零触碰）+ reports/×1 + docs/（含 README 索引 1 行 M）—— 与 task 钉死白名单完全吻合。
- B1 抽核 5 条 ✅：#4 conftest 零 diff（0 行）· #5 acceptance 既有脚本零改动（name-status 无非 multi_replica 项）· #1/#2/#3 相关测试文件在全量跑中全绿（仅 3 基线红 + 1 flaky · 均不在 B1 面）· #10 alembic 零 diff ✅ · #7 collected 1349→1358（+9）属实 ✅。
- Eureka 自称核验 ✅：`grep -rni eureka app/` = 0 命中（网关在外仓属实）。

## 验收 26 条映射（全 PASS）

| 块 | 条目 | 判定 | 证据 |
|----|------|------|------|
| 闸 | HG-AUDIT-R1 approved 后方勾码项 | ✅ | task 闸表 approved · 30 合规开工 |
| D1×5 | compose 双实例+网关形态标注 / 无亲和对照 / 会话亲和 / 混合负载两实例命中 / 报告字段族 | ✅×5 | 报告亲读（动作 3）· 脚本存在性 |
| D2×5 | 双进程 fixture+归属先断言 / A 起 B replay seq 连续 / 他 user 404 / 续写同 run_id 接 last_seq / 前置配置+并发 setup 不死锁 | ✅×5 | 亲跑 9/9 ×2 + 读码（动作 2） |
| D3×3 | 清单 8 条目锚点 / budget 放大+scope+catalog 对拍 / 扫描基线兜底 | ✅×3 | 亲读+抽核（动作 4 · 附注锚点 1 处偏 2 行） |
| D4×3 | 图真的续跑 / 409+503 负路径 / runbook 轨实测 | ✅×3 | 亲跑+读码（动作 2）· 报告 D4 五条 ok:true（动作 3） |
| D5×3 | 零 alembic+graph-compile 绿 / app/ 零 diff / 文档落盘（README 移行留 CLOSE） | ✅×3 | 动作 6 |
| 变异×3 | ① 归属可检 40 亲复做 / ② 外置可检 / ③ 失真可检 | ✅×3 | ① 亲跑 8 挂→还原绿（动作 5）；②③ 钩子读码+30 留痕 |
| 工程×3 | B1 闸前置逐条处置 / 全量 pytest+ruff / diff 白名单 | ✅×3 | 动作 1/6（附 flaky 观察项） |

## 问题清单（如实记 · 均不阻塞验收）

1. **flaky 观察项**：`test_reconcile_mismatch_marks_failed` 在分支全量语境 3/3 触发红、基线全量 1/1 未触发、单跑 3/3 绿；机制 = 测试自身时序竞态（并发插入 vs 扫描快照 · `embedded==2` 实得 3）；app/ 零 diff 排除本波引入；30 自称「全量复跑绿」系时序运气。**建议**：后续开 fix/测试加固 task 用显式屏障替代隐式时序假设（非本 task 范围 · 不顺手修钉死）。
2. **清单锚点漂移**：GUIDE 条目 1 `gateway.py:81` 实为 :79（偏 2 行 · 行号漂移非语义错 · 建议 CLOSE 或下次触碰时顺手校正）。
3. **变异②③** 40 未亲复跑（指令裁量 1 条 · 钩子读码 + 30 留痕兜底）；若 CLOSE 要求全三条亲跑可补。
4. **Eureka 未覆盖待补**（承 SPEC §7 ② 残余风险 · 报告/runbook/清单三处如实标注 · 不阻塞）。

## 分支铁律自查

全程 `task/multi-replica-verify`（每次 commit 前 `git branch --show-current` 核验）· 未切 master/main（基线对照走 git worktree /tmp/ops-desk-mrv-baseline @ d5234aa + 补同 .env）· 未 push · 未签任何闸 · 未改实现码（本帽 diff 仅 docs/）。基线 worktree 用后已清理。

## 遗留（给 CLOSE）

- 问题清单 1-4 承上；spec README 占位表移行 = CLOSE 流处理（task 钉死）。
- runbook 轨结论时效：复跑入口 ./scripts/acceptance/multi_replica_verify.sh（承 SPEC §7 ④）。
