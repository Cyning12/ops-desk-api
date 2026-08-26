# SPEC：Structured Output Gateway（v0 · 初版）

> **状态**：`active`（SPEC 已签收 · **P0–P3 已落地** · 下一里程碑见 ROADMAP）  
> **track**：`agent-infra` / structured-output  
> **文档位置**：`docs/spec/agent-infra/structured-output/`（L2 现行契约）  
> **升级路线**：[`ROADMAP_kernel_hygiene_v0.md`](./ROADMAP_kernel_hygiene_v0.md)（schema 抽离等 · **不**在本文扩写）  
> **上游讨论**：`docs/discussions/2026-08-26_lg-rag-agent-capability-architecture.md`  
> **对照思想**：Agently output-control（`ResponseParser` + `ModelRequestResultDataFlow`）；**不是** Skill  
> **下游**：须 00 拆 task → 10/20 → `HG-AUDIT-R1` 后才可 30；本 SPEC **不**直接授权 30  
> **Open Folder（实现）**：`ops-desk-api/`  
> **包路径**：`app/ops/structured_output/`

---

## Harness 元信息

| 字段 | 值 |
|---|---|
| **spec_slug** | `structured-output-gateway` |
| **invoke_slug** | `structured-output-gateway`（开 task 后启用） |
| **test_strategy** | `required` |
| **test_strategy_note** | 单元：合法 JSON / 围栏杂讯 / 结构坏引号 repair / schema 失败重试预算耗尽；接入后 router/supervisor 解析路径 mock 单测不回归 |
| **graph_change_layer（建议）** | `G-L1`（`lg_rag` 备注 + 可选新模块行） |
| **freeze_id** | 无 |
| **默认分支（建议）** | `task/structured-output-gateway` |

### 人工闸（SPEC 阶段）

| human_gate_id | status | 说明 |
|---|---|---|
| **HG-SPEC-SIGNOFF** | approved | 维护者会话签收 2026-08-26；**优先**由 00 统筹 P0–P3；颗粒度由 00 决定 |

---

## 1. 背景与目标

### 背景

- Agently 在 **Prompt 契约 + host 校验 + 预算重试** 上保证结构化输出；LangGraph **无**对等内置管道（仅有可选 `with_structured_output` / `response_format`）。  
- 本仓 `lg_rag` 多用 `_extract_json_object` / `_parse_route` / `_parse_subtasks`：**宽容解析、弱校验、无统一重试纠偏**。  
- 讨论结论：应用层建 **Structured Output Gateway**（仿 Agently DataFlow），作为节点出口的**强制基础设施**，不要做成模型可选 tool。

### 一句话目标

提供统一的 **parse →（可选）deterministic repair → schema/ensure 校验 → 预算内 LLM 纠偏重试** 管道，供 router / supervisor / extract 等结构化节点复用。

### 非目标（v0）

- 复制 Agently 全套 Prompt slot / 流式 instant parser  
- 把校验做成 LLM 可调用的 action（禁止模型自选跳过）  
- 业务答案质量评分（仍属 grader / evaluate）  
- 改 Chat 主图或 SSE 事件契约  
- 依赖 Agently / instructor 等重框架（v0 优先标准库 + Pydantic）

---

## 2. 与 LangGraph / Agently 的关系

| 层 | 谁负责 |
|---|---|
| LangGraph | 节点何时调用 Gateway；失败后图路由（fallback / END） |
| **本 Gateway** | 单次（或预算内多次）结构化结果的正确性 |
| LLM Provider | `complete` 调用；Gateway **不**取代 `get_llm_provider` |
| Capability Gateway | 外置工具执行；与本 SPEC **正交**（可组合：先结构化 plan，再 invoke 能力） |

**LangGraph 没有** Agently 级内置 output-control Prompt；本网关自带：

1. **首轮**：调用方传入的 system/user（或由 Gateway 追加 schema 摘要）  
2. **重试**：注入 `OUTPUT CORRECTION` 风格反馈（字段级 reason 截断）

---

## 3. 管道契约（v0）

```text
raw_text (或由 Gateway 触发一次 LLM)
        │
        ▼
1. extract / parse          ← 抽 JSON 对象；剥 code fence
        │
        ▼
2. deterministic repair     ← 仅 parse 失败时；结构符号修复（中英括号等）
        │
        ▼
3. schema validate          ← Pydantic model 或 JSON Schema
        │
        ▼
4. ensure_keys（可选）       ← 必填路径 presence / not_null
        │
        ▼
5. custom validate（可选）   ← 业务 handler
        │
   pass → StructuredResult
   fail → 若 retry_count < max_retries 且允许 LLM 重试
            → 注入 correction → 再请求 → 回步骤 1
          否则 → raise 或返回 StructuredFailure（由调用方选）
```

### 3.1 表面 API（概念）

```text
parse_only(text, *, schema) -> ParseOutcome
                       # 无 LLM；仅 parse+repair+validate

complete_structured(
    messages | (system, user),
    *,
    schema,
    ensure_keys=None,
    validate=None,
    max_retries=3,
    raise_on_failure=True,
    llm_ctx=None,          # provider/model 覆盖
) -> T | StructuredFailure
```

### 3.2 Host 权威原则

- Schema / ensure / custom validate **全部在 host 执行**；模型输出不得自称「已校验」。  
- Pydantic 失败：**不得**当作成功业务数据返回（对齐 Agently）。  
- 敏感规则可 `no_retry`（fail closed，不把隐藏规则泄漏进 correction prompt）。

### 3.3 Repair 边界

- **确定性 repair**：只修结构性标点/括号；**不**改写字符串语义内容。  
- **LLM repair**：仅通过预算内完整重生成；不做「只改坏字段」的半截补丁（v0 简化；日后可迭代）。

---

## 4. 接入面（分波）

| 波次 | 内容 | 验收草案 |
|---|---|---|
| **P0** | `parse_only` + Pydantic；抽公共 JSON 提取（替换/封装 `_extract_json_object`） | 单测覆盖 fence / 杂讯 / 非法 |
| **P1** | `complete_structured` + `max_retries` + correction 注入 | mock LLM：第 1 次坏、第 2 次好 |
| **P2** | 接入 `supervisor_node` / `_parse_subtasks`、`router` `_parse_route`、`info_extract`（选型：节点 `complete` + `parse_only`，避免双重 LLM） | 现有 fallback 语义保留（非法 → 单 rag 等） |
| **P3** | ensure_keys / custom validate；可选与 `with_structured_output` 并存策略文档 | 文档 + 单测 |

**调用方策略示例（supervisor）**：Gateway 失败 → 仍可走现有「fallback 单 rag」，但须在 span 标记 `structured_output_fallback=true`。

---

## 5. 观测

- span / metadata：`schema_name` · `attempt` · `repaired` · `validation_error` 截断 · `fallback`  
- 与 `trace_span("supervisor"|"router"|"info_extract")` 同树

---

## 6. 失败路径

| 触发 | 行为 | 可重试 |
|---|---|---|
| 无法抽出 JSON | repair → 仍失败则计入 attempt | Y（LLM） |
| Schema 不匹配 | correction 反馈 | Y |
| ensure / custom 失败 | 同左；`no_retry` 则直接失败 | 视标记 |
| 预算耗尽 | `raise` 或 `StructuredFailure` | N |
| LLM 传输异常 | 上抛或按调用方 | Y（上层） |

---

## 7. 明确不是 Skill

| | Skill | Structured Output Gateway |
|---|---|---|
| 加载 | 可选绑定 | 节点出口基础设施 |
| 能否跳过 | 可 | **不可**（有契约的节点必须走） |
| 目的 | 业务能力包 | 结构化结果正确性 |

---

## 8. 测试策略（开 task 时细化）

- parse：合法 / fence / 前后废话 / 中文引号结构坏例  
- validate：缺字段 / 类型错  
- retry：mock provider 计数；correction 出现在第 2 次 messages  
- 接入：multi / router 相关单测不回归；fallback 路径仍触发

---

## 9. 修订记录

| 日期 | 版本 | 说明 |
|---|---|---|
| 2026-08-26 | v0 | 初版：对照 Agently DataFlow；划清与 Skill / Capability / LangGraph 边界；P0–P3 |
| 2026-08-26 | v0 | `HG-SPEC-SIGNOFF=approved`；状态 `active`；维护者授权 00 统筹本 SPEC 全波次 |
| 2026-08-26 | v0 | **P0–P3 落地状态**：P0 `parse_only`+repair；P1 `complete_structured`+correction；P2 router/supervisor/extract 接入；P3 `ensure_keys`/`validate`/`no_retry`+并存策略文档 `docs/guides/DESIGN_structured-output-gateway-coexistence_v0.md` |
| 2026-08-26 | v0 | 迁入 `docs/spec/agent-infra/structured-output/`；P2 接入选型写明 parse_only；下一里程碑 [`ROADMAP_kernel_hygiene_v0.md`](./ROADMAP_kernel_hygiene_v0.md)；根路径留 POINTER |
| 2026-08-26 | v0 | **H1 落地**（契约未升版）：域 schema → `app/ops/lg_rag/schemas/`（PR #67）；H2 跳过 |
