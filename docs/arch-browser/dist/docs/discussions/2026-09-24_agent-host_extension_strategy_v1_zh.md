# 2026-09-24 · Agent Host 扩展策略（名实分离 · 扩展轴 · 高 ROI 能力）

> **状态**：讨论稿 v1 · **非 freeze** · 只思考可落地方向，**不**直接授权 30  
> **上游**：  
> - [完整框架大纲](./2026-09-23_agent-host-full-framework-outline_v0.md)  
> - [当前总架构对照](./2026-09-24_agent-host_current_architecture_v1_zh.md)  
> - [多服务工程方案](./2026-09-23_agent-host-multi-service-engineering-architecture_v0.md)  
> - 出口复核：V1-A~E + SLI G1 CLOSE  
> **立项动机**：主线代码/契约仍叫 `lg-rag`，实质已是进程内 Agent Host；扩展须按 Host 叙事，而非「继续做简单 RAG」。

---

## 1. 名实分离（先改说法，慎改路径）

| 层 | 建议 |
|---|---|
| **叙事 / 图谱 / 文档** | 主线 = **Agent Host**；写明「执行入口/传输契约仍为 lg-rag」 |
| **HTTP / freeze** | **短期保留** `/api/ops/lg-rag/*` 与 `lg-rag-sse-v1`（改路径=新 freeze + 全客户端） |
| **代码包** | **不急**重命名 `app/ops/lg_rag`；若迁名须单列 SPEC，不与功能波绑死 |
| **心智模型** | `lg_rag` = **执行面装配壳**（图 + SSE + run_events）；控制面在 `capability` / `strategy` / `hitl` / `memory` / `llm` |

**原则**：壳稳定（拓扑 + freeze）；脑与手可换（模型档、能力集、工人类型）。

---

## 2. 三条扩展轴（勿混成一条）

```text
轴 A · 功能深化（进程内）     ← 大纲「部分」15 项 · 近中期主战场
轴 B · 域能力扩展（manifest） ← 低成本、高业务杠杆 · 本文 §4 重点
轴 C · 部署拆分（v2.0）       ← 触发条件驱动 · 不为拆而拆
```

```text
                    ┌─ 新 capability（manifest）← 首选扩展面
用户 ─SSE(/lg-rag)─►│ 执行面壳 lg_rag
                    │    ├─ Orchestrator（规划/令牌/scope）
                    │    └─ Specialists（RAG | extract | tools | …可增）
                    ├─ 控制面（可见集/SO/Policy/HITL/记忆）← 深化「部分」
                    └─ LLM 工厂（档/预算/缓存/降级）← 换脑不换壳
```

---

## 3. 近中期波次建议（N0–N5）

| 波次 | 主题 | 码量感 | 说明 |
|---|---|---|---|
| **N0 叙事** | 文档/图谱「主线=Host；lg-rag=执行入口」；可选 ADR 保留包名理由 | 零/低码 | 防团队按 RAG 路线图排期 |
| **N1 能力** | 接入 1～N 个高 ROI ops 能力（见 §4） | 中（多为 local_fn + manifest） | **业务可见最快** |
| **N2 治理** | HITL 三档 **或** 统一审计台账（二选一先做） | 中高 | Host 完整度 |
| **N3 工人** | 如 rerank / 新 specialist 一类 | 中 | 执行面变强；RAG 仍是工人不是产品名 |
| **N4 工厂** | 能力标签路由 **或** 输出侧过滤 | 中 | 质量与安全 |
| **N5 v2.0** | 控制面服务化等 | 高 | 仅触发条件满足 |

### 反模式（明确不做）

| 反模式 | 原因 |
|---|---|
| 再立第二主线图并行 `lg_rag` | 分裂闸链与会话 |
| 为「不像 RAG」急改 URL/包名 | freeze 成本 ≫ 心智收益 |
| 未观测就默认 enforce 新闸 | 违背 v1.0 纪律 |
| 无触发条件上微服务 | 违反工程方案 |
| 模型可选「自验 SO/Policy」 | 破坏 Host 权威 |

---

## 4. 能力接入：什么样的 ROI 较高

### 4.1 ROI 公式（本仓实用定义）

```text
ROI ≈ (用户可感知价值 × 调用频次 × 可断言性)
      / (接入成本 × 风险面 × 运维耦合)
```

| 因子 | 高分条件 | 低分条件 |
|---|---|---|
| **用户可感知价值** | 直接回答「查/比/摘要本域对象」 | 纯内部探针、仅开发者用 |
| **调用频次** | supervisor 规划常选中 | 极冷门、需复杂前置 |
| **可断言性** | 有稳定 schema、租户谓词、可单测 | 依赖外网抖动、输出不可验 |
| **接入成本** | 已有 DB/service 函数可包成 `local_fn` | 新微服务、新 OAuth、新协议栈 |
| **风险面** | `side_effect=read` · 低 risk · 默认可自动签发令牌 | 写/不可逆 · 必 HITL · 涉密外发 |
| **运维耦合** | 同进程、同 PG、无新密钥面 | 第三方 SLA、密钥轮换、配额计费 |

**一句话**：优先 **只读 · 本域数据已在仓 · schema 清晰 · 规划器容易选对** 的能力。

### 4.2 现状锚点（避免重复造轮）

已有本域等价物（应 **复用/补全目录**，而非平行再造）：

| 已有 | 形态 | 启示 |
|---|---|---|
| issue/PR **按号 lookup** | `lookups.py` · tenant 谓词 | 「主键精确读」ROI 已验证 |
| `harness.*` CLI | 白名单 · Policy 默认关 | 治理向能力要双键，不进业务默认目录 |
| `task_writer` | 受控写盘 | **写路径贵**：闸/HITL/审计成本高 |
| RAG / evidence | 工人而非 capability 目录主体 | 检索继续当 Specialist，不必硬塞成 tool 名单膨胀 |
| builtin manifest | 少量 local_fn 只读 | 目录仍薄 → **N1 空间大** |

大纲已排除：admin sync 旧业务主叙事、报警/车控垂域——**不作为 N1 ROI 主候选**（除非产品显式改范围）。

### 4.3 高 ROI 能力画像（推荐优先）

按「先做」排序：

#### S 级（建议 N1 首批）

| 类型 | 例（示意 id） | 为何高 ROI |
|---|---|---|
| **本域实体精确读** | `ops.issue.get` / `ops.pr.get`（已有可补列表/搜索） | 频次高、只读、租户隔离已有、易断言 |
| **本域列表/过滤读** | `ops.issue.list_by_label` · `ops.pr.list_open` | 补「按号」之外的规划入口；仍只读 |
| **会话/跑批只读诊断** | `ops.run.get_events_summary` · `ops.thread.get_recent_turns` | 让 Agent 解释「刚才发生了什么」；数据已在 `run_events`/threads |
| **观测只读切片** | `ops.llm.usage_for_run` · capability 调用摘要（若 admin 面可下沉为 capability） | 支撑 Cost/命中率叙事；只读账本 |

#### A 级（N1 后半 / N2 并行）

| 类型 | 例 | 条件 |
|---|---|---|
| **受控只读外联** | 固定白名单 HTTP GET（文档/状态页） | 必须：超时、体积上限、禁止跟随任意 URL、默认 Policy blocked 或高 risk |
| **记忆只读查询** | `ops.memory.list_facts_for_user`（承既有 service） | 默认关开关对齐；禁止跨租户；审计记动作不记内容 |
| **幂等轻写** | 标签追加、草稿状态（若产品要） | 必须：幂等键 + HITL 或 PRE_AUTHORIZED + 可撤销字段 |

#### B 级 / 暂缓（ROI 常被高估）

| 类型 | 原因 |
|---|---|
| 通用「随便调外部 API」工具 | 风险面大、难断言、可见集难裁 |
| Shell / 任意代码执行 | 永久高危；与 harness 白名单哲学冲突 |
| 未收敛的 MCP 全量目录 | 默认关合理；全开=目录污染 + 策略难写 |
| 重写类（直接改生产工单/合入 PR） | HITL/撤销/审计成本 ≫ 首版演示收益 |
| 报警/车控等大纲排除域 | 范围外；拉回需改产品边界 |
| 「再包一层 RAG 检索 capability」 | 与 `rag_subtask` 双通道；易让规划器重复选 |

### 4.4 接入成本分级（估工）

| 档 | 内容 | 典型成本 |
|---|---|---|
| **L1** | 已有 async 函数 → `local_fn` + manifest 四字段 + 单测 | 0.5–2 人日 |
| **L2** | 薄封装 + args_schema + tenant 谓词补齐 + 目录/红线 | 2–5 人日 |
| **L3** | 新写路径 / 外网 / HITL 新语义 | 1 周+，且常挡在 N2 治理之后 |

**N1 纪律**：默认只接 **L1/L2 + side_effect=read**；写能力单列 task，不塞进「目录冲量」。

### 4.5 验收口径（每个新能力最小集）

- [ ] manifest：`risk_level` / `side_effect` / 可撤销四字段齐全  
- [ ] `args_schema` 可被 FC 暴露（或显式不暴露的理由）  
- [ ] 跨租户负例断言（阶段 T）  
- [ ] 默认目录策略：业务默认可规划 vs 双键才开（对齐 harness 先例）  
- [ ] 委派：只读自动签发路径可测；写则 HITL 台账可测  
- [ ] 观测：至少 `capability_id` + `ok` span；剔除/拦截有 reason 码  

### 4.6 首批候选清单（可直接开 task 时裁剪）

> 下列为 **方向名**，正式 id 以 manifest 词表为准；实施前用 `npx spec-wave` 开 task，勿在讨论稿里假装已实现。

| 优先级 | 候选方向 | 依赖数据 | 预估档 |
|---|---|---|---|
| P0 | Issue/PR **列表与简单过滤**（补强按号 lookup） | 已有 sync/库表 | L1–L2 |
| P0 | **Run/Thread 只读摘要**（给用户解释进度与失败） | `run_events` / threads | L2 |
| P1 | **Usage/Cost 只读按 run** | `ops_llm_usage` | L1–L2 |
| P1 | **记忆事实只读列表**（默认关） | `ops_memory_facts` | L2 |
| P2 | 白名单只读 HTTP（文档/状态） | 新适配器 | L2–L3 |
| P2 | 一条幂等轻写（产品点名再开） | HITL 分级更稳后 | L3 |

---

## 5. 与架构对照文档的衔接

| 文档 | 关系 |
|---|---|
| [当前总架构对照](./2026-09-24_agent-host_current_architecture_v1_zh.md) | 「现在有什么 / 缺什么」 |
| **本文** | 「下一步怎么扩 / 先接什么能力」 |
| [分模块 M01–M34](./agent-host-current-architecture/) | 单模块内部结构 |
| 工程方案 P0–P3 | 轴 C 触发条件 |

---

## 6. 修订

| 日期 | 说明 |
|---|---|
| 2026-09-24 | 初版：名实分离 · 三轴 · N0–N5 · 高 ROI 能力画像与首批候选 |
