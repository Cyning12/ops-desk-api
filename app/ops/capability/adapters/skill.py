"""Skill kind 预留 adapter（Capability Gateway · P3）。

区分两类表面（SPEC §4 P3）：

- ``provide(*, ctx)``：注入 Skill **上下文**（给人 / 节点读的说明或片段）
- ``invoke(args, *, ctx)``：跑 Skill **可执行步骤**（完整引擎 · **本波未实现**）

**非**完整 Skill 执行引擎；**不**等同 ``docs/skills/`` 仓内人读 Skill 包。
边界见 ``docs/guides/GUIDE_capability-gateway-p3-skill-boundary_v0.md``。
"""

from __future__ import annotations

from typing import Any


class SkillStubAdapter:
    """``kind=skill`` 接口 stub：``provide`` 可用；``invoke`` 显式未实现引擎。"""

    kind = "skill"

    def __init__(
        self,
        *,
        skill_ref: str = "",
        skill_id: str = "",
    ) -> None:
        """``skill_ref``：可选指向仓内路径（如 ``docs/skills/s-l0-project-map``），仅作元数据。"""
        self.skill_ref = skill_ref
        self.skill_id = skill_id

    def provide(self, *, ctx: dict[str, Any] | None = None) -> dict[str, Any]:
        """预留：注入上下文（stub · 不读盘、不执行步骤）。"""
        return {
            "mode": "provide",
            "skill_id": self.skill_id,
            "skill_ref": self.skill_ref,
            "context": (
                f"[stub] skill context for {self.skill_id or self.skill_ref or '(unnamed)'}"
            ),
            "ctx_keys": sorted((ctx or {}).keys()),
            "engine": "stub",
            "note": (
                "P3 stub · provide 仅注入占位上下文；人读 Skill 见 docs/skills/；完整执行引擎未实现"
            ),
        }

    def invoke(self, args: Any, *, ctx: dict[str, Any] | None = None) -> Any:
        """预留：可执行步骤。P3 **未**实现完整引擎 → ``NotImplementedError``。"""
        del args, ctx
        raise NotImplementedError("kind=skill invoke() 预留：完整 Skill 执行引擎未实现（P3 stub）")
