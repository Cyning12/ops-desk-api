# invoke · 10 · multi-replica-verify · task 落稿

| 项 | 内容 |
|----|------|
| **时间** | 2026-09-22 |
| **帽** | 10-task（SPEC signed 后落稿 · 本棒由 00 委派 10-task 帽 Agent 执行） |
| **文件** | `docs/tasks/active/task_multi_replica_verify.md` |
| **上游** | `docs/spec/multi-replica-verify/SPEC-multi-replica-verify_v1.md`（signed · HG-SPEC-SIGNOFF=approved 2026-09-22 · 8236747 · F1 双轨 + P1 subprocess 双进程 + 验证≠投产签收锁死） |
| **格式基准** | `docs/tasks/done/task_memory_compliance_delete.md`（真读对齐字段 · PR #163 已合 · CLOSE 归档） |

## 结论

**PASS（落稿）** · track=verify（预期零生产码）；范围 D1 部署验证（compose 双实例 + 前置网关 · 无亲和/会话亲和对照 · 混合负载两实例均有命中 · 报告如实标注网关形态 · 外部网关不可得时 Eureka 条目标未覆盖待补）/ D2 状态外置（**双进程 pytest** · subprocess 两 uvicorn 同 PG 异端口 · 每用例**实例归属先断言 FAIL 非 skip** · A 起 B replay 全程帧 seq 连续 · 他 user 404 · 续写同 run_id 接 last_seq · 前置配置断言 + 并发 setup 不死锁）/ D3 边界清单（≥8 条目 file:line 锚点 + budget 配额放大实证断言总放行 > 单实例上限 + `/runtime` scope 对拍 + `/catalog` 对拍 + 全仓模块级状态扫描基线兜底漏项）/ D4 HITL 跨实例（A 挂起 → B 见申请 → B 批准 → B resume **图真的续跑** state 推进 + answer 非空 + 帧续写 · 不只断 200 · 负路径 409/503 · runbook 轨复走）/ D5 图谱文档（零 alembic · 零新路由/一级模块/SSE 事件按实判 · app/ 零 diff · 发现 bug 另开 fix task）；非范围沿用 SPEC §3 九条；验收 **26 条**全否定性断言化逐块映射 SPEC §6（人工闸 1 / D1×5 / D2×5 / D3×3 / D4×3 / D5×3 / 变异检验×3 / 工程×3）· 与 SPEC 实质差异**零**；failure_paths **14 条**（SPEC §5 十条翻四列 + 双进程基建起停不稳 + 过程三）；R0–R5 全轮无 early_stop。

## 实扫留痕（本帽真跑）

- `git branch --show-current` = `task/multi-replica-verify` ✓（SPEC 签收 8236747 在链）
- checkpointer.py：单一开关 `LG_RAG_HTTP_CHECKPOINTER`（:27 进程级唯一真源）· `setup()` 幂等（:48-53 docstring「幂等，可每次传」复核一致）
- resume.py：fail-closed 503 `checkpointer_not_configured`（:329-336 复核一致）· 每次调用新开 `apostgres_saver(setup=True)`（:338）· 零进程内定位状态
- budget.py：`_SESSIONS` + 模块级锁（:51-56 复核一致）· `MAX_TRACKED_SESSIONS=512` 插入序淘汰（:62）
- registry.py：进程内单例 dict（:29/:32 复核一致）· 拒绝覆盖（:38-40）
- **双进程 pytest 零先例实证**：`grep -rnE 'uvicorn' tests/ --include='*.py'` = **零命中**（tests 全 TestClient 同进程形态 · subprocess 仅 test_capability_harness_cli 非服务进程）
- 验证形态先例：`ls scripts/acceptance/` = **15 脚本**（hitl_persistence_smoke.py/.sh · hitl_approval_loop.py/.sh 起停壳 + 纯 HTTP 断言 + 自清库先例在案）
- pytest 基线真跑：`python -m pytest tests --collect-only -q` = **1349 collected**（= 1333 基线 + memory-compliance-delete 16）
- B1 落盘 **10 行**（回归×5 · **改编×0 预期** · 新增×3 · 风险对策×1 · 迁移无×1 · 删除×0）；关键实证：无既有用例依赖「单实例」反向断言 → 改编面预期零钉死；用例计数 11 文件真跑（lg_rag_http 11 / lg_rag_sse_resume 10 / lg_rag_sse_hitl 10 / lg_rag_sse_stream 8 / hitl 20 / hitl_resume 19 / hitl_resume_events 13 / capability_gateway 32 / capability_idempotency 17 / capability_persistence_db 15 / admin_capability_observability 12）；checkpointer 关联守护 15 文件
- HG-GRAPH-MODULES 真值核验：**真读** `docs/_tech_graph/l1/01_modules.md`——模块表已建置（bootstrap 签 2026-07-16 · 签录链完整至 :93 memory-compliance-delete 行）· `lg_rag` 行 :27 · `hitl` 行 :31 · `capability` 行 :26（**进程内注册表**明示非跨进程注册中心）· `db` 行 :33（checkpoint 表 checkpoints/checkpoint_writes 同库不同表在案）· `api` 行 :20 → **预期无图谱新签义务按实判**（零新路由/零新一级模块/零新表/零新 SSE 事件）+ **偏离回炉补闸条款**钉死
- SPEC §1 锚点抽核**零语义偏差**

## 闸态

- `HG-TASK-DRAFT` = **落稿时待签**（00 验收代录/人签 · 本帽不签）
- `HG-AUDIT-R1` = **落稿时待签**（blocks 30 · 20 审后人签/授权代录）→ **30 拒开工**
- `HG-GRAPH-MODULES` = **approved（模块表已建置 · 本帽真读）** + 本 task **预期无新签义务按实判**（零新路由/零新一级模块/零新表/零新 SSE 事件）；偏离（新增观测端点/新路由/新表/新 SSE 事件/改被验证对象语义）→ 本闸转有义务回炉补闸
- `HG-PILOT-OPSDESK-GLAYER` = n/a

## lint

`npx spec-wave task lint --file docs/tasks/active/task_multi_replica_verify.md` = **PASS**（exit 0 · 2026-09-22 真跑）

## 下一棒

20-task-audit 书面审（对照 SPEC）→ HG-TASK-DRAFT + HG-AUDIT-R1 人签 → 30（`task/multi-replica-verify` · 承 SPEC §8 序：D2 双进程基建先行 → D4 HITL 双进程 → D3 清单+对照实测 → D1 runbook+实测 → D5 文档 · 铁律：双进程真隔离禁同进程双 app · 归属先断言 FAIL 非 skip · app/ 零改动发现 bug 另开 fix task · HITL 断言图真的续跑 · 报告含环境指纹）→ 40（变异检验三条 + 双轨证据核验）→ CLOSE。后续 20/30/40 invoke 由各棒落盘本目录（命名对齐 `invoke_<yyyymmdd>_<hat>_<verb>_multi_replica_verify.md`）。
