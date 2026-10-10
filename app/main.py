"""FastAPI application entry point."""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.ops.hitl import auto_resume
from app.ops.router import router as ops_router
from app.ops.tracing import log_tracing_startup


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
