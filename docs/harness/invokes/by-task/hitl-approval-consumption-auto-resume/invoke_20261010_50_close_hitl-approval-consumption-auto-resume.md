---
hat: 50
task_slug: hitl-approval-consumption-auto-resume
date: 2026-10-10
---

# invoke · 50+CLOSE · hitl-approval-consumption-auto-resume（T2 · D5 批准后自动继续可配置面 · 触发器+行锁认领+补偿扫描）

## 收口结论

- 链路全通：10-task（SPEC v1 signed 承接 D5 · 骨架先行增量落盘 · 锚点逐行实读 master `4d905e0` · R2-N1/N2/N3 三钉（400 形态/挂点/行锁）· early_stop at R5）→ 20-task-audit R1（PASS · 审查文 `docs/harness/reviews/task_hitl_approval_consumption_auto_resume_audit_R1_20261010.md` · N-1~N-3 非阻塞吸收）→ 维护者三闸人签（HG-TASK-DRAFT / HG-AUDIT-R1 / HG-GRAPH-MODULES · 00 代录 2026-10-10 · `invoke_20261010_00_gate_signoff_t2.md` 留痕 · **T1 merge 前置达成**：`3f6a630` 已入 master 后 30 开工）→ 30（`6530bd0` 配置面+触发器+恢复段同源抽取+行锁认领+补偿扫描 · `d35369a` 验收 TB1–TB6 断言化 39 枚 · `8d03e64` 图谱 hitl/lg_rag 行备注回写+30 invoke · `893eda5` 30 回填 TB1–TB8 实证与实操-E 裁定（run 终态真源=事件表 done 帧只读查询））→ 40（核验 PASS 带偏差登记 · 独立复跑不采信自报 · TB1–TB8 全机断绿 · 全量 1748 passed · live 六 env 组+auto 全链达成 · `b43dee4`）。
- 闸链：三闸全 approved（维护者签 · 00 代录 · 图谱闸表在册行 hitl/lg_rag 在案 01_modules.md）。
- PR [#218](https://github.com/Cyning12/ops-desk-api/pull/218)：CI 四绿（import-linter / lint-wiki-delta / pytest / check）→ merge master `0e13fc4`（2026-10-10 · Asia/Shanghai）。
- 归档：task → `done/`（头部状态 done · F1–F8 + 验收 TB1–TB8 勾选 · TB1 live 末段标注「自动恢复全链走通 · done{completed} 末段 replan 重盖章上抛 SPEC v2」· 修订表 CLOSE 行）；active README 登记表补行；Hub `docs/tasks/done/README.md` engineering 域表行 + 修订记录行补登；本 CLOSE invoke 落盘。

## 交付摘要

| 项 | 内容 |
|---|---|
| **产出** | `app/ops/hitl/router.py` decide 载荷可选键 `resume_mode`（str 缺省 inherit · 手工白名单未知值 400 · decision Literal/422 一行不动）+ 成功分支触发器派发（R2-N2 挂点）+ `resume_request` 恢复段抽取同源复用（禁 HTTP 自调）· `app/ops/hitl/store.py` Db 新增 `FOR UPDATE SKIP LOCKED` 认领方法（纯新增 68 行 · 既有四方法 diff 空）· `app/main.py` lifespan 补偿扫描（启动扫+周期任务+shutdown cancel · manual 零创建）· `OPS_HITL_AUTO_RESUME` env（manual 默认 · 非法回退）· 台账三件套（triggered/claimed/compensated）· 39 枚新测 + 图谱 hitl/lg_rag 行备注回写 |
| **验收** | TB1 auto 全链（pytest 机制段+live 实证：decide(approved) 200 `{required:false, auto_triggered:true}` → 不调 resume → triggered→claimed→同源恢复→hitl.resumed 帧→图继续 replay=:13）· TB2 无状态恢复钉死组（同源只读事件表+DB · 补偿幂等 · Db 组真 PG 并发双认领仅一成功 · resume_mode 未知值 400 非 422 · 非法 env 回退 manual）· TB3 防重（重复 decide 409 原样绿 · 触发与扫描并发仅一执行）· TB4 崩溃兜底（补偿扫描补触发 · compensated 台账 ttl_remaining 逐轮递减实证）· TB5 不循环（auto 后仍拦回挂起 · triggered 计数==1 · 扫描跳过同 run 未决 pending）· TB6 manual/off 零 diff（spy 零调用 · lifespan 面无任务 · B1 全文件原样绿）· TB7 反回归（store/registry/policy/nodes/delegation diff 空 · `await resume_hitl_run(` 调用点==1 同源机断钉）· TB8 工程面（全量 1748 passed · ruff 触及面零新增 · graph-compile EXIT=0） |
| **红线** | `store.py` `adecide`/`_DECIDE` diff 空（SPEC A7 存续）· OA callback 签名面零 diff 不挂触发器 · T1 消费门/unlock 回填一行未动 · deny 判序/Policy 写闸/gateway 闸链 diff 空 · manual 默认字面零 diff · 零新表零新列零 alembic 零 SSE 事件类型 · 触发器不载状态（无状态恢复纪律 · 进程内任务句柄不落盘） |

## 偏差登记（40 核验 · 上抛 SPEC v2）

- **末段 `done{completed}` 未达成 = T1 已登记偏差复现**：live auto 全链中 resume 后 supervisor 走 LLM 正常重规划 → `_stamp_host_plan` 重盖 sid（:1→:2）→ 消费键 (run_id, subtask_id, capability_id) 失配 → 无 `delegation_approval_consumed` 台账 → 再拦新 pending :2（FP-3 循环）。**非 T2 回归**——T2 机制面（decide→自动派发→行锁认领→同源恢复→图继续）live 全达；T1 40 已登记同一根因，裁定（carry 保号 vs 消费键放宽）仍留 SPEC v2。
- **附带观察 · 孤儿 pending**：resume 时 `observe_node` 重放致 `_persist_hitl`（nodes.py:1727 · 落库先于挂起）在 `interrupt()` 返回前为已批准 sid 重建孤儿 pending（live 实证 `hitl_5cefb116…:1`）——LangGraph 节点重放语义使然，手动/自动路径同源共有，nodes.py 本 task diff 空。上抛 SPEC v2 一并裁定。

## SPEC 全链收官段（签发审批消费回路 · 三棒齐）

- **T3（D3 · PR #213 · merge `7853334`）**：strategy 候选 map env 追加口 `OPS_STRATEGY_EXTRA_CANDIDATE_CAPABILITY_IDS`（默认不设逐字节零 diff · 下游闸全链不动）——消费回路可审对象接入口。
- **T1（D1/D2/D4 · PR #216 · merge `3f6a630`）**：审批消费门（三元组消费键+TTL fail-closed）+ unlock 空形态回填（resume 409 修复）+ 台账/34 枚新测——批准→放行消费成环核心。
- **T2（D5 · 本 task · PR #218 · merge `0e13fc4`）**：批准后自动继续可配置面（env+resume_mode 双级 · 触发器+行锁认领+补偿扫描 · 无状态恢复纪律）——manual 半环补成 auto 全环。
- **收官裁定**：SPEC v1（`docs/spec/hitl-approval-consumption/SPEC-hitl-approval-consumption_v1.md`）D1–D5 实现面全闭合 · Q1/Q2/Q3/Q5/Q6/Q7 裁定全落地 · FP-1~FP-11 机制+断言全覆盖 · A1–A10 验收面全机断绿（live 偏差如实登记）。
- **上抛项（留 SPEC v2 · 待维护者裁定）**：① replan 重盖章致消费键失配 —— resume 后对 approved 步骤走 **carry 保号** / 或 **消费键放宽**（(run_id, capability_id) 粒度）二选一（T1/T2 40 双重实证）；② resume 重放致**孤儿 pending**（observe_node 节点重放语义 · 手动/自动共有）；③ SPEC v2 起草与否、以及 OA callback 面 auto 触发器（本波非范围留案）——均归维护者。

## 留痕

- 40 核验期全量 4 failed=基线环境性（capability_lookups×3+lg_rag_multi×1 · delegation no_token · 与 T1 40 钉案同签名 · 失败文件均非本分支触及 · 零新增红 · 40 invoke 有实证）。
- 基点注记：本分支自 `3f6a630` 切出（40 核验时本地 master 实指 `94cb1c6` 含 PR #217 T1 close chore · 对拍基线以 merge-base 为准）；PR #217 T1 CLOSE（`0b65118`）先行合入后，PR #218 merge 为 `0e13fc4`。
- graph-compile 时间戳噪音已 checkout 还原（EXIT=0 实证）；CLOSE 机械闸（task lint done/ 路径 · graph-compile）复跑结果见本 PR 留痕。
- worktree `t2-auto-resume` 与分支 `task/hitl-approval-consumption-auto-resume` 待清理由 00 处理（active README 已登记）。

## 移交

- **全链收口**：签发审批消费回路三 task（T3+T1+T2）全闭合 —— 本 CLOSE 即全链收官；active 目录无本回路在途 task。
- SPEC v1 实现面闭合；**SPEC v2 裁定项（carry 保号/消费键放宽 · 孤儿 pending · OA 面 auto）留维护者**；若起 SPEC v2 另立 10-spec 流程，本 invoke 与 T1/T2 40 invoke 为偏差实证锚点。
