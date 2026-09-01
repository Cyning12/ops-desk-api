"""lg-rag T5 · 终答 answer token delta 桥（freeze lg-rag-sse-v1 扩展）。

背景：aggregator / direct_answer 走自定义 ``provider.complete``（非
LangChain BaseChatModel），``astream(stream_mode="messages")`` 不会表面化
其 token。故采用 provider 流式桥接：``BaseProvider.complete_stream``
（SiliconFlow / Bailian 均实现，OpenAI 兼容 ``stream=True``）。

机制：SSE emit 循环（``sse_stream.iter_lg_rag_sse``）经 contextvar 挂
token sink；终答节点调 ``complete_answer_streaming`` ——
- 有 sink：``complete_stream`` 逐 chunk 推送 ``(agent_role, chunk)``，
  emit 循环发 ``answer`` ``{"delta": ...}`` 帧；节点 updates 帧到后再发
  终帧 ``{"content": <full>, "final": true}``（T2 兼容）；
- 无 sink（invoke / 非 SSE 路径）：直接 ``complete``，行为与 T2 完全一致；
- 流式不可用 / 异常：降级 ``complete`` 整段（T2 行为）+ 日志
  （failure_paths：provider 不支持流式 / token 桥异常）。

token 归属 **仅** aggregator / direct_answer 的 LLM 调用；其他节点 LLM
token 不进 SSE。禁止 import app.ops.session / app.ops.chat。
"""
from __future__ import annotations

import contextvars
import logging
from collections.abc import Awaitable, Callable, Iterable

from app.llm.schema import BaseProvider, LlmMessage

logger = logging.getLogger(__name__)

# sink(agent_role, chunk_text)：把终答 token chunk 交给 SSE emit 循环
AnswerTokenSink = Callable[[str, str], Awaitable[None]]

_answer_token_sink: contextvars.ContextVar[AnswerTokenSink | None] = (
    contextvars.ContextVar("lg_rag_answer_token_sink", default=None)
)


def current_answer_token_sink() -> AnswerTokenSink | None:
    """当前上下文的 token sink；无（invoke / 非 SSE）则 ``None``。"""
    return _answer_token_sink.get()


def set_answer_token_sink(
    sink: AnswerTokenSink,
) -> contextvars.Token[AnswerTokenSink | None]:
    """挂 sink（SSE emit 循环在创建图执行 task 前调用，context 随之传播）。"""
    return _answer_token_sink.set(sink)


def reset_answer_token_sink(
    handle: contextvars.Token[AnswerTokenSink | None],
) -> None:
    """摘除 sink（emit 循环 finally 中复位，防泄漏到调用方 context）。"""
    _answer_token_sink.reset(handle)


async def complete_answer_streaming(
    provider: BaseProvider,
    messages: Iterable[LlmMessage],
    *,
    model: str | None = None,
    node: str,
) -> str:
    """终答 LLM 调用：有 sink 走 ``complete_stream`` 逐 chunk 上屏，否则整段。

    返回全文（与 ``provider.complete`` 语义一致，节点照常写回 messages）。
    流式中途异常：已推送的 delta 保留，降级 ``complete`` 取整段并照常返回
    （终帧 ``content`` 全量替换语义兜底，见 05 §10.4 常见坑）。
    """
    sink = current_answer_token_sink()
    if sink is None:
        return await provider.complete(messages, model=model)
    parts: list[str] = []
    try:
        async for chunk in provider.complete_stream(messages, model=model):
            text = chunk.content if isinstance(chunk.content, str) else ""
            if not text:
                continue
            parts.append(text)
            await sink(node, text)
    except Exception as exc:
        logger.warning(
            "lg_rag %s token 流不可用（已发 %d chunk），降级整段 complete err=%r",
            node,
            len(parts),
            exc,
        )
        return await provider.complete(messages, model=model)
    return "".join(parts)
