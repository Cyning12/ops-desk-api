# invoke_40 · acceptance（p2b-t1-mcp-legacy-config）

## 内容

40 验收：提交后全量测试复跑 + 验收标准逐条核对。

## 验证台账

| 项 | 结果 |
|---|---|
| `pytest tests` 全量（五键 blank 前缀 · CI 无 .env 等效） | **2205 passed, 1 skipped**（45s） |
| `test_tc8_diff_whitelist` + `test_wave_gate_registry`（提交后复绿） | 2 passed（脏树期红为结构性常态，提交后绿） |
| `ruff check app tests` | All checks passed |
| `graph-compile.sh` | 绿（normalize check 10 md OK） |
| 五符号 grep（app/ tests/ .env.example docs/spec/ docs/_tech_graph/） | 零命中（McpClientAdapter / HttpJsonRpcTransport / FakeTransport / register_mcp_client_if_enabled / MCP_CLIENT_CAPABILITY_ID） |
| env 键 grep（大小写不敏感 endpoint/default_tool） | 零命中 |
| mcp_config 模块 AST 检查 | 零网络 import（stdlib + yaml 例外豁免） |

## 验收标准逐条

- [x] A1 `mcp_client.py` 全文件删除（git rm · 208 行）
- [x] A2 `config.py` 删 `ops_capability_mcp_endpoint` / `ops_capability_mcp_default_tool`，保留总闸
- [x] A3 R8 四处同清（.env.example · capability README · ROADMAP · 01_modules.md 行中段）
- [x] A4 `mcp_config.py` 纯解析 loader 落位（fail-closed · 钉版 2025-06-18 · 零连接 · 零网络 import）
- [x] A5 gateway 测试 U3 段只删不建（637→496 行）
- [x] A6 新增解析单测全拒载面 + happy path
- [x] A7 全量 pytest 绿 + ruff 绿 + graph-compile 绿
- [x] A8 registry N3 entry + R1 审查文 + invokes 落盘

## 偏差终录

1. **D1**：`adapters/mcp.py`:5 docstring 一行改写（验收 grep 要求；整删属 T4）。
2. **D2**：`probes.py`:13-14 与 `http_generic.py`:246 两处 stale 指针顺手清（各一行）。
3. **D3**：ROADMAP:95 历史表行（2026-08-26 档案行）不动；cap-mcp-real invokes / task done 档 / 审查文档案豁免。

## 结果

40 验收 GO · 进 feat PR。
