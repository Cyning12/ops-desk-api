# module · `auth`

| 字段 | 值 |
|------|-----|
| **Wave** | W5 |
| **graph_change_layer** | `G-L1`（仅 anchors / 可选 implementedBy） |

---

## 1. 代码范围

`app/ops/auth.py` · `deps.py` · `security.py` · `chat/router.py`（`sessions/latest`）

---

## 2. 现状

| 资产 | 状态 |
|------|------|
| `10_flow_auth` | ✅ 14 边 **均有 anchors**（EVAL 标杆） |
| G-L2 | ❌ 无 implementedBy |
| `01_modules` | ✅ |

---

## 3. 目标资产（W5）

| 优先级 | 动作 |
|--------|------|
| P2 | 刷新 anchors 行号（若源码行漂移） |
| P3 | 可选：为 `get_current_user` / `login` 补 `implementedBy` + indexes（仅当要做 auth 域 G-L2） |

---

## 4. 验收清单

- [ ] `10_flow_auth` harness check 仍 OK
- [ ] 与 lc/lg HTTP 的鉴权关系在 flow 备注中 POINTER 到 `deps.CurrentUser`（可选边 label）

---

## 5. 非范围

- 改鉴权逻辑
- 新建 `10_flow_auth`（已存在）
