"""lg-rag 窗口压缩与图输入装配（不依赖 chat/session）。

`compress_window` / `assemble_graph_messages` 保持纯函数（无 DB · 无 IO）。
事实型记忆注入（memory-facts-p0）集中在
`assemble_graph_messages_with_memory`：**默认关**（`MEMORY_FACTS_ENABLED`），
关闭时输出与 `assemble_graph_messages` 逐字节一致；开启时把召回到的
active facts 渲染为**系统消息尾部独立块**（`[已知事实]`，每条 `key=value` 一行）。
"""
from __future__ import annotations

import json
import logging
import os
from collections.abc import Mapping
from typing import Any

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage

from app.ops.tracing import update_current_span_metadata

logger = logging.getLogger(__name__)

DEFAULT_MAX_FULL_TURNS = 6
DEFAULT_GROUP_SIZE = 2


def compress_window(
    turns: list[dict],
    *,
    max_full_turns: int = DEFAULT_MAX_FULL_TURNS,
    group_size: int = DEFAULT_GROUP_SIZE,
) -> list[dict]:
    """保留最近 ``max_full_turns`` 轮全量；更早轮次按 ``group_size`` 合并为摘要占位。

    每 turn 形如 ``{"role": "user"|"assistant"|"system", "content": str}``。
    压缩失败时降级为截断（只保留尾部 max_full_turns 轮）。
    """
    try:
        if max_full_turns <= 0 or len(turns) <= max_full_turns:
            return list(turns)
        if group_size <= 0:
            return list(turns[-max_full_turns:])

        tail = turns[-max_full_turns:]
        head = turns[:-max_full_turns]
        compressed: list[dict] = []
        for i in range(0, len(head), group_size):
            chunk = head[i : i + group_size]
            roles = {t.get("role") for t in chunk}
            compressed.append(
                {
                    "role": "system",
                    "content": (
                        f"[历史摘要 · {len(chunk)} 轮 · roles={','.join(sorted(str(r) for r in roles))}]"
                    ),
                }
            )
        return compressed + list(tail)
    except Exception:
        if max_full_turns <= 0:
            return []
        return list(turns[-max_full_turns:])


def assemble_graph_messages(
    query: str,
    history_turns: list[dict] | None = None,
    *,
    max_full_turns: int = DEFAULT_MAX_FULL_TURNS,
    group_size: int = DEFAULT_GROUP_SIZE,
) -> list[BaseMessage]:
    """历史压缩后的 LC 消息 + 本轮 HumanMessage(query)。"""
    compressed = compress_window(
        list(history_turns or []),
        max_full_turns=max_full_turns,
        group_size=group_size,
    )
    messages: list[BaseMessage] = []
    for turn in compressed:
        role = (turn.get("role") or "user") if isinstance(turn, dict) else "user"
        content = ""
        if isinstance(turn, dict):
            raw = turn.get("content")
            content = raw if isinstance(raw, str) else str(raw or "")
        if role == "assistant":
            messages.append(AIMessage(content=content))
        elif role == "system":
            messages.append(SystemMessage(content=content))
        else:
            messages.append(HumanMessage(content=content))
    messages.append(HumanMessage(content=query))
    return messages


# ---------------- 事实型记忆注入（memory-facts-p0 · 默认关） ----------------

#: 注入块首行标记；块内每条事实 `key=value` 一行
MEMORY_FACTS_HEADER = "[已知事实]"
DEFAULT_MEMORY_FACTS_MAX_ITEMS = 8

_TRUTHY = ("1", "true", "yes", "on")
_FALSY = ("0", "false", "no", "off")


def memory_facts_enabled() -> bool:
    """`MEMORY_FACTS_ENABLED`：默认 false；非法值回退 false + warning。"""
    raw = (os.getenv("MEMORY_FACTS_ENABLED") or "").strip().lower()
    if not raw:
        return False
    if raw in _TRUTHY:
        return True
    if raw in _FALSY:
        return False
    logger.warning("invalid MEMORY_FACTS_ENABLED=%r; fallback to false", raw)
    return False


def memory_facts_max_items() -> int:
    """`MEMORY_FACTS_MAX_ITEMS`：默认 8；非法或 ≤0 回退 8 + warning。"""
    raw = (os.getenv("MEMORY_FACTS_MAX_ITEMS") or "").strip()
    if not raw:
        return DEFAULT_MEMORY_FACTS_MAX_ITEMS
    try:
        n = int(raw)
    except ValueError:
        logger.warning(
            "invalid MEMORY_FACTS_MAX_ITEMS=%r; fallback to %d",
            raw,
            DEFAULT_MEMORY_FACTS_MAX_ITEMS,
        )
        return DEFAULT_MEMORY_FACTS_MAX_ITEMS
    if n <= 0:
        logger.warning(
            "MEMORY_FACTS_MAX_ITEMS=%r <= 0; fallback to %d",
            raw,
            DEFAULT_MEMORY_FACTS_MAX_ITEMS,
        )
        return DEFAULT_MEMORY_FACTS_MAX_ITEMS
    return n


def _fact_key_value(item: Any) -> tuple[str, Any]:
    """兼容 ORM 行与 dict（service 返回 ORM；测试可传 dict）。"""
    if isinstance(item, Mapping):
        return str(item.get("key") or ""), item.get("value")
    return str(getattr(item, "key", "") or ""), getattr(item, "value", None)


def render_memory_facts_block(facts: list[Any]) -> str:
    """渲染注入块：首行 `[已知事实]`，其后每条 `key=value` 一行。

    value 为 str 时直写（换行转义为 \\n 保住一行一条），其它标量 JSON 序列化。
    空列表返回空串（调用方据此不注入）。
    """
    if not facts:
        return ""
    lines = [MEMORY_FACTS_HEADER]
    for item in facts:
        key, value = _fact_key_value(item)
        text = (
            value.replace("\n", "\\n")
            if isinstance(value, str)
            else json.dumps(value, ensure_ascii=False)
        )
        lines.append(f"{key}={text}")
    return "\n".join(lines)


def inject_memory_facts_block(
    messages: list[BaseMessage], block: str
) -> list[BaseMessage]:
    """把块作为**独立 SystemMessage** 插到既有前缀系统消息之后（无则置队首）。

    空块原样返回（零 diff）；不掺入任何 prompt 模板 / 指令正文。
    """
    if not block:
        return messages
    idx = 0
    for msg in messages:
        if isinstance(msg, SystemMessage):
            idx += 1
        else:
            break
    return [*messages[:idx], SystemMessage(content=block), *messages[idx:]]


async def assemble_graph_messages_with_memory(
    query: str,
    history_turns: list[dict] | None = None,
    *,
    tenant_id: str | None = None,
    user_id: str | None = None,
    max_full_turns: int = DEFAULT_MAX_FULL_TURNS,
    group_size: int = DEFAULT_GROUP_SIZE,
) -> list[BaseMessage]:
    """装配 + 可选记忆注入。**关闭时与 assemble_graph_messages 逐字节一致。**

    身份纪律：tenant/user 由调用方从请求 ctx 取（tenant_context ContextVar /
    阶段 T 头校验链路 / session 用户）后**显式传入**；模型产出不得参与。
    召回故障 → 记 log + span `memory_degraded`，降级为不注入（不拖垮请求）。
    span metadata 记 `memory_facts_injected=N`（tracing 未开时静默 no-op）。
    """
    messages = assemble_graph_messages(
        query,
        history_turns,
        max_full_turns=max_full_turns,
        group_size=group_size,
    )
    if not memory_facts_enabled():
        return messages
    if not (tenant_id or "").strip() or not (user_id or "").strip():
        logger.warning(
            "MEMORY_FACTS_ENABLED on but tenant/user missing; skip injection"
        )
        return messages
    try:
        # 延迟 import：continuity 保持纯函数可独立加载；memory 依赖 db
        from app.ops.memory import service as memory_service

        facts = await memory_service.recall_active(
            tenant_id.strip(),
            user_id.strip(),
            limit=memory_facts_max_items(),
        )
    except Exception:
        logger.exception("memory facts recall failed; degrade to no injection")
        update_current_span_metadata({"memory_degraded": True})
        return messages
    if not facts:
        update_current_span_metadata({"memory_facts_injected": 0})
        return messages
    block = render_memory_facts_block(facts)
    update_current_span_metadata({"memory_facts_injected": len(facts)})
    return inject_memory_facts_block(messages, block)
