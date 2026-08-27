"""细 Intent schema v1（S2 · 喂给 Strategy Builder）。

与粗 router 三路（rag|direct|refuse）正交：本模型不是安全闸。
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class IntentV1(BaseModel):
    """细意图 v1：域 / 需否 tool·skill / 复合 / 风险提示 / 摘要。"""

    model_config = ConfigDict(extra="ignore")

    domain: Literal["ops_kb", "general", "unknown"] = Field(
        default="unknown",
        description="意图域：ops_kb / general / unknown",
    )
    needs_tool: bool = Field(default=False, description="是否需要调用工具")
    needs_skill: bool = Field(default=False, description="是否需要 Skill 注入")
    is_composite: bool = Field(default=False, description="是否为复合任务")
    risk_hint: Literal["low", "medium", "high"] = Field(
        default="low",
        description="风险提示：low / medium / high；不得绕过 Policy",
    )
    summary: str = Field(default="", description="一句话意图摘要")
