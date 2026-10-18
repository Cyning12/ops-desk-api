"""通用传输重试（llm-layer-hardening D1）：指数退避 + full jitter。

判据钉死（SPEC §2 D1）：
- **仅** `LlmProviderError` 且 `retryable=True` 才重试（408/429/5xx/传输错/SSE
  解析错——`providers/base.py` 既有分类）；其余异常（含 `retryable=False` 的
  4xx、缺 key `ValueError`）**零重试**。**分类靠结构不靠文案**。
- 退避：`delay_i = random(0, min(cap, base × 2^i))`；默认 `base=0.5s · cap=8s
  · max_attempts=3`（**总尝试次数**，含首次；=1 即旧语义单次）。
- 流式纪律：重试只允许发生在**首 content chunk yield 之前**（施加在
  `BaseProviderImpl` 边界包装层，不在本模块）。
- env 非法值一律回退默认 + warning（对齐 `grader_prompt_version` 模式）。
"""

from __future__ import annotations

import asyncio
import logging
import os
import random
from dataclasses import dataclass

logger = logging.getLogger(__name__)

_ENV_ENABLED = "OPS_LLM_RETRY_ENABLED"
_ENV_MAX_ATTEMPTS = "OPS_LLM_RETRY_MAX_ATTEMPTS"
_ENV_BASE_DELAY = "OPS_LLM_RETRY_BASE_DELAY_S"
_ENV_MAX_DELAY = "OPS_LLM_RETRY_MAX_DELAY_S"

DEFAULT_MAX_ATTEMPTS = 3
DEFAULT_BASE_DELAY_S = 0.5
DEFAULT_MAX_DELAY_S = 8.0

_TRUTHY = ("1", "true", "yes", "on")
_FALSY = ("0", "false", "no", "off")


@dataclass(frozen=True)
class RetryConfig:
    """一次解析的重试参数（每次调用重读 env，测试可 monkeypatch 环境变量）。"""

    enabled: bool = True
    max_attempts: int = DEFAULT_MAX_ATTEMPTS
    base_delay_s: float = DEFAULT_BASE_DELAY_S
    max_delay_s: float = DEFAULT_MAX_DELAY_S


def _bool_env(name: str, default: bool) -> bool:
    raw = (os.getenv(name) or "").strip().lower()
    if not raw:
        return default
    if raw in _TRUTHY:
        return True
    if raw in _FALSY:
        return False
    logger.warning("invalid %s=%r; fallback to %s", name, raw, default)
    return default


def _int_env(name: str, default: int, *, minimum: int = 1) -> int:
    raw = (os.getenv(name) or "").strip()
    if not raw:
        return default
    try:
        n = int(raw)
    except ValueError:
        logger.warning("invalid %s=%r; fallback to %s", name, raw, default)
        return default
    if n < minimum:
        logger.warning("invalid %s=%r (< %d); fallback to %s", name, raw, minimum, default)
        return default
    return n


def _float_env(name: str, default: float, *, minimum: float = 0.0) -> float:
    raw = (os.getenv(name) or "").strip()
    if not raw:
        return default
    try:
        v = float(raw)
    except ValueError:
        logger.warning("invalid %s=%r; fallback to %s", name, raw, default)
        return default
    if v <= minimum:
        logger.warning("invalid %s=%r (<= %s); fallback to %s", name, raw, minimum, default)
        return default
    return v


def retry_config() -> RetryConfig:
    """从 env 解析重试配置；非法值回退默认 + warning。"""
    return RetryConfig(
        enabled=_bool_env(_ENV_ENABLED, True),
        max_attempts=_int_env(_ENV_MAX_ATTEMPTS, DEFAULT_MAX_ATTEMPTS),
        base_delay_s=_float_env(_ENV_BASE_DELAY, DEFAULT_BASE_DELAY_S),
        max_delay_s=_float_env(_ENV_MAX_DELAY, DEFAULT_MAX_DELAY_S),
    )


def backoff_delay(retry_index: int, cfg: RetryConfig) -> float:
    """第 `retry_index` 次重试（从 0 起）的退避：`random(0, min(cap, base×2^i))`。"""
    upper = min(cfg.max_delay_s, cfg.base_delay_s * (2**retry_index))
    return random.uniform(0.0, upper)


async def sleep(delay: float) -> None:
    """退避等待。**测试 monkeypatch 本函数**记录延迟序列，不假 sleep。"""
    await asyncio.sleep(delay)
