"""cli kind 探针 adapter（Capability Gateway · P2）。

**Mock only**：默认不调 ``subprocess`` / 不包装 ``app.tools.run_code``。
真实 bash（``run_bash``）高风险，禁止进 defaults / CI 默认路径。
本地启用见 ``app.ops.capability.probes``。
"""

from __future__ import annotations

from typing import Any


class MockCliAdapter:
    """CLI 罐头探针；``invoke`` 回显伪命令结果，零子进程。"""

    kind = "cli"

    def invoke(self, args: Any, *, ctx: dict[str, Any] | None = None) -> Any:
        del ctx
        return {
            "cli": "mock",
            "kind": self.kind,
            "input": args,
            "stdout": "cli-mock-ok",
            "exit_code": 0,
        }
