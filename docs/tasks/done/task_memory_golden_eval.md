# Task：记忆抽取金样评测 + 融合权重调参（M1 · P1 生产开启前置）

> **状态**：`done`（2026-09-21 闭环：三闸 approved · 30 E1–E5 交付（零生产语义改动）· 40 独立核验 PASS（10/10 · 偏差#1 裁定接受）· 代码在 `task/memory-golden-eval` 分支 · **PR 待开** · 真跑裁决=维护者复制区）  
> **类型**：eval / 记忆轨 · **不交付新产品行为**  
> **上游 SPEC**：`docs/spec/memory-golden-eval/SPEC-memory-golden-eval_v1.md`（**signed** · HG-SPEC-SIGNOFF=approved 2026-09-21）  
> **分支**：`task/memory-golden-eval`（base：`master` · 已含 P1 合并 `5deb430`）  
> **00 注**：2026-09-21 · 维护者令「先按照建议排序来进行M1，其他方案也留下占位spec」（P0/P1 同模式授权延续：00 代录闸 · 30/40 子 Agent）· 9 个占位 SPEC 已随本分支落盘

---

## Harness 元信息

| 字段 | 值 |
|------|-----|
| **task_slug** | `memory-golden-eval` |
| **git_branch** | `task/memory-golden-eval` |
| **implement_repo** | `ops-desk-api` |
| **test_strategy** | `required` |
| **test_strategy_note** | CI 全 fake 确定性（不连外网）：金样 schema 校验、runner 指标三态、扫参 27 组完整性；真跑=维护者复制区（SPEC §8） |
| **code_quality_bar** | `L2_backend` |
| **graph_change_layer** | `none` |
| **graph_delta** | `n/a` |
| **graph_delta_note** | eval 资产（evals/memory/ + tests/ + reports/）· 无新模块/无对外契约改动 · HG-GRAPH-MODULES 以 `none` 代录 |
| **wiki_delta** | `n/a` |
| **wiki_delta_note** | 契约真值在 SPEC `memory-golden-eval` |
| **review_hat** | `20` |
| **required_invoke_hats** | `10,20,30,40` |
| **invoke_retention_profile** | `default` |
| **experience_capture** | `recommended` |
| **kpi_aggregator** | `CLOSE` |
| **orchestration** | 10 落稿 → 20 R1 → 00 代录闸 → 30 → 40 → CLOSE → 维护者真跑裁决 |
| **freeze_id** | 无 |

### 人工闸

| human_gate_id | status | blocks_hats | 说明 |
|---------------|--------|-------------|------|
| HG-TASK-DRAFT | **approved** | 20-R1, 30 | 2026-09-21 维护者令 M1 优先 · SPEC 已签 |
| HG-AUDIT-R1 | **approved** | **30** | 2026-09-21 维护者令 M1（P0/P1 同模式授权延续）· 00 代录（20 R1 终轮零阻塞已落盘） |
| HG-GRAPH-MODULES | **approved** | **30** | 2026-09-21 00 代录 · `graph_change_layer=none`（eval 资产 · 无模块改动） |

---

## 背景与目标

P1 双开关默认关：机制正确性已被 fake 红线证明，**效果未知**（真实抽取精度 / 复述召回 / 权重初值）。本 task 交付金样集 + 离线 runner + 扫参 + CI 测试——**只交证据，不改生产语义**；真跑与裁决是维护者动作（SPEC §2 D5 / §8）。

铁律：评测轨不碰闸/状态机/融合代码逻辑；CI 一律 fake；金样含负样本。

---

## 现状锚点（只读 · 30 必读 · 10 已扫）

| 主题 | 路径 · 锚点 | 现状 |
|------|-------------|------|
| 既有金样 runner | `evals/golden/run_eval.py` + `queries_v1.yaml`（RAG 轨 · YAML 进出先例） | 结构可仿 · **不复用**（SPEC R2-S2：指标语义不匹配） |
| 红线/eval 测试 | `tests/eval/` 6 文件 · `tests/test_golden_eval_runner.py` | 评测测试组织先例 |
| 记忆机制（被测对象） | `app/ops/memory/{gate,service,extract}.py` | **零改动** · fake 注入点：embedder 参数 / provider 桩 |
| 报告先例 | `reports/`（qdrant_bench / r4 系列 YAML） | 报告落 reports/ · 头部写门槛 |
| 清场机制 | `revoke_by_source`（P0）· 独立 tenant `memory-eval` | 真跑防污染 |

---

## 钉死契约（自 SPEC 锁死；30 不得静默改义）

| 项 | 钉死 |
|----|------|
| **零生产语义改动** | `app/ops/memory/**` · `app/ops/lg_rag/**` · `app/db/**` **零 diff**（除必要的测试可注入性调整——须 20/40 审） |
| **金样** | `evals/memory/golden_v1.yaml` ≥40 条四类：应记 ≥12 / 不应记（负样本）≥12 / 冲突 supersede ≥8 / 复述召回 ≥10 |
| **runner** | `evals/memory/run_eval.py` · `--backend fake`（默认 · CI 确定性）/ `--backend live`（真实 embedder+LLM）；live 缺 key/外网 → 非零退出**显式报错**，不静默冒充 |
| **指标** | 抽取 precision / 噪声写入率 / 漏记率 · 复述 top1/top3 命中 · supersede 正确率；报告落 `reports/memory_golden_eval_*.yaml` **头部写死门槛与达成情况** |
| **扫参** | `half_life {7,30,90}` × `sim_floor {0.3,0.5,0.7}` × `source_weight_extract {0.6,0.8,1.0}` = 27 组；**只出建议不改常量** |
| **真跑隔离** | tenant=`memory-eval` · 跑后 `revoke_by_source` 自动清场 |
| **门槛（D5）** | precision ≥0.9 · 噪声写入率 ≤0.1 · 复述 top3 ≥0.8 · supersede=1.0 |
| **CI** | fake only · 不连外网 · 无新第三方依赖 |

---

## 范围（同 task 竖切）

- [x] **E1 · 金样**：`evals/memory/golden_v1.yaml` ≥40 条四类 + schema 文档（README 或 runner docstring）
- [x] **E2 · runner**：`evals/memory/run_eval.py` 双模式 + 指标 + 报告（头部门槛）
- [x] **E3 · 扫参**：27 组网格 + 推荐组合与理由结构（fake 模式产物即可 · live 产物维护者跑）
- [x] **E4 · CI 测试**：`tests/test_memory_golden_eval.py`（schema 校验 / 指标三态（全过·全错·混合）/ 扫参完整性 / live 缺 key 显式失败）
- [x] **E5 · 文档**：`evals/memory/README.md`（金样标注指南 · 双模式用法 · 复制区指针）

### 非范围

- 改闸/状态机/融合/抽取代码；改生产默认开关；权重常量改值（另 task 按报告裁决）
- 真跑进 CI；画像/回填/真摘要（各有占位 SPEC）；新对外端点 / SSE / 新依赖
- span 真实 tracing 验证（memory-embedding-backfill 占位 SPEC 的 M6 项）

---

## failure_paths

| 触发条件 | 系统行为 | 可重试 | 用户可见 |
|----------|----------|--------|----------|
| `HG-AUDIT-R1` pending 即 30 | **拒开工** | 是 | 是 |
| live 缺 key / 外网不通 | 非零退出 + 显式错误（不静默 fake 冒充） | 是 | 是（runner 用户） |
| 金样 YAML 非法 | CI schema 校验 fail（早失败） | 是（修 YAML） | 否 |
| 真跑中途 LLM 失败 | 该用例记 error 入报告 · 不中断全量 | 是 | 是（报告） |
| 真跑污染测试库 | tenant=`memory-eval` 隔离 + 跑后自动清场 | 是 | 否 |
| 扫参全部不达标 | 报告如实 · 不推荐组合 | — | 是（报告） |
| 报告被当"已达标"引用 | 头部写死门槛与达成情况 · 40 核验 | — | 否 |
| 30 顺手改 app/ops/memory 语义 | 审查拒收（零 diff 契约） | 是 | 否 |

---

## 验收标准

- [x] 人工闸：`HG-AUDIT-R1` approved 后方可勾选下列码项
- [x] E1：金样 ≥40 条四类齐（schema 校验单测绿 · 数量下限断言）
- [x] E2：fake 模式端到端确定性绿（指标三态断言）；live 缺 key 非零显式失败测试绿
- [x] E3：27 组扫参产物完整性断言；报告含推荐组合/理由/门槛达成结构
- [x] E4：`tests/test_memory_golden_eval.py` 全绿
- [x] E5：README 齐（标注指南 · 双模式 · 复制区）
- [x] `app/ops/memory/**` · `app/ops/lg_rag/**` · `app/db/**` 零 diff
- [x] **旧测 grep 影响面**（行为变更类 · 20 checklist · 2026-09-21 代跑）：`tests/test_golden_eval_runner.py`（5 命中 · RAG 轨 runner 测试 · 本波不复用不改动）；`tests/eval/` 6 文件（评测基设 · 只仿不改）；memory 系 3+2 文件（被测对象零 diff）——30 须保持以上全绿
- [x] `ruff` 触及路径绿；`pytest` 本波 + 既有 memory + eval 回归绿
- [x] `npx spec-wave task lint --file docs/tasks/active/task_memory_golden_eval.md` PASS

### 维护者真跑裁决（不占 30 验收 · SPEC §2 D5）

- [ ] `reports/memory_golden_eval_*.yaml` 对照门槛 → 裁决开/不开 · 先开哪个

---

## 依赖

| 依赖 | 说明 |
|------|------|
| SPEC | `docs/spec/memory-golden-eval/SPEC-memory-golden-eval_v1.md`（signed） |
| P1（已合并） | `docs/tasks/done/task_memory_facts_p1.md` · PR #145（`5deb430`） |
| 评测先例 | `evals/golden/run_eval.py` · `tests/eval/` · `docs/tasks/done/task_rag_reranker_p0` 系（"未达门槛不改默认"先例） |
| 编码规范 | `docs/standards/CODING_BACKEND_L2_v1_zh.md` |

---

## 给执行帽的必读列表

1. `AGENTS.md`
2. 本 task（钉死契约 · 零生产语义改动 · 非范围）
3. SPEC `docs/spec/memory-golden-eval/SPEC-memory-golden-eval_v1.md`
4. `docs/standards/CODING_BACKEND_L2_v1_zh.md`
5. 代码：`evals/golden/run_eval.py` · `app/ops/memory/{gate,service,extract}.py`（只读）· `tests/eval/`
6. `docs/harness/prompts/FRAGMENT_30_gate_verify_v1_zh.md`

---

## 思考轮控制

| 轮 | 结论 | early_stop | reason（early_stop） | residual_risks |
|----|------|------------|----------------------|----------------|
| R0 | M1 = 交证据不改语义；SPEC 已签 | no | — | none |
| R1 | 30 硬阻塞于 HG-AUDIT-R1（00 代录） | no | — | 无 |
| R2 | E1–E5 同竖切；graph=none | no | — | 无 |
| R3 | live 显式失败不冒充；tenant 隔离+清场；报告写死门槛 | no | — | 无 |
| R4 | CI 全 fake；门槛对齐"未达不改默认"先例 | no | — | 金样覆盖度有限（继承 SPEC residual ①） |
| R5 | 可交 20 | no | — | 门槛经验值待首轮校准（继承 SPEC residual ②） |

**actual_last_round**：R5 · **early_stop**：no · **residual_risks**：见 R4/R5

### R0 · 问题框定

机制已证、效果未知；开开关的裁决需要证据，证据需要金样+runner，本 task 只交这些。

### R1 · 开工闸

单闸（AUDIT-R1）；GRAPH 以 none 代录（eval 资产无模块改动）。

### R2 · 竖切

金样/runner/扫参/CI 测试同 task：分开会出现"有 runner 没金样"的空转交付；图谱 none。

### R3 · 失败语义

评测工具最大的恶是"假绿"：live 失败必须显式、报告必须写死门槛、真跑必须隔离清场——三条都钉死。

### R4 · 可测性

CI 确定性靠 fake 双桩（embedder/provider）；指标正确性用三态（全过/全错/混合）断言而非抽查。

### R5 · 交接就绪

可交 20；30 验收不含真跑（维护者复制区），与 reranker-p0 先例一致。

---

### 自检结论（执行者）

> **hat 40** · 2026-09-21 · **40 PASS**（独立核验 · 只读+实跑 · 零退回项）

| 命令 | 退出码 | 摘要 |
|------|--------|------|
| git diff --stat -- app/ evals/golden/ tests/ | 0 | 空输出 · 零生产语义改动硬项达成 |
| .venv/bin/ruff check evals/memory tests/test_memory_golden_eval.py | 0 | All checks passed |
| .venv/bin/pytest tests/test_memory_golden_eval.py -q --tb=short | 0 | 10 passed（schema/三态/确定性/扫参/live 缺 key） |
| .venv/bin/pytest 既有 memory×5 + golden_runner 回归 | 0 | 89 passed · 旧测影响面全绿 |
| .venv/bin/pytest tests -q --tb=short | 1 | 1098 passed / 1 skipped / 3 failed（既有环境失败 capability proxy + chat_ws×2 · 无新增） |
| .venv/bin/python evals/memory/run_eval.py --backend fake --out /tmp/mge_40_fake.yaml | 0 | 50 用例全过 · 报告头部四门槛 MET + 防假绿注记 |
| env SILICONFLOW_API_KEY= ... --backend live --limit 1 | 2 | 显式失败 stderr · 不静默冒充（契约达成） |
| .venv/bin/python evals/memory/run_eval.py --backend fake --sweep | 0 | 27 组齐 · recommended 含 reason · 「改值另 task」注记 |
| npx spec-wave task lint --file docs/tasks/active/task_memory_golden_eval.md | 0 | LINT: PASS |

**验收摘要**：10 项全 ✅。金样 50 条四类（14/14/10/12 超下限）· 负样本真双形态（闸可拒 7 + prompt 级 7）· 复述 query 真改写；fake 两跑逐字节一致（亲跑复验）；罐头抽取真过 `should_write` 闸不绕过；live preflight 三段显式失败退出码 2；偏差#1（清场含 tenant 级硬删）裁定**接受**——WHERE tenant_id='memory-eval' 严格限专用租户、仅 live 路径、README 已声明、实测零残留零误伤；live 烟跑两真实信号（**key 漂移** project.deploy_target vs deploy.target → supersede 失效 · **复述 top1 压力**）30 均如实记录未藏丑。

**已知未测项**：① live 全量 50 条真跑（维护者复制区 · SPEC §8）；② 扫参 recommended:null 分支无强制触发单测（代码路径亲读确认在）；③ 3 条既有环境失败根因未查（与本波无关）。

**结论**：**40 PASS** · 可进 PR 流程 · 真跑裁决=维护者（SPEC §2 D5）

---

## 修订

| 日期 | 说明 |
|------|------|
| 2026-09-21 | 10-task 落稿 · R0–R5 全轮 · HG-AUDIT-R1 pending → 30 拒开工 |
| 2026-09-21 | 20 R1 终轮零阻塞签收 · 00 代录 AUDIT-R1 · 30 开工 |
| 2026-09-21 | 30 交付 E1–E5（零生产 diff · live 烟跑暴露 key 漂移+top1 压力两真实信号）→ 40 PASS（10/10 · 偏差#1 接受）→ 00 回写 · 归档 done · CLOSE |
