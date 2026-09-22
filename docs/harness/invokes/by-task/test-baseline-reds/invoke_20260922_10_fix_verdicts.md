# invoke · 10-task · 修复方向裁定汇总（写入 task 钉死契约）

> hat=10 · 2026-09-22

| 缺陷 | 裁定 | 排除的岔路 |
|------|------|------------|
| D1 chat_ws×2 | ① 断言序列对齐现行图拓扑（含 `tool_result`）② 检索链打桩确定化（rag_nodes 侧 provider/embedder/hybrid_recall 最小面）③ conftest 代理 env 净化（对齐 OPS_CHAT_TRACER 先例）④ conftest 补 `ops_knowledge_chunks` 建表 DDL（逐字对齐 migration 20260808） | skip/xfail；回退图拓扑；改生产 trust_env；重建测试库 |
| D2 proxy | 测试内 monkeypatch `urllib.request.proxy_bypass` → False | 改 `_capability_opener` 生产语义；换非 loopback 目标地址 |
| D3 flaky | 并发注入行确定性小 id（恒落 keyset 水位前） | 改 run_backfill 分页；retry/sleep 等待；Event 时序钉（钉不死 uuid 排序变量本体） |

纪律：三条全部「修复前红 → 修复后绿」断言化；禁止「本地跳过」式掩盖；只改 tests/。
