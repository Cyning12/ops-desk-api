#!/usr/bin/env python3
"""金样查询集 · 三方生成 Prompt 包制作（task golden-query-set-v1）。

三方 chat 是网页版（无 DB 权限）：本脚本把 issue 内容嵌进 prompt，
每节整体复制粘贴即可，回收纯 YAML 后人筛选标注。

用法：.venv/bin/python scripts/make_query_gen_pack.py [输出路径] [--url]
      --url 模式：prompt 内嵌 GitHub API 链接而非全文（要求三方 chat 能抓链接）
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import psycopg

DB_DSN = "host=localhost port=5432 dbname=opsdesk user=ops password=ops_password"
BODY_LIMIT = 2200  # 贴给网页 chat 的正文截断（控制单次上下文）

_TPL_ZH = """你是企业研发协作工具的用户。阅读下面的 GitHub issue，生成 2 个中文问题。
要求：
- 模拟真实用户：遇到现象问原因 / 想调配置问安全值 / 关心成本问开销 / 对比行为差异 / 问内部机制
- 不复述标题；口语化但保留关键技术词（函数名、配置项）
- 答案必须能在正文中找到（至少部分覆盖）
- 只输出 YAML，不要任何解释：
- query: "……"
  angle: 原因|配置|成本|对比|机制

issue #{number}：
标题：{title}
正文：
{body}"""

_TPL_EN = """You are a user of an engineering-collaboration tool. Read the GitHub issue below and write 2 questions in English.
Rules:
- Real user voice: root cause / safe config value / cost / behavior difference / internals
- Do not restate the title; keep key technical terms (function names, config keys)
- The answer must be findable in the body (at least partially)
- Output YAML only, no explanation:
- query: "……"
  angle: cause|config|cost|comparison|mechanism

issue #{number}:
Title: {title}
Body:
{body}"""

_URL_HINT_ZH = "请联网阅读这个 GitHub issue（JSON 格式，body 字段为正文）：\n{url}"
_URL_HINT_EN = "Read this GitHub issue via web (JSON; the body field is the content):\n{url}"


def cjk_ratio(body: str) -> float:
    if not body:
        return 0.0
    stripped = re.sub(r"[一-龥]", "", body)
    return (len(body) - len(stripped)) / len(body)


def spread(xs: list, n: int) -> list:
    """等距抽样（确定性，可复跑）。"""
    if len(xs) <= n:
        return xs
    step = len(xs) / n
    return [xs[int(i * step)] for i in range(n)]


def main() -> None:
    url_mode = "--url" in sys.argv
    out_path = (
        Path(sys.argv[1])
        if len(sys.argv) > 1 and not sys.argv[1].startswith("--")
        else Path("evals/golden/query_gen_pack_v1_urls.md" if url_mode else "evals/golden/query_gen_pack_v1.md")
    )
    with psycopg.connect(DB_DSN) as conn:
        rows = conn.execute(
            "SELECT i.number, i.title, i.body, r.full_name FROM ops_issues i "
            "JOIN ops_repos r ON r.id = i.repo_id "
            "WHERE i.body IS NOT NULL AND length(i.body) > 1500 ORDER BY i.number"
        ).fetchall()

    pure_en, mixed, mostly_zh = [], [], []
    for number, title, body, repo in rows:
        r = cjk_ratio(body)
        if r == 0:
            pure_en.append((number, title, body, repo))
        elif r > 0.1:
            mostly_zh.append((number, title, body, repo))
        else:
            mixed.append((number, title, body, repo))

    samples = [
        ("ZH问→EN文档", _TPL_ZH, spread(pure_en, 8) + spread(mixed, 2)),
        ("ZH问→ZH/混合文档", _TPL_ZH, spread(mostly_zh, 8) + spread(mixed, 2)),
        ("EN问→EN文档", _TPL_EN, spread(pure_en[8:], 8) or spread(pure_en, 8)),
    ]

    lines = [
        "# 金样 query 生成 Prompt 包（task golden-query-set-v1）",
        "",
        "用法：每节整体复制贴入网页版三方 chat → 回收 YAML → 人筛选 + 标注 expect_hit。",
        f"模式：{'URL 链接（需三方能联网抓取）' if url_mode else '全文嵌入'}。",
        "负样本不进本包（人写，防泄漏进语料）。",
    ]
    idx = 0
    for quadrant, tpl, issues in samples:
        lines.append(f"\n---\n\n## 象限：{quadrant}\n")
        for number, title, body, repo in issues:
            idx += 1
            if url_mode:
                url = f"https://api.github.com/repos/{repo}/issues/{number}"
                hint = _URL_HINT_ZH if tpl is _TPL_ZH else _URL_HINT_EN
                prompt = tpl.format(number=number, title=title, body=hint.format(url=url))
            else:
                prompt = tpl.format(number=number, title=title, body=body[:BODY_LIMIT])
            lines.append(f"### P{idx:02d} · issue #{number}\n\n```text\n{prompt}\n```\n")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"写出 {out_path} · {idx} 条 prompt（EN 池 {len(pure_en)} / 混合 {len(mixed)} / 中文 {len(mostly_zh)}）")


if __name__ == "__main__":
    main()
