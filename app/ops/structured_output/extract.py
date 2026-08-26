"""公共 JSON 对象提取（剥 code fence、容忍前后杂讯）。"""

from __future__ import annotations

import json
import re

_FENCE_RE = re.compile(r"^\x60{3}(?:json)?|\x60{3}$", flags=re.MULTILINE)
_OBJECT_RE = re.compile(r"\{.*\}", flags=re.DOTALL)


def strip_code_fences(text: str) -> str:
    """去掉首尾 markdown code fence（含可选 json 语言标签）。"""
    return _FENCE_RE.sub("", text).strip()


def extract_json_object(raw: str) -> dict | None:
    """宽容提取文本中的 JSON 对象。

    行为对齐原 ``lg_rag.multi.nodes._extract_json_object``：
    容忍 fence 与前后杂文本；成功仅返回 ``dict``，否则 ``None``。
    """
    text = (raw or "").strip()
    if not text:
        return None
    text = strip_code_fences(text)
    try:
        data = json.loads(text)
    except (json.JSONDecodeError, TypeError):
        m = _OBJECT_RE.search(text)
        if not m:
            return None
        try:
            data = json.loads(m.group(0))
        except (json.JSONDecodeError, TypeError):
            return None
    return data if isinstance(data, dict) else None
