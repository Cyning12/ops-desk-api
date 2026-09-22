# SPEC：记忆抽取金样评测 + 融合权重调参（M1 · P1 生产开启前置）（v1）

> **状态**：`signed`（HG-SPEC-SIGNOFF=**approved** · 2026-09-21 维护者令「先按照建议排序来进行M1」）  
> **track**：`eval`（评测轨 · 不交付新产品行为）  
> **上游**：`docs/spec/memory-facts-p1/SPEC-memory-facts-p1_v1.md`（已实施 · PR #145 merged `5deb430`）residual ①② · 40 已知未测项（真实 embedder/LLM 未端到端）  
> **下游**：人签 SPEC → 00 出 task → 20-task-audit → 30 实现 → 维护者真跑裁决  
> **Open Folder（实现）**：`ops-desk-api/`

---

## Harness 元信息

| 字段 | 值 |
|---|---|
| **spec_slug** | `memory-golden-eval` |
| **invoke_slug** | `memory-golden-eval`（task 阶段） |
| **test_strategy** | `required` |
| **test_strategy_note** | CI：fake embedder/fake LLM 确定性单测（金样 schema 校验、runner 指标计算、扫参网格正确性 · 不连外网）；真跑：维护者复制区（真实 SiliconFlow embedder + 真实 LLM 抽取），产出 reports/memory_golden_eval_*.yaml |
| **Open Folder（实现）** | `ops-desk-api/` |
| **默认分支** | `task/memory-golden-eval`（base：`master`） |
| **graph_change_layer（建议）** | `none`（eval 资产 · 无新模块/无对外契约改动；若需 G-L2 indexes 由 task 裁定） |

### 人工闸（SPEC 阶段）

| human_gate_id | status | 说明 |
|---|---|---|
| **HG-SPEC-SIGNOFF** | approved（2026-09-21 维护者「先按照建议排序来进行M1」） | 签收后方可 00 出 task / 30 改码 |

---

## 1. 背景与目标

### 现状

P1 已合并：向量召回（`MEMORY_FACTS_VECTOR_RECALL_ENABLED=false`）与 LLM 离线抽取（`MEMORY_FACTS_EXTRACT_ENABLED=false`）双开关**默认关**。P1 红线全部由 fake embedder / fake LLM 确定性化验证——**机制正确性已证，效果未知**：

| 未知项 | 风险 |
|---|---|
| 真实 LLM 抽取精度 | 抽错/抽噪 → 记忆污染（机制上可 revoke，但量大即不可用） |
| 真实 embedder 复述召回 | 向量通路对中文复述的真实命中率未知 |
| 融合权重初值（sim_floor=0.5 · half_life=30d · source_weight=0.8） | 拍脑袋值，可能压掉该召回的或抬起噪声 |

**一句话目标**：交**金样集 + 离线评测 runner + 首轮真实评测报告 + 权重推荐值**，给出"两个开关能不能开、先开哪个"的裁决依据。**达标才另 task 改默认；不达标只交报告**（对齐 rag-reranker-p0「未达门槛不改生产默认」先例）。

### 设计纪律

1. **评测轨不碰生产语义**——本波不改闸/状态机/融合代码逻辑；权重是常量，调值建议写进报告，改值另 task 按报告裁决。
2. **CI 一律 fake 确定性**（仓内纪律：CI 不连真外网）；真跑走维护者复制区。
3. **金样含负样本**（对齐仓内金样纪律：只做正向会得到假通过）。

---

## 2. 范围

### D1 · 金样集 `evals/memory/golden_v1.yaml`（必做）

≥40 用例，四类（schema 随 runner 定义 · README 写明）：

| 类别 | 数量 | 内容 | 判定 |
|---|---|---|---|
| **应记** | ≥12 | 对话片段含稳定事实（负责的项目/常用环境/明确声明的约束） | 抽取应产出且过闸 |
| **不应记（负样本）** | ≥12 | 一次性信息/易失状态/通用知识/他人事实 | 抽取应拒（闸拒或未产出）· **零写入** |
| **冲突 supersede** | ≥8 | 同一 key 先 A 后 B | 召回只见 B；A 表内 superseded |
| **复述召回** | ≥10 | 先写入事实，用改写/换说法 query 检索 | 向量通路 top-1 或 top-3 命中 |

### D2 · 离线 runner `evals/memory/run_eval.py`（必做）

- 双模式：`--backend fake`（CI 确定性 · 默认）/ `--backend live`（真实 embedder + 真实 LLM · 维护者本地）
- 指标输出 `reports/memory_golden_eval_YYYYMMDD.yaml`：
  - 抽取：**precision**（写入的事实中标注为"应记"的比例）、**噪声写入率**（负样本被写入比例）、**漏记率**（应记未记）
  - 召回：复述 **top1 / top3 命中率**
  - 冲突：supersede 正确率
- 复用既有 runner 结构（`evals/golden/run_eval.py` 先例：YAML 进出 · 可复现 · 报告落 reports/）

### D3 · 权重扫参（必做）

网格：`half_life ∈ {7, 30, 90}` × `sim_floor ∈ {0.3, 0.5, 0.7}` × `source_weight_extract ∈ {0.6,0.8,1.0}`（27 组）→ 每组复述召回+时效性用例得分 → 报告推荐组合与理由。**只出建议，不改代码常量**（改值另 task 按报告裁决）。

### D4 · CI 测试（必做）

`tests/test_memory_golden_eval.py`：金样 YAML schema 校验（类别/必填字段/用例数下限）；fake 模式 runner 端到端（指标计算正确性 · 全过/全错/混合三态）；扫参网格 27 组产物完整性。**不连外网**。

### D5 · 裁决门槛（真跑后由维护者裁决）

| 指标 | 门槛（草案 · 签收锁死） |
|---|---|
| 抽取 precision | **≥ 0.9**（错记率 ≤ 10%） |
| 噪声写入率（负样本） | **≤ 0.1** |
| 复述召回 top3 | **≥ 0.8** |
| supersede 正确率 | **= 1.0**（机制已证 · 真跑防回归） |

**全达标** → 建议后续 task：先开 `MEMORY_FACTS_VECTOR_RECALL_ENABLED`（低风险 · 失败有确定性兜底），抽取开关视 precision 余量再议。**任一不达标** → 只交报告 + 改进建议（prompt 迭代/判据加严另 task），**不改任何默认值**。

---

## 3. 非范围

- ❌ 改闸判据/状态机/融合代码语义/生产默认开关（调值与开默认均另 task 按报告裁决）
- ❌ 真实 embedder/LLM 进 CI（fake only · 仓内纪律）
- ❌ 画像记忆 / embedding 回填 / 真摘要（各有占位 SPEC）
- ❌ 新对外端点 / SSE 改动 / 新第三方依赖
- ❌ span 真实 tracing 后端验证（并入 memory-embedding-backfill 占位 SPEC 的 M6 小项）

---

## 4. 方案对比（R2）

| 方案 | 做法 | 收益 | 代价 | 裁决 |
|---|---|---|---|---|
| **S1 · 专用金样+双模式 runner（本 SPEC）** | evals/memory/ 新资产 | 与 RAG 金样隔离 · 指标按记忆语义定制 | 新 runner 维护成本 | **推荐** |
| S2 · 复用 evals/golden/run_eval.py 直接扩 | RAG runner 加用例 | 零新代码 | RAG 指标（recall@5/best_relevance）不匹配记忆语义（precision/噪声率/supersede） | 弃 |
| S3 · 直接生产开小流量观察 | 线上试错 | "真实" | 污染真实用户记忆 · 错了只能 revoke 全撤 | 弃（违反"可逆性先行"） |
| S4 · LLM-as-judge 在线评分 | 热路径加判分 | 看似省事 | 延迟翻倍+新不确定性（手册 §1.8 纪律） | 弃 |

---

## 5. 边界 / 失败路径 / 安全

| 触发 | 行为 | 可重试 |
|---|---|---|
| live 模式缺 API key / 外网不通 | 明确报错退出（非零）· 不静默降级 fake 冒充真跑 | Y |
| 金样 YAML 非法 | CI schema 校验 fail（早失败） | — |
| 真跑中途 LLM 失败 | 该用例记 error 计入报告 · 不中断全量 | Y |
| 真跑写入测试库污染 | runner 用独立 tenant（`memory-eval`）· 跑后自动 `revoke_by_source` 清场 | Y |
| 扫参结果全部不达标 | 报告如实给结论 · 不推荐任何组合 | — |
| 报告被当成"已达标"引用 | 报告头部写死裁决门槛与达成情况 · 40 核验 | — |

---

## 6. 验收标准

### 功能（CI 可验）

- [ ] `evals/memory/golden_v1.yaml` ≥40 用例四类齐（schema 校验单测）
- [ ] `run_eval.py --backend fake` 端到端确定性绿（指标三态断言）
- [ ] 扫参 27 组产物完整 · 报告含推荐组合与理由结构
- [ ] ruff + pytest 绿（本波 + 既有 memory 测试回归）
- [ ] `npx spec-wave task lint` PASS

### 质量（维护者真跑后裁决 · 不占 30 验收）

- [ ] `reports/memory_golden_eval_*.yaml` 对照 §2 D5 门槛 → 维护者裁决开/不开 · 开哪个

---

## 7. 思考轮控制（10-spec）

| 轮 | 结论摘要 | 状态 |
|---|---|---|
| R0 | P1 机制已证效果未知；开开关前必须先有证据（用户令 M1 优先） | done |
| R1 | 范围=金样+runner+扫参+CI 测试+门槛；非范围=改生产语义/真跑进 CI | done |
| R2 | 推荐 S1 专用资产；弃 S2 复用 RAG runner（指标不匹配）/S3 生产试错/S4 在线 judge | done |
| R3 | live 缺 key 显式失败不冒充；独立 tenant+清场防污染；报告写死门槛防误引 | done |
| R4 | CI 全 fake 确定性；真跑门槛对齐 reranker-p0「未达不改默认」先例 | done |
| R5 | SPEC 可签收；30 只交 CI 可验部分，真跑=维护者复制区 | done |
| early_stop | no | — |
| residual_risks | ① 金样 ≥40 条覆盖度仍有限（中文运维域长尾）；② 门槛值（0.9/0.1/0.8）为经验值，首轮真跑后可能需校准 | 签收时知悉 |

---

## 8. 下一棒

1. ~~**维护者**：签 `HG-SPEC-SIGNOFF=approved`~~ **done**（2026-09-21 令 M1 优先）
2. **00**：起草 `docs/tasks/active/task_memory_golden_eval.md`
3. **20-task-audit**：书面审 → 00 代录闸（维护者同模式授权）
4. **30**：`task/memory-golden-eval` 分支实现 D1–D4（CI 可验部分）
5. **维护者**：复制区真跑 → 按 D5 裁决 → 决定后续（开开关 / prompt 迭代 / 调值 task）

### 复制区（给维护者 · 真跑）

```text
# 需 .env 含 SiliconFlow key；独立 tenant=memory-eval · 跑后自动清场
.venv/bin/python evals/memory/run_eval.py --backend live --golden evals/memory/golden_v1.yaml --out reports/memory_golden_eval_$(date +%Y%m%d).yaml
# 对照 SPEC §2 D5 门槛裁决
```

---

## 修订

| 日期 | 说明 |
|---|---|
| 2026-09-21 | 初稿并签收（维护者令「先按照建议排序来进行M1」） |
