# Invoke：close_b2_and_specwave330 · 50_close（2026-10-11）

> **帽位**：50 CLOSE（最小包 ②③ · 维护者令 m00267「开始」· 授权链 m00106 00 代录签收过程文档）
> **工作隔离**：worktree `t-close-b2-330` · 分支 `docs/close-b2-and-specwave330`（base = master `92a8526`）· 主仓 checkout 未动
> **对象**：`b2_nit3_admin_items_array`（PR #241 MERGED · squash `4d2dd22`）+ `specwave_330_graph_update`（PR #242 MERGED · squash `92a8526`）
> **性质**：纯文档关账 · 零实现码改动

## 一 · 交付清单

| # | 交付物 | 路径 |
|---|--------|------|
| 1 | CLOSE 文档（b2） | `docs/tasks/close/close_b2_nit3_admin_items_array_20261011.md` |
| 2 | CLOSE 文档（specwave_330） | `docs/tasks/close/close_specwave_330_graph_update_20261011.md` |
| 3 | task 档归档 ×2（git mv active→done/ + 状态行 CLOSED + 修订记录 CLOSED 行） | `docs/tasks/done/task_b2_nit3_admin_items_array.md` · `docs/tasks/done/task_specwave_330_graph_update.md` |
| 4 | b2 task 档 W3 自检结论回填（30 棒遗留占位符 · 本 CLOSE 闭合） | `docs/tasks/done/task_b2_nit3_admin_items_array.md` 自检结论节 |
| 5 | R1 审查文址B 复制件（b2 · 双址规约 §二 过渡期口径 · 档头 2 行复制说明 · 址A 原件不动） | `docs/audits/task-review/20261011_b2-nit3-admin-items-array_r1.md` |
| 6 | active README 登记表补登两行（最新在最上） | `docs/tasks/active/README.md` |
| 7 | 本 invoke | 本档 |
| 8 | verify 豁免清单扩列一枚（specwave_330 归档后 `missing R<n> review` 缺口处置 · 四字段齐 · 扩列纪律承 `task_specwave_verify_baseline` 失败路径表第 4 行 · 本 CLOSE PR 即人审面 · 禁伪造审查故不补假 R1 档） | `docs/harness/legacy-gate-exempt.yaml` |

## 二 · 关键裁定与口径

1. **归档方式**：维护者指令字面为「git rm」，按仓内 CLOSE 先例（tool-catalog-page / hitl-approved-replan-quality / repo-logging-init 均 `git mv` 归档 done/）执行 **git mv active→done/** —— 偏离指令字面 · 承先例 · 已在 CLOSE 档与汇报中明示。
2. **W3 占位符回填（b2）**：30 invoke 明示「W3 自检结论占位符待 close 棒回填」· task lint W3 提醒 draft 期合法 —— 本 CLOSE 按 30 invoke 验收矩阵实证回填（红测时序 · nit n-1 裁定①恒出键 None · TC1-TC6 逐项 · 实现裁定 · F811×4/format 漂移遗留照登 · 注明 50 代录回填授权链 m00106）。
3. **nit n-1 闭合记入（b2）**：R1 留 30 二选一消歧 → 30 裁定选①visibility_reason 恒出键（非 denied = None）· 保 14 键全条目键集相等与「键集精确」自洽 · TC1 恒出键断言钉死 —— CLOSE 档 §四.1 记入。
4. **specwave_330 无 R1 审查文照录**：双址（址A reviews/ · 址B audits/task-review/）均无该 task 审查文 · 补录档口径「20 书面审由 task 档自检结论替代 · 维护者令直签 + PR 审兜底」—— CLOSE 档 §四.1 如实照录，无址B 复制件义务。
5. **CI 钉版不一致观察点照录禁擅改**：`package.json` 已钉 spec-wave 3.3.0，但 `scripts/graph-compile.sh:28`（`GRAPH_CLI=${GRAPH_CLI:-spec-wave@3.0.1}`）与 `.github/workflows/lint-wiki-delta.yml:35`（`npx --yes spec-wave@3.0.1`）仍钉 3.0.1 —— 事实照录入 CLOSE 档 §四观察点节，刻意或遗漏待维护者确认，本棒未擅改。
6. **verify-upstream 收口挂上游发版**：上游 issue #35/PR #36 已提 · `task_verify-upstream-dual-address` 仍 active（不在本 CLOSE 范围 · 照登）。
7. **维护者 checklist 00 代录**：两 CLOSE 档 §七 维护者验收 checklist 均 00 代录（授权链 m00106）· 需人重新验收项逐条列明。

## 三 · 质量钉复跑（重定向取真码）

```bash
# 改动前基线（worktree 干净态）
npx --yes spec-wave verify --target . > /tmp/verify_close_baseline.log 2>&1; echo EXIT=$?
# → EXIT=0 · VERIFY: PASS（spec-wave 3.3.0 · 93 存量豁免命中）

# 归档后首跑
npx --yes spec-wave verify --target . > /tmp/verify_close.log 2>&1; echo EXIT=$?
# → EXIT=2 · VERIFY: BLOCKED（缺口 1：done/task_specwave_330_graph_update.md · missing R<n> review
#   —— 归档 done/ 后入 reviews 扫描面 · 该 task 无 R1 审查文属补录档口径）
# 处置：legacy-gate-exempt.yaml 按扩列纪律新增一枚（slug specwave-330-graph-update · 四字段齐 ·
#   reason 如实注记「维护者直令兜底 · 无 R1 审查文」· 本 CLOSE PR 即人审面 · 禁伪造审查）
# 扩列后复跑 → EXIT=0 · VERIFY: PASS（94 豁免命中含本枚 · 0 invalid）

# task lint 两 done/ 档
npx --yes spec-wave task lint --file docs/tasks/done/task_b2_nit3_admin_items_array.md    # → EXIT=0 · LINT: PASS
npx --yes spec-wave task lint --file docs/tasks/done/task_specwave_330_graph_update.md     # → EXIT=0 · LINT: PASS
```

- graph-compile 未纳入本棒跑批（本棒零图谱面改动 · 若跑出产噪音一律 checkout 还原的纪律在案 · 未触发）。
- 终态 `git status` 干净（commit 后）· 零实现码改动（diff 全落 docs/ 与登记表）。

## 四 · 遗留与移交

| 项 | 归属 | 口径 |
|----|------|------|
| worktree `t-b2-nit3-admin-items-array` + 分支 `task/b2-nit3-admin-items-array` | 移交 00 统一清理 | CLOSE PR 合并后删（已 squash 合入 `4d2dd22` · 删除安全） |
| 分支 `task/specwave-330-graph-update` | 移交 00 统一清理 | CLOSE PR 合并后删（已 squash 合入 `92a8526` · 删除安全） |
| worktree `t-close-b2-330` + 分支 `docs/close-b2-and-specwave330` | 移交 00 统一清理 | CLOSE PR 合并后删 |
| b2：F811×4 + ruff format 分支基线漂移 | 评估另案 | CLOSE 档 §七后续建议第 1 条 |
| 330：CI 钉版不一致（graph-compile.sh:28 / lint-wiki-delta.yml:35 仍钉 3.0.1） | 待维护者确认刻意或遗漏 | CLOSE 档 §四观察点节照录 · 未擅改 |
| 330：verify-upstream 收口 | 挂上游发版（issue #35/PR #36） | `task_verify-upstream-dual-address` 仍 active |

## 五 · 修订记录

| 日期 | 说明 |
|------|------|
| 2026-10-11 | 50 CLOSE 落稿：九节结构沿仓内先例（亲读 `close_tool_catalog_page_b1b2_20261011.md` 与 `close_hitl_approved_replan_quality_20261011.md` 学结构）· 两 CLOSE 档 + 归档 + 址B 复制件 + README 补登 + 质量钉复跑全绿 |
