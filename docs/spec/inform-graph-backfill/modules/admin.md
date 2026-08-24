# module · `admin`

| 字段 | 值 |
|------|-----|
| **Wave** | W5 |
| **graph_change_layer** | `G-L1` |

---

## 1. 代码范围

`app/ops/admin/sync.py` · `service.py` · `schema.py`

`POST /api/ops/admin/sync` — maintainer 鉴权 · GHA payload 入库

---

## 2. 现状

| 资产 | 状态 |
|------|------|
| G-L0 `admin_sync` | ✅ |
| `10_flow_auth` | ✅ 含 admin_sync + maintainer_check |
| `10_flow_chat` / `11_flow_sync_to_chat` | ✅ 含 sync 侧链 |
| `01_modules` | ✅ |

---

## 3. 目标资产

| 优先级 | 动作 |
|--------|------|
| P2 | 统一三图中 `admin_sync` 节点 label / id（避免读者混淆） |
| P2 | 刷新 `admin/service.py` anchors |

---

## 4. 验收清单

- [ ] sync upsert 边指向 `service.py` 与 schema 一致
- [ ] auth flow 中 maintainer 依赖链完整

---

## 5. 非范围

- GHA sender 迁移（`task_ops_sync_sender_migration`）单独 task 决定是否补图
