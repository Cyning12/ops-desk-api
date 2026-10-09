# SPEC：工具列表页（当前用户可见能力目录 + admin 总表扩充）（tool-catalog-page）（v0）

> **层级**：L1 功能轨（capability 观测面补强 · 承 chat-history-hitl-ux 验收期实证）
> **状态**：`draft`（10-spec 初稿 · 维护者三裁定已答 Q1/Q2/Q4 · Q3 本帽裁定 · 待 20-spec-audit → HG-SPEC-SIGNOFF 人签）
> **立项令（原话留痕）**：维护者 2026-10-09「获取当前用户权限下所有工具的列表，前端出一个新的工具列表页，包含描述、权限、状态等」+ 三裁定原话：「catalog新立，admin是超级管理员可看的总表，且当前有些简略，需要扩充返回内容」（Q1/Q2）·「B2可以先用方案2」（Q4 承前批）
> **上游实证**：2026-10-09 本地验收期真读——`GET /api/ops/admin/capability/catalog` 当前仅回 `visible_ids` + 计数摘要（`app/ops/admin/capability.py:163-216`），无描述/权限/状态字段；可见集 8 个 tool 全 `side_effect: read`（`manifests/builtin.v1.yaml` · `oa.readonly.v1.yaml`）
> **下游**：HG-SPEC-SIGNOFF → 拆 task（后端 B1/B2 先 · 前端 F1 专项 SPEC 另立——承 chat-history-hitl-ux Q4 同款分仓纪律）
> **Open Folder（实现）**：`ops-desk-api`（后端 B1/B2）· `ops-desk-web`（前端 F1 · 专项 SPEC 后补）

---

## Harness 元信息

| 字段 | 值 |
|---|---|
| **spec_slug** | `tool-catalog-page` |
| **invoke_slug** | `tool-catalog-page`（task 阶段） |
| **test_strategy** | `required`（后端：用户态端点字段族/鉴权/可见集对拍/manifest 故障降级；admin 扩充向后兼容对拍；前端专项 SPEC 自填） |
| **默认分支** | `task/tool-catalog-page`（后端）· 前端仓另定（**禁止 master 直改**） |
| **graph_change_layer** | `G-L1` 预期（新 REST 路由行备注义务 · 实现 task 按实判 · HG-GRAPH-MODULES 随交付签录） |
| **freeze_id** | 无（纯 REST 查询面 · 零 SSE 帧改动 · 零 capability 执行语义改动） |

### 人工闸（SPEC 阶段）

| human_gate_id | status | 说明 |
|---|---|---|
| **HG-SPEC-SIGNOFF** | pending | 20-spec-audit 落盘后维护者签 |

---

## 1. 背景与目标

验收期实证：维护者想知道「当前用户能用哪些工具」时只能读 manifest YAML 猜——现有 catalog 端点是 **admin 预览面**且返回简略（只有 id 列表 + 计数），没有承载描述、权限（side_effect/risk）、状态（在册/可见/被裁原因）的用户可读形态。

### 现状实证（本帽真读 · file:line 锚点）

| 缺口 | 真态 |
|---|---|
| 无用户态工具端点 | capability 查询面仅 admin 系：`GET /admin/capability/catalog`（:163）· `/runtime`（:79）· `/metrics` · `/receipts` · `/idempotency`（`app/ops/admin/capability.py:45` 起 · `AdminSyncAuth`）；登录用户（viewer/maintainer）无「我自己能看见什么」的端点 |
| admin 总表返回简略 | `catalog` 仅回 `{filter, principal, visible_ids, **summary}`（:199-215）——`visible_ids` 是裸 id 列表；manifest 里丰富的 `description`/`when_to_use`/`risk_level`/`side_effect`/`enabled`/`tags`/`tenant_scoped` 全部没出端点 |
| 字段族其实在册 | manifest 每条目已含：`id`/`kind`/`description`/`when_to_use`/`when_not_to_use`/`tags`/`risk_level`/`side_effect`/`enabled`/`tenant_scoped`/`reversible`/`execution_type`（`builtin.v1.yaml:7-29` 范式）——缺的只是**出站投影** |
| 可见性求值已完备 | `capability_catalog_snapshot`（`gateway.py:133-143`）→ `evaluate_visibility` 回「可见集 + 谁被裁、为什么」——用户态端点可直接复用，只需把 principal 换成会话用户 |
| manifest 故障会静默缺条目 | 实证（docker api 日志）：`manifest 加载失败（已跳过该文件）`——总表若无「在册状态」字段，此类缺失不可观测 |

### 一句话目标

给**登录用户**一个「我的工具箱」只读端点（B1）+ 把 **admin 总表**从 id 列表扩成含描述/权限/状态的全字段总表（B2），前端据此出**工具列表页**（F1 · 专项 SPEC 另立）——纯只读观测面，零执行语义改动。

### 设计纪律（签收时锁死）

1. **只读零写**：不新增/修改/启停任何 capability；不改 manifest 真源（条目内容变更走各自 task，本 SPEC 只做出站投影）。
2. **admin 总表向后兼容**：B2 只**增**返回键，不改/不删既有键（`visible_ids`/`filter`/`principal`/summary 计数原样保留）——既有调用方零 diff。
3. **可见性语义单源**：B1 的「当前用户可见集」必须复用 `evaluate_visibility`（`gateway.py` / `visibility.py`），禁止在路由层另写过滤逻辑造成双真源。
4. **不泄露内部实现**：出站字段**不含** `adapter`（`local_fn:...` 代码路径）等内部装配信息；manifest 注释已钉「无密钥字段」，投影时仍显式排除 adapter。
5. **freeze 零动**：零 SSE 帧改动。

---

## 2. 范围

### B1 · 用户态工具端点（后端 · 新立 · 维护者裁定 Q1）

| 端点 | 语义 |
|---|---|
| `GET /api/ops/capability/mine` | **新增**（cookie 登录用户 · Q3 本帽裁定 `CurrentUser`）：当前用户可见能力列表。principal 由会话用户构造（`user_id`/`tenant_id`/`roles` 承 `deps.get_current_user` + `request.state.ops_tenant_id` 语义）；每条目字段族：`id` · `kind` · `description` · `when_to_use` · `tags` · `risk_level` · `side_effect` · `enabled` · `status`（`available` · 承可见性求值结果）；返回 `{items, count}`（对齐既有列表端点外形） |

- **只回可见集**（`available`）：用户面不展示「被裁掉的有什么」（那是 admin 面的诊断信息 · 防探测）。
- 可见集为空 → 200 `{items: [], count: 0}`（不 500 · 空态如实）。
- 复用 `capability_catalog_snapshot` / `evaluate_visibility`（设计纪律 #3）；出站投影显式排除 `adapter`（纪律 #4）。

### B2 · admin 总表扩充（后端 · 原地增键 · 维护者裁定 Q2）

| 端点 | 语义 |
|---|---|
| `GET /api/ops/admin/capability/catalog` | **原地扩充返回内容**（鉴权 `AdminSyncAuth` 不动）：既有键全保留（纪律 #2）；新增 `items` 数组——**每个在册 capability 一条**（不止可见集）：`id` · `kind` · `description` · `when_to_use` · `when_not_to_use` · `tags` · `risk_level` · `side_effect` · `enabled` · `tenant_scoped` · `reversible` · `execution_type` · `status`（`visible` / `denied:<原因码>` / `disabled`）· `visibility_reason`（被裁原因文本 · 承 evaluate_visibility 摘要语义） |

- `status` 三态语义：`visible`=通过可见性求值 · `denied:<reason>`=在册但被裁（附原因）· `disabled`=manifest `enabled: false`。
- manifest 加载失败被跳过的文件：在响应 `summary` 增 `manifest_errors` 计数键（或沿用既有 meta 面 · 实现 task 裁定落点），让「缺条目」可观测（实证缺口 #5）。

### F1 · 前端工具列表页（概要 · 专项 SPEC 另立）

- 新页面「工具列表」：表格列 = 名称(id) · 描述(description) · 用途(when_to_use) · 权限(side_effect + risk_level) · 状态(status/enabled)；数据源 B1 `/capability/mine`。
- admin（maintainer）视角可切「总表」模式（B2），看被裁条目及原因。
- 空态/加载失败态有明确视觉（不只白屏）。

---

## 3. 非范围

- ❌ capability 注册/修改/启停/删除（manifest 真源零改动 · 非只读测试 capability 归 D 组 task）
- ❌ capability 执行面 / 编排面 / 委派令牌面任何改动
- ❌ MCP 形态（tech_graph 读取能力的生产形态归 SPEC-C 裁定 · 维护者 2026-10-09 令挂起待 cyning-harness-meta 完善）
- ❌ 前端实现细节（组件/样式/路由）——前端专项 SPEC 另立（承 Q4 分仓纪律）
- ❌ 新 SSE 事件 / freeze 契约改动
- ❌ args_schema 出站（本期不暴露参数形态 · 有需求另立）
- ❌ 跨用户可见集对比视图（admin 已可用 query 参数模拟任意 principal · 不新增 UI 语义）

---

## 4. 开放裁定（全部作答）

### Q1 · 用户态端点形态（维护者裁定）

| 方案 | 裁决 |
|---|---|
| **S1 · 新立 `GET /api/ops/capability/mine`** | **裁定（维护者原话：「catalog新立」）**：用户面与 admin 诊断面分离 · 鉴权语义清晰（cookie 登录 vs AdminSyncAuth）· 爆炸半径隔离 |
| S2 · admin catalog 加 principal 参数复用 | 弃选：admin 面混入用户面 · 鉴权链（AdminSyncAuth 含 Bearer 机读）与「当前用户」语义不符 |

### Q2 · admin 总表扩充方式（维护者裁定）

| 方案 | 裁决 |
|---|---|
| **S1 · 原地增键（`items` 全字段数组）· 向后兼容** | **裁定（维护者原话：「admin是超级管理员可看的总表，且当前有些简略，需要扩充返回内容」）**：既有键零 diff · 新消费方用 `items` |
| S2 · 新立 `/catalog/full` 端点 | 弃选：双总表语义漂移 · 维护者已明示「扩充」而非「另立」 |

### Q3 · 用户面鉴权口径（本帽裁定）

| 方案 | 裁决 |
|---|---|
| **S1 · `CurrentUser`（任意登录用户 · 按各自可见集返回）** | **推荐（裁定）**：需求原话「当前用户权限下所有工具」——viewer 与 maintainer 可见集本就由 `evaluate_visibility` 按 principal 求值区分，无需路由层再设角色门；未登录 401 |
| S2 · 仅 maintainer | 弃选：把「权限下的工具列表」错配成「管理员专属」· viewer 看自己空集也是合法答案 |

### Q4 · 分仓与 SPEC 策略（维护者裁定 · 承前例）

| 方案 | 裁决 |
|---|---|
| **S1 · 合并 SPEC 先落后端仓 · 前端专项 SPEC 另立** | **裁定（维护者 2026-10-09 承 chat-history-hitl-ux Q4 同款：「B2可以先用方案2」+ 前后端一起开发令）**：本 SPEC 钉契约面与后端范围；F1 只写概要 |
| S2 · 双仓各写各的 | 弃选：契约面须单源 |

---

## 5. failure_paths

| # | 路径 | 处置 |
|---|---|---|
| FP-1 | 未登录访问 `/capability/mine` | **401**（`get_current_user` 既有语义） |
| FP-2 | 用户可见集为空（viewer 被全裁 / manifest 空） | 200 `{items: [], count: 0}` · 前端空态（不 500 · 不伪造条目） |
| FP-3 | manifest 加载失败（实证：加载失败跳过文件） | 总表 `manifest_errors` 可观测；用户面按实际在册集如实返回 · 不 500 |
| FP-4 | admin 总表既有调用方依赖旧响应形 | B2 只增不删（纪律 #2）· 验收钉既有键对拍 |
| FP-5 | 出站泄露内部装配（adapter 路径） | 投影白名单字段（纪律 #4）· 验收钉响应体不含 `adapter` 子串 |
| FP-6 | 可见性逻辑被路由层复制出第二真源 | 验收钉：路由层零过滤逻辑（复用 `evaluate_visibility`）· lint/走查拒收 |

---

## 6. 验收标准

### B1（后端 · 可机断）

- [ ] `GET /api/ops/capability/mine`：cookie maintainer 200 · `items` 字段族齐（`id`/`kind`/`description`/`when_to_use`/`tags`/`risk_level`/`side_effect`/`enabled`/`status=available`）· 条目集与 `evaluate_visibility` 对拍一致（当前实证可见集 8 个 · 以测试 fixture manifest 为准）
- [ ] 未登录 → 401（FP-1）；viewer fixture → 200 且条目 ⊆ maintainer 可见集（principal 区分实证 · FP-2 空集亦合法）
- [ ] 响应体不含 `adapter` / `local_fn:` 子串（FP-5）
- [ ] 路由层无自写过滤逻辑（FP-6 · 走查 + 单测对拍求值函数直出）

### B2（后端 · 可机断）

- [ ] `/admin/capability/catalog` 响应：既有键（`filter`/`principal`/`visible_ids`/summary 计数）**逐键对拍零 diff**（FP-4）
- [ ] 新增 `items`：覆盖**全部在册** capability（含被裁者）· 字段族齐（含 `when_not_to_use`/`tenant_scoped`/`reversible`/`execution_type`）· `status` 三态可分辨（`visible`/`denied:*`/`disabled`）· `denied` 条目附 `visibility_reason`
- [ ] manifest 加载故障注入 → 总表可观测（`manifest_errors` 或裁定落点 · FP-3）

### 契约 / 图谱

- [ ] 零 SSE 帧 diff（freeze 零动）
- [ ] 新 REST 路由 G-L1 行备注 + HG-GRAPH-MODULES 签录（实现 task 随交付）
- [ ] `pytest tests` 全绿 · `lint-imports` 绿（新端点落 `app/ops/` 哪一包由 task 裁定 · 不跨 import-linter 契约）

### 前端（F1）

- [ ] 以前端专项 SPEC 为准（本 SPEC 不钉前端验收 · Q4 裁定）

---

## 7. 思考轮回填（R0–R5）

- **R0（读人聊/目标）**：维护者需求原话（工具列表页 · 描述/权限/状态）+ 三裁定原话（catalog 新立 / admin 总表扩充 / 方案2 分仓）+ 验收期实证（catalog 返回简略 · 可见集全只读 · manifest 故障静默）。
- **R1（范围/非范围）**：B1/B2 后端 + F1 概要；执行面/manifest 真源/MCP/SSE/args_schema 显式排除。
- **R2（方案对比）**：Q1/Q2 维护者裁定 + Q3/Q4 本帽/承例裁定（均 ≥2 案）。
- **R3（边界/失败路径）**：FP-1~FP-6；最锋利边界 = 向后兼容（只增不删）与可见性单源（禁双真源）。
- **R4（验收/可测性）**：B1/B2 全可 pytest 机断（fixture manifest → 字段族/对拍/401/故障注入）；契约面 diff 断言。
- **R5（签收就绪）**：开放裁定无遗留；后端可立即拆 task；前端专项 SPEC 另立。

### 思考轮控制

| 轮 | 状态 | 说明 |
|---|---|---|
| R0 | done | 维护者原话 + 验收期实证 + 码面锚点真读 |
| R1 | done | 范围 B1/B2/F1 · 非范围锁死 |
| R2 | done | Q1–Q4 全部作答（≥2 案对比 · 裁定留痕） |
| R3 | done | FP-1~FP-6 裁定 |
| R4 | done | 验收全可机断（后端）· 前端归专项 |
| R5 | done | 签收就绪 → 20-spec-audit → HG-SPEC-SIGNOFF |
| early_stop | no | — |

---

## 8. 关联

- 实证源：2026-10-09 本地验收记录 `docs/acceptance/20261009_chat-history-hitl-ux_local_acceptance.md`（catalog 全只读实证 · 401 自查口诀）
- 码面锚点：`app/ops/admin/capability.py:163-216`（catalog 现状）· `app/ops/capability/gateway.py:133-143`（catalog_snapshot）· `app/ops/capability/visibility.py`（evaluate_visibility）· `app/ops/capability/manifests/builtin.v1.yaml:7-29`（字段族范式）· `app/ops/deps.py:56-115`（鉴权依赖）· `app/ops/router.py`（挂载点）
- 相邻工作面：D 组（非只读测试 capability 注册 · 本 SPEC 不涉）· SPEC-C（tech_graph 读码能力 · MCP 形态裁定挂起）· B 面（对话过程全量展示 + SSE 导出 · 另 SPEC）
- 前端专项 SPEC（待立）：`ops-desk-web` 仓 · 依据本 SPEC §2 F1 概要 + B1/B2 契约面

## 修订记录

| 日期 | 版本 | 内容 |
|---|---|---|
| 2026-10-09 | v0 | 10-spec 初稿：维护者三裁定（catalog 新立 / admin 总表原地扩充 / 分仓承例）+ Q3 本帽裁定（CurrentUser）· 码面锚点真读（catalog 简略出站 · manifest 字段族在册 · 可见性求值完备）· FP-1~FP-6 · R0–R5 回填 · 未签 HG-SPEC-SIGNOFF |
