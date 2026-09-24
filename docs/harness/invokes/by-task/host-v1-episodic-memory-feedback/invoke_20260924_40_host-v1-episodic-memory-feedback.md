# Invoke · 40（核验 + PR）· host-v1-episodic-memory-feedback（V1-D）

> **日期**：2026-09-24  
> **帽**：40（**00 委派子 Agent** · 00 本窗未改 `app/`；图谱人签行已由 00 代录 `approved`）  
> **前置**：30-resume 收口（[V1-D 30-resume 收口](7c27abf6-c067-421f-b607-0789aa54fcaf) · commits `d4bc8d7`/`fec4f63`/`0c5b787`/`0a0e5bb` + 00 代录签 commit）  
> **工作目录**：`/private/tmp/opsdesk-wt-v1d` · 分支 `task/host-v1-episodic-memory-feedback`  
> **PR**：[https://github.com/Cyning12/ops-desk-api/pull/184](https://github.com/Cyning12/ops-desk-api/pull/184) **MERGED**（merge `669e76a` · 2026-09-24T02:29:49Z · squash tip `97f2352`；本 invoke 修订随 docs 跟进 PR 入 master · **CLOSE 留给 00**）

## 40 必做

1. **独立核验**（不采信 30 口号）：新增三测全绿 · B1 相关回归抽核 · `ruff check app tests` 净增 0（对照 master）· `./scripts/graph-compile.sh` 绿 · alembic upgrade/downgrade 可逆抽核 · diff 白名单对拍 task D6。
2. 变异检验：确认 30 三条「破坏→必挂→恢复」证据（commit message / 测试锚点）；缺则补跑留痕。
3. **push** `-u origin HEAD` + **`gh pr create`**（title/body 对齐 V1-A/C 风格 · 含验收/测试计划）。
4. 盯 CI 至绿；**不代 merge**（等待 auto-merge 或维护者）；若需 ENABLE auto-merge 可按仓先例。
5. 回写本 invoke：pytest/ruff/graph 摘要 · PR URL · CI 态。**CLOSE 归档留给 00**（merge 后）。

## 非做

- 不改业务语义 / 不扩非范围  
- 不归档 `done/`（00 CLOSE）  
- 不启动 V1-E

## 40 核验结论（独立 · 全真跑 · tip `97f2352`）

| 面 | 证据 | 结论 |
|---|---|---|
| GATE | HG-AUDIT-R1=approved · HG-GRAPH-MODULES=approved · `01_modules.md` 末行 V1-D 00 代录 approved | 可 40 ✅ |
| 新增三测 | `test_memory_episode_gate` / `test_memory_episode_recall` / `test_episode_pattern_mine` → **84 passed** | 全绿 ✅ |
| B1 抽核 | `test_memory_gate` + `test_memory_injection` + `test_memory_service_db` → **80 passed** | 全绿 ✅ |
| 全量 pytest | collected **1587**（master 1503 · **+84** 零删除）· **1574 passed / 0 failed / 1 skipped / 12 errors** | 12 ERROR 基线环境性（见下）✅ |
| 12 ERROR 实证 | `test_import_from_supabase`×3 + `test_multi_replica_dualproc`×9 · setup `ops_sessions.tenant_id` NOT NULL；**master + 同 .env 复跑同 12 ERROR** | 与本 diff 无关 ✅ |
| ruff | branch 57 errors = master archive 57 · **净增 0** | 净增 0 ✅ |
| graph-compile | `./scripts/graph-compile.sh` exit 0（仅 `generated_at` 时间戳漂移 · 已 restore 不入库） | 绿 ✅ |
| 白名单 | `app/`/`alembic/`/`scripts/`：episode_gate/episode_service 新增 · continuity · models · migration · episode_pattern_mine · 无越界 | 对拍 D6 ✅ |
| 变异检验 | commit `fec4f63` + 测试锚点①互写②闸恒放行③摘分节头 | 3/3 锚点 ✅ |

## CI 态

| check | 初态（PR 创建后） | 终态 |
|---|---|---|
| lint-wiki-delta | **pass** | **pass**（11s） |
| check（tech-graph） | pending | **pass**（16s） |
| pytest | pending / IN_PROGRESS | **pass**（1m26s · merge 后收齐） |

> 注：merge 时刻（02:29:49Z）pytest 仍 IN_PROGRESS；仓规则在 check+lint 绿后即 squash merge。pytest 终态随后 **pass**。

## 修订

| 日期 | 说明 |
|---|---|
| 2026-09-24 | 00 下发 40（图谱已 00 代录 approved · 委派核验+PR） |
| 2026-09-24 | 40 独立核验收口 · push · PR #184 **MERGED** · CI 三绿终态留痕 · invoke 修订 merge 后 docs 跟进 · **不做 CLOSE** |
