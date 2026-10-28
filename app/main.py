"""FastAPI application entry point."""

import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

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


# N-40-1：初始化必须先于首个 app 包 import——import 链执行期（窗口期）capability
# 模块级装配（app/ops/capability/__init__.py:112 → persistence.py）即发射 WARNING/INFO；
# root 无 handler 则 WARNING 走 lastResort 裸格式、INFO 整行被吞。函数仅用 stdlib，
# 无循环 import 风险；basicConfig 幂等（root 已有 handler 时 no-op）。
_init_logging()


def _sanitize_no_proxy_env() -> None:
    """启动期清洗 NO_PROXY/no_proxy 方括号 IPv6 条目（import 期 · 幂等 · 纯 stdlib）。

    - 背景：Clash 系客户端常写 NO_PROXY=localhost,127.0.0.1,::1,[::1]；httpx
      （trust_env）构造 client 时把 '[::1]' 当 URL 解析，':1]' 被截为端口 →
      InvalidURL("Invalid port: ':1]'")，凡旁路 LLM 流式调用即炸
      （lg_rag.worker_failed · run 0fbebc8e seq19 钉案）。
    - 双键覆盖：httpx 按 urllib 惯例小写 no_proxy 优先，只洗大写会被小写绕过
      （2026-10-28 第四实证），故 NO_PROXY / no_proxy 同处理。
    - 逐条目剥方括号（'[::1]' → '::1'），其余条目与顺序不动；仅实际变化时
      回写 os.environ（无方括号条目 → 零 diff，env 逐字节不变）。
    - client **构造时**读 env，import 期清洗覆盖其后全部构造；--reload 子进程
      继承 supervisor env，import 期清洗天然覆盖每次 reload。幂等：重跑零 diff。
    """
    for key in ("NO_PROXY", "no_proxy"):
        raw = os.environ.get(key)
        if raw is None or "[" not in raw:
            continue
        entries = raw.split(",")
        cleaned = [
            entry[1:-1] if entry.startswith("[") and entry.endswith("]") else entry
            for entry in entries
        ]
        sanitized = ",".join(cleaned)
        if sanitized != raw:
            os.environ[key] = sanitized


# 同 N-40-1 行序约束：必须先于任何 app 包 import（import 链窗口期即可能构造
# httpx client 的先例见上方注释块）；纯 stdlib，无循环 import 风险。
_sanitize_no_proxy_env()


from app.config import settings  # noqa: E402
from app.ops.hitl import auto_resume  # noqa: E402
from app.ops.router import router as ops_router  # noqa: E402
from app.ops.tracing import log_tracing_startup  # noqa: E402


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


# 架构浏览器：docs/arch-browser/dist 衍生静态视图（MD/_tech_graph 仍为真值源）
_ARCH_BROWSER_DIST = Path(__file__).resolve().parents[1] / "docs" / "arch-browser" / "dist"
if (_ARCH_BROWSER_DIST / "index.html").is_file():
    app.mount(
        "/docs/arch-browser",
        StaticFiles(directory=str(_ARCH_BROWSER_DIST), html=True),
        name="arch_browser",
    )
