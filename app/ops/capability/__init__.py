"""Capability Gateway · 可迁移内核（Mode A：list + invoke）。

SPEC：``docs/spec/agent-infra/capability/SPEC-capability-gateway_v0.md``
表面：``register`` / ``unregister`` / ``list_capabilities`` / ``schemas_for_llm`` /
``invoke`` / ``provide``（P3 skill 上下文注入）
**默认导出零 LG 运行时依赖**；ToolNode 桥见 ``app.ops.capability.extras.langchain``。
P2 探针：``MockMcpAdapter`` / ``MockSandboxAdapter`` / ``MockCliAdapter``；
默认**不**进 ``ensure_default_capabilities``；启用见 ``probes.register_p2_probes``。
U3 真 MCP：``McpClientAdapter``（``OPS_CAPABILITY_MCP_ENABLED`` 默认关；CI 不外网）。
P3 skill：``SkillStubAdapter`` + ``register_skill_stub``；**非**完整引擎；
边界见 ``docs/guides/GUIDE_capability-gateway-p3-skill-boundary_v0.md``。
Mode A / filter 契约：``docs/guides/GUIDE_capability-portable-core-mode-a_v0.md``。
"""

from app.ops.capability.adapters import (
    FakeTransport,
    LocalFnAdapter,
    McpClientAdapter,
    MockCliAdapter,
    MockMcpAdapter,
    MockSandboxAdapter,
    SkillStubAdapter,
    register_mcp_client_if_enabled,
)
from app.ops.capability.defaults import ensure_default_capabilities
from app.ops.capability.gateway import (
    get_registry,
    invoke,
    list_capabilities,
    provide,
    register,
    schemas_for_llm,
    unregister,
)
from app.ops.capability.probes import register_p2_probes
from app.ops.capability.skill_stub import register_skill_stub
from app.ops.capability.types import (
    CapabilityFilter,
    CapabilityResult,
    CapabilitySpec,
)

ensure_default_capabilities()
# U3：仅当 OPS_CAPABILITY_MCP_ENABLED=true 且配置了 endpoint 才注册真 client
register_mcp_client_if_enabled()

__all__ = [
    "CapabilityFilter",
    "CapabilityResult",
    "CapabilitySpec",
    "FakeTransport",
    "LocalFnAdapter",
    "McpClientAdapter",
    "MockCliAdapter",
    "MockMcpAdapter",
    "MockSandboxAdapter",
    "SkillStubAdapter",
    "get_registry",
    "invoke",
    "list_capabilities",
    "provide",
    "register",
    "register_mcp_client_if_enabled",
    "register_p2_probes",
    "register_skill_stub",
    "schemas_for_llm",
    "unregister",
]
