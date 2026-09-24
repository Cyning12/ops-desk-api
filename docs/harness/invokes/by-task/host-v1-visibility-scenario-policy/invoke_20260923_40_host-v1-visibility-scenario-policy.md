# Invoke · 40（核验 + PR + CLOSE）· host-v1-visibility-scenario-policy（V1-B 波）

> **日期**：2026-09-23  
> **帽**：00（40 独立复核收口）  
> **PR**：[#181](https://github.com/Cyning12/ops-desk-api/pull/181) **MERGED**（CI 三绿：check · lint-wiki-delta · pytest · merge commit 8aecab9 · 2026-09-23）

## 40 核验结论（00 独立复核 · 全真跑）

| 面 | 证据 | 结论 |
|---|---|---|
| 全量 pytest | 1460 collected（+40 · 零既有删除）· 1307 passed / 11 failed / 142 skipped | **11 红全部基线环境性**：本地 PG 5432 未起；detached worktree @ master + 同 .env 复跑同 11 挂（lg_rag_http×4 · session_continuity×3 · sse_resume×1 · react_observe×3）；CI（有 PG）pytest **pass** 印证 |
| 新用例 | test_strategy_scenario.py 19 + test_capability_reversibility.py 21 = 40 | 全绿 ✅ |
| ruff | 改动文件 9 errors 与 master 同数 | 净增 0 ✅ |
| graph-compile | worktree 内 exit 0 | 绿 ✅ |
| alembic | 迁移 diff 为空 | 零义务成立 ✅ |
| 变异检验 | 30 回报三条「破坏→必挂→恢复绿」（d9e28b2 提交说明） | 3/3 ✅ |
| diff 白名单 | 10 文件（scenario.py/intent.py/state.py/builder.py/nodes.py/types.py/manifest.py/builtin.v1.yaml/两测试文件） | 全在名单 ✅ |
| B-1 落点 | Builder 内 scenario_trim 收窄 allowlist → supervisor 交集传导（nodes.py 注释对齐语义零改）· delegation_scope 不越场景维断言（test_supervisor_delegation_scope_never_exceeds_scenario_trim） | SPEC R1 澄清落实 ✅ |

## 图谱回写（HG-GRAPH-MODULES · 00 代录）

`docs/_tech_graph/l1/01_modules.md`：`capability` 行备注（manifest 四字段+三硬规则+三档派生）· `lg_rag` 行备注（scenario_trim 场景维 stage 2+剔除台账+intent_fallback channel · 三重交集钉死）· 人签记录新行 **approved · 00 代录**（维护者令原话+本窗双令留痕）；**不新增一级模块** · 零新跨模块边 · 不增 implementedBy。

## CLOSE

task 状态 done · 归档 `docs/tasks/done/` · Hub 补登 · CLOSE 走分支 PR（承 #172/#180 先例）。**V1-B CLOSE · 可停稳态**；V1-C/D 在轨并行 · V1-E 最后。

## 修订

| 日期 | 说明 |
|---|---|
| 2026-09-23 | 40 棒 invoke 落盘（核验全绿 · PR #181 MERGED · CLOSE 归档） |
