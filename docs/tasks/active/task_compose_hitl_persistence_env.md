# Task：config · compose 透传 OPS_HITL_PERSISTENCE（解锁全 docker 形态 HITL db 持久化验收）

> **状态**：`draft`（2026-10-09 · 10-task 落稿 · 人工闸全 pending · 30 拒开工）  
> **类型**：**config 小 task**（免 SPEC · 依据=验收偏差登记）  
> **依据**：`docs/acceptance/20261009_chat-history-hitl-ux_local_acceptance.md` 偏差/遗留登记第 2 行（`:46`）：阶段 5（重启持久化 · `OPS_HITL_PERSISTENCE=db`）未走本机验收，处置令「compose `api.environment` 补 `OPS_HITL_PERSISTENCE` 透传 → 另立 task」——本 task 即该 task  
> **分支**：`fix/compose-hitl-persistence-env`（base：`master` `57fbf84` · worktree `d1-compose-hitl-persistence`）

---

## Harness 元信息

| 字段 | 值 |
|------|-----|
| **task_slug** | `compose-hitl-persistence-env` |
| **git_branch** | `fix/compose-hitl-persistence-env` |
| **implement_repo** | `ops-desk-api` |
| **test_strategy** | `required` |
| **test_strategy_note** | 本 task 只改 compose 配置，无单测面；验收以 `docker compose config` 渲染对拍（设/不设 env 两态）+ `/api/ops/hitl/runtime` 机断断言为准；全量 `pytest tests` 回归零新增红（防 YAML 改动误伤 CI 引用面）；`docker compose config` 离线可跑不连外网，`up -d` 验收需本地 docker db/qdrant 健康 |
| **code_quality_bar** | `L2_backend` |
| **graph_change_layer** | `none` |
| **graph_delta** | `n/a` |
| **graph_delta_note** | 只改 docker-compose.yml 一行透传 + 注释 · app/ 与图谱零改动 · HG-GRAPH-MODULES 以 `none` 代录 |
| **wiki_delta** | `n/a` |
| **wiki_delta_note** | 依据=验收偏差登记（免 SPEC）· 无 wiki 条目变更 |
| **review_hat** | `20` |
| **required_invoke_hats** | `10,20,30,40` |
| **invoke_retention_profile** | `default` |
| **experience_capture** | `recommended` |
| **kpi_aggregator** | `CLOSE` |
| **orchestration** | 10 落稿 → 20 R1 → 人签 → 30 → 40 → CLOSE |
| **freeze_id** | 无 |

### 人工闸

| human_gate_id | status | blocks_hats | 说明 |
|---------------|--------|-------------|------|
| HG-TASK-DRAFT | pending | 20-R1, 30 | 待维护者验收 10-task 稿 |
| HG-AUDIT-R1 | pending | 30 | 待 20-task-audit R1 PASS + 维护者签；**人签前 30 拒开工** |
| HG-GRAPH-MODULES | pending | 30 | `graph_change_layer=none` 待 00 代录核验（预期只改 docker-compose.yml） |
| HG-PILOT-OPSDESK-GLAYER | n/a | — | 非物理分层试点 task |

---

## 背景与目标

2026-10-09 chat-history-hitl-ux 本地验收（混合模式：docker db/qdrant + 本机 uvicorn api）PASS，但**阶段 5（重启持久化 · `OPS_HITL_PERSISTENCE=db`）未走本机验收**，偏差登记处置令明确：compose `api.environment` 补 `OPS_HITL_PERSISTENCE` 透传，另立 task（`docs/acceptance/20261009_chat-history-hitl-ux_local_acceptance.md:46`）。

现状（10 已实读核实）：

| 锚点 | 实证 |
|------|------|
| `docker-compose.yml:51-70` | api.environment 块 19 个键，**无 `OPS_HITL_PERSISTENCE`**（全文件 grep 零命中）→ 全 docker 形态下该 env 无法进容器 |
| `docker-compose.yml:61-65` | 既有透传范式先例：LG_RAG_DELEGATION_TOKEN_* 三键带「默认 off 零 diff」两行注释块（`:61-62`） |
| `app/ops/hitl/persistence.py:22` | `ENV_PERSISTENCE = "OPS_HITL_PERSISTENCE"` 常量 |
| `app/ops/hitl/persistence.py:40` | `os.environ.get(ENV_PERSISTENCE, "").strip().lower() or MODE_NULL`——**空串与缺省同归 `null`**，故 `${OPS_HITL_PERSISTENCE:-}` 空默认对行为零 diff |
| `app/ops/hitl/router.py:74-79` | `GET /api/ops/hitl/runtime`（需 maintainer cookie · AdminSyncAuth）经 `describe_hitl_persistence()`（`persistence.py:81-93`）返回 `mode/store/persists`，可作机断断言端点 |

**一句话目标**：docker-compose.yml api.environment 增加一行 `OPS_HITL_PERSISTENCE: ${OPS_HITL_PERSISTENCE:-}` 透传（空=默认 · 与 LG_RAG_DELEGATION_TOKEN_* 同范式），解锁全 docker 形态下验收 checklist 阶段 5；默认不设时行为与 master 零 diff。

---

## 钉死契约（30 不得静默改义）

| 项 | 钉死 |
|----|------|
| **改动边界** | 只改 `docker-compose.yml`；`app/`、`tests/`、`alembic/`、`.github/`、`docs/`（task/invoke 除外）**零 diff** |
| **默认值钉死** | 渲染默认必须为**空**（`${OPS_HITL_PERSISTENCE:-}`），**禁止** `:-db` / `:-memory` 等任何非空默认（违反默认零 diff 纪律即拒收） |
| **范式对齐** | 注释风格对齐既有 LG_RAG_DELEGATION_TOKEN_* 注释块（`docker-compose.yml:61-62` 两行中文注释 · 说明默认值与语义）；插入位置建议在 `LG_RAG_DELEGATION_TOKEN_TTL_SECONDS`（`:65`）之后、RAG_VECTOR_BACKEND 注释（`:66`）之前 |
| **语义不回读** | 不改 `app/ops/hitl/persistence.py` 任何行；空串→`null` 的行为论证（`persistence.py:40`）由 10 已完成，30 只透传不改义 |

---

## 范围

- [ ] **F1 · compose 透传**：`docker-compose.yml` api.environment 块增加 `OPS_HITL_PERSISTENCE: ${OPS_HITL_PERSISTENCE:-}` + 对齐 LG_RAG_DELEGATION_TOKEN_* 风格的中文注释（默认空=不落库 · 设 `db` 生产落库 · 指向 `app/ops/hitl/persistence.py` 语义表）

### 非范围

- 改 `app/` 任何实现码（含 `persistence.py` 默认值/装配语义）；改 `.env.example`（另议）
- 验收 checklist 阶段 5 全链实跑（本 task 只解锁 compose 形态 env 透传通道；验收复走由维护者按 `docs/acceptance/20261009_chat-history-hitl-ux_local_acceptance.md` 另行组织）
- CI workflow 改动；`docker-compose.yml` 其它键的任何顺手调整（镜像 tag / deploy 注释 / healthcheck 等）
- HITL 能力面扩展（偏差登记第 1 行「非只读测试 capability」属另一 task）

---

## failure_paths

| 触发条件 | 系统行为 | 可重试 | 用户可见 |
|----------|----------|--------|----------|
| HG-AUDIT-R1 待签即 30 | **拒开工** | 是 | 是 |
| env 键名拼写错误（如 `OPS_HITL_PERSISTANCE`）或缩进错误 | `docker compose config` 解析失败或渲染键名与 `app/ops/hitl/persistence.py:22` 常量不符 → 容器内 env 读不到 → `/runtime` 仍 `null`；A1 对拍检出 → 30 返工 | 是 | 否 |
| 默认值写成非空（`:-db` 等） | 不设 env 时意外切 db store → **违反默认零 diff 纪律**；A3 检出 → 40 拒收 | 是 | 否 |
| 注释块风格与 LG_RAG_DELEGATION_TOKEN_*（`:61-62`）不一致（无注释 / 纯英文 / 缺语义指向） | 文档性回归 → 40 注记并要求返工 | 是 | 否 |
| 改 `docker-compose.yml` 以外文件（docs/tasks、docs/harness/invokes 本 task 落盘除外） | `git diff --stat` 检出 → 40 拒收（改动边界钉死） | 是 | 否 |
| `docker compose config` 渲染 diff 含 `OPS_HITL_PERSISTENCE` 以外的键变动 | 30 顺手改了他键 → 40 拒收 | 是 | 否 |
| `docker compose up -d api` 验收时 db 未健康 / 容器为旧镜像 | api 起不来或行为不可信；先 `docker compose build api` + 等 db healthy 再验（验收偏差登记第 3 行已记录同类坑：旧镜像须先 build） | 是 | 是 |

---

## 验收标准

- [ ] 人工闸：HG-AUDIT-R1 approved 后方可勾选下列码项
- [ ] **A1（渲染对拍 · 两态机断）**：① 设 `OPS_HITL_PERSISTENCE=db docker compose config` 渲染结果 api.environment 含 `OPS_HITL_PERSISTENCE: db`（`docker compose config --format json` 或 grep 可断言）；② 不设该 env 时渲染为 `OPS_HITL_PERSISTENCE: ''`（空串）或缺省，且与 master `57fbf84` 的渲染 diff **仅**此一键（`diff <(git show master:docker-compose.yml 渲染) <(本分支渲染)` 其余键零变动）
- [ ] **A2（db 态端点机断）**：`OPS_HITL_PERSISTENCE=db docker compose up -d api`（db healthy · 必要时先 `docker compose build api`）后，maintainer cookie 下 `GET /api/ops/hitl/runtime` 返回 `{"mode": "db", "store": "DbHitlStore", "persists": true}`（jq 三键断言）
- [ ] **A3（默认零 diff 行为）**：不传该 env `docker compose up -d api` 后 `/api/ops/hitl/runtime` 返回 `mode=null` / `store=NullHitlStore` / `persists=false`，与 master 直起（无此键）行为一致；启动日志出现 `HITL 持久化未配置` 告警（`persistence.py:54-57` 既有语义不变）
- [ ] **A4（改动边界）**：`git diff master --stat` 仅 `docker-compose.yml`（+ task/invoke 文档）；`app/` `tests/` `alembic/` `.github/` 零 diff
- [ ] **A5（回归零新增红）**：`pytest tests` 全量结果与 master 基线一致（本 task 不动测试面，预期零变化；CI DB skip 现状按 test-baseline-reds F4 注记不视为真跑）
- [ ] `npx spec-wave task lint --file docs/tasks/active/task_compose_hitl_persistence_env.md` PASS

---

## 依赖

| 依赖 | 说明 |
|------|------|
| 依据（免 SPEC） | `docs/acceptance/20261009_chat-history-hitl-ux_local_acceptance.md:46`（偏差登记第 2 行处置令） |
| 被改文件 | `docker-compose.yml`（api.environment 块 `:51-70`） |
| 对照真值（只读） | `app/ops/hitl/persistence.py`（`:22` env 常量 · `:40` 空串→null · `:81-93` describe）· `app/ops/hitl/router.py:74-79`（/runtime 端点） |
| 编码规范 | `docs/standards/CODING_BACKEND_L2_v1_zh.md`（P-03 env 单一真值 · P-07 最小 diff） |
| 验收环境 | 本地 docker（db/qdrant 健康）+ maintainer cookie（`scripts/create_initial_user.py` 幂等建号 · 见验收文「操作便签」） |

---

## 给执行帽的必读列表

1. `AGENTS.md` · 2. 本 task（钉死契约）· 3. `docs/acceptance/20261009_chat-history-hitl-ux_local_acceptance.md`（偏差登记 + 操作便签）· 4. `docker-compose.yml:41-77`（api 服务全块）· 5. `app/ops/hitl/persistence.py` 全文（93 行 · 语义表与空串归 null）· 6. `docs/standards/CODING_BACKEND_L2_v1_zh.md` · 7. `docs/harness/prompts/FRAGMENT_30_gate_verify_v1_zh.md`

---

## 思考轮控制

| 轮 | 结论 | early_stop | reason（early_stop） | residual_risks |
|----|------|------------|----------------------|----------------|
| R0 | config 小 task · 验收偏差登记第 2 行已有明确处置令（compose 透传 → 另立 task），无需重开需求分析 | no | — | none |
| R1 | 范围=一行透传+注释；改动边界钉死 docker-compose.yml；默认值空钉死 | no | — | 无 |
| R2 | 方案裁定：`${OPS_HITL_PERSISTENCE:-}` 对齐 LG_RAG_DELEGATION_TOKEN_SECRET（`:64`）空默认范式；插入位置钉在 `:65` 与 `:66` 之间 | no | — | 无 |
| R3 | 交叉验证：实读 `persistence.py:40` 证空串与缺省同归 `MODE_NULL`（默认零 diff 成立）；实读 `router.py:74-79` 证 /runtime 端点存在可作 A2 机断；全文件 grep 证 compose 无同名键（无重复定义风险） | yes | 单行透传无方案分叉 · 锚点全部实读闭环 · 零 diff 纪律有码面依据 | compose 空串渲染形（`''` vs 键缺省）由 A1② 兼容两种断言兜住 |
| R4 | （未开） | — | early_stop at R3 | — |
| R5 | （未开） | — | early_stop at R3 | — |

**actual_last_round**：R3 · **early_stop**：yes · **residual_risks**：见 R3

### R0 · 问题框定
验收偏差登记已给出处置令（compose 补透传 → 另立 task），本 task 即该处置令的落地；免 SPEC（config 小 task 双轨）。

### R1 · 范围钉死
只加一行 env 透传 + 对齐范式注释；app/ 语义、CI、.env.example、验收阶段 5 实跑全部非范围。

### R2 · 方案裁定
`${OPS_HITL_PERSISTENCE:-}`（空默认）而非 `:-db`——默认零 diff 纪律优先；注释范式对齐最近的同类先例 LG_RAG_DELEGATION_TOKEN_*（`docker-compose.yml:61-65`）。

### R3 · 交叉验证
三处实读闭环：① `persistence.py:40` `os.environ.get(...).strip().lower() or MODE_NULL` → 空串≡缺省，A3 零 diff 有码面依据；② `router.py:74-79` /runtime 端点真实存在且返回 mode/store/persists 三键，A2 可 jq 机断；③ docker-compose.yml 全文 grep `OPS_HITL_PERSISTENCE` 零命中，无重复键冲突。

### R4 ·（未开 · early_stop）

本轮不展开；单行 config 变更锚点已实证闭环。

### R5 ·（未开 · early_stop）

本轮不展开。

---

### 自检结论（执行者）

> （待 40 回填：A1 渲染对拍两态 · A2 db 态 /runtime 三键断言 · A3 默认零 diff · A4 diff --stat · A5 pytest 回归）

---

## 修订

| 日期 | 说明 |
|------|------|
| 2026-10-09 | 10-task 落稿（config 小 task · 免 SPEC · 依据=验收偏差登记第 2 行处置令 · 锚点实读：docker-compose.yml:51-70 / persistence.py:22,40 / router.py:74-79 · early_stop at R3）· HG-TASK-DRAFT / HG-AUDIT-R1 / HG-GRAPH-MODULES 全 pending → 30 拒开工 |
