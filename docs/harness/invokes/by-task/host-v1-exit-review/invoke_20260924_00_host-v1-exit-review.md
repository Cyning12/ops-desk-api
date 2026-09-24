# Invoke · 00 启动 · host-v1-exit-review（Agent Host v1.0 出口复核 · 新窗口执行）

> **日期**：2026-09-24  
> **帽**：00（统筹 · 只委派实现帽 · 本波以**复核/报告/缺口 task**为主，默认不新开功能波）  
> **维护者令（原话留痕）**：「生成下v1.0出口复核的00 Prompt，授权00签收过程文档」  
> **授权面**：**00 可代签/代录本复核相关全部过程文档**——含（若开）HG-TASK-DRAFT · HG-AUDIT-R1 · HG-GRAPH-MODULES（本复核预期 `graph_change_layer=none`）· 审查文/报告签收位；每处代录须「维护者令原话 + 日期」留痕。  
> **规划真值**：`docs/spec/agent-infra/07_host_v1_landing_plan_v0.md` §4（出口八面）  
> **前置状态**：V1-A~E **全 CLOSE** · FINDINGS#1 dualproc fixture **CLOSED**（PR #190/#192）· `docs/tasks/active/` 空 · 分支干净仅 `master`  
> **执行窗口**：新窗口 · Open Folder = `ops-desk-api/` 仓根 · 启用 skill `harness-00-delegate-only`

---

## 1. 目标（一句话）

对 Agent Host **v1.0** 做 **07 §4 全轨出口复核**：八面逐条给 **PASS / PASS-WITH-GAP / FAIL** + 证据锚点（task/PR/测试/图谱/报告）；产出复核报告落盘；缺口只开 **fix/docs/eval 跟进 task**，不重开已 CLOSE 功能波。

## 2. 开工前必读（按序）

1. `AGENTS.md`
2. `docs/spec/agent-infra/07_host_v1_landing_plan_v0.md`（§4 出口 · §3 波次）
3. `docs/harness/invokes/by-task/host-v1-landing/invoke_20260923_00_host-v1-landing.md`（落地长程原令）
4. done 任务（证据主源）：
   - `docs/tasks/done/task_host_v1_delegation_token.md`（V1-A · #179）
   - `docs/tasks/done/task_host_v1_visibility_scenario_policy.md`（V1-B · #181）
   - `docs/tasks/done/task_host_v1_llm_factory_closure.md`（V1-C · #183）
   - `docs/tasks/done/task_host_v1_episodic_memory_feedback.md`（V1-D · #184）
   - `docs/tasks/done/task_host_v1_splittability_hardening.md`（V1-E · #187）
   - `docs/tasks/done/task_multi_replica_dualproc_tenant_session.md`（dualproc fixture · #190）
5. `docs/_tech_graph/l1/01_modules.md`（签录链 · V1-A~E 回写行）
6. `docs/reports/host_v1_splittability_hardening/`（含 FINDINGS · dualproc 口径）
7. 指标面对照：`docs/spec/agent-infra/04_eval_and_observability_plan_v0.md`（若存在）+ V1-C Cost per Successful Task 落点

## 3. 复核范围（钉死 · 07 §4）

| # | 面 | 出口判据（摘要） | 证据方向（00 须填） |
|---|---|---|---|
| 1 | 委派链路 | 全链路令牌 · 无令/越权/过期拒 · 审批留痕 | V1-A task/测/PR |
| 2 | 可见集 | 两阶段裁剪 · 安全默认 · 剔除台账 | V1-B |
| 3 | manifest | 四字段 · 缺失→HITL · 加载期强制 | V1-B |
| 4 | LLM 工厂 | 预算闸 · degraded · 缓存可观测 · 声明式降级 | V1-C |
| 5 | 记忆 | episode 零互写 · 聚类报告 | V1-D |
| 6 | 工程 | import-linter CI · **双进程报告** · registry 可替换 | V1-E + #190；**双进程须如实：fixture 已修后是否再跑绿 · 禁止假绿** |
| 7 | 指标 | SLI/SLO 四项：定义/有数/看板 | 最可能 GAP · 对照 04 轨 + V1-C Cost |
| 8 | 图谱 | 01_modules 回写 · HG-GRAPH-MODULES 签录完整 | 真读签录表至 V1-E |

**非范围**：不开 v2.0 拆分 · 不重做 V1-A~E 功能 · 不顺手改 `app/`（缺口另开 task 后委派 30）。

## 4. 交付物

1. **复核报告**（建议路径）：  
   `docs/reports/host_v1_exit_review/REPORT_host_v1_exit_review_20260924_v1_zh.md`  
   须含：八面结论表 · 每面证据链接 · GAP 清单（可执行下一棒）· 总裁定（`v1.0 EXIT PASS` / `PASS-WITH-GAP` / `NOT READY`）
2. **00 invoke 过程档**：本文件修订表回写；若开 follow-up task 则 `docs/tasks/active/task_*.md` + 对应 invoke
3. **可选**：对 GAP 直接起草 10-task（指标面/看板等）并 **00 代录 HG-TASK-DRAFT**；HG-AUDIT-R1 仍须 20 后或 00 按 bugfix/docs 先例代录（原话留痕）

## 5. 00 行为纪律

- 启用 **harness-00-delegate-only**：本窗**不亲自改 `app/`**；实现一律委派。
- 复核本身以读码/读报告/跑只读命令为主；写盘限 docs/reports · tasks · invokes · reviews。
- 首输出：状态扫描（active 空？master 干净？V1 done 五件+dualproc 在？）+ 本复核 GATE（无 30 改码则注明「复核棒 · 非实现棒」）。
- 用户口头「开工」≠ 闸；跟进实现须 task 表闸真实。
- 双进程口径：**禁止**仅因 V1-E CLOSE 就写「工程面双进程全绿」；须引用 #190 后复跑证据或缺测说明。

## 6. 建议执行序

1. 扫盘 done/PR/图谱/FINDINGS  
2. 八面填表（证据不足标 GAP，不猜）  
3. 落盘 REPORT  
4. 若总裁定含 GAP → 列 1～N 个 follow-up slug → 维护者未反对则可直接开最早 1 个 10-task（优先「指标面」）  
5. 短报维护者：总裁定 + GAP 条数 + 已开/待开 task

## 7. 复制区（新窗口整段粘贴）

见用户消息中的 `````text` 复制块（与本 invoke §1–§6 同义）。

---

## 8. 本棒执行结果（00 · 2026-09-24）

| 项 | 值 |
|---|---|
| 扫盘 | active 空 → 开 follow-up 后 active=`task_host_v1_sli_four_metrics` · master 无改 tracked · V1-A~E+dualproc done 在 |
| 报告 | `docs/reports/host_v1_exit_review/REPORT_host_v1_exit_review_20260924_v1_zh.md` |
| **EXIT** | **PASS-WITH-GAP** |
| 八面 | 1–5/8 **PASS** · 6/7 **PASS-WITH-GAP** |
| 主 GAP | 指标四项未齐（定义/有数/看板） |
| 跟进 | `docs/tasks/active/task_host_v1_sli_four_metrics.md` · HG-TASK-DRAFT **00 代录 approved** · HG-AUDIT-R1 **pending** |
| 本窗 | **未改** `app/` · 未派 30 |

---

## 修订

| 日期 | 说明 |
|---|---|
| 2026-09-24 | 初版 · 维护者令「生成v1.0出口复核00 Prompt · 授权00签收过程文档」 |
| 2026-09-24 | **00 执行完**：落盘 REPORT · EXIT=PASS-WITH-GAP · 开 G1 task（指标面）并代录 HG-TASK-DRAFT · 短报维护者 |
