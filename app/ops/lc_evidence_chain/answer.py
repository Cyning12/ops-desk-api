"""依据 → 回答：prompt 外置 answer_system_prompt.yaml。"""

from __future__ import annotations

import logging
import os
from functools import lru_cache
from pathlib import Path

import yaml

from app.config import settings
from app.llm.factory import get_llm_provider
from app.llm.schema import LlmMessage
from app.ops.lc_evidence_chain.types import EvidenceItem
from app.ops.prompts.slots import (
    SlotIsolationError,
    assert_slots_declared,
    declare_slots,
    security_input_isolation_enabled,
    wrap_slot,
)
from app.ops.tracing import trace_span, update_current_span_metadata

logger = logging.getLogger(__name__)

_PROMPT_PATH = Path(__file__).with_name("answer_system_prompt.yaml")
DEFAULT_ANSWER_PROMPT = "v1"
EMPTY_EVIDENCE_ANSWER = "未检索到足够依据，无法给出有根据的回答。"
PARTIAL_GATE_SYSTEM_NOTE = (
    "【闸提示】当前为部分证据（answer_partial）："
    "回答开头必须写明「仅部分证据」，只陈述依据已覆盖部分，未覆盖处不要猜测。"
)


def answer_prompt_version() -> str:
    """``RAG_LC_ANSWER_PROMPT``：默认 v1。"""
    raw = (os.getenv("RAG_LC_ANSWER_PROMPT") or DEFAULT_ANSWER_PROMPT).strip().lower()
    return raw or DEFAULT_ANSWER_PROMPT


@lru_cache(maxsize=1)
def _load_prompt_file() -> dict:
    data = yaml.safe_load(_PROMPT_PATH.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"invalid answer prompt file: {_PROMPT_PATH}")
    return data


def _join_prompt_lines(lines: list | str) -> str:
    if isinstance(lines, str):
        return lines.strip()
    return "\n".join(str(x).rstrip() for x in lines).strip()


def answer_system_prompt(version: str | None = None) -> str:
    ver = (version or answer_prompt_version()).strip().lower()
    data = _load_prompt_file()
    block = (data.get("system") or {}).get(ver)
    if block is None:
        logger.warning("answer system prompt %r 缺失；回退 %s", ver, DEFAULT_ANSWER_PROMPT)
        block = (data.get("system") or {}).get(DEFAULT_ANSWER_PROMPT)
    if block is None:
        raise KeyError(f"answer system prompt missing: {ver}")
    return _join_prompt_lines(block)


def answer_user_template(version: str | None = None) -> str:
    ver = (version or answer_prompt_version()).strip().lower()
    data = _load_prompt_file()
    block = (data.get("user") or {}).get(ver)
    if block is None:
        logger.warning("answer user prompt %r 缺失；回退 %s", ver, DEFAULT_ANSWER_PROMPT)
        block = (data.get("user") or {}).get(DEFAULT_ANSWER_PROMPT)
    if block is None:
        raise KeyError(f"answer user prompt missing: {ver}")
    return _join_prompt_lines(block)


def format_evidence_block(evidence: list[EvidenceItem]) -> str:
    """把证据列表格式化为 user prompt 中的「检索依据」正文。"""
    if not evidence:
        return "（无检索依据）"
    lines: list[str] = []
    for i, e in enumerate(evidence, 1):
        title = e.title or e.anchor
        lines.append(f"[{i}] {e.source_type} {e.anchor} · {title}")
        lines.append(e.snippet)
        lines.append("")
    return "\n".join(lines).rstrip()


def _answer_model() -> str | None:
    return (os.getenv("RAG_LC_ANSWER_MODEL") or "").strip() or settings.ops_llm_model


def _assemble_isolated_messages(
    ver: str,
    query: str,
    retrieved_chunks: list[EvidenceItem],
    gate_action: str | None,
) -> list[LlmMessage]:
    """on 态装配（security-input-isolation D2 · RAG 面）：检索片段/问题走槽位。

    - 片段块走 `wrap_slot("rag_evidence", ...)`：`[{i}] {anchor}` 引用格式保留，
      节首加不可信声明 + 边界标记；query 走 `user_query` 槽；指令资产归
      `system_instruction`（trusted · 逐字节不变）。
    - 装配校验 `assert_slots_declared` 在发往 LLM 前执行：内容违例（未声明/
      未包装段）→ :class:`SlotIsolationError` 显式炸，**请求不发出**（下游
      零请求）；机制自身故障由调用方降级 off 态装配（与本异常语义分立）。
    """
    system = answer_system_prompt(ver)
    user = answer_user_template(ver).format(
        question=str(wrap_slot("user_query", query)),
        retrieved_chunks=str(wrap_slot("rag_evidence", format_evidence_block(retrieved_chunks))),
    )
    if (gate_action or "").strip() == "answer_partial":
        system = f"{system}\n{PARTIAL_GATE_SYSTEM_NOTE}"
        user = f"仅部分证据。\n\n{user}"
    system_msg = LlmMessage(role="system", content=wrap_slot("system_instruction", system))
    user_msg = LlmMessage(role="user", content=user)
    declare_slots(user_msg, ["user_query", "rag_evidence"])
    assert_slots_declared([system_msg, user_msg])
    return [system_msg, user_msg]


async def answer_question(
    query: str,
    retrieved_chunks: list[EvidenceItem],
    *,
    prompt_version: str | None = None,
    gate_action: str | None = None,
) -> str:
    """根据问题与证据生成答案；无证据时不调 LLM。

    ``gate_action=answer_partial`` 时注入「仅部分证据」约束（契约 4c）。
    """
    if not retrieved_chunks:
        logger.info("answer: empty evidence query=%r", query[:60])
        return EMPTY_EVIDENCE_ANSWER

    ver = (prompt_version or answer_prompt_version()).strip().lower()
    system = answer_system_prompt(ver)
    user = answer_user_template(ver).format(
        question=query,
        retrieved_chunks=format_evidence_block(retrieved_chunks),
    )
    if (gate_action or "").strip() == "answer_partial":
        system = f"{system}\n{PARTIAL_GATE_SYSTEM_NOTE}"
        user = f"仅部分证据。\n\n{user}"

    provider_name = (os.getenv("RAG_LC_ANSWER_PROVIDER") or "").strip() or None
    provider = get_llm_provider(provider_name)
    model = _answer_model()
    if security_input_isolation_enabled():
        try:
            messages = _assemble_isolated_messages(ver, query, retrieved_chunks, gate_action)
            update_current_span_metadata({"slots_wrapped": 3})
        except SlotIsolationError:
            # 内容违例（未声明/未包装段）→ 显式炸，**请求不发出**（下游零请求），
            # 与机制故障降级（except Exception 支路）语义分立。
            update_current_span_metadata({"input_isolation_rejected": True})
            logger.warning(
                "answer: input isolation rejected undeclared content; request not sent",
                exc_info=True,
            )
            raise
        except Exception:
            # 机制故障 → 该请求降级 off 态装配（与 off 态逐字节一致）+ span + log。
            logger.exception("answer: input isolation mechanism failed; degrade to off-state")
            update_current_span_metadata({"input_isolation_degraded": True})
            messages = [
                LlmMessage(role="system", content=system),
                LlmMessage(role="user", content=user),
            ]
    else:
        messages = [
            LlmMessage(role="system", content=system),
            LlmMessage(role="user", content=user),
        ]
    # 自研 provider 不走 LangChain LLM 类，CallbackHandler 抓不到 → 显式 generation
    with trace_span("answer_llm", run_type="llm", model=model):
        text = await provider.complete(messages, model=model)
    logger.info(
        "answer: prompt=%s gate=%s model=%s query=%r evidence=%d chars=%d",
        ver,
        gate_action or "-",
        model,
        query[:60],
        len(retrieved_chunks),
        len(text or ""),
    )
    return text if isinstance(text, str) else str(text)
