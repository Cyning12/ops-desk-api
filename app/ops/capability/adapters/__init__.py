"""Capability Gateway · adapters（可迁移内核 · 零 LG 运行时依赖）。

P0：local_fn；P2：mcp / sandbox / cli mock 探针
（默认不进 defaults，见 ``app.ops.capability.probes``）；
P3：skill stub（``provide`` / ``invoke`` 预留，见 ``adapters.skill``）。

ToolNode 桥已迁至 ``app.ops.capability.extras.langchain``（非默认导出）。
"""

from app.ops.capability.adapters.cli import MockCliAdapter
from app.ops.capability.adapters.local_fn import LocalFnAdapter
from app.ops.capability.adapters.mcp import MockMcpAdapter
from app.ops.capability.adapters.sandbox import MockSandboxAdapter
from app.ops.capability.adapters.skill import SkillStubAdapter

__all__ = [
    "LocalFnAdapter",
    "MockCliAdapter",
    "MockMcpAdapter",
    "MockSandboxAdapter",
    "SkillStubAdapter",
]
