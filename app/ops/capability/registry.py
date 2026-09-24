"""Capability Registry · 注册 / 注销 / 筛选列表。

重复 id 行为（P0 钉死）：
- ``register`` 时若 ``capability_id`` 已存在 → **拒绝覆盖**，raise ``ValueError``。
- 需要替换：先 ``unregister(id)`` 再 ``register``；禁止静默覆盖，以免重复注册掩盖启动/测试 bug。

V1-E（host-v1-splittability-hardening · D3）：读写分离协议
``RegistryReader`` / ``RegistryWriter``；本地 dict 实现仍为本类
（语义原样 · 对拍零 diff）。远程注册中心客户端属 v2.0，本波只留接口。
"""

from __future__ import annotations

from dataclasses import replace
from typing import Any, Protocol, runtime_checkable

from app.ops.capability.types import (
    WRITE_SIDE_EFFECTS,
    CapabilityFilter,
    CapabilitySpec,
)


class CapabilityAdapter(Protocol):
    """执行后端最小协议（P0：LocalFnAdapter）。"""

    kind: str

    def invoke(self, args: Any, *, ctx: dict[str, Any] | None = None) -> Any: ...


@runtime_checkable
class RegistryReader(Protocol):
    """读侧协议（本地缓存 / 未来远程只读客户端形态）。"""

    def get(
        self, capability_id: str
    ) -> tuple[CapabilitySpec, CapabilityAdapter] | None: ...

    def list_specs(
        self, *, filter: CapabilityFilter | None = None
    ) -> list[CapabilitySpec]: ...

    def snapshot(self) -> dict[str, Any]: ...


@runtime_checkable
class RegistryWriter(Protocol):
    """写侧协议（注册中心客户端形态 · 本地 dict 默认同义封装）。"""

    def register(self, spec: CapabilitySpec, adapter: CapabilityAdapter) -> None: ...

    def unregister(self, capability_id: str) -> bool: ...

    def reload(self) -> None: ...


class CapabilityRegistry:
    """进程内注册表（单例见 ``gateway`` 模块）· 默认 ``RegistryReader``+``RegistryWriter``。"""

    def __init__(self) -> None:
        self._entries: dict[str, tuple[CapabilitySpec, CapabilityAdapter]] = {}

    def register(self, spec: CapabilitySpec, adapter: CapabilityAdapter) -> None:
        cid = (spec.capability_id or "").strip()
        if not cid:
            raise ValueError("capability_id 不能为空")
        if cid in self._entries:
            # 钉死：拒绝覆盖（见模块 docstring）
            raise ValueError(f"capability_id 已注册: {cid}")
        if spec.capability_id != cid:
            # 用手工重建会**静默丢字段**（历史 bug：tenant_scoped 曾被漏掉）。
            # 新增 side_effect / http / hitl_required 等字段后风险更大 → 一律用 replace。
            spec = replace(spec, capability_id=cid)
        self._entries[cid] = (spec, adapter)

    def unregister(self, capability_id: str) -> bool:
        return self._entries.pop(capability_id, None) is not None

    def get(
        self, capability_id: str
    ) -> tuple[CapabilitySpec, CapabilityAdapter] | None:
        return self._entries.get(capability_id)

    def list_specs(
        self, *, filter: CapabilityFilter | None = None
    ) -> list[CapabilitySpec]:
        specs = [spec for spec, _ in self._entries.values()]
        if filter is None:
            return list(specs)
        return [s for s in specs if _match_filter(s, filter)]

    def snapshot(self) -> dict[str, Any]:
        """只读摘要（id 有序列表 + 计数）；不暴露 adapter。"""
        ids = sorted(self._entries.keys())
        return {
            "capability_ids": ids,
            "count": len(ids),
            "backend": "local_dict",
            "scope": "process-local",
        }

    def reload(self) -> None:
        """本地 dict：清空条目（远程实现将拉取并重建；本波不实现远程）。"""
        self._entries.clear()

    def clear(self) -> None:
        """测试用：清空注册表（与 ``reload`` 同义 · 保留历史调用面）。"""
        self._entries.clear()


def _match_filter(spec: CapabilitySpec, f: CapabilityFilter) -> bool:
    """可见集裁剪（SPEC §3.3）。

    判序：形态 → 风险 → 副作用 → 标签收窄。``allow_tags_any`` 只作用于**第一层**
    （豁免 kinds 裁剪），不放宽后面的 deny_* —— 否则它就成了「一个 tag 换全部豁免」。
    """
    if not spec.enabled:
        return False
    if f.kinds is not None and spec.kind not in f.kinds:
        exempt = bool(
            f.allow_tags_any and f.allow_tags_any.intersection(spec.tags)
        )
        if not exempt:
            return False
    if f.deny_high_risk and spec.risk_level == "high":
        return False
    if f.deny_write and spec.side_effect in WRITE_SIDE_EFFECTS:
        return False
    # node_role / mode：P0 仅占位字段，不裁剪（无 tags 绑定时全放行）
    if f.tags_any is None:
        return True
    return bool(f.tags_any.intersection(spec.tags))
