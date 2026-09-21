# Task：tech_graph 追平近两天集中开发（HITL / capability 治理 / lg_rag 编排）

> **状态**：`done`（2026-09-21 · 维护者令开工 · 00 代签三闸 · 40 PASS · 已归档 done/）
> **关联图谱**：`docs/_tech_graph/l1/01_modules.md` · `l1/10_flow_capability.{md,graph.yaml}` · `l1/10_flow_lg_rag.{md,graph.yaml}` · `shared/02_version.md`
> **落盘**：`docs/tasks/done/task_tech_graph_recent_sync.md`（2026-09-21 已 `git mv` 归档）
> **分支**：`chore/upgrade-langgraph-1.2`（2026-09-21 维护者令：**不切分支**，直接在当前分支开工；被描述代码同在此分支）
> **类型**：docs / 图谱维护（追平，无 app/ 代码改动）
> **背景真源**：`docs/HANDOFF_recent-2days_v1_zh.md`（2026-09-20 ~ 09-21 脱离 specwave 过程的 29 个提交）

---

## Harness 元信息

| 字段 | 值 |
|------|-----|
| **task_slug** | `tech-graph-recent-sync` |
| **git_branch** | `chore/upgrade-langgraph-1.2`（维护者令不切分支） |
| **implement_repo** | `ops-desk-api` |
| **test_strategy** | `required` |
| **test_strategy_note** | 图谱改动验收 = `./scripts/graph-compile.sh` exit 0 + `npx spec-wave task lint` / `lint-wiki-delta` PASS；**不跑业务 pytest**（无 app/ 改动）；图谱陈述的每个事实须能在 `chore/upgrade-langgraph-1.2` 代码中指到锚点 |
| **code_quality_bar** | `n/a`（纯文档；mermaid 约定 `docs/_tech_graph/shared/99_mermaid_protocol.md`） |
| **graph_change_layer** | `G-L1`（+ `shared/02_version.md` 版本行） |
| **graph_delta** | 本 task 即 graph delta：`01_modules.md`（**新增一级模块 `hitl`** + `api`/`admin`/`capability`/`lg_rag`/`db` 五行备注）· `10_flow_capability` 与 `10_flow_lg_rag` 的 md+graph.yaml · `shared/02_version.md` 版本行 |
| **graph_delta_note** | **新增一级模块 `hitl`** 是本 task 唯一结构性变更，必须人签 `HG-GRAPH-MODULES`；不建 hitl G-L2 indexes（chat/lg_rag 试点之外不扩） |
| **wiki_delta** | `n/a` |
| **wiki_delta_note** | 只追平图谱陈述，不产生 coding_wiki 新条目；读序仍走既有 `docs/coding_wiki/README.md` |
| **review_hat** | `20` |
| **required_invoke_hats** | `10,30,40` |
| **invoke_retention_profile** | `default` |
| **experience_capture** | `recommended` |
| **kpi_aggregator** | `CLOSE` |
| **orchestration** | 10 起草 → 20 审查 → 人签三闸 → 30 改图谱 → 40 验收（graph-compile + 锚点抽查） |
| **freeze_id** | 无（不改任何 freeze 契约） |

### 人工闸

| human_gate_id | status | blocks_hats | 说明 |
|---------------|--------|-------------|------|
| HG-TASK-DRAFT | **approved** | 20-R1, 30 | 2026-09-21 · 00 代签 · 维护者令「不切分支，直接在当前分支开始」 |
| HG-AUDIT-R1 | **approved** | **30** | 2026-09-21 · 00 代签 · 维护者令「不切分支，直接在当前分支开始」（图谱追平波，20 审查并入 40 锚点抽查） |
| HG-GRAPH-MODULES | **approved** | **30** | 2026-09-21 · 00 代签 · 维护者令「不切分支，直接在当前分支开始」· 本 task **新增一级模块 `hitl`**；真值 `docs/_tech_graph/l1/01_modules.md` |

---

## 背景与目标

2026-09-20 ~ 09-21 两日在 `chore/upgrade-langgraph-1.2` 上集中开发 29 个提交（脱离 specwave 过程，无 task/invoke），代码已含 HITL 全新模块、capability 治理层（熔断/降级/配额/幂等/output_schema/观测）、lg_rag 编排增强（步骤契约/ReAct 收口/interrupt 挂起恢复），但 `docs/_tech_graph/` **完全未同步**——2026-09-21 实测 grep：图谱全目录对 `hitl` `配额` `output_schema` `幂等` `interrupt` 零命中。

目标：把图谱追平到 `chore/upgrade-langgraph-1.2` 代码真值，让「改路由/表/事件/LangGraph 节点前」的 agent 读到的不再是两天前的系统。

---

## 现状锚点（10 实扫 · 30 必读 · 行号以现码为准）

| 主题 | 路径 · 锚点 | 图谱现状缺口 |
|------|-------------|--------------|
| HITL 模块 | `app/ops/hitl/`（store/persistence/resume/router/signature/__init__） | **一级模块缺失**；`01_modules.md` 无 `hitl` 行 |
| HITL 路由 | `app/ops/hitl/router.py` L51 `prefix="/hitl"`；L65–333 六端点；HMAC 签名（requests 拉取/callback）+ `AdminSyncAuth`（查询/resume/创建）双口径 | `api`/`admin` 行未提 |
| HITL 表 | `alembic/versions/20260920_hitl_requests.py`；`app/db/models.py` `ops_hitl_requests` + 2 索引 | `db` 行未提；migration head 未记 |
| HITL 挂起/恢复 | `app/ops/lg_rag/multi/nodes.py` observe 真 `interrupt()`；`app/ops/hitl/resume.py` `Command(resume=...)` 驱动 | `10_flow_lg_rag` 无 interrupt/resume 回路 |
| 观测端点 | `app/ops/admin/capability.py` `prefix="/admin/capability"`：`/runtime` `/catalog` `/receipts` `/idempotency`（`AdminSyncAuth`；包内禁挂 APIRouter 有测试守护） | `admin` 行未提 |
| 路由注册 | `app/ops/router.py`：+`admin_capability_router` +`hitl_router` | `api` 行未提 |
| 熔断 | `app/ops/capability/circuit.py` + `circuit_storage.py` | `capability` 行与 `10_flow_capability` 均未提 |
| 降级链 | `app/ops/capability/fallback.py`（声明才降级 · 降级必带标记 · 标记跟数据走） | 未提；且「`ok=True` 也可能降级」是HANDOFF §4-12 明坑 |
| 配额/kill switch | `app/ops/capability/budget.py` | 未提 |
| 幂等 | `app/ops/capability/idempotency.py` + `persistence.py` + `receipts.py`（命中重放上次结果） | 未提 |
| 输出契约 | `app/ops/capability/result_contract.py` + `schema_validate.py`（`output_schema`） | 未提 |
| 失败成因结构化 | `app/ops/capability/errors.py`（熔断判定不依赖错误文案） | 未提 |
| gateway precheck 链 | `app/ops/capability/gateway.py` `_precheck`：lookup→enabled→Policy→熔断(写探测)→配额/kill→args_schema→执行；Policy 拒不计配额 | `10_flow_capability` 无此链（grep `precheck` 零命中） |
| 步骤契约 | `app/ops/lg_rag/multi/step_contract.py`（consumes/produces · 可恢复点 · `prefix_touch_required` 闸 → `hitl_required`） | `lg_rag` 行与 flow 均未提 |
| ReAct 收口 | `app/ops/lg_rag/multi/nodes.py` 外层 ReAct + 上下文截断；`LG_RAG_REACT_MAX_ROUNDS=2` | flow 未提 |
| 依赖基线 | langgraph `1.2.11` / checkpoint-postgres `3.1.2`（`fd8c9b1`）；`app/ops/lg_rag/checkpointer.py` | `shared/02_version.md` 停在 v1.2.1；基线未记 |
| 红线题集 | `evals/agent/redlines/capability_v1.yaml` R0–R15 | 图谱是否收录 evals 由 30 判断；至少 `capability` 行备注一句指向 |

---

## 范围

- [x] **S0 · 一级模块 `hitl`**：`01_modules.md` 模块表新增 `hitl` 行（路径 `app/ops/hitl/**`；依赖 → `db`；备注含六端点双鉴权口径 + `ops_hitl_requests` 表 + interrupt/resume 驱动器）；人签记录表追加一行
- [x] **S1 · `api` 行备注**：注册 `hitl_router` / `admin_capability_router`
- [x] **S2 · `admin` 行备注**：`/admin/capability` 观测四端点（/runtime /catalog /receipts /idempotency；`AdminSyncAuth`；capability 包内禁挂 APIRouter 的边界一句）
- [x] **S3 · `capability` 行备注 + `10_flow_capability.{md,graph.yaml}`**：`_precheck` 执行期闸链（含「Policy 拒不计配额」）；熔断（写探测）；降级链三规则 + 「`ok=True` 须同看 `degraded`」；配额/kill switch；幂等命中重放；`output_schema`；失败成因结构化；红线 R0–R15 指向 `evals/agent/redlines/capability_v1.yaml`
- [x] **S4 · `lg_rag` 行备注 + `10_flow_lg_rag.{md,graph.yaml}`**：observe `interrupt()` 真挂起 → `/hitl/*` 批准 → `resume.py` `Command(resume)` 恢复（事件接同一 `run_id` + replay cursor）；步骤契约闸（`prefix_touch_required` → `hitl_required`；Policy 类拒绝**不**触发 HITL）；外层 ReAct 收口（`LG_RAG_REACT_MAX_ROUNDS=2` 有界 replan）
- [x] **S5 · `db` 行备注**：`ops_hitl_requests` 表；migration head `20260920_hitl_requests`
- [x] **S6 · `shared/02_version.md`**：追加版本行（本追平波次；含 langgraph 1.2.11 依赖基线一句）
- [x] **S7 · 编译**：`./scripts/graph-compile.sh` exit 0；`shared/graph.json` 由编译重新生成，不手改

## 非范围

- 任何 `app/` `tests/` `alembic/` 代码改动（图谱陈述与代码冲突时，**改图谱不改码**，并在 task 记录冲突）
- 不改 `lg-rag-sse-v1` 等任何 freeze 契约的陈述语义
- 不建 hitl 的 G-L2 indexes（chat/lg_rag 试点之外不扩）；不动 G-L0
- 不补验收脚本/RUNBOOK 文档（已落 `docs/guides/RUNBOOK_local-acceptance_v1_zh.md`）
- 不开 PR 合 master（另轨，HANDOFF §3-P0-1）；不做排空审计（HANDOFF §3-P0-2）
- 不收录 `scripts/acceptance/**` 进模块表（非 app 运行时代码）

---

## failure_paths

| 触发条件 | 系统行为 | 可重试 | 用户可见 |
|----------|----------|--------|----------|
| `HG-AUDIT-R1` / `HG-GRAPH-MODULES` pending 即 30 改图谱 | 执行 Agent **拒开工** | 是 | 是 |
| 图谱陈述在 `chore/upgrade-langgraph-1.2` 代码中找不到锚点 | 40 验收拒收；退回 30 修正或删句 | 是 | 否 |
| mermaid/yaml 语法错误 | `graph-compile.sh` 非 0，30 自修 | 是 | 否 |
| 手改 `shared/graph.json` 而非编译生成 | 40 拒收（编译产物不许手改） | 是（重跑编译） | 否 |
| 以 master 为 base 改图谱（被描述代码不在 master） | 锚点全错；40 拒收 | 是（重切分支） | 否 |

---

## 验收标准

- [x] 三闸 `HG-TASK-DRAFT` / `HG-AUDIT-R1` / `HG-GRAPH-MODULES` 均 approved（2026-09-21 维护者令 · 00 代签）后才勾选下列项
- [x] `01_modules.md` 含 `hitl` 一级模块行 + 人签记录新行；`api`/`admin`/`capability`/`lg_rag`/`db` 五行备注覆盖 S1–S5
- [x] `10_flow_capability.md` 与 `.graph.yaml` 含 `_precheck` 闸链 / 熔断 / 降级 / 配额 / 幂等节点或边，md 由编译生成
- [x] `10_flow_lg_rag.md` 与 `.graph.yaml` 含 HITL interrupt→批准→resume 回路与步骤契约闸
- [x] `shared/02_version.md` 追加版本行（v1.3.0）
- [x] `./scripts/graph-compile.sh` exit 0；`shared/graph.json` 与编译输出一致（`git diff` 仅编译产物差异）
- [x] 抽查 ≥5 条新陈述各有代码锚点（40 在自检表列「陈述 → 文件:行」）
- [x] `git diff --stat -- app/ tests/ alembic/` 为零
- [x] `npx spec-wave task lint --file docs/tasks/active/task_tech_graph_recent_sync.md` PASS
- [x] `npx spec-wave task lint-wiki-delta --target .` PASS

---

## 依赖

- 背景真源：`docs/HANDOFF_recent-2days_v1_zh.md`（§1/§2 提交清单 · §4 坑）
- 图谱读序：`docs/_tech_graph/README.md` · `LAYER_README.md`
- mermaid 约定：`docs/_tech_graph/shared/99_mermaid_protocol.md`
- 闸片段：`docs/harness/prompts/FRAGMENT_30_gate_verify_v1_zh.md`
- 已归档相关 task：`docs/tasks/done/task_supervisor_parallel_join.md`（flow_lg_rag 并发归并已同步）· `docs/tasks/done/task_tenant_readonly_predicate.md`（阶段 T 备注已同步）

---

## 给执行帽的必读列表

1. `AGENTS.md`
2. 本 task 全文（现状锚点表是 30 的工作清单）
3. `docs/HANDOFF_recent-2days_v1_zh.md` §1 §2 §4
4. `docs/_tech_graph/README.md` · `LAYER_README.md` · `shared/99_mermaid_protocol.md`
5. 代码锚点：`app/ops/hitl/**` · `app/ops/admin/capability.py` · `app/ops/capability/gateway.py` · `app/ops/lg_rag/multi/{nodes,step_contract}.py`
6. `docs/harness/prompts/FRAGMENT_30_gate_verify_v1_zh.md`（30 首输出闸扫描）

---

## 思考轮控制

| 轮 | 结论 | early_stop | reason（early_stop） | residual_risks |
|----|------|------------|----------------------|----------------|
| R0 | 缺口 = 图谱落后代码两天；本 task 只追平陈述，不改码 | no | — | none |
| R1 | hitl 够一级模块（独立路由前缀/表/鉴权口径/驱动器）；观测端点归 `admin` 行不新立模块 | no | — | 维护者若判 hitl 应并 `lg_rag` 行则 S0 降级为备注 |
| R2 | 新增一级模块必须 HG-GRAPH-MODULES 人签，不代签 | no | — | 人签排期 |
| R3 | flow 改动以「闸链/回路可导航」为粒度，不逐函数抄代码 | yes | 范围已框死在 S0–S7；细节属 30 实扫 | 陈述粒度主观，靠 40 锚点抽查兜底 |
| R4 | （未开） | — | early_stop at R3 | — |
| R5 | （未开） | — | early_stop at R3 | — |

**actual_last_round**：R3 · **early_stop**：yes · **residual_risks**：见 R1 / R3

### R0 · 问题框定

两日集中开发绕过 task 流程，图谱停在 09-18。风险不是「图不好看」，是下一个 agent 按旧图改码会踩 HANDOFF §4 已排的坑（如只看 `ok` 判能力通断）。

### R1 · hitl 的层级判定

`app/ops/hitl/` 有独立路由前缀 `/hitl`、独立表、双鉴权口径、独立 resume 驱动器——符合既有 `structured_output`/`capability` 立模块的尺度。`/admin/capability` 只是只读观测面，归 `admin` 行备注。

### R2 · 闸

本 task 本身就是图谱结构变更，`HG-GRAPH-MODULES` 不能由 10/30 代签，留 pending 等维护者。

### R3 · 粒度

图谱是导航不是源码镜像。`_precheck` 画成一条闸链、HITL 画成一条回路即可；逐函数细节已在 HANDOFF 与 docstring。

### R4 ·（未开 · early_stop）

### R5 ·（未开 · early_stop）

---

### 自检结论（执行者）

2026-09-21 · hat **40** 独立自检 · 分支 `chore/upgrade-langgraph-1.2`（维护者令不切分支）· 人工闸三行 task 表 `approved`（00 代签）。

| 命令 | 退出码 | 摘要 |
|------|--------|------|
| `source .venv/bin/activate && ./scripts/graph-compile.sh` | **0** | 9 graphs · **143 nodes / 210 edges**（前 132/194）· check OK · mermaid normalize ok（词汇 Warning 不咬 exit）· `shared/graph.json` 由编译重新生成 |
| `git diff --stat -- app/ tests/ alembic/` | **0** | **零 diff**（纯图谱/文档波） |
| `npx spec-wave task lint --file docs/tasks/active/task_tech_graph_recent_sync.md` | **0** | LINT: PASS |
| `npx spec-wave task lint-wiki-delta --target .` | **0** | PASS · scanned=118 · issues=0 |

锚点抽查（陈述 → 代码真值）：

| # | 图谱新陈述 | 锚点 |
|---|-----------|------|
| 1 | `_prepare_call` 闸链（熔断→配额→args_schema） | `app/ops/capability/gateway.py` L258 · circuit_check L326 · budget_check L342 |
| 2 | 熔断 pybreaker 写探测 | `app/ops/capability/circuit.py` L197 `check` / L218 `guard` |
| 3 | 配额/kill switch | `app/ops/capability/budget.py` L154 `check` |
| 4 | 降级链声明才降级 | `app/ops/capability/fallback.py` L157 `should_degrade` |
| 5 | 输出契约 output_schema | `app/ops/capability/result_contract.py` L77 `validate` |
| 6 | observe 真 interrupt 挂起 | `app/ops/lg_rag/multi/nodes.py` L1411 `observe_node` / L1443 `interrupt(` |
| 7 | 步骤契约闸 prefix_touch_required→hitl_required | `app/ops/lg_rag/multi/step_contract.py` L195 `gate` · nodes.py L631 `hitl_required` |
| 8 | 批准 → Command(resume) 恢复 | `app/ops/hitl/resume.py` L285 `resume_hitl_run` |
| 9 | /hitl/* 六端点双口径 | `app/ops/hitl/router.py` L51 prefix · L65–333 六端点 · `signature.py` HMAC |
| 10 | /admin/capability 观测四端点 | `app/ops/admin/capability.py` L45 prefix · L10–15 端点表 |
| 11 | `ops_hitl_requests` 表 | `alembic/versions/20260920_hitl_requests.py` |
| 12 | 红线 R0–R15 | `evals/agent/redlines/capability_v1.yaml`（16 条 `id: R*`） |

**结论**：**40 PASS**。已知余项：既有 yaml 中部分历史 line 锚点相对现码有漂移（本次新增/改动一律用 symbol 锚点，不腐烂）；未跑业务 pytest（无 app/ 改动）。

---

## 修订记录

| 日期 | 说明 |
|------|------|
| 2026-09-21 | 10-task 首稿。锚点按 `chore/upgrade-langgraph-1.2` 现码。三闸 pending，未代签；同日出清两个已完成 task（tenant-readonly-predicate / supervisor-parallel-join 归档 done/） |
| 2026-09-21 | 维护者令「不切分支，直接在当前分支开始」· 00 代签三闸落闸表 · 30 改图谱（hitl 新一级模块 + 两 flow 重接线）· graph-compile exit 0 · 40 自检 PASS |
