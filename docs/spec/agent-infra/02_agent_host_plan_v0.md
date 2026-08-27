# Agent Host · 初版 SPEC 规划（v0）

> **层级**：L0 规划（Gateway 升级轨收官后的 **架构 flesh** 轨）  
> **状态**：`completed`（规划真值 · HG-SPEC-SIGNOFF **approved** · **H1–H5 全轨 CLOSE** · 2026-08-27）  
> **版本**：v0 · 2026-08-27  
> **上游**：[`00_architecture_and_boundaries.md`](./00_architecture_and_boundaries.md) · [讨论阶段性总结](../../discussions/2026-08-26_agent-host-architecture-phase-summary.md)  
> **前置轨**：[`01_upgrade_roadmap.md`](./01_upgrade_roadmap.md)（**stable** · Capability portable + SO 卫生 + MCP）  
> **Open Folder**：`ops-desk-api/`

---

## Harness 元信息

| 字段 | 值 |
|---|---|
| **plan_slug** | `agent-host-plan` |
| **invoke_slug** | `agent-host-plan`（00 统筹启用后） |
| **test_strategy** | `required`（按子波次裁剪） |
| **test_strategy_note** | mock 单测为主；H3 触 chat DB/SSE；H2 sandbox 默认关、CI 零外网 |
| **graph_change_layer（建议）** | 多为 `G-L1`（`lg_rag` / 可选 `chat` 备注）；H4/H5 可能 n/a |
| **freeze_id** | 无新业务 HTTP freeze（沿用 lg-rag-http-v1） |
| **默认分支（建议）** | `task/agent-host-<wave-slug>` |

### 人工闸（SPEC 阶段）

| human_gate_id | status | 说明 |
|---|---|---|
| **HG-SPEC-SIGNOFF** | approved | 2026-08-27 维护者会话签收；00 已拆 H1–H5 task |

---

## 1. 背景与目标

### 背景

- **Gateway 轨已 stable**：Capability（P0–P3 + portable + MCP）、Structured Output（P0–P3 + schema 卫生）契约与实现已落地。  
- **架构 flesh 缺口**：讨论结论中的 Host 六模块里，**编排↔赋能闭环**、**Policy**、**Session**、**PromptAssembly**、**SkillRegistry** 仍缺或未接实。  
- **本仓首选接入面**：`lg_rag` supervisor（静态图 + 动态 plan）；Chat 多轮为 H3 产品向波次。

### 一句话目标

在 **不推翻** 既有 Gateway 契约的前提下，按波次把 **Agent Host 运行时模块** 从「散落在 lg_rag 节点」收敛为可描述、可测、可迁移的装配面；优先 **supervisor 读赋能列表并校验 plan**。

### 非目标（本规划全轨）

- 重写 Capability / SO 内核  
- 动态 StateGraph compile  
- 模型可选「校验 tool」  
- 完整 Skill 执行引擎  
- 生产级无限制 sandbox / 默认 CI 外网  
- 改 `chat/graph.py` 拓扑（H3 仅会话/消息/SSE 衔接，不动主图拓扑）  
- OWL 本体入库  
- Agently 运行时依赖  

---

## 2. 模块地图与现状

| Host 模块 | 本仓包/落点 | 现状 | 本规划波次 |
|---|---|---|---|
| OrchestrationShell | `app/ops/lg_rag/` | 三图 + supervisor 已有 | **H1** 接 Capability 目录 |
| CapabilityGateway | `app/ops/capability/` | stable | **H1** 消费侧；**H2** Policy |
| StructuredOutputGateway | `app/ops/structured_output/` | stable | 继承；H1 plan 仍 `parse_only` |
| ControlPlane · Policy | （缺独立包） | `risk_level` 字段；invoke 前弱 | **H2** |
| ControlPlane · 观测 | `app/ops/tracing.py` | Langfuse 已有 | 各波次沿用 |
| SessionContinuity | `app/ops/chat/` + checkpointer | DB session 有；压缩/断点弱 | **H3** |
| PromptAssembly | （缺） | 节点硬编码 system | **H4** |
| SkillRegistry | `docs/skills` + `kind=skill` stub | 人读为主；无 NL 匹配 | **H5** |

```text
已完成（01 轨）          本规划（02 轨）
Capability ──┐
SO ──────────┼──► H1 编排闭环 ──► H2 Policy ──► H3 Session ──► H4 Prompt ──► H5 Skill
lg_rag ──────┘
```

---

## 3. 执行波次总表

| 序 | 波次 ID | 域夹 | 内容摘要 | 建议 task slug | 详规 |
|---|---|---|---|---|---|
| **H1** | `host-orchestration-catalog` | [`orchestration/`](./orchestration/) | supervisor `list_capabilities` → prompt；plan 校验 tool id；低危真实 capability 样例 | `lg-rag-supervisor-capability-catalog` | [ROADMAP](./orchestration/ROADMAP_supervisor_capability_catalog_v0.md) |
| **H2** | `host-capability-policy` | [`capability/`](./capability/) | invoke 前 Policy 门；sandbox/cli/code 注册 + env 默认关 | `capability-policy-sandbox` | [ROADMAP](./capability/ROADMAP_policy_and_sandbox_v0.md) |
| **H3** | `host-session-continuity` | [`session/`](./session/) | Chat 消息持久化、窗口压缩策略、SSE 游标/replay 设计 | `chat-session-continuity` | [ROADMAP](./session/ROADMAP_chat_continuity_v0.md) |
| **H4** | `host-prompt-assembly` | [`prompt/`](./prompt/) | 从 lg_rag/chat 抽模板；slot 装配；版本字段 | `prompt-assembly-p1` | [ROADMAP](./prompt/ROADMAP_prompt_assembly_v0.md) |
| **H5** | `host-skill-registry` | [`skill/`](./skill/) | Skill 元数据索引；NL 匹配 → `provide`；不建完整引擎 | `skill-registry-p0` | [ROADMAP](./skill/ROADMAP_skill_registry_v0.md) |
| **—** | 暂缓 | — | A2A 跨进程；acomplete 全面接入；chat/graph 拓扑变更 | — | — |

**顺序钉死**：H1 → H2 → H3；H4 可与 H2 尾穿插；H5 依赖 H4 元数据面。  
**禁止**：未过 H1 先开大改 Chat Session 或 Skill NL。

### 3.1 Task 颗粒度（已拆 · active）

| 波次 | task 文件 | task_slug | 分支（建议） | 前置 | 闸（起草时） |
|---|---|---|---|---|---|
| H1 | [`task_lg_rag_supervisor_capability_catalog.md`](../../tasks/done/task_lg_rag_supervisor_capability_catalog.md) | `lg-rag-supervisor-capability-catalog` | `task/lg-rag-supervisor-capability-catalog` | — | **CLOSE** ✓ |
| H2 | [`task_capability_policy_sandbox.md`](../../tasks/done/task_capability_policy_sandbox.md) | `capability-policy-sandbox` | — | **CLOSE** ✓ |
| H3 | [`task_chat_session_continuity.md`](../../tasks/done/task_chat_session_continuity.md) | `chat-session-continuity` | H2 ✓ | **CLOSE** ✓ |
| H4 | [`task_prompt_assembly_p1.md`](../../tasks/done/task_prompt_assembly_p1.md) | `prompt-assembly-p1` | — | **CLOSE** ✓ |
| H5 | [`task_skill_registry_p0.md`](../../tasks/done/task_skill_registry_p0.md) | `skill-registry-p0` | H4 ✓ | **CLOSE** ✓ · agent-host-plan **收官** |

00 invoke：[`docs/harness/invokes/by-task/agent-host-plan/invoke_20260827_00_agent-host-plan.md`](../../harness/invokes/by-task/agent-host-plan/invoke_20260827_00_agent-host-plan.md)

---

## 4. 跨波次硬约束（写入各 task）

1. **Mode A 主路径**：`list_capabilities` + `invoke`；extras 不回流默认导出。  
2. **Host 权威**：SO 校验不可做成模型可选 tool；Policy 键不可由 plan 写入。  
3. **静态图 + 动态 plan**：H1 只改 plan 数据与 prompt 注入，不 compile 新图。  
4. **失败语义**：tool 未知/被拒 → `ok=False` 记入 `subtask_results`，不拖垮整图（继承 v0）。  
5. **观测**：`capability_id` / `policy_blocked` / `structured_output_fallback` 进 span metadata。  
6. **无关 task 不混改**：`ops-sync-sender-migration` · 在跑 RAG 检索 task。

---

## 5. 建议包路径（草案 · 以 task 为准）

| 波次 | 新增/主要触及 |
|---|---|
| H1 | `app/ops/lg_rag/multi/nodes.py` · `app/ops/capability/defaults.py` · 可选 `app/ops/lg_rag/prompts/`（临时，H4 再迁） |
| H2 | `app/ops/capability/gateway.py` · `app/ops/capability/policy.py`（新）· adapters |
| H3 | `app/ops/chat/` · `app/db/models`（若需消息表）· 可选 `app/ops/session/`（新） |
| H4 | `app/ops/prompts/`（新） |
| H5 | `app/ops/skill/` 或 `app/ops/capability/skill_registry.py`（00 定夺） |

---

## 6. 测试策略（规划级）

| 波次 | 必跑 |
|---|---|
| H1 | `test_lg_rag_multi` + 新 mock：catalog 进 prompt、非法 tool id |
| H2 | capability 单测 + invoke blocked/allowed；CI 无真 sandbox 外网 |
| H3 | chat 路由/流 mock；压缩策略纯函数单测 |
| H4 | 模板渲染单测；lg_rag 节点 golden prompt 片段 |
| H5 | 匹配 stub（关键词/embedding mock）；provide 不执行 SKILL.md |

合并前：`pytest` 相关子集 + `ruff` 触及路径 + 触图谱则 `./scripts/graph-compile.sh`。

---

## 7. 文档层级（本轨新增）

```text
docs/spec/agent-infra/
├── 02_agent_host_plan_v0.md          # 本文件 · L0 规划总表
├── orchestration/                    # L1 · H1
├── session/                          # L1 · H3
├── prompt/                           # L1 · H4
└── skill/                            # L1 · H5
    capability/ROADMAP_policy_*       # L1 延续 · H2
```

`01_upgrade_roadmap.md` 保持 **stable** 归档；**活跃排期以本文件为准**。

---

## 8. 00 统筹入口

- Prompt：[`PROMPT_00_agent-host-plan.md`](../../harness/invokes/by-task/_prompts/PROMPT_00_agent-host-plan.md)  
- 派发记录：[`invoke_20260827_00_agent-host-plan.md`](../../harness/invokes/by-task/agent-host-plan/invoke_20260827_00_agent-host-plan.md)  
- **当前棒**：**agent-host-plan H1–H5 全部 CLOSE**（2026-08-27）

---

## 9. 修订记录

| 日期 | 说明 |
|---|---|
| 2026-08-27 | 初版：Gateway 轨收官后 Agent Host flesh 五波次规划 |
| 2026-08-27 | **HG-SPEC-SIGNOFF=approved**；拆 H1–H5 active task + 00 invoke |
| 2026-08-27 | **H1–H5 全轨 CLOSE**；00 invoke CLOSE；规划状态 → completed |
