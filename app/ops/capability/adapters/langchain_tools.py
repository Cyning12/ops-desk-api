"""可选 LangChain StructuredTool / ToolNode 适配（Capability Gateway · P1）。

**可选探针**：供 ``bind_tools`` / 原生 FC 子图 smoke；**不**强制挂
``app/ops/lg_rag/multi/graph.py`` 或 ``lg_rag`` 主路径拓扑（plan 直调
``invoke`` 与 FC 双路径并存时以节点编排为准，本模块不改图）。

无 ``args_schema``：与 ``schemas_for_llm`` 一致，**跳过**（不生成 tool）。
"""

from __future__ import annotations

from typing import Any

from langchain_core.tools import BaseTool, StructuredTool
from langgraph.prebuilt import ToolNode
from pydantic import BaseModel, Field, create_model

from app.ops.capability.gateway import invoke, list_capabilities
from app.ops.capability.types import CapabilityFilter, CapabilitySpec

_TYPE_MAP: dict[str, type] = {
    "string": str,
    "integer": int,
    "number": float,
    "boolean": bool,
    "object": dict,
    "array": list,
}


def _model_from_json_schema(name: str, schema: dict[str, Any]) -> type[BaseModel]:
    """最小 JSON Schema → Pydantic（仅 object + properties；P1 smoke）。"""
    props = schema.get("properties") or {}
    required = set(schema.get("required") or [])
    fields: dict[str, Any] = {}
    for key, prop in props.items():
        prop_d = prop if isinstance(prop, dict) else {}
        py_type = _TYPE_MAP.get(str(prop_d.get("type", "string")), str)
        desc = prop_d.get("description")
        if key in required:
            fields[key] = (py_type, Field(description=desc))
        else:
            fields[key] = (py_type | None, Field(default=None, description=desc))
    safe = "".join(c if c.isalnum() or c == "_" else "_" for c in name) or "Capability"
    return create_model(f"{safe}_Args", **fields)  # type: ignore[call-overload]


def _spec_to_structured_tool(spec: CapabilitySpec) -> StructuredTool:
    cid = spec.capability_id
    assert spec.args_schema is not None  # 调用方已过滤

    def _call(**kwargs: Any) -> Any:
        result = invoke(cid, kwargs)
        if not result.ok:
            raise RuntimeError(result.error or f"capability failed: {cid}")
        return result.output

    return StructuredTool(
        name=cid,
        description=spec.description,
        func=_call,
        args_schema=_model_from_json_schema(cid, spec.args_schema),
    )


def as_structured_tools(
    *, filter: CapabilityFilter | None = None
) -> list[BaseTool]:
    """将可见且带 ``args_schema`` 的能力转为 StructuredTool 列表（可选）。

    无 args_schema → 跳过（与 ``schemas_for_llm`` 钉死行为一致）。
    """
    tools: list[BaseTool] = []
    for spec in list_capabilities(filter=filter):
        if spec.args_schema is None:
            continue
        tools.append(_spec_to_structured_tool(spec))
    return tools


def as_tool_node(*, filter: CapabilityFilter | None = None) -> ToolNode:
    """薄封装：``ToolNode(as_structured_tools(...))``；**不**接入主图。"""
    return ToolNode(as_structured_tools(filter=filter))
