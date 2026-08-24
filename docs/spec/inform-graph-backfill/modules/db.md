# module · `db`

| 字段 | 值 |
|------|-----|
| **Wave** | —（仅 external 节点） |
| **graph_change_layer** | `none` |

---

## 1. 代码范围

`app/db/**` · `alembic/**`

---

## 2. 现状

| 资产 | 状态 |
|------|------|
| 各 flow | `PostgreSQL` external 节点 ✅ |
| `01_modules` | ✅ |
| ORM 表级图 | ❌ 不做（非 Inform 本仓范围） |

---

## 3. 补齐策略

**保持 external 节点**；不为每张表建 G-L1 flow。

可选：在 `01_modules` 契约表保留 `AsyncSession` · `ops_*` 表 POINTER（已存在）。

---

## 4. 验收清单

- [ ] 新 flow（lc/lg）含 `db` 依赖边（session / 只读查询）
- [ ] 无 `10_flow_db`

---

## 5. 非范围

- ER 图 / migration 可视化
