# CLOSE：b2-nit3-admin-items-array（admin catalog items 全字段数组 + NIT-3 meta 键集相等断言补强）（2026-10-11）

> **task**：[../done/task_b2_nit3_admin_items_array.md](../done/task_b2_nit3_admin_items_array.md)（已归档 done/ · 状态行 CLOSED 回写 · W3 自检结论回填）
> **类型**：SPEC 拆分实现 task（tool-catalog-page §2 B2 显式非范围回收 · 观测面补强 · 纯只读 · 零执行语义改动）+ 测试断言补强小面（NIT-3）
> **关账日期**：2026-10-11 · 帽位：CLOSE（50 · 最小包 ②③ · 维护者令「开始」· 授权链 m00106 00 代录签收过程文档）

---

## 一 · 任务信息

| 项 | 值 |
|----|----|
| task_slug | `b2_nit3_admin_items_array` |
| 依据 | SPEC `docs/spec/tool-catalog-page/SPEC-tool-catalog-page_v0.md` §2 B2（items 数组钉案 :75-78）+ §5 FP-4/FP-5/FP-6 + §6 B2 验收（HG-SPEC-SIGNOFF approved 2026-10-11）· CLOSE 档 `docs/tasks/close/close_tool_catalog_page_b1b2_20261011.md` §7 后续建议第 2/3 条（本 task 承接 · 第 1/4 条入非范围） |
| 目标 | admin 总表从「id 列表 + 摘要」扩成全字段总表：`GET /api/ops/admin/capability/catalog` 增顶层 `items` 数组（每个在册 capability 一条 · 含被裁与 disabled 条目 · 14 键字段族 + status 三态 + visibility_reason）；NIT-3 落成机断（meta 断言逐键值 → 键集相等）· 纯只读零执行语义改动 |
| 分支 / worktree | `task/b2-nit3-admin-items-array`（worktree `t-b2-nit3-admin-items-array` · 自立分支） |
| 帽链 | 10 落稿（R2 裁定 items 数据源 S1 全量在册 = disabled 三态唯一可达路径）→ 20-task-audit R1 **PASS-WITH-NITS**（C1–C12 ✅ · nit n-1 键集/缺省表述张力留 30 二选一消歧）→ 三闸 approved（00 代录 · 授权 m00106）→ 30 红测先行（RED TC1/TC2/TC3 `KeyError: 'items'` → GREEN 11 件全绿）+ 验收矩阵全过 + 30 invoke 落盘（W3 自检结论占位符留 close 棒回填义务在案）→ PR #241 → CLOSE（本档 · W3 回填 + 归档 + 址B 复制件） |

## 二 · 交付

| 环节 | 实证 |
|------|------|
| PR | [#241](https://github.com/Cyning12/ops-desk-api/pull/241) · **MERGED 2026-10-11T05:56:25Z · squash commit `4d2dd22`**（交付 commit `11645a6` · CI 绿） |
| 码面 | `app/ops/admin/capability.py`（增 `_project_catalog_item(spec, hidden)` 14 键精确投影 + catalog 路由顶层 `items` 键：`get_registry().list_specs()` 全量在册 → `evaluate_visibility(specs, principal)` hidden 按 id 索引 → 逐条投影按 id 排序）· `tests/test_admin_capability_catalog_items.py`（新 · TC1–TC4）· `tests/test_capability_manifest.py`（NIT-3 键集相等 · :334/:359）· `tests/test_admin_capability_manifest_errors.py`（TC2 键面并集增 `"items"` 预期内涟漪） |
| 钉死契约落地 | 七条全落地（30 invoke 验收矩阵）：①只增不删既有键逐键零 diff（TC2）②items 恒全量在册不受 baseline/query 裁剪（TC2 三组组合）③status 三态（disabled 优先判定承 registry.py:120 首判语义 · TC3 三探针）④可见性单源（denied 复用包顶 `evaluate_visibility` hidden 条目 · 路由层零重算）⑤14 键精确键集相等 + adapter/args_schema 不出站（TC1/TC4 双保险）⑥NIT-3 键集相等在前 + 原断言存续 + 被测面零 diff（TC5）⑦只读零写鉴权不动（AdminSyncAuth 存续 · B1 mine 零改动） |
| invokes | `docs/harness/invokes/by-task/b2_nit3_admin_items_array/`（10_task_draft / 20_task_audit_r1 / 30_implementation 三件 · 本 CLOSE 补 50 于 `by-task/close_b2_and_specwave330/`） |
| **CLOSE 增量** | task 档归档 done/（状态行 CLOSED + W3 自检结论回填 + 修订记录 CLOSED 行）· R1 审查文址B 复制件 `docs/audits/task-review/20261011_b2-nit3-admin-items-array_r1.md` 落盘（址A 原件不动 · 双址规约 §二 过渡期口径）· active README 登记表补登 · 本档 + 50 invoke 落盘 |

## 三 · 核验结论（验收终态摘要 · 承 30 验收矩阵实证）

30 验收矩阵（[30 invoke](../../harness/invokes/by-task/b2_nit3_admin_items_array/invoke_20261011_30_implementation.md) · 交付 commit `11645a6`）：

| 验收项 | 结果 | 实证 |
|--------|------|------|
| TC1 items 全覆盖 + 字段族 | ✅ | 长度 == 全量在册数（含 disabled/被裁）· 每条目 14 键精确键集相等 · denied 对拍 `evaluate_visibility` 直出 · **恒出键 None**（nit n-1 裁定①钉死） |
| TC2 既有键零 diff | ✅ | 既有 10 键在场 + `capability_catalog_snapshot` 直出逐键对拍 + 三组 query 下覆盖集不变 |
| TC3 三态可分辨 | ✅ | register/unregister try/finally 三探针 disabled / denied:department_mismatch / visible 同现 · disabled 不在 visible_ids 不附 reason |
| TC4 防泄露 | ✅ | 响应体禁 `adapter`/`local_fn:`/`args_schema`/`secret_param`/`PROBE_BASE_URL` 子串 |
| TC5 NIT-3 键集相等 | ✅ | :334/:359 两处 `set(meta.keys()) == {"version","capability_manifest_count"}` 在前 + 原逐键值存续 · 实现零 diff |
| TC6 工程面 | ✅ | pytest 全量 **1787 passed / 6 failed 六红逐项钉案全环境性**（三件主仓基线同红 · 三件 worktree 缺 `.env` SILICONFLOW_API_KEY 带主仓 .env 复跑全绿）· ruff check 三改动文件 All checks passed · lint-imports 12 kept 0 broken · graph-compile EXIT=0（噪音已还原）· task lint PASS |
| 红测时序 | ✅ | RED（TC1/TC2/TC3 `KeyError: 'items'`）→ GREEN（11 件全绿）· TC4 空转绿/TC5 基线即绿照实录 |
| dualproc parity | ✅ | `test_runtime_scope_and_catalog_parity` 绿（items 不入对拍面符合既有契约） |

**CLOSE 质量钉复跑（本帽 · 归档后仓态 · 重定向取真码）**：

- 改动前基线：`npx --yes spec-wave verify --target . > /tmp/verify_close_baseline.log 2>&1; echo EXIT=$?` → **EXIT=0 · VERIFY: PASS**（spec-wave 3.3.0 · 93 存量豁免命中留痕）。
- 归档后复跑：`npx --yes spec-wave verify --target . > /tmp/verify_close.log 2>&1; echo EXIT=$?` → **EXIT=0 · VERIFY: PASS**（本 task 址A 审查文在案供门禁消费 · 挪档 done/ 后自身零缺口；同批归档的 specwave_330 无 R1 审查文曾报 `missing R<n> review` 一枚，已按其 CLOSE 档 §三 的豁免扩列处置后 PASS · 详见 `close_specwave_330_graph_update_20261011.md`）。
- `npx --yes spec-wave task lint --file docs/tasks/done/task_b2_nit3_admin_items_array.md` → **EXIT=0 · LINT: PASS**（W3 占位符已回填 · 提醒消除）。

## 四 · 偏差与 nit（如实照登）

1. **nit n-1 闭合（R1 留 30 二选一消歧）**：30 裁定选 **①visibility_reason 恒出键（非 denied = `None`）**——保 14 键全条目键集相等，与钉死契约 5「键集精确」表述自洽（R1 推荐项）· TC1 恒出键断言钉死 · 本 CLOSE 记入。
2. **F811×4 未修（分支基线既有）**：`tests/test_capability_manifest.py` :468/:476/:554/:581 被 :523/:531/:597/:624 重定义——git stash 实证分支基线 HEAD 同挂 · 30 未动 · 留评估另案（见 §七后续建议）。
3. **ruff format 分支基线漂移未修**：`capability.py`/`test_capability_manifest.py` format --check 未过，hunk 全落 30 棒未触既有行（:78/:96/:229/:310 等）· 主仓锁版 ruff 0.15.21 基线同挂这两文件 → 非本 task 引入 · 遵「勿当回归修」未修 · 留评估另案。
4. **实现裁定留痕（绕 import 契约）**：初版直导 `app.ops.capability.visibility` 被 admin-outbound forbidden 契约拦（lint-imports 白名单不覆盖 · splittability D2 双用例红）→ 改走包顶 `evaluate_visibility` hidden 条目（`__init__.py:101` 已导出 · 码+文本一体单源更彻底）· 零契约改动零公共面扩张。
5. **预期内涟漪照登**：`tests/test_admin_capability_manifest_errors.py` TC2 键面并集增 `"items"`（items 系本 task 交付的新增顶层键 · 既有键逐键零 diff 断言 :104 未动）。
6. **环境坑留痕（worktree 冷启动 · 30 invoke 全集）**：worktree 无 venv 须 `uv pip install -r requirements.txt` + `-e ".[dev]"` · 测试须 `uv run python -m pytest`（裸 pytest 命中 venv 外 9.1.1 炸 asyncpg）· `.env` 不随 worktree 分发 · git stash pop 部分应用坑。
7. **W3 自检结论占位符（本 CLOSE 闭合）**：30 invoke 明示「W3 自检结论占位符待 close 棒回填」· task lint W3 提醒 draft 期合法 —— 本 CLOSE 已回填（task 档自检结论节 · 实证承 30 invoke 验收矩阵）。

## 五 · 签录（闸态表与审查文链）

| 闸 / 环节 | 状态 | 文档 / 实证 |
|-----------|------|------------|
| HG-TASK-DRAFT | **approved** | 00 代录（授权 m00106 · 2026-10-11）· task 人工闸表为真值 |
| HG-AUDIT-R1 | **approved** | 00 代录（授权 m00106）· 依据 R1 PASS-WITH-NITS |
| HG-GRAPH-MODULES | **approved** | 00 代录（授权 m00106）· 预判 n/a 复核通过（modules.md :34/:38 既有行备注覆盖 · R1 亲核属实 · 条件回写义务未触发：无新 env/机制面） |
| HG-PILOT-OPSDESK-GLAYER | n/a | 无外部试点面 |
| 20 R1 审查 | **PASS-WITH-NITS** | 址A 原件 `docs/harness/reviews/task_b2_nit3_admin_items_array_audit_R1_20261011.md`（C1–C12 ✅ · nit n-1 照登）· 址B 复制件 `docs/audits/task-review/20261011_b2-nit3-admin-items-array_r1.md`（**本 CLOSE 落** · 档头 2 行复制说明 · 正文逐字一致 · 址A 原件不动） |
| invokes | — | `by-task/b2_nit3_admin_items_array/`（10/20_r1/30）· 50_close 落 `by-task/close_b2_and_specwave330/` |
| 合并 | **MERGED** | PR [#241](https://github.com/Cyning12/ops-desk-api/pull/241) · squash `4d2dd22e7bc0190c9b62d7938cb92a3825b6a17c` · 2026-10-11T05:56:25Z · CI 绿 |

## 六 · 资源清理

- **本 CLOSE 不删任何东西**：worktree `t-b2-nit3-admin-items-array` 与本地/远端分支 `task/b2-nit3-admin-items-array`、`docs/close-b2-and-specwave330` **移交 00/维护者统一清理**——CLOSE PR 未合并前 close 分支在役；**CLOSE PR 合并后**：`git worktree remove` + 删除分支（task 分支已 squash 合入 master `4d2dd22` · 删除安全 · 远端一并清）。
- 先例对照：repo-logging-init / hitl-approved-replan-quality / tool-catalog-page 各 CLOSE 均将 worktree/分支清理移交 00（active README 登记表在案）· 本件同口径。

## 七 · 维护者验收 checklist 与后续建议

### 维护者验收 checklist（00 代录 · 授权 m00106 · 需人重新验收项）

- [ ] **items 全字段出站抽验**：调 `GET /api/ops/admin/capability/catalog`（AdminSyncAuth），亲验顶层 `items` 每条目精确 14 键（id/kind/description/when_to_use/when_not_to_use/tags/risk_level/side_effect/enabled/tenant_scoped/reversible/execution_type/status/visibility_reason）· 非 denied 条目 `visibility_reason` 恒出键为 `null`（nit n-1 裁定①）· 响应体不含 `adapter`/`local_fn:`/`args_schema` 子串。复跑口径：[30 invoke](../../harness/invokes/by-task/b2_nit3_admin_items_array/invoke_20261011_30_implementation.md) 验收矩阵（仓内无独立冒烟脚本 · TC1–TC4 测试断言在 `tests/test_admin_capability_catalog_items.py`）。
- [ ] **三态分辨抽验**：items 中 `disabled`（enabled:false）/`denied:<原因码>`/`visible` 三态语义与 manifest/visibility 配置一致 · disabled 条目不在 `visible_ids` 且不附 reason。
- [ ] **既有键零 diff 回归**：catalog 既有键（filter/principal/visible_ids/visibility_*/manifest_errors/manifest_error_details）与升级前一致 · `/runtime` meta 仍两键（version/capability_manifest_count）。
- [ ] **NIT-3 断言强度抽验**：`tests/test_capability_manifest.py` :334/:359 两处键集相等断言在前 + 原逐键值存续 · `get_capability_manifest_metadata` 实现零 diff。

### 后续建议

1. **F811×4 + ruff format 基线漂移评估另案**：tests/test_capability_manifest.py 四枚重定义（:468/:476/:554/:581 ← :523/:531/:597/:624）与两文件 format 漂移均分支基线既有、本 task 未修 —— 建议另立测试卫生小 task 统一收口（修前须先钉口径：重定义是否覆盖语义有意）。
2. **前端 F1 专项 SPEC（SPEC 既定下游 · 承上案 close 档）**：`ops-desk-web` 仓工具列表页 —— B1 mine 九键 + catalog items 14 键契约面现已齐备，立项条件成熟（承 chat-history-hitl-ux Q4 分仓纪律）。
3. **冒烟脚本化（可选 · 承上案 close 档第 4 条）**：admin 观测面验收目前只有 invoke 文档口径无独立脚本 —— 如需反复复跑建议固化 scripts/ 冒烟脚本。

## 八 · 修订记录

| 日期 | 说明 |
|------|------|
| 2026-10-11 | CLOSE 落稿（50 close 棒 · worktree `t-close-b2-330` · 分支 `docs/close-b2-and-specwave330` · base master `92a8526`）：九节沿仓内先例（tool-catalog-page / hitl-approved-replan-quality CLOSE 文档）· W3 自检结论回填（30 invoke 验收矩阵承录 · nit n-1 裁定①记入）· 质量钉复跑（verify 改动前基线 EXIT=0 PASS → 归档后 EXIT=0 PASS · task lint done/ 档 PASS · spec-wave 3.3.0 · 重定向取真码）· R1 审查文址B 复制件落盘（址A 原件不动）· 维护者 checklist 00 代录（授权 m00106） |

## 九 · 附录

### 关键路径

| 类别 | 路径 |
|------|------|
| task（已归档） | `docs/tasks/done/task_b2_nit3_admin_items_array.md`（状态行 CLOSED · 自检结论已回填） |
| SPEC | `docs/spec/tool-catalog-page/SPEC-tool-catalog-page_v0.md`（§2 B2 :75-78 · §5 FP-4/FP-5/FP-6） |
| 交付码面 | `app/ops/admin/capability.py`（`_project_catalog_item` + catalog `items` 键）· `tests/test_admin_capability_catalog_items.py` · `tests/test_capability_manifest.py`（:334/:359）· `tests/test_admin_capability_manifest_errors.py` |
| 审查文（址A 原件） | `docs/harness/reviews/task_b2_nit3_admin_items_array_audit_R1_20261011.md` |
| 审查文（址B 复制件） | `docs/audits/task-review/20261011_b2-nit3-admin-items-array_r1.md`（本 CLOSE 落） |
| invokes | `docs/harness/invokes/by-task/b2_nit3_admin_items_array/`（10/20_r1/30）· `by-task/close_b2_and_specwave330/`（50_close） |
| 双址规约 | `docs/harness/CONVENTION_review_gate_dual_address_v1_zh.md`（§二 过渡期口径） |

### CLOSE 复跑命令留痕

```bash
npx --yes spec-wave verify --target . > /tmp/verify_close_baseline.log 2>&1; echo "EXIT=$?"   # 改动前基线 EXIT=0 · VERIFY: PASS
npx --yes spec-wave verify --target . > /tmp/verify_close.log 2>&1; echo "EXIT=$?"           # 归档后 EXIT=0 · VERIFY: PASS（specwave_330 豁免扩列处置后 · 见其 CLOSE 档 §三）
npx --yes spec-wave task lint --file docs/tasks/done/task_b2_nit3_admin_items_array.md       # EXIT=0 · LINT: PASS
```
