"""lc-evidence HTTP：鉴权、校验、envelope 与 snippet 序列化（mock 链，不连真库）。"""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

from httpx import AsyncClient

from app.llm.schema import LlmProviderError
from app.ops.lc_evidence_chain.answer import EMPTY_EVIDENCE_ANSWER
from app.ops.lc_evidence_chain.types import ChainResult, EvidenceItem, Grade, RetrieveResult
from app.ops.rag.grader import Relevance

_PATH = "/api/ops/lc-evidence/invoke"


def _hit_result() -> ChainResult:
    item = EvidenceItem(
        id=8587,
        repo="ops-desk-workspace",
        source_type="issue",
        source_id="2720",
        chunk_index=4,
        content="Title: compaction abort\n---\nContent: 手动压缩成功但自动失败",
        title="compaction abort",
        url="https://github.com/MoonshotAI/kimi-code/issues/2720",
        grade=Grade(
            evidence_id=8587,
            relevance=Relevance.EXACT,
            reason="正文覆盖",
        ),
    )
    return ChainResult(
        query="q",
        evidence=[item],
        answer="因为自动压缩在触发比等于阻塞比时会立刻卡住。",
        meta={
            "hit_count": 1,
            "graded": True,
            "grade_count": 1,
            "kept_count": 1,
            "gate_action": "answer",
            "best_relevance": "exact",
        },
    )


def _refuse_result() -> ChainResult:
    return ChainResult(
        query="q",
        evidence=[],
        answer="没有可用证据。",
        meta={
            "hit_count": 0,
            "graded": False,
            "grade_count": 0,
            "kept_count": 0,
            "gate_action": "refuse",
            "best_relevance": "unrated",
        },
    )


async def test_invoke_requires_auth(client: AsyncClient) -> None:
    """无 cookie → 401。"""
    response = await client.post(_PATH, json={"query": "为什么自动压缩失败"})
    assert response.status_code == 401


async def test_invoke_empty_query_422(client: AsyncClient, override_auth_maintainer) -> None:
    """空 query → 422。"""
    response = await client.post(_PATH, json={"query": ""})
    assert response.status_code == 422


async def test_invoke_query_too_long_422(client: AsyncClient, override_auth_maintainer) -> None:
    """超长 query → 422。"""
    response = await client.post(_PATH, json={"query": "x" * 8001})
    assert response.status_code == 422


async def test_invoke_missing_query_422(client: AsyncClient, override_auth_maintainer) -> None:
    """缺 query 字段 → 422。"""
    response = await client.post(_PATH, json={})
    assert response.status_code == 422


async def test_invoke_ok_includes_snippet(client: AsyncClient, override_auth_maintainer) -> None:
    """200 + {ok,data} 且 evidence 含 snippet / anchor。"""
    with patch(
        "app.ops.lc_evidence_chain.router.ainvoke_evidence_answer",
        new=AsyncMock(return_value=_hit_result()),
    ):
        response = await client.post(_PATH, json={"query": "为什么自动压缩失败"})
    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is True
    data = body["data"]
    assert data["answer"]
    assert data["meta"]["gate_action"] == "answer"
    assert data["meta"]["kept_count"] == 1
    assert data["evidence"]
    item = data["evidence"][0]
    assert isinstance(item["snippet"], str)
    assert item["snippet"]
    assert item["anchor"] == "2720#4"
    assert item["grade"]["relevance"] == "exact"
    assert "content" not in item


async def test_invoke_refuse_is_200(client: AsyncClient, override_auth_maintainer) -> None:
    """gate_action=refuse 仍是 200 成功态。"""
    with patch(
        "app.ops.lc_evidence_chain.router.ainvoke_evidence_answer",
        new=AsyncMock(return_value=_refuse_result()),
    ):
        response = await client.post(_PATH, json={"query": "无关问题"})
    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is True
    assert body["data"]["meta"]["gate_action"] == "refuse"
    assert body["data"]["evidence"] == []


async def test_invoke_upstream_failure_envelope(
    client: AsyncClient, override_auth_maintainer
) -> None:
    """链抛错 → 500 + {ok:false,error}。"""
    with patch(
        "app.ops.lc_evidence_chain.router.ainvoke_evidence_answer",
        new=AsyncMock(side_effect=RuntimeError("llm down")),
    ):
        response = await client.post(_PATH, json={"query": "为什么自动压缩失败"})
    assert response.status_code == 500
    body = response.json()
    assert body["ok"] is False
    assert body["error"]["code"] == "lc_evidence_failed"
    assert body["error"]["message"]


async def test_invoke_grader_llm_error_is_200(
    client: AsyncClient, override_auth_maintainer
) -> None:
    """grader complete 抛错走真实 ainvoke → 200 refuse，不是 500。"""
    item = EvidenceItem(
        id=1,
        repo="MoonshotAI/kimi-code",
        source_type="issue",
        source_id="1",
        chunk_index=0,
        content="body",
        title="t",
    )

    class _Boom:
        async def complete(self, messages, model=None):
            raise LlmProviderError("grader down", retryable=True, status_code=503)

    with (
        patch(
            "app.ops.lc_evidence_chain.chain.retrieve_evidence",
            new=AsyncMock(return_value=RetrieveResult(query="q", evidence=[item])),
        ),
        patch(
            "app.ops.lc_evidence_chain.grader.get_llm_provider",
            return_value=_Boom(),
        ),
    ):
        response = await client.post(_PATH, json={"query": "为什么自动压缩失败"})

    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is True
    assert body["data"]["meta"]["gate_action"] == "refuse"
    assert body["data"]["evidence"] == []
    assert body["data"]["answer"] == EMPTY_EVIDENCE_ANSWER
