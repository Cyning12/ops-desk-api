"""结构感知 chunker（契约 §Q1a 规则 1-3 + §1d E1/E2/E5）。

切分优先级：标题 > 段落 > 句子；原子单元（fence / 表格）不切开。
- E1：原子单元允许整体超 800 上限单独成 chunk；truncate_middle 是 8192 保险丝
- E2：< 100 tokens 的小 chunk 与后邻合并，末尾无后邻则并入前一个
- E5：800 只管 content，不含前缀

token 计数通过 TokenCounter 注入，本模块不依赖具体 tokenizer。
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from app.ops.rag.tokenizer import TokenCounter

MAX_CHUNK_TOKENS = 800
MIN_CHUNK_TOKENS = 100
HARD_TOKEN_LIMIT = 8192  # bge-m3 模型序列上限

_HEADER_RE = re.compile(r"^#{1,6}\s")
_TABLE_ROW_RE = re.compile(r"^\s*\|.*\|")
_FENCE_LINE_RE = re.compile(r"^\s*(```|~~~)")
_FENCE_OPEN_RE = re.compile(r"^\s*(`{3,}|~{3,})")  # 捕获fence字符与长度（E9 参考实现用）
_SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?。！？;；:：])\s+|\n{2,}")


def _is_fence_close(line: str, opener: tuple[str, int], strict: bool) -> bool:
    """fence 闭合判定。strict=True 时按 CommonMark：同字符且长度 >= 开 fence。"""
    m = _FENCE_OPEN_RE.match(line)
    if not m:
        return False
    if not strict:
        return True
    return m.group(1)[0] == opener[0] and len(m.group(1)) >= opener[1]


@dataclass
class Block:
    kind: str  # "header" | "paragraph" | "code" | "table"
    text: str


def parse_blocks(md: str, *, _fence_strict: bool = False) -> list[Block]:
    """行级解析：fence / 表格 / 标题 / 段落四类块。空行仅作分隔。"""
    blocks: list[Block] = []
    lines = md.split("\n")
    i = 0
    while i < len(lines):
        line = lines[i]
        if not line.strip():
            i += 1
            continue
        if _FENCE_LINE_RE.match(line):
            om = _FENCE_OPEN_RE.match(line)
            opener = (om.group(1)[0], len(om.group(1)))
            j = i + 1
            while j < len(lines) and not _is_fence_close(lines[j], opener, _fence_strict):
                j += 1
            j = min(j + 1, len(lines))  # 含闭合行；未闭合则到文末
            blocks.append(Block("code", "\n".join(lines[i:j])))
            i = j
        elif _TABLE_ROW_RE.match(line):
            j = i
            while j < len(lines) and _TABLE_ROW_RE.match(lines[j]):
                j += 1
            blocks.append(Block("table", "\n".join(lines[i:j])))
            i = j
        elif _HEADER_RE.match(line):
            blocks.append(Block("header", line.strip()))
            i += 1
        else:
            j = i
            while (
                j < len(lines)
                and lines[j].strip()
                and not _HEADER_RE.match(lines[j])
                and not _FENCE_LINE_RE.match(lines[j])
                and not _TABLE_ROW_RE.match(lines[j])
            ):
                j += 1
            blocks.append(Block("paragraph", "\n".join(lines[i:j])))
            i = j
    return blocks


def parse_blocks_commonmark(md: str) -> list[Block]:
    """【未调用 · E9 参考实现】CommonMark fence 长度配对版 parse_blocks。

    与生产版的差异：开 fence 为 N 个反引号时，只有同字符且 >=N 的反引号行
    才闭合，```` 外层包裹 ``` 内层的嵌套代码块可正确识别为一个原子块。
    注意：#1089 类「内外同为 ``` 」的畸形源在本实现下行为不变（规范本就如此）；
    切换条件：语料中 ```` 嵌套形态增多时，将 parse_blocks 调用点换成本函数。
    """
    return parse_blocks(md, _fence_strict=True)


def split_sections(blocks: list[Block]) -> list[list[Block]]:
    """按标题分组：标题与其后续内容同 section（规则 1 的第一级边界）。"""
    sections: list[list[Block]] = []
    for b in blocks:
        if b.kind == "header" and sections:
            sections.append([b])
        elif sections:
            sections[-1].append(b)
        else:
            sections.append([b])
    return sections


def _split_sentences(text: str, counter: TokenCounter, budget: int) -> list[str]:
    """段落超限时按句子贪心打包；单句超限则整句独立（E1 原子化兜底）。"""
    sentences = [s for s in _SENTENCE_SPLIT_RE.split(text) if s.strip()]
    if not sentences:
        return [text]
    return _pack(sentences, counter, budget)


def _split_table(text: str, counter: TokenCounter, budget: int) -> list[str]:
    """表格超限时按行切，每组重复表头（契约规则 2：断表行失去列语义）。"""
    lines = text.split("\n")
    header_lines = lines[:2] if len(lines) >= 2 else lines[:1]  # 表头 + 分隔行
    rows = lines[len(header_lines) :]
    groups: list[str] = []
    cur = list(header_lines)
    for row in rows:
        trial = "\n".join(cur + [row])
        if len(cur) > len(header_lines) and counter.count(trial) > budget:
            groups.append("\n".join(cur))
            cur = list(header_lines)
        cur.append(row)
    if cur:
        groups.append("\n".join(cur))
    return groups


def _to_units(blocks: list[Block], counter: TokenCounter, budget: int) -> list[str]:
    """把块规范化为原子单元：超限段落/表格降级，fence 永不拆（E1）。"""
    units: list[str] = []
    for b in blocks:
        if counter.count(b.text) <= budget:
            units.append(b.text)
        elif b.kind == "table":
            units.extend(_split_table(b.text, counter, budget))
        elif b.kind == "paragraph":
            units.extend(_split_sentences(b.text, counter, budget))
        else:  # code / header：原子，整体超限也保留（E1）
            units.append(b.text)
    return units


def _pack(units: list[str], counter: TokenCounter, budget: int) -> list[str]:
    """贪心打包；超限原子单元先冲出当前包、单独成 chunk。"""
    chunks: list[str] = []
    cur: list[str] = []
    cur_tokens = 0
    for u in units:
        n = counter.count(u)
        if n > budget:
            if cur:
                chunks.append("\n\n".join(cur))
                cur, cur_tokens = [], 0
            chunks.append(u)
            continue
        if cur and cur_tokens + n > budget:
            chunks.append("\n\n".join(cur))
            cur, cur_tokens = [], 0
        cur.append(u)
        cur_tokens += n
    if cur:
        chunks.append("\n\n".join(cur))
    return chunks


def _merge_small(chunks: list[str], counter: TokenCounter, min_tokens: int) -> list[str]:
    """E2：小 chunk 与后邻合并；末尾小 chunk 无后邻则并入前一个。"""
    merged: list[str] = []
    i = 0
    while i < len(chunks):
        c = chunks[i]
        if counter.count(c) < min_tokens and i + 1 < len(chunks):
            merged.append(c + "\n\n" + chunks[i + 1])
            i += 2
        else:
            merged.append(c)
            i += 1
    if len(merged) > 1 and counter.count(merged[-1]) < min_tokens:
        merged[-2] = merged[-2] + "\n\n" + merged[-1]
        merged.pop()
    return merged


def chunk_markdown(
    md: str,
    counter: TokenCounter,
    max_tokens: int = MAX_CHUNK_TOKENS,
    min_tokens: int = MIN_CHUNK_TOKENS,
) -> list[str]:
    """入口：markdown → 有序 content chunk 列表（前缀由调用方注入）。"""
    chunks: list[str] = []
    for section in split_sections(parse_blocks(md)):
        text = "\n\n".join(b.text for b in section)
        if counter.count(text) <= max_tokens:
            chunks.append(text)
        else:
            chunks.extend(_pack(_to_units(section, counter, max_tokens), counter, max_tokens))
    return [c for c in _merge_small(chunks, counter, min_tokens) if c.strip()]


def truncate_middle(text: str, counter: TokenCounter, hard_limit: int = HARD_TOKEN_LIMIT) -> str:
    """E1 保险丝：超模型上限时截中段、保留头尾。调用方负责记日志（契约 §1d E1）。

    实测语料最大原子单元 ~2k tokens，正常不会触发；触发即说明数据异常。
    """
    if counter.count(text) <= hard_limit:
        return text
    half = hard_limit // 2
    lines = text.split("\n")
    head: list[str] = []
    for line in lines:
        if counter.count("\n".join(head + [line])) >= half:
            break
        head.append(line)
    tail: list[str] = []
    for line in reversed(lines):
        if counter.count("\n".join([line] + tail)) >= half:
            break
        tail.insert(0, line)
    return "\n".join(head) + "\n…[middle truncated]…\n" + "\n".join(tail)
