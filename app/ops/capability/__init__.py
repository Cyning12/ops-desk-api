"""Capability Gateway · 可迁移内核（Mode A：list + invoke）。

SPEC：``docs/spec/agent-infra/capability/SPEC-capability-gateway_v0.md``
表面：``register`` / ``unregister`` / ``list_capabilities`` / ``schemas_for_llm`` /
``invoke`` / ``ainvoke`` / ``provide``（P3 skill 上下文注入）
**默认导出零 LG 运行时依赖**；ToolNode 桥见 ``app.ops.capability.extras.langchain``。
P2 探针：``MockMcpAdapter`` / ``MockSandboxAdapter`` / ``MockCliAdapter``；
默认**不**进 ``ensure_default_capabilities``；启用见 ``probes.register_p2_probes``。
U3 真 MCP：``McpClientAdapter``（``OPS_CAPABILITY_MCP_ENABLED`` 默认关；CI 不外网）。
P3 skill：``SkillStubAdapter`` + ``register_skill_stub``；**非**完整引擎；
边界见 ``docs/guides/GUIDE_capability-gateway-p3-skill-boundary_v0.md``。
Mode A / filter 契约：``docs/guides/GUIDE_capability-portable-core-mode-a_v0.md``。

H4：``kind=http``（``GenericHttpAdapter``）+ 稳定错误码词表（``errors``）+
写操作闸（``side_effect``）。额外清单按 env 显式加载（``OPS_CAPABILITY_EXTRA_MANIFESTS``，
默认空 → 不动存量），与 U3 MCP 同一约定。
"""

from app.ops.capability.adapters import (
    EnvCredentialVault,
    FakeHttpTransport,
    FakeTransport,
    GenericHttpAdapter,
    HttpCapabilityError,
    HttpResponse,
    HttpTransport,
    LocalFnAdapter,
    McpClientAdapter,
    MockCliAdapter,
    MockMcpAdapter,
    MockSandboxAdapter,
    SkillStubAdapter,
    StaticCredentialVault,
    UrllibHttpTransport,
    register_mcp_client_if_enabled,
)
from app.ops.capability.baseline import (
    DEFAULT_KINDS,
    DOMAIN_ALLOW_TAGS,
    baseline_filter,
)
from app.ops.capability.defaults import ensure_default_capabilities
from app.ops.capability.errors import STABLE_ERROR_CODES
from app.ops.capability.gateway import (
    ainvoke,
    capability_catalog_snapshot,
    get_registry,
    invoke,
    list_capabilities,
    provide,
    register,
    schemas_for_llm,
    unregister,
)
from app.ops.capability.idempotency import (
    DEFAULT_LEASE_SECONDS,
    AsyncIdempotencyStore,
    DbIdempotencyStore,
    IdempotencyClaim,
    IdempotencyStore,
    InMemoryIdempotencyStore,
    NullIdempotencyStore,
    get_idempotency_store,
    reset_idempotency_store,
    set_idempotency_store,
)
from app.ops.capability.manifest import (
    BUILTIN_MANIFEST_PATH,
    MANIFEST_DIR,
    get_capability_manifest_metadata,
    load_capability_manifests,
    load_extra_manifests_from_env,
)
from app.ops.capability.probes import register_p2_probes
from app.ops.capability.persistence import (
    ENV_PERSISTENCE,
    configure_persistence_from_env,
    describe_persistence,
)
from app.ops.capability.receipts import (
    AsyncReceiptSink,
    DbReceiptSink,
    InMemoryReceiptSink,
    NullReceiptSink,
    Receipt,
    ReceiptSink,
    arecord_receipt,
    get_receipt_sink,
    reset_receipt_sink,
    set_receipt_sink,
)
from app.ops.capability.skill_stub import register_skill_stub
from app.ops.capability.types import (
    CapabilityFilter,
    CapabilityResult,
    CapabilitySpec,
    Principal,
)
from app.ops.capability.visibility import (
    check_visible,
    evaluate_visibility,
    filter_visible,
    principal_from_ctx,
)

ensure_default_capabilities()
# U3：仅当 OPS_CAPABILITY_MCP_ENABLED=true 且配置了 endpoint 才注册真 client
register_mcp_client_if_enabled()
# H4：仅当 OPS_CAPABILITY_EXTRA_MANIFESTS 显式列出清单文件才加载（默认空）
load_extra_manifests_from_env()
# W6：仅当 OPS_CAPABILITY_PERSISTENCE=db|memory 才启用防重与回执落库（默认不启用）
configure_persistence_from_env()

__all__ = [
    "BUILTIN_MANIFEST_PATH",
    "DEFAULT_KINDS",
    "DEFAULT_LEASE_SECONDS",
    "DOMAIN_ALLOW_TAGS",
    "ENV_PERSISTENCE",
    "MANIFEST_DIR",
    "STABLE_ERROR_CODES",
    "AsyncIdempotencyStore",
    "AsyncReceiptSink",
    "CapabilityFilter",
    "CapabilityResult",
    "CapabilitySpec",
    "DbIdempotencyStore",
    "DbReceiptSink",
    "EnvCredentialVault",
    "FakeHttpTransport",
    "FakeTransport",
    "GenericHttpAdapter",
    "HttpCapabilityError",
    "HttpResponse",
    "HttpTransport",
    "IdempotencyClaim",
    "IdempotencyStore",
    "InMemoryIdempotencyStore",
    "InMemoryReceiptSink",
    "LocalFnAdapter",
    "McpClientAdapter",
    "MockCliAdapter",
    "MockMcpAdapter",
    "MockSandboxAdapter",
    "NullIdempotencyStore",
    "NullReceiptSink",
    "Principal",
    "Receipt",
    "ReceiptSink",
    "SkillStubAdapter",
    "StaticCredentialVault",
    "UrllibHttpTransport",
    "ainvoke",
    "arecord_receipt",
    "baseline_filter",
    "capability_catalog_snapshot",
    "check_visible",
    "configure_persistence_from_env",
    "describe_persistence",
    "evaluate_visibility",
    "filter_visible",
    "get_capability_manifest_metadata",
    "get_idempotency_store",
    "get_receipt_sink",
    "get_registry",
    "invoke",
    "list_capabilities",
    "load_capability_manifests",
    "load_extra_manifests_from_env",
    "principal_from_ctx",
    "provide",
    "register",
    "register_mcp_client_if_enabled",
    "register_p2_probes",
    "register_skill_stub",
    "reset_idempotency_store",
    "reset_receipt_sink",
    "schemas_for_llm",
    "set_idempotency_store",
    "set_receipt_sink",
    "unregister",
]
