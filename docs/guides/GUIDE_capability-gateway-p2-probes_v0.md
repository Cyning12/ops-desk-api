# GUIDE：Capability Gateway · P2 探针（MCP / sandbox / cli）

> **状态**：active · **SPEC**：`SPEC-capability-gateway_v0.md` §4 P2  
> **范围**：mock 探针 only；禁止真 MCP / 生产 sandbox / 真外网进 CI 默认路径

## 默认关闭

`ensure_default_capabilities()` **只**注册 `local_fn` 两枚 mock（issue / deploy）。  
P2 三 kind 探针**不**写入 defaults。

## 本地启用

```python
from app.ops.capability.probes import register_p2_probes
from app.ops.capability import invoke

register_p2_probes(enabled=True)
r = invoke("probe_mcp_echo", {"q": "hi"})
assert r.ok
```

| capability_id | kind | adapter |
|---|---|---|
| `probe_mcp_echo` | `mcp` | `MockMcpAdapter` |
| `probe_sandbox_echo` | `sandbox` | `MockSandboxAdapter` |
| `probe_cli_echo` | `cli` | `MockCliAdapter` |

`enabled=False`（`register_p2_probes()` 默认）：可登记；带 `CapabilityFilter` 的 list 不可见；`invoke` → `ok=False`（`meta.blocked=disabled`）。无 filter 的 `list_capabilities()` 仍可能枚举到条目（调试用），但 defaults **从不**自动注册探针。

## 与 `app/tools/run_code.py`

`run_bash` / 真子进程 **禁止**进 defaults。若日后包装为 cli adapter，须显式注册且默认 `enabled=False`。当前 P2 cli 探针为零 subprocess 罐头。

## 非范围

skill（P3 · 见 `GUIDE_capability-gateway-p3-skill-boundary_v0.md`）· 改 `chat/graph.py` · Agently · 真外网 MCP client
