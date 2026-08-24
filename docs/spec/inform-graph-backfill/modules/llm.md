# module · `llm`

| 字段 | 值 |
|------|-----|
| **Wave** | W5（备注级） |
| **graph_change_layer** | `none` 或 `G-L1`（模块表半句） |

---

## 1. 代码范围

`app/llm/**` — `factory.py` · `providers/*` · `model_catalog.py`

---

## 2. 现状

| 资产 | 状态 |
|------|------|
| G-L0/G-L1 | 作为 **external** 节点出现在 chat/auth/lc/lg flow |
| `01_modules` | ✅ 备注含 usage 上报 |

---

## 3. 目标资产

| 优先级 | 动作 |
|--------|------|
| P3 | 各 flow 中 `llm` 边统一 label（`complete` / `complete_stream`） |
| P3 | 不在 G-L0 展开 provider 工厂（避免 >7 节点展开规则） |

---

## 4. 验收清单

- [ ] 无独立 `10_flow_llm`（除非未来多 provider 路由复杂化）
- [ ] `01_modules` 与 flow external 节点命名一致

---

## 5. 非范围

- Provider 切换逻辑入图
