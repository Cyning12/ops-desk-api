"""lg-rag 窗口压缩与图输入装配（纯函数 · 无 DB · 不依赖 chat/session）。"""
from __future__ import annotations

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage

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
