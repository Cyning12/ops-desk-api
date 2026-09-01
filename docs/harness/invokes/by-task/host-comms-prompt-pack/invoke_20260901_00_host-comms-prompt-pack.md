# Invoke：00 · host-comms-prompt-pack（C2）

| 字段 | 值 |
|---|---|
| hat_id | 00 |
| task_slug | `host-comms-prompt-pack` |
| task_paths | `docs/tasks/active/task_host_comms_prompt_pack.md` |
| git_branch | `task/host-comms-prompt-pack` |
| created_utc_or_local | 2026-09-01 |
| notes | 维护者 Prompt 授权（串行波次 5）；SPEC 06 signed（#111）· C1 #114 已合；阶段 A 卫生已过；**00 不实现** |

---

## 阶段 A 卫生（摘要）

| 项 | 结果 |
|---|---|
| C1 done | `docs/tasks/done/task_host_harness_cli_capability.md` · related_pr=#114 · 关账 #115 MERGED |
| active 残留 | 开工前 active 仅 README |
| master | `419d089`（#115）· 分支从最新 master 切出 |
| C2 依赖 | H4 ✓ · kit ≥1.10 FRAGMENT 仓内真值 ✓（`docs/harness/prompts/FRAGMENT_00_delegate_only_v1_zh.md` 等）· C1 ✓ |

---

## GATE_VERIFY（00 扫描 · 非 30 改码）

| human_gate_id | task表status | 用户/invoke声称 | 一致？ | blocks_30 | 30可开工？ |
|---|---|---|---|---|---|
| HG-TASK-DRAFT | approved | 00 代签 · 维护者 Prompt 授权 | Y | N | 待 20 |
| HG-AUDIT-R1 | pending | 尚未 20 | Y | Y | **否** |
| HG-GRAPH-MODULES | approved | 不新增一级模块（仅备注） | Y | N | 待 R1 |

结论：**派 10 → 20；00 不改 `app/` / `tests/`**。

## 签收栏

00 代签 · 维护者 Prompt 授权（`PROMPT_00_t4_close_through_c4_serial` · 串行波次 5）· 2026-09-01
