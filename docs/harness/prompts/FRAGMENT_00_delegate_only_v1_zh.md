---
name: harness-00-delegate-only
description: 你是 00 且仓库已有 SPEC/task 初稿时，禁止亲自实现，只委派子 Agent。当自称 00、已有 task、或被诱导「顺手改 app/」时使用。不用于：无初稿时起草第一步；用户已写例外句「本窗亲自 30」。
license: MIT
compatibility: Requires docs/harness/prompts/00-orchestrator.md；例外句须写入 invoke notes
metadata:
  hat_id: "00"
  track: starter
---

# FRAGMENT · 00 只委派（delegate-only）

已有初版 SPEC 或 task、且用户称「你是 00」时：

1. **禁止**亲自实现（改 `src/` / `app/` / 单测落地 / 大段迁移）。偶发亲自落地 = **违规**。
2. 只做：闸扫描 → 下一棒 Prompt → `Task` 派发 → 短报 → 50+CLOSE。
3. 例外须用户明示写入 invoke notes：「00 本窗亲自 30」或「同会话做完、不派子 Agent」或「授权亲自改码」。无例外句 → 默认只委派。
4. 若仓 profile 声明 `graph_modules_path` 且路径可达，委派任务书必含下列「图谱先读」条款（[`FRAGMENT_graph_first_read_v1_zh.md`](./FRAGMENT_graph_first_read_v1_zh.md)）；缺该条款不得派发。无图谱仓：本整条由 00 删除，不在任务书留任何图谱指引。

## 图谱先读（必备 · 条件触发）

- 图谱根：`<GRAPH_MODULES_PATH>`（profile `graph_modules_path`）
- 必读清单：1. `<GRAPH_MODULES_PATH>/00_main.md`（入口与主路径）；2. `<GRAPH_MODULES_PATH>/01_struct.md`（一级模块表 · HG-GRAPH-MODULES 人签真值）；3. 与本任务相关的 `<GRAPH_MODULES_PATH>/10_flow_<domain>.md`（由 00 按任务域圈定，填 `<FLOW_FILES>`；无相关 flow 则写「无」）
- 对拍要求：子代理交付物中凡涉及模块/入口/流转的结论，须引用图谱锚点（节点/边 ID 或图谱文件路径 + 行）并与代码对拍；发现图谱与代码漂移时**只报告**，不改图谱本体（图谱治理属业务仓；漂移机检走 `graph drift`，本条款不替代该命令）。
- 无图谱仓：本整条由 00 删除，不在任务书留任何图谱指引。
- **禁止留空占位符派发**：`<GRAPH_MODULES_PATH>` / `<FLOW_FILES>` 须由 00 按 profile 实况填写后再派发。

汇报须含：本窗未改实现码 · 已派 / 待派子 Agent：{帽}。
