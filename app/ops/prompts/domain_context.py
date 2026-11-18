"""P4-T2 · 部署级领域上下文（domain-pack-v1 · 19 契约 §3.3）。

域 = 部署级配置（``OPS_DOMAIN`` env · 进程单值 · **不挂 tenant** ·
承 QDRANT_COLLECTION 先例 · 18 设计文 :94-97）。

词表纪律（19 §1.2 R5）：domain 词表 ``[a-z0-9_]+``（**无点号**），与
template id 词表（loader._ID_RE 允许点号）各自独立、**禁止互拼**——
domain 只拼目录名（``assets/<domain>/``），不得拼进 template_id。

注入面（§3.3）：`start_run_worker` `_main()` 内
`set_current_domain(resolve_domain_from_env())`（与 set_current_tenant
同位 · finally reset）；未注入时 `current_domain()` 回落 env 解析
（R-P4-2 漏设无害化强化：OPS_DOMAIN 缺省/非法 → ops，与现状同值）。
"""

from __future__ import annotations

import logging
import os
import re
from contextvars import ContextVar, Token
from functools import cache

logger = logging.getLogger(__name__)

DEFAULT_DOMAIN = "ops"
OPS_DOMAIN_ENV = "OPS_DOMAIN"
_DOMAIN_RE = re.compile(r"[a-z0-9_]+")

_current: ContextVar[str | None] = ContextVar("ops_prompt_domain", default=None)


def resolve_domain(raw: str | None) -> str:
    """解析部署级域值：缺省/空白/词表外（防路径穿越 · §5.1）→ ops + warning。"""
    value = (raw or "").strip()
    if not value:
        return DEFAULT_DOMAIN
    return _resolve_cached(value)


@cache
def _resolve_cached(value: str) -> str:
    """按原始值缓存解析结果（warning 一值一次 · 防日志洪泛）。"""
    if not _DOMAIN_RE.fullmatch(value):
        logger.warning(
            "OPS_DOMAIN 非法值 %r 回退 %s（domain 词表 [a-z0-9_]+ · 19 §5.1 防路径穿越）",
            value,
            DEFAULT_DOMAIN,
        )
        return DEFAULT_DOMAIN
    return value


def resolve_domain_from_env() -> str:
    """读 ``OPS_DOMAIN`` env 解析部署级域（部署级进程单值）。"""
    return resolve_domain(os.environ.get(OPS_DOMAIN_ENV))


def current_domain() -> str:
    """当前域：contextvar 已注入用注入值；未注入回落 env 解析（默认 ops）。"""
    value = _current.get()
    if value is not None:
        return value
    return resolve_domain_from_env()


def set_current_domain(domain: str) -> Token[str | None]:
    """注入当前域（词表外 = 编程错误 → ValueError 显式炸 · 仅 env 面 fail-closed）。"""
    if not _DOMAIN_RE.fullmatch(domain):
        raise ValueError(f"非法 domain（词表 [a-z0-9_]+）: {domain!r}")
    return _current.set(domain)


def reset_current_domain(token: Token[str | None]) -> None:
    """复位 contextvar（worker finally 路径 · 防跨 run 泄漏）。"""
    _current.reset(token)
