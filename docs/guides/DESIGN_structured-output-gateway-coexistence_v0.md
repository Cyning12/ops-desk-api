# DESIGN：Structured Output Gateway 与 LangGraph `with_structured_output` 并存策略（v0）

> **状态**：active  
> **上游 SPEC**：`docs/spec/agent-infra/SPEC-structured-output-gateway_v0.md`  
> **对应 task**：`structured-output-gateway-p3`  
> **硬约束**：本仓自建 Gateway 是**强制基础设施**（有契约的节点出口必须走 Host 管道）；**不是**消灭 LangGraph 原生 API，也不是互斥替换一切 LLM 调用。

---

## 1. 一句话

- **Gateway**：parse → repair → schema → ensure_keys → validate →（预算内）OUTPUT CORRECTION 重试；Host 权威，模型不能自选跳过。  
- **`with_structured_output` / `response_format`**：LangGraph / Provider 侧可选绑定；适合单次 schema 约束、无统一 ensure/自定义校验/纠偏预算的路径。  
- **并存**：同一仓可同时存在两种用法；选型由**节点契约与失败语义**决定，禁止「模型自行选择是否走 Gateway」。

---

## 2. 何时用 Gateway（默认）

| 场景 | 原因 |
|---|---|
| router / supervisor / info_extract 等**已有结构化契约**的节点 | 需要统一 extract/repair、fallback 标记、可观测 attempt |
| 需要 `ensure_keys` / custom `validate` | 原生 API 无对等 Host 管道 |
| 需要预算内 LLM 纠偏（OUTPUT CORRECTION） | 统一重试与截断 reason |
| 敏感规则须 `no_retry`（fail closed） | 避免把隐藏规则泄漏进 correction prompt |

调用方失败后仍可走业务 fallback（如单 rag），但须在 span/metadata 标记 `structured_output_fallback=true`（见 SPEC §4）。

---

## 3. 何时仍可用原生 `with_structured_output`

| 场景 | 说明 |
|---|---|
| 一次性实验 / 原型、无 Host ensure/validate | 可先用原生绑定，**升生产契约前**迁 Gateway |
| Provider 强依赖 `response_format` 且无纠偏预算需求 | 可并存；若后续要 ensure/重试，再包一层 Gateway |
| 非「结构化节点出口」的自由文本补全 | 本来就不走 Gateway |

**禁止**把原生 API 当成「跳过 Gateway 校验」的旁路：有契约的节点必须以 Host 管道为准。

---

## 4. 组合与边界

```text
LangGraph 节点
    │
    ├─ 有结构化契约 → Structured Output Gateway（强制）
    │                    └─ 内部仍可调用 get_llm_provider.complete
    │
    └─ 无契约 / 纯文本 → 直接 LLM 或可选 with_structured_output
```

- Gateway **不**取代 `get_llm_provider`；只保证结构化结果正确性。  
- 与 Capability Gateway **正交**（可先结构化 plan，再 invoke 能力）。  
- **不**引入 Agently / instructor 等重框架依赖（v0）。

---

## 5. 反模式

1. 模型输出自称「已校验」即当作成功业务数据。  
2. 为图省事绕过 Gateway，仅靠 prompt「请输出 JSON」。  
3. 文档/评审把并存写成「禁用 `with_structured_output`」——SPEC 明确是**并存**，非互斥消灭。  
4. `no_retry` 场景仍把敏感 reason 写入 OUTPUT CORRECTION。

---

## 6. 修订

| 日期 | 说明 |
|---|---|
| 2026-08-26 | P3 初版：并存策略；Gateway 为强制基础设施 |
