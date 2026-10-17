# CLOSE：rag-golden-eval-r4-r5（R-4 四类 golden 结案级评测 + R-5 Demo 证据表 · 汇总脚本/模板/测试交付）（2026-10-17）

> **task**：[../done/task_rag_golden_eval_r4_r5.md](../done/task_rag_golden_eval_r4_r5.md)（已归档 done/）
> **类型**：评测 / 证据资产（检索轨 golden 结案汇总 + Demo 证据表模板 · **零生产语义改动**）
> **关账日期**：2026-10-17 · 帽位：CLOSE（50 · 批量关账棒 · 分支 close/active-batch-20261017-pm · 三闸维护者授权 00 代录签收 m00238）

---

## 一 · 任务信息

| 项 | 值 |
|----|----|
| task_slug | `rag_golden_eval_r4_r5` |
| 依据 | 路线 `../ops-desk-workspace/docs/05-plan/04-agent-completion-roadmap_v1_zh.md` §P1-RAG（R-4/R-5 标注「仍可能缺口 · 结案勿假设」）· §3 评测纪律（自建不用 BMH）· 契约 `../ops-desk-workspace/docs/contracts/rag-knowledge-contract-v1.md`（只读核对） |
| 背景 | 金标集 73 条（`queries_v1.yaml`）与 runner（`run_eval.py`）早已闭环，`reports/r4*.yaml` 18 份皆逐案过程稿——**无一份对齐路线的结案报告**（逐象限汇总 + 门槛判定 + confidence + 观测口径）；zh2en ≥1/3 门槛无显式判定；拒答正确率无汇总；R-5 Demo 证据表无资产 |
| 目标 | 交付结案级汇总脚本（复用 runner 产物不旁路重写检索路径）+ 确定性测试 + 结案报告模板 + R-5 Demo 证据表模板；真跑回填钉人工闸 HG-EVAL-LIVE-RUN 由 40/维护者执行 |
| 分支 | `task/rag-golden-eval-r4-r5`（自 master 新切） |
| 帽链 | 10-task 落稿 → 20-task-audit R1 **签收（零内容阻塞）** → 三闸 approved（2026-10-17 00 代录 · m00238 · R1 书面审豁免口径照登）→ 30 交付（汇总脚本+12 测+两模板+契约核对 · TC-R4-1/2/3/4/6/7 绿）→ PR #262 → **CLOSE（本档）**；40 棒未走（TC-R4-5 结案真跑待 HG-EVAL-LIVE-RUN） |

## 二 · 交付

| 环节 | 实证 |
|------|------|
| PR | [#262](https://github.com/Cyning12/ops-desk-api/pull/262) · **MERGED 2026-10-17T05:50:17Z · squash commit `e1697ad`** |
| E1 汇总脚本 | `evals/golden/summarize_r4.py`（394 行）：只读 `reports/r4*.yaml` 聚合不 import app/*（CI 无需 DB/LLM）· 四象限（zh2en/zh2zh/en2en/negative）recall@5 / min_relevance / citation_in_hits / 拒答正确率聚合 · zh2en ≥1/3 **三态判定** MET/NOT_MET/NO_DATA（**判定用未舍入原始比率**，round(·,4) 会让恰好 1/3 误判，测试钉死边界）· 每比率附 `n=N · Wilson 95% CI=[lo,hi] · confidence=low`（FP-7 小样本老实标）· 拒答分类：误答=negative 象限 gate_action≠refuse · 疑似误拒=正样本 refuse 仅列 ID 供人工复核 · FP-2 残缺/非法报告 SystemExit 非零退出不冒充全量 · **原子写** `write_text_atomic`（mkstemp+fsync+replace · :338-350）出结案 YAML+Markdown · 默认排除 `r4_final_*` 防递归聚合结案产物 · 兼容旧过程稿 71 条与现集 73 条（按报告内容取数不假设条数） |
| E4 测试 | `tests/test_golden_eval_r4_summary.py` **12 测全绿**（四象限分组 / zh2en 门槛三态含 1/3 边界 / 拒答分类 / confidence 标注存在 / FP-2 显式失败 / CLI 端到端确定性 / r4-1.yaml 结构冒烟）；不连真库/真 LLM/外网 |
| E2 结案报告模板 | `reports/r4_final_TEMPLATE.md`（逐象限指标 + zh2en 门槛显式判定位 + 样本量/confidence 位 + 观测口径注记位 · FP-8 注记写死第 5 节） |
| E3 Demo 证据表模板 | `evals/golden/demo_evidence_TEMPLATE.md`（版本/commit/输入/结果/引用/错误与降级/复现命令七段 · 回填纪律：≥4 条每象限 ≥1 含 ≥1 负样本拒答演示） |
| E5 契约核对 | **零漂移**（TC-R4-6）：亲读契约 v1 对照 `app/ops/rag/grader.py` / `retrieve.py` / `app/ops/chat/rag_nodes.py:54-62`——四级枚举 / gate 决策（best≤weak→refuse · relevant→answer_partial · exact→answer · 空 grades→refuse）/ RRF_K=60 1:1 等权融合分数不进 gate / 拒答文案逐字 / 引用卡字段+snippet≤400+前缀剥离 全对齐；观察项 `Relevance.UNRATED`（level=-1）为内部标记 never 出现在 grader 输出 → 非漂移；契约文件零 diff 无 FP-5 上抛 |
| 图谱/码面 | `graph_change_layer=none` · `app/ops/rag/**` · `app/ops/lg_rag/**` · `app/db/**` 零 diff · `queries_v1.yaml`/`run_eval.py` 零语义 diff（TC-R4-4） |
| invokes | `docs/harness/invokes/by-task/rag-golden-eval-r4-r5/`（10_task_draft / 20_task_audit_r1 / 30_summary_script_templates） |
| 审查文 | 址A `docs/harness/reviews/task_rag_golden_eval_r4_r5_audit_R1_20261017.md`（R1 签收零内容阻塞 · 无 R2） |
| **CLOSE 增量** | 本档落盘（50 帽 · 零 git 操作 · 零其他文件改动） |

## 三 · 核验结论（验收终态摘要 · TC-R4-1..7）

| 验收项 | 结果 | 实证 |
|--------|------|------|
| TC-R4-1 脚本+测试 | ✅ | `pytest tests/test_golden_eval_r4_summary.py -q` → 12 passed（30 自检 + 本 CLOSE 复核 invoke 证据在案） |
| TC-R4-2 结案报告模板 | ✅ | `reports/r4_final_TEMPLATE.md` 四象限指标/门槛判定/confidence/观测口径位全在 |
| TC-R4-3 Demo 证据表模板 | ✅ | `evals/golden/demo_evidence_TEMPLATE.md` 七段全在 · 回填纪律（≥4 条每象限 ≥1 含负样本拒答）写入模板 |
| TC-R4-4 零 diff | ✅ | 30 自检 `git status`：app/ 零改动 · queries/runner 零 diff |
| TC-R4-5 结案真跑 | ⏸ **待 40/维护者** | **HG-EVAL-LIVE-RUN pending**——真跑需本地/生产库+真 LLM key 授权；**必须用现集 73 条**（旧过程稿 71 条 pre-G72/G73 ≠ 现集，zh2en 分母按实际报告） |
| TC-R4-6 契约核对 | ✅ | 零漂移（详 §二 E5）；SPEC-evaluation-observation 真值文件两仓未检索到 → 报告按路线 A-P1-3 引用口径对齐并显式注记「照登：无实证」（FP-8 · 20 R1 独立 grep 复核属实：仅路线 :67 一处引用） |
| TC-R4-7 质量门 | ✅ | ruff 触及路径 All checks passed · `test_golden_eval_runner.py` 13 passed 零新增红 · task lint LINT: PASS |

**CLOSE 质量钉复跑（本帽 · 归档后仓态 · 重定向取真码）**：

- `npx --yes spec-wave verify --target . --task docs/tasks/done/task_rag_golden_eval_r4_r5.md` > /tmp/verify_close_rag.log → **EXIT=0 · VERIFY: PASS**（三闸 approved · HG-EVAL-LIVE-RUN pending 不阻 30/CLOSE · 仅阻结案真跑）。
- `npx --yes spec-wave task lint --file docs/tasks/done/task_rag_golden_eval_r4_r5.md` → **EXIT=0 · LINT: PASS**。

## 四 · 偏差与 nit（如实照登）

1. **HG-EVAL-LIVE-RUN 保持 pending（唯一未闭环验收项）**：结案级真跑（TC-R4-5）需维护者签授权（本地/生产库 + 真 LLM key）；30 交付物本身不依赖本闸，故本 task 可 CLOSE、真跑回填移交 40/维护者（承 task_memory_golden_eval「真跑=维护者复制区」先例）。真跑流程：`run_eval.py`（现集 73 条）→ `summarize_r4.py --report <新报告>` → 按模板补「结论与签字」→ Demo 证据 ≥4 条落 `reports/demo_evidence_*.md`。
2. **冒烟跑产物仅 /tmp 未入仓（照登）**：30 冒烟 `summarize_r4.py --report reports/r4-1.yaml` 出 SUMMARY zh2en=19/25 gate=MET refuse=9/10——**过程稿结构验证数值，非结案数值**；产物刻意落 /tmp 不入仓，防冒充结案产物。
3. **旧过程稿 71 条 ≠ 现集 73 条（照登）**：`reports/r4*.yaml` 18 份系 pre-G72/G73 旧集过程稿；结案真跑必须用现集 73 条，zh2en 分母按实际报告取数（脚本兼容两种条数，不假设条数）。
4. **SPEC-evaluation-observation 两仓无真值（照登：无实证）**：api 仓与 workspace 仓均未检索到该 SPEC 真值文件（20 R1 独立 grep 复核：仅路线 :67 一处引用）；观测口径以路线引用口径为准，注记写死 `SPEC_OBSERVATION_NOTE` 常量与模板第 5 节（FP-8）；若日后觅得真值文件按实校正。
5. **观察项非漂移**：`Relevance.UNRATED`（level=-1）为内部标记、never 出现在 grader 输出，不计契约漂移（30 契约核对节在案）。

## 五 · 签录（闸态表与审查文链）

| 闸 / 环节 | 状态 | 文档 / 实证 |
|-----------|------|------------|
| HG-TASK-DRAFT | **approved** | 2026-10-17 维护者授权 00 代录（m00238） |
| HG-AUDIT-R1 | **approved** | 2026-10-17 维护者授权 00 代录（m00238 · 20 R1 书面审经授权豁免口径照登 · R1 审查文实存在址A） |
| HG-GRAPH-MODULES | **approved** | 2026-10-17 代录：全局真值 approved（`docs/_tech_graph/l1/01_modules.md:63`）· `graph_change_layer=none` |
| HG-EVAL-LIVE-RUN | **pending** | 待维护者签：结案真跑需库 + 真 LLM key 访问授权（仅阻 TC-R4-5 · 不阻本 CLOSE） |
| 20 R1 审查 | **签收（零内容阻塞）** | 址A `docs/harness/reviews/task_rag_golden_eval_r4_r5_audit_R1_20261017.md`（73 条四象限逐字核对 · 18 份过程稿计数 · SPEC 缺失独立复核 · lint 亲跑 PASS） |
| invokes | — | `by-task/rag-golden-eval-r4-r5/`（10/20/30 三件） |
| 合并 | **MERGED** | PR [#262](https://github.com/Cyning12/ops-desk-api/pull/262) · squash `e1697ad` · 2026-10-17T05:50:17Z |

## 六 · 资源清理

- **本 CLOSE 不删任何东西**：分支 `task/rag-golden-eval-r4-r5`（本地/远端）**移交 00/维护者统一清理**——task 分支已 squash 合入 master `e1697ad`，删除安全，远端一并清。
- /tmp 冒烟产物（`verify_close_rag.log` 及 30 冒烟 `r4_final_*` 输出）为易失面，不入仓不清理移交。

## 七 · 维护者验收 checklist 与后续建议

### 维护者验收 checklist（需人验收项）

- [ ] **HG-EVAL-LIVE-RUN 签署**：授权本地/生产库 + 真 LLM key 后，40/维护者执行结案真跑（现集 73 条 · 禁复用 71 条旧过程稿充当结案数值）。
- [ ] **结案产物抽验**：`reports/r4_final_*.md|yaml` 头部写死门槛与达成情况与 confidence · zh2en 命中数/26 与拒答正确率显式可见 · 观测口径注记位（FP-8）已填。
- [ ] **Demo 证据抽验**：`reports/demo_evidence_*.md` ≥4 条（每象限 ≥1 · 含 ≥1 负样本拒答演示）· 复现命令可执行。
- [ ] **聚合正确性抽验**：`pytest tests/test_golden_eval_r4_summary.py -q` 12 passed 复跑绿。

### 后续建议

1. **真跑后若 zh2en 未达 ≥1/3 或拒答正确率差**：报告如实判 NOT-MET + 失败条目清单——**不改默认参数**（「未达门槛不改默认」先例 task_rag_reranker_p0 系不变 · 调参另 task）。
2. **SPEC-evaluation-observation 真值寻回**：若日后觅得真值文件，按实校正模板第 5 节注记与 `SPEC_OBSERVATION_NOTE` 常量。
3. **姊妹 task 在册**：生产向量水位核查归 `task_prod_vector_waterline_check`（独立立项 · 本 CLOSE 不涉）。

## 八 · 修订记录

| 日期 | 说明 |
|------|------|
| 2026-10-17 | CLOSE 落稿（50 close 棒 · 批量分支 `close/active-batch-20261017-pm`）：九节沿仓内先例（close_hitl_resume_async_20261015）· 验收终态承 30 invoke TC-R4-1/2/3/4/6/7 实证全录 · TC-R4-5 待闸如实照登 · 质量钉复跑（verify EXIT=0 PASS · task lint EXIT=0 PASS · 重定向取真码）· 冒烟仅 /tmp / 71≠73 / SPEC 无真值 / UNRATED 观察项如实照登 · 零 git 操作 · 零其他文件改动 |

## 九 · 附录

### 关键路径

| 类别 | 路径 |
|------|------|
| task（已归档） | `docs/tasks/done/task_rag_golden_eval_r4_r5.md` |
| CLOSE 档 | `docs/tasks/close/close_rag_golden_eval_r4_r5_20261017.md`（本档） |
| 交付码面 | `evals/golden/summarize_r4.py` · `tests/test_golden_eval_r4_summary.py`（12 测）· `reports/r4_final_TEMPLATE.md` · `evals/golden/demo_evidence_TEMPLATE.md` |
| 审查文（址A） | `docs/harness/reviews/task_rag_golden_eval_r4_r5_audit_R1_20261017.md` |
| invokes | `docs/harness/invokes/by-task/rag-golden-eval-r4-r5/`（10/20/30） |
| 复用资产（零 diff） | `evals/golden/queries_v1.yaml`（73 条）· `evals/golden/run_eval.py` · `evals/golden/hygiene_denylist.yaml` · `reports/r4*.yaml`（18 份过程稿） |

### CLOSE 复跑命令留痕

```bash
npx --yes spec-wave verify --target . --task docs/tasks/done/task_rag_golden_eval_r4_r5.md > /tmp/verify_close_rag.log 2>&1; echo "EXIT=$?"   # EXIT=0 · VERIFY: PASS
npx --yes spec-wave task lint --file docs/tasks/done/task_rag_golden_eval_r4_r5.md                    # EXIT=0 · LINT: PASS
```
