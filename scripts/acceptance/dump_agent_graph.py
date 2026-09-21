"""把三张图的**静态拓扑**导成 mermaid 落盘（不调 LLM、秒出）。

用途：看"这张图到底有哪些节点、边怎么连"。要**这一次实际跑了哪些节点**的图，
看 `agent_nl_smoke.py --mermaid-out`（它按真实帧序画运行链）。

    ./.venv/bin/python scripts/acceptance/dump_agent_graph.py                # 三张图都导
    ./.venv/bin/python scripts/acceptance/dump_agent_graph.py --graph supervisor --print

产物落在 `.acceptance-reports/agent-graphs/`（该目录已 gitignore）：
    <name>-topology.mmd   纯 mermaid 源（VS Code mermaid 插件 / mermaid.live 可直接渲染）
    <name>-topology.md    同上，包一层可直接预览的 Markdown

为什么要落盘而不是每次现画：mermaid 源在 Code Review / 复盘时是最省事的"图"，
而且能进 diff —— 拓扑改了会**看得见**。

⚠️ 不用 `draw_mermaid_png()`：它要走外网渲染服务，CI/内网会挂。
"""

from __future__ import annotations

import argparse
import pathlib
import sys

_ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_ROOT))

# 脚本自带的渲染辅助（与 agent_nl_smoke 共用），在脚本同目录
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from mermaid_util import normalize, write_all  # noqa: E402

DEFAULT_OUT = _ROOT / ".acceptance-reports" / "agent-graphs"

_BUILDERS = {
    "supervisor": ("app.ops.lg_rag.multi.graph", "build_supervisor_agent"),
    "router": ("app.ops.lg_rag.graph", "build_router_agent"),
    "basic": ("app.ops.lg_rag.graph", "build_basic_agent"),
}


def _build(name: str):
    import importlib

    mod_name, fn_name = _BUILDERS[name]
    mod = importlib.import_module(mod_name)
    return getattr(mod, fn_name)()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--graph",
        default="all",
        choices=(*_BUILDERS, "all"),
        help="导哪张图（默认 all）",
    )
    ap.add_argument("--out-dir", default=str(DEFAULT_OUT))
    ap.add_argument("--print", action="store_true", help="同时打到 stdout")
    args = ap.parse_args()

    import app.config  # noqa: F401  ← 先加载 .env（图本身不联网，但配置要一致）

    out_dir = pathlib.Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    names = list(_BUILDERS) if args.graph == "all" else [args.graph]

    for name in names:
        graph = _build(name)
        g = graph.get_graph()
        # ⚠️ 原生输出带 YAML front matter + `<p>` + `&nbsp;`，很多预览器（含
        #    WorkBuddy 的 Markdown 预览）渲染不出来 —— 必须归一化。
        raw = g.draw_mermaid()
        mermaid = normalize(raw)

        mmd, html_path = write_all(
            out_dir,
            f"{name}-topology",
            title=f"{name} 图 · 静态拓扑",
            sections=[("拓扑", mermaid)],
            note=f"节点 {len(g.nodes)} / 边 {len(g.edges)} · 由 dump_agent_graph.py 生成",
        )

        md = out_dir / f"{name}-topology.md"
        md.write_text(
            f"# {name} 图 · 静态拓扑\n\n"
            f"- 节点数：{len(g.nodes)}\n"
            f"- 边数：{len(g.edges)}\n"
            f"- 生成：`scripts/acceptance/dump_agent_graph.py --graph {name}`\n"
            f"- 渲染不出来就看 `{html_path.name}`（自渲染 HTML，不依赖宿主预览器支持 mermaid）\n\n"
            f"```mermaid\n{mermaid}```\n"
        )
        print(f"[OK] {name}: 节点 {len(g.nodes)} / 边 {len(g.edges)} -> {mmd.name} / {html_path.name}")
        if args.print:
            print(mermaid)

    print(f"\n产物目录：{out_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
