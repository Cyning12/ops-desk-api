"""Capability args 最小 JSON Schema 校验（有 ``args_schema`` 才跑）。

仅支持本仓默认能力所需子集：``type``（含 union list）、``properties``、
``required``、``additionalProperties``。业务不变量（涨跌幅等）**禁止**写进
``args_schema``——见 ``docs/standards/CODING_BACKEND_L2_v1_zh.md`` P-16 与
本包 docstring。Gateway 只做形态校验，不做领域规则。
"""

from __future__ import annotations

from typing import Any


def validate_capability_args(
    args: Any,
    schema: dict[str, Any] | None,
) -> str | None:
    """校验 ``args``；通过返回 ``None``，失败返回含 ``args_schema_invalid`` 的错误串。

    ``schema is None`` → 不做参数 schema 校验（钉死：无 schema 可调用）。
    """
    if schema is None:
        return None
    ok, detail = _match(args, schema)
    if ok:
        return None
    return f"args_schema_invalid: {detail}"


def _type_names(schema: dict[str, Any]) -> list[str] | None:
    raw = schema.get("type")
    if raw is None:
        return None
    if isinstance(raw, list):
        return [str(t) for t in raw]
    return [str(raw)]


def _match(value: Any, schema: dict[str, Any]) -> tuple[bool, str]:
    types = _type_names(schema)
    if types is not None:
        if not any(_is_type(value, t) for t in types):
            return False, f"期望 type={types}，实际={type(value).__name__}"
        # union：选第一个匹配的分支做后续约束（object 才查 properties）
        if "object" in types and isinstance(value, dict):
            return _match_object(value, schema)
        return True, ""
    if isinstance(value, dict):
        return _match_object(value, schema)
    return True, ""


def _is_type(value: Any, type_name: str) -> bool:
    if type_name == "null":
        return value is None
    if type_name == "string":
        return isinstance(value, str)
    if type_name == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if type_name == "number":
        return isinstance(value, int | float) and not isinstance(value, bool)
    if type_name == "boolean":
        return isinstance(value, bool)
    if type_name == "object":
        return isinstance(value, dict)
    if type_name == "array":
        return isinstance(value, list)
    return True


def _match_object(value: dict[str, Any], schema: dict[str, Any]) -> tuple[bool, str]:
    props = schema.get("properties")
    if not isinstance(props, dict):
        props = {}
    required = schema.get("required") or []
    if not isinstance(required, list):
        return False, "required 必须是 list"
    for key in required:
        if key not in value:
            return False, f"缺必填字段: {key}"
    for key, prop_schema in props.items():
        if key not in value:
            continue
        if not isinstance(prop_schema, dict):
            continue
        prop_types = _type_names(prop_schema)
        if prop_types is None:
            continue
        if not any(_is_type(value[key], t) for t in prop_types):
            return (
                False,
                f"字段 {key} 期望 type={prop_types}，实际={type(value[key]).__name__}",
            )
    additional = schema.get("additionalProperties", True)
    if additional is False:
        allowed = set(props.keys())
        extra = [k for k in value if k not in allowed]
        if extra:
            return False, f"禁止额外字段: {extra}"
    return True, ""
