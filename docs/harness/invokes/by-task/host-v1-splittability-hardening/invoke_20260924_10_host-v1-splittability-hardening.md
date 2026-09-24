# Invoke · 10-task · host-v1-splittability-hardening（V1-E · 收尾波）

> **日期**：2026-09-24  
> **帽**：10-task（00 委派 · 隔离 worktree · 分支 `task/host-v1-splittability-hardening` @ master `ff3cfbe`+）  
> **维护者令（原话留痕 · 闸代录口径预留）**：「签收，并生成对此长程任务的00启动Prompt，新窗口执行，授权00签收所有过程文档，完整落地1.0版本内容」·「继续，完成后自行进行下一波，无特殊情况无需停下等待接收命令」  
> **SPEC**：`docs/spec/host-v1-splittability-hardening/SPEC-host-v1-splittability-hardening_v0.md`（**signed** · HG-SPEC-SIGNOFF 00 代录 2026-09-23）  
> **task**：`docs/tasks/active/task_host_v1_splittability_hardening.md`（draft · HG-TASK-DRAFT **pending** 00 代录位预留 · HG-AUDIT-R1 **pending**）  
> **前置**：V1-A~D 全 CLOSE（#186）· multi-replica-verify 已 CLOSE（#165 · D1 承继）

## 必读（按序 · 已读）

1. `AGENTS.md` / 10-task skill ✓  
2. SPEC `host-v1-splittability-hardening` 全文（§2 D* / §3 / §4 Q1–Q2 / §5 FP / §6）✓  
3. `SPEC-multi-replica-verify_v1.md`（D1 原样）✓  
4. 格式基准 `task_host_v1_episodic_memory_feedback.md`（done）✓  
5. `CODING_BACKEND_L2_v1_zh.md`（依赖声明）✓  
6. **真读** `docs/_tech_graph/l1/01_modules.md`（签录至 V1-D · 出边列=import contracts 真值）✓  
7. 既有 D1 产物：`GUIDE_process_local_state_boundaries_v1.md`（确认缺 V1-A~D 新状态）· `test_multi_replica_dualproc.py` ✓

## 开放裁定（SPEC §4 · 不重演 · 锁死入 task）

| Q | 裁定 |
|---|---|
| Q1 import 闸工具 | **import-linter**（自研弃） |
| Q2 策略包 | **YAML schema v0 + 单面试点** · 优先级 env>策略包>代码默认（全量搬家弃） |

**铁律**：硬化≠重构 · 对拍零 diff · 验证≠投产（发现即另开）· D1 **承继** #165 不重写基建 · **无 alembic** · 零 freeze。

## D1 承继口径（本棒关键裁定留痕）

`task_multi_replica_verify` 已 CLOSE（PR #165）。本波 D1 ≠ 重做：映射 multi-replica §6 验收，实施=双进程回归绿 + 边界清单补扫（delegation nonce / llm budget / infer_cache）+ runbook/报告可复核 + 变异三条可机跑 + app/ 验证轨零生产码。

## 30 前置闸

| 闸 | 状态 |
|---|---|
| HG-TASK-DRAFT | **pending**（00 代录位预留 · 本帽不签） |
| HG-AUDIT-R1 | **pending** → **30 拒开工**（本帽不签） |
| HG-GRAPH-MODULES | approved（真读 · 预期无新签按实判） |
| 分支 | `task/host-v1-splittability-hardening` |

## 实扫留痕（摘要）

- 命名冲突：`RegistryReader`/`RegistryWriter`/`.importlinter`/`strategy_pack` → **零命中**
- 边界清单：V1-C/D 进程内项 **未入** GUIDE（补扫义务钉死）
- B1：capability≈168 / llm≈87 / dualproc=9 / hitl≈62 / strategy≈39 methods；处置以回归为主、改编预期零
- 基线：承 V1-D CLOSE **1587 collected**（本 worktree `.venv` 缺 pytest · collect 未本机展开 · 30/40 复核）

## lint

`npx spec-wave task lint --file docs/tasks/active/task_host_v1_splittability_hardening.md` = **PASS**（exit 0 · 2026-09-24 真跑 · CLI 拉起 spec-wave 3.0.2）

## 下一棒

**20-task-audit** 书面审 → 00 代录 HG-TASK-DRAFT + HG-AUDIT-R1 → 30 委派（序 D2→D3→D4→D1→D5）· **禁止本窗 30**。

## 修订

| 日期 | 说明 |
|---|---|
| 2026-09-24 | 10-task 落稿 invoke：D1 承继口径 · 闸表 pending/pending · B1 实扫 · 可交 20 |
