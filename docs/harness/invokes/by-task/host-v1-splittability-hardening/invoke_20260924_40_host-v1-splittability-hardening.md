# Invoke · 40（核验 + PR）· host-v1-splittability-hardening（V1-E）

> **日期**：2026-09-24  
> **帽**：40（**00 委派子 Agent**）  
> **前置 30**：[V1-E 30 实现收口](88d8c578-e399-4cf7-a51c-6881fee6de43) · tip `5bed0ae` / feat `41fca32`  
> **图谱**：HG-GRAPH-MODULES 人签行已 **00 代录 approved**  
> **工作目录**：`/private/tmp/opsdesk-wt-master40` · 分支 `task/host-v1-splittability-hardening`  
> **核验 tip**：`a1d8e98`（图谱 00 代录 + 本 invoke 初稿）· 本修订 commit 随后 push  
> **PR**：见修订表（创建后回填 URL）· **不做 CLOSE**

## 40 必做

1. `git pull` · 确认图谱人签为纯 `approved` · `npx spec-wave verify --task …` PASS  
2. **独立核验**（不采信 30）：  
   - `tests/test_splittability_hardening.py` 全绿  
   - `lint-imports` 12 kept / 0 broken  
   - ruff 净增 ≤0（对照 master）  
   - `graph-compile` 绿  
   - B1 相关抽核  
   - diff 白名单对拍 task  
3. **D1 dualproc 纪律（强制）**：`test_multi_replica_dualproc.py` 若仍 ERROR，须用 master+同 .env 实证为基线/fixture 漂移；**禁止**在 PR/验收中写成「双进程全绿」。对照 D5 FINDINGS #1（另开 `fix-multi-replica-dualproc-tenant-session` 建议保留）。GUIDE 补扫条目须在。  
4. push（若有 00 代录 commit）+ `gh pr create`（标题建议含 V1-E / splittability）  
5. 盯 CI；**不做 CLOSE**（留给 00）  
6. 回写本 invoke：摘要 · PR URL · CI · dualproc 结论口径

## 40 核验结论（独立 · tip `a1d8e98`）

| 面 | 证据 | 结论 |
|---|---|---|
| GATE | `npx spec-wave verify --task docs/tasks/active/task_host_v1_splittability_hardening.md` → **PASS**；HG-TASK-DRAFT / HG-AUDIT-R1 / HG-GRAPH-MODULES 均为 **approved** | 可 40 ✅ |
| D2 import-linter | `lint-imports` → **Contracts: 12 kept, 0 broken** | 全绿 ✅ |
| D3/D4 硬化测 | `pytest tests/test_splittability_hardening.py` → **7 passed**（含变异①②③锚点） | 全绿 ✅ |
| D1 GUIDE 补扫 | `GUIDE_process_local_state_boundaries_v1.md` 条目 **9–11**（delegation nonce / llm budget / infer_cache）存在 | 已落 ✅ |
| D1 dualproc | 本分支：`test_multi_replica_dualproc.py` → **9 ERROR**（setup `ops_sessions.tenant_id` NOT NULL）；**master `ff3cfbe` + 同 `.env` 复跑同形 9 ERROR** | **环境/fixture 漂移**（非本 diff 引入）· **禁止写「双进程全绿」** · 对齐 D5 FINDINGS #1 · 建议另开 `fix-multi-replica-dualproc-tenant-session` |
| D5 | `docs/reports/host_v1_splittability_hardening/FINDINGS_open_elsewhere_v1.md` #1 open | 另开建议保留 ✅ |
| ruff | branch **56** errors · master archive **57** · **净增 −1 ≤0** | 净增 ≤0 ✅ |
| graph-compile | `./scripts/graph-compile.sh` exit 0（仅 `generated_at` 时间戳漂移 · 已 restore 不入库） | 绿 ✅ |
| 白名单 | `git diff master --name-only` **27** 文件；均落 task 白名单（`app/ops/capability/` · `app/llm/` · `.importlinter` · deps · workflows · `tests/` · `docs/` · `reports/` · `.env.example`）；**无** checkpointer/resume/alembic 越界 | 对拍 ✅ |

### dualproc 口径（强制 · 交 00 / PR）

- **不得**声称「双进程全绿 / D1 双进程回归 PASS」。  
- 正确表述：D1 **边界清单补扫 9–11 已落**；双进程用例 **环境红 BLOCKED**（fixture 未写 `tenant_id` · 阶段 T 后 schema NOT NULL）；**master+同 env 实证同红** → 归 D5 FINDINGS #1，建议另开 `fix-multi-replica-dualproc-tenant-session`。  
- 报告真值：`reports/multi_replica_verify/REGRESSION_host_v1_splittability_hardening_20260924.md`（BLOCKED-ENV）。

## CI 态

| check | 初态（PR 创建后） | 终态 |
|---|---|---|
| （PR 创建后回填） | pending | — |

## 修订

| 日期 | 说明 |
|---|---|
| 2026-09-24 | 00 下发 40（图谱已代录 · dualproc 红须如实标注） |
| 2026-09-24 | 40 独立核验 PASS（D2–D5 / ruff≤0 / graph / 白名单）· dualproc 9 ERROR 经 master+同.env 实证为基线漂移 · PR 创建中 · **不做 CLOSE** |
