# Invoke · 00 启动 · host-v1-wrap-up · D1 文档闭环（新窗口执行）

> **日期**：2026-09-24  
> **帽**：00（统筹 · D1=docs-only · 无 30 改码面 · 可由 00 直接执行文档编辑或委派）  
> **维护者令（原话留痕）**：「签收，生成00 Prompt，在新窗口开始D1统筹」（2026-09-24）· 承：「落盘上面的收尾清单生成spec，为下一步更新进行准备」（2026-09-24）· 长程令「签收，并生成对此长程任务的00启动Prompt，新窗口执行，授权00签收所有过程文档，完整落地1.0版本内容」（2026-09-23）  
> **授权面**：**00 代签/代录本轨全部过程文档**——HG-TASK-DRAFT · HG-AUDIT-R1（docs-only 承 task_agent_host_framework_alignment 先例 · docs 面无代码审查面）· HG-GRAPH-MODULES（预期 none · 按实判）；每处代录必须「维护者令原话 + 日期」留痕。  
> **SPEC 真值**：`docs/spec/host-v1-wrap-up/SPEC-host-v1-wrap-up_v0.md`（**signed** · 00 代录 · 开放裁定 Q1 合一 PR / Q2 逐闸独立 / Q3 登记不消化 锁死）  
> **执行窗口**：新窗口 · Open Folder = `ops-desk-api/` 仓根

---

## 1. 目标（一句话）

按 SPEC §2 D1 完成 **v1.0 文档闭环四件**（07 转 completed · G2 REGRESSION 更新报告 · multi-replica SPEC 实施态 · landing invoke 终条）——**docs-only 单分支单 PR**，CI 绿后 merge，CLOSE 归档 + Hub 补登。

## 2. 开工前必读（新窗口按序）

1. `AGENTS.md`（仓纪律 · 分支纪律 · GATE_VERIFY）
2. `docs/spec/host-v1-wrap-up/SPEC-host-v1-wrap-up_v0.md`（signed · 本棒唯一范围真值）
3. `docs/spec/agent-infra/07_host_v1_landing_plan_v0.md`（D1-1 修改对象）
4. `docs/reports/host_v1_exit_review/ACCEPTANCE_three_party_20260924_00.md`（G2 证据源 · 三方验收）
5. `docs/reports/host_v1_exit_review/REPORT_host_v1_exit_review_20260924_v1_zh.md`（G2 残余登记）
6. `docs/spec/multi-replica-verify/SPEC-multi-replica-verify_v1.md`（D1-3 修改对象）
7. `docs/harness/invokes/by-task/host-v1-landing/invoke_20260923_00_host-v1-landing.md`（D1-4 修改对象）
8. `docs/tasks/done/task_multi_replica_dualproc_tenant_session.md`（#190 fix KPI 证据源）

## 3. 范围（钉死 · SPEC §2 D1 · 超此清单即停）

| # | 件 | 修改对象 | 动作（**只增不改 · 历史真值零回改**） |
|---|---|---|---|
| D1-1 | 07 规划转 completed | `docs/spec/agent-infra/07_host_v1_landing_plan_v0.md` | 状态行 signed→`completed`（引证：五波 CLOSE #179/#181/#183/#184/#187 + 三方验收 #195）· 修订记录追加行（维护者令原话+日期留痕 · 00 代录） |
| D1-2 | G2 REGRESSION 更新报告 | 新文件 `reports/multi_replica_verify/REGRESSION_dualproc_post_fix_20260924.md` | result=**PASS** · 证据=#190 fixture fix（`ops_sessions.tenant_id`）+ #190 CI pytest pass + 三方验收亲跑 `test_multi_replica_dualproc.py` 9 passed @ master `1cae38f` + recorded_at/git sha 环境指纹；**旧 BLOCKED-ENV 报告保留不删**（历史真值） |
| D1-3 | multi-replica SPEC 实施态 | `docs/spec/multi-replica-verify/SPEC-multi-replica-verify_v1.md` | 状态行/修订表补「已实施（V1-E #187 + dualproc fix #190/#192 · 2026-09-24）」 |
| D1-4 | landing invoke 终条 | `docs/harness/invokes/by-task/host-v1-landing/invoke_20260923_00_host-v1-landing.md` | 修订表追加：五波全 CLOSE + 出口复核（PASS-WITH-GAP → G1 closed #193/#194）+ 三方验收 #195 PASS · 长程令全链路闭合 |

**同时落盘**（同 PR · SPEC §2 D4 顺带）：`docs/reports/host_v1_exit_review/BACKLOG_register_20260924.md`（三条目登记：legacy 92 缺口指豁免机制 · 代跑 WIP 分支归原线 · test_import_from_supabase 本地环境性 3 ERROR 非缺陷）。

## 4. 非范围（钉死 · 越任一条即停）

- ❌ 任何 `app/` 改动（含「顺手」）· 任何代码面 task
- ❌ D2 六闸灰度推进（另棒 · SPEC §2 D2 框架已立）
- ❌ 回改历史文档正文（只准追加修订行/状态行 · 旧报告零删改）
- ❌ legacy 缺口消化 · 他人 WIP 分支触碰
- ❌ 图谱行备注（预期 none；若执行中误判需图谱登记 → 停并回 10-spec）

## 5. 执行流（不可跳步）

1. **GATE_VERIFY 首输出**：当前无 active task 属正常（v1.0 全 CLOSE）——本棒先立 task 再执行；任何 HG-AUDIT-R1 pending 的 task 存在 → 停并上报。
2. **10-task**：起草 `docs/tasks/active/task_host_v1_wrap_up.md`（类型 docs-only · test_strategy=docs-only · graph_change_layer=none · required_invoke_hats=10,40 · 闸表：HG-TASK-DRAFT=approved（00 代录 · 维护者令原话留痕）· HG-AUDIT-R1=approved（00 代录 · docs-only 承先例）· HG-GRAPH-MODULES=approved（预期无义务按实判））→ `task lint` PASS。
3. **分支**：`git checkout -b docs/host-v1-wrap-up`（自 master · **禁 master 直改**）。
4. **执行 D1-1~D1-4 + BACKLOG**（按 §3 表 · 只增不改）。
5. **验证**：`git diff master --stat` 全 docs/ · 旧文件仅追加行（抽查 diff 无正文删改）· `npx spec-wave verify --task` PASS · graph-compile 若未触图谱可略（触则必跑绿）。
6. **PR + CI 绿 + merge**（承「PR 过 CI 后 merge」先例）。
7. **CLOSE**：task 归档 done/ + Hub 补登（域表行+修订记录行）+ 40 invoke 落盘 + `task close --yes`（豁免留痕按需）。
8. **短报维护者**：四件完成证据 + PR 号 + 下一棒候选（D2 委派令牌闸观察期）。

## 6. 00 行为纪律（新窗口）

- 本棒 **docs-only 无 30 改码面**：00 可直接执行文档编辑（承 task_agent_host_framework_alignment 先例）；若出现任何代码面冲动 → STOP。
- 每处代录带「维护者令原话 + 日期」（见头部授权面三令）。
- 会话锚丢失 → 读本文件 + SPEC 重锚（承 hat-reanchor 纪律）。
- 代跑 agent 的 WIP（`docs/agent-host-current-architecture-20260924` 分支 + 09-24 讨论稿）**不触碰**；开工前先 `git status` 确认工作树状态并如实记录。

---

## 修订

| 日期 | 说明 |
|---|---|
| 2026-09-24 | 00 启动 invoke 初版（维护者令原话留痕 · SPEC signed 同令代录） |

---

## 复制区（新窗口整段粘贴）

```text
你是 ops-desk-api 仓（Open Folder = 仓根）的 00 统筹帽。先读启动真值：
docs/harness/invokes/by-task/host-v1-wrap-up/invoke_20260924_00_host-v1-wrap-up.md
——维护者令（2026-09-24 原话）：「签收，生成00 Prompt，在新窗口开始D1统筹」。
任务：按 invoke §3 完成 v1.0 文档闭环 D1 四件（07 转 completed · G2 REGRESSION
更新报告 · multi-replica SPEC 实施态 · landing invoke 终条）+ BACKLOG 登记，
docs-only 单分支 docs/host-v1-wrap-up 单 PR，CI 绿 merge 后 CLOSE 归档+Hub 补登。
SPEC 真值：docs/spec/host-v1-wrap-up/SPEC-host-v1-wrap-up_v0.md（signed）。
授权：00 代签/代录本轨全部过程文档（每处带维护者令原话+日期留痕）。
纪律：只增不改历史真值 · 零 app/ 改动 · 首输出 GATE_VERIFY · 先立 task 再执行。
首输出先给 GATE_VERIFY 表与 git status 工作树快照。
```
