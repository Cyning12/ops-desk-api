"""bge-m3 稀疏向量（lexical weights）↔ pgvector sparsevec 文本格式。

C 臂实验：FlagEmbedding 产出 lexical weights；库内 `sparse_embedding sparsevec(250002)`。
pgvector 限制 sparsevec 最多 1000 个非零元 → 按 |weight| 截断。
"""
from __future__ import annotations

import logging
import math
import os
from collections.abc import Mapping
from typing import Any

logger = logging.getLogger(__name__)

# bge-m3 tokenizer vocab；与 FlagEmbedding / sentencepiece 一致
BGE_M3_SPARSE_DIM = 250002
# pgvector sparsevec 硬顶
SPARSEVEC_MAX_NNZ = 1000

_model = None


def lexical_weights_to_sparsevec(
    weights: Mapping[Any, Any] | None,
    *,
    dim: int = BGE_M3_SPARSE_DIM,
    max_nnz: int = SPARSEVEC_MAX_NNZ,
) -> str:
    """将 `{token_id: weight}` 转为 `{i:v,...}/dim`（1-based index）。"""
    if not weights:
        return f"{{}}/{dim}"
    items: list[tuple[int, float]] = []
    for k, v in weights.items():
        try:
            fv = float(v)
        except (TypeError, ValueError):
            continue
        if fv == 0.0 or not math.isfinite(fv):
            continue
        try:
            # FlagEmbedding token id 为 0-based；sparsevec 文本索引为 1-based
            idx = int(k) + 1
        except (TypeError, ValueError):
            continue
        if idx < 1 or idx > dim:
            continue
        items.append((idx, fv))
    items.sort(key=lambda x: abs(x[1]), reverse=True)
    items = items[:max_nnz]
    items.sort(key=lambda x: x[0])
    if not items:
        return f"{{}}/{dim}"
    body = ",".join(f"{i}:{v}" for i, v in items)
    return f"{{{body}}}/{dim}"


def _get_bgem3(model_name: str | None = None):
    """懒加载 BGEM3FlagModel（仅 sparse 路需要；隔离依赖冲突见实验 README）。"""
    global _model
    if _model is None:
        from FlagEmbedding import BGEM3FlagModel  # 延迟导入

        name = model_name or os.getenv("RAG_SPARSE_MODEL", "BAAI/bge-m3")
        logger.info("loading FlagEmbedding BGEM3FlagModel %s for sparse ...", name)
        use_fp16 = os.getenv("RAG_SPARSE_FP16", "").strip().lower() in ("1", "true", "yes")
        _model = BGEM3FlagModel(name, use_fp16=use_fp16)
    return _model


def encode_texts_sparse(
    texts: list[str],
    *,
    model_name: str | None = None,
    batch_size: int = 16,
) -> list[str]:
    """批算 lexical weights → sparsevec 文本列表。"""
    if not texts:
        return []
    model = _get_bgem3(model_name)
    out = model.encode(
        texts,
        batch_size=batch_size,
        return_dense=False,
        return_sparse=True,
        return_colbert_vecs=False,
    )
    weights_list = out["lexical_weights"]
    return [lexical_weights_to_sparsevec(w) for w in weights_list]


def encode_query_sparse(query: str, *, model_name: str | None = None) -> str:
    """单条 query 稀疏编码。"""
    return encode_texts_sparse([query], model_name=model_name, batch_size=1)[0]
