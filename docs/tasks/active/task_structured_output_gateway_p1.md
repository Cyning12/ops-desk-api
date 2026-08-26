# Task：Structured Output Gateway · P1（complete_structured + 预算重试）

> **状态**：completed（P1 50 PASS · 同分支待合入；2026-08-26）  
> **类型**：feature / agent-infra（Structured Output Gateway 第二波）  
> **上游 SPEC**：`docs/spec/agent-infra/SPEC-structured-output-gateway_v0.md`（active · `HG-SPEC-SIGNOFF=approved`）  
> **前置**：`structured-output-gateway-p0`（50 PASS · 同分支）  
> **总轨**：`structured-output-gateway`  
> **分支**：`task/structured-output-gateway`  
> **无关**：勿与其他 active task 混改；禁止 Capability Gateway；禁止改 `chat/graph.py`。

---

## Harness 元信息

| 字段 | 值 |
|---|---|
| **task_slug** | `structured-output-gateway-p1` |
| **git_branch** | `task/structured-output-gateway` |
| **implement_repo** | `ops-desk-api` |
| **test_strategy** | `required` |
| **test_strategy_note** | mock LLM provider：第 1 次坏 JSON/schema、第 2 次好；断言 correction 出现在第 2 次 messages；预算耗尽失败；不连真 LLM/真库 |
| **code_quality_bar** | `L2_backend` |
| **graph_change_layer** | `G-L1` |
| **graph_delta** | `docs/_tech_graph/l1/01_modules.md` |
| **graph_delta_note** | `lg_rag` 备注可补一句 complete_structured；**不**新增一级模块（若仅实现无备注必要可说明 n/a 但须仍过 compile 若触及） |
| **wiki_delta** | `n/a` |
| **wiki_delta_note** | 无业务 HTTP / Wiki 面变更 |
| **review_hat** | `20` |
| **required_invoke_hats** | `10,30` |
| **invoke_retention_profile** | `default` |
| **freeze_id** | 无 |
| **orchestration** | 总轨四子 task：本 task = P1 |

### 人工闸

| human_gate_id | status | blocks_hats | 说明 |
|---|---|---|---|
| HG-TASK-DRAFT | approved | 22-R1 | 2026-08-26 00 代签（20 R1 pass · 维护者授权过程闸） |
| HG-AUDIT-R1 | approved | 30 | 2026-08-26 00 代签；`docs/harness/reviews/task_structured_output_gateway_p1_audit_R1_20260826.md` |
| HG-GRAPH-MODULES | approved | 30 | 不新增一级模块；沿用惯例 |

---

## 背景与目标

P0 已交付无 LLM 的 `parse_only`。P1 补齐 SPEC §3.1 `complete_structured`：触发 LLM → parse 管道 → 失败则预算内注入 `OUTPUT CORRECTION` 风格反馈再请求。

**完成态**：可 mock 的 `complete_structured`；默认 `max_retries=3`；Host 权威；单测钉死 correction 注入与预算耗尽。

---

## 范围 / 非范围

**范围**：

- 在 `app/ops/structured_output/` 实现 `complete_structured(...)`（概念 API；可异步 `acomplete_structured` 若仓内 provider 为 async）
- 参数至少覆盖 SPEC：messages 或 (system, user)、schema、`max_retries`、`raise_on_failure`、可选 `llm_ctx`（provider/model 覆盖）
- 校验失败 → 注入 OUTPUT CORRECTION（字段级 reason 截断）→ 再请求 → 再走 parse_only 管道
- `StructuredFailure`（或等价）在 `raise_on_failure=False` 时返回；为 True 时 raise
- 敏感规则钩子预留：`no_retry` 标记可在失败时直接失败（P1 可最小实现；完整 ensure/custom 属 P3）
- 单测 mock provider（计数 + 捕获 messages）
- 若改 G-L1 备注：一句即可 + graph-compile

**非范围**：

- 接入 supervisor / router / info_extract（→ P2）
- `ensure_keys` / 完整 custom validate / 并存策略文档（→ P3；P1 仅可预留参数签名为 Optional 未实现则文档注明）
- Capability Gateway
- 改 `app/ops/chat/graph.py`
- Agently 依赖
- 半截「只改坏字段」补丁式 LLM repair（SPEC：完整重生成）

---

## 验收标准

- [x] 可 import 的 `complete_structured`（或 `acomplete_structured`）公开 API
- [x] mock：第 1 次坏、第 2 次好 → 返回成功 schema 实例；provider 被调用 2 次
- [x] 第 2 次 messages（或 user 追加）含 OUTPUT CORRECTION（或 task/实现注明的等价标记串）与截断后的校验 reason
- [x] 预算耗尽（连续失败 ≥ max_retries+1 次尝试语义与实现注释一致）→ raise 或 StructuredFailure；**不得**返回成功业务数据
- [x] Host 权威：schema 失败路径不得 `ok` 成功 data
- [x] 单测不连真 LLM/真库；触及 pytest 绿
- [x] ruff 触及路径绿
- [x] `app/ops/chat/graph.py` 零 diff
- [x] 无 Agently 依赖；未改无关 active task
- [x] 未接入 P2 业务节点（supervisor/router/info_extract 无本 task 业务改写，除 import 无关）

---

## failure_paths

| 触发 | 行为 | 可重试 | 用户可见 |
|---|---|---|---|
| 无法抽出 JSON | 计入 attempt；预算内 LLM 纠偏 | Y | 调用方 |
| Schema 不匹配 | correction 反馈后重试 | Y | 调用方 |
| 预算耗尽 | raise 或 StructuredFailure | N | 调用方 |
| LLM 传输异常 | 上抛或按调用方/llm_ctx | Y（上层） | 调用方 |
| `no_retry` 标记失败 | 直接失败，不把隐藏规则写入 correction | N | 调用方 |
| 误改 chat graph / Capability / Agently | 验收打回 | N | 开发 |

---

## 依赖

- P0 包：`app/ops/structured_output/`（`parse_only`）
- SPEC §3.1 / §3.2 / §4 P1 / §6
- `app/llm/factory.py` · provider `complete`
- `CODING_BACKEND_L2_v1_zh.md`
- `FRAGMENT_30_gate_verify_v1_zh.md`

---

## 给执行帽（30）必读

1. 本 task + SPEC §3–§4 P1 + §6
2. P0 实现：`parse.py` / `__init__.py`
3. `get_llm_provider` 用法（`lg_rag/nodes.py` 对照）
4. FRAGMENT_30 + CODING_BACKEND_L2
5. 硬约束同总轨 Prompt

---

## 思考轮

### 思考轮控制

| 字段 | 值 |
|---|---|
| **actual_last_round** | R5 |
| **early_stop** | no |
| **residual_risks** | correction 文案过长泄漏；用截断。mock 与真 provider 签名差导致接入 P2 时需适配。`max_retries` 语义（重试次数 vs 总尝试次数）须在实现注释与单测钉死。 |

### R0
P1 只加 LLM 预算管道；不接业务节点。

### R1
复用 P0 `parse_only`；禁止复制一套 parse。

### R2
OUTPUT CORRECTION 注入对齐 Agently 思想；本仓自建文案即可。

### R3
`raise_on_failure` 双模式；失败不得成功 data。

### R4
`llm_ctx` 可覆盖 provider/model；默认走 `get_llm_provider`。

### R5
单测 mock 计数；不连网。

---

### 自检结论

> 2026-08-26 · 00 机械复检 · **PASS**（30 [Review](9e193a26-c0d5-4df5-bee1-da698482b77d)）

- [x] 验收标准全部勾选
- [x] ruff / pytest（27 passed：complete+parse_only+multi）绿
- [x] `chat/graph.py` 零 diff
- [x] verify PASS

**50 结论**：PASS · 下一棒 P2

---

## CLOSE

| 项 | 内容 |
|---|---|
| 日期 | 2026-08-26 |
| 定稿 | `acomplete_structured` + OUTPUT CORRECTION + StructuredFailure |
| 归档 | 暂留 active（同分支全波次后归档） |
| PR | 待全波次 · 维护者授权 |

---

## 修订

| 日期 | 说明 |
|---|---|
| 2026-08-26 | 00 起草 P1；闸 pending |
| 2026-08-26 | 20 R1 pass；00 代签 HG-TASK-DRAFT + HG-AUDIT-R1 |
| 2026-08-26 | 30/40 PASS；00 50 PASS；CLOSE |
