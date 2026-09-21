"""自然语言入口 · 真 LLM 端到端冒烟（走 HTTP · 真会话 · 真模型）。

## 为什么必须有这一条

其余验收（A 九层 / B 落库 / C 出网 / D 审批 / E 回流）都是**单测级、CD 级或进程内直调**——
没有一条从**自然语言入口**进去。而"入口那一层"恰恰最容易整层失效：
鉴权、SSE 帧序、租户解析、图装配、能力调用，任何一环断了，前面五条线照样全绿。

**入口本身**（`POST /api/ops/lg-rag/stream`，freeze `lg-rag-sse-v1`，默认 `mode=supervisor`）：

```
登录（一次性邀请 token） → cookie 会话 → 提交自然语言 → 逐帧回 SSE
```

`POST /api/ops/chat/stream` 已于 2026-08-31 下线（`app/ops/chat/router.py` 里留了
successor-version 提示），所以**唯一**的自然语言入口就是上面这个。

## 这条冒烟验什么（结构不变量，不验"答案对不对"）

1. 入口可达 + **鉴权真的能过**（铸 token → 登录 → 拿到 `ops_session` cookie）
2. 请求被接受：首帧是 `run.start`
3. **图真的跑了**：能看到 `intent_node` / `strategy_builder` / `supervisor` 这类节点帧
4. 出结论：`answer` 帧非空；或明确转入 `hitl.waiting`（在等人批，也是合法终局）
5. 正常收口：有 `done`；**没有 `error` 帧**
6. 报告是否真的**用到了能力**（`tool_exec` / `subtask.progress`）——默认只报告不强制，
   加 `--expect-tool` 才硬断言

**不验**"答得对不对"——那是评测集（`evals/`）与 `scripts/router_accuracy.py` 的职责。

## 代价与前置

- **会真的调用 LLM**（花钱、有延迟，单次通常 10–60s）。
- 需要 `.env` 里的 `SILICONFLOW_API_KEY`（或对应 provider 的 key）。
- 默认 query 只依赖 **builtin** 的 5 个 `local_fn` 能力（supervisor 模式的候选集就是它们），
  所以**不需要 mock-oa、不需要 OA 凭证**。
"""

from __future__ import annotations

import asyncio

import argparse
import http.cookiejar
import json
import os
import pathlib
import sys
import time
import urllib.error
import urllib.request

_ROOT = pathlib.Path(__file__).resolve().parents[2]

_AGENT_PORT = os.environ.get("AGENT_PORT", "8123")
AGENT = f"http://127.0.0.1:{_AGENT_PORT}/api/ops"
SMOKE_USER = "nl-smoke"

# 出口代理会把打 127.0.0.1 的请求送到代理去（拿到看不懂的 502）
OPENER_BASE = urllib.request.build_opener(urllib.request.ProxyHandler({}))

failures: list[str] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    print(f"[{'PASS' if ok else 'FAIL'}] {name}" + (f" —— {detail}" if detail else ""))
    if not ok:
        failures.append(name)


# ---------------------------------------------------------------------------
# 会话：铸一次性邀请 token → 登录
# ---------------------------------------------------------------------------

#: 本次**实际创建**的东西。收尾只删这里记下的 ——
#: 绝不按"未消费的邀请"这种范围条件批量删（那是别人的数据，且 `--help` 也会踩到）。
_CREATED: dict[str, object] = {"invite_id": None, "username": None}


async def _mint_invite() -> str:
    """铸**一枚**一次性邀请 token（等价 ``scripts/create_initial_user.py`` 的做法）。

    ``ops_invite_tokens`` 的 token 列存的是**哈希**，明文只在这一刻存在。
    返回明文，并把刚创建那行的 id 记进 ``_CREATED`` 供收尾精确删除。
    """
    from datetime import datetime, timedelta

    from app.db.models import OpsInviteToken
    from app.db.session import AsyncSessionLocal
    from app.ops.security import generate_invite_token, hash_token

    plain = generate_invite_token()
    async with AsyncSessionLocal() as db:
        row = OpsInviteToken(
            token=hash_token(plain),
            role="maintainer",
            expires_at=datetime.utcnow() + timedelta(hours=1),
        )
        db.add(row)
        await db.commit()
        await db.refresh(row)
        _CREATED["invite_id"] = row.id
    return plain


async def _cleanup_session() -> None:
    """只删**本次创建**的邀请 / 会话 / 冒烟用户。**报出删了什么**，不静默留垃圾。

    ⚠️ 曾经写成"删掉所有未消费的邀请"—— 那是**别人的**数据，而且 `--help`
    （argparse 直接 SystemExit）也会走到 finally 里把它删掉。收尾一律按"自己创建的主键"删。
    """
    from sqlalchemy import delete, select

    from app.db.models import OpsInviteToken, OpsSession, OpsUser
    from app.db.session import AsyncSessionLocal

    invite_id = _CREATED.get("invite_id")
    if invite_id is None and not _CREATED.get("username"):
        # 本次什么都没建（例如只跑了 --help）—— 绝不碰任何已有数据
        print("收尾：本次未创建任何数据，跳过清理")
        return

    async with AsyncSessionLocal() as db:
        n_sess = 0
        if _CREATED.get("username"):
            user = await db.scalar(
                select(OpsUser).where(OpsUser.username == str(_CREATED["username"]))
            )
            if user is not None:
                n_sess = (
                    await db.execute(
                        delete(OpsSession).where(OpsSession.user_id == user.id)
                    )
                ).rowcount or 0
                await db.execute(delete(OpsUser).where(OpsUser.id == user.id))
        n_inv = 0
        if invite_id is not None:
            n_inv = (
                await db.execute(
                    delete(OpsInviteToken).where(OpsInviteToken.id == invite_id)
                )
            ).rowcount or 0
        await db.commit()
    print(
        f"收尾：删除邀请 {n_inv} 条、session {n_sess} 条"
        + (f"、用户 {_CREATED['username']}" if _CREATED.get("username") else "")
    )


def _opener() -> urllib.request.OpenerDirector:
    """带 cookie jar 的 opener —— 会话是 cookie，不是 Bearer。"""
    jar = http.cookiejar.CookieJar()
    return urllib.request.build_opener(
        urllib.request.ProxyHandler({}), urllib.request.HTTPCookieProcessor(jar)
    )


def _login(opener: urllib.request.OpenerDirector, invite: str) -> dict:
    body = json.dumps({"username": SMOKE_USER, "invite_token": invite}).encode()
    req = urllib.request.Request(f"{AGENT}/auth/login", data=body, method="POST")
    req.add_header("Content-Type", "application/json")
    with opener.open(req, timeout=30) as res:
        return json.loads(res.read().decode() or "{}")


# ---------------------------------------------------------------------------
# 自然语言 → SSE
# ---------------------------------------------------------------------------

def _stream_nl(
    opener: urllib.request.OpenerDirector,
    *,
    query: str,
    mode: str,
    thread_id: str,
    timeout: int,
) -> list[dict]:
    """提交自然语言，逐帧收 SSE（`event: X` + `data: {json}`）。"""
    body = json.dumps({"query": query, "mode": mode, "thread_id": thread_id}).encode()
    req = urllib.request.Request(f"{AGENT}/lg-rag/stream", data=body, method="POST")
    req.add_header("Content-Type", "application/json")
    # 刻意**不带** X-Ops-Tenant：带了会与会话租户做一致性校验，不带则用会话租户
    req.add_header("Accept", "text/event-stream")

    frames: list[dict] = []
    with opener.open(req, timeout=timeout) as res:
        for raw in res:  # 逐行；流式响应会边到边出
            line = raw.decode("utf-8").rstrip("\r\n")
            if line.startswith("data: "):
                try:
                    frames.append(json.loads(line[len("data: ") :]))
                except json.JSONDecodeError:
                    continue
    return frames


def _timeline(frames: list[dict]) -> list[tuple[str, str]]:
    return [
        (str(f.get("event_type") or ""), str(f.get("agent_role") or "")) for f in frames
    ]


# ---------------------------------------------------------------------------
# 运行链 mermaid（按**真实帧序**画，不是静态拓扑）
# ---------------------------------------------------------------------------

#: SSE 的 agent_role 是**别名**（见 sse_stream._ROLE_ALIAS），要映射回节点 id
_ALIAS_TO_NODE = {"intent": "intent_node", "critic": "critic_node"}
#: 三个"工人"节点（画图时给不同配色）
_SUBTASK_NODES = frozenset({"rag_subtask", "info_extract", "tool_exec"})
#: 这些帧不对应某个节点（是流的外壳）
_SHELL_EVENTS = frozenset({"run.start", "done", "hitl.waiting"})


def _node_chain(frames: list[dict]) -> list[tuple[str, int]]:
    """把帧序压成 ``[(节点名, 该节点连续产出的帧数)]``。

    为什么"连续重复"要合并：终答节点的 token delta 会连发很多帧，
    不合并的话运行链上会出现 20 个一模一样的节点，看不清真实跳转。
    """
    out: list[tuple[str, int]] = []
    for f in frames:
        et = str(f.get("event_type") or "")
        role = str(f.get("agent_role") or "")
        if et in _SHELL_EVENTS or not role or role == "system":
            continue
        node = _ALIAS_TO_NODE.get(role, role)
        if out and out[-1][0] == node:
            out[-1] = (node, out[-1][1] + 1)
            continue
        out.append((node, 1))
    return out


def _run_chain_mermaid(
    chain: list[tuple[str, int]], edge_labels: dict[tuple[str, str], str]
) -> str:
    """时序链：每次访问用**独立节点**（n1/n2…），所以循环与重复访问如实画出来。"""
    if not chain:
        return "flowchart TD\n  empty[\"没有收到任何节点帧\"]\n"
    lines = ["flowchart TD", "  S([START]):::term"]
    prev = "S"
    for i, (node, cnt) in enumerate(chain, 1):
        label = f"{i}. {node}" + (f" ×{cnt}" if cnt > 1 else "")
        lines.append(f'  n{i}["{label}"]:::{"sub" if node in _SUBTASK_NODES else "graph"}')
        branch = edge_labels.get((chain[i - 2][0] if i > 1 else "__start__", node), "")
        arrow = f"-- {branch} -->" if branch else "-->"
        lines.append(f"  {prev} {arrow} n{i}")
        prev = f"n{i}"
    lines.append(f"  {prev} --> E([END]):::term")
    lines += [
        "  classDef graph fill:#B5D4F4,stroke:#185FA5,color:#042C53",
        "  classDef sub fill:#5DCAA5,stroke:#0F6E56,color:#04342C",
        "  classDef term fill:#FAC775,stroke:#854F0B,color:#412402",
    ]
    return "\n".join(lines) + "\n"


def _edge_labels() -> dict[tuple[str, str], str]:
    """从静态拓扑里取"条件边的分支名"，让运行链的箭头带上 ``settle`` / ``replan`` 这类标签。"""
    from app.ops.lg_rag.multi.graph import build_supervisor_agent

    g = build_supervisor_agent().get_graph()
    labels: dict[tuple[str, str], str] = {}
    for e in g.edges:
        data = getattr(e, "data", None) or ""
        if data:
            labels[(e.source, e.target)] = str(data).replace("&nbsp;", "").strip()
    return labels


def _write_run_report(
    *,
    out_dir: pathlib.Path,
    query: str,
    mode: str,
    thread_id: str,
    frames: list[dict],
    elapsed: float,
    answer: str,
) -> pathlib.Path:
    """把这一轮的**运行链**落盘成可直接预览的 Markdown（内含 mermaid）。"""
    chain = _node_chain(frames)
    visited = {n for n, _ in chain}
    base = _edge_labels()
    chain_edges = {}
    for i in range(1, len(chain)):
        chain_edges[(chain[i - 1][0], chain[i][0])] = base.get(
            (chain[i - 1][0], chain[i][0]), ""
        )
    run_mmd = _run_chain_mermaid(chain, base)
    topo_mmd = ""
    if mode == "supervisor":
        from app.ops.lg_rag.multi.graph import build_supervisor_agent

        topo_mmd = build_supervisor_agent().get_graph().draw_mermaid()

    counts: dict[str, int] = {}
    for n, _ in chain:
        counts[n] = counts.get(n, 0) + 1

    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = time.strftime("%Y%m%d-%H%M%S")
    slug = "".join(ch for ch in query[:16] if ch.isalnum() or ch in "-_") or "run"
    path = out_dir / f"{stamp}-{slug}.md"

    # ⚠️ 归一化 + 额外落一份自渲染 HTML：宿主 Markdown 预览未必支持 mermaid
    #    （实测 WorkBuddy 预览渲染不出来，Cursor 可以）。
    from mermaid_util import normalize, write_all

    run_mmd = normalize(run_mmd)
    topo_mmd = normalize(topo_mmd) if topo_mmd else ""
    sections = [("实际运行链", run_mmd)]
    if topo_mmd:
        sections.append(("静态拓扑（对照）", topo_mmd))
    _, html_path = write_all(
        out_dir,
        f"{stamp}-{slug}",
        title=f"Agent 运行链 · {stamp}",
        sections=sections,
        note=f"问题：{query} · mode={mode} · {len(frames)} 帧 / {elapsed:.1f}s",
    )

    lines = [
        f"# Agent 运行链 · {stamp}",
        "",
        "| 项 | 值 |",
        "|---|---|",
        f"| 问题 | `{query}` |",
        f"| mode | `{mode}` |",
        f"| thread_id | `{thread_id}` |",
        f"| 帧数 | {len(frames)} |",
        f"| 耗时 | {elapsed:.1f}s |",
        f"| 终答字数 | {len(answer)} |",
        "",
        f"渲染不出来就看 `{html_path.name}`（自渲染 HTML，不依赖宿主预览器支持 mermaid）",
        "",
        "## 实际运行链（按帧序，循环/重复如实画）",
        "",
        "```mermaid",
        run_mmd.rstrip("\n"),
        "```",
        "",
        "## 节点访问次数",
        "",
        "| 节点 | 访问次数 |",
        "|---|---|",
    ]
    for n, c in sorted(counts.items(), key=lambda kv: (-kv[1], kv[0])):
        lines.append(f"| `{n}` | {c} |")
    if topo_mmd:
        unvisited = sorted(
            n for n in _topology_node_ids() if n not in visited
        )
        lines += [
            "",
            "## 本次未走到的节点",
            "",
            ("、".join(f"`{n}`" for n in unvisited) if unvisited else "无（全走到了）"),
            "",
            "## 静态拓扑（对照用）",
            "",
            "```mermaid",
            topo_mmd.rstrip("\n"),
            "```",
        ]
    lines.append("")
    path.write_text("\n".join(lines))
    return path


def _topology_node_ids() -> set[str]:
    from app.ops.lg_rag.multi.graph import build_supervisor_agent

    g = build_supervisor_agent().get_graph()
    return {n for n in g.nodes if not str(n).startswith("__")}


def _verify_trace(thread_id: str, *, tries: int = 6, delay: float = 2.0) -> tuple[bool, str]:
    """查 Langfuse：这一轮的 trace 到底落库了没（按 ``session_id = thread_id``）。

    **为什么要"查"而不是"假设"**：上报是异步的，SDK 不报错 ≠ 平台收到了。
    常见的静默失败：环境名对不上（UI 选了别的 environment 就"看起来没有"）、
    key 是另一个 project 的、网络被拦。只有查一次才知道。
    """
    try:
        from langfuse import get_client

        client = get_client()
    except Exception as exc:
        return False, f"SDK 初始化失败：{exc!r}"

    last = ""
    for _ in range(tries):
        try:
            page = client.api.trace.list(session_id=thread_id, limit=5)
            data = list(getattr(page, "data", None) or [])
        except Exception as exc:
            return False, f"查询失败：{exc!r}"
        if data:
            t = data[0]
            return True, f"trace_id={getattr(t, 'id', '')} name={getattr(t, 'name', '')}"
        time.sleep(delay)
    return False, f"{tries}×{delay}s 内没查到（ingestion 异步；也可能 environment 选错）"


async def _main_async(args: argparse.Namespace) -> int:
    """全程在**同一个事件循环**里做完。

    ⚠️ 不能把铸 token 与收尾清理各自 `asyncio.run(...)`：async SQLAlchemy 的连接池
    会把连接绑在创建它的那个 loop 上，第二次 `asyncio.run` 建的是新 loop，
    于是收尾时抛 `attached to a different loop` —— 而那时异常在 finally 里，
    表现为"冒烟全过、收尾失败、垃圾数据留在库里"。
    """
    from datetime import datetime, timedelta

    key = (os.environ.get("SILICONFLOW_API_KEY") or "").strip()
    print(f"provider={os.environ.get('OPS_LLM_PROVIDER')} model={os.environ.get('OPS_LLM_MODEL')}")
    check("LLM key 已配置（这条冒烟会真调模型）", bool(key) or bool(os.environ.get("BAILIAN_API_KEY")))

    # 1 · 会话：铸 token → 登录
    opener = _opener()
    try:
        info = _login(opener, await _mint_invite())
    except urllib.error.HTTPError as exc:
        check(
            "登录成功（cookie 会话）",
            False,
            f"{exc.code} {exc.read().decode('utf-8', 'replace')[:120]}",
        )
        return 1
    check("登录成功（cookie 会话）", bool(info.get("ok")),
          json.dumps(info, ensure_ascii=False)[:120])
    if not info.get("ok"):
        return 1
    # 登录成功 = 用户（可能新建）与会话都产生了，收尾要一起清
    _CREATED["username"] = SMOKE_USER

    # 2 · 提交自然语言，收 SSE
    thread_id = f"nl-smoke-{int(time.time())}"
    print(f"\n提交自然语言：{args.query!r}（mode={args.mode}，thread_id={thread_id}）")
    t0 = time.perf_counter()
    try:
        frames = _stream_nl(
            opener,
            query=args.query,
            mode=args.mode,
            thread_id=thread_id,
            timeout=args.timeout,
        )
    except urllib.error.HTTPError as exc:
        check("入口接受请求（未 401/403/5xx）", False,
              f"{exc.code} {exc.read().decode('utf-8', 'replace')[:160]}")
        return 1
    elapsed = time.perf_counter() - t0

    kinds = [k for k, _ in _timeline(frames)]
    roles = sorted({r for _, r in _timeline(frames) if r})
    print(f"共 {len(frames)} 帧，耗时 {elapsed:.1f}s")
    print("帧序：", " → ".join(kinds[:24]) + (" …" if len(kinds) > 24 else ""))
    print("出现过的 agent_role：", roles)

    answer = ""
    for f in frames:
        if f.get("event_type") == "answer":
            answer = str((f.get("payload") or {}).get("content") or "") or answer
    payload_done = next(
        (f.get("payload") or {} for f in frames if f.get("event_type") == "done"), {}
    )

    # 3 · 结构不变量
    check("首帧是 run.start", bool(frames) and kinds[0] == "run.start",
          kinds[0] if kinds else "无帧")
    check("图真的跑了（看到节点帧）", any(r not in ("system", "") for r in roles), str(roles))
    err_payload = next(
        (json.dumps(f.get("payload"), ensure_ascii=False)[:160]
         for f in frames if f.get("event_type") == "error"),
        "",
    )
    check("没有 error 帧", "error" not in kinds, err_payload)
    waiting = "hitl.waiting" in kinds
    check(
        "出结论（answer 非空）或转入等待授权",
        bool(answer.strip()) or waiting,
        f"answer {len(answer)} 字" + ("；hitl.waiting=True" if waiting else ""),
    )
    check("正常收口（有 done）", "done" in kinds)

    # ⚠️ 分清两件事，别混："跑了工人节点" ≠ "调到了能力"。
    #    只有 ``tool_exec`` 会经 Capability Gateway 打真实能力；
    #    rag_subtask / info_extract 走的是检索与抽取，不打能力。
    worker_roles = ("tool_exec", "rag_subtask", "info_extract")
    used_worker = any(r in worker_roles for r in roles)
    used_capability = "tool_exec" in roles
    print(
        f"\n本次：跑了工人节点={used_worker}；**真的调到能力={used_capability}**"
        f"（tool_exec {'在' if used_capability else '不在'}角色表里）"
    )
    if answer:
        print(f"answer 预览：{answer[:200]}")
    if payload_done:
        print(f"done payload：{json.dumps(payload_done, ensure_ascii=False)[:200]}")
    if args.expect_tool:
        # ⚠️ 这条**依模型选择而定**：同一句话，模型这次可能拆成 rag 子任务、
        # 下次才拆成 tool 子任务。断言失败不等于链路坏了 —— 所以失败信息要写清
        # "是模型没选工具"，而不是让人去查代码。要确定性就用图级 mock 测试。
        check(
            "这次真的调到了能力（--expect-tool：要求出现 tool_exec）",
            used_capability,
            f"本次角色：{roles}"
            + ("" if used_capability else "；模型这轮把它拆成了检索/抽取，没走工具——非链路故障"),
        )

    # 4 · 运行链落盘（结束后看"这次到底走了哪些节点、按什么顺序"）
    if not args.no_mermaid:
        try:
            path = _write_run_report(
                out_dir=pathlib.Path(args.mermaid_out),
                query=args.query,
                mode=args.mode,
                thread_id=thread_id,
                frames=frames,
                elapsed=elapsed,
                answer=answer,
            )
            print(f"\n运行链已落盘：{path}")
            print(f"自渲染 HTML（宿主预览器不认 mermaid 时看这个）：{path.with_suffix('.html')}")
        except Exception as exc:
            check("运行链落盘", False, repr(exc))

    # 5 · 追踪：**查一次** Langfuse，别假设上报成功
    from app.ops.tracing import tracing_enabled

    if tracing_enabled():
        print("\n追踪已开（OPS_CHAT_TRACER），查 Langfuse 是否真的收到这一轮…")
        ok, detail = _verify_trace(thread_id)
        check("Langfuse 收到本轮 trace（session_id=thread_id）", ok, detail)
    else:
        print(
            "\n追踪未开（OPS_CHAT_TRACER 为空）⇒ 不会有 trace。"
            "要看 trace：让 .env 里 OPS_CHAT_TRACER=langfuse 并对本脚本用 OPS_NL_SMOKE_NO_TRACING=0。"
        )

    print()
    if failures:
        print(f"自然语言冒烟失败 {len(failures)} 项：{failures}")
        return 1
    print("自然语言冒烟全部通过")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--query",
        default="查一下 issue 21 的标题和状态",
        # 为什么默认是这一句：实测它能走完**完整多智能体链**并**真的调到一个能力**
        # （intent → strategy_builder → supervisor → tool_exec → observe → aggregator → critic），
        # 比"现在是几点？"（实测走 rag、192s、不调工具）更能说明链路是通的。
        # 依赖开发库里有 issue 21；换库/空库时用 --query 指定别的。
        help="自然语言问题（默认会命中 get_issue_by_number 这个工具）",
    )
    ap.add_argument("--mode", default="supervisor", choices=("supervisor", "router", "basic"))
    ap.add_argument("--timeout", type=int, default=180, help="整体读流超时（秒）")
    ap.add_argument(
        "--expect-tool",
        action="store_true",
        help="硬断言这次确实用到了能力（默认只报告；选不选工具由模型决定）",
    )
    ap.add_argument(
        "--mermaid-out",
        default=str(_ROOT / ".acceptance-reports" / "agent-runs"),
        help="把这轮的**运行链 mermaid** 落盘到哪个目录（默认 .acceptance-reports/agent-runs）",
    )
    ap.add_argument(
        "--no-mermaid",
        action="store_true",
        help="不落盘运行链",
    )
    args = ap.parse_args()

    import app.config  # noqa: F401  ← 必须先 import：不然 .env 不会被 load_dotenv 读进来

    return asyncio.run(_run_all(args))


async def _run_all(args: argparse.Namespace) -> int:
    """一次 `asyncio.run` 包住全程 —— 铸 token / 登录 / 收流 / 收尾清理同一个事件循环。"""
    try:
        return await _main_async(args)
    finally:
        try:
            await _cleanup_session()
        except Exception as exc:
            print(f"收尾清理失败（可能残留会话/用户）：{exc!r}")


if __name__ == "__main__":
    sys.exit(main())
