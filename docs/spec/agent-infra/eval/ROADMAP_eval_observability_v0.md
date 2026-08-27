# ROADMAP：Eval & Observability（L2 · 可拆 task）

> **层级**：L2 路线（eval 域）  
> **状态**：`draft`（随 [`../04_eval_and_observability_plan_v0.md`](../04_eval_and_observability_plan_v0.md)；**不**授权 30）  
> **控制面**：Langfuse Dataset / Experiment / Score（默认）

---

## 1. 目标

把「每模块观测点 + 测评点」从口头约定变成：**键字典 + 金标 + runner +（可选）Langfuse Experiment 门禁**。

### 非目标

- Fork Langfuse / 自建完整 APM  
- 默认启用 LangSmith  
- 用 SO Gateway 代替业务 grader  
- 无字典前大规模打分（避免键污染）

---

## 2. 交付项

| ID | 内容 | 验收 |
|---|---|---|
| E1-a | SLI / metadata / score **名字典**（文档表；与现 span 键对齐） | 表进 ROADMAP 或 `docs/standards/` 短文 |
| E1-b | 缺口键补齐清单（仅文档或最小代码；00 定夺） | 与 tracing 兼容 |
| E2-a | `tests/eval/` 或 `docs/eval/golden/` 最小集：router · supervisor plan · 1 E2E | 可本地跑 |
| E2-b | 确定性评估器：枚举相等、tool id ∈ allowlist、JSON schema | pytest 绿 |
| E3-a | Langfuse Dataset 同步策略（git 为源 of truth 或双向） | GUIDE 一页 |
| E3-b | Experiment runner 脚本：跑金标 → 写 scores；对比基线阈值 | mock 可 CI |
| E3-c | CI 门禁草案（workflow 或文档先） | 失败语义清晰 |
| E4-a | 生产抽样 score（规则：fallback 率告警；可选 judge） | 采样率可配；不影响热路径 |
| E4-b | 难例回流 Dataset + **Langfuse Annotation Queue**（可按 `module` 过滤） | 流程文档 |
| E5-a | LLM 路径 usage 上报审计（缺帧标记）；`model`/`provider` metadata 钉死 | 单测 / 清单 |
| E5-b | 价表（模型×单价×生效日）+ 按日/模块聚合导出（CSV 或内部 API） | 文档 + 可跑脚本 |
| E5-c | Langfuse 侧 model 单价配置或 Dashboard 费用列说明（与 Host 价表对齐） | GUIDE 一页 |

---

## 3. SLI 字典草案（E1 真值起点 · 可修订）

### 3.0 模块切片约定

| 约定 | 值 |
|---|---|
| metadata `module` | `router` · `strategy_builder` · `supervisor` · `tool_exec` · `rag` · `skill` · `critic` · `e2e` |
| score 前缀 | `acc.<module>.*` · `stab.<module>.*` · `avail.*` · `cost.*`（可选） |
| Dataset 命名 | `golden-<module>-vN` 或目录 `golden/<module>/` |
| 只改 Builder 的门禁 | 必跑 `golden/strategy_builder`；E2E 可异步 |

### 3.1 Metadata（已有 / 规划）

| 键 | 模块 | 含义 |
|---|---|---|
| `route` | router | 分流结果 |
| `router_fallback` | router | 路由退化 |
| `supervisor_fallback` | supervisor | plan 退化 |
| `supervisor_invalid_tool_id` | supervisor | 非法 tool |
| `structured_output_fallback` | SO 接入节点 | 结构化出口退化 |
| `capability_catalog_count` | supervisor | 可见目录大小 |
| `capability_id` / `ok` / `policy_blocked` | capability | 调用结果 |
| `rebinding_count` | strategy（规划） | 再赋能次数 |
| `critic_*` | critic（规划） | 达标判定 |

### 3.2 Score 名（建议 · Experiment / 线上）

| score name | 维度 | 取值 |
|---|---|---|
| `avail.success` | 可用性 | 0/1 请求是否正常 END |
| `avail.capability_ok` | 可用性 | 0/1 该次 tool 调用 |
| `acc.route_match` | 准确性 | 0/1 vs 金标 |
| `acc.plan_match` | 准确性 | 0/1 或分项 |
| `acc.answer_judge` | 准确性 | 0–1（须 schema） |
| `stab.fallback` | 稳定性 | 0/1 本请求是否 fallback |
| `stab.replay_var` | 稳定性 | 重放方差（run-level） |
| `cost.tokens_in` / `cost.tokens_out` | 成本 | 可选 score 或仅用 generation usage |
| `cost.usd_est` | 成本 | Host 按价表计算后写入（非 LLM 估算） |

写入 Langfuse 时 **不得**擅自改名；新增须改本表。

---

## 4. 建议 task

| slug | 覆盖 | 前置 |
|---|---|---|
| `eval-sli-dictionary` | E1 | E0 签收 |
| `eval-goldenset-lg-rag` | E2（含模块切片目录） | E1 |
| `eval-langfuse-experiment-ci` | E3（含模块 CI job） | E2 |
| `eval-online-sample-scores` | E4 | E1；建议 E3 |
| `eval-token-cost-ledger` | E5 | E1 |

`test_strategy`：`required`（E2+）。`graph_change_layer`：多为 `n/a` 或 G-L1 备注观测键。

---

## 5. 修订记录

| 日期 | 说明 |
|---|---|
| 2026-08-27 | 初版：E1–E4 · SLI/score 草案 · Langfuse 默认 |
| 2026-08-27 | 模块切片 · Annotation · E5 token/计费 · score 成本键 |
