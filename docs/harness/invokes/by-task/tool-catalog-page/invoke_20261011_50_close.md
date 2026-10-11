---
hat: 50
task_slug: tool-catalog-page
date: 2026-10-11
---

# invoke · 50+CLOSE · tool-catalog-page（B1 capability-mine-endpoint + B2 catalog-manifest-errors-surface 双 task 合一 CLOSE）

## 收口结论

- B1 链路全通：10 落稿（ba4a078/7c47ecd）→ 20-task-audit R1 BLOCKER（2440949 · B-1 lint E5 缺自检结论节）→ B-1 修订 f6c041f → R2 PASS（daa6871 · r-n1 残留 nit 已随修订表回填闭合）→ 三闸 approved（维护者授权 m01606/m00255 · 00 代录）→ 闸表机读归一 863260c → 审查文址A 复制 826b2ff → 30 红测先行 e30b7ca（6 红）→ 实现 f79fe3f → 30 invoke+自检回填 9aed10e → 40 核验 PASS（788b9fe · 契约八条全✅ · live 冒烟五场景）。
- B2 链路全通：10 落稿（a778c13 · N4 裁落点 A）→ 20-task-audit R1 PASS-WITH-NITS（c3d5e57 · 锚点 14 组全核真 · NIT-1/2 随 2bf0bd1 消化 · NIT-3 照登）→ 三闸 approved（同上授权链）→ 30 红测先行 520425f → 实现 2a2503d（.importlinter 补边系 00 裁定授权）→ 30 invoke+自检回填 7c9bc8d → 接管棒收尾复验+ruff 计数订正 42803fc → 40 核验 PASS（fa10905 · 契约七条全✅ · live 冒烟五场景）。
- PR [#231](https://github.com/Cyning12/ops-desk-api/pull/231)：MERGED 2026-10-11T02:05:06Z · squash `a7d748b` · CI 绿（双 task 同 PR）。
- 归档：双 task → done/（头部状态 done · 修订表 CLOSED 行）；active README 登记表补行；done README Hub engineering 域表双行+修订记录行补登；CLOSE 文档 `docs/tasks/close/close_tool_catalog_page_b1b2_20261011.md` 落盘（维护者验收 checklist 在第七节）。
- SPEC 状态行 draft→signed 回写（HG-SPEC-SIGNOFF approved fb85675 已在闸表 · 仅状态行漏回写 · 零语义改动 + 修订记录行补登）。
- 双址过渡：审查文 B1 R1/R2 + B2 R1 址A 复制件系 **30 期 826b2ff 先行复制**（序2 教训前置吸收 · 档头注址B 原件路径 · 内容逐字零改动）——本 CLOSE 复跑 verify EXIT=0 实证门禁消费无碍 · 址B 原件不动。

## 交付摘要

| 项 | 内容 |
|---|---|
| **B1 产出** | `GET /api/ops/capability/mine` 用户态可见能力目录端点（`app/ops/capability_mine.py` 包外落点 · CurrentUser 401 · principal 会话构造 · evaluate_visibility 单源路由层零过滤 · 精确九键白名单 · 防探测空集 200）+ TC1-TC6 + modules.md 行备注回写 |
| **B2 产出** | catalog 顶层 `manifest_errors`/`manifest_error_details` 透出（按 path 排序 · 错误态留存含首次失败+修复 pop）+ hidden 附 `visibility_reason`（词表四码中文映射 · 未知码原样兜底）+ 既有键零 diff + TC1-TC4 |
| **验收** | 40 双 PASS：契约八条/七条 diff 复核全✅ · 工程面亲跑（全量 1653 passed/4 failed 基线逐枚同败零新增红 · ruff 2 errors 同码区 · lint-imports 0 broken · graph-compile EXIT=0 钉版 3.0.1）· live 冒烟双五场景全绿（uvicorn :8070 `OPS_DESK_SECRET=verify40-secret`） |
| **红线** | 零执行语义改动 · 纯只读 · 零 SSE 帧改动 · 零 schema/迁移/env（B2 .importlinter 补边系 00 裁定授权）· 钉死契约 8+7 条全落地 |

## 钉案登记（详见 CLOSE 文档第四节）

1. B1 R1 BLOCKER（B-1 lint E5 缺自检结论节）→ f6c041f 修订 → R2 PASS——过程偏差闭合 · r-n1（修订表补行）亦闭合。
2. B2 NIT-1（契约 4 引「#3/#6」删「/#6」）/NIT-2（锚 :413-435→:409-435）随 2bf0bd1 消化；NIT-3（:331/:354 逐键值断言非键集相等）照登留后续裁定。
3. ruff UP038 口径订正：ruff 0.15.21 已移除该规则（B2 30 棒 4 errors 漏记订正 → 40 实证 2 errors I001+UP034 与基线同码区）。
4. graph-compile 上游 3.2.0 漂移照录 · 钉版 3.0.1（npm ci）后 EXIT=0 · CI 已钉 3.0.1。
5. 审查文址A 复制件 826b2ff 先行（序2 教训前置吸收）—— CLOSE 帽新增归档必须址A 可机读审查文的增量门禁口径满足。

## 质量钉（CLOSE 机械闸复跑 · spec-wave@3.0.1 CI 同版 · 重定向取真码）

- 仓级 verify：`npx --yes spec-wave@3.0.1 verify --target . > /tmp/close_verify_tool_catalog.txt 2>&1; echo EXIT=$?` → **EXIT=0 · VERIFY: PASS**（挪档 done/ 后零新增缺口 · 址A 复制件供门禁消费）。
- task lint B1：`npx --yes spec-wave@3.0.1 task lint --file docs/tasks/done/task_capability_mine_endpoint.md` → **EXIT=0 · LINT: PASS**（done/ 路径复跑）。
- task lint B2：`npx --yes spec-wave@3.0.1 task lint --file docs/tasks/done/task_catalog_manifest_errors_surface.md` → **EXIT=0 · LINT: PASS**（done/ 路径复跑）。
- graph-compile：本 CLOSE 无图谱变更（B1 modules.md 回写随 30 交付已完成 · B2 graph_delta=n/a 实判维持）· n/a。

## 移交

- 维护者验收 checklist（m01606 令③需人重新验收项）在 CLOSE 文档第七节：B1 viewer/maintainer 可见集差异+九键白名单 · B2 坏 manifest 注入 manifest_errors 精确点名 · 复跑口径=双 40 invoke live 冒烟节（仓内无独立冒烟脚本）。
- 后续：前端 F1 专项 SPEC（ops-desk-web）· admin items 全字段数组另立 task · 冒烟脚本化可选。
- worktree `t-tool-catalog-page` 与分支 `task/tool-catalog-page`、`close/tool-catalog-page` 待 CLOSE PR 合并后由 00/维护者统一清理（本 CLOSE 在该 worktree 内作业无法自清 · CLOSE 文档第六节在案）。
