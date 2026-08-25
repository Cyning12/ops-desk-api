# Task：Grader 混档证据（exact + relevant）作答约束 · 探讨与方案选型

> **状态**：active（draft · 待人审 · **探讨型，30 前须维护者选型**）  
> **类型**：RAG 质量 / 契约补洞 · **设计 + 小样验证，默认不直接改生产默认行为**  
> **来源**：lc_evidence_chain / Chat RAG 链路对话梳理（2026-08-23）  
> **关联代码**：`app/ops/lc_evidence_chain/{grader,answer,chain}.py` · `app/ops/rag/grader.py` · `app/ops/chat/{rag_nodes,nodes}.py`  
> **关联评测**：`evals/golden/queries_v1.yaml` · `reports/r4-R-floor04.yaml`（混档 pass 样例 G01 等）  
> **实现仓**：本仓  
> **分支**：启动时再切 `task/rag-answer-mixed-evidence`  
> **无关**：勿与 `task_ops_sync_sender_migration`、`task_lg_rag_phase*` 混改；本波**不**改 rerank 双阈值 / 嵌入 / 金样条目语义。

---

## Harness 元信息

| 字段 | 值 |
|---|---|
| **task_slug** | `rag-answer-mixed-evidence` |
| **git_branch** | `task/rag-answer-mixed-evidence`（启动时再切） |
| **implement_repo** | `ops-desk-api` |
| **test_strategy** | `required`（若进入 30 实现）；探讨阶段可先 `n/a` + 小样脚本 |
| **test_strategy_note** | 探讨：手工/脚本抽 G01/G12 类 case 对比 prompt 变体；实现后：`tests/test_lc_evidence_chain.py` + `tests/test_chat_nodes.py` + 可选金样子集复跑 |
| **code_quality_bar** | `L2_backend` |
| **graph_change_layer** | `G-L1`（若改 answer 契约）或 `none`（仅旁路试点） |
| **graph_delta** | 待定：维护者选型后补 `docs/_tech_graph/l1/01_modules.md` 半句（answer 混档纪律） |
| **graph_delta_note** | 不新增一级模块；闸枚举四档不变，仅 answer 阶段展示/约束补洞 |
| **wiki_delta** | `n/a`（选型结论可写本 task 或 `docs/guides/` 短文，非硬门槛） |
| **review_hat** | `20` |
| **required_invoke_hats** | `10`（探讨）；若落地实现再加 `30` |
| **invoke_retention_profile** | `default` |
| **orchestration** | 探讨 task：10 起草 → 人审选型 → 可选 30 实现子 task 或本 task 扩 scope |

### 人工闸

| human_gate_id | status | blocks_hats | 说明 |
|---|---|---|---|
| HG-TASK-DRAFT | pending | 22-R1 | 维护者确认探讨范围、选型门槛（旁路 only vs Chat 对齐） |
| HG-AUDIT-R1 | pending | 30 | 进入改码前须签；探讨阶段不阻塞文档 |
| HG-GRAPH-MODULES | pending | 30 | 真值 `docs/_tech_graph/l1/01_modules.md`；实现前更新 answer 契约半句 |

---

## 背景与问题陈述

Grader 四档（`irrelevant` / `weak` / `relevant` / `exact`）经 `decide_grade` 压成三种 `gate_action`：

| 最高档 | gate_action | 当前 answer 行为 |
|---|---|---|
| ≤ `weak` | `refuse` | 不调 answer LLM · 固定拒答文案 |
| `relevant` | `answer_partial` | **强约束**：system + user 注入「仅部分证据」 |
| `exact` | `answer` | 正常作答 · **无额外混档提示** |

**缺口（已确认）**：当 `kept` 中 **同时存在 `exact` 与 `relevant`** 且最高档为 `exact` 时：

1. `gate_action` 仍为 `answer`（不会降级为 `answer_partial`）。
2. `format_evidence_block` **不向 answer LLM 暴露逐条档位**（仅 anchor + snippet）。
3. `relevant` 块与 `exact` 块 **平权进入 prompt**，存在把「部分覆盖」陈述成完整事实的风险。

**旁路 vs Chat 差异（须纳入选型）**：

| 路径 | kept 过滤 | 混档风险 |
|---|---|---|
| `lc_evidence_chain` | 仅 `relevant`+`exact` 进 answer | 有缺口，但无 weak 块混入 |
| Chat `rag_nodes` + `nodes` | grade 后 **不滤** `retrieved`，top-5 全进 generate | 混档 + weak/irrelevant 标签仅在前端 sources |

金样参考：`reports/r4-R-floor04.yaml` 中 `gate_action=answer` 且 top5>1 的 case（如 **G01**）；`answer_partial` pass 约 12 条（如 **G12**）行为已符合契约，**不在本 task 首波改动范围**。

---

## 目标（探讨阶段完成态）

- [ ] **问题量化**：从 `r4-R-floor04.yaml`（或重跑）统计 `answer` 模式下 `kept` 含 `relevant`+`exact` 的占比；列 top-N case ID + query 摘要。
- [ ] **方案对比表**（维护者选型用）：至少覆盖下列三轨，并写清改前/改后 prompt 片段与用户可见差异。

### 方案 A · 依据块打标签（结构提示）

- `format_evidence_block`（及 Chat `_build_messages` 资料段）为每条依据追加 `[exact]` / `[relevant]`（及可选 `reason` 摘要）。
- `gate_action` 不变；`answer_partial` 逻辑不变。

### 方案 B · `answer` 模式混档弱约束（文字纪律）

- 触发：`gate_action==answer` 且 `kept` 中同时含 `exact` 与 `relevant`。
- 动作：仅向 **system** 追加弱约束（不要求 user 前缀「仅部分证据」）；文案草案见下文「附录 · 弱约束草案」。
- 可选：`meta.has_mixed_evidence=true`（Langfuse 观测）。

### 方案 C · 组合 A+B（推荐待验证）

- 标签 + 弱 system 纪律；实现量略大，预期防夸大最好。

### 方案 D · 硬过滤（仅 `exact` 进 answer）

- `gate_action` 仍为 `answer`，但 `kept` 只留 `exact`；`relevant` 仅进 sources/观测。
- 风险：丢失合法补充上下文；需金样回归。

- [ ] **小样对比**：≥3 条混档 case（建议 G01 + 另 2 条自报告抽取）各跑 A/B/C（可脚本化，落 `experiments/rag_compare/mixed_evidence/`）。
- [ ] **选型结论**：维护者在 task 人工闸表或 invoke 10 中勾选方案 + 是否同步 Chat 主链。
- [ ] **若选型通过**：拆 30 实施清单（文件级 diff 预估、单测、金样子集回归命令）。

**探讨阶段不做（除非维护者明示扩 scope）**：

- 不改 Grader 四档定义 / `decide_grade` 最高档规则。
- 不改 `answer_partial` 强约束文案（除非小样证明需统一措辞）。
- 不默认改 `RAG_*` env 生产值。

---

## 方案要点（改前 / 改后摘要）

### 现状（改前）

```text
gate_action=answer
  → system: answer_system_prompt.yaml（无混档句）
  → user: 问题 + [1] anchor · title + snippet（无档位）
  → relevant 与 exact 平权
```

### 方案 B 改后（弱约束 · 最小 diff）

```text
gate_action=answer 且 mixed
  → system: 原 prompt + MIXED_GATE_SYSTEM_NOTE
  → user: 不变（无「仅部分证据。」前缀）
```

### 方案 A 改后（标签）

```text
user 依据块:
  [1] issue 1089#2 · [exact] …
  [2] issue 2720#4 · [relevant] …
```

### 与 `answer_partial` 的边界（锁定）

| 模式 | 开头 | 适用 |
|---|---|---|
| `answer_partial` | 必须「仅部分证据」 | 最高档 = `relevant` |
| `answer` + mixed 弱约束 | 不要求 | 最高档 = `exact` 且混有 `relevant` |
| `answer` 纯 exact | 无额外 | 最高档 = `exact` 且全 exact |

---

## 验收标准（探讨关账）

- [ ] 报告或本 task「选型」节有维护者勾选（A/B/C/D + Chat 是否对齐）。
- [ ] 混档 case 清单 + 占比有数据出处（报告 yaml 或脚本输出）。
- [ ] 每方案至少有 1 条「改前/改后」理想输出示例（可引用对话 G01/G12 类）。
- [ ] 若结论为「暂不改」：须写明接受的风险与复评触发条件。

## 验收标准（若进入 30 实现 · 占位）

- [ ] `lc_evidence_chain` 按选定方案实现 + 单测绿。
- [ ] Chat 主链：维护者若要求对齐，则 `nodes.py` / `rag_nodes.py` 同步；否则 task 注明「旁路 only」。
- [ ] `ruff check` 相关路径绿。
- [ ] 金样子集（混档 ID 列表）复跑无 neg 回退。

---

## failure_paths

| 触发 | 行为 | 可重试 |
|---|---|---|
| 小样 LLM 方差大 | 同 prompt 跑 2 次，结论标 `confidence: low` | Y |
| 方案 B 单独不足以防夸大 | 选型倾向 C 或 D；不在探讨阶段强行合入 | — |
| Chat 与旁路行为分叉 | 文档显式标注；另开对齐子 task | — |
| 维护者未签 HG-TASK-DRAFT | 只保留本 md，30 拒改码 | — |

---

## 依赖与读序

1. `app/ops/lc_evidence_chain/grader.py` · `decide_grade`
2. `app/ops/lc_evidence_chain/answer.py` · `PARTIAL_GATE_SYSTEM_NOTE` / `format_evidence_block`
3. `app/ops/rag/grader.py` · 契约 4c 四档定义
4. `app/ops/chat/rag_nodes.py` · `grade_node` 不滤 retrieved
5. `app/ops/chat/nodes.py` · `_build_messages` · `answer_partial` 分支
6. `reports/r4-R-floor04.yaml` · G01 / G12 等

---

## 附录 · 弱约束草案（方案 B/C 用）

```text
【闸提示】依据中同时含「可直接作答」与「仅部分覆盖」的块：
以可直接作答的块为主组织答案；
对部分覆盖的块只可引用其已写明内容，勿延伸推断或补全未写明的结论。
```

---

## 修订

| 日期 | 说明 |
|---|---|
| 2026-08-23 | 初版（探讨型 task）：混档 exact+relevant 风险 · 方案 A/B/C/D · 待 HG-TASK-DRAFT |
