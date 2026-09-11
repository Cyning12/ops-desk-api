# SPEC：Langfuse SDK / 项目 v4 迁移（v1）

> **状态**：`draft` · **优先级：暂不排期**（见 `docs/tasks/PRIORITY_DEFERRED.md`）  
> **track**：`observability` / Langfuse  
> **上游**：2026-08-17 code-only 盘点（官方 [v4-project-migration](https://raw.githubusercontent.com/langfuse/skills/main/skills/langfuse/references/v4-project-migration.md) · [Compatibility](https://langfuse.com/docs/compatibility) · [Python v3→v4](https://langfuse.com/docs/observability/sdk/upgrade-path/python-v3-to-v4) · [v4 overview](https://langfuse.com/docs/v4)）  
> **下游**：**暂不**起草 `docs/tasks/active/task_*.md`；接近 Cloud cutover 或维护者令后再开 00 → 20 → 30  
> **Open Folder（实现）**：`ops-desk-api/`  
> **Bounded Context**：观测旁路与 Chat / LCEL tracing；**不**借机改 `chat/graph` 拓扑、**不**升业务 freeze。

---

## Harness 元信息

| 字段 | 值 |
|---|---|
| **spec_slug** | `langfuse-sdk-v4-migration` |
| **invoke_slug** | `langfuse-sdk-v4-migration`（开 task 后启用） |
| **test_strategy** | `required` |
| **test_strategy_note** | pytest：`tests/test_ops_tracing.py` + Chat/LCEL tracing mock；装包后冒烟 `scripts/trace_smoke.py` / `lc_evidence_smoke.py`（需非生产 Langfuse 项目验观察）；`git diff` 不改 `app/ops/chat/graph.py` 拓扑 |
| **Open Folder（实现）** | `ops-desk-api/` |
| **默认分支（建议）** | `task/langfuse-sdk-v4-migration` |
| **graph_change_layer（建议）** | `G-L1`（`01_modules.md` 观测备注增量） |
| **freeze_id** | 无业务 HTTP freeze 变更 |
| **Python** | **无需**为 v4 升 Python；现 `>=3.11,<3.12` 已满足 SDK 4.x（`>=3.10,<4`） |

### 人工闸（SPEC 阶段）

| human_gate_id | status | 说明 |
|---|---|---|
| **HG-SPEC-SIGNOFF** | pending | 草案落盘；未签收前禁止 30；且本项当前在 **PRIORITY_DEFERRED** |

---

## 1. 背景与目标

### 背景

仓内已接 Langfuse（可选开关 `OPS_CHAT_TRACER=langfuse`）：

- 封装：`app/ops/tracing.py`
- Chat：`CallbackHandler` + 根 span（`app/ops/chat/service.py`）
- LCEL：`lc-evidence-chain` Callback + `trace_span`（`app/ops/lc_evidence_chain/chain.py`）

依赖：声明 `langfuse>=3.0,<4`；`uv.lock` 解析 **3.15.0**。Langfuse Cloud **v3/v4 双轨至 2026-11-16**，此后 Cloud 仅 v4，legacy 摄入/读 API/trace-level evaluator 等移除（见 [Compatibility](https://langfuse.com/docs/compatibility)）。

### 一句话目标

在 **不升级 Python、不改 Chat graph** 的前提下，将 SDK 升到 **v4（建议 ≥4.7.0）**，按 observations-first 改写仓内 tracing 封装，并完成项目侧 evaluator / export 核查与非生产验收入库。

### 非目标

- 仅为 Langfuse 升级 Python 到 3.12+
- 开 active task / 本波 30 改码（见 PRIORITY_DEFERRED）
- 为兼容 Legacy 规则新增或保留 `set_current_trace_io` / `set_trace_io`（官方默认禁止；除非维护者书面坚持）
- 改 `app/ops/chat/graph.py` 节点与边
- 自托管 Langfuse server 运维（本仓为 Cloud；若日后自托管另开 SPEC）
- Langfuse Prompt Management / Scores 产品化 / Dataset 实验平台建设

---

## 2. 现状盘点（2026-08-17 · code-only）

| 面 | 现状 | v4 影响 |
|---|---|---|
| SDK | 3.15.0 · pin `<4` | 须升到 4.x（建议 ≥4.7.0 实时 ingestion） |
| Python | 3.11.15 · `>=3.11,<3.12` | **无阻塞** |
| `start_as_current_span` / `start_as_current_generation` | `tracing.py` | → `start_as_current_observation(..., as_type=...)` |
| `update_current_trace` / `observation.update_trace(tags=…)` | `trace_span` 写 tags | → `propagate_attributes(...)` |
| `CallbackHandler()` | Chat / LCEL，无 `update_trace=` | 保持；勿传已移除参数 |
| `observe` / `get_client` / `flush` | 使用中 | 预期兼容；升包后回归 |
| `update_current_span_metadata` | 可能非 `dict[str,str]` | v4 metadata 更严（值≤200 字符、偏 string） |
| 裸 `/api/public/ingestion` | 未见 | — |
| `DatasetItem.run` / `api.observations_v_2` | 未见 | — |
| Evaluators / Exports | **未查项目** | 开 task 后必查 UI |

### Readiness 快照（开 task 前）

| 区域 | 状态 |
|---|---|
| project access | blocked（未配本轮项目读权限） |
| SDK/instrumentation | blocked（仍 `<4`；无 task） |
| trace / dataset evaluators | blocked |
| direct APIs | ready（代码视角：无自研 deprecated REST） |
| exports | blocked |
| verification/rollback | blocked |

---

## 3. 方案（实现时采用）

| 决策 | 选择 | 理由 |
|---|---|---|
| Python | **保持 3.11** | SDK 4 不要求升 Python |
| SDK 目标 | **langfuse≥4.7,<5**（实现时再锁精确上界） | GA major + 实时 ingestion |
| 封装策略 | **只改 `app/ops/tracing.py` 及单测/冒烟**；业务节点继续走仓内 API | 爆破面最小 |
| tags / session | `propagate_attributes`；Chat 继续 `langfuse_session_id` metadata | 对齐 v4 传播模型 |
| Trace I/O 逃逸 | **默认不加** `set_current_trace_io` | 官方 migration 禁止「仅为 Legacy 规则保留」 |
| 验收入库 | 非生产项目打样 + UI 查 observation 树 | mock 不算过闸 |

### 建议实现切片（开 task 后）

1. 依赖：`pyproject.toml` / `requirements.txt` / `uv.lock` → 4.x  
2. `tracing.py`：span API + tags 传播；metadata 字符串化  
3. 确认 `CallbackHandler` 构造无破坏性参数  
4. pytest 绿；可选本机 smoke + Langfuse UI  
5. 项目侧：Evaluators Legacy 行、Exports 源；Migration Assistant  
6. G-L1 备注一行

---

## 4. 验收标准（开 task 后）

- [ ] 声明与 lock 均为 langfuse 4.x（建议 ≥4.7.0）  
- [ ] `tests/test_ops_tracing.py` 及相关 tracing mock 全绿  
- [ ] 非生产环境可见 Chat / LCEL 根 observation 与子树；tags/session/environment 可过滤  
- [ ] 代码无 `update_current_trace` / `start_as_current_span|generation`（或仅经已废弃兼容层且有移除计划）  
- [ ] 未新增 `set_current_trace_io`（除非维护者书面例外）  
- [ ] `git diff` 相对基线：`app/ops/chat/graph.py` 拓扑无改  
- [ ] 项目侧 evaluator / export 结论写入 invoke 或 review（非猜测）

---

## 5. 风险与回滚

| 风险 | 缓解 |
|---|---|
| v4 默认 span 过滤导致树断裂 | `LANGFUSE_DEBUG`；必要时 `should_export_span` 白名单（勿默认 export-all 除非必要） |
| metadata 类型收紧丢字段 | 上报前统一 `str` 截断 |
| Cloud cutover 前未迁完 | PRIORITY_DEFERRED 设 revisit：**2026-10-01** 或 Migration Assistant 红灯 |
| 回滚 | 保留 pin `>=3,<4` 的提交可 revert；Legacy 规则禁用而非删除 |

---

## 6. 与 PRIORITY_DEFERRED 的关系

本 SPEC **允许提前落盘**，但 **禁止**仅凭本文件驱动：

- 新建 `docs/tasks/active/task_langfuse_*`  
- 30 改码 / 升依赖  

启动条件见 `docs/tasks/PRIORITY_DEFERRED.md` 中本条的 **Revisit 触发器**。

---

## 7. 参考链接

| 主题 | URL |
|---|---|
| v4 overview | https://langfuse.com/docs/v4 |
| Compatibility | https://langfuse.com/docs/compatibility |
| Python v3→v4 | https://langfuse.com/docs/observability/sdk/upgrade-path/python-v3-to-v4 |
| Evaluator migration | https://langfuse.com/faq/all/llm-as-a-judge-migration |
| Cloud migration status | https://cloud.langfuse.com/v4-migration |
| Skill workflow | https://raw.githubusercontent.com/langfuse/skills/main/skills/langfuse/references/v4-project-migration.md |

---

## 修订

| 日期 | 说明 |
|---|---|
| 2026-08-17 | 首版 draft：code-only 盘点 + 七行 readiness 摘要；暂不排期、不开 active task |
