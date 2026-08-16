# Invoke：50 · langchain-evidence-chain（独立复检）

---

## 元信息表

| 字段 | 值 |
|------|-----|
| hat_id | 50 |
| task_slug | `langchain-evidence-chain` |
| task_paths | `docs/tasks/active/task_langchain_evidence_chain.md` |
| related_30 | `invoke_20260816_30_langchain-evidence-chain.md` |
| related_40 | `invoke_20260816_40_langchain-evidence-chain.md` |
| git_branch | `task/langchain-evidence-chain` |
| created_utc_or_local | 2026-08-16 |
| notes | Harness 50 独立复检 · 只读抽查 + pytest 复跑 · 关账机械动作 |

---

## 50 结论：**PASS**

### 对照验收标准

| 验收项 | 50 判定 | 证据 |
|---|---|---|
| `app/ops/chat/graph.py` 拓扑无变更 | **pass** | `git diff master -- app/ops/chat/graph.py` 为空 |
| `build_chain().ainvoke` → evidence + answer | **pass** | `chain.py` LCEL retrieve\|grade\|answer；单测覆盖 |
| evidence 含 `anchor` / `snippet` | **pass** | `types.EvidenceItem` + 单测 |
| `tests/test_lc_evidence_chain.py` | **pass** | 复跑 **10 passed** |
| CLI 冒烟 | **pass** | `scripts/lc_evidence_smoke.py` 存在（本轮不强制连 DB） |
| G-L1 `01_modules.md` 旁路说明 | **pass** | `lc_evidence_chain` 行 + **默认不进入** chat/graph |
| IMPL 与实现一致 | **pass** | 包路径 `app/ops/lc_evidence_chain/`（task 建议路径已落地为旁路包） |

### 代码抽查

| 点 | 判定 | 备注 |
|---|---|---|
| `chain.py` 编排 | pass | retrieve → grade → answer；`gate_action` 写入 meta 并传入 answer |
| `decide_grade` | pass | weak→refuse；relevant→answer_partial；exact→answer；空 grades fail-closed |
| `answer_question(gate_action=)` | pass | 空证据早退；`answer_partial` 注入「仅部分证据」约束 |

### 50 复跑命令

| 命令 | 退出码 |
|---|---|
| `.venv/bin/pytest tests/test_lc_evidence_chain.py -q` | 0 · **10 passed** |
| `git diff master -- app/ops/chat/graph.py` | 空 |

### 50 不通过项

无。

### 遗留风险（不阻塞关账）

1. CLI 全量连库冒烟留给本机有语料时可选复跑  
2. 双栈（LangGraph chat + LCEL 旁路）维护成本  
3. 工作树另有未纳入本 task 交付的 `_tech_graph` 脏文件（flow/json），关账不依赖其干净
