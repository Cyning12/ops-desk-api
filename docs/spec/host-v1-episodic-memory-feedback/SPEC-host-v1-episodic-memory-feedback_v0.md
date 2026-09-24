# SPEC：Agent Host V1-D · 情景记忆 + 失败模式库（episodic-memory-feedback · 闸/库物理分离零互写）（v0）

> **层级**：L1 波次 SPEC（07 L0 规划的 V1-D 波 · 依赖 V1-A CLOSE · 可与 C 并行）  
> **状态**：`signed`（HG-SPEC-SIGNOFF=**approved** · 2026-09-23 · **00 代录** · 维护者令原话：「签收，并生成对此长程任务的00启动Prompt，新窗口执行，授权00签收所有过程文档，完整落地1.0版本内容」+ 本窗令「继续，完成后自行进行下一波，无特殊情况无需停下等待接收命令」）  
> **种子**：[`../agent-infra/08_host_v1_wave_spec_outlines_v0.md`](../agent-infra/08_host_v1_wave_spec_outlines_v0.md) §4（signed · 本 SPEC 为其正式展开，冲突以本 SPEC 为准）  
> **上游**：[`../agent-infra/07_host_v1_landing_plan_v0.md`](../agent-infra/07_host_v1_landing_plan_v0.md)（signed）· 大纲 v0.2 #9/#32/#33/#34（记忆分层/反馈闭环差距 · D3 Tier 2 语义）· [`../memory-facts-p0/SPEC-memory-facts-p0_v1.md`](../memory-facts-p0/SPEC-memory-facts-p0_v1.md)（signed · 事实记忆闸/状态机/注入先例）· `docs/tasks/done/task_host_v1_delegation_token.md`（V1-A · run 归因载体）  
> **下游**：HG-SPEC-SIGNOFF → 00 出 task → 20-task-audit → HG-AUDIT-R1 → 30（委派子 Agent · 分支 `task/host-v1-episodic-memory-feedback`）→ 40 → PR+CI 绿+merge → 图谱回写（00 代录）→ CLOSE  
> **Open Folder（实现）**：`ops-desk-api/`

---

## Harness 元信息

| 字段 | 值 |
|---|---|
| **spec_slug** | `host-v1-episodic-memory-feedback` |
| **invoke_slug** | `host-v1-episodic-memory-feedback`（task 阶段） |
| **test_strategy** | `required` |
| **test_strategy_note** | 零互写断言（episode 写不触 ops_memory_facts · fact 写不触 episodes · 跨表 SQL 守护）· 召回分节断言（`[相似经验]` 独立块 · off 零 diff）· 跨租户零召回断言 · 聚类报告断言（指纹规则 · 频次阈值）· 回写建议未确认零生效断言 · 默认关零 diff |
| **默认分支** | `task/host-v1-episodic-memory-feedback`（自 `master` 分出；**禁止 master/main 直改**） |
| **graph_change_layer** | `G-L1` 行备注（`memory` 行：情景记忆闸/库分离+召回分节+失败模式聚类 · `db` 行：登记新表 `ops_memory_episodes` · **有 alembic 义务**（本波唯一新表波 · off 态不读不写 drop 安全 · 承 session_summaries 先例）；HG-GRAPH-MODULES 随 30 回写 00 代录） |
| **freeze_id** | 无（不改 freeze 契约 · SSE 零新事件类型 · 零新路由） |

### 人工闸（SPEC 阶段）

| human_gate_id | status | 说明 |
|---|---|---|
| **HG-SPEC-SIGNOFF** | **approved**（2026-09-23 · 00 代录） | 维护者双令原话留痕（见状态行）；开放裁定 Q1/Q2/Q3 已答；00 可拆 task |

---

## 1. 背景与目标

### 现状与差距（承大纲 v0.2 #9/#32/#33/#34 + U4）

事实/偏好记忆已 stable（`memory/gate.py` should_write 写入闸 · `service.py` 状态机 supersede/revoke/TTL · `continuity.py` 注入分节 `[已知事实]`/`[用户偏好]` 默认关）；缺**情景记忆**（成功/失败模式沉淀 · 供规划参考）与**失败模式库→规则回写**。铁律：**与事实记忆闸/库物理分离 · 零互写**（U4）——经验≠事实：事实可验证可枚举；经验是模式归纳，判据、存储、召回全部分立。

### 关键实证（2026-09-23 本帽真读）

- **闸先例**：`gate.py:115-147` should_write 纯函数（任一不过即拒 · 调用方不得落库）——episode 闸物理不同函数。
- **注入先例**：`continuity.py:115-117/:212/:236` 单块双节 `[已知事实]`/`[用户偏好]` · `MEMORY_FACTS_ENABLED` 默认 false 非法回退（:128-136）· 召回失败降级不注入（:369）——`[相似经验]` 分节承同形态。
- **状态机先例**：`revoke_by_source` 一键纠错（记忆 P0）——episode 同款 revoke 面。
- **run 归因载体**：V1-A 令牌 subject_binding（tenant+user+run_id+subtask_id）+ `ops_lg_rag_run_events` 事件落盘——episode 归因与聚类输入齐备。
- **Tier 2 语义**（大纲 v0.2 D3）：episode 状态演进按事件可重放 · 确定性折叠设计（单进程实现预留 · v2.0 上楼零语义改动）。

### 一句话目标

情景记忆独立面：`ops_memory_episodes` 新表 + `should_write_episode` 独立闸（零互写）+ 规划期相似成功经验召回 `[相似经验]` 分节（默认关）+ 离线失败模式聚类（指纹规则）→ redlines/manifest **建议**（人工确认才生效 · 禁全自动）。

### 设计纪律（跨波公共约束继承 · 签收时锁死）

1. **闸/库物理分离（U4）**：episode 与事实记忆不同表、不同闸函数、不同召回路径；零互写断言化（任一向另一表写即挂）。
2. **默认关**：`MEMORY_EPISODES_ENABLED=false`（召回注入）· `MEMORY_EPISODES_WRITE_ENABLED=false`（写入 · 双开关独立灰度）；off 态不读不写 · drop 表安全（承 session_summaries 先例）。
3. **审计记动作不记内容**：episode 写/召回/聚类记动作与计数；plan 摘要/工具序列是结构元数据非用户内容（长度截断）；台账不含 query 原文。
4. **人工确认闸**：规则回写只产**建议**（报告/建议文件）· 人工确认后另行生效；禁全自动回写。
5. **租户隔离**：tenant 谓词承阶段 T 纪律（ContextVar · 模型产出不参与身份构造）；跨租户零召回断言。
6. **零 freeze 动**：不改 freeze 契约 · SSE 零新事件 · 零新路由；alembic 迁移 upgrade/downgrade 可逆。

---

## 2. 范围（D 块展开 · 承 08 §4.2）

### D1 · episode schema（必做 · Q1 裁定 run 级）

新表 `ops_memory_episodes`（alembic migration · upgrade/downgrade 可逆 · off 态不读不写 drop 安全）：

| 列 | 类型 | 说明 |
|---|---|---|
| `id` | uuid PK | |
| `tenant_id` | text not null | 代码从 ctx 构造（ContextVar · 承阶段 T）· 模型产出不得参与 |
| `run_id` | text not null | run 归因（V1-A 主体绑定同源）· 索引 |
| `task_domain` | text not null | 任务域（承 IntentV1 domain 词表 · unknown 允许） |
| `context_fingerprint` | text not null | 上下文指纹（确定性哈希：domain+意图特征+工具序列骨架 · 聚类键）· 索引 |
| `plan_summary` | text not null | plan 摘要（≤200 字符截断 · 承 MAX_VALUE_CHARS 先例） |
| `tool_sequence` | jsonb not null | 工具序列（capability id 数组 · 上限截断） |
| `outcome` | text not null | `success \| failure \| partial` 成败标签 |
| `failure_class` | text null | 失败分类（规则词表：`capability_blocked\|so_failure\|budget_exhausted\|upstream_error\|contract_violation\|other` · Q2 聚类键） |
| `status` | text not null default `active` | `active \| revoked`（承事实记忆逻辑失效不物理删） |
| `created_at` | timestamptz not null | |

索引：`(tenant_id, outcome, status)` · `(context_fingerprint)` · `(run_id)`。

### D2 · 独立写入闸（必做 · 物理分离）

`app/ops/memory/episode_gate.py` 新文件：`should_write_episode(candidate) -> Decision` 纯函数（与 `gate.py::should_write` **物理不同函数不同表**）。判据：① run 归因齐全（tenant+run_id 非空）② outcome 词表合法 ③ tool_sequence 上限（≤16 · 承 MAX_FIELDS）④ plan_summary 截断 ⑤ failure 时 failure_class 必填合法。拒绝=不落库（承「拒绝不是存了不召回」铁律）。

写入面 `app/ops/memory/episode_service.py`：`write_episode`（过闸才落库）· `revoke_by_run(run_id)`（承 revoke_by_source 先例 · 动作留审计日志记动作不记内容）。**零互写**：episode_service 不 import 事实记忆写面；SQL 守护断言。

### D3 · 召回注入（必做 · 默认关）

- `MEMORY_EPISODES_ENABLED=false` 默认关（关闭=装配逐字节零 diff · 承 MEMORY_FACTS_ENABLED 先例 :128-136 非法回退）。
- 召回（确定性）：同 tenant + `outcome=success` + `status=active` + context_fingerprint 匹配（当前意图 fingerprint 同规则计算）按 created_at desc 取 top-N。
- **预算**（Q3 裁定）：`MEMORY_EPISODES_MAX_ITEMS` 默认 3 · 单条 ≤200 字符 · 整块 ≤800 字符（承 step_contract MAX_CONTEXT_BLOCK_CHARS 先例）· 超限从尾部截断低优先级。
- 注入：装配面系统消息**独立分节** `[相似经验]`（与 `[已知事实]`/`[用户偏好]` 物理分节 · 承 continuity.py :115-117 先例）；召回失败降级不注入（承 :369 先例）；span `memory_episodes_injected=N`。

### D4 · 失败模式聚类（必做 · Q2 裁定指纹规则）

- **离线批处理**（scripts/ · 非热路径）：读 `ops_memory_episodes`（failure/partial）+ run_events 聚合 → **指纹规则聚类**（按 `failure_class` × `context_fingerprint` 分组计数 · 频次阈值 `EPISODE_PATTERN_MIN_COUNT` 默认 3）→ 模式库报告 `reports/episode_patterns/<date>.yaml`（承 backfill 报告先例）。
- embedding 聚类**弃选**（Q2 · v1 无可机验口径 · 指纹规则确定性可重放）。
- 报告字段族：`pattern_id/failure_class/fingerprint/count/sample_run_ids(≤5)/first_seen/last_seen/suggested_rule`。

### D5 · 规则回写建议（必做 · 人工确认闸）

- 高频模式（≥阈值）→ 生成 redlines/manifest **建议段**（报告内 `suggested_rule` 字段 · 文本建议非自动改动）；**人工确认后才可由人另行落地**（禁全自动回写 · 断言：本波代码零路径自动改 redlines/manifest）。
- 建议未确认零生效断言：聚类跑完后 redlines yaml 与 manifest 文件零 diff（git 守护断言）。

### D6 · 测试（必做）

1. **零互写断言**：write_episode 后 ops_memory_facts 零变化；write_fact 后 episodes 零变化；episode_service/gate 不 import 事实记忆写面（import 守护）
2. 闸断言：五判据逐条（缺归因/非法 outcome/超长序列/超长摘要/failure 缺 class 全拒不落库）
3. 召回分节断言：`[相似经验]` 独立块 · 与事实记忆块物理分节 · off 零 diff · 预算截断（条数/单条/整block）
4. 跨租户零召回断言（他 tenant episode 不可见）
5. 聚类报告断言：频次阈值 · 指纹分组确定性（同输入同报告 · 可重放）
6. 建议未确认零生效断言（redlines/manifest 零 diff）
7. revoke_by_run 断言（revoke 后召回零命中 · 表内仍可查）
8. off 态 drop 安全断言（表不存在时读写路径不炸 · 承 session_summaries 先例）
9. 迁移 upgrade/downgrade 可逆断言

---

## 3. 非范围

- ❌ D3 记忆跨进程同步（v2.0 · 三层并发机制本体在大纲 §6 D3 · 本波仅 Tier 2 语义设计输入）
- ❌ 自动规则回写（建议+人工确认 · 全自动禁）
- ❌ 实时聚类（离线批处理起步）
- ❌ 用户可见的记忆管理面 / 对外 HTTP 端点
- ❌ subtask 级 episode（Q1 裁定 run 级）
- ❌ embedding 聚类（Q2 裁定指纹规则）
- ❌ 改事实记忆闸/状态机/召回既有语义（零互写含零改）
- ❌ 改 freeze 契约 / 新 SSE 事件 / 新路由

---

## 4. 开放裁定（必答题 · 全部作答）

### Q1 · episode 粒度

| 方案 | 做法 | 裁决 |
|---|---|---|
| **S1 · run 级**（一 run 一 episode · 工具序列作字段） | 归因=run_id（V1-A 主体绑定同源） | **推荐（裁定）**：归因载体天然（run_events/令牌均以 run 为轴）· 写入频次低（每 run 最多 1 条）· 聚类噪声小 |
| S2 · subtask 级 | 每子任务一条 | 弃选：写入放大（一 run 多条）· 单 subtask 上下文不足以构成「经验」· 聚类噪声大 |

### Q2 · 聚类选型

| 方案 | 做法 | 裁决 |
|---|---|---|
| **S1 · 指纹规则**（failure_class × context_fingerprint 确定性分组 + 频次阈值） | 纯代码可重放 | **推荐（裁定）**：确定性可机验（同输入同报告）· 零新依赖 · 与 episode schema 的 failure_class/fingerprint 字段天然对位 |
| S2 · embedding 聚类 | 向量相似度分组 | 弃选：v1 无可机验口径（聚类质量无法断言）· 引入向量依赖 · 噪声不可复盘 |

### Q3 · 注入 token 预算占比上限

| 方案 | 做法 | 裁决 |
|---|---|---|
| **S1 · 条数+单条+整块三闸**（默认 3 条 · 单条 ≤200 字符 · 整块 ≤800 字符） | 承 step_contract 上下文块预算先例 | **推荐（裁定）**：三闸防累加污染（承「单值截断挡不住累加」教训 · step_contract :28-30）；整块 800 字符 ≈ 装配系统块的小个位数占比，远低 10% 上限 |
| S2 · 百分比动态预算 | 按装配总量比例 | 弃选：装配总量无运行时真值 · 动态预算不可机验 |

---

## 5. failure_paths（承 08 §4.4 · 全部正面裁定）

| # | 路径 | 裁定 |
|---|---|---|
| FP-1 | episode 污染（错误经验被召回放大） | 成败标签 + 只召回 success + `revoke_by_run` 纠错（承事实记忆先例）· 召回失败降级不注入 |
| FP-2 | 聚类噪声（低频偶发被当模式） | 频次阈值（默认 ≥3）+ 人工确认闸（D5 · 建议不自动生效）双保险 |
| FP-3 | 隐私/租户隔离 | tenant 谓词承阶段 T · 跨租户零召回断言 · 模型产出不参与身份构造 |
| FP-4 | 新表 alembic 义务 | upgrade/downgrade 可逆 · off 态不读不写 · drop 表读写路径不炸（承 session_summaries 先例 · 断言化） |
| FP-5 | 指纹碰撞（不同任务同 fingerprint 互相污染召回） | 指纹含 domain+意图特征+工具序列骨架三元 · 碰撞只召回 success 经验且条数上限 · 误判进台账可复盘（方向=宁可不召回） |
| FP-6 | 热路径写入放大（每 run 一条拖慢主答） | 写开关独立默认关 · 写入走 run 终态异步面（承 memory extract「热路径零抽取」先例 · run 后触发不挡主答） |
| FP-7 | 与事实记忆双写漂移（同一经验两表各写一份） | 零互写断言 + 抽取来源分立：episode 只从 run 终态结构化产物生成（不经 LLM 抽取 · 与事实记忆 LLM 抽取管道物理不同源） |

---

## 6. 验收标准（可机验）

1. 零互写断言通过（双向 · import 守护 + 表计数对拍）
2. 独立闸五判据逐条断言（拒绝=不落库）
3. 召回分节断言（`[相似经验]` 独立块 · off 零 diff · 三闸预算截断）
4. 跨租户零召回断言
5. 聚类报告产出且确定性可重放（同输入同报告）· 频次阈值断言
6. 建议未确认零生效断言（redlines/manifest 零 diff）
7. revoke_by_run 断言（召回零命中 · 表内可查）
8. off 态 drop 安全 + 迁移可逆断言
9. `pytest tests` 全绿 + `ruff check app tests` 净增 0
10. 图谱回写完成（memory/db 行 + HG-GRAPH-MODULES 00 代录）+ graph-compile 绿
11. PR 到 master 经 CI 绿后 merge

---

## 7. 思考轮回填（R0–R5）

- **R0（读人聊/目标）**：维护者令长程授权；08 §4 种子 + 事实记忆三 SPEC/任务链 + V1-A 归因载体真读毕。经验≠事实是本波第一性。
- **R1（范围/非范围）**：闸/库分离为边界（U4 铁律）；D1–D6 承种子展开；D3 跨进程/自动回写/实时聚类/用户面显式排除。
- **R2（方案对比）**：Q1 run 级（subtask 级弃——写入放大+噪声）· Q2 指纹规则（embedding 弃——不可机验）· Q3 三闸预算（动态百分比弃——无真值）；粒度与聚类各两案以上。
- **R3（边界/失败路径）**：FP-1~FP-7 全裁定；最锋利边界=污染放大防线（只召回 success+revoke+降级不注入三层）与双写漂移（零互写断言+来源分立）。
- **R4（验收/可测性）**：验收 11 条全可机验；零互写是变异检验式断言（任一向另表写→必挂）。
- **R5（签收就绪）**：alembic 义务确认（有 · off 态 drop 安全 · 可逆）；图谱义务定（memory/db 行备注）；可交 00 代录 HG-SPEC-SIGNOFF 后拆 task。

### 思考轮控制

| 轮 | 状态 | 说明 |
|---|---|---|
| R0 | done | 维护者令 + 07/08 §4 + 事实记忆面 + V1-A 归因已读 |
| R1 | done | 范围 D1–D6 / 非范围锁死 |
| R2 | done | Q1/Q2/Q3 ≥2 案对比 + 裁定 |
| R3 | done | FP-1~FP-7 裁定 |
| R4 | done | 验收 11 条 + test_strategy=required |
| R5 | done | 签收就绪 → 00 代录 HG-SPEC-SIGNOFF |
| early_stop | no | — |

---

## 8. 关联

- 规划/种子：[`../agent-infra/07_host_v1_landing_plan_v0.md`](../agent-infra/07_host_v1_landing_plan_v0.md) · [`../agent-infra/08_host_v1_wave_spec_outlines_v0.md`](../agent-infra/08_host_v1_wave_spec_outlines_v0.md) §4（双 signed）
- 事实记忆面：[`../memory-facts-p0/SPEC-memory-facts-p0_v1.md`](../memory-facts-p0/SPEC-memory-facts-p0_v1.md)（signed · 闸/状态机/注入先例）· `docs/tasks/done/task_memory_preference_profile.md`（分节注入先例）
- 前波：`docs/tasks/done/task_host_v1_delegation_token.md`（V1-A · run 归因）
- 代码锚点：`app/ops/memory/gate.py:115-147`（闸先例）· `app/ops/memory/service.py`（write/revoke 先例）· `app/ops/lg_rag/continuity.py:115-117/:212/:236/:369`（分节注入/降级先例）· `app/ops/lg_rag/multi/step_contract.py:23-30`（预算三闸先例）· `app/db/models.py`（OpsMemoryFact）
- 图谱：`docs/_tech_graph/l1/01_modules.md`（memory/db 行）

## 修订记录

| 日期 | 版本 | 内容 |
|---|---|---|
| 2026-09-23 | v0 | 10-spec 初稿：以 08 §4 种子展开 D1–D6；开放裁定 Q1（run 级）/Q2（指纹规则聚类）/Q3（条数+单条+整块三闸预算）全部作答；FP-1~FP-7 裁定；alembic 义务确认（有 · off 态 drop 安全）；R0–R5 回填 |
| 2026-09-23 | v0 | **00 代录 HG-SPEC-SIGNOFF=approved**（维护者双令原话留痕）；下一棒：00 起草 task（`docs/tasks/active/task_host_v1_episodic_memory_feedback.md`）→ 20-task-audit |
