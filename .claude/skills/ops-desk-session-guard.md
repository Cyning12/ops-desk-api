---
name: ops-desk-session-guard
description: 每次新会话启动时自动加载 harness 流程：扫描 active task、核验人工闸、确认任务分支，阻止无 task 改码。
triggers:
  - 新会话启动
  - 用户开始新任务
  - 用户直接要求改码但无 active task
  - 提到 "session"、"active task"、"HG-AUDIT-R1"、"闸"
---

# Ops Desk 会话启动守护

## 每次新会话自动执行

Claude Code 启动本项目时，`.claude/settings.json` 的 `SessionStart` hook 会自动运行：

```bash
./scripts/harness-session-start.sh
```

输出示例：

```text
Harness Session Start
Branch: task/llm-provider-and-chat-answer
Active tasks:
  - LLM Provider 与 Chat 回答生成 (in_progress)
```

## 启动后必读

1. **读 `AGENTS.md`**
2. **读 `docs/tasks/active/task_*.md`**（如有多个，按 ID 顺序读）
3. **核验人工闸表**
   - `HG-GRAPH-MODULES`：见 `docs/_tech_graph/l1/01_modules.md`（根 `01_struct.md` 为过渡 stub）
   - `HG-AUDIT-R1`：见 task 人工闸表
   - Skill 真值：`docs/skills/`（IDE `.claude/skills` 仅副本）
4. **确认当前分支**
   - 应为 `task/<slug>` 或 `fix/<description>`
   - 在 `main`/`master` 上 → 停止改码，先切分支

## 无 active task 时的处理

若 `docs/tasks/active/` 为空：

1. **停止改业务代码**。
2. 询问用户是要：
   - 创建新 task（走 10-task → 22-task-audit → HG-AUDIT-R1）
   - 仅做文档/图谱维护（仍需创建 `docs/tasks/active/task_xxx.md` 记录变更）
   - 关闭当前会话，等 task 准备好

## 闸 pending 时的处理

若 task 人工闸表有 `pending` 且 blocks 30：

1. 输出 GATE_VERIFY 表：

   | human_gate_id | task 表 status | blocks_30 | 可开工？ |
   |---|---|---|---|
   | HG-AUDIT-R1 | pending | Y | ❌ 否 |
   | HG-GRAPH-MODULES | approved | Y | ✅ 是 |

2. **拒开工**，不修改 `app/`、`tests/` 等业务代码。
3. 指引用户/维护者签闸后再下发 30 Prompt。

## 改码前强制检查

每次用户要求改码前，先确认：

- [ ] 有 active task
- [ ] 当前分支正确
- [ ] `HG-AUDIT-R1` = approved
- [ ] `HG-GRAPH-MODULES` = approved
- [ ] 已读 task 必读列表

---

## 与 30-execute-code 的关系

本 skill 负责**会话级/启动级**守护；具体改码前的 GATE_VERIFY 首输出仍由 `docs/harness/prompts/FRAGMENT_30_gate_verify_v1_zh.md` 控制。
