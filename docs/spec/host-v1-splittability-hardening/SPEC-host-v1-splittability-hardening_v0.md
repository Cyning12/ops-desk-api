# SPEC：Agent Host V1-E · 可拆性硬化（multi-replica-verify 实施 + import 机械闸 + registry 接口抽象 + 策略收敛）（splittability-hardening · 收尾波）（v0）

> **层级**：L1 波次 SPEC（07 L0 规划的 V1-E 波 · **必须最后** · 依赖 V1-A~D 全 CLOSE）  
> **状态**：`signed`（HG-SPEC-SIGNOFF=**approved** · 2026-09-23 · **00 代录** · 维护者令原话：「签收，并生成对此长程任务的00启动Prompt，新窗口执行，授权00签收所有过程文档，完整落地1.0版本内容」+ 本窗令「继续，完成后自行进行下一波，无特殊情况无需停下等待接收命令」；**顺序纪律留痕**：本波 30 实施必须最后——V1-A~D 全 CLOSE 后方可拆 task 开工）  
> **种子**：[`../agent-infra/08_host_v1_wave_spec_outlines_v0.md`](../agent-infra/08_host_v1_wave_spec_outlines_v0.md) §5（signed · 本 SPEC 为其正式展开，冲突以本 SPEC 为准）  
> **直接执行真值**：[`../multi-replica-verify/SPEC-multi-replica-verify_v1.md`](../multi-replica-verify/SPEC-multi-replica-verify_v1.md)（**signed** 2026-09-22 · 本波 D1 原样执行其 §2/§6 · 不重演论证）  
> **上游**：[`../agent-infra/07_host_v1_landing_plan_v0.md`](../agent-infra/07_host_v1_landing_plan_v0.md)（signed）· 工程架构（C1/C5/C7 可拆性约束 · P1 包边界硬化出口）· 大纲 v0.2 §6 D3（Tier 语义）  
> **下游**：HG-SPEC-SIGNOFF → 00 出 task → 20-task-audit → HG-AUDIT-R1 → 30（委派子 Agent · 分支 `task/host-v1-splittability-hardening`）→ 40 → PR+CI 绿+merge → 图谱回写（00 代录 · 预期无义务按实判）→ CLOSE → **v1.0 出口清单全表复核**  
> **Open Folder（实现）**：`ops-desk-api/`

---

## Harness 元信息

| 字段 | 值 |
|---|---|
| **spec_slug** | `host-v1-splittability-hardening` |
| **invoke_slug** | `host-v1-splittability-hardening`（task 阶段） |
| **test_strategy** | `required` |
| **test_strategy_note** | D1 承 multi-replica-verify §6（双进程 pytest+runbook+清单 · 其变异检验三条原样映射）；import 闸断言（越界 import 必挂 · 白名单消账）；registry 抽象对拍零 diff 断言（接口替换实现语义不变）；策略包加载断言（env 覆盖优先不变）；零 app/ 生产码偏离回炉 |
| **默认分支** | `task/host-v1-splittability-hardening`（自 `master` 分出；**禁止 master/main 直改**） |
| **graph_change_layer** | **预期无（承 multi-replica-verify 验证轨先例）· 按实判**：import 闸=CI/配置面 · registry 抽象=capability 行内重构（接口化零语义改）· 策略包=配置面；若 registry 抽象触发行备注更新则如实登记（HG-GRAPH-MODULES 00 代录位预留） |
| **freeze_id** | 无（不改 freeze 契约 · SSE 零新事件 · 零新路由 · 零新表） |

### 人工闸（SPEC 阶段）

| human_gate_id | status | 说明 |
|---|---|---|
| **HG-SPEC-SIGNOFF** | **approved**（2026-09-23 · 00 代录） | 维护者双令原话留痕（见状态行）；开放裁定 Q1/Q2 已答；**实施顺序钉死：E 必须最后**（V1-A~D 全 CLOSE 后拆 task） |

---

## 1. 背景与目标

### 定位（承 08 §5.1）

工程方案 C1/C5/C7 + signed `multi-replica-verify`：功能稳定后做可拆性硬化——**这是 v1.0 与 v2.0 的分界线**：做完本波，上楼只是换传输层。本波是 v1.0 收尾波，CLOSE 后须全表复核 07 §4 出口标准八面。

### 关键裁定（SPEC 级 · 留痕）

- **D1 不另拆 task**：signed `multi-replica-verify` SPEC 的实施**并入本波 task 作 D1**（其 §6 验收原样映射 · 其 §2 范围/§5 failure_paths 直接引用不重演）；其 §8「00 起草 task_multi_replica_verify」由本波 task 承载（slug 统一 `host-v1-splittability-hardening`）。
- **硬化不是重构**：registry 抽象只抽接口不改语义（对拍零 diff）；import 闸只加机械闸不改模块归属；策略收敛 v1 只盘点+schema 试点不搬家。

### 一句话目标

双进程共享 PG 验证报告全绿 + 进程内状态边界清单落盘 + import 机械闸 CI 绿（模块出边=未来服务边界真值化）+ capability registry 读写分离接口化（本地实现为默认 · 可替换）+ env 散落盘点与策略包 schema 试点。

### 设计纪律（跨波公共约束继承 · 签收时锁死）

1. **验证≠投产**（承 multi-replica-verify §1 定性）：发现阻断 bug → 另开 fix task · 本波不顺手修。
2. **对拍零 diff**：registry 抽象前后行为逐字节一致（同一测试基线全绿即证）；接口先行实现在 v2.0。
3. **默认关/向后兼容**：import 闸白名单机制消账（既有合理越界逐条登记）；策略包 env 覆盖优先级不变。
4. **零 freeze 动**：不改 freeze 契约 · SSE 零新事件 · 零新路由 · 零新表。
5. **图谱按实判**：预期无义务；registry 抽象若触行备注 → 如实登记 00 代录。

---

## 2. 范围（D 块展开 · 承 08 §5.2）

### D1 · multi-replica-verify 实施（必做 · signed SPEC 直接执行）

按 [`../multi-replica-verify/SPEC-multi-replica-verify_v1.md`](../multi-replica-verify/SPEC-multi-replica-verify_v1.md) §2 D1–D5 原样执行：双进程 pytest（P1 subprocess 两 uvicorn · 禁同进程双 app · 每用例实例归属先断言 FAIL 非 skip）· 状态外置实证（A 起 run B replay/404/续写 seq）· HITL 跨实例（A 挂起 B resume 图真的续跑）· 边界清单（≥8 条目带锚点+扫描基线兜底）· runbook+实测报告（网关形态如实标注）· **预期零 app/ 生产码**（发现 bug 另开 fix task）。验收=其 §6 全表（含变异检验三条）原样映射入本波 task。

### D2 · import 机械闸（必做 · Q1 裁定 import-linter）

- 工具：**import-linter**（Q1 裁定 · 成熟声明式 contracts · 零自研）；配置 `.importlinter`（或 setup.cfg 段）：真值=`docs/_tech_graph/l1/01_modules.md` 依赖出边列（capability 禁 import lg_rag · llm 禁 import lg_rag/strategy · 控制面禁 import providers 等 · 以图谱出边为准生成 contracts）。
- **白名单消账**：既有合理越界逐条 `ignore_imports` 登记+注释理由（禁大水漫灌）· 图谱出边若实测有误 → 同步修正图谱（如实登记）。
- CI 接线：`.github/workflows/` 增 import-linter job（或并入既有 check workflow）· 绿为 merge 前提。

### D3 · registry 接口抽象（必做 · C1）

- capability registry 读写分离接口化：读侧 `RegistryReader` 协议（get/list/snapshot · 本地缓存抽象）· 写侧 `RegistryWriter` 协议（register/unregister/reload · 「注册中心客户端」接口形态）· **本地 dict 实现为默认**（现有 registry.py 语义原样封装）。
- **只抽接口不改语义**：调用点（gateway/manifest/admin）改面向协议注入 · 行为对拍零 diff（既有 1420+ 基线全绿即证）· 远程实现（v2.0 注册中心客户端）本波只留接口不实现。

### D4 · 策略收敛（必做 · C7 · Q2 裁定盘点+试点）

- **env 散落盘点**：全仓 env 变量清单文档（名称/默认/非法回退/归属面 · grep 基线 · 含本 v1.0 五波新增 env）。
- **策略包 schema 试点**：声明式策略包 YAML schema v0（版本化 · 承 prompts 资产化先例）——试点一面（建议 llm 档级面 TASK_TIER_MODELS/FALLBACKS/单价表）；**env 覆盖优先级不变**（Q2 裁定：env > 策略包默认 > 代码默认 · 承 OPS_LLM_TIER_* 先例）· 灰度：先并存读取（策略包缺省=现状逐字节）。
- **不做全量搬家**（v1 只 schema+试点 · 全量收敛 v2.0）。

### D5 · 问题修复纪律（必做 · 过程面）

验证/实扫发现的阻断 bug → **另开 fix task**（承 multi-replica-verify 不顺手修纪律 · 本波只记录证据与「发现即另开」条目）。

---

## 3. 非范围

- ❌ 实际多副本生产部署 / 投产切换灰度回滚（验证≠投产）
- ❌ 服务拆分 / 注册中心实现（接口先行 · 实现在 v2.0）
- ❌ 进程内状态外置改造（budget/circuit/metrics 改 DB/Redis 是修复动作 · 另开 SPEC）
- ❌ 策略包全量收敛（v1 只盘点+schema 试点）
- ❌ k8s 清单 / 服务网格 / Java 网关仓改动
- ❌ 改 freeze 契约 / 新 SSE 事件 / 新路由 / 新表
- ❌ 顺手修验证发现的 bug（另开 fix task）

---

## 4. 开放裁定（必答题 · 全部作答）

### Q1 · import 闸工具选型

| 方案 | 做法 | 裁决 |
|---|---|---|
| **S1 · import-linter** | 声明式 layers/forbidden contracts · 配置文件入仓 · CI 接线 | **推荐（裁定）**：成熟零自研 · contracts 即文档（与 01_modules 出边同构）· 白名单机制原生支持消账 |
| S2 · 自实现 ruff 插件 | AST 扫描自研 | 弃选：重复造轮 · 规则引擎维护成本 · 误报处理机制要自建 |

### Q2 · 策略包格式与 env 回退关系

| 方案 | 做法 | 裁决 |
|---|---|---|
| **S1 · YAML 策略包 schema v0 + 优先级 env>策略包>代码默认 + 单面试点** | 版本化声明 · 缺省=现状 | **推荐（裁定）**：承 prompts 资产化先例 · env 覆盖不变向后兼容（承 OPS_LLM_TIER_* 先例）· 试点先行控制爆炸半径 |
| S2 · 一次性全量收敛 | 全 env 搬策略包 | 弃选：大爆炸变更 · 灰度无门 · 与「每波可停稳态」冲突 |

---

## 5. failure_paths（承 08 §5.4 · 全部正面裁定）

| # | 路径 | 裁定 |
|---|---|---|
| FP-1 | 双进程验证发现状态泄漏 | 另开 fix task · 本波记录边界清单（承 signed SPEC §5 · 不顺手修） |
| FP-2 | import 闸误报（既有合理越界） | 白名单机制 + 逐条消账（注释理由）· 图谱出边同步修正（如实登记） |
| FP-3 | registry 抽象改动面大 | 只抽接口不改语义 · 对拍测试零 diff（全量基线即证）· 调用点注入式最小侵入 |
| FP-4 | 双进程 pytest 基建不稳（端口冲突/就绪等待/收尾） | 承 signed SPEC §7 残余①：hitl_persistence_smoke .sh 壳参照 fixture 化 · 端口动态分配+就绪轮询+finally 杀进程 |
| FP-5 | 外部 Java 网关不可得 | 降级形态（compose 轻量 LB）+ 报告如实标注（承 signed SPEC D1 钉死 · 禁把降级写成网关验证通过） |
| FP-6 | 策略包与 env 冲突致行为漂移 | 优先级钉死 env>策略包>代码默认 · 策略包缺省=现状逐字节 · 试点面先行 |
| FP-7 | import 闸 CI  flaky（缓存/路径差异） | contracts 静态解析无运行时 · 与 pytest 同环境复跑 · 白名单消账留痕 |

---

## 6. 验收标准（可机验）

1. **D1 全表**：multi-replica-verify §6 验收（D1 部署/D2 状态外置/D3 清单/D4 HITL/D5 边界纪律 + 变异检验三条）全绿 · 双进程报告+实测报告落盘
2. import 闸 CI 绿（contracts 与 01_modules 出边一致 · 白名单逐条有理由）
3. registry 接口可替换（协议注入断言：mock 实现替换后调用方行为一致）· 对拍零 diff（全量基线全绿）
4. 策略包盘点完成（env 清单文档）+ schema 试点加载断言（env 覆盖优先不变 · 缺省=现状）
5. 零 alembic · 零新路由/SSE 事件/一级模块 · graph-compile 绿
6. `pytest tests` 全绿 + `ruff check app tests` 净增 0
7. PR 到 master 经 CI 绿后 merge
8. **v1.0 出口清单全表复核**（07 §4 八面）留痕：本波 CLOSE 前由 00 逐面对证（委派链路/可见集/manifest/LLM 工厂/记忆/工程/指标/图谱签录链）

---

## 7. 思考轮回填（R0–R5）

- **R0（读人聊/目标）**：维护者令长程授权；08 §5 种子 + multi-replica-verify signed SPEC（直接执行真值）+ 工程架构 C1/C5/C7 真读毕。硬化不是重构。
- **R1（范围/非范围）**：D1–D5 承种子展开；D1 并入本波 task 的裁定留痕；投产/拆分/外置改造/全量收敛显式排除。
- **R2（方案对比）**：Q1 import-linter（自研弃——重复造轮）· Q2 盘点+试点（全量搬家弃——大爆炸）；闸工具与策略包形态各两案。
- **R3（边界/失败路径）**：FP-1~FP-7 全裁定；最锋利边界=对拍零 diff防线（抽象不改语义）与不顺手修纪律（发现即另开）。
- **R4（验收/可测性）**：验收 8 条；D1 直接映射 signed SPEC §6（含其变异检验）· registry mock 替换断言 · 闸误报白名单消账断言。
- **R5（签收就绪）**：v1.0 出口复核义务确认（本波 CLOSE 附带）；图谱按实判（预期无）；可交 00 代录 HG-SPEC-SIGNOFF 后拆 task。

### 思考轮控制

| 轮 | 状态 | 说明 |
|---|---|---|
| R0 | done | 维护者令 + 07/08 §5 + multi-replica signed SPEC + 工程架构已读 |
| R1 | done | 范围 D1–D5 / 非范围锁死 |
| R2 | done | Q1/Q2 ≥2 案对比 + 裁定 |
| R3 | done | FP-1~FP-7 裁定 |
| R4 | done | 验收 8 条 + test_strategy=required |
| R5 | done | 签收就绪 → 00 代录 HG-SPEC-SIGNOFF |
| early_stop | no | — |

---

## 8. 关联

- 规划/种子：[`../agent-infra/07_host_v1_landing_plan_v0.md`](../agent-infra/07_host_v1_landing_plan_v0.md)（signed · §4 出口标准复核对象）· [`../agent-infra/08_host_v1_wave_spec_outlines_v0.md`](../agent-infra/08_host_v1_wave_spec_outlines_v0.md) §5（signed）
- 直接执行：[`../multi-replica-verify/SPEC-multi-replica-verify_v1.md`](../multi-replica-verify/SPEC-multi-replica-verify_v1.md)（signed · D1 真值）
- 工程面：[`../../discussions/2026-09-23_agent-host-multi-service-engineering-architecture_v0.md`](../../discussions/2026-09-23_agent-host-multi-service-engineering-architecture_v0.md)（C1/C5/C7 · P1 出口）
- 前波：V1-A（令牌 Tier 1）· V1-B（可见集/manifest）· V1-C（预算/缓存/降级）· V1-D（情景记忆 Tier 2）
- 图谱：`docs/_tech_graph/l1/01_modules.md`（出边=import 闸 contracts 真值）

## 修订记录

| 日期 | 版本 | 内容 |
|---|---|---|
| 2026-09-23 | v0 | 10-spec 初稿：以 08 §5 种子展开 D1–D5；D1 并入本波 task 裁定留痕（multi-replica signed SPEC 直接执行不另拆 task）；开放裁定 Q1（import-linter）/Q2（盘点+schema 试点 · env>策略包>代码默认）全部作答；FP-1~FP-7 裁定；v1.0 出口复核义务入验收 §6-8；R0–R5 回填 |
| 2026-09-23 | v0 | **00 代录 HG-SPEC-SIGNOFF=approved**（维护者双令原话留痕）；顺序纪律：V1-A~D 全 CLOSE 后方可拆 task（E 必须最后 · 承 07 §3.1） |
