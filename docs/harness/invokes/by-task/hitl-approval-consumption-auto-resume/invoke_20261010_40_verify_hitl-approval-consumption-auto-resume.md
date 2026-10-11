---
hat: 40
task_slug: hitl-approval-consumption-auto-resume
date: 2026-10-10
---

# Invoke：40 核验 hitl-approval-consumption-auto-resume（T2 · D5 批准后自动继续可配置面）

> **帽**：Harness 40（核验） · **task**：`docs/tasks/active/task_hitl_approval_consumption_auto_resume.md`
> **分支**：`task/hitl-approval-consumption-auto-resume`（worktree t2-auto-resume · base master `3f6a630` 含 T1 merge）
> **核验对象**：`6530bd0`（feat：auto_resume.py + router 挂点 + SKIP LOCKED + run_is_terminal + lifespan）· `d35369a`（39 枚测试）· `8d03e64` + `893eda5`（图谱+invoke）
> **结论**：**PASS（带偏差登记 · 可进 PR 队列）**
> **纪律**：独立复跑 · 不采信自报 · invoke 骨架先行逐项回填

---

## 基点澄清（40 先手实证）

- 本地 master 实指 `94cb1c6`（=3f6a630 + PR #217 T1 close chore 0b65118，close 归档面在 master 侧）；T2 分支自 `3f6a630` 切出（`git merge-base HEAD master`=`3f6a630` 实证）。
- 故裸 `git diff master` 混含 T1 close 归档面（50 invoke 删除/任务回迁 active/README 行），**非 T2 产出**；本核验一律以 merge-base `3f6a630` 为对拍基线。
- `master..HEAD` 恰为四枚核验对象 commit（6530bd0/d35369a/8d03e64/893eda5），无夹带。

## 核验总表（八项 · 逐项回填）

| # | 核验项 | 结论 | 实证 |
|---|--------|------|------|
| 1 | diff 面对拍 + TB7 既有函数 diff 空 + store.py 纯新增 | **PASS** | `git diff 3f6a630 HEAD --stat`：8 文件（auto_resume.py+261 / router.py±154 / store.py+76 / event_store.py+35 / main.py±12 / 图谱±6 / 30 invoke+79 / 测试+769）· 面外零改动；registry.py/policy.py/nodes.py/delegation.py diff **空**（亲跑）；store.py `-U0` 删除行=**0**（68 行纯新增 · `_DECIDE`/`adecide` 段零触）；`_DecidePayload.decision` Literal/422 形态一行未动 |
| 2 | 39 枚新测试抽跑 + 断言分组亲读 | **PASS** | `pytest tests/test_hitl_auto_resume.py` → collect **39** · **39 passed**（0 skip · Db 组 4 枚真 PG 非 skip · DB_AVAILABLE=True）；亲读：`test_db_claim_skip_locked_only_one_succeeds` 为**真锁语义**（holder 连接 `FOR UPDATE` 持锁期间认领=None · 释放后成功）；InMemory 组仅条件过滤+状态机幂等（`test_inmemory_double_dispatch_state_machine_idempotent` 执行==1）· **无行锁假断言**（实操-C 守住）；400/422 对照钉（`test_decide_resume_mode_unknown_400_not_422` 同测双断言）；AST 无状态钉 + `await resume_hitl_run(` 调用点==1 同源钉 |
| 3 | 全量 pytest + ruff + graph-compile | **PASS** | .env 与主仓**逐字节一致**（diff 空）；全量 `pytest tests` → **1748 passed · 1 skipped · 4 failed**（62s）——4 红=capability_lookups×3+lg_rag_multi×1（`delegation no_token` · 与 T1 40 钉案（d1b0c06）同签名同文件 · 失败文件均非本分支触及 → **基线环境性 · 零新增红**）；ruff 触及六路径 `All checks passed` + base 3f6a630 影子树同路径同绿（零新增）；全仓 ruff 55 错均在未触及文件（按文件分组亲核）；graph-compile **EXIT=0**（freeze_id/日期噪音承 T1 40 口径 checkout 还原） |
| 4 | B1 十三文件抽核 | **PASS** | 13 文件 `pytest` → **243 passed**（与 30 自报一致）；⚠️ 过程坑登记：首轮与全量 pytest **并发**共享测试 PG 致 4 枚窗口性红（auto_resume×3+1 · 行/锁互相干扰）· 串行复跑全绿——非代码归因，操作纪律教训（勿并发跑两套 pytest 对同一测试库） |
| 5 | TB1 live 段 + 台账三动作 | **PASS 带偏差（末段命中 T1 已登记偏差 · 如实登记）** | 见下「live 实录」整段 |
| 6 | 闸面终态 | **PASS** | `npx spec-wave verify` → **VERIFY: PASS · EXIT=0**（三闸 approved 如实）；`task lint` PASS（回填后复跑同 PASS）；`lint-wiki-delta` PASS；01_modules.md hitl 行（resume_mode/白名单 400/触发器同源/SKIP LOCKED/lifespan 扫描/台账三件套）+ lg_rag 行（run_is_terminal 谓词 + auto 同源说明）备注 diff 实证 · 在册行（T2 行 · 00 代录措辞承 T1 先例形态）在案 → **00 ratify：措辞合规即认可口径** |
| 7 | task 自检结论段回填 | **PASS** | 已回填（40 核验结论段 · 本 commit 带入） |
| 8 | 现场清理 | **PASS** | live 服务 :8030 已杀（lsof 空实证）；/tmp 临时件（t2_40_*.py/log/jar、ops40 残留无）销毁；.env 全程未动（与主仓逐字节一致复核）；graph.json 噪音还原后 git status 仅余 40 自产两文件 |

## live 实录（TB1 段 · handoff「A1 第四段补全实录」验收令复跑）

**环境**：docker PG15（healthy）+ 本机 uvicorn :8030（worktree 代码 · 剥代理 env · INFO 日志启动器 /tmp/t2_40_serve.py ephemeral）；**env 组**：`LG_RAG_DELEGATION_TOKEN_MODE=enforce` + `LG_RAG_DELEGATION_TOKEN_SECRET`（承 .env）+ `OPS_CAPABILITY_EXTRA_MANIFESTS=oa.readonly+testing.v1` + `OPS_CAPABILITY_ALLOW_WRITE_TAGS=testing` + `OPS_STRATEGY_EXTRA_CANDIDATE_CAPABILITY_IDS=testing.write.echo` + `OPS_HITL_PERSISTENCE=db` + `OPS_CAPABILITY_ALLOW_WRITE=1` + **`OPS_HITL_AUTO_RESUME=auto`** + `OPS_HITL_AUTO_RESUME_SCAN_INTERVAL_SECONDS=5`；登录 admin cookie；catalog 实证 `testing.write.echo` 在可见集（visible_ids 9 枚）；`/api/ops/hitl/runtime`=db。

**主链（run `dbc0fc7430134fc497196846a4dd3ce5` · thread `19c8f37a…`）**：

| 段 | 结果 | 证据 |
|----|------|------|
| ① plans 含写 tool → 挂起 | ✅ | SSE `hitl.waiting`（seq 6 · request `hitl_e44954bd…` · `unlock_subtask_id=:1` 回填 live 实证）→ `done{waiting_approval}`（seq 7） |
| ② pending 可见 | ✅ | GET /hitl/pending 200 含该单（归属过滤生效） |
| ③ decide(approved) | ✅ | 200 `persisted=true` · `decision_by=admin`；**resume 块 auto 形态 live 实证**（补拍另一单）：`{"required":false,"auto_triggered":true,"method":"POST","endpoint":…/resume}` |
| ④ **不调 resume → 自动恢复** | ✅ | 10:55:03.209 `hitl_auto_resume_triggered`（resume_mode=inherit · ttl_remaining=3599）→ .211 `hitl_auto_resume_claimed` → .246 「已批准，解锁 1 步并从可恢复点重跑 unlocked=[':1']」→ 事件帧 seq 8 `hitl.resumed` → 10:55:28 「HITL 恢复完成 replay=:13」——**与手动 resume 同源路径 live 走通** |
| ⑤ 末段 | ⚠️ **命中已登记偏差 · 未伪造** | replan 重盖章 sid :1→:2（10:55:28 `token_issue_hitl_required subtask=:2`）→ 消费键失配（全程**零** `delegation_approval_consumed` 台账）→ 再拦（seq 12 `hitl.waiting` req `41a30a:2` · seq 13 `done{waiting_approval}`）→ **`done{completed}` 不可达**，与 T1 40「重要发现」逐点吻合（replan 重盖章 sid 失配 · 已在案）· **非 T2 回归** |
| ⑥ FP-11 不循环 live | ✅ | 台账计数亲核：本 request `triggered`==**1** · `claimed`==**1** · `compensated`==**0**（同 run 有未决 pending → 补偿扫描跳过 · 第四条件 live 成立）· 回挂起态等人 |

**台账第三动作（compensated）实证**：播种「崩溃遗留」形态 approved 单据（`t2live40_comp_c515a302` · 幽灵 thread）→ 服务启动扫描首轮即补触发：`hitl_auto_resume_compensated` → `hitl_auto_resume_claimed`（ttl_remaining 逐轮 3547→3542→3537 递减实证周期扫描）→ 恢复执行对幽灵 thread 如实失败（ResumeError 落日志 · 不改任何已返回结果）→ 删行止刷。**FP-9 崩溃兜底链 live 成立**。

**派发不阻响应 live**：补拍 decide 即时 200，triggered/claimed 随后落账（异步派发实证 · 实操-F 守住）。

## 40 附带观察（登记上抛 · 非 T2 归因）

**resume 重放留孤儿 pending**：live 实证 decide 后 34ms 内出现已批准 sid :1 的新 pending（`hitl_5cefb116…` · 无对应签发/拦截日志 · 不进任何 hitl.waiting 帧）。实读 `observe_node`（nodes.py:1725-1727「落库先于挂起」+ :1727 `_persist_hitl` 在 :1736 `interrupt()` 之前）：LangGraph resume 时**节点从头重放**，`_persist_hitl` 在 `interrupt()` 返回恢复值之前按旧状态重建 pending。手动/自动 resume 同源共有（nodes.py 本 task diff 空 · TB7 钉）——**T1 面既有语义 · 建议随 replan 重盖章裁定一并纳入 SPEC v2 视野**（孤儿 pending 会影响 pending 列表 UX 与「同 run 无未决 pending」判定的输入纯度）。

## FAIL 判定扫描

30 无造假：39 枚/全量 1748·4 红/diff 空/纯新增/图谱/lint/verify **全部独立复跑一致**；30 对 live 末段的「预计撞同一偏差」预告与 live 实证逐点吻合（诚信加分项）。B1 并发窗 4 红经串行复跑证伪（操作坑 · 已登记）。

## 给维护者的裁定建议

1. **可进 PR 队列**（机制面 pytest+live 双实证 · 末段缺口为 T1 已登记偏差 · 非本 task 回归）；
2. SPEC v2 裁定候选项维持 T1 40 上抛（replan 后 approved 步骤 carry 保号 / 消费键放宽粒度），**并纳入本帽新观察之「resume 重放孤儿 pending」**；
3. HG-GRAPH-MODULES 在册行留 00 ratify（措辞合规 · 承 T1 先例形态）；
4. .env.example 未增 `OPS_HITL_AUTO_RESUME`/SCAN_INTERVAL 两键（承 T1 TTL 键先例 · 30 留转在案）——如要求补登记另议。

## 环境注记

- 核验全程未改仓内代码（仅自产文档两件）；live 对 dev DB 的足迹：本 run 单据行留存（dbc0fc74 三行 · 承 T1 live 先例不清理），补拍将一枚 01:39 遗留 pending 置为 approved（如实登记）。
- 端口 8020 无残留进程（lsof 实证）· 起用 8030 避开 8000 既有 dev server（8000 上 python 进程非本核验所起 · 未动）。

---

## 修订

| 日期 | 说明 |
|------|------|
| 2026-10-10 | 40 骨架先行落盘（基点澄清：master=94cb1c6 · 对拍基线=merge-base 3f6a630） |
| 2026-10-10 | 40 核验闭环：八项逐项 PASS（live TB1 机制段全达 · 末段命中 T1 已登记偏差如实登记 · 台账三动作 live 实证 · 孤儿 pending 附带观察上抛）· task 自检段回填 · 现场清理 |
