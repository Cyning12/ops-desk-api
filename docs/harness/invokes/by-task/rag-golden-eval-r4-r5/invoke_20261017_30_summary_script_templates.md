---
hat: 30
task_slug: rag_golden_eval_r4_r5
date: 2026-10-17
---

# Invoke 30 · rag-golden-eval-r4-r5 汇总脚本+模板+测试交付

## GATE_VERIFY（开工前）

`npx --yes spec-wave verify --target . --task docs/tasks/active/task_rag_golden_eval_r4_r5.md` → **VERIFY: PASS**

| human_gate_id | status | blocks_hats | 30 可否开工 |
|---------------|--------|-------------|------------|
| HG-TASK-DRAFT | approved | 20, 30 | ✅ |
| HG-AUDIT-R1 | approved | 30 | ✅ |
| HG-GRAPH-MODULES | approved | 30 | ✅（graph_change_layer=none） |
| HG-EVAL-LIVE-RUN | pending | 40 | 不阻 30（仅阻结案真跑） |

分支核验：`task/rag-golden-eval-r4-r5`（正确 · 非 master 直改）。

## 交付清单

| 交付物 | 路径 | 对应 TC |
|--------|------|---------|
| E1 汇总脚本 | `evals/golden/summarize_r4.py` | TC-R4-1 |
| E4 确定性测试 | `tests/test_golden_eval_r4_summary.py`（12 项） | TC-R4-1 |
| E2 结案报告模板 | `reports/r4_final_TEMPLATE.md` | TC-R4-2 |
| E3 Demo 证据表模板 | `evals/golden/demo_evidence_TEMPLATE.md` | TC-R4-3 |
| task 文档回填 | `docs/tasks/active/task_rag_golden_eval_r4_r5.md`（状态/TC/自检/修订记录） | — |

## 设计要点（留 20 审要点）

1. **不旁路 runner**：summarize_r4.py 只读 `run_eval.py` 产出的报告 YAML 做聚合，不 import app/*（CI 无需 DB/LLM/env），不连库不连外网。
2. **FP-2 显式失败**：`load_report()` 对缺 results / 空 results / 非法 quadrant / 非法 verdict / 非法三态指标 / 非法 gate_action 一律 SystemExit 非零退出，不静默跳过条目冒充全量。
3. **zh2en ≥1/3 三态判定**：MET / NOT_MET / NO_DATA；**判定用未舍入原始比率**（展示值 round(·,4) 会让恰好 1/3 误判 NOT_MET —— 测试 `test_zh2en_gate_three_states[1-3-MET]` 钉死此边界）。
4. **分母口径对齐 runner**：各指标分母 = 该指标非 null 条数（negative 象限 recall/cite 分母为 0，与 `quadrant_recall_summary` 一致）。
5. **拒答分类**：误答 = negative 象限 gate_action≠refuse；疑似误拒 = 正样本（有金标命中）gate_action=refuse，仅列 ID 供人工复核，不改默认参数（FP-3）。
6. **FP-7 小样本老实标**：每个比率附 `n=N · Wilson 95% CI=[lo,hi] · confidence=low`；结案报告头部透传源报告观测三字段（measurement_source/confidence/comparability）。
7. **FP-8 注记**：SPEC-evaluation-observation 真值文件两仓未检索到（照登：无实证），观测口径按路线 A-P1-3 引用口径对齐，注记写死在 `SPEC_OBSERVATION_NOTE` 常量与模板第 5 节。
8. **兼容性**：旧过程稿 71 条（pre-G72/G73）与现集 73 条均可聚合（脚本按报告内容取数，不假设条数）；默认排除 `r4_final_*` 防止把结案产物当源报告递归聚合。

## 契约核对结论（TC-R4-6 · E5）

亲读 `../ops-desk-workspace/docs/contracts/rag-knowledge-contract-v1.md` 对照实现 → **零漂移**：

| 契约条目 | 实现 | 结论 |
|----------|------|------|
| Q4a 四级枚举 irrelevant/weak/relevant/exact | `app/ops/rag/grader.py` `Relevance` StrEnum | 对齐（另有内部标记 `UNRATED` level=-1，never 出现在 grader 输出 → 观察项非漂移） |
| Q4b 批量 top-5 单次调用 + gate 决策 | `grade_chunks()` 批量单调用；`decide()`：best≤weak→refuse / relevant→answer_partial / exact→answer / 空 grades→refuse | 对齐 |
| Q4b RRF 分数不进 gate（仅日志） | `retrieve.py` RRF_K=60，`rrf_fuse` 1:1 等权双通道，分数仅日志 | 对齐 |
| Q4c 拒答文案逐字 | `REFUSAL_TEXT` = 「未查询到相关内容，无法针对此问题进行回答」 | 逐字一致 |
| Q4c 引用卡字段 + snippet ≤400 + 前缀剥离 | `app/ops/chat/rag_nodes.py:54-62` `_to_source` | 对齐 |

契约文件本 task 零 diff；无 FP-5 上抛事项（零漂移）。

## 验证证据

| 命令 | 结果 | exit |
|------|------|------|
| `pytest tests/test_golden_eval_r4_summary.py -q` | 12 passed | 0 |
| `pytest tests/test_golden_eval_runner.py -q`（回归） | 13 passed | 0 |
| `ruff check evals/golden/summarize_r4.py tests/test_golden_eval_r4_summary.py` | All checks passed! | 0 |
| `summarize_r4.py --report reports/r4-1.yaml --out-* /tmp/…`（冒烟 · 输出到 /tmp 不入仓） | SUMMARY zh2en=19/25 gate=MET refuse=9/10 | 0 |
| `npx --yes spec-wave task lint --file docs/tasks/active/task_rag_golden_eval_r4_r5.md` | LINT: PASS | 0 |
| `git status` | `app/` 零 diff · `queries_v1.yaml`/`run_eval.py` 零 diff（TC-R4-4） | — |

## 非范围确认

- 未改 `app/ops/rag/**` / `app/ops/lg_rag/**` / `app/db/**`（零 diff 已核）。
- 未做结案真跑（TC-R4-5 · HG-EVAL-LIVE-RUN pending · 40/维护者在授权环境执行）。
- 未调参、未改契约、未接 BMH、未加 CI workflow。
- 冒烟跑出 `reports/r4_final_*` 产物仅落 /tmp，未入仓（避免冒充结案产物）。

## 移交 40/维护者

1. HG-EVAL-LIVE-RUN 签署后：真跑 `run_eval.py`（现集 73 条）→ `summarize_r4.py --report <新报告>` 生成 `reports/r4_final_*` → 按 `reports/r4_final_TEMPLATE.md` 补「结论与签字」。
2. Demo 证据：按 `evals/golden/demo_evidence_TEMPLATE.md` 填 ≥4 条（每象限 ≥1 · 含 ≥1 负样本拒答演示）→ 落 `reports/demo_evidence_*.md`。
3. 注意旧过程稿为 71 条（pre-G72/G73），结案真跑必须用现集 73 条，zh2en 分母按实际报告。
