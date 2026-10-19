# Task：rag-golden-eval-live-run（R-4 结案真跑：现集 73 条 golden 对本地知识库全量真跑 + 结案报告 + R-5 Demo 证据表回填）

> **状态**：done（2026-10-19 CLOSE · PR #280 MERGED squash 4ab5f3a · TC-LR-1~6 全 PASS · zh2en MET 19/26=73.08%（门槛≥1/3 · Wilson CI=[0.54,0.86] · confidence=low）· 拒答正确率 10/11 · 整体建议「有条件通过」签字位留维护者 · 归档 done/）
> **类型**：评测真跑（40 轨 · **含 LLM 调用与配额消耗** · 建议零落码——优先复用既有管线全链零新码 · 承 task_local_rag_knowledge_rebuild「零落码 40 单棒」先例）
> **上游**：[`task_rag_golden_eval_r4_r5.md`](../done/task_rag_golden_eval_r4_r5.md) 已 CLOSE（PR #262 · CLOSE 档 [`close_rag_golden_eval_r4_r5_20261017.md`](../close/close_rag_golden_eval_r4_r5_20261017.md)）——**TC-R4-5「结案真跑」移交本 task**，HG-EVAL-LIVE-RUN 维护者 2026-10-19（会话「全做」）选定推进，授权口径由 00 签闸时统一代录
> **分支**：无（建议零落码 · 零 git 操作纪律；报告/invoke 产物提交与否由 00/维护者事后裁定）
> **前置实证（10 亲跑 2026-10-19）**：本地知识库 PG `ops_knowledge_chunks`=8648 == Qdrant `ops_knowledge` points_count=8648（双容器 Up 2 days healthy · 承 PR #276 三对照 match）· `SILICONFLOW_API_KEY` 在 .env 存在非空（grep 计数=1 · 值不落档）· 评测资产齐备（run_eval.py / summarize_r4.py / 双模板 · PR #262 交付）

---

## Harness 元信息

| 字段 | 值 |
|------|-----|
| **task_slug** | `rag_golden_eval_live_run` |
| **git_branch** | 无（零落码建议 · 零 git 操作） |
| **implement_repo** | `ops-desk-api` |
| **test_strategy** | `required` |
| **test_strategy_note** | 实证 + 机断混合：40 真跑实证（真跑命令全文+输出/结案报告/Demo 证据全链留档）；机断旁证 = `pytest tests/test_golden_eval_r4_summary.py -q`（12 测）与 `tests/test_golden_eval_runner.py`（13 测）复跑零新增红（管线零 diff 硬约束的活证）；真跑需本地库+真 LLM key，不占 CI 绿 |
| **code_quality_bar** | `L2_backend` |
| **graph_change_layer** | `none` |
| **graph_delta** | `none` |
| **graph_delta_note** | 建议零落码（既有 run_eval.py 全量真跑 + summarize_r4.py 聚合 + 双模板回填，全链零新码）；无新模块/路由/表/事件类型/配置改动；若执行中实证须落码即 STOP 退回另立 task 补 30 棒+图谱闸评估（FP-6） |
| **wiki_delta** | `n/a` |
| **wiki_delta_note** | 结案数值是否回写路线 §P1-RAG（R-4/R-5 结案口径）由维护者阅结案报告后裁定，非本 task |
| **review_hat** | `20` |
| **required_invoke_hats** | `10,40` |
| **invoke_retention_profile** | `default`（实取 10+40 · 零落码建议下无 30 改码棒；若 FP-6 实证须落码则改 `10,30,40` 并另立 task） |
| **experience_capture** | `recommended` |
| **kpi_aggregator** | `n/a` |
| **orchestration** | 10 落稿 → 20 R1（按维护者授权取舍）→ 维护者签闸（HG-TASK-DRAFT / HG-AUDIT-R1 / HG-EVAL-LIVE-RUN · 00 代录）→ 40 真跑（F1 前置核验+全量真跑 → F2 聚合成结案报告 → F3 Demo 证据表回填 → F4 留档收口）+ 验收勾选/自检结论回填 → CLOSE |
| **freeze_id** | 无 |
| **related_tasks** | [`task_rag_golden_eval_r4_r5.md`](../done/task_rag_golden_eval_r4_r5.md)（直接母体 · TC-R4-5 移交源）· [`task_local_rag_knowledge_rebuild.md`](../done/task_local_rag_knowledge_rebuild.md)（前置 · 8648 知识库 + 零落码 40 单棒先例）· [`task_golden-query-set-v1.md`](../done/task_golden-query-set-v1.md)（金标集+runner 母体）· [`task_memory_golden_eval.md`](../done/task_memory_golden_eval.md)（「真跑=维护者复制区」先例） |

### 人工闸

| human_gate_id | status | blocks_hats | 说明 |
|---------------|--------|-------------|------|
| HG-TASK-DRAFT | approved | 20, 40 | 2026-10-19 维护者「全做」授权 + 授权链（m00238/m01101）00 代录 · R1 task_rag_golden_eval_live_run_audit_R1_20261019.md 通过 |
| HG-AUDIT-R1 | approved | 40 | 2026-10-19 维护者「全做」授权 + 授权链 00 代录 · 20 R1 书面审通过（零阻塞 nit×2 知悉照登） |
| HG-EVAL-LIVE-RUN | approved | 40 | **本 task 核心闸**：维护者 2026-10-19「全做」授权真跑（本地库 + 真 LLM key + 配额消耗）· 授权链 00 代录 |
| HG-GRAPH-MODULES | approved | 30 | 授权链 00 代录 · `graph_change_layer=none` 零图谱改动（零落码裁定承建议 · 无 30 棒）；若 FP-6 实证须落码即 STOP 回抛另立 task 并补签本闸 |

> 关联闸照登：HG-PROD-READONLY-ACCESS 仍 pending（仅阻生产侧任何动作）；**本 task 零涉生产**（本地 compose 口径），不受其阻、也不消解之（FP-9 报告 disclaimer 钉死本地口径）。

---

## 背景与目标

### 移交口径（防重复纪律 · 禁重复立项）

上游 task_rag_golden_eval_r4_r5（PR #262 已 CLOSE）交付了**全部评测资产**：`evals/golden/summarize_r4.py`（394 行 · 逐象限聚合 + zh2en≥1/3 未舍入三态判定 + Wilson 95% CI + 拒答误拒/误答分类 + 原子写）、`tests/test_golden_eval_r4_summary.py`（12 测绿）、`reports/r4_final_TEMPLATE.md`（结案报告模板）、`evals/golden/demo_evidence_TEMPLATE.md`（R-5 Demo 证据表模板）、契约核对零漂移。唯一未闭环验收项 = **TC-R4-5 结案真跑**（HG-EVAL-LIVE-RUN pending 移交）。本 task **只做真跑回填这一增量**，资产零重写。

### 实证锚点（10 亲跑亲读 2026-10-19 · 40 必读）

| 主题 | 命令 / 路径 · 锚点 | 现状（亲跑实录） |
|------|---------------------|-------------------|
| 金标集现集 | `evals/golden/queries_v1.yaml`（575 行）· `grep -o 'quadrant: [a-z0-9]*' | sort | uniq -c` | **73 条四象限：zh2en=26 / zh2zh=20 / en2en=16 / negative=11**（10 亲跑计数）——⚠️ **现集 73 条 ≠ 旧过程稿 71 条**（pre-G72/G73），结案真跑必须用现集，zh2en 分母按实际报告取数（FP-10） |
| 真跑 runner | `evals/golden/run_eval.py` docstring（:1-14） | 用法：`.venv/bin/python evals/golden/run_eval.py`（全量）· `--limit 3`（冒烟）· `--stability 0` · `--out reports/r4.yaml` · `--resume`（断点续跑）；生产同路径 hybrid_recall →（可选 CE rerank）→ grade → decide，不旁路重写 |
| 聚合脚本 | `evals/golden/summarize_r4.py`（:42-50） | `ZH2EN_THRESHOLD = 1.0/3.0`（未舍入原始比率判定，防恰好 1/3 边界误判）；用法 `--report X --out-yaml Y --out-md Z`；默认排除 `r4_final_*` 防递归聚合；FP-2 残缺报告 SystemExit 非零退出不冒充全量；`SPEC_OBSERVATION_NOTE` 常量（FP-8 注记照登） |
| 结案报告模板 | `reports/r4_final_TEMPLATE.md` | 七节：运行标识（语料 N 必须显式）/ 逐象限指标 / 门槛判定（MET/NOT_MET/NO_DATA + Wilson CI + confidence）/ 未达成项与归因 / 观测口径注记（小样本老实标）/ 契约漂移 / 结论与签字 |
| Demo 证据表模板 | `evals/golden/demo_evidence_TEMPLATE.md` | 七段（版本/commit/输入/结果/引用/错误与降级/复现命令）；回填纪律：**≥4 条 · 每象限 ≥1 · 含 ≥1 条负样本拒答演示**；拒答文案须与契约 4c 逐字「未查询到相关内容，无法针对此问题进行回答」；每条与结案报告 case id 交叉引用；禁编造，无实证处写「照登：无实证」 |
| 旧过程稿（禁冒充） | `reports/r4*.yaml` | **18 份过程稿**（10 亲跑计数 · 首跑 2026-08-11）皆 pre-G72/G73 旧集 71 条逐案稿，**无结案效力**；30 冒烟产物刻意落 /tmp 未入仓（CLOSE 档 §四.2 在案） |
| 知识库活态 | `docker ps` · `docker exec ops-desk-api-db-1 psql -c 'select count(*) from ops_knowledge_chunks'` · `curl :6333/collections/ops_knowledge` | **PG=8648 == Qdrant=8648**（dim=1024 Cosine · status=green）· 双容器 Up 2 days (healthy)——承 PR #276 三对照 match，真跑前置已备 |
| LLM key 面 | `grep -c '^SILICONFLOW_API_KEY=.' .env` | 计数=1（存在非空 · **密钥值永不落档**）；grader/answer 走 `RAG_GRADER_*` / `RAG_LC_ANSWER_PROVIDER` env（.env 已配 · 真跑消耗 SiliconFlow 配额） |
| 配额/超时先例 | [`close_local_rag_knowledge_rebuild_20261018.md`](../close/close_local_rag_knowledge_rebuild_20261018.md) §三 | ApiEmbedder 无内部批切（API 单批上限≈500）→ **分批 --limit 75 步递增先例（25/25 步 · 248s）**；httpx InvalidURL ':1]' = shell NO_PROXY 含 [::1] 触发代理解析 bug → **env -u NO_PROXY 清洗先例**；两例均零落码解决 |
| 评测纪律 | 路线 `../ops-desk-workspace/docs/05-plan/04-agent-completion-roadmap_v1_zh.md` §P1-RAG + §3 | 自建 scenario eval 不用 BMH；zh2en 跨语言 ≥1/3 门槛显式判定；「未达门槛不改默认参数」先例（task_rag_reranker_p0 系）不变 |

### 目标

F1 真跑（前置核验 + run_eval.py 全量现集 73 条对本地知识库 8648 chunks 真跑 · 报告落 reports/）→ F2 聚合（summarize_r4.py 出 `reports/r4_final_*` 结案报告 · zh2en≥1/3 门槛如实判定 · Wilson CI · 拒答正确率）→ F3 回填（R-5 Demo 证据表实证 ≥4 条落 `reports/demo_evidence_*`）→ F4 收口（40 invoke+证据落档 · 验收回填）。全链不假绿、不凑数、门槛未达如实 NOT_MET。

---

## 范围

- **F1 · 前置核验与全量真跑（含 LLM 配额消耗 · 本 task 核心动作）**：
  - 前置核验（缺一不硬闯）：`docker ps` 双容器 healthy 落档；.env `SILICONFLOW_API_KEY` 存在非空 grep 计数落档（值不落档）；知识库计数双侧实证（PG `ops_knowledge_chunks` == Qdrant `ops_knowledge` points_count · 预期 8648，实测照登）；现集条数复核（quadrant 计数=73 四象限分布落档）。
  - 冒烟先行：`.venv/bin/python evals/golden/run_eval.py --limit 3 --out /tmp/r4_live_smoke.yaml`（产物刻意 /tmp 不入仓 · 承上游冒烟先例）；冒烟异常先按 FP-3/FP-5 处置，禁带病全量。
  - 全量真跑：`.venv/bin/python evals/golden/run_eval.py --out reports/r4_live_<UTCts>.yaml`（现集 73 条 · 默认 arm 口径与生产一致 · rerank 开关按 .env 现态如实记录报告头）；**建议分批降级预案**（超时/限流即 `--limit` 分批 + `--resume` 续跑 · 承 248s 分批先例）；环境代理异常先 `env -u NO_PROXY` 清洗复跑（承 [::1] 先例）。
  - 真跑命令全文 + 报告头（embedder/grader/语料 N/arm）+ 耗时/调用量实测落档（配额消耗诚实照登）。
- **F2 · 聚合成结案报告（机断+实证）**：
  - `.venv/bin/python evals/golden/summarize_r4.py --report reports/r4_live_<UTCts>.yaml --out-yaml reports/r4_final_<run_slug>.yaml --out-md reports/r4_final_<run_slug>.md`。
  - 按 `reports/r4_final_TEMPLATE.md` 核七节齐全：语料 N 显式（=实测 chunks 数）· 逐象限指标 · zh2en≥1/3 门槛判定（**如实 MET/NOT_MET/NO_DATA · 禁粉饰**）· Wilson 95% CI + confidence · 拒答正确率（误答/疑似误拒清单）· 观测口径注记（FP-8 照登）· 契约漂移节 · 「结论与签字」位留维护者。
  - 机断旁证：`pytest tests/test_golden_eval_r4_summary.py -q` 12 passed + `pytest tests/test_golden_eval_runner.py -q` 13 passed 复跑零新增红（管线零 diff 活证）。
- **F3 · R-5 Demo 证据表回填（实证）**：
  - 按 `evals/golden/demo_evidence_TEMPLATE.md` 填实证 ≥4 条落 `reports/demo_evidence_<UTCts>.md`：四象限每象限 ≥1 条 · **含 ≥1 条负样本拒答演示**（拒答文案与契约 4c 逐字核对）· 每条七段齐全 · 复现命令可执行 · 与 `reports/r4_final_<run_slug>.yaml` 中 case id 交叉引用。
  - 证据来自本 task 真跑（run_eval.py 或 chat SSE 实际调用）· 禁编造 · 无实证处写「照登：无实证」。
- **F4 · 留档收口**：
  - 40 invoke + 证据附件（命令全文/原始输出/报告索引）落 `docs/harness/invokes/by-task/rag-golden-eval-live-run/`。
  - 本档验收勾选 + 自检结论 + 修订记录回填；产物提交与否由 00/维护者事后裁定（承重建 task 先例）。

## 非范围

- **生产环境任何访问**（HG-PROD-READONLY-ACCESS 仍 pending · 不消解 · 报告 disclaimer 钉死本地/compose 口径不外推）。
- **评测管线/脚本功能改码**：`evals/golden/run_eval.py` · `evals/golden/summarize_r4.py` · `evals/golden/queries_v1.yaml` · `evals/golden/hygiene_denylist.yaml` · 两模板（r4_final_TEMPLATE.md / demo_evidence_TEMPLATE.md）**零 diff 硬约束**；实证须改码即 STOP 另立 task（FP-6 · 补 30 棒 + HG-GRAPH-MODULES 图谱闸评估）。
- **知识库重建/补灌**（已完成 8648 · PR #276；重建面非本 task）· `app/** · scripts/** · alembic/** · docker-compose.yml` 零 diff。
- **调参**（rerank 地板/权重/HNSW/模型切换）：报告只如实记录指标，「未达门槛不改默认」先例（task_rag_reranker_p0 系）不变；调参诉求另立 task。
- **契约改动**：`../ops-desk-workspace/docs/contracts/rag-knowledge-contract-v1.md` 零 diff；漂移只记录上抛（FP-8）。
- 金标集扩条/改条目（确需勘误经 20/维护者裁定后另记）· BMH 接入 · LLM-as-judge 上云 · Langfuse Dataset/CI 新 workflow · 新写测试。

---

## 失败路径

| 触发条件 | 系统行为 | 可重试 | 用户可见 |
|----------|----------|--------|----------|
| FP-1 闸 pending 即 40 真跑 | GATE_VERIFY **拒开工**（真值在本档人工闸表 · 本 task 含 LLM 配额消耗，闸未签禁真跑） | 是 | — |
| FP-2 不假绿硬约束（真跑中途失败/中断） | 如实记部分完成：**已完成条数 + 失败条目 + 错误全文照登，不凑数不冒充全量**；残缺报告喂 summarize_r4.py 会 SystemExit 非零退出（既有 FP-2 语义）——不得绕过；`--resume` 续跑补齐后再聚合 | 是（--resume） | 40 invoke + 报告头 |
| FP-3 配额/超时/限流（embedding 或 grader LLM 调用失败） | 进程非零退出如实记失败计数与错误全文；降级策略：**分批 `--limit` + `--resume` 续跑**（承 ApiEmbedder 无批切 --limit 75 分批 248s 先例）；代理类异常 `env -u NO_PROXY` 清洗复跑（承 httpx [::1] InvalidURL 先例）；持续失败照登回抛维护者裁定暂停/降判，**禁假绿** | 是 | 40 invoke + 报告 |
| FP-4 门槛未达（zh2en < 1/3 或拒答正确率差） | 结案报告如实判 **NOT_MET** + 失败条目清单与归因（检索/评级/金标/语料）；**不改默认参数不改管线**（调参另 task）；不粉饰不四舍五入凑线（判定用未舍入原始比率既有语义） | 是 | 结案报告 §3/§4 |
| FP-5 LLM key 失效/缺失（SILICONFLOW_API_KEY 无效 · grader/answer 面不可用） | **阻塞登记照登**：preflight 显式失败不冒充；真跑不启动；回抛维护者更新密钥后重跑 | 是 | 40 invoke 阻塞登记 |
| FP-6 顺手落码冲动 | 执行中若判断须新落/改任何码（含 evals/ 管线与模板）→ **STOP**；退回维护者裁定另立 task 补 30 棒 + HG-GRAPH-MODULES 图谱闸评估；本 task 不边做边扩范围 | — | 报告 + 40 invoke |
| FP-7 小样本被当「已达标」引用 | 结案报告头部写死样本量与 confidence（n<50 置信有限 · 任何「已达标」表述必须同时引用 n 与 Wilson CI）；40 核验 | 否 | 报告头部 |
| FP-8 契约漂移实证 / SPEC 真值仍不可得 | 漂移：记入结案报告「契约漂移」节 + invoke 上抛维护者，本 task 零改契约零改实现；SPEC-evaluation-observation 真值文件仍不可得 → 模板第 5 节 SPEC_OBSERVATION_NOTE 注记照登（「照登：无实证 · 以路线 A-P1-3 引用口径为准」） | 是（另 task 修） | 报告 §5/§6 + 上抛记录 |
| FP-9 旧过程稿冒充结案（71≠73） | **结案数值必须源自本 task 新跑报告**（reports/r4_live_*）；reports/r4*.yaml 18 份旧过程稿（pre-G72/G73 旧集 71 条）仅作历史对照，禁充当结案数值；zh2en 分母按实际报告取数 | — | 报告 §1 源报告字段 |
| FP-10 证据不可复现 | 全链命令全文 + 原始输出附件必落档（对齐上游 e00–e11 先例）；缺附件即对应 TC 判 FAIL；**禁凭记忆转述** | 是 | 40 invoke 实录 |

---

## 验收标准

- [x] **TC-LR-1（实证 · 前置核验）**：F1 前置完成——`docker ps` 双容器 healthy 输出落档；.env `SILICONFLOW_API_KEY` 存在非空 grep 计数落档（密钥值零落档）；知识库双侧计数实证落档（PG==Qdrant · 实测值照登 · 预期 8648）；现集 73 条四象限计数（zh2en=26/zh2zh=20/en2en=16/negative=11）复核落档
- [x] **TC-LR-2（实证 · 全量真跑）**：F1 真跑完成——`run_eval.py` 全量现集 73 条报告落 `reports/r4_live_<UTCts>.yaml`；冒烟先行（/tmp 产物不入仓）+ 全量命令全文/报告头/耗时落档；中途失败如实记部分完成（FP-2/FP-3 处置记录）而非凑数；配额消耗实测照登
- [x] **TC-LR-3（机断+实证 · 结案报告）**：F2 完成——`reports/r4_final_<run_slug>.{yaml,md}` 存在且七节齐全；zh2en≥1/3 门槛判定（MET/NOT_MET/NO_DATA 如实）· zh2en 命中数/n 与拒答正确率显式可见 · Wilson 95% CI + confidence 位已填 · 观测口径注记（FP-8）照登；`pytest tests/test_golden_eval_r4_summary.py -q` 12 passed + `pytest tests/test_golden_eval_runner.py -q` 13 passed 复跑零新增红
- [x] **TC-LR-4（实证 · Demo 证据表）**：F3 完成——`reports/demo_evidence_<UTCts>.md` ≥4 条：每象限 ≥1 · 含 ≥1 负样本拒答演示（拒答文案与契约 4c 逐字「未查询到相关内容，无法针对此问题进行回答」）· 每条七段齐全 · 复现命令可执行 · 与结案报告 case id 交叉引用
- [x] **TC-LR-5（机断 · 零 diff 硬约束）**：`git status` 实证 `app/** · scripts/** · alembic/**` 零改动；`evals/golden/run_eval.py` · `summarize_r4.py` · `queries_v1.yaml` · `hygiene_denylist.yaml` · 两模板零 diff；契约文件零 diff
- [x] **TC-LR-6（机断 · 留档收口）**：40 invoke + 证据附件落 `docs/harness/invokes/by-task/rag-golden-eval-live-run/`；`npx --yes spec-wave task lint --file docs/tasks/active/task_rag_golden_eval_live_run.md` 输出含 `LINT: PASS`；本档验收勾选 + 自检结论 + 修订记录回填

## 依赖

- 母体与移交口径：[`task_rag_golden_eval_r4_r5.md`](../done/task_rag_golden_eval_r4_r5.md) + [`close_rag_golden_eval_r4_r5_20261017.md`](../close/close_rag_golden_eval_r4_r5_20261017.md)（TC-R4-5 移交 · 71≠73 警示 · 冒烟 /tmp 先例）
- 复用资产（零 diff 硬约束）：`evals/golden/queries_v1.yaml`（现集 73 条）· `evals/golden/run_eval.py` · `evals/golden/summarize_r4.py` · `evals/golden/hygiene_denylist.yaml` · `reports/r4_final_TEMPLATE.md` · `evals/golden/demo_evidence_TEMPLATE.md` · `tests/test_golden_eval_r4_summary.py`（12 测）· `tests/test_golden_eval_runner.py`（13 测）
- 前置（已备）：本地知识库 8648 chunks PG==Qdrant（[`task_local_rag_knowledge_rebuild.md`](../done/task_local_rag_knowledge_rebuild.md) · PR #276）· `SILICONFLOW_API_KEY` 在 .env
- 路线真值：`../ops-desk-workspace/docs/05-plan/04-agent-completion-roadmap_v1_zh.md` §P1-RAG（R-4/R-5）· §3 评测纪律（自建不用 BMH）
- 契约页（只读核对 · 不改）：`../ops-desk-workspace/docs/contracts/rag-knowledge-contract-v1.md`（上游 TC-R4-6 核对零漂移在案）
- 降级先例：[`close_local_rag_knowledge_rebuild_20261018.md`](../close/close_local_rag_knowledge_rebuild_20261018.md) §三（分批 248s · NO_PROXY 清洗）
- 先例参照：[`task_memory_golden_eval.md`](../done/task_memory_golden_eval.md)（显式失败不冒充 · 报告写死门槛 · 真跑隔离）· [`task_rag_reranker_p0.md`](../done/task_rag_reranker_p0.md)（未达门槛不改默认）

## 给执行帽的必读列表

1. 本 task 全文（移交口径 · 实证锚点表 · FP-2 不假绿 · FP-6 零落码 · FP-9 旧稿禁冒充硬项）。
2. [`close_rag_golden_eval_r4_r5_20261017.md`](../close/close_rag_golden_eval_r4_r5_20261017.md) §四（71≠73 · 冒烟 /tmp · SPEC 无实证 · HG-EVAL-LIVE-RUN 真跑流程指引）。
3. `evals/golden/run_eval.py` 与 `evals/golden/summarize_r4.py` docstring（禁信转述）。
4. `reports/r4_final_TEMPLATE.md` + `evals/golden/demo_evidence_TEMPLATE.md`（七节/七段与回填纪律）。
5. [`close_local_rag_knowledge_rebuild_20261018.md`](../close/close_local_rag_knowledge_rebuild_20261018.md) §三（分批/代理降级先例）。
6. 路线 §P1-RAG + §3（`../ops-desk-workspace/docs/05-plan/04-agent-completion-roadmap_v1_zh.md`）。
7. `docs/harness/prompts/FRAGMENT_30_gate_verify_v1_zh.md`（闸扫描纪律 · 本 task 40 同源适用）。

## 思考轮控制

| 轮 | 结论 | early_stop | reason（early_stop） | residual_risks |
|---|------|------------|----------------------|----------------|
| R0 | 框定：本 task 是「真跑回填」单增量非「从零」缺口；评测资产（脚本+测试+双模板）已随 PR #262 闭环，唯 TC-R4-5 移交 | false | — | 移交口径依赖 CLOSE 档准确性 |
| R1 | 证据：现集 73 条亲跑计数（zh2en=26/zh2zh=20/en2en=16/negative=11）· 知识库 PG==Qdrant==8648 活态实证 · SILICONFLOW_API_KEY 在 .env · 18 份旧过程稿无结案效力 · 降级先例两例在档 | false | — | LLM 配额余量未实测 |
| R2 | 方案：零落码——run_eval.py 全量真跑 + summarize_r4.py 聚合 + 模板回填；冒烟先行 /tmp 不入仓；分批+--resume 降级预案 | false | — | 真跑耗时与配额消耗量级待实测 |
| R3 | 反例：防重复立项（资产零重写）· 旧过程稿禁冒充（71≠73）· 门槛未达不改默认 · 顺手落码即 STOP 另立 | false | — | 真跑暴露新缺陷须另立 task 处置 |
| R4 | 验收：TC-LR-1..6 实证+机断可对命令输出断言；真跑不占 CI 绿；机断旁证复跑 12+13 测 | false | — | 闸未签 |
| R5 | 收口：草稿交 20；四闸 pending 待维护者签/00 代录；禁 40 | true | 增量边界、资产清单与先例已钉死，再轮无新锚点 | 闸未签 · 配额窗口 |

**actual_last_round**：R5（early_stop）

### R0 · 问题框定

上游 task_rag_golden_eval_r4_r5 CLOSE 档 §四.1 钉死：唯一未闭环 = TC-R4-5 结案真跑（HG-EVAL-LIVE-RUN pending 移交）。本 task 只做这一增量，禁重复立项资产面。

### R1 · 证据收集

10 亲跑 2026-10-19：quadrant 计数 73 条四象限分布与上游记录逐字一致；PG 8648 == Qdrant 8648 双容器 healthy；SILICONFLOW_API_KEY 存在非空；reports/r4*.yaml 18 份过程稿（71 条旧集）无结案效力；run_eval/summarize/双模板均在库且 docstring 用法亲读。

### R2 · 方案生成

零落码：全链复用既有管线（run_eval.py 全量 → summarize_r4.py 聚合 → 模板回填），无新码无新测试；冒烟先行产物 /tmp；配额/超时降级走分批 --limit + --resume 先例。

### R3 · 反例与边界

FP-9 旧稿禁冒充（71≠73）；FP-4 门槛未达如实 NOT_MET 不改默认；FP-6 顺手落码即 STOP；FP-8 契约漂移只上抛；FP-2 不假绿（部分完成如实记）。

### R4 · 验收/可测性

TC-LR-1..6：实证项（前置/真跑/报告/证据表）均可对命令输出与文件存在性断言；机断项（零 diff git status 实证 · 12+13 测复跑 · lint PASS）可机械核验；真跑不占 CI 绿。

### R5 · 收口

草稿交 20 R1（按授权取舍）；四闸全 pending 待维护者签/00 代录；闸未签禁 40 真跑。

### 自检结论（执行者）

40 实证棒 2026-10-19 回填（命令与 exit 码实证表 · 全链附件见 invoke_20261019_40_live_run.md + evidence_r4_live_run_log_20261019T032150Z.txt）：

| 项 | 命令（节略） | 结果 |
|---|---|---|
| 闸核验 | `npx spec-wave verify --target . --task docs/tasks/active/task_rag_golden_eval_live_run.md` | VERIFY: PASS（四闸 approved） |
| 前置核验 | docker ps / grep -c SILICONFLOW_API_KEY / psql count / curl :6333 / quadrant uniq -c | 双容器 healthy · key 计数=1 · PG=8648==Qdrant=8648 · 73 条（26/20/16/11） |
| 冒烟 | `run_eval.py --limit 3 --out /tmp/r4_live_smoke.yaml`（env -u NO_PROXY -u no_proxy） | pass=2/3 · stability=1.0（初两轮代理炸已按先例处置） |
| 全量真跑 | `run_eval.py --out reports/r4_live_20261019T032150Z.yaml`（7/73 中断 EXIT=1）→ 全洗代理 `--resume` 续跑 | 73/73 · partial=false · pass=54/73 · zh2en=19/26 · zh2zh=18/20 · en2en=15/16 · neg=10/11 · stability=1.0 · ≈56.6min（exit=1=verdict fail 语义 · run_eval.py:812） |
| 结案聚合 | `summarize_r4.py --report … --out-yaml … --out-md …` | EXIT=0 · zh2en gate=**MET**（19/26=73.08% vs ≥1/3 · Wilson CI=[0.54,0.86]）· 拒答 10/11（CI=[0.62,0.98]）· 误答 G63 · 疑似误拒 9 条 |
| 机断旁证 | `pytest tests/test_golden_eval_r4_summary.py -q` / `tests/test_golden_eval_runner.py -q` | 12 passed / 13 passed · 零新增红 |
| Demo 证据 | reports/demo_evidence_20261019T033800Z.md | 4 条四象限齐 · G62 拒答演示（契约 4c 三面逐字一致）· case id 交叉引用 |
| 零 diff | `git diff --stat HEAD -- app/ scripts/ alembic/ …（硬约束面）` | 空输出零 diff · 契约文件零 diff（workspace 仓干净） |
| lint | `npx --yes spec-wave task lint --file docs/tasks/active/task_rag_golden_eval_live_run.md` | LINT: PASS |

验收摘要：TC-LR-1..6 全过；zh2en 判定 **MET**；整体判定建议「有条件通过」（19/73 verdict fail 待归因复核另 task）· 签字位留维护者。
已知未测项：① 逐案 LLM 调用数/配额无本地计量（照登：无实证）；② run_eval 路径不生成自然语言答案正文（拒答话术实证链=常量三面逐字对照）；③ demo 模板 `--only` 复现参数现版 runner 不支持（模板 nit 已上抛 · 零 diff 未改）。

---

## 修订记录

| 日期 | 说明 |
|------|------|
| 2026-10-19 | 10-task 落稿（R-4 结案真跑 + R-5 Demo 证据表回填 · 零落码建议 40 单棒 · 四闸 pending 待维护者签/00 代录 · 未 commit）；10 亲跑实证锚点：73 条四象限计数 · PG==Qdrant==8648 · SILICONFLOW_API_KEY 在 .env · 18 份旧过程稿 |
| 2026-10-19 | 维护者「全做」授权 + 授权链（m00238/m01101）00 代录四闸 approved；20 R1 书面审通过（零阻塞 nit×2 照登） |
| 2026-10-19 | 40 实证完成：73/73 全量真跑（FP-3 两连处置：NO_PROXY 双写双洗 + 全洗代理直连 --resume 续跑 · FP-2 中断如实记）→ 结案报告 zh2en **MET**（19/26=73.08% · Wilson CI=[0.54,0.86]）· 拒答 10/11 · 误答 G63 + 疑似误拒 9 条照登 → Demo 证据表 4 条（G62 拒答演示契约 4c 逐字）→ TC-LR-1..6 勾选 + 自检结论回填；产物：reports/r4_live_20261019T032150Z.yaml · r4_final_live_20261019T032150Z.{yaml,md} · demo_evidence_20261019T033800Z.md · invoke_20261019_40_live_run.md + 证据附件 |
| 2026-10-19 | 50 CLOSE（goal-eb568703 承授权链合并）：PR #280 squash 4ab5f3a 已并 · 归档 done/ · 状态行 CLOSED · README 登记 · 遗留=结案报告 §7 签字位 + G63 误答/9 疑似误拒归因复核另 task 候选 |
