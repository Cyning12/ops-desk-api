# SPEC：LangChain Evidence+Answer Chain（并行于现网 LangGraph）（v1）

> **状态**：`accepted`（HG-SPEC-SIGNOFF=**approved** · 2026-08-14 维护者签收 v1）  
> **track**：`rag`（答问链实验 · 与现网 graph 解耦）  
> **上游**：现网 `app/ops/chat/graph.py`（LangGraph）· `app/ops/rag/*`（hybrid_recall / Qdrant Flag）· 规划 `docs/deployment/rag-frontend-api-plan.md`  
> **下游**：00/10-task 已预置 → 20-task-audit + HG-AUDIT-R1 → **维护者本人执行 30**（按 IMPL）  
> **Open Folder（实现）**：`ops-desk-api/`  
> **Bounded Context**：**禁止**改 `graph.py` / 现网 SSE 默认路径；本波只交付可独立调用的 LangChain 链 + 可选旁路入口。

---

## Harness 元信息

| 字段 | 值 |
|---|---|
| **spec_slug** | `langchain-evidence-chain` |
| **invoke_slug** | `langchain-evidence-chain` |
| **test_strategy** | `required` |
| **test_strategy_note** | 单测 mock 召回+LLM；CLI/旁路冒烟 1 问；断言不 import 修改 graph 拓扑 |
| **Open Folder（实现）** | `ops-desk-api/` |
| **默认分支** | `task/langchain-evidence-chain` |
| **graph_change_layer（建议）** | `G-L1`（新增 rag 旁路模块契约） |
| **实现辅助文档（与 task 分离）** | `docs/guides/IMPL_langchain-evidence-chain_v1.md` |

### 人工闸（SPEC 阶段）

| human_gate_id | status | 说明 |
|---|---|---|
| **HG-SPEC-SIGNOFF** | approved | 维护者 2026-08-14 签收 v1；可推进 task 审与 HG-AUDIT-R1 |

---

## 1. 背景与目标

### 背景

现网答问主路径是 **LangGraph**：`detect_intent → (retrieve→grade→answer | load_context→answer)`。  
维护者希望**另开一条**基于 **LangChain（LCEL）** 的路径，亲手跑通「检索 → 查询依据 → 回答」，用于：

1. 学习/对照 LangChain 写法（相对 LangGraph nodes）  
2. 产出可复用的 **evidence（查询依据）** 结构，形状兼容现网 `sources` / 未来可升为 graph node  
3. RAG 出问题时可**单独修这条链**，不拖垮现网 graph

### 目标（可验收）

1. 实现独立模块（建议包名 `app/ops/rag/lc_evidence_chain/`），输入 `query`，输出：  
   - `evidence` / `sources`：可序列化引用列表（对齐 `rag_nodes._to_source` 字段子集）  
   - `answer`：基于 evidence 的自然语言回答  
2. **零改动** `app/ops/chat/graph.py` 的节点与边（允许「未调用」；禁止改拓扑）  
3. 检索内核**复用**现有 `hybrid_recall`（及 Flag/Qdrant），禁止复制 SQL  
4. 提供 CLI 或显式 Flag 旁路入口，便于本机验收（默认不影响生产 chat）  
5. 文档：`IMPL_*.md` 分阶段示例代码，供维护者按阶段粘贴实现

### 非目标

- 替换或重写现网 LangGraph  
- 本期强制挂到 `POST /chat/stream` 默认路径  
- 重做 ingest / Qdrant 迁移  
- 独立微服务  
- 前端 UI（可后续接）

---

## 2. 方案对比（R2）

| 方案 | 描述 | 结论 |
|---|---|---|
| A · 在现有 graph 内加 LangChain 节点 | 改 graph，耦合高 | **否决**（违背「不影响当前 graph」） |
| B · 并行 LCEL 链 + 复用 retrieve | 新包；retrieve 可抽成「纯函数/Runnable」便于未来变 node | **采用** |
| C · 全新 HTTP RAG API 先做 | 见 `rag-frontend-api-plan` 路线 B | **本期不做**（可列为后续）；本波先 CLI/库级链 |

**推荐 B**：`evidence_runnable`（召回+整形）+ `answer_runnable`（LLM）组成 LCEL；evidence 输出 dict 列表与现网 `sources` 对齐，未来可把同一函数挂回 `retrieve_node` / 新 node。

---

## 3. 架构约束

```text
[现网 · 勿改拓扑]
  chat/stream → LangGraph(graph.py) → … → SSE

[本波 · 并行]
  CLI / 可选 Flag 旁路
       → lc_evidence_chain.ainvoke({query})
            1) embed + hybrid_recall (+ 可选 rerank)
            2) build_evidence(sources)
            3) LLM answer(evidence)
       → { evidence, answer, meta }
```

| 约束 | 要求 |
|---|---|
| 检索 | 调用 `app.ops.rag.retrieve.hybrid_recall`（或 detail）；尊重 `RAG_VECTOR_BACKEND` |
| Evidence 字段 | 至少：`source_type, source_id, chunk_index, anchor, title?, snippet, url?, relevance?` |
| LLM | 复用 `get_llm_provider`；模型可用 env（如 `RAG_LC_ANSWER_MODEL`）或沿用 chat 默认 |
| Grade 闸 | **P0 可选**：默认可跳过 grade（先出 evidence+answer）；若启用须复用 `grade_chunks`/`decide`，不得另起一套枚举 |
| 依赖 | 已有 `langchain` / `langchain-core`；优先 LCEL `RunnableLambda` / `RunnablePassthrough`，避免再引重框架 |

---

## 4. 验收标准（SPEC 级）

1. `git grep` / 审 diff：**无**对 `graph.py` 拓扑的修改（或仅注释说明「未改」）  
2. 模块可 `ainvoke`：给定 query，返回非空 `answer` 与 `evidence` list（语料库有命中时）  
3. 单测：mock recall + mock LLM，断言输出结构  
4. 维护者按 `IMPL_*.md` 分阶段手写实现后，CLI 冒烟 1 条通过  
5. 实现辅助文档与 task **分文件**；task 内有指向与阶段清单  

---

## 5. failure_paths

| 触发 | 行为 | 可重试 | 用户可见 |
|---|---|---|---|
| 召回为空 | `evidence=[]`，answer 走拒答文案或明确「无依据」 | Y（换问法） | answer 说明无资料 |
| Qdrant 失败 | 沿用 dense fallback → pgvector | Y | meta.backend / fallback |
| LLM 失败 | 抛错或返回 error 结构；CLI 非 0 | Y | 错误信息 |
| 误改 graph | 审查/验收打回 | N | PR 拒绝 |

---

## 思考轮

### 思考轮控制

| 字段 | 值 |
|---|---|
| **actual_last_round** | R5 |
| **early_stop** | yes |
| **early_stop_reason** | 范围清晰：并行 LCEL + 复用 retrieve；实现细节交给 IMPL 文档与维护者 30 |
| **residual_risks** | LangChain 与现网 LangGraph 双栈心智负担；若过早挂 SSE 易回归 |

### R0 · 问题框定

要一条**不影响 graph** 的 LangChain 证据+回答链，供手写学习与未来 node 化。

### R1 · 范围

新包 + CLI/旁路；复用 hybrid_recall；evidence 字段兼容 sources。

### R2 · 方案

采用并行 LCEL（方案 B）；否决改 graph、否决本期独立 HTTP。

### R3 · 边界

空召回、fallback、LLM 失败；禁止复制 SQL；禁止默认切生产 chat。

### R4 · 验收

结构单测 + CLI 冒烟 + graph 未改。

### R5 · 签收就绪

交人签 HG-SPEC-SIGNOFF → task + IMPL 文档 → 维护者 30。

---

## 修订

| 日期 | 说明 |
|---|---|
| 2026-08-14 | v1 draft：并行 LangChain evidence+answer 链 |
| 2026-08-14 | 维护者签收 · HG-SPEC-SIGNOFF=approved |
