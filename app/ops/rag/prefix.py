"""向量文本前缀注入（契约 §1b）。

语义信号以文本前缀注入 content 再 embed；展示时剥离（strip_doc_context_prefix）。
分工原则：用户会念出来的（标题/编号/类型）进前缀；只用于过滤和展示的留
metadata 或活表。两边都放 = 浪费 token + 稀释向量。
"""
from __future__ import annotations

import re

PREFIX_HEADER = "[Document Context]"

_PREFIX_RE = re.compile(r"\A\[Document Context\]\n.*?\n---\nContent: ", re.DOTALL)


def build_prefix(
    *,
    title: str,
    source_type: str,
    ref: str,
    module_tag: str | None = None,
) -> str:
    """构造前缀块。

    ref 取值：issue/pr 为 ``<repo>#<number>``；doc 为文档路径。
    module_tag 有才写（契约 §1b）。
    """
    lines = [
        PREFIX_HEADER,
        f"Title: {title}",
        f"Type: {source_type}",
        f"Ref: {ref}",
    ]
    if module_tag:
        lines.append(f"Module: {module_tag}")
    return "\n".join(lines)


def embed_text(prefix: str, content: str) -> str:
    """embed 输入 = 前缀 + content（E5：800 上限只管 content，前缀计入模型硬顶断言）。"""
    return f"{prefix}\n---\nContent: {content}"


def strip_doc_context_prefix(text: str) -> str:
    """展示前剥离前缀（Ink 实证：snippet 不含语义注入）。"""
    return _PREFIX_RE.sub("", text, count=1)
