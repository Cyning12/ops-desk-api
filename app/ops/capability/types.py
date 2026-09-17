"""Capability Gateway · 契约类型（SPEC §3）。

进程内**注册表**条目（非跨进程「注册中心」）。``args_schema`` 仅描述参数形态；
业务不变量不进 schema（见 CODING P-16）。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class CapabilitySpec:
    """进程内注册表条目（SPEC §3.1）。"""

    capability_id: str
    kind: str
    description: str
    args_schema: dict[str, Any] | None = None
    tags: tuple[str, ...] = ()
    risk_level: str = "low"  # low | medium | high
    enabled: bool = True
    # True：invoke 须 ctx 含租户谓词（tenant_id / _host_tenant）；缺则拒
    tenant_scoped: bool = False


@dataclass(frozen=True)
class CapabilityFilter:
    """可见集合裁剪（SPEC §3.3 · v0 最小）。"""

    node_role: str | None = None
    mode: str | None = None
    tags_any: frozenset[str] | None = None
    kinds: frozenset[str] | None = None
    deny_high_risk: bool = False


@dataclass
class CapabilityResult:
    """统一 invoke 结果（SPEC §3.2）。"""

    ok: bool
    output: Any = None
    error: str | None = None
    capability_id: str = ""
    duration_ms: float | None = None
    meta: dict[str, Any] = field(default_factory=dict)
