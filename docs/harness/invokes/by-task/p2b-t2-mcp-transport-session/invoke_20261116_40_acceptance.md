# invoke_40 · acceptance（p2b-t2-mcp-transport-session）

## 内容

40 验收：提交前全量测试复跑 + 提交后闸测试复绿 + 验收标准逐条核对。

## 验证台账

| 项 | 结果 |
|---|---|
| `pytest tests` 全量（五键 blank 前缀 · CI 无 .env 等效） | **2272 passed, 2 skipped**（70s）· 2 failed 为脏树期结构性红（test_tc8_diff_whitelist / test_wave_gate_registry · T1/T4 钉案 · 提交后复绿） |
| `test_tc8_diff_whitelist` + `test_wave_gate_registry`（提交后复跑） | 2 passed（提交后复绿实证） |
| `ruff check app tests` | All checks passed |
| import-linter（.importlinter） | Contracts: 12 kept, 0 broken（mcp 子包零新 forbidden 出边） |
| `graph-compile.sh` | 绿（normalize check 10 md OK） |
| mcp 四测试文件（五键 blank） | 54 passed（transport 15 + session 16 + manager 9 + e2e 14） |
| stdio stub e2e 握手冒烟 | 真子进程 initialize/ping/tools/list/tools/call echo 全链路绿 · 退出子进程回收（returncode 非 None） |
| registry.yaml N3 entry | yaml.safe_load PASS · waves=21 · base=575ab69b |

## 验收标准逐条

- [x] mcp/ 六模块存在；零新外部依赖（pyproject/requirements 零 diff）
- [x] 协议子集五件 + server→client ping 应答/其余 -32601/通知与 list_changed 忽略（test_mux_*）
- [x] 握手降级链+应答版本支持集+initialize 超时断连（test_handshake_*）
- [x] expected_server 精确相等+不匹配断开+span reason=identity_mismatch（test_expected_server_* + e2e）
- [x] 双超时 clamp floor 1000ms/cap 120000ms/默认 10s/30s（test_clamp_* / test_*_timeout_*）
- [x] env 白名单不继承 os.environ（test_filtered_env_* + e2e 双向实证）
- [x] stdio stub e2e 握手冒烟绿 + 负例三枚（test_negative_*）行为断言绿
- [x] manager 隔离/去重/迟关闭/取消感知/unregister 钩子/aclose 逆序（九枚）
- [x] 总闸 off lifespan 零创建；on+坏配置 warn 降级不炸（test_lifespan_* 五枚）
- [x] pytest 全量绿（闸测试提交后复绿）· CI 四绿为终裁
- [x] ruff 绿 · import-linter 绿
- [x] 01_modules.md capability 行备注 + HG-GRAPH-MODULES 签收行

## 偏差终录

1. **D1（节号漂移）**：委派书 §5-①~⑥/§5-②/§5-④/§7-①/§9.2 终稿零命中 → 以委派书内联技术细节实现。
2. **D2（握手降级 vs 钉版）**：config 钉版=首选 + session 回退链 (2025-06-18, 2025-03-26, 2024-11-05) + 应答版本支持集断言。
3. **D3（模块清单）**：§7-① 不存在 → 建包 app/ops/capability/mcp/。
4. **D4（e2e server）**：无零安装真 server → tests/fixtures/mcp_stdio_stub.py 手工桩（委派书备选口径）。
5. **D5（unregister 挂点）**：T3 未落地 → unregister_hook 仅接口面+注释。

## 结果

40 验收 GO · 进 feat PR。
