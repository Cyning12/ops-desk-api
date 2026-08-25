#!/usr/bin/env python3
"""Post-compile Mermaid 归一化：把 harness emit 改成 IDE 可预览形态。

背景：
  @cyning/harness / 旧 generateMermaid 默认产出：
    - 锚点注释 `// → …`（Mermaid 只认 `%%`）
    - 边 `--"label"-->`（IDE 常见预览易丢边）
    - 特殊字符节点标签未加引号
  本脚本在 `graph yaml compile` 之后改写同目录 `*.md` 的 mermaid 围栏，
  不改 `.graph.yaml` 拓扑真值。

官方依据（修 emit / 归一化时对照，勿凭记忆）：
  - https://mermaid.js.org/intro/syntax-reference.html  （注释 %%）
  - https://mermaid.js.org/syntax/flowchart.html       （边上文字 A-->|text|B）
  - 本地可对照：Projects/mermaid/packages/mermaid/src/docs/syntax/flowchart.md

治根仍在 dsh-coding-kit DEF-023；本脚本是消费者仓过渡方案，迁移 kit 后可对照反哺。
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None  # type: ignore

# 节点标签含这些字符时强制 Id["label"]
_SPECIAL = re.compile(r"""[\s()\[\]{}|>+/\\#`'"]""")

_EDGE_QUOTED = re.compile(
    r'^(\s*)([A-Za-z_][\w]*)\s+--"((?:\\.|[^"\\])*)"-->\s*([A-Za-z_][\w]*)\s*$'
)
_NODE_DECL = re.compile(
    r'^(\s*)([A-Za-z_][\w]*)(\[\[|\[\(|\[|\{|\(\()(.*)$'
)
_COMMENT_SLASH = re.compile(r'^(\s*)//(\s*→|\s*->|\s+)')
_FENCE_START = re.compile(r'^```mermaid\s*$')
_FENCE_END = re.compile(r'^```\s*$')


def _escape_label(label: str) -> str:
    return label.replace("\\", "\\\\").replace('"', '\\"')


def _quote_node_shape(shape_open: str, rest: str) -> str | None:
    """把 `[label]` / `[[label]]` 等改为带引号；无法识别则返回 None。"""
    rest = rest.rstrip()
    if shape_open == "[[":
        if rest.endswith("]]"):
            inner = rest[:-2]
            if inner.startswith('"') and inner.endswith('"'):
                return f"[[{inner}]]"
            return f'[["{_escape_label(inner)}"]]'
        return None
    if shape_open == "[(":
        if rest.endswith(")]"):
            inner = rest[:-2]
            if inner.startswith('"') and inner.endswith('"'):
                return f"[({inner})]"
            return f'[("{_escape_label(inner)}")]'
        return None
    if shape_open == "[":
        if rest.endswith("]"):
            inner = rest[:-1]
            if inner.startswith('"') and inner.endswith('"'):
                return f"[{inner}]"
            if _SPECIAL.search(inner) or inner.startswith(">"):
                return f'["{_escape_label(inner)}"]'
            return f"[{inner}]"
        return None
    if shape_open == "{":
        if rest.endswith("}"):
            inner = rest[:-1]
            if inner.startswith('"') and inner.endswith('"'):
                return f"{{{inner}}}"
            if _SPECIAL.search(inner):
                return f'{{"{_escape_label(inner)}"}}'
            return f"{{{inner}}}"
        return None
    return None


def normalize_mermaid_body(body: str) -> str:
    out: list[str] = []
    for line in body.splitlines():
        m_c = _COMMENT_SLASH.match(line)
        if m_c:
            out.append(f"{m_c.group(1)}%%{m_c.group(2)}{line[m_c.end():]}")
            continue

        m_e = _EDGE_QUOTED.match(line)
        if m_e:
            indent, src, label, dst = m_e.groups()
            out.append(f'{indent}{src} -->|"{_escape_label(label)}"| {dst}')
            continue

        m_n = _NODE_DECL.match(line)
        if m_n and "-->" not in line and "--" not in line.split("[", 1)[0]:
            indent, nid, shape_open, rest = m_n.groups()
            # 跳过 classDef / class 行
            if nid in ("classDef", "class", "style", "linkStyle", "click"):
                out.append(line)
                continue
            quoted = _quote_node_shape(shape_open, rest)
            if quoted is not None:
                out.append(f"{indent}{nid}{quoted}")
                continue

        out.append(line)
    return "\n".join(out)


def _load_kind_map(yaml_path: Path) -> dict[str, str]:
    if yaml is None or not yaml_path.is_file():
        return {}
    with yaml_path.open(encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    return {
        str(n["id"]): str(n.get("kind") or "")
        for n in data.get("nodes") or []
        if n.get("id")
    }


def _load_label_map(yaml_path: Path) -> dict[str, str]:
    if yaml is None or not yaml_path.is_file():
        return {}
    with yaml_path.open(encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    return {
        str(n["id"]): str(n.get("label") or "")
        for n in data.get("nodes") or []
        if n.get("id")
    }


def _class_lines(kind_map: dict[str, str], label_map: dict[str, str] | None = None) -> list[str]:
    """按 kind / 文档指针标签补 class 赋值。"""
    label_map = label_map or {}
    phase: list[str] = []
    doc: list[str] = []
    infra: list[str] = []
    for nid, kind in kind_map.items():
        k = kind.lower()
        label = label_map.get(nid, "")
        if label.startswith(">") or "doc" in nid.lower() or nid.lower().endswith("_md"):
            doc.append(nid)
            continue
        if k in ("flow", "struct"):
            phase.append(nid)
        elif k == "external":
            low = nid.lower()
            if any(x in low for x in ("db", "llm", "rag", "pg", "postgres", "qdrant")):
                infra.append(nid)
            else:
                phase.append(nid)
        else:
            phase.append(nid)

    lines: list[str] = []
    if phase:
        lines.append(f"    class {','.join(phase)} phase")
    if doc:
        lines.append(f"    class {','.join(doc)} doc")
    if infra:
        lines.append(f"    class {','.join(infra)} infra")
    return lines


def _ensure_class_assignments(
    body: str,
    kind_map: dict[str, str],
    label_map: dict[str, str] | None = None,
) -> str:
    if not kind_map:
        return body
    if "classDef phase" not in body:
        return body
    extra = _class_lines(kind_map, label_map)
    if not extra:
        return body
    # 去掉旧 class 赋值行后重写（保留 classDef）
    lines = [ln for ln in body.splitlines() if not re.match(r"^\s*class\s+\w", ln)]
    insert_at = None
    for i, line in enumerate(lines):
        if line.strip().startswith("classDef "):
            insert_at = i + 1
    if insert_at is None:
        return body
    while insert_at < len(lines) and lines[insert_at].strip() == "":
        insert_at += 1
    new_lines = lines[:insert_at] + [""] + extra + lines[insert_at:]
    return "\n".join(new_lines)


def normalize_md_file(md_path: Path) -> bool:
    """归一化单个 md。返回是否有改动。"""
    text = md_path.read_text(encoding="utf-8")
    lines = text.splitlines(keepends=True)
    yaml_path = md_path.parent / (md_path.name.replace(".md", ".graph.yaml"))
    kind_map = _load_kind_map(yaml_path)
    label_map = _load_label_map(yaml_path)

    out: list[str] = []
    i = 0
    changed = False
    while i < len(lines):
        line = lines[i]
        if _FENCE_START.match(line.rstrip("\n")):
            out.append(line)
            i += 1
            block_lines: list[str] = []
            while i < len(lines) and not _FENCE_END.match(lines[i].rstrip("\n")):
                block_lines.append(lines[i])
                i += 1
            body_core = "\n".join(l.rstrip("\r\n") for l in block_lines)
            normalized = normalize_mermaid_body(body_core)
            normalized = _ensure_class_assignments(normalized, kind_map, label_map)
            if normalized != body_core:
                changed = True
            out.append(normalized + "\n")
            if i < len(lines):
                out.append(lines[i])  # closing fence
                i += 1
            continue
        out.append(line)
        i += 1

    new_text = "".join(out)
    if new_text != text:
        changed = True
        md_path.write_text(new_text, encoding="utf-8")
    return changed


def verify_md(md_path: Path) -> list[str]:
    """返回问题列表；空=通过。"""
    issues: list[str] = []
    text = md_path.read_text(encoding="utf-8")
    in_fence = False
    for ln, line in enumerate(text.splitlines(), 1):
        if _FENCE_START.match(line):
            in_fence = True
            continue
        if in_fence and _FENCE_END.match(line):
            in_fence = False
            continue
        if not in_fence:
            continue
        if re.match(r"^\s*//", line):
            issues.append(f"{md_path}:{ln}: slash comment in mermaid")
        if re.search(r'\w\s+--"', line) and "-->" in line:
            issues.append(f"{md_path}:{ln}: legacy quoted edge --\"…\"-->")
    return issues


def iter_graph_mds(graph_dir: Path) -> list[Path]:
    mds: list[Path] = []
    for yml in sorted(graph_dir.rglob("*.graph.yaml")):
        md = yml.with_name(yml.name.replace(".graph.yaml", ".md"))
        if md.is_file():
            mds.append(md)
    return mds


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "graph_dir",
        nargs="?",
        default="docs/_tech_graph",
        help="tech graph 根目录（默认 docs/_tech_graph）",
    )
    p.add_argument(
        "--check",
        action="store_true",
        help="只检查，不写入（有问题 exit 1）",
    )
    args = p.parse_args(argv)
    root = Path(args.graph_dir)
    if not root.is_dir():
        print(f"error: not a directory: {root}", file=sys.stderr)
        return 2

    mds = iter_graph_mds(root)
    if not mds:
        print(f"error: no *.graph.yaml→*.md pairs under {root}", file=sys.stderr)
        return 2

    if args.check:
        all_issues: list[str] = []
        for md in mds:
            all_issues.extend(verify_md(md))
        if all_issues:
            print("mermaid normalize check FAILED:")
            for x in all_issues:
                print(f"  {x}")
            return 1
        print(f"[ok] mermaid normalize check: {len(mds)} md file(s)")
        return 0

    n_changed = 0
    for md in mds:
        if normalize_md_file(md):
            n_changed += 1
            print(f"  normalized {md}")
    # 写后再验
    all_issues = []
    for md in mds:
        all_issues.extend(verify_md(md))
    if all_issues:
        print("mermaid normalize verify FAILED after write:", file=sys.stderr)
        for x in all_issues:
            print(f"  {x}", file=sys.stderr)
        return 1
    print(f"[ok] mermaid normalize: {n_changed}/{len(mds)} file(s) changed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
