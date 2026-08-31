# ROADMAP：Eval & Observability（L2 · 可拆 task）

> **层级**：L2 路线（eval 域）  
> **状态**：`active`（随 [`../04_eval_and_observability_plan_v0.md`](../04_eval_and_observability_plan_v0.md) **E0 签收**；E1 字典本文件 §3 为真值；**不**直接授权 30）  
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
| E1-a | SLI / metadata / score **名字典**（文档表；与现 span 键对齐） | **DONE** · 本文件 §3 |
| E1-b | 缺口键补齐清单（仅文档或最小代码；00 定夺） | **DONE** · §3.3；**本波不改** `app/` |
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

## 3. SLI 字典（E1 签收真值 · 2026-08-28）

> **新增键必须改本表**，禁止节点各自发明同义名。  
> **状态**：`已埋` = 2026-08-28 对照源码已写入 Langfuse span metadata；`缺口` = 约定了名字但热路径未写或未统一。  
> **00 定夺（E1-b）**：缺口 **不在本波改码**；补 `module` 标签可随 E2 最小 diff，score 热路径随 E3/E4。

### 3.0 模块切片约定

| 约定 | 值 |
|---|---|
| metadata `module` | `intent` · `router` · `strategy_builder` · `supervisor` · `tool_exec` · `rag` · `skill` · `critic` · `e2e` |
| score 前缀 | `acc.<module>.*` · `stab.<module>.*` · `avail.*` · `cost.*`（可选） |
| Dataset 命名 | `golden-<module>-vN` 或目录 `golden/<module>/` |
| 只改 Builder 的门禁 | 必跑 `golden/strategy_builder`；E2E 可异步 |
| span 名（已有） | `intent` · `router` · `strategy_builder` · `supervisor` · `critic` · `retrieve` / `grade_llm` · capability 调用挂在 tool span |

### 3.1 Metadata（对照源码）

| 键 | 模块 | 状态 | 落点（约） | 含义 |
|---|---|---|---|---|
| `module` | intent / strategy_builder | 已埋 | `intent.py` · `builder.py` | 切片过滤；其它节点多为**缺口** |
| `route` | router | 已埋 | `lg_rag/nodes.py` | 分流：`rag` / `rewrite` / `direct` 等 |
| `router_fallback` | router | 已埋 | 同上 | 路由退化 |
| `router_raw` | router | 已埋 | 同上 | 原始分类文本截断 |
| `intent_fallback` | intent | 已埋 | `strategy/intent.py` | SO/LLM 失败走保守 intent |
| `intent_domain` | intent | 已埋 | 同上 | IntentV1.domain |
| `intent_needs_tool` | intent / strategy_builder | 已埋 | intent + builder | 是否需要 tool |
| `intent_risk_hint` | strategy_builder | 已埋 | `builder.py` | 不得绕过 Policy |
| `strategy_builder_catalog_count` | strategy_builder | 已埋 | `builder.py` | Policy 可见目录大小 |
| `strategy_builder_allowed_count` | strategy_builder | 已埋 | 同上 | 本轮 allowlist 大小 |
| `strategy_builder_stripped_ids` | strategy_builder | 已埋 | 同上 | 被剔除的非法 id（可空） |
| `capability_catalog_count` | supervisor | 已埋 | `lg_rag/multi/nodes.py` | 本轮可见 capability 数 |
| `subtask_count` / `subtask_types` | supervisor | 已埋 | 同上 | plan 规模与类型 |
| `supervisor_fallback` | supervisor | 已埋 | 同上 | plan 退化单 rag |
| `supervisor_empty_allowlist` | supervisor | 已埋 | 同上 | 空 allowlist 触发 fallback |
| `supervisor_invalid_tool_id` | supervisor | 已埋 | 同上 | 非法 tool id |
| `supervisor_raw` | supervisor | 已埋 | 同上 | 原始 plan 截断 |
| `structured_output_fallback` | router / intent / supervisor | 已埋 | 多节点共用键 | 结构化出口失败/退化 |
| `capability_id` · `ok` · `kind` | tool_exec / capability | 已埋 | `capability/gateway.py` | 调用结果 |
| `policy_blocked` | capability | 已埋 | 同上 | Policy 拒绝时为 true |
| `risk_level` | capability | 已埋 | 同上 | spec.risk_level |
| `error` | capability | 已埋 | 同上 | 截断错误串 |
| `capability_manifest_version` · `capability_manifest_count` | capability | 已埋 | `manifest.py` | 加载时（非每请求） |
| `critic_outcome` | critic | 已埋 | `strategy/critic.py` | pass / retry_planner / rebind / … |
| `inner_retry_count` | critic | 已埋 | 同上 | 内层重试计数 |
| `rebinding_count` | critic | 已埋 | 同上 | 再赋能次数（原「规划」现已埋） |
| `gate_action` · `best_relevance` | rag | 已埋 | `chat/rag_nodes.py` | grader 门 |
| `grade_failed` | rag | 已埋 | `lc_evidence_chain/grader.py` | grader 失败 |

### 3.2 Score 名（Experiment / 线上 · 热路径均为缺口）

写入 Langfuse 时 **不得**擅自改名；新增须改本表。  
**本波不写 score**（无 `score_current_trace` 封装）。UI 手动打分可用下列名字练手。

| score name | 维度 | 取值 | 状态 |
|---|---|---|---|
| `avail.success` | 可用性 | 0/1 请求是否正常 END | 缺口 |
| `avail.capability_ok` | 可用性 | 0/1 该次 tool 调用 | 缺口（metadata `ok` 已有） |
| `acc.route_match` | 准确性 | 0/1 vs 金标 | 缺口 · E2 |
| `acc.plan_match` | 准确性 | 0/1 或分项 | 缺口 · E2 |
| `acc.strategy.allowlist_match` | 准确性 | 0/1 vs 金标 allowlist | 缺口 · E2 |
| `acc.answer_judge` | 准确性 | 0–1（须 schema） | 缺口 · E4 |
| `stab.fallback` | 稳定性 | 0/1 本请求是否 fallback | 缺口（metadata fallback 布尔已有） |
| `stab.replay_var` | 稳定性 | 重放方差（run-level） | 缺口 |
| `cost.tokens_in` / `cost.tokens_out` | 成本 | 可选；优先 generation usage | 缺口 · E5 |
| `cost.usd_est` | 成本 | Host 价表计算（非 LLM 估） | 缺口 · E5 |

### 3.3 缺口补齐清单（E1-b · 00 定夺）

| 优先级 | 缺口 | 建议波次 | 本波 |
|---|---|---|---|
| P1 | 为 `router` / `supervisor` / `critic` / tool span 补统一 `module=` | E2 最小 diff 或随金标 runner | **不改码** |
| P1 | `tracing.score_current_trace` no-op 包装 + 1～2 调用点（如 `supervisor_fallback`→`stab.fallback`） | E3/E4 | **不改码** |
| P2 | Dataset `golden/strategy_builder` · `golden/router` | E2 | 文档约定目录即可 |
| P3 | usage 缺帧 `usage_missing` · `model`/`provider` 强制 | E5 | — |

**明确不做（本波）**：改 `chat/graph.py` 拓扑；Langfuse SDK v4（DEF-001）；DEF-003/004 RAG 草案；Fork Langfuse。

---

## 4. 建议 task（颗粒度 · 00 定夺）

**原则**：一次只开 **一个** 可 30 的实现单；不追求 E 轨一次做完。**00 只统筹/签收，不实现。**

| slug | 覆盖 | 前置 | 谁做 | 状态 |
|---|---|---|---|---|
| `eval-e0-e1` | E0 签收 + E1 字典 | — | **仅 00 文档**（可同单：无 30） | **DONE** · PR #92 |
| `eval-goldenset-lg-rag` | **仅 E2**：模块金标目录 + 最小集；`module=` 本波默认不做 | E1 | **30 实现**；00 不写 fixture | **DONE** · PR #93 |
| `eval-langfuse-experiment-ci` | **仅 E3**：Dataset 映射 + mock Experiment | E2 | **30 实现**；00 不写 runner | **DONE** · PR #94 |
| `eval-online-sample-scores` | **仅 E4**：抽样 score + Annotation GUIDE | E3 | **30 实现**；00 不写码 | **DONE** · PR #95 |
| `eval-token-cost-ledger` | **仅 E5**：usage 审计 + 价表 + 导出 | E4 | **DONE** · [#96](https://github.com/Cyning12/ops-desk-api/pull/96) | 已归档 |

`test_strategy`：E0+E1 = `none`；E2+ = `required`。`graph_change_layer`：多为 `n/a` 或 G-L1 备注观测键。

**E2 明确不含**：Langfuse Dataset 同步、CI Experiment job、热路径 `score_current_trace`、价表。

### 4.1 00 后续编排（不落地）

> 维护者 2026-08-28：00 继续统筹后续 · **禁止本窗实现**任何 E2–E5 代码/fixture。  
> **禁止**在当前实现单未 CLOSE 时把下一波 E4/E5 写入 `docs/tasks/active/`。

| 顺序 | 何时 | 00 做什么 | 00 不做什么 |
|---|---|---|---|
| **现在** | E5 **DONE** · Eval 轨 E0–E5 收官 | — | — |
| **E5 CLOSE 后** | 无强制下一棒（观测/内容 I/O 见传输轨 `05`） | — | — |

可复制下一棒 00（E3 合入后拆 E4）：届时另写 Prompt；本文件 E2 后 Prompt 已用过。

---

## 5. 修订记录

| 日期 | 说明 |
|---|---|
| 2026-08-27 | 初版：E1–E4 · SLI/score 草案 · Langfuse 默认 |
| 2026-08-27 | 模块切片 · Annotation · E5 token/计费 · score 成本键 |
| 2026-08-28 | **E1 签收**：§3 对照源码标已埋/缺口；E1-b 定夺本波不改 `app/`；建议 task 增 `eval-e0-e1` |
| 2026-08-28 | **颗粒度**：E2–E5 各一 task；00 不实现；本窗不起草 E2 |
| 2026-08-28 | **E2 开工**：task `eval-goldenset-lg-rag`；金标根 `evals/agent/`；00 不实现 |
| 2026-08-28 | **§4.1 后续编排**：E3→E4→E5 分波；E2 未绿不合 PR；00 不落地 |
| 2026-08-28 | **E3 开工**：`eval-langfuse-experiment-ci`；E2 归档 #93 |
| 2026-08-28 | **E4 开工**：`eval-online-sample-scores`；E3 归档 #94 |
| 2026-08-29 | **E5 开工**：`eval-token-cost-ledger`；E4 归档 #95 |
| 2026-08-31 | **E5 DONE**：[#96](https://github.com/Cyning12/ops-desk-api/pull/96) MERGED；task 归档补登 |
| 2026-08-30 | **交叉引用**：Generation 内容 I/O 优先级见 L0 [`../05_lg_rag_transport_and_session_plan_v0.md`](../05_lg_rag_transport_and_session_plan_v0.md) §3；**不**在 Eval 轨单开 Obs-I/O task |
