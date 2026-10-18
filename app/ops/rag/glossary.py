"""跨语言 query 扩展（契约 Q6 · 方案 D · 先手）。

痛点：tsvector 关键词路对中文 query 失明（'simple' 分词 + 语料含大量英文）。
机制：query 里的中文术语查表扩出英文同义词，组内 OR、组间 AND：
  「自动压缩被取消」→ (压缩 | compaction) & (取消 | cancel | cancelled)

词表外置 `glossary.yaml`（同目录），迭代维护不改代码。
命中词表的才展开，未命中的中文段不进 tsquery（交给语义路）；英文原词保留。
"""

from __future__ import annotations

import re
from pathlib import Path

import yaml

_GLOSSARY_PATH = Path(__file__).with_name("glossary.yaml")

_ZH_TO_EN: dict[str, list[str]] | None = None


def _load() -> dict[str, list[str]]:
    """懒加载词表（模块导入不读盘）。"""
    global _ZH_TO_EN
    if _ZH_TO_EN is None:
        data = yaml.safe_load(_GLOSSARY_PATH.read_text(encoding="utf-8"))
        _ZH_TO_EN = {str(k): [str(w) for w in v] for k, v in (data or {}).items()}
    return _ZH_TO_EN


_EN_WORD_RE = re.compile(r"[A-Za-z][A-Za-z0-9_.\-/#]+")


def expand_query_for_fts(query: str) -> str | None:
    """把混合 query 展开为 to_tsquery 表达式；无可用词项时返回 None。

    组内 OR（中文 | 英文同义词）、组间 AND。词表未命中的中文段丢弃（语义路兜底）。
    """
    table = _load()
    groups: list[str] = []
    consumed: set[str] = set()
    # 词表命中：长词优先（避免短词先吃掉长词组合）
    for zh in sorted(table, key=len, reverse=True):
        if zh in query and zh not in consumed:
            consumed.add(zh)
            syns = " | ".join([zh] + table[zh])
            groups.append(f"( {syns} )")
    # 英文原词保留（去重、跳过已被词表同义覆盖的）
    covered_en = {w for syns in table.values() for w in syns}
    for w in _EN_WORD_RE.findall(query):
        if w.lower() not in covered_en and w not in groups:
            groups.append(w)
    if not groups:
        return None
    return " & ".join(groups)
