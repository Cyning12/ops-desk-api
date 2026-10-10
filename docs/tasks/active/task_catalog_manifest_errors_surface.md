# Task：catalog-manifest-errors-surface（B2 catalog 故障可见性 · manifest 加载失败从静默到可观测 + hidden 附 visibility_reason）

> **状态**：draft（10 落稿 · 三人工闸 pending · 未代签）
> **类型**：SPEC 拆分实现 task（观测面补强 · 纯只读 · 零执行语义改动）
> **依据**：`docs/spec/tool-catalog-page/SPEC-tool-catalog-page_v0.md` §2 B2 + §5 FP-3/FP-4 + §6 B2 验收（HG-SPEC-SIGNOFF approved 2026-10-11）· 20 审 R1 PASS-WITH-NITS `docs/harness/reviews/spec_tool-catalog-page_audit_R1_20261011.md`（**N4 携带回填 · 本 task 裁一**）
> **分支**：`task/tool-catalog-page`（既有分支 · 勿切 · SPEC 默认分支 · 与 B1/B2 兄弟 task 共分支按 00 编排）

## Harness 元信息

| 字段 | 值 |
|------|-----|
| **task_slug** | `catalog-manifest-errors-surface` |
| **git_branch** | `task/tool-catalog-page` |
| **implement_repo** | `ops-desk-api` |
| **test_strategy** | `required` |
| **test_strategy_note** | TC1 故障注入式断言（坏 manifest → catalog 响应 manifest_errors 可观测）+ TC2 零故障基线既有键逐键对拍 + TC3 visibility_reason 钉源对拍 + TC4 失败域隔离存续 + TC5 工程面 |
| **code_quality_bar** | `L2_backend` |
| **graph_change_layer** | `n/a`（预判 · 既有端点响应增键 · 无新一级模块/路由/SSE 事件/表/env · capability 行既有「观测快照 visibility.py（经 admin 模块端点暴露）」覆盖语义） |
| **graph_delta** | `n/a`（预判照实写 · 30 实证若需行备注回写则升级 G-L1 + HG-GRAPH-MODULES 00 代录） |
| **graph_delta_note** | 改动面收敛于 capability/admin 模块既有行备注覆盖的「manifest 加载 register + 观测快照经 admin 端点暴露」机制内；若 30 引入新 env 旋钮或新机制面 → capability 行备注回写义务触发 |
| **wiki_delta** | `n/a` |
| **review_hat** | `20` |
| **required_invoke_hats** | `10,20,30,40` |
| **invoke_retention_profile** | `default` |
| **experience_capture** | `required` |
| **kpi_aggregator** | `n/a` |
| **orchestration** | 10 落稿 → 20 R1 → 维护者签 → 30（故障注入红测先行再实现）→ 40 → PR+CI 绿 → CLOSE |
| **freeze_id** | 无（零 SSE 帧改动 · 零新表/迁移 · 零 capability 执行语义改动） |

### 人工闸

| human_gate_id | status | blocks_hats | 说明 |
|---|---|---|---|
| HG-TASK-DRAFT | approved | 20-R1, 30 | 2026-10-11 · 00 代录（授权 m01606/m00255）· R1 PASS-WITH-NITS（c3d5e57 · NIT-1~3 照登不阻） |
| HG-AUDIT-R1 | approved | 30 | 同上代录 · 锚点 14 组全核真 · N4 落点 A 裁定成立 |
| HG-GRAPH-MODULES | approved | 30 | 同上代录 · 按实判：预判 n/a · 30 实证触发 capability 行备注则随交付回填 |
| HG-PILOT-OPSDESK-GLAYER | n/a | — | 无外部试点面 |

## 背景与目标

### 实证锚点（SPEC :43 + R1 C15 · 逐字关键行）

- manifest 加载失败**仅落日志**：`app/ops/capability/manifest.py:200` `logger.error("manifest 加载失败（已跳过该文件）: %s: %s", ...)`——docker api 日志实证该行出现过，但端点面不可观测。
- 失败信息**即弃**：`load_capability_manifests`（manifest.py:175-201）收集 `failed: list[tuple[str, str]]` 进 `MultiManifestLoadResult`（:127-136），但启动期调用点 `load_extra_manifests_from_env()`（`app/ops/capability/__init__.py:110`）返回值被丢弃——失败集在加载完成后无任何进程内留存。
- 既有 meta 面仅 version+count：`get_capability_manifest_metadata`（manifest.py:145-147）回 `_LAST_META` = {version, capability_manifest_count}（:102-105），无故障字段；消费方为 `/runtime` 端点 `"manifest"` 键（`app/ops/admin/capability.py:99`）。
- 结果：总表若无「在册状态」字段，故障导致的**静默缺条目不可观测**（SPEC 缺口 #5 · FP-3）。

### N4 裁定（本 task 裁一 · 携带回填）

**裁定：落点 A —— catalog 响应 summary 面增键**（SPEC §2 B2 首选语序：「在响应 summary 增 `manifest_errors` 计数键」）：

- catalog 响应**顶层增两键**：`manifest_errors`（int · 最近一次加载失败文件计数）+ `manifest_error_details`（数组 · 每元素 `{path, error}` · 零故障时为空数组）。
- 弃选落点 B（扩 `get_capability_manifest_metadata` meta 面）理由：该 meta 同时被 `/runtime`（admin/capability.py:99）消费，扩它 = 两个端点响应面同动 + `tests/test_capability_manifest.py:331/:354` meta 断言牵连，爆炸半径更大；落点 A 把响应 diff 收敛在 catalog 单端点，与既有 `visibility_*` 摘要键平铺外形一致，故障注入断言单点机断。
- 无论落点，manifest.py 均需新增**模块级故障记录**（加载期持久化 failed 集 · 现状即弃）——数据落 manifest.py，出站长 catalog 路由只读透传。

### 一句话目标

manifest 加载失败从「仅日志」变为「catalog 响应可观测」（`manifest_errors`/`manifest_error_details` · 故障注入可机断），且 catalog 被裁条目（summary `visibility_hidden`）附 `visibility_reason` 文本（钉源 `evaluate_visibility` · visibility.py:126）——纯只读观测面，零加载/校验/执行语义改动。

## 现状锚点

| 锚点 | 位置 | 事实 |
|---|---|---|
| 故障日志唯一留存 | app/ops/capability/manifest.py:200 | `logger.error("manifest 加载失败（已跳过该文件）: %s: %s")` · 之后 failed 集无进程内留存 |
| 失败集产生点 | app/ops/capability/manifest.py:182-201 | `load_capability_manifests` 逐文件 try · failed.append((str(target), str(exc))) · 失败域隔离（:14-15 模块注释钉死） |
| 返回值丢弃点 | app/ops/capability/__init__.py:110 | `load_extra_manifests_from_env()` 启动期调用 · MultiManifestLoadResult 未消费 |
| 既有 meta 面 | app/ops/capability/manifest.py:102-105 · :145-147 | `_LAST_META` = {version, capability_manifest_count} · `get_capability_manifest_metadata` 仅两键 |
| meta 消费方 | app/ops/admin/capability.py:99 | `/runtime` 响应 `"manifest": get_capability_manifest_metadata()`（N4 弃选 B 的爆炸半径证据） |
| catalog 响应现状 | app/ops/admin/capability.py:163-214 | 返回 {filter, principal, visible_ids, **summary}（R1 N1：return 实起 :192）· summary 承 evaluate_visibility |
| hidden 条目现状 | app/ops/capability/visibility.py:126 | `hidden.append({"capability_id": ..., "reason": ...})` · 原因码词表 :38-41（department/role/project/classification） |
| 求值摘要数据源 | app/ops/capability/visibility.py:112-135 · gateway.py:133-143 | `evaluate_visibility` 回 (kept, summary) · catalog 经 `capability_catalog_snapshot` 直出 |
| SPEC 钉案 | docs/spec/tool-catalog-page/SPEC-tool-catalog-page_v0.md | §2 B2 :78（manifest_errors 落点留 task 裁定）· §5 FP-3/FP-4 · §6 B2 验收 · 纪律 #2 只增不删 |
| R1 携带 | docs/harness/reviews/spec_tool-catalog-page_audit_R1_20261011.md | N4（落点二选一 · 本 task 裁 A）· N1（锚点 :199-215 → :163-214）· N5（Q4「方案2」承前批编号勿误读） |

## 钉死契约

1. **只增不删（SPEC 纪律 #2）**：catalog 既有键（`filter`/`principal`/`visible_ids`/`visibility_*` 计数与 `visibility_hidden` 既有子键）逐键零 diff；本 task 只增 `manifest_errors` + `manifest_error_details` 顶层键与 hidden 条目 `visibility_reason` 子键。
2. **N4 落点钉 A**：故障面落 catalog 响应顶层（summary 面）· `get_capability_manifest_metadata` 与 `/runtime` 响应**零 diff**（tests/test_capability_manifest.py:331/:354 断言存续）。
3. **故障记录生命周期**：manifest.py 新增模块级故障记录 = 「最近一次 `load_capability_manifests` 调用的 failed 集」；单文件 `reload_capability_manifest` 成功 → 该文件故障记录清除。语义上限：记录必须如实反映「当前在册表是怎么来的」，禁止故障后重启语义外的自动清零。细节（结构/键名）30 钉并留痕。
4. **visibility_reason 钉源单源**：hidden 条目 `visibility_reason` 文本承 `evaluate_visibility` 摘要语义（visibility.py:126 reason 码 → 文本映射表落 visibility.py 模块 :38-41 词表旁）；**路由层零自写判定/零重算**（SPEC 纪律 #3 · FP-6）。
5. **只读零写**：不改 manifest 真源 · 不改加载/校验/失败域隔离语义（manifest.py:14-15 存续）· 不新增/启停任何 capability · 零 SSE 帧改动 · 零新表/迁移/新 env。
6. **不泄露内部实现（SPEC 纪律 #4）**：`manifest_error_details[].error` 透出的是 ManifestError 消息（含文件 path · manifest 注释已钉无密钥字段）；`adapter`/`local_fn:` 子串不出站存续。
7. **鉴权不动**：catalog 仍 `AdminSyncAuth`；用户面 B1 端点不涉本 task；admin `items` 全字段数组（13 字段族 + status 三态）归 B2 主 task，本 task 不动。

## 范围

- **F1 故障记录持久化**：manifest.py 模块级故障记录（`load_capability_manifests` failed 集落存 · reload 成功清除该文件记录 · 钉死契约 3）。
- **F2 catalog 透出**：`GET /api/ops/admin/capability/catalog` 响应增 `manifest_errors` + `manifest_error_details`（路由只读透传 · N4 落点 A）。
- **F3 hidden 附 visibility_reason**：summary `visibility_hidden` 各条目增 `visibility_reason` 文本子键（映射表落 visibility.py · 钉死契约 4）。
- **F4 测试断言化**（TC1–TC5 · 故障注入红测先行）。
- **F5 图谱判定回写**：预判 n/a 照实写；实证触发则 capability 行备注 + HG-GRAPH-MODULES 代录。
- **F6 invoke 留档**（10/20/30/40 按 required_invoke_hats）。

### 非范围

- ❌ admin `items` 全字段数组 / `status` 三态投影（归 B2 主 task · 本 task 只在既有 summary.hidden 面上增子键）。
- ❌ B1 用户态端点 `/capability/mine`（兄弟 task）。
- ❌ manifest 加载/校验/reload 语义改动 · 失败域隔离改动 · 自动热加载（manifest.py:17-19 禁令存续）。
- ❌ `/runtime` 响应面与 `get_capability_manifest_metadata` 键集改动（钉死契约 2）。
- ❌ capability 注册/修改/启停/删除 · 执行面/编排面/委派令牌面任何改动。
- ❌ 新 SSE 事件 / freeze 契约改动 · 前端任何改动（F1 专项 SPEC 另立）。

## failure_paths

| 编号 | 失败路径 | 处置 |
|---|---|---|
| — | HG-TASK-DRAFT/HG-AUDIT-R1/HG-GRAPH-MODULES pending 即 30 | 拒开工（闸表 pending 不代签） |
| FP-1 | 故障注入污染全局注册表/故障记录影响其他测试 | 测试隔离：注入用 tmp_path 坏 manifest + 显式恢复（注入后重载好 manifest 清零故障记录）· fixture 收尾还原 · 禁跨用例泄漏 |
| FP-2 | 故障记录语义与 reload 生命周期不一致（重启前故障记录残留误导） | 钉死契约 3 语义断言：reload 成功后该文件记录清除 · TC4 覆盖 |
| FP-3 | 响应增键破坏既有调用方/多副本对拍 | TC2 既有键逐键零 diff；tests/test_multi_replica_dualproc.py:674-718 catalog parity 亲跑（新键跨副本一致性：同 manifest 集 → 同故障记录） |
| FP-4 | visibility_reason 文本与 reason 码漂移出第二真源 | 映射表单源落 visibility.py · TC3 与 `evaluate_visibility` 直出对拍 · 路由层零重算走查拒收 |
| FP-5 | error 文本泄露内部装配/密钥 | ManifestError 消息现状仅含 path+校验原因（无密钥 · _reject_secret_keys 加载期已拦）；TC1 断言 details 不含 `local_fn:`/`adapter` 子串 |
| FP-6 | `get_capability_manifest_metadata` 被顺手扩键（落点跑偏成 B） | 钉死契约 2 + tests/test_capability_manifest.py:331/:354 原样绿机断 |

## B1 · 旧测影响面

| 测试文件 | 关系 | 预期 |
|---|---|---|
| tests/test_admin_capability_observability.py | catalog 端点五测试（:54 鉴权 · :113 hidden 解释 · :149 kinds 裁剪 · :173 filter · :185 deny_write） | 原样绿；:113 hidden 断言面若逐键精确则需对齐增 `visibility_reason` 子键并留痕（只增） |
| tests/test_capability_manifest.py | :331/:354 `get_capability_manifest_metadata` 断言 | 原样绿（钉死契约 2 · meta 面零 diff） |
| tests/test_capability_manifest_http.py | :409-435 `load_capability_manifests` 失败域隔离/重复 id | 原样绿（加载语义零改动）；故障记录持久化新增断言另起用例不动既有 |
| tests/test_multi_replica_dualproc.py | :674-718 runtime/catalog 跨副本 parity | 亲跑绿（FP-3 · 新键跨副本一致） |
| tests/test_capability_visibility_and_receipts.py | :135 visibility 求值面 | 原样绿（求值语义零改动 · 只增映射表） |

## 验收标准

- [x] **TC1 故障注入可观测**（30 实证：test_admin_capability_manifest_errors.py::test_tc1 ✅）：tmp 坏 manifest（非法 YAML/非法字段）经 `load_capability_manifests` 注入 → `GET /api/ops/admin/capability/catalog` 响应 `manifest_errors >= 1` 且 `manifest_error_details` 含该 path + error 摘要；details 不含 `adapter`/`local_fn:` 子串（FP-5）；既有键逐键零 diff。
- [x] **TC2 零故障基线**（30 实证：test_tc2 snapshot 直出逐键对拍 ✅）：默认装配 catalog 响应 `manifest_errors == 0` · `manifest_error_details == []` · 既有键（filter/principal/visible_ids/visibility_*）逐键对拍零 diff（SPEC FP-4）。
- [x] **TC3 visibility_reason 钉源**（30 实证：test_tc3 词表钉源+直出对拍 ✅）：fixture manifest 含 visibility 受限条目 + 受限 principal 查询 → hidden 条目附 `visibility_reason` 文本且与 `evaluate_visibility` 直出 reason 码一一对应；路由层零过滤/零重算（走查 + 单测对拍求值函数直出）。
- [x] **TC4 失败域隔离与生命周期存续**（30 实证：test_tc4 隔离+reload 清记录+meta 两键零 diff ✅）：坏文件不带崩好文件（manifest.py:14-15 语义 · test_capability_manifest_http.py:413 面存续）；reload 该文件成功后其故障记录清除（钉死契约 3）；`get_capability_manifest_metadata` 两键零 diff（钉死契约 2）。
- [x] **TC5 工程面**：pytest 全绿（仓级基线钉案照登 · 零新增红）· ruff 触及路径零新增 · graph-compile EXIT=0 · `npx spec-wave task lint` PASS · 三闸 approved 后才 30。（30 实证：全量 1653 passed · 4 failed 全基线同现同败——hitl asyncpg/memory_vector_p1 环境存量 + multi_replica hitl 两枚 stash/HEAD~1 复跑同败 · ruff 触及路径 2 错基线同现零新增 · lint-imports 12 kept 0 broken · graph-compile EXIT=0 · lint/verify PASS）

## 依赖

- SPEC：`docs/spec/tool-catalog-page/SPEC-tool-catalog-page_v0.md`（§2 B2 · §5 FP-3/FP-4 · §6 B2 · 纪律 #2/#3/#4 · HG-SPEC-SIGNOFF approved）。
- R1 审查：`docs/harness/reviews/spec_tool-catalog-page_audit_R1_20261011.md`（N4 落点 · N1 锚点修正 :163-214 · N5 编号警示）。
- 码面：`app/ops/capability/manifest.py` · `app/ops/capability/visibility.py` · `app/ops/capability/gateway.py:133-143` · `app/ops/admin/capability.py:163-214`。
- 编码规范：仓内 coding standards（L2_backend bar）。

## 给执行帽的必读列表

1. SPEC v0 §2 B2 + §5 + §6 B2 + §1 设计纪律（docs/spec/tool-catalog-page/SPEC-tool-catalog-page_v0.md）。
2. R1 审查 N1/N4/N5（docs/harness/reviews/spec_tool-catalog-page_audit_R1_20261011.md）——**N5：Q4「方案2」系承前批编号勿误读为本文 Q4 S2**。
3. `app/ops/capability/manifest.py` :102-147（`_LAST_META` + metadata getter）· :175-217（load_capability_manifests / reload）。
4. `app/ops/capability/visibility.py` 全文（:38-41 词表 · :112-135 evaluate_visibility · :126 hidden reason）。
5. `app/ops/admin/capability.py` :163-214（catalog · R1 N1 修正锚点）+ :99（meta 消费方 · N4 弃选 B 证据）。
6. B1 表列测试文件（尤其 test_admin_capability_observability.py:113 与 test_multi_replica_dualproc.py:674-718）。

## 思考轮控制

| 轮 | 结论 | early_stop | reason（early_stop） | residual_risks |
|---|---|---|---|---|
| R0 | 问题框定：manifest 故障仅日志（:200）· failed 集即弃（__init__.py:110）· 端点面不可观测 | false | — | 故障记录生命周期语义未定 |
| R1 | 证据收集：SPEC §2 B2/FP-3 + R1 C15/N4 + 码面六锚点亲读（meta 消费方 :99 = 落点 B 爆炸半径证据） | false | — | — |
| R2 | 方案生成：落点 A summary 增键 vs 落点 B 扩 meta 面 → **裁 A**（SPEC 首选语序 + 单端点 diff + meta 双消费方牵连 + 断言单点） | false | — | 记录结构细节留 30 |
| R3 | 反例/边界：注入污染隔离 · reload 生命周期 · 多副本 parity · reason 文本双真源 · meta 面跑偏 | false | — | B1 :113 断言对齐量待 30 实证 |
| R4 | 收敛：改动面锁 manifest.py 故障记录 + admin/capability.py catalog 透出 + visibility.py 映射表 · 钉死契约七条 | false | — | 图谱判定为预判 |
| R5 | 收口：TC1–TC5 全可机断 + failure_paths + B1 表 + 三闸 pending 不代签 · N4 裁定留痕 | true | 范围/非范围/验收/failure_paths/锚点齐备 · N4 裁一闭合 · 再轮无新增信息 | 故障记录结构细节待 30 钉（刻意开放） |

**actual_last_round**：R5（early_stop）

### R0 · 问题框定

SPEC 缺口 #5：manifest 加载失败静默缺条目。实证链：失败仅 `logger.error`（manifest.py:200）→ failed 集随 `MultiManifestLoadResult` 在启动期调用点（`__init__.py:110`）被丢弃 → 端点面只有 version+count（:145-147）→ 总表缺条目不可观测。本 task = B2 故障可见性子面收口。

### R1 · 证据收集

SPEC §2 B2 :78「summary 增 manifest_errors 计数键（或沿用既有 meta 面 · 实现 task 裁定落点）」+ R1 N4 原文 + 码面亲读六锚点。关键新证：`get_capability_manifest_metadata` 被 `/runtime`（admin/capability.py:99）消费且 tests/test_capability_manifest.py:331/:354 钉其键集——落点 B 爆炸半径实证大于落点 A。

### R2 · 方案生成（N4 裁定）

落点 A（summary 面增键）vs 落点 B（扩 meta 面）。**裁 A**：①SPEC 语序首选；②A 响应 diff 收敛 catalog 单端点，B 牵连 /runtime 双端点 + meta 断言面；③与 visibility_* 平铺外形一致；④故障注入断言单点机断。数据落 manifest.py 模块级记录（两案共同前提），出站长路由只读透传。

### R3 · 反例与边界

- 注入隔离：tmp manifest + 收尾还原，禁跨用例泄漏（FP-1）。
- 生命周期：reload 成功清除该文件记录，禁止无理由自动清零（钉死契约 3 · FP-2）。
- 多副本 parity：同 manifest 集 → 同故障记录（FP-3 · dualproc 亲跑）。
- 双真源防：reason→文本映射表单源落 visibility.py，路由层零重算（FP-4 · SPEC 纪律 #3）。
- 落点跑偏防：meta 面零 diff 机断（FP-6）。

### R4 · 收敛

改动面锁三文件：manifest.py（故障记录持久化）+ admin/capability.py（catalog 透出两键）+ visibility.py（reason→文本映射表 + hidden 条目增子键）；测试面 TC1–TC5。图谱预判 n/a 照实写。非范围六条显式排除（items 数组归 B2 主 task · B1 端点兄弟 task · meta 面 · 加载语义 · SSE · 前端）。

### R5 · 收口

范围 F1–F6、非范围六条、failure_paths FP-1~FP-6+闸行、B1 五文件表、验收五条全可机断；N4 裁定留痕（落点 A）；三人工闸 pending 不代签；结构对齐 task_hitl_auto_resume_claim_race 先例。裁定收口，early_stop at R5。

### 自检结论（10 起草者）

1. **范围对 SPEC 无溢出**：本 task 只做 B2 故障可见性子面（manifest_errors 透出 + hidden 附 visibility_reason）；admin items 全字段数组、B1 用户态端点显式归兄弟 task（非范围节钉死），与 SPEC §2 B2 验收逐项对应可机断。
2. **N4 裁一闭合**：落点 A（summary 面增键）裁定留痕，弃 B 理由有码面实证（meta 双消费方 app/ops/admin/capability.py:99 + tests/test_capability_manifest.py:331/:354 断言面）。
3. **实证锚点六处亲读**（manifest.py:200/:145-147 · __init__.py:110 · admin/capability.py:99/:163-214 · visibility.py:126）与 R1 C15/N1/N4 一致；无凭记忆引码。
4. **三闸 pending 未代签**；freeze 零动；graph 预判 n/a 照实写（条件回写义务在案）。
5. **lint 形态**：对齐 task_hitl_auto_resume_claim_race 先例（元信息表/人工闸表/钉死契约/TC 组/思考轮控制表头）。

## 修订

| 日期 | 说明 |
|------|------|
| 2026-10-11 | 30 开工前格式归一 + NIT 消化：人工闸表转 4 列 canonical（status 纯值 · 闸真值不变 · fec3abf 在案不动）——原 3 列 + 状态格内嵌说明致 `spec-wave verify` 解析 0 行误报 BLOCKED · NIT-1 契约 4 引「SPEC 纪律 #3/#6」删「/#6」（实为 #3+FP-6）· NIT-2 B1 表锚 :413-435→:409-435（失败域隔离用例实起 :409） |
| 2026-10-11 | 10 落稿：SPEC §2 B2 + R1 N4 携带回填 · **N4 裁定落点 A（summary 面增 `manifest_errors`/`manifest_error_details` · 弃 B：meta 双消费方爆炸半径）** · 实证锚点六处亲读（:200 故障日志 · :145-147 meta 仅 version+count · __init__.py:110 返回值即弃 · :99 meta 消费方 · visibility.py:126 reason · catalog :163-214）· 钉死契约七条 · TC1–TC5 · 三人工闸 pending（未代签） |
