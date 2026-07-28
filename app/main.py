"""FastAPI application entry point."""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.ops.router import router as ops_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan."""
    yield


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
    """Health check endpoint.

    ``probe`` 为临时部署可辨字段；冒烟确认后须回滚删除（task health-temp-probe）。
    """
    return {"status": "ok", "probe": "20260728-a"}
