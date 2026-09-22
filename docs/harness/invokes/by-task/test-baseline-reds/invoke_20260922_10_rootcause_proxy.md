# invoke · 10-task · D2 proxy 根因定位

> hat=10 · 2026-09-22 · 探针实证

## 根因

macOS 系统级 loopback 代理旁路：`urllib.request.proxy_bypass("127.0.0.1")` 在 darwin 恒 `True`（实证 probe 输出 True；系统「忽略这些主机与域的代理设置」默认列表含 127.0.0.1/localhost/*.local/内网段）。

`ProxyHandler.proxy_open` 内部先查 `proxy_bypass(host)`：即使 `_capability_opener`（`app/ops/capability/adapters/http_generic.py:306-313`）显式挂了 `ProxyHandler({"http": "http://127.0.0.1:1"})`，目标 host=127.0.0.1 被短路为直连 → 本地 JSON 服务正常应答 → DID NOT RAISE。

Linux CI 的 `proxy_bypass` 只认 env `no_proxy`（用例已 delenv）→ 显式代理真生效 → 连接失败 → 绿。**本地红 CI 绿**的 OS 差异根因。

## 修复方向裁定

测试内 `monkeypatch.setattr(urllib.request, "proxy_bypass", lambda h: False)` 做 OS 隔离；不改 `_capability_opener` 生产语义（空 dict 默认不走代理是刻意设计）。备选（不取）：目标 URL 改非 loopback 本机地址 —— 引入网卡依赖，不如打桩确定。
