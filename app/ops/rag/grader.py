"""R-3 枚举评级闸（契约 Q4 · 本页最重要）。

CRAG 式：融合后 grader 节点逐条评级（top-5 批量一次调用，便宜模型），
按最高等级决定答/拒。四档判死定义（契约 4a）：
  irrelevant 毫不相关 → 拒答
  weak       有关键词重叠但无可用证据 → 拒答
  relevant   含可用证据但只覆盖一部分 → 回答 + 引用 + 注明「仅部分证据」
  exact      直接回答所问 → 回答 + 引用
RRF 分数不进闸（契约 4b）。

Prompt 版本（env ``RAG_GRADER_PROMPT``，默认 ``v1``）：
  v1 — 基线文案（r4-2 / r4-R-floor04 等历史报告所用）
  v2 — 加严「可用证据」边界，便于在 CE floor=0.4/ratio=0.75 下对照实验
"""
from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass
from enum import StrEnum

from app.llm.schema import BaseProvider, LlmMessage
from app.ops.rag.prefix import strip_doc_context_prefix
from app.ops.rag.retrieve import RetrievedChunk

logger = logging.getLogger(__name__)

REFUSAL_TEXT = "未查询到相关内容，无法针对此问题进行回答"  # 契约 4c 人填话术

DEFAULT_GRADER_PROMPT = "v1"


class Relevance(StrEnum):
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


# --- Prompt 版本：枚举与 JSON 契约不变，仅措辞；对照时只改 RAG_GRADER_PROMPT ---

GRADER_SYSTEM_V1 = """你是检索结果评级器。给定用户问题和若干候选文档块，逐条判断文档块与问题的相关等级。

等级判死定义：
* irrelevant：主题不搭
* weak：有关键词重叠但无可用证据（提了词，没实质内容）
* relevant：含可用证据，但只覆盖问题一部分
* exact：直接回答所问

只输出 JSON 数组，每项 {"chunk_id": <int>, "relevance": "<irrelevant|weak|relevant|exact>", "reason": "<一行>"}。
不要输出任何其他内容。"""

GRADER_SYSTEM_V2 = """你是检索结果评级器。给定用户问题和若干候选文档块，逐条判断该块能否作为回答该问题的证据。

### 等级判死（四档不变）
* irrelevant：主题不搭，或讨论的是别的功能/场景（即便有个别相同词）
* weak：仅有关键词/目录/标题级重叠，**没有**可用来回答问题的事实、步骤、结论或配置说明
* relevant：含可用证据，但只覆盖问题一部分（缺条件、缺步骤、缺另一半结论）
* exact：块内证据足以直接回答所问（允许跨语言：问中文、块英文亦可）

### 判定纪律（v2）
1. 「可用证据」= 读完该块后，能据此写出问题答案的一部分或全部；仅主题相近 ≠ relevant。
2. 宁可标 weak / irrelevant，也不要把「同产品线闲聊/相邻功能」抬成 relevant。
3. 负向/语料外问题：若块无法证实或证伪用户所问之事，最高多为 weak。
4. 跨语言不降档：证据在即可，不因中英不一致而降为 weak。
5. 每个 chunk 独立评级；不要因为同批其它块很相关就抬高本块。

### 输出
只输出 JSON 数组，每项 {"chunk_id": <int>, "relevance": "<irrelevant|weak|relevant|exact>", "reason": "<一行>"}。
不要输出任何其他内容。"""

_GRADER_PROMPTS: dict[str, str] = {
    "v1": GRADER_SYSTEM_V1,
    "v2": GRADER_SYSTEM_V2,
}

# 兼容旧引用名：指向基线 v1 原文（非「当前选中」）
_GRADER_SYSTEM = GRADER_SYSTEM_V1


def grader_prompt_version() -> str:
    """``RAG_GRADER_PROMPT``：v1（默认）| v2。未知值回退 v1 并打警告。"""
    raw = (os.getenv("RAG_GRADER_PROMPT") or DEFAULT_GRADER_PROMPT).strip().lower()
    if raw in _GRADER_PROMPTS:
        return raw
    logger.warning("RAG_GRADER_PROMPT=%r 未知；回退 %s", raw, DEFAULT_GRADER_PROMPT)
    return DEFAULT_GRADER_PROMPT


def grader_system_prompt(version: str | None = None) -> str:
    """返回指定或当前 env 选定的 grader system prompt。"""
    ver = (version or grader_prompt_version()).strip().lower()
    return _GRADER_PROMPTS.get(ver, GRADER_SYSTEM_V1)


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
    snippet_chars: int = 1200,
    prompt_version: str | None = None,
) -> list[Grade]:
    """top-5 批量一次调用（契约 4b：每 query +1 次 LLM 调用，便宜模型）。"""
    ver = (prompt_version or grader_prompt_version()).strip().lower()
    system = grader_system_prompt(ver)
    blocks = []
    for c in chunks:
        body = strip_doc_context_prefix(c.content)[:snippet_chars]
        blocks.append(f"### chunk_id={c.id}（{c.source_type} {c.anchor}）\n{body}")
    user = f"用户问题：{query}\n\n候选文档块：\n\n" + "\n\n".join(blocks)
    raw = await provider.complete(
        [LlmMessage(role="system", content=system), LlmMessage(role="user", content=user)],
        model=model,
    )
    grades = parse_grades(raw, {c.id for c in chunks})
    logger.info(
        "grader: prompt=%s query=%r grades=%s",
        ver,
        query[:60],
        [(g.chunk_id, g.relevance.value) for g in grades],
    )
    return grades
