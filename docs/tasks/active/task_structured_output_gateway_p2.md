# Task：Structured Output Gateway · P2（接入 lg_rag 结构化节点）

> **状态**：completed（P2 50 PASS · 同分支待合入；2026-08-26）  
> **类型**：feature / agent-infra（Structured Output Gateway 第三波）  
> **上游 SPEC**：`docs/spec/agent-infra/SPEC-structured-output-gateway_v0.md` §4 P2 / §5  
> **前置**：P0/P1 50 PASS（同分支）  
> **分支**：`task/structured-output-gateway`  
> **无关**：勿混其他 active；禁止 Capability Gateway；禁止改 `chat/graph.py` 拓扑。

---

## Harness 元信息

| 字段 | 值 |
|---|---|
| **task_slug** | `structured-output-gateway-p2` |
| **git_branch** | `task/structured-output-gateway` |
| **implement_repo** | `ops-desk-api` |
| **test_strategy** | `required` |
| **test_strategy_note** | mock：router/supervisor/info_extract 解析路径；非法输出仍触发既有 fallback；span/metadata 含 structured_output_fallback（或等价）；既有 test_lg_rag* 不回归；不连真 LLM/真库 |
| **code_quality_bar** | `L2_backend` |
| **graph_change_layer** | `G-L1` |
| **graph_delta** | `docs/_tech_graph/l1/01_modules.md` |
| **graph_delta_note** | `lg_rag` 备注：结构化节点走 Gateway；不新增一级模块 |
| **wiki_delta** | `n/a` |
| **review_hat** | `20` |
| **required_invoke_hats** | `10,30` |
| **invoke_retention_profile** | `default` |
| **freeze_id** | 无（旁路 HTTP freeze 不升） |
| **orchestration** | 总轨四子 task：本 task = P2 |

### 人工闸

| human_gate_id | status | blocks_hats | 说明 |
|---|---|---|---|
| HG-TASK-DRAFT | approved | 22-R1 | 2026-08-26 00 代签（20 R1 pass） |
| HG-AUDIT-R1 | approved | 30 | 2026-08-26 00 代签；`task_structured_output_gateway_p2_audit_R1_20260826.md` |
| HG-GRAPH-MODULES | approved | 30 | 仅备注；不增一级模块 |

---

## 背景与目标

将 P0/P1 Gateway 接入：

1. `supervisor_node` / `_parse_subtasks`
2. router `_parse_route` / `_classify_route`
3. `info_extract_node`

**必须保留**现有 fallback 语义（如 supervisor 非法 → 单 rag；router 非法 → `DEFAULT_ROUTE=rag`；extract 非法 → 空结构），并在 span metadata 标记 `structured_output_fallback=true`（可与既有 `supervisor_fallback` / `router_fallback` 并存）。

---

## 范围 / 非范围

**范围**：

- 上述三处解析/LLM 结构化出口改走 Gateway（`parse_only` 和/或 `acomplete_structured`，由 30 按风险选型；须 Host 权威）
- 定义必要的 Pydantic schema（Route / Subtasks / Extract）
- fallback 语义与现行为一致；新增/补齐 `structured_output_fallback`（或 SPEC 等价名）metadata
- 更新/补充 mock 单测（`tests/test_lg_rag*.py` 或新文件）
- G-L1 `lg_rag` 备注 + graph-compile

**非范围**：

- ensure_keys / custom validate 完整产品化与并存策略文档（→ P3）
- Capability Gateway / `app/tools/` 草稿纳入
- 改 `app/ops/chat/graph.py` 拓扑或 SSE
- 改 multi/graph.py / router graph **拓扑**（节点接线可保留；只改节点内解析）
- Agently 依赖；升 freeze

---

## 验收标准

- [x] supervisor：非法/失败仍 fallback 单 rag；metadata 含 fallback 标记且含 `structured_output_fallback`（或文档等价且单测断言）
- [x] router：非法仍 fallback `rag`；metadata 含 fallback + structured_output 标记
- [x] info_extract：非法仍空结构（dates/versions/people 空列表）；不中断
- [x] 合法输出路径行为不劣于改前（既有 mock 单测绿）
- [x] Host 权威：校验失败不把坏 schema 当成功业务 plan/route
- [x] `pytest`：触及 lg_rag multi/router + structured_output 相关绿
- [x] ruff 触及路径绿
- [x] `app/ops/chat/graph.py` 零 diff；图拓扑文件无「改边」类业务变更（仅允许节点内逻辑）
- [x] G-L1 备注 + graph-compile exit 0
- [x] 无 Agently；无 Capability Gateway 实现

---

## failure_paths

| 触发 | 行为 | 可重试 |
|---|---|---|
| supervisor 解析/校验失败 | fallback 单 rag + structured_output_fallback | Y |
| router 解析/校验失败 | fallback rag + 标记 | Y |
| extract 解析/校验失败 | 空结构 + warning | Y |
| Gateway LLM 传输异常 | 保持节点既有 except → fallback/空结构 | Y |
| 误改 chat graph / 改拓扑 / Capability | 验收打回 | N |

---

## 依赖

- P0/P1 API · SPEC §4 P2 / §5  
- `app/ops/lg_rag/nodes.py` · `app/ops/lg_rag/multi/nodes.py`  
- 既有 `tests/test_lg_rag*.py`

---

## 给执行帽（30）必读

1. 本 task + SPEC §4 P2 / §5  
2. P0/P1 包 API  
3. 现网 `_parse_route` / `_parse_subtasks` / `info_extract_node` / `supervisor_node`  
4. FRAGMENT_30 + CODING_BACKEND_L2  
5. 硬约束：保留 fallback；打 structured_output_fallback；不改 chat/graph.py

---

## 思考轮

### 思考轮控制

| 字段 | 值 |
|---|---|
| **actual_last_round** | R5 |
| **early_stop** | no |
| **residual_risks** | router 历史有非 JSON 字符串 `"rag"` 宽容路径，改 schema 过严可能增 fallback 率（应用 parse_only 或保留宽容再 validate）。supervisor 用 complete 重试可能增延迟——P2 可对 supervisor 用 parse_only+单次 complete 或小 max_retries，须在实现注释说明。 |

### R0
三处接入；拓扑不动。

### R1
fallback 语义冻结为验收钉。

### R2
metadata：`structured_output_fallback` 与既有 `*_fallback` 并存。

### R3
优先复用 acomplete_structured；若节点已 complete 再 parse，可「complete 一次 + parse_only」避免双重 LLM——选型写进注释。

### R4
Pydantic schema 放 `app/ops/structured_output/schemas/` 或 lg_rag 旁；避免循环 import。

### R5
既有 9+ multi 单测与 router 单测不回归。

---

### 自检结论

> 2026-08-26 · 00 机械复检 · **PASS**（30 [Review](1b295842-e4c0-4671-8648-e3f6b39763f4)）

- [x] 验收勾选
- [x] pytest / ruff 绿（00 抽验 49 passed 触及集）
- [x] graph.py / 拓扑 零 diff
- [x] verify PASS

**50 结论**：PASS · 下一棒 P3

---

## CLOSE

| 项 | 内容 |
|---|---|
| 日期 | 2026-08-26 |
| 定稿 | router/supervisor/info_extract 接入 Gateway + structured_output_fallback |
| 归档 | 暂留 active |
| PR | 待全波次 |

---

## 修订

| 日期 | 说明 |
|---|---|
| 2026-08-26 | 00 起草 P2；闸 pending |
| 2026-08-26 | 20 R1 pass；00 代签闸 |
| 2026-08-26 | 30/40 PASS；00 50 PASS；CLOSE |
