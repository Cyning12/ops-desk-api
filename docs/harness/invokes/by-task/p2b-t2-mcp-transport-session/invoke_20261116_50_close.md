# invoke_50 · close（p2b-t2-mcp-transport-session）

## 内容

50 CLOSE 关账：feat PR #412 squash merge 完成（wave_tip=8e65f8e1），registry
status active→closed 钉 wave_tip，task 档 active→done（回填状态行与关联 PR）。

## 验证台账

| 项 | 结果 |
|---|---|
| feat PR | #412 · squash merge `8e65f8e1` |
| CI 四绿 | pytest pass (2m29s) · check pass · import-linter pass · lint-wiki-delta pass |
| wave_tip | `8e65f8e1`（feat(capability): P2b-T2 MCP 薄 transport 层 + McpSessionManager (#412)） |
| registry | status=closed · base=575ab69b · wave_tip=8e65f8e1 · yaml.safe_load PASS |
| task 档 | docs/tasks/active/ → docs/tasks/done/task_p2b_t2_mcp_transport_session.md |
| 全量 pytest（提交前 · 五键 blank） | 2272 passed, 2 skipped（闸测试提交后复绿 2 passed） |
| mcp 四测试文件 | 54 passed（transport 15 · session 16 · manager 9 · e2e 14） |
| stdio stub e2e 握手冒烟 | 真子进程 initialize/ping/tools/list/tools/call echo 全链路绿 · 退出回收实证 |
| ruff / import-linter / graph-compile | 全绿（contracts 12 kept, 0 broken） |

## 偏差终录

1. **D1 · 委派书节号漂移**：委派书引用的 §5-①~⑥（20+2 协议子集表）、§5-②（floor/cap 超时表）、§5-④（握手降级回退表）、§7-①（模块清单）、§9.2 MCP (a)-(g) 在设计终稿（workspace 11 号 · commit 2b8f2dd）、architect 初稿、09 映射文、issue #23 评论中 grep 零命中（32601/握手降级/120000/20+2 均无）。处置：以委派书内联技术细节为操作真源实现，登记偏差。
2. **D2 · 握手降级链 vs 终稿 §11 钉版**：委派书要「一次试 2025-06-18 失败降级回退表」与终稿 §11 非范围「仅钉版 2025-06-18」冲突。调和实现：config 层钉版语义不变（首选版本=MCP_PROTOCOL_VERSION=2025-06-18），session 层回退链 SUPPORTED_PROTOCOL_VERSIONS=(2025-06-18, 2025-03-26, 2024-11-05) + 应答版本必须在支持集否则断连。e2e 双向实证（stub 注入 2024-11-05 走降级 · 默认 2025-06-18 直连）。
3. **D3 · 模块清单自裁定**：§7-① 不存在 → 建包 `app/ops/capability/mcp/` 六模块（承 mcp_config.py 先例 · importlinter capability-outbound 12 kept 0 broken 实证零新 forbidden 出边）。
4. **D4 · e2e server 选型**：无零安装真 stdio MCP server → 委派书备选口径启用：`tests/fixtures/mcp_stdio_stub.py` 零依赖手工 JSON-RPC stdio 桩（sys.executable 起真子进程）。
5. **D5 · unregister 仅接口面**：R5c 要求 shutdown 同步 unregister mcp.* 条目，T3（manifest/翻译器）未落地尚无 mcp.* 条目 → McpSessionManager(unregister_hook=None) 接口面+main.py lifespan 挂点注释建好，T3 落地时接线；manager 单测覆盖 hook 调用序与失败容错。

## 结果

CLOSE GO · P2b-T2 关账完成。MCP transport/session 面可用：`OPS_CAPABILITY_MCP_ENABLED=true` + `OPS_CAPABILITY_MCP_SERVERS_CONFIG=<yaml>`（总闸默认关 · 零创建 · 配置缺失/坏文件 warn 降级为空）。T3（kind=mcp 词表+翻译器）接 McpSessionManager.get_session 与 unregister_hook 挂点。
