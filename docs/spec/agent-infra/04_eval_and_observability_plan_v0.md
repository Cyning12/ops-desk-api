# ROADMAP：Eval · Observability（持续观测与测评）

> **层级**：L0 规划（跨 tracing / lg_rag / capability / strategy）  
> **状态**：`active`（2026-08-28 **E0 签收** · HG-SPEC-SIGNOFF approved；**不**直接授权 30 改 `app/`；**00 不实现**）  
> **上游**：[`00_architecture_and_boundaries.md`](./00_architecture_and_boundaries.md) · [`03_strategy_and_intent_plan_v0.md`](./03_strategy_and_intent_plan_v0.md)（S1–S4 **DONE**）  
> **域夹**：[`eval/`](./eval/)  
> **E1 字典真值**：[`eval/ROADMAP_eval_observability_v0.md`](./eval/ROADMAP_eval_observability_v0.md) §3  
> **实现现状**：`app/ops/tracing.py`（Langfuse · env 开关；**langsmith 支路未启用**）  
> **本波落地**：E4 由 30 · [`task_eval_online_sample_scores`](../../tasks/active/task_eval_online_sample_scores.md)；00 **不写码**

---

## Harness 元信息

| 字段 | 值 |
|---|---|
| **plan_slug** | `eval-and-observability` |
| **invoke_slug** | `eval-e0-e1` |

### 人工闸（SPEC / E0）

| human_gate_id | status | 说明 |
|---|---|---|
| **HG-SPEC-SIGNOFF** | approved | 2026-08-28 · **00 代签 · 维护者令签收 Eval spec 并统筹 E0+E1** |

---

## 1. 问题与目标

Agent 需要**持续**回答三问：

| 维度 | 含义 | 典型信号 |
|---|---|---|
| **可用性** | 能否跑完、能力能否调用 | 成功率、超时、`capability.ok`、`policy_blocked`、依赖健康 |
| **准确性** | 意图/plan/答案是否正确 | 金标对比、tool id 合法率、引用可支撑、judge 分 |
| **稳定性** | 同输入是否抖、变更是否回归 | 重放方差、fallback/rebind 率、版本对比 |

目标形态：

```text
每个模块：观测点（运行时事实）+ 测评点（判定）
        ↓
遥测上报（Langfuse traces / scores）
        ↓
聚合 SLI + Dataset Experiments +（可选）线上抽样 judge
        ↓
变更门禁（CI / 发布）
```

**非目标**：用 SO Gateway 做业务答案质量分（见 `00`）；完整自建可观测平台；默认双开 Langfuse+LangSmith。

---

## 2. Langfuse / LangSmith 能否支撑？

### 2.1 结论（选型钉死草案）

| 能力面 | Langfuse | LangSmith | 本仓态度 |
|---|---|---|---|
| 运行时 trace / span / generation | ✓（**已用**） | ✓ | **继续 Langfuse** |
| 结构化 metadata 过滤/检索 | ✓（依赖键规范） | ✓ | Host 钉 **SLI 字典** |
| Scores 挂到 trace / run | ✓ | ✓ | 评测结果回写 score |
| Datasets + Experiments（离线回归） | ✓（含 versioned dataset） | ✓（更偏 annotation UX） | **优先 Langfuse Dataset/Experiment** |
| LLM-as-judge / Code evaluator | ✓ | ✓（模板更多） | Judge 须 SO schema；确定性检查优先 code |
| 人评 annotation | ✓（含 Annotation Queues） | ✓（UX 常更顺） | **默认用 Langfuse 人评**；不因人评另开 Smith |
| 自托管 / 开源 | ✓ | ✗（托管为主） | 与现 jp 云或自托管一致即可 |
| Token usage / 成本估算 | ✓（generation usage + model 单价） | ✓ | Host 须补齐上报与 model 标签；见 §2.5 |
| 基础设施 SLI（CPU/DB/队列） | 弱 | 弱 | **Prometheus/日志** 互补，不塞进 LLM 平台 |

**一句话**：模块级观测点 + 离线/准实时测评，**Langfuse 能支撑主体**；不是「只开 Tracing 菜单就自动有模块看板」，而是 **规范 metadata/score 名 + Dataset 实验 +（可选）线上 score**。  
LangSmith **能**做同类事；本仓 tracing 已 Langfuse-only，**暂不双栈**。人评以 Langfuse Annotation 为准即可。

### 2.2 「在 Langfuse 里看其它点方不方便？」

| 做法 | 方便程度 | 说明 |
|---|---|---|
| 点开单条 trace 看 span 树 + metadata | **高** | 现状已够用（router/supervisor/tool_exec） |
| 按 `supervisor_fallback` / `capability_id` 筛失败 | **中→高** | 键必须稳定、枚举化；自由文本难筛 |
| **只看某一模块**（如只改了 Strategy Builder） | **可满足 · 需约定** | 见 §2.4；不是零配置，但不必全量 E2E |
| 模块仪表盘（可用性/准确率趋势） | **中** | 需 Scores + 命名约定 + Dashboard/API 聚合 |
| 金标回归对比（prompt/catalog/模型变更） | **高（用对功能后）** | Datasets → Experiments → run-level scores |
| Token / 费用列与按模型汇总 | **中（补齐后）** | 见 §2.5；现状 usage 有上报入口，展示与计价未成方案 |
| 集群/DB/向量库可用性 | **低（不该指望）** | 用基础设施监控 |

**现状缺口**：只用了运行时 monitoring；**未**系统化使用 Dataset / Experiment / Score Analytics / Annotation；token 未成「列展 + 计费」产品面。

### 2.3 模块 × 观测点 × 测评点（清单）

| 模块 | 观测点（runtime） | 测评点（eval） |
|---|---|---|
| Intent / router | `route` · `router_fallback` · latency | 金标：query→期望 route/intent |
| Strategy Builder | allowlist 大小 · `rebinding_count` | 过赋能/欠赋能用例 |
| Work Planner (supervisor) | `subtask_types` · `supervisor_invalid_tool_id` · fallback | plan 结构金标 |
| tool_exec / Capability | `capability_id` · `ok` · `policy_blocked` | 输出契约 / 未知 id 率 |
| RAG / evidence | retrieve/grade/answer meta | 引用支撑、空答率 |
| Skill match / provide | match ids · provide ok | 匹配贴题金标 |
| Critic | 达标原因码 | 与人评一致性抽检 |
| E2E | 根 span 成功/耗时 | 场景集端到端 |

### 2.4 单模块针对性测评（例：只改 Strategy Builder）

**可以满足**，推荐「切片金标 + 模块 score 命名空间」，而非每次全图人肉翻 trace。

| 手段 | 做法 | 升级只改 Builder 时 |
|---|---|---|
| **模块 Dataset** | `golden/strategy_builder.yaml`：input → 期望 allowlist / 禁止 id | 只跑该 Dataset 的 Experiment |
| **Score 前缀** | `acc.strategy.allowlist_match` · `stab.strategy.rebind` | UI/API 按 score name 过滤对比基线 |
| **Span 名 / tag** | `trace_span("strategy_builder")` + `module=strategy_builder` | Trace 过滤只看该 span；对比 latency/错误 |
| **metadata 版本** | `strategy_builder_version` / git sha / prompt 版 | 筛「本版 vs 上版」 |
| **门禁范围** | CI job `eval-strategy-builder` 只挡该模块阈值 | 不强制等全 E2E 绿才合（E2E 可夜间） |
| **人评队列** | Annotation Queue 只收 `module=strategy_builder` 抽样 | 升级后定向打分 |

**注意**：模块切片证明「Builder 裁对了」；**不**自动证明下游 supervisor/RAG 仍好——建议「模块必跑 + E2E 抽样/夜间」。只改 Builder 时，针对性测评**足够作发布主证据**，E2E 作回归网。

### 2.5 Token 与计费

| 层 | 现状 | 目标 |
|---|---|---|
| **上报** | `update_current_generation_usage`（input/output tokens）；部分 `complete()` 路径已接 | 凡 LLM generation span 尽量上报；缺 usage 帧则标明 `usage_missing` |
| **模型维度** | span/model 字段不统一则难按价计 | metadata 强制 `model` · `provider`（与价表键一致） |
| **UI 列展** | Langfuse 对 generation 有 usage；自定义「费用列」靠 Dashboard/导出或单价配置 | 在 Langfuse 配 **model 单价**（平台能力）或 Host 用 API 拉 usage × 价表出报表 |
| **计费方案** | **未立** | Host「Cost 账本」：价表（模型×单价×币种×生效日）→ 按 trace/日/模块聚合；可先 CSV/内部 API，不必自建完整计费中台 |

Langfuse **可以**展示 token，并在配置了模型价格后估算 cost；**不能替代**你们的商务价表（折扣、自建模型、按租户账单）。  
计费 = **usage 遥测（Langfuse）+ 价表与聚合（Host 薄层）**；与 Eval 同属观测轨，可单开 **E5**。

### 2.6 Langfuse 产品模块地图（相对本仓现状）

> 对照 Langfuse UI（如 v4.16 · 项目 Ops-desk-agent）：本仓目前主要用 **Observability → Tracing**。

| UI 分组 | 模块 | 做什么 | 本仓建议用法 |
|---|---|---|---|
| — | **Home** | 项目总览 | 扫一眼健康即可 |
| — | **Dashboards** | 自定义图表（延迟、分数、用量等） | E1 后按 `module`/score 做模块看板 |
| Observability | **Tracing** | 单次请求的 span/generation 树、metadata、usage | **已用**；补 `module`/枚举键 |
| Observability | **Sessions** | 多轮/同用户多次 trace 串成会话 | 对齐 H3 thread/session；看多轮退化 |
| Observability | **Users** | 按终端用户聚合 | 若上报 `userId` 可做人均成本/质量 |
| Observability | **Alerts** | 阈值/错误率告警 | fallback 率、失败率超阈通知 |
| Prompt Management | **Prompts** | Prompt 版本库（可与代码/H4 并存） | 可选；H4 PromptAssembly 为仓内真值时勿双源打架 |
| Prompt Management | **Playground** | 在 UI 里试 prompt/模型 | 调 prompt 用；正式回归仍走 Dataset Experiment |
| Evaluation | **Scores** | 挂在 trace/observation/run 上的分数 | 模块测评与费用相关分；见 score 字典 |
| Evaluation | **Evaluators** | 自动评（LLM-as-judge / code） | 线上抽样或 Experiment 内；judge 须 schema |
| Evaluation | **Human Annotation** | Annotation Queues 人审队列 | 升级后定向抽检（可按 module 建队列） |
| Evaluation | **Datasets** | 金标输入/期望输出集合（可版本） | 模块切片金标源；与 git golden 对齐 |
| Evaluation | **Experiments** | 对 Dataset 跑多版本对比 | 「只改 Builder」时只跑对应 Dataset |

**阅读顺序建议**：Tracing（现状）→ Scores/Datasets/Experiments（测评）→ Human Annotation（人审）→ Dashboards/Alerts（运营）→ Sessions/Users（会话与租户）→ Prompts/Playground（可选，注意与 H4 真值）。

### 2.7 推荐学习 / 启用路线（由浅入深）

面向本仓（已会 Tracing · 规划 Eval E 轨 · 策略轨并行）：

```text
L0 会看单次请求
  Tracing：span 树、metadata、generation usage
      ↓
L1 会量「好不好」
  Scores → Datasets → Experiments
  （先确定性分，再考虑 Evaluator / judge）
      ↓
L2 会用人审补盲区
  Human Annotation（按 module 建队列）
      ↓
L3 会运营与告警
  Dashboards → Alerts
      ↓
L4 会会话与用户维度
  Sessions → Users（须先埋 userId / sessionId）
      ↓
L5 可选：云端 Prompt
  Playground 试错 → Prompts 版本（与 H4 定真值后再用）
```

| 阶段 | 学什么 / 启用什么 | 练手目标（Ops Desk） | 对应规划 |
|---|---|---|---|
| **L0** | Tracing 过滤、metadata、对比两次请求 | 能解释一次 supervisor fallback 为何发生 | 现状 |
| **L1a** | Scores：手动/脚本给 trace 打 0/1 | 给非法 tool / 成功 END 打分 | E1 |
| **L1b** | Datasets：10～20 条金标（先 router 或 strategy） | 建 `golden/strategy_builder` 或 router 小集 | E2 |
| **L1c** | Experiments：同一 Dataset 跑基线 vs 改动版 | 「只改 Builder」只跑该实验、看分数差 | E3 |
| **L1d** | Evaluators：code 优先，再 LLM-as-judge | allowlist 集合相等；judge 须 schema | E3/E4 |
| **L2** | Human Annotation Queue | 队列「review strategy allowlist」抽 5 条 | E4 |
| **L3** | Dashboards + Alerts | fallback 率、模块 score、token 趋势；超阈告警 | E1 后 / E5 |
| **L4** | Sessions / Users | 多轮 Chat 同 session 串联；人均费用 | H3 对齐后 |
| **L5** | Playground → Prompts | 仅当决定「某 prompt 以 Langfuse 为发布源」 | 可选；默认真值在仓内 H4 |

**节奏建议**：L0→L1c 为测评最小闭环（约可与 E1–E3 同步）；L2/L3 上线后做；L4/L5 按产品需要，勿一上来双源 Prompt。

**刻意后置**：未有 Dataset 前不要堆 Evaluator；未埋 `module`/session 前不要期望 Users/Sessions 看板有意义；未定 H4 真值前不要把 Prompts 当生产源。

### 2.8 Scores 如何开始（官方 SDK + 本仓）

官方：[Scores via API/SDK](https://langfuse.com/docs/evaluation/evaluation-methods/scores-via-sdk)。  
要点：Score 可挂 **trace / observation / session / dataset run**；类型 Numeric / Categorical / Boolean / Text；可用 `create_score(trace_id=…)` 或上下文内 `score_current_span` / `score_current_trace`。

| 起步方式 | 要不要改本仓代码 | 适合 |
|---|---|---|
| **A. UI 手动打分**（Scores / Annotation） | **否** | 今天就学界面；对已有 Tracing 点选打分 |
| **B. 仓外脚本** SDK `create_score` | **否**（脚本可放 `scripts/`） | 事后按 trace_id 补分；不碰热路径 |
| **C. 热路径薄封装** | **是**（建议 `tracing.py` + 1～2 调用点） | 持续自动：如 `supervisor_fallback`→ Boolean score |
| **D. Langfuse Evaluators**（平台跑） | 配置为主；trace 已够即可 | L1d；先 A/C 再上 |

**推荐最小闭环（后续 30 task，非本波、非 00）**：

1. UI（A）：对几条已有 lg_rag/supervisor trace 手动打 `avail.success` / 备注。  
2. 钉 E1 字典里 **2～3 个 score 名**（勿先发明一堆）。  
3. 可选 spike（C）：`tracing` 增加 `score_current_trace(name, value, …)` no-op 包装——属 **E3/E4**，须另开 task；**00 不写**。  
4. Dataset/Experiment 放到模块金标有了之后（**E3**，前置 E2）。

**不必**一上来大改 Agent；Scores ≠ 新业务功能，是观测面增量。

### 2.9 与 Agent 升级的并行策略

| 选择 | 内容 | 何时 |
|---|---|---|
| **主升级** | [`03`](./03_strategy_and_intent_plan_v0.md) **S1** Strategy Builder allowlist | 架构下一棒；有明确产品增量 |
| **伴学观测** | Scores A→C（§2.8）+ 必要时 E1 字典短文 | **可与 S1 并行**；改 Builder 时顺带打 `acc.strategy.*` |
| **暂缓** | 完整 Intent S2、Critic S4、Cost E5、云端 Prompts | 有 S1 + 最小 Scores 后再开 |
| **不建议** | 先停 Agent 升级、只学满 Langfuse 全模块 | 缺少真实变更，Experiment 对比无意义 |

**结论**：策略轨 **S1–S4 已合入**。测评主线从 **E0/E1（本波文档）** 进入 **E2 模块金标**（**另开 task**；00 **不**在本窗实现）。Scores 热路径封装放到 E3/E4，**本波不改** `tracing.py`。  
**不建议**：把 DEF-003/004 RAG 草案或 Langfuse SDK v4（DEF-001）捆进 Eval 收尾；**禁止**一次做完 E2–E5。

---


**推荐：混合 · 不以 Fork 三方为主。**

```text
┌─────────────────────────────────────────────┐
│  Langfuse（控制面 · 可官方云或自托管）         │
│  traces · scores · datasets · experiments   │
│  annotation queues · usage/cost（单价配置）   │
└──────────────────▲──────────────────────────┘
                   │ SDK 上报 / score ingest
┌──────────────────┴──────────────────────────┐
│  Host Eval / Cost 薄层（仓内自建 · 可迁移）     │
│  · SLI / score / module 标签字典             │
│  · 模块金标 + E2E 金标                        │
│  · runners + CI 模块门禁                     │
│  · 价表与费用聚合（可选）                     │
└─────────────────────────────────────────────┘
```

| 选项 | 态度 | 说明 |
|---|---|---|
| **完整自建** 观测+评测平台 | **否** | 重复造 Langfuse |
| **Fork Langfuse 改 UI/逻辑** | **默认否** | 升级痛苦；仅当必须深度定制列/权限且上游拒绝时再议 |
| **自托管 Langfuse + 配置/插件式扩展** | **可** | 仍算「用产品」，不是业务仓二开核心 |
| **仓内二开（Eval harness / Cost 账本 / 模块 Dataset）** | **是 · 主路径** | 单模块测评、价表、CI 门禁都在这里做 |
| 评估器库（RAGAS 等） | **可选** | 分数映射进统一 score 名 |
| 双开 LangSmith | **非默认** | 人评用 Langfuse Annotation 即可 |

**「二开也可以做到吗？」**  
- **仓内二开（推荐）**：完全可以做到单模块测评、score 列语义、费用报表。  
- **Fork Langfuse 二开**：理论上也能做更贴业务的列展，但**不划算**；优先 API + Dashboard + Host 报表。  
- 人评：**不必**为 annotation 换 Smith；Langfuse 已含 human annotation。

---

## 4. 持续节奏

| 节奏 | 动作 |
|---|---|
| 每请求 | 结构化 metadata；`module` / 版本标签；usage 尽量上报 |
| 日/周 | Dashboard：成功率、fallback、token/费用 Top、按模块错误 |
| 每变更 | **改哪测哪**（模块 Dataset）+ 夜间/门禁 E2E |
| 抽样线上 | 规则 score / 可选 judge / Annotation Queue |
| 发布门禁 | 模块阈值 +（约定）E2E 不退化 |

稳定性：固定输入 + 钉模型/prompt/catalog/Builder 版本 + 可控温度。

---

## 5. 建议波次（E 轨）

| 序 | ID | 摘要 | 状态 |
|---|---|---|---|
| **E0** | `eval-spec-signoff` | 本文件 + `eval/ROADMAP` 签收 | **DONE** · 2026-08-28 |
| **E1** | `sli-score-dictionary` | metadata/score/`module` 键字典 | **DONE** · 真值在 ROADMAP §3 |
| **E2** | `goldenset-lg-rag-v0` | 最小金标 + **按模块切片**目录 | **DONE** · PR #93 |
| **E3** | `langfuse-dataset-experiment` | Dataset/Experiment + **模块 CI job** | **DONE** · PR #94 |
| **E4** | `online-sample-scores` | 抽样 score + Annotation 回流 | **本波 task** `eval-online-sample-scores`（30 · 00 不写码） |
| **E5** | `token-cost-ledger` | usage 全路径补齐 · 价表 · 费用聚合/导出 | 待 E4 · **勿绑进 E4** |

详规：[`eval/ROADMAP_eval_observability_v0.md`](./eval/ROADMAP_eval_observability_v0.md)。  
策略轨已收官。**E2** 起须另开 task + 人工闸；本文件仍 **不**直接授权 30 改码。**00 不实现。**

---

## 6. 硬约束

1. Score / metadata / `module` 标签 **名字典**为 Host 真值；禁止各节点随意发明同义键。  
2. LLM-as-judge 出口走 Structured Output（分项 + 原因枚举）。  
3. 金标与阈值进 git（或 Dataset version 钉死）；实验可复现。  
4. 评测失败不污染主请求路径（异步/旁路）；CI 门禁另通道。  
5. 费用以 usage×价表为准；禁止用 LLM「估个价」当账本。  
6. 本文件**不直接授权 30** 改 `app/`；E2+ 须另开 task。  
7. **00 只签收/统筹，不实现** task（含不在签收窗内写金标、改 tracing、开 Dataset runner）。

---

## 7. 修订记录

| 日期 | 说明 |
|---|---|
| 2026-08-27 | 初版：Langfuse/Smith 能力边界 · 混合架构 · 模块观测测评清单 · E0–E4 |
| 2026-08-27 | §2.4 单模块针对性测评；§2.5 token/计费；人评默认 Langfuse；E5；二开边界澄清 |
| 2026-08-27 | §2.6 Langfuse UI 模块地图（相对 Tracing 现状） |
| 2026-08-27 | §2.7 推荐学习/启用路线 L0–L5 |
| 2026-08-27 | §2.8 Scores 起步；§2.9 与 03/S1 并行策略 |
| 2026-08-28 | **E0 签收**：HG-SPEC-SIGNOFF approved；§2.9 改为 S 轨已收官、下一棒 E2；E1 字典见 ROADMAP §3 |
| 2026-08-28 | 过程文档二次签收；颗粒度 E2–E5 分 task；钉 00 不实现 |
| 2026-08-28 | E2 开工：独立 task `eval-goldenset-lg-rag`；00 不实现 |
| 2026-08-28 | 00 后续编排见 eval ROADMAP §4.1；E3 起须 E2 合入后另开；00 不落地 |
| 2026-08-28 | E3 开工：`eval-langfuse-experiment-ci` |
| 2026-08-28 | E3 MERGED · E4 开工：`eval-online-sample-scores` |
