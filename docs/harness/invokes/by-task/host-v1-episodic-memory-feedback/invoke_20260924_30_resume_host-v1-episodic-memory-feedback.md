# Invoke · 30-resume（改码收口 · 00 委派）· host-v1-episodic-memory-feedback（V1-D）

> **日期**：2026-09-24  
> **帽**：30（**00 委派子 Agent** · 00 本窗未改 `app/`）  
> **闸态（真读 task 表）**：HG-TASK-DRAFT / HG-AUDIT-R1 / HG-GRAPH-MODULES 全 **approved** · `npx spec-wave verify --task …episodic…` **PASS**  
> **背景**：2026-09-23 已下发 30；worktree `/private/tmp/opsdesk-wt-v1d` 有 D1–D5 文件面 WIP，**零 commit**，分支相对 `master` **落后 12**（尚停在 V1-A 时代 tip），图谱备注未落。

## 30-resume 必做

1. **唯一工作目录**：`/private/tmp/opsdesk-wt-v1d`（分支 `task/host-v1-episodic-memory-feedback`）。主仓只读；禁 `master` 直改。
2. **先对齐 master**：`git fetch`（若需）+ `git merge origin/master`（或 rebase；保留全部 WIP）。冲突只解本波白名单面。
3. **对照 task 钉死契约收口 D1–D6**：
   - D1 迁移可逆 · off 态 drop 安全
   - D2 `episode_gate`/`episode_service` · U4 零互写 · 闸五判据含 class 词表合法 · import 守护
   - D3 continuity `[相似经验]` · 双开关默认关 · 三闸预算
   - D4 `scripts/episode_pattern_mine.py` · 频率≥3 · 确定性可重放
   - D5 建议面 · redlines/manifest **零自动回写**（git 守护）
   - D6 测试 + `docs/_tech_graph/l1/01_modules.md` memory/db 行备注 + HG-GRAPH-MODULES 人签新行（**占位写法留给 00 代录签** · 30 先落备注文）+ `graph-compile.sh` 绿 · 变异检验 3 条「破坏→必挂→恢复」
4. **验证**：主仓 venv `/Users/cyning/Desktop/Ops-desk/ops-desk-api/.venv/bin/python -m pytest …`；ruff 净增 0；B1 6+1 组回填；基线以 merge 后 collect 数为准如实记。
5. **交付**：本地 commit（可多 commit · 信息 `feat(memory): …`）；**不 push / 不开 PR**（40 棒做）。回写本 invoke 修订表：commit SHA · 新增用例数 · 已知红（环境性须实证）。

## 非范围红线（越任回炉）

零第二张表 · 零新路由/SSE · 不改 freeze · 不改事实记忆既有语义 · 无自动回写 redlines/manifest · 无实时聚类 · 无 subtask 级 · 无 embedding 聚类。

## 修订

| 日期 | 说明 |
|---|---|
| 2026-09-24 | 00 接手扫盘：WIP 未提交 + 落后 master → 委派 30-resume 收口 |
| 2026-09-24 | **30-resume 收口完成（本帽）**：merge master=`ffaa82e` fast-forward · 零冲突 · stash pop 净；D1–D6 齐；`graph-compile` 绿；ruff `app tests`=57（=master 净增 0）；三新增测文件 **84 collected / 84 passed**；B1 抽 `test_memory_gate`+`test_memory_injection`+`test_memory_service_db` **80 passed**；全量 collect **1587**（merge 后基线，含 V1-B/C）；变异①互写→断言挂（facts 1≠0）→恢复绿 · ②闸恒放行→DID NOT RAISE→恢复绿 · ③摘`[相似经验]`头→分节断言挂→恢复绿；HG-GRAPH-MODULES 人签行 **pending / 待 00 代录签**（memory/db 备注文已落）；**未 push / 未开 PR**。commits `d4bc8d7` / `fec4f63` / `39e7ace`。 |

### 交付 SHA / 核验摘要

| 项 | 值 |
|---|---|
| merge tip | `ffaa82e`（master） |
| feat commit | `d4bc8d7` |
| test commit | `fec4f63` |
| docs commit | `39e7ace` |
| collected 全量 | 1587 |
| 新增用例（三文件） | 84 |
| pytest 新增三文件 | 84 passed |
| B1 抽测 | 80 passed |
| ruff `app tests` | 57（净增 0 vs master） |
| graph-compile | 绿 |
| 变异①②③ | 破坏必挂 → 恢复绿 |
| 已知红 | 无（本机曾缺 PG/pgvector 属环境；起 brew postgresql@18 + `CREATE EXTENSION vector` 后 DB 段全绿） |
| 可交 40 | **Y**（阻塞：HG-GRAPH-MODULES 人签行待 00 代录 `pending→approved`；本帽未 push） |
