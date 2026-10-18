"""lg-rag HTTP：鉴权、校验、envelope 与三 mode 分派（mock 图入口，不连真库/LLM）。"""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

from httpx import AsyncClient
from langchain_core.messages import AIMessage, HumanMessage

_PATH = "/api/ops/lg-rag/invoke"

_CHAIN_META = {
    "gate_action": "answer",
    "hit_count": 2,
    "kept_count": 1,
    "best_relevance": "exact",
    "grade_count": 2,
}


def _state(
    *,
    answer: str = "因为自动压缩在触发比等于阻塞比时会立刻卡住。",
    route: str = "",
    retry_count: int = 0,
    chain_meta: dict | None = None,
    subtasks: list[dict] | None = None,
    subtask_results: list[dict] | None = None,
) -> dict:
    return {
        "messages": [HumanMessage(content="q"), AIMessage(content=answer)],
        "route": route,
        "retry_count": retry_count,
        "chain_meta": chain_meta or {},
        "subtasks": subtasks or [],
        "subtask_results": subtask_results or [],
    }


def _patch_entries(**overrides: AsyncMock) -> tuple:
    """patch router 模块内三个 ainvoke 入口；未覆盖的给默认 AsyncMock。"""
    mocks = {
        "basic": AsyncMock(return_value=_state()),
        "router": AsyncMock(return_value=_state()),
        "supervisor": AsyncMock(return_value=_state()),
    }
    mocks.update(overrides)
    return (
        patch("app.ops.lg_rag.router.ainvoke_basic_agent", new=mocks["basic"]),
        patch("app.ops.lg_rag.router.ainvoke_router_agent", new=mocks["router"]),
        patch(
            "app.ops.lg_rag.router.ainvoke_supervisor_agent",
            new=mocks["supervisor"],
        ),
        mocks,
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


async def test_invoke_invalid_mode_422(client: AsyncClient, override_auth_maintainer) -> None:
    """非法 mode → 422（Pydantic Literal 校验）。"""
    response = await client.post(_PATH, json={"query": "q", "mode": "chat"})
    assert response.status_code == 422


async def test_invoke_thread_id_too_long_422(client: AsyncClient, override_auth_maintainer) -> None:
    """超长 thread_id → 422（freeze：≤255 显式拒绝，与 web SPEC 一致）。"""
    response = await client.post(_PATH, json={"query": "q", "thread_id": "t" * 256})
    assert response.status_code == 422


async def test_invoke_default_mode_is_router(client: AsyncClient, override_auth_maintainer) -> None:
    """缺省 mode=router → 走 ainvoke_router_agent；envelope 字段齐。"""
    mock_router = AsyncMock(return_value=_state(route="rag", retry_count=1, chain_meta=_CHAIN_META))
    p_basic, p_router, p_supervisor, mocks = _patch_entries(router=mock_router)
    with p_basic, p_router, p_supervisor:
        response = await client.post(_PATH, json={"query": "为什么自动压缩失败"})
    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is True
    data = body["data"]
    assert data["mode"] == "router"
    assert data["answer"]
    assert data["route"] == "rag"
    assert data["retry_count"] == 1
    assert data["chain_meta"]["gate_action"] == "answer"
    assert data["chain_meta"]["hit_count"] == 2
    assert data["chain_meta"]["kept_count"] == 1
    assert data["chain_meta"]["best_relevance"] == "exact"
    assert data["chain_meta"]["grade_count"] == 2
    assert data["subtasks"] == []
    assert data["subtask_results"] == []
    mock_router.assert_awaited_once()
    mocks["basic"].assert_not_called()
    mocks["supervisor"].assert_not_called()


async def test_invoke_basic_mode_dispatch(client: AsyncClient, override_auth_maintainer) -> None:
    """mode=basic → 走 ainvoke_basic_agent；无 router，route 为空串。"""
    mock_basic = AsyncMock(return_value=_state(answer="basic 答案"))
    p_basic, p_router, p_supervisor, mocks = _patch_entries(basic=mock_basic)
    with p_basic, p_router, p_supervisor:
        response = await client.post(_PATH, json={"query": "q", "mode": "basic"})
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["mode"] == "basic"
    assert data["answer"] == "basic 答案"
    assert data["route"] == ""
    assert data["retry_count"] == 0
    assert data["chain_meta"] == {
        "gate_action": "",
        "hit_count": 0,
        "kept_count": 0,
        "best_relevance": "",
        "grade_count": 0,
    }
    mock_basic.assert_awaited_once()
    mocks["router"].assert_not_called()
    mocks["supervisor"].assert_not_called()


async def test_invoke_supervisor_mode_dispatch(
    client: AsyncClient, override_auth_maintainer
) -> None:
    """mode=supervisor → 走 ainvoke_supervisor_agent；subtasks 非空回显。"""
    mock_supervisor = AsyncMock(
        return_value=_state(
            answer="综合答案",
            subtasks=[{"id": 1, "type": "rag", "input": "压缩失败"}],
            subtask_results=[{"id": 1, "answer": "子答案"}],
        )
    )
    p_basic, p_router, p_supervisor, mocks = _patch_entries(supervisor=mock_supervisor)
    with p_basic, p_router, p_supervisor:
        response = await client.post(_PATH, json={"query": "q", "mode": "supervisor"})
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["mode"] == "supervisor"
    assert data["subtasks"] == [{"id": 1, "type": "rag", "input": "压缩失败"}]
    assert data["subtask_results"] == [{"id": 1, "answer": "子答案"}]
    mock_supervisor.assert_awaited_once()
    mocks["basic"].assert_not_called()
    mocks["router"].assert_not_called()


async def test_invoke_thread_id_generated_and_echoed(
    client: AsyncClient, override_auth_maintainer
) -> None:
    """缺省 thread_id 由服务端生成并回显；显式传入则原样回显并传给入口。"""
    mock_router = AsyncMock(return_value=_state())
    p_basic, p_router, p_supervisor, _ = _patch_entries(router=mock_router)
    with p_basic, p_router, p_supervisor:
        gen_resp = await client.post(_PATH, json={"query": "q"})
    assert gen_resp.status_code == 200
    generated = gen_resp.json()["data"]["thread_id"]
    assert generated
    assert len(generated) <= 255
    kwargs = mock_router.await_args.kwargs
    assert kwargs["thread_id"] == generated

    mock_router2 = AsyncMock(return_value=_state())
    p_basic, p_router, p_supervisor, _ = _patch_entries(router=mock_router2)
    with p_basic, p_router, p_supervisor:
        echo_resp = await client.post(_PATH, json={"query": "q", "thread_id": "my-thread-1"})
    assert echo_resp.status_code == 200
    assert echo_resp.json()["data"]["thread_id"] == "my-thread-1"
    assert mock_router2.await_args.kwargs["thread_id"] == "my-thread-1"


async def test_invoke_failure_envelope(client: AsyncClient, override_auth_maintainer) -> None:
    """入口抛错 → 500 + {ok:false,error}。"""
    mock_router = AsyncMock(side_effect=RuntimeError("llm down"))
    p_basic, p_router, p_supervisor, _ = _patch_entries(router=mock_router)
    with p_basic, p_router, p_supervisor:
        response = await client.post(_PATH, json={"query": "q"})
    assert response.status_code == 500
    body = response.json()
    assert body["ok"] is False
    assert body["error"]["code"] == "lg_rag_failed"
    assert body["error"]["message"] == "旁路调用失败"
