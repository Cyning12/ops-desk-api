"""Capability Gateway · 契约类型（SPEC §3）。"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class CapabilitySpec:
    """注册表条目（SPEC §3.1）。"""

    capability_id: str
    kind: str
    description: str
    args_schema: dict[str, Any] | None = None
    tags: tuple[str, ...] = ()
    risk_level: str = "low"  # low | medium | high
    enabled: bool = True


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
