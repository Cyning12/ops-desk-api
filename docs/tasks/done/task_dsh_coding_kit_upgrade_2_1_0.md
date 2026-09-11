# Task：dsh-coding-kit 升级 2.1.0（1.10.0 → 2.1.0 · `.coding-kit` 布局）

> **状态**：done  
> **类型**：基础设施 / harness 过程轨升级（major 跨度：含 1.11 布局 + 2.x host adapt）  
> **前置**：manifest / package 钉 `1.10.0`；npm 最新 **`2.1.0`**  
> **分支**：`task/dsh-coding-kit-2-1-0`  
> **执行模式**：Open Folder = **ops-desk-api**；过程轨；不改 `app/` 业务逻辑（测试钉版字符串除外）

---

## Harness 元信息

| 字段 | 值 |
|------|-----|
| **task_slug** | `dsh-coding-kit-upgrade-2-1-0` |
| **git_branch** | `task/dsh-coding-kit-2-1-0` |
| **implement_repo** | `ops-desk-api` |
| **test_strategy** | `required` |
| **test_strategy_note** | `npx dsh-coding-kit@2.1.0 check` / `upgrade` / `sync prompts` / `verify --task`；`./scripts/graph-compile.sh`；`pytest tests/test_capability_harness_cli.py`；CI 钉 `@2.1.0` |
| **code_quality_bar** | `not_applicable` |
| **graph_change_layer** | `none` |
| **graph_delta** | `none` |
| **graph_delta_note** | 过程轨升级；compile 产物可能因 kit 变化改写，不改 YAML 源 |
| **wiki_delta** | `none` |
| **wiki_delta_note** | 本波不晋升 coding_wiki；FEEDBACK 走 evidence + doc-health/feedback |
| **experience_capture** | `recommended` |
| **kpi_aggregator** | `CLOSE` |
| **invoke_retention_profile** | `minimal` |
| **required_invoke_hats** | `30` |
| **close_pr_policy** | `required` |
| **related_pr** | #132 |
| **review_hat** | `20` |

### 人工闸

| human_gate_id | status | blocks_hats | 说明 |
|---------------|--------|-------------|------|
| HG-TASK-DRAFT | approved | 22-R1, 30 | 2026-09-10 维护者「确认执行」升到 2.1.0 |
| HG-AUDIT-R1 | approved | 30 | 过程轨 · 禁改 app/ 业务逻辑 · 同窗代签 · 见 reviews R1 |

---

## 背景与目标

把本仓 **dsh-coding-kit 1.10.0 → 2.1.0**，消费：

1. **1.11 布局**：过程落盘根 `.coding-kit/`（legacy `.cyning-harness/` 只读保留）
2. **1.12 / 2.0 / 2.1**：host adapt + Skills/Commands parity（本波可选 `host apply`，默认不强制物化 expanded）
3. 精确钉 `package.json` + CI `@2.1.0`
4. `sync prompts`（保留仓内 `HG-GRAPH-MODULES` 行补丁）
5. Host capability 单测 mock 钉版字符串对齐

## 范围

1. `package.json` / lock 钉 **`2.1.0`（exact）**；`upgrade --yes` 写 `.coding-kit/manifest.json`
2. `.gitignore` 对齐 `.coding-kit/` local/backups（同 legacy 口径）
3. `refresh-ide-blocks` dry-run → 需要时 `--yes`；确认 local 块零改写
4. `sync prompts --yes`；冲突：**合入 kit 增量**，**保留** GATE_VERIFY / STOP 中的 `HG-GRAPH-MODULES`
5. CI `lint-wiki-delta.yml` → `@2.1.0`
6. `tests/test_capability_harness_cli.py` mock `1.10.0` → `2.1.0`
7. `skills install`（`.dsh/skills` · 不入库）
8. `verify --task` · `graph-compile.sh` · FEEDBACK

## 非范围

- 不改 `app/` 业务逻辑（仅测试钉版；`harness_cli.py` 仍读 env）
- 不搬迁根级裸 `SPEC-*.md`
- 不 `npm publish`；不擅自 `gh pr merge`
- 不以 `--force` 覆盖带 `HG-GRAPH-MODULES` 的本地补丁
- 不强制 `host apply --profile expanded`（**维护者已手跑** `host update --tools cursor,claude,dsh --yes` · core 物化入库）

## 验收标准

- [x] manifest（`.coding-kit/`）`2.1.0` · `from_version=1.10.0`
- [x] `package.json` / CI 钉 `2.1.0`
- [x] GATE_VERIFY / STOP 仍含 **HG-GRAPH-MODULES** 行
- [x] `npx dsh-coding-kit@2.1.0 check --target .` 通过（已是最新）
- [x] `verify --task` 本 task PASS
- [x] `./scripts/graph-compile.sh` exit 0
- [x] `pytest tests/test_capability_harness_cli.py` PASS
- [x] FEEDBACK 落盘
- [x] 维护者 `host update --tools cursor,claude,dsh --yes`（Cursor/Claude commands+skills · DSH kit-* skills）

## failure_paths

| 触发 | 行为 |
|------|------|
| sync `--force` 冲掉 HG-GRAPH-MODULES | 拒；手合后 FEEDBACK |
| `.coding-kit` 未写入 / upgrade 仍写旧根 | STOP · FEEDBACK kit |
| graph-compile 仅戳/格式 diff | 接受并入库（若有） |
| 兄弟 active task 挡 wiki lint | 本波不默认 `--with-wiki-lint` |

### 自检结论

| 命令 | 退出码 |
|------|--------|
| `check`（升级后） | 0（已是最新） |
| `verify --task` | 0（PASS） |
| `graph-compile.sh` | 0 |
| `pytest harness_cli` | 0（32 passed） |
| `sync prompts --yes` | 0（written=0 · conflict 手留） |

### KPI

Task_KPI%: 100 · kit 钉 2.1.0 · `.coding-kit` 布局落地 · HG-GRAPH-MODULES 行保留 · skills 落 `.dsh/` 不入库 · 待 PR/CLOSE
