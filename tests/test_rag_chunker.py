"""RAG 管线首测（human-node: rag-first-test — <一句话>）。

断言映射契约：Q1a 结构切分 · 1c 图片锚点 · 1d E1/E2/E3/E5。
写法约定：一条规则一个 test；断言行为（输出长什么样），不断言实现。
"""

import re

from app.ops.rag.chunker import chunk_markdown, truncate_middle
from app.ops.rag.clean import clean_markdown
from app.ops.rag.prefix import build_prefix, embed_text, strip_doc_context_prefix
from app.ops.rag.tokenizer import FuncTokenCounter

# 假计数器：按词数计，确定、可读、够用（真 tokenizer 的口径差异不影响规则正确性）
counter = FuncTokenCounter(lambda t: max(1, len(t.split())))

FIXTURE = """
### What issue are you seeing?

Auto compaction is cancelled at commit time.
<img width="431" alt="Image" src="https://user-attachments/abc.png"/>

| compaction | outcome |
|---|---|
| auto | cancel |

### Root cause

In fullCompactionService.ts the guard discards the result.

```js
if (!historySafeToCompact(current, original)) { cancel(); }
```

"""


def test_sections_become_chunks():
    """
    结构切分：两个小 section 应各自成块
    """
    cleaned = clean_markdown(FIXTURE)
    chunks = chunk_markdown(cleaned.text, counter, max_tokens=10, min_tokens=2)
    # print(cleaned.text)
    for idx, chunk in enumerate(chunks):
        print(f"\n==========\nchunk {idx+1}:\n", chunk)
    assert len(chunks) == 5
    assert chunks[0].startswith("###")
    assert "### Root cause" in chunks[3]
    assert "```js" in chunks[4]
    assert all(len(c.strip()) > 0 for c in chunks)

def test_code_fence_is_atomic():
    """
    代码块应整体切分，不要切断
    """
    big_fence = "```js\n" + "\n".join(f"line {i}" for i in range(100)) + "\n```"
    cleaned = clean_markdown(big_fence)
    chunks = chunk_markdown(cleaned.text, counter, max_tokens=20)
    assert len(chunks) == 1
    assert chunks[0].startswith("```js")
    assert chunks[0].endswith("```")

def test_table_split_repeats_header():
    """
    超限表格按行切、每片重复表头
    """
    table = "| a | b |\n|---|---|\n" + "\n".join(f"| {i + 1} | {i + 2} |" for i in range(100))
    print(table)
    chunks = chunk_markdown(table, counter, max_tokens=20, min_tokens=1)
    for idx, chunk in enumerate(chunks):
        print(f"\n==========\nchunk {idx+1}:\n", chunk)
    assert len(chunks) == 50
    assert all(chunk.startswith("| a | b |") for chunk in chunks)
    data_rows = [r for c in chunks for r in c.split("\n") if re.match(r"^\| \d+ \| \d+ \|$", r)]
    assert len(data_rows) == 100
    assert len(set(data_rows)) == 100


# ---- 以下 5 条为 AI 起草（2026-08-09），待人逐条对契约审断言 ----


def test_image_anchor_and_fence_protection():
    """§1c + E3：图片锚点化 + metadata 有序记录；fence 内 HTML 不清洗"""
    md = '<img alt="架构图" src="https://x/1.png"/>\n\n```\n<img src="https://x/2.png"/>\n```'
    r = clean_markdown(md)
    assert "[IMAGE#1: 架构图]" in r.text  # 有意义 alt 进文本
    assert 'src="https://x/2.png"' in r.text  # fence 内保持原样
    assert r.media == [
        {"anchor": "[IMAGE#1]", "url": "https://x/1.png", "alt": "架构图", "kind": "image"}
    ]


def test_meaningless_alt_stays_out_of_text():
    """§1c：无信息 alt（"Image"）不进向量文本；alt 仍存 metadata（未来多模态用）"""
    r = clean_markdown('<img alt="Image" src="https://x/1.png"/>')
    assert r.text.strip() == "[IMAGE#1]"
    assert r.media[0]["alt"] == "Image"


def test_html_noise_and_video():
    """E3：HTML 注释剥除；details 展开、summary 作伪标题；裸视频链接锚点化"""
    md = (
        "<!-- hidden -->\n"
        "<details><summary>详情</summary>\n内容\n</details>\n"
        "https://github.com/user-attachments/files/1/a.mp4"
    )
    r = clean_markdown(md)
    assert "hidden" not in r.text
    assert "**详情**" in r.text and "内容" in r.text
    assert "[VIDEO#1]" in r.text
    assert r.media[0] == {
        "anchor": "[VIDEO#1]",
        "url": "https://github.com/user-attachments/files/1/a.mp4",
        "alt": "",
        "kind": "video",
    }


def test_prefix_roundtrip():
    """§1b：前缀四行格式 + 展示剥离往返；无 module_tag 不写 Module 行（有才写）"""
    p = build_prefix(
        title="标题", source_type="issue",
        ref="MoonshotAI/kimi-code#2720", module_tag="agent-core",
    )
    lines = p.splitlines()
    assert lines[0] == "[Document Context]"
    assert "Title: 标题" in lines
    assert "Type: issue" in lines
    assert "Ref: MoonshotAI/kimi-code#2720" in lines
    assert "Module: agent-core" in lines
    assert strip_doc_context_prefix(embed_text(p, "正文")) == "正文"

    p_doc = build_prefix(title="t", source_type="doc", ref="docs/05-plan/04.md")
    assert "Module:" not in p_doc


def test_truncate_middle_fuse():
    """E1 保险丝：超硬顶截中段、保留头尾、总长受控；未超则原样返回"""
    big = "\n".join(f"line {i}" for i in range(500))  # 1000 词
    t = truncate_middle(big, counter, hard_limit=100)
    assert "[middle truncated]" in t
    assert t.startswith("line 0")
    assert t.rstrip().endswith("line 499")
    assert counter.count(t) <= 100

    small = "short text"
    assert truncate_middle(small, counter, hard_limit=100) == small
