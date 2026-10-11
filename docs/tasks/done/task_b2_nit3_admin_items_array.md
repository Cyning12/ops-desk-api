# Task：b2-nit3-admin-items-array（B2 后续：admin catalog items 全字段数组 + NIT-3 meta 键集相等断言补强）

> **状态**：done（CLOSED 2026-10-11 · PR [#241](https://github.com/Cyning12/ops-desk-api/pull/241) MERGED（squash `4d2dd22` · 2026-10-11T05:56:25Z · CI 绿）· 交付 commit `11645a6` · 30 验收矩阵全过：TC1–TC6 全绿（pytest 1787 passed/6 failed 六红逐项钉案全环境性 · lint-imports 12 kept 0 broken · graph-compile EXIT=0）· 三闸 approved（00 代录 · 授权 m00106）· R1 PASS-WITH-NITS（nit n-1 由 30 裁定选①：visibility_reason 恒出键 None）· CLOSE 归档 done/ · 细节见 CLOSE 文档 [`../close/close_b2_nit3_admin_items_array_20261011.md`](../close/close_b2_nit3_admin_items_array_20261011.md)）
> **类型**：SPEC 拆分实现 task（tool-catalog-page §2 B2 显式非范围回收 · 观测面补强 · 纯只读 · 零执行语义改动）+ 测试断言补强小面（NIT-3）
> **依据**：`docs/spec/tool-catalog-page/SPEC-tool-catalog-page_v0.md` §2 B2（items 数组钉案 :75-78）+ §5 FP-4/FP-5/FP-6 + §6 B2 验收（HG-SPEC-SIGNOFF approved 2026-10-11）· CLOSE 档 `docs/tasks/close/close_tool_catalog_page_b1b2_20261011.md` §7 后续建议第 2/3 条
> **分支**：`task/b2-nit3-admin-items-array`（worktree `../ops-desk-api-worktrees/t-b2-nit3-admin-items-array` · 自立分支勿切）

## Harness 元信息

| 字段 | 值 |
|------|-----|
| **task_slug** | `b2_nit3_admin_items_array` |
| **git_branch** | `task/b2-nit3-admin-items-array` |
| **worktree_root** | `../ops-desk-api-worktrees/t-b2-nit3-admin-items-array` |
| **implement_repo** | `ops-desk-api` |
| **test_strategy** | `required` |
| **test_strategy_note** | 红测先行：TC1 items 全字段键集/全覆盖断言 + TC2 既有键逐键零 diff + TC3 disabled 三态分辨 + TC4 防泄露子串断言 + TC5 NIT-3 meta 键集相等补强 + TC6 工程面 |
| **code_quality_bar** | `L2_backend` |
| **graph_change_layer** | `n/a`（预判 · 既有端点响应增键 + 纯测试断言强化 · 无新一级模块/路由/SSE 事件/表/env · `docs/_tech_graph/l1/01_modules.md` :38 admin 行既有「Capability 观测端点」备注覆盖语义） |
| **graph_delta** | `n/a`（预判照实写 · 30 实证若需行备注回写则升级 G-L1 + HG-GRAPH-MODULES 00 代录） |
| **graph_delta_note** | 改动面收敛于 admin/capability.py catalog 既有端点响应增 `items` 键 + tests 断言强化，均在 modules.md :38/:34 既有行备注覆盖的「观测快照经 admin 模块端点暴露」机制内；若 30 引入新 env 旋钮或新机制面 → 行备注回写义务触发 |
| **wiki_delta** | `n/a` |
| **wiki_delta_note** | 纯观测面增键 + 测试断言补强，无新编码模式/纪律沉淀；先例（落点裁定/防探测/单源）已在 SPEC 与 B1/B2 兄弟 task 留痕，无需 wiki 新页 |
| **review_hat** | `20` |
| **required_invoke_hats** | `10,20,30,40` |
| **invoke_retention_profile** | `default` |
| **experience_capture** | `required` |
| **kpi_aggregator** | `n/a` |
| **orchestration** | 10 落稿 → 20 R1 → 维护者签 → 30（红测先行再实现）→ 40 → PR+CI 绿 → CLOSE |
| **freeze_id** | 无（零 SSE 帧改动 · 零新表/迁移 · 零 capability 执行语义改动） |

### 人工闸

| human_gate_id | status | blocks_hats | 说明 |
|---|---|---|---|
| HG-TASK-DRAFT | approved | 20-R1, 30 | 初稿人扫 · 00 代录（授权 m00106 · 2026-10-11） |
| HG-AUDIT-R1 | approved | 30 | R1 PASS-WITH-NITS（docs/harness/reviews/task_b2_nit3_admin_items_array_audit_R1_20261011.md · nit n-1 契约5 键集/缺省张力留 30 二选一消歧）· 00 代录（授权 m00106） |
| HG-GRAPH-MODULES | approved | 30 | 预判 n/a（modules.md :34/:38 既有行备注覆盖 · R1 亲核属实）· 30 实证触发则回填代录义务在案 · 00 代录（授权 m00106） |
| HG-PILOT-OPSDESK-GLAYER | n/a | — | 无外部试点面 |

## 背景与目标

### 立项来源（交接档 + CLOSE 档照录）

交接档 `docs/harness/invokes/by-task/_prompts/PROMPT_00_spec-campaign-handoff_20261011.md` §2.2 第 4 项立项：「B2 NIT-3 / admin items 全字段数组（close 档后续建议四条照录）」。

CLOSE 档 `docs/tasks/close/close_tool_catalog_page_b1b2_20261011.md` §7 后续建议四条照录：

1. **前端 F1 专项 SPEC（SPEC 既定下游）**：`ops-desk-web` 仓工具列表页 · 依据本 SPEC §2 F1 概要 + B1/B2 契约面（mine 九键 + catalog manifest_errors/visibility_reason）——承 chat-history-hitl-ux Q4 同款分仓纪律。
2. **admin items 全字段数组（B2 显式非范围）**：SPEC §2 B2 的 admin 总表 items 扩充面本 task 未做（非范围节钉死 · 归后续 task）——若维护者仍需要请另立 task。
3. **B2 NIT-3 观察项跟进（可选）**：tests/test_capability_manifest.py:331/:354 系逐键值断言非键集相等 —— 如需键集相等强度断言可另立测试补强小 task。
4. **冒烟脚本化（可选）**：双 40 invoke 的 :8070 live 冒烟目前只有 invoke 文档口径无独立脚本（scripts/ grep 实证零命中）——若验收期需反复复跑，建议固化为 scripts/ 下冒烟脚本。

**本 task 承接第 2 条 + 第 3 条**；第 1 条（前端专项 SPEC · 分仓）与第 4 条（冒烟脚本化）显式归非范围。

### 实证锚点（本帽亲读核真 · file:line）

- **catalog 响应现状**（`app/ops/admin/capability.py:164-219`）：返回 `{filter, principal, visible_ids, **summary, manifest_errors, manifest_error_details}`——`visible_ids`（:214）仍是裸 id 列表；manifest 里丰富的 `description`/`when_to_use`/`risk_level`/`side_effect`/`tags`/`tenant_scoped`/`reversible`/`execution_type` 全部没出端点（SPEC §1 缺口 #2 存续 · B2 只做了故障可见性子面）。
- **字段族在册**（`app/ops/capability/types.py:77-130` CapabilitySpec）：`capability_id`/`kind`/`description`/`args_schema`/`tags`/`risk_level`/`enabled`/`tenant_scoped`/`side_effect`/`when_to_use`/`when_not_to_use`/`visibility`/`reversible`/`execution_type` 等——缺的只是出站投影。
- **disabled 条目在 filter 层被裁**（`app/ops/capability/registry.py:120-121`）：`_match_filter` 首判 `if not spec.enabled: return False`——catalog 默认走 `baseline_filter(node_role="admin_preview")`（admin/capability.py:179-181），故经 `capability_catalog_snapshot(filter=cap_filter)` 拿到的 specs **不含 disabled 条目**；而无 filter 时 `list_specs`（registry.py:85-91）回**全量在册**（含 `enabled: false`）。这是 items 数组「status 三态含 disabled」的数据源设计关键（见 R2 裁定）。
- **可见性求值单源**（`app/ops/capability/visibility.py:93-151`）：`check_visible` 回 `(visible, reason)` · `evaluate_visibility` 回 `(kept, summary)`，hidden 条目已附 `visibility_reason` 中文映射（:135-141 · 词表 `VISIBILITY_REASON_TEXTS` :44-49 · B2 已交付）——items 的 denied 条目直接复用，禁路由层重算。
- **NIT-3 锚点**（`tests/test_capability_manifest.py:331-333` 与 :354-356）：`meta = get_capability_manifest_metadata()` 后仅逐键值断言 `meta["version"] == 9` / `meta["capability_manifest_count"] == 1`——**无键集相等断言**，meta 面若被顺手扩键（B2 R2 落点 B 跑偏形态）现断言抓不住。meta 真源 `app/ops/capability/manifest.py:102-105`（`_LAST_META` 两键）+ :150-152 getter。

### 一句话目标

把 admin 总表从「id 列表 + 摘要」扩成含描述/权限/状态的全字段总表：`GET /api/ops/admin/capability/catalog` 响应新增 `items` 数组（**每个在册 capability 一条 · 含被裁与 disabled 条目** · SPEC §2 B2 :75 字段族 + status 三态 + visibility_reason）；同时把 NIT-3 观察项落成机断——`get_capability_manifest_metadata` 断言从逐键值升级为键集相等。纯只读观测面，零执行语义改动。

## 钉死契约

1. **只增不删（SPEC 纪律 #2 · FP-4）**：catalog 既有键（`filter`/`principal`/`visible_ids`/`visibility_*` 计数与 `visibility_hidden`/`manifest_errors`/`manifest_error_details`）逐键零 diff；本 task 只增顶层 `items` 键。
2. **items 覆盖全部在册（SPEC §2 B2 :75「每个在册 capability 一条（不止可见集）」）**：数据源为**无 filter 的全量注册表**（registry.py:85-91 口径），**不经 baseline/kinds/deny_write 场景裁剪**——`baseline` 等 query 参数对 `visible_ids`/summary 的影响存续，但对 `items` 覆盖集零影响（items 恒为全量在册集）。
3. **status 三态语义（SPEC :77）**：`disabled` ⇔ manifest `enabled: false`（**优先判定**，registry.py:120 同款语义）；`denied:<原因码>` ⇔ enabled 但 `check_visible` 裁掉（原因码承 visibility.py:38-41 四码）；`visible` ⇔ 其余。denied 条目附 `visibility_reason` 文本（单源 `VISIBILITY_REASON_TEXTS` :44-49，未知码原样兜底）。
4. **可见性单源（SPEC 纪律 #3 · FP-6）**：status/visibility_reason 判定复用 `check_visible`/`evaluate_visibility` 直出；**路由层零自写可见性规则、零重算**（投影只允许做字段拷贝与状态映射）。
5. **字段族钉案（SPEC :75）**：items 每条目键集精确 = `id`/`kind`/`description`/`when_to_use`/`when_not_to_use`/`tags`/`risk_level`/`side_effect`/`enabled`/`tenant_scoped`/`reversible`/`execution_type`/`status`/`visibility_reason`（14 键；`visibility_reason` 仅 denied 条目非空 · 其余 `None` 或缺省由 30 裁定并钉入测试）。**显式排除** `adapter`（含 `local_fn:` 路径 · SPEC 纪律 #4 · FP-5）与 `args_schema`（SPEC §3 非范围钉死）——键集相等断言机断，多一键少一键都红。
6. **NIT-3 键集相等补强**：`tests/test_capability_manifest.py:331-333/:354-356` 的 meta 断言升级为「键集相等 + 原逐键值存续」——`set(meta.keys()) == {"version", "capability_manifest_count"}` 在前，原值断言不动。**meta 面本身零改动**（B2 钉死契约 2 存续：`get_capability_manifest_metadata` 两键 · `/runtime` 响应零 diff）。
7. **只读零写 · 鉴权不动**：不改 manifest 真源/加载/校验/可见性求值语义；catalog 仍 `AdminSyncAuth`（admin/capability.py:166）；零 SSE 帧改动 · 零新表/迁移/新 env；B1 用户态端点 `/capability/mine` 零改动（九键白名单外形存续）。

## 范围

- **F1 items 投影**：`app/ops/admin/capability.py` catalog 响应增顶层 `items` 数组（数据源全量在册 · 钉死契约 1/2/3/4/5）。
- **F2 投影函数**：出站白名单投影（建议落点：admin/capability.py 模块内私有函数或承 B1 `project_capability` 先例的独立投影点 · 30 钉并留痕；adapter/args_schema/http/idempotency_key/hitl_* 等内部装配一律不出站）。
- **F3 NIT-3 断言补强**：tests/test_capability_manifest.py:331-333/:354-356 键集相等断言（钉死契约 6 · 纯测试改动）。
- **F4 测试断言化**（TC1–TC6 · 红测先行 · fixture manifest 注入 disabled/visibility 受限条目）。
- **F5 图谱判定回写**：预判 n/a 照实写；实证触发则 modules.md 行备注 + HG-GRAPH-MODULES 代录。
- **F6 invoke 留档**（10/20/30/40 按 required_invoke_hats）。

## 非范围

- ❌ **前端 F1 工具列表页**（CLOSE 后续建议第 1 条 · `ops-desk-web` 仓专项 SPEC 另立 · 承 Q4 分仓纪律）。
- ❌ **冒烟脚本化**（CLOSE 后续建议第 4 条 · 如需另立 task）。
- ❌ B1 用户态端点 `/capability/mine` 任何改动（兄弟 task 已 CLOSED · 九键外形存续）。
- ❌ `args_schema` 出站（SPEC §3 钉死 · 有需求另立）。
- ❌ `get_capability_manifest_metadata` / `/runtime` 响应面键集改动（钉死契约 6 · NIT-3 只动测试断言强度不动被测面）。
- ❌ manifest 加载/校验/reload 语义改动 · 可见性求值规则改动 · capability 注册/修改/启停/删除 · 执行面/编排面/委派令牌面任何改动。
- ❌ 新 SSE 事件 / freeze 契约改动 · 新表/迁移/新 env。
- ❌ 跨用户可见集对比视图（SPEC §3 钉死 · admin 已可用 query 参数模拟任意 principal）。

## 失败路径

| 触发条件 | 系统行为 | 可重试 | 用户可见 |
|----------|----------|--------|----------|
| HG-TASK-DRAFT/HG-AUDIT-R1/HG-GRAPH-MODULES pending 即 30 改码 | 执行 Agent **拒开工** | 是 | 须先 20 R1 落盘 + 人签 |
| items 数据源误用 `capability_catalog_snapshot(filter=cap_filter)`（disabled 被 filter 层裁掉 · registry.py:120-121） | status=disabled 永不出现 · TC3 红 | 是 | admin 总表缺 disabled 条目（三态语义破） |
| items 随手蹭 baseline/kinds/deny_write 裁剪 | 违背「每个在册一条」· TC1 全覆盖断言红 | 是 | admin 看不到被场景裁剪的在册条目 |
| 响应增键破坏既有调用方/多副本对拍 | TC2 既有键逐键零 diff；tests/test_multi_replica_dualproc.py:674-728 catalog parity 亲跑（同 manifest 集 → 同 items） | 是 | 既有消费方零 diff（只增键） |
| items 泄露内部装配 | 投影键集相等断言 + 响应体不含 `adapter`/`local_fn:` 子串断言（TC4 · SPEC FP-5） | 是 | 不外泄（机断拦截） |
| status/visibility_reason 判定路由层自写出第二真源 | 走查拒收 + TC1 与 `check_visible`/`evaluate_visibility` 直出对拍（SPEC 纪律 #3 · FP-6） | 是 | 文本与 reason 码不漂移 |
| NIT-3 补强误改 meta 被测面（顺手扩/删 `_LAST_META` 键） | 钉死契约 6 + `/runtime` meta 两键零 diff 回归（tests/test_admin_capability_observability.py:62 runtime 面存续） | 是 | meta 面零 diff |
| 测试注入污染全局注册表影响其他用例 | fixture tmp manifest + 显式恢复（承 B2 FP-1 同款隔离纪律 · 禁跨用例泄漏） | 是 | 无（测试内） |

## B1 · 旧测影响面

| 测试文件 | 关系 | 预期 |
|---|---|---|
| tests/test_admin_capability_observability.py | catalog 端点五测试（:54 鉴权 · :113 hidden 解释 · :149 kinds 裁剪 · :173 filter · :185 deny_write） | 原样绿（既有键零 diff · 只增 `items` 顶层键 · :113 等断言面不触及 items） |
| tests/test_capability_manifest.py | :331-333/:354-356 meta 断言 | **本 task 主动改**（NIT-3 键集相等补强 · 钉死契约 6）；其余用例原样绿 |
| tests/test_capability_manifest_errors.py | B2 故障注入 TC1-TC4（manifest_errors/details） | 原样绿（故障面零改动 · items 与 manifest_errors 共存） |
| tests/test_multi_replica_dualproc.py | :674-728 runtime/catalog 跨副本 parity | 亲跑绿（items 跨副本一致：同 manifest 集 → 同 items 数组） |
| tests/test_capability_mine.py | B1 用户态端点六测试 | 原样绿（B1 零改动 · 钉死契约 7） |

## 验收标准

- [ ] 全量测试命令通过（与本仓 CI 一致）：`pytest tests`（仓级基线钉案照登 · 零新增红 · 基线对拍口径承 B1/B2 40 先例）
- [ ] `npx --yes spec-wave@3.0.1 task lint-wiki-delta --target .` 通过（wiki_delta 预检 · 与 lint-wiki-delta.yml:35 run 行逐字一致）
- [ ] **TC1 items 全覆盖 + 字段族**：默认装配 catalog 响应 `items` 长度 == 全量在册数（含 disabled/被裁条目 · 钉死契约 2）；每条目键集精确 14 键（键集相等断言）；denied 条目 `visibility_reason` 与 `evaluate_visibility` 直出对拍一致
- [ ] **TC2 既有键零 diff**：`filter`/`principal`/`visible_ids`/`visibility_*`/`manifest_errors`/`manifest_error_details` 逐键对拍零 diff（SPEC FP-4）；`baseline=false` 与 query 参数组合下 `items` 覆盖集不变（恒全量在册）
- [ ] **TC3 三态可分辨**：fixture manifest 含 enabled:false 条目 + visibility 受限条目 → items 中同现 `disabled`/`denied:<原因码>`/`visible` 三态；disabled 条目不在 `visible_ids`（registry.py:120 语义）且不附 visibility_reason
- [ ] **TC4 防泄露**：响应体不含 `adapter`/`local_fn:`/`args_schema` 子串（SPEC FP-5 · 纪律 #4）
- [ ] **TC5 NIT-3 键集相等**：tests/test_capability_manifest.py:331/:354 两处 `set(meta.keys()) == {"version", "capability_manifest_count"}` 断言在前 + 原逐键值断言存续；`get_capability_manifest_metadata` 实现零 diff（钉死契约 6）
- [ ] **TC6 工程面**：ruff 触及路径零新增 · lint-imports 绿 · graph-compile EXIT=0（钉版 spec-wave@3.0.1 先例）· `npx spec-wave task lint --file` 本 task PASS · 三闸 approved 后才 30

## 依赖

- SPEC：`docs/spec/tool-catalog-page/SPEC-tool-catalog-page_v0.md`（§2 B2 :75-78 items 钉案 · §3 非范围 · §5 FP-4/FP-5/FP-6 · §6 B2 验收 · 纪律 #2/#3/#4 · HG-SPEC-SIGNOFF approved 2026-10-11）
- CLOSE 档：`docs/tasks/close/close_tool_catalog_page_b1b2_20261011.md`（§4 偏差 NIT-3 照登 · §7 后续建议四条 · 本 task 立项令）
- 交接档：`docs/harness/invokes/by-task/_prompts/PROMPT_00_spec-campaign-handoff_20261011.md`（§2.2 第 4 项 · §3/§4 坑全集）
- 兄弟 task（已 done · 契约面共存基准）：`docs/tasks/done/task_capability_mine_endpoint.md` · `docs/tasks/done/task_catalog_manifest_errors_surface.md`
- 码面：`app/ops/admin/capability.py:164-219`（catalog）· `app/ops/capability/gateway.py:133-143`（catalog_snapshot）· `app/ops/capability/visibility.py:38-49/:93-151`（词表 + check_visible + evaluate_visibility）· `app/ops/capability/registry.py:85-91/:112-121`（list_specs / _match_filter disabled 首判）· `app/ops/capability/types.py:77-130`（CapabilitySpec 字段族）· `app/ops/capability/manifest.py:102-105/:150-152`（_LAST_META + getter）· `app/ops/capability_mine.py:35-51`（B1 投影先例）
- 编码规范：`docs/standards/CODING_BACKEND_L2_v1_zh.md`（L2_backend bar）

## 给执行帽的必读列表

1. SPEC v0 §2 B2（:75-78）+ §3 非范围 + §5 FP-4/FP-5/FP-6 + §1 设计纪律（`docs/spec/tool-catalog-page/SPEC-tool-catalog-page_v0.md`）。
2. CLOSE 档 §4 偏差 2（NIT-3 原文）+ §7 后续建议四条（`docs/tasks/close/close_tool_catalog_page_b1b2_20261011.md`）。
3. `app/ops/admin/capability.py:164-219`（catalog 现状 · items 落点）+ :179-181（baseline filter 构造）。
4. `app/ops/capability/registry.py:85-91`（无 filter 全量在册）+ :112-121（_match_filter · disabled 首判——**为何 items 数据源不能走 cap_filter 的实证**）。
5. `app/ops/capability/visibility.py` 全文（:38-49 词表 · :93-117 check_visible · :120-151 evaluate_visibility——status/visibility_reason 唯一真源）。
6. `app/ops/capability/types.py:77-130`（CapabilitySpec 字段族 · adapter/args_schema 显式排除面）。
7. `app/ops/capability_mine.py:35-51`（B1 九键投影先例 · 本 task 14 键族扩面参照）。
8. `tests/test_capability_manifest.py:311-356`（NIT-3 用例上下文）+ B1 旧测影响面表列文件。

## 思考轮控制

| 轮 | 结论 | early_stop | reason（early_stop） | residual_risks |
|---|---|---|---|---|
| R0 | 问题框定：catalog 仍裸 id 列表（admin/capability.py:214）· SPEC B2 items 面未做（B2 非范围钉死）· NIT-3 逐键值断言强度不足 | false | — | items 数据源口径未定 |
| R1 | 证据收集：SPEC :75-78 钉案 + CLOSE §7 四条 + 码面七锚点亲读（registry.py:120-121 disabled filter 层首判 = 数据源设计关键实证） | false | — | — |
| R2 | 方案生成：items 数据源 S1 全量在册（无 filter）vs S2 蹭 cap_filter 快照 → **裁 S1**（SPEC「每个在册一条」+ disabled 三态只在 S1 可达 · S2 下 registry.py:120 使 disabled 永不出现） | false | — | visibility_reason 非 denied 条目形态（None/缺省）留 30 钉 |
| R3 | 反例/边界：数据源跑偏 · 蹭 baseline 裁剪 · 既有键 diff · 多副本 parity · 装配泄露 · 双真源 · NIT-3 误改被测面 | false | — | — |
| R4 | 收敛：改动面锁 admin/capability.py（items 投影）+ tests/test_capability_manifest.py（键集断言）+ 新测试文件；钉死契约七条 | false | — | 图谱判定为预判 |
| R5 | 收口：TC1–TC6 全可机断 + failure_paths + B1 表 + 三闸 pending 不代签 · R2 裁定留痕 | true | 范围/非范围/验收/failure_paths/锚点齐备 · 数据源裁定闭合 · 再轮无新增信息 | 投影函数落点细节待 30 钉（刻意开放） |

**actual_last_round**：R5（early_stop）

### R0 · 问题框定

SPEC §2 B2 钉了 admin 总表 items 扩充面（:75-78），B1/B2 双 task 实际只交付了 mine 端点与故障可见性子面，items 全字段数组被显式钉入 B2 非范围（close 档 §7 后续建议第 2 条「若维护者仍需要请另立 task」）；同时 R1 NIT-3 观察（tests/test_capability_manifest.py:331/:354 逐键值断言非键集相等）照登不阻留后续。交接档 §2.2 第 4 项将两者合并立项为本 task。

### R1 · 证据收集

SPEC §2 B2 :75 字段族钉案 + :77 status 三态语义 + CLOSE §7 四条原文照录 + 码面亲读七锚点。关键新证：**`_match_filter` 首判 `if not spec.enabled: return False`（registry.py:120-121）**，而 catalog 默认构造 `baseline_filter(node_role="admin_preview")`（admin/capability.py:179-181）——经 cap_filter 路径永远拿不到 disabled 条目，SPEC 三态语义中的 `disabled` 只有在「无 filter 全量在册」数据源下可达（registry.py:85-91 回全量含 disabled）。

### R2 · 方案生成（items 数据源裁定）

- **S1 · 全量在册（无 filter）+ 逐 spec 状态映射**：items 数据源 = 无 filter 的注册表全量（registry.py:85-91 口径）；`enabled==False` → `disabled`；否则 `check_visible(spec, principal)` → `visible`/`denied:<原因码>`。query 的 baseline/filter 参数只影响既有 `visible_ids`/summary（零 diff），不影响 items 覆盖集。
- **S2 · 蹭 `capability_catalog_snapshot(filter=cap_filter)` 结果拼 items**：kept → visible · summary.hidden → denied。
- **裁 S1**：①SPEC :75 钉死「每个在册 capability 一条（不止可见集）」，S2 下被 kinds/deny_write 场景裁剪的在册条目缺出；②S2 下 disabled 条目永不出现（registry.py:120-121），三态语义缺一角；③S1 下 disabled/denied/visible 三态单点可机断。S1 代价是路由需直接取全量 spec 列表（落点细节 30 钉），但状态判定仍复用 check_visible 单源，不破纪律 #3。

### R3 · 反例与边界

- 数据源跑偏：误用 cap_filter 快照 → TC3 disabled 断言红（failure_paths 第 2 行）。
- 蹭裁剪：items 随 baseline/query 变化 → 违背钉死契约 2 · TC2 覆盖集不变断言红。
- 向后兼容：只增 `items` 一键，既有键逐键零 diff（TC2 · SPEC FP-4）；多副本 parity 亲跑（dualproc :674-728）。
- 泄露面：adapter/args_schema/http/idempotency_key/hitl_* 不出站 · 键集相等 + 子串断言双保险（TC4）。
- 双真源：status/visibility_reason 全部承 check_visible/evaluate_visibility 直出（钉死契约 4）。
- NIT-3 边界：只加断言不改 `_LAST_META`（钉死契约 6 · `/runtime` meta 面零 diff 存续）。

### R4 · 收敛

改动面锁两处实现 + 一处测试补强：admin/capability.py（catalog 增 items 投影 · 路由只读透传 + 状态映射复用 visibility 单源）+ 新测试文件（TC1-TC4 红测先行）+ tests/test_capability_manifest.py 两处键集断言（TC5）。图谱预判 n/a 照实写（modules.md :38 admin 行「Capability 观测端点」既有备注覆盖 · 条件回写义务在案）。非范围八条显式排除（前端 F1 / 冒烟脚本化 / B1 / args_schema / meta 被测面 / 加载与执行语义 / SSE / 跨用户对比视图）。

### R5 · 收口

范围 F1–F6、非范围八条、failure_paths 闸行+七行、B1 五文件表、验收六条+两默认行全可机断；R2 数据源裁定（S1）留痕；三人工闸 pending 未代签；CLOSE 后续建议四条照录完毕（第 2/3 条入范围 · 第 1/4 条入非范围）。裁定收口，early_stop at R5。

### 自检结论（执行者）

**30 自检（2026-10-11 · 交付 commit `11645a6` · 实证全文见 [30 invoke](../../harness/invokes/by-task/b2_nit3_admin_items_array/invoke_20261011_30_implementation.md) · close 棒 50 代录回填 · 授权链 m00106）**：

- [x] 红测先行时序实证：RED（TC1/TC2/TC3 `KeyError: 'items'`）→ GREEN（新测试文件 4 件 + TC5 + 受击面 splittability D2 双用例共 11 件全绿）；TC4 实现前空转绿照实录、实现后咬合；TC5 目标用例基线即绿（NIT-3 属测试加固非行为修复 · 照实录）
- [x] **nit n-1 裁定（R1 留 30 二选一消歧）**：选 **①visibility_reason 恒出键（非 denied = `None`）**，保 14 键全条目键集相等（与「键集精确」表述自洽 · R1 推荐项）· TC1 恒出键断言钉死
- [x] TC1 items 全覆盖（长度 == 全量在册数 · 含 disabled/被裁条目）+ 每条目 14 键精确键集相等 + denied 条目 visibility_reason 对拍 `evaluate_visibility` 直出
- [x] TC2 既有 10 键在场 + 与 `capability_catalog_snapshot` 直出逐键对拍零 diff + 三组 query 组合下 items 覆盖集不变（恒全量在册）
- [x] TC3 三探针 disabled / denied:department_mismatch / visible 三态同现（register/unregister try/finally 隔离 · disabled 不在 visible_ids 不附 reason）
- [x] TC4 防泄露：响应体禁 `adapter|local_fn:` + `args_schema|secret_param|PROBE_BASE_URL` 子串（SPEC FP-5）
- [x] TC5 NIT-3 键集相等：tests/test_capability_manifest.py :334/:359 两处 `set(meta.keys()) == {"version", "capability_manifest_count"}` 在前 + 原逐键值断言存续 · 被测面零 diff
- [x] TC6 工程面：pytest 全量 1787 passed/6 failed（六红逐项钉案全环境性：三件主仓基线同红 · 三件 worktree 缺 `.env` 缺 SILICONFLOW_API_KEY、带主仓 .env 复跑全绿）· ruff check 三改动文件 All checks passed · lint-imports 12 kept 0 broken · graph-compile EXIT=0（graph.json 噪音已 checkout 还原）· task lint PASS · uv.lock 噪音已还原
- [x] 关键实现裁定：denied 判定复用包顶 `evaluate_visibility` hidden 条目（不直导 visibility 子模块 · 绕 admin-outbound forbidden 契约 · 码+文本一体单源）；disabled 优先判定承 registry._match_filter 首判语义（投影层）
- [x] 遗留照登：F811×4（tests/test_capability_manifest.py:468/:476/:554/:581 被 :523/:531/:597/:624 重定义 · 分支基线既有未修）· ruff format 两文件分支基线漂移（hunk 全落本棒未触既有行 · 主仓锁版 ruff 0.15.21 基线同挂 · 遵「勿当回归修」未修）

## 修订记录

| 日期 | 说明 |
|------|------|
| 2026-10-11 | 10 落稿（10-task 棒 · worktree `t-b2-nit3-admin-items-array` · 分支 `task/b2-nit3-admin-items-array` · base master 286d825）：交接档 §2.2 第 4 项立项 · CLOSE §7 后续建议四条照录（第 2/3 条入范围 · 第 1/4 条入非范围）· 实证锚点七处亲读（admin/capability.py:164-219 · registry.py:85-91/:120-121 · visibility.py:38-151 · types.py:77-130 · manifest.py:102-105/:150-152 · capability_mine.py:35-51 · test_capability_manifest.py:331/:354）· **R2 裁定 items 数据源 S1 全量在册（disabled 三态唯一可达路径）** · 钉死契约七条 · TC1–TC6 · 三人工闸 pending（未代签） |
| 2026-10-11 | 三闸 approved（**00 代录 · 授权 m00106**）：HG-TASK-DRAFT · HG-AUDIT-R1（R1 PASS-WITH-NITS · 审查文址A 在案 · nit n-1 留 30 二选一消歧）· HG-GRAPH-MODULES（n/a 复核通过 · 条件回写义务在案）→ 30 解锁 |
| 2026-10-11 | 30 自检结论回填 + **CLOSED**（50 close 棒 · 分支 `docs/close-b2-and-specwave330` · 授权链 m00106）：W3 占位符回填（实证承 30 invoke 验收矩阵 · nit n-1 裁定选① visibility_reason 恒出键 None · TC1 恒出键断言钉死）· PR [#241](https://github.com/Cyning12/ops-desk-api/pull/241) MERGED（squash `4d2dd22` · CI 绿）· 归档 done/ + 状态行 CLOSED 回写 · CLOSE 文档 `docs/tasks/close/close_b2_nit3_admin_items_array_20261011.md` · R1 审查文址B 复制件 `docs/audits/task-review/20261011_b2-nit3-admin-items-array_r1.md` 随本 CLOSE 落（址A 原件不动）· worktree `t-b2-nit3-admin-items-array` 与分支 `task/b2-nit3-admin-items-array` 移交 00 统一清理 |
