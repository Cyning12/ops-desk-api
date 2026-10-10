---
hat: 50
task_slug: hitl-auto-resume-claim-race
date: 2026-10-11
---

# invoke · 50+CLOSE · hitl-auto-resume-claim-race（auto_resume 认领竞态 · 验收 D1 偏差收口）

## 收口结论

- 链路全通：10-task 起草（7022e20 · 验收 D1 实证锚点逐字承接 · 候选 A/B/C/D 开放）→ 20-task-audit R1（b7639ce · PASS-WITH-NITS · N-1~N-3 非阻塞 · 审查文 docs/audits/task-review/20261010_hitl-auto-resume-claim-race_r1.md）→ 维护者三闸人签（00 代录 · 2f91f67）→ 30（79b6485 红测先行修复前 2 failed 与 live D1 同形签名 → 51e17ca 方向 A 实现 → ac7f635 30 invoke+图谱回写）→ 40（2714092 · 七项核验全 PASS · 红测时序 worktree 复跑实证 · TC3 live 零 stranded_checkpoint · deferred×5 机制本体实证 · 恰好一次执行）。
- 闸链：HG-TASK-DRAFT / HG-AUDIT-R1 / HG-GRAPH-MODULES 三闸 approved（维护者授权 · 00 代录 · 图谱 l1/01_modules.md:39 hitl 行随 30 回写在案）。
- PR [#224](https://github.com/Cyning12/ops-desk-api/pull/224)：CI 四绿 → merge master 11fb7e6（2026-10-10 · Asia/Shanghai）。
- 归档：task → done/（头部状态 done · 修订表 CLOSE 行）；active README 登记表补行；Hub docs/tasks/done/README.md 表行+修订记录行补登；CLOSE 文档 docs/tasks/close/close_hitl_auto_resume_claim_race_20261010.md 落盘。

## 交付摘要

| 项 | 内容 |
|---|---|
| **产出** | app/ops/hitl/auto_resume.py +52：_interrupt_metadata_visible 只读就绪校验（有 pending tasks ∧ interrupts 全空 → defer 等下轮补偿扫描 · 台账 hitl_auto_resume_deferred 记动作不记内容）· 认领不写状态（FOR UPDATE SKIP LOCKED 随事务释放 · defer 零回滚）· 执行仍 _execute_decided_resume 同源（无状态恢复纪律） |
| **验收** | TC1/TC2 注入式红测（_RaceWindow 窗口替身）· TC3 live（隔离库 opsdesk_tc3）：triggered→claimed→(compensated→claimed→deferred)×5→approval_consumed→token_issued→token_verified→恢复完成 · 零 stranded · 零执行失败 ERROR · 恰好一次执行 |
| **红线** | nodes.py/store.py/router.py/resume.py/消费门/guard diff 全空 · tests/test_hitl_resume.py diff 0 行（手动 409 语义存续）· 零新表零迁移零 SSE 事件零 env · B1 七文件 174 passed · 全量 1764 passed 基线零新增红 |

## 钉案登记（详见 CLOSE 文档第八/九节）

1. 裸 uvicorn 无台账（全仓零 logging.basicConfig）——live 核验须自写启动器；建议后续仓级 task 收口进 app/main.py。
2. 仓级 verify EXIT=2（done/ 遗留档缺口基线 · 主仓同）——照登不新增。
3. not_interrupted 子窗口窄判定维持；stranded_checkpoint 分类语义（resume.py:41-51 注释）建议随下次触及 resume.py 的 task 修正表述。

## 质量钉（CLOSE 机械闸复跑）

- 仓级 verify：EXIT=2 BLOCKED（仓级基线 · 主仓 master 同 · 照登不新增）。
- graph-compile：本 CLOSE 无图谱变更（回写已随 PR #224 入 master）· n/a。

## 移交

- 验收 20261010 链全收口：验收文档 PR #223 已签录合并（4a36b7c · 维护者令「此次checklist通过，同时把你发现的文档问题和坑位补全」00 代录 · 便签坑位修正版+D1 处置更新随签录落盘）· 本 task 为其 D1 偏差收口件。
- active 目录无在途 task；worktree 与 task/close 分支由本 CLOSE 清理。

## 事故留痕（过程教训）

- 本 CLOSE 首棒在主仓作业时，其暂存挪档（git mv active→done 的 done/ 侧）被并行的验收签录 commit a42ac37 误卷入 PR #223；00 以 3e0827e 从验收分支剔除（挪档权属本 CLOSE），抢救首棒产物（close 文档/README 双侧/done 档回填）至 /tmp/close_rescue 后本棒重落——教训：**多棒并行时主仓 index 是共享态，暂存即暴露**；CLOSE 棒应在独立 worktree 作业或即作即提交。
