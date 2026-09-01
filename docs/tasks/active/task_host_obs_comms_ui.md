# Task：Host C4 · /obs 沟通入口（api 契约 + web Prompt）

> **状态**：active  
> **类型**：契约 / 跨仓编排（**api 侧无码** · docs-only）  
> **上游**：[`06_host_comms_boundary_spec_v0.md`](../../spec/agent-infra/06_host_comms_boundary_spec_v0.md)（**signed** · #111）§9 · §10（C4 行）· §11（/obs 主入口建议钉 · 已随签收生效）  
> **前置**：C3 CLOSE · [`task_host_comms_task_writer`](../done/task_host_comms_task_writer.md) · [#118](https://github.com/Cyning12/ops-desk-api/pull/118)；web `/obs` 契约类型已在 `ops-desk-web/src/api/obs.ts`（对齐 kit obs_status.v1 / obs_timeline.v1 · 现 fixture 加载）  
> **分支**：`task/host-obs-comms-ui`  
> **帽子**：00 起草闸；**10** 补全；**20** 审；本波 **无 30**（api 无码）。  
> **无关**：C1–C3 返工 · web Vue 实现（另 task · 本仓出 Prompt）· 真 status 数据源实现（另议 · 本波只钉契约）· 改产品 lg-rag/Chat

---

## Harness 元信息

| 字段 | 值 |
|---|---|
| **task_slug** | `host-obs-comms-ui` |
| **git_branch** | `task/host-obs-comms-ui` |
| **implement_repo** | `ops-desk-api` |
| **test_strategy** | `n/a` |
| **test_strategy_note** | api 侧无码（契约 + Prompt）；验收=契约章节齐全 + 20 R1 pass + web Prompt 落盘 |
| **code_quality_bar** | `L2_backend` |
| **graph_change_layer** | `none` |
| **graph_delta** | `none` |
| **graph_delta_note** | 契约文档 · 不动图谱（真源实现波再同步） |
| **wiki_delta** | `n/a` |
| **review_hat** | `20` |
| **required_invoke_hats** | `10,00` |
| **invoke_retention_profile** | `default` |
| **freeze_id** | `n/a`（不改 lg-rag-sse-v1；obs 契约新立 `obs-comms-v0` 文档级 · 未实现不冻结行为） |
| **close_pr_policy** | `required` |
| **kpi_aggregator** | `CLOSE` |
| **orchestration** | C 轨末波：C1 ✓ → C2 ✓ → C3 ✓ → **C4**；web 实现另 task（本 Prompt 跨仓并行允许项） |

### 人工闸

| human_gate_id | status | blocks_hats | 说明 |
|---|---|---|---|
| HG-TASK-DRAFT | approved | 22-R1 | 2026-09-01 · **00 代签 · 维护者 Prompt 授权** |
| HG-AUDIT-R1 | n/a | 30 | 本波 **无 30**（api 无码）；20 R1 审 task/契约仍走 |
| HG-GRAPH-MODULES | n/a | — | 无图谱变更 |

---

## 00 定夺（草案 · 人可后签）

| 项 | 钉死 |
|---|---|
| **slug** | **`host-obs-comms-ui`** |
| **本波形态** | **api 无码**：契约文档 + web Prompt 落盘 `_prompts/`；web 实现另 task（跨仓） |
| **契约落点** | `docs/spec/agent-infra/host_comms_obs_contract_v0.md`（契约 id `obs-comms-v0`） |
| **status 契约** | 对齐 web `ObsStatus`/`ObsTimeline`（kit obs_status.v1 / obs_timeline.v1）；字段表 + 示例 JSON；**数据源决策点**写明两候选（A: api 端点读仓内 docs——须解决部署容器无 docs/ 问题；B: GHA sync 落库后 api 读表）· 本波不选定实现（另 task） |
| **发起沟通契约** | `/obs` 入口语义：显式发起 → 进 comms session（SPEC §4/§9）；**人确认**后 C3 writer 才落盘；任何「已代签」字样违规（§6） |
| **harness.status** | C1 留白项：真源实现波需要时补做（写进契约依赖注记） |
| **web Prompt** | `PROMPT_web_00_c4_obs_comms_ui.md`：fixture→契约真源切换点 · 发起沟通入口 UI · 浏览器禁跑 npx 红线沿用 |
| **模块** | 不新增一级模块 |

---

## 范围

1. 契约文档 `host_comms_obs_contract_v0.md`（status/timeline 字段表 · 示例 · 数据源决策点 · 发起沟通语义 · 依赖注记）  
2. web Prompt 落盘 `docs/harness/invokes/by-task/_prompts/PROMPT_web_00_c4_obs_comms_ui.md`  
3. 20-task-audit 审查文落盘  
4. `lint-wiki-delta` PASS

## 非范围

- web Vue 实现（另 task）· api 真源端点实现（另 task · 本波仅契约）  
- `harness.status` 实现（C1 留白 · 真源波补做）  
- 改 C1–C3 交付物 · 改产品 lg-rag/Chat  
- 浏览器侧任何 npx/CLI 能力（红线沿用）

---

## 验收标准

- [ ] 契约文档存在且章节齐全（字段表对齐 web ObsStatus/ObsTimeline · 示例 JSON · 数据源决策点 A/B · 发起沟通语义 · 依赖注记）  
- [ ] 契约与 web `src/api/obs.ts` 类型逐字段核对一致（不一致处写明偏离与理由）  
- [ ] web Prompt 落盘 `_prompts/PROMPT_web_00_c4_obs_comms_ui.md`（含红线：浏览器禁 npx · 人确认 · 分 session）  
- [ ] `docs/harness/reviews/` 落 20 R1 审查文且 **pass**  
- [ ] `app/` · `tests/` **零改动**（diff 为空）  
- [ ] `npx --yes dsh-coding-kit@1.10.0 task lint-wiki-delta --target .` 通过

---

## failure_paths

| 触发 | 行为 | 可重试 | 用户可见 |
|---|---|---|---|
| 部署容器无 docs/ | 契约决策点 A 标风险；真源波须解决（打包 docs 或选 B） | — | 契约条文 |
| web 抢先接真源 | 契约先于实现；web 侧未接前仍 fixture | — | Prompt 红线 |
| 沟通入口误判 | 显式发起才进 comms（SPEC §4）；默认 product | 是 | 契约条文 |

---

## 给执行帽的必读列表

1. 本 task（含 **00 定夺**）  
2. `docs/spec/agent-infra/06_host_comms_boundary_spec_v0.md` §4 · §6 · §9 · §10 · §11  
3. web 契约类型：`ops-desk-web/src/api/obs.ts`（只读跨仓参照）  
4. C1–C3 done 文件（能力面事实）

---

## 修订记录

| 日期 | 说明 |
|---|---|
| 2026-09-01 | **00**：C3 CLOSE（#118/#119）后起草 C4；钉 api 无码（契约+Prompt）；契约落点 `host_comms_obs_contract_v0.md`；status 对齐 web ObsStatus/kit obs_status.v1；数据源决策点 A/B 不选定；发起沟通=显式+人确认 |
