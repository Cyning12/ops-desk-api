"""HITL 持久化装配（与能力层同一条纪律：显式选，不自动探测）。

| ``OPS_HITL_PERSISTENCE`` | 存储 | 适用 |
|---|---|---|
| ``db`` | ``DbHitlStore``（跨实例、跨重启） | **生产** |
| ``memory`` | ``InMemoryHitlStore``（进程内，重启即丢） | 单实例 / 联调 |
| 不设（默认） | ``NullHitlStore``（**不落库 + 显式标记**） | 开发；**不能上生产** |

为什么默认不是 memory：内存存储会让"审批申请"看起来提交成功了，重启后
却消失——而"申请丢了"和"没人申请过"在观测上完全一样，人会一直等。
宁可让编排层**说出来"申请没落库"**，也不要给一个看起来成功的假象。
"""

from __future__ import annotations

import logging
import os
from typing import Any

logger = logging.getLogger(__name__)

ENV_PERSISTENCE = "OPS_HITL_PERSISTENCE"

MODE_DB = "db"
MODE_MEMORY = "memory"
MODE_NULL = "null"

_STORE: Any = None


def configure_hitl_from_env() -> str:
    """按 env 装配；返回实际模式。默认 ``null``（不落库并告警）。"""
    global _STORE
    from app.ops.hitl.store import (
        DbHitlStore,
        InMemoryHitlStore,
        NullHitlStore,
    )

    mode = os.environ.get(ENV_PERSISTENCE, "").strip().lower() or MODE_NULL
    if mode == MODE_DB:
        _STORE = DbHitlStore()
        logger.info("HITL 持久化：db（审批申请跨实例、跨重启可查）")
        return MODE_DB
    if mode == MODE_MEMORY:
        _STORE = InMemoryHitlStore()
        logger.warning("HITL 持久化：memory（进程内）—— **重启后审批申请即丢失**，勿用于生产")
        return MODE_MEMORY
    if mode != MODE_NULL:
        logger.error("%s=%r 无法识别（仅 db / memory），按不落库处理", ENV_PERSISTENCE, mode)
    _STORE = NullHitlStore()
    logger.warning(
        "HITL 持久化未配置（%s 未设）：**审批申请不会落库**，不可上生产",
        ENV_PERSISTENCE,
    )
    return MODE_NULL


def get_hitl_store() -> Any:
    """取当前存储；未装配时按 ``null`` 处理（不抛，但编排层必须检查 persisted）。"""
    global _STORE
    if _STORE is None:
        configure_hitl_from_env()
    return _STORE


def set_hitl_store(store: Any) -> None:
    """显式替换（单测 / 装配用）。"""
    global _STORE
    _STORE = store


def reset_hitl_store() -> None:
    """测试隔离用：进程内全局状态必须能显式 reset。"""
    global _STORE
    _STORE = None


def describe_hitl_persistence() -> dict[str, Any]:
    """给 ``/runtime`` 一类端点用：现在到底落不落库。"""
    store = get_hitl_store()
    name = type(store).__name__
    return {
        "mode": {
            "DbHitlStore": MODE_DB,
            "InMemoryHitlStore": MODE_MEMORY,
            "NullHitlStore": MODE_NULL,
        }.get(name, "unknown"),
        "store": name,
        "persists": name != "NullHitlStore",
    }
