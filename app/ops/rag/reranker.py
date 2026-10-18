"""精排（RAG · SPEC 方案 B + SiliconFlow HTTP 打分）。

粗排（RRF）候选 top-M → 打分后端 → 动态过滤 → top-5。
默认打分：SiliconFlow ``POST /rerank``（``BAAI/bge-reranker-v2-m3``）。
仅 ``RAG_RERANK_BACKEND=local`` 才加载本机 CrossEncoder。
分数仅观测/日志，不进闸、不上用户卡片。
加载/HTTP 失败 fail-closed：回退粗排 top-5。

过滤策略（方案 B）：
1. 顶分地板 ``RAG_RERANK_MIN_SCORE``（默认 0.4）：``max(score) < 地板`` → 空列表（真空拒答）
2. 相对顶分 ``RAG_RERANK_SCORE_RATIO``（默认 0.75）：保留 ``score >= max * ratio``
"""

from __future__ import annotations

import logging
import os
import time
from collections.abc import Callable, Sequence
from typing import TYPE_CHECKING, Any

import httpx

if TYPE_CHECKING:
    from app.ops.rag.retrieve import RetrievedChunk

logger = logging.getLogger(__name__)

DEFAULT_RERANK_MODEL = "BAAI/bge-reranker-v2-m3"
DEFAULT_CANDIDATES = 20
DEFAULT_K_EACH = 20
DEFAULT_TOP_N = 5
DEFAULT_MIN_SCORE = 0.4
DEFAULT_SCORE_RATIO = 0.75
DEFAULT_RERANK_BACKEND = "siliconflow"
DEFAULT_SILICONFLOW_BASE = "https://api.siliconflow.cn/v1"
# 短超时：避免与 LC Evidence 120s 叠穿（勿照抄 embedder 60s×3）
DEFAULT_RERANK_HTTP_TIMEOUT = 12.0
_429_RETRY_SLEEP_S = 0.4

_cross_encoder = None
_cross_encoder_model_name: str | None = None


def rerank_enabled() -> bool:
    """生产默认 false；实验复测显式 true。"""
    return os.getenv("RAG_RERANK_ENABLED", "").strip().lower() in ("1", "true", "yes")


def rerank_backend() -> str:
    """打分后端：``siliconflow``（默认，含空/未设）或 ``local``。"""
    raw = (os.getenv("RAG_RERANK_BACKEND") or "").strip().lower()
    if not raw:
        return DEFAULT_RERANK_BACKEND
    if raw in ("siliconflow", "local"):
        return raw
    logger.warning(
        "invalid RAG_RERANK_BACKEND=%r; fallback to %s",
        raw,
        DEFAULT_RERANK_BACKEND,
    )
    return DEFAULT_RERANK_BACKEND


def rerank_model_name() -> str:
    raw = (os.getenv("RAG_RERANK_MODEL") or DEFAULT_RERANK_MODEL).strip()
    return raw or DEFAULT_RERANK_MODEL


def rerank_candidates() -> int:
    """粗排 top-M（融合后再精排）。"""
    return _positive_int_env("RAG_RERANK_CANDIDATES", DEFAULT_CANDIDATES)


def recall_k_each() -> int:
    """每路召回条数；仅 rerank 开启时由调用方使用（关闭时保持现网 10）。"""
    return _positive_int_env("RAG_RECALL_K_EACH", DEFAULT_K_EACH)


def rerank_min_score() -> float:
    """顶分地板：池内最高 CE 分低于此值 → 全灭拒答。"""
    return _float_env("RAG_RERANK_MIN_SCORE", DEFAULT_MIN_SCORE)


def rerank_score_ratio() -> float:
    """相对顶分比例：保留 score >= max * ratio（夹紧到 [0, 1]）。"""
    value = _float_env("RAG_RERANK_SCORE_RATIO", DEFAULT_SCORE_RATIO)
    if value < 0.0:
        logger.warning("RAG_RERANK_SCORE_RATIO=%r < 0; clamp to 0", value)
        return 0.0
    if value > 1.0:
        logger.warning("RAG_RERANK_SCORE_RATIO=%r > 1; clamp to 1", value)
        return 1.0
    return value


def _positive_int_env(name: str, default: int) -> int:
    raw = (os.getenv(name) or "").strip()
    if not raw:
        return default
    try:
        value = int(raw)
    except ValueError:
        logger.warning("invalid %s=%r; fallback to %d", name, raw, default)
        return default
    if value < 1:
        logger.warning("%s=%r must be >= 1; fallback to %d", name, raw, default)
        return default
    return value


def _float_env(name: str, default: float) -> float:
    raw = (os.getenv(name) or "").strip()
    if not raw:
        return default
    try:
        return float(raw)
    except ValueError:
        logger.warning("invalid %s=%r; fallback to %s", name, raw, default)
        return default


def _load_cross_encoder():
    """进程内懒加载单例（对齐 embedder Q3）。仅 local 后端使用。"""
    global _cross_encoder, _cross_encoder_model_name
    name = rerank_model_name()
    if _cross_encoder is not None and _cross_encoder_model_name == name:
        return _cross_encoder
    from sentence_transformers import CrossEncoder  # 延迟导入，保持模块轻量

    logger.info("loading reranker model %s ...", name)
    _cross_encoder = CrossEncoder(name)
    _cross_encoder_model_name = name
    return _cross_encoder


def _post_rerank(
    url: str,
    payload: dict[str, Any],
    headers: dict[str, str],
) -> httpx.Response:
    """短超时 POST；仅 429 再试一次短退避。"""
    timeout = DEFAULT_RERANK_HTTP_TIMEOUT
    resp = httpx.post(url, json=payload, headers=headers, timeout=timeout)
    if resp.status_code == 429:
        logger.warning(
            "siliconflow rerank 429; %.1fs 后重试一次",
            _429_RETRY_SLEEP_S,
        )
        time.sleep(_429_RETRY_SLEEP_S)
        resp = httpx.post(url, json=payload, headers=headers, timeout=timeout)
    return resp


def _score_siliconflow(query: str, texts: Sequence[str]) -> list[float]:
    """SiliconFlow POST /rerank；按 index 填回与 texts 等长的分数。

    缺 key / 4xx / 5xx / 超时均抛给 ``rerank_chunks`` 既有 fallback。
    禁止在模块 import 或单例构造期因缺 key 而 raise。
    """
    if not texts:
        return []
    api_key = (os.getenv("SILICONFLOW_API_KEY") or "").strip()
    if not api_key:
        raise RuntimeError("缺少 SILICONFLOW_API_KEY")

    base = (os.getenv("SILICONFLOW_BASE_URL") or DEFAULT_SILICONFLOW_BASE).strip().rstrip("/")
    if not base:
        base = DEFAULT_SILICONFLOW_BASE
    url = f"{base}/rerank"
    payload = {
        "model": rerank_model_name(),
        "query": query,
        "documents": list(texts),
        "top_n": len(texts),
    }
    headers = {"Authorization": f"Bearer {api_key}"}
    resp = _post_rerank(url, payload, headers)
    resp.raise_for_status()
    try:
        body = resp.json()
    except ValueError as exc:
        raise RuntimeError("siliconflow rerank 响应非 JSON") from exc
    results = body.get("results") if isinstance(body, dict) else None
    if not isinstance(results, list):
        raise RuntimeError("siliconflow rerank 缺少 results")

    scores = [0.0] * len(texts)
    for item in results:
        if not isinstance(item, dict):
            raise RuntimeError(f"siliconflow rerank 条目异常: {item!r}")
        try:
            idx = int(item["index"])
            score = float(item["relevance_score"])
        except (KeyError, TypeError, ValueError) as exc:
            raise RuntimeError(f"siliconflow rerank 响应字段异常: {item!r}") from exc
        if idx < 0 or idx >= len(texts):
            raise RuntimeError(f"siliconflow rerank index 越界: {idx}")
        scores[idx] = score
    return scores


def _default_score_fn(query: str, texts: Sequence[str]) -> list[float]:
    """默认打分：siliconflow → HTTP；仅 local 才加载 CrossEncoder。"""
    if rerank_backend() == "local":
        model = _load_cross_encoder()
        pairs = [(query, t) for t in texts]
        scores = model.predict(pairs, show_progress_bar=False)
        return [float(s) for s in scores]
    return _score_siliconflow(query, texts)


def _chunk_text_for_rerank(chunk: RetrievedChunk) -> str:
    """精排用正文：剥 Document Context 前缀，避免元数据稀释。"""
    from app.ops.rag.prefix import strip_doc_context_prefix

    return strip_doc_context_prefix(chunk.content) or chunk.content


def rerank_chunks(
    query: str,
    candidates: Sequence[RetrievedChunk],
    top_n: int = DEFAULT_TOP_N,
    *,
    score_fn: Callable[[str, Sequence[str]], Sequence[float]] | None = None,
    min_score: float | None = None,
    score_ratio: float | None = None,
) -> list[RetrievedChunk]:
    """对粗排候选精排，经顶分地板 + 相对顶分过滤后截断 top_n。

    ``score_fn`` 可注入（单测 fake）；默认走 SiliconFlow HTTP，
    ``RAG_RERANK_BACKEND=local`` 时走本机 CrossEncoder。
    ``min_score`` / ``score_ratio`` 默认读 env；``max < min_score`` → 空列表。
    加载/推理/HTTP 异常 → 回退 ``candidates[:top_n]``（等同关 rerank，不施过滤）。
    """
    if top_n < 1:
        return []
    items = list(candidates)
    if not items:
        return []

    floor = rerank_min_score() if min_score is None else float(min_score)
    ratio = rerank_score_ratio() if score_ratio is None else float(score_ratio)
    if ratio < 0.0:
        ratio = 0.0
    elif ratio > 1.0:
        ratio = 1.0

    texts = [_chunk_text_for_rerank(c) for c in items]
    scorer = score_fn or _default_score_fn
    try:
        scores = list(scorer(query, texts))
    except Exception:
        logger.exception(
            "rerank failed; fallback to coarse top-%d query=%r",
            top_n,
            query[:60],
        )
        return items[:top_n]

    if len(scores) != len(items):
        logger.error(
            "rerank score length mismatch (%d vs %d); fallback coarse top-%d",
            len(scores),
            len(items),
            top_n,
        )
        return items[:top_n]

    ranked = sorted(
        zip(items, scores, strict=True),
        key=lambda pair: pair[1],
        reverse=True,
    )
    top_score = float(ranked[0][1])
    if top_score < floor:
        logger.info(
            "rerank: query=%r candidates=%d max=%.4f < floor=%s → empty (refuse)",
            query[:60],
            len(items),
            top_score,
            floor,
        )
        return []

    rel_cut = top_score * ratio
    out: list[RetrievedChunk] = []
    dropped = 0
    for chunk, score in ranked:
        s = float(score)
        if s < rel_cut:
            dropped += 1
            continue
        chunk.rerank_score = s
        out.append(chunk)
        if len(out) >= top_n:
            break
    logger.info(
        "rerank: query=%r candidates=%d max=%.4f floor=%s ratio=%s cut=%.4f "
        "kept=%d dropped=%d top=%s",
        query[:60],
        len(items),
        top_score,
        floor,
        ratio,
        rel_cut,
        len(out),
        dropped,
        [(c.anchor, round(c.rerank_score or 0.0, 4)) for c in out],
    )
    return out
