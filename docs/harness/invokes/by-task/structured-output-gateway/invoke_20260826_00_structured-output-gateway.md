# Invoke：00 · structured-output-gateway（统筹启动）

> **用途**：维护者签收 SPEC 后，00 编排入口快照。00 **不实现** `app/` / `tests/` 业务代码。

---

## 元信息表

| 字段 | 值 |
|------|-----|
| hat_id | 00 |
| task_slug | `structured-output-gateway`（子 task slug 由 00 再定） |
| freeze_id | 无 |
| task_paths | （待 00 起草 `docs/tasks/active/task_*.md`） |
| related_spec | `docs/spec/agent-infra/SPEC-structured-output-gateway_v0.md` |
| related_review_or_none | 无（SPEC 维护者直签；子 task 须 20 R1） |
| git_branch | `task/structured-output-gateway`（建议） |
| worktree_root | `.` |
| created_utc_or_local | 2026-08-26 |
| notes | 维护者授权 00：签收过程文档、统筹 P0–P3、只派发与验收；颗粒度自定；Capability Gateway 排队不混入 |

---

## 派发计划（启动骨架 · 00 可改）

| 步 | 帽 | 执行者 | 产出 |
|---|---|---|---|
| 0 | 读 | 00 | SPEC + discussions + AGENTS；确认分支 |
| 1 | 切分 | 00 | 决定 P0–P3 → 若干子 task；写入本 invoke 修订 |
| 2 | 10-task | 00 | 首个子 task + 10 invoke + task lint |
| 3 | 20-task-audit | 00 书面审 | reviews R1；代签 HG-TASK-DRAFT / HG-AUDIT-R1 |
| 4 | verify | 00 | harness verify；pending → 拒 30 |
| 5 | 30+40 | **子 agent** | 仅当前子 task 范围 |
| 6 | 机械核对 | 00 | pytest / ruff / graph-compile / verify |
| 7 | 循环 | 00 | 下一子 task 直至 P0–P3 按切分完成 |
| 8 | 汇总 | 00 | CLOSE/PR（维护者授权）+ SPEC 修订记录落地状态 |

可复制 Prompt：`PROMPT_00_orchestrate.md`

---

## 交付摘要

- **当前**：SPEC 已签；等待 00 会话粘贴 Prompt 开工。
- **下一棒**：新 00 会话执行 `PROMPT_00_orchestrate.md` 复制区。

---

## 修订记录

| 日期 | 说明 |
|------|------|
| 2026-08-26 | 维护者双 SPEC 签收；优先 structured-output；落盘 00 Prompt |
