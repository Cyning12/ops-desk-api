# task_p2a_t4_verification_smoke · 20-R1 审查文（2026-11-16）

## 元信息

| 键 | 值 |
|---|---|
| task | docs/tasks/active/task_p2a_t4_verification_smoke.md |
| 审查轮 | R1（终轮） |
| 审查帽 | 20-task-audit |
| 授权依据 | issue Cyning12/ops-desk-workspace#23（m03064 夜间授权窗口）+ 08-p2a-tools-design.md 终稿 §6/§7 T4 行 |

## 结论摘要

- **内容面**：GO · 零内容阻塞。
- **流程闸**：HG-AUDIT-R1 / HG-GRAPH-MODULES / HG-PILOT-OPSDESK-GLAYER 三行 approved（task 人工闸表 · 授权范围零新增 · 承 T1/T2 同窗口先例）。

## 核对项

| 项 | 结论 |
|---|---|
| 范围 vs 08 §7 T4 行 | 一致：回归 + 四样例一次跑完 + 验收记录落盘；CI 结构断言与人工冒烟双件制齐全（§6） |
| 非范围 | 承 §8：app/ 零改动 · 图/SSE/依赖/DDL/图谱全禁；description 修订与 mock 收窄列入失败处置另波 · 不越界 |
| 验收标准 | 全部可机断（断言绿/电池绿/对拍恒等/ruff/CI 四绿/落盘路径）；(a)-(f) 判定与三级裁定口径照 §6 原文 |
| failure_paths | 覆盖 §6 失败处置四路（选错→description · mock 误选→收窄 · 表达力→§3 重估 · 数据错→退 T1/T2）+ Langfuse 不可达与无 GUI 两条环境偏差路径 |
| test_strategy | mock LLM 范式有既有真源（tests/test_lg_rag_supervisor_capability_catalog.py）· 五键 blank 协议承 T1/T2 |
| 必读列表 | 08 设计 §3/§6/§7/§8 · catalog 测试 · nodes.py/config.py · T2 task 档 · 齐全 |
| 行为变更类「旧测 grep 影响面」 | 不适用（纯新增测试文件 · 零行为变更） |
| 思考轮控制 | R0-R5 槽位齐 · 点名小节齐 · actual_last_round=R5 · early_stop 理由成立（设计终稿即审计真源 · 全机断） |
| invoke 留档 | default 集合 {10,30,40} · 与委派要求一致 |

## 阻塞 / 非阻塞

- 阻塞：无。
- 非阻塞提醒一条：结构断言中「四样例 → 预期 capability」对照只能钉 wiring 与表达力，真 LLM 选择质量以冒烟 (a)-(f) 判定为准；两处口径勿混（审查已确认 task 档范围 1/2 分写清楚）。

## 签收

R1 审查通过 · 本论为终轮（签收关闭）。30 可依 task 表 approved 状态开工。
