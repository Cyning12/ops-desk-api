# 审查文：task_host_v1_splittability_hardening · 20-task-audit R1（2026-09-24）

> **hat_id**：20-task-audit · **轮次**：R1 · **审查对象**：`docs/tasks/active/task_host_v1_splittability_hardening.md`（active · HG-TASK-DRAFT=approved · HG-AUDIT-R1=pending）  
> **对照真值**：SPEC `docs/spec/host-v1-splittability-hardening/SPEC-host-v1-splittability-hardening_v0.md`（signed）· D1 `docs/spec/multi-replica-verify/SPEC-multi-replica-verify_v1.md`（signed · #165 CLOSE）  
> **方法**：task/两份 SPEC 真读；边界清单/双进程锚点/gateway·delegation·llm budget·infer_cache 亲读；B1 `def test_` 计数亲跑；`npx spec-wave task lint --file` PASS；**未**代签 HG-AUDIT-R1 · **未**改 `app/`

---

## 结论摘要

| 维度 | 结论 |
|------|------|
| **内容** | **PASS-WITH-NITS** · 阻塞项为零 · 3 条非阻塞微修（N1–N3 · 本棒已落盘） |
| **流程闸** HG-AUDIT-R1 | **pending（如实）** → 30 拒开工维持；本帽不签发 |

**总结论：PASS-WITH-NITS · 阻塞项为零**。D1「承继 #165 + 回归 + V1-A~D 边界补扫」与 SPEC「并入本波 / 可直接执行 multi-replica §2/§6」一致且**未**偷偷重开基建；D2–D4 与 Q1/Q2 锁死一致；failure_paths / 验收 / B1 / 闸表 AUDIT pending / graph_delta_note 回炉条款均够用可交签。N1–N3 为 00 代录后思考轮/注记陈旧与锚点行号精度，已微修，不构成退回 10。

---

## 一、逐面核对（证据带行号）

### 面 1 · 范围 / 非范围 / 验收 / failure_paths 与 SPEC 一致性 ✅

| 核对项 | task 证据 | SPEC 证据 | 结论 |
|--------|-----------|-----------|------|
| 范围 D1–D5 | task :98-104（竖切 D2→D3→D4→D1→D5） | SPEC §2 :60-83 | 一致；实现序合理（闸/接口/策略先行 → 验证回归） |
| **D1 承继口径** | 钉死 :87 · 非范围 :118 · 验收 :145-152 | SPEC :41「D1 并入本波」· multi-replica §2/§6；历史 CLOSE #165 | ✅ **不重做基建**；本波=回归绿 + 边界补扫（≥ delegation nonce / llm budget / infer_cache）+ 报告可复核 + §6 变异三条；app/ 验证轨零改 |
| D2 import-linter | :88 · :100 · :156-158 | SPEC Q1 :100-106 · §2 D2 :64-68 | ✅ 工具/contracts 真值/`ignore_imports` 逐条/CI 接线锁死 |
| D3 RegistryReader/Writer | :89 · :101 · :160-164 | SPEC §2 D3 :70-73 | ✅ 本地 dict 默认 · 对拍零 diff · 远程不实现 |
| D4 盘点+schema 试点 | :90 · :102 · :166-169 | SPEC Q2 :108-113 · §2 D4 :75-79 | ✅ env>策略包>代码默认 · 缺省零 diff · 不做全量搬家 |
| D5 发现即另开 | :91 · :103 · :171-173 | SPEC §2 D5 :81-83 · FP-1 | ✅ |
| 非范围 | task :109-118（9 条） | SPEC §3 :87-96（7 条）+ 承继纪律 | ✅ 全收并显式增「重写已 CLOSE 双进程基建」「alembic」——与 D1 承继一致、无越界 |
| failure_paths | task :122-138（**12** 行） | SPEC FP-1~7 + multi-replica 假阳性 + 清单漏补扫 + 过程三 | ✅ 计数与 R3 自述一致；四列齐全 |
| 验收 ↔ SPEC §6 | task :141-183 | SPEC §6 1–8 + multi-replica §6 | ✅ D1 原样映射 §6-D1~D5+变异；D2–D5/工程/变异×3 覆盖；§6-7 PR merge 注记 orchestration（:177） |

### 面 2 · D1 承继专项（审查重点）✅

| 检查 | 结论 |
|------|------|
| 不得要求重做 #165 基建 | ✅ 钉死/非范围/现状锚点均写「禁重写」；验收允许「承 #165 + 本波回归时间戳」 |
| 须含 V1-A~D 边界补扫 | ✅ 验收 :149 点名三条 + file:line 义务；FP「清单漏 V1」拒收；真读 GUIDE：**零命中** `app/llm/budget` / `infer_cache` / `delegation` nonce（capability budget 既有条目 ≠ llm budget）→ 补扫义务成立 |
| multi-replica §6 原样映射 | ✅ 部署/外置/清单/HITL/纪律 + 变异三条均有勾选位；D3 接口 diff 白名单与 D1「验证轨零 diff」分立清楚 |

### 面 3 · D2–D4 ↔ Q1/Q2 · 钉死契约 ✅

| 项 | 锁死 | task | 结论 |
|----|------|------|------|
| Q1 | import-linter | 钉死 D2 · 非范围无自研闸 | ✅ |
| Q2 | YAML schema 试点 + env>包>代码 | 钉死 D4 · 变异③优先级可检 | ✅ |
| 图谱按实判 + 回炉 | SPEC :22 · :54 | `graph_delta_note` :25：一级模块/路由/观测端点/alembic/SSE/freeze/对拍非零/顺手修 D1 bug/策略全量搬家 → 退回 10 补闸 | ✅ **够用**（覆盖本波主要偏离面） |

### 面 4 · B1 / 思考轮 / 闸表诚实 ✅（NITS 见下）

- **B1** :185-198 八行三态齐全（回归×5 · 新增×2 · 迁移无×1）；亲跑 `def test_`：capability 九文件 **168** · llm 七文件 **87** · HITL 四文件 **62** · dualproc **9** —— 与括注一致 ✅。
- **行为变更类旧测影响面**：D3/D4 属接口/策略读取面 · B1 已列 → checklist 满足。
- **思考轮** R0–R5 齐全 · early_stop=no · residual 白名单过宽/试点面选错如实携带。
- **闸表**：HG-TASK-DRAFT=approved · **HG-AUDIT-R1=pending** · HG-GRAPH-MODULES=approved（真读出边与 task 例列一致）· PILOT n/a —— AUDIT 诚实 ✅。
- ⚠ **N1**：R1 控制表/正文在 00 代录后仍写「HG-TASK-DRAFT pending」→ 与闸表冲突（流程陈旧，非内容阻塞）。
- ⚠ **N2**：头部「10 注」仍写「落稿待 00 代录」→ 同上。

### 面 5 · 验收可执行性 / 防空真 ✅

- D1–D5 + 工程 + 变异×3 均可勾选机验；对拍零 diff / import 越界必挂 / env 优先 三条变异 falsifiable。
- 生产路径 diff 白名单 :175 与钉死落点一致；禁顺手改 checkpointer/resume/budget **语义** 明示。
- 基线 1587 collected 承 V1-D 并注明本机未真跑 → 30/40 复核义务清楚（非阻塞）。

### 面 6 · 锚点抽验 ✅（1 处行号精度 → N3）

| # | 锚点 | 复核 |
|---|------|------|
| 1 | `gateway.py:81` `_registry` | ✅ |
| 2 | `delegation.py:320+` `_NonceRegistry` / `:352` `_nonce_registry` | ✅ |
| 3 | `app/llm/budget.py:83-85` `_LOCK`/`_SESSIONS` | ✅；`snapshot()["scope"]="process-local"` 在 **:387/:407**（非 83-85）→ N3 |
| 4 | `infer_cache.py:187-189` `_LOCK`/`_CACHE` | ✅ |
| 5 | 仓内无 `.importlinter` / 无 import-linter 依赖 | ✅ |
| 6 | RegistryReader/Writer / strategy_pack 于 app/tests | ✅ 零命中 |
| 7 | GUIDE 缺 llm budget / infer_cache / delegation | ✅ 补扫义务成立 |
| 8 | alembic head `20260923_memory_episodes` · 本波无迁移 | ✅ |
| 9 | `task lint --file` | ✅ LINT PASS |

---

## 二、阻塞项清单

阻塞项为零。

## 三、非阻塞修正 / 建议清单（本棒已微修）

| # | 级别 | 内容 | 处置 |
|---|------|------|------|
| N1 | 微修 | 思考轮 R1 控制表 + R1 正文仍写 HG-TASK-DRAFT **pending**，与闸表 **approved** 冲突 | 已改为 approved（代录后态） |
| N2 | 微修 | 头部「10 注」仍写「HG-TASK-DRAFT 落稿待 00 代录」 | 已改为「已代录 approved · AUDIT 仍 pending」 |
| N3 | 微修 | llm budget 锚点把 `snapshot scope: process-local` 挂在 :83-85 | 已拆行：状态桶 :83-85 · snapshot :387/:407 |

以上不改变 SPEC 锁死语义；无退回 10 实质问题。

---

## 四、纪律自查

- 本帽未改 `app/` · 未把 HG-AUDIT-R1 改为 approved · 未附 30 Prompt。
- 仅 NITS 微修 task + 审查文 + 20 invoke 修订表。

## 维护者签闸（20 后 · 30 前）

- [ ] 已读 R1 审查结论（PASS-WITH-NITS · 阻塞项为零 · N1–N3 已微修）
- [ ] 在 task 人工闸表将 HG-AUDIT-R1 改为 approved（维护者授权 · **00 代录** · 日期 + 原话留痕）
- [ ] commit task 文档或确认已签
- [ ] 再下发 Harness 30 Prompt（00 委派子 Agent · 分支 `task/host-v1-splittability-hardening`）

30 Agent 将以 task 表为准；pending 时必须拒开工（见 TEMPLATE_30_gate_stop.md）。

---

## 修订记录

| 日期 | 摘要 |
|------|------|
| 2026-09-24 | 20-task-audit R1：六面核 + D1 承继专项 + B1 亲跑 + lint PASS → **PASS-WITH-NITS**（N1 思考轮闸态同步 · N2 10 注 · N3 budget snapshot 行号）· HG-AUDIT-R1 维持 pending · **建议 00 代录 AUDIT=Y** |
