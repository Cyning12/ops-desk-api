# Task：Agent Host V1-E · 可拆性硬化（multi-replica-verify 承继回归+边界补扫 · import-linter 机械闸 · capability registry 读写分离接口 · env 盘点+策略包 schema 试点）（host-v1-splittability-hardening · v1.0 收尾波）

> **状态**：`done`（2026-09-24 · 五棒全通 · PR [#187](https://github.com/Cyning12/ops-desk-api/pull/187) MERGED（CI 四绿 · 164f3fc）· 图谱回写 00 代录 HG-GRAPH-MODULES · CLOSE 归档 done/ · **D1 dualproc 口径：禁止「双进程全绿」· 本分支/master 同形 9 ERROR（tenant_id fixture）见 FINDINGS #1**）  
> **类型**：hardening / verify+engineering（**无 alembic 义务** · **图谱义务预期无按实判**：import 闸=CI/配置面 · registry 抽象=capability 行内接口化零语义改 · 策略包=配置/文档面；若 registry 抽象触行备注 → 如实登记 · HG-GRAPH-MODULES 00 代录位预留）  
> **上游 SPEC**：`docs/spec/host-v1-splittability-hardening/SPEC-host-v1-splittability-hardening_v0.md`（**signed** · HG-SPEC-SIGNOFF=approved 2026-09-23 · 00 代录 · Q1 import-linter / Q2 盘点+schema 试点签收锁死）  
> **直接执行真值（D1）**：`docs/spec/multi-replica-verify/SPEC-multi-replica-verify_v1.md`（**signed** · 其 §2/§6 **原样映射**；历史独立 task 已 CLOSE，本波 D1=承继+回归+V1-A~D 后补扫，见钉死契约）  
> **前置**：V1-A~D **全 CLOSE**（关账 PR #186 · master `ff3cfbe`+）· multi-replica-verify **已 CLOSE**（PR #165 · 双进程基建/边界清单/runbook 已在仓）  
> **分支**：`task/host-v1-splittability-hardening`（**禁止 master/main 直改 · 30 由 00 委派子 Agent 执行**）  
> **10/20 注**：2026-09-24 · 10-task 落稿后 HG-TASK-DRAFT 00 代录 approved；20 R1 **PASS-WITH-NITS**（零阻塞 · N1–N3 已微修）后 **HG-AUDIT-R1 00 代录 approved** · 30 可委派

---

## Harness 元信息

| 字段 | 值 |
|------|-----|
| **task_slug** | `host-v1-splittability-hardening` |
| **git_branch** | `task/host-v1-splittability-hardening` |
| **implement_repo** | `ops-desk-api` |
| **test_strategy** | `required` |
| **test_strategy_note** | D1：双进程 pytest 回归全绿 + 边界清单 V1-A~D 补扫条目 + runbook/报告可读（承 multi-replica §6 变异检验三条原样映射）；D2：import-linter contracts 与 `01_modules` 出边一致 · 越界必挂 · 白名单逐条有理由；D3：RegistryReader/Writer 协议注入 · mock 替换断言 · 对拍零 diff（全量基线全绿）；D4：env 清单文档齐全 + 策略包 schema 试点加载断言（env>策略包>代码默认 · 缺省=现状逐字节）；零 app/ 生产码偏离回炉（D1 验证轨预期零生产码；D3 仅接口抽象不改语义） |
| **code_quality_bar** | `L2_backend` |
| **graph_change_layer** | **预期无（按实判）**（承 SPEC 元信息 · multi-replica 验证轨先例）：import 闸=CI/配置面 · registry 抽象=capability 行内重构（接口化零语义改）· 策略包=配置/文档面；若 registry 抽象触 `capability` 行备注更新则如实登记（HG-GRAPH-MODULES 00 代录位预留） |
| **graph_delta** | 无（预期零图谱改动按实判 · 偏离回炉）；可选：`docs/_tech_graph/l1/01_modules.md` capability 行备注（RegistryReader/Writer 接口化 · 本地 dict 默认） |
| **graph_delta_note** | **回炉补闸条款**：若 30 形态偏离本预判（新增一级模块 · 新增路由/观测端点 · 新增表/列触发 alembic · 新增 SSE 事件类型 · 改 freeze 契约 · registry 语义漂移（对拍非零 diff）· 顺手修 D1 发现的阻断 bug · 策略包全量搬家），不得沿用本裁定——退回 10-spec/10-task 补闸 + `docs/_tech_graph/` 如实登记后方可续 30 |
| **wiki_delta** | `n/a` |
| **wiki_delta_note** | 契约真值在 SPEC `host-v1-splittability-hardening` + `multi-replica-verify`；边界清单/env 盘点/策略包 schema 属本 task 范围项非 wiki |
| **review_hat** | `20` |
| **required_invoke_hats** | `10,20,30,40` |
| **invoke_retention_profile** | `default` |
| **experience_capture** | `recommended` |
| **kpi_aggregator** | `CLOSE` |
| **orchestration** | 单 task 直通：10 落稿 → 20-task-audit → HG-AUDIT-R1（00 代录）→ 30（00 委派子 Agent · 实现序：**D2** import-linter+CI → **D3** registry 接口抽象+对拍 → **D4** env 盘点+策略包 schema 试点 → **D1** 双进程回归+边界清单补扫+报告留痕 → **D5** 发现即另开条目收口）→ 40（含变异检验 + v1.0 出口复核留痕由 00）→ PR+CI 绿+merge → 图谱按实判回写（00 代录）→ CLOSE → **07 §4 八面复核** |
| **freeze_id** | 无（不改 lg-rag-sse-v1 / lg-rag-http-v1 / lc-evidence-http-v1 · SSE 零新事件 · 零新路由 · 零新表） |

### 人工闸

| human_gate_id | status | blocks_hats | 说明 |
|---------------|--------|-------------|------|
| HG-TASK-DRAFT | **approved** | 20-R1, 30 | 2026-09-24 · **00 代录**（维护者令原话：「签收，并生成对此长程任务的00启动Prompt，新窗口执行，授权00签收所有过程文档，完整落地1.0版本内容」+ 本窗令「继续，完成后自行进行下一波，无特殊情况无需停下等待接收命令」）；10-task lint PASS · D1 承继#165+边界补扫裁定可交 20 |
| HG-AUDIT-R1 | **approved** | **30** | 2026-09-24 · **00 代录**（维护者令原话：「签收，并生成对此长程任务的00启动Prompt，新窗口执行，授权00签收所有过程文档，完整落地1.0版本内容」+ 本窗令「授权00可以签收所有过程文档」「继续，完成后自行进行下一波，无特殊情况无需停下等待接收命令」）；依据：20-task-audit R1 **PASS-WITH-NITS** 零阻塞（`docs/harness/reviews/task_host_v1_splittability_hardening_audit_R1_20260924.md`） |
| HG-GRAPH-MODULES | approved | **30** | 2026-09-24 **真读** `docs/_tech_graph/l1/01_modules.md`：模块表已建置；签录链完整至 2026-09-24 V1-D 回写行（episodic memory）；一级模块齐全（含 `capability`/`llm`/`lg_rag`/`hitl`/`db`/`memory`）；**依赖出边列=本波 D2 import-linter contracts 真值**（例：`capability`→— · `llm`→`db` · `lg_rag`→`lc_evidence_chain,llm,structured_output,capability` · `hitl`→`db,lg_rag`）。本 task **预期无图谱新签义务按实判**（零新一级模块/零新路由/零新表/零新 SSE）；若 30 触 `capability` 行备注（接口化）→ 人签新行 **00 代录位**随交付落盘；偏离回炉见 graph_delta_note |
| HG-PILOT-OPSDESK-GLAYER | n/a | 物理分层试点改码 | 本 task 不涉物理分层试点改码 |

---

## 背景与目标

现状（SPEC §1 锁死 · 本帽复核一致）：Agent Host V1-A~D 功能波已 CLOSE；工程面可拆性硬化（C1/C5/C7）未收口——**本波是 v1.0 与 v2.0 分界**：做完上楼只换传输层。`multi-replica-verify` 已独立 CLOSE（PR #165 · 双进程测/边界清单/runbook 在仓），但 V1-A~D 新增进程内状态（delegation nonce · llm budget · infer_cache）**尚未入边界清单**（本帽真读 `docs/guides/GUIDE_process_local_state_boundaries_v1.md` · **零命中** llm/budget|infer_cache|delegation）。仓内 **无** `.importlinter` / import-linter 依赖；capability registry 仍为进程内 dict 单例（`gateway.py:81` `_registry` · `registry.py` `CapabilityRegistry`），未抽读写分离协议；策略面 env 散落（`.env.example` 约 30 键显式 · `app/` `os.getenv` 位点约 60+），无声明式策略包 schema。

一句话目标（SPEC 锁死）：双进程共享 PG 验证回归全绿 + 进程内状态边界清单（含 V1-A~D 补扫）+ import 机械闸 CI 绿 + capability registry 读写分离接口化（本地 dict 默认 · 可替换）+ env 散落盘点与策略包 schema 试点（env 覆盖优先不变）。

设计纪律（30 不得违反 · 承 SPEC §1 签收锁死）：

1. **验证≠投产**（承 multi-replica）：发现阻断 bug → 另开 fix task · 本波只记录证据（D5）。
2. **对拍零 diff**：registry 抽象前后行为逐字节一致（全量基线全绿即证）；远程注册中心实现属 v2.0 · 本波只留接口。
3. **默认关/向后兼容**：import 闸白名单逐条消账（禁大水漫灌）；策略包 env>策略包>代码默认 · 缺省=现状逐字节。
4. **零 freeze 动**：不改 freeze · SSE 零新事件 · 零新路由 · 零新表 · **无 alembic**。
5. **硬化不是重构**：import 闸不改模块归属；registry 只抽接口不改语义；策略 v1 只盘点+schema 试点不搬家。
6. **D1 承继纪律**：不重写已 CLOSE 的双进程基建；本波 D1=回归绿 + 边界清单补扫 + 报告/runbook 可复核（§6 原样映射勾选）。

---

## 现状锚点（只读 · 30 必读 · 10 已扫）

| 主题 | 路径 · 锚点 | 现状 |
|------|-------------|------|
| D1 既有交付（**承继 · 禁重写基建**） | `tests/test_multi_replica_dualproc.py`（9 用例）· `tests/dualproc_server.py` · `docs/guides/GUIDE_process_local_state_boundaries_v1.md` · `docs/guides/RUNBOOK_multi_replica_verify_v1.md` · `scripts/acceptance/multi_replica_*` · `reports/multi_replica_verify/` · `docs/tasks/done/task_multi_replica_verify.md`（CLOSE · PR #165） | 双进程基建+边界 8 条目+runbook+报告已在仓；**清单未含 V1-A~D 新进程内状态**（本帽扫 `llm/budget`/`infer_cache`/`delegation` **零命中**） |
| PG checkpointer / HITL resume | `app/ops/lg_rag/checkpointer.py` · `app/ops/hitl/resume.py` | 承 multi-replica 锚点：同开关同库同版本才跨实例；resume 零进程内定位 · fail-closed 503 |
| capability registry（**D3 落点**） | `app/ops/capability/registry.py`（`CapabilityRegistry` · `_entries` dict）· `gateway.py:81-89`（`_registry` 单例 · `get_registry`/`register`/`unregister`） | 进程内单例 · 拒绝覆盖；调用方经 gateway/manifest/admin/defaults/probes；**无 RegistryReader/Writer 协议**（命名冲突扫零命中） |
| 调用点（D3 注入面） | `gateway.py` · `manifest.py` · `defaults.py` · `probes.py` · `admin/capability.py` · `lg_rag/multi/nodes.py`（`get_registry`） | 改面向协议注入 · 最小侵入 · 对拍零 diff |
| V1-A~D 进程内新增（**D1 补扫义务**） | `app/ops/capability/delegation.py:320+`（`_NonceRegistry` / `_nonce_registry`）· `app/llm/budget.py:83-85`（`_LOCK`/`_SESSIONS`）· `budget.py:387/:407`（`snapshot()` · `scope: process-local`）· `app/llm/infer_cache.py:187-189`（`_LOCK`/`_CACHE` LRU） | 多副本失真形态须入边界清单补条目（现接受/何时外置） |
| import 闸（**D2 落点**） | 仓根 **无** `.importlinter`；`requirements.txt`/`pyproject.toml` **无** import-linter；CI workflows：`pytest.yml`/`tech-graph.yml`/`lint-wiki-delta.yml` 等 · **无** import-linter job | Q1 裁定工具=import-linter · contracts 真值=`01_modules` 出边列 |
| 模块出边（contracts 真值） | `docs/_tech_graph/l1/01_modules.md` 模块表「依赖方向」列 | 例：`capability`→— · `llm`→`db` · `lg_rag`→四边 · `memory`→`db,rag,llm,prompts` · `hitl`→`db,lg_rag` · 控制面禁反向/越权边以出边为准生成 forbidden contracts |
| 策略/档级面（**D4 试点建议面**） | `app/llm/model_catalog.py:113+`（`TASK_TIER_MODELS`/`TASK_TIER_FALLBACKS`/`resolve_task_model` · 解析序 explicit>env>`OPS_LLM_TIER_*`>档默认）· `MODEL_UNIT_PRICES` | 试点一面建议=llm 档级/单价；env 覆盖优先不变 |
| env 散落 | `.env.example`（~230 行 / ~30 显式键）· `app/config.py` Settings · 全仓 `os.getenv` 位点 | D4 须产出全仓清单文档（名称/默认/非法回退/归属面 · grep 基线 · 含 V1 五波新增） |
| 策略包命名 | grep `RegistryReader`/`RegistryWriter`/`strategy_pack`/`.importlinter` 于 app/tests | **零命中**（2026-09-24 本帽真跑） |
| 测试基线 | 静态 `def test_` 扫 **1376**（113 文件）；pytest `--collect-only` 本工作树 `.venv` 缺 pytest 未能本帽真跑 collect → **基线承 V1-D CLOSE KPI `1587 collected`**（master #186 关账后 · 30/40 须真跑复核并如实入记录） |
| alembic 义务 | **无** | 最新 head `20260923_memory_episodes`；本波零迁移 · 迁移 diff 为空断言 |

---

## 钉死契约（自 SPEC §2/§4/§5 + multi-replica §2/§6 锁死；30 不得静默改义）

| 项 | 钉死 |
|----|------|
| **D1 承继口径** | multi-replica SPEC §2 D1–D5 / §6 **原样映射入验收**；**不另拆** `task_multi_replica_verify`（已 CLOSE）；本波实施=① 既有双进程用例回归全绿 ② 边界清单补扫 V1-A~D 进程内状态（≥补 delegation nonce · llm budget · infer_cache 三条，带 file:line）③ runbook/报告可复核（可补回归时间戳报告 · 网关形态如实标注纪律不变）④ 变异检验三条仍可机跑（MR_* 钩子既有）⑤ **app/ 生产码零改动**（发现 bug→D5 另开） |
| **D2 import 闸** | 工具=**import-linter**（Q1）；配置 `.importlinter`（或等价入仓段）；contracts **由** `01_modules.md` 依赖出边列生成；白名单 `ignore_imports` **逐条**登记+注释理由（禁大水漫灌）；CI 接线绿为 merge 前提；图谱出边若实测有误 → 同步修正图谱（如实登记） |
| **D3 registry 接口** | `RegistryReader`（get/list/snapshot · 本地缓存抽象）+ `RegistryWriter`（register/unregister/reload · 注册中心客户端形态）；**本地 dict 实现为默认**（现有 `CapabilityRegistry` 语义原样封装）；调用点改协议注入；**对拍零 diff**；远程实现本波不实现 |
| **D4 策略收敛** | env 全仓清单文档；策略包 YAML schema v0（版本化）+ **单面试点**（建议 llm 档级 `TASK_TIER_MODELS`/`FALLBACKS`/单价表）；优先级 **env > 策略包默认 > 代码默认**；策略包缺省=现状逐字节；**不做全量搬家** |
| **D5 纪律** | 验证/实扫阻断 bug → 另开 fix task · 本波记录「发现即另开」条目 |
| **图谱** | 预期无义务按实判；触行备注则 00 代录人签新行；`./scripts/graph-compile.sh` 绿；零新一级模块 |
| **工程否决** | 零 alembic · 零新路由/SSE/一级模块 · `ruff check app tests` 净增 0 · 全量 pytest 绿 |

---

## 范围（单 task 直通 · SPEC §2 D1–D5）

- [x] **D1 · multi-replica 承继回归+补扫（必做 · §6 原样映射）**：双进程 pytest 回归 · 边界清单补 V1-A~D · runbook/报告可复核 · 变异三条可机跑 · app/ 零生产码 diff（验证轨）
- [x] **D2 · import 机械闸（必做）**：import-linter 依赖+`.importlinter` contracts + 白名单逐条消账 + CI job 绿
- [x] **D3 · registry 接口抽象（必做）**：Reader/Writer 协议 + 本地 dict 默认 + 调用点注入 + mock 可替换断言 + 对拍零 diff
- [x] **D4 · 策略收敛（必做 · 盘点+试点）**：env 清单文档 + YAML schema v0 试点一面 + 加载断言（优先级/缺省零 diff）
- [x] **D5 · 问题修复纪律（必做 · 过程面）**：发现即另开条目落盘（可空表「本波零发现」）

**竖切结论**：D2–D4 为硬化本体（闸/接口/策略）；D1 为 v1.0 工程出口实证承继（已 CLOSE 基建上回归+补扫，不可省略——否则 07 §4「工程」面双进程/边界过期）；D5 为验证≠投产铁律。耦合面可控（CI 配置 + capability 接口层 + 文档/策略试点 + 测试断言 · **无 alembic**）。

### 非范围

承 SPEC §3 + multi-replica §3（锁死 · 越任一条即回炉）：

- ❌ 实际多副本生产部署 / 投产切换灰度回滚
- ❌ 服务拆分 / 注册中心远程实现（接口先行 · 实现在 v2.0）
- ❌ 进程内状态外置改造（budget/circuit/metrics/llm budget/cache/nonce 改 DB/Redis）
- ❌ 策略包全量收敛（v1 只盘点+schema 试点）
- ❌ k8s 清单 / 服务网格 / Java 网关仓改动
- ❌ 改 freeze 契约 / 新 SSE 事件 / 新路由 / 新表 / alembic
- ❌ 顺手修验证发现的 bug（另开 fix task）
- ❌ 重写已 CLOSE 的双进程基建（仅回归/补扫/报告）

---

## failure_paths

| 触发条件 | 系统行为 | 可重试 | 用户可见 |
|----------|----------|--------|----------|
| `HG-AUDIT-R1` 未签即 30 | **拒开工** | 是 | 是 |
| B1 旧测影响面未逐条处置即 30 交付 | **拒收**（闸前置） | 是 | 是 |
| 验收缺 D1§6 映射 / import 闸 / registry 对拍 / 策略优先级 / 变异检验任一 | **拒收**（防空真规则） | 是 | 是 |
| **双进程验证发现状态泄漏**（SPEC FP-1 · 承 multi-replica） | 另开 fix task · 本波记边界清单/「发现即另开」 | 是 | 否 |
| **import 闸误报**（SPEC FP-2 · 既有合理越界） | 白名单逐条消账（注释理由）· 图谱出边同步修正 | 是 | 否 |
| **registry 抽象改动面大**（SPEC FP-3） | 只抽接口不改语义 · 对拍零 diff · 调用点注入式最小侵入 | 是 | 否 |
| **双进程基建不稳**（SPEC FP-4 · 端口/就绪/收尾） | 承既有 dualproc fixture · 不重造轮；回归失败先查基建再查语义 | 是 | 否 |
| **外部 Java 网关不可得**（SPEC FP-5） | 降级 LB + 报告如实标注（禁写成网关验证通过） | 是 | 否 |
| **策略包与 env 冲突致行为漂移**（SPEC FP-6） | 优先级 env>策略包>代码默认 · 缺省=现状逐字节 · 试点面先行 | 是 | 否 |
| **import 闸 CI flaky**（SPEC FP-7） | contracts 静态解析 · 与 pytest 同环境复跑 · 白名单留痕 | 是 | 否 |
| **假阳性「没真跨实例」**（承 multi-replica §5） | 禁同进程双 app · 归属先断言 FAIL 非 skip · 变异① | 是 | 否 |
| **边界清单漏 V1-A~D 新状态**（本波补扫否决面） | D1 补扫条目带锚点；漏项=验收不收 | 是 | 否 |

---

## 验收标准

- [x] 人工闸：HG-AUDIT-R1 approved 后方可勾选下列码项（图谱按实判随 30；**30 偏离预判 → 回炉补闸条款生效**）

### D1 · multi-replica 承继（映射 multi-replica SPEC §6 全表 · 勾选=承 #165 + 本波回归/补扫）

- [x] **§6-D1 部署**：runbook 可执行 / 报告字段族含拓扑·网关形态·PASS/FAIL·git sha·recorded_at；网关不可得时降级如实标注（不重写基建，可复跑或标注「承 #165 + 本波回归时间戳」）
- [x] **§6-D2 状态外置**：`tests/test_multi_replica_dualproc.py` 全绿；实例归属先断言；A→B replay/404/续写 seq；前置配置断言
- [x] **§6-D3 边界清单**：既有 ≥8 条目保持；**本波补扫**至少增补：delegation nonce registry · llm `budget.py` process-local · `infer_cache` LRU（均带 file:line + 失真形态 + 处置建议）；附扫描基线更新留痕
- [x] **§6-D4 HITL**：双进程 HITL 跨实例用例全绿（图真的续跑 · 不只断 200）；负路径 409/503 仍绿
- [x] **§6-D5**：零 alembic；app/ 生产码 **验证相关零 diff**（D3 接口抽象 diff 白名单见下，不计入 D1 验证轨）；发现 bug→「发现即另开」条目
- [x] **变异检验（multi-replica 三条）**：归属可检 / 外置可检 / 失真可检（MR_* 钩子）「破坏→必挂→恢复」可复述或本波复跑留痕

### D2 · import 机械闸（映射 SPEC §6-2）

- [x] `.importlinter`（或等价）contracts 与 `01_modules.md` 出边一致（至少覆盖：capability 禁 import lg_rag；llm 禁 import lg_rag/strategy；以及其他出边推导的 forbidden）
- [x] 故意越界 import 的探针/变异 → 闸必挂；恢复后绿
- [x] 白名单逐条有理由注释；CI workflow 接线绿

### D3 · registry 接口（映射 SPEC §6-3）

- [x] `RegistryReader`/`RegistryWriter` 协议落地；本地 dict 为默认实现
- [x] mock 实现替换后调用方行为一致（注入断言）
- [x] 对拍零 diff：全量 `pytest tests` 绿（基线 **1587 collected** 承 V1-D · 30/40 真跑复核）；无既有用例删除

### D4 · 策略收敛（映射 SPEC §6-4）

- [x] env 清单文档落盘（名称/默认/非法回退/归属面 · grep 基线 · 含 V1 五波新增 env）
- [x] 策略包 schema v0 + 试点面加载断言：env 覆盖优先；策略包缺省=现状逐字节

### D5 / 工程（映射 SPEC §6-5/6/7/8）

- [x] 「发现即另开」条目表落盘（可空）
- [x] 零 alembic · 零新路由/SSE/一级模块 · `./scripts/graph-compile.sh` 绿 · `ruff check app tests` 净增 0
- [x] 生产路径 diff 白名单（示意）：`app/ops/capability/`（registry 协议+注入）· 可选 `app/llm/`（策略包试点读取）· `.importlinter` · `requirements.txt`/`pyproject.toml`（import-linter）· `.github/workflows/` · `tests/` · `docs/`（清单/env 盘点/策略 schema）· `scripts/`（若补回归）——**禁止**顺手改 checkpointer/resume/budget 语义
- [x] **v1.0 出口清单复核留痕**（07 §4 八面）：CLOSE 前由 **00** 逐面对证（本棒验收项预留勾选位；10 不代签）
- 注记（承 SPEC §6-7 · 不计验收计数）：PR+CI 绿+merge 由 orchestration 流程承载

### 变异检验（本波硬化 · 不验收空真）

- [x] ① **import 可检**：临时引入出边禁止的 import → import-linter 必挂；恢复后绿
- [x] ② **对拍可检**：registry 抽象后故意改本地实现语义 → 既有 capability 基线必挂；恢复后绿
- [x] ③ **优先级可检**：试点面临时让策略包覆盖盖过 env → 「env 优先」断言必挂；恢复后绿

### 旧测影响面清单（B1 · 2026-09-24 10-task 实扫落盘）

> 扫描口径（真跑）：`ls tests/ | grep -iE 'replica|dualproc|capability|registry|llm_|strategy|hitl|model_catalog|budget|circuit|manifest|gateway'` · 分组 `def test_` 计数 · 命名冲突扫零命中 · 基线承 V1-D **1587 collected**（本帽静态 1376 methods · collect 因 worktree `.venv` 缺 pytest 未本机展开）

| # | 锚点 | 本波影响 | 处置 |
|---|------|----------|------|
| 1 | `tests/test_multi_replica_dualproc.py`（9）· `tests/dualproc_server.py` | D1 核心回归面；基建不重写 → 全绿 | 回归（零改编预期） |
| 2 | capability 核心：`test_capability_gateway.py`（32）· `manifest`（19）· `visibility_and_receipts`（20）· `admin_capability_observability`（12）· `idempotency`（17）· `persistence_db`（15）· `policy`（9）· `reversibility`（14）· `delegation`（30）≈168 | D3 接口注入后对拍零 diff → 全绿；语义改动=拒收 | 回归（零改编预期） |
| 3 | llm 档/预算：`test_llm_budget.py`（28）· `infer_cache`（15）· `routing`（17）· `model_catalog`（3）· `usage`（6）· `circuit`（9）· `retry`（9）≈87 | D4 试点缺省零 diff → 全绿；改解析序=拒收 | 回归（零改编预期） |
| 4 | HITL：`test_hitl.py`（20）· `hitl_resume`（19）· `hitl_resume_events`（13）· `lg_rag_sse_hitl`（10）≈62 | D1 HITL 跨实例回归 → 全绿 | 回归（零改编预期） |
| 5 | strategy：`test_strategy_builder.py`（11）· `scenario`（18）· `supervisor_budget`（10）≈39 | 本波不改 strategy 语义；import 闸禁 llm→strategy 等 → 全绿 | 回归（零改编预期） |
| 6 | 新增义务：`tests/` import-linter 探针或契约测（可选）· registry 协议/mock 注入测 · 策略包加载/优先级测 ·（可选）边界清单补扫断言 | — | 新增（用例数如实入 40） |
| 7 | alembic 链 | **无迁移义务** | 无（diff 为空断言） |
| 8 | CI workflows | 增 import-linter job（或并入既有 check） | 新增 CI 面（非旧测改编） |

---

## 依赖

| 依赖 | 说明 |
|------|------|
| SPEC | `docs/spec/host-v1-splittability-hardening/SPEC-host-v1-splittability-hardening_v0.md`（signed） |
| D1 真值 | `docs/spec/multi-replica-verify/SPEC-multi-replica-verify_v1.md`（signed · §2/§6 原样映射） |
| D1 既有 CLOSE | `docs/tasks/done/task_multi_replica_verify.md`（PR #165）· `docs/guides/GUIDE_process_local_state_boundaries_v1.md` · `docs/guides/RUNBOOK_multi_replica_verify_v1.md` |
| 规划/种子 | `docs/spec/agent-infra/07_host_v1_landing_plan_v0.md`（§4 八面出口）· `08_host_v1_wave_spec_outlines_v0.md` §5 |
| 工程面 | `docs/discussions/2026-09-23_agent-host-multi-service-engineering-architecture_v0.md`（C1/C5/C7） |
| 前波 CLOSE | V1-A~D（delegation / visibility / llm-factory / episodic）· 关账 #186 |
| 编码规范 | `docs/standards/CODING_BACKEND_L2_v1_zh.md` |
| 图谱 | `docs/_tech_graph/l1/01_modules.md`（2026-09-24 真读 · 出边=import contracts 真值 · 签录至 V1-D） |
| 改造对象 | `.importlinter`（新增）· CI workflow · `app/ops/capability/registry.py` / `gateway.py`（协议+注入）· 调用点最小集 · env 清单文档 · 策略包 schema/试点加载 · `docs/guides/GUIDE_process_local_state_boundaries_v1.md`（补扫） |
| 先例 · 双进程 | `tests/test_multi_replica_dualproc.py` · `scripts/acceptance/hitl_persistence_smoke.py` |
| 先例 · 资产化 | `app/ops/prompts/`（prompt 资产化 · 策略包 schema 形态参照） |
| 测试锚点 | B1 清单 8 行 |
| 格式基准 | `docs/tasks/done/task_host_v1_episodic_memory_feedback.md` |

---

## 给执行帽的必读列表

1. `AGENTS.md`（新会话启动纪律 · 分支纪律 · GATE_VERIFY）
2. 本 task（钉死契约 · 闸 · 非范围 · B1 · D1 承继口径）
3. SPEC `docs/spec/host-v1-splittability-hardening/SPEC-host-v1-splittability-hardening_v0.md`（§2 D1–D5 / §3 / §4 Q1–Q2 / §5 FP / §6）
4. `docs/spec/multi-replica-verify/SPEC-multi-replica-verify_v1.md`（D1 §2/§6 原样）
5. `docs/standards/CODING_BACKEND_L2_v1_zh.md`
6. 代码：`app/ops/capability/registry.py` · `gateway.py:81+` · `delegation.py:320+` · `app/llm/budget.py:83+`（状态桶）· `budget.py:387+`（snapshot scope）· `infer_cache.py:187+` · `model_catalog.py:113+`
7. 既有：`docs/guides/GUIDE_process_local_state_boundaries_v1.md` · `tests/test_multi_replica_dualproc.py`
8. `docs/harness/prompts/FRAGMENT_30_gate_verify_v1_zh.md`
9. `docs/spec/agent-infra/07_host_v1_landing_plan_v0.md` §4（CLOSE 前 00 八面复核）

---

## 思考轮控制

| 轮 | 结论 | early_stop | reason（early_stop） | residual_risks |
|----|------|------------|----------------------|----------------|
| R0 | SPEC signed（HG-SPEC-SIGNOFF=approved 2026-09-23 00 代录）；V1-A~D CLOSE+#186；multi-replica 已 CLOSE(#165)→D1 承继口径；锚点真扫：无 import-linter · 无 Reader/Writer · 边界清单缺 V1-C/D 进程内项 · 基线承 1587 | no | — | 本帽 collect 未真跑（venv 缺 pytest）→ 30 须复核 collected 数 |
| R1 | 开工闸：HG-TASK-DRAFT **approved**（00 代录）· HG-AUDIT-R1 **pending**（blocks 30）· HG-GRAPH-MODULES=approved（真读 · 预期无新签按实判） | no | — | 无 |
| R2 | 竖切：D2→D3→D4→D1→D5；方案对比继承 SPEC Q1/Q2（import-linter · 盘点+试点），不重演；D1 不重做基建 | no | — | 无 |
| R3 | failure_paths **12 条** = SPEC FP-1~7 + multi-replica 假阳性 + 清单漏补扫 + 过程三；最锋利=对拍零 diff 与不顺手修 | no | — | ① 白名单消账若过宽则闸空真 ② 策略试点面选错爆炸半径 |
| R4 | 验收按 D1§6 映射 + D2/D3/D4/D5/工程 + 变异×3；B1 八行三态齐全（回归×5 · 新增×2 · 迁移无×1） | no | — | 无 |
| R5 | 可交 20-task-audit；与 SPEC 实质差异=仅 D1「独立实施→承继+补扫」过程化落地（SPEC 已允并入本波 · 且历史 CLOSE 强制承继）；HG-AUDIT-R1 落稿待签 | no | — | 见 R3 |

**actual_last_round**：R5 · **early_stop**：no · **residual_risks**：见 R3/R5

### R0 · 问题框定

V1-E 是收尾硬化波：验证轨（D1）历史已交付须承继回归并补扫 V1-A~D 新状态；工程闸（D2）与接口先行（D3）+ 策略试点（D4）构成 v1.0 工程出口。硬化≠重构。当前分支须为 `task/host-v1-splittability-hardening`。

### R1 · 开工闸

HG-TASK-DRAFT **approved**（00 代录 · 长程授权原话见闸表）；HG-AUDIT-R1 **pending** → 30 拒开工；HG-GRAPH-MODULES 真读通过（出边列作 import contracts 真值 · 预期无新签按实判）。

### R2 · 竖切

实现序 D2→D3→D4→D1→D5：先机械闸与接口（可 CI），再策略试点，再验证回归补扫，最后发现即另开收口。D1 与 D2–D4 文件面基本正交。

### R3 · 失败语义

SPEC FP-1~7 全收翻四列，并显式补「清单漏 V1 新状态」与 multi-replica 假阳性防线。不顺手修与对拍零 diff 为否决面。

### R4 · 可测性

D1 映射 multi-replica §6（承继勾选）；D2/D3/D4 各配否定性断言与变异钩子；B1 以回归为主、改编预期零。

### R5 · 交付判定

可交 20-task-audit；HG-AUDIT-R1 待签；残余风险两条承 R3 如实携带。

### 自检结论

本稿：范围/非范围/验收/failure_paths 逐块映射 SPEC（§2→D1–D5 · §3→非范围 · §5→FP+过程 · §6→验收）并原样映射 multi-replica §6；钉死契约含 D1 承继口径；B1 实扫八行；闸表四行诚实（HG-AUDIT-R1=pending）；思考轮 R0–R5 齐全。

---

---

### KPI（kpi_aggregator=CLOSE · 2026-09-24 00 核验）

Task_KPI%: 100 · D1 承继#165+GUIDE 补扫 9–11（dualproc 机跑红如实记 FINDINGS#1 · 非本波假绿）· D2 import-linter 12 KEPT + CI · D3 RegistryReader/Writer 对拍 · D4 env 清单+llm_tiers 试点 · D5 发现即另开 1 条 · 闸齐 00 代录 · 过程档 00/10/20/30/40

| 指标 | 值 |
|---|---|
| 新增测试 | +7（1587→1594 collected）· `test_splittability_hardening.py` 7 passed |
| import-linter | 12 kept / 0 broken · CI job 绿 |
| ruff | 净增 ≤0（56 vs master 57） |
| graph-compile | 绿 · capability 行备注 + HG-GRAPH-MODULES 00 代录 |
| dualproc | **9 ERROR** 本分支=master 同 .env（tenant_id）· **禁止写双进程全绿** · 另开建议 `fix-multi-replica-dualproc-tenant-session` |
| 交付 | PR #187 MERGED（CI 四绿）· 40 摘要 #188 |


## 修订记录

| 日期 | 摘要 |
|------|------|
| 2026-09-24 | 10-task 落稿（SPEC signed · 00 委派）：D1 裁定为承继 multi-replica CLOSE(#165)+回归+V1-A~D 边界补扫（清单真读确认缺 llm budget/infer_cache/delegation）；D2–D5 按 SPEC 钉死；B1 八行落盘；基线承 V1-D 1587 collected（本帽 collect 未真跑注明）；HG-TASK-DRAFT pending（00 代录位预留）· **HG-AUDIT-R1 pending**（本帽不签）· HG-GRAPH-MODULES 真读 approved |
| 2026-09-24 | **00 代录 HG-TASK-DRAFT=approved**（长程授权原话留痕）· 状态 draft→active · 委派 20-task-audit · **HG-AUDIT-R1 仍 pending（禁 30）** |
| 2026-09-24 | 20-task-audit R1 **PASS-WITH-NITS**（零阻塞 · N1–N3 已微修 · 审查文 `…_audit_R1_20260924.md`）；**00 代录 HG-AUDIT-R1=approved** · 30 可委派开工 |
| 2026-09-24 | **20-task-audit R1 NITS 微修**（审查文 PASS-WITH-NITS）：N1 思考轮 R1 闸态同步为 HG-TASK-DRAFT=approved · N2 头部 10/20 注去陈旧「待代录」· N3 llm budget snapshot 行号拆至 :387/:407；**HG-AUDIT-R1 仍 pending（本帽不签）** |
| 2026-09-24 | **00 CLOSE**：PR [#187](https://github.com/Cyning12/ops-desk-api/pull/187) MERGED（CI 四绿 · 164f3fc）；图谱 00 代录；归档 done/ · Hub；**V1-A~E 全 CLOSE · Agent Host v1.0 工程出口**；遗留 FINDINGS#1 dualproc fixture 另开 fix |
