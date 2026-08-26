# 技术图谱前后对比 · Agent Infra 双 Gateway 升一级模块（方案 B）

> **日期**：2026-08-26  
> **授权**：维护者会话明示「授权 B · 新增一级模块」  
> **分支 / PR**：`task/capability-gateway` · [#59](https://github.com/Cyning12/ops-desk-api/pull/59)  
> **范围**：仅 `docs/_tech_graph/`（+ 本对比文）；**不**改 `app/ops/chat/graph.py` 业务拓扑

---

## 1. 一句话

实现落地后，双 Gateway 曾只写在 `lg_rag` **备注**里；方案 B 将其升为 G-L1 **独立 `module_id`**，并各立一张 flow graph，同时修正 `lg_rag` 依赖出边与 `tool_exec` 标签。

---

## 2. 更新前（Before）

### 2.1 模块表（`l1/01_modules.md`）

| 项 | 状态 |
|---|---|
| `structured_output` / `capability` 作为 `module_id` | **无** |
| 路径 glob 覆盖 `app/ops/structured_output/**`、`app/ops/capability/**` | **无** |
| `lg_rag` 依赖出边 | `→ lc_evidence_chain, llm`（**未**指向两 Gateway） |
| 两 Gateway 信息 | 仅堆在 `lg_rag` **备注**长句中 |
| 跨模块契约表 | **无** `ParseOutcome` / `CapabilityResult` 行 |
| HG-GRAPH-MODULES 人签（新增一级） | **无**（task 曾禁止新增一级模块） |

### 2.2 Flow graphs

| graph_id | 状态 |
|---|---|
| `10_flow_structured_output` | **不存在** |
| `10_flow_capability` | **不存在** |
| `10_flow_lg_rag` · `s_tool` 标签 | `tool_exec_node（Mock 注册表）`（与代码已迁 Gateway **不一致**） |
| compile 统计（PR #59 合入能力码后、本变更前） | **7** graphs |

### 2.3 G-L0

`00_main` **无**独立 Gateway 节点（方案 B 仍保持：由 `lg_rag_flow` 下钻，不强制抬升 G-L0）。

### 2.4 语义问题

- 代码包已独立，图谱却不可按 module 发现 / 依赖分析。  
- `tool_exec` 仍写 Mock 注册表，inform 图与实现漂移。

---

## 3. 更新后（After）

### 3.1 模块表

| module_id | 路径 glob | 依赖出边 | flow |
|---|---|---|---|
| `structured_output` | `app/ops/structured_output/**` | → `llm` | [`10_flow_structured_output.md`](../_tech_graph/l1/10_flow_structured_output.md) |
| `capability` | `app/ops/capability/**` | → — | [`10_flow_capability.md`](../_tech_graph/l1/10_flow_capability.md) |
| `lg_rag`（修订） | `app/ops/lg_rag/**` | → `lc_evidence_chain`, `llm`, **`structured_output`**, **`capability`** | [`10_flow_lg_rag.md`](../_tech_graph/l1/10_flow_lg_rag.md) |

新增契约行：

- `ParseOutcome` / `acomplete_structured` · 提供方 `structured_output` · 消费方 `lg_rag`
- `CapabilityResult` / `invoke` · 提供方 `capability` · 消费方 `lg_rag`（`tool_exec_node`）

人签：`HG-GRAPH-MODULES` · 维护者授权 B · 2026-08-26（见 `01_modules.md` 人签表）。

### 3.2 Flow graphs

| graph_id | 内容摘要 |
|---|---|
| `10_flow_structured_output` | caller → complete/parse_only → extract → repair → validate → outcome；失败预算内 CORRECTION 回环 |
| `10_flow_capability` | register → list/filter → invoke → local_fn / probes / skill_stub → CapabilityResult；可选 FC adapter |
| `10_flow_lg_rag` | `s_tool` → **Capability Gateway**；并增边至 `structured_output_gw` / `capability_gw` external |

compile 统计：**9** graphs · 123 nodes · 173 edges（本机 `./scripts/graph-compile.sh` exit 0）。

### 3.3 G-L0

仍无独立 Gateway 节点（有意）：总图继续 `lg_rag_router` → `lg_rag_flow`，细节在 G-L1 模块与子 flow。

---

## 4. Diff 清单（文件级）

| 路径 | 变更 |
|---|---|
| `docs/_tech_graph/l1/01_modules.md` | +2 module 行 · `lg_rag` 出边 · 契约 · 人签 · 关联链 |
| `docs/_tech_graph/l1/10_flow_structured_output.graph.yaml` | **新增** |
| `docs/_tech_graph/l1/10_flow_capability.graph.yaml` | **新增** |
| `docs/_tech_graph/l1/10_flow_lg_rag.graph.yaml` | `s_tool` 标签 · +2 external · +4 接入边 · version |
| `docs/_tech_graph/l1/10_flow_*.md` / `graph.json` | `graph-compile` 衍生 |
| 本文 | 前后对比真值 |

---

## 5. 对照表（Before → After）

| 维度 | Before | After |
|---|---|---|
| 一级模块数（agent-infra Gateway） | 0（备注） | 2（`structured_output`, `capability`） |
| `lg_rag` → Gateway 依赖 | 隐式备注 | 显式出边 |
| 独立 flow | 0 | 2 |
| `tool_exec` 图谱文案 | Mock 注册表 | Capability Gateway |
| graphs 数量 | 7 | 9 |
| 是否改 Chat 主图 | — | 否 |

---

## 6. 非目标（本变更未做）

- 不把双 Gateway 抬进 G-L0 `00_main` 骨架  
- 不改业务代码 / SSE 契约 / freeze  
- 不把 `app/tools/` 草稿登记为模块  
- 不引入 Agently 运行时

---

## 7. 验证

```bash
./scripts/graph-compile.sh
# 期望：OK 含 10_flow_structured_output · 10_flow_capability；graphs 9
```

---

## 8. 修订

| 日期 | 说明 |
|---|---|
| 2026-08-26 | 初版：方案 B 落地后的前后对比 |
