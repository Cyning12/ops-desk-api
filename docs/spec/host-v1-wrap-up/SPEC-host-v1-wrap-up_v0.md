# SPEC：Agent Host v1.0 落地收尾（文档闭环 + 观测灰度框架 + 背景债登记）（host-v1-wrap-up）（v0）

> **层级**：L1 收尾轨（07 L0 规划的 v1.0 后跟踪 · 非新功能波）  
> **状态**：`signed`（HG-SPEC-SIGNOFF=**approved** · 2026-09-24 · **00 代录** · 维护者令原话：「落盘上面的收尾清单生成spec，为下一步更新进行准备」+ 承 2026-09-23 长程令「签收，并生成对此长程任务的00启动Prompt，新窗口执行，授权00签收所有过程文档，完整落地1.0版本内容」）  
> **立项令（原话留痕）**：维护者 2026-09-24「落盘上面的收尾清单生成spec，为下一步更新进行准备」  
> **上游**：[`../agent-infra/07_host_v1_landing_plan_v0.md`](../agent-infra/07_host_v1_landing_plan_v0.md)（signed · §4 出口八面）· `docs/reports/host_v1_exit_review/REPORT_host_v1_exit_review_20260924_v1_zh.md`（EXIT PASS-WITH-GAP · G2 残余）· `docs/reports/host_v1_exit_review/ACCEPTANCE_three_party_20260924_00.md`（三方验收 PASS · 收尾清单来源）  
> **下游**：HG-SPEC-SIGNOFF → 按 D 块拆 task（D1 可立即 · D2 逐闸 · D3 待数据 · D4 仅登记）  
> **Open Folder（实现）**：`ops-desk-api/`

---

## Harness 元信息

| 字段 | 值 |
|---|---|
| **spec_slug** | `host-v1-wrap-up` |
| **invoke_slug** | `host-v1-wrap-up`（task 阶段） |
| **test_strategy** | `docs-only`（D1/D4）· `required`（D2 灰度task按各闸 SPEC 验收断言复跑 · D3 runbook 实测） |
| **默认分支** | `docs/host-v1-wrap-up`（D1）· 后续 task 各自 `task/<slug>`（**禁止 master/main 直改**） |
| **graph_change_layer** | `none` 预期（D1/D3/D4 均为文档/报告面 · D2 开闸为配置面零码改）；若 D2 某闸灰度需新观测端点 → 回 10-spec 修订 |
| **freeze_id** | 无（不改任何 freeze 契约 · SSE 零新事件 · 零新路由 · 零新表） |

### 人工闸（SPEC 阶段）

| human_gate_id | status | 说明 |
|---|---|---|
| **HG-SPEC-SIGNOFF** | **approved**（2026-09-24 · 00 代录） | 维护者令原话留痕（见状态行 · 双令）；开放裁定 Q1/Q2/Q3 已答；00 可按 D 块拆 task（D1 可立即） |

---

## 1. 背景与目标

v1.0 全轨（V1-A~E + dualproc fix + 出口复核 + SLI 跟进）已 CLOSE 并经三方验收 PASS（`ACCEPTANCE_three_party_20260924_00.md`）。验收同时产出**收尾清单**（P1 文档闭环四项 · P2 运营灰度两项 · P3 背景债两项），本 SPEC 将其固化为可执行轨道，为下一步更新做准备。

### 现状实证（2026-09-24 本帽真读）

| 项 | 真态 |
|---|---|
| 07 规划状态 | 仍 `signed`（未转 completed · 五波 CLOSE+三方验收已满足其 §4） |
| dualproc REGRESSION 报告 | 仅 `REGRESSION_host_v1_splittability_hardening_20260924.md`（BLOCKED-ENV 旧文）· post-#190 更新版未落盘（功能面已 PASS：本窗亲跑 9 passed @ 1cae38f · #190 CI 绿） |
| multi-replica-verify SPEC | `signed` 未标实施态（V1-E #187 + fix #190 已执行完毕） |
| host-v1-landing 启动 invoke | 无五波全 CLOSE 终条 |
| 六个新闸 | 全部默认 off（`.env` 实证未配置）：委派令牌 `LG_RAG_DELEGATION_TOKEN_MODE` · 场景维 `LG_RAG_VISIBILITY_SCENARIO_MODE` · 四字段派生 `OPS_CAPABILITY_REVERSIBILITY_MODE` · LLM 预算 `OPS_LLM_BUDGET_MODE` · 推理缓存 `OPS_LLM_INFER_CACHE_ENABLED` · 情景记忆 `MEMORY_EPISODES_WRITE_ENABLED`/`MEMORY_EPISODES_ENABLED` |
| episode 聚类 | `reports/episode_patterns/` 无生产样例（能力有测试覆盖 · 出口复核如实登记） |
| legacy 审查缺口 | 仓级 reviews 裸扫描 92 缺口全 legacy（host_v1 零缺口 · --json 过滤实证） |
| 前端 | 零跟进需求（契约面无变化 · 六闸默认 off · 唯一新标记 degraded 前端零消费） |

### 一句话目标

闭合 v1.0 文档面（P1 四件一次收口）+ 立六闸观测灰度框架（统一观察期报告格式 · 逐闸独立推进）+ episode 聚类首跑 runbook 备料 + 背景债如实登记（不消化不承诺）。

### 设计纪律（签收时锁死）

1. **不重开已 CLOSE 波**；D1 为 docs-only；D2 开闸为配置面（env）零码改——任何灰度中发现的阻断 bug → 另开 fix task（承不顺手修纪律）。
2. **观察期先行**：任何闸 enforce 前必须有该闸 observe 期 would_block 报告（承各波 SPEC 灰度条款）。
3. **每闸独立 task**：灰度爆炸半径最小化（Q2 裁定）；观察报告格式统一。
4. **背景债只登记**：legacy 92 缺口与他人 WIP 分支不在本轨消化（Q3 裁定）。
5. **零 freeze 动**：不改契约 · SSE 零新事件 · 零新路由 · 零新表 · 前端零跟进维持。

---

## 2. 范围

### D1 · 文档闭环四件（docs-only · 单 task 单 PR 收口 · Q1 裁定合一）

| # | 件 | 内容 | 验收 |
|---|---|---|---|
| D1-1 | 07 规划转 `completed` | 状态行 signed→completed（五波 CLOSE + 三方验收引证 · 承 02 轨 completed 先例）· 修订记录留痕 | 状态行+修订行含 #179~#195 PR 链 |
| D1-2 | G2 REGRESSION 更新报告 | `reports/multi_replica_verify/REGRESSION_dualproc_post_fix_20260924.md`：result=PASS · 证据=#190 fix + CI + 三方验收亲跑 9 passed @ 1cae38f + recorded_at/git sha 环境指纹 | 报告字段族齐（承 reconcile/backfill 先例）· 旧 BLOCKED-ENV 文不删（历史真值） |
| D1-3 | multi-replica-verify SPEC 实施态 | 状态行补「已实施（V1-E #187 + fix #190 · 2026-09-24）」· 修订记录留痕 | 状态行+修订行 |
| D1-4 | landing invoke 终条 | `invoke_20260923_00_host-v1-landing.md` 修订表补：五波 CLOSE + 出口复核（PASS-WITH-GAP→G1 closed）+ 三方验收 #195 PASS · 长程令全链路闭合 | 修订行含完整 PR 链 |

### D2 · 六闸观测灰度框架（框架 + 逐闸推进 · Q2 裁定逐闸独立）

- **统一观察报告格式**（本 SPEC 钉死 · `reports/gate_observe/<gate>_<period>.yaml`）：gate 名 · 模式（observe）· 周期 · would_block 计数与分类 · 误判抽样本（≤10 · 记动作不记内容）· 结论建议（维持 observe / 可 enforce / 需修）· recorded_at。
- **六闸矩阵**（逐闸独立 task · 每闸两阶段：① 开 observe + 观察期报告 → ② 报告支持后开 enforce）：

| 闸 | env（observe 值） | enforce 前置（承各波 SPEC） |
|---|---|---|
| 委派令牌 | `LG_RAG_DELEGATION_TOKEN_MODE=observe` | would_block 零误判报告 + enforce 需 `LG_RAG_DELEGATION_TOKEN_SECRET` 配置 |
| 场景维裁剪 | `LG_RAG_VISIBILITY_SCENARIO_MODE=observe` | would_strip 报告方向正确（宁缺毋滥） |
| 四字段派生 | `OPS_CAPABILITY_REVERSIBILITY_MODE=observe` | builtin 已全量补齐（V1-B）· undeclared 告警零新增 |
| LLM 预算 | `OPS_LLM_BUDGET_MODE=observe` | 预算声明值需先按 usage 账本基线设定（D2 附带口径建议） |
| 推理缓存 | `OPS_LLM_INFER_CACHE_ENABLED=true`（开关型 · 观测=命中率 span） | 命中率与陈旧 miss 率观察报告 |
| 情景记忆 | `MEMORY_EPISODES_WRITE_ENABLED=true` → `MEMORY_EPISODES_ENABLED=true`（写先行召回后行） | 零互写观察 + 召回质量抽评 |

- **本 SPEC 只立框架与第一闸（委派令牌）task 化准备**；其余五闸在委派令牌观察期报告产出后按同模板逐闸推进。

### D3 · episode 聚类首跑 runbook（备料 · 待数据）

- `scripts/episode_pattern_mine.py` 首份生产报告 runbook：前置（episodes 写观察期积累 ≥ 阈值样本）· 执行 · 报告落盘 `reports/episode_patterns/<date>.yaml` · 人工评审建议字段（suggested_rule 人工确认纪律承 V1-D SPEC）。
- **触发条件驱动**：episode 写观察期未积累前不开 task。

### D4 · 背景债登记（只登记不消化 · Q3 裁定）

- `docs/reports/host_v1_exit_review/BACKLOG_register_20260924.md`：① legacy 92 审查缺口（指引 `legacy-gate-exempt.yaml` 豁免机制 · 消化与否另案）② 代跑 agent WIP 分支 `docs/agent-host-current-architecture-20260924`（归原线负责人）③ `test_import_from_supabase` 本地环境性 3 ERROR（CI 绿 · 非缺陷）。

---

## 3. 非范围

- ❌ 重开 V1-A~E 任何功能面 · v2.0 多服务拆分
- ❌ D2 任何 `app/` 代码改动（开闸=env 配置面 · 需改码即回 10-spec）
- ❌ 六闸一次性全开（Q2 裁定逐闸 · 禁大爆炸）
- ❌ legacy 缺口批量消化 / 他人 WIP 分支收口
- ❌ 前端改动（零跟进维持 · 契约面无变化）
- ❌ episode 数据未积累时的聚类空跑（无样本报告无意义）

---

## 4. 开放裁定（必答题 · 全部作答）

### Q1 · P1 四件合一 PR 还是分项

| 方案 | 裁决 |
|---|---|
| **S1 · 合一（单 docs PR）** | **推荐（裁定）**：四件同主题（v1.0 文档闭环）· 均 docs-only · 单 PR 降低过程成本 · CI 三绿即收 |
| S2 · 分项四 PR | 弃选：纯过程成本 · 无独立语义边界需要隔离 |

### Q2 · 六闸灰度推进形态

| 方案 | 裁决 |
|---|---|
| **S1 · 逐闸独立 task + 统一观察报告格式** | **推荐（裁定）**：爆炸半径最小（单闸误判不牵连他闸）· 观察期独立可长可短 · 报告格式统一保可比性（承「拦截开关按 surface 粒度 · 默认关」铁律） |
| S2 · 统一观测面一次全开 observe | 弃选：六闸语义不同（安全闸/预算闸/缓存/记忆）· 统一周期不合理 · 误判归因困难 |

### Q3 · legacy 92 缺口处置口径

| 方案 | 裁决 |
|---|---|
| **S1 · 登记不消化（BACKLOG 文档 + 指豁免机制）** | **推荐（裁定）**：存量形成于 v1.0 之前且已有 `legacy-gate-exempt.yaml` 机制 · 批量消化与 v1.0 收尾无因果 · 全仓裸 verify 转绿非 v1.0 出口判据 |
| S2 · 本轨批量补审消化 | 弃选：92 件历史任务的补审是独立工程 · 混入收尾轨必然烂尾 |

---

## 5. failure_paths

| # | 路径 | 处置 |
|---|---|---|
| FP-1 | D1 文档修改误触历史真值（旧 BLOCKED-ENV 报告/done task 回改） | 只增不改：旧文件零改动 · 新内容只追加（修订行/新文件）· diff 白名单断言 |
| FP-2 | observe 期误判率高却强推 enforce | 观察报告结论须明示「可 enforce / 维持 observe / 需修」· 误判率无可接受口径则停（宁停勿闯 · 承阻断上报纪律） |
| FP-3 | 开闸后发现阻断 bug | 另开 fix task（不顺手修）· 闸退回 off 待修 |
| FP-4 | episode 样本不足聚类空跑 | D3 触发条件钉死（写观察期积累 ≥ 阈值）· 不满足不开 task |
| FP-5 | 预算声明值拍脑袋（无基线） | D2 附带口径：按 `ops_llm_usage` 账本近 N 日 P95 设定初始声明 · 报告留计算过程 |
| FP-6 | 密钥面误配（委派令牌 enforce 无 SECRET） | SPEC 已锁 enforce 缺密钥=拒签发+告警；灰度 task 验收含配置检查项 |

---

## 6. 验收标准

1. **D1**：四件全部落盘（07 completed · REGRESSION PASS 报告 · multi-replica SPEC 实施态 · landing invoke 终条）· 单 PR CI 绿 merge · 旧文件零改动断言
2. **D2**：观察报告格式文档落盘 · 委派令牌闸 observe 开启 + 首份观察报告产出（would_block 计数与误判抽样）· 六闸矩阵登记
3. **D3**：首跑 runbook 落盘（触发条件/执行/评审三节）
4. **D4**：BACKLOG 登记文档落盘（三条目）
5. 全部 docs/报告面：零 `app/` 改动 · 零新路由/表/SSE 事件 · graph-compile 绿（若触图谱）
6. PR 到 master 经 CI 绿后 merge

---

## 7. 思考轮回填（R0–R5）

- **R0（读人聊/目标）**：维护者令「落盘上面的收尾清单生成spec」；收尾清单源自三方验收报告（本窗亲验产出）· 出口复核 G2 · EXIT PASS-WITH-GAP 轨迹全真读。
- **R1（范围/非范围）**：D1–D4 四块；重开波/码改/批量消化/前端显式排除。
- **R2（方案对比）**：Q1 合一（分项弃——纯过程成本）· Q2 逐闸（统一面弃——语义异质归因难）· Q3 登记（批量消化弃——独立工程必烂尾）。
- **R3（边界/失败路径）**：FP-1~FP-6；最锋利边界=观察期质量门禁（宁停勿闯）与历史真值只增不改。
- **R4（验收/可测性）**：验收 6 条全部可对命令/文件断言（docs 面验收=文件存在+字段族+零 app diff）。
- **R5（签收就绪）**：开放裁定无遗留；D1 可立即拆 task；可交 00 代录 HG-SPEC-SIGNOFF。

### 思考轮控制

| 轮 | 状态 | 说明 |
|---|---|---|
| R0 | done | 维护者令 + 收尾清单源文档 + 现状实证已读 |
| R1 | done | 范围 D1–D4 / 非范围锁死 |
| R2 | done | Q1/Q2/Q3 ≥2 案对比 + 裁定 |
| R3 | done | FP-1~FP-6 裁定 |
| R4 | done | 验收 6 条 + test_strategy 按块定 |
| R5 | done | 签收就绪 → 00 代录 HG-SPEC-SIGNOFF |
| early_stop | no | — |

---

## 8. 关联

- 规划：[`../agent-infra/07_host_v1_landing_plan_v0.md`](../agent-infra/07_host_v1_landing_plan_v0.md)（signed · D1-1 对象）
- 验收/复核：`docs/reports/host_v1_exit_review/ACCEPTANCE_three_party_20260924_00.md`（收尾清单源）· `REPORT_host_v1_exit_review_20260924_v1_zh.md`（G2 残余）
- 实施真值：`docs/spec/multi-replica-verify/SPEC-multi-replica-verify_v1.md`（D1-3 对象）· `docs/harness/invokes/by-task/host-v1-landing/invoke_20260923_00_host-v1-landing.md`（D1-4 对象）
- 六闸 SPEC：`../host-v1-delegation-token/` · `../host-v1-visibility-scenario-policy/` · `../host-v1-llm-factory-closure/` · `../host-v1-episodic-memory-feedback/`（各波灰度条款真值）

## 修订记录

| 日期 | 版本 | 内容 |
|---|---|---|
| 2026-09-24 | v0 | 10-spec 初稿：收尾清单四块展开 D1–D4；开放裁定 Q1（合一 PR）/Q2（逐闸独立+统一报告格式）/Q3（登记不消化）全部作答；FP-1~FP-6 裁定；R0–R5 回填 |
| 2026-09-24 | v0 | **00 代录 HG-SPEC-SIGNOFF=approved**（维护者令原话留痕见状态行与人工闸表）；下一棒：拆 D1 task（`docs/host-v1-wrap-up` 分支 · docs-only 单 PR 收口） |
