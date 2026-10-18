"""LangChain 旁路 HTTP：POST /api/ops/lc-evidence/invoke。

薄包装 ``ainvoke_evidence_answer``；专用响应模型保证 ``snippet`` 进 JSON
（``EvidenceItem.snippet`` 是普通 ``@property``，``model_dump()`` 不含该键）。
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from app.db.models import OpsUser
from app.ops.deps import CurrentUser
from app.ops.lc_evidence_chain.chain import ainvoke_evidence_answer
from app.ops.lc_evidence_chain.types import ChainResult, EvidenceItem, Grade
from app.ops.tracing import flush_traces, tracing_enabled

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/lc-evidence", tags=["lc-evidence"])

QUERY_MAX_LENGTH = 8000
_FAIL_CODE = "lc_evidence_failed"
_FAIL_MESSAGE = "旁路调用失败"


class InvokeRequest(BaseModel):
    """旁路 invoke 请求体。"""

    query: str = Field(..., min_length=1, max_length=QUERY_MAX_LENGTH)


class GradeOut(BaseModel):
    evidence_id: int
    relevance: str
    reason: str = ""


class EvidenceOut(BaseModel):
    id: int
    source_type: str
    source_id: str
    chunk_index: int
    anchor: str
    title: str | None
    url: str | None
    snippet: str
    grade: GradeOut | None = None


class MetaOut(BaseModel):
    hit_count: int = 0
    graded: bool = False
    grade_count: int = 0
    kept_count: int = 0
    gate_action: str = ""
    best_relevance: str = ""


class DataOut(BaseModel):
    query: str
    evidence: list[EvidenceOut]
    answer: str
    meta: MetaOut


def _grade_out(grade: Grade | None) -> GradeOut | None:
    if grade is None:
        return None
    relevance = grade.relevance
    value = relevance.value if hasattr(relevance, "value") else str(relevance)
    return GradeOut(
        evidence_id=grade.evidence_id,
        relevance=value,
        reason=grade.reason,
    )


def _evidence_out(item: EvidenceItem) -> EvidenceOut:
    return EvidenceOut(
        id=item.id,
        source_type=item.source_type,
        source_id=item.source_id,
        chunk_index=item.chunk_index,
        anchor=item.anchor,
        title=item.title,
        url=item.url,
        snippet=item.snippet,
        grade=_grade_out(item.grade),
    )


def _meta_out(result: ChainResult) -> MetaOut:
    meta = result.meta or {}
    return MetaOut(
        hit_count=int(meta.get("hit_count") or 0),
        graded=bool(meta.get("graded") or False),
        grade_count=int(meta.get("grade_count") or 0),
        kept_count=int(meta.get("kept_count") or len(result.evidence)),
        gate_action=str(meta.get("gate_action") or ""),
        best_relevance=str(meta.get("best_relevance") or ""),
    )


def serialize_chain_result(result: ChainResult) -> DataOut:
    """把 ChainResult 转成 freeze 响应 data（含 snippet）。"""
    return DataOut(
        query=result.query,
        evidence=[_evidence_out(item) for item in result.evidence],
        answer=result.answer,
        meta=_meta_out(result),
    )


@router.post("/invoke")
async def invoke_lc_evidence(
    body: InvokeRequest,
    _user: OpsUser = CurrentUser,
) -> JSONResponse:
    """同步调用 LCEL 旁路；须登录。"""
    try:
        result = await ainvoke_evidence_answer(body.query)
    except Exception:
        logger.exception("lc-evidence invoke failed")
        if tracing_enabled():
            flush_traces()
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "ok": False,
                "error": {"code": _FAIL_CODE, "message": _FAIL_MESSAGE},
            },
        )
    if tracing_enabled():
        flush_traces()
    return JSONResponse(content={"ok": True, "data": serialize_chain_result(result).model_dump()})
