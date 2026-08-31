# Invoke：CLOSE · dsh-coding-kit-upgrade-1-10-0

| 字段 | 值 |
|------|-----|
| hat_id | CLOSE（00） |
| task_slug | `dsh-coding-kit-upgrade-1-10-0` |
| task_paths | `docs/tasks/done/task_dsh_coding_kit_upgrade_1_10_0.md` |
| git_branch | `chore/close-t2-kit-1-10-0` |
| created_utc_or_local | 2026-08-31 |
| notes | 00 代签 · 维护者 Prompt 授权 · 本窗未改 `app/` |

---

## 启用核对（1.10.0）

| 项 | 结果 |
|---|---|
| `npx dsh-coding-kit@1.10.0 check --target .` | 已是最新 |
| `sync prompts` dry-run | re-anchor / 00-delegate **skip**（已落地）；conflict 仅仓内 HG-GRAPH-MODULES 手合件 |
| `skills install` | `.dsh/skills` 含 `harness-00-delegate-only` / `harness-hat-reanchor`（`.gitignore` · 不入库） |
| GATE_VERIFY / STOP | 仍含 **HG-GRAPH-MODULES** 行 |
| PR | [#98](https://github.com/Cyning12/ops-desk-api/pull/98) **MERGED**（master `c10dd1b`） |
| dry-run | `CLOSE: READY`（`--allow-no-pr-merge`：本窗 `gh` TLS timeout） |
| `--yes` | **CLOSE: PASS** |

## 签收栏

00 代签 · 维护者 Prompt 授权 · 2026-08-31
