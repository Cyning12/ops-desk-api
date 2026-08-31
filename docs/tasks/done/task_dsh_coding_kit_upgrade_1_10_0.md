# Task：dsh-coding-kit 升级 1.10.0（sync prompts + re-anchor 条文）

> **状态**：completed（2026-08-31 CLOSE · PR [#98](https://github.com/Cyning12/ops-desk-api/pull/98) MERGED）  
> **类型**：基础设施 / harness 过程轨升级（minor）  
> **前置**：manifest / package 钉 `1.9.1`；npm 最新 **`1.10.0`**  
> **分支**：`task/dsh-coding-kit-1-10-0`  
> **执行模式**：Open Folder = **ops-desk-api**；过程轨；不改 `app/`

---

## Harness 元信息

| 字段 | 值 |
|------|-----|
| **task_slug** | `dsh-coding-kit-upgrade-1-10-0` |
| **git_branch** | `task/dsh-coding-kit-1-10-0` |
| **implement_repo** | `ops-desk-api` |
| **test_strategy** | `required` |
| **test_strategy_note** | `npx dsh-coding-kit@1.10.0 check` / `upgrade` / `sync prompts` / `verify --task`；`./scripts/graph-compile.sh` exit 0；CI 钉 `@1.10.0` |
| **code_quality_bar** | `not_applicable` |
| **graph_change_layer** | `none` |
| **graph_delta** | `none` |
| **graph_delta_note** | 过程轨升级；compile 产物 `generated_at` 可能因 kit ≥1.9.2 内容戳改写，不改 YAML 源 |
| **wiki_delta** | `none` |
| **wiki_delta_note** | 本波不晋升 coding_wiki；FEEDBACK 走 evidence + doc-health/feedback |
| **experience_capture** | `recommended` |
| **kpi_aggregator** | `CLOSE` |
| **invoke_retention_profile** | `minimal` |
| **required_invoke_hats** | `30` |
| **close_pr_policy** | `required` |
| **related_pr** | `#98` |

### 人工闸

| human_gate_id | status | blocks_hats | 说明 |
|---------------|--------|-------------|------|
| HG-TASK-DRAFT | approved | 22-R1, 30 | 2026-08-31 维护者签收「重新更新到 1.10.0」 |
| HG-AUDIT-R1 | approved | 30 | 过程轨 · 不改 app/ · 同窗代签 · 见 reviews R1 |

---

## 背景与目标

把本仓 **dsh-coding-kit 1.9.1 → 1.10.0**，消费：

1. **`sync prompts`**（关闭「upgrade 不同步 prompts」旧 FEEDBACK）  
2. **re-anchor / 00 delegate-only** 新 FRAGMENT + `00-orchestrator` 链  
3. **graph compile `generated_at` 内容戳**（≥1.9.2，同字节幂等）  
4. 精确钉 `package.json` + CI `@1.10.0`  
5. **保留** 仓内 `HG-GRAPH-MODULES` 行补丁（勿被 `--force` 冲掉）

## 范围

1. `package.json` / lock 钉 **`1.10.0`（exact）**；`.cyning-harness/manifest.json` upgrade  
2. `refresh-ide-blocks` dry-run（local 块零改写）  
3. `sync prompts --yes`；冲突文件：**合入 kit 增量**，**保留** GATE_VERIFY / STOP 模板中的 `HG-GRAPH-MODULES` 行；10-spec / 20-spec-audit 若仅 skill 链差异可保留仓内相对链  
4. 手补 `docs/_tech_graph/shared/99_mermaid_protocol.md` §0 `generated_at` 内容戳说明（非 sync 白名单）  
5. CI `lint-wiki-delta.yml` → `@1.10.0`  
6. `skills install`（`.dsh/skills` 落点；是否入库另记）  
7. `verify --task` · `graph-compile.sh` · FEEDBACK

## 非范围

- 不改 `app/`  
- 不搬迁根级裸 `SPEC-*.md`  
- 不 `npm publish`；不擅自 `gh pr merge`  
- 不以 `--force` 覆盖带 `HG-GRAPH-MODULES` 的本地补丁

## 验收标准

- [x] manifest `1.10.0` · `from_version=1.9.1`
- [x] `package.json` / CI 钉 `1.10.0`
- [x] 新 FRAGMENT `FRAGMENT_hat_reanchor` / `FRAGMENT_00_delegate_only` 已落地
- [x] GATE_VERIFY / STOP 仍含 **HG-GRAPH-MODULES** 行
- [x] `npx dsh-coding-kit@1.10.0 check --target .` 通过（已是最新）
- [x] `verify --task` 本 task PASS
- [x] `./scripts/graph-compile.sh` exit 0
- [x] FEEDBACK 落盘

## failure_paths

| 触发 | 行为 |
|------|------|
| sync `--force` 冲掉 HG-GRAPH-MODULES | 拒；手合后 FEEDBACK |
| graph-compile 仅时间戳/戳形态 diff | 接受并入库（内容戳为预期） |
| 兄弟 active task 挡 wiki lint | 本波不默认 `--with-wiki-lint` |

### 自检结论

| 命令 | 退出码 |
|------|--------|
| `check`（升级后） | 0（已是最新） |
| `verify --task` | 0（PASS） |
| `graph-compile.sh` | 0 |
| `sync prompts --yes` | 0（written=2 · conflict 手合） |

### KPI

Task_KPI%: 100 · kit 钉 1.10.0 · re-anchor / 00-delegate 已 sync · HG-GRAPH-MODULES 行保留 · skills 落 `.dsh/` 不入库

## CLOSE

| 项 | 值 |
|------|-----|
| PR | [#98](https://github.com/Cyning12/ops-desk-api/pull/98) **MERGED** 2026-08-31 |
| 启用核对 | `check` 已是最新 1.10.0 · `sync prompts` dry-run：re-anchor / 00-delegate 在 skip；conflict 仅仓内 HG-GRAPH-MODULES 手合件（GATE_VERIFY / STOP / 10-spec / 20-spec-audit）· skills：`.dsh/skills` 含 `harness-00-delegate-only` / `harness-hat-reanchor`（`.gitignore` · 不入库） |
| Hub | 本文件 + `docs/tasks/done/README.md` harness 域行 |
| 归档 | 2026-08-31 · 00 关账 · 维护者 Prompt 授权 |
