"""LLM 推理缓存（Agent Host V1-C · llm-factory-closure D3 · 默认关）。

SPEC：docs/spec/host-v1-llm-factory-closure/SPEC-host-v1-llm-factory-closure_v0.md
（signed · Q2 只缓存 plan·参数模板锁死 · 终答 answer 不缓存）。

设计纪律（SPEC §1/§2 D3 签收锁死）：

1. **默认关**：``OPS_LLM_INFER_CACHE_ENABLED=false`` 默认关（关 = 零 diff）；
   非法值回退关。
2. **只缓存结构化产物**（Q2 裁定）：intent/plan 档 structured 输出 + 高频能力
   参数模板（均走 structured 档 complete 管道 · CACHEABLE_TASK_TYPES）；
   **终答 answer 不缓存**（时效性证据 · 缓存 = 静默陈旧 · 承 fallback B2 精神），
   summary/grader 同不入缓存。
3. **版本入键**（防陈旧命中）：键 = task_type + 模型档 id + prompt 模板版本
   + 规范化输入哈希；plan 类另含 **catalog 版本/可见集哈希**（FP-2：目录变 →
   键变 → 自然失效）。prompt 版本 / 目录指纹由调用方经 ContextVar 注入
   （use_infer_cache_context）；未注入时用 PROMPT_VERSIONS 集中声明的档级
   默认版本（bump 即全键失效）。
4. **进程内边界**：LRU（``OPS_LLM_INFER_CACHE_MAX_ENTRIES`` 默认 256）+ TTL
   （``OPS_LLM_INFER_CACHE_TTL_SECONDS`` 默认 3600 · 非法回退）；重启失效
   如实定性（跨进程共享 v2.0 非范围）。
5. **缓存击穿**（FP-6）：get/put 走进程内锁原子化；v1 接受并发同键 miss
   各算各的（不引 singleflight 复杂度 · 如实定性）。
6. **观测记动作不记内容**：命中/未命中进 span metadata（infer_cache_hit /
   infer_cache_key_prefix），**不记缓存内容**。
"""

from __future__ import annotations

import hashlib
import json
import os
import threading
import time
from collections import OrderedDict
from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar, Token
from dataclasses import dataclass
from typing import Any

ENV_ENABLED = "OPS_LLM_INFER_CACHE_ENABLED"
ENV_MAX_ENTRIES = "OPS_LLM_INFER_CACHE_MAX_ENTRIES"
ENV_TTL_SECONDS = "OPS_LLM_INFER_CACHE_TTL_SECONDS"

DEFAULT_MAX_ENTRIES = 256
DEFAULT_TTL_SECONDS = 3600

#: 可缓存档（Q2 裁定：只缓存结构化产物 —— intent/plan 档 structured 输出 +
#: 高频能力参数模板）。**终答 answer 不缓存**（静默陈旧风险）；
#: summary/grader 时效面同不入缓存。
CACHEABLE_TASK_TYPES: frozenset[str] = frozenset({"structured"})

#: 档级 prompt 模板版本集中声明（调用方未注入版本时的默认；**bump = 全键
#: 自然失效**，承「版本入键」纪律 · 变异检验②锚点）。
PROMPT_VERSIONS: dict[str, str] = {
    "structured": "v1",
}
_UNVERSIONED = "v0-unversioned"


@dataclass(frozen=True)
class InferCacheContext:
    """缓存键上下文（调用方注入）：prompt 版本 + plan 类目录指纹。"""

    prompt_version: str | None = None
    catalog_fingerprint: str | None = None


_DEFAULT_CACHE_CONTEXT = InferCacheContext()
_current: ContextVar[InferCacheContext] = ContextVar(
    "llm_infer_cache_context", default=_DEFAULT_CACHE_CONTEXT
)


def current_cache_context() -> InferCacheContext:
    return _current.get()


def set_cache_context(
    *, prompt_version: str | None = None, catalog_fingerprint: str | None = None
) -> Token[InferCacheContext]:
    """注入缓存键上下文（None 字段继承当前值）；返回 token 供复位。"""
    cur = _current.get()
    return _current.set(
        InferCacheContext(
            prompt_version=(prompt_version if prompt_version is not None else cur.prompt_version),
            catalog_fingerprint=(
                catalog_fingerprint if catalog_fingerprint is not None else cur.catalog_fingerprint
            ),
        )
    )


def reset_cache_context(token: Token[InferCacheContext]) -> None:
    _current.reset(token)


@contextmanager
def use_infer_cache_context(
    *, prompt_version: str | None = None, catalog_fingerprint: str | None = None
) -> Iterator[None]:
    """with 块内注入缓存键上下文（plan 类调用方注入 catalog 版本/可见集哈希），
    退出自动复位。"""
    token = set_cache_context(
        prompt_version=prompt_version, catalog_fingerprint=catalog_fingerprint
    )
    try:
        yield
    finally:
        reset_cache_context(token)


def _truthy(raw: str) -> bool:
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _env_int(name: str, default: int) -> int:
    """读 env；非法 / 非正值一律回退默认（承 step_contract._env_int 纪律）。"""
    raw = os.environ.get(name, "").strip()
    if not raw:
        return default
    try:
        n = int(raw)
    except ValueError:
        return default
    return n if n > 0 else default


def infer_cache_enabled() -> bool:
    """缓存总开关；**默认关**（关 = 零 diff）；非法值回退关。"""
    return _truthy(os.environ.get(ENV_ENABLED, ""))


def cache_max_entries() -> int:
    return _env_int(ENV_MAX_ENTRIES, DEFAULT_MAX_ENTRIES)


def cache_ttl_seconds() -> int:
    return _env_int(ENV_TTL_SECONDS, DEFAULT_TTL_SECONDS)


def prompt_version_of(task_type: str | None) -> str:
    """prompt 模板版本：调用方注入优先，否则 PROMPT_VERSIONS 集中声明默认。"""
    injected = current_cache_context().prompt_version
    if injected and injected.strip():
        return injected.strip()
    return PROMPT_VERSIONS.get((task_type or "").strip().lower(), _UNVERSIONED)


def normalize_input(parts: list[str] | tuple[str, ...]) -> str:
    """规范化输入（去首尾空白 · 统一换行）后哈希；不记原文。"""
    normalized = "\n".join(p.replace("\r\n", "\n").strip() for p in parts)
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def make_key(
    task_type: str,
    model: str | None,
    *,
    input_parts: list[str] | tuple[str, ...],
    prompt_version: str | None = None,
    catalog_fingerprint: str | None = None,
) -> str:
    """缓存键 = sha256(task_type + 模型档 id + prompt 版本 + 输入哈希 [+ 目录指纹])。

    **版本入键**（防陈旧命中 · FP-2）：模型档变更 / prompt 版本 bump / plan 类
    catalog 版本·可见集哈希变 → 键自然变 → 旧条目自然 miss（无需主动清缓存）。
    catalog_fingerprint 缺省取 ContextVar 注入值（plan 调用方声明目录指纹）。
    """
    task = (task_type or "").strip().lower()
    version = prompt_version if prompt_version is not None else prompt_version_of(task)
    fingerprint = catalog_fingerprint
    if fingerprint is None:
        fingerprint = current_cache_context().catalog_fingerprint or ""
    payload = {
        "task_type": task,
        "model": (model or "").strip(),
        "prompt_version": version,
        "input_sha256": normalize_input(input_parts),
        "catalog_fingerprint": fingerprint or "",
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


_LOCK = threading.Lock()
#: key → (expires_at_epoch, value)；OrderedDict 保序 = LRU 序（尾 = 最新）
_CACHE: OrderedDict[str, tuple[float, str]] = OrderedDict()
_HITS = 0
_MISSES = 0
_EVICTED = 0


def get(key: str, *, now: float | None = None) -> str | None:
    """命中返回缓存值并记 hits；未命中 / 过期返回 None 并记 misses（观测计数）。"""
    global _HITS, _MISSES
    current = now if now is not None else time.time()
    with _LOCK:
        entry = _CACHE.get(key)
        if entry is None:
            _MISSES += 1
            return None
        expires_at, value = entry
        if expires_at <= current:
            del _CACHE[key]
            _MISSES += 1
            return None
        _CACHE.move_to_end(key)
        _HITS += 1
        return value


def put(key: str, value: str, *, now: float | None = None) -> None:
    """写入（TTL 到期时刻 + LRU 落尾）；容量超界淘汰最老（dict 保序头部）。"""
    global _EVICTED
    current = now if now is not None else time.time()
    with _LOCK:
        _CACHE[key] = (current + cache_ttl_seconds(), value)
        _CACHE.move_to_end(key)
        while len(_CACHE) > cache_max_entries():
            _CACHE.popitem(last=False)
            _EVICTED += 1


def report_span(metadata: dict[str, Any]) -> None:
    """命中/未命中进当前 span metadata（记动作不记内容 · 失败不挡主流程）。"""
    try:
        from app.ops.tracing import update_current_span_metadata

        update_current_span_metadata(metadata)
    except Exception:  # 观测面故障绝不拖垮主流程（承 delegation.audit 先例）
        pass


def reset() -> None:
    """清空缓存与计数（测试**必须**每个用例前调一次：进程内全局状态）。"""
    global _HITS, _MISSES, _EVICTED
    with _LOCK:
        _CACHE.clear()
        _HITS = 0
        _MISSES = 0
        _EVICTED = 0


def snapshot() -> dict[str, Any]:
    """/runtime 观测用。**显式标出进程内边界**（重启失效 · 不跨进程共享）。"""
    with _LOCK:
        size = len(_CACHE)
        hits = _HITS
        misses = _MISSES
        evicted = _EVICTED
    return {
        "enabled": infer_cache_enabled(),
        "cacheable_task_types": sorted(CACHEABLE_TASK_TYPES),
        "size": size,
        "max_entries": cache_max_entries(),
        "ttl_seconds": cache_ttl_seconds(),
        "hits": hits,
        "misses": misses,
        "evicted": evicted,
        # 已知边界（FP-6）：进程内缓存 · 并发同键 miss 各算各的（v1 如实定性）
        "scope": "process-local",
    }
