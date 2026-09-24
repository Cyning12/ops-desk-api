# Task：bugfix · dualproc `_create_user` 补 `ops_sessions.tenant_id`（fix-multi-replica-dualproc-tenant-session）

> **状态**：`active`（2026-09-24 · 10 落稿 · 闸全 **approved** 00 代录 · 30 可委派）  
> **类型**：**bugfix**（可跳独立 SPEC · 依据=V1-E D5 FINDINGS #1）  
> **依据**：`docs/reports/host_v1_splittability_hardening/FINDINGS_open_elsewhere_v1.md` #1 · V1-E CLOSE 遗留  
> **分支**：`fix/multi-replica-dualproc-tenant-session` · worktree `/private/tmp/opsdesk-wt-fix-dualproc`  
> **10 注**：2026-09-24 · 00 亲起（无初稿第一步）· 维护者长程授权延续代录闸

---

## Harness 元信息

| 字段 | 值 |
|------|-----|
| **task_slug** | `multi-replica-dualproc-tenant-session` |
| **git_branch** | `fix/multi-replica-dualproc-tenant-session` |
| **implement_repo** | `ops-desk-api` |
| **test_strategy** | `required` |
| **test_strategy_note** | `pytest tests/test_multi_replica_dualproc.py`：setup 不再因 `tenant_id` NOT NULL 9 ERROR；用例在本地有 PG 时绿或如实 skip；禁止改生产 `app/` 语义 |
| **code_quality_bar** | `L2_backend` |
| **graph_change_layer** | `none` |
| **graph_delta** | `n/a` |
| **graph_delta_note** | 测试基建 fixture · 无模块/契约改动 |
| **wiki_delta** | `n/a` |
| **wiki_delta_note** | 依据=FINDINGS #1 |
| **review_hat** | `20` |
| **required_invoke_hats** | `10,30,40` |
| **invoke_retention_profile** | `minimal` |
| **experience_capture** | `optional` |
| **kpi_aggregator** | `CLOSE` |
| **orchestration** | 10 → 00 代录闸 → 30（fixture）→ 40 → PR → CLOSE · 回写 FINDINGS #1=closed |
| **freeze_id** | 无 |

### 人工闸

| human_gate_id | status | blocks_hats | 说明 |
|---------------|--------|-------------|------|
| HG-TASK-DRAFT | **approved** | 20-R1, 30 | 2026-09-24 · **00 代录**（长程授权：「签收…授权00签收所有过程文档…」+「继续，完成后自行进行下一波」· 本令「开 fix dualproc tenant_id fixture」） |
| HG-AUDIT-R1 | **approved** | **30** | 2026-09-24 · **00 代录**（同令 · bugfix 单点 fixture · 范围钉死仅 tests · 零 app/ 生产改动预判） |
| HG-GRAPH-MODULES | **approved** | **30** | 2026-09-24 · 00 代录 · `graph_change_layer=none` |
| HG-PILOT-OPSDESK-GLAYER | n/a | — | 不涉 |

---

## 背景与目标

V1-E 双进程回归：`_create_user` 裸 SQL INSERT `ops_sessions` **未写 `tenant_id`**，而 ORM/库列为 `nullable=False`（默认 `ops-desk-pilot`，阶段 T 后）→ `NotNullViolationError` → **9 ERROR**。master+同 .env 同形（非本波假绿）。

一句话：fixture INSERT 补 `tenant_id`，与 `tests/dualproc_server.py` 使用的租户标识对齐（现网头为 `"dualproc"`），使 dualproc 套件可机跑；**零 `app/` 生产语义改动**。

---

## 现状锚点

| 主题 | 路径 | 现状 |
|------|------|------|
| 故障 | `tests/test_multi_replica_dualproc.py` `_create_user` ~:294-297 | INSERT 列无 `tenant_id` |
| ORM | `app/db/models.py` `OpsSession.tenant_id` :80 | `nullable=False` · default `"ops-desk-pilot"` |
| 双进程租户 | `tests/dualproc_server.py` ~:98 | `"tenant_id": "dualproc"` |
| FINDINGS | `docs/reports/host_v1_splittability_hardening/FINDINGS_open_elsewhere_v1.md` #1 | open |

---

## 钉死契约

| 项 | 钉死 |
|----|------|
| **改动面** | 仅 `tests/test_multi_replica_dualproc.py`（必要时 docstring）；**禁止**改 `app/` / alembic / 生产默认租户语义 |
| **tenant 值** | 与 dualproc 服务一致：优先常量 `"dualproc"`（与 `dualproc_server` 对齐）；若测需与 ORM 默认一致须在 commit 说明，但默认跟 dualproc |
| **验收** | 该文件 collect+run：不再出现 `tenant_id` NOT NULL；本地无 PG 如实记（CI 有 PG 为准） |
| **FINDINGS** | #1 状态改为 closed + 修订行 |

### 非范围

- 不改 `OpsSession` 模型/迁移  
- 不外置进程内状态 / 不重写 dualproc 基建  
- 不顺手修其他基线红  

---

## failure_paths

| 触发 | 行为 | 可重试 | 可见 |
|------|------|--------|------|
| 改到 `app/` | **拒收** | 是 | 是 |
| 仍 NOT NULL | **拒收** | 是 | 是 |
| 租户与 dualproc 头不一致导致鉴权/隔离误测 | 对齐 `"dualproc"` 后重跑 | 是 | 否 |

---

## 验收标准

- [ ] INSERT `ops_sessions` 含 `tenant_id`（值对齐 dualproc）
- [ ] `pytest tests/test_multi_replica_dualproc.py`：无 `tenant_id` NOT NULL ERROR（有 PG 时用例绿）
- [ ] `git diff master -- app/` 为空
- [ ] FINDINGS #1 → closed
- [ ] ruff 净增 0（触及文件）

---

## 依赖

- FINDINGS #1 · V1-E CLOSE · `task_multi_replica_verify` done  

---

## 给执行帽必读

1. 本 task · FINDINGS #1  
2. `tests/test_multi_replica_dualproc.py` `_create_user`  
3. `tests/dualproc_server.py` tenant 头  
4. `app/db/models.py` `OpsSession.tenant_id`（只读）  

---

## 思考轮控制

| 轮 | 结论 | early_stop | reason（early_stop） | residual_risks |
|----|------|------------|----------------------|----------------|
| R0 | 单点 fixture NOT NULL · 根因清楚（FINDINGS #1） | no | — | 无 |
| R1 | 闸 00 代录全 approved · graph=none · 可 30 | no | — | 无 |
| R2 | 竖切=唯一方案：INSERT 补 `tenant_id='dualproc'` | no | — | 本地无 PG 时须 CI 实证 |
| R3 | failure_paths 三条（改 app 拒收 / 仍 NOT NULL 拒收 / 租户不一致重跑） | no | — | 无 |
| R4 | 验收可机跑（diff app 空 + dualproc 无 NOT NULL） | no | — | 无 |
| R5 | 可交 30；单点测试基建无需加轮 | yes | 方案唯一 · 锚点已钉 · 无方案分叉 | 见 R2 |

**actual_last_round**：R5 · **early_stop**：yes · **residual_risks**：见 R2

### R0 · 问题框定

FINDINGS #1：dualproc `_create_user` 裸 SQL 漏 `tenant_id` → NOT NULL → 9 ERROR。

### R1 · 开工闸

三闸 approved（00 代录）· verify 须 PASS 后 30。

### R2 · 竖切

只改 tests fixture 一处 INSERT；tenant=`dualproc` 对齐 dualproc_server。

### R3 · 失败语义

见 failure_paths 表。

### R4 · 可测性

pytest dualproc 文件 + `git diff master -- app/` 空。

### R5 · 交付判定

可委派 30。

### 自检结论

本稿：范围仅 fixture 一列 · 非范围锁死零 app/ · 验收可机跑 · failure_paths 三条 · 闸表三行 approved（00 代录 · bugfix 单点）· 思考轮 R0–R5 齐全 · early_stop 于 R5 正当。可委派 30。

---

## 修订记录

| 日期 | 摘要 |
|------|------|
| 2026-09-24 | 00 10 落稿 + 三闸代录 approved · 委派 30 |
