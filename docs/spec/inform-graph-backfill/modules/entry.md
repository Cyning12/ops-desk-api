# module · `entry`

| 字段 | 值 |
|------|-----|
| **Wave** | W5（低优先） |
| **graph_change_layer** | `G-L0`（若补锚点） |

---

## 1. 代码范围

`app/main.py` · `app/config.py`

---

## 2. 现状

| 资产 | 状态 |
|------|------|
| G-L0 `app` / `health` | ✅ |
| `01_modules` 行 | ✅ |
| 独立 flow | ❌ 不需要 |

---

## 3. 目标资产

| 优先级 | 动作 |
|--------|------|
| P2 | 核对 `app` → `ops_router` anchor（`main.py` include_router 行） |
| P2 | `health` → `app` mounted_on 边 |

---

## 4. 验收清单

- [ ] anchors 与 `main.py` 一致
- [ ] 无新建 flow

---

## 5. 非范围

- CORS / 中间件细节入图
