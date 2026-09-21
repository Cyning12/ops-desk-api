# SPEC：事实型记忆 P0（ops_memory_facts + 写入闸 + 确定性召回注入）（v1）

> **状态**：`signed`（HG-SPEC-SIGNOFF=**approved** · 2026-09-21 维护者签收）  
> **track**：`feature`（L4 上下文与记忆 · 长期语义记忆层的第一块）  
> **上游**：`../ops-desk-workspace/docs/08-interview/07_agent-memory-prompt-module-landscape_v1_zh.md` §1.5–§1.9（记忆四层拆分 + 最小方案 + 反模式）  
> **下游**：人签 SPEC → 00 出 task → 20-task-audit → HG-AUDIT-R1 人签 → 30 实现  
> **Open Folder（实现）**：`ops-desk-api/`

---

## Harness 元信息

| 字段 | 值 |
|---|---|
| **spec_slug** | `memory-facts-p0` |
| **invoke_slug** | `memory-facts-p0`（task 阶段） |
| **test_strategy** | `required` |
| **test_strategy_note** | 单测为主：写入闸判据 / supersede / revoke_by_source / 过期双保险 / 预算截断 / 开关关闭=现状回归；变异检验：写入→召回→撤销→消失全链路断言 |
| **Open Folder（实现）** | `ops-desk-api/` |
| **默认分支** | `task/memory-facts-p0`（自 `master` 分出；**禁止 master 直改**） |
| **graph_change_layer（建议）** | `G-L1`（新增一级模块 `memory`；task 阶段须在 `docs/_tech_graph/l1/01_modules.md` 由维护者签 `HG-GRAPH-MODULES` 新行后方可 30 改码） |

### 人工闸（SPEC 阶段）

| human_gate_id | status | 说明 |
|---|---|---|
| **HG-SPEC-SIGNOFF** | approved（2026-09-21 维护者） | 维护者签收本 SPEC 后方可 00 出 task / 30 改码 |

---

## 1. 背景与目标

### 现状

| 记忆层 | 现状 | 证据 |
|---|---|---|
| 工作记忆 | ✅ State + checkpointer（`LG_RAG_HTTP_CHECKPOINTER=postgres` 才走 PG） | `app/ops/lg_rag/checkpointer.py` |
| 会话记忆 | ⚠️ 截断+占位标记（**非摘要**）：最近 6 轮全量，更早替换为仅含轮数+角色的占位符 | `app/ops/lg_rag/continuity.py` |
| 长期语义记忆 | ❌ 语义层没有；✅ 基础设施齐备（Qdrant/pgvector 双后端 `RAG_VECTOR_BACKEND`、影子写+DLQ、p95 基准） | `app/ops/rag/backend.py` |
| 画像记忆 | ❌ 没有 | — |

**痛点**：跨会话零延续；「什么该记住 / 新旧冲突 / 记错纠正 / 怎么遗忘」四问无任何机制承接。而做记忆需要的存储与迁移基础设施已在知识检索线跑通——**缺的不是技术，是写入策略、冲突消解、遗忘机制**。

### 一句话目标

落**事实型记忆 P0**：一张 `ops_memory_facts` 表 + 写入闸纯函数 + 状态机（supersede / revoke / TTL）+ **确定性**召回注入（默认关），每条机制配一条**否定性断言**；**不碰向量召回、不做 LLM 抽取、不做画像**。

设计纪律（从上游文档继承，签收时锁死）：

1. **只记事实，不记对话**——事实可验证、可枚举、可删；对话摘要摘错是静默污染且不可回退。
2. **判据在写入时判，不在检索时筛**——写入时有上下文，检索时只有 query。
3. **不能自证的机制等于没装**——每条机制的验收都是一条可执行断言。

---

## 2. 范围

### D1 · 存储（必做）

新表 `ops_memory_facts`（alembic migration，upgrade/downgrade 可逆）：

| 列 | 类型 | 说明 |
|---|---|---|
| `id` | uuid PK | |
| `tenant_id` | text not null | 与 Principal 同源，**代码从 ctx 构造**（`app/ops/tenant_context.py` ContextVar），不取模型产出 |
| `user_id` | text not null | 主体隔离最小粒度 |
| `key` | text not null | 规范化事实键（如 `project.primary_repo`）；命名约定随本 SPEC 附带 |
| `value` | jsonb not null | 事实值（长度上限，见 §5） |
| `kind` | text not null default `fact` | P0 只接受 `fact`；`preference` 属画像，P1+ |
| `source_run_id` | text null | 溯源：产生该事实的 run（可空=人工/系统导入） |
| `source_turn` | int null | 溯源到轮次 |
| `supersedes` | uuid null FK→本表 | 显式声明取代哪条旧事实 |
| `status` | text not null default `active` | `active \| superseded \| revoked \| expired` |
| `expires_at` | timestamptz null | TTL；null=不过期 |
| `created_at` / `updated_at` | timestamptz not null | |

索引：`(tenant_id, user_id, key, status)`、`(source_run_id)`、`(expires_at)`（部分索引 WHERE status='active'）。  
**P0 不含 embedding 列**——向量召回是 P1，届时加列 + 复用 `RAG_VECTOR_BACKEND`。

### D2 · 写入闸与状态机（必做）

新一级模块 `app/ops/memory/`（service 层，**无对外 HTTP 写端点**）：

| 函数 | 职责 | 关键约定 |
|---|---|---|
| `should_write(candidate) -> Decision` | 写入闸**纯函数**：三条判据（可复用 / 稳定 / 与主体相关）落成显式规则 | 拒绝时返回原因码；**拒绝 = 不落库**，不是"存了不召回" |
| `write_fact(...)` | 过闸 → 落库；同 `(tenant_id, user_id, key)` 已有 active → 同事务置旧值 `superseded` + 新行 `supersedes` 指旧 id | 逻辑失效，**不物理删**（保审计对账） |
| `revoke_by_source(source_run_id)` | 按源头批量置 `revoked` | 纠错唯一入口；动作本身留审计日志 |
| `sweep_expired(now)` | 定期任务：`expires_at < now` 置 `expired` | **查询路径不依赖它**（见 §5 双保险） |

**P0 候选来源**：显式调用（service API / 测试驱动 / 后续 capability 接入）。**LLM 自动抽取是 P1**——在写入判据未被验证前，不让模型决定记什么。

### D3 · 确定性召回注入（必做 · 默认关）

| 项 | 约定 |
|---|---|
| env 开关 | `MEMORY_FACTS_ENABLED=false`（默认；关闭时消息装配与现网**逐字节一致**） |
| 召回方式 | **确定性**（无向量）：`(tenant_id, user_id)` 查 `status='active'` 且未过期，按 `updated_at desc` 取 top-N |
| 预算 | `MEMORY_FACTS_MAX_ITEMS`（默认 8）；超长按分数/时间**从尾部截断低优先级条目**，不随机截断 |
| 注入点 | `app/ops/lg_rag/continuity.py` 装配路径，系统消息**尾部独立块**（`[已知事实]` 标记），与指令正文分离、不掺入 prompt 模板 |
| 身份来源 | tenant/user 取自请求 ctx（对齐阶段 T：`X-Ops-Tenant-Id` 校验 + ContextVar），**模型产出不得参与身份构造** |
| 观测 | retrieve/装配 span metadata 记 `memory_facts_injected=N`；SSE/用户卡片**不输出**原始事实（对齐 rerank 分数纪律） |

### D4 · 评测与红线（必做）

单测（fake DB / 内存 repo）+ **否定性断言**：

1. 闸拒绝的候选**没落库**（查表为零，不是"存了没召回"）
2. 同 key 写新值：召回**只见新值**；旧值表内 `superseded` 仍可查
3. `revoke_by_source` 后召回**零命中**
4. 过期事实查询路径**查不到**（不依赖 sweep 已跑）
5. **变异检验**：写入错误事实 → 断言它确实出现在注入块（证明通路是通的）→ 撤销 → 断言消失；缺第一步则"撤销成功"是假通过
6. `MEMORY_FACTS_ENABLED=false` 回归：装配输出与现网一致

### D5 · 图谱与文档（必做）

- `docs/_tech_graph/l1/01_modules.md` 新增 `memory` 行（依赖方向 → `db`；被 `lg_rag` 装配路径消费）——**须维护者签 `HG-GRAPH-MODULES` 新行**
- `./scripts/graph-compile.sh` 通过
- key 命名约定短文（随模块 README）

---

## 3. 非范围

- ❌ 向量召回 / embedding 列 / 语义相似排序（**P1**，基础设施已就位，接入成本低）
- ❌ LLM 自动事实抽取（**P1**；判据未验证前不让模型决定记什么）
- ❌ 偏好型画像（`kind=preference`）；跨 Agent 共享策略（天然同库可读，无需本波设计）
- ❌ 对外 HTTP 写端点 / 运营后台 / 用户面记忆管理 UI
- ❌ 对话摘要（维持"截断+占位"现状，见上游 §1.2.2 纪律）
- ❌ 合规物理删除权（`status` 状态机已预留，物理删随合规需求另开）
- ❌ HITL 人工确认（记忆写是内部状态、可 revoke 回退，不产生对外副作用；与 capability 写操作的人闸语义不同）
- ❌ 改窗口压缩 / 改 checkpointer / 改对外 REST 契约

---

## 4. 方案对比（R2）

| 方案 | 做法 | 收益 | 代价 | 裁决 |
|---|---|---|---|---|
| **S1 · 事实表+写入闸+确定性召回（本 SPEC）** | PG 一表 + 纯函数闸 + key 级状态机 | 每条机制可自证；先解决最难的"什么该记住" | 无向量召回，覆盖靠 key 约定 | **推荐** |
| S2 · 直接上向量语义记忆 | 全量经历 embedding 入库 | 召回"看起来智能" | 写入判据未解决 → 噪声淹没；冲突/时效无解（相似度只懂像不像） | 置后 P1（事实层验证后接） |
| S3 · LLM 对话摘要存库 | 定期摘要历史 | 实现快 | 摘错=静默造错误前提且不可回退（§1.2.2） | 弃 |
| S4 · 共享黑板 / 全文历史注入 | 历史全塞 prompt | 零设计 | 成本随会话线性涨；依赖变隐式约定 | 弃 |
| S5 · 第三方记忆服务（mem0 类） | 托管记忆 | 省开发 | 溯源/删除权/红线评测不可控，合规风险 | 弃 |

---

## 5. 边界 / 失败路径 / 安全

| 触发 | 行为 | 可重试 |
|---|---|---|
| 写入闸拒绝 | 不落库 + 返回原因码 + 日志可观测 | — |
| 同 key 并发写 | 事务内 supersede；后写赢，旧值可审计 | — |
| revoke 不存在的 source | 影响行数=0，正常返回（幂等） | — |
| sweep 未运行/失败 | **查询路径仍按 `expires_at` 过滤**（过期不可见是双保险，不依赖任务存活） | Y |
| 跨 tenant 查询 | 所有 SQL 必带 `tenant_id` 谓词；跨 tenant = 空结果（对齐阶段 T 404 语义） | — |
| 记忆召回 DB 故障 | **降级为无记忆注入**（记忆是放大器非承重墙）：span 打 `memory_degraded`，不拖垮 chat | Y |
| 记忆写 DB 故障 | 报错不静默（写路径可重试，无半成功态） | Y |
| value 超长 / 含指令性文本 | 长度上限拒绝；注入独立块不参与指令拼装（对齐注入防护顺序：结构隔离优先于检测） | — |
| 模型在回答中自称"记得"某事但无记忆 | 红线用例：无记忆时不得幻觉用户偏好（离线金样，P1 接金样集） | — |

---

## 6. 验收标准

### 功能

- [ ] `MEMORY_FACTS_ENABLED=false`（默认）：lg_rag 装配输出与现网一致（回归单测）
- [ ] `=true`：active facts 注入系统消息尾部独立块；span 可见 `memory_facts_injected`
- [ ] §5 全部否定性断言通过（闸拒不落库 / supersede 旧值不出现 / revoke 零命中 / 过期查不到 / 变异检验全链路）
- [ ] 预算截断确定性：超限截断的是低优先级条目

### 工程

- [ ] ruff + pytest 绿；alembic upgrade/downgrade 可逆
- [ ] `memory` 模块入图谱（`01_modules.md` 新行 + `HG-GRAPH-MODULES` 维护者新签 + `graph-compile.sh` 通过）
- [ ] 新 env 全部有默认值且非法值回退+告警（对齐仓内 env 纪律）

---

## 7. 思考轮控制（10-spec）

| 轮 | 结论摘要 | 状态 |
|---|---|---|
| R0 | 上游=interview doc §1（四层拆分+四问+最小方案）；用户令「落盘 spec 开始升级」 | done |
| R1 | 范围=事实表+写入闸+确定性召回注入+红线；非范围=向量/LLM 抽取/画像/HTTP 写端点 | done |
| R2 | 推荐 S1；弃 S3 摘要（不可回退）/S4 黑板（隐式依赖）/S5 托管（不可审计）；S2 置后 P1 | done |
| R3 | 过期双保险；tenant 谓词强制；召回失败降级不拖垮 chat；注入独立块结构隔离 | done |
| R4 | 验收全为否定性断言 + 变异检验；默认关回归；不依赖 sweep 存活 | done |
| R5 | SPEC draft 可交人签 HG-SPEC-SIGNOFF；签后 00 出 task | done |
| early_stop | no | — |
| residual_risks | ① P0 无自动候选来源，实用性依赖 P1 抽取/显式接入（签收时知悉）；② key 命名约定需随首用例迭代；③ `MEMORY_FACTS_MAX_ITEMS` 默认值需实测调整 | 签收时知悉 |

---

## 8. 下一棒

1. ~~**维护者**：审本 SPEC → 签 `HG-SPEC-SIGNOFF=approved`~~ **done**（2026-09-21）
2. **00**：起草 `docs/tasks/active/task_memory_facts_p0.md`（含 `graph_change_layer=G-L1`、failure_paths、人工闸表）
3. **20-task-audit**：书面审 task → 维护者签 `HG-AUDIT-R1=approved`
4. **维护者**：`docs/_tech_graph/l1/01_modules.md` 签 `memory` 模块新行（`HG-GRAPH-MODULES`）
5. **30**：`task/memory-facts-p0` 分支实现 D1–D5

> **当前闸态（2026-09-21 核查）**：无 active task；`HG-AUDIT-R1`=pending（无 task 可签）；当前分支 `master`。**30 改码条件不满足，拒开工**——先走 1→4。

---

## 修订

| 日期 | 说明 |
|---|---|
| 2026-09-21 | 初稿（事实型记忆 P0；承接 interview doc §1.5–§1.9 最小方案与反模式清单） |
| 2026-09-21 | HG-SPEC-SIGNOFF=approved（维护者会话签收）；交 00 起草 task |
