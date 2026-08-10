"""R-3 枚举评级闸（契约 Q4 · 本页最重要）。

CRAG 式：融合后 grader 节点逐条评级（top-5 批量一次调用，便宜模型），
按最高等级决定答/拒。四档判死定义（契约 4a）：
  irrelevant 毫不相关 → 拒答
  weak       有关键词重叠但无可用证据 → 拒答
  relevant   含可用证据但只覆盖一部分 → 回答 + 引用 + 注明「仅部分证据」
  exact      直接回答所问 → 回答 + 引用
RRF 分数不进闸（契约 4b）。
"""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from enum import Enum

from app.llm.schema import BaseProvider, LlmMessage
from app.ops.rag.prefix import strip_doc_context_prefix
from app.ops.rag.retrieve import RetrievedChunk

logger = logging.getLogger(__name__)

REFUSAL_TEXT = "未查询到相关内容，无法针对此问题进行回答"  # 契约 4c 人填话术


class Relevance(str, Enum):
    IRRELEVANT = "irrelevant"
    WEAK = "weak"
    RELEVANT = "relevant"
    EXACT = "exact"


_RANK = {
    Relevance.IRRELEVANT: 0,
    Relevance.WEAK: 1,
    Relevance.RELEVANT: 2,
    Relevance.EXACT: 3,
}


@dataclass
class Grade:
    chunk_id: int
    relevance: Relevance
    reason: str


@dataclass
class GateDecision:
    action: str  # "refuse" | "answer_partial" | "answer"
    best: Relevance
    grades: list[Grade]


_GRADER_SYSTEM = """你是检索结果评级器。给定用户问题和若干候选文档块，逐条判断文档块与问题的相关等级。

等级判死定义：
* irrelevant：主题不搭
* weak：有关键词重叠但无可用证据（提了词，没实质内容）
* relevant：含可用证据，但只覆盖问题一部分
* exact：直接回答所问

只输出 JSON 数组，每项 {"chunk_id": <int>, "relevance": "<irrelevant|weak|relevant|exact>", "reason": "<一行>"}。
不要输出任何其他内容。"""


def decide(grades: list[Grade]) -> GateDecision:
    """闸判定（纯函数 · 契约 4b）：最高评级定行为。"""
    if not grades:
        return GateDecision(action="refuse", best=Relevance.IRRELEVANT, grades=[])
    best = max(grades, key=lambda g: _RANK[g.relevance])
    if _RANK[best.relevance] <= _RANK[Relevance.WEAK]:
        action = "refuse"
    elif best.relevance is Relevance.RELEVANT:
        action = "answer_partial"
    else:
        action = "answer"
    return GateDecision(action=action, best=best.relevance, grades=grades)


def parse_grades(raw: str, valid_ids: set[int]) -> list[Grade]:
    """解析 grader 输出；非法 JSON / 未知枚举 / 越界 chunk_id 一律丢弃（宁缺毋滥）。"""
    try:
        items = json.loads(raw.strip().removeprefix("```json").removesuffix("```").strip())
    except json.JSONDecodeError:
        logger.warning("grader 输出非 JSON：%r", raw[:200])
        return []
    grades: list[Grade] = []
    for item in items if isinstance(items, list) else []:
        try:
            chunk_id = int(item["chunk_id"])
            relevance = Relevance(str(item["relevance"]))
        except (KeyError, TypeError, ValueError):
            continue
        if chunk_id in valid_ids:
            grades.append(
                Grade(chunk_id=chunk_id, relevance=relevance, reason=str(item.get("reason", "")))
            )
    return grades


async def grade_chunks(
    provider: BaseProvider,
    query: str,
    chunks: list[RetrievedChunk],
    model: str | None = None,
    snippet_chars: int = 600,
) -> list[Grade]:
    """top-5 批量一次调用（契约 4b：每 query +1 次 LLM 调用，便宜模型）。"""
    blocks = []
    for c in chunks:
        body = strip_doc_context_prefix(c.content)[:snippet_chars]
        blocks.append(f"### chunk_id={c.id}（{c.source_type} {c.anchor}）\n{body}")
    user = f"用户问题：{query}\n\n候选文档块：\n\n" + "\n\n".join(blocks)
    raw = await provider.complete(
        [LlmMessage(role="system", content=_GRADER_SYSTEM), LlmMessage(role="user", content=user)],
        model=model,
    )
    grades = parse_grades(raw, {c.id for c in chunks})
    logger.info(
        "grader: query=%r grades=%s",
        query[:60],
        [(g.chunk_id, g.relevance.value) for g in grades],
    )
    return grades
