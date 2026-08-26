"""Capability Gateway · adapters。

P0：local_fn；P1：可选 langchain_tools；P2：mcp / sandbox / cli mock 探针
（默认不进 defaults，见 ``app.ops.capability.probes``）；
P3：skill stub（``provide`` / ``invoke`` 预留，见 ``adapters.skill``）。
"""

from app.ops.capability.adapters.cli import MockCliAdapter
from app.ops.capability.adapters.langchain_tools import as_structured_tools, as_tool_node
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
    "as_structured_tools",
    "as_tool_node",
]
