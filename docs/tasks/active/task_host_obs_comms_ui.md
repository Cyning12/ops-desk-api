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

### 自检结论

> **10-task** · 2026-09-01 · 分支 `task/host-obs-comms-ui` · docs-only 本帽（不改 `app/` / `tests/` · 不改 web 仓任何文件）· 人工闸状态未改（HG-TASK-DRAFT approved · HG-AUDIT-R1 n/a 保持不动）

**00 定夺核对**（逐项 · 结论：**全部命中 · 零修正**）

| 定夺项 | task 落点 | 结果 |
|---|---|---|
| api 无码（契约 + web Prompt 落 `_prompts/`） | L4/L8/L50 | ✅ |
| 契约落点 `host_comms_obs_contract_v0.md`（id `obs-comms-v0`） | L51 | ✅ 契约已起草落盘 |
| status 对齐 web `ObsStatus`/`ObsTimeline` · 数据源 A/B 不选定 | L52 | ✅ 契约 §2/§3 字段表 + §6 决策点（不选定） |
| 发起沟通=显式+人确认 · 「已代签」违规 | L53 | ✅ 契约 §7 |
| `harness.status` C1 留白依赖注记 | L54 | ✅ 契约 §8 |
| web Prompt `PROMPT_web_00_c4_obs_comms_ui.md` | L55 | ✅ 已落盘 `_prompts/` |
| 不新增一级模块 | L56 | ✅ `graph_change_layer=none` 一致 |

**契约 ↔ web 类型逐字段核对**（基准 `ops-desk-web/src/api/obs.ts` + 四份 fixture · 只读）：ObsStatus 14 字段（含 gates/reviews/hgm 等嵌套）+ ObsTimeline 9 字段（含 events 6 子字段）**逐字段一致**；**唯一偏离** = `ObsTimeline.ingest` web `unknown` → 契约收窄 `object|null`（理由：fixture 期占位宽类型收敛以便真源生成；TS `unknown` 为超集，web 零改动兼容）· 明细见契约 §4。示例 JSON ready/blocked 与 web fixture 同形。

**lint 与禁区**

- [x] `npx dsh-coding-kit@1.10.0 task lint --file docs/tasks/active/task_host_obs_comms_ui.md` → **PASS**（exit 0 · W4 合法：无思考轮节 · 思考轮由 SPEC 06 §15 承载，本 task 为 SPEC 落地执行波）
- [x] `npx --yes dsh-coding-kit@1.10.0 task lint-wiki-delta --target .` → **PASS**
- [x] `app/` · `tests/` 零改动；web 仓零改动（跨仓仅只读参照）；人工闸状态未改
- [x] invoke 落盘：`docs/harness/invokes/by-task/host-obs-comms-ui/invoke_20260901_10_task_host-obs-comms-ui.md`（hat_id=10-task）
- 下一棒：**20-task-audit** R1 审 task/契约 → 落盘审查文（本波无 30 · HG-AUDIT-R1 n/a）

---

## 修订记录

| 日期 | 说明 |
|---|---|
| 2026-09-01 | **00**：C3 CLOSE（#118/#119）后起草 C4；钉 api 无码（契约+Prompt）；契约落点 `host_comms_obs_contract_v0.md`；status 对齐 web ObsStatus/kit obs_status.v1；数据源决策点 A/B 不选定；发起沟通=显式+人确认 |
| 2026-09-01 | **10-task**：00 定夺逐项核对全命中零修正；起草契约 `docs/spec/agent-infra/host_comms_obs_contract_v0.md`（字段表逐字段对齐 web ObsStatus/ObsTimeline · 唯一偏离 `ingest` 收窄 `object\|null` · 示例 ready/blocked · 决策点 A/B 不选定 · 发起沟通语义 · 依赖注记）；web Prompt 落盘 `_prompts/PROMPT_web_00_c4_obs_comms_ui.md`（fixture→真源切换点 · 发起沟通入口 · 红线）；补 `### 自检结论`；invoke 落盘；app/tests/web 仓零改动 · 闸状态未动 · 下一棒 20-task-audit |
