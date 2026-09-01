# Task：Host C0 · 沟通边界 SPEC（comms vs product）

> **状态**：active  
> **类型**：Spec / 边界签收（**docs-only** · 无 30）  
> **上游**：[`2026-08-31_host_comms_agent_kit_nesting_plan_draft.md`](../../discussions/2026-08-31_host_comms_agent_kit_nesting_plan_draft.md)（随本 PR 合入 master）· [`02_agent_host_plan_v0.md`](../../spec/agent-infra/02_agent_host_plan_v0.md)（H1–H5 已 CLOSE · C 轨是沟通嵌套 kit · **不是**重开 H1–H5）  
> **前置**：T6 CLOSE · [`task_lg_rag_deprecate_chat_stream`](../done/task_lg_rag_deprecate_chat_stream.md) · [#108](https://github.com/Cyning12/ops-desk-api/pull/108)；草稿「暂缓 C0」前提（chat→lg-rag 迁移联调）已达成（T6 #108 · web T5 CLOSE #109）；维护者 Prompt 授权开 C 轨（串行波次 3）  
> **分支**：`task/host-comms-boundary-spec`  
> **帽子**：00 起草闸；**10-spec** 起草 SPEC；**20-spec-audit** 审；本波 **无 30**。  
> **无关**：C1–C4 实现 · 改 05 freeze 字段 · 改产品 Chat/lg-rag · web `/obs` 实现（C4 另议）· 重开 H1–H5

---

## Harness 元信息

| 字段 | 值 |
|---|---|
| **task_slug** | `host-comms-boundary-spec` |
| **git_branch** | `task/host-comms-boundary-spec` |
| **implement_repo** | `ops-desk-api` |
| **test_strategy** | `n/a` |
| **test_strategy_note** | docs-only SPEC 波；无代码改动；验收=SPEC 章节齐全 + 20-spec-audit pass + HG-SPEC-SIGNOFF |
| **code_quality_bar** | `L2_backend` |
| **graph_change_layer** | `none` |
| **graph_delta** | `none` |
| **graph_delta_note** | docs-only SPEC；不动图谱（C1 实现波再同步） |
| **wiki_delta** | `n/a` |
| **wiki_delta_note** | SPEC 落 `docs/spec/agent-infra/06_*`；不晋升 coding_wiki |
| **review_hat** | `20` |
| **required_invoke_hats** | `10,00` |
| **invoke_retention_profile** | `default` |
| **close_pr_policy** | `required` |
| **kpi_aggregator** | `CLOSE` |
| **orchestration** | C0 仅 SPEC 签收；C1–C4 后续串行（C4 可与 C3 尾并行 · 仅 web 侧） |

### 人工闸

| human_gate_id | status | blocks_hats | 说明 |
|---|---|---|---|
| HG-TASK-DRAFT | approved | — | 2026-09-01 · **00 代签 · 维护者 Prompt 授权** |
| HG-SPEC-SIGNOFF | pending | — | 待 **20-spec-audit** 落盘后 00 代签（docs-only SPEC 波代签授权：内容零阻塞 + 审查落盘） |
| HG-AUDIT-R1 | n/a | 30 | 本波 **无 30**（docs-only） |
| HG-GRAPH-MODULES | n/a | — | 无图谱变更 |

---

## 00 定夺（草案 · 人可后签）

| 项 | 钉死 |
|---|---|
| **slug** | **`host-comms-boundary-spec`** |
| **SPEC 落点** | `docs/spec/agent-infra/06_host_comms_boundary_spec_v0.md`（接 02/05 编号序列） |
| **上游草稿** | discussions `2026-08-31_host_comms_agent_kit_nesting_plan_draft.md` 随本 PR 合入 master（自 `docs/hat-identity-feedback-host-plan` 分支取出）；SPEC 以其为素材、**真值以 SPEC 为准** |
| **意图路由** | 默认 **product**；显式「立项 / 开 task / 写 SPEC」类意图 → **comms** Pack；误判回退 product（SPEC 写清判定与回退） |
| **产物路径** | comms 写盘 **仅** `docs/tasks/`（active/draft）+ invoke 草稿；**禁写 `app/`**（C3 受控写盘的边界在 C0 SPEC 钉死） |
| **禁代签** | Host 沟通 Agent **永不**签发 human_gate；闸真值仍在 task 表。与「00 过程代签（维护者 Prompt 授权）」区分写明：后者是人工授权流程，不是模型自签 |
| **Capability** | 白名单 **仅 `harness.*`**（verify / task_lint / status）；**禁止**通用 shell Capability；Policy **默认关**；kit 版本 env 钉 `DSH_CODING_KIT_VERSION`（C1 落地） |
| **Skills≠verify** | SPEC 明文：Skill 短提示 ≠ 机械闸；C1 CLI Capability **必做**，不得以 Skill 替代 |
| **分 session** | comms 与 product **分 thread/session**；共用 CapabilityGateway，**不共用** system prompt |
| **C1–C4 波次表** | SPEC 收录建议 slug/形态/依赖（C1 capability → C2 prompt pack → C3 task writer → C4 obs UI）；顺序钉死 C1→C2→C3 |
| **待拍板（草稿 §8.2/8.3）** | SPEC 给建议钉：写盘落点=**api 仓 `docs/tasks/`**；`/obs` 作 comms UI 主入口（C4 跨仓）。随 HG-SPEC-SIGNOFF 一并签收；维护者异议走 SPEC 修订 |

---

## 范围

1. SPEC `06_host_comms_boundary_spec_v0.md`：背景 / 范围 / 非范围 / 意图路由 / 产物路径 / 闸纪律 / C1–C4 波次表 / 风险 / failure_paths / 验收  
2. discussions 草稿合入 master（本 PR 携带）  
3. 20-spec-audit 审查文落盘 + HG-SPEC-SIGNOFF 签收  
4. `lint-wiki-delta` PASS

## 非范围

- C1–C4 **任何实现码**（Capability / PromptAssembly / 写盘 / UI）  
- 改 `05` freeze 契约字段（本波无 freeze 变更）  
- 改产品 Chat / lg-rag 行为 · 重开 H1–H5  
- web `/obs` 实现（C4 另 task · 跨仓）  
- 通用 shell Capability（永久禁令 · SPEC 明文）  

---

## 验收标准

- [ ] SPEC `06_host_comms_boundary_spec_v0.md` 存在且章节齐全（背景/范围/非范围/意图路由/产物路径/闸纪律/C1–C4 波次表/风险/failure_paths/验收）  
- [ ] SPEC 明文含 00 定夺全部钉死项（意图路由 · 产物路径 · 禁代签 · 白名单仅 harness.* · Skills≠verify · 分 session · 待拍板建议钉）  
- [ ] discussions 草稿 `2026-08-31_host_comms_agent_kit_nesting_plan_draft.md` 在 master（本 PR 携带）  
- [ ] `docs/harness/reviews/` 落 20-spec-audit 审查文且结论 **pass**  
- [ ] HG-SPEC-SIGNOFF=approved（00 代签 · 维护者 Prompt 授权 · 审查落盘后）  
- [ ] `npx --yes dsh-coding-kit@1.10.0 task lint-wiki-delta --target .` 通过  
- [ ] `app/` · `tests/` **零改动**（diff 为空）

---

## failure_paths

| 触发 | 行为 | 可重试 | 用户可见 |
|---|---|---|---|
| 模型代签 human_gate | SPEC 禁令 + C3 写盘前人确认；闸真值在 task 表 | — | SPEC 条文 |
| 范围蔓延到实现 | 非范围钉死 C1–C4 无码；PR diff 验收 `app/` 零改动 | — | PR 检查 |
| 上游草稿漂移 | 真值以 master 版 SPEC 为准；草稿仅素材 | — | — |
| 意图误判 comms/product | 回退 product；SPEC 写明判定与回退 | 是 | 后续 C2 联调 |

---

## 给执行帽的必读列表

1. 本 task（含 **00 定夺**）  
2. `docs/discussions/2026-08-31_host_comms_agent_kit_nesting_plan_draft.md`（本分支已带入）  
3. `docs/spec/agent-infra/02_agent_host_plan_v0.md`（H1–H5 边界 · 勿重开）  
4. `docs/spec/agent-infra/00_architecture_and_boundaries.md`（SPEC 风格参照）  

---

---

### 自检结论

> **10-spec** · 2026-09-01 · 分支 `task/host-comms-boundary-spec` · docs-only · 无 30 · HG-SPEC-SIGNOFF 保持 **pending**（本帽不签发）

**SPEC 章节清单核对**（`docs/spec/agent-infra/06_host_comms_boundary_spec_v0.md`）

- [x] §1 背景（H1–H5 CLOSE · 草稿「暂缓 C0」前提已达成：T6 #108 · web T5 #109）
- [x] §2 范围 · §3 非范围（含 **永久禁令 A 通用 shell Capability · B 模型代签 human_gate**）
- [x] §4 意图路由（默认 product · 显式进 comms · 误判回退 product）
- [x] §5 产物路径 · §6 闸纪律（禁代签 · 闸真值在 task 表 · 与 00 过程代签区分）
- [x] §7 Capability 白名单（`harness.verify`/`task_lint`/`status` · Policy 默认关 · env 钉 `DSH_CODING_KIT_VERSION`）
- [x] §8 Skills≠verify 明文 · §9 session 隔离（分 thread · 共用 Gateway · 不共用 system）
- [x] §10 C1–C4 波次表（slug/形态/依赖 · 顺序钉死 C1→C2→C3 · C4 可与 C3 尾并行仅 web）
- [x] §11 待拍板建议钉（写盘=api 仓 `docs/tasks/` · `/obs` 作 comms UI 主入口 · 随 HG-SPEC-SIGNOFF 签收）
- [x] §12 风险表 · §13 failure_paths · §14 验收 · §15 思考轮 R0–R5（early_stop=no + residual_risks）
- [x] §16 freeze 声明（不改 `lg-rag-sse-v1` 任何字段 · 05 不回写）· §17 修订记录

**00 定夺落 SPEC 逐项核对**

| 00 定夺项 | SPEC 落点 | 结果 |
|---|---|---|
| slug=`host-comms-boundary-spec` | 头部 + Harness 元信息 | ✅ |
| SPEC 落点 06（接 02/05 序列） | 文件 `06_host_comms_boundary_spec_v0.md` | ✅ |
| 草稿为素材 · 真值以 SPEC 为准 | §1 · §12 风险表 | ✅ |
| 意图路由默认 product · 显式进 comms · 回退 product | §4 | ✅ |
| 产物路径仅 `docs/tasks/` + invoke 草稿 · 禁写 `app/` | §5 | ✅ |
| 禁代签 · 闸真值在 task 表 · 与 00 过程代签区分 | §3 禁令 B · §6 | ✅ |
| 白名单仅 `harness.*` · Policy 默认关 · env 钉 `DSH_CODING_KIT_VERSION` | §7（§3 禁令 A 禁通用 shell） | ✅ |
| Skills≠verify · C1 CLI Capability 必做 | §8 | ✅ |
| comms/product 分 session · 共用 Gateway 不共用 system | §9 | ✅ |
| C1–C4 波次表 · 顺序 C1→C2→C3 · C4 并行仅 web | §10 | ✅ |
| 待拍板建议钉（写盘=api 仓 docs/tasks · `/obs` 主入口） | §11 | ✅ |

**lint 与禁区**

- [x] `npx dsh-coding-kit@1.10.0 task lint --file docs/tasks/active/task_host_comms_boundary_spec.md` → **PASS**（exit 0 · W4：无思考轮节 · 由 SPEC §15 承载合法）
- [x] `npx --yes dsh-coding-kit@1.10.0 task lint-wiki-delta --target .` → **PASS**（scope=all · scanned=99 · issues=0）
- [x] `app/` · `tests/` 零改动；05/02/00 SPEC 正文未动；`lg-rag-sse-v1` 字段零改；人工闸状态未改（HG-SPEC-SIGNOFF 仍 pending）
- [x] invoke 落盘：`docs/harness/invokes/by-task/host-comms-boundary-spec/invoke_20260901_10_spec_host-comms-boundary-spec.md`（hat_id=10-spec）
- 下一棒：**20-spec-audit** → 00 代签 HG-SPEC-SIGNOFF → 00 起草 C1 task

## 修订记录

| 日期 | 说明 |
|---|---|
| 2026-09-01 | **00**：T6 CLOSE（#108/#110）后起草 C0；钉 slug=`host-comms-boundary-spec`；SPEC 落点=06；docs-only 无 30；草稿「暂缓 C0」前提已达成（T6 + web T5 CLOSE）· 维护者 Prompt 授权开 C 轨 |
| 2026-09-01 | **10-spec**：SPEC 06 初稿落盘（draft · 章节齐全 · R0–R5 回填 · 00 定夺逐项落入 · 永久禁令 A/B · freeze 声明 05 不回写）；补 `### 自检结论`；invoke 落盘；HG-SPEC-SIGNOFF 保持 pending · 下一棒 20-spec-audit |
