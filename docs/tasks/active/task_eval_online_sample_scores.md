# Task：Eval E4 · 线上抽样 score + Annotation 回流

> **状态**：in_progress（2026-08-28 · 00 起草 · 维护者令开 E4）  
> **类型**：测评 / 热路径薄封装 + 流程文档  
> **上游**：`docs/spec/agent-infra/04_eval_and_observability_plan_v0.md` · `eval/ROADMAP` §3.2 / §4.1  
> **前置**：E3 [#94](https://github.com/Cyning12/ops-desk-api/pull/94) MERGED  
> **分支**：`task/eval-online-sample-scores`  
> **帽子**：**00 不实现**；30 写 `score_current_trace` + 抽样调用点 + GUIDE。  
> **无关**：E5 价表；扩金标；E3 Dataset runner 大改；LLM-as-judge 热路径；Langfuse SDK v4；DEF-003/004；`chat/graph.py`。

---

## Harness 元信息

| 字段 | 值 |
|---|---|
| **task_slug** | `eval-online-sample-scores` |
| **git_branch** | `task/eval-online-sample-scores` |
| **implement_repo** | `ops-desk-api` |
| **test_strategy** | `required` |
| **test_strategy_note** | mock Langfuse；关 tracing / 采样 miss 时零调用；不连真云 |
| **code_quality_bar** | `L2_backend` |
| **graph_change_layer** | `none` |
| **graph_delta** | `none` |
| **graph_delta_note** | 仅 `tracing` 薄封装 + supervisor 1～2 调用点；不新增一级模块 |
| **wiki_delta** | `n/a` |
| **wiki_delta_note** | 不改 coding_wiki 正文 |
| **review_hat** | `20` |
| **required_invoke_hats** | `10,00,30` |
| **invoke_retention_profile** | `default` |
| **freeze_id** | 无 |
| **orchestration** | 仅 E4；E5 不进 active；00 不实现 |

### 人工闸

| human_gate_id | status | blocks_hats | 说明 |
|---|---|---|---|
| HG-TASK-DRAFT | approved | 22-R1 | 2026-08-28 · **00 代签 · 维护者令「继续E4」** |
| HG-AUDIT-R1 | approved | 30 | 2026-08-28 · **00 代签** · 见 `docs/harness/reviews/task_eval_online_sample_scores_audit_R1_20260828.md` |
| HG-GRAPH-MODULES | approved | — | 不新增一级模块 · **00 代签** |

---

## 背景与目标

E1 字典已有 score 名；E3 只做离线 Experiment。E4 把 **规则分**接到热路径：薄封装 `score_current_trace`（未开 tracing 时 no-op），按可配采样率写 `stab.fallback` 等；另用 GUIDE 钉 Annotation Queue 回流，不实现平台侧队列 API。

---

## 范围 / 非范围

### 00 定夺

| 项 | 定夺 |
|---|---|
| API | `app/ops/tracing.py`：`score_current_trace(name, value, **kwargs)`；tracing 关 / SDK 失败 → **静默 no-op** |
| 采样 | env `OPS_EVAL_SCORE_SAMPLE_RATE`（0.0–1.0，默认 `0` = 关闭线上打分；CI/本地默认不打网） |
| 调用点 | **至少 1**：`supervisor_fallback=True` → Boolean `stab.fallback=1`；可选第 2：`router_fallback` → 同名或文档说明 defer |
| Score 名 | 只用字典：`stab.fallback`（本波必做）；`avail.success` 可选；**禁止**热路径 `acc.answer_judge` |
| E4-b | GUIDE 一页：难例 → Annotation Queue（按 `module` 过滤）+ 回流 git Dataset 流程；**不**调 Langfuse Queue API |
| 热路径约束 | score 失败不得抛到业务；不得阻塞请求；默认 sample_rate=0 |
| 图谱 | 不新增一级模块；可不改 `01_modules.md` |

**范围（E4-a / E4-b）**：

- `score_current_trace` + 采样门控  
- supervisor（必）调用点；pytest mock  
- GUIDE：抽样策略 + Annotation 回流  

**非范围**：

- E5 usage/价表  
- LLM-as-judge / `acc.answer_judge` 热路径  
- 改 `chat/graph.py`；扩 E2 金标；新 GHA secret job  
- 全节点补 `module=`（仍可 defer）  

---

## 验收标准

- [ ] `tracing.score_current_trace` 存在；tracing 关时零 SDK 调用
- [ ] `OPS_EVAL_SCORE_SAMPLE_RATE=0` 时 supervisor fallback **不**打分；rate=1 + mock tracing 时写 `stab.fallback`
- [ ] 至少一处 `supervisor_fallback` → `stab.fallback` 调用点
- [ ] GUIDE 落盘并链到 `eval/README.md`
- [ ] `pytest tests -q --tb=short -k 'eval_sample or score_current'`（或 30 写明等价）绿
- [ ] `pytest tests -q --tb=short -k 'eval_agent or eval_experiment'` 不回归
- [ ] `chat/graph.py` 零 diff；无新 GHA secret workflow
- [ ] `npx --yes dsh-coding-kit task lint-wiki-delta --target .` 通过

---

## failure_paths

| 触发 | 行为 | 可重试 | 用户可见 |
|---|---|---|---|
| tracing 关 / 无 key | score no-op | — | 无 |
| sample miss | 不写 score | — | 无 |
| SDK score 抛错 | 吞掉；业务继续 | 是 | 日志 debug |
| sample_rate 非法 | 按 0 关闭并 warning | 是 | 日志 |

---

## 给执行帽必读

1. `eval/ROADMAP` §3.2 score 名 · §3.3 P1 score 封装  
2. `app/ops/tracing.py` · `app/ops/lg_rag/multi/nodes.py`（supervisor_fallback）  
3. `docs/standards/CODING_BACKEND_L2_v1_zh.md`  
4. 本 task · `PROMPT_30_execute.md`

---

## test_strategy

```text
required · mock Langfuse
pytest -k eval_sample（或 score_current）
回归：-k 'eval_agent or eval_experiment'
不连真 Langfuse
ruff 触及路径
chat/graph.py git diff 空
```

---

## 思考轮控制

| 字段 | 值 |
|---|---|
| **actual_last_round** | R4 |
| **early_stop** | yes |
| **early_stop_reason** | 默认 sample_rate=0 + 单 score 名 + GUIDE 已钉；judge/E5 排除 |
| **residual_risks** | 30 可能全量节点打分；验收限 1～2 调用点 |

### R0
E4 = 规则分热路径 + Annotation 文档，不是 judge。

### R1
默认关闭采样，避免生产突打分。

### R2
仅 `stab.fallback` 必做；其它 score 名留给后续。

### R3
Annotation = GUIDE，不调 Queue API。

### R4
不绑 E5；不改 chat/graph。

### R5
（提前停 · 未开）

---

### 自检结论（执行者）

（30 回填）

---

## 修订

| 日期 | 说明 |
|---|---|
| 2026-08-28 | 00 起草 E4；维护者令开 E4；闸代签；00 不实现 |
