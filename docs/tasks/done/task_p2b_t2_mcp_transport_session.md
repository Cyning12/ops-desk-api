---
title: task · feat · P2b-T2 MCP 薄 transport 层 + McpSessionManager
---

# task · feat · P2b-T2 MCP 薄 transport 层 + McpSessionManager

> **状态**：`closed`（2026-11-16 落卡 · 夜间自动执行波 · 2026-11-16 关账 · feat PR #412 squash merge `8e65f8e1` · 台账见 invoke_20261116_50_close.md）
> **来源**：issue Cyning12/ops-desk-workspace#23（m03064/m03216 夜间授权 · 设计真源 workspace 11-p2b-mcp-skill-design.md 终稿 §8 T2 行 + §5 连接生命周期 + §10 失败路径；操作真源 lead 委派书 m00002）

## Harness 元信息

| 键 | 值 |
|----|----|
| **task_slug** | p2b-t2-mcp-transport-session |
| base | 575ab69b |
| 关联 issue | Cyning12/ops-desk-workspace#23 |
| 关联 PR | #412（feat · squash merge `8e65f8e1`）· CLOSE 见 invoke_50 台账 |
| **wiki_delta** | `n/a` |
| **wiki_delta_note** | 本仓未启用 WikiTrack；本波为 capability MCP transport/session 运行时 |
| graph_change_layer | G-L1（01_modules.md capability 行备注 + HG-GRAPH-MODULES 签收行） |
| review_hat | 20（R1 审查文已落盘 · GO） |

### 人工闸

| human_gate_id | status | blocks_hats | 说明 |
|---------------|--------|-------------|------|
| HG-TASK-DRAFT | approved | 30 | approved 2026-11-16 · 授权 issue #23 m03064/m03216（夜间授权）+ 11 设计终稿 §8 T2 行 + lead 委派书 m00002 为唯一范围真源；§0.1 R1-R10 修订为硬约束 |
| HG-AUDIT-R1 | approved | 30 | approved 2026-11-16 · 同上授权（11 设计终稿即审计真源）+ R1 审查文 docs/harness/reviews/task_p2b_t2_mcp_transport_session_audit_R1_20261116.md（GO） |
| HG-GRAPH-MODULES | approved | 30 | approved 2026-11-16 · 同上授权（无新一级模块/路由/表/SSE 事件类型；capability 内新增子包属行内备注义务）· capability 行备注随 30 交付回填（承 :135/:136 先例） |

## 背景

P2b（MCP/Skill 面重建）第 2 单。T1 已合 `mcp_config.py` 配置面纯解析 loader（零连接），T4 已合 skill 面并删除旧 mock MCP adapter。本单承 T1 建 `app/ops/capability/mcp/` 子包：薄 transport（stdio/http 两实现 · httpx 既有依赖 · 零新外部依赖）+ McpSessionManager（lifespan 启动期按 mcp_servers.yaml 白名单建连 · expected_server 校验 · 单 server 失败隔离 · shutdown 清理与 unregister 接口面）。**本单不注册 capability 条目**（翻译器与 register 是 T3），manager 只产出 session 面（ping/tools/list/tools/call）。设计真源：11 终稿 §5/§8 T2 行/§10；委派书 m00002 内联协议子集与超时表为操作真源（节号偏差见「实现备忘 · 偏差登记」）。

## 范围

1. **新增 `app/ops/capability/mcp/errors.py`**：`McpError` 基类 + `McpTransportError`（`cause=CAUSE_TRANSPORT` 供 circuit.is_environmental_failure 计数）/ `McpHandshakeError` / `McpIdentityMismatchError` / `McpTimeoutError` / `McpProtocolError`。
2. **新增 `app/ops/capability/mcp/jsonrpc.py`**：JSON-RPC 2.0 编解码（request/notification/response/error）+ 错误码常量（-32700/-32600/**-32601**/-32603）+ `JsonRpcRemoteError`（远端 error 应答）+ id 生成（单调计数）。
3. **新增 `app/ops/capability/mcp/transport.py`**：`McpTransport` Protocol（async 形态：`request(method, params, *, timeout_s)` / `notify(method, params)` / `aclose()`）+ 两实现：
   - `StdioTransport`：`asyncio.create_subprocess_exec`；**env 白名单过滤**——不继承 `os.environ`，仅 PATH/HOME/LANG 等最小集 + `env_allowlist` 显式键；newline 分隔 JSON-RPC 行帧；后台 reader task 分发。
   - `HttpTransport`：`httpx.AsyncClient`（既有依赖）；POST `Content-Type: application/json`，Accept `application/json, text/event-stream`（StreamableHTTP 最小子集；SSE 应答解析取匹配 id 的 message 事件）。
   - server→client 请求纪律：`ping` 应答 `{}` result；**其余请求 1s 内回 JSON-RPC 错误 -32601 防挂起**；通知（无 id）安全忽略，`notifications/tools/list_changed` 不响应不动作。
4. **新增 `app/ops/capability/mcp/session.py`**：`McpSession`：
   - 握手：`initialize` 首选 config.protocol_version（钉版 2025-06-18）；失败按回退链 `SUPPORTED_PROTOCOL_VERSIONS = ("2025-06-18", "2025-03-26", "2024-11-05")` 降级重试；server 应答 `protocolVersion` 须 ∈ 支持集否则断连（偏差 D2 登记）；initialize timeout = connect_timeout（默认 10s 钉死）超时断连。
   - `expected_server` 校验：`serverInfo.name` **精确相等**；不匹配断开 + span 拒连 `reason=identity_mismatch`（trace_span 承 tracing.py:162 零成本 no-op 先例）。
   - ping 门：握手成功后首 ping 验证活性。
   - `tools/list` / `tools/call`：call_timeout 默认 30s 钉死；双超时分层=配置值 → transport 默认 → 调用时 clamp(floor=1000ms, cap=120000ms)。
5. **新增 `app/ops/capability/mcp/manager.py`**：`McpSessionManager`：`start()` 遍历配置并发建连（asyncio.gather · per-server 异常隔离 warn 跳过，§10）；`get_session(key)` 缺省 `None`（T3 转 ok=False mcp_session_unavailable）；`aclose()` 逆序 close + **R5c unregister 接口面**（`unregister_hook: Callable[[str], None] | None` 构造注入，本单注释 T3 挂点：T3 落地后由 lifespan 传 registry.unregister 同步摘除 mcp.* 条目）；**并发去重**（同 key 同时只建一次 · 单 flight dict）；**迟关闭**（aclose 后完成的连接立即 close 不入池）；**取消感知**（CancelledError 清理半成品后重抛）。
6. **`app/main.py` lifespan 挂接**（:82-95 承 auto_resume 先例）：总闸 `ops_capability_mcp_enabled` off（默认）→ 零创建零 diff；on 且有 config 路径 → `load_mcp_servers_config`（缺失/解析失败 warn + MCP 面降级为空 · §10）→ `McpSessionManager` → `app.state.mcp_sessions` → `await manager.start()`；finally 逆序 `await manager.aclose()`。
7. **熔断按 server**：manager/session 调用经 `circuit.guard(spec)`（circuit.py:218）· spec 轻量对象 `capability_id=f"mcp.{server_key}"`、`side_effect` 读态（写探测限制不触发）；call_async 禁用（Tornado-only · circuit.py:27 钉案）。
8. **测试**（四文件 + 一 fixture）：
   - `tests/test_capability_mcp_transport.py`：jsonrpc 编解码 + FakeTransport 协议纪律（-32601/通知忽略/list_changed 不响应/ping 应答）+ env 白名单过滤断言（不继承 os.environ · 最小集+allowlist）。
   - `tests/test_capability_mcp_session.py`：FakeTransport 握手谱系（首选成功/降级回退/应答版本不支持断连/initialize 超时断连/identity mismatch 拒连+span reason/ping 门失败）+ 双超时 clamp 表（floor 1000ms/cap 120000ms/默认 10s/30s 钉死）。
   - `tests/test_capability_mcp_manager.py`：单 server 失败隔离/并发去重/迟关闭/取消感知/unregister 钩子调用面/aclose 逆序。
   - `tests/test_capability_mcp_e2e.py`：**stdio 真子进程握手 e2e 冒烟**（`tests/fixtures/mcp_stdio_stub.py` 零依赖手工 JSON-RPC stdio 脚本，经 `sys.executable` 起子进程）+ **负例三枚**（不存在命令 → 隔离 warn；http 端口不通 → 隔离 warn；返回非 JSON → 隔离 warn）+ import 零网络 AST 源检查（承 T1 教训：不查 sys.modules）。
9. **图谱**：`docs/_tech_graph/l1/01_modules.md` capability 行备注（mcp 子包：transport/session/manager · 默认关）+ HG-GRAPH-MODULES 签收行（承 :135/:136 先例）。

## 非范围

- 不碰 `manifest.py` kind 词表与翻译器、capability 注册（T3）；manager.unregister_hook 仅建接口面。
- 不碰 skill 面（T4 已闭环）；不碰 `config.py` MCP 键面与 `.env.example`（T1 已定）。
- 不做真社区 server 互操作（T5b）；e2e 用零依赖 stub 脚本（委派书明示偏差登记口径）。
- 不做 listResources/listPrompts（仅注释 P2c 挂点）；不做 batching/通知订阅/热加载（终稿 §11）。
- 不改 `mcp_config.py` 既有 API（T1 已合）；不改 circuit.py/gateway.py/registry.py 既有行为。
- alembic/ · scripts/ · lg_rag/ · skill_registry/ 一律不碰。

## 失败路径

- `mcp_servers.yaml` 缺失/解析失败（总闸 on）→ 启动 warn + MCP 面降级为空（§10 · lifespan 不炸）。
- 单 server 握手失败/identity mismatch/超时 → warn + 跳过该 server，其余不受影响（§4-B 降级）。
- stdio 子进程启动失败（不存在命令）→ McpTransportError，per-server 隔离。
- 调用期 session 未建立 → T3 转 `ok=False mcp_session_unavailable` fail-closed（本单 get_session 返回 None）。
- 熔断 open → circuit.CircuitOpen（承 circuit.py 既有口径）。
- 回退 = revert 本波 PR；新包为纯新增，main.py 摘除 lifespan 段即回旧态。
- 并行 agent 撞 registry.yaml / 01_modules.md 同区冲突 → 保留双方 entry 手动解，冲突块如实登记。

## 验收标准

- [x] `app/ops/capability/mcp/` 六模块存在；零新外部依赖（pyproject/requirements 零 diff；仅 httpx/asyncio 既有）
- [x] 协议子集五件（initialize/initialized 通知/tools/list/tools/call/ping）实现；server→client 非 ping 请求 1s 内回 -32601 有测试锚；通知与 tools/list_changed 安全忽略有测试锚
- [x] 握手降级链（2025-06-18→2025-03-26→2024-11-05）+ 应答版本支持集断言 + initialize 超时断连 有测试锚
- [x] expected_server `serverInfo.name` 精确相等校验 + 不匹配断开 + span `reason=identity_mismatch` 有测试锚
- [x] 双超时分层 clamp（floor 1000ms / cap 120000ms / 默认 connect 10s call 30s）有测试锚
- [x] env 白名单过滤（不继承 os.environ）有测试锚
- [x] stdio stub server e2e 握手冒烟绿；负例三枚（不存在命令/端口不通/非 JSON）行为断言绿
- [x] manager 单 server 失败隔离 / 并发去重 / 迟关闭 / 取消感知 / unregister 钩子面 / aclose 逆序 有测试锚
- [x] 总闸 off 时 lifespan 零创建（app.state.mcp_sessions 不存在）；on+坏配置 warn 降级不炸
- [x] `pytest tests` 全绿（capability 相关用例五键 blank 前缀；CI 终裁）
- [x] `ruff check app tests` 绿；import-linter 绿（capability 出边不新增 forbidden）
- [x] 01_modules.md capability 行备注 + HG-GRAPH-MODULES 签收行已回写

### 自检结论

- 验收 1：`app/ops/capability/mcp/` 六模块在；pyproject/requirements 零 diff（仅 httpx/asyncio 既有依赖）→ **PASS**
- 验收 2：协议子集五件实现；server→client ping 应答/其余 -32601/通知与 list_changed 忽略 → tests/test_capability_mcp_transport.py（test_mux_replies_* / test_mux_ignores_notifications_including_list_changed）→ **PASS**
- 验收 3：握手降级链+应答版本支持集+initialize 超时断连 → tests/test_capability_mcp_session.py（test_handshake_fallback_* / test_handshake_chain_exhausted_raises_and_closes / test_handshake_initialize_timeout_raises_and_closes）→ **PASS**
- 验收 4：expected_server 精确相等+不匹配断开+span reason=identity_mismatch → test_expected_server_mismatch_rejects_and_closes + e2e test_stdio_identity_mismatch_rejected_e2e → **PASS**
- 验收 5：双超时 clamp（floor 1000ms/cap 120000ms/默认 10s/30s）→ test_clamp_timeout_defaults_floor_cap_and_nan / test_initialize_timeout_value_is_clamped_connect_timeout / test_call_tool_timeout_clamped_to_cap → **PASS**
- 验收 6：env 白名单不继承 os.environ → test_filtered_env_* + e2e test_stdio_env_allowlist_passes_protocol_version_e2e / test_stdio_env_not_allowlisted_defaults_to_pinned_e2e → **PASS**
- 验收 7：stdio stub e2e 握手冒烟 + 负例三枚 → tests/test_capability_mcp_e2e.py（test_stdio_handshake_and_call_tool_e2e / test_negative_*）→ **PASS**
- 验收 8：manager 隔离/去重/迟关闭/取消感知/unregister 钩子/aclose 逆序 → tests/test_capability_mcp_manager.py 九枚 → **PASS**
- 验收 9：总闸 off 零创建；on+坏配置 warn 降级不炸 → test_lifespan_gate_* 五枚 → **PASS**
- 验收 10：capability 相关用例五键 blank 前缀 54 passed（四文件）；全量 pytest 与 CI 终裁见 invoke_40 → **PASS**
- 验收 11：`ruff check app tests` 绿；import-linter 绿（capability 出边仅既有 tracing/config · mcp 子包无新 forbidden 出边）→ **PASS**
- 验收 12：01_modules.md capability 行备注 + HG-GRAPH-MODULES 签收行已回写（2026-11-16）→ **PASS**

## 必读列表

- 设计真源：`../ops-desk-workspace/docs/01-scope/03-general-agent/11-p2b-mcp-skill-design.md` 终稿（§0.1 R1-R10 硬约束 · §5 连接生命周期 · §8 T2 行 · §10 失败路径 · §11 非范围）
- 勘察：`/tmp/opsdesk-rfc/inv-p2b.md`
- 配置面：`app/ops/capability/mcp_config.py`（T1 已合 · 本单唯一配置输入）
- 熔断：`app/ops/capability/circuit.py`（guard 用法 :218-245 · call_async Tornado-only 钉案 :27）
- lifespan 先例：`app/main.py:82-95`（auto_resume 条件创建 · TestClient 零 diff 纪律）
- tracing：`app/ops/tracing.py:162` trace_span（未开启零成本 no-op）
- T1 体例：`docs/tasks/done/task_p2b_t1_mcp_legacy_config.md` + `/tmp/opsdesk-rfc/p2b-t1-exec.md` · T4 教训 `/tmp/opsdesk-rfc/p2b-t4-exec.md`（git add 只加具名文件 · .venv 严禁入库）

## 思考轮

| 轮 | 议题 | 状态 |
|----|------|------|
| R0 | 范围对账（委派书 vs 设计终稿 §8 T2 行） | done |
| R1 | 失败路径推演（§10 + 委派书负例三枚） | done |
| R2 | 非范围边界（T3/T5b/P2c 切面） | done |
| R3 | 关键决策记录（transport 接口形态/回退链/熔断 key/包结构） | done |
| R4 | 体例对账（T1 模板/registry/invokes/审查文） | done |
| R5 | 收尾复核（验收 checklist 全锚定） | done |

actual_last_round: R5

### R0 · 范围对账

委派书引用节号（§5-①~⑥ 协议子集表 / §5-② 超时表 / §5-④ 握手回退表 / §7-① 模块清单 / §9.2 MCP 七件）在设计终稿、architect 初稿、09 映射文、issue #23 评论中 grep 零命中（32601/握手降级/120000/20+2 均不存在）。裁定：以委派书内联技术细节为操作真源实现，差异入偏差登记（D1-D4，见实现备忘）。终稿 §5/§8/§10 与委派书实质一致（薄 transport · ping 门 · 双超时 · expected_server · 隔离降级 · shutdown 清理）。

### R1 · 失败路径推演

见「失败路径」节：yaml 缺失降级为空 / 单 server 隔离 / stdio 启动失败 / session 未建立 fail-closed / 熔断 open / revert 回退。新增：initialize 期间 server 不应答 → connect_timeout 断连；server→client 未知请求 1s 内 -32601（防 server 挂起等应答）；aclose 期间连接任务迟到完成 → 立即 close 不入池（迟关闭）。

### R2 · 非范围边界

T3（翻译器+register+kind 词表）切面=manager 只到 session 面 + unregister_hook 接口面；T5b（真社区 server）切面=e2e 只用 stub；P2c（resources/prompts）切面=仅注释挂点。config.py/env 键面 T1 已定不动。

### R3 · 关键决策记录

- **transport 接口形态**：高阶 `request/notify/aclose`（frame 编解码收敛进 transport 内部，session 只见 JSON-RPC 语义）——备选「frame pump 暴露」被否：两传输帧格式差异（行帧 vs HTTP 请求-响应）会泄到 session。
- **握手降级链**：委派书要求回退表 vs 终稿 §11 钉版唯一 → 调和为「config 钉版=首选版本（语义不变）+ 单回退链三版本 + 应答版本支持集断言」，偏差 D2 登记。
- **熔断 key**：`mcp.{server_key}` 轻量 spec（side_effect=read），复用 circuit.guard，不动 circuit.py。
- **包结构**：`app/ops/capability/mcp/` 六模块（委派书「§7-① 或承 mcp_config.py 先例建包」二选一 → 建包，与 mcp_config.py 同级邻居）。
- **manager 不读 settings**：由 lifespan 注入配置对象（保守守 capability-outbound importlinter 边界）；trace_span 直连（gateway.py 包内先例）。

### R4 · 体例对账

照 T1：task 档结构/人工闸表/registry N3（base=575ab69b · yaml safe_load 验证）/invokes by-task 四件/R1 审查文 GO 机读词/spec-wave task lint PASS 为闸。

### R5 · 收尾复核

验收 12 条逐条锚到测试或文件证据；偏差 D1-D4 全登记；回退路径=revert PR。

## 实现备忘

### 偏差登记

- **D1（节号漂移）**：委派书引用的 §5-①~⑥/§5-②/§5-④/§7-①/§9.2 (a)-(g) 在 11 设计终稿中不存在（grep 实证零命中）。处理：以委派书内联技术细节为真源实现；协议覆盖矩阵按委派书字面 (a) 握手+钉版 (b) expected_server (c) 超时+负例 (f) env 白名单 锚定。
- **D2（握手降级 vs 钉版）**：委派书要求降级回退表；终稿 §11「多协议版本协商（仅钉版 2025-06-18）」为非范围且 `mcp_config.py` 钉版仅接受 2025-06-18。调和：config 层钉版语义不变（=首选版本），session 层实现单回退链 `("2025-06-18", "2025-03-26", "2024-11-05")`——仅当 server 应答不同 protocolVersion 或 initialize 失败时按链降级；应答版本 ∈ 支持集才接受，否则断连。
- **D3（模块清单）**：委派书「app/ops/capability/mcp/ 或 §7-① 路径」二选一；§7-① 不存在 → 建包 `app/ops/capability/mcp/`（errors/jsonrpc/transport/session/manager + __init__），承 mcp_config.py 同级邻居先例。
- **D4（e2e server）**：委派书首选「python -m mcp 或同等零安装」，备选「最小手工 JSON-RPC stdio 脚本充当 server 并登记偏差」。本仓无 mcp 包依赖（零新依赖纪律）→ 采备选：`tests/fixtures/mcp_stdio_stub.py` 零依赖手工脚本经 `sys.executable` 起真子进程。
- **D5（unregister 挂点）**：委派书「R5c 同步 unregister mcp.* 条目——T3 未落地尚无条目，先把 shutdown 钩子结构与 unregister 接口面建好并注释 T3 挂点」→ `unregister_hook` 构造注入接口面 + 注释，本单无真实条目注销行为（无条目可注销）。

### 目录/文件清单

新增：`app/ops/capability/mcp/{__init__,errors,jsonrpc,transport,session,manager}.py`、`tests/test_capability_mcp_{transport,session,manager,e2e}.py`、`tests/fixtures/mcp_stdio_stub.py`。改动：`app/main.py`（lifespan mcp 段）、`docs/_tech_graph/l1/01_modules.md`（capability 行备注+签收行）。

## 测试策略

- capability 相关用例五键 blank 前缀跑：`OPS_HITL_PERSISTENCE= OPS_CAPABILITY_ALLOW_WRITE= OPS_CAPABILITY_ALLOW_WRITE_TAGS= OPS_CAPABILITY_PERSISTENCE= OPS_CAPABILITY_EXTRA_MANIFESTS= python -m pytest tests/test_capability_mcp_*.py -q`
- 全量 `python -m pytest tests -q`（worktree .venv）；脏树期 wave_gate 红为结构性常态（T1/T4 钉案），提交后复绿。
- CI（无 .env）为锚终裁。
- e2e stub server 仅本机回环/子进程，零外网（CI 可跑）。

## 修订记录

| 日期 | 版本 | 变更 |
|------|------|------|
| 2026-11-16 | v1 | 落卡过闸（HG-TASK-DRAFT/HG-AUDIT-R1/HG-GRAPH-MODULES approved · 夜间授权 issue #23 m03064/m03216） |
| 2026-11-16 | v2 | 30 实现完成：mcp/ 六模块+main.py lifespan+测试四文件一 fixture（54 枚绿 · ruff 绿 · graph-compile 绿）· 验收全勾+自检回填 |
