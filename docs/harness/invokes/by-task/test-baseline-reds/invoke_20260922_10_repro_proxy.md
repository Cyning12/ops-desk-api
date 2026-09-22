# invoke · 10-task · D2 capability proxy 复现

> hat=10 · 2026-09-22

## 命令与结果

`pytest tests/test_capability_http_adapter.py -q -k proxy` → **1 failed, 1 passed**

```
tests/test_capability_http_adapter.py:384: Failed: DID NOT RAISE
<class 'app.ops.capability.adapters.http_generic.HttpCapabilityError'>
```

- 红：`test_urllib_transport_honors_explicit_capability_proxy`（显式代理指向 127.0.0.1:1 不可达，期望调用失败以证明代理真被用上）
- 绿：`test_urllib_transport_bypasses_ambient_http_proxy`（断言语义相反，碰巧不受 macOS 旁路影响）
- 稳定复现（非 flaky）。
