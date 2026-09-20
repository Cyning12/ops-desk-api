"""极简 JSONPath 子集（``$`` / ``$.a.b`` / ``$.a[0].b``）。

**为什么单独成模块**：``receipt_capture``（回执抓取）、``success_when``（成功判定）、
``output_schema``（结果契约，P0-1）三处都要按路径取值——各写一份迟早漂移，
而漂移的表现是"回执抓到了但契约说缺字段"这种自相矛盾的结论。

取不到一律返回 :data:`MISSING`（**不是 None**）——"字段存在但值是 null" 与
"字段根本不存在" 必须能区分，否则契约会把缺失当成空值放过。
"""

from __future__ import annotations

from typing import Any, Final


class _Missing:
    """哨兵：路径不存在。"""

    __slots__ = ()

    def __repr__(self) -> str:  # pragma: no cover - 调试用
        return "MISSING"

    def __bool__(self) -> bool:
        return False


MISSING: Final[Any] = _Missing()


def jsonpath_get(data: Any, expr: str) -> Any:
    """按 expr 取值；取不到返回 :data:`MISSING`。"""
    path = str(expr or "").strip()
    if path in ("", "$"):
        return data
    if path.startswith("$"):
        path = path[1:]
    if path.startswith("."):
        path = path[1:]
    cur = data
    for token in [t for t in path.split(".") if t]:
        name, _, indexes = token.partition("[")
        if name:
            if not isinstance(cur, dict) or name not in cur:
                return MISSING
            cur = cur[name]
        while indexes:
            idx_str, _, rest = indexes.partition("]")
            try:
                idx = int(idx_str)
            except ValueError:
                return MISSING
            if not isinstance(cur, list) or idx >= len(cur) or idx < -len(cur):
                return MISSING
            cur = cur[idx]
            indexes = rest.lstrip("[").lstrip("]")
    return cur
