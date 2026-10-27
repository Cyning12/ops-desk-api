# task 审查（R1 · 20-task-audit）：supervisor 重规划错误反哺

> **审查对象**：docs/tasks/active/task_supervisor_replan_error_feedback.md（45 行 · 草案 · HG-AUDIT-R1 pending）
> **审查人**：Harness 20（task-audit，书面审查）· 2026-10-27
> **审查性质**：只书面核对，不改 task 实质内容；发现问题列出，由维护者/10-task 决定。

## 元信息

- task 分支：task/supervisor-replan-error-feedback（feature）
- 根因钉案：2026-10-27 实测 run cb25483697624aafbb1cf864015c3b10（write 步 contract_missing_field → 重规划照抄错声明 → 两轮 budget_exhausted）
- 修复设计：A. _format_prefix_block 追加失败摘要行；B. step_contract.py 契约闸 detail 注入前驱可用字段清单
- **SPEC 缺失说明**：本 task 无独立 SPEC 文档。按仓内惯例（如 task_fix_delegation_pattern_fullmatch 等先例），以 task 文件自身为审查对象。经核对，task 自身含根因 / 修复设计（范围）/ 非范围 / 验收标准 / failure_paths / 人工闸表，**自足可审**。

## 结论摘要

| 维度 | 结论 |
|------|------|
| 内容审查 | **通过 · 零内容阻塞** |
| 流程闸 HG-AUDIT-R1 | **pending** → 须维护者签 task 表 → approved（本审查文不代签） |

## 逐项核对

### 1. 范围 / 非范围边界 —— 清晰 ✓

- 范围 = 修复设计两层（A 前缀失败摘要行 + B 字段级纠错回路），task 明写「本 task 全做」。
- 非范围 2 条：①manifest 补 output_schema（另立 task，本 task B 层先行止血）；②不改前缀不可变语义、不动 join/契约闸判定逻辑本身。
- 非范围①与根因第 3 点（无机器可读可用字段清单）的处理策略自洽：B 层用 `sorted(output.keys())` 止血而非改 manifest schema。

### 2. 验收标准 4 条 —— 可测、可执行 ✓（1 条轻微提示）

1. 复现 run cb2548 场景 → 第二轮重规划 prompt 含失败原因行 + 可用字段清单（spy/测试断言 prompt 内容）——**可测**，有现成先例：tests/test_hitl_approved_replan_quality.py:123-159 用 AsyncMock spy `complete.await_args` 断言 system prompt 内容。
2. 同场景第二轮 consumes 收敛到真实字段名、write 成功（评测或实测）——可执行；依赖 LLM 行为，可测性弱于其余 3 条，但「评测或实测」给了落地弹性，**可接受（记录项 P3）**。
3. 主路径零 diff：无 blocked 步时 prompt 逐字节不变（FP 口径沿用 preserved_block 先例，即 nodes.py:1176 注释的 FP-3 口径）——**可测**。
4. `pytest tests`、`ruff check` 绿——**可测**。

### 3. failure_paths 坐标 —— 逐条实测核对（2026-10-27 现码）✓

| task 声称 | 现码核对 | 结果 |
|---|---|---|
| step_contract.py:196-241 `gate()` | 函数体恰为 196-241 | ✓ 精确 |
| 拦截 detail 组装 :221-228 | :221-228 consumes 缺字段分支；:227 reason 分派 `BLOCKED_PREFIX_TOUCH if dep in prefix_ids else BLOCKED_CONTRACT_MISSING`；:228 detail = `f"前驱 {dep} 输出缺少字段 {missing}"` | ✓ 精确 |
| output 字段提取 :176-185（非 dict 不校验，「不替模型猜」） | `output_fields()` 176-185；docstring :179-181 原文即「不替模型猜」 | ✓ 精确 |
| nodes.py:784-804 `_format_prefix_block`；只在前驱 terminal 含 output 键时附终态摘要（:798） | :798 原文 `if term and "output" in term:` | ✓ 精确 |
| 保号块 :807-826 | `_format_preserved_block` 恰为 807-826 | ✓ 精确 |
| 重规划 prompt 组装 nodes.py:1170-1184 调 `_build_supervisor_suffix_system` | :1170 `if locked or preserved:` 分支起点，:1179-1184 调用（catalog_block + prefix_block + preserved_block 三输入） | ✓ 准确 |
| 200 字符截断摘要 | nodes.py:800-801 `summary[:200] + "…(截断)"` | ✓ |
| 根因 point 2：critic verdict `error_nonempty_allowlist` → `retry_planner`，verdict 不进重规划 prompt | `app/ops/strategy/critic.py:32 _REASON_NONEMPTY_ALLOWLIST = "error_nonempty_allowlist"`，:61 → retry_planner；supervisor prompt 输入仅 catalog + prefix + preserved（nodes.py:1169-1186），无 verdict 通道 | ✓ |
| 根因 point 1：被拦步 terminal 只有 blocked_by/error | nodes.py:943-951：`sc.gate` 拦截 → `_error_terminal(row, label（detail）)` + `blocked["blocked_by"] = reason`，无 output 键 → :798 跳过摘要 | ✓ |

### 4. 根因结论与修复设计自洽性 —— 自洽 ✓

- 根因 4 点 → 设计映射完整：A 层对应 point 1/2（模型不知失败、不知死因 → 前缀追加失败摘要行）；B 层对应 point 3/4（无字段清单、需自行映射推理 → detail/prompt 注入 `sorted(output.keys())` 清单，「猜字段名」变「从清单选字段名」）。
- 修复不动判定逻辑、不动前缀不可变语义，与非范围②一致；A 层只在 terminal 含 error/blocked_by 时追加行，与验收 3「无 blocked 步逐字节零 diff」相容。

## 发现的问题（均为记录项 · 非阻塞 · 退回与否由维护者裁定）

- **P1（轻微 · 实现提示）**：task 只点名 :221-228 consumes 分支，但 step_contract.py:230-240 produces 未兑现分支同样产出 `contract_missing_field`（:239-240）；且 :221-228 分支自身在 `dep in prefix_ids` 时产 `BLOCKED_PREFIX_TOUCH`（:227）。B 层「写进 blocked detail」对这两处同构分支是否同待未写明。鉴于非范围②允许改 detail 内容（不动判定），建议 30 实现时同构处理或显式排除即可，**不阻塞签闸**。
- **P2（K7 checklist 提醒 · 非机械闸）**：本 task 属行为变更类（改 prompt 组装 + blocked detail 内容），验收未单列「旧测 grep 影响面」项。审查已代查，影响面近零：
  - tests 中对 detail 文本「输出缺少字段」的断言 **0 hit**；test_step_contract.py:85/99 仅断言 detail 含 dep id / 缺字段名子串，追加可用字段清单不破坏。
  - prompt 断言测试（test_hitl_approved_replan_quality.py:123-159）只用成功 output 终态，A 层新增行不触发。
  - 据此**不因此退回 10-task**，记录在案。
- **P3（记录）**：验收 2 依赖 LLM 收敛行为，可测性弱于其余 3 条；「评测或实测」弹性措辞可接受。
- **P4（记录）**：无独立 SPEC，以 task 自足文件为审查对象（见元信息节）；仓内有先例，可接受。

## 结论

**内容审查：通过**（零内容阻塞；P1–P4 均为记录项）。

**流程闸：HG-AUDIT-R1 = pending**，本审查文不代签（人工闸，仅维护者可签）。

## 维护者签闸（20 后 · 30 前）

- [ ] 已读 R1 审查结论
- [ ] 在 task 人工闸表将 HG-AUDIT-R1 改为 approved（维护者 · 日期）
- [ ] commit task 文档或确认已签
- [ ] 再下发 Harness 30 Prompt

30 Agent 将以 task 表为准；pending 时必须拒开工（见 TEMPLATE_30_gate_stop.md）。
