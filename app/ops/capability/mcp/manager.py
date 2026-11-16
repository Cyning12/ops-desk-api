"""P2b-T2 · `McpSessionManager`：进程级单例，挂 `app.state.mcp_sessions`（main.py lifespan）。

生命周期纪律（11 终稿 §5.1 + 委派书 §4-E 三条）
---------------------------------------------
- `start()`：遍历 mcp_servers.yaml 配置**并发建连**；单 server 失败 warn 跳过，
  不影响其余（§4-B 降级隔离 · §10）。
- `aclose()`：**逆序** close 全部 session；若在途建连则取消之（取消感知：
  子任务清理半成品 transport 后重抛 CancelledError）；aclose 后才完成的连接
  **立即 close 不入池**（迟关闭）。
- **并发去重**：同 key 同时只允许一条在建连接（`_inflight` 单 flight）。
- 总闸 off 时 lifespan 零创建本对象（main.py 侧保证 · TestClient 零 diff）。

R5c unregister 接口面（**T3 挂点 · 本单无 mcp.* 条目可注销**）
----------------------------------------------------------
构造注入 `unregister_hook: Callable[[str], None]`：aclose 时对每个已建连 server
以 `server_key` 回调一次。T3 落地后由 main.py lifespan 注入「遍历 capability
registry 摘除 `mcp.{server_key}.*` 条目」的实现（承 §5.1 shutdown 逆序
close+unregister mcp:// 条目）。本单 hook 缺省 None = no-op。
"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Callable

from app.ops.capability.mcp.errors import McpProtocolError
from app.ops.capability.mcp.session import McpSession
from app.ops.capability.mcp.transport import (
    HttpTransport,
    McpTransport,
    StdioTransport,
)
from app.ops.capability.mcp_config import McpServerConfig

logger = logging.getLogger(__name__)

TransportFactory = Callable[[McpServerConfig], McpTransport]


def default_transport_factory(config: McpServerConfig) -> McpTransport:
    """按 config.transport 建实现（config 层已拒未知词表，此处双保险）。"""
    if config.transport == "stdio":
        return StdioTransport(
            command=config.command or "",
            args=config.args,
            cwd=config.cwd,
            env_allowlist=config.env_allowlist,
        )
    if config.transport == "http":
        return HttpTransport(url=config.url or "")
    raise McpProtocolError(f"未知 transport: {config.transport!r}")


class McpSessionManager:
    """MCP 会话管理器（进程级单例 · 不读 settings · 配置由 lifespan 注入）。"""

    def __init__(
        self,
        configs: tuple[McpServerConfig, ...] | list[McpServerConfig],
        *,
        transport_factory: TransportFactory | None = None,
        unregister_hook: Callable[[str], None] | None = None,
    ) -> None:
        self._configs = tuple(configs)
        self._factory = transport_factory or default_transport_factory
        self._unregister_hook = unregister_hook
        self._sessions: dict[str, McpSession] = {}
        self._inflight: dict[str, asyncio.Task[None]] = {}
        self._started = False
        self._closed = False

    # ---- 查询面 ----

    def get_session(self, key: str) -> McpSession | None:
        """取已建连 session；未建立返回 None（T3 转 ok=False mcp_session_unavailable）。"""
        return self._sessions.get(key)

    def connected_keys(self) -> tuple[str, ...]:
        return tuple(self._sessions.keys())

    # ---- 生命周期 ----

    async def start(self) -> None:
        """并发建连全部配置 server；单 server 失败 warn 跳过（隔离）。"""
        if self._started or self._closed:
            return
        self._started = True
        results = await asyncio.gather(
            *(self._connect_one(c) for c in self._configs), return_exceptions=True
        )
        for config, res in zip(self._configs, results, strict=True):
            if isinstance(res, asyncio.CancelledError):
                # 外层取消已由 gather 正常传播；走到这里说明子任务自抛取消——记 warn
                logger.warning("mcp server=%s 建连被取消", config.key)

    async def aclose(self) -> None:
        """逆序关闭全部 session + 取消在途建连 + unregister_hook 回调（T3 挂点）。幂等。"""
        if self._closed:
            return
        self._closed = True
        # 先取消在途建连并等其收尾（子任务自清半成品 transport）
        inflight = list(self._inflight.values())
        for task in inflight:
            task.cancel()
        if inflight:
            await asyncio.gather(*inflight, return_exceptions=True)
        # 逆序 close（§5.1 shutdown 逆序）
        for key in reversed(list(self._sessions.keys())):
            session = self._sessions.pop(key)
            try:
                await session.aclose()
            except Exception:  # noqa: BLE001 - 单 server 关闭失败不阻塞其余回收
                logger.warning("mcp server=%s 关闭失败", key, exc_info=True)
            self._run_unregister_hook(key)

    # ---- 内部 ----

    async def _connect_one(self, config: McpServerConfig) -> None:
        key = config.key
        if self._closed or key in self._sessions or key in self._inflight:
            return  # 已关闭直接拒建；并发去重：同 key 单 flight
        task = asyncio.current_task()
        if task is not None:
            self._inflight[key] = task
        transport: McpTransport | None = None
        try:
            transport = self._factory(config)
            session = await McpSession.connect(config, transport)
            if self._closed:
                # 迟关闭：aclose 后才建完的连接立即 close，不入池
                await session.aclose()
                return
            self._sessions[key] = session
            logger.info(
                "mcp server=%s 已建连（protocol=%s · tools=%d）",
                key,
                session.negotiated_version,
                len(session.tools),
            )
        except asyncio.CancelledError:
            # 取消感知：清理半成品 transport 后重抛
            if transport is not None:
                try:
                    await transport.aclose()
                except Exception:  # noqa: BLE001
                    logger.warning("mcp server=%s 取消清理失败", key, exc_info=True)
            raise
        except Exception as exc:  # noqa: BLE001 - §4-B 单 server 失败隔离
            logger.warning("mcp server=%s 建连失败，跳过（MCP 面其余不受影响）: %s", key, exc)
        finally:
            self._inflight.pop(key, None)

    def _run_unregister_hook(self, key: str) -> None:
        """R5c 接口面：T3 落地后由 lifespan 注入真实摘除逻辑；hook 失败仅 warn。"""
        if self._unregister_hook is None:
            return
        try:
            self._unregister_hook(key)
        except Exception:  # noqa: BLE001
            logger.warning("mcp unregister_hook 失败: server=%s", key, exc_info=True)


__all__ = [
    "McpSessionManager",
    "TransportFactory",
    "default_transport_factory",
]
