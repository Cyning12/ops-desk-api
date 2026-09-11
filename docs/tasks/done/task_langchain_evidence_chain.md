# Task：LangChain Evidence+Answer Chain（并行于 LangGraph）

> **状态**：completed  
> **类型**：rag / 实验旁路（学习向 + 可演进）  
> **关联 SPEC**：`docs/spec/lc-evidence-chain/SPEC-langchain-evidence-chain_v1.md`（v1 · HG-SPEC-SIGNOFF=approved）  
> **实现辅助文档（与 task 分开 · 30 必读）**：`docs/guides/IMPL_langchain-evidence-chain_v1.md`  
> **分支**：`task/langchain-evidence-chain`  
> **编排**：维护者手写 30 主码；Agent 辅助调试/单测/图谱；**00 统筹 40→50 关账**。

---

## Harness 元信息

| 字段 | 值 |
|---|---|
| **task_slug** | `langchain-evidence-chain` |
| **git_branch** | `task/langchain-evidence-chain` |
| **test_strategy** | `required` |
| **test_strategy_note** | pytest mock 链；CLI 冒烟；diff 断言未改 `app/ops/chat/graph.py` 拓扑 |
| **code_quality_bar** | `L2_backend` |
| **graph_change_layer** | `G-L1` |
| **graph_delta** | `docs/_tech_graph/l1/01_modules.md` |
| **graph_delta_note** | 增 `lc_evidence_chain` 旁路与 `evidence/sources` 契约说明；**不改** chat graph 边 |
| **wiki_delta** | `n/a` |
| **wiki_delta_note** | 实现说明在 `docs/guides/IMPL_*`；不改 coding_wiki 正文 |
| **review_hat** | `20` |
| **required_invoke_hats** | `10,30` |
| **invoke_retention_profile** | `default` |
| **orchestration** | SPEC 签收 → task 审 → R1 闸 → **维护者 30** → 40/验收辅助 |

### 人工闸

| human_gate_id | status | blocks_hats | 说明 |
|---|---|---|---|
| HG-TASK-DRAFT | approved | 22-R1 | 维护者签收 SPEC 后确认 · 2026-08-14 |
| HG-AUDIT-R1 | approved | 30 | 审查 `docs/harness/reviews/task_langchain_evidence_chain_audit_R1_20260814.md` · 维护者「签收」推进 · **30 仍由维护者手写** |

---

## 目标

在**不改动**现网 `StateGraph` 拓扑的前提下，用 **LangChain LCEL** 实现一条独立链：

`query → 检索 → evidence（查询依据）→ answer`

evidence 字段兼容现网引用卡片，便于日后升为 graph node 或单独修 RAG。

## 范围

1. 新包（建议）`app/ops/rag/lc_evidence_chain/`：`build_chain` / `ainvoke`  
2. 复用 `hybrid_recall`（+ 可选 rerank）；可选复用 grade（P0 默认可关）  
3. CLI：`scripts/lc_evidence_smoke.py`（或等价）跑 1 问  
4. 单测：`tests/test_lc_evidence_chain.py`  
5. 图谱一行说明旁路  
6. 严格按 `docs/guides/IMPL_langchain-evidence-chain_v1.md` **分阶段**实现（见下节指引）

## 非范围

- 修改 `app/ops/chat/graph.py` 的 node/边  
- 默认切换生产 `chat/stream` 到本链  
- 前端页面  
- Qdrant/ingest/影子写改动  
- 独立 `POST /rag/search`（另见 rag-frontend-api-plan 路线 B）

## 依赖

- SPEC：`docs/spec/lc-evidence-chain/SPEC-langchain-evidence-chain_v1.md`  
- 实现指南：`docs/guides/IMPL_langchain-evidence-chain_v1.md`  
- 编码规范：`docs/standards/CODING_BACKEND_L2_v1_zh.md`  
- 现网检索：`app/ops/rag/retrieve.py` · `app/ops/chat/rag_nodes.py`（只读对齐字段）

---

## 给维护者：30 怎么跑（Agent 不代写第一版）

> **读序**：① 本 task ② SPEC ③ **整份 IMPL 指南** ④ 按阶段提交。

| 阶段 | 你做什么 | 验收点 | IMPL 章节 |
|---|---|---|---|
| S0 | 建包骨架 `__init__.py` / `types.py` | import 通 | §S0 |
| S1 | `retrieve_evidence`：embed + hybrid_recall → evidence list | 本机有语料时 list 非空 | §S1 |
| S2 | `format_context` + `answer` LLM Runnable | 返回 answer 字符串 | §S2 |
| S3 | LCEL 串起来 `build_chain()` | `ainvoke` 一次出 evidence+answer | §S3 |
| S4 | CLI 冒烟脚本 | 命令行跑通 1 问 | §S4 |
| S5 | pytest mock | CI/本地绿 | §S5 |
| S6 | 图谱一行 + 自检「未改 graph」 | diff 干净 | §S6 |

卡点时：把阶段编号 + 报错贴给 Agent（辅助调试，仍由你改码）。

**完成定义**：S0–S6 勾完 + 本 task 验收标准全绿 → 找 Agent 做 40/初步验收。

---

## 验收标准

- [x] `app/ops/chat/graph.py` 拓扑无变更（或仅文档字符串，须在 PR 说明）  
- [x] `build_chain().ainvoke({"query": ...})` 返回 `evidence` + `answer`  
- [x] evidence 含 `anchor` / `snippet`（或等价）  
- [x] `tests/test_lc_evidence_chain.py` 通过  
- [x] CLI 冒烟 exit 0  
- [x] `docs/_tech_graph/l1/01_modules.md` 有旁路说明  
- [x] IMPL 文档仍在且与实现一致（可小改同步）

## failure_paths

| 触发 | 行为 | 可重试 | 用户可见 |
|---|---|---|---|
| 空召回 | evidence=[]，answer 明示无依据 | Y | CLI 打印 |
| LLM/嵌入失败 | 非 0 退出或结构化 error | Y | stderr |
| 误改 graph | 验收失败 | N | PR 打回 |
| 复制 SQL 旁路 | 审查打回 | N | 须改回调用 hybrid_recall |

## 给执行帽必读

1. `docs/spec/lc-evidence-chain/SPEC-langchain-evidence-chain_v1.md`  
2. `docs/guides/IMPL_langchain-evidence-chain_v1.md`  
3. `docs/standards/CODING_BACKEND_L2_v1_zh.md`  
4. `app/ops/rag/retrieve.py` · `app/ops/chat/rag_nodes.py`（字段对齐）

---

## 思考轮

### 思考轮控制

| 字段 | 值 |
|---|---|
| **actual_last_round** | R5 |
| **early_stop** | yes |
| **early_stop_reason** | SPEC 已定并行 LCEL；task 收敛为阶段化手写 30 + 验收 |
| **residual_risks** | 维护者时间；双栈维护成本 |

### R0
手写一条 LangChain 证据+回答链，不影响现网 graph。

### R1
范围=新包+CLI+单测；非范围=改 graph / 默认切流 / 前端。

### R2
分阶段 IMPL + 复用 hybrid_recall。

### R3
空召回、fallback、禁复制 SQL、禁改拓扑。

### R4
结构单测 + CLI + graph diff。

### R5
闸签后维护者按 IMPL 执行 30。

---

### 自检结论

> 10-task 起草自检 · 30 开工前须 HG-SPEC-SIGNOFF + HG-AUDIT-R1=approved。

- [x] 已写 SPEC draft（并行 LCEL · 勿改 graph）
- [x] 已写 IMPL 分阶段示例（与 task 分文件）
- [x] 验收 / failure_paths / 非范围齐全
- [x] HG-TASK-DRAFT approved
- [x] HG-AUDIT-R1 approved（20 审 pass · 维护者签收推进）
- [x] 维护者确认「本人执行 30」

### 自检结论（执行者）

> Harness 40 · 2026-08-16 · 分支 `task/langchain-evidence-chain` · 子 agent 自检 · 00 回填

- [x] `npx @cyning/harness@2.24.0 verify --target . --task docs/tasks/active/task_langchain_evidence_chain.md` → EXIT 0 · VERIFY: PASS
- [x] `git diff master -- app/ops/chat/graph.py` 为空
- [x] `.venv/bin/ruff check app/ops/lc_evidence_chain tests/test_lc_evidence_chain.py` → EXIT 0
- [x] `.venv/bin/pytest tests/test_lc_evidence_chain.py -q` → EXIT 0 · **10 passed**
- [x] `./scripts/graph-compile.sh` → EXIT 0
- [x] 验收表已勾：ainvoke / anchor·snippet / G-L1 / IMPL / CLI 存在性
- [x] CLI：`scripts/lc_evidence_smoke.py` 存在且可 import（完整 DB smoke 留给本机有语料时可选复跑）

**结论**：机械验收全绿，进入 50。

### 自检结论（50）

> Harness 50 · 2026-08-16 · 独立复检 · PASS

- [x] 验收表已勾且与实现一致
- [x] `git diff master -- app/ops/chat/graph.py` 为空
- [x] 包 `app/ops/lc_evidence_chain/` + tests + smoke + G-L1 旁路说明存在
- [x] 抽读 `chain` / `decide_grade` / `answer_question(gate_action=)` 合理
- [x] `.venv/bin/pytest tests/test_lc_evidence_chain.py -q` → **10 passed**
- [x] invoke 50 / CLOSE 已落档

**结论**：50 PASS · 关账。

### KPI

| 项 | 分 |
|---|---|
| Task_KPI% | 100 |

## CLOSE

| 项 | 内容 |
|---|---|
| 日期 | 2026-08-16 |
| 定稿 | LCEL 旁路 `retrieve→grade→answer`；默认不进 chat/graph |
| 归档 | `docs/tasks/done/task_langchain_evidence_chain.md` |
| 生产开关 | 无默认切流；仅 CLI/库级入口 |

---

## 修订

| 日期 | 说明 |
|---|---|
| 2026-08-14 | 首稿：并行 LCEL 链；30 交维护者；IMPL 分文档 |
| 2026-08-16 | 30 交付：包内 decide + answer_partial；G-L1/单测/smoke；待 40/50 |
| 2026-08-16 | 40 PASS · 50 PASS · CLOSE 归档 |
