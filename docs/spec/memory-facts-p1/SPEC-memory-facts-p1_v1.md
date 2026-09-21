# SPEC：事实型记忆 P1（向量语义召回 + LLM 候选抽取）（v1）

> **状态**：`signed`（HG-SPEC-SIGNOFF=**approved** · 2026-09-21 维护者签收）  
> **track**：`feature`（L4 记忆层 · 承接 P0）  
> **上游**：`docs/spec/memory-facts-p0/SPEC-memory-facts-p0_v1.md`（signed · 已实施 · PR #144）· `../ops-desk-workspace/docs/08-interview/07_agent-memory-prompt-module-landscape_v1_zh.md` §1.5（召回注入行）· §1.8（评测）  
> **下游**：人签 SPEC → 00 出 task → 20-task-audit → HG-AUDIT-R1 → 30 实现  
> **Open Folder（实现）**：`ops-desk-api/`

---

## Harness 元信息

| 字段 | 值 |
|---|---|
| **spec_slug** | `memory-facts-p1` |
| **invoke_slug** | `memory-facts-p1`（task 阶段） |
| **test_strategy** | `required` |
| **test_strategy_note** | 单测：向量召回混合排序/降级/开关关闭=P0 行为；抽取：候选全过闸 + 噪声拒写 + 失败零写入 + source_run_id 溯源；金样/红线：复述召回、噪声精度、热路径零抽取调用 |
| **Open Folder（实现）** | `ops-desk-api/` |
| **默认分支** | `task/memory-facts-p1`（base：`task/memory-facts-p0`——PR #144 未合则叠放，合入后 rebase `master`） |
| **graph_change_layer（建议）** | `G-L1`（`memory` 行备注更新：向量召回 + 抽取；**不新增**一级模块 · 依赖出边增 `rag`（embedder）与 `llm`（抽取）） |

### 人工闸（SPEC 阶段）

| human_gate_id | status | 说明 |
|---|---|---|
| **HG-SPEC-SIGNOFF** | approved（2026-09-21 维护者） | 维护者签收本 SPEC 后方可 00 出 task / 30 改码 |

---

## 1. 背景与目标

### 现状（P0 已交付 · PR #144）

| 能力 | 状态 |
|---|---|
| 事实存储 + 状态机 | ✅ `ops_memory_facts`（supersede / revoke / TTL 双保险） |
| 写入闸 | ✅ `should_write` 纯函数（7 稳定拒绝码） |
| 召回 | ⚠️ **仅确定性**：`(tenant,user)` active 未过期，`updated_at desc` top-N |
| 候选来源 | ⚠️ **仅显式调用**（service API / 测试）；无自动抽取 |

### 痛点

1. **语义盲区**：用户换种说法（"我主要在搞哪个仓" vs key `project.primary_repo`），确定性召回只能按时间全量 top-N，**找得到找不到全凭 key 约定覆盖**。
2. **写入靠喂**：P0 没有自动候选来源，记忆层实用性依赖人工/显式接入——SPEC-P0 residual_risk ① 签收时已知悉，本波解决。

### 一句话目标

在 **P0 机制（闸/状态机/双保险/默认关）一行不改语义** 的前提下，加两条默认关的增强：**① 向量语义召回**（复用现成 `Embedder` 与 `RAG_VECTOR_BACKEND` 基础设施）；**② LLM 候选抽取**（run 完成后离线产出候选，**全部过同一个写入闸**）。两条各自独立开关、独立降级。

设计纪律（沿用 P0，签收时锁死）：

1. **向量只解决"怎么召回"，不解决"该不该记"**——写入判据永远由闸在写入时判。
2. **抽取产物是候选，不是事实**——过不了闸的抽取 = 零写入，且**热路径零抽取调用**。
3. **每条增强可独立关闭，关闭后行为 = P0 现网**。

---

## 2. 范围

### D1 · 向量语义召回（必做 · 默认关）

| 项 | 约定 |
|---|---|
| env 开关 | `MEMORY_FACTS_VECTOR_RECALL_ENABLED=false`（默认；关闭时召回 = P0 确定性路径，**逐字节一致**） |
| 存储 | `ops_memory_facts` 加 `embedding` 列（vector · nullable · alembic migration；**P0 已留 P1 位**）；写入时嵌入（复用 `app/ops/rag/embedder.py` `Embedder` 协议 · 默认 SiliconFlow HTTP `ApiEmbedder`）；既有行 null embedding → 只走确定性通路，不回填（回填另开） |
| 召回融合 | 确定性 top-N（recency）∪ 向量 top-M（cosine）→ 去重 → 排序 = 向量相似 × 时间衰减 × 来源权重（用户明说 > 系统推断；来源字段 P0 已有 `source_run_id` 可空=人工/显式 → 权重高）→ 预算截断（沿用 `MEMORY_FACTS_MAX_ITEMS`，**截低分不随机**） |
| 注入面 | 不变（同一 `[已知事实]` 独立块 / 同一身份来源 / 同一降级语义） |
| 降级 | embedder / 向量查询失败 → **回退确定性召回** + span/log `memory_vector_degraded`，不拖垮 chat（对齐 P0 召回降级语义） |
| 异步纪律 | `Embedder.embed` 为同步协议 → 异步路径须线程卸载（对齐 rag 既有用法），禁止阻塞事件循环 |

### D2 · LLM 候选抽取（必做 · 默认关）

| 项 | 约定 |
|---|---|
| env 开关 | `MEMORY_FACTS_EXTRACT_ENABLED=false`（默认） |
| 触发点 | **run 完成后离线**（后台任务 / 非请求路径）；**热路径零抽取调用、零额外延迟** |
| 输入 | 该 run 的对话/结果摘要（**证据本体不进抽取 prompt**，对齐黑盒原则；只传必要文本窗） |
| 产出 | 候选列表 `FactCandidate` → **逐条过 `should_write`** → 过闸走 `write_fact`（同 P0 事务 supersede） |
| 溯源 | 抽取写入的事实 **必带** `source_run_id` + `source_turn`（`revoke_by_source` 一键全撤，P0 机制直接复用） |
| 失败语义 | 抽取 LLM 失败 / 输出非法 JSON / 超时 → **零写入** + log，不重试风暴（有限重试 ≤1）；绝不静默写入 |
| 结构化 | 抽取输出走 `structured_output` 管道（parse → repair → validate），不手撕 JSON |
| 成本 | 每 run 至多一次抽取调用；span 记 `memory_extract_candidates=N written=M` |

### D3 · 评测与红线（必做）

在 P0 六条否定断言之上新增：

1. **复述召回**：写入 `project.primary_repo=ops-desk-api`，用"我主要负责哪个仓库"类复述 query，断言向量通路召回该事实（fake embedder 确定性向量）
2. **抽取噪声拒写**：构造抽取产出 5 条（3 应拒：一次性/易失/非主体），断言拒写 3 条**查表为零**、过闸 2 条落库
3. **抽取失败零写入**：LLM 返回非法 JSON / 抛错 → 表行数不变
4. **热路径零抽取**：`MEMORY_FACTS_EXTRACT_ENABLED=true` 时请求路径 span **无**抽取 LLM 调用（抽取只发生在线程外/后台钩子）
5. **向量降级**：embedder 抛错 → 断言回退确定性结果 + `memory_vector_degraded` 标记
6. **开关关闭=P0**：两开关全关时装配输出与 P0 **逐字节一致**（复用 P0 回归测试结构）
7. **变异检验**：同 P0 思路——先断言错误事实经向量通路**真被复述 query 召回**，revoke 后断言消失

### D4 · 图谱与文档（必做）

- `docs/_tech_graph/l1/01_modules.md` `memory` 行备注更新（向量召回 + 抽取；依赖出边 + `rag` /`llm`）——**不新增一级模块**，但须维护者签 HG-GRAPH-MODULES 新行
- `app/ops/memory/README.md` 增 env 表两行 + 召回融合算法 + 抽取时序
- `./scripts/graph-compile.sh` 绿

---

## 3. 非范围

- ❌ 画像 / `kind=preference`（仍只 `fact`）
- ❌ 既有行 embedding 回填批处理（另开；本波 null embedding 走确定性通路即正确）
- ❌ 热路径抽取 / 实时写入 / 流中抽取
- ❌ 对外 HTTP 端点 / 运营后台 / 用户面 UI
- ❌ 跨用户/跨租户共享记忆（tenant 谓词纪律不变）
- ❌ 改 P0 闸判据语义 / 状态机语义 / 注入块格式（P0 行为是回归基线）
- ❌ A/B 分流 / 效果归因平台（Prompt 资产化路线的事，见上游 §2.4）
- ❌ 合规物理删除权（状态机已预留）
- ❌ web / ios

---

## 4. 方案对比（R2）

| 方案 | 做法 | 收益 | 代价 | 裁决 |
|---|---|---|---|---|
| **S1 · 混合召回 + 离线抽取（本 SPEC）** | 确定性 ∪ 向量融合；run 后离线抽取过闸 | 两条增强独立开关独立降级；闸语义零改 | 抽取引入新 LLM 调用面（已离线化+过闸对冲） | **推荐** |
| S2 · 纯向量替换确定性召回 | 全量走 embedding | 实现简单 | 向量只懂像不像不懂新不新（上游 §1.3）；recency 信号丢失 | 弃 |
| S3 · 热路径同步抽取 | 请求内抽取 | "记忆即时" | 延迟翻倍 + 新不确定性进热路径（违反上游 §1.8 纪律） | 弃 |
| S4 · 先回填全量 embedding 再上线 | 批处理回填 | 召回覆盖全 | 无新行为验证先行；回填可后补不阻塞 | 置后（另 task） |
| S5 · 引入 mem0 等托管记忆 | 外部服务 | 省开发 | 溯源/删除权/闸语义不可控（同 P0-S5） | 弃 |

---

## 5. 边界 / 失败路径 / 安全

| 触发 | 行为 | 可重试 |
|---|---|---|
| embedder 加载/调用失败 | 回退确定性召回 + `memory_vector_degraded` | Y |
| 向量列不存在（migration 未跑） | 启动/首次使用检测 → 回退确定性 + 明确 log（不炸请求） | Y（跑 migration） |
| 抽取 LLM 失败/超时/非法 JSON | 零写入 + log；有限重试 ≤1 | Y（下一 run） |
| 抽取产出全被闸拒 | 零写入（正常态，非错误）· span 记 candidates/written | — |
| 错误事实经抽取写入 | `revoke_by_source(run_id)` 一键全撤（P0 机制） | — |
| 跨 tenant 向量召回 | 向量查询**必带** tenant_id 谓词（与 P0 SQL 同纪律；跨 tenant=空） | — |
| 抽取 prompt 注入（run 内容含指令性文本） | 抽取输出只是候选 → 过闸（key 约定/长度/标量）+ 不参与指令拼装；结构化输出 validate 拦截畸形 | — |
| 抽取成本失控 | 每 run 至多 1 次调用；开关全局可关；span 计数 | — |
| 两开关全关 | 行为 = P0 现网逐字节一致 | — |

---

## 6. 验收标准

### 功能

- [ ] `MEMORY_FACTS_VECTOR_RECALL_ENABLED=true`：复述 query 经向量通路召回事实（fake embedder 确定性断言）；embedder 故障回退确定性 + 降级标记
- [ ] `MEMORY_FACTS_EXTRACT_ENABLED=true`：run 后离线抽取 → 候选全过闸 → 写入带 `source_run_id`；噪声候选查表为零；LLM 失败零写入
- [ ] 两开关全关：装配输出与 P0 现网**逐字节一致**
- [ ] 热路径零抽取调用（span 断言）
- [ ] 变异检验：错误事实经向量通路真被召回 → revoke → 消失

### 工程

- [ ] ruff + pytest 绿（本波 + P0 memory 回归 + lg_rag/session 回归）
- [ ] alembic upgrade/downgrade 可逆（embedding 列可增可删）
- [ ] 图谱 `memory` 行备注 + HG-GRAPH-MODULES 新签 + graph-compile 绿
- [ ] 新 env 非法值回退+告警；抽取走 structured_output 管道
- [ ] 旧测 grep 影响面项（20-task-audit checklist 沿用）

---

## 7. 思考轮控制（10-spec）

| 轮 | 结论摘要 | 状态 |
|---|---|---|
| R0 | P0 已闭环（PR #144 CI 绿）；P1 = SPEC-P0 residual ①（无自动候选）+ 召回语义盲区 | done |
| R1 | 范围=向量召回+离线抽取+红线+图谱备注；非范围=画像/回填/热路径抽取/HTTP 端点 | done |
| R2 | 推荐 S1 混合召回+离线抽取；弃 S2 纯向量（丢 recency）/S3 热路径抽取（延迟+不确定性）/S5 托管 | done |
| R3 | embedder 失败回退确定性；抽取失败零写入；注入威胁由闸+结构化 validate 对冲；tenant 谓词纪律延到向量查询 | done |
| R4 | 验收全为否定性/可执行断言；复述召回用 fake embedder 确定性化；热路径零抽取 span 断言 | done |
| R5 | SPEC draft 可交人签 HG-SPEC-SIGNOFF；签后 00 出 task | done |
| early_stop | no | — |
| residual_risks | ① 融合权重（相似×衰减×来源）初值需实测调参；② 抽取精度依赖金样迭代，首期可能保守（written 少）；③ 抽取每 run 一次调用的成本需按量评估 | 签收时知悉 |

---

## 8. 下一棒

1. ~~**维护者**：审本 SPEC → 签 `HG-SPEC-SIGNOFF=approved`~~ **done**（2026-09-21）
2. ~~**维护者**：合并 PR #144~~ **done**（2026-09-21 · master 已含 P0）
3. **00**：起草 `docs/tasks/active/task_memory_facts_p1.md`
4. **20-task-audit**：书面审 → 维护者签 `HG-AUDIT-R1` + 图谱 `memory` 行新签
5. **30**：`task/memory-facts-p1` 分支实现 D1–D4

---

## 修订

| 日期 | 说明 |
|---|---|
| 2026-09-21 | 初稿（向量语义召回 + LLM 离线候选抽取；承接 P0 residual ① 与召回语义盲区） |
| 2026-09-21 | HG-SPEC-SIGNOFF=approved（维护者「签收」）；PR #144 已合并 · 交 00 起草 task |
