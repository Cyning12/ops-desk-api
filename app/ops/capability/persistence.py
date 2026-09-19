"""持久化装配：决定能力层用哪个防重存储与回执 sink。

**为什么要有这个模块**：默认值是"不防重"（`NullIdempotencyStore` 每次写都告警）。
上线前必须显式选择——**装配是部署动作，不是代码默认值**。把选择集中在一处，
避免"某个入口忘了配"这种只在生产才发现的静默失效。

| `OPS_CAPABILITY_PERSISTENCE` | 防重存储 | 回执 sink | 适用 |
|---|---|---|---|
| `db` | `DbIdempotencyStore`（跨实例） | `DbReceiptSink`（跨重启可查） | **生产** |
| `memory` | `InMemoryIdempotencyStore`（进程内） | `InMemoryReceiptSink`（重启即丢） | 单实例 / 联调 |
| 不设（默认） | `NullIdempotencyStore`（**不防重，告警**） | `NullReceiptSink`（**不落库，告警**） | 开发；**不能上生产** |

刻意**不做"自动探测数据库可用性"**：悄悄换存储实现正是我们要避免的那类惊喜——
出问题时会表现为"防重时有时无"，极难排查。要 DB 就显式写 `db`。
"""

from __future__ import annotations

import logging
import os

logger = logging.getLogger(__name__)

ENV_PERSISTENCE = "OPS_CAPABILITY_PERSISTENCE"

MODE_DB = "db"
MODE_MEMORY = "memory"
MODE_NULL = "null"


def configure_persistence_from_env() -> str:
    """按 env 装配，返回实际生效的模式。默认 ``null``（显式不防重并告警）。"""
    from app.ops.capability.idempotency import (
        InMemoryIdempotencyStore,
        set_idempotency_store,
    )
    from app.ops.capability.receipts import InMemoryReceiptSink, set_receipt_sink

    mode = os.environ.get(ENV_PERSISTENCE, "").strip().lower() or MODE_NULL

    if mode == MODE_DB:
        # 延迟 import：只有真选 db 才拉起 SQLAlchemy / 建引擎
        from app.ops.capability.idempotency import DbIdempotencyStore
        from app.ops.capability.receipts import DbReceiptSink

        set_idempotency_store(DbIdempotencyStore())
        set_receipt_sink(DbReceiptSink())
        logger.info("能力层持久化：db（跨实例防重 + 回执落库）")
        return MODE_DB

    if mode == MODE_MEMORY:
        set_idempotency_store(InMemoryIdempotencyStore())
        set_receipt_sink(InMemoryReceiptSink())
        logger.warning(
            "能力层持久化：memory（进程内）—— **多实例下防重无效**，勿用于生产"
        )
        return MODE_MEMORY

    if mode != MODE_NULL:
        logger.error(
            "%s=%r 无法识别（仅 db / memory），已按不防重处理",
            ENV_PERSISTENCE,
            mode,
        )
    logger.warning(
        "能力层持久化未配置（%s 未设）：**幂等防重与回执落库均未启用**，不可上生产",
        ENV_PERSISTENCE,
    )
    return MODE_NULL
