# Task：capability-mine-endpoint（B1 · 用户态可见能力目录端点 GET /api/ops/capability/mine）

> **状态**：draft（10-task 落稿 · 三闸 pending 待签 · 30 拒开工）
> **类型**：新端点（只读观测面 · SPEC tool-catalog-page §2 B1 拆出 · 零执行语义改动）
> **依据**：`docs/spec/tool-catalog-page/SPEC-tool-catalog-page_v0.md`（HG-SPEC-SIGNOFF approved 2026-10-11 · Q1 维护者裁定「catalog新立」· Q3 本帽裁定 CurrentUser）+ R1 审 `docs/harness/reviews/spec_tool-catalog-page_audit_R1_20261011.md`（PASS-WITH-NITS · N1–N3 本 task 携带回填）
> **分支**：`task/tool-catalog-page`（既有 · 勿切）

## Harness 元信息

| 字段 | 值 |
|------|-----|
| **task_slug** | `capability-mine-endpoint` |
| **git_branch** | `task/tool-catalog-page` |
| **implement_repo** | `ops-desk-api` |
| **test_strategy** | `required` |
| **test_strategy_note** | TC1 鉴权 401 · TC2 maintainer 字段族+对拍 · TC3 viewer⊆maintainer（N3 钉死）· TC4 空集 200 · TC5 出站白名单 · TC6 单源对拍 · TC7 反回归工程面 |
| **code_quality_bar** | `L2_backend` |
| **graph_change_layer** | `G-L1`（预期 · 新 REST 路由行备注义务 · 30 按实判） |
| **graph_delta** | `G-L1`（预判 · 新增一条 REST 路由行 · 无新一级模块/跨模块边/表/SSE 事件） |
| **graph_delta_note** | 新端点落 `app/ops/` 新模块（候选 `capability_mine.py`）+ router.py 一行注册 → `docs/_tech_graph/l1/01_modules.md` 路由行备注回写 + HG-GRAPH-MODULES 随交付签录；若 30 裁定落点变动照实回填 |
| **wiki_delta** | `n/a` |
| **review_hat** | `20` |
| **required_invoke_hats** | `10,20,30,40` |
| **invoke_retention_profile** | `default` |
| **experience_capture** | `required` |
| **kpi_aggregator** | `n/a` |
| **orchestration** | 10 落稿 → 20 R1 → 维护者签 → 30（fixture manifest 先行 · 红测先行）→ 40 → PR+CI 绿 → CLOSE |
| **freeze_id** | 无（纯 REST 查询面 · 零 SSE 帧改动 · 零 capability 执行语义改动） |

### 人工闸

| human_gate_id | status | blocks_hats | 说明 |
|---------------|--------|-------------|------|
| HG-TASK-DRAFT | pending | 30 | 10 落稿后维护者签 |
| HG-AUDIT-R1 | pending | 30 | 20 R1 落盘后维护者签 |
| HG-GRAPH-MODULES | pending | 30 | 随交付按实判签录（新 REST 路由 G-L1 行备注义务） |
| HG-PILOT-OPSDESK-GLAYER | n/a | — | 无外部试点面 |

## 背景与目标

验收期实证：维护者想知道「当前用户能用哪些工具」只能读 manifest YAML 猜——capability 查询面仅 admin 系（`app/ops/router.py:4/:27` 仅注册 `admin_capability_router` · 全仓 grep `capability/mine` 零命中），登录用户（viewer/maintainer）无「我自己能看见什么」的端点；admin catalog 仅回 `{filter, principal, visible_ids, **summary}`（`app/ops/admin/capability.py:192-214`），manifest 在册字段族（description/when_to_use/risk_level/side_effect/enabled 等）全部没出端点。

SPEC §2 B1 裁定（Q1 维护者「catalog新立」· Q3 本帽 CurrentUser）：新立用户态只读端点，principal 由会话用户构造，可见集复用 `evaluate_visibility` 单源求值。

**一句话目标**：给登录用户一个「我的工具箱」只读端点 `GET /api/ops/capability/mine`——返回当前用户可见能力列表（字段族九键 + `{items, count}` 外形），只回可见集（防探测），空集 200 如实，零写零执行语义改动。

## 现状锚点

| 锚点 | 位置 | 事实 |
|---|---|---|
| 鉴权依赖本体（N2 回填） | app/ops/deps.py:18-53 | `get_current_user`：cookie→OpsSession（未登录/过期/用户不存在均 401 · :25-27/:40-42/:49-51）→ 返 OpsUser |
| tenant_id 注入 | app/ops/deps.py:44 | `request.state.ops_tenant_id = (session.tenant_id or "ops-desk-pilot").strip() or "ops-desk-pilot"` |
| CurrentUser 别名 | app/ops/deps.py:114 | `CurrentUser = Depends(get_current_user)`（Q3 裁定口径 · 任意登录用户） |
| 用户角色单值（N3 回填） | app/db/models.py:40 · deps.py:58 旁证 | `OpsUser.role` 单值 str（default "viewer"）；映射 `Principal.roles` 集合属实现细节 · 本 task 钉死 |
| 可见性求值单源 | app/ops/capability/visibility.py:112-135 | `evaluate_visibility(specs, principal) -> (kept, summary)`；被裁附 reason（:126 · 词表 :38-41） |
| catalog 快照入口 | app/ops/capability/gateway.py:133-143 | `capability_catalog_snapshot(filter, principal)` → `_registry.list_specs(filter)` + `evaluate_visibility`（:142-143） |
| admin catalog 形态对齐源（N1 回填） | app/ops/admin/capability.py:163-214 | catalog 函数体 :163-214 · 返回字典实起 :192（`filter`:193-203 · `principal`:204-211 · `visible_ids`:212 · `**summary`:213）；B1 仅对齐外形不复制逻辑 |
| 包内路由禁令 | app/ops/admin/capability.py:1-6（docstring） | `app/ops/capability/` 内**禁止挂 APIRouter**（有测试守着）→ B1 端点模块须落包外 |
| `{items, count}` 外形先例 | app/ops/hitl/router.py:94 · :172 | `return {"items": items, "count": len(items)}`（空集 :164 `{"items": [], "count": 0}`） |
| 用户态路由挂载点 | app/ops/router.py:19-34 | `router = APIRouter(prefix="/api/ops")` + include_router 列表（admin_capability_router :27） |
| viewer fixture 先例 | tests/conftest.py:414 · tests/test_hitl_pending_decide.py:50 | `role="viewer"` 用户构造在案 · TC3 直接复用形态 |
| manifest 字段族范式 | app/ops/capability/manifests/builtin.v1.yaml:7-29 | id/kind/description/when_to_use/tags/risk_level/side_effect/enabled 在册（+adapter :26 为排除对象） |
| 可见集实证基线 | SPEC :6 · 验收记录 20261009 | 当前可见集 8 个 tool 全 `side_effect: read`（builtin 5 + oa.readonly 3）· 以测试 fixture manifest 为准 |

## 钉死契约

1. **端点形态钉死**：`GET /api/ops/capability/mine` · 鉴权 `CurrentUser`（deps.py:114 · 任意登录用户 · 未登录 401 承 get_current_user 既有语义 :25-27/:40-42/:49-51 三分支）——Q1/Q3 裁定存续，不设角色门（viewer 看自己空集亦合法答案）。
2. **Principal 构造钉死（N3 回填）**：路由层由会话用户构造——`user_id=str(user.id)` · `tenant_id=request.state.ops_tenant_id`（deps.py:44 语义 · 缺省 "ops-desk-pilot"）· `roles=frozenset({user.role})`（OpsUser.role 单值→集合 · 本 task 钉死口径）· `departments/projects` 空集 · `classification_max` 用 Principal 缺省；**禁取自请求参数/模型产出**（visibility.py:54-72 主体由代码构造纪律同源）。
3. **可见性语义单源（SPEC 纪律 #3）**：可见集必须经 `capability_catalog_snapshot` / `evaluate_visibility`（gateway.py:133-143 · visibility.py:112-135）求值；**路由层零过滤逻辑**（禁双真源 · FP-6 走查+对拍拒收）。
4. **出站白名单钉死（SPEC 纪律 #4）**：每条目仅九键 `id`/`kind`/`description`/`when_to_use`/`tags`/`risk_level`/`side_effect`/`enabled`/`status`（`status="available"` 常量 · 承可见性求值结果）；显式排除 `adapter`（local_fn 代码路径）· `args_schema`（SPEC 非范围）· `when_not_to_use`/`tenant_scoped`/`reversible`/`execution_type`（归 B2 admin 面）；响应体不含 `adapter`/`local_fn:` 子串（FP-5 机断）。
5. **只回可见集（防探测）**：用户面不暴露「被裁掉的有什么/为什么」（那是 admin 面诊断信息）；可见集为空 → 200 `{"items": [], "count": 0}`（不 500 · 空态如实 · FP-2）。
6. **只读零写（SPEC 纪律 #1）**：不新增/修改/启停任何 capability · manifest 真源零改动 · 零 SSE 帧改动 · 零新表/零迁移/零新 env。
7. **落点纪律**：端点模块**禁落 `app/ops/capability/` 包内**（APIRouter 禁令 · 有测试守着）；候选 `app/ops/capability_mine.py` 新模块 + `app/ops/router.py` 注册一行；不跨 import-linter 契约（30 亲跑 `lint-imports`）。
8. **baseline 形态裁剪开放候选**：默认**不叠加** `baseline_filter`（用户面语义=「这个人能看见什么」· 非「这个场景该出现哪类」· 对拍以 evaluate_visibility 直出为准）；若 30 实证 registry 内含非默认条目致语义偏差 → 候选叠加并在 invoke 留裁定依据（**候选倾向：不加**）。

## 范围

- **F1 端点实现**：`app/ops/capability_mine.py`（候选落点）新模块 —— `GET /capability/mine` · CurrentUser 注入 · Principal 构造（钉死契约 2）· `capability_catalog_snapshot` 求值 · 白名单投影 → `{"items", "count"}`。
- **F2 路由注册**：`app/ops/router.py` include 一行（G-L1 行备注义务随交付）。
- **F3 测试断言化**（TC1–TC7 · fixture manifest 控在册集 · 红测先行）。
- **F4 图谱判定回写**：`docs/_tech_graph/l1/01_modules.md` 新路由行备注 + HG-GRAPH-MODULES 随交付签录。
- **F5 invoke 留档**（10/20/30/40 按 required_invoke_hats）。

### 非范围

- ❌ capability 注册/修改/启停/删除 · manifest 真源改动（SPEC 纪律 #1 · 归 D 组 task）
- ❌ B2 admin 总表扩充（另 task 拆 · 本 task 不动 `app/ops/admin/capability.py` 任何一行）
- ❌ capability 执行面/编排面/委派令牌面任何改动
- ❌ 前端页面（F1 前端专项 SPEC 另立 · ops-desk-web 仓 · Q4 裁定）
- ❌ 新 SSE 事件 / freeze 契约改动 · args_schema 出站 · 跨用户可见集对比
- ❌ MCP 形态（SPEC-C 裁定挂起）

## failure_paths

| 编号 | 失败路径 | 处置 |
|---|---|---|
| — | HG-TASK-DRAFT/HG-AUDIT-R1/HG-GRAPH-MODULES pending 即 30 | 拒开工（闸表 pending 不代签） |
| FP-1 | 未登录访问 `/capability/mine` | **401**（get_current_user 既有语义 deps.py:25-27/:40-42/:49-51 三分支 · TC1 钉） |
| FP-2 | 用户可见集为空（viewer 被全裁 / fixture manifest 空） | 200 `{"items": [], "count": 0}`（不 500 · 不伪造条目 · TC4 钉） |
| FP-3 | manifest 加载失败被跳过文件 | 用户面按实际在册集如实返回 · 不 500（总表 `manifest_errors` 可观测归 B2 task · 本 task 不涉） |
| FP-4 | roles 映射口径漂移（N3） | 钉死 `roles=frozenset({user.role})` · TC3 viewer⊆maintainer 对拍机断 |
| FP-5 | 出站泄露内部装配（adapter 路径 / args_schema） | 投影白名单九键（钉死契约 4）· TC5 响应体 grep `adapter`/`local_fn:` 零命中机断 |
| FP-6 | 可见性逻辑被路由层复制出第二真源 | 路由层零过滤逻辑（钉死契约 3）· TC6 单测对拍求值函数直出 + 走查拒收 |
| FP-7 | 端点误落 `app/ops/capability/` 包内（APIRouter 禁令） | 落点纪律（钉死契约 7）· 既有包内禁令测试 + lint-imports 双闸 |
| FP-8 | baseline filter 叠加与否语义漂移 | 默认不叠加（钉死契约 8 · 候选倾向不加）· 30 实证 registry 内容后裁定 · invoke 留痕 |

## B1 · 旧测影响面

| 测试文件 | 关系 | 预期 |
|---|---|---|
| tests/test_admin_capability_observability.py | admin catalog 面（本 task 零触达 `app/ops/admin/capability.py`） | 原样绿 · 零 diff |
| tests/test_capability_gateway.py · test_capability_domain_allowlist.py | 求值单源面（只调用不改动） | 原样绿 |
| tests/test_chat_router.py · tests/test_hitl_pending_decide.py（viewer fixture 先例） | 鉴权/fixture 形态参照 | 原样绿 |
| 全量 `pytest tests` | 基线 | 全绿（基线钉案若有 failed 照登 · 零新增红） |

## 验收标准

- [ ] **TC1 鉴权**：无 cookie 请求 `GET /api/ops/capability/mine` → 401（FP-1 · dependency_overrides 不挂即为真 401 路径）。
- [ ] **TC2 maintainer 字段族+对拍**：cookie maintainer → 200 · `items` 每条目九键齐（id/kind/description/when_to_use/tags/risk_level/side_effect/enabled/status="available"）· `count==len(items)` · 条目 id 集与 `evaluate_visibility` 对同一 fixture manifest 直出对拍**完全一致**（钉死契约 3/6）。
- [ ] **TC3 viewer⊆maintainer（N3 钉死）**：viewer fixture（role="viewer"）→ 200 且条目集 ⊆ maintainer 条目集；Principal roles=`{user.role}` 映射断言在测（FP-4）。
- [ ] **TC4 空集如实**：构造全裁 principal fixture（或空 manifest）→ 200 `{"items": [], "count": 0}`（FP-2 · 不 500）。
- [ ] **TC5 出站白名单**：响应体序列化后不含 `adapter` / `local_fn:` 子串（FP-5 · grep 机断）；九键之外零键（`args_schema`/`when_not_to_use` 等 B2 字段不出站）。
- [ ] **TC6 单源对拍**：单测断言路由返回值 == `capability_catalog_snapshot`/`evaluate_visibility` 直出投影（路由层零过滤 · FP-6）+ 走查。
- [ ] **TC7 工程面**：`pytest tests` 全绿（零新增红）· `ruff check app tests` 触及路径零新增 · `lint-imports` 绿 · `./scripts/graph-compile.sh` EXIT=0 · `npx spec-wave verify` PASS · G-L1 路由行备注回写 + HG-GRAPH-MODULES 签录 · 三闸 approved 后才 30。

## 依赖

- SPEC：`docs/spec/tool-catalog-page/SPEC-tool-catalog-page_v0.md`（§2 B1 端点语义表 · §4 Q1/Q3 裁定 · §5 FP-1/FP-2/FP-5/FP-6 · §6 B1 验收 · HG-SPEC-SIGNOFF approved :27）。
- R1 审：`docs/harness/reviews/spec_tool-catalog-page_audit_R1_20261011.md`（N1 锚点改引 capability.py:163-214 · N2 deps.py 改引 :18-115 · N3 roles 映射本 task 钉死）。
- 码面：`app/ops/deps.py:18-115` · `app/ops/capability/visibility.py:112-135` · `app/ops/capability/gateway.py:133-143` · `app/ops/admin/capability.py:163-214`（外形对齐源 · 零改动）· `app/ops/router.py:19-34` · `app/db/models.py:40`（OpsUser.role 单值）。
- 编码规范：`docs/standards/CODING_BACKEND_L2_v1_zh.md`（L2_backend bar）。

## 给执行帽的必读列表

1. SPEC v0 §1（设计纪律 1–5）· §2 B1 · §4 Q1/Q3 · §5 · §6 B1（`docs/spec/tool-catalog-page/SPEC-tool-catalog-page_v0.md`）。
2. R1 审 N1–N3（`docs/harness/reviews/spec_tool-catalog-page_audit_R1_20261011.md:44-52`）。
3. `app/ops/deps.py:18-115`（get_current_user 本体 :18-53 · ops_tenant_id :44 · CurrentUser :114）。
4. `app/ops/capability/visibility.py` 全文（evaluate_visibility :112-135 · Principal 构造纪律 :54-72 · reason 词表 :38-41）。
5. `app/ops/capability/gateway.py:116-143`（list_capabilities / capability_catalog_snapshot）。
6. `app/ops/admin/capability.py:163-214`（外形对齐源 :192-214 · 包内路由禁令 docstring :1-6）。
7. `app/ops/router.py`（挂载点）+ `app/ops/hitl/router.py:94/:164/:172`（`{items, count}` 外形先例）。
8. viewer fixture 先例：tests/conftest.py:414 · tests/test_hitl_pending_decide.py:50。

## 思考轮控制

| 轮 | 结论 | early_stop | reason（early_stop） | residual_risks |
|---|---|---|---|---|
| R0 | 问题框定：SPEC B1 已裁定（Q1 新立 · Q3 CurrentUser）· 本 task=出站投影落地 · 携带 N1–N3 回填 | false | — | 无 |
| R1 | 证据收集：锚点 13 行全亲读（n-2 计数修正）（deps :18-115 · visibility :112-135 · gateway :133-143 · admin :163-214 · router · models :40 · fixture 先例） | false | — | registry 非默认条目未实证（FP-8） |
| R2 | 方案生成：落点候选（`capability_mine.py` 新模块=倾向）· baseline 叠加候选（默认不加=倾向）· 均开放给 30 | false | — | 落点若变须回填 graph_delta_note |
| R3 | 反例/边界：包内路由禁令 · adapter 泄露 · 双真源 · roles 映射漂移 · 空集 500 风险 → 钉死契约 2–7 + FP-1~FP-8 | false | — | 无 |
| R4 | 收敛：TC1–TC7 全可 pytest 机断（对拍/⊆/401/空集/grep/工程面） | false | — | 无 |
| R5 | 收口：范围 F1–F5 · 非范围六条 · 三闸 pending 不代签 · 结构对齐 hitl-auto-resume-claim-race 先例 | true | SPEC 裁定闭合 · 锚点齐备 · 验收全机断 · 候选开放性显式留 30 · 再轮无新增信息 | 落点/baseline 两候选未锁死（刻意） |

**actual_last_round**：R5（early_stop）

### R0 · 问题框定

SPEC tool-catalog-page v0 已 HG-SPEC-SIGNOFF approved（2026-10-11），§2 B1 钉死用户态端点形态（Q1 维护者「catalog新立」· Q3 本帽 CurrentUser）；R1 审 PASS-WITH-NITS 携 N1（锚点 :163-214）/N2（deps :18-115）/N3（roles 映射钉死）三回填归本 task。任务面 = 纯出站投影落地，无新裁定需求。

### R1 · 证据收集

亲读：deps.py 全文 116 行（get_current_user 三 401 分支 · ops_tenant_id 缺省 "ops-desk-pilot" :44 · CurrentUser :114）；visibility.py 全文 141 行（evaluate_visibility :112-135 · 主体由代码构造纪律 :14 · fail-closed :15）；gateway.py :100-174（catalog_snapshot :133-143 直转 evaluate_visibility）；admin/capability.py :1-230（包内 APIRouter 禁令 docstring :1-6 · catalog 返回字典 :192-214）；router.py 全文 34 行（/api/ops 前缀 :19 · include 列表）；models.py:40（OpsUser.role 单值 default viewer）；{items, count} 先例 hitl/router.py:94/:172；viewer fixture 先例 conftest.py:414。

### R2 · 方案生成

两候选开放不锁死：①落点——`app/ops/capability_mine.py` 新模块（倾向：与 issues.py/pulls.py 同级用户态模块 · 避开包内禁令）；②baseline filter——默认不叠加（倾向：用户面=身份求值 · 对拍以 evaluate_visibility 直出为准），30 实证 registry 内容后裁定。两者均写入钉死契约 7/8 + FP-7/FP-8。

### R3 · 反例与边界

最锋利边界 = 可见性单源（禁路由层第二真源 · SPEC 纪律 #3/FP-6）与出站白名单（adapter/args_schema 不出站 · 纪律 #4/FP-5）；roles 单值→集合映射若 drift 则 viewer 对拍失真（N3 → FP-4 钉死）；空集须 200 不 500（FP-2）；落点撞包内禁令有既有测试兜底（FP-7）。

### R4 · 收敛

TC1–TC7 全部 pytest 机断：401 / 九键齐+对拍一致 / ⊆ / 空集 200 / grep 零命中 / 单源对拍 / 工程面四命令。无人工判断残留。

### R5 · 收口

范围 F1–F5、非范围六条、failure_paths 闸行+FP-1~FP-8、B1 旧测面、验收七条、必读八项齐备；三人工闸 pending 不代签；两候选（落点/baseline）开放性显式留 30。early_stop at R5。

### 自检结论（10 起草者）

1. **B-1 修复**：补本节（E5 lint 缺节 · 兄弟 task_catalog_manifest_errors_surface.md :190 先例形态对齐）。
2. **范围无溢出**：仅 GET /capability/mine 出站投影 · admin 面/manifest_errors 显式归兄弟 task；锚点 13 行全亲读核真（R1 C1–C12 全通过在案）。
3. **N1–N3 回填闭合**：锚点改引 :163-214 · deps :18-115 · roles=frozenset({user.role}) 钉死契约 2 + TC3 ⊆ 对拍。
4. **nit 回填**：n-1 契约 1/FP-1 补引第三 401 分支 deps.py:49-51 ✓ · n-2 R1 思考轮计数 12→13 ✓。
5. **三闸 pending 未代签**；落点/baseline 两候选开放留 30 实证。

---

## 修订

| 日期 | 说明 |
|------|------|
| 2026-10-11 | 10 落稿骨架（全节标题 + TBD · commit ba4a078） |
| 2026-10-11 | 10 逐节回填完成：SPEC B1 裁定承接 · N1–N3 回填钉死（锚点 :163-214 · deps :18-115 · roles=frozenset({user.role})）· 钉死契约八条 · TC1–TC7 · 三闸 pending 不代签 · 落点/baseline 两候选开放留 30 |
