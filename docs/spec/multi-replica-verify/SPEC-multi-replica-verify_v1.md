# SPEC：L0 多副本验证（单实例 → 多实例）（v1）

> **状态**：`draft-complete`（HG-SPEC-SIGNOFF=**pending** 待签 · 10-spec 已补全 · 人签前不出 task / 不改码）
> **track**：`verify`（验证/实证类 · **预期零生产码改动**——产物是验证方案 + 实测证据 + 进程内状态边界清单；**无 alembic 义务** · **图谱义务预期无**（按实判见 §2 D5）：零新路由/零新表/零新事件；若实扫发现阻断性 bug → 另开 fix task，不在本 SPEC 顺手修）
> **上游**：`../ops-desk-workspace/docs/08-interview/07_agent-memory-prompt-module-landscape_v1_zh.md`（手册 L0 行 :369/:506 · §3.4 第三类「成熟度标志」）
> **格式基准**：`docs/spec/memory-compliance-delete/SPEC-memory-compliance-delete_v1.md`（signed · 机读纪律同款）
> **下游**：人签 SPEC → 00 出 task → 20-task-audit → HG-AUDIT-R1 → 30 实施（测试 + runbook + 报告）
> **Open Folder（实施）**：`ops-desk-api/`

---

## Harness 元信息

| 字段 | 值 |
|---|---|
| **spec_slug** | `multi-replica-verify` |
| **invoke_slug** | `multi-replica-verify` |
| **test_strategy** | `required` |
| **test_strategy_note** | 双轨验证：① **双进程 pytest 集成测**（两独立进程共享同一 PG · 实例归属先断言再语义断言——防假阳性「没真跨实例」）覆盖 D2 状态外置与 D4 HITL 跨实例核心语义；② **runbook + 手工实测报告**（compose 双容器 + 外部 Java 网关 · `scripts/acceptance/` + `reports/multi_replica_verify/*.yaml` 留痕 · hitl_persistence_smoke / qdrant reconcile 先例同形）覆盖 D1 部署面与亲和对照；③ D3 边界清单逐条带代码锚点 + 对照实测（budget 配额放大实证）；变异检验三条（见 §6）；全量 pytest 绿 |
| **Open Folder（实施）** | `ops-desk-api/` |
| **默认分支** | `task/multi-replica-verify` |
| **graph_change_layer（建议）** | **预期无图谱义务（按实判）**：零新路由/零新一级模块/零新表/零 SSE 事件类型——产物为测试、runbook 脚本、reports/ 报告、边界清单文档。若 30 形态偏离（实扫发现阻断性 bug 须改生产码 → 另开 fix task；或验证本身需要新增观测端点）→ 回 10-spec 修订 |

### 人工闸（SPEC 阶段）

| human_gate_id | status | 说明 |
|---|---|---|
| **HG-SPEC-SIGNOFF** | pending | 落稿时待签 · 维护者审后签 approved |
| **HG-GRAPH-MODULES** | pending（预期无义务） | 预期零图谱改动；若 30 出现新路由/新表 → 本闸转为有义务，30 前须 approved |

---

## 1. 背景与目标

L0 现状：鉴权/租户/Principal 代码构造 ✅ · Java 侧网关+Eureka **存在于外部仓**（`ops-desk-api-java-gateway` Spring Cloud Gateway + `ops-desk-eureka-server`，本仓 grep 零命中 · 上游手册 :369 明示）· **但单实例，多副本未验证**（手册 L0 ⚠️ · 边界纪律：别说成「已做服务发现与多副本」）。属「成熟度标志」前置验证——有真实流量前必须回答的问题：**这个系统能不能跑两份**。

### 验证 ≠ 投产（本 SPEC 的根本定性）

本 SPEC 的产物是**验证方案 + 实测证据 + 边界清单**，不是生产多副本改造。状态外置在代码层面已有设计（PG checkpointer / 事件表 / DB 幂等 / DB HITL store），但「设计了」与「实证成立」之间隔着一整类静默错：配置漂移（A 开 B 关）、双写口径、进程内计数失真未被发现。实证的价值就在于把这些「应该成立」变成「断言过成立」。**实扫中发现阻断性 bug 时，如实记录并另开 fix task，不在本 SPEC 顺手修**（验证活动顺手改被验证对象 = 证据失效）。

### 现状（2026-09-22 实扫 · 锚点逐个核）

| 锚点 | 实扫结论 |
|---|---|
| `app/ops/lg_rag/checkpointer.py` | PG saver 由**单一开关** `LG_RAG_HTTP_CHECKPOINTER=postgres` 控制（:27 进程级唯一真源 · 默认关）；DSN 由 `settings.database_url` 转 psycopg（:41-43 · 与业务表**同库**不同表 checkpoints/checkpoint_writes）；`setup()` 幂等可每次传（:48,53）；HTTP invoke 与 SSE 走同一把闸（:25-27 docstring 钉死）。**跨实例前提 = 两副本同开关同库同版本** |
| `app/ops/lg_rag/event_store.py` | SSE 事件落 PG 表 `ops_lg_rag_run_events`（每帧独立 commit :34-47）；归属按 user_id 反查（`run_owner` :50-69 · 跨用户 replay → `LgRagRunNotFoundError` 404 :87-95）；`last_seq` :72-84 供恢复段**接着编号**。事件表天然跨实例可读——B 实例 replay A 实例的 run 无进程内障碍 |
| `app/ops/hitl/resume.py` | **A 挂起 B resume 结构上天然成立**：定位靠 thread_id → PG checkpoint（:16-17 docstring）；resume 驱动器**零进程内定位状态**（每次调用新开 `apostgres_saver(setup=True)` :338）；没开 PG 开关 **fail-closed 503**（`checkpointer_not_configured` :329-336 · 不假装恢复成功）；`stranded_checkpoint` 409（:236-248 · 旧版本格式残留永远恢复不了——证明**版本漂移是实证必查项**）；恢复段事件续写同一 run_id（`ResumeEventSink` · start_seq 接 last_seq）。成立前提三件套：两副本同开 `LG_RAG_HTTP_CHECKPOINTER=postgres` + 同库 + 同代码版本 |
| `app/ops/capability/registry.py` | 进程内单例 dict（:29/:32）；注册**仅发生在启动 import 路径**（`capability/__init__.py` :106-112 ensure_default_capabilities / mcp / extra manifests · 拒绝覆盖 :38-40）；`admin/capability.py` 五个端点全 GET 只读（:79/:163/:217/:228/:255 · **零运行时注册/注销端点**）→ 同镜像同 env 则各副本注册表一致，漂移面 ≈ 部署配置漂移；实证形态 = 两实例 `/catalog` 对拍 |
| `app/ops/capability/budget.py` | per-session 配额 + kill switch **进程内计数**（`_SESSIONS` + 模块级锁 :51-56）；docstring :22-24 明示「多实例各进程各一份」已知边界；`snapshot()` 显式 `scope: process-local`（:246）；`MAX_TRACKED_SESSIONS=512` 插入序淘汰（:62 · 被淘汰会话配额归零）。**多副本失真：配额按实例数放大（2 副本 ≈ 2× 上限）· 会话跳实例 = 配额重置**；kill switch 每次调用读 env（:83-85）→ 副本间一致性 = 部署 env 一致性 |
| `app/ops/capability/circuit.py` + `circuit_storage.py` | pybreaker 进程内 `_BREAKERS`（circuit.py :72）；三后端 memory/redis/mock-unavailable，**默认 mock-unavailable → process-local(degraded)**（circuit_storage.py :45-47 刻意让 Redis 不可用逼回落路径被真走）；Redis 共享路径已设计未接（同步客户端 asyncio 阻塞坑 docstring :12-13）；`snapshot()` 显式 `scope`/`degraded`/`redis_error`（circuit.py :317-325）。**A 熔断 B 照打，故障期拉长 N 倍——已知边界，实证入清单** |
| `app/ops/capability/metrics.py` | 进程内计数 + JSON 快照（:1-13 docstring 明示多实例各一份已知边界 · 不引 Prometheus）→ 多副本下 `/metrics` 各说各话，聚合须外部 |
| `app/ops/capability/persistence.py` + `idempotency.py` | `OPS_CAPABILITY_PERSISTENCE=db` → `DbIdempotencyStore` **跨实例防重**（(tenant,key) 唯一约束 · 租约判定交 DB 时钟 idempotency.py :50-51 明示多实例时钟偏差坑）；默认 `null` 不防重告警（persistence.py :11 「不能上生产」）。**多副本生产必须显式 db——配置漂移（A=db B=null）= 防重时有时无的静默错** |
| `app/ops/hitl/persistence.py` | `OPS_HITL_PERSISTENCE=db` → `DbHitlStore` 跨实例跨重启；默认 `null` 不落库告警（:7 「不能上生产」）；同「显式选不自动探测」纪律（:9-12）。**审批申请跨实例可见 = 本开关 = db** |
| auth 会话 | `ops_sessions` 表 DB 存会话（models.py :66-69 · cookie 携 token · auth.py :36-46）→ **鉴权天然无状态，多副本无需会话亲和** |
| SSE live 流 | live 帧只在**服务该连接的进程内**（sse_stream.py :20-22 · PG checkpointer 整个流期间持有）；断连后 replay 走 PG 事件表 cursor（event_store.load_events_after）→ **跨实例续传成立的前提是事件已落盘**；live 中途换实例 = 断连 + replay 续传（非无缝） |
| 部署面 | 仓内：Dockerfile（单容器 uvicorn）+ docker-compose.yml（api **单服务** · 无 replicas/无 LB · db+qdrant）+ `.github/workflows/deploy-api.yml`（GHA 部署）；**零 k8s 清单**；Java 网关 + Eureka 在**外部仓**（本仓 grep eureka/zuul/ribbon 零命中）→ 网关面验证只能手工实测 |
| 验证形态先例 | `scripts/acceptance/hitl_persistence_smoke.py`（.sh 壳起服务/等就绪/收尾杀进程 · 纯 HTTP 断言 · 自清库并报清理数）；`reports/qdrant_migrate/reconcile_p1_*.yaml`（双侧计数对账 · count_diff=0 判 pass）；`reports/memory_embedding_backfill/*.yaml`（字段族 + 计数守恒 + 退出码语义）。仓内**无双进程 pytest 先例**——D2/D4 双进程测为本 SPEC 新建形态 |

### 一句话目标

实证回答「这个系统跑两份成不成立」：**双进程 pytest** 断言状态外置核心语义（A 起 run · B 恢复/查询/404 · A 挂起 · B resume 续写同 run）+ **runbook + 手工实测报告**覆盖部署面（2 容器 + 外部网关 · 会话亲和/无亲和对照）+ 产出**进程内状态边界清单**（哪些计数/注册表/熔断在多副本下失真 · 逐条带代码锚点与实证）；预期零生产码改动，发现阻断性 bug 另开 fix task。

---

## 2. 范围

### D1 · 多副本部署验证（必做 · runbook + 实测报告）

| 项 | 约定 |
|---|---|
| 拓扑 | 2 个 api 容器（compose `deploy.replicas=2` 或双 service 别名 · **共享同一 db**）+ 前置网关 |
| 网关面 | 首选外部 Java 网关（Eureka 注册 2 实例 · 与手册 L0 行对齐）；网关不可得的降级形态 = compose 内置轻量 LB（nginx/haproxy round-robin），**报告中必须如实标注用的是哪一种**，不得把降级形态写成「网关验证通过」 |
| 亲和对照 | 两组实测：**无亲和**（round-robin · 同会话连续请求落不同实例 · 断言鉴权/查询语义不漂移）与**会话亲和**（若网关支持 · 断言同会话落同实例）；对照结论落报告 |
| 断言面 | ① 两实例健康且注册可见；② 登录态跨实例（A 登录的 cookie 打 B → 200）；③ thread 历史跨实例（A 产生的 thread turns B 读出一致）；④ 无亲和下混合负载 N 请求两实例均有命中（日志/实例标识对拍——防「LB 实际只打到一个」假阳性） |
| 产物 | `scripts/acceptance/multi_replica_*.sh/py` + `reports/multi_replica_verify/deploy_<ts>.yaml`（拓扑 · 网关形态 · 各断言 PASS/FAIL · 环境指纹 git sha/镜像 digest） |

### D2 · 状态外置实证（必做 · 双进程 pytest · 核心）

| 项 | 约定 |
|---|---|
| 形态 | pytest 集成测起**两个独立进程**（subprocess uvicorn 或等价隔离形态 · 共享同一 PG DSN · 不同端口）——模块级单例（registry/budget/circuit）是进程内状态，同进程双 app 实例是**假跨实例**，禁止 |
| 实例归属先断言 | 每个跨实例用例**先断言请求确落不同进程**（实例标识：进程 pid/端口注入响应头或启动 banner 对拍），再断言语义——归属断言失败 = 用例 FAIL 而不是跳过 |
| 跨实例恢复 run | A 起 run（interrupt 挂起或自然完结）→ B 经 checkpoint 读回 state / 经事件表 replay 全程帧（seq 连续 · 归属正确） |
| 跨实例查他人 run | B 以他 user 身份 replay A 的 run → 404（`assert_run_owned` :87-95 既有语义跨实例保持） |
| 事件续写 | B 恢复段事件续写同一 run_id 且 seq 接 last_seq（不重开 · 不覆盖） |
| 前置配置 | 两进程均 `LG_RAG_HTTP_CHECKPOINTER=postgres` + `OPS_HITL_PERSISTENCE=db`；用例前置断言配置生效（防「开关没开测了个寂寞」） |

### D3 · 跨实例一致性盘点（必做 · 边界清单文档 + 对照实测）

| 项 | 约定 |
|---|---|
| 产物 | `docs/guides/`（或 `docs/spec/multi-replica-verify/` 夹内）**进程内状态边界清单**：每条目 = 状态名 · 代码锚点（file:line）· 多副本行为（失真形态）· 既有自首（snapshot scope 字段/docstring）· 处置建议（现接受 / 何时须外置） |
| 最小条目集 | ① capability registry（启动注册 · 同镜像同 env 则一致 · 漂移面=配置）；② budget per-session 配额（**失真：按实例数放大 · 跳实例重置**）；③ kill switch（env 一致性）；④ circuit breaker（默认 process-local(degraded) · A 熔 B 照打）；⑤ metrics（各说各话）；⑥ idempotency/receipts（=db 跨实例 · =null/memory 失真）；⑦ HITL store（=db 跨实例）；⑧ SSE live 流（进程内 · 断连 replay 兜底） |
| 对照实测 | budget 配额放大实证（2 实例 · 同 session 交替打 · 总放行数 > 单实例上限断言）；两实例 `/runtime` snapshot 对拍（scope 字段如实呈现）；两实例 `/catalog` 对拍一致 |
| 基线扫描 | 清单须附全仓模块级进程内状态扫描基线（grep `threading.Lock`/模块级 dict 单例/`_LOCK`）——清单漏项由基线扫描兜底 |

### D4 · HITL 跨实例（必做 · 双进程 pytest + runbook 双轨实证）

| 项 | 约定 |
|---|---|
| 核心断言 | A 挂起（interrupt → checkpoint 落 PG + hitl 申请落 DbHitlStore）→ **B resume**：申请列表 B 可见 → B 批准 → B 恢复驱动跑完 → 事件续写同 run_id（hitl.resumed 帧 → done(status=resumed)）→ B 或 A replay 全程可见 |
| 假阳性防线 | 「看起来批了但什么都没发生」是已知最坏形态（resume.py :5-7 docstring）；断言链必须覆盖到**图真的继续跑**（state 推进 + answer 非空 + 事件续写），不是只断言 200 |
| 负路径 | B 以错 thread_id resume → 409 not_interrupted；未开 checkpointer 的实例 resume → 503 checkpointer_not_configured（fail-closed 跨实例保持） |
| runbook 轨 | 手工实测复走同链路（双容器 + 网关 · 报告留痕）——pytest 轨证语义，runbook 轨证部署面下仍成立 |

### D5 · 图谱 / 文档 / alembic（必做 · 按实判）

- **alembic 义务：无**（预期零 schema 改动 · 迁移 diff 为空断言）。
- **图谱义务：预期无（按实判）**。零新路由/零新一级模块/零 SSE 事件类型；若 30 形态偏离（需新增观测端点或修生产码）→ 回 10-spec 修订 + HG-GRAPH-MODULES 转有义务。
- 文档同步：D3 边界清单落盘；runbook 落 `scripts/acceptance/` 配套说明；spec README 占位表移行（done 后）；不回改历史文档。
- **发现阻断性 bug → 另开 fix task**：本 SPEC 的测试/runbook 只如实记录 FAIL 与证据，不顺手修被验证对象。

---

## 3. 非范围

- ❌ **真上生产多副本**（验证≠投产 · 生产切换/灰度/回滚预案另案）
- ❌ **服务发现选型变更**（Eureka 换 Nacos/k8s Service 等 · 现状盘点如实写，选型不动）
- ❌ **容量规划 / 灾备 / 多活**（更后续）
- ❌ **进程内状态外置改造**（budget/circuit/metrics 改 DB/Redis 是**修复动作**非验证动作 · 本 SPEC 只盘点与实证失真，改造另开 SPEC——circuit Redis 路径已设计未接同样不在本波接通）
- ❌ **Java 网关 / Eureka 代码改动**（外部仓 · 本 SPEC 只在其实测可用时用它做拓扑，不可用走降级形态如实标注）
- ❌ **k8s 清单新建**（仓内零 k8s 现状 · 引入编排体系是投产动作）
- ❌ **生产码修复**（实扫/实证发现阻断性 bug → 记录证据 + 另开 fix task · 本 SPEC diff 预期零 app/ 生产码）
- ❌ SSE live 流跨实例无缝迁移（断连 + replay 续传是既有设计兜底 · 无缝化另案）
- ❌ 前端/管理台 UI；历史文档回改

---

## 4. 方案对比（R2）

### 验证判定形态（核心裁定）

| 方案 | 做法 | 收益 | 代价 | 裁决 |
|---|---|---|---|---|
| **F1 · 双轨组合（本 SPEC）** | 核心语义走**双进程 pytest**（两独立进程共享同一 PG · 可 CI 可回归 · 变异检验兜底）；部署面（2 容器 + 网关 · 亲和对照）走 **runbook + 手工实测报告**（`reports/multi_replica_verify/*.yaml` 留痕） | 语义断言进 CI 防回归；部署面诚实（网关在外仓 CI 跑不了就不假装能跑）；两轨证据互补（pytest 证语义 · runbook 证拓扑下成立）；先例全有（hitl_persistence_smoke · qdrant reconcile） | 双进程 pytest 仓内无先例须新建基建（起进程/等就绪/归属断言/收尾）；runbook 复跑靠人 | **推荐** |
| F2 · 纯手工 runbook + 实测报告 | 全部四块断言都走手工实测 + yaml 报告 | 基建成本最低；最接近真实部署 | **零 CI 回归保护**——下次改 checkpointer/resume 语义漂移无人发现；复跑成本高；「验证过」随时间贬值成「曾经验证过」 | 弃（部署面子集并入 F1） |
| F3 · 全自动化双实例 + 网关 CI | CI 编排 Java gateway + Eureka + 2 api 容器全链路 | 最完整 | 网关/Eureka 在**外部仓**（本仓零代码）；CI 引入 Java 栈 + 镜像编排，成本与验证收益完全不成比例；单仓 CI 管不了外部仓版本 | 弃（外部依赖越界 · 成本失真） |

### 双进程隔离形态（D2/D4 · 裁定）

| 方案 | 做法 | 收益 | 代价 | 裁决 |
|---|---|---|---|---|
| **P1 · subprocess 两 uvicorn 进程（本 SPEC）** | pytest fixture 起两个 uvicorn subprocess（同 PG DSN · 异端口 · 同 env 开关）· HTTP 断言 · 收尾杀进程 | 进程内单例真隔离（registry/budget/circuit 各一份 = 真跨实例）；与 hitl_persistence_smoke 的 .sh 壳同族形态；归属断言可落在 pid/端口 | 起停慢（秒级/用例族）· 须处理端口分配与就绪等待 | **推荐** |
| P2 · 同进程双 app 实例 | 两个 FastAPI app/TestClient 共享同进程 | 快 | **假跨实例**：模块级单例全共享，budget/registry 失真断言全部空真——恰是本 SPEC 要防的假阳性 | 弃（验证对象被测试形态架空） |

---

## 5. 边界 / 失败路径 / 安全（failure_paths）

| 触发 | 行为 | 可重试 |
|---|---|---|
| **假阳性「验证了但没真跨实例」**（测试形态共享进程内状态 / LB 实际只打到一个实例） | **静默错**（本 SPEC 头号风险）；防线三层：① D2 禁止同进程双 app（P2 弃选钉死）；② 每用例**实例归属先断言**（pid/端口/响应标识对拍 · 归属断言失败 = FAIL 非 skip）；③ runbook 混合负载断言两实例均有命中；变异检验 ① 兜底（同进程跑 → 归属断言必挂） | Y（修测试形态） |
| **进程内状态失真未发现**（budget 放大 / circuit 不共享 / registry 漂移 · 清单漏项） | **静默错**；D3 清单逐条带代码锚点 + 对照实测（配额放大实证断言总放行 > 单实例上限）；清单附全仓模块级状态扫描基线兜底漏项；既有 `snapshot() scope: process-local` 自首字段为对拍锚 | Y（补清单条目） |
| **配置漂移 A 开 B 关**（`LG_RAG_HTTP_CHECKPOINTER` / `OPS_*_PERSISTENCE` 两副本不一致） | resume 侧已有 fail-closed（503 不假装成功）；但 persistence A=db B=null = **防重/审批时有时无的静默错**；D2/D4 用例前置断言两进程配置生效；runbook 拓扑检查项含两实例 env 对拍 | Y（对齐配置重测） |
| **checkpoint 版本漂移**（两副本代码版本不同 · langgraph checkpoint 格式不兼容） | `stranded_checkpoint` 409 既有分支（resume.py :236-248 实测过 0.2→1.2 炸点）证明此风险真实；runbook 断言两实例镜像 digest 一致；实证报告记录版本指纹 | N（排空在飞审批 + 对齐版本） |
| **HITL「看起来批了但什么都没发生」** | 已知最坏形态（resume.py :5-7）；D4 断言链必须覆盖图真的续跑（state 推进 + answer 非空 + hitl.resumed/done 帧续写同 run_id），**只断 200 = 用例不合格** | Y |
| **双实例同时 setup() checkpoint 表** | `saver.setup()` 幂等（checkpointer.py :48,53 docstring）；D2 前置两进程并发启动不死锁实测（启动竞态实证一次） | Y |
| **验证污染数据残留**（实测造的 thread/run/hitl 申请留库） | hitl_persistence_smoke 清库收尾先例（造了什么删什么 · 报告清理数）；实测用**专用租户/用户标识**前缀；报告含清理断言 | Y |
| **网关不可用 / 外部仓版本不明** | 降级形态（compose 轻量 LB）顶上，报告**如实标注**网关形态与外部仓版本；禁止把降级形态写成「网关验证通过」（D1 钉死） | Y |
| **实测报告无法复核**（无命令/无输出/无环境指纹） | 报告字段族对齐 reconcile/backfill 先例：命令 · 关键输出摘录 · PASS/FAIL · git sha · 镜像 digest · recorded_at；缺字段 = 报告不收 | Y（补录重跑） |
| **验证中发现阻断性 bug** | 如实记 FAIL + 证据（复现步骤/日志/锚点）→ **另开 fix task**，本 SPEC 不顺手修（顺手修 = 证据失效 · 非范围钉死）；报告标注「发现即另开」条目 | — |

安全：验证只读面为主（replay/catalog/runtime）；写面限专用租户沙盒；实测报告不含真实用户数据/凭证；双进程测试用本地临时 PG schema 或专用库，不碰共享开发库。

---

## 6. 验收标准（task 直接可用）

### D1 · 部署验证（runbook + 报告）

- [ ] compose 双实例拓扑可起（共享同一 db）；报告标注网关形态（外部 Java 网关 / 降级 LB · 版本指纹）
- [ ] 无亲和对照：同会话连续请求落不同实例（归属标识对拍）· 鉴权 cookie 跨实例 200 · thread 历史跨实例一致
- [ ] 会话亲和对照（网关支持时）：同会话落同实例断言
- [ ] 混合负载 N 请求两实例均有命中（防「只打到一个」）
- [ ] `reports/multi_replica_verify/deploy_<ts>.yaml` 落盘：拓扑 · 断言逐项 PASS/FAIL · git sha / 镜像 digest · recorded_at

### D2 · 状态外置（双进程 pytest）

- [ ] 双进程 fixture：两独立 uvicorn 进程 · 同 PG 异端口 · 每用例**实例归属先断言**（失败 = FAIL 非 skip）
- [ ] A 起 run → B 经事件表 replay 全程帧（seq 连续 · 归属正确 · 内容一致）
- [ ] B 以他 user replay A 的 run → 404（跨实例归属语义保持）
- [ ] B 恢复段事件续写同 run_id 且 seq 接 last_seq（不重开不覆盖）
- [ ] 两进程前置配置断言（`LG_RAG_HTTP_CHECKPOINTER=postgres` 生效）；两进程并发启动 + 同时 `setup()` 不死锁

### D3 · 边界清单

- [ ] 清单落盘：≥ §2 D3 最小条目集 8 条 · 每条带 file:line 锚点 + 失真形态 + 处置建议
- [ ] 对照实测：budget 配额放大断言（2 实例同 session 总放行 > 单实例上限）；两实例 `/runtime` scope 字段对拍；两实例 `/catalog` 对拍一致
- [ ] 清单附全仓模块级进程内状态扫描基线（grep 基线 + 逐条已盘点/不适用标注）

### D4 · HITL 跨实例

- [ ] 双进程：A 挂起 → B 见申请 → B 批准 → B resume **图真的续跑**（state 推进 + answer 非空 + hitl.resumed/done 帧续写同 run_id · 不只断 200）
- [ ] 负路径：B 错 thread_id → 409；未开 checkpointer 实例 resume → 503
- [ ] runbook 轨：双容器 + 网关下同链路手工实测通过 · 报告留痕

### D5 · 图谱 / 文档 / 边界纪律

- [ ] 零 alembic（迁移 diff 为空断言）；零新路由/零新一级模块/零 SSE 事件；`./scripts/graph-compile.sh` 绿；若偏离 → 本 SPEC 回炉
- [ ] app/ 生产码 diff 为空（发现阻断性 bug → 报告「发现即另开 fix task」条目 · 不在本波修）
- [ ] spec README 占位表本 slug 移行（done 后由 CLOSE 流处理）

### 变异检验（不验收空真规则）

- [ ] ① 归属可检：D2 用例临时改为同进程双 app（或单进程打两次）→ 实例归属断言必挂；恢复后全绿
- [ ] ② 外置可检：B 进程临时换 InMemorySaver（或关 checkpointer 开关）→ 跨实例 resume/replay 断言必挂（证明断言真依赖 PG 外置而非进程内巧合）；恢复后全绿
- [ ] ③ 失真可检：budget 放大实证临时收回单实例 → 「总放行 > 单实例上限」断言必挂（证明实证真在打两个实例的计数）；恢复后全绿

### 工程

- [ ] 全量 `pytest tests` 绿；`ruff check app tests` 绿；diff 只含：tests/（双进程集成测）· scripts/acceptance/ · reports/multi_replica_verify/ · docs/（边界清单 + runbook 说明）· spec/README 索引

---

## 7. 思考轮控制（10-spec）

| 轮 | 结论摘要 | 状态 |
|---|---|---|
| R0 | 上游手册 L0 行（:369/:506 单实例未验证 ⚠️）+ §3.4 第三类；锚点逐个实扫确认/纠正占位：① **HITL 跨实例结构上天然成立**——resume 驱动器零进程内定位状态 · 定位全靠 thread_id → PG checkpoint · fail-closed 503 兜底 · stranded_checkpoint 409 证明版本漂移是真实风险；② 事件表/会话/auth 全在 PG · 鉴权天然无需亲和；③ 进程内状态边界初步清单 8 条目（registry 启动注册零运行时写端点漂移面小 · budget 配额按实例数放大失真最重 · circuit 默认 process-local(degraded) · metrics 各说各话 · idempotency/HITL store 须 =db）；④ Java 网关+Eureka 在**外部仓**（本仓 grep 零命中）→ 网关面只能手工实测；⑤ 仓内零 k8s 清单 · compose 单 api 服务；⑥ hitl_persistence_smoke / qdrant reconcile 为 runbook+报告形态先例，**双进程 pytest 仓内无先例须新建** | done |
| R1 | 范围 = D1 部署验证（runbook+报告）/ D2 状态外置（双进程 pytest · 核心）/ D3 边界清单（文档+对照实测）/ D4 HITL 跨实例（双轨）/ D5 图谱文档按实判；非范围 = 真投产 · 选型变更 · 容量灾备 · 进程内状态外置改造 · Java 仓改动 · k8s 新建 · 生产码修复（发现即另开 fix task）· SSE 无缝迁移（占位原文沿用并据实扫扩列） | done |
| R2 | 判定形态三案：选 **F1 双轨组合**（弃 F2 纯手工：零 CI 回归保护 · 「验证过」贬值成「曾经验证过」；弃 F3 全自动网关 CI：网关在外仓 · CI 引入 Java 栈成本失真）；双进程隔离两案：选 **P1 subprocess 两 uvicorn**（弃 P2 同进程双 app：模块级单例全共享 = 假跨实例，恰是要防的假阳性） | done |
| R3 | failure_paths 10 条；两静默错定性：假阳性「没真跨实例」（防线：禁同进程形态 + 归属先断言 FAIL 非 skip + 变异检验①）与进程内状态失真未发现（防线：清单锚点 + 对照实测 + 扫描基线兜底漏项）；配置漂移 A 开 B 关为「防重时有时无」静默错（前置配置断言）；版本漂移由 stranded_checkpoint 既有分支证明真实；验证不顺手修被验证对象钉死 | done |
| R4 | 验收全为可执行断言：归属先断言 · A 起 B 恢复/404/续写 seq · 配额放大实证 · HITL「图真的续跑」不只断 200 · 报告字段族含环境指纹；变异检验三条（归属/外置/失真各一）；工程面 diff 白名单（零 app/ 生产码） | done |
| R5 | SPEC draft-complete 可交人签（HG-SPEC-SIGNOFF 落稿时待签）；签后 00 出 task（slug `multi-replica-verify` · failure_paths 沿用 §5 · 预期零图谱义务零 alembic · 铁律：双进程真隔离 · 归属先断言 · 验证≠投产 · 发现 bug 另开 fix task 不顺手修）；track 裁定 `verify`（实证类 · 预期零生产码改动 · 产物=验证方案+实测证据+边界清单） | done |
| early_stop | no | — |
| residual_risks | ① 双进程 pytest 基建仓内无先例——起停稳定性（端口冲突/就绪等待/收尾杀进程）是 30 阶段实做风险，hitl_persistence_smoke 的 .sh 壳可参照但 pytest fixture 化是新建；② 外部 Java 网关实测可用性不受本仓控制——网关不可得时 D1 走降级 LB 形态，「网关+Eureka 注册 2 实例」这一条只能标注未覆盖待补；③ 边界清单的「处置建议」是建议不是承诺——budget/circuit 外置改造的优先级裁决留给人签与后续 SPEC；④ 验证结论有时效：checkpointer/resume/事件表语义后续漂移时，双进程 pytest 在 CI 兜住核心语义，runbook 轨结论随时间贬值须复跑 | 签收时知悉 |

---

## 8. 下一棒

1. **维护者**：审本 SPEC → 签 `HG-SPEC-SIGNOFF=approved`
2. **00**：起草 `docs/tasks/active/task_multi_replica_verify.md`（范围 §2 D1–D5 · failure_paths 沿用 §5 · 人工闸表：HG-GRAPH-MODULES 预期无义务按实判 · 无 alembic · 变异检验三条入验收 · 铁律：双进程真隔离（禁同进程双 app）· 每用例实例归属先断言（FAIL 非 skip）· 验证≠投产 · app/ 生产码零改动（发现阻断性 bug 另开 fix task 不顺手修）· HITL 断言链覆盖「图真的续跑」不只断 200 · 报告字段族含环境指纹）
3. **20-task-audit**：书面审 → 维护者签 `HG-AUDIT-R1`
4. **30**：`task/multi-replica-verify` 分支实施（D2 双进程基建先行 → D4 HITL 双进程 → D3 清单+对照实测 → D1 runbook+实测 → D5 文档）
5. **40**：验收（含变异检验三条）→ PR（与 memory-compliance-delete 等同模式）

### 下一棒可复制 Prompt（20-spec-audit 预审 / 00 起草 task）

```text
你是 ops-desk-api 仓（/Users/cyning/Desktop/Ops-desk/ops-desk-api）的 <20-spec-audit ｜ 00>。
SPEC：docs/spec/multi-replica-verify/SPEC-multi-replica-verify_v1.md（draft-complete · HG-SPEC-SIGNOFF 待签）。
<20-spec-audit>：书面审范围/非范围/验收/failure_paths 与 R0–R5 思考轮（重点：验证≠投产定性 · F1 双轨 vs F2/F3 裁决 · P1 双进程真隔离 vs P2 假跨实例裁决 · 假阳性「没真跨实例」防线可执行性 · HITL 跨实例「天然成立」结论的证据充分性 · 发现 bug 不顺手修的纪律），结论落盘 docs/harness/reviews/，不代签人闸。
<00>：待维护者签 HG-SPEC-SIGNOFF=approved 后，按 SPEC §8 起草 docs/tasks/active/task_multi_replica_verify.md（D1–D5 · failure_paths 沿用 SPEC §5 · HG-GRAPH-MODULES 预期无义务按实判 · 无 alembic · 铁律：双进程真隔离、归属先断言 FAIL 非 skip、验证≠投产、app/ 生产码零改动（发现 bug 另开 fix task）、HITL 断言「图真的续跑」、报告含环境指纹）。
```

---

## 修订

| 日期 | 说明 |
|---|---|
| 2026-09-21 | 占位稿（范围草案 + 锚点 + 验收方向 + 接续指引） |
| 2026-09-22 | 10-spec 补全：锚点逐个实扫（checkpointer 单开关同库 · event_store PG 表归属反查 · **hitl/resume 零进程内定位状态——A 挂起 B resume 结构上天然成立，前提=两副本同开 PG 开关+同库+同版本（stranded_checkpoint 409 证明版本漂移真实）** · capability 进程内状态八条目盘点（registry 启动注册零运行时写端点 · budget 配额按实例数放大 · circuit 默认 process-local(degraded) · metrics 进程内 · idempotency/HITL store 须 =db） · 部署面：仓内 Dockerfile+compose 单 api+GHA，零 k8s，Java 网关+Eureka 在外部仓 · auth 会话 DB 存无需亲和 · 先例：hitl_persistence_smoke/qdrant reconcile，双进程 pytest 仓内无先例）；**track 裁定 `verify`**（实证类 · 预期零生产码改动 · 发现阻断性 bug 另开 fix task）；**F1 双轨裁定**（双进程 pytest 核心语义 + runbook+实测报告部署面 · 弃 F2 纯手工零回归 · 弃 F3 网关 CI 外部依赖越界）；**P1 subprocess 双进程裁定**（弃 P2 同进程双 app 假跨实例）；failure_paths 10 条（假阳性「没真跨实例」与进程内状态失真未发现两静默错防线钉死）；R0–R5 回填；HG-SPEC-SIGNOFF 保持待签 |
