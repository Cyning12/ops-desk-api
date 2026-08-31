# G-L2 · Indexes 补齐规格

> **Wave**：W3（chat 追平）· P2 拍板（第二试点 = **lg_rag**）  
> **试点真值**：`docs/_tech_graph/l2/README.md`  
> **传输系列硬约束**：[`../../agent-infra/05_lg_rag_transport_and_session_plan_v0.md`](../../agent-infra/05_lg_rag_transport_and_session_plan_v0.md) **§9**

---

## 1. 现状（2026-08-31）

| 文件 | 覆盖 |
|------|------|
| `l2/indexes/by_path.yaml` · `by_symbol.yaml` | chat · `10_flow_chat` 全 `implementedBy` |
| `l2/indexes/by_path_lg_rag.yaml` · `by_symbol_lg_rag.yaml` | lg_rag · `10_flow_lg_rag` **全** `implementedBy`（含 multi/strategy） |

**注释**：手维；W5 可选 `--check`，**不进** harness 默认 check。

---

## 2. W3 目标（chat 试点追平 · 历史）

### 2.1–2.3

见既有 W3 交付（`rag_nodes` 三条已入 chat indexes）。略。

---

## 3. 一致性规则（手维）

1. 域内 `implementedBy` 集合 ⊆ 该域 indexes  
2. **by_symbol**：同一 `(path, symbol)` 一个主 `node_id`；图上复用（如 `rag_node`→`b_rag`/`r_rag`）用 `also_node_ids`  
3. **by_path**：可按 node_id 多条列出同一 symbol（便于「所有节点」审计）  
4. `graph_id` 分文件钉死（chat=`10_flow_chat` · lg_rag=`10_flow_lg_rag`）  
5. bump `version` 与 flow yaml 变更同日为宜  

---

## 4. P2 拍板：第二 G-L2 试点域

| 选项 | 态度 |
|------|------|
| A · 只 chat | 历史 |
| **B · lg_rag** | **已选（2026-08-30）** · 分文件 |
| C · lc_evidence | 未开 |

**定夺**：

1. **2026-08-30**：选 B · 分文件起步（曾写「传输切片」）。  
2. **2026-08-31**：维护者要求——**传输 Spec 系列（`05`）凡涉及节点须更新 L2**；覆盖升为 **`10_flow_lg_rag` 全部 `implementedBy`**，写入 `05` §9；T3–T6 task 验收默认带 L2 钩子。

---

## 5. 验收清单

### 5.0 W3 chat（历史）

- [x] chat flow + indexes 含 `rag_nodes`  
- [x] `graph-compile` 绿  

### 5.1 P2-B + Spec §9（2026-08-31）

- [x] 分文件 `*_lg_rag.yaml`，不与 chat 混排  
- [x] indexes 覆盖 `10_flow_lg_rag` **全部** `implementedBy`（传输 + basic/router/supervisor/strategy）  
- [x] `05` §9 与 `l2/README` / 本文件互指  
- [ ] CI 自动校验 indexes（仍 W5 可选）

---

## 6. 非范围

- 全仓每个 `app/ops/**/*.py` 进 indexes  
- AST 自动生成 indexes  
- 把 lg_rag 倒排写入 chat yaml  
- 默认把 `structured_output_gw` / `capability_gw` 等**无** `implementedBy` 的外部 POINTER 节点强行建假条目  

---

## 7. 修订记录

| 日期 | 说明 |
|---|---|
| （W3） | chat 试点追平 |
| 2026-08-30 | **P2 选 B**：lg_rag 分文件；传输/SSE 切片起步 |
| 2026-08-31 | **全量 implementedBy** + `05` §9 系列硬约束；废止「另波再追平 multi」 |
