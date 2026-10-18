"""Router 意图分类 schema。"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class RouteDecision(BaseModel):
    """router LLM 结构化出口：三路白名单。"""

    model_config = ConfigDict(extra="ignore")

    route: Literal["rag", "direct", "refuse"] = Field(description="意图路由：rag / direct / refuse")
