# Task：Capability · 真 MCP adapter（cap-mcp-real）

> **状态**：completed（PR [#68](https://github.com/Cyning12/ops-desk-api/pull/68) MERGED · 2026-08-26 关账）  
> **类型**：feature / agent-infra（升级轨波次 3）  
> **上游 ROADMAP**：`docs/spec/agent-infra/capability/ROADMAP_portable_core_v0.md` §U3  
> **总轨**：`agent-infra-upgrade`  
> **分支**：`task/cap-mcp-real`  
> **前置**：`so-schema-hygiene` PR [#67](https://github.com/Cyning12/ops-desk-api/pull/67) · `cap-portable-core` [#66](https://github.com/Cyning12/ops-desk-api/pull/66) MERGED  
> **无关**：勿与其他 active task 混改；禁止改 `app/ops/chat/graph.py`。

---

## Harness 元信息

| 字段 | 值 |
|---|---|
| **task_slug** | `cap-mcp-real` |
| **git_branch** | `task/cap-mcp-real` |
| **implement_repo** | `ops-desk-api` |
| **test_strategy** | `required` |
| **test_strategy_note** | 默认 CI：mock 探针 + **FakeTransport** 单测（零外网）；可选 `@pytest.mark.integration` / env 真连，**不**进默认 CI；`tests/test_capability_gateway.py` 绿 |
| **code_quality_bar** | `L2_backend` |
| **graph_change_layer** | `G-L1` |
| **graph_delta** | `docs/_tech_graph/l1/01_modules.md`（可选备注） |
| **graph_delta_note** | capability 行补「真 MCP adapter · env 默认关」；不增一级模块 |
| **wiki_delta** | `n/a` |
| **wiki_delta_note** | 本波不晋升 WikiTrack |
| **review_hat** | `20` |
| **required_invoke_hats** | `10,30` |
| **invoke_retention_profile** | `default` |
| **freeze_id** | 无 |
| **orchestration** | 总轨波次 3；完成后跳过波次 4（除非维护者另令）并收官 |

### 人工闸

| human_gate_id | status | blocks_hats | 说明 |
|---|---|---|---|
| HG-TASK-DRAFT | approved | 22-R1 | 2026-08-26 00 代签 · 维护者授权全程自动推进 |
| HG-AUDIT-R1 | approved | 30 | 2026-08-26 00 代签；`docs/harness/reviews/task_cap_mcp_real_audit_R1_20260826.md` |
| HG-GRAPH-MODULES | approved | 30 | 仅备注；不增一级 |

> **HG-SPEC-SIGNOFF**：v0 已签；本波为 ROADMAP U3。若破坏 `invoke` 契约 → 停问升 v1。

---

## 背景与目标

P2 仅有 `MockMcpAdapter`（罐头）。U3 增加**真 MCP client adapter**（可注入 transport），与 mock **并行**；统一仍走 `invoke(id, args, ctx) → CapabilityResult`。默认关闭、env 开关；**禁止**默认 CI 打外网。

---

## 范围 / 非范围

**范围（U3）**：

1. 新增 client adapter（建议 `adapters/mcp_client.py` 或扩展 `mcp.py` 内 `McpClientAdapter`），实现 `CapabilityAdapter` 协议
2. 可注入 transport / session（stdio 或 HTTP JSON-RPC 抽象均可）；单测用 FakeTransport 模拟 tools/call
3. env 开关（示例）：`OPS_CAPABILITY_MCP_ENABLED`（默认 false）+ endpoint/command 配置；未启用时不注册真 client
4. 保留 `MockMcpAdapter` + probes 供 CI
5. 单测：假 transport 成功/失败 → `CapabilityResult.ok`；默认测试路径无 socket/HTTP 真连
6. 可选：`@pytest.mark.integration` 真连用例（默认 skip）
7. 文档：ROADMAP/域 README 补「真 MCP · 默认关」一行；G-L1 可选备注

**非范围**：

- 生产级 MCP 全集 / 多 server 编排 / OAuth 全集
- 替换 Mode A；改 chat/graph；引入 Agently
- 把 Host/SO 校验做成 MCP tool
- 默认 CI 外网
- 波次 4 `so-complete-adopt`

---

## 验收标准

- [x] 存在真 MCP client adapter；契约仍 `invoke → CapabilityResult`
- [x] Mock 探针保留；默认 defaults **不**注册真 client
- [x] FakeTransport（或等价）单测覆盖成功 + 失败；**零外网**
- [x] env 关闭时行为与改前兼容（既有 capability 测绿）
- [x] `chat/graph.py` 零 diff；无 Agently；ruff 绿
- [x] 文档注明默认关 / CI 不外网

---

## failure_paths

| 触发 | 行为 | 可重试 |
|---|---|---|
| transport/超时/协议错 | `CapabilityResult(ok=False, error=…)`，不拖垮图 | Y |
| env 未开却误注册真 client | 打回；默认关闭 | N |
| 默认 CI 真连外网 | 打回 | N |
| 破坏 invoke 契约 / 改 chat graph | 打回；考虑升 SPEC | N |

---

## 依赖

- `docs/spec/agent-infra/capability/ROADMAP_portable_core_v0.md` §U3
- `docs/spec/agent-infra/capability/SPEC-capability-gateway_v0.md`（契约）
- `app/ops/capability/adapters/mcp.py` · `probes.py` · `registry.py`
- `docs/standards/CODING_BACKEND_L2_v1_zh.md` · `FRAGMENT_30_gate_verify_v1_zh.md`

---

## 给执行帽（30）必读

本 task · ROADMAP §U3 · 现有 MockMcpAdapter · CapabilityAdapter Protocol · FRAGMENT_30 · CODING_BACKEND_L2

**硬约束**：invoke 契约不变；mock 保留；默认 CI 零外网；不改 chat/graph；不引 Agently。优先**可注入 FakeTransport** 而非强依赖未列入 requirements 的重 SDK；若必须加依赖须可选/轻量并说明。

---

## 思考轮

### 思考轮控制

| 字段 | 值 |
|---|---|
| **actual_last_round** | R4 |
| **early_stop** | yes |
| **early_stop_reason** | U3 边界清晰；核心是 env 闸 + FakeTransport |
| **residual_risks** | 真协议方言差异；依赖选型过重——优先自研薄 client + 注入 |

### R0
并行 mock，不替换 CI 探针。

### R1
FakeTransport 保默认 CI 零网。

### R2
env 默认 false。

### R3
不改 Mode A / chat graph。

### R4
依赖能免则免；必须加则 optional。

### R5
（提前停）

---

### 自检结论

> pending · 30 完成后 00 回填

---

## 修订记录

| 日期 | 说明 |
|---|---|
| 2026-08-26 | 10 起草 U3；00 代签；总轨自动推进 |


### KPI

Task_KPI%: 100

## CLOSE

| 项 | 内容 |
|---|---|
| 日期 | 2026-08-26 |
| PR | [#68](https://github.com/Cyning12/ops-desk-api/pull/68) MERGED |
| 定稿 | McpClientAdapter + FakeTransport；env 默认关 |
| 归档 | docs/tasks/done/task_cap_mcp_real.md |
| 下一棒 | 总轨收官（跳过 so-complete-adopt） |
