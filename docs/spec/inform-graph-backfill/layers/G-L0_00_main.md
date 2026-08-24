# G-L0 · `00_main` 补齐规格

> **Wave**：W1  
> **源文件**：`docs/_tech_graph/l0/00_main.graph.yaml`  
> **代码对照**：`app/ops/router.py` · `app/main.py`

---

## 1. 现状缺口

| 缺口 | 证据 |
|------|------|
| 未挂 `lc-evidence` / `lg-rag` HTTP | `router.py` L25–26 `include_router`；`00_main` 无对应节点 |
| `ops_router` 边 anchors 行号旧 | yaml 写 L14–20；现文件含 8 个 include |
| 无 rag 域节点 | `rag` 仅经 chat 间接消费 |

---

## 2. 目标节点（增量）

在 `nodes` 追加（`kind: flow` 或 `struct` 与现有 auth/chat 一致）：

| node id | label | 说明 |
|---------|-------|------|
| `lc_evidence_router` | `LC Evidence 路由` | `POST /api/ops/lc-evidence/invoke` |
| `lg_rag_router` | `LG RAG 路由` | `POST /api/ops/lg-rag/invoke` |

可选（W4 或更晚）：

| node id | label |
|---------|-------|
| `rag_domain` | `>../l1/10_flow_rag.md` · `kind: external` |

---

## 3. 目标边

```text
ops_router --routes--> lc_evidence_router
ops_router --routes--> lg_rag_router
```

W2 完成后追加：

```text
lc_evidence_router --::triggers--> lc_evidence_flow   # >../l1/10_flow_lc_evidence.md
lg_rag_router --::triggers--> lg_rag_flow             # >../l1/10_flow_lg_rag.md
```

**anchors**（W1 至少）：

| 边 | path | 说明 |
|----|------|------|
| ops_router → lc_evidence | `app/ops/router.py` | `include_router(lc_evidence_router)` 行 |
| ops_router → lg_rag | `app/ops/router.py` | `include_router(lg_rag_router)` 行 |

---

## 4. 版本与元数据

-  bump `version` 字段（建议 `2026-08-23` 或执行日）
- `layer` / `primary_layer` 保持 `G-L0`
- 不改 `struct_doc` → `01_modules`  POINTER

---

## 5. 同步文件

| 文件 | 动作 |
|------|------|
| `l0/00_main.graph.yaml` | 编辑源 |
| `l0/00_main.md` | compile 生成 |
| `l0/POINTERS_cross_repo.md` | 增旁路 flow 表行（W1 可写 TBD，W2 填实） |
| `shared/graph.json` | compile 生成 |

---

## 6. 验收清单

- [ ] `00_main` 节点含 lc_evidence / lg_rag 路由
- [ ] anchors 指向真实 `router.py` 行
- [ ] W2 后两条 `::triggers` 边存在且 target 为 external flow 指针
- [ ] `./scripts/graph-compile.sh` exit 0
- [ ] **未改** `app/` 代码

---

## 7. 失败路径

| 条件 | 处理 |
|------|------|
| flow 文件 W2 未建 | W1 可先只挂路由节点，triggers 边 W2 再加 |
| harness check 失败 | 查节点 id 唯一性、边 from/to 引用 |
