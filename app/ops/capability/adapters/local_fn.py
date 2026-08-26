"""local_fn adapter：进程内可调用对象。"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any


class LocalFnAdapter:
    """同步本地函数适配器；``invoke(args)`` 将 args 作为唯一位置参数传入 fn。"""

    kind = "local_fn"

    def __init__(self, fn: Callable[[Any], Any]) -> None:
        self._fn = fn

    def invoke(self, args: Any, *, ctx: dict[str, Any] | None = None) -> Any:
        del ctx  # P0 未用；预留策略/审批上下文
        return self._fn(args)
