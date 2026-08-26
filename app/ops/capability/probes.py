"""P2 探针注册辅助（MCP / sandbox / cli · mock）。

默认：**不**在 ``ensure_default_capabilities`` 中注册，避免 CI 误开外网路径。

开启方式（本地 smoke）::

    from app.ops.capability.probes import register_p2_probes
    register_p2_probes(enabled=True)   # 测试 / 本地显式开启
    # 或 enabled=False：仅登记；带 filter 的 list 不可见；invoke → blocked

关闭：``unregister`` 各 capability_id，或进程重启后默认即无探针。

真 MCP client（U3）与本模块无关：见 ``adapters.mcp_client`` +
``OPS_CAPABILITY_MCP_ENABLED``（默认关；CI 不外网）。

可选：日后将 ``app.tools.run_code.run_bash`` 包进 cli adapter 时，仍须
``enabled=False`` 且**禁止**写入 defaults。
"""

from __future__ import annotations

from app.ops.capability.adapters.cli import MockCliAdapter
from app.ops.capability.adapters.mcp import MockMcpAdapter
from app.ops.capability.adapters.sandbox import MockSandboxAdapter
from app.ops.capability.gateway import get_registry, register
from app.ops.capability.registry import CapabilityAdapter
from app.ops.capability.types import CapabilitySpec

# 稳定 id（单测 / 文档引用）
PROBE_MCP_ID = "probe_mcp_echo"
PROBE_SANDBOX_ID = "probe_sandbox_echo"
PROBE_CLI_ID = "probe_cli_echo"

_PROBE_SPECS: list[tuple[str, CapabilitySpec, CapabilityAdapter]] = [
    (
        PROBE_MCP_ID,
        CapabilitySpec(
            capability_id=PROBE_MCP_ID,
            kind="mcp",
            description="P2 探针：MCP mock（罐头，无外网）",
            tags=("probe", "mcp", "p2"),
            risk_level="low",
            enabled=False,
        ),
        MockMcpAdapter(),
    ),
    (
        PROBE_SANDBOX_ID,
        CapabilitySpec(
            capability_id=PROBE_SANDBOX_ID,
            kind="sandbox",
            description="P2 探针：sandbox mock（无子进程）",
            tags=("probe", "sandbox", "p2"),
            risk_level="medium",
            enabled=False,
        ),
        MockSandboxAdapter(),
    ),
    (
        PROBE_CLI_ID,
        CapabilitySpec(
            capability_id=PROBE_CLI_ID,
            kind="cli",
            description="P2 探针：cli mock（无 subprocess）",
            tags=("probe", "cli", "p2"),
            risk_level="medium",
            enabled=False,
        ),
        MockCliAdapter(),
    ),
]


def register_p2_probes(*, enabled: bool = False) -> list[str]:
    """幂等注册三 kind 探针；``enabled`` 默认 False（list 不可见 / invoke blocked）。

    返回本次新注册的 capability_id 列表（已存在则跳过）。
    """
    registry = get_registry()
    newly: list[str] = []
    for cid, base_spec, adapter in _PROBE_SPECS:
        if registry.get(cid) is not None:
            continue
        spec = CapabilitySpec(
            capability_id=base_spec.capability_id,
            kind=base_spec.kind,
            description=base_spec.description,
            args_schema=base_spec.args_schema,
            tags=base_spec.tags,
            risk_level=base_spec.risk_level,
            enabled=enabled,
        )
        register(spec, adapter)
        newly.append(cid)
    return newly
