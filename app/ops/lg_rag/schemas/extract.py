"""info_extract 抽取结果 schema。"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


def _coerce_str_list(value: Any) -> list[str]:
    """对齐历史：非 list → 空；list 元素一律 str。"""
    if not isinstance(value, list):
        return []
    return [str(v) for v in value]


class ExtractResult(BaseModel):
    """信息抽取结构化出口；缺字段默认空列表。"""

    model_config = ConfigDict(extra="ignore")

    dates: list[str] = Field(default_factory=list)
    versions: list[str] = Field(default_factory=list)
    people: list[str] = Field(default_factory=list)

    @field_validator("dates", "versions", "people", mode="before")
    @classmethod
    def _list_fields(cls, value: Any) -> list[str]:
        if value is None:
            return []
        return _coerce_str_list(value)
