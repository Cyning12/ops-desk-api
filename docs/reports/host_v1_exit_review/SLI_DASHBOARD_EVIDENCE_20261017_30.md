# SLI Dashboard 落地证据（30 帽 · 2026-10-17）

> **task**：`docs/tasks/active/task_host_v1_sli_dashboard.md`（task_slug=`host_v1_sli_dashboard`）
> **操作真值**：`docs/spec/agent-infra/eval/GUIDE_host_v1_sli_dashboard_v1.md`
> **定义真值**：`docs/spec/agent-infra/eval/SLI_host_v1_four_metrics_v1.md`（signed 2026-09-24 · 禁同义异名）
> **结论速览**：D1 走 GUIDE 声明的 fixture 降级路径（**照登：无实证（无 Langfuse 项目权限）**，禁伪造截图/数字）；D2 查询钉死已文档化（本文 §3）；D3 fixture 聚合对拍输出四键齐 + unknown 语义实证；D4 离线 pytest 9 passed。

---

## 1. GATE_VERIFY（30 开工前闸扫描）

命令：`npx spec-wave verify --target . --task docs/tasks/active/task_host_v1_sli_dashboard.md`

| human_gate_id | status | blocks_hats | 30 影响 |
|---------------|--------|-------------|---------|
| HG-TASK-DRAFT | approved | 20, 30 | — |
| HG-AUDIT-R1 | approved | 30 | ✅ 可 30 |
| HG-GRAPH-MODULES | approved | —（`graph_change_layer=none`） | ✅ |

VERIFY: PASS（输出原句：`VERIFY: PASS · task_host_v1_sli_dashboard.md`）。

## 2. D1 · Dashboard 实证 → 降级路径（FP-1）

**照登：无实证（无 Langfuse 项目权限）。** 本环境未配置 Langfuse 凭据且无自建实例可达，无法打开项目保存 widget，故无截图、无真实数字——按 task FP-1 纪律禁伪造。

探测证据（2026-10-17 12:5x +08:00，本 worktree）：

| 探测 | 命令 / 方式 | 结果 |
|---|---|---|
| 环境变量 | `env \| grep -iE 'LANGFUSE\|OPS_'` | **无任何输出**（`LANGFUSE_PUBLIC_KEY`/`LANGFUSE_SECRET_KEY`/`OPS_LANGFUSE_HOST` 均未设） |
| 仓内配置 | `.env.example:120-131` | Langfuse 块全部注释（`# OPS_CHAT_TRACER=langfuse` 等），凭据仅示例占位 |
| 代码默认 | `app/ops/tracing.py:60-61` `_langfuse_configured()` 要求双 key 齐备，否则 no-op | 双 key 缺失 → tracing no-op |
| 本地实例 | `curl --max-time 2 http://localhost:3000` / `127.0.0.1:3000` | 均 `000`（连接失败，无自建 Langfuse） |

**待补实证条件**（获权后重跑 D1）：拿到与 `OPS_CHAT_TRACER=langfuse` 写入同 project 的 Langfuse 项目权限后，按本文 §3 钉死条件保存四项 widget 并截图入本目录（文件名含日期）。

## 3. D2 · 可复现查询 / 导出钉死（文档化）

四项 widget 的保存/筛选/窗口条件如下；第三者按此表可在同 project 复开同视图。**widget 名必须与 dict_key 逐字一致**（SLI 定义表 §1/§2 钉死契约；FP-2 同义异名拒收）：

| widget 名（=dict_key · 逐字） | UI 入口（Langfuse） | 筛 / 过滤条件 | 时间窗 | 导出字段 |
|---|---|---|---|---|
| `latency.e2e_p99_ms` | Dashboards → 新 widget（Latency P99）；或 Tracing → Traces 列表 · Latency 列 | 根/e2e span；可选 `metadata.module=e2e`；不筛成功（延迟面含失败 run） | 评审窗口（如近 7 天），UI Date range 选择器 | `run_id`, `duration_ms` |
| `avail.success` | Dashboards → 新 widget（Score 名 `avail.success`，若已打）；或导出 traces 按终态聚 | 分子仅终态 `done`（承 V1-C）；分母=窗口内有终态的 run | 同上 | `run_id`, `terminal_status` |
| `avail.capability_ok` | Tracing → Traces/Observations 过滤 `metadata.ok`；或 Score `avail.capability_ok`（若已打） | capability/tool span 的 metadata `ok`；**勿把 metadata 键 `ok` 当 score 名上报**（FP-7） | 同上 | `capability_id`, `ok` |
| `host.cost_per_successful_task` | Dashboards → Generations usage + Host 价表；或跑仓内聚合（见 §4） | 仅成功 `done` run 的 usage 行 × `model_catalog` 单价；缺单价标 `unknown` 不伪造 0（FP-6） | 同上 | `run_id`, `model`, `prompt_tokens`, `completion_tokens` |

导出映射约定（FP-3 脱敏）：Traces/Scores CSV 仅保留 fixture 形状字段（`run_id`/`duration_ms`/`terminal_status`/`ok`/token 计数/`model`），用户内容/租户标识一律剔除；原始 CSV **不入仓**。本棒无真实导出（D1 降级），fixture 形状样例即 `evals/agent/sli/fixtures/sli_sample.json`（mock export，2026-09-24 已在仓）+ 本棒新增 `sli_sample_unknown.json`（unknown 语义演示样例，非真实数据）。

## 4. D3 · 聚合对拍留档（GUIDE §步骤 3.2 命令实跑）

### 4.1 fixture 主样例（`evals/agent/sli/fixtures/sli_sample.json`）

命令（GUIDE §步骤 3.2 原文命令，`uv run` 前缀承载本 worktree 虚拟环境）：

```bash
uv run python -c "from evals.agent.sli.aggregate_sli import aggregate_all_from_fixture; import json; print(json.dumps(aggregate_all_from_fixture(), indent=2, ensure_ascii=False))"
```

输出摘录（exit 0 · 四键齐 · 键名与 SLI 定义表 §2 dict_key 列逐字一致）：

```json
{
  "latency.e2e_p99_ms": { "value": 400.0, "sample_size": 10, "unit": "ms", "method": "nearest_rank_p99" },
  "avail.success": { "value": 0.6, "successful_tasks": 3, "total_tasks": 5, "basis": "done_over_terminal_runs" },
  "avail.capability_ok": { "value": 0.75, "hits": 3, "calls": 4, "basis": "mean_metadata_ok" },
  "host.cost_per_successful_task": { "value": 0.004, "successful_tasks": 2, "total_cost": 0.008, "basis": "estimate_only_not_billing" }
}
```

### 4.2 unknown 语义实证（本棒新增样例 `evals/agent/sli/fixtures/sli_sample_unknown.json`）

目的：实证 TC-D3「缺单价/缺 `ok` 面输出 `unknown` 而非 0」（FP-6 铁律的可跑证据；对应离线断言 `tests/eval/test_host_v1_sli.py:106-109,132-140`）。

命令：

```bash
uv run python -c "from pathlib import Path; from evals.agent.sli.aggregate_sli import aggregate_all_from_fixture; import json; print(json.dumps(aggregate_all_from_fixture(Path('evals/agent/sli/fixtures/sli_sample_unknown.json')), indent=2, ensure_ascii=False))"
```

输出摘录（exit 0）：

```json
{
  "latency.e2e_p99_ms": { "value": 260.0, "sample_size": 3 },
  "avail.success": { "value": 1.0, "successful_tasks": 2, "total_tasks": 2 },
  "avail.capability_ok": { "value": "unknown", "hits": null, "calls": 2 },
  "host.cost_per_successful_task": { "value": "unknown", "total_cost": "unknown", "basis": "estimate_only_not_billing" }
}
```

→ 缺 `ok` 行 → `avail.capability_ok.value = "unknown"`（非 0）；缺单价模型 → `host.cost_per_successful_task.value = "unknown"`（非 0）。**铁律实证 PASS。**

真实导出样例聚合结果：**照登：无实证（无 Langfuse 项目权限，无真实导出）**，仅有上述 fixture 两组结果并列；获权补实证后按 §3 导出映射重跑并列。

## 5. D4 · 离线闸复验

```bash
uv sync --extra dev   # worktree 内建环境（pytest 在 optional-dependencies dev extra）
uv run pytest tests/eval/test_host_v1_sli.py -q
```

输出摘录：`......... [100%] 9 passed in 0.09s`（exit 0 · 不连网 · fixture）。

ruff：本棒 **零 `.py` 改动**（diff 白名单见 §6），触及面净增 0。备查：`uv run ruff check evals/agent/sli/ tests/eval/` 现存 7 处错误均为 `tests/eval/test_capability_redlines.py` 等存量文件既有问题（如 F811 行 948），与本棒 diff 零交集，不修（越界即 STOP）。

## 6. TC-D5 · 零越界 diff 白名单

`git diff --stat master...HEAD` 全量触及面（含 untracked 新增）：

| 路径 | 性质 | 白名单 |
|---|---|---|
| `docs/reports/host_v1_exit_review/SLI_DASHBOARD_EVIDENCE_20261017_30.md` | 新增（本件） | ✅ 证据目录 |
| `evals/agent/sli/fixtures/sli_sample_unknown.json` | 新增样例 | ✅ task 显式允许「只允许新增 fixture 样例文件」 |
| `docs/tasks/active/task_host_v1_sli_dashboard.md` | task 档维护（状态/自检/修订记录） | ✅ 本 task |
| `docs/harness/invokes/by-task/host-v1-sli-dashboard/invoke_20261017_30_*.md` | 30 invoke | ✅ invoke 档 |
| `docs/harness/invokes/by-task/host-v1-sli-dashboard/invoke_20261017_10_*.md`、`invoke_20261017_20_*.md` | 既有 10/20 invoke（上游棒产物，随本 PR 一并入仓） | ✅ invoke 档 |
| `docs/harness/reviews/task_host_v1_sli_dashboard_audit_R1_20261017.md` | 既有 R1 审查文（20 棒产物，随本 PR 一并入仓） | ✅ 审查文 |

零触及：`app/` · `evals/agent/sli/aggregate_sli.py` · `docs/spec/agent-infra/eval/SLI_host_v1_four_metrics_v1.md`（+ yaml）· `GUIDE_host_v1_sli_dashboard_v1.md`（未回写，筛选条件文档化落本件 §3，task D2 允许「落 reports 或回写 GUIDE」二选一）· freeze/SSE/热路径。

## 7. TC-D6 · 口径一致自检

- 四项键名逐字比对：证据中出现的键仅有 `latency.e2e_p99_ms` / `avail.success` / `avail.capability_ok` / `host.cost_per_successful_task`，与 SLI 定义表 §2 dict_key 列逐字一致；无 `e2e_latency_p99`/`success_rate`/`tool_hit_rate` 等同义异名（FP-2 PASS）。
- 成功口径=终态 `done`（承 V1-C）：聚合输出 `basis: "done_over_terminal_runs"`，无另发明公式字样。
- Cost 铁律：`unknown` 实证见 §4.2；无任何伪造 0。
- metadata `ok` 未当 score 名上报（FP-7 PASS；本棒零热路径写入）。

## 8. failure_paths 合规声明

| FP | 处置 |
|---|---|
| FP-1 无权限 | ✅ 触发并走 D5 降级；照登句式已钉；零伪造截图/数字 |
| FP-2 键名漂移 | ✅ widget 名建议=dict_key 逐字钉死于 §3 表 |
| FP-3 导出脱敏 | ✅ 无真实导出入仓；映射约定已钉（仅 fixture 形状字段） |
| FP-4 越界出数 | ✅ 未触发：fixture 聚合即可出数，无需改热路径/score/聚合公式 |
| FP-6 伪造 0 | ✅ unknown 实证（§4.2） |
| FP-7 ok≠score | ✅ 文档与证据中明示区分 |
| FP-8 证据入仓 | ✅ 本件 + fixture 样例均有文件落点 |

## 修订记录

| 日期 | 说明 |
|---|---|
| 2026-10-17 | 30 帽落地证据：D1 降级照登（无 Langfuse 项目权限）· D2 查询钉死 · D3 fixture/unknown 对拍 · D4 pytest 9 passed · D5/D6 自检 |
