# invoke · 40 · memory-extract-calibration · R1 核验 FAIL（退回 30）

| 项 | 内容 |
|----|------|
| **时间** | 2026-09-22 |
| **帽** | 40（子 Agent 独立核验 · 未复信 30） |
| **结论** | **FAIL** · 阻塞项 = D 防泄题；其余纪律面全绿（藏丑核查 PASS · 确认轮 IDENTICAL · 金样零 diff · 零越面 · 351 passed · 清场 0） |

## 退回项（已 send_message 退回 30 续执行）

1. **（阻塞）** prompt v3 few-shot ①②④⑤ = 金样 SR01/SR06/NG06/NG04 模板同构换值（近义改写泄题）→ v3 的 0.96/0.0714 对该四类用例不度量泛化 → 须真·新文本重写 + bump v4 + 重跑连续 2 轮四门槛
2. （次要）run_eval 报告头部补 `prompt_version` 字段（归因链契约）
3. （次要）校准日志补记 incident-feed 示例引入轮次

## 有价值的环境发现（40 实测）

.env 里 `MEMORY_FACTS_ENABLED=true` 会被 pydantic 读入——仅 unset shell 旗标不够，pytest 须**显式置 false**。已写入 30 续跑指令。再次佐证候选卫生 task：conftest 隔离 MEMORY_* 旗标。

## 流程注记

40 FAIL → 退回 30 整改 → 整改后 40 做 R2 复审（防泄题复检 + 新确认轮真实性）。30 剩余 live 预算 5 轮（上限 8 已用 3 · 作废轮计入成本）。
