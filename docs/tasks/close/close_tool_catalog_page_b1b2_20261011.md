# CLOSE：tool-catalog-page B1+B2（capability-mine-endpoint + catalog-manifest-errors-surface）（2026-10-11）

> **task**：[../done/task_capability_mine_endpoint.md](../done/task_capability_mine_endpoint.md)（B1 · 已归档 done/）· [../done/task_catalog_manifest_errors_surface.md](../done/task_catalog_manifest_errors_surface.md)（B2 · 已归档 done/）
> **类型**：SPEC 拆分实现双 task（tool-catalog-page v0 §2 B1/B2 · 后端观测面 · 同分支同 PR 编排）
> **关账日期**：2026-10-11 · 帽位：CLOSE（双 task 合一档）

---

## 一 · 任务信息

| 项 | 值 |
|----|----|
| task_slug | `capability-mine-endpoint`（B1）· `catalog-manifest-errors-surface`（B2） |
| 依据 | `docs/spec/tool-catalog-page/SPEC-tool-catalog-page_v0.md`（**signed** · HG-SPEC-SIGNOFF approved 2026-10-11 · 00 代录 fb85675 · 授权 m01606 · 状态行 draft→signed 本 CLOSE 回写）· 20-spec-audit R1 `docs/harness/reviews/spec_tool-catalog-page_audit_R1_20261011.md`（PASS-WITH-NITS · N1–N5 拆 task 携带回填） |
| B1 目标 | 用户态只读端点 `GET /api/ops/capability/mine`——当前登录用户可见能力列表（字段族九键白名单 + `{items, count}` 外形 · 只回可见集防探测 · 空集 200 如实 · 零写零执行语义改动） |
| B2 目标 | catalog 故障可见性——顶层增 `manifest_errors`/`manifest_error_details`（坏 manifest 从静默到可观测 · details 按 path 排序）+ hidden 条目附 `visibility_reason` 中文映射（既有键零 diff · 纯只读） |
| B1 帽链 | 10 落稿（ba4a078/7c47ecd）→ 闸表 4 列契约（389e0d5）→ 10 invoke（fc9885e）→ 20-task-audit R1 BLOCKER（2440949 · B-1 lint E5 缺自检结论节）→ B-1 修订（f6c041f）→ R2 PASS（daa6871）→ 三闸 approved（00 代录 · 授权 m01606/m00255）→ 闸表机读归一（863260c）→ 审查文址A 复制（826b2ff）→ 30 红测先行 e30b7ca（6 红）→ 实现 f79fe3f → 30 invoke+自检回填（9aed10e）→ 40 核验 PASS（788b9fe）→ PR #231 → CLOSE |
| B2 帽链 | 10 落稿（a778c13 · N4 裁落点 A）→ 20-task-audit R1 PASS-WITH-NITS（c3d5e57 · 锚点 14 组全核真 · NIT-1~3 照登）→ 三闸 approved（00 代录 · 同上授权）→ 闸表机读归一+NIT 消化（2bf0bd1）→ 30 红测先行 520425f（TC1-TC4）→ 实现 2a2503d（.importlinter 补边系 00 裁定授权）→ 30 invoke+自检回填（7c9bc8d）→ 30 接管棒收尾复验+ruff 计数订正（42803fc）→ 40 核验 PASS（fa10905）→ PR #231 → CLOSE |

## 二 · 交付

| 环节 | 实证 |
|------|------|
| PR | [#231](https://github.com/Cyning12/ops-desk-api/pull/231) · **MERGED · squash commit `a7d748b`**（mergedAt 2026-10-11T02:05:06Z · CI 绿 · 双 task 同 PR） |
| B1 码面 | `app/ops/capability_mine.py`（新端点模块 · 落 `app/ops/` 包外守「capability 包内禁挂 APIRouter」禁令）+ `app/ops/router.py` 一行注册 + `tests/test_capability_mine.py`（TC1-TC6 六枚 · 红测先行 6 红→6 绿时序在案）· `docs/_tech_graph/l1/01_modules.md` api 行注册备注回写 + HG-GRAPH-MODULES 随交付签录 |
| B2 码面 | `app/ops/capability/manifest.py`（错误态留存含首次失败+修复 pop · load/reload 统一）+ `app/ops/admin/capability.py`（catalog 透出两键 · meta 面零 diff）+ `app/ops/capability/visibility.py`（reason→文本映射表词表四码 + 未知码原样兜底 + hidden 增子键）+ `tests/test_capability_manifest_errors.py`（TC1-TC4 · 红测先行）· `.importlinter` 白名单补 manifest 边（00 裁定授权 · 无环实判） |
| 钉死契约 | B1 八条全落地（40 diff 复核+live 双证）：落点包外 · CurrentUser 401 · principal 会话构造 · 可见性单源路由层零过滤 · 精确九键+status 常量 · 防探测空集 200 · 只读零写 · baseline_filter 不叠加（FP-8 裁定）；B2 七条全落地：catalog 顶层增两键 · 既有键零 diff · 错误态留存 · hidden 增 visibility_reason · .importlinter 补边无环 · 零 schema/迁移/env |
| invokes | `docs/harness/invokes/by-task/capability-mine-endpoint/`（10/20_r1/20_r2/30/40 五件）· `docs/harness/invokes/by-task/catalog-manifest-errors-surface/`（10/20_r1/30/40 四件）· `docs/harness/invokes/by-task/tool-catalog-page/`（20_spec_audit_r1 + 本 CLOSE 补 50） |
| **CLOSE 增量** | 双 task 归档 done/（状态行 done + 修订表 CLOSED 行回填）· 审查文址A 复制件**30 期已先行**（826b2ff · 序2 教训前置吸收 · 本 CLOSE 复跑 verify 实证门禁消费）· SPEC 状态行 draft→signed 回写 · active/done README 双侧补登 · 本档 + 50 invoke 落盘 |

## 三 · 核验结论（40 双 PASS · 独立复核不轻信自述）

双 task 40 核验均 **PASS**（详见 [B1 40 invoke](../../harness/invokes/by-task/capability-mine-endpoint/invoke_20261011_40_verify.md) · [B2 40 invoke](../../harness/invokes/by-task/catalog-manifest-errors-surface/invoke_20261011_40_verify.md)）：

- **契约复核**：B1 钉死契约八条逐条 ✅（diff fec3abf...HEAD 对拍 + live 双证）；B2 钉死契约七条逐条 ✅（同口径）。
- **工程面（双 task 同口径亲跑）**：全量 pytest 1653 passed/1 skipped/4 failed（4 红基线 `/tmp/base-fec3abf` 逐枚同败 → **零新增红独立实证**）· ruff 2 errors（I001+UP034）与基线同码区 · lint-imports 12 kept 0 broken · graph-compile EXIT=0（npm ci 钉版 spec-wave 3.0.1 后 · 3.2.0 漂移照录不 merge master）· spec-wave verify/task lint 双 PASS。
- **B1 live 冒烟五场景全绿**（uvicorn :8070 `OPS_DESK_SECRET=verify40-secret` + curl）：未登录 401 · maintainer count=5 精确九键 adapter 零命中 · viewer ⊆ maintainer 真子集 · departments:[finance] 限定条目 fail-closed 不出站 · B1/B2 共存零互扰。
- **B2 live 冒烟五场景全绿**（同环境）：坏 manifest 注入 `manifest_errors=1` details 精确点名 path · `visibility_reason` 中文映射「部门不在该能力的可见范围内」真实出站 · /runtime meta 仍两键回归 · viewer 403/匿名 401 · B1 共存零互扰。

**CLOSE 质量钉复跑（本帽 · 归档后仓态 · CI 同版 spec-wave@3.0.1 · 重定向取真码）**：

- `npx --yes spec-wave@3.0.1 verify --target . > /tmp/close_verify_tool_catalog.txt 2>&1; echo EXIT=$?` → **EXIT=0 · VERIFY: PASS**（挪档 done/ 后零新增缺口 · 址A 复制件供门禁消费 · 序2 教训已前置吸收）。
- `npx --yes spec-wave@3.0.1 task lint --file docs/tasks/done/task_capability_mine_endpoint.md` → **EXIT=0 · LINT: PASS**（done/ 路径复跑）。
- `npx --yes spec-wave@3.0.1 task lint --file docs/tasks/done/task_catalog_manifest_errors_surface.md` → **EXIT=0 · LINT: PASS**（done/ 路径复跑）。

## 四 · 偏差与 nit（如实照登）

1. **B1 R1 BLOCKER 偏差（已闭合）**：20-task-audit R1（2440949）判 BLOCKER——B-1 lint E5 缺自检结论节退 10（内容面 C1-C12 全过）；10 修订 f6c041f 补自检结论节+n-1/n-2 回填 → R2 PASS（daa6871 · f6c041f diff 零越界亲核）。R2 残留 nit r-n1（f6c041f 未在修订表补行）已随后续修订表回填闭合。
2. **B2 R1 NIT 处置分账**：NIT-1（契约 4 引「SPEC 纪律 #3/#6」删「/#6」· 实为 #3+FP-6）与 NIT-2（B1 表锚 :413-435→:409-435）均随 30 开工前格式归一 commit 2bf0bd1 消化闭合；NIT-3（观察：:331/:354 系逐键值断言非键集相等）照登不阻——对拍口径偏强不偏弱，留后续如需强化键集相等断言另议。
3. **ruff 计数/口径订正（B2 30 棒 42803fc + 40 棒订正注）**：30 首记 2 errors 漏 UP038 两枚（实 4）→ 收尾复验订正；40 进一步实证 **ruff 0.15.21 已移除 UP038 规则**，实存 2 errors（I001+UP034）与基线 fec3abf 同码区 —— 计数漂移全程如实留痕，零新增结论不变。
4. **graph-compile 上游漂移照录**：spec-wave 3.2.0 上游漂移致 graph-compile 不稳 · 钉版 3.0.1（npm ci）后 EXIT=0 · CI 已钉 3.0.1（lint-wiki-delta.yml 在案）· 不为漂移 merge master。
5. **全量 4 failed = 基线环境性**：/tmp/base-fec3abf 临时 worktree 复跑逐枚同败（环境敏感存量红）→ 归因零新增红成立（双 task 40 各自独立实证）。
6. **审查文双址过渡（序2 教训前置吸收）**：B1 R1/R2 + B2 R1 审查文址A 复制件系 **30 期 826b2ff 先行复制**（非本 CLOSE 补落）——档头注来源址B 原件路径 · diff 源档仅多 2 行复制说明 · 内容逐字零改动；本 CLOSE 复跑 verify EXIT=0 实证门禁消费无碍。址B 原件原址原内容不动。
7. **SPEC 状态行漏回写（本 CLOSE 修正）**：HG-SPEC-SIGNOFF approved（fb85675 00 代录）早已落闸表，惟 SPEC 状态行滞留 `draft`——本 CLOSE 回写 `signed` 并补修订记录行（零语义改动）。

## 五 · 签录（闸与审查文链）

| 环节 | 文档 / 实证 |
|------|------------|
| SPEC 闸 | HG-SPEC-SIGNOFF **approved**（2026-10-11 · 00 代录 fb85675 · 授权 m01606 · 依据 R1 PASS-WITH-NITS）· SPEC 状态行 signed 本 CLOSE 回写 |
| B1 人工闸 | HG-TASK-DRAFT / HG-AUDIT-R1 / HG-GRAPH-MODULES 三闸 **approved**（2026-10-11 · 维护者授权 m01606/m00255 · 00 代录 · task 人工闸表为真值 · HG-GRAPH-MODULES 随 30 交付回填 modules.md api 行备注）· HG-PILOT-OPSDESK-GLAYER n/a |
| B2 人工闸 | HG-TASK-DRAFT / HG-AUDIT-R1 / HG-GRAPH-MODULES 三闸 **approved**（同上授权链 · 图谱实判维持 n/a）· HG-PILOT-OPSDESK-GLAYER n/a |
| B1 20 审查 | R1 址B 原件 `docs/audits/task-review/20261011_capability-mine-endpoint_r1.md`（BLOCKER 退修订 · B-1 lint E5）· R2 址B 原件 `docs/audits/task-review/20261011_capability-mine-endpoint_r2.md`（**PASS** · B-1 闭合）· 址A 复制件 `docs/harness/reviews/task_capability_mine_endpoint_audit_R{1,2}_20261011.md`（826b2ff 先行 · verify 按最高 R 轮消费 R2） |
| B2 20 审查 | R1 址B 原件 `docs/audits/task-review/20261011_catalog-manifest-errors-surface_r1.md`（**PASS-WITH-NITS** · 锚点 14 组全核真 · N4 落点 A 裁定成立）· 址A 复制件 `docs/harness/reviews/task_catalog_manifest_errors_surface_audit_R1_20261011.md`（826b2ff 同批） |
| invokes | B1：`by-task/capability-mine-endpoint/`（10/20_r1/20_r2/30/40）· B2：`by-task/catalog-manifest-errors-surface/`（10/20_r1/30/40）· 共享：`by-task/tool-catalog-page/`（20_spec_audit_r1/50_close 本档同落） |
| 合并 | PR [#231](https://github.com/Cyning12/ops-desk-api/pull/231) MERGED 2026-10-11T02:05:06Z · squash `a7d748b9e4994dc030771331c0368a6fc7466796` · CI 绿 |

## 六 · 资源清理

- **已清**：本 CLOSE 工作区仅本档所述 diff（git status 干净 · `.venv` untracked 存量不动）。
- **待清（留 00/维护者统一清理）**：worktree `t-tool-catalog-page` 与本地/远端分支 `task/tool-catalog-page`、`close/tool-catalog-page`——本 CLOSE 在该 worktree 内作业无法自清，且 CLOSE PR 未合并前 close 分支在役；**CLOSE PR 合并后**：`git worktree remove` + 删除两条分支（task 分支已 squash 合入 master `a7d748b` · 删除安全 · 远端分支一并清）。
- 先例对照：repo-logging-init / specwave-verify-baseline 各 CLOSE 均将 worktree/分支清理移交 00（active README 登记表在案）· 本件同口径。

## 七 · 维护者验收 checklist 与后续建议

### 维护者验收 checklist（m01606 令③ · 需人重新验收项）

- [ ] **B1 可见集差异 + 九键白名单**：以 maintainer 与 viewer 两账号分别调 `GET /api/ops/capability/mine`，亲验 viewer 可见集 ⊆ maintainer（departments 限定条目对 viewer fail-closed 不出站）· 每条 item 精确九键（id/name/description/when_to_use/risk_level/side_effect/enabled/status/adapter 族 · adapter 不外泄）。复跑口径：[B1 40 invoke live 冒烟节](../../harness/invokes/by-task/capability-mine-endpoint/invoke_20261011_40_verify.md)（uvicorn :8070 `OPS_DESK_SECRET=verify40-secret` 起服 + curl · 仓内无独立冒烟脚本 · 场景命令逐条在案）。
- [ ] **B2 坏 manifest 注入点名**：注入一枚坏 manifest（YAML 语法错/缺必填键均可）→ 重调 admin catalog 端点，亲验顶层 `manifest_errors=1` 且 `manifest_error_details` 精确点名该 path · 既有键零 diff · hidden 条目 `visibility_reason` 中文映射真实出站。复跑口径：[B2 40 invoke live 冒烟节](../../harness/invokes/by-task/catalog-manifest-errors-surface/invoke_20261011_40_verify.md)（同环境 · 坏 manifest 注入与恢复步骤在案）。
- [ ] **共存零互扰抽验**：同一会话内连调 mine + catalog + /runtime 三端点，确认 B1/B2 共存零互扰、/runtime meta 仍两键（双 40 invoke 场景五均在案）。

### 后续建议

1. **前端 F1 专项 SPEC（SPEC 既定下游）**：`ops-desk-web` 仓工具列表页 · 依据本 SPEC §2 F1 概要 + B1/B2 契约面（mine 九键 + catalog manifest_errors/visibility_reason）——承 chat-history-hitl-ux Q4 同款分仓纪律。
2. **admin items 全字段数组（B2 显式非范围）**：SPEC §2 B2 的 admin 总表 items 扩充面本 task 未做（非范围节钉死 · 归后续 task）——若维护者仍需要请另立 task。
3. **B2 NIT-3 观察项跟进（可选）**：tests/test_capability_manifest.py:331/:354 系逐键值断言非键集相等 —— 如需键集相等强度断言可另立测试补强小 task。
4. **冒烟脚本化（可选）**：双 40 invoke 的 :8070 live 冒烟目前只有 invoke 文档口径无独立脚本（scripts/ grep 实证零命中）——若验收期需反复复跑，建议固化为 scripts/ 下冒烟脚本。

## 八 · 修订记录

| 日期 | 说明 |
|------|------|
| 2026-10-11 | CLOSE 落稿（CLOSE 棒 · worktree `t-tool-catalog-page` · 分支 `close/tool-catalog-page` · base origin/master `dd60384`）：双 task 合一档九节沿仓内先例（repo-logging-init / specwave-verify-baseline）· 质量钉复跑（verify EXIT=0 PASS · task lint 双档 PASS · spec-wave@3.0.1 CI 同版 · 重定向取真码）后回填 · 审查文址A 复制件 826b2ff 先行实证 · SPEC 状态行 signed 回写 |

## 九 · 附录

### 关键路径

| 类别 | 路径 |
|------|------|
| SPEC | `docs/spec/tool-catalog-page/SPEC-tool-catalog-page_v0.md`（signed · 闸表 :27 · 状态行 :4） |
| B1 交付码面 | `app/ops/capability_mine.py` · `app/ops/router.py`（注册行）· `tests/test_capability_mine.py` |
| B2 交付码面 | `app/ops/capability/manifest.py` · `app/ops/admin/capability.py` · `app/ops/capability/visibility.py` · `tests/test_capability_manifest_errors.py` · `.importlinter` |
| 审查文（址B 原件） | `docs/audits/task-review/20261011_capability-mine-endpoint_r1.md` · `..._r2.md` · `docs/audits/task-review/20261011_catalog-manifest-errors-surface_r1.md` |
| 审查文（址A 复制件） | `docs/harness/reviews/task_capability_mine_endpoint_audit_R1_20261011.md` · `..._R2_20261011.md` · `docs/harness/reviews/task_catalog_manifest_errors_surface_audit_R1_20261011.md`（826b2ff 先行 · 档头注址B 原件路径） |
| invokes | `docs/harness/invokes/by-task/capability-mine-endpoint/`（10/20r1/20r2/30/40）· `docs/harness/invokes/by-task/catalog-manifest-errors-surface/`（10/20r1/30/40）· `docs/harness/invokes/by-task/tool-catalog-page/`（20_spec_audit_r1/50_close） |
| 图谱回写 | `docs/_tech_graph/l1/01_modules.md`（api 行 2026-10-11 注册备注 · HG-GRAPH-MODULES 签录行） |

### B1/B2 交付 commit 链（摘）

- SPEC 段：c3fdb68→e1a7a64→b26005d→8ebca08（20-spec-audit R1）→ fb85675（HG-SPEC-SIGNOFF 00 代录）
- B1：ba4a078/7c47ecd（落稿）→ 389e0d5（闸表 4 列）→ fc9885e（10 invoke）→ 2440949（R1 BLOCKER）→ f6c041f（B-1 修订）→ daa6871（R2 PASS）→ 863260c（闸表机读归一）→ 826b2ff（审查文址A 复制）→ e30b7ca（红测 6 红）→ f79fe3f（实现）→ 9aed10e（30 invoke+自检回填）→ 788b9fe（40 PASS）
- B2：a778c13（落稿）→ c3d5e57（R1 PASS-WITH-NITS）→ 2bf0bd1（机读归一+NIT 消化）→ 520425f（红测 TC1-TC4）→ 2a2503d（实现）→ 7c9bc8d（30 invoke+自检回填）→ 42803fc（收尾复验+ruff 订正）→ fa10905（40 PASS）
- 合并：PR #231 squash `a7d748b`（2026-10-11T02:05:06Z）

### CLOSE 复跑命令留痕

```bash
npx --yes spec-wave@3.0.1 verify --target . > /tmp/close_verify_tool_catalog.txt 2>&1; echo "EXIT=$?"   # EXIT=0 · VERIFY: PASS
npx --yes spec-wave@3.0.1 task lint --file docs/tasks/done/task_capability_mine_endpoint.md          # EXIT=0 · LINT: PASS
npx --yes spec-wave@3.0.1 task lint --file docs/tasks/done/task_catalog_manifest_errors_surface.md   # EXIT=0 · LINT: PASS
```
