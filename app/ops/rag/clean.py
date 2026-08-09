"""RAG 入库清洗：HTML 噪声剥离 + 图片/视频锚点化。

契约锚点：ops-desk-workspace/docs/contracts/rag-knowledge-contract-v1.md
- §1c 图片位置锚点（[IMAGE#n]，URL 有序入 metadata，alt 有意义时进文本）
- §1d E3：<img>/<video>/user-attachments 锚点化；剥 HTML 注释；
  <details> 保留内容、<summary> 作伪标题

关键约束：代码 fence 内**不做**任何替换（fence 感知分段，避免把代码里的
示例 HTML 改成锚点）。
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

_FENCE_LINE_RE = re.compile(r"^\s*(```|~~~)")
_HTML_COMMENT_RE = re.compile(r"<!--.*?-->", re.DOTALL)
_DETAILS_OPEN_RE = re.compile(r"<details[^>]*>", re.IGNORECASE)
_DETAILS_CLOSE_RE = re.compile(r"</details\s*>", re.IGNORECASE)
_SUMMARY_RE = re.compile(r"<summary[^>]*>(.*?)</summary\s*>", re.IGNORECASE | re.DOTALL)
_IMG_TAG_RE = re.compile(r"<img\b[^>]*>", re.IGNORECASE)
_VIDEO_TAG_RE = re.compile(r"<video\b[^>]*>(?:.*?</video\s*>)?", re.IGNORECASE | re.DOTALL)
_MD_IMAGE_RE = re.compile(r"!\[([^\]]*)\]\((https?://[^)\s]+)[^)]*\)")
_BARE_VIDEO_URL_RE = re.compile(
    r"(?<![\w(/])((?:https?://\S*user-attachments/\S+?\.(?:mp4|mov|webm)))(?![\w)])",
    re.IGNORECASE,
)
_SRC_ATTR_RE = re.compile(r'src\s*=\s*"([^"]+)"', re.IGNORECASE)
_ALT_ATTR_RE = re.compile(r'alt\s*=\s*"([^"]*)"', re.IGNORECASE)

# 契约 §1c：alt 为 "Image"/空 等无信息值时不进向量文本
_MEANINGLESS_ALTS = {"", "image", "img", "picture", "screenshot"}


@dataclass
class CleanResult:
    text: str
    media: list[dict] = field(default_factory=list)
    # media 条目: {"anchor": "[IMAGE#1]", "url": ..., "alt": ..., "kind": "image"|"video"}


def _fence_segments(text: str) -> list[tuple[bool, str]]:
    """按 fence 边界切成 (is_fence, segment) 序列，换行符保留在段内。"""
    segments: list[tuple[bool, str]] = []
    buf: list[str] = []
    in_fence = False

    def flush() -> None:
        if buf:
            segments.append((in_fence, "".join(buf)))
            buf.clear()

    for line in text.splitlines(keepends=True):
        if _FENCE_LINE_RE.match(line):
            flush()
            in_fence = not in_fence
        buf.append(line)
    if buf:
        # 未闭合 fence 的容错：末段按 fence 处理（不清洗），宁可不洗也不错洗代码
        segments.append((in_fence, "".join(buf)))
    return segments


def _anchor(kind: str, url: str, alt: str, media: list[dict], counters: dict[str, int]) -> str:
    counters[kind] += 1
    label = "IMAGE" if kind == "image" else "VIDEO"
    plain = f"[{label}#{counters[kind]}]"
    media.append({"anchor": plain, "url": url, "alt": alt, "kind": kind})
    if alt.strip().lower() in _MEANINGLESS_ALTS:
        return plain
    return f"[{label}#{counters[kind]}: {alt.strip()}]"

def _clean_segment_in_fence(seg: str, counters: dict[str, int]) -> tuple[str, list[dict]]:
    media: list[dict] = []
    seg = _HTML_COMMENT_RE.sub("", seg)
    seg = _SUMMARY_RE.sub(lambda m: f"\n**{m.group(1).strip()}**\n", seg)
    seg = _DETAILS_OPEN_RE.sub("", seg)
    seg = _DETAILS_CLOSE_RE.sub("", seg)

    def img_sub(m: re.Match) -> str:
        tag = m.group(0)
        src = _SRC_ATTR_RE.search(tag)
        alt = _ALT_ATTR_RE.search(tag)
        if not src:
            return ""
        return _anchor("image", src.group(1), alt.group(1) if alt else "", media, counters)

    def video_sub(m: re.Match) -> str:
        tag = m.group(0)
        src = _SRC_ATTR_RE.search(tag)
        if not src:
            return ""
        return _anchor("video", src.group(1), "", media, counters)

    seg = _IMG_TAG_RE.sub(img_sub, seg)
    seg = _VIDEO_TAG_RE.sub(video_sub, seg)
    seg = _MD_IMAGE_RE.sub(
        lambda m: _anchor("image", m.group(2), m.group(1), media, counters), seg
    )
    seg = _BARE_VIDEO_URL_RE.sub(
        lambda m: _anchor("video", m.group(1), "", media, counters), seg
    )
    return seg, media


def clean_markdown(body: str) -> CleanResult:
    """清洗入库正文：返回锚点化文本 + 有序 media 列表（契约 §1c metadata.images）。"""
    all_media: list[dict] = []
    all_counters: dict[str, int] = {"image": 0, "video": 0}
    parts: list[str] = []
    for is_fence, seg in _fence_segments(body):
        if is_fence:
            parts.append(seg)
        else:
            seg, media = _clean_segment_in_fence(seg, all_counters)
            all_media.extend(media)
            parts.append(seg)

    return CleanResult(text="".join(parts), media=all_media)
