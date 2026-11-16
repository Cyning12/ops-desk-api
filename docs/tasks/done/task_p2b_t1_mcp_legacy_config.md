---
title: task · feat · P2b-T1 旧 MCP 遗产清除 + mcp_servers.yaml 配置面
---

# task · feat · P2b-T1 旧 MCP 遗产清除 + mcp_servers.yaml 配置面

> **状态**：`active`（2026-11-16 落卡过闸）
> **来源**：issue Cyning12/ops-desk-workspace#23（m03064/m03216 夜间授权 · 设计真源 workspace 11-p2b-mcp-skill-design.md 终稿 §8 T1 行）

## Harness 元信息

| 键 | 值 |
|----|----|
| **task_slug** | p2b-t1-mcp-legacy-config |
| base | bf1c23f2 |
| 关联 issue | Cyning12/ops-desk-workspace#23 |
| 关联 PR | （落 PR 后回填） |
| **wiki_delta** | `n/a` |
| **wiki_delta_note** | 本仓未启用 WikiTrack；本波为 capability MCP 面遗产清除 + 配置 loader |
| graph_change_layer | G-L1（01_modules.md capability 行备注 + HG-GRAPH-MODULES 签收行） |
| review_hat | 20（R1 审查文已落盘 · GO） |

### 人工闸

| human_gate_id | status | blocks_hats | 说明 |
|---------------|--------|-------------|------|
| HG-TASK-DRAFT | approved | 30 | approved 2026-11-16 · 授权 issue #23 m03064/m03216（夜间授权）+ 11 设计终稿 §8 T1 行为唯一范围真源；§0.1 R1-R10 修订为硬约束 |
| HG-AUDIT-R1 | approved | 30 | approved 2026-11-16 · 同上授权（11 设计终稿即审计真源：§0.1 R1-R10 整合修订已评审）+ R1 审查文 docs/harness/reviews/task_p2b_t1_mcp_legacy_config_audit_R1_20261116.md（GO） |
| HG-GRAPH-MODULES | approved | 30 | approved 2026-11-16 · 同上授权（按实判 · 无新一级模块/路由/表/SSE 事件类型）· capability 行备注义务随 30 交付回填（承 :135/:136 先例） |

## 背景

P2b（MCP/Skill 面重建）第 1 单。旧 U3 真 MCP client 是单枚代理形态（`McpClientAdapter` + endpoint/default_tool 两 env 键 + urllib sync transport），与 11 号设计终稿的多 server 白名单配置面不兼容，须整体退役。本单做两件事：(1) 清除旧 MCP 遗产（代码 + env 键 + R8 残留文档面）；(2) 新增 `mcp_servers.yaml` 配置面的**纯解析 loader**（零连接；连接/握手/注册/翻译是 T2）。设计真源：`../ops-desk-workspace/docs/01-scope/03-general-agent/11-p2b-mcp-skill-design.md` 终稿（§0.1 R1-R10 修订为硬约束、§2 删除面、§7-② 配置键面、§8 T1 行）。

## 范围

1. **删除** `app/ops/capability/adapters/mcp_client.py` 全文件（`register_mcp_client_if_enabled` / `McpClientAdapter` / `HttpJsonRpcTransport` / `FakeTransport` / `McpTransport` Protocol / `McpClientError` / `MCP_CLIENT_CAPABILITY_ID`）。
2. `app/ops/capability/__init__.py`：删 mcp_client 相关 import（:22/:28/:35）、`ensure_default_capabilities` 内 :108 的 `register_mcp_client_if_enabled()` 调用、`__all__` 三处（:131/:141/:173）、docstring :9 U3 行。
3. `app/ops/capability/adapters/__init__.py`：删 :29-35 import 块、`__all__` 五处（:42/:45/:49/:50/:58）、docstring :5 U3 行。
4. `app/config.py`：删 `ops_capability_mcp_endpoint` / `ops_capability_mcp_default_tool` 两键；**保留** `ops_capability_mcp_enabled` 作 MCP 面总闸（注释语义改写为「启用 MCP 面」）；新增 `ops_capability_mcp_servers_config`（mcp_servers.yaml 显式路径，禁目录扫描）。
5. **新增** `app/ops/capability/mcp_config.py`：`mcp_servers.yaml` schema + 纯解析 loader（`parse_mcp_servers(data)` / `load_mcp_servers_config(path)`，零连接、零外网）。键面按 11 §7-②：`key` / `transport`(stdio|http) / `url`|`command`+`args` / `cwd` / `env_allowlist` / `protocol_version` 钉版（默认且仅接受 `2025-06-18`）/ `expected_server` / `connect_timeout_s`（默认 10）/ `call_timeout_s`（默认 30）/ `default_side_effect` / `tool_overrides`（含 `description_override`）/ `exclude_tools`。未知键 / 缺键 / 未知 transport / 未知 side_effect 词表 / 坏 server_key / 重复 key 全拒（fail-closed 抛 `McpServersConfigError(ValueError)`）。
6. **新增** `tests/test_capability_mcp_config.py`：解析单测（非法 yaml / 缺键 / 未知 transport / 未知 side_effect 词表 / 传输不兼容键 / 未知键 / 坏 server_key / 重复 key / protocol_version 不符 / override 未知键 / exclude_tools 非 list / 超时非正 / 缺文件 全拒；happy path stdio+http+defaults 全过；模块零网络 import 断言）。
7. `tests/test_capability_gateway.py`：删 U3 段（:498-637，七用例 + skip 态 live 测试），本单**只删不建**（T2 以新 FakeTransport 重建）。
8. **R8 残留四处同清**：`.env.example`:137-140（重写 MCP 段为总闸+config 路径）、`docs/spec/agent-infra/capability/README.md`:23、`docs/spec/agent-infra/capability/ROADMAP_portable_core_v0.md`:52、`docs/_tech_graph/l1/01_modules.md`:34（删行中「真 MCP · 默认关 · CI 不外网」段 + 追加 P2b-T1 备注 + HG-GRAPH-MODULES 签收行，承 :135/:136 先例）。
9. `app/ops/capability/adapters/mcp.py`:5 docstring 一行改写（含 `McpClientAdapter` 字样，验收 grep 零命中要求必清；整文件删除是 T4，本单仅改 docstring —— 登记偏差 D1）。
10. stale 指针顺手清：`app/ops/capability/probes.py`:13-14、`app/ops/capability/adapters/http_generic.py`:246（各一处 docstring）。

## 非范围

- 不碰 `manifest.py`（T3 的 kind 词表）；不动 tests/test_capability_manifest.py:251-263 的 `kind: mcp` 用例（T3 地盘）。
- 不碰 `skill_registry` / `slots` / `nodes`（并行 T4 地盘）。
- 不删 `adapters/skill.py`、`capability/skill_stub.py`、`adapters/mcp.py` 整文件（T4 删；本单仅改 mcp.py:5 一行 docstring，见偏差 D1）。
- 不动 P2 mock 探针用例（test_capability_gateway.py:357-441，MockMcpAdapter/probe_mcp_echo，T4 地盘）。
- 不实现连接/握手/注册/翻译（T2）；loader 只解析，缺失/解析失败直接 raise（T2 负责 warn+降级，设计 §10）。
- 历史冻结档案不改（docs/tasks/done/task_cap_mcp_real.md、docs/audits/task-review/20261011_*、docs/harness/reviews/task_cap_mcp_real_*、docs/harness/invokes/by-task/cap-mcp-real/*）——验收 grep 对这些路径豁免（档案面）。

## 失败路径

- 非法 yaml / 缺键 / 未知 transport / 未知词表值 / 传输不兼容键 / 未知键 / 重复 key → loader fail-closed 抛 `McpServersConfigError(ValueError)`（T2 runtime catch + warn + MCP 面降级为空，设计 §10）。
- 总闸 off（默认）→ lifespan 不读配置不建连，零行为变化。
- 回退=revert 本波 PR 即可；loader 为纯新增模块，摘除即回到旧态。
- 并行 agent 撞 registry.yaml / 01_modules.md 同区冲突 → 保留双方 entry 手动解，冲突块如实登记。

## 验收标准

- [ ] 旧符号全清单 grep 零命中（范围 `app/ tests/ .env.example docs/spec/ docs/_tech_graph/`，档案豁免见非范围）：`register_mcp_client_if_enabled` / `McpClientAdapter` / `HttpJsonRpcTransport` / `ops_capability_mcp_endpoint` / `ops_capability_mcp_default_tool`
- [ ] R8 四处残留清零（.env.example:137-140 · capability README:23 · ROADMAP:52 · 01_modules:34）
- [ ] `app/ops/capability/mcp_config.py` 存在且零连接（无 httpx/socket/urllib/subprocess import）
- [ ] `ops_capability_mcp_servers_config` 键进 `app/config.py`；`ops_capability_mcp_enabled` 保留且注释语义为「启用 MCP 面」
- [ ] 配置解析单测全绿（拒载场景全覆盖 + happy path）
- [ ] `pytest tests` 全绿（capability 相关用例五键 blank 前缀；CI 终裁）
- [ ] `ruff check app tests` 绿
- [ ] import-linter 绿（capability 出边仍为空，mcp_config.py 仅 stdlib+yaml）
- [ ] 01_modules.md capability 行备注 + HG-GRAPH-MODULES 签收行已回写

### 自检结论

（30/40 完成后回填）

## 必读列表

- workspace 11-p2b-mcp-skill-design.md 终稿 §0.1 R1-R10/§2/§7-②/§8 T1 行（设计唯一范围真源）
- `/tmp/opsdesk-rfc/inv-p2b.md`（勘察）
- `docs/tasks/done/task_p2a_t1_panel_list_tools.md`（过闸体例模板）
- `docs/_tech_graph/l1/01_modules.md`:34/:135/:136（签收先例）
- `app/ops/capability/types.py`:22-24（RISK_LEVELS/SIDE_EFFECTS 词表）

## 思考轮控制

| 轮 | 结论 | early_stop | reason（early_stop） | residual_risks |
|---|---|---|---|---|
| R0 | 勘察：删除面五符号 + R8 四处全部 grep 实证定位；档案豁免面（task_cap_mcp_real 族）识别；P2 mock 探针用例（gateway:357-441）与 manifest kind:mcp 用例（T3/T4 地盘）划出本单 | false | — | 无 |
| R1 | 审查：docs/harness/reviews/task_p2b_t1_mcp_legacy_config_audit_R1_20261116.md（GO）；设计终稿 §0.1 R1-R10 整合修订已评审 | false | — | 无 |
| R2 | 方案：mcp_client.py 全删（`McpTransport` Protocol 不挪不留，T2 在新 transport 模块自定义 async 形态）；配置面顶层 `{servers: [...]}` 纯解析 loader 零连接；总闸保留语义转「启用 MCP 面」 | false | — | 无 |
| R3 | 反例/边界：fail-closed 全拒面（未知键/缺键/未知 transport/未知 side_effect 词表/坏 server_key/重复 key/传输互斥键/protocol_version 钉版/超时非正）；server_key 限 kebab 无点（^[a-z0-9]+(?:-[a-z0-9]+)*$ · 承 R-D1'） | false | — | 并行 agent 撞 registry/01_modules 同区（F 路径已备：保留双方手解） |
| R4 | 收敛：验收九勾全可机断（grep 零命中清单+范围明示 · pytest · ruff · import-linter · CI 终裁） | false | — | 无 |
| R5 | 收口：范围 10 项 · 非范围 · 失败路径 · 三闸 approved（授权 issue #23 m03064/m03216 + 11 终稿） | true | 设计终稿即审计真源 · 锚点全实证 · 验收全机断 · 再轮无新增信息 | 无 |

**actual_last_round**：R5（early_stop）

### R0 · 勘察定论

五符号（register_mcp_client_if_enabled/McpClientAdapter/HttpJsonRpcTransport/ops_capability_mcp_endpoint/ops_capability_mcp_default_tool）+ R8 四处（.env.example:137-140 · capability README:23 · ROADMAP:52 · 01_modules:34）全部命中点已 grep 定位。档案面（docs/tasks/done/task_cap_mcp_real.md、docs/audits/task-review/20261011_*、docs/harness/reviews/task_cap_mcp_real_*、docs/harness/invokes/by-task/cap-mcp-real/*）命中属历史冻结，豁免。tests/test_capability_manifest.py:251-263 `kind: mcp` 用例为 T3 kind 词表地盘，不动。

### R1 · 审查

11 设计终稿 §0.1 R1-R10 整合修订已评审，本档照终稿执行；R1 审查文对照终稿核对范围/非范围/验收/failure_paths 一致性，结论 GO（审查文已落盘）。

### R2 · 方案生成

mcp_client.py 全删（含 `McpTransport` Protocol——不挪不留，T2 在新 transport 模块自定义 async 形态，避免现在猜形状）；capability 包两处 `__init__` 清 import/调用/__all__/docstring；config.py 删两键留总闸加 config 路径键；mcp_config.py 纯解析 loader（dataclass 冻结实例 · 仅 stdlib+yaml，满足 import-linter capability-outbound 出边为空契约）。

### R3 · 反例与边界

fail-closed 全拒面：未知键 / 缺 key/transport / 未知 transport / 未知 side_effect 词表 / http 缺 url · stdio 缺 command / 传输互斥键（http 禁 command/args/cwd/env_allowlist · stdio 禁 url）/ 坏 server_key（须 kebab 无点）/ 重复 key / protocol_version 不符钉版 2025-06-18 / override 未知键 / exclude_tools 非 list / 超时非正或 bool / 缺文件。happy path：stdio+http 双 server + 默认值（connect 10/call 30/protocol 钉版）+ tool_overrides 全字段 + exclude_tools。

### R4 · 收敛

验收九勾全可机断：grep 零命中清单（范围与档案豁免明示）· R8 四处行号清零 · mcp_config.py 零连接 import 断言 · pytest（五键 blank 前缀 · CI 无 .env 终裁）· ruff app tests · import-linter capability-outbound。

### R5 · 收口

范围 10 项与非范围/失败路径互斥闭合；三闸 approved（授权 issue #23 m03064/m03216 夜间授权 + 11 设计终稿 · 不代签）；early_stop——设计终稿即审计真源、锚点全实证、验收全机断，再轮无新增信息。

## 实现备忘

（30 完成后回填；预定登记：McpTransport Protocol 不保留决策 · 偏差 D1 mcp.py:5 一行 docstring · probes.py/http_generic.py stale 指针清理）

## 测试策略

`pytest tests` 全量（capability 相关用例带五键 blank 前缀：`OPS_HITL_PERSISTENCE= OPS_CAPABILITY_ALLOW_WRITE= OPS_CAPABILITY_ALLOW_WRITE_TAGS= OPS_CAPABILITY_PERSISTENCE= OPS_CAPABILITY_EXTRA_MANIFESTS=`）；`ruff check app tests`；CI（无 .env）为锚终裁：pytest + check + import-linter + lint-wiki-delta。真 PG：`postgresql+asyncpg://ops:ops_password@localhost:5432/opsdesk_test`（如需 db 用例本地复跑）。

## 修订记录

- 2026-11-16：落卡过闸（HG-TASK-DRAFT / HG-AUDIT-R1 / HG-GRAPH-MODULES approved · issue #23 m03064/m03216 夜间授权 + 11 设计终稿；R1 审查文 GO）。
