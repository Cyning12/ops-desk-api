# task_memory_facts_p0 · 20-task-audit 审查文（R1）

| 项 | 内容 |
|----|------|
| **日期** | 2026-09-21 |
| **帽** | 20-task-audit（R1） |
| **对象** | `docs/tasks/active/task_memory_facts_p0.md` |
| **对照** | `docs/spec/memory-facts-p0/SPEC-memory-facts-p0_v1.md`（signed） |

## 结论摘要

| 维度 | 结论 |
|---|---|
| **内容** | ❌ **1 项阻塞**（行为变更类 checklist：验收缺「旧测 grep 影响面」项）→ **退回 10-task** |
| **流程闸** | HG-AUDIT-R1=pending · HG-GRAPH-MODULES=pending（维护者签，见文末签闸清单） |
| **思考轮** | PASS（控制表 R0–R5 齐 · 回填闭合 · 无 early_stop · residual_risks 已填且与 SPEC 残留一致） |

## 核对项（已通过部分）

| 核对 | 结论 |
|---|---|
| 范围 M0–M5 vs SPEC §2 D1–D5 | 一致（schema/闸/状态机/召回注入/断言/图谱全覆盖，无擅自扩缩） |
| 非范围 vs SPEC §3 | 一致（向量/LLM 抽取/画像/HTTP 写端点/摘要/物理删除权均排除） |
| 钉死契约 vs SPEC §2/§5 | 一致（默认关零 diff、确定性召回、ctx 身份、双保险过期、降级语义） |
| failure_paths | 12 行均含 触发→行为→可重试→用户可见；闸拒开工在首行 |
| test_strategy | required，note 与验收断言一一对应；不连真外网/生产 Qdrant |
| 必读列表 | 含 AGENTS / task / SPEC / L2 规范 / 触及代码 / FRAGMENT_30_gate_verify |
| task lint | PASS（2026-09-21） |

## 阻塞（内容 · 退回 10-task 回填）

**B1 · 验收标准缺「旧测 grep 影响面」项**（行为变更类 checklist · 非机械闸）

本 task 引入新 fallback 语义（记忆召回 DB 故障→降级无记忆注入）且 30 将修改既有装配路径 `app/ops/lg_rag/continuity.py` 与 `app/db/models.py`，属行为变更类边缘情形，验收标准须显式列旧测影响面。20 已代跑 grep，回填时直接使用：

| 面 | 结果 |
|---|---|
| `continuity\|assemble_graph_messages\|compress_window` | 17 命中 · 2 文件：`tests/test_session_continuity.py` · `tests/test_lg_rag_session_continuity.py`（默认关零 diff 的直接守护） |
| `app.db.models` | 27 命中 · 14 文件（含 `conftest.py`；新增 model 为纯增量，低风险） |
| `alembic\|migration` | 0 命中（无 migration 测试；可逆性靠验收 M0 自证） |
| `tenant_context` | 10 命中 · 2 文件（本 task 只复用不改义） |
| `load_session_turns\|session/history` | 0 命中 |

**回填位置**：task「验收标准」节新增一项。

---

> 本 R1 有内容阻塞，**不附 30 Prompt**。下一棒：10-task 回填 B1 → 20 R2 复审。
