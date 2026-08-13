# Invoke：CLOSE · rag-zhparser-arm-a

---

## 元信息表

| 字段 | 值 |
|------|-----|
| hat_id | CLOSE |
| task_slug | `rag-zhparser-arm-a` |
| related_30 | invoke_20260812_30_40_rag-zhparser-arm-a.md |
| related_50 | invoke_20260812_50_rag-zhparser-arm-a.md |
| git_branch | `task/rag-zhparser-arm-a` |
| created_utc_or_local | 2026-08-13 |
| notes | 维护者授权：r4-A 实测定稿后关账；弃 A→C；A 入口保留 |

---

## CLOSE 结论：**PASS**

### 裁决（相对 r4-2）

| 指标 | r4-2 | r4-A | Δ / 裁决 |
|---|---|---|---|
| zh2zh recall@5 | 17/20（85%） | 17/20（85%） | **+0pp** → 落 &lt; +5pp 档 |
| kw 非空 | 5/71 | 5/73 | 仍几乎全死；zh2zh **0/20** |
| 同 id 翻转 | — | fixed=0 / regressed=0 | 无结构变化 |

→ **放弃 A 上生产，转 C 臂**。  
→ **保留 A 可调用入口**（不删）：`Dockerfile.pg-zhparser` · `experiments/rag_compare/zhparser_arm_a/` · `RAG_FTS_CONFIG=chinese`（默认仍 `simple`）。

### 证据

- 分词探针 / 影子库 / COPY 8574：维护者实跑（task 自检结论）
- 金样：`reports/r4-A.yaml`
- 对照回写：`experiments/rag_compare/README.md` · `REPORT_q6_arms_vs_baseline_20260812.md`
- 50 初验 PASS（附条件）后维护者补齐实跑 → 终验可关

### 关账动作

- task：状态 `completed` · 验收全勾 · `### KPI` · `## CLOSE`
- `harness task close --file docs/tasks/active/task_rag_zhparser_arm_a.md --yes`
- 归档 → `docs/tasks/done/task_rag_zhparser_arm_a.md`
