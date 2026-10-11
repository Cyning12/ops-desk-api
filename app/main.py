"""FastAPI application entry point."""
import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.ops.hitl import auto_resume
from app.ops.router import router as ops_router
from app.ops.tracing import log_tracing_startup

_LOG_FORMAT = "%(asctime)s %(name)s %(levelname)s %(message)s"
_LOG_LEVEL_NAMES = ("CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG")


def _init_logging() -> None:
    """仓级 logging 初始化（import 期 · 幂等）：root 挂唯一 StreamHandler。

    - level 取自 OPS_LOG_LEVEL，缺省/非法一律 INFO（fail-closed · 承 auto_resume env 先例）；
    - basicConfig 在 root 已有 handler 时天然 no-op（--reload supervisor 子进程重启 /
      自写启动器 / scripts/evals 自含配置面零 diff）；
    - 不动 uvicorn logger（uvicorn/uvicorn.access propagate=False 自带 handler ·
      access log 不吞 · 同一事件不双行）。
    """
    raw = os.environ.get("OPS_LOG_LEVEL", "").strip().upper()
    valid = raw in _LOG_LEVEL_NAMES
    level = getattr(logging, raw) if valid else logging.INFO
    logging.basicConfig(level=level, format=_LOG_FORMAT)
    if raw and not valid:
        logging.getLogger(__name__).error(
            "OPS_LOG_LEVEL=%r 无法识别（仅 CRITICAL/ERROR/WARNING/INFO/DEBUG），按 INFO 处理",
            raw,
        )


_init_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan."""
    log_tracing_startup()
    # T2 补偿扫描挂点（FP-9 崩溃兜底）：仅 auto 模式创建（manual 默认**零创建**——
    # TestClient 经 lifespan 的既有测试面零 diff · 实操-D）；shutdown 须 cancel。
    scan_started = auto_resume.auto_resume_mode() == auto_resume.MODE_AUTO
    if scan_started:
        auto_resume.start_compensation_scanner()
    try:
        yield
    finally:
        if scan_started:
            await auto_resume.stop_compensation_scanner()


app = FastAPI(
    title=settings.app_name,
    debug=settings.debug,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(ops_router)


@app.get("/health", tags=["health"])
async def health() -> dict:
    """Health check endpoint."""
    return {"status": "ok"}
