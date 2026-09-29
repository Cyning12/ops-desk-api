# Task：D2 委派令牌闸 · 本地观察准备（RUNBOOK + compose env 配置面）（host-v1-delegation-token-observe）

> **状态**：`active`（2026-09-24 · 10 立稿 · 三闸 00 代录 approved · 配置面+docs · 零 app/ 码改）  
> **类型**：**config+docs**（部署配置透传 + 灰度 runbook · 零 `app/` 改动 · `graph_change_layer=none`）  
> **依据**：`docs/spec/host-v1-wrap-up/SPEC-host-v1-wrap-up_v0.md`（signed）§2 D2——「本 SPEC 只立框架与第一闸（委派令牌）task 化准备」  
> **维护者令（原话留痕）**：「仓内改动也可以吧，LG_RAG_DELEGATION_TOKEN_SECRET本地如何生成？落盘一份完成的本地checklist」（2026-09-24 · D2 推进窗口）· 承「签收，生成00 Prompt，在新窗口开始D1统筹」（2026-09-24）与 2026-09-23 长程令  
> **分支**：`task/host-v1-delegation-token-observe`（自 master · git worktree 隔离 · 禁 master 直改）  
> **10 注**：2026-09-24 · 00 亲起（SPEC §2 D2 已 sanction 第一闸 task 化准备 · Q2 裁定逐闸独立）

---

## Harness 元信息

| 字段 | 值 |
|------|-----|
| **task_slug** | `host-v1-delegation-token-observe` |
| **git_branch** | `task/host-v1-delegation-token-observe` |
| **implement_repo** | `ops-desk-api` |
| **test_strategy** | `docs-only` |
| **test_strategy_note** | 验收=文件落盘+配置渲染断言：`git diff master --stat -- app/` 为空 · compose 透传默认值=off（`delegation_mode()` 缺省 off · `app/ops/capability/delegation.py:97-102` 锚点）· `npx spec-wave verify --task` PASS；`docker compose config` 渲染含三键（本地执行记录留痕 · CI 无 docker 不机跑） |
| **code_quality_bar** | `L2_backend`（无码面 · compose/env 配置面） |
| **graph_change_layer** | `none` |
| **graph_delta** | `none` |
| **graph_delta_note** | 配置面+文档面 · 零新模块/路由/表/SSE 事件（开闸=env · V1-A 代码已在仓） |
| **wiki_delta** | `n/a` |
| **wiki_delta_note** | runbook 属 guides 面 · 不触 standards/wiki 真值 |
| **review_hat** | `20` |
| **required_invoke_hats** | `10,40` |
| **invoke_retention_profile** | `default` |
| **experience_capture** | `optional` |
| **kpi_aggregator** | `CLOSE` |
| **orchestration** | 10 → 00 代录闸 → 20-task-audit R1 → 00 执行（docs+compose 配置面 · 无 30 码面）→ PR + CI 绿 + merge → 40/CLOSE；**观察期执行与首份报告=下一棒**（维护者本地按 RUNBOOK 跑 → 报告落盘 `reports/gate_observe/` 另行登记） |
| **freeze_id** | 无 |

### 人工闸

| human_gate_id | status | blocks_hats | 说明 |
|---------------|--------|-------------|------|
| HG-TASK-DRAFT | **approved** | 20-R1, 30 | 2026-09-24 · **00 代录**（维护者令原话：「仓内改动也可以吧，LG_RAG_DELEGATION_TOKEN_SECRET本地如何生成？落盘一份完成的本地checklist」+ 承「签收，生成00 Prompt，在新窗口开始D1统筹」2026-09-24 与 2026-09-23 长程令） |
| HG-AUDIT-R1 | **approved** | **30** | 2026-09-24 · **00 代录**（同令 · 配置面+docs 承 task_agent_host_framework_alignment 先例 · 零 app/ diff 验收断言钉死 · 20-task-audit R1 书面审随交付） |
| HG-GRAPH-MODULES | **approved** | **30** | 2026-09-24 · 00 代录 · `graph_change_layer=none`（V1-A 图谱行 105 已签录 · 本棒零图谱义务） |
| HG-PILOT-OPSDESK-GLAYER | n/a | — | 不涉 |

---

## 背景与目标

SPEC §2 D2 六闸灰度框架第一闸=委派令牌（`LG_RAG_DELEGATION_TOKEN_MODE`）。V1-A 码面已在仓（gateway.py:287-323 三档闸 · delegation.py 签发/验签/台账）；开闸=纯 env 配置面。本地 compose 的 api 服务是显式 environment 白名单（无 `env_file:`）——三键不透传则 `.env` 写了也进不了容器。

一句话：落盘**完整本地观察 checklist**（RUNBOOK）+ compose 三键 env 透传（默认 `off` 零 diff）+ `.env.example` 注释键，使维护者本地一条命令即可开启 observe 并产出首份 `reports/gate_observe/` 报告。

---

## 范围（钉死）

| # | 件 | 修改对象 | 动作 |
|---|---|---|---|
| D1 | RUNBOOK 本地 checklist | 新文件 `docs/guides/RUNBOOK_delegation_token_observe_local_v1_zh.md` | 完整流程：前置 → SECRET 生成 → env 注入 → 起栈冒烟（台账行可见断言）→ 观察期（真实流量+合成演练场景）→ 日志捞取聚合 → 报告落盘（SPEC §2 D2 钉死格式）→ 结论/enforce 前置 → 复位 → 故障排查 |
| D2 | compose env 透传 | `docker-compose.yml` api 服务 environment | 追加三键：`LG_RAG_DELEGATION_TOKEN_MODE`（默认 `off`）· `LG_RAG_DELEGATION_TOKEN_SECRET`（默认空）· `LG_RAG_DELEGATION_TOKEN_TTL_SECONDS`（默认 600）· 注释指 RUNBOOK |
| D3 | env 示例键 | `.env.example` | LG_RAG 区块追加三键注释样例（承 `# LG_RAG_HTTP_CHECKPOINTER` 同款注释体 · 含 SECRET 生成命令与禁入库纪律） |
| D4 | 报告模板 | 新文件 `reports/gate_observe/_TEMPLATE_delegation_token.yaml` | SPEC §2 D2 钉死字段族模板（gate/mode/period/would_block 计数与分类/误判抽样≤10/结论建议/recorded_at） |

## 非范围（钉死 · 越任一条即停）

- ❌ 任何 `app/` 改动（V1-A 码面已在仓 · 本棒零码改）
- ❌ 开闸执行本身（observe 开启与观察期跑批=维护者本地按 RUNBOOK 执行 · 非本 PR 交付）
- ❌ 首份观察报告产出（下一棒 · 报告落盘 `reports/gate_observe/delegation_token_<period>.yaml` 另行登记）
- ❌ 其余五闸推进（Q2 裁定逐闸独立 · 待委派令牌观察报告产出后按同模板逐闸）
- ❌ enforce 开启（前置=零误判观察报告 + SECRET 已配 · SPEC 锁死）
- ❌ Langfuse 本地引入（单通道如实标注 · 重型自托管不进本棒）

---

## failure_paths

| 触发 | 行为 | 可重试 | 可见 |
|------|------|--------|------|
| compose 透传默认值非 off（误把 observe 当默认） | **拒收**（默认关铁律 · `delegation_mode()` 缺省 off 锚点断言） | 是 | 是 |
| SECRET 写入仓内任何文件（.env.example/compose/RUNBOOK 出现真实密钥值） | **拒收**（密钥纪律：只写生成命令 · 值禁入库） | 是 | 是 |
| diff 出现 `app/` | **拒收** | 是 | 是 |
| RUNBOOK 步骤缺「台账行可见」冒烟断言 | 退回补列（无冒烟=开没开闸无法证） | 是 | 是 |

---

## 验收标准

- [ ] D1：RUNBOOK 落盘 · 含 SECRET 生成命令（openssl/python 双法）· 冒烟断言节（`docker compose logs` 见 `delegation token_` 行）· 报告模板节 · 复位节
- [ ] D2：compose api environment 含三键透传且默认值=`off`/空/600 · 注释指 RUNBOOK
- [ ] D3：`.env.example` LG_RAG 区块含三键注释样例（无真实密钥值）
- [ ] D4：`reports/gate_observe/_TEMPLATE_delegation_token.yaml` 字段族与 SPEC §2 D2 钉死格式一致
- [ ] `git diff master --stat -- app/` 为空 · 仓内全文件 grep 无真实 SECRET 值
- [ ] `npx spec-wave verify --task` PASS · PR 经 CI 绿后 merge

---

## 依赖

- SPEC：`docs/spec/host-v1-wrap-up/SPEC-host-v1-wrap-up_v0.md` §2 D2（六闸矩阵 · 报告格式钉死）
- 码面真值：`app/ops/capability/gateway.py:287-323`（三档闸）· `app/ops/capability/delegation.py:97-149`（mode/env/台账）
- V1-A SPEC：`docs/spec/host-v1-delegation-token/SPEC-host-v1-delegation-token_v0.md`（灰度条款真值）

---

## 给执行帽必读

1. 本 task · SPEC §2 D2 · RUNBOOK 成稿
2. `app/ops/capability/gateway.py:287-323` · `app/ops/capability/delegation.py:41-102`
3. `docker-compose.yml` api environment 块（:51-70 白名单形态 · 含本棒新增三键）

---

## 思考轮控制

| 轮 | 结论 | early_stop | reason（early_stop） | residual_risks |
|----|------|------------|----------------------|----------------|
| R0 | D2 第一闸 task 化准备已被 signed SPEC sanction · 维护者令明确（仓内改动可 · 要 checklist） | no | — | 无 |
| R1 | 三闸 00 代录 approved · 配置面+docs 无 30 码面 · graph=none | no | — | 无 |
| R2 | 形态唯一：RUNBOOK+compose 透传+env 样例+报告模板四件 · 单 PR | no | — | 无 |
| R3 | failure_paths 四条（默认非 off 拒收/密钥入库拒收/app 混入拒收/缺冒烟断言退回） | no | — | 无 |
| R4 | 验收六条全可对文件/diff/grep/命令断言 | no | — | 无 |
| R5 | 可执行：00 亲做（无 30 面）· 观察期执行明确归下一棒 | yes | 配置面+docs 微修 · SPEC D2 已钉死框架与报告格式 | 观察期样本覆盖面（纯 RAG 能力集窄）→ RUNBOOK 内如实写覆盖面声明与合成演练补法 |

**actual_last_round**：R5 · **early_stop**：yes · **residual_risks**：见 R5

### R0 · 问题框定

本地 compose 是 env 白名单 → 三键不透传开不了闸；维护者要完整 checklist。SPEC D2 报告格式已钉死，备模板即可。

### R1 · 开工闸

三闸 approved（00 代录 · 维护者令原话留痕）· 配置面+docs · 零 app/。

### R2 · 竖切

四件单 PR：RUNBOOK（主交付）+ compose 三键（默认 off）+ .env.example 注释 + 报告模板。

### R3 · 失败语义

见 failure_paths：最锋利边界=默认关铁律与密钥禁入库。

### R4 · 可测性

验收=文件存在+diff 白名单+grep 无密钥+verify PASS。

### R5 · 交付判定

00 亲执行 → PR CI 绿 merge → CLOSE；观察期执行与首份报告归下一棒（维护者本地跑 → 报告落盘另行登记）。

### 自检结论

本稿：范围四件钉死 · 非范围锁死零 app/ 零执行 · 验收六条可机断 · failure_paths 四条 · 闸表三行 approved（00 代录）· 思考轮 R0–R5 齐全 · early_stop 于 R5 正当。可执行。

---

## 修订记录

| 日期 | 摘要 |
|------|------|
| 2026-09-24 | 10 立稿：D2 第一闸本地观察准备四件（RUNBOOK/compose 透传/env 样例/报告模板）· 三闸 00 代录 approved（维护者令原话留痕见头部） |