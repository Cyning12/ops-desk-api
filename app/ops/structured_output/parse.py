"""parse_only：extract →（可选）deterministic repair → Pydantic → ensure_keys → validate。"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, ValidationError

from app.ops.structured_output.extract import extract_json_object, strip_code_fences
from app.ops.structured_output.repair import deterministic_repair

T = TypeVar("T", bound=BaseModel)

# validate：返回 None 表示通过；返回非空 str 为失败 reason（进入 Host 失败路径 / correction）
ValidateFn = Callable[[BaseModel], str | None]


@dataclass(frozen=True)
class ParseOutcome(Generic[T]):
    """结构化解析结果。失败时 ``data`` 恒为 ``None``（Host 权威：无半成功业务数据）。"""

    ok: bool
    data: T | None = None
    error: str | None = None
    repaired: bool = False

    @property
    def success(self) -> bool:
        return self.ok


def _try_extract_with_optional_repair(text: str) -> tuple[dict | None, bool]:
    """先直接提取；失败则对候选文本做 deterministic repair 后再提取。"""
    obj = extract_json_object(text)
    if obj is not None:
        return obj, False

    # 对剥 fence 后的全文做结构修复（含杂讯包围时再抽对象）
    candidate = strip_code_fences((text or "").strip())
    repaired_text = deterministic_repair(candidate)
    if repaired_text == candidate:
        return None, False

    obj = extract_json_object(repaired_text)
    if obj is not None:
        return obj, True

    # 杂讯 + 坏结构：先抓最外层 {...} 再 repair
    start = repaired_text.find("{")
    end = repaired_text.rfind("}")
    if start >= 0 and end > start:
        fragment = deterministic_repair(repaired_text[start : end + 1])
        obj = extract_json_object(fragment)
        if obj is not None:
            return obj, True

    return None, True


def _walk_dot_path(payload: Any, path: str) -> tuple[bool, Any]:
    """按点分路径取值。

    路径约定（v0）：
    - 使用 ``a.b.c`` 点分键名，在 ``model_dump()`` 得到的嵌套 ``dict`` 上逐段查找。
    - 每一段必须是映射键；**不支持**列表下标（如 ``items.0.id``）。
    - 空路径或含空段（如 ``a..b``）视为非法，按 missing 失败。
    - presence：段缺失 → 失败；not_null：值 ``None`` → 失败。
    """
    if not path or ".." in path or path.startswith(".") or path.endswith("."):
        return False, None
    cur: Any = payload
    for segment in path.split("."):
        if not segment:
            return False, None
        if not isinstance(cur, dict) or segment not in cur:
            return False, None
        cur = cur[segment]
    return True, cur


def check_ensure_keys(payload: dict[str, Any], keys: Sequence[str]) -> str | None:
    """检查必填路径 presence / not_null。通过返回 ``None``，否则返回失败 reason。"""
    for path in keys:
        found, value = _walk_dot_path(payload, path)
        if not found:
            return f"ensure_keys: missing path '{path}'"
        if value is None:
            return f"ensure_keys: path '{path}' is null"
    return None


def parse_only(
    text: str,
    *,
    schema: type[T],
    ensure_keys: Sequence[str] | None = None,
    validate: Callable[[T], str | None] | None = None,
) -> ParseOutcome[T]:
    """无 LLM 的结构化解析管道：extract → repair → Pydantic → ensure_keys → validate。

    Schema / ensure / custom validate 均在 Host 执行；失败时返回 ``ok=False`` 且 ``data=None``。
    """
    obj, repaired = _try_extract_with_optional_repair(text)
    if obj is None:
        return ParseOutcome(
            ok=False,
            data=None,
            error="unable to extract JSON object",
            repaired=repaired,
        )
    try:
        model = schema.model_validate(obj)
    except ValidationError as exc:
        return ParseOutcome(
            ok=False,
            data=None,
            error=str(exc),
            repaired=repaired,
        )

    if ensure_keys:
        dumped = model.model_dump()
        ensure_err = check_ensure_keys(dumped, ensure_keys)
        if ensure_err is not None:
            return ParseOutcome(
                ok=False,
                data=None,
                error=ensure_err,
                repaired=repaired,
            )

    if validate is not None:
        reason = validate(model)
        if reason:
            return ParseOutcome(
                ok=False,
                data=None,
                error=reason,
                repaired=repaired,
            )

    return ParseOutcome(ok=True, data=model, error=None, repaired=repaired)
