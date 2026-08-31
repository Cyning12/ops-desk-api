# FEEDBACK · dsh-coding-kit 1.10.0 · from ops-desk-api

> **日期**：2026-08-31  
> **业务仓**：`ops-desk-api`（分支 `task/dsh-coding-kit-1-10-0`）  
> **起点**：manifest / package `1.9.1` → 目标 **`dsh-coding-kit@1.10.0`**  
> **对照**：`/tmp/kit-cmp/191` vs `/tmp/kit-cmp/110`（`npm pack`）  
> **执行**：本窗 · 过程轨；未改 `app/`  
> **触发**：维护者「重新更新，现在应该是 1.10.0」

---

## 1. 结论

| 项 | 结果 |
|----|------|
| manifest | **1.10.0**（`from_version=1.9.1` · preset/ide 保留） |
| package / CI | 精确钉 `1.10.0` · `lint-wiki-delta.yml` `@1.10.0` |
| AGENTS/CLAUDE local 块 | **零改写**（refresh dry-run rewrites=0 · skipped_local=1） |
| upgrade 幂等 | **PASS**（二跑 `1.10.0→1.10.0`；仍刷新 `upgraded_at`） |
| `sync prompts` | **已接线**：`--yes` 写入 2 个新 FRAGMENT；5 conflict **未**盲 `--force` |
| HG-GRAPH-MODULES 补丁 | **保留**（GATE_VERIFY / STOP 手合） |
| graph compile | exit 0 · md `generated_at` → `sha256-<16hex>` |
| severity=block | **无** |

**判定**：1.9.1→1.10.0 minor 在本仓成立。旧 FEEDBACK「upgrade 不同步 prompts」被正式 `sync prompts` **关闭**（upgrade 仍只写 manifest，但会提示跑 sync）。

---

## 2. 1.10.0 增量（相对 1.9.1）

| 面 | 内容 |
|----|------|
| CLI | `sync prompts`（白名单 prompts + TASK_TEMPLATE；conflict 需 `--force`） |
| prompts | `FRAGMENT_hat_reanchor_v1_zh` · `FRAGMENT_00_delegate_only_v1_zh` · `00-orchestrator` 链 |
| skills | `harness-hat-reanchor` · `harness-00-delegate-only`（`skills install` → `.dsh/skills`） |
| graph（含 1.9.2） | compile md `generated_at` 内容戳（幂等） |

---

## 3. sync prompts 实证

```text
add:     FRAGMENT_hat_reanchor_v1_zh.md · FRAGMENT_00_delegate_only_v1_zh.md
skip:    10-task / 20-task-audit / 30 / 40 / TASK_TEMPLATE（同内容）
conflict: 00-orchestrator · 10-spec · 20-spec-audit · FRAGMENT_30_gate_verify · TEMPLATE_30_gate_stop
```

处理：

- `00-orchestrator`：采 kit（仅增 re-anchor 节）  
- GATE_VERIFY / STOP：**手合** kit 接线说明文案 + **保留** `HG-GRAPH-MODULES` 行  
- 10-spec / 20-spec-audit：保留仓内相对 md 链（kit 指向 `../../skills/...`，与本仓 `docs/skills` 产品 skill 布局不符）

---

## 4. 摩擦 / 建议（给 kit）

| ID | 主题 | 严重度 | 说明 |
|----|------|--------|------|
| R-sync-local | conflict 含仓特异闸行 | P3 | 建议 sync 报告对「仅增行」给出 merge hint；或允许 consumer overlay |
| R-graph-json | 本仓 `graph_yaml_to_json.py` 仍 wall-clock + 日更 freeze_id | P3 | 与 kit md 内容戳不一致；非本包 bug |
| R-upgrade-hint | upgrade 成功后提示 sync | — | **已做**（本波验证到） |

---

## 5. 命令与退出码

| 命令 | exit |
|------|------|
| `dsh-coding-kit@1.10.0 check`（升级前） | 0（可升级；裸 SPEC WARN 8） |
| `refresh-ide-blocks --dry-run --json` | 0（rewrites=0） |
| `upgrade --yes` | 0（1.9.1→1.10.0） |
| `sync prompts --yes --json` | 0（written=2 · conflict=5） |
| `skills install --force` | 0（copied=8 → `.dsh/skills`；已 `.gitignore`） |
| `verify --task <本task>` | 0（PASS） |
| `check`（升级后） | 0（已是最新） |
| `./scripts/graph-compile.sh` | 0 |

所有 npx 均带 `npm_config_cache=/tmp/npm-cache-lg`。
