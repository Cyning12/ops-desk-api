"""多轮指代消解 · 装配层查询重写（query-coref-rewrite · 默认关）。

纪律（SPEC query-coref-rewrite §2/§5 · task D1–D3 钉死）：
- **先重写后召回**（D1）：resolved_query 由装配层（continuity impl）在两条
  装配分支（session_summary on/off）**之前**一次算出；末位 HumanMessage 与
  记忆向量召回统一吃它，禁颠倒。
- **off（未设/falsy/非法值）→ 零 LLM 调用零 span**，装配输出与现网逐字节
  一致（TC1 三模式对拍钉死）；非法值 warning 回退关（session_summary 先例）。
- **任何失败 → 静默降级原文**（D2/FP-3）：LLM 异常 / 超时 / 非法输出
  （确定式三规则：strip 空串 / 含换行拒多行不截首行 / strip 后 >512 字符，
  不以问号作判据 · 不另加启发式）→ span query_rewrite_applied=false +
  query_rewrite_fallback=true；成功 → query_rewrite_applied=true +
  原文/改写长度（不落改写全文）。禁止因重写失败让主链路失败。
- **原文 SoT 零污染**（D3/FP-6）：落盘 persist_thread_turns 与 run.start
  payload.query 仍记原文（装配层以下零感知）；首轮无历史短路零 LLM 调用。
- LLM 调用走 **rewrite 档**（resolve_task_model("rewrite") · 默认 None 沿用
  现网默认 · OPS_LLM_TIER_REWRITE_MODEL 覆盖）；usage 经 use_run_context
  （task_type="rewrite" · surface="lg_rag"）归因；重试/熔断由 provider
  包装层自动继承零改造。每请求至多一次重写调用；不扩 CACHEABLE_TASK_TYPES。
- 边界：本模块属 lg_rag 族，允许出边 llm/prompts/tracing/config（import-linter
  lg-rag-outbound 契约）；不依赖 chat/session/db/memory。
"""

from __future__ import annotations

import asyncio
import logging
import os

from app.config import settings
from app.llm.factory import get_llm_provider
from app.llm.model_catalog import resolve_task_model
from app.llm.schema import LlmMessage
from app.llm.usage import use_run_context
from app.ops.prompts import render
from app.ops.tracing import update_current_span_metadata

logger = logging.getLogger(__name__)

#: 指代消解 prompt 资产（无变量 · 对话历史与最新问题经 user 消息传入 · summary 先例）
QUERY_REWRITE_TEMPLATE_ID = "lg_rag.query_rewrite.system"
#: 单次重写调用超时（秒 · summary SUMMARY_TIMEOUT_S 先例）；超时 = 降级原文
QUERY_REWRITE_TIMEOUT_S = 30.0
#: 改写输出长度上限（strip 后字符数 · 恰 512 接受 · 超出判非法降级）
QUERY_REWRITE_MAX_CHARS = 512
#: 喂给重写器的历史窗口轮数上限（与 compress_window 默认 max_full_turns 对齐）
_HISTORY_WINDOW = 6

_TRUTHY = {"1", "true", "on", "yes"}
_FALSY = {"0", "false", "off", "no"}


def query_rewrite_enabled() -> bool:
    """LG_RAG_QUERY_REWRITE_ENABLED 开关（默认关 · 非法值 warning 回退关）。

    session_summary_enabled 先例三件套：strip/lower；空与 falsy → False；
    非法值 → warning + False（env 每次重读即时生效 · 无缓存）。
    """
    raw = os.getenv("LG_RAG_QUERY_REWRITE_ENABLED", "").strip().lower()
    if not raw:
        return False
    if raw in _TRUTHY:
        return True
    if raw in _FALSY:
        return False
    logger.warning("invalid LG_RAG_QUERY_REWRITE_ENABLED=%r; fallback to false", raw)
    return False


def _resolve_model() -> str:
    """rewrite 档解析；档 None → 沿用现网默认（settings.ops_llm_model）。"""
    tier_model, _source = resolve_task_model("rewrite")
    return tier_model or settings.ops_llm_model


def _validate_rewrite(raw: str) -> str | None:
    """确定式三规则判非法（task D2 钉死 · 不以问号作判据 · 不另加启发式）：

    1. strip 后空串 → 非法；
    2. 含换行（LF/CR）→ 拒多行 **不截首行**，整体非法；
    3. strip 后 >QUERY_REWRITE_MAX_CHARS 字符 → 非法（恰 512 接受）。
    合法 → 返回 strip 后文本（strip 是规范化不是判非法）。
    """
    text = raw.strip()
    if not text:
        return None
    if "\n" in text or "\r" in text:
        return None
    if len(text) > QUERY_REWRITE_MAX_CHARS:
        return None
    return text


def _build_user_content(query: str, history_turns: list[dict]) -> str:
    """user 消息窗：对话历史（末 _HISTORY_WINDOW 轮）+ 最新问题原文。"""
    lines = []
    for turn in history_turns[-_HISTORY_WINDOW:]:
        role = "用户" if turn.get("role") == "user" else "助手"
        lines.append(f"{role}：{turn.get('content') or ''}")
    history_block = "\n".join(lines)
    return f"对话历史：\n{history_block}\n\n最新问题：{query}"


async def maybe_rewrite_query(query: str, history_turns: list[dict] | None) -> str:
    """开关 on 且有历史 → 至多一次 LLM 指代消解；其余路径原样返回原文。

    - off / 非法 env → 零调用零 span 原文返回；
    - 首轮无历史（None/[]）→ 短路，零调用零 span（TC4）；
    - LLM 异常 / 超时 / 非法输出 → 降级原文 + span 双标记（TC3/TC9）。
    """
    if not query_rewrite_enabled():
        return query
    if not history_turns:
        return query
    provider = get_llm_provider()
    model = _resolve_model()
    system_content = render(QUERY_REWRITE_TEMPLATE_ID)
    try:
        with use_run_context(surface="lg_rag", task_type="rewrite"):
            raw = await asyncio.wait_for(
                provider.complete(
                    [
                        LlmMessage(role="system", content=system_content),
                        LlmMessage(
                            role="user",
                            content=_build_user_content(query, history_turns),
                        ),
                    ],
                    model=model,
                ),
                timeout=QUERY_REWRITE_TIMEOUT_S,
            )
    except Exception:
        logger.warning(
            "lg-rag query rewrite failed; fallback to original query", exc_info=True
        )
        update_current_span_metadata(
            {"query_rewrite_applied": False, "query_rewrite_fallback": True}
        )
        return query
    text = _validate_rewrite(raw)
    if text is None:
        logger.warning("lg-rag query rewrite invalid output; fallback to original query")
        update_current_span_metadata(
            {"query_rewrite_applied": False, "query_rewrite_fallback": True}
        )
        return query
    update_current_span_metadata(
        {
            "query_rewrite_applied": True,
            "query_rewrite_src_len": len(query),
            "query_rewrite_dst_len": len(text),
        }
    )
    return text
