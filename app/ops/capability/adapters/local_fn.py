"""local_fn adapter：进程内可调用对象。"""

from __future__ import annotations

import inspect
from collections.abc import Callable
from typing import Any


class LocalFnAdapter:
    """本地函数适配器；``invoke`` / ``ainvoke`` 将 args 作为唯一位置参数传入 fn。

    异步 fn 须走 ``ainvoke``（P-13）；同步 ``invoke`` 对其抛 TypeError。
    """

    kind = "local_fn"

    def __init__(self, fn: Callable[[Any], Any]) -> None:
        self._fn = fn

    def invoke(self, args: Any, *, ctx: dict[str, Any] | None = None) -> Any:
        del ctx  # P0 未用；预留策略/审批上下文
        if inspect.iscoroutinefunction(self._fn):
            raise TypeError("async local_fn 请使用 ainvoke")
        return self._fn(args)

    async def ainvoke(self, args: Any, *, ctx: dict[str, Any] | None = None) -> Any:
        del ctx
        result = self._fn(args)
        if inspect.isawaitable(result):
            return await result
        return result
