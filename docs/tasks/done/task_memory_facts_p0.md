# Task：事实型记忆 P0（ops_memory_facts + 写入闸 + 确定性召回注入）

> **状态**：`done`（2026-09-21 闭环：三闸 approved · 30 M0–M5 交付 · 40 独立核验 PASS · 代码在 `task/memory-facts-p0` 分支 · **PR 待开**）  
> **类型**：feature / L4 记忆层  
> **上游 SPEC**：`docs/spec/memory-facts-p0/SPEC-memory-facts-p0_v1.md`（**signed** · HG-SPEC-SIGNOFF=approved 2026-09-21）  
> **分支**：`task/memory-facts-p0`（base：`master`；**禁止 master 直改**）  
> **00 注**：2026-09-21 · 维护者令「落盘 spec 开始升级」· SPEC 已签收 · 本 task 仅落稿；**30 开工前置 = HG-AUDIT-R1 approved + HG-GRAPH-MODULES 签 memory 新行 + 切任务分支**

---

## Harness 元信息

| 字段 | 值 |
|------|-----|
| **task_slug** | `memory-facts-p0` |
| **git_branch** | `task/memory-facts-p0` |
| **implement_repo** | `ops-desk-api` |
| **test_strategy** | `required` |
| **test_strategy_note** | 单测为主（fake DB / 内存 repo）：写入闸判据、supersede、revoke_by_source、过期双保险、预算截断、开关关闭=现状回归；变异检验：写入→召回→撤销→消失全链路；不连真外网 / 不连生产 Qdrant |
| **code_quality_bar** | `L2_backend` |
| **graph_change_layer** | `G-L1` |
| **graph_delta** | `docs/_tech_graph/l1/01_modules.md`（**新增一级模块 `memory`** 行）· 可选 flow 一句 |
| **graph_delta_note** | 新增 `memory`（`app/ops/memory/**` → `db`；被 `lg_rag` 装配路径消费）；**须维护者签 HG-GRAPH-MODULES 新行** |
| **wiki_delta** | `n/a` |
| **wiki_delta_note** | 契约真值在 SPEC `memory-facts-p0`；key 命名约定随模块 README |
| **review_hat** | `20` |
| **required_invoke_hats** | `10,20,30,40` |
| **invoke_retention_profile** | `default` |
| **experience_capture** | `recommended` |
| **kpi_aggregator** | `CLOSE` |
| **orchestration** | 10 落稿 → 20-task-audit 书面审 → 维护者签 HG-AUDIT-R1 + HG-GRAPH-MODULES 新行 → 30 → 40 |
| **freeze_id** | 无（不改 `lg-rag-sse-v1` / `lg-rag-http-v1`） |

### 人工闸

| human_gate_id | status | blocks_hats | 说明 |
|---------------|--------|-------------|------|
| HG-TASK-DRAFT | **approved** | 20-R1, 30 | 2026-09-21 维护者令起草 · SPEC 已签收 |
| HG-AUDIT-R1 | **approved** | **30** | 2026-09-21 维护者令「授权00签收后续过程文档，完成此task」· 00 代录（20-task-audit R2 终轮零阻塞已落盘 `docs/harness/reviews/`） |
| HG-GRAPH-MODULES | **approved** | **30** | 2026-09-21 维护者令同上 · 00 代录 · `01_modules.md` 已签 `memory` 新模块行 |

---

## 背景与目标

跨会话记忆零延续；「什么该记住 / 新旧冲突 / 记错纠正 / 怎么遗忘」四问无机制。向量基础设施（Qdrant/pgvector 双后端、影子写+DLQ、p95 基准）已在知识检索线跑通——**缺的不是技术，是写入策略、冲突消解、遗忘机制**（SPEC §1）。

本竖切交付**事实型记忆 P0**：一张 `ops_memory_facts` 表 + 写入闸纯函数 + 状态机（supersede / revoke / TTL）+ 确定性召回注入（默认关），每条机制配否定性断言。**不碰向量召回、不做 LLM 抽取、不做画像**（SPEC §2/§3 钉死）。

设计纪律（30 不得违反）：

1. **只记事实，不记对话**；2. **判据在写入时判，不在检索时筛**；3. **不能自证的机制等于没装**。

---

## 现状锚点（只读 · 30 必读 · 10 已扫）

| 主题 | 路径 · 锚点 | 现状缺口 |
|------|-------------|----------|
| ORM | `app/db/models.py`（`OpsRun` 等 13 表） | **无** memory 表 → 30 须 DDL + model |
| 迁移 | `alembic/versions/`（head `20260920_hitl_requests`） | 新 migration 接 head |
| 装配路径 | `app/ops/lg_rag/continuity.py`（窗口压缩 + LC 消息装配） | **无**记忆注入点；须尾部独立块且默认关零 diff |
| 租户上下文 | `app/ops/tenant_context.py`（ContextVar）· 阶段 T 头校验在 `lg_rag` 路由 | 身份必须取自 ctx，**禁止**模型产出参与 |
| 向量后端 | `app/ops/rag/backend.py`（`RAG_VECTOR_BACKEND`） | P0 **不接**；P1 复用 |
| env 纪律 | `app/ops/rag/grader.py:144`（未知值回退+告警） | 新 env 同纪律 |
| 观测 | `app/ops/tracing.py` · `app/ops/admin/capability.py` | span metadata 记注入条数；用户面不泄漏 |

---

## 钉死契约（自 SPEC §2/§5 锁死；30 不得静默改义）

| 项 | 钉死 |
|----|------|
| **表结构** | `ops_memory_facts`：id / tenant_id / user_id / key / value(jsonb) / kind(仅 `fact`) / source_run_id / source_turn / supersedes / status(`active\|superseded\|revoked\|expired`) / expires_at / created_at / updated_at；索引 `(tenant_id,user_id,key,status)` · `(source_run_id)` · `(expires_at)` 部分索引；**P0 无 embedding 列** |
| **开关** | `MEMORY_FACTS_ENABLED=false` 默认；**关闭时装配输出与现网逐字节一致** |
| **召回** | 确定性（无向量）：`(tenant_id,user_id)` + `status='active'` + 未过期，`updated_at desc` top-N；`MEMORY_FACTS_MAX_ITEMS` 默认 8；超限**截断低优先级**，不随机 |
| **注入** | 系统消息**尾部独立块**（`[已知事实]`），不掺入 prompt 模板 / 指令正文 |
| **身份** | tenant/user 取自请求 ctx（阶段 T：`X-Ops-Tenant-Id` 校验 + ContextVar） |
| **写入口径** | 闸拒绝=**不落库**（非"存了不召回"）；同 key 新值=事务内置旧 `superseded` + `supersedes` 指针；**不物理删** |
| **遗忘** | 过期不可见=**查询路径过滤 + sweep 双保险**（不依赖任务存活） |
| **故障语义** | 召回 DB 故障 → **降级无记忆注入** + span `memory_degraded`，不拖垮 chat；写故障 → 报错不静默 |
| **SSE/契约** | 零改 event_type；无新对外 HTTP 端点 |
| **候选来源** | P0 仅 service API 显式调用；**LLM 自动抽取禁止**（P1） |

---

## 范围（同 task 竖切）

- [x] **M0 · Schema**：`ops_memory_facts` model + alembic migration（upgrade/downgrade 可逆，接 head `20260920_hitl_requests`）
- [x] **M1 · 写入闸**：`should_write(candidate)` 纯函数（可复用 / 稳定 / 与主体相关三判据 + kind=fact + value 长度上限）；拒绝返回原因码
- [x] **M2 · 状态机 service**：`write_fact`（过闸 + 同事务 supersede）· `revoke_by_source`（批量 revoked + 审计日志）· `sweep_expired`
- [x] **M3 · 召回注入**：`continuity.py` 装配路径尾部独立块 + env 开关 + 预算截断 + span metadata；默认关零 diff
- [x] **M4 · 否定性断言 + 变异检验**：闸拒不落库 / supersede 旧值不召回 / revoke 零命中 / 过期查不到 / 写入→召回→撤销→消失 / 开关关闭回归
- [x] **M5 · 图谱**：`01_modules.md` 新增 `memory` 行 + `graph-compile.sh` 绿 + key 命名约定 README

**竖切结论**：M0–M4 同 task 必交；M5 随 30 一并（HG-GRAPH-MODULES 签行后）。

### 非范围

- 向量召回 / embedding 列 / LLM 事实抽取 / 偏好画像（P1）
- 对外 HTTP 写端点 / 运营后台 / 用户面 UI
- 对话摘要；改窗口压缩 / checkpointer / SSE freeze / 对外 REST 契约
- 合规物理删除权（状态机已预留）；HITL（内部状态可 revoke，无对外副作用）
- web / ios

---

## failure_paths

| 触发条件 | 系统行为 | 可重试 | 用户可见 |
|----------|----------|--------|----------|
| `HG-AUDIT-R1` / `HG-GRAPH-MODULES` pending 即 30 | **拒开工** | 是 | 是 |
| 写入闸拒绝候选 | 不落库 + 原因码 + 日志 | 是（修候选） | 否（service 层） |
| 同 key 并发写 | 事务内 supersede，后写赢，旧值可审计 | — | 否 |
| revoke 不存在 source | 影响 0 行，幂等返回 | — | 否 |
| sweep 未跑 / 失败 | 查询路径仍按 `expires_at` 过滤（双保险） | 是 | 否 |
| 跨 tenant 查询 | 必带 `tenant_id` 谓词；跨 tenant = 空结果 | 否 | 是（安全空） |
| 召回 DB 故障 | 降级无记忆注入 + `memory_degraded` span | 是 | 否 |
| 写 DB 故障 | 报错不静默，无半成功态 | 是 | 否 |
| value 超长 / 含指令性文本 | 闸拒绝；注入独立块不参与指令拼装 | 是 | 否 |
| 开关关闭但装配有 diff | 审查拒收（零 diff 回归） | 是 | 否 |
| 无变异检验却宣称红线有效 | 40/verify 拒收（假通过风险） | 是 | 否 |

---

## 验收标准

- [x] 人工闸：`HG-AUDIT-R1` · `HG-GRAPH-MODULES` 均 approved 后方可勾选下列码项
- [x] M0：migration upgrade/downgrade 可逆；`OpsMemoryFact` model 落 `app/db/models.py`
- [x] M1：闸三判据 + 长度上限单测绿；拒绝候选**查表为零**
- [x] M2：supersede / revoke_by_source / sweep 单测绿；旧值表内可查（审计）
- [x] M3：`MEMORY_FACTS_ENABLED=false` 装配输出与现网**逐字节一致**（回归单测）；`=true` 独立块注入 + 预算截断确定性 + span 记 `memory_facts_injected`
- [x] M4：五条否定性断言全绿 + **变异检验记录**（写入错误事实→确认污染注入块→撤销→确认消失）
- [x] M5：`01_modules.md` `memory` 行 + `./scripts/graph-compile.sh` 绿
- [x] **旧测 grep 影响面**（行为变更类 · 20 R1-B1 要求 · grep 已于 2026-09-21 代跑）：`continuity` 系 2 文件（`tests/test_session_continuity.py` · `tests/test_lg_rag_session_continuity.py`，默认关零 diff 直接守护）；`app.db.models` 系 14 文件（新增 model 纯增量）；`tenant_context` 系 2 文件（只复用不改义）；alembic / history 系 0 文件——30 须保持以上全绿
- [x] `ruff` 触及路径绿；`pytest` 本波相关 + 既有 lg_rag/session 回归绿
- [x] 新 env 非法值回退+告警（对齐仓内纪律）
- [x] `npx spec-wave task lint --file docs/tasks/active/task_memory_facts_p0.md` PASS

---

## 依赖

| 依赖 | 说明 |
|------|------|
| SPEC | `docs/spec/memory-facts-p0/SPEC-memory-facts-p0_v1.md`（signed） |
| 上游设计 | `../ops-desk-workspace/docs/08-interview/07_agent-memory-prompt-module-landscape_v1_zh.md` §1.5–§1.9 |
| 阶段 T（租户上下文） | `docs/tasks/done/task_tenant_readonly_predicate.md`（ctx / 头校验 / 谓词纪律直接复用） |
| 编码规范 | `docs/standards/CODING_BACKEND_L2_v1_zh.md` |
| 图谱 | `docs/_tech_graph/l1/01_modules.md`（HG-GRAPH-MODULES 真值） |

---

## 给执行帽的必读列表

1. `AGENTS.md`
2. 本 task（钉死契约 · 闸 · 非范围）
3. SPEC `docs/spec/memory-facts-p0/SPEC-memory-facts-p0_v1.md`
4. `docs/standards/CODING_BACKEND_L2_v1_zh.md`
5. 代码：`app/db/models.py` · `app/ops/lg_rag/continuity.py` · `app/ops/tenant_context.py` · `app/ops/tracing.py`
6. `docs/harness/prompts/FRAGMENT_30_gate_verify_v1_zh.md`

---

## 思考轮控制

| 轮 | 结论 | early_stop | reason（early_stop） | residual_risks |
|----|------|------------|----------------------|----------------|
| R0 | P0 = 事实表+闸+确定性召回； SPEC 已签收 | no | — | none |
| R1 | 30 硬阻塞于 HG-AUDIT-R1 + HG-GRAPH-MODULES 新行 | no | — | 闸未签前任何 app/ diff 违规 |
| R2 | M0–M4 同竖切；图谱随 30；SSE 零改 | no | — | 无 |
| R3 | 故障语义钉死：召回降级 / 写报错 / 过期双保险 | no | — | 无 |
| R4 | 验收全为否定性断言 + 变异检验 + 默认关零 diff | no | — | `MAX_ITEMS=8` 默认值需实测 |
| R5 | 可交 20-task-audit 书面审 | no | — | P0 无自动候选来源（SPEC residual ① 继承） |

**actual_last_round**：R5 · **early_stop**：no · **residual_risks**：见 R4/R5

### R0 · 问题框定

SPEC 已把"记忆"拆四层并钉死 P0 = 事实型最小方案；本 task 不重开设计，只把 SPEC §2/§5 落成可执行竖切。

### R1 · 开工闸

两个 30 阻塞闸（AUDIT-R1、GRAPH 新模块行）未签 → task 落稿但**拒 30**；GATE_VERIFY 以本表为真值。

### R2 · 竖切

Schema/闸/状态机/注入/断言同 task，避免"表落了没闸"或"闸落了没注入"的半截合入；图谱 G-L1 新模块随 30 一并无单独 task。

### R3 · 失败语义

记忆是放大器非承重墙：读路径任何故障都不得拖垮 chat（降级+标记）；写路径故障必须显式（不静默）。过期不可见做成查询路径双保险，不把正确性押在定时任务存活上。

### R4 · 可测性

每条机制的验收都是否定性断言（拒不落库/旧值不现/撤销零命中/过期查不到），外加变异检验防"永远为真的空规则"；默认关零 diff 回归防装配路径被静默改义。

### R5 · 交接就绪

思考充分，可交 20-task-audit；残余风险两项（默认值实测、无自动候选来源）已在 SPEC 签收时知悉。

---

### 自检结论（执行者）

> **hat 40** · 2026-09-21 · 独立核验（未复信 30 报告；实跑 + 亲读 diff）

| 命令 | 退出码 | 摘要 |
|------|--------|------|
| ruff check（app/ops/memory + 触及 8 文件 + 3 测试） | 0 | All checks passed |
| pytest tests/test_memory_{gate,injection,service_db}.py tests/test_session_continuity.py tests/test_lg_rag_session_continuity.py | 0 | 73 passed（service_db 7 条真 PG 无 skip） |
| pytest tests（全量） | 1 | 3 failed / 1066 passed / 1 skipped；3 失败=chat_ws×2+capability proxy×1，master worktree 同 env 复跑同失败（补齐 .env 后错误文案逐字一致）⇒ master 既有环境失败，与本波无关 |
| ./scripts/graph-compile.sh | 0 | 9 graphs 一致性 OK；graph.json 仅 generated_at diff 已还原 |
| alembic downgrade -1 && upgrade head | 0 / 0 | 20260921_memory_facts ↔ 20260920_hitl_requests 往返可逆 |
| npx spec-wave task lint --file docs/tasks/active/task_memory_facts_p0.md | 0 | LINT: PASS |

**验收摘要**：11 项全 PASS。否定性断言六条齐备且含真变异检验（先断言污染进注入块、revoke 后断言消失）；默认关逐字节回归对比消息类型+全文内容；身份 tenant=ContextVar/session、user=session 显式透传，无模型产出参与；recall 故障降级+memory_degraded、写故障上抛不静默；无新 HTTP 端点/embedding/LLM 抽取/HITL 改动；无新依赖；SSE 零改事件类型。

**已知未测项**：① span `memory_facts_injected` 元数据无专门单测断言（代码路径在，降级路径有测试）；② 全量 3 条失败为 master 既有环境相关（本机 .env/代理残留），30 报告漏报其中 capability proxy 1 条；③ 提交/PR 走后续流程。

**结论**：**40 PASS** · 无阻塞 · 可进 PR 流程

---

## 修订

| 日期 | 说明 |
|------|------|
| 2026-09-21 | 10-task 落稿 · R0–R5 全轮 · HG-AUDIT-R1/HG-GRAPH-MODULES pending → 30 拒开工 |
| 2026-09-21 | 20 R1 退回 B1（缺旧测 grep 影响面）→ 10-task 回填验收项（grep 结果随 R1 审查文） |
| 2026-09-21 | 20 R2 终轮零阻塞签收；维护者令「授权00签收后续过程文档，完成此task」→ HG-AUDIT-R1 / HG-GRAPH-MODULES 00 代录 approved · 图谱 memory 新行落 · 30 开工 |
| 2026-09-21 | 30 交付 M0–M5（未 commit 时报告）→ 40 独立核验 PASS（11/11）→ 00 回写勾选+自检结论 · 归档 done · CLOSE |
