"""lg_rag Postgres checkpointer 工厂（Phase 1 · S5）。

说明书：docs/guides/IMPL_langgraph-lg-rag-phase1_v1.md S5。
优先 AsyncPostgresSaver（仓内 FastAPI + asyncpg 异步栈）；
保留同步 PostgresSaver 工厂供 CLI / 脚本场景。

坑位（IMPL S5 表）：
- DSN：settings.database_url 为 postgresql+asyncpg://，
  须转 psycopg 可认的 postgresql://（langgraph-checkpoint-postgres
  底层走 psycopg v3，勿直接塞 +asyncpg）；
- setup()：首次使用必须建表（幂等）；生产应迁 Alembic /
  启动钩子只跑一次；
- thread_id ≤ 255（ainvoke_basic_agent 已截断）；
- 与业务表同库不同表（checkpoints / checkpoint_writes 等默认表名）。
"""

from __future__ import annotations

from collections.abc import AsyncIterator, Iterator
from contextlib import asynccontextmanager, contextmanager

from app.config import settings


def _psycopg_dsn() -> str:
    """asyncpg DSN → psycopg DSN。"""
    return settings.database_url.replace("postgresql+asyncpg://", "postgresql://")


@asynccontextmanager
async def apostgres_saver(*, setup: bool = False) -> AsyncIterator[object]:
    """异步 PostgresSaver 上下文；setup=True 时先建表（幂等，可每次传）。"""
    from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

    async with AsyncPostgresSaver.from_conn_string(_psycopg_dsn()) as saver:
        if setup:
            await saver.setup()
        yield saver


@contextmanager
def postgres_saver(*, setup: bool = False) -> Iterator[object]:
    """同步 PostgresSaver 上下文（CLI / 脚本场景）。"""
    from langgraph.checkpoint.postgres import PostgresSaver

    with PostgresSaver.from_conn_string(_psycopg_dsn()) as saver:
        if setup:
            saver.setup()
        yield saver
