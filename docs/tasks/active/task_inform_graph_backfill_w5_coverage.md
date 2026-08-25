# Task：Inform 图谱补齐 · W5（anchors + coverage warn）

> **状态**：active（闸已签 · 00 代签授权）  
> **类型**：图谱 / 文档（无业务 Python 改码）  
> **范围真值**：`docs/spec/inform-graph-backfill/01_execution_waves.md` §W5 及对应模块/层 spec  
> **分支**：`task/inform-graph-backfill-w3-w6`（W3–W6 集成分支）  
> **执行模式**：00 编排/验收；30 子 agent 执行（与 W6 同子 agent 串行）

---

## Harness 元信息

| 字段 | 值 |
|---|---|
| **task_slug** | `inform-graph-backfill-w5-coverage` |
| **git_branch** | `task/inform-graph-backfill-w3-w6` |
| **graph_change_layer** | `mixed` |
| **wiki_delta** | `n/a` |
| **review_hat** | `20` |
| **required_invoke_hats** | `10,30` |
| **test_strategy** | `required` |
| **test_strategy_note** | `./scripts/graph-compile.sh` exit 0；`git diff app/` 为空（W5 新增 coverage 脚本除外，其为 scripts/ 工具非 app/） |
| **code_quality_bar** | `not_applicable` |

### 人工闸

| human_gate_id | status | blocks_hats | 说明 |
|---|---|---|---|
| HG-TASK-DRAFT | approved | 22-R1 | 2026-08-25 00 代签（维护者指令「开启图谱 W3–W6」+ 本窗授权；SPEC 已签收） |
| HG-AUDIT-R1 | approved | 30 | 2026-08-25 00 代签（纯图谱/文档，范围锁定对应 wave spec；同 W1/W2 例） |
| HG-GRAPH-MODULES | approved | 30 | 2026-08-25 00 签：00 统一复检过（compile 绿 · graphs 7 · coverage OK · 01_modules 仅备注列变化 diff 证据） |

---

## 范围

1. `10_flow_auth` / `11_flow_sync_to_chat` 硬边 anchors 补全或刷新行号（指向当前真实行）
2. 实现 `scripts/graph_coverage_check.py`（warn 级）：对比 `app/ops/router.py` include_router 集合 vs `00_main` 子路由节点，缺漏 warn
3. 可选接入 `.github/workflows/tech-graph.yml`（warn 不 fail）

## 非范围

- coverage fail 级门禁（本波只 warn）
- `app/` 业务代码

## 验收标准

- [x] 两 flow anchors 行号与代码当前行一致（抽读）
- [x] coverage 脚本跑出报告且当前无缺失（或有缺失则列出清单）
- [x] CI 接入为 warn（若做）；`./scripts/graph-compile.sh` exit 0

---

## 自检结论（30 回填 · 2026-08-25）

- **anchors 刷新**：`10_flow_auth` 14 条硬边 anchors 全部重指当前真实行（auth.py 45→57 / 50→67 / 92→103 / 99→111 / 108→121 / 119→130；deps.py 13→16×2 / 41→52 / 33→52 / 27→30；chat/router.py 277→103 / 285→113；admin/sync.py 20→28）；`11_flow_sync_to_chat` 6 条 anchors 刷新（sync.py 45→28；service.py 20→46；issues.py 25→40；pulls.py 25→38；graph.py 16→21；nodes.py 63→99）。逐条抽读源码核对一致；两 yaml version bump 至 2026-08-25。
- **coverage 脚本**：新增 `scripts/graph_coverage_check.py`（R1–R4 · warn only · 默认 exit 0；`--strict` 为二期预留 flag）。当前仓运行 [OK] 无缺失/多余：R1 10 includes ↔ 9 G-L0 子路由节点（chat_sse+chat_ws 并入 chat_router 节点）；R2 3 处 ::triggers flow 引用齐全；R3 0 行 START→ 长拓扑；R4 retrieve 在图。负例自测通过：删 G-L0 节点 → R1 warn；删 flow 文件 → R2/R3 warn；删 retrieve 节点 → R4 warn；--strict 有 warn 时 exit 1。
- **CI 接入（可选项 · 已做）**：`.github/workflows/tech-graph.yml` 追加 warn 步骤（continue-on-error: true + || true，永不 fail job）。
- **compile**：`./scripts/graph-compile.sh` exit 0（7 graphs · 99 nodes · 142 edges · harness check 全 OK · normalize check 7/7）。`git diff app/` 为空。

### 偏差及理由

- spec 将 `--strict` 列为「未来维护者拍板」；脚本仅提供 flag 且默认 warn，未接入任何 fail 门禁，未越权。
- `10_flow_chat.graph.yaml` 内 `admin/sync.py:45` 两处 anchors 亦已漂移，但该文件属 W1/并行子 agent 文件集，本波不动 → 转遗留风险。

### 遗留风险

- 10_flow_chat 的 admin_sync 两处 anchors 漂移待其责任 wave 刷新。
- anchors 行号比对未自动化（spec 明确列二期）。

## 修订

| 日期 | 说明 |
|---|---|
| 2026-08-25 | 初版（00 起草 + 代签闸 · 维护者授权）：范围自 01_execution_waves.md §W5 锁定 |
| 2026-08-25 | 30 回填：anchors 刷新至当前真实行 + 新增 graph_coverage_check.py（warn）+ CI warn 步骤；验收三项全勾 |
