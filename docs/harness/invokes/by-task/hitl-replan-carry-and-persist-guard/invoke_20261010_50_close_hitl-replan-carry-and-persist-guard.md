---
hat: 50
task_slug: hitl-replan-carry-and-persist-guard
date: 2026-10-10
---

# invoke · 50+CLOSE · hitl-replan-carry-and-persist-guard（replan 保号 + _persist_hitl 建单前检查 · SPEC v1 FP-3 偏差裁定落地）

## 收口结论

- 链路全通：10-task（维护者双裁定逐字承接 · 骨架先行增量落盘 · 锚点逐行实读 base bdd45f9 · R0–R5 early_stop at R5）→ 20-task-audit R1（PASS 零阻塞 · 审查文 docs/harness/reviews/task_hitl_replan_carry_and_persist_guard_audit_R1_20261010.md · N-1/N-2 顺手补 · N-3 供 30 参考）→ 维护者三闸人签（00 代录 2026-10-10 · invoke_20261010_00_gate_signoff.md）→ 30（228d7d2 nodes.py 保号段+建单检查段 · 687689d TB1–TB6 断言化 14 枚 · b857af6 图谱 G-L1 两行回写+30 invoke）→ 40（67148a9 · 七项核验全过 · 独立复跑不采信自报 · live 三 run 双靶点闭合）。
- 闸链：三闸全 approved（维护者签 · 00 代录 · 图谱闸在册行 lg_rag/hitl 随 30 回写在案）。
- PR [#221](https://github.com/Cyning12/ops-desk-api/pull/221)：CI 绿 → merge master 85058f7（2026-10-10 · Asia/Shanghai）。
- 归档：task → done/（头部状态 done · TB1–TB8 勾选 · KPI/经验总结回填 · 修订表 CLOSE 行）；active README 登记表补行；Hub docs/tasks/done/README.md engineering 域表行+修订记录行补登；CLOSE 文档 docs/tasks/close/close_hitl_replan_carry_and_persist_guard_20261010.md 落盘。

## 交付摘要

| 项 | 内容 |
|---|---|
| **产出** | nodes.py +102/-7：_unlocked_preserved_rows（P=hitl_unlocked_ids∩plan行∩无终态∩非locked · dict 副本带回）· _stamp_host_plan preserved 形参（full=locked+preserved+plan · prefix/recoverable 仍仅随 locked · 空 preserved 逐字节不变）· supervisor 三路径接线（空 allowlist 短路+统一收口 · fallback-carry 零改）· _approved_fresh_for_subtask（镜像消费门：同一 TTL/归一/blocked_by 守卫 · 读异常 fail-open False+hitl_persist_guard_read_failed warning）· _persist_hitl 命中→hitl_persist_guard_skip info+continue |
| **验收** | TB1–TB6 14 枚新断言全绿（含 TB6⑦ Db store 真 PG 非 skip）· TB4 空 unlocked 五键序列化逐字节对拍 · TB7 回归存续（T1 34+T2 39+B1 面合计 107 枚全绿）· TB8 live 三 run：保号消费命中原 sid（568d288a 四轮 consumed · a0850a8e token+echo 真执行）· hitl_persist_guard_skip 每次重放在案 · 终态 done{resumed}+零 pending |
| **红线** | 消费门/_delegation_issue_block_reason/auto_resume/store.py/resume.py diff 空 · interrupt 语义段零 diff · 零新表零新列零 payload 新键零 SSE 事件类型（freeze 存续）· 空 unlocked 与 master 逐字节零 diff |

## 钉案登记（三条 · 详见 CLOSE 文档第四节）

1. resume.py:131 resumed 语义——TB8 字面 done{completed} 结构性不可达 · 语义终态达成（event_store.py:99-107）· 面外既有设计。
2. approved 路径自然完成双重结构性不可达（LLM 盲循环 + router.py:328-357 _collect_decisions 恒 replan）——建议另立后续 task。
3. 仓级 verify EXIT=2（92 缺口 · done/ 遗留档基线 · 主仓同）——仓级钉案照登不新增；30 自报「verify EXIT=0」不准（疑管道吞退出码）。

## 质量钉（CLOSE 机械闸复跑）

- task lint（done/ 路径）：PASS · EXIT=0。
- 仓级 verify：EXIT=2 BLOCKED（92 缺口 = 仓级基线 · 主仓 master 同 · 照登不新增）。
- graph-compile：EXIT=0（generated_at 日期噪音已 checkout 还原 · 不入 commit）。

## 移交

- 签发审批消费回路（T3+T1+T2+本 task）SPEC v1 偏差裁定全落地；active 目录无在途 task。
- 钉案②后续 task 裁定权留维护者；worktree t-hitl-carry-and-persist-guard 与分支 task/hitl-carry-and-persist-guard 由本 CLOSE 清理（git worktree remove --force + 本地/远端分支删）。
