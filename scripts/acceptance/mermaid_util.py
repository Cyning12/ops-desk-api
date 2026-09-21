"""把 mermaid 源码整成**到处都能渲染**的形态 + 落一份自渲染 HTML。

## 为什么要这个

LangGraph 原生 `draw_mermaid()` 的输出在 Cursor / GitHub 能渲染，但**在 WorkBuddy 的
Markdown 预览里渲染不出来**。实测原因有三处不兼容：

1. **YAML front matter**（`--- config: ... ---`）：很多渲染器不认，直接整段当文本。
2. **`<p>` 包裹的标签**（`__start__([<p>__start__</p>])`）：部分渲染器会报语法错。
3. **`&nbsp;` 实体**（`critic -. &nbsp;end&nbsp; .-> __end__`）：同上，且边标签里带实体很难看。

所以：先**归一化**成保守语法，再额外落一份 HTML —— HTML 用 mermaid ESM 自己渲染，
不依赖宿主预览器是否支持 mermaid（CDN 拿不到时降级为 `<pre>` 显示源码，不会白屏）。
"""

from __future__ import annotations

import html as _html
import pathlib
import re

#: mermaid 里不能出现的裸字符（图内会当语法用）
_SAFE_LABEL = re.compile(r'[<>"|{}]')


def _strip_front_matter(src: str) -> str:
    """去掉开头的 `--- ... ---` YAML 块（渲染器不认它，留着整张图就废了）。"""
    lines = src.splitlines()
    if lines and lines[0].strip() == "---":
        for i in range(1, len(lines)):
            if lines[i].strip() == "---":
                return "\n".join(lines[i + 1 :]).lstrip("\n")
    return src


def normalize(src: str) -> str:
    """归一化成保守 mermaid：无 front matter、无 `<p>`、无 `&nbsp;`。"""
    out = _strip_front_matter(src)
    out = out.replace("<p>", "").replace("</p>", "")
    out = out.replace("&nbsp;", " ")
    # 连续空格在边标签里难看，压掉（不碰缩进）
    out = re.sub(r"[ \t]{2,}", " ", out)
    return out.strip() + "\n"


def to_html(title: str, *sources: tuple[str, str], note: str = "") -> str:
    """把若干 (小节标题, mermaid 源) 合成一个**自渲染** HTML。

    用 CDN 的 mermaid ESM；拿不到 CDN 时 mermaid 不会渲染，但源码在 `<pre>` 里仍可读
    （所以正文同时留了源码，不让它变成空白页）。
    """
    blocks = []
    for heading, src in sources:
        if not src or not src.strip():
            continue
        blocks.append(
            f"<h2>{_html.escape(heading)}</h2>\n"
            f'<div class="mermaid">{_html.escape(normalize(src))}</div>\n'
            f"<details><summary>mermaid 源码</summary>"
            f"<pre>{_html.escape(normalize(src))}</pre></details>\n"
        )
    body = "\n".join(blocks)
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<title>{_html.escape(title)}</title>
<style>
  body {{ font-family: -apple-system, "PingFang SC", "Microsoft YaHei", sans-serif;
         margin: 24px; color: #1f2937; background: #ffffff; }}
  h1 {{ font-size: 18px; }} h2 {{ font-size: 15px; margin-top: 28px; }}
  .note {{ color: #6b7280; font-size: 13px; }}
  .mermaid {{ background: #f8fafc; border: 1px solid #e5e7eb; border-radius: 8px;
             padding: 12px; overflow: auto; }}
  pre {{ background: #f3f4f6; padding: 10px; border-radius: 6px; overflow: auto;
        font-size: 12px; }}
  details {{ margin-top: 8px; font-size: 13px; }}
</style>
</head>
<body>
<h1>{_html.escape(title)}</h1>
{f'<p class="note">{_html.escape(note)}</p>' if note else ''}
{body}
<script type="module">
  try {{
    const m = await import("https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.esm.min.mjs");
    m.default.initialize({{ startOnLoad: true, theme: "neutral" }});
    await m.default.run({{ querySelector: ".mermaid" }});
  }} catch (e) {{
    for (const el of document.querySelectorAll(".mermaid")) {{
      el.insertAdjacentHTML("afterend",
        '<p class="note">mermaid CDN 不可用，请看下方源码（或复制到 mermaid.live）。</p>');
    }}
  }}
</script>
</body>
</html>
"""


def write_all(
    out_dir: pathlib.Path,
    stem: str,
    *,
    title: str,
    sections: list[tuple[str, str]],
    note: str = "",
) -> tuple[pathlib.Path, pathlib.Path]:
    """落 `.mmd`（归一化源码）+ `.html`（自渲染）。返回两个路径。"""
    out_dir.mkdir(parents=True, exist_ok=True)
    merged = "\n\n".join(f"%% {h}\n{normalize(s)}" for h, s in sections if s and s.strip())
    mmd = out_dir / f"{stem}.mmd"
    mmd.write_text(merged)
    html_path = out_dir / f"{stem}.html"
    html_path.write_text(to_html(title, *sections, note=note))
    return mmd, html_path
