# harness/prompts

从本目录向用户仓 **`docs/harness/prompts/`** 复制 **Starter 子集**。

## 标准流程（V2）

```text
人 + 00 chat 大纲
  → 10-spec R0–R9
  → 20-spec-audit + HG-SPEC-SIGNOFF（人签 · 可多轮）
  → 00 起草 P0 task
  → 10-task → 20-task-audit R1（↺ 10-task）→ HG-AUDIT-R1
  → 30 → 40（同 Agent · 自修重跑直至通过）
  → 50（↺ 30 · 可选）→ CLOSE
```

流程图源文件：[`DAG.md`](./DAG.md)

```mermaid
flowchart TD
    subgraph Human_Lane["人类工作区 · 输出控制闸"]
        H0["发起 00 Chat 大纲"]:::human
        H1{"人闸 1<br/>HG-SPEC-SIGNOFF<br/>规格书签署"}:::human
        H2{"人闸 2<br/>HG-AUDIT-R1<br/>任务审计签署"}:::human
    end

    subgraph Agent_Lane["Agent 工作区 · 过程透明化"]
        A1["10-spec-requirements<br/>拆解 R0-R9"]:::agent
        A2["20-spec-audit<br/>规格书面审计"]:::agent
        A3["00 起草 P0 Task<br/>任务初始化"]:::agent
        A4["10-task-requirements<br/>思考与验收路径"]:::agent
        A5["20-task-audit<br/>R1 自查与审计"]:::agent
        A6["30-execute-code<br/>代码实现"]:::agent
        A7["40-self-check<br/>自检闭环 规则分文件"]:::agent
        A8["50 复核<br/>最终审查"]:::agent
    end

    H0 --> A1
    A1 --> A2
    A2 --> H1
    H1 -->|"通过 / 签署"| A3
    H1 -->|"多轮打回重修"| A2

    A3 --> A4
    A4 --> A5
    A5 -->|"审计失败 · 修订"| A4
    A5 -->|"审计通过"| H2

    H2 -->|"通过 / 签署"| A6
    H2 -->|"打回重修"| A5

    A6 --> A7
    A7 -->|"自检失败 · 自修重跑"| A6
    A7 -->|"自检通过"| A8

    A8 -->|"可选打回 · 30"| A6
    A8 -->|"复核通过"| CLOSE(["CLOSE 归档"]):::endNode

    classDef human fill:#FFD2D2,stroke:#FF0000,stroke-width:2px
    classDef agent fill:#D4E6F1,stroke:#2980B9,stroke-width:2px
    classDef endNode fill:#D5F5E3,stroke:#27AE60,stroke-width:2px
```

详述：[`../docs/methodology/product/SDD_HAT_FLOW_v2_zh.md`](../docs/methodology/product/SDD_HAT_FLOW_v2_zh.md)

| 10 | 20 | 人闸 |
|----|-----|------|
| 10-spec | 20-spec-audit | HG-SPEC-SIGNOFF |
| 10-task | 20-task-audit | HG-AUDIT-R1 |

## Starter（本目录）

| 文件 | hat_id | 说明 |
|------|--------|------|
| [`10-task-requirements.md`](./10-task-requirements.md) | 10-task | task 思考 · 验收/failure_paths |
| [`10-spec-requirements.md`](./10-spec-requirements.md) | 10-spec | SPEC 思考 · R0–R5 |
| [`20-task-audit.md`](./20-task-audit.md) | 20-task-audit | reviews/ · HG-AUDIT-R1 |
| [`20-spec-audit.md`](./20-spec-audit.md) | 20-spec-audit | SPEC 书面审 · HG-SPEC-SIGNOFF |
| [`30-execute-code.md`](./30-execute-code.md) | 30 | 实现 · **含 40 自检闭环** |
| [`40-self-check.md`](./40-self-check.md) | 40 | 与 30 同 Agent · 规则分文件 |
| [`TEMPLATE_30_gate_stop.md`](./TEMPLATE_30_gate_stop.md) | — | 30 拒开工 |

Extended（00 / 50 / handoff / 链式 PROMPT）：工作区 `docs/harness/prompts/` · 见 [`SDD_HAT_FLOW_v2_zh.md`](../docs/methodology/product/SDD_HAT_FLOW_v2_zh.md) §4。

> **V2 改名（v2.4.0）**：`10-requirements.md` → `10-task-requirements.md`（+新增 `10-spec-requirements.md`）；`22-task-audit.md` → `20-task-audit.md`（+新增 `20-spec-audit.md`）。旧文件已删除；业务仓升级时 sync 会对残留旧帽 warn 提示人工删除。

## 修订记录

| 日期 | 摘要 |
|------|------|
| 2026-06-21 | V2 标准流程 · 30→40 同 Agent · 50/CLOSE 打回 |
| 2026-07-24 | V2 拆分收编：10→10-task/10-spec · 22→20-task-audit/20-spec-audit · 旧文件删除 |
| 2026-08-12 | 标准流程嵌入可渲染 Mermaid DAG（修围栏 / END 保留字 / 边标签引号） |
