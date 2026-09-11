# Invoke：30（含 40）· dsh-coding-kit-upgrade-2-1-0

---

## 元信息表

| 字段 | 值 |
|------|-----|
| hat_id | 30（含 40） |
| task_slug | `dsh-coding-kit-upgrade-2-1-0` |
| task_paths | `docs/tasks/active/task_dsh_coding_kit_upgrade_2_1_0.md` |
| related_review_or_none | `docs/harness/reviews/task_dsh_coding_kit_upgrade_2_1_0_audit_R1_20260910.md` |
| git_branch | `task/dsh-coding-kit-2-1-0` |
| created_utc_or_local | 2026-09-10 |
| notes | 维护者「确认执行」；过程轨；**未**改 `app/` 业务逻辑（仅测试钉版） |

---

## 人工闸扫描（GATE_VERIFY · 首输出）

| human_gate_id | task表status | 用户/invoke声称 | 一致？ | blocks_30 | 30可开工？ |
|---------------|--------------|-----------------|--------|-----------|------------|
| HG-TASK-DRAFT | approved | 「确认执行」 | Y | Y | Y |
| HG-AUDIT-R1 | approved | 00 代签 + R1 文 | Y | Y | Y |
| HG-GRAPH-MODULES | —（graph_change_layer=none） | — | — | N | Y |

reviews：`task_dsh_coding_kit_upgrade_2_1_0_audit_R1_20260910.md` 存在？ **是**

pre-30 invoke：`required_invoke_hats=30`（minimal）→ 无 pre-30 硬闸。

结论：**可进入 30**

---

## 交付摘要（执行后回填）

- **升级**：`1.10.0` → **`2.1.0`**（`.coding-kit/manifest` · package exact · CI `@2.1.0`）
- **布局**：新根 `.coding-kit/`；legacy `.cyning-harness/` 只读保留；`.gitignore` 对齐
- **sync prompts**：written=0；conflict 4 手留（含 HG-GRAPH-MODULES）
- **skills install**：skipped=8 → `.dsh/skills`（gitignore）
- **host update**（维护者手跑）：`npx dsh-coding-kit@2.1.0 host update --tools cursor,claude,dsh --yes` → `.cursor/commands` · `.cursor/skills` · `.cursor/rules/05-kit-starter.mdc` · `.claude/commands/kit` · `.claude/skills` · `.dsh/skills/kit-*`
- **验证**：verify PASS · check 已是最新 · graph-compile exit 0 · pytest harness_cli 32 passed
- **FEEDBACK**：`docs/harness/evidence/FEEDBACK_dsh_coding_kit_2_1_0_from_ops_desk_api_20260910.md` · doc-health `2026-09-10_2.1.0_layout-coding-kit-upgrade.md`
- **下一步**：commit（排除无关 `uv.lock`）· push · PR → master
