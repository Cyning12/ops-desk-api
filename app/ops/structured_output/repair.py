"""确定性结构 repair：只修标点/括号类结构符号，不改写字符串语义意图。"""

from __future__ import annotations

import re

# 弯引号 / 全角括号 → ASCII JSON 结构符号（不含「」以免误伤字符串内语义）
_STRUCT_TRANS = str.maketrans(
    {
        "\u201c": '"',  # “
        "\u201d": '"',  # ”
        "\u2018": "'",  # ‘
        "\u2019": "'",  # ’
        "\uff5b": "{",  # ｛
        "\uff5d": "}",  # ｝
        "\uff3b": "[",  # ［
        "\uff3d": "]",  # ］
    }
)

_TRAILING_COMMA_RE = re.compile(r",\s*([}\]])")


def deterministic_repair(text: str) -> str:
    """对疑似 JSON 文本做确定性结构修复。

    仅替换弯引号、全角括号，并去掉 ``}`` / ``]`` 前的尾随逗号。
    不改写已是合法字符串字面量内的语义字符（如中文引号「」）。
    """
    out = (text or "").translate(_STRUCT_TRANS)
    return _TRAILING_COMMA_RE.sub(r"\1", out)
