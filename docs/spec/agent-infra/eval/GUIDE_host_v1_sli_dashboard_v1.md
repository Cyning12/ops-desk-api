# GUIDE：Host v1.0 SLI 四项看板（Langfuse · 三步打开）

> **定义真值**：[`SLI_host_v1_four_metrics_v1.md`](./SLI_host_v1_four_metrics_v1.md)  
> **有数**：[`evals/agent/sli/aggregate_sli.py`](../../../../evals/agent/sli/aggregate_sli.py) · fixture `evals/agent/sli/fixtures/sli_sample.json`  
> **Cost**：复用 `app/llm/budget.cost_per_successful_task`（缺单价 `unknown` 不伪造 0）  
> **本页可复现**：不依赖「以后再做」；无项目权限时用 fixture 聚合作有数证据。

---

## 三步打开看板

### 步骤 1 · 打开 Langfuse 项目

1. 浏览器打开本环境 Langfuse（`OPS_LANGFUSE_HOST` / 团队云端项目）。  
2. 选择与 `OPS_CHAT_TRACER=langfuse` 写入同一 **project**。  
3. 左侧进入 **Dashboards**（或 **Tracing → Traces** 作临时看板）。

### 步骤 2 · 按四项字段筛窗口

| SLI | UI 入口 | 筛 / 看什么 |
|---|---|---|
| 端到端 P99 | Traces 列表 · Latency 列；或 Dashboard → latency P99 widget | 时间窗 +（可选）`metadata.module=e2e` / 根 span |
| 任务完成率 | Scores 名 `avail.success`；或导出 traces 后按终态 `done` 聚 | 时间窗；分子仅 terminal=`done` |
| 能力命中率 | Traces/Observations 过滤 `metadata.ok`；Scores `avail.capability_ok`（若已打） | capability / tool span；**勿**把 `ok` 元数据键当 score 名上报 |
| Cost per Successful Task | Generations usage + Host 价表；或跑仓内聚合 | 仅成功 `done` run；缺单价标 unknown |

### 步骤 3 · 钉死可复现查询 / 导出

任选其一留证据：

1. **UI**：Dashboard 保存四项 widget（名建议与 `dict_key` 一致）→ 截图入 `docs/reports/host_v1_exit_review/`（可选）。  
2. **导出**：Traces / Scores CSV → 映射为 `evals/agent/sli/fixtures/` 形状 →  
   `python -c "from evals.agent.sli.aggregate_sli import aggregate_all_from_fixture; import json; print(json.dumps(aggregate_all_from_fixture(), indent=2, ensure_ascii=False))"`  
3. **离线 CI**：`pytest tests/eval/test_host_v1_sli.py -q`（不连网 · 用 fixture）。

---

## 字段清单（看板 / 导出列）

| dict_key | 必填输入字段 | 类型 | 备注 |
|---|---|---|---|
| `latency.e2e_p99_ms` | `run_id`, `duration_ms` | float ms | 根/e2e span；P99 nearest-rank |
| `avail.success` | `run_id`, `terminal_status` | enum | `done` 计成功；其它终态计未完成 |
| `avail.capability_ok` | `capability_id`, `ok` | bool | 缺 `ok` → 整窗 `unknown` |
| `host.cost_per_successful_task` | `run_id`, `model`, `prompt_tokens`, `completion_tokens` | — | 行集须已是成功 run；走 `UsageCostRow` |

---

## 非范围

- 自建完整可观测中台 / 新对外计费 API  
- 改 freeze / SSE / 热路径强制写 score（本波 docs-only）  
- 把 `cost.usd_est` 与 Host Cost SLI 合并

---

## 修订

| 日期 | 说明 |
|---|---|
| 2026-09-24 | 初版 · Host v1.0 出口四项看板三步 + 字段清单 |
