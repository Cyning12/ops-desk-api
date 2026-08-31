# Invoke：30（含 40）· dsh-coding-kit-upgrade-1-10-0

---

## 元信息表

| 字段 | 值 |
|------|-----|
| hat_id | 30（含 40） |
| task_slug | `dsh-coding-kit-upgrade-1-10-0` |
| task_paths | `docs/tasks/active/task_dsh_coding_kit_upgrade_1_10_0.md` |
| related_review_or_none | `docs/harness/reviews/task_dsh_coding_kit_upgrade_1_10_0_audit_R1_20260831.md` |
| git_branch | `task/dsh-coding-kit-1-10-0` |
| created_utc_or_local | 2026-08-31 |
| notes | 维护者令「重新更新到 1.10.0」；过程轨；**未**动 `app/` |

---

## 人工闸扫描（GATE_VERIFY · 首输出）

| human_gate_id | task表status | 用户/invoke声称 | 一致？ | blocks_30 | 30可开工？ |
|---------------|--------------|-----------------|--------|-----------|------------|
| HG-TASK-DRAFT | approved | 「重新更新，现在应该是 1.10.0」 | Y | Y | Y |
| HG-AUDIT-R1 | approved | 00 代签 + R1 文 | Y | Y | Y |
| HG-GRAPH-MODULES | —（graph_change_layer=none） | — | — | N | Y |

reviews：`task_dsh_coding_kit_upgrade_1_10_0_audit_R1_20260831.md` 存在？ **是**

pre-30 invoke：`required_invoke_hats=30`（minimal）→ 无 pre-30 硬闸。

结论：**可进入 30**

---

## 交付摘要（执行后回填）

- **升级**：`1.9.1` → **`1.10.0`**（manifest · package exact · CI `@1.10.0`）
- **sync prompts**：写入 `FRAGMENT_hat_reanchor` / `FRAGMENT_00_delegate_only`；`00-orchestrator` 采 kit；GATE_VERIFY/STOP **手合保留 HG-GRAPH-MODULES**
- **skills install**：8 → `.dsh/skills`（已 `.gitignore`）
- **验证**：verify PASS · check 已是最新 · graph-compile exit 0（md `generated_at` 内容戳）
- **FEEDBACK**：`docs/harness/evidence/FEEDBACK_dsh_coding_kit_1_10_0_from_ops_desk_api_20260831.md` · doc-health `2026-08-31_1.10.0_sync-prompts-closed.md`
- **未**：commit / push / PR（待授权）
