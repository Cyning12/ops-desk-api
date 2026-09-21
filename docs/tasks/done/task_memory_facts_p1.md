# Task：事实型记忆 P1（向量语义召回 + LLM 离线候选抽取）

> **状态**：`done`（2026-09-21 闭环：三闸 approved · 30 V0–V4 交付 · 40 独立核验 PASS（A–I 全过 · 11/11）· 代码在 `task/memory-facts-p1` 分支 · **PR 待开**）  
> **类型**：feature / L4 记忆层 · 承接 P0  
> **上游 SPEC**：`docs/spec/memory-facts-p1/SPEC-memory-facts-p1_v1.md`（**signed** · HG-SPEC-SIGNOFF=approved 2026-09-21）  
> **分支**：`task/memory-facts-p1`（base：`master` · 已含 P0 合并 `39f6863` · **禁止 master 直改**）  
> **00 注**：2026-09-21 · 维护者令「签收」（P0 同模式授权：00 代录后续过程闸 · 30/40 派子 Agent）

---

## Harness 元信息

| 字段 | 值 |
|------|-----|
| **task_slug** | `memory-facts-p1` |
| **git_branch** | `task/memory-facts-p1` |
| **implement_repo** | `ops-desk-api` |
| **test_strategy** | `required` |
| **test_strategy_note** | 单测：向量融合排序/降级/开关关闭=P0 逐字节；抽取：候选全过闸 + 噪声拒写查表为零 + LLM 失败零写入 + 热路径零抽取 span 断言 + source_run_id 溯源；变异检验：错误事实经向量通路真被复述召回→revoke→消失；fake embedder 确定性化，不连真外网 |
| **code_quality_bar** | `L2_backend` |
| **graph_change_layer** | `G-L1` |
| **graph_delta** | `docs/_tech_graph/l1/01_modules.md`（`memory` 行备注：向量召回 + 离线抽取 · 依赖出边 +`rag`/`llm`） |
| **graph_delta_note** | **不新增**一级模块；须维护者签 HG-GRAPH-MODULES 新行（00 代录） |
| **wiki_delta** | `n/a` |
| **wiki_delta_note** | 契约真值在 SPEC `memory-facts-p1` |
| **review_hat** | `20` |
| **required_invoke_hats** | `10,20,30,40` |
| **invoke_retention_profile** | `default` |
| **experience_capture** | `recommended` |
| **kpi_aggregator** | `CLOSE` |
| **orchestration** | 10 落稿 → 20-task-audit → 维护者授权 00 代录闸 → 30 → 40 → CLOSE |
| **freeze_id** | 无（不改 `lg-rag-sse-v1` / `lg-rag-http-v1`） |

### 人工闸

| human_gate_id | status | blocks_hats | 说明 |
|---------------|--------|-------------|------|
| HG-TASK-DRAFT | **approved** | 20-R1, 30 | 2026-09-21 维护者令「签收」· SPEC 已签 |
| HG-AUDIT-R1 | **approved** | **30** | 2026-09-21 维护者令「签收」（P0 同模式授权）· 00 代录（20-task-audit R1 终轮零阻塞已落盘） |
| HG-GRAPH-MODULES | **approved** | **30** | 2026-09-21 同上 · 00 代录 · `01_modules.md` memory 行备注 + 人签记录已落 |

---

## 背景与目标

P0 已闭环（PR #144 merged）：事实表 + 闸 + 状态机 + 确定性召回注入。两个已知缺口（SPEC-P1 §1）：**① 召回语义盲区**（换说法就找不到，全靠 key 约定覆盖）；**② 写入靠喂**（无自动候选来源）。

本竖切交付两条**默认关**增强：向量语义召回（复用现成 `Embedder`/`RAG_VECTOR_BACKEND`）+ LLM 离线候选抽取（run 后离线产出候选，**全部过同一个写入闸**）。**P0 闸/状态机/注入语义一行不改；两开关全关 = P0 现网逐字节一致**。

设计纪律（30 不得违反）：1. 向量只解决"怎么召回"，写入判据永远闸判；2. 抽取产物是候选不是事实，热路径零抽取调用；3. 每条增强可独立关闭独立降级。

---

## 现状锚点（只读 · 30 必读 · 10 已扫）

| 主题 | 路径 · 锚点 | 现状缺口 |
|------|-------------|----------|
| 记忆存储/状态机 | `app/ops/memory/{gate,service}.py` · `app/db/models.py` `OpsMemoryFact` | 无 embedding 列；recall 仅确定性 |
| 注入装配 | `app/ops/lg_rag/continuity.py` `assemble_graph_messages_with_memory` | 召回源单一；融合算法待加 |
| Embedder | `app/ops/rag/embedder.py`（`Embedder` 协议 · `ApiEmbedder` 默认 SiliconFlow · **同步接口**） | 异步路径须线程卸载（对齐 rag 既有用法） |
| 结构化输出 | `app/ops/structured_output/`（`parse_only` / `acomplete_structured`） | 抽取输出必须走此管道，不手撕 JSON |
| 后台任务先例 | T5.1 persist 后台不阻塞 SSE yield（`app/ops/lg_rag/`） | 抽取钩子同模式：run 后离线触发 |
| env 纪律 | P0 `memory_facts_enabled()` 非法回退+warning | 两个新 env 同纪律 |
| P0 测试基线 | `tests/test_memory_{gate,injection,service_db}.py`（34 用例） | **全绿是本波回归底线** |

---

## 钉死契约（自 SPEC §2/§5 锁死；30 不得静默改义）

| 项 | 钉死 |
|----|------|
| **开关** | `MEMORY_FACTS_VECTOR_RECALL_ENABLED=false` · `MEMORY_FACTS_EXTRACT_ENABLED=false`（均默认关 · 非法值回退+warning） |
| **全关=P0** | 两开关全关时装配输出与 P0 现网**逐字节一致**（P0 回归测试结构复用） |
| **embedding 列** | nullable vector · alembic 可逆；**既有行不回填**（null → 只走确定性通路即正确） |
| **融合排序** | 确定性 top-N ∪ 向量 top-M → 去重 → 向量相似 × 时间衰减 × 来源权重（显式/人工来源 > 抽取）→ `MEMORY_FACTS_MAX_ITEMS` 预算截断（截低分不随机） |
| **向量降级** | embedder/向量查询失败 → 回退确定性召回 + `memory_vector_degraded` · 不拖垮 chat |
| **抽取触发** | **run 完成后离线**（对齐 T5.1 后台 persist 模式）；**热路径零抽取调用** |
| **抽取过闸** | 产出仅为 `FactCandidate` → 逐条 `should_write` → `write_fact`（P0 事务 supersede 复用） |
| **抽取溯源** | 写入必带 `source_run_id` + `source_turn`（`revoke_by_source` 一键全撤） |
| **抽取失败** | LLM 失败/非法 JSON/超时 → **零写入** + log · 有限重试 ≤1 · 绝不静默写入 |
| **抽取管道** | 输出走 `structured_output`（parse → repair → validate） |
| **成本** | 每 run 至多 1 次抽取调用；span 记 `memory_extract_candidates=N written=M` |
| **tenant 纪律** | 向量查询**必带** `tenant_id` 谓词（跨 tenant=空）；身份来源同 P0 |
| **SSE/HTTP** | 零改事件类型；无新对外端点 |

---

## 范围（同 task 竖切）

- [x] **V0 · Schema**：`ops_memory_facts` 加 `embedding` 列（nullable · alembic 往返可逆 · 接 head `20260921_memory_facts`）；model 同步
- [x] **V1 · 向量召回**：写入时嵌入（线程卸载）· 混合召回融合（相似×衰减×来源权重）· 降级通路 · env 开关
- [x] **V2 · LLM 抽取**：run 后离线钩子（T5.1 模式）· structured_output 管道 · 候选过闸写库（带 source）· 失败零写入 · span 计数
- [x] **V3 · 红线七条**：复述召回 / 噪声拒写查表为零 / 失败零写入 / 热路径零抽取 span 断言 / 向量降级 / 全关=P0 逐字节 / 变异检验（向量通路版）
- [x] **V4 · 图谱与文档**：`01_modules.md` `memory` 行备注 + graph-compile 绿 + README 增 env/算法/时序

**竖切结论**：V0–V3 同 task 必交；V4 随 30 一并。

### 非范围

- 画像 / `kind=preference`；既有行 embedding 回填批处理（另 task）
- 热路径/实时/流中抽取；对外 HTTP 端点 / 用户面 UI
- 改 P0 闸判据/状态机/注入块语义；改 SSE；跨租户共享
- A/B 分流；合规物理删除权；web / ios；新第三方依赖

---

## failure_paths

| 触发条件 | 系统行为 | 可重试 | 用户可见 |
|----------|----------|--------|----------|
| `HG-AUDIT-R1` / `HG-GRAPH-MODULES` pending 即 30 | **拒开工** | 是 | 是 |
| embedder 加载/调用失败 | 回退确定性召回 + `memory_vector_degraded` | 是 | 否 |
| 向量列不存在（migration 未跑） | 回退确定性 + 明确 log，不炸请求 | 是（跑 migration） | 否 |
| 抽取 LLM 失败/超时/非法 JSON | 零写入 + log；重试 ≤1 | 是（下一 run） | 否 |
| 抽取产出全被闸拒 | 零写入（正常态）· span 记 candidates/written | — | 否 |
| 错误事实经抽取写入 | `revoke_by_source(run_id)` 一键全撤 | — | 否 |
| 跨 tenant 向量召回 | 必带 tenant 谓词；跨 tenant=空 | 否 | 是（安全空） |
| 抽取 prompt 注入（run 内容含指令性文本） | 输出仅为候选 → 闸 + validate 拦截；不参与指令拼装 | — | 否 |
| 抽取成本失控 | 每 run ≤1 次；开关全局可关；span 计数 | — | 否 |
| 两开关全关但装配有 diff | 审查拒收（=P0 逐字节回归） | 是 | 否 |
| 无变异检验却宣称红线有效 | 40/verify 拒收 | 是 | 否 |

---

## 验收标准

- [x] 人工闸：`HG-AUDIT-R1` · `HG-GRAPH-MODULES` 均 approved 后方可勾选下列码项
- [x] V0：embedding 列 migration 往返可逆；`OpsMemoryFact` 同步
- [x] V1：复述 query 经向量通路召回（fake embedder 确定性断言）；embedder 故障回退 + 降级标记；融合排序确定性（截低分）
- [x] V2：离线抽取 → 候选全过闸 → 写入带 `source_run_id`；噪声候选查表为零；LLM 失败/非法 JSON 零写入；热路径零抽取 span 断言；走 structured_output 管道
- [x] V3：红线七条全绿（含变异检验：错误事实经向量通路真被召回 → revoke → 消失）
- [x] 两开关全关：装配输出与 P0 现网**逐字节一致**
- [x] V4：`memory` 行备注 + graph-compile 绿 + README 更新
- [x] **旧测 grep 影响面**（行为变更类 · 20 checklist · 2026-09-21 代跑）：`test_memory_*` 3 文件 34 用例（P0 语义回归底线）；embedder 系 `tests/test_rag_embedder.py` 等 3 文件（只复用不改义）；structured_output 系 10+ 文件（只调管道不改管道）；全量 pytest 保持绿（master 既有环境失败除外）
- [x] `ruff` 触及路径绿；`pytest` 本波 + P0 memory + lg_rag/session 回归绿
- [x] 新 env 非法值回退+告警；无新第三方依赖
- [x] `npx spec-wave task lint --file docs/tasks/active/task_memory_facts_p1.md` PASS

---

## 依赖

| 依赖 | 说明 |
|------|------|
| SPEC | `docs/spec/memory-facts-p1/SPEC-memory-facts-p1_v1.md`（signed） |
| P0（已合并） | `docs/tasks/done/task_memory_facts_p0.md` · PR #144（`39f6863`） |
| 上游设计 | `../ops-desk-workspace/docs/08-interview/07_agent-memory-prompt-module-landscape_v1_zh.md` §1.5/§1.8 |
| 编码规范 | `docs/standards/CODING_BACKEND_L2_v1_zh.md` |
| 图谱 | `docs/_tech_graph/l1/01_modules.md`（HG-GRAPH-MODULES 真值） |

---

## 给执行帽的必读列表

1. `AGENTS.md`
2. 本 task（钉死契约 · 闸 · 非范围）
3. SPEC `docs/spec/memory-facts-p1/SPEC-memory-facts-p1_v1.md`
4. `docs/standards/CODING_BACKEND_L2_v1_zh.md`
5. 代码：`app/ops/memory/**` · `app/ops/lg_rag/continuity.py` · `app/ops/rag/embedder.py` · `app/ops/structured_output/**` · T5.1 后台 persist 先例
6. `docs/harness/prompts/FRAGMENT_30_gate_verify_v1_zh.md`

---

## 思考轮控制

| 轮 | 结论 | early_stop | reason（early_stop） | residual_risks |
|----|------|------------|----------------------|----------------|
| R0 | P1 = 向量召回 + 离线抽取；SPEC 已签收；P0 已合 master | no | — | none |
| R1 | 30 硬阻塞于 HG-AUDIT-R1 + HG-GRAPH-MODULES（00 代录） | no | — | 无 |
| R2 | V0–V3 同竖切；图谱随 30；SSE 零改 | no | — | 无 |
| R3 | 降级/零写入/溯源/成本四条失败语义钉死 | no | — | 无 |
| R4 | 红线七条全否定性断言；fake embedder 确定性化；热路径 span 断言 | no | — | 融合权重初值需实测（继承 SPEC residual ①） |
| R5 | 可交 20-task-audit | no | — | 抽取精度依赖金样迭代（继承 SPEC residual ②） |

**actual_last_round**：R5 · **early_stop**：no · **residual_risks**：见 R4/R5

### R0 · 问题框定

P0 把"该不该记"机制化；P1 只补"怎么召回"与"候选从哪来"，不重开 P0 已钉语义。

### R1 · 开工闸

两闸 pending 期间拒 30；维护者已授权 00 代录（同 P0 模式）。

### R2 · 竖切

召回与抽取同 task：两者都改召回/写入链路但各自独立开关，分开交付会出现"有召回没候选"或"有抽取没召回"的半截态；图谱备注随 30。

### R3 · 失败语义

向量通路任何故障都不得劣于 P0 确定性通路（回退+标记）；抽取通路任何失败都必须是零写入（候选不是事实）；抽取写入必须可一键全撤（source 溯源）。

### R4 · 可测性

向量语义用 fake embedder 确定性向量消解随机性；热路径零抽取用 span 断言而非口头保证；全关=P0 逐字节复用 P0 回归结构。

### R5 · 交接就绪

思考充分可交 20；残余风险两条继承 SPEC 签收知悉项。

---

### 自检结论（执行者）

> **hat 40** · 2026-09-21 · 独立核验（未复信 30 报告；实跑 + 亲读 diff）

| 命令 | 退出码 | 摘要 |
|------|--------|------|
| ruff check（10 触及文件） | 0 | All checks passed |
| pytest P0 memory×3 + P1 新测×2 + session/continuity×2 | 0 | 95 passed（P0 基线 54 用例全绿 · task 落稿时"34"为旧计数） |
| pytest tests（全量 · 剥代理 env） | 1 | 1088 passed / 1 skipped / 3 failed=chat_ws×2+capability proxy×1；git stash 回 master 干净树复跑同 3 失败 ⇒ 既有环境失败零新增 |
| ./scripts/graph-compile.sh | 0 | graph.json 仅 generated_at 漂移已还原 |
| alembic downgrade -1 && upgrade head | 0 / 0 | 20260921_memory_facts_embedding ↔ 20260921_memory_facts 往返可逆 |
| npx spec-wave task lint --file docs/tasks/active/task_memory_facts_p1.md | 0 | LINT: PASS |

**验收摘要**：11 项全 PASS。红线七条全真断言——变异检验先钉 updated_at 证确定性通路漏掉错误事实（排除假通过）→ 向量通路真召回排首 → revoke 后 fused+装配块双消失；噪声拒写查表为零且过闸带 source_run_id/source_turn；LLM 失败零写入且 provider.calls 计数证重试 ≤1；热路径零抽取为真 spy 断言；两开关全关=P0 逐字节（全内容元组 × 3 组参数化）；向量 SQL 必带 tenant+user 谓词（跨 tenant=空有测）；deferred=True 实证 P0 读通路 SQL 不含 embedding 列；写通路 migration 未跑时也不炸（INSERT 省略该列 / SAVEPOINT 隔离留 NULL 走确定性）——读写两侧均满足契约。conftest +9 行 ALTER 偏差经独立验证**接受**（同构既有 3 条先例 · 幂等最小）。SSE 零新事件类型；无新依赖。

**已知未测项**：① 真实 SiliconFlow embedder 端到端未测（fake 确定性化）；② 真实 LLM 抽取精度依赖金样迭代（SPEC residual ②）；③ 融合权重初值未实测调参（SPEC residual ①）；④ span 元数据未在真实 tracing 后端验证；⑤ SSE 点火以 mock astream 验证未跑真图全链路。

**结论**：**40 PASS** · 无阻塞 · 可进 PR 流程

---

## 修订

| 日期 | 说明 |
|------|------|
| 2026-09-21 | 10-task 落稿 · R0–R5 全轮 · HG-AUDIT-R1/HG-GRAPH-MODULES pending → 30 拒开工 |
| 2026-09-21 | 20 R1 终轮零阻塞签收 · 00 代录两闸 · 图谱 memory 行备注落 · 30 开工 |
| 2026-09-21 | 30 交付 V0–V4 → 40 独立核验 PASS（11/11 · conftest 偏差经裁定接受）→ 00 回写勾选+自检结论 · 归档 done · CLOSE |
