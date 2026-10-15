"""lg-rag StreamSubscriber：HTTP SSE 只读 fanout / 已落盘事件。

断连（generator aclose / 请求 cancel）**只**取消本订阅，不 cancel RunWorker。
"""
from __future__ import annotations

import asyncio
import contextlib
import logging
from collections.abc import AsyncIterator
from typing import Any

from app.ops.lg_rag.run_worker import (
    RunEventBus,
    bus_end_sentinel,
    get_run_bus,
)

logger = logging.getLogger(__name__)


async def subscribe_run_sse(
    run_id: str,
    *,
    bus: RunEventBus | None = None,
    keepalive_interval_s: float | None = None,
) -> AsyncIterator[str]:
    """订阅 ``run_id`` 的 SSE 帧直至 worker 收尾哨兵。

    ``bus`` 缺省时从进程内 registry 取；无 bus（worker 已 GC）则空流结束。
    订阅者 aclose / CancelledError → 仅 unsubscribe，不碰 worker task。
    """
    # 延迟导入：避免与 sse_stream.iter → subscribe 环依赖
    from app.ops.lg_rag import sse_stream as _sse_mod

    active = bus or get_run_bus(run_id)
    if active is None:
        logger.warning("lg-rag subscribe: no bus for run_id=%s", run_id)
        return

    # 经模块属性读间隔，便于单测 patch sse_stream._KEEPALIVE_INTERVAL_S
    interval = (
        _sse_mod._KEEPALIVE_INTERVAL_S
        if keepalive_interval_s is None
        else keepalive_interval_s
    )
    q = active.subscribe()
    end = bus_end_sentinel()
    try:
        while True:
            try:
                item: Any = await asyncio.wait_for(q.get(), timeout=interval)
            except TimeoutError:
                yield _sse_mod._KEEPALIVE_FRAME
                continue
            if item is end:
                break
            if isinstance(item, str):
                yield item
    except (GeneratorExit, asyncio.CancelledError):
        logger.info(
            "lg-rag subscriber cancelled run_id=%s (worker untouched)", run_id
        )
        raise
    finally:
        active.unsubscribe(q)


async def drain_subscribe(
    agen: AsyncIterator[str],
) -> list[str]:
    """测试辅助：读尽订阅流（忽略 keepalive comment）。"""
    frames: list[str] = []
    async for raw in agen:
        if raw.startswith(":"):
            continue
        frames.append(raw)
    return frames


@contextlib.asynccontextmanager
async def closing_subscribe(agen: AsyncIterator[str]):
    """确保 subscribe 生成器 aclose（不 cancel worker）。"""
    try:
        yield agen
    finally:
        aclose = getattr(agen, "aclose", None)
        if aclose is not None:
            with contextlib.suppress(Exception):
                await aclose()
