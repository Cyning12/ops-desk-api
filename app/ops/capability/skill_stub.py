"""P3 skill stub 注册辅助（kind=skill · provide / invoke 预留）。

默认：**不**在 ``ensure_default_capabilities`` 中注册。

开启::

    from app.ops.capability.skill_stub import register_skill_stub
    from app.ops.capability import provide, invoke

    register_skill_stub(enabled=True)
    r = provide("stub_skill_s_l0_project_map")
    assert r.ok  # provide 注入 stub 上下文

    inv = invoke("stub_skill_s_l0_project_map", None)
    assert inv.ok is False  # invoke → NotImplementedError → ok=False
"""

from __future__ import annotations

from app.ops.capability.adapters.skill import SkillStubAdapter
from app.ops.capability.gateway import get_registry, register
from app.ops.capability.types import CapabilitySpec

# 稳定 id（单测 / 文档引用）
STUB_SKILL_ID = "stub_skill_s_l0_project_map"
# 与 docs/skills/ 对齐的「引用」元数据（不自动加载 / 不执行）
STUB_SKILL_REF = "docs/skills/s-l0-project-map"


def register_skill_stub(*, enabled: bool = False) -> list[str]:
    """幂等注册 skill stub；``enabled`` 默认 False（list 不可见 / provide·invoke blocked）。

    返回本次新注册的 capability_id 列表（已存在则跳过）。
    """
    registry = get_registry()
    if registry.get(STUB_SKILL_ID) is not None:
        return []
    spec = CapabilitySpec(
        capability_id=STUB_SKILL_ID,
        kind="skill",
        description=(
            "P3 stub：kind=skill（provide 注入上下文 / invoke 可执行步骤预留；"
            "非完整引擎；边界见 GUIDE_capability-gateway-p3-skill-boundary）"
        ),
        tags=("stub", "skill", "p3"),
        risk_level="low",
        enabled=enabled,
    )
    adapter = SkillStubAdapter(
        skill_id=STUB_SKILL_ID,
        skill_ref=STUB_SKILL_REF,
    )
    register(spec, adapter)
    return [STUB_SKILL_ID]
