"""Supervisor 子任务拆解 schema。"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class SubtaskItem(BaseModel):
    """单个子任务；type 白名单规整在节点侧（非法 → rag）。

    ``args``：可选结构化参数；``tool_exec`` 优先传 Gateway，兼容仅 ``input``。
    """

    model_config = ConfigDict(extra="ignore")

    # Q4 步骤契约：两者都可选，不声明 ⇒ 不校验（契约不推测，见 step_contract 第 1 条）
    id: str | None = None
    type: str | None = None
    input: str = Field(..., min_length=1)
    tool: str | None = None
    args: dict[str, Any] | None = None
    depends_on: list[str] | None = None
    produces: list[str] | None = None
    consumes: dict[str, Any] | None = None


class SubtasksPlan(BaseModel):
    """supervisor LLM 结构化出口。

    ``subtasks`` 元素先以 ``Any`` 收下，再由节点对前 ``MAX_SUBTASKS`` 项
    做 ``SubtaskItem`` 校验——避免 cap 外坏项把整单打成 fallback。
    """

    model_config = ConfigDict(extra="ignore")

    subtasks: list[Any] = Field(..., min_length=1)
