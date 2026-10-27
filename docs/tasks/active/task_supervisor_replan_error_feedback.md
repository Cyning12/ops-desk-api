# task（feature · HG-AUDIT-R1 已签 · 30 进行中）：supervisor 重规划错误反哺（契约闸失败原因 + 可用字段进 prompt）

> **状态**：HG-AUDIT-R1 维护者 2026-10-27 会话签收（00 转录入表）。
> **由来**：2026-10-27 实测 run cb25483697624aafbb1cf864015c3b10——write 步被契约闸拦（`contract_missing_field`：声明 `['title','body','status']`，前驱实际字段 `state`），重规划**原样照抄同一错误声明**，两轮后 `budget_exhausted` 收场。用户裁定方向：第一轮的错误必须反哺第二轮。
> **分支**：task/supervisor-replan-error-feedback（feature，非紧急 fix）。

## Harness 元信息

| 字段 | 值 |
|---|---|
| **task_slug** | `supervisor-replan-error-feedback` |
| **git_branch** | `task/supervisor-replan-error-feedback` |
| **implement_repo** | `ops-desk-api` |
| **test_strategy** | `required` |
| **test_strategy_note** | spy 断言重规划 prompt 内容 + 两轮闭环收敛 + 主路径逐字节零 diff；不连真网 |
| **code_quality_bar** | `L2_backend` |
| **graph_change_layer** | `none` |
| **graph_delta** | `n/a` |
| **wiki_delta** | `n/a` |
| **review_hat** | `20` |
| **required_invoke_hats** | `10,30` |
| **invoke_retention_profile** | `minimal` |
| **close_pr_policy** | `required` |

## 根因（已钉案，2026-10-27）

重规划 prompt 的全部输入 = 能力菜单 + `_format_prefix_block` + `_format_preserved_block`（app/ops/lg_rag/multi/nodes.py:1170-1184 调 `_build_supervisor_suffix_system`），三样里**零错误信息**：

1. `_format_prefix_block`（nodes.py:784-804）只在前驱 terminal **含 output 键**时附终态摘要（:798）；被拦步 terminal 只有 `blocked_by`/`error` → 前缀行光秃秃，模型**不知道它失败、更不知道为什么**。
2. critic verdict（`error_nonempty_allowlist` → `retry_planner`）只说「重试」，verdict 内容不进重规划 prompt。
3. 前驱真实产出仅以 200 字符截断 JSON 摘要形式存在，无机器可读「可用字段清单」。
4. 前缀不可变（:3 的 produces 声明改不了），模型自救只能改后缀 :4 的 consumes——需要它自己做字段名映射推理。

## 修复设计（两层，本 task 全做）

**A. 错误摘要进前缀块（最小修复）**：`_format_prefix_block` 对 terminal 含 `error`/`blocked_by` 的步追加 `→ 失败：{blocked_by}：{error 截断}` 行。模型至少知道「这步死了、死因是什么」。

**B. 字段级纠错回路（结构化反哺）**：契约闸拦截时（app/ops/lg_rag/multi/step_contract.py:221-228 `contract_missing_field` 分支）把**前驱实际可用字段清单**（`sorted(output.keys())`，来自 output_fields :176-185）写进 blocked detail；重规划 prompt 以结构化行注入：「前驱 X 实际产出字段 [number,title,state,...]；你声明的 ['status'] 不存在」。把「猜字段名」变成「从清单选字段名」。

## 非范围

- manifest 补 output_schema（源头消灭猜测，改 yaml schema + catalog 格式 + 校验）——更大scope，另立 task，本 task 的 B 层先行止血。
- 不改前缀不可变语义、不动 join/契约闸判定逻辑本身。

## 验收标准

1. 复现 run cb2548 场景（consumes 声明错字段名）→ 第二轮重规划 prompt 中含失败原因行 + 前驱可用字段清单（可用 spy/测试断言 prompt 内容）。
2. 同场景第二轮 consumes 能收敛到真实字段名，write 步执行成功（评测或实测）。
3. 主路径零 diff：无 blocked 步时 prompt 逐字节不变（FP 口径沿用 preserved_block 先例）。
4. `pytest tests`、`ruff check` 绿。

## failure_paths

- 契约闸分支坐标：step_contract.py:196-241 `gate()`；拦截 detail 组装 :221-228；output 字段提取 :176-185（非 dict 不校验，「不替模型猜」）。
- 前缀块组装：nodes.py:784-804；保号块 :807-826；prompt 模板 `_build_supervisor_suffix_system`。
- 200 字符截断可能与字段清单互补（摘要给内容、清单给字段名）。

## 人工闸表

| 闸 | 状态 | 备注 |
|---|---|---|
| HG-AUDIT-R1 | approved | 维护者 2026-10-27 会话签收，00 转录 |
| HG-GRAPH-MODULES | n/a | 不动图谱分层 |