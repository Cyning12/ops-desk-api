# 面试待改进意见 · 采纳与本仓落地决议

> **日期**：2026-09-17  
> **范围**：Q1–Q6 技术面 + Q7 软技能反馈中的「待改进」  
> **原则**：区分三档——**采纳为口径** / **本仓近期落地** / **不纳入本仓（平台级或产品边界外）**  
> **本仓约束**：ops-desk-api 当前是企业只读助手 + Host 旁路；无多租户 Workspace 产品、无高危写主路径。落地须走 task + 闸，本文不授权 30。

---

## 0. 总览


| 档                            | 含义                         | 条数（约） |
| ---------------------------- | -------------------------- | ----- |
| **A · 采纳且本仓近期做**             | 与现网痛点同构、ROI 高、不撑破产品边界      | 见 §1  |
| **B · 采纳为设计口径，本仓缓做或只写 SPEC** | 方案正确，但依赖多租户/多团队/写能力才有负载    | 见 §2  |
| **C · 部分采纳 / 改表述**           | 意见对，但落点或力度需修正              | 见 §3  |
| **D · 本仓明确不做（或极远期）**         | 与 Mode A / 只读成品冲突，或成本 > 收益 | 见 §4  |


**结论先行：**  
面试扣分点里，**值得立刻推进本仓的是契约与授权硬化（args_schema、invoke 校验、按 agent_type 可见集、Policy/租户叙述、评测负样本）**；**服务化 Registry、完整本体包、多 Agent 委派平台、灰度指标体系** 采纳为架构口径，用 ROADMAP 挂账，不在无写能力/无多团队注册前硬上代码。

---



## 1. A 档 · 采纳且建议本仓近期落地


| 意见来源  | 待改进摘要                               | 采纳？           | 本仓落地建议                                                                                                            | 优先级               |
| ----- | ----------------------------------- | ------------- | ----------------------------------------------------------------------------------------------------------------- | ----------------- |
| Q1    | 「注册中心」用词过大 → 应称进程内注册表               | **是**         | 文档/简历改口：Registry table，非 service；可迁移指内核无 LG，非跨进程发现                                                                | P0 口径             |
| Q1/Q3 | `args_schema` 缺省是契约空洞；invoke 前无参数校验 | **是**         | ① 默认 lookup 能力补最小 JSON Schema ② Gateway `invoke` 可选/强制校验（写能力强制）③ Supervisor tool 子任务从自由 `input` 升级为结构化 args（可分两波） | **P0**            |
| Q1    | 可见性全局、非按 Agent；`node_role` 占位       | **是（窄落地）**    | 先做 **agent_type / mode → allowlist 配置**（替代裸 `CANDIDATE_CAPABILITY_IDS=None`），不必上完整授权服务                            | **P0**            |
| Q2    | 灰度无进入/退出指标                          | **部分 → 评测语言** | 本仓无多 version 能力发布；把「金样门禁后通过率 / ontology 负样本拒答率」写成切流判据模板，挂 RAG/Host 切流文档                                           | P1 文档             |
| Q2    | 控制面挂时 fail-open vs fail-closed      | **是（写死口径）**   | 无独立控制面时：本地 Registry 即真源；若未来拉授权快照——**读可短期旧缓存，写/高危 fail-closed** 写入 Policy ROADMAP                                  | P1 SPEC           |
| Q3    | 业务不变量 vs 能力契约分层                     | **是**         | 编码规范：Gateway 只做 schema；业务规则不进 `args_schema`（即使暂无域服务，也不把涨跌幅写进能力 version）                                           | P0 纪律             |
| Q3    | 「一道闸」= 审批对象须已结构化                    | **是**         | 口径修正；若做 HITL，confirmation 绑定规范化 Intent 对象                                                                         | 随写能力              |
| Q3    | 审计串 plan→args→审批→执行；接 Langfuse      | **是**         | 扩展现有 span metadata：`capability_id`、args 摘要、policy、subtask_id；写路径预留 approval_id 字段                                 | P1                |
| Q4    | 委派 attenuation（只能降权）                | **采纳口径**      | 单 Supervisor 图内暂无真「子 Agent」；在 multi Agent ROADMAP 写死；本仓若只派 subtask，允许 list ⊆ 父 allowlist                          | P2 SPEC           |
| Q4    | confirmation 跨独立 run                | **采纳口径**      | 同上，随 TaskEnvelope；本仓无父子双 run 前不写码                                                                                 | P2                |
| Q4    | 并发子任务预算会计                           | **是（可薄做）**    | supervisor 已有 ≤4 subtasks；可加总步数/墙钟预算与「耗尽则 aggregate」——小改、利防幻觉循环                                                   | P1                |
| Q4    | acceptance 结构化                      | **是（薄）**      | AgentResult/聚合出口增加可选结构化字段；否则标注 subjective                                                                         | P2                |
| Q5/Q6 | 关系实例 SoR + 作用域下推 + fail-closed 缓存   | **部分**        | 本仓无多 Workspace 产品：对 Issue/PR lookup **强制会话用户/库范围**（已有 DB 范围则文档化）；RAG **检索前租户/语料集过滤**（若未来多租户）今日单租户则写「构造性单租户」       | P1 视多租户           |
| Q6    | 下推靠机制非自觉                            | **是**         | 能力注册增加 `tenant_scoped`（或等价）+ 单测断言「无租户谓词拒」；先覆盖默认 lookup/retrieve                                                   | **P0**（字段+测试）     |
| Q6    | 只读主收益是检索谓词；本体是纵深                    | **是**         | **先落地谓词/语料隔离**；本体 Package 不抢主路径                                                                                   | **P0 谓词 / P2 本体** |
| Q6    | SoR 增强读失败姿态                         | **是**         | 鉴权相关：resolve 失败 → deny；纯增强失败策略写进 Policy 注释                                                                        | P1                |
| Q7    | 无证据不发规范文档                           | **是**         | Harness/推行类文档流程：金样或试点页先于规范广播（过程纪律，可写进 coding_wiki）                                                                | P1 文档             |


---



## 2. B 档 · 采纳为架构口径，本仓缓做 / 只挂 ROADMAP


| 意见来源  | 待改进摘要                                     | 为何缓                              | 本仓动作                                                   |
| ----- | ----------------------------------------- | -------------------------------- | ------------------------------------------------------ |
| Q1    | owner/team、version、timeout、幂等、配额、SLA、发布状态 | 单产品、能力 <20，治理字段 ROI 低            | SPEC 增「平台字段预留表」；新能力注册逐步填 version/side_effect           |
| Q1/Q2 | 服务化 Registry、跨进程发现                        | 与「可迁移内核」不同；现网同进程足够               | 简历改口；ROADMAP 远期                                        |
| Q2    | 声明式授权策略语言（ABAC）                           | 无 3 团队 × 200 能力                  | 先配置化 allowlist；语言选型进 ROADMAP                           |
| Q2    | 变更风暴：推送+版本化快照                             | 无控制面扇出                           | 文档一句占位                                                 |
| Q4    | 完整多 Agent 注册/调用授权/类型队列隔离                  | 产品是 lg_rag supervisor，非 Agent 市场 | `02_agent_host_plan` / orchestration ROADMAP 吸收接缝      |
| Q4    | 跨 run Langfuse 根因（4 run 链）                | 无父子多 run                         | 现网强化单 trace 内 subtask 关联即可                             |
| Q5    | 完整 Ontology Package + 域 Owner 治理闸         | 无多域写、无 3 团队 OKR 冲突               | 面试方案保留；本仓最多 `docs/spec/.../ontology` 草案 + agent 负样本集骨架 |
| Q5    | ontology 评测 95%/样本量/功效                    | 先有负样本集再谈功效                       | `evals/agent/ontology` 骨架 + 小 N 起步                     |
| Q6    | GA 门禁绑 ontology + 自动降级 + 影子路径检测           | 过重；易逼出绕道且本仓无域发布矩阵                | **不**上自动降级；若做门禁只绑「高危能力须 schema+policy 测试」              |


---



## 3. C 档 · 部分采纳（修正后落地）


| 意见                     | 修正后立场                                                                            |
| ---------------------- | -------------------------------------------------------------------------------- |
| 「选谁」迁到结构化语义契约 / 本体论接选人 | **不采纳为选人主路径**（与 Mode A 一致）。采纳为：**catalog 机读标签 + 校验面**；选人仍 allowlist + Supervisor |
| 只读要落本体                 | **采纳「只读要封堵泄密」**；落点改为 **检索/lookup 谓词为主，本体不变量为纵深定义**                               |
| 治理靠发布闸换维护              | **采纳「机制 > 共识」**；本仓改为 **合并门禁（测试）**，不上「ontology 过期自动 deny」以免影子路径                   |


---



## 4. D 档 · 本仓明确不做或极远期


| 意见                          | 理由                    |
| --------------------------- | --------------------- |
| 把 Gateway 做成语义路由 / 本体选工具主路径 | 与已钉 Mode A 冲突         |
| 配置中心当契约真源                   | Q2 已正确否定，保持           |
| 完整 HITL 调价链 / 沙箱写池隔离        | 产品边界只读；除非新开写能力 task   |
| 多 Workspace 混存向量库的租户分片      | 当前语料模型非多租户 SaaS；有需求再开 |
| 业务域 Owner OKR 绑定自动降级        | 无多域治理对象               |


---



## 5. 建议落地顺序（若开 task）

```text
波次 α（契约硬化 · 对齐面试伤疤）
  1. 默认 capability 补 args_schema + invoke 校验开关
  2. tool 子任务结构化 args（或 parse input→schema）
  3. agent_type/mode → allowlist 配置（取代全局默认可视）
  4. tenant_scoped 声明 + lookup/retrieve 单测
  5. Langfuse metadata 补全（plan/tool/policy）

波次 β（编排预算与口径）
  6. supervisor 总预算（步数/墙钟）与耗尽行为
  7. 文档：注册表≠注册中心；控面降级；业务不变量分层
  8. 推行纪律：无证据不发规范（wiki）

波次 γ（平台预留 · 少码）
  9. CapabilitySpec 可选治理字段
  10. ontology / multi-agent attenuation / confirmation 跨 run → SPEC only
  11. evals/agent/ontology 负样本骨架（有租户后再加重）
```

**不建议**在无 HG/task 下直接改 `app/`；优先开一条 `task_capability_contract_hardening`（名自定）把 α 收进闸。

> **进度（2026-09-18）**：波次 α CLOSE · PR [#138](https://github.com/Cyning12/ops-desk-api/pull/138) MERGED。波次 β `task_supervisor_budget_h_beta` **00 CLOSE** · PR [#141](https://github.com/Cyning12/ops-desk-api/pull/141)（40 reverify PASS · pytest 41 · ~~待合入~~ **已 MERGED 2026-09-18** · merge commit `4896701`）。阶段 T：~~条件核对 NO-GO 30（缺第二租户试点数据）~~ **Fixture 轨已 CLOSE**：`f048c57` ∈ master（PR [#142](https://github.com/Cyning12/ops-desk-api/pull/142) · merge commit `8be477c` · 2026-09-18）· web PR #76 · 前置见 workspace `docs/05-plan/06_stage_t_second_tenant_prep_v0_zh.md`。W/P 未开。  
> 修订注记（2026-10-30）：PR #141 待合入 / 阶段 T NO-GO 30 两处为陈旧表述，已按磁盘实态（`git log 4896701` / `git branch --contains f048c57`）更正。

---



## 6. 简历 / 口述同步（立即做、零码）


| 改什么        | 怎么说                                          |
| ---------- | -------------------------------------------- |
| Agent Host | 「可迁移」= Capability/SO 内核不绑编排框架；**非**已上服务化注册中心 |
| 工具参数       | 承认早期自由文本；升级方向为 schema + invoke 校验            |
| 只读安全       | 强调作用域/谓词与机密性，不说「错了最多查空」除非已下推                 |
| 失败故事       | 继续用日期格式 RAG；推行教训改口为「无演示证据不发文档」               |


---



## 7. 决议表（一句话）


| 决议            | 内容                                         |
| ------------- | ------------------------------------------ |
| **采纳面试架构批评**  | 是——作为 Host 下一阶段真值，不辩解                      |
| **本仓立刻该做的**   | 契约校验、按类型可见集、作用域机制化、观测字段、预算、口径改词            |
| **本仓不该假装已做的** | 服务化 Registry、多 Agent 委派平台、完整本体治理、写路径 HITL  |
| **需要你拍板**     | ~~是否授权阶段 H~~ → **已授权 00 统筹**（见 `docs/harness/invokes/by-task/capability-contract-hardening/PROMPT_00_orchestrate.md`）；T/W 仍按 §8 串行、本波不做 |


---

## 8. 多租户 / 写能力：应插在哪一阶段

> **前提（维护者确认）**：产品线要加入多租户与写能力；当前路线尚无这两项。

### 8.1 推荐插入序（钉死）

```text
[现网] 只读单租户 · lg-rag + Host
    ↓
阶段 H · Host 契约硬化（波次 α）     ← 现在就该做；产品上仍可暂不宣传多租户/写
    ↓
阶段 T · 只读多租户（租户封闭）       ← 多租户先落在只读面
    ↓
阶段 W · 受控写能力（HITL + 沙箱）   ← 写能力最后开
    ↓
阶段 P · 平台项（按需）               ← 服务化 Registry / 本体治理 / 多 Agent 委派…
```

| 阶段 | 做什么 | 不做什么 | 进入条件 |
|------|--------|----------|----------|
| **H** | args_schema + invoke 校验；按 agent_type 可见集；`tenant_scoped` + 单测；观测串链；supervisor 预算 | 不开写；不宣称多租户 SaaS | **α+β 均已 CLOSE（2026-09-17）**；进入 T 条件：schema/allowlist/tenant_scoped 测绿 ✓；另须第二租户试点数据 |
| **T** | Principal↔Workspace；Issue/PR/Chunk 查询下推；RAG ANN 前语料/元数据过滤；跨租户负样本金样 | 不开放 write capability | H 的 schema/allowlist/tenant_scoped 测试绿；有第二租户试点数据 |
| **W** | 首条极窄写能力；结构化 Intent + confirmation + Policy；幂等与审计 | 不自动改码合 PR；不跳过 HITL | T 跨租户负样本门禁达标；审批与令牌设计签收 |
| **P** | 面试 B 档平台项 | — | 真出现多团队注册冲突再开 |

### 8.2 为什么是这个顺序

1. **写不能早于租户封闭**——无 T，写的爆炸半径是串租户改数；只读串租是泄密，写是破坏。
2. **租户紧接契约硬化**——无 H，多租户只是给自由文本加过滤；H→T 连续，T 不拖到「大平台做完」。
3. **与完善路线关系**——RAG 金样/水位可与 **H 并行**；**H→T→W 必须串行**。勿为简历跳过 T 直接 W。
4. **与迁移主线关系**——迁移 Phase 已完成；H/T/W 是上线后增强线，不回写已关闭 Week 表。

### 8.3 显式不建议的插入点

| 插入点 | 为何不合适 |
|--------|------------|
| 写与 H 并行首发 | 无契约/无租户的写 ≈ 客服 RAG 激进上线重演 |
| 多租户拖到服务化 Registry 之后 | 租户封闭不依赖注册中心 |
| 写 = 自动提 PR / 改码合并 | 属 Coding Agent 线，非本产品 |

### 8.4 一句话

> **阶段 H 波次 α 已 CLOSE 且合入**（PR #138）；**波次 β 已 CLOSE 且合入**（`task_supervisor_budget_h_beta` · PR [#141](https://github.com/Cyning12/ops-desk-api/pull/141) ~~待合入~~ **MERGED 2026-09-18** · merge commit `4896701`）；下一产品串行是阶段 T（只读多租户）→ W；~~T 的 30 仍阻塞于第二租户试点数据~~ **阶段 T Fixture 轨已 CLOSE**（`f048c57` ∈ master · PR [#142](https://github.com/Cyning12/ops-desk-api/pull/142) · merge commit `8be477c` · 2026-09-18 · web PR #76；前置清单见 workspace `06_stage_t_second_tenant_prep_v0_zh.md`）。  
> 修订注记（2026-10-30）：原「PR #141 待合入」「T 的 30 仍阻塞于第二租户试点数据」为陈旧表述，按磁盘实态更正（H β PR #141 已 MERGED；阶段 T Fixture 轨 CLOSE · `f048c57` ∈ master）。  
> **跨仓总 00**：`ops-desk-workspace/docs/harness/invokes/by-task/ops-desk-post-h-stage/` · 简报 `05_post_h_stage_brief_v1_zh.md`

---

## 修订

| 日期 | 说明 |
|------|------|
| 2026-09-17 | 首版：汇总 Q1–Q7 待改进 → A/B/C/D 与本仓落地序 |
| 2026-09-17 | §8：多租户/写能力插入阶段 H→T→W |
| 2026-09-17 | §5/§8：阶段 H α 竖切 CLOSE（`task_capability_contract_hardening`）；T/W/P 未开 · 00 代签过程 · 维护者令开启 |
| 2026-09-17 | §5/§8：阶段 H β CLOSE（`task_supervisor_budget_h_beta`）；T 仍 NO-GO 30（第二租户数据） |
| 2026-10-30 | §5 进度/§8.4：PR #141 已 MERGED 2026-09-18（merge commit `4896701`）；阶段 T Fixture 轨已 CLOSE（`f048c57` ∈ master · PR #142 · merge commit `8be477c` · 2026-09-18 · web PR #76）；陈旧「待合入」「NO-GO 30」表述更正（维护者变更请求 · 文档健康修复） |


