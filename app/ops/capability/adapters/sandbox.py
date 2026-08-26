"""sandbox kind 探针 adapter（Capability Gateway · P2）。

**Mock only**：不启真实 sandbox / 容器 / 外网。默认**不**进入
``ensure_default_capabilities``；本地启用见 ``app.ops.capability.probes``。
"""

from __future__ import annotations

from typing import Any


class MockSandboxAdapter:
    """Sandbox 罐头探针；``invoke`` 返回伪 stdout，零子进程。"""

    kind = "sandbox"

    def invoke(self, args: Any, *, ctx: dict[str, Any] | None = None) -> Any:
        del ctx
        return {
            "sandbox": "mock",
            "kind": self.kind,
            "input": args,
            "stdout": "sandbox-mock-ok",
            "exit_code": 0,
        }
