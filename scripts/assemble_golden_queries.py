#!/usr/bin/env python3
"""组装金样查询集 yaml（task golden-query-set-v1）。

输入：三方 chat 回收的筛选文本（按 —— NN —— 分节）+ 生成包的 P##→issue 映射。
输出：evals/golden/queries_v1.yaml（G01–G05 契约迁入 + G06+ 新增）。

用法：.venv/bin/python scripts/assemble_golden_queries.py <筛选文本路径>
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

# 生成包 P## → issue 映射（evals/golden/query_gen_pack_v1.md）
P_TO_ISSUE = {
    1: "43", 2: "705", 3: "1138", 4: "1566", 5: "1924", 6: "2157", 7: "2358",
    8: "2548", 9: "87", 10: "1885",
    11: "173", 12: "325", 13: "525", 14: "981", 15: "1356", 16: "1909",
    17: "2111", 18: "2380", 19: "87", 20: "1885",
    21: "225", 22: "800", 23: "1219", 24: "1685", 25: "1943", 26: "2163",
    27: "2370", 28: "2549",
}


def quadrant_of(p: int) -> str:
    if p <= 10:
        return "zh2en"
    if p <= 20:
        return "zh2zh"
    return "en2en"


# P01–P03 回收于对话（不在附件里），手工补录
P01_03 = [
    (1, "这个页脚用量指示器默认是开启的吗？还是需要我手动在配置文件里设个开关才能显示？", "配置"),
    (1, "正文里提到 auto-refresh 每 60 秒更新一次，又说 on turn completion 也能触发刷新，这两个机制是同时生效还是互斥的？实际刷新逻辑到底是轮询还是事件驱动？", "机制"),
    (2, "报错里说 tool_call_id Read:158 没有对应的 tool response，但我看日志里 Read 工具明明是执行完了的，这到底是怎么弄丢的？是并发写 state 的时候 race 了吗？", "原因"),
    (2, "我看到 Related PR 里有个 cleanupOrphanedToolCalls() 函数，这个修复是默认就会生效，还是需要我在配置里手动开启某个开关才能用？", "配置"),
    (3, "MCP 服务器发过来 notifications/tools/list_changed 之后，为什么 McpConnectionManager 还是只认旧的工具列表？是不是 listChanged.tools.onChanged 这个事件根本没有被接进现有的 MCP client 封装里？", "机制"),
    (3, "看 Related 里提到 #383 的 reload 命令可以手动刷新，那这个修复跟手动 reload 比，实际用起来有什么本质区别？是不是修完之后就不用再手动敲 reload 了？", "对比"),
]

SECTION_RE = re.compile(r"^[—\-\s]*(\d{1,2})[—\-\s|]*$", re.MULTILINE)
QUERY_RE = re.compile(r'query:\s*"(.+?)"\s*$', re.MULTILINE)
ANGLE_RE = re.compile(r"angle:\s*([一-龥\w]+)")


def parse_sections(text: str) -> list[tuple[int, str, str]]:
    """按分节标记切分，返回 (P编号, query, angle) 列表。"""
    marks = list(SECTION_RE.finditer(text))
    out: list[tuple[int, str, str]] = []
    for i, m in enumerate(marks):
        p = int(m.group(1))
        seg = text[m.end(): marks[i + 1].start() if i + 1 < len(marks) else len(text)]
        queries = QUERY_RE.findall(seg)
        angles = ANGLE_RE.findall(seg)
        for j, q in enumerate(queries):
            angle = angles[j] if j < len(angles) else ""
            out.append((p, q, angle))
    return out


def yaml_entry(gid: str, query: str, source_id: str, quadrant: str, angle: str) -> str:
    # 防 yaml 转义坑：先处理回收文本里的 \" 残留，再统一双引号→单引号
    query = query.replace('\\"', "'").replace('"', "'").replace("\\'", "'")
    return f"""  - id: {gid}
    query: "{query}"
    quadrant: {quadrant}
    expect_hit: {{ source_type: issue, source_id: "{source_id}" }}
    assert: {{ recall_at: 5, min_relevance: relevant, citation_in_hits: true }}
    expect_relevance: exact  # 预填 · 人校准（部分覆盖改 relevant）
    note: "angle={angle} · 三方生成人筛"
"""


HEADER = """# 金样查询集 v1（task golden-query-set-v1）
# 断言锚格式：source_id#chunk_index；评测卫生：runner 断言前过滤含金样原文的文档
# expect_relevance 为预填值，需人校准一遍（部分覆盖的降为 relevant）
# 负样本（negative 象限）待人手写后追加
golden:
"""


def main() -> None:
    text = Path(sys.argv[1]).read_text(encoding="utf-8")
    entries = parse_sections(text) + P01_03
    seen: set[tuple[int, str]] = set()
    lines = [HEADER]
    gid = 6
    for p, query, angle in entries:
        if (p, query) in seen or p not in P_TO_ISSUE:
            continue
        seen.add((p, query))
        lines.append(yaml_entry(f"G{gid:02d}", query, P_TO_ISSUE[p], quadrant_of(p), angle))
        gid += 1
    out = Path("evals/golden/queries_v1.yaml")
    out.write_text("\n".join(lines), encoding="utf-8")
    print(f"写出 {out} · 新增 {gid - 6} 条（G06–G{gid - 1:02d}）")


if __name__ == "__main__":
    main()
