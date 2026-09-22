# Task：L0 多副本验证（单实例 → 多实例）（track=verify 预期零生产码）· F1 双轨实证（双进程 pytest 进 CI + runbook+reports 手工实测）· P1 subprocess 双 uvicorn 真隔离（禁同进程双 app 假跨实例）· D2 状态外置（A 起 B 恢复/查询 · 跨 user 404 · 实例归属先断言 FAIL 非 skip）· D3 进程内状态边界清单 8 条目 file:line 锚点 + budget 放大实证 · D4 HITL 跨实例断言「图真的续跑」不只断 200（multi-replica-verify）

> **状态**：`done`（2026-09-22 · 五棒全通 · 40 PASS 验收 26/26 · PR #165 CI 全绿合并 master（7541102）· CLOSE 归档 · 占位队列清零末棒）  
> **类型**：verify（验证/实证类 · **预期零生产码改动**——产物是验证方案 + 双进程集成测 + runbook/实测报告 + 进程内状态边界清单；**无 alembic 义务**（零 schema 改动预期 · 迁移 diff 为空断言）· **图谱义务预期无按实判**（零新路由/零新一级模块/零新表/零新 SSE 事件 · 偏离回炉条款见闸表与 graph_delta_note）；实扫发现阻断性 bug → 另开 fix task，不在本 task 顺手修）  
> **上游 SPEC**：`docs/spec/multi-replica-verify/SPEC-multi-replica-verify_v1.md`（**signed** · HG-SPEC-SIGNOFF=approved 2026-09-22 · 8236747 · F1 双轨 + P1 subprocess 双进程 + 验证≠投产签收锁死）  
> **分支**：`task/multi-replica-verify`（**禁止 master/main 直改 · 禁止 push**）  
> **10 注**：2026-09-22 · 本棒由 00 委派 10-task 帽 Agent 执行；HG-TASK-DRAFT / HG-AUDIT-R1 落稿时待签（10 帽不签）

---

## Harness 元信息

| 字段 | 值 |
|------|-----|
| **task_slug** | `multi-replica-verify` |
| **git_branch** | `task/multi-replica-verify` |
| **implement_repo** | `ops-desk-api` |
| **test_strategy** | `required` |
| **test_strategy_note** | **F1 双轨**（SPEC §4 裁决 · 不重演）：① **双进程 pytest 集成测**（pytest fixture 起两个独立 uvicorn subprocess · 同 PG DSN 异端口同 env 开关 · 每用例**实例归属先断言**（pid/端口对拍 · 归属断言失败 = FAIL 非 skip）· HTTP 断言 · 收尾杀进程）覆盖 D2 状态外置与 D4 HITL 跨实例核心语义（可 CI 可回归）；② **runbook + 手工实测报告**（compose 双容器 + 外部 Java 网关或降级 LB · `scripts/acceptance/` + `reports/multi_replica_verify/*.yaml` 留痕 · hitl_persistence_smoke / qdrant reconcile 先例同形）覆盖 D1 部署面亲和对照与 D4 部署轨；③ D3 边界清单逐条 file:line 锚点 + 对照实测（budget 配额放大实证断言 2 实例同 session 总放行 > 单实例上限）；变异检验三条（归属可检 / 外置可检 / 失真可检 · 见验收「变异检验」）；全量 pytest 绿（基线 **1349 collected** 真跑）+ ruff 零新增 |
| **code_quality_bar** | `L2_backend` |
| **graph_change_layer** | **预期无图谱义务（按实判）**（SPEC §2 D5）：产物为 tests/（双进程集成测）· scripts/acceptance/ · reports/multi_replica_verify/ · docs/（边界清单 + runbook 说明）——零新路由/零新一级模块/零新表/零新 SSE 事件类型（**本帽真读复核**见闸表 HG-GRAPH-MODULES 行与 R1）；若 30 形态偏离（验证本身需新增观测端点 · 实扫发现阻断性 bug 须改生产码 → 另开 fix task）→ 回 10-spec 修订 + 本闸转有义务 |
| **graph_delta** | 无（预期零图谱改动按实判 · 偏离回炉） |
| **graph_delta_note** | **回炉补闸条款**：若 30 阶段实现形态偏离预判（新增路由/观测端点 · 新增一级模块 · 新增表/列触发 alembic · 新增 SSE 事件类型 · 改 checkpointer/event_store/resume/capability 既有语义 · 顺手修被验证对象等 SPEC §3 非范围项），**不得沿用本裁定**——退回 10-spec 修订 SPEC + 10-task 补闸 + `docs/_tech_graph/` 如实登记后方可续 30 |
| **wiki_delta** | `n/a` |
| **wiki_delta_note** | 契约真值在 SPEC `multi-replica-verify`；D3 边界清单落 `docs/guides/`（或 spec 夹内）属本 task 范围项非 wiki |
| **review_hat** | `20` |
| **required_invoke_hats** | `10,20,30,40` |
| **invoke_retention_profile** | `default` |
| **experience_capture** | `recommended` |
| **kpi_aggregator** | `CLOSE` |
| **orchestration** | 单 task 直通：10 落稿 → 20-task-audit → HG-AUDIT-R1 人签 → 30（承 SPEC §8 序：D2 双进程基建先行 → D4 HITL 双进程 → D3 清单+对照实测 → D1 runbook+实测 → D5 文档）→ 40（变异检验三条 + 双轨证据核验 + app/ 零 diff）→ CLOSE |
| **freeze_id** | 无（不改 `lg-rag-sse-v1` / `lg-rag-http-v1` / `lc-evidence-http-v1`；零新 SSE 事件类型；零新路由预期） |

### 人工闸

| human_gate_id | status | blocks_hats | 说明 |
|---------------|--------|-------------|------|
| HG-TASK-DRAFT | approved | 20-R1, 30 | 2026-09-22 · 00 验收 10-task 稿通过（维护者本窗授权 00 签收过程文档 · 原话留痕 SPEC 状态行） |
| HG-AUDIT-R1 | approved | **30** | 2026-09-22 · 20-task-audit R1 PASS 零阻塞零退回（`docs/harness/reviews/task_multi_replica_verify_audit_R1_20260922.md` · 变异相容性核验成立 · B1 抽 5 亲跑）· 维护者本窗授权 00 代录签收 |
| HG-GRAPH-MODULES | approved | **30** | 2026-09-22 本帽**真读** `docs/_tech_graph/l1/01_modules.md`：模块表已建置（bootstrap 签 2026-07-16 · 签录链完整至 :93 memory-compliance-delete 行）；`lg_rag` 行 :27（checkpointer/事件表/replay 在案）· `hitl` 行 :31（resume 驱动 + 申请落库）· `capability` 行 :26（**进程内注册表**明示非跨进程注册中心）· `db` 行 :33（checkpoint 表 checkpoints/checkpoint_writes 同库不同表已在案）· `api` 行 :20 均在表。SPEC §2 D5 判**预期无图谱义务按实判**：零新路由/零新一级模块/零新表/零新 SSE 事件——无新签义务，**不阻塞 30 开工形态预判**；**若 30 形态偏离（新增观测端点/新路由/新表/新 SSE 事件/改被验证对象语义）→ 本闸转有义务回炉补闸**（见 graph_delta_note，不得沿用本裁定） |
| HG-PILOT-OPSDESK-GLAYER | n/a | 物理分层试点改码 | 本 task 不涉物理分层试点 |

---

## 背景与目标

现状（SPEC §1 实扫锁死 · 2026-09-22 本帽复核一致）：L0 鉴权/租户/Principal 代码构造 ✅，Java 网关+Eureka 在**外部仓**（本仓 grep eureka/zuul/ribbon 零命中），**但单实例，多副本未验证**（上游手册 L0 ⚠️ · 边界纪律：不说成「已做服务发现与多副本」）。状态外置在代码层面已有设计（PG checkpointer / 事件表 / DB 幂等 / DB HITL store），但「设计了」与「实证成立」之间隔着一整类静默错：配置漂移（A 开 B 关）、双写口径、进程内计数失真未被发现。

一句话目标（SPEC 锁死）：实证回答「这个系统跑两份成不成立」——**双进程 pytest**（P1 subprocess 双 uvicorn 真隔离）断言状态外置核心语义（A 起 run · B 恢复/查询/404 · A 挂起 · B resume 续写同 run）+ **runbook + 手工实测报告**覆盖部署面（2 容器 + 网关 · 会话亲和/无亲和对照）+ 产出**进程内状态边界清单**（8 条目逐条 file:line 锚点 + budget 放大实证 + 全仓扫描基线兜底漏项）；预期零生产码改动，发现阻断性 bug 另开 fix task。

设计纪律（30 不得违反 · 承 SPEC §1/§2/§4 签收锁死）：

1. **验证 ≠ 投产**：本 task 产物是验证方案 + 实测证据 + 边界清单，不是生产多副本改造（生产切换/灰度/回滚预案另案）；实扫/实证发现阻断性 bug → 如实记 FAIL + 证据 → **另开 fix task**，本 task 不顺手修被验证对象（顺手修 = 证据失效）。
2. **双进程真隔离铁律（P1 裁定 · P2 弃选钉死）**：pytest fixture 起两个独立 uvicorn subprocess（同 PG DSN · 异端口 · 同 env 开关）；**同进程双 app 实例是假跨实例**（模块级单例 registry/budget/circuit 全共享 · 失真断言全部空真）——禁止。
3. **实例归属先断言铁律**：每个跨实例用例先断言请求确落不同进程（pid/端口注入响应头或启动 banner 对拍），再断言语义；**归属断言失败 = 用例 FAIL 而不是跳过**（防「没真跨实例」头号静默错）。
4. **HITL 断言链覆盖「图真的续跑」**：「看起来批了但什么都没发生」是已知最坏形态（resume.py :5-7 docstring）；断言必须到 state 推进 + answer 非空 + hitl.resumed/done 帧续写同 run_id，**只断 200 = 用例不合格**。
5. **网关形态如实标注**：首选外部 Java 网关（Eureka 注册 2 实例）；不可得时降级 compose 轻量 LB（nginx/haproxy round-robin），报告**如实标注用的是哪一种**——外部网关不可得时 Eureka 条目标「未覆盖待补」，**不得把降级形态写成「网关验证通过」**。
6. **报告字段族含环境指纹**：拓扑 · 网关形态 · 各断言 PASS/FAIL · 命令 · 关键输出摘录 · git sha · 镜像 digest · recorded_at（reconcile/backfill 先例字段族）；缺字段 = 报告不收。
7. **配置漂移防线**：两进程均 `LG_RAG_HTTP_CHECKPOINTER=postgres` + `OPS_HITL_PERSISTENCE=db`（+ `OPS_CAPABILITY_PERSISTENCE=db` 对拍面）；用例前置断言配置生效（防「开关没开测了个寂寞」）；runbook 拓扑检查项含两实例 env 对拍与镜像 digest 一致（stranded_checkpoint 409 证明版本漂移真实）。

---

## 现状锚点（只读 · 30 必读 · 10 已复核 · 承 SPEC §1）

| 主题 | 路径 · 锚点 | 现状（本帽复核结论） |
|------|-------------|----------------------|
| PG checkpointer | `app/ops/lg_rag/checkpointer.py` | 单一开关 `LG_RAG_HTTP_CHECKPOINTER=postgres`（:27 进程级唯一真源 · 默认关 · 本帽复核一致）；DSN 由 settings.database_url 转 psycopg（:41-43 · 与业务表同库不同表）；`setup()` 幂等可每次传（:48-53 docstring 复核一致）；HTTP invoke 与 SSE 同一把闸（:25-27）——**跨实例前提 = 两副本同开关同库同版本** |
| SSE 事件表 | `app/ops/lg_rag/event_store.py` | 事件落 `ops_lg_rag_run_events` 每帧独立 commit（:34-47）；归属按 user_id 反查（`run_owner` :50-69 · 跨用户 replay → `LgRagRunNotFoundError` 404 :87-95）；`last_seq` :72-84 供恢复段接着编号——事件表天然跨实例可读 |
| HITL resume 驱动 | `app/ops/hitl/resume.py` | **A 挂起 B resume 结构上天然成立**：定位靠 thread_id → PG checkpoint（:16-17）；驱动器零进程内定位状态（每次调用新开 `apostgres_saver(setup=True)` :338 · 本帽复核 :329-340 一致）；未开 PG 开关 **fail-closed 503**（`checkpointer_not_configured` :329-336）；`stranded_checkpoint` 409（:236-248 · 版本漂移实证必查项）；恢复段事件续写同 run_id 接 last_seq |
| capability registry | `app/ops/capability/registry.py` | 进程内单例 dict（:29/:32 本帽复核一致）；注册仅发生在启动 import 路径（拒绝覆盖 :38-40 复核一致）；admin/capability.py 五端点全 GET 只读零运行时注册端点 → 同镜像同 env 各副本一致，实证形态 = 两实例 `/catalog` 对拍 |
| budget per-session | `app/ops/capability/budget.py` | `_SESSIONS` + 模块级锁进程内计数（:51-56 本帽复核一致）；`MAX_TRACKED_SESSIONS=512` 插入序淘汰（:62 复核一致）；`snapshot()` 显式 `scope: process-local`（:246）——**多副本失真：配额按实例数放大 · 跳实例重置**（对照实测否决面） |
| kill switch / circuit / metrics | `budget.py` :83-85 · `circuit.py` :72/:317-325 · `circuit_storage.py` :45-47 · `metrics.py` :1-13 | kill switch 每次读 env（副本一致性 = 部署 env 一致性）；pybreaker 进程内 `_BREAKERS` · 默认 mock-unavailable → process-local(degraded)（A 熔 B 照打已知边界）；metrics 进程内各说各话（docstring 明示） |
| 幂等 / HITL store | `capability/persistence.py` :11 · `idempotency.py` :50-51 · `hitl/persistence.py` :7-12 | `OPS_CAPABILITY_PERSISTENCE=db` → DbIdempotencyStore 跨实例防重（默认 null 不防重告警「不能上生产」）；`OPS_HITL_PERSISTENCE=db` → DbHitlStore 跨实例（默认 null 不落库告警）——**配置漂移（A=db B=null）= 防重/审批时有时无的静默错** |
| auth 会话 / SSE live | `models.py` :66-69 · `auth.py` :36-46 · `sse_stream.py` :20-22 | `ops_sessions` DB 存会话 → 鉴权天然无状态**无需会话亲和**；live 帧只在服务该连接的进程内，断连后 replay 走 PG 事件表 cursor 续传（非无缝 · 既有设计兜底） |
| 部署面 | Dockerfile · docker-compose.yml · `.github/workflows/deploy-api.yml` | compose api **单服务**（无 replicas/无 LB · db+qdrant）；**零 k8s 清单**；Java 网关+Eureka 在外部仓 → 网关面只能手工实测，不可得走降级 LB 如实标注 |
| 验证形态先例 | `scripts/acceptance/hitl_persistence_smoke.py/.sh` · `hitl_approval_loop.py/.sh` · `reports/qdrant_migrate/reconcile_p1_*.yaml` · `reports/memory_embedding_backfill/*.yaml` | .sh 壳起服务/等就绪/收尾杀进程 · 纯 HTTP 断言 · 自清库报清理数（本帽 ls 实证 15 个 acceptance 脚本）；报告字段族 + 计数守恒 + 双侧对账先例；**仓内双进程 pytest 零先例**（tests/ grep uvicorn 零命中 · 仅 TestClient 同进程形态 · subprocess 仅 test_capability_harness_cli 非服务进程）——D2/D4 双进程基建为本 task 新建形态 |
| 命名/路径冲突扫 | `grep -rn 'multi_replica\|multi-replica' app/ tests/ scripts/ docs/_tech_graph/` | 预期零命中（新测试文件名/脚本名/报告目录无冲突 · 落稿时真跑复核） |
| 测试基线 | `python -m pytest tests --collect-only -q` | **1349 collected**（2026-09-22 本帽真跑 · = 1333 基线 + memory-compliance-delete 16）；相关面用例计数见 B1 清单 |
| alembic 义务 | 无 | 零新表零列预期；迁移 diff 为空断言入 D5 验收 |

---

## 钉死契约（自 SPEC §2/§4 锁死；30 不得静默改义）

| 项 | 钉死 |
|----|------|
| **判定形态（F1）** | 双轨组合：核心语义（D2/D4）走**双进程 pytest** 进 CI 可回归；部署面（D1 + D4 runbook 轨）走 **runbook + 手工实测报告** `reports/multi_replica_verify/*.yaml` 留痕——两轨证据互补（pytest 证语义 · runbook 证拓扑下成立） |
| **隔离形态（P1）** | subprocess 两 uvicorn 进程（同 PG DSN · 异端口 · 同 env 开关 · HTTP 断言 · 收尾杀进程）；**禁同进程双 app**（P2 弃选钉死：模块级单例全共享 = 验证对象被测试形态架空） |
| **归属先断言** | 每用例先断言请求确落不同进程（pid/端口标识对拍）再断语义；归属断言失败 = **FAIL 非 skip**；runbook 混合负载 N 请求断言两实例均有命中（防「LB 只打到一个」） |
| **D2 语义断言** | A 起 run（interrupt 挂起或自然完结）→ B 经 checkpoint 读回 state / 经事件表 replay 全程帧（seq 连续 · 归属正确 · 内容一致）；B 以他 user replay A 的 run → 404（`assert_run_owned` 既有语义跨实例保持）；B 恢复段事件续写同 run_id 且 seq 接 last_seq（不重开 · 不覆盖） |
| **D4 语义断言** | A 挂起（interrupt → checkpoint 落 PG + hitl 申请落 DbHitlStore）→ B 见申请 → B 批准 → B resume **图真的续跑**（state 推进 + answer 非空 + hitl.resumed/done 帧续写同 run_id · 不只断 200）；负路径：B 错 thread_id → 409 not_interrupted；未开 checkpointer 实例 resume → 503 checkpointer_not_configured（fail-closed 跨实例保持） |
| **D1 部署断言** | 两实例健康且注册可见；登录态跨实例（A 登录 cookie 打 B → 200）；thread 历史跨实例一致；无亲和下同会话连续请求落不同实例且语义不漂移；会话亲和对照（网关支持时）同会话落同实例；混合负载两实例均有命中；报告如实标注网关形态 + 外部仓版本指纹 |
| **D3 清单形态** | 每条目 = 状态名 · file:line 锚点 · 多副本失真形态 · 既有自首（snapshot scope 字段/docstring）· 处置建议（现接受 / 何时须外置）；最小 8 条目（registry / budget / kill switch / circuit / metrics / idempotency / HITL store / SSE live）；对照实测 budget 放大断言（2 实例同 session 总放行 > 单实例上限）+ 两实例 `/runtime` scope 对拍 + `/catalog` 对拍一致；附全仓模块级进程内状态扫描基线（grep `threading.Lock`/模块级 dict 单例/`_LOCK` · 逐条已盘点/不适用标注）兜底漏项 |
| **app/ 零改动** | `git diff master -- app/` 为空；发现阻断性 bug → 报告「发现即另开 fix task」条目如实记 FAIL + 证据（复现步骤/日志/锚点），不在本波修 |
| **验证卫生** | 实测用专用租户/用户标识前缀（造了什么删什么 · 报告清理数 · hitl_persistence_smoke 先例）；双进程测用本地临时 PG schema 或专用库不碰共享开发库；报告不含真实用户数据/凭证 |
| **变异检验三条** | ① 归属可检（同进程跑 → 归属断言必挂）；② 外置可检（B 换 InMemorySaver/关开关 → 跨实例 resume/replay 断言必挂）；③ 失真可检（budget 实证收回单实例 → 「总放行 > 单实例上限」断言必挂）；恢复后全绿 |
| **图谱/迁移（D5）** | 零 alembic（迁移 diff 为空断言）；零新路由/零新一级模块/零新 SSE 事件；`./scripts/graph-compile.sh` 绿；偏离 → 回炉补闸 + SPEC 回炉 |
| **安全** | 无新凭证面/无新对外端点预期；写面限专用租户沙盒；验证以只读面为主（replay/catalog/runtime） |

---

## 范围（单 task 直通 · SPEC §2 D1–D5）

- [ ] **D1 · 多副本部署验证（必做 · runbook + 实测报告）**：compose 双实例拓扑可起（`deploy.replicas=2` 或双 service 别名 · 共享同一 db）+ 前置网关（首选外部 Java 网关 · 不可得降级 compose 轻量 LB 如实标注）；无亲和/会话亲和对照两组实测；断言面四项（健康注册可见 · cookie 跨实例 200 · thread 历史跨实例一致 · 混合负载两实例均有命中）；`scripts/acceptance/multi_replica_*.sh/py` + `reports/multi_replica_verify/deploy_<ts>.yaml` 落盘（拓扑 · 网关形态 · 逐项 PASS/FAIL · git sha/镜像 digest/recorded_at）
- [ ] **D2 · 状态外置实证（必做 · 双进程 pytest · 核心）**：双进程 fixture（两独立 uvicorn subprocess · 同 PG 异端口 · 归属先断言 FAIL 非 skip）；A 起 run → B replay 全程帧（seq 连续 · 归属正确）；B 他 user replay → 404；B 恢复段续写同 run_id 接 last_seq；前置配置断言（`LG_RAG_HTTP_CHECKPOINTER=postgres` 两进程生效）；两进程并发启动 + 同时 `setup()` 不死锁（启动竞态实证一次）
- [ ] **D3 · 跨实例一致性盘点（必做 · 边界清单文档 + 对照实测）**：清单落盘 `docs/guides/`（或 spec 夹内）≥ 8 条目逐条 file:line 锚点 + 失真形态 + 处置建议；budget 配额放大实证 + `/runtime` scope 对拍 + `/catalog` 对拍；附全仓模块级进程内状态扫描基线（逐条已盘点/不适用标注）
- [ ] **D4 · HITL 跨实例（必做 · 双进程 pytest + runbook 双轨）**：A 挂起 → B 见申请 → B 批准 → B resume 图真的续跑（state 推进 + answer 非空 + 帧续写同 run_id）；负路径 409/503；runbook 轨双容器 + 网关下同链路手工实测复走 · 报告留痕
- [ ] **D5 · 图谱 / 文档 / alembic（必做 · 按实判）**：零 alembic（迁移 diff 为空断言）；零新路由/零新一级模块/零新 SSE 事件；graph-compile 绿；边界清单落盘 + runbook 配套说明；app/ 生产码 diff 为空（发现阻断性 bug → 报告「发现即另开 fix task」条目）；spec README 占位表移行（done 后由 CLOSE 流处理）

**竖切结论**：D1–D5 同 task 一次提交（承 SPEC §8 序：D2 双进程基建先行 → D4 HITL 双进程 → D3 清单+对照实测 → D1 runbook+实测 → D5 文档收口）；语义断言不进 CI = 「验证过」随时间贬值成「曾经验证过」（F2 弃选理由钉死）；部署面不实测 = 网关面诚实性失守；清单无锚点 = 失真漏项无兜底。耦合面小（测试 + 脚本 + 报告 + 文档，零 app/ 预期），单 PR 可控。

### 非范围

- ❌ **真上生产多副本**（验证≠投产 · 生产切换/灰度/回滚预案另案）
- ❌ **服务发现选型变更**（Eureka 换 Nacos/k8s Service 等 · 现状盘点如实写，选型不动）
- ❌ **容量规划 / 灾备 / 多活**
- ❌ **进程内状态外置改造**（budget/circuit/metrics 改 DB/Redis 是修复动作非验证动作 · 本 task 只盘点与实证失真，改造另开 SPEC——circuit Redis 路径已设计未接同样不在本波接通）
- ❌ **Java 网关 / Eureka 代码改动**（外部仓 · 只在其实测可用时用它做拓扑，不可用走降级形态如实标注）
- ❌ **k8s 清单新建**（仓内零 k8s 现状 · 引入编排体系是投产动作）
- ❌ **生产码修复**（实扫/实证发现阻断性 bug → 记录证据 + 另开 fix task · 本 task diff 预期零 app/ 生产码）
- ❌ **SSE live 流跨实例无缝迁移**（断连 + replay 续传是既有设计兜底 · 无缝化另案）
- ❌ 前端/管理台 UI；历史文档回改

---

## failure_paths

| 触发条件 | 系统行为 | 可重试 | 用户可见 |
|----------|----------|--------|----------|
| `HG-AUDIT-R1` 未签即 30 | **拒开工** | 是 | 是 |
| B1 旧测影响面未落盘/未逐条处置即 30 交付 | **拒收**（闸前置 · 30 逐条执行处置并在提交说明逐条回填） | 是 | 是 |
| 验收缺归属先断言/双进程真隔离/A 起 B 恢复/404/续写 seq/配额放大实证/HITL 图真的续跑/报告环境指纹/变异检验三条任一 | **拒收**（防空真规则） | 是 | 是 |
| **假阳性「验证了但没真跨实例」**（测试形态共享进程内状态 / LB 实际只打到一个实例） | **静默错**（本 task 头号风险）；防线三层：① D2 禁同进程双 app（P2 弃选钉死）；② 每用例实例归属先断言（pid/端口对拍 · 归属失败 = FAIL 非 skip）；③ runbook 混合负载断言两实例均有命中；变异检验①兜底（同进程跑 → 归属断言必挂） | 是（修测试形态） | 是 |
| **进程内状态失真未发现**（budget 放大 / circuit 不共享 / registry 漂移 · 清单漏项） | **静默错**；D3 清单逐条 file:line 锚点 + 对照实测（配额放大断言总放行 > 单实例上限）；清单附全仓模块级状态扫描基线兜底漏项；既有 `snapshot() scope: process-local` 自首字段为对拍锚 | 是（补清单条目） | 否 |
| **配置漂移 A 开 B 关**（`LG_RAG_HTTP_CHECKPOINTER` / `OPS_*_PERSISTENCE` 两副本不一致） | resume 侧已有 fail-closed（503 不假装成功）；但 persistence A=db B=null = **防重/审批时有时无的静默错**；D2/D4 用例前置断言两进程配置生效；runbook 拓扑检查项含两实例 env 对拍 | 是（对齐配置重测） | 是 |
| **checkpoint 版本漂移**（两副本代码版本不同 · langgraph checkpoint 格式不兼容） | `stranded_checkpoint` 409 既有分支（resume.py :236-248 实测过 0.2→1.2 炸点）证明此风险真实；runbook 断言两实例镜像 digest 一致；实证报告记录版本指纹 | 否（排空在飞审批 + 对齐版本） | 是 |
| **HITL「看起来批了但什么都没发生」** | 已知最坏形态（resume.py :5-7）；D4 断言链必须覆盖图真的续跑（state 推进 + answer 非空 + hitl.resumed/done 帧续写同 run_id），**只断 200 = 用例不合格** | 是 | 是 |
| **双实例同时 setup() checkpoint 表** | `saver.setup()` 幂等（checkpointer.py :48,53 docstring · 本帽复核）；D2 前置两进程并发启动不死锁实测（启动竞态实证一次） | 是 | 否 |
| **双进程 fixture 起停不稳**（端口冲突 / 就绪等待超时 / 进程泄漏 · 仓内零先例新建基建） | CI 红 / flake 风险；对策：动态端口分配（不可用固定端口）+ 就绪轮询（healthz 超时上限）+ `finally` 杀进程树（收尾不泄漏）+ hitl_persistence_smoke .sh 壳起停形态参照；用例级超时上限防挂死 | 是（修基建） | 是 |
| **验证污染数据残留**（实测造的 thread/run/hitl 申请留库） | hitl_persistence_smoke 清库收尾先例（造了什么删什么 · 报告清理数）；实测用专用租户/用户标识前缀；报告含清理断言；双进程测用本地临时 PG schema 或专用库不碰共享开发库 | 是 | 否 |
| **网关不可用 / 外部仓版本不明** | 降级形态（compose 轻量 LB）顶上，报告**如实标注**网关形态与外部仓版本；Eureka 注册 2 实例条目标「未覆盖待补」；禁止把降级形态写成「网关验证通过」（D1 钉死） | 是 | 是 |
| **实测报告无法复核**（无命令/无输出/无环境指纹） | 报告字段族对齐 reconcile/backfill 先例：命令 · 关键输出摘录 · PASS/FAIL · git sha · 镜像 digest · recorded_at；缺字段 = 报告不收 | 是（补录重跑） | 是 |
| **验证中发现阻断性 bug** | 如实记 FAIL + 证据（复现步骤/日志/锚点）→ **另开 fix task**，本 task 不顺手修（顺手修 = 证据失效 · 非范围钉死）；报告标注「发现即另开」条目 | — | 是 |

安全：验证只读面为主（replay/catalog/runtime）；写面限专用租户沙盒；实测报告不含真实用户数据/凭证；双进程测试用本地临时 PG schema 或专用库，不碰共享开发库。

---

## 验收标准

- [ ] 人工闸：HG-AUDIT-R1 approved 后方可勾选下列码项（HG-GRAPH-MODULES 模块表已建置 approved · 本 task **预期无图谱新签义务按实判**（零新路由/零新一级模块/零新表/零新 SSE 事件）；**若 30 偏离预判（新增观测端点/新路由 · 新增一级模块 · 新增表列触发 alembic · 新增 SSE 事件类型 · 改被验证对象既有语义）→ 回炉补闸**，见闸表与 graph_delta_note）

### D1 · 部署验证（runbook + 报告 · 映射 SPEC §6-D1）

- [ ] compose 双实例拓扑可起（共享同一 db）；报告标注网关形态（外部 Java 网关 / 降级 LB · 版本指纹）；外部网关不可得时 Eureka 注册条目标「未覆盖待补」不撒谎
- [ ] 无亲和对照：同会话连续请求落不同实例（归属标识对拍）· 鉴权 cookie 跨实例 200 · thread 历史跨实例一致
- [ ] 会话亲和对照（网关支持时）：同会话落同实例断言
- [ ] 混合负载 N 请求两实例均有命中（防「只打到一个」）
- [ ] `reports/multi_replica_verify/deploy_<ts>.yaml` 落盘：拓扑 · 断言逐项 PASS/FAIL · git sha / 镜像 digest · recorded_at

### D2 · 状态外置（双进程 pytest · 映射 SPEC §6-D2）

- [ ] 双进程 fixture：两独立 uvicorn 进程 · 同 PG 异端口 · 每用例**实例归属先断言**（失败 = FAIL 非 skip）
- [ ] A 起 run → B 经事件表 replay 全程帧（seq 连续 · 归属正确 · 内容一致）
- [ ] B 以他 user replay A 的 run → 404（跨实例归属语义保持）
- [ ] B 恢复段事件续写同 run_id 且 seq 接 last_seq（不重开不覆盖）
- [ ] 两进程前置配置断言（`LG_RAG_HTTP_CHECKPOINTER=postgres` 生效）；两进程并发启动 + 同时 `setup()` 不死锁

### D3 · 边界清单（映射 SPEC §6-D3）

- [ ] 清单落盘：≥ 最小条目集 8 条 · 每条带 file:line 锚点 + 失真形态 + 处置建议
- [ ] 对照实测：budget 配额放大断言（2 实例同 session 总放行 > 单实例上限）；两实例 `/runtime` scope 字段对拍；两实例 `/catalog` 对拍一致
- [ ] 清单附全仓模块级进程内状态扫描基线（grep 基线 + 逐条已盘点/不适用标注）

### D4 · HITL 跨实例（映射 SPEC §6-D4）

- [ ] 双进程：A 挂起 → B 见申请 → B 批准 → B resume **图真的续跑**（state 推进 + answer 非空 + hitl.resumed/done 帧续写同 run_id · 不只断 200）
- [ ] 负路径：B 错 thread_id → 409；未开 checkpointer 实例 resume → 503
- [ ] runbook 轨：双容器 + 网关下同链路手工实测通过 · 报告留痕

### D5 · 图谱 / 文档 / 边界纪律（映射 SPEC §6-D5）

- [ ] 零 alembic（迁移 diff 为空断言）；零新路由/零新一级模块/零 SSE 事件；`./scripts/graph-compile.sh` 绿；若偏离 → 回炉补闸 + SPEC 回炉
- [ ] app/ 生产码 diff 为空（`git diff master -- app/` 为空）；发现阻断性 bug → 报告「发现即另开 fix task」条目 · 不在本波修
- [ ] 文档：D3 边界清单落盘 + runbook 配套说明；spec README 占位表本 slug 移行（done 后由 CLOSE 流处理）

### 变异检验（不验收空真规则 · 映射 SPEC §6-变异检验）

- [ ] ① **归属可检**：D2 用例临时改为同进程双 app（或单进程打两次）→ 实例归属断言必挂；恢复后全绿
- [ ] ② **外置可检**：B 进程临时换 InMemorySaver（或关 checkpointer 开关）→ 跨实例 resume/replay 断言必挂；恢复后全绿
- [ ] ③ **失真可检**：budget 放大实证临时收回单实例 → 「总放行 > 单实例上限」断言必挂；恢复后全绿

### 工程（映射 SPEC §6-工程）

- [ ] **闸前置**：30 开工前旧测影响面清单已落盘且逐条有处置（回归/新增理由）——清单见下「旧测影响面清单（B1）」，30 逐条执行处置并在提交说明逐条回填
- [ ] 全量 `pytest tests` 绿（基线 **1349 collected** · 2026-09-22 本帽真跑；**无既有用例删除**，新增双进程用例数如实入 40 记录）；`ruff check app tests` 绿（零新增告警口径）
- [ ] diff 白名单：`git diff master` 只含 tests/（双进程集成测）· scripts/acceptance/ · reports/multi_replica_verify/ · docs/（边界清单 + runbook 说明 + task/invoke）· spec README 索引；**app/ 零改动**

### 旧测影响面清单（B1 · 2026-09-22 10-task 实扫落盘）

> 扫描口径（真跑）：`ls tests/ | grep -iE 'lg_rag|hitl|capability|sse'`（命中 31 文件 · 含 prompt_assembly/prompt_assets 经 capability 关联面）· `grep -c 'def test_'` 逐文件真跑（lg_rag_http 11 / lg_rag_sse_resume 10 / lg_rag_sse_hitl 10 / lg_rag_sse_stream 8 / hitl 20 / hitl_resume 19 / hitl_resume_events 13 / capability_gateway 32 / capability_idempotency 17 / capability_persistence_db 15 / admin_capability_observability 12）· `grep -rnE 'uvicorn' tests/ --include='*.py'` = **零命中**（tests 全 TestClient 同进程形态 · subprocess 仅 test_capability_harness_cli 且非服务进程——**双进程 pytest 基建零先例实证**）· `grep -rlE 'checkpointer|CHECKPOINTER' tests/` 命中 15 文件（单进程 checkpointer 语义守护面）· `ls scripts/acceptance/` = 15 脚本（hitl_persistence_smoke.py/.sh · hitl_approval_loop.py/.sh 起停壳先例在案）· `python -m pytest tests --collect-only -q` = **1349**。本波行为变更源裁定：**零 app/ 生产码改动预期**（track=verify 钉死）——影响面以**回归**为主、**改编预期为零**（实扫确认：无既有用例依赖「单实例」反向断言；既有 checkpointer/resume/replay 用例为单进程语义守护，双进程用例为纯新增不进既有文件断言面），**无测试删除**。处置三态：**回归**（不受影响，全量重跑确认）/ **改编**（本清单预期零 · 若 30 实做发现须改编既有用例 → 停手回 10-task 补记）/ **删除**（本清单无）。

| # | 锚点 | 旧测/调用点现状 | 本波影响 | 处置 |
|---|------|----------------|----------|------|
| 1 | `tests/test_lg_rag_sse_resume.py` 10 用例 · `tests/test_lg_rag_sse_hitl.py` 10 用例 · `tests/test_hitl_resume_events.py` 13 用例 | replay/resume/事件续写单进程语义守护（含 checkpointer 开关对拍 · 事件 seq 连续断言 · `/replay` 路由）——D2/D4 跨实例断言的**单进程基线形态先例** | 本波零生产码改动（非范围钉死）→ 既有用例零改动全绿；双进程跨实例断言为纯新增（见 #7） | 回归（零改动）+ 新增双进程断言（新增义务 · 见 #7） |
| 2 | `tests/test_hitl.py` 20 用例 · `tests/test_hitl_resume.py` 19 用例 | HITL 申请/resume 守护（`OPS_HITL_PERSISTENCE` 开关对拍 · resume 驱动语义 · 409/503 负路径既有断言） | hitl 模块语义零改动 → 零改动全绿；D4 负路径 409/503 跨实例版为新增（见 #7 · 既有 503/409 断言形态直接复用） | 回归（零改动）+ 新增跨实例负路径断言（见 #7） |
| 3 | `tests/test_capability_gateway.py` 32 用例 · `tests/test_capability_idempotency.py` 17 用例 · `tests/test_capability_persistence_db.py` 15 用例 · `tests/test_admin_capability_observability.py` 12 用例 | 闸链/幂等/DB 持久化/观测端点守护（`/catalog` `/runtime` snapshot 形态先例——D3 对拍断言直接消费面） | capability 语义零改动 → 零改动全绿；两实例对拍/budget 放大实证为新增（见 #7） | 回归（零改动）+ 新增对拍/放大实证（见 #7） |
| 4 | `tests/conftest.py`（budget 命中 · 共享 fixture 面） | 既有 fixture 提供单进程 TestClient/DB 夹具 | 双进程 fixture **新增不改既有 conftest 语义**（新 fixture 独立命名 · 子进程 env 隔离不影响主 pytest 进程 · `LG_RAG_HTTP_CHECKPOINTER` 为子进程 env 不污染既有用例） | 回归（零改动 · 新增独立 fixture） |
| 5 | `scripts/acceptance/hitl_persistence_smoke.py/.sh` · `hitl_approval_loop.py/.sh`（本帽 ls 实证 15 脚本） | runbook 形态先例：.sh 壳起服务/等就绪/收尾杀进程 · 纯 HTTP 断言 · 自清库报清理数 | D1/D4 runbook 轨 `multi_replica_*` 脚本沿用同形态（新增 · 不改既有脚本） | 回归（零改动）+ 新增 runbook 脚本（见 #7） |
| 6 | `reports/qdrant_migrate/reconcile_p1_*.yaml` · `reports/memory_embedding_backfill/*.yaml` | 报告字段族先例（命令 · 输出摘录 · PASS/FAIL · 环境指纹 · 计数守恒） | `reports/multi_replica_verify/*.yaml` 新目录沿用字段族（新增） | 新增（报告目录 · 见 #7） |
| 7 | 新增义务：双进程集成测（`tests/` 新文件族：双进程 fixture · 归属先断言 · A 起 B replay/404/续写 seq · 前置配置断言 · 并发 setup 不死锁 · D4 A 挂起 B resume 图真的续跑 + 409/503 负路径）· `scripts/acceptance/multi_replica_*` runbook · `reports/multi_replica_verify/*.yaml` · D3 边界清单文档 · 变异检验三条 | 当前不存在（双进程 pytest 仓内零先例实证：tests/ uvicorn grep 零命中） | 本波新增守护测试与证据面（工程验收项）；collected 自 1349 增加，新增数入 40 记录 | 新增（30 实现 · 40 核验） |
| 8 | `tests/test_lg_rag_http.py` 11 · `tests/test_lg_rag_sse_stream.py` 8 · 其余 lg_rag/capability 文件（basic/router/retry/multi/session_continuity/sse_token_stream/sse_subtask_message/structured_output_p2/supervisor_capability_catalog/domain_allowlist/manifest/manifest_http/http_adapter/lookups/policy/task_writer/visibility_and_receipts/harness_cli） | 与多副本验证面正交的单进程语义守护 | 本波零生产码 → 零改动全绿 | 回归（零改动） |
| 9 | 双进程基建零先例风险（**入 failure_paths**） | 仓内无双进程 pytest 先例（实证）；hitl_persistence_smoke .sh 壳可参照但 pytest fixture 化是新建 | 起停稳定性（端口冲突/就绪等待/收尾杀进程/CI 时长）为 30 阶段实做风险；对策钉入 failure_paths「双进程 fixture 起停不稳」行（动态端口 · 就绪轮询 · finally 杀进程树 · 用例级超时） | 风险对策已入 failure_paths（30 实做 · 40 核验稳定性） |
| 10 | alembic 链 | 本波**无迁移义务**（零新表零列预期 · track=verify） | 迁移 diff 为空断言入 D5 验收 | 无（零迁移钉死） |

---

## 依赖

| 依赖 | 说明 |
|------|------|
| SPEC | `docs/spec/multi-replica-verify/SPEC-multi-replica-verify_v1.md`（signed · HG-SPEC-SIGNOFF=approved 2026-09-22 · 8236747 · F1 双轨 + P1 双进程 + 验证≠投产锁死） |
| 上游手册 | `../ops-desk-workspace/docs/08-interview/07_agent-memory-prompt-module-landscape_v1_zh.md`（手册 L0 行 :369/:506 单实例未验证 ⚠️ · §3.4 第三类「成熟度标志」） |
| 编码规范 | `docs/standards/CODING_BACKEND_L2_v1_zh.md` |
| 图谱 | `docs/_tech_graph/l1/01_modules.md`（HG-GRAPH-MODULES 真值 · 2026-09-22 真读核验 · lg_rag 行 :27 / hitl 行 :31 / capability 行 :26（进程内注册表明示）/ db 行 :33（checkpoint 表在案）/ api 行 :20 / 签录链至 :93） |
| 验证对象 | `app/ops/lg_rag/checkpointer.py` · `app/ops/lg_rag/event_store.py` · `app/ops/hitl/resume.py` · `app/ops/hitl/persistence.py` · `app/ops/capability/{registry,budget,circuit,circuit_storage,metrics,persistence,idempotency}.py`（**只读 · 零改动钉死**） |
| 先例 · runbook 形态 | `scripts/acceptance/hitl_persistence_smoke.py/.sh`（.sh 壳起停 + 纯 HTTP 断言 + 自清库）· `scripts/acceptance/hitl_approval_loop.py/.sh`（HITL 审批环手工实测） |
| 先例 · 报告字段族 | `reports/qdrant_migrate/reconcile_p1_*.yaml`（双侧计数对账 · count_diff=0）· `reports/memory_embedding_backfill/*.yaml`（字段族 + 计数守恒 + 退出码语义） |
| 先例 · 单进程语义断言形态 | `tests/test_lg_rag_sse_resume.py` · `tests/test_lg_rag_sse_hitl.py` · `tests/test_hitl_resume.py`（409/503 负路径断言形态）· `tests/test_admin_capability_observability.py`（`/catalog` `/runtime` snapshot 断言形态） |
| 测试锚点 | 见 B1 清单 #1-#5 |
| 格式基准 | `docs/tasks/done/task_memory_compliance_delete.md`（signed → done 五棒全通 · PR #163 · 本 task 格式对齐此） |

---

## 给执行帽的必读列表

1. `AGENTS.md`
2. 本 task（钉死契约 · 闸 · 非范围 · B1 · 变异检验）
3. SPEC `docs/spec/multi-replica-verify/SPEC-multi-replica-verify_v1.md`（§1 锚点 / §2 D1–D5 / §3 非范围 / §4 F1+P1 裁决 / §5 failure_paths / §6 验收 / §7 residual）
4. `docs/standards/CODING_BACKEND_L2_v1_zh.md`
5. 验证对象（只读）：`app/ops/lg_rag/checkpointer.py`（:25-53）· `app/ops/lg_rag/event_store.py`（:34-95）· `app/ops/hitl/resume.py`（:5-17 · :236-248 · :329-340）· `app/ops/hitl/persistence.py`（:7-12）· `app/ops/capability/budget.py`（:22-24 · :51-62 · :83-85 · :246）· `app/ops/capability/registry.py`（:29-40）· `app/ops/capability/circuit.py`（:72 · :317-325）· `app/ops/capability/circuit_storage.py`（:45-47）· `app/ops/capability/metrics.py`（:1-13）· `app/ops/capability/persistence.py`（:11）· `app/ops/capability/idempotency.py`（:50-51）
6. 先例：`scripts/acceptance/hitl_persistence_smoke.sh`（起停壳）· `tests/test_hitl_resume.py`（409/503 负路径形态）· `tests/test_admin_capability_observability.py`（snapshot 断言形态）· `reports/qdrant_migrate/reconcile_p1_*.yaml`（报告字段族）
7. 部署面：`docker-compose.yml` · `Dockerfile` · `.github/workflows/deploy-api.yml`
8. `docs/harness/prompts/FRAGMENT_30_gate_verify_v1_zh.md`

---

## 思考轮控制

| 轮 | 结论 | early_stop | reason（early_stop） | residual_risks |
|----|------|------------|----------------------|----------------|
| R0 | SPEC signed（HG-SPEC-SIGNOFF=approved 2026-09-22 · 8236747）；范围 D1–D5 承 SPEC §2 不重开辩论；本帽实扫复核：分支正确（`task/multi-replica-verify` · SPEC 8236747 在链）· checkpointer.py 单开关 :27/setup 幂等 :48-53 · resume.py fail-closed 503 :329-336/apostgres_saver(setup=True) :338 · budget.py `_SESSIONS`+锁 :51-56/MAX 512 :62 · registry.py 单例 :29/:32/拒绝覆盖 :38-40——SPEC §1 锚点抽核全部一致；tests/ uvicorn grep 零命中（双进程 pytest 零先例实证）· scripts/acceptance/ 15 脚本（hitl_persistence_smoke/.sh 先例在案）· pytest 基线 **1349 collected**（真跑） | no | — | none |
| R1 | 开工闸：HG-TASK-DRAFT / HG-AUDIT-R1 落稿时待签（10 帽不签 · blocks 30 未放行）· HG-GRAPH-MODULES=approved（模块表已建置 · **真读** `01_modules.md`：lg_rag 行 :27 · hitl 行 :31 · capability 行 :26 进程内注册表明示 · db 行 :33 checkpoint 表在案 · api 行 :20 · 签录链至 :93）+ **预期无新签义务按实判**（零新路由/零新一级模块/零新表/零新 SSE 事件）+ 偏离回炉补闸条款 · HG-PILOT-OPSDESK-GLAYER=n/a | no | — | 无 |
| R2 | 竖切：D1–D5 同 task 一次提交（承 SPEC §8 序：D2 双进程基建先行 → D4 HITL 双进程 → D3 清单+对照实测 → D1 runbook+实测 → D5 文档）；方案对比继承 SPEC §4 两组裁决（F1 双轨弃 F2 纯手工零回归/F3 网关 CI 外部依赖越界 · P1 subprocess 双进程弃 P2 同进程双 app 假跨实例），不重演 | no | — | 无 |
| R3 | failure_paths **14 条** = SPEC §5 十条翻四列 + 双进程基建起停不稳一条（仓内零先例风险对策 · B1 #9 钉入）+ 过程三（闸未签拒开工 · B1 闸前置拒收 · 缺断言/变异检验拒收）；两静默错定性承 SPEC：假阳性「没真跨实例」（防线：禁同进程形态 + 归属先断言 FAIL 非 skip + 变异检验①）与进程内状态失真未发现（防线：清单锚点 + 对照实测 + 扫描基线兜底漏项）；验证不顺手修被验证对象钉死 | no | — | 无 |
| R4 | 验收 **26 条**全否定性断言化逐块映射 SPEC §6（人工闸 1 / D1×5 / D2×5 / D3×3 / D4×3 / D5×3 / 变异检验×3 / 工程×3）；B1 实扫 **10 行**落盘（回归×5 · 改编×0 预期 · 新增×3 · 风险对策×1 · 迁移无×1 · 删除×0）；关键实证：tests/ uvicorn grep 零命中（双进程零先例）· 无既有用例依赖「单实例」反向断言 → 改编面预期零钉死 | no | — | 双进程 fixture 起停稳定性（端口/就绪/收尾/CI 时长）是 30 实做风险（failure_paths 已钉对策 · 40 核验稳定性） |
| R5 | 可交 20-task-audit；与 SPEC 实质差异为零（B1 / 闸行留痕 / 基线数 / 锚点行号复核 / 双进程基建风险对策入 failure_paths 均为过程化落地）；HG-TASK-DRAFT 与 HG-AUDIT-R1 落稿时待签 | no | — | ① 双进程 pytest 基建仓内无先例（承 SPEC §7 ① · 对策已入 failure_paths）；② 外部 Java 网关实测可用性不受本仓控制（承 SPEC §7 ② · 不可得时 Eureka 条目标未覆盖待补）；③ 边界清单「处置建议」是建议不是承诺（承 SPEC §7 ③）；④ 验证结论时效：runbook 轨结论随时间贬值须复跑（承 SPEC §7 ④ · pytest 轨 CI 兜核心语义） |

**actual_last_round**：R5 · **early_stop**：no · **residual_risks**：见 R4/R5

### R0 · 问题框定

SPEC 已签收（F1 双轨 + P1 subprocess 双进程 + 验证≠投产锁死），本 task 只做可执行化拆解：状态外置已设计未实证（「设计了」与「实证成立」之间隔着配置漂移/双写口径/进程内计数失真一整类静默错）。本帽实扫复核：分支 `task/multi-replica-verify` 正确（SPEC 8236747 在链）；checkpointer.py 单一开关 `LG_RAG_HTTP_CHECKPOINTER`（:27）与 `setup()` 幂等（:48-53 docstring「幂等，可每次传」复核一致）；resume.py fail-closed 503（:329-336）与每次新开 `apostgres_saver(setup=True)`（:338）复核一致；budget.py `_SESSIONS`+模块级锁（:51-56）与 `MAX_TRACKED_SESSIONS=512`（:62）复核一致；registry.py 进程内单例（:29/:32）与拒绝覆盖（:38-40）复核一致；`tests/` uvicorn grep **零命中**（全 TestClient 同进程形态 · subprocess 仅 test_capability_harness_cli 非服务进程——**双进程 pytest 零先例实证**）；`scripts/acceptance/` ls 实证 15 脚本（hitl_persistence_smoke.py/.sh · hitl_approval_loop.py/.sh 起停壳先例在案）；pytest 基线 **1349 collected**（真跑 · = 1333 + memory-compliance-delete 16）。SPEC §1 锚点抽核**零语义偏差**。

### R1 · 开工闸

HG-TASK-DRAFT / HG-AUDIT-R1 落稿时待签（10 帽不签 · blocks 30 未放行 → **30 拒开工**）；HG-GRAPH-MODULES **真读** `docs/_tech_graph/l1/01_modules.md` 核验：模块表已建置（bootstrap 签 2026-07-16 · 签录链完整至 :93 memory-compliance-delete 行）；`lg_rag` 行（:27 · checkpointer/事件表/replay 在案）· `hitl` 行（:31 · resume 驱动 + 申请落库在案）· `capability` 行（:26 · **进程内注册表**明示「非跨进程注册中心」）· `db` 行（:33 · langgraph checkpoint 表 checkpoints/checkpoint_writes 同库不同表已在案）· `api` 行（:20 · 注册面）均在表。SPEC §2 D5 判**预期无图谱义务按实判**：零新路由/零新一级模块/零新表/零新 SSE 事件——**无新签义务**，不阻塞 30 开工形态预判；**回炉补闸条款**钉死（偏离 → 本闸转有义务 + 退 10-spec + 图谱如实登记）。HG-PILOT-OPSDESK-GLAYER=n/a。

### R2 · 竖切

D1–D5 是不可拆语义单元：语义断言不进 CI = 「验证过」贬值成「曾经验证过」（F2 弃选理由钉死）；部署面不实测 = 网关面诚实性失守（降级形态写成「网关验证通过」是 D1 钉死的撒谎形态）；清单无锚点无扫描基线 = 失真漏项无兜底；pytest 轨不配套 runbook 轨 = 拓扑下成立性无证。耦合面小（测试 + 脚本 + 报告 + 文档 · 零 app/ 预期），单 PR 不巨型。实现序承 SPEC §8：D2 双进程基建先行 → D4 HITL 双进程 → D3 清单+对照实测 → D1 runbook+实测 → D5 文档收口。方案对比不重演，直接继承 SPEC §4 两组裁决（F1 双轨弃 F2 纯手工零 CI 回归/F3 全自动网关 CI 外部依赖越界成本失真 · P1 subprocess 双进程弃 P2 同进程双 app 模块级单例全共享假跨实例）。

### R3 · 失败语义

SPEC §5 十条失败面全收并翻四列：两静默错（假阳性「没真跨实例」/ 进程内状态失真未发现）防线钉死（禁同进程形态 + 归属先断言 FAIL 非 skip + 变异检验① / 清单锚点 + 对照实测 + 扫描基线兜底漏项）；配置漂移 A 开 B 关为「防重/审批时有时无」静默错（前置配置断言 + env 对拍）；版本漂移由 stranded_checkpoint 409 既有分支证明真实（镜像 digest 断言）；HITL「批了但什么都没发生」最坏形态由「图真的续跑」断言链钉死（只断 200 = 用例不合格）；并发 setup() 由幂等 docstring + 启动竞态实证覆盖；验证污染由专用租户前缀 + 清库收尾先例覆盖；网关不可用由降级形态如实标注钉死；报告无法复核由字段族缺字段不收钉死；发现阻断性 bug 另开 fix task 不顺手修钉死。补**双进程 fixture 起停不稳**一条（仓内零先例风险 · 对策：动态端口 + 就绪轮询 + finally 杀进程树 + 用例级超时 · B1 #9 钉入）与过程三行（闸未签拒开工 · B1 未落盘拒收 · 缺断言/变异检验拒收防空真规则）。

### R4 · 可测性

验收 **26 条**全部可执行断言：归属先断言 FAIL 非 skip · A 起 B replay 全程帧 seq 连续 · 他 user 404 · 续写同 run_id 接 last_seq · 前置配置断言 + 并发 setup 不死锁 · HITL 图真的续跑（state 推进 + answer 非空 + 帧续写）· 409/503 负路径 · 亲和对照 + 混合负载两实例均有命中 · 报告字段族含环境指纹 · 清单 8 条目 file:line 锚点 · budget 放大断言 + `/runtime`/`/catalog` 对拍 · 扫描基线兜底 · 零 alembic + graph-compile 绿 · app/ 零 diff · 变异检验三条 · pytest/ruff/diff 白名单。B1 实扫落盘 **10 行**：回归×5（#1-#5 · 含 conftest 零改动与 runbook 先例零改动）· **改编×0 预期**（零生产码钉死 · 无既有用例依赖「单实例」反向断言 · 若 30 实做发现须改编 → 停手回 10-task 补记）· 新增×3（#6 报告目录 · #7 双进程集成测+runbook+清单 · #9 风险对策已入 failure_paths 计新增义务面）· 迁移无×1（#10）· **删除×0**。

### R5 · 交付判定

可交 20-task-audit：与 SPEC 实质差异为零（B1 实扫落盘 / 闸行留痕 / pytest 基线数 / 锚点行号抽核 / 双进程基建风险对策入 failure_paths 均为过程化落地，无范围/验收/非范围语义偏移）；HG-TASK-DRAFT 与 HG-AUDIT-R1 落稿时待签（10 帽不签）；残余风险四条承 SPEC §7 如实携带（双进程基建零先例 · 外部网关可用性不受控 · 清单处置建议是建议非承诺 · runbook 轨结论时效），无新增风险。

### 自检结论

本稿：范围/非范围/验收/failure_paths 逐块映射 SPEC（§2→范围 D1–D5 · §3→非范围 9 条 · §5→failure_paths 10+1+过程三=14 条 · §6→验收 26 条）；钉死契约自 SPEC §2/§4 锁死不重开辩论（F1 双轨 · P1 双进程真隔离 · 归属先断言 FAIL 非 skip · 验证≠投产 · app/ 零改动 · HITL 图真的续跑 · 报告环境指纹 · 网关形态如实标注）；B1 实扫落盘 10 行处置三态齐全（含双进程基建零先例风险对策入 failure_paths）；闸表四行（HG-TASK-DRAFT 落稿时待签 · HG-AUDIT-R1 落稿时待签 blocks 30 · HG-GRAPH-MODULES 模块表已建置 approved + 预期无新签义务按实判 + 偏离回炉条款 · HG-PILOT-OPSDESK-GLAYER n/a）；R0–R5 全轮无 early_stop；可交 20-task-audit。

---

## 修订记录

| 日期 | 摘要 |
|------|------|
| 2026-09-22 | 10-task 落稿（SPEC signed 8236747 后 · 本棒由 00 委派 10-task 帽 Agent 执行）：锚点抽核（checkpointer :27/:48-53 · resume :329-340 · budget :51-62 · registry :29-40 复核一致 · tests/ uvicorn grep 零命中双进程零先例实证 · acceptance 15 脚本 · 基线 1349 collected 真跑）；验收 26 条断言化映射 SPEC §6；failure_paths 14 条（SPEC §5 十条 + 双进程基建起停不稳 + 过程三）；B1 实扫 10 行（回归×5 · 改编×0 预期 · 新增×3 · 风险对策×1 · 迁移无×1 · 删除×0）；HG-GRAPH-MODULES 真读核模块表（lg_rag :27 / hitl :31 / capability :26 / db :33 / api :20 · 签录链至 :93）+ 预期无新签义务按实判 + 偏离回炉条款；HG-TASK-DRAFT / HG-AUDIT-R1 落稿时待签 |
| 2026-09-22 | **40 核验 PASS · 验收 26/26 通过**（invoke_20260922_40_verify_multi_replica_verify.md）：全量 pytest ×3（1358 collected=1349+9 · 1353 passed · 3 红基线对照 worktree @ d5234aa 同 .env 复现 + 第 4 红 test_reconcile_mismatch_marks_failed 判既有 flaky 时序竞态 · 单跑全绿）· 双进程 9/9 亲跑 ×2 + 归属断言/resume 断言链读码合格 · 部署报告亲读 16/16 PASS+Eureka 未覆盖如实 · 清单锚点抽核 10 处 9 中（gateway.py:81 实为 :79 偏 2 行附注）· 变异①亲复做 8 挂→还原 9/9 绿 · ruff 57=基线 · graph-compile 绿 · app//alembic/ 三点零 diff（两点非空纯因 origin/master 前进）· B1 抽核 5 条全属实 · diff 白名单吻合；问题清单 4 条（flaky 观察 · 锚点漂移 · 变异②③未亲跑 · Eureka 待补）均不阻塞 |
| 2026-09-22 | **50+CLOSE**：PR [#165](https://github.com/Cyning12/ops-desk-api/pull/165) CI 全绿 merge master（`7541102`）· 归档 done/ · 合并前解 SPEC add/add 冲突（master #146 带入占位原件 vs 本分支 signed 版 → 取 signed 版）· 遗留：Eureka 条目未覆盖待补（外部网关）· runbook 轨结论时效须复跑 · test_reconcile_mismatch_marks_failed flaky 建议 fix task 加固 · 清单锚点 1 处偏 2 行 |
