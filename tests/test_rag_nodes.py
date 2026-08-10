"""R-3 接线节点单测（gate 路由 / 拒答 / 引用卡片映射）。"""
from app.ops.chat.rag_nodes import _to_source, refuse_node, route_by_gate
from app.ops.rag.grader import REFUSAL_TEXT
from app.ops.rag.retrieve import RetrievedChunk


def _chunk() -> RetrievedChunk:
    return RetrievedChunk(
        id=1,
        repo="MoonshotAI/kimi-code",
        source_type="issue",
        source_id="2720",
        chunk_index=3,
        content="[Document Context]\nTitle: 压缩取消\nType: issue\nRef: R#2720\n---\nContent: 正文",
        metadata={"html_url": "https://github.com/x/2720"},
    )


def test_route_by_gate():
    assert route_by_gate({"gate_action": "refuse"}) == "refuse"
    assert route_by_gate({"gate_action": "answer_partial"}) == "generate_answer"
    assert route_by_gate({"gate_action": "answer"}) == "generate_answer"


async def test_refuse_node_uses_contract_text():
    result = await refuse_node({"query": "q"})
    assert result["answer"] == REFUSAL_TEXT
    event = result["events"][0]
    assert event["event_type"] == "answer"
    assert event["payload"]["refused"] is True


def test_to_source_contract_shape():
    s = _to_source(_chunk(), "exact")
    assert s["anchor"] == "2720#3"
    assert s["title"] == "压缩取消"  # 前缀 Title 行解析
    assert s["snippet"] == "正文"  # 剥前缀（契约 4c）
    assert s["url"] == "https://github.com/x/2720"
    assert s["relevance"] == "exact"
    assert "rrf" not in s  # 用户面不展示分数（契约 4c）
