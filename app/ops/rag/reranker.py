"""Cross-Encoder 精排（RAG P0 · SPEC-rag-reranker-p0）。

粗排（RRF）候选 top-M → bge-reranker-v2-m3 → 动态过滤 → top-5。
分数仅观测/日志，不进闸、不上用户卡片。
加载失败 fail-closed：回退粗排 top-5。

过滤策略（方案 B）：
1. 顶分地板 ``RAG_RERANK_MIN_SCORE``（默认 0.4）：``max(score) < 地板`` → 空列表（真空拒答）
2. 相对顶分 ``RAG_RERANK_SCORE_RATIO``（默认 0.75）：保留 ``score >= max * ratio``
"""
from __future__ import annotations

import logging
import os
from collections.abc import Callable, Sequence
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.ops.rag.retrieve import RetrievedChunk

logger = logging.getLogger(__name__)

DEFAULT_RERANK_MODEL = "BAAI/bge-reranker-v2-m3"
DEFAULT_CANDIDATES = 20
DEFAULT_K_EACH = 20
DEFAULT_TOP_N = 5
DEFAULT_MIN_SCORE = 0.4
DEFAULT_SCORE_RATIO = 0.75

_cross_encoder = None
_cross_encoder_model_name: str | None = None


def rerank_enabled() -> bool:
    """生产默认 false；实验复测显式 true。"""
    return os.getenv("RAG_RERANK_ENABLED", "").strip().lower() in ("1", "true", "yes")


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
    """进程内懒加载单例（对齐 embedder Q3）。"""
    global _cross_encoder, _cross_encoder_model_name
    name = rerank_model_name()
    if _cross_encoder is not None and _cross_encoder_model_name == name:
        return _cross_encoder
    from sentence_transformers import CrossEncoder  # 延迟导入，保持模块轻量

    logger.info("loading reranker model %s ...", name)
    _cross_encoder = CrossEncoder(name)
    _cross_encoder_model_name = name
    return _cross_encoder


def _default_score_fn(query: str, texts: Sequence[str]) -> list[float]:
    model = _load_cross_encoder()
    pairs = [(query, t) for t in texts]
    scores = model.predict(pairs, show_progress_bar=False)
    return [float(s) for s in scores]


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

    ``score_fn`` 可注入（单测 fake）；默认走本地 CrossEncoder。
    ``min_score`` / ``score_ratio`` 默认读 env；``max < min_score`` → 空列表。
    加载/推理异常 → 回退 ``candidates[:top_n]``（等同关 rerank，不施过滤）。
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
