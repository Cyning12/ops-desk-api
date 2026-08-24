# module · `api`

| 字段 | 值 |
|------|-----|
| **Wave** | W1（与 G-L0 同步） |
| **graph_change_layer** | `G-L0`（经 `00_main`） |

---

## 1. 代码范围

- `app/ops/router.py` — 一级 `include_router` 聚合
- `app/ops/*/router.py` — 各域子路由

---

## 2. 现状

| 资产 | 状态 |
|------|------|
| `01_modules` 行 | ✅ |
| G-L0 `ops_router` | ⚠️ 缺 lc/lg 子路由；anchors 旧 |
| 独立 `10_flow_api` | ❌ 不需要（路由注册非独立业务域） |

---

## 3. 目标资产

| 优先级 | 文件 | 动作 |
|--------|------|------|
| P0 | `l0/00_main.graph.yaml` | `ops_router` 出边覆盖全部 include（见 `layers/G-L0_00_main.md`） |
| P0 | 同上 | 刷新 anchors 至当前 `router.py` 行号 |

**include_router 清单（2026-08）**：

auth · overview · issues · pulls · graph · admin_sync · chat · chat_ws · **lc_evidence** · **lg_rag**

G-L0 已有：auth · overview · issues · pulls · graph · admin_sync · chat（含 ws 可合并或单列）。

---

## 4. 验收清单

- [ ] G-L0 子路由节点与 `router.py` 一一对应（chat_ws 策略：合并到 chat_router 或独立节点 · W1 维护者二选一并在 yaml 备注）
- [ ] 无新建 `10_flow_api`
- [ ] compile 绿

---

## 5. 非范围

- 不改路由注册代码
- SSE 协议细节（留在 `10_flow_chat`）
