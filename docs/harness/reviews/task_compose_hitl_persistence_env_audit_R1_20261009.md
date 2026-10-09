# R1 审查 · task_compose_hitl_persistence_env（帽 20-task-audit）

## 元信息

| 项 | 值 |
|---|---|
| **审查帽** | 20-task-audit（任务书面审查 · 不实现代码 · 不改 task 实质内容） |
| **日期** | 2026-10-09 |
| **审查对象** | `docs/tasks/active/task_compose_hitl_persistence_env.md`（D1 · config 小 task · 免 SPEC · slug `compose-hitl-persistence-env` · commit `cd19feb`） |
| **对照真值** | 需求真值 = `docs/acceptance/20261009_chat-history-hitl-ux_local_acceptance.md:46`（偏差/遗留登记表第 2 行处置令 · 实读确认行号）· 代码锚点 `docker-compose.yml:51-70` / `app/ops/hitl/persistence.py:22,40,81-93` / `app/ops/hitl/router.py:74-79` · 标准 `docs/standards/CODING_BACKEND_L2_v1_zh.md` |
| **审查方式** | 真值源真读（验收登记 / compose / persistence / router）+ 锚点逐条核实 + 机跑实证（task lint / spec-wave verify / git branch / merge-base / grep 耦合面） |
| **轮次** | R1（HG-AUDIT-R1 仍 pending · 20 只书面审 · 不代签 human_gate） |

---

## 机跑证据（命令 · 退出码）

| 命令 | 结果 | 退出码 |
|---|---|---|
| `git branch --show-current`（worktree d1-compose-hitl-persistence） | `fix/compose-hitl-persistence-env` | 0 |
| `git merge-base master HEAD` | `57fbf84`（与 task 钉死 base 一致） | 0 |
| `git diff master --stat` | 仅 task 文档 + 10-task invoke 快照两文件（+201 行 · 业务码零 diff · 符合 draft 期形态） | 0 |
| `npx spec-wave task lint --file docs/tasks/active/task_compose_hitl_persistence_env.md` | `LINT: PASS · task_compose_hitl_persistence_env.md` | **0** |
| `npx spec-wave verify --target . --task docs/tasks/active/task_compose_hitl_persistence_env.md` | `VERIFY: BLOCKED · HG-AUDIT-R1 pending`（HG-TASK-DRAFT / HG-AUDIT-R1 / HG-GRAPH-MODULES 三闸 pending → 30 拒开工） | **2**（流程闸未签 · 非内容缺陷） |
| `grep -n OPS_HITL_PERSISTENCE docker-compose.yml` | 零命中（无重复键冲突 · task R3 ③ 属实） | 1（预期） |
| grep `docker-compose` 于 `tests/` 全目录 | **零命中** | — |
| grep `docker compose` 于 `.github/workflows/` | 仅 `deploy-api.yml:72-81` 引用 `docker-compose.prod.yml`（**非本 task 所改文件**）；CI 对 `docker-compose.yml` 零引用 | — |

---

## 核对项表 · 流程闸（与内容分开列）

| # | 核对项 | 证据 | 判定 |
|---|--------|------|------|
| P1 | HG-TASK-DRAFT | task 人工闸表 L37 = `pending` · blocks「20-R1, 30」 | ⏳ pending（维护者尚未扫签） |
| P2 | HG-AUDIT-R1 | task 人工闸表 L38 = `pending` · blocks 30；本 R1 审查文落盘后交维护者人签 | ⏳ pending（20 不代签） |
| P3 | HG-GRAPH-MODULES | task 人工闸表 L39 = `pending` · blocks 30；`graph_change_layer=none`（L20）+ `graph_delta_note`（L22）如实「只改 docker-compose.yml · app/ 与图谱零改动」；本 task 不新增路由/表/事件类型，AGENTS.md 图谱同步条款不触发，`none` 代录恰当 | ⏳ pending（待 00 代录核验 · 随交付签录） |
| P4 | HG-PILOT-OPSDESK-GLAYER | task 人工闸表 L40 = `n/a`（非物理分层试点 task） | ✅ n/a 恰当 |
| P5 | 分支隔离（禁 master 直改） | worktree 分支 `fix/compose-hitl-persistence-env`（fix/ 前缀符合小修约定）· base `57fbf84` 与 task L6 一致 · master 零直改 | ✅ |
| P6 | task lint 机械闸 | `task lint` = **PASS · EXIT=0** | ✅ |
| P7 | spec-wave verify | **EXIT=2 · BLOCKED**（三闸 pending）· 30 必须拒开工 | ⏳ 属实（非内容缺陷） |
| P8 | invoke 快照 | `required_invoke_hats=10,20,30,40`（L26）**含 20** → 按 skill 分工本轮须落盘 20 invoke；10 快照 `invoke_20261009_10_task_compose-hitl-persistence-env.md` 已随 cd19feb 落盘；20 快照随本审查 commit 补齐 | ✅（本轮落盘） |

---

## 核对项表 · 内容

| # | 核对项 | 证据 | 判定 |
|---|--------|------|------|
| C1 | 需求真值承接（免 SPEC 双轨） | 实读 `docs/acceptance/20261009_chat-history-hitl-ux_local_acceptance.md:41-49`：偏差/遗留登记表第 2 行（**实读确认 = 文件 :46**）=「阶段 5（重启持久化 · `OPS_HITL_PERSISTENCE=db`）未走本机验收 → 处置：compose `api.environment` 补 `OPS_HITL_PERSISTENCE` 透传 → 另立 task」；task L5/L46/L116 引用行号与内容**逐字属实**；免 SPEC 定性（config 小 task）与处置令粒度相称 | ✅ |
| C2 | 范围钉死 | 范围仅 F1（L75）：一行透传 + 对齐范式注释；钉死契约 L64-69 四条（改动边界 / 默认值空 / 范式对齐 / 语义不回读）与处置令一一对应 | ✅ |
| C3 | 非范围锁死 | L79-82 四条：app/ 实现码与 .env.example / 验收阶段 5 全链实跑（归维护者另行组织）/ CI 与其它键顺手调整 / HITL 能力面扩展（=偏差登记第 1 行 · 另 task）；边界干净无悬置 | ✅ |
| C4 | 锚点真实（逐条实读，非只信 task） | 全部命中：`docker-compose.yml:51-70` = api.environment 块 ✓ · `:61-62` LG_RAG_DELEGATION_TOKEN_* 两行中文注释 ✓ · `:63-65` 三键（`:-off` / `:-` / `:-600`）✓ · `:66` RAG_VECTOR_BACKEND 注释 ✓（插入位 `:65-66` 之间成立）· `persistence.py:22` `ENV_PERSISTENCE = "OPS_HITL_PERSISTENCE"` ✓ · `:40` `os.environ.get(ENV_PERSISTENCE, "").strip().lower() or MODE_NULL` ✓（空串≡缺省 · 默认零 diff 的码面依据成立）· `:54-57` 「HITL 持久化未配置」告警文案 ✓ · `:81-93` `describe_hitl_persistence()` 返回 mode/store/persists ✓ · `router.py:74-79` `GET /runtime`（AdminSyncAuth）✓ | ✅ |
| C5 | 验收可机断性（A1–A5 + lint） | A1 两态渲染断言（grep / `--format json` + diff 仅此一键）· A2 `/runtime` jq 三键（`{"mode":"db","store":"DbHitlStore","persists":true}` 与 `describe_hitl_persistence` :85-92 输出逐键吻合 · 端点多出的 `callback_secret_configured` 键不影响 jq 三键断言）· A3 默认三键 + 启动告警文案（:54-57 原文命中）· A4 `git diff master --stat` 白名单 · A5 pytest 基线对拍 · 外加 `task lint`；全部可对命令机械断言，无主观措辞 | ✅（A1② 命令写法见 nit N2） |
| C6 | failure_paths 完备锋利 | L90-96 共 7 条：未签闸拒开工 / 拼写缩进错（A1 检出返工）/ 非空默认（A3 检出 40 拒收）/ 注释风格回归 / 越改动边界（diff --stat 检出）/ 渲染带他键变动（A1② 检出）/ docker 验收前置坑（build + db healthy · 承接验收登记第 3 行 :47 旧镜像坑）；均含「可重试/用户可见」，与验收项一一联锁 | ✅ |
| C7 | 思考轮 R0–R5 控制表与回填闭合 | L132-141 控制表：R0–R3 四轮有结论 · early_stop at R3（理由：单行透传无方案分叉 · 锚点全实读闭环 · 零 diff 纪律有码面依据）· R4/R5 标「未开 · early_stop」· `actual_last_round=R3` · residual_risks 如实登记「空串渲染形（`''` vs 键缺省）由 A1② 兼容两态兜住」；L143-161 各节回填与控制表闭合一致；对单行 config task，early_stop at R3 理由成立 | ✅ 闭合 |
| C8 | 行为变更类「旧测 grep 影响面」（K7 提醒） | 本 task 不改默认值/校验/策略门/fallback 语义（app/ 零 diff · 渲染默认空 → 运行时零 diff），K7 不严格触发；实证兜底：`tests/` 对 docker-compose 零引用（grep 零命中）· CI workflows 仅 deploy 用 `docker-compose.prod.yml`（非本文件）→ **旧测影响面 = 零**（有机跑证据） | ✅ |
| C9 | graph_change_layer / review_hat / 生产字段 | `graph_change_layer=none`（L20）恰当（不新增路由/表/事件）· `review_hat=20`（L25）· `test_strategy=required` + note（L17-18）· `orchestration`（L30）· `kpi_aggregator=CLOSE`（L29）齐备 | ✅ |
| C10 | 依赖与必读列表真实 | 依赖表 L114-120：验收登记 :46 ✓ · 被改文件 :51-70 ✓ · 对照真值 persistence/router 锚点 ✓ · 标准文件存在 ✓ · `scripts/create_initial_user.py` 存在 ✓；必读 L126 七项全部实证存在（含 `FRAGMENT_30_gate_verify_v1_zh.md` ✓ · conftest F4 注记 :12 存在 ✓） | ✅ |
| C11 | A2/A3 前置环境风险如实 | A2 明示「db healthy · 必要时先 `docker compose build api`」承接验收登记第 3 行（旧镜像坑 :47）；failure_paths 第 7 条同义兜底；`depends_on db: service_healthy`（compose :71-73）使 `up -d api` 自动带 db · 与 A2 命令兼容 | ✅ |
| C12 | 范式对齐先例引用准确 | `LG_RAG_DELEGATION_TOKEN_SECRET: ${LG_RAG_DELEGATION_TOKEN_SECRET:-}`（:64）即空默认透传先例，与拟定 `OPS_HITL_PERSISTENCE: ${OPS_HITL_PERSISTENCE:-}` 同范式；注释块 :61-62 两行中文风格明确 | ✅ |

**核对计数**：内容 12 项 · 通过 12 · 不通过 0（C5 附非阻塞 nit N2 · C1/C4 附 nit N1）。

---

## 起草者自报五要点 · 逐条裁定

| # | 要点 | 裁定 | 理由 |
|---|------|------|------|
| Q1 | A1②「与 master 渲染 diff 仅此一键」对拍命令写法是否够机断 | **PASS（附 nit N2）** | **断言本身可机断**（diff 输出仅含 `OPS_HITL_PERSISTENCE` 一键 · 二值判定无主观空间）；但 task L103 的 `diff <(git show master:docker-compose.yml 渲染) <(本分支渲染)` 是**伪码简写**，不可直接执行——`git show` 产出的是源 YAML，须先落临时文件再经 `docker compose -f` 渲染，且跨目录渲染需固定 `--project-directory` 防 project 名前缀污染 volume/network 名。裁定：验收标准成立 · 命令写法够「机断目标」但不够「机断执行」，留 nit 给 30/40 具体化（参考命令见 N2），不阻塞 |
| Q2 | failure_paths 第 2 条（拼写/缩进 → 读不到 → 仍 null）与 A2 的联锁是否充分 | **PASS · 充分** | 三层检出链完整：① YAML 解析失败 → `docker compose config` 非零退出 → A1 直接 fail；② 键名拼错但仍合法 YAML → A1① 精确键名 grep 断言失败 + A1② diff 出现非预期键；③ 若渲染层漏网 → A2 行为层 `/runtime` 仍 `null` ≠ 期望 `db` 兜底。FP 第 2 条写「A1 对拍检出 → 30 返工」如实（主检出器确为 A1），A2 为端到端行为确认，纵深防御成立，无需补强 |
| Q3 | A5 pytest 回归对纯 config 改动是否过度 | **PASS · 保留不裁减**（40 可注记替代本地跑） | 实证：`tests/` 对 docker-compose **零引用**、CI 仅 deploy workflow 引用 `docker-compose.prod.yml`（非本文件）→ A5 实质是「零变化断言」而非真回归面。但合并必经 PR + CI 必跑 pytest，增量成本≈0，且 task 已自注「预期零变化 · CI DB skip 按 F4 注记不视为真跑」（L107）。裁定：**不过度、保留**；40 执行时可裁为注记——「CI 绿 + tests/ 零 diff + 耦合面 grep 零命中」即可满足 A5 意图，不必本地再全量跑 |
| Q4 | 人工闸三 pending 是否齐备 | **PASS · 齐备** | HG-TASK-DRAFT（blocks 20-R1,30）/ HG-AUDIT-R1（blocks 30）/ HG-GRAPH-MODULES（blocks 30 · `none` 待 00 代录核验）三闸全 pending 且 blocks 标注正确；HG-PILOT-OPSDESK-GLAYER=n/a 恰当；`spec-wave verify` EXIT=2 机跑确认三闸拒 30 生效 |
| Q5 | 「禁止 `:-db` 非空默认」契约是否需强化 | **PASS · 无需强化** | 已三层钉死：钉死契约 L67「禁止 `:-db`/`:-memory` 等任何非空默认（违反即拒收）」+ failure_paths 第 3 条「A3 检出 → 40 拒收」+ A1②（不设 env 渲染为空/缺省 · diff 仅此一键）/ A3（行为层三键 + 告警文案）双机断兜底；码面依据 `persistence.py:40` 空串≡缺省由 10 实读闭合。措辞、检出、拒收路径完整，再加固属冗余 |

---

## 阻塞清单

**零内容阻塞 · 零流程内容阻塞。**

- 未发现需「退回 10-task」的实质缺口：需求真值（验收登记 :46 第 2 行处置令）承接逐字属实；改动边界 / 默认空 / 范式对齐 / 语义不回读四契约钉死；A1–A5 全可机断且与 failure_paths 七条一一联锁；思考轮 R0–R3 + early_stop 回填闭合；锚点全部实读命中。
- 流程闸 HG-TASK-DRAFT / HG-AUDIT-R1 / HG-GRAPH-MODULES 均 pending 属实且**符合本轮时序**（20 审完 → 维护者签 → 30）· 非 task 内容缺陷。`spec-wave verify` EXIT=2 即此三闸未签所致。

---

## 非阻塞清单（nits · 不影响 PASS）

| # | 级别 | nit | 建议处置 |
|---|------|-----|---------|
| N1 | 事实性微差 | task L52 背景表称 api.environment 块「**19 个键**」；实数 = **16 键**（机数 · DATABASE_URL…QDRANT_COLLECTION） | 不阻塞（非契约/验收项 · 不影响执行）；维护者签闸时可顺手改 16，或留 40 注记 |
| N2 | 验收命令具体化 | A1② 对拍命令为伪码简写（见 Q1） | 30/40 可用如下具体形（`--project-directory` 固定防 project 名污染 · `jq -S` 键序归一）：`git show 57fbf84:docker-compose.yml > /tmp/master-compose.yml` → `docker compose -f /tmp/master-compose.yml --project-directory . config --format json \| jq -S '.services.api.environment' > /tmp/env_master.json` → 本分支同法出 `/tmp/env_branch.json` → `diff` 预期仅 `OPS_HITL_PERSISTENCE` 一键；compose 版本无 `--format json` 时退回 grep 断言（task 已兼容） |
| N3 | 交付提示 · A5 形态 | A5 对纯 config 改动为零变化断言（耦合面实证零） | 40 可裁为注记：「CI 绿 + tests/ 零 diff + grep 耦合零命中」即满足；不强制本地全量 pytest |

---

## 结论：R1 PASS-WITH-NITS（内容面终轮签收）

R1 书面审 **PASS-WITH-NITS**：免 SPEC 依据（验收偏差登记 :46 第 2 行处置令）承接逐字属实；范围 F1 一行透传钉死、非范围四条锁死；「空默认 / 零 diff / 语义不回读」契约三层钉死且码面依据（`persistence.py:40`）实读成立；A1–A5 全可机断、failure_paths 七条与验收一一联锁；思考轮 R0–R3 early_stop 回填闭合；K7 旧测影响面实证为零。**内容 12/12 通过 · 零内容阻塞**；三条非阻塞 nits（19→16 键计数 / A1② 命令具体化 / A5 可注记化）转 30/40 顺手处理，不影响签闸。本轮为内容面终轮，**签收**。

流程闸现状（属实时序）：HG-TASK-DRAFT / HG-AUDIT-R1 / HG-GRAPH-MODULES = **pending** → 30 **拒开工**；本帽不代签，须维护者签 HG-AUDIT-R1（并扫签 HG-TASK-DRAFT · 00 代录核验 HG-GRAPH-MODULES）后方可下发 30。

---

## 修订记录

| 日期 | 摘要 |
|------|------|
| 2026-10-09 | R1 审查落盘：真值源真读（验收登记 :46 第 2 行 · docker-compose.yml:51-70 · persistence.py:22/40/54-57/81-93 · router.py:74-79）+ 机跑 `task lint`(EXIT=0) / `spec-wave verify`(EXIT=2 · 三闸 pending) / merge-base=57fbf84 / tests·CI 耦合面 grep 零命中 / env 键实数 16 · 内容 12/12 通过 · 零阻塞 · nit 3 · 结论 PASS-WITH-NITS（内容面终轮签收） |

---

## 维护者签闸（20 后 · 30 前）

- [ ] 已读 R1 审查结论
- [ ] 在 task 人工闸表将 HG-AUDIT-R1 改为 approved（维护者 · 日期）
- [ ] commit task 文档或确认已签
- [ ] 再下发 Harness 30 Prompt

30 Agent 将以 task 表为准；pending 时必须拒开工（见 TEMPLATE_30_gate_stop.md）。
