"""Critic 判定 schema（S4 · 规则 stub；本波不接 LLM）。"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

CriticOutcome = Literal["pass", "retry_planner", "rebind", "end"]


class CriticVerdict(BaseModel):
    """规则 stub 产出的判定；供后波 LLM Critic 复用同一形状。"""

    model_config = ConfigDict(extra="ignore")

    outcome: CriticOutcome = Field(description="pass / retry_planner / rebind / end")
    reason: str = Field(default="", description="简短原因码")
