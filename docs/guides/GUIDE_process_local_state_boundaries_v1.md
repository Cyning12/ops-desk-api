# GUIDE · 进程内状态边界清单（多副本失真盘点 · v1）

> **任务**：`multi-replica-verify` D3（SPEC §2 D3 / §6-D3）· 2026-09-22 30 帽实扫落盘
> **定性**：verify 轨产物 —— **盘点与实证失真，不做外置改造**（改造另开 SPEC，非范围钉死）
> **实证来源**：`tests/test_multi_replica_dualproc.py`（双进程 pytest · 9 用例）

> [!IMPORTANT] 「处置建议」是建议不是承诺（SPEC §7 ③）：外置改造的优先级裁决留给人签与后续 SPEC。

---

## 判定总表（8 条目最小集 + 实证结论）

| # | 状态 | 锚点（file:line · 2026-09-22 复核） | 多副本失真形态 | 既有自首 | 处置建议 | 实证 |
|---|------|----------------------------------|----------------|----------|----------|------|
| 1 | capability registry（进程内单例） | `app/ops/capability/gateway.py:81`（`_registry = CapabilityRegistry()` 模块级单例）· `app/ops/capability/registry.py:29-32`（docstring「进程内注册表」+ `_entries` dict）· `registry.py:38-40`（拒绝覆盖钉死） | 注册仅发生在启动 import 路径（`capability/__init__.py` ensure_default_capabilities / manifests），运行时零注册端点（`admin/capability.py` 五端点全 GET 只读）→ 同镜像同 env 各副本一致；漂移面 = 部署配置漂移（镜像/env 不一致才会分叉） | docstring 明示「进程内注册表」（图谱 capability 行同步明示「非跨进程注册中心」） | **现接受**；引入运行时注册/远程 manifest 拉取之日须重估（那时漂移面从部署期移到运行期） | ✅ `test_runtime_scope_and_catalog_parity`：两实例 `/catalog` `visible_ids` 对拍一致 |
| 2 | budget per-session 配额 + 拦截计数 | `app/ops/capability/budget.py:51-56`（`_LOCK` + `_SESSIONS` + `_BLOCKED_*` 进程内）· `budget.py:62`（`MAX_TRACKED_SESSIONS=512` 插入序淘汰 · 被淘汰会话配额归零）· `budget.py:22-24`（docstring 自首「多实例各进程各一份」） | **最重失真**：配额按实例数放大（N 副本 ≈ N× 上限）· 会话跳实例 = 配额重置（换桶重数）；写操作上限同理放大，失控兜底被稀释 | `snapshot()` 显式 `scope: process-local`（`budget.py:246`） | **现接受**（泄流兜底量级 · 见 budget docstring「分布式计数当前阶段不值得」）；若配额语义升级为**硬限额**（资损面）则须外置 DB/Redis 计数 | ✅ `test_budget_quota_amplification_across_instances`：上限 2 · A 放行 2 + B 放行 2 = 总 4 > 2（变异③ 收回单实例 → 断言必挂实证可检） |
| 3 | kill switch | `app/ops/capability/budget.py:83-85`（`kill_switch_patterns()` 每次调用读 env）· `budget.py:44`（`OPS_CAPABILITY_KILL_SWITCH`） | 无进程内记忆：每次读 env → 副本一致性 = 部署 env 一致性；A 按 B 不按的唯一形态是 env 漂移（配置问题不是状态问题） | 「只支持全局」docstring 明示 | **现接受**；runbook 拓扑检查项含两实例 env 对拍兜底漂移 | ✅ 双进程 fixture 两进程同 env；`whoami` 前置断言配置生效 |
| 4 | circuit breaker（capability 下游熔断） | `app/ops/capability/circuit.py:71-72`（`_LOCK` + `_BREAKERS` 进程内）· `app/ops/capability/circuit_storage.py:45-47`（默认 `mock-unavailable` 刻意逼回落路径 · Redis 共享路径已设计未接）· `circuit.py:317-325`（`snapshot()` 显式 `scope`/`degraded`/`redis_error`） | **A 熔 B 照打**：故障期拉长 N 倍（每副本各自积累失败才熔断）；默认后端下 `scope=process-local(degraded)` | snapshot 显式 scope + degraded + redis_error 三字段 | **现接受**（默认 degraded 已如实上报）；`circuit-storage` Redis 路径接通之日失真消除（接通 = 另开 SPEC · 非本 task 范围） | ✅ `/runtime` `circuits.scope` 字段对拍（runtime 断言内含）；图谱/清单记录在案 |
| 5 | metrics（进程内计数） | `app/ops/capability/metrics.py:1-13`（docstring 自首「多实例下各进程各一份，这是已知边界」· 不引 Prometheus）· `metrics.py:24-36`（`_LOCK` + `_BY_CAPABILITY`/`_BY_OUTCOME`/`_DEGRADED_*`） | `/metrics` 各说各话：任一单实例读数 ≠ 全局；`write.blocked` 等红线指标须聚合才有意义 | docstring 明示 + 「要接监控在 /metrics 外套 exporter」 | **现接受**；接监控系统时走 exporter 聚合（外部动作） | ✅ 清单记录在案（观测面 · 不阻断多副本） |
| 6 | idempotency / receipts（防重与回执） | `app/ops/capability/persistence.py:1-13`（装配表：`db`/`memory`/默认 `null` 不防重告警「不能上生产」）· `app/ops/capability/idempotency.py:45-52`（`DbIdempotencyStore` (tenant,key) 唯一约束跨实例 · 租约判定交 DB 时钟 `now()` —— 多实例时钟偏差坑明示） | `=db` 跨实例防重成立（唯一约束兜底）；`=null`/`memory` 多副本下**防重时有时无**；配置漂移（A=db B=null）= 静默错 | 装配 docstring「显式选不自动探测」+ Null 告警 | **多副本生产必须显式 `db`**（纪律项）；时钟偏差由 DB 时钟化解已在案 | ✅ 双进程前置断言 `capability_persistence.mode == db` 且 `idempotency.scope == cross_instance`（两实例同） |
| 7 | HITL store（审批申请） | `app/ops/hitl/persistence.py:1-13`（装配表同纪律：默认 `null` 不落库告警「不能上生产」）· `persistence.py:28`（`_STORE` 进程级装配点） | `=db` → `DbHitlStore` 跨实例跨重启（申请 B 可见）；`=null` 进程内不落库 → 多副本下「人在等一个不存在的审批」；A=db B=null = 审批时有时无静默错 | Null 告警 + docstring | **多副本生产必须显式 `db`**（纪律项） | ✅ `test_hitl_cross_instance_resume`：A 挂起申请 → B 签名拉待办可见 → B 批准 → B resume 续跑 |
| 8 | SSE live 流（在飞帧） | `app/ops/lg_rag/sse_stream.py:20-22`（docstring：PG checkpointer 整个流期间持有 · 挂起帧翻译）· live 帧只在服务该连接的进程内 | live 中途换实例 = 断连；断连后 replay 走 PG 事件表 cursor 续传（**非无缝** · 既有设计兜底 · 无缝化另案非范围） | replay 通道 + cursor 机制既有 | **现接受**（断连重连语义既有）；无缝迁移另案 | ✅ `test_cross_instance_replay`：A 的 run 帧 B 经事件表 replay 全程一致（续传成立的实证面） |

## 对照实测定量记录（双进程 pytest · 2026-09-22）

| 实证 | 形态 | 结果 |
|------|------|------|
| budget 配额放大 | `OPS_CAPABILITY_MAX_CALLS_PER_SESSION=2` 两实例 · 同 session A×2 + B×2 | **总放行 4 > 单实例上限 2**（A 侧第 3 次 `budget_exhausted` 拦回 · 上限本身生效）；`/runtime` snapshot：A 有该 session 计数、B 没有（计数分家实证） |
| `/runtime` scope 对拍 | 两实例 `budget.scope` | 均 `process-local`（自首字段两实例一致如实） |
| `/catalog` 对拍 | 两实例 `visible_ids` | 完全一致（registry 启动注册零漂移） |
| 变异③ 失真可检 | `MR_BUDGET_SINGLE=1` 收回单实例 | 「总放行 > 单实例上限」断言必挂（`总放行 2 ≯ 2`）→ 实证真在打两个实例的计数 |

## 全仓模块级进程内状态扫描基线（兜底漏项 · 2026-09-22 真跑）

扫描口径：`grep -rn "threading.Lock()" app/` · `grep -rn "^_LOCK" app/` · 模块级可变单例正则 `^_[A-Z_]+: (dict|list|set)` · `ContextVar` 扫。逐条处置：

| 命中 | 处置 | 说明 |
|------|------|------|
| `app/ops/capability/budget.py:51,53,56`（`_LOCK`/`_SESSIONS`/`_EVICTED_SESSIONS`） | **已盘点**（条目 2） | 配额放大失真实证在案 |
| `app/ops/capability/circuit.py:71-72`（`_LOCK`/`_BREAKERS`） | **已盘点**（条目 4） | A 熔 B 照打在案 |
| `app/ops/capability/metrics.py:24-36`（`_LOCK`/`_BY_*`/`_DEGRADED_*`） | **已盘点**（条目 5） | 各说各话在案 |
| `app/ops/capability/fallback.py:94-96`（`_CACHE_MAX_ENTRIES`/`_LOCK`/`_CACHE`） | **已盘点**（本行补录 · 第八条目外新增） | 降级缓存进程内有界：A 缓存命中的降级结果 B 没有 → 同一调用两副本可给出「降级/实时」不同答案。**现接受**（降级本就是业务决策 · TTL 300s 有界）；一致性敏感场景须注意 |
| `app/ops/capability/idempotency.py:184` / `receipts.py:86`（实例内 `_lock`） | 不适用 | `InMemory*` 实现内部的锁 —— 仅 `=memory` 装配用；生产 `=db` 不经过；进程内语义已随条目 6 盘点 |
| `app/llm/circuit.py:52-53`（`_LOCK`/`_BREAKERS`） | **已盘点**（随条目 4 同源） | LLM provider 熔断进程内：与 capability 熔断同形态（A 熔 B 照打）；`OPS_LLM_CB_*` env 一致性 = 部署一致性 |
| `app/ops/capability/manifest.py:101,107`（`_LAST_META`/`_FILE_IDS`） | 不适用 | 启动期加载的 manifest 元数据缓存（同镜像同文件 → 各副本一致；漂移面 = 部署面） |
| `app/ops/capability/registry.py:29-32` + `gateway.py:81`（`_registry`） | **已盘点**（条目 1） | 启动注册零运行时写端点 |
| `app/ops/hitl/persistence.py:28` / `app/ops/capability/persistence.py`（`_STORE` 装配点） | **已盘点**（条目 6/7） | 装配是部署动作 · 进程级单例 holder 非业务状态 |
| `app/ops/capability/circuit_storage.py:50`（`_last_redis_error`） | 不适用 | 观测回显字段（snapshot 如实带出）· 非决策状态 |
| `app/ops/rag/glossary.py:19`（`_ZH_TO_EN` 惰性缓存） | 不适用 | 只读词典文件缓存（同镜像一致） |
| `ContextVar` 族（`app/llm/usage.py:44` · `app/ops/tenant_context.py:16` · `lc_evidence_chain/step_hook.py:18` · `answer_stream`/`progress_stream` sink） | 不适用 | 请求/task 级上下文（每请求独立）· 非跨请求进程状态 |
| 其余模块级 dict/list（`_PROVIDERS`/`_GRADER_PROMPTS`/`_TASK_DIRS`/`_DEFAULT_*`/`_PROBE_SPECS`/`_TYPE_MAP`/schema 常量等） | 不适用 | 启动期常量表（只读 · 同镜像一致） |

**漏项兜底结论**：扫描命中的**可变跨请求**进程内状态 = 清单 8 条目 + fallback 降级缓存（本表补录）；其余均为启动期常量 / 请求级 contextvar / 观测回显，逐条标注如上。

## 跨实例成立面（对照 · 非进程内）

以下状态**已在 PG/DB**，双进程实证成立（D2/D4 用例）：

| 状态 | 锚点 | 实证 |
|------|------|------|
| LangGraph checkpoint | `app/ops/lg_rag/checkpointer.py:27`（单开关）· `:41-43`（同库不同表）· `:48-53`（setup 幂等） | A 挂起 → B resume 续跑（`test_hitl_cross_instance_resume`）；并发 setup 不死锁（`test_concurrent_startup_setup_no_deadlock`） |
| SSE 事件表 | `app/ops/lg_rag/event_store.py:34-47`（每帧独立 commit）· `:50-69`（归属反查）· `:87-95`（跨用户 404）· `:72-84`（last_seq 续写） | B replay A 的 run 逐帧一致（`test_cross_instance_replay`）；他 user 404（`test_cross_user_replay_404`）；恢复段 seq 接 last_seq（D4 断言链） |
| auth 会话 | `app/db/models.py:66-83`（`ops_sessions` DB 存）· `app/ops/deps.py:18-53` | 鉴权天然无状态无需会话亲和（D1 runbook 轨 cookie 跨实例 200 实证） |
| HITL resume 驱动 | `app/ops/hitl/resume.py:329-336`（未开开关 fail-closed 503）· `:236-248`（stranded_checkpoint 409 版本漂移实证锚）· `:338`（每次新开 saver 零进程内定位状态） | 503/409 负路径双进程实证（`test_resume_without_checkpointer_503` / `test_resume_wrong_thread_409`） |

---

## 修订

| 日期 | 说明 |
|------|------|
| 2026-09-22 | v1 落盘（task multi-replica-verify D3 · 8 条目 + fallback 缓存补录 + 扫描基线兜底 + 双进程实证结论） |
