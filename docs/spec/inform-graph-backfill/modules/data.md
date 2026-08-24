# module · `data`

| 字段 | 值 |
|------|-----|
| **Wave** | W5 |
| **graph_change_layer** | `G-L1`（anchors 刷新） |

---

## 1. 代码范围

`app/ops/overview.py` · `issues.py` · `pulls.py` · `graph.py`

只读 API：`GET /api/ops/overview` · `/issues` · `/pulls` · `/graph`

---

## 2. 现状

| 资产 | 状态 |
|------|------|
| `11_flow_sync_to_chat` | ✅ 含 issues/pulls/graph/chat_stream |
| G-L0 | ✅ overview/issues/pulls/graph 路由节点 |
| `01_modules` | ✅ |

---

## 3. 目标资产

| 优先级 | 动作 |
|--------|------|
| P2 | 刷新 `11_flow_sync_to_chat` anchors（`issues.py` L25 等） |
| P3 | 若 overview 指标路径变更，补 G-L0 `overview` 边说明 |

---

## 4. 验收清单

- [ ] sync→chat flow 与 admin 写入表名一致
- [ ] compile 绿

---

## 5. 依赖

- → `db`（只读）
- ← `admin`（数据写入）
