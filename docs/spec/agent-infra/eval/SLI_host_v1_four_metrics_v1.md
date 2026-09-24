# Host v1.0 出口 SLI 四项定义表

> **状态**：signed（host-v1-sli-four-metrics · 2026-09-24）  
> **锚点**：07 §4 指标面 · 出口 GAP G1 · E1 字典 [`ROADMAP_eval_observability_v0.md`](./ROADMAP_eval_observability_v0.md) §3  
> **机读副本**：[`sli_host_v1_four_metrics_v1.yaml`](./sli_host_v1_four_metrics_v1.yaml)  
> **有数**：[`evals/agent/sli/aggregate_sli.py`](../../../../evals/agent/sli/aggregate_sli.py)  
> **看板**：[`GUIDE_host_v1_sli_dashboard_v1.md`](./GUIDE_host_v1_sli_dashboard_v1.md)

---

## 1. 钉死契约

| 项 | 值 |
|---|---|
| **成功任务口径** | 承 V1-C：成功任务 = supervisor run 终态 `done` 的 `run_id` 集合（调用方按 `run_events` 筛后传入；与 `app/llm/budget.cost_per_successful_task` docstring 一致）；**禁止另发明** |
| **Cost 铁律** | 复用 `cost_per_successful_task`；缺单价 → `unknown` **不伪造 0** |
| **E1 对齐** | 完成率↔`avail.success` · 命中率↔`avail.capability_ok`（metadata `ok`≠SLI 名，但可作数据源）· Cost↔Host 函数（**非** `cost.usd_est`）· P99↔本表扩展键 `latency.e2e_p99_ms`（E1 §3.2 原无 latency score） |
| **热路径 score** | 默认关或观察；本波 **docs-only**，不强制写 score |

---

## 2. 四项定义表

| sli_id | 显示名 | dict_key | 公式 | 标签 | 成功口径 | 数据源 | 有数落点 | 看板 |
|---|---|---|---|---|---|---|---|---|
| `e2e_p99` | 端到端延迟 P99 | `latency.e2e_p99_ms` | 窗口内根/e2e span `duration_ms` 的 P99（nearest-rank：`ceil(0.99·n)` 位，1-indexed） | `module=e2e` 或根 trace | 不筛成功（延迟面含失败 run；失败可另切） | Langfuse trace latency / 导出 `duration_ms` | `aggregate_e2e_p99` + fixture | GUIDE §三步 · Dashboard latency |
| `task_completion` | 任务完成率 | `avail.success` | `\|{run_id: terminal=done}\| / \|runs\|`；分母=窗口内有终态的 run | `avail` | 分子仅 `done`（承 V1-C） | `run_events` 终态 / score `avail.success`（若已打） | `aggregate_task_completion` + fixture | GUIDE · score/metadata 筛选 |
| `capability_hit` | 能力命中率 | `avail.capability_ok` | `mean(ok)` over capability 调用行；任一贡献行缺 `ok` → 聚合标 `unknown` **不伪造 0** | `avail` · `module`∈ tool_exec/capability | 单次调用 `ok=true` 计命中；**勿**把 metadata 键名当 score 名 | span metadata `ok`（已埋）/ score `avail.capability_ok`（E1 缺口·可选） | `aggregate_capability_hit` + fixture | GUIDE · metadata `ok` 过滤 |
| `cost_per_success` | Cost per Successful Task | `host.cost_per_successful_task` | `Σ(成功 run LLM cost) / 成功任务数`（承 V1-C） | `cost` · Host | 成功=`done` run_id | usage 账本行 × `model_catalog` 单价 | **对拍** `cost_per_successful_task` | GUIDE · Cost Dashboard / 导出 |

**禁止同义异名**：不得另起 `e2e_latency_p99` / `success_rate` / `tool_hit_rate` / 第二套 Cost 公式键。

---

## 3. 与 E1 字典关系

| 本表 dict_key | E1 §3.2 原状 | 本波动作 |
|---|---|---|
| `latency.e2e_p99_ms` | **无** | **扩展**写入 ROADMAP §3.2（状态=观察·聚合面；热路径 score 默认不写） |
| `avail.success` | 缺口 | 键名沿用；有数靠 run 终态聚合，不强制热路径写 score |
| `avail.capability_ok` | 缺口（metadata `ok` 已埋） | 键名沿用；聚合可读 metadata `ok` |
| `host.cost_per_successful_task` | 非 E1 score；对照 `cost.usd_est` | **显式分流**：出口 SLI 用 Host 函数；`cost.usd_est` 仍为 E5 可选 score，语义不合并 |

---

## 4. 修订记录

| 日期 | 说明 |
|---|---|
| 2026-09-24 | Host v1.0 出口四项定稿（task `host-v1-sli-four-metrics`） |
