# invoke · 30 · multi-replica-verify · 双轨实证实现（D2/D4 双进程 pytest + D1/D4 runbook + D3 清单）

| 项 | 内容 |
|----|------|
| **时间** | 2026-09-22 |
| **帽** | 30-implement（verify 轨 · 预期零生产码 —— 实做确认 app/ 零改动） |
| **task** | docs/tasks/active/task_multi_replica_verify.md（signed · HG-TASK-DRAFT/HG-AUDIT-R1=approved） |
| **上游** | docs/spec/multi-replica-verify/SPEC-multi-replica-verify_v1.md（signed · 8236747） |
| **分支** | task/multi-replica-verify（每次 commit 前 git branch --show-current 核验） |
| **required_invoke_hats** | 10,20,30,40（本快照为 30 项） |

## 开工闸（GATE_VERIFY · 真跑）

- npx spec-wave verify --target . --task docs/tasks/active/task_multi_replica_verify.md → **VERIFY: PASS**
  （HG-TASK-DRAFT approved · HG-AUDIT-R1 approved blocks 30 ✅ · HG-GRAPH-MODULES approved）
- pre-30 invoke 在案：invoke_20260922_10_task_* / invoke_20260922_20_task_audit_* ✓
- git branch = task/multi-replica-verify ✓（禁 master/main · 禁 push · 不签任何闸 —— 全程遵守）

## 形态落地（钉死契约逐条）

| 契约 | 落地 |
|------|------|
| P1 subprocess 双 uvicorn 真隔离 | tests/dualproc_server.py（子进程入口 · 确定性替身图换 LLM · 状态外置链路全真）+ tests/test_multi_replica_dualproc.py（module fixture 起两进程 · 动态端口 · 内容型就绪探针 · finally 杀进程 · 清库报数） |
| 归属先断言 FAIL 非 skip | assert_distinct_instances()（whoami pid/port 对拍）每个跨实例用例首句；变异①实证必挂 |
| LLM 替身诚实声明 | dualproc_server docstring + RUNBOOK + 报告 graph_substitution 字段三处同源：替身只换 LLM 编排，PG checkpoint/事件表/DbHitlStore/resume 驱动/配额计数全真 |
| D2 语义断言 | test_cross_instance_replay（A 起 B replay 逐帧对拍 seq 连续）· test_cross_user_replay_404（双侧 404）· test_concurrent_startup_setup_no_deadlock（并发首跑不死锁）· test_instance_attribution_and_config（前置配置断言 whoami 三开关） |
| D4 图真的续跑 | test_hitl_cross_instance_resume：A 挂起 → B 签名拉待办可见 → B 签名批准 → B resume 200 **且** state 非空 + answer 非空 + A replay 全程 seq 连续含 hitl.resumed(接 last_seq)/answer/done(resumed)；负路径 test_resume_wrong_thread_409 / test_resume_without_checkpointer_503（第三实例 C 无 checkpointer） |
| D3 清单 | docs/guides/GUIDE_process_local_state_boundaries_v1.md：8 条目 file:line 锚点 + fallback 缓存补录 + 全仓扫描基线（threading.Lock/模块级单例/ContextVar 逐条处置）兜底漏项；对照实证 test_budget_quota_amplification_across_instances（上限 2 · 总放行 4 > 2）+ test_runtime_scope_and_catalog_parity（scope 对拍 + 计数分家 + catalog 一致） |
| D1 runbook | scripts/acceptance/multi_replica_verify.sh/.py + multi_replica_compose.yml（双 service 别名共享专用库 opsdesk_mrv）+ multi_replica_Dockerfile/constraints.txt（增量镜像）+ nginx rr（无亲和）+ 自研 Python LB cookie-sticky（亲和）；报告 reports/multi_replica_verify/deploy_20260922_095547.yaml **16/16 PASS · exit 0** |
| 网关形态如实标注 | 报告 gateway_form：首选外部 Java 网关**未覆盖**（外仓 + 本仓无 Eureka 客户端）→ Eureka 条目「未覆盖待补」；nginx 为 SPEC 命名降级形态；亲和组归自研 LB（vanilla nginx 无 cookie 亲和）——三处分开标注不混 |
| 报告字段族 | 拓扑/网关形态/逐项 PASS-FAIL/命令/git sha 7cbbd28/镜像 sha256:33c37d…/recorded_at/清理数 ✓ |
| 验证卫生 | mr<hex>- 前缀 · 专用库 opsdesk_mrv（收尾 drop）· pytest 轨清库报数（末次 179 行/模块）· 报告零真实用户数据 |
| 变异检验 ×3 | ① MR_FORCE_SAME_PROCESS=1 → 归属断言必挂（8 failed · 「两实例同进程 pid=…」）；② MR_B_CHECKPOINTER_OFF=1 → 前置配置断言 + B resume 503 必挂（fail-closed 真值复现）；③ MR_BUDGET_SINGLE=1 → 「总放行 2 ≯ 2」必挂。恢复后（无 env）9/9 全绿 ×2 复跑 |

## 实做坑（30 真值 · 供 40/CLOSE 参考）

1. **dotenv 复活**：子进程 env pop 掉的开关会被 .env 重新注入（override=False 只认键存在）——关开关必须给**空串**。变异②/503 负路径首跑曾因此假 200，改空串后 503 真值复现。
2. **容器 pid namespace**：两容器 init 都是 pid 1 —— runbook 轨归属对拍用 name（pytest 轨 host 进程用 pid 真值）。
3. **Docker VM 时钟快宿主 8h**：+2h 邀请码一落地即「过期」401 —— 过期余量按天给（对齐 conftest days=1 先例）。
4. **镜像依赖层漂移**：ops-desk-api-api:latest（09-20 建）早于 langgraph 1.2/pybreaker；增量镜像 + constraints 钉宿主版本（镜像日 langgraph 1.2.12 实测 SSE 首请求挂起 + psycopg「another command is already in progress」；钉回 1.2.11 后复跑通过）。**这是验证基建事实记录，非被验证对象 bug（宿主版本全绿）。**
5. **nginx upstream_addr 是 Docker 网关 IP**（192.168.65.254:8101）非主机名 —— 归属头按端口尾段归一。
6. **容器 127.0.0.1 bind 坑**：端口映射到 eth0 非 loopback —— dualproc_server 加 --host（pytest 轨默认 127.0.0.1 · 容器 0.0.0.0）。

## 验证（真跑）

- pytest tests 全量：**1358 collected（1349 基线 + 9 新增）· 1354 passed · 3 failed = 基线环境性三红**
  （test_capability_http_adapter 代理 + test_chat_ws ×2，基线复跑同三红）；
  memory_embedding_backfill::test_reconcile_mismatch_marks_failed 首跑撞上已知 flaky，单文件复跑 15/15 绿 + 单条复跑 2/2 绿 + 全量复跑绿（区分完毕 · 非本波引入）
- 新文件族单跑：tests/test_multi_replica_dualproc.py **9/9 PASS**（~5s · 两进程起停稳定）
- ruff check app tests = **57（基线 57 · 零新增）**；新文件族 ruff 全绿
- ./scripts/graph-compile.sh **绿**（再生产生的 graph.json 日期翻滚已还原 · 图谱零义务按实判成立）
- git diff master -- app/ = **空**（零生产码钉死达成）；无 alembic 改动（迁移 diff 为空）
- diff 白名单：tests/ ×2 · scripts/acceptance/ ×7 · reports/multi_replica_verify/ ×1 · docs/ ×3（含本 invoke）

## B1 旧测影响面逐条回填（闸前置义务）

| # | 处置执行 |
|---|----------|
| 1 | 回归零改动：test_lg_rag_sse_resume/sse_hitl/hitl_resume_events 全绿（全量复跑）；跨实例断言纯新增在新文件 ✓ |
| 2 | 回归零改动：test_hitl/hitl_resume 全绿；409/503 跨实例版新增（断言形态复用 approval_loop 先例） ✓ |
| 3 | 回归零改动：capability 四文件全绿；/catalog /runtime 对拍与 budget 放大实证新增 ✓ |
| 4 | conftest 零改动（新 fixture 独立命名 dualproc · 子进程 env 隔离） ✓ |
| 5 | 既有 acceptance 脚本零改动；multi_replica_* 同形态新增 ✓ |
| 6 | reports/multi_replica_verify/ 新目录沿用字段族 ✓ |
| 7 | 新增义务全部落地（本 invoke「形态落地」表） · collected 1349 → 1358（+9） |
| 8 | 正交面回归零改动全绿 ✓ |
| 9 | 双进程基建零先例风险对策全部执行：动态端口 / 内容型就绪探针 / finally 杀进程 / HTTP 超时上限；起停稳定性实证（9 用例 × 多次复跑 + 3 轮变异跑零起停失败） |
| 10 | 零迁移 ✓（alembic 链未触） |

改编=0 · 删除=0 —— 与 B1 预期一致（无停手回炉项）。

## 阻断性 bug 扫描结论

实做/实证全程**未发现被验证对象的阻断性 bug**（坑 1-6 全是验证基建/环境层，就地记录并按 task 写明对策执行）；无需另开 fix task 的条目。

## 遗留（给 40 / CLOSE）

- 外部 Java 网关 + Eureka 注册条目**未覆盖待补**（外仓 · 本仓无 Eureka 客户端 · 已在报告/文档如实标注）
- runbook 轨结论时效：复跑入口 = ./scripts/acceptance/multi_replica_verify.sh（承 SPEC §7 ④）
- spec README 占位表移行 = CLOSE 流处理（task 钉死）
- 边界清单「处置建议」是建议不是承诺（承 SPEC §7 ③）
