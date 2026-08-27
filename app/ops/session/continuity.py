"""Chat 窗口压缩策略（纯函数 · 无 DB）。"""

from __future__ import annotations


def compress_window(
    turns: list[dict],
    *,
    max_full_turns: int = 6,
    group_size: int = 2,
) -> list[dict]:
    """保留最近 ``max_full_turns`` 轮全量；更早轮次按 ``group_size`` 合并为摘要占位。

    每 turn 形如 ``{"role": "user"|"assistant", "content": str}``。
    压缩失败时降级为截断（只保留尾部 max_full_turns 轮）。
    """
    if max_full_turns <= 0 or len(turns) <= max_full_turns:
        return list(turns)
    if group_size <= 0:
        return turns[-max_full_turns:]

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
                    f"[历史摘要 · {len(chunk)} 轮 · roles={','.join(sorted(roles))}]"
                ),
            }
        )
    return compressed + tail
