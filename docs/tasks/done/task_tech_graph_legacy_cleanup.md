# Task：tech-graph / harness 过渡历史产物清理

> **状态**：completed（PR #61 MERGED · 已归档；2026-08-26）  
> **类型**：过程卫生 / 文档与 compile 过渡清理  
> **背景**：Phase α C1 根 `graph.json` 双写、C2 `01_struct.md` stub、`.cyning-harness` 过时 QUICKREF/refresh 备份、`scripts/legacy` 切命令面回滚 bak 已无消费价值  
> **分支**：`chore/tech-graph-legacy-cleanup`  
> **执行模式**：维护者本窗授权「新建轻 task · 签闸 · 自行 30+40 · PR · CI 绿 merge · 归档」

---

## Harness 元信息

| 字段 | 值 |
|---|---|
| **task_slug** | `tech-graph-legacy-cleanup` |
| **git_branch** | `chore/tech-graph-legacy-cleanup` |
| **implement_repo** | `ops-desk-api` |
| **test_strategy** | `required` |
| **test_strategy_note** | `./scripts/graph-compile.sh` exit 0；根目录不再生成 `docs/_tech_graph/graph.json`；`shared/graph.json` 仍为真值；不跑业务 pytest（无 app/ 改动） |
| **code_quality_bar** | `not_applicable` |
| **graph_change_layer** | `none` |
| **graph_delta** | 删根 `graph.json` 双写 + 删 `01_struct.md` stub；更新 README / `02_version` / `99_mermaid_protocol` / `01_modules` 过渡文案；**不改**任何 `*.graph.yaml` 拓扑 |
| **wiki_delta** | `n/a` |
| **review_hat** | `20` |
| **required_invoke_hats** | `10,30,40` |
| **invoke_retention_profile** | `default` |
| **orchestration** | 轻量单棒 |

### 人工闸

| human_gate_id | status | blocks_hats | 说明 |
|---|---|---|---|
| HG-TASK-DRAFT | approved | 22-R1 | 2026-08-26 00 代签（维护者本窗授权） |
| HG-AUDIT-R1 | approved | 30 | 2026-08-26 00 代签；见 `task_tech_graph_legacy_cleanup_audit_R1_20260826.md` |
| HG-GRAPH-MODULES | approved | 30 | 不增删一级模块；真值仍 `l1/01_modules.md` |

---

## 背景与目标

停用已过期的过渡约定，只保留现行真值路径，避免 Agent/人继续读到双写副本或 stub。

---

## 范围

1. **停 C1 根双写**：`scripts/graph_yaml_to_json.py` 仅写 `shared/graph.json`；删除 `docs/_tech_graph/graph.json`；更新 `graph-compile.sh` / README / `02_version` / `99_mermaid_protocol` 相关文案。
2. **删 C2 stub**：删除 `docs/_tech_graph/01_struct.md`；`l1/01_modules.md` 去掉「根 stub」句；**不**批量改写历史 done/invoke 旧链接（保留历史字面）。
3. **清 `.cyning-harness` 可删项**：删 `QUICKREF.md`（文内已写可手动删除且命令过时）；删 `backups/refresh-ide-blocks/**`；`.gitignore` 增加 `backups/`（保留 `profile.json` / `manifest.json`）。
4. **清 `scripts/legacy/*.bak`**：目录已无回滚需要；删除 bak + README（或整目录），并去掉 `99_mermaid_protocol` 等对 legacy 路径的强依赖句（可改为一句「迁移已完成」）。

## 非范围

- 改任何 `*.graph.yaml` 节点/边/anchors
- 改 `app/` 业务代码；不动 untracked `app/tools/`
- 批量改写 `docs/tasks/done/**` / 历史 invoke 中的 `01_struct` 旧字面
- 升级 kit / 改 `profile.json` tracks

---

## 验收标准

- [x] `docs/_tech_graph/graph.json` 不存在；compile 后亦不再生
- [x] `docs/_tech_graph/shared/graph.json` 仍由 compile 生成且 check 绿
- [x] `docs/_tech_graph/01_struct.md` 不存在；现行读序只指 `l1/01_modules.md`
- [x] `.cyning-harness/QUICKREF.md` 与 `backups/` 不存在；`profile.json` / `manifest.json` 保留
- [x] `scripts/legacy/` 无 `.bak`（目录可删空）
- [x] `./scripts/graph-compile.sh` exit 0；`git diff app/` 为空（相对本分支意图）

---

## failure_paths

| 触发 | 行为 | 可重试 | 用户可见 |
|---|---|---|---|
| 仍有工具硬读根 `graph.json` | 停删、先改调用方或保留双写并记偏差 | Y | compile/CI 失败或本地脚本报错 |
| 误删 `profile.json` / `manifest.json` | 从 git 恢复；拒合入 | N | kit upgrade/verify 异常 |
| 误改 `*.graph.yaml` | 打回 · 还原 | N | 超范围 diff |

---

## 依赖

- `docs/tasks/done/task_glayer_phase_alpha_api.md`（C1/C2 拍板）
- `docs/_tech_graph/README.md` · `LAYER_README.md`
- `scripts/graph_yaml_to_json.py` · `scripts/graph-compile.sh`

---

## 给执行帽（30）必读

本 task · FRAGMENT_30 · `graph_yaml_to_json.py` · `_tech_graph/README.md`

---

## 思考轮控制

| 轮 | 结论 | residual_risks |
|---|---|---|
| R0 | 范围=过渡清理；无拓扑变更 | none |
| early_stop | R0 足够（纯删除+文案） | none |

### R0

根双写与 stub 已明示过渡；kit 切命令面后 legacy bak / QUICKREF 过时。清理收益高于继续保留。

---

### 自检结论

> 30/40 · **PASS**（2026-08-26）

- 根双写已停；compile 后无 `docs/_tech_graph/graph.json`；`shared/graph.json` check 绿（9 graphs）
- stub / QUICKREF / backups / `scripts/legacy` 已删；`profile.json` · `manifest.json` 保留
- `00_main.md` Sub-graph Links 已改指 `l1/01_modules` + `shared/02_version`（kit 会保留 footer，勿回写成 01_struct）
- `app/` 无本 task 改动（`app/tools/` untracked 未纳入）

---

## CLOSE

| 项 | 内容 |
|---|---|
| 日期 | 2026-08-26 |
| 定稿 | 停根 graph.json 双写；删 01_struct stub；清 QUICKREF/backups 与 scripts/legacy |
| 归档 | `docs/tasks/done/task_tech_graph_legacy_cleanup.md` |
| PR | https://github.com/Cyning12/ops-desk-api/pull/61 |

## 修订记录

| 日期 | 说明 |
|---|---|
| 2026-08-26 | 初版（00 起草 + 维护者授权代签闸） |
| 2026-08-26 | 30+40 完成：过渡产物清理；自检 PASS |
| 2026-08-26 | 00 关账：PR #61 已合入 · 归档 done/ |
