# task_memory_extract_calibration · 20-task-audit 审查文（R1 · 终轮）

| 项 | 内容 |
|----|------|
| **日期** | 2026-09-22 |
| **帽** | 20-task-audit（R1 · 零阻塞即终轮） |
| **对象** | `docs/tasks/active/task_memory_extract_calibration.md`（worktree excal） |
| **对照** | SPEC-memory-golden-eval §2 D5 · tuned live 报告 · weight-tuning 循环先例 |

## 结论摘要

| 维度 | 结论 |
|---|---|
| **内容** | ✅ **零阻塞**（循环协议承 weight-tuning 实战验证骨架 + 校准特有双纪律：version bump 归因 · 防泄题禁令——这两条正是 prompt 调参特有的作假面） |
| **流程闸** | HG-AUDIT-R1=**pending** · HG-GRAPH-MODULES=**pending**（均 00 代录） |
| **思考轮** | PASS（R0–R5 闭合 · R3 对「supersede=1.0 可能够不到」的诚实路径预判是成熟信号） |
| **task lint** | PASS |

## 核对项（全表）

| 核对 | 结论 |
|---|---|
| 可改面/不可改面 | 钉死且最小：prompt 资产正文+version · 可选别名表（数据驱动触发）；金样/闸/管道/融合/开关默认值全禁 |
| 防作假面 | 金样一字不改（移动球门）+ 金样原文禁入 prompt（泄题）+ version bump（归因断链）+ 确认轮全量（sweep 冒充）+ 变差轮留痕（藏丑）——五条全覆盖 |
| 病灶-手段对齐 | live 数据两大病（key 漂移 · 准入过松）都有对应手段位（prompt key 目录/few-shot · 别名表备选）；首轮「先看逐条失败 detail 再动笔」写进协议 |
| 回归哨兵 | top3≥0.8 每轮必看——防校准波及已定稿向量侧 |
| 停止条件 | 达标/收敛/上限/异常四停则与 weight-tuning 一致且量化 |
| failure_paths | 8 行四要素齐全 · 五条作假面各有拒收行 |
| 验收 | 8 项可执行 · 锚=确认轮报告+日志 version 对应 |
| base | origin/master 07b0eba（已含全部记忆轨 · 无叠放 · 吸取 restack 教训：merge-base 核验不需要） |

## 审查结论

**签收（内容侧）** · R1 即终轮，审查关闭。两道流程闸 00 代录。

## 维护者签闸（20 后 · 30 前）

- [x] 已读 R1 审查结论
- [ ] task 人工闸表 **HG-AUDIT-R1** → approved（00 代录）
- [ ] `01_modules.md` **HG-GRAPH-MODULES** 新行（memory 行备注 · 00 代录）
- [ ] 下发 30（worktree `../ops-desk-api-excal`）
