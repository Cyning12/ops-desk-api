# Invoke：00 · host-harness-cli-capability（C1）

| 字段 | 值 |
|---|---|
| hat_id | 00 |
| task_slug | `host-harness-cli-capability` |
| task_paths | `docs/tasks/active/task_host_harness_cli_capability.md` |
| git_branch | `task/host-harness-cli-capability` |
| created_utc_or_local | 2026-09-01 |
| notes | 维护者 Prompt 授权（串行波次 4）；SPEC 06 已 signed（#111）；阶段 A 卫生已过；**00 不实现** |

---

## 阶段 A 卫生（摘要）

| 项 | 结果 |
|---|---|
| C0 done | `docs/tasks/done/task_host_comms_boundary_spec.md` · related_pr=#111 · 关账 #112 MERGED |
| active 残留 | 开工前 active 仅 README |
| master | `abdcddd`（#112）· 分支从最新 master 切出 |
| C1 依赖 | H2 ✓（capability gateway CLOSE）· SPEC 06 signed ✓（§10 依赖列满足） |

---

## GATE_VERIFY（00 扫描 · 非 30 改码）

| human_gate_id | task表status | 用户/invoke声称 | 一致？ | blocks_30 | 30可开工？ |
|---|---|---|---|---|---|
| HG-TASK-DRAFT | approved | 00 代签 · 维护者 Prompt 授权 | Y | N | 待 20 |
| HG-AUDIT-R1 | pending | 尚未 20 | Y | Y | **否** |
| HG-GRAPH-MODULES | approved | 不新增一级模块（capability 已存在 · 仅备注/flow） | Y | N | 待 R1 |

reviews：尚无 R1 → 30 不可开工。

结论：**派 10 → 20；00 不改 `app/` / `tests/`**。

## 签收栏

00 代签 · 维护者 Prompt 授权（`PROMPT_00_t4_close_through_c4_serial` · 串行波次 4）· 2026-09-01
