# Task：Structured Output Gateway · P3（ensure / validate + 并存策略）

> **状态**：completed（P3 50 PASS · PR #58 MERGED · 已归档；2026-08-26）  
> **类型**：feature / agent-infra（Structured Output Gateway 收官波）  
> **上游 SPEC**：`docs/spec/agent-infra/SPEC-structured-output-gateway_v0.md` §3 / §4 P3  
> **前置**：P0–P2 50 PASS  
> **分支**：`task/structured-output-gateway`

---

## Harness 元信息

| 字段 | 值 |
|---|---|
| **task_slug** | `structured-output-gateway-p3` |
| **git_branch** | `task/structured-output-gateway` |
| **implement_repo** | `ops-desk-api` |
| **test_strategy** | `required` |
| **test_strategy_note** | 单测：ensure_keys 缺路径失败；custom validate 失败；no_retry 不注入 correction；不连真 LLM |
| **code_quality_bar** | `L2_backend` |
| **graph_change_layer** | `G-L1` |
| **graph_delta** | `docs/_tech_graph/l1/01_modules.md` 或 `none`（若仅文档+API 无模块备注必要则 `none` 并在 note 说明） |
| **graph_delta_note** | 可选一句；不新增一级模块 |
| **wiki_delta** | `n/a` |
| **review_hat** | `20` |
| **required_invoke_hats** | `10,30` |
| **invoke_retention_profile** | `default` |
| **freeze_id** | 无 |
| **orchestration** | 总轨收官 |

### 人工闸

| human_gate_id | status | blocks_hats | 说明 |
|---|---|---|---|
| HG-TASK-DRAFT | approved | 22-R1 | 2026-08-26 00 代签 |
| HG-AUDIT-R1 | approved | 30 | 2026-08-26 00 代签；`task_structured_output_gateway_p3_audit_R1_20260826.md` |
| HG-GRAPH-MODULES | approved | 30 | 不增一级模块 |

---

## 背景与目标

补齐管道可选步：`ensure_keys`、`custom validate`；落盘与 LangGraph `with_structured_output` **并存策略**文档（本仓自建 Gateway 为强制基础设施，非互斥替换一切调用）。

---

## 范围 / 非范围

**范围**：

- `parse_only` / `acomplete_structured` 接通 `ensure_keys` 与 `validate`（callable）；失败走 Host 权威路径；`no_retry` 可跳过 LLM correction
- 单测覆盖 ensure / validate / no_retry
- 文档：建议 `docs/guides/DESIGN_structured-output-gateway-coexistence_v0.md` 或写入 `docs/spec/agent-infra/` 短文 / SPEC 修订节——说明与 `with_structured_output` 并存（何时用 Gateway、何时可用原生、禁止模型自选跳过）
- SPEC 修订记录追加「P0–P3 落地状态」一行（00 可在关账时写，或本 task 30 写）

**非范围**：

- 新业务节点接入；Capability Gateway；改 chat/graph.py；Agently 依赖；升 freeze

---

## 验收标准

- [x] `ensure_keys`：缺必填路径 → 失败（parse_only 与/或 complete 路径至少一侧钉死）
- [x] custom `validate`：返回失败 reason → 失败；complete 路径预算内可重试（除非 no_retry）
- [x] `no_retry`：失败不把敏感规则写入 OUTPUT CORRECTION（单测断言 messages）
- [x] 并存策略文档落盘且可读
- [x] SPEC 修订记录含 P0–P3 落地状态（或明确由 00 关账回填）
- [x] pytest / ruff 绿；`chat/graph.py` 零 diff；无 Agently

---

## failure_paths

| 触发 | 行为 | 可重试 |
|---|---|---|
| ensure_keys 失败 | 失败 outcome；complete 可 correction（除非 no_retry） | 视标记 |
| custom validate 失败 | 同左 | 视标记 |
| no_retry | 直接 StructuredFailure / raise | N |
| 误改 chat graph / Capability | 打回 | N |

---

## 依赖

P0–P2 代码 · SPEC §3 管道步骤 4–5 · §4 P3

---

## 给执行帽（30）必读

本 task · SPEC · `complete.py` / `parse.py` · FRAGMENT_30 · CODING_BACKEND_L2

---

## 思考轮

### 思考轮控制

| 字段 | 值 |
|---|---|
| **actual_last_round** | R5 |
| **early_stop** | no |
| **residual_risks** | ensure_keys 路径表达（dot path vs list）须文档化；并存文档勿写成「禁用 with_structured_output」——SPEC 是并存 |

### R0
接通 ensure/validate 到现有 API。

### R1
no_retry 防泄漏。

### R2
文档讲并存非互斥消灭。

### R3
不新接业务节点。

### R4
单测 mock only。

### R5
SPEC 修订记录落地状态。

---

### 自检结论

> 2026-08-26 · 00 机械复检 · **PASS**（30 [Review](74bb29f3-bbe1-40ff-b210-624aba668db6)）

- [x] 验收勾选
- [x] pytest / ruff（全波触及 46 passed）
- [x] graph.py 零 diff

**50 结论**：PASS · 全波次 P0–P3 完成 · 待维护者授权 commit/PR

---

## CLOSE

| 项 | 内容 |
|---|---|
| 日期 | 2026-08-26 |
| 定稿 | ensure_keys / validate / no_retry + 并存策略文档 + SPEC 落地状态 |
| 归档 | `docs/tasks/done/task_structured_output_gateway_p3.md` |
| PR | [#58](https://github.com/Cyning12/ops-desk-api/pull/58) MERGED |

---

## 修订

| 日期 | 说明 |
|---|---|
| 2026-08-26 | 00 起草 P3 |
| 2026-08-26 | 20 R1 pass；00 代签闸 |
| 2026-08-26 | 30/40 PASS；00 50 PASS；CLOSE；全波次收官 |

| 2026-08-26 | 归档：PR #58 MERGED · git mv → docs/tasks/done/ |
