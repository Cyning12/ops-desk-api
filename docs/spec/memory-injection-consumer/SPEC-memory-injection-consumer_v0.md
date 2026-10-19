# SPEC：memory 注入消费者实证与处置（v0 · 先证后修）

> **状态**：`draft`（HG-SPEC-SIGNOFF=pending）
> **track**：`verify+feature`（Phase A 实证零改码 → Phase B 按实证结论二选一修复；不新增路由 / 表 / event_type）
> **上游**：2026-10-19 supervisor 全流程审核疑点 #2（高置信）：memory facts/episodes 注入进 `state.messages`，但 supervisor 链路疑似**没有任何节点消费它**
> **建议序**：**2/5**
> **现状锚点**：
> - 注入侧：facts `continuity.py:341-354`（`[已知事实]`/`[用户偏好]` 独立 SystemMessage 插前缀系统消息后）、episodes :483-514（`[相似经验]`）；开关 `MEMORY_FACTS_ENABLED` / `MEMORY_EPISODES_ENABLED` 均**默认关**；
> - 疑似无消费者：planner 只吃 query（`multi/nodes.py:1163-1170`）；aggregator 只吃 query+子任务结果（:2035-2043）；rag 工人子图输入隔离重建 fresh messages（:1432-1435，不传 history）；`_worker_state`（:1041-1063）虽带全量 messages 但 rag 工人内部不用；
> - **但** router/basic 模式主图直接吃 `state.messages`（direct_answer/rag 节点），注入在那两条链路**可能**有效——「零效果」疑似为 supervisor 模式特有。
> **下游**：20-spec-audit / HG-SPEC-SIGNOFF → 00 出 task → 20-task-audit → HG-AUDIT-R1 → 30
> **Open Folder（实现）**：`ops-desk-api/`

---

## Harness 元信息

| 字段 | 值 |
|---|---|
| **spec_slug** | `memory-injection-consumer` |
| **invoke_slug** | `memory-injection-consumer` |
| **test_strategy** | `required` |
| **test_strategy_note** | Phase A：spy LLM provider 断言各节点实际收到的消息清单（注入开 × 三模式矩阵）· Phase B 按结论：接线修复（注入进 planner/aggregator prompt）或按模式跳过注入（supervisor 不注入）· 全程默认关零 diff |
| **默认分支** | `task/memory-injection-consumer` |
| **graph_change_layer** | `none` 预期（Phase B 若选「接线进 prompt」也只改 prompt 组装，不增 event_type/路由/表；`01_modules.md` memory 行备注更新） |
| **freeze_id** | 无契约变更（SSE/HTTP 零动） |

### 人工闸（SPEC 阶段）

| human_gate_id | status | 说明 |
|---|---|---|
| **HG-SPEC-SIGNOFF** | **pending** | 待 20-spec-audit 或维护者人签 |

---

## 1. 背景与目标

V1-B 波次交付了 memory facts/episodes 注入（默认关），但审核发现：注入写进 `state.messages` 后，supervisor 链路的所有 LLM 消费点（planner / aggregator / rag 工人）**都不读 `state.messages`**。疑似「开关开了也零效果」——静默无效比没有更糟（运维以为有记忆增强，实际没有）。

**但疑似≠坐实**：需要先用 spy provider 实测三模式 × 开关矩阵，再决定修复方向。本 SPEC 强制「先证后修」，禁止跳过实证直接接线。

### 一句话目标

实证确认 memory 注入在三模式下的真实消费面；若 supervisor 零消费坐实，则二选一处置：**(a) 接线**（注入块进 planner/aggregator prompt）或 **(b) 收窄**（supervisor 模式跳过注入 + 文档写明）；处置结论由 Phase A 证据决定，不在本 SPEC 预设。

---

## 2. 范围

单 task（Phase A + Phase B 同 task 两阶段；Phase B 方向由 Phase A 证据触发，两条分支的实现方案都已在 §4 预写，30 不临场发明第三方案）。

### Phase A · 实证（零生产码改动）

| 项 | 约定 |
|---|---|
| 方法 | spy/fake LLM provider 记录每次 complete/complete_stream 收到的消息清单；注入开关开，造 facts/episodes 各 ≥2 条 |
| 矩阵 | `mode=basic / router / supervisor` × facts / episodes |
| 产出 | 实证表（哪个节点收到/没收到注入块）落 invoke；结论触发 Phase B 分支选择 |

### Phase B · 处置（二选一，由 Phase A 裁定）

| 分支 | 触发条件 | 内容 |
|---|---|---|
| **B-a 接线** | supervisor 零消费坐实，且产品判断「supervisor 应有记忆增强」 | planner system 尾部 + aggregator user 头部注入 `[已知事实]`/`[用户偏好]`/`[相似经验]` 块（复用 continuity 已产出的注入文本，不重复查询）；rag 工人**不**接（输入隔离是设计，另案） |
| **B-b 收窄** | supervisor 零消费坐实，且判断「本波不接」 | supervisor 模式跳过注入（省无谓查询与 token）；router/basic 维持；`01_modules.md` memory 行写明「supervisor 不消费」 |
| 实证推翻疑点 | 三模式均有消费者 | Phase B 整体不做，invoke 记录「疑点不成立」关 task |

---

## 3. 非范围

- ❌ 跳过 Phase A 直接接线（本 SPEC 核心纪律）
- ❌ 改注入文本格式 / 记忆召回排序 / 写入闸（memory-facts 系列 SPEC 的领域）
- ❌ rag 工人子图吃历史（输入隔离是既定设计，改动另立 SPEC）
- ❌ 开默认开关（所有记忆开关维持默认关）
- ❌ episodes 写路径接线（write_episode 全仓无生产调用方是另一疑点，另案）

---

## 4. 方案对比（R2 落盘）

| 方案 | 内容 | 裁定 |
|---|---|---|
| A 直接接线进 planner/aggregator | 不实测就改 | **弃**。若疑点不成立则白改；若 rag 才是正确消费点则接错位置 |
| B 直接收窄（supervisor 不注入） | 不实测就砍 | **弃**。同上，且可能砍掉 router/basic 已在吃的有效注入 |
| C 本 SPEC：先证后修 | Phase A 矩阵实证 → Phase B 二选一 | **采纳** |

---

## 5. failure_paths

| ID | 路径 | 期望 |
|---|---|---|
| FP-1 | 开关默认关 | 三模式零 diff（spy 断言无任何注入块） |
| FP-2 | 注入开 × supervisor | 实证记录每个 LLM 节点的消息清单；若 planner/aggregator 消息内无注入块 → 疑点坐实 |
| FP-3 | 注入开 × router/basic | 同上；若 direct_answer/rag 收到注入块 → 「零效果为 supervisor 特有」坐实 |
| FP-4 | B-a 接线后 | planner/aggregator prompt 含注入块；facts  revoked/为空时不出现空块标题 |
| FP-5 | B-b 收窄后 | supervisor 模式不再查询 facts/episodes（spy DB 断言）；router/basic 不变 |
| FP-6 | 实证推翻疑点 | 关 task，零生产码改动落盘 |

---

## 6. 验收

- [ ] Phase A 实证表落 invoke（三模式 × facts/episodes 全覆盖）
- [ ] Phase B 分支选择有 Phase A 证据引用（invoke 内写明「因 FP-x 选 B-a/B-b/关闭」）
- [ ] 若 B-a：金样断言 planner 与 aggregator 实际收到注入块；rag 工人不收到
- [ ] 若 B-b：supervisor 模式注入查询被跳过（零 DB 命中）；图谱 memory 行备注更新
- [ ] 全程默认关零 diff；pytest 绿；不增 event_type/路由/表

---

## 7. 风险

| 风险 | 缓解 |
|---|---|
| Phase A 被跳过或形式化 | SPEC 明文禁止；20-task-audit 核对 invoke 实证表 |
| B-a 接线后 prompt 膨胀 | 注入块已有长度纪律（窗 query+answer 各截 4000 先例）；块总量设上限（task 阶段定数值） |
| 「接线」与「收窄」争议 | 由维护者在 task 签收时按 Phase A 证据裁定，SPEC 不预设 |

回滚：B-a/B-b 均为开关默认关下的行为，回滚=恢复原注入路径。

---

## 8. 思考轮控制

| 轮 | 结论 | early_stop | reason | residual_risks |
|---|---|---|---|---|
| R0 | 疑点：supervisor 链路疑似无消费者 | no | | |
| R1 | 范围=实证 + 二选一处置；rag 输入隔离/写路径另案 | no | | |
| R2 | 采纳 C 先证后修；弃不实测直接改 | no | | 实证方法依赖 spy provider 可信度 |
| R3 | 三模式区分是裁定的关键证据 | no | | |
| R4 | spy provider 可全测；不打真模型 | no | | |
| R5 | draft 可交 20-spec-audit | no | 人签未发生 | HG-SPEC-SIGNOFF=pending |

`actual_last_round`：R5

### R0
审核会话疑点 #2 证据：planner :1163-1170 / aggregator :2035-2043 / rag :1432-1435 均不消费 `state.messages`。

### R1
成功=记忆注入消费面有实证台账；失败=不存在「开了开关零效果」的静默状态。

### R2
见 §4。实证先行是防「修错方向」的唯一手段。

### R3
不新增鉴权/闸链面；spy 只在测试。

### R4
`test_strategy=required`。

### R5
本文件不授权改 `app/`。下一棒：20-spec-audit 或维护者人签 → 00 起草 task。

---

## 9. 修订记录

| 日期 | 说明 |
|---|---|
| 2026-10-19 | v0 draft：supervisor 审核疑点 #2 落盘（先证后修 · B-a/B-b 双分支预写） |
