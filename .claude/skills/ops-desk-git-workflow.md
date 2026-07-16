---
name: ops-desk-git-workflow
description: Ops Desk 项目的 Git 分支与 PR 流程约束：禁止直接在 main 改码，必须使用任务分支并通过 PR 合并。
triggers:
  - 用户提到分支、PR、merge、main 分支
  - 用户要求直接提交到 main
  - 开始新任务前
  - 任务完成需要合并时
---

# Ops Desk Git 工作流

## 核心规则

**禁止直接在 `main`/`master` 分支上修改代码。** 所有代码改动必须通过任务分支 + Pull Request 合并。

## 分支命名

| 类型 | 命名 | 示例 |
|---|---|---|
| 功能任务 | `task/<short-description>` | `task/llm-provider-and-chat-answer` |
| 缺陷修复 | `fix/<short-description>` | `fix/chat-sse-reconnect` |
| 文档/图谱 | `docs/<short-description>` | `docs/update-tech-graph` |

## 标准流程

1. **创建分支**
   ```bash
   git checkout main
   git pull origin main
   git checkout -b task/<short-description>
   ```

2. **在任务分支开发**
   - 所有 Write/Edit 操作都在任务分支上进行。
   - 每次代码变更同步更新 `docs/_tech_graph/*.graph.yaml`。
   - 提交前运行 `./scripts/graph-compile.sh`。

3. **提交并推送**
   ```bash
   git add -A
   git commit -m "type(scope): description"
   git push -u origin task/<short-description>
   ```

4. **创建 Pull Request**
   - 目标分支：`main`
   - PR 标题遵循提交信息格式：`type(scope): description`
   - PR 描述包含：变更摘要、图谱更新说明、测试/检查结论

5. **合并前检查**
   - `pytest tests` 通过
   - `ruff check app tests` 通过
   - `./scripts/graph-compile.sh` 通过
   - CI 全部绿色

6. **合并后清理**
   ```bash
   git checkout main
   git pull origin main
   git branch -d task/<short-description>
   ```

## 禁止行为

- ❌ `git push origin main`
- ❌ 在 `main` 分支直接 Edit/Write 代码
- ❌ 绕过 PR 流程合并代码
- ❌ 任务分支长期不合并（超过 1 周需说明）

## 紧急修复

即使紧急修复也使用 `fix/` 分支，通过 PR 合并。唯一例外：仓库完全无法工作且无法创建分支时，需人工显式授权并在修复后立即补 PR 审查记录。

## 与 harness 的配合

- 每个 task 对应 `docs/tasks/active/task_<slug>.md`。
- 30 改码前确认 `HG-AUDIT-R1` 与 `HG-GRAPH-MODULES` 状态。
- 40 自检后提交 PR，PR 合并视为 task 关账。
