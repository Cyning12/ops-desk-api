"""步骤契约 + 可恢复点（P1 · Q4 / Q8）的**配置级**闸门检查。

为什么单有单测不够
------------------
R14 / R15 在红线层用**假的工具调用**证明了闸门逻辑。但那证明不了"闸门真的
挡在出网之前"——假调用记的是我自己的计数器，不是请求。这一层用
``FakeHttpTransport`` 的 ``calls`` 记账，走的是**真 Gateway**（真 adapter、
真参数渲染、真 payload 解析），所以"零请求"是**请求层面的零**，不是记账层面的零。

另外两点只有这一层能验：

1. **绑定值真的进了出站请求的参数里**（``tx.calls[-1]["params"]``）——
   单测断言的是"派发载荷里的 args"，中间还隔着 adapter 的渲染。
   契约命中但 adapter 没渲染出来，闸门照样全绿，链子照样是断的。
2. **可恢复点是一份声明**（``plan_prefix_ids`` / ``recoverable_point``），
   不只是"看起来没重跑"。

退出码：0 全部成立；1 有条目不成立。
"""

from __future__ import annotations

import asyncio
import contextlib
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

os.environ["OA_BASE"] = "http://oa.test.local"
os.environ.setdefault("OPS_CAP_CRED_OA_GATEWAY_TOKEN", "local-dev-token")

from typing import Any  # noqa: E402

from app.ops.capability import register, unregister  # noqa: E402
from app.ops.capability.adapters import (  # noqa: E402
    FakeHttpTransport,
    GenericHttpAdapter,
    StaticCredentialVault,
)
from app.ops.capability.types import CapabilitySpec  # noqa: E402
from app.ops.lg_rag.multi import step_contract as sc  # noqa: E402
from app.ops.lg_rag.multi.nodes import (  # noqa: E402
    _issue_plan,
    _join_subtasks,
    route_next_subtask,
    supervisor_node,
    tool_exec_node,
)
from app.ops.lg_rag.state import SubtaskResultBatch  # noqa: E402

problems: list[str] = []


def check(label: str, ok: bool, detail: str = "") -> None:
    mark = "PASS" if ok else "FAIL"
    print(f"  [{mark}] {label}{(' · ' + detail) if detail else ''}")
    if not ok:
        problems.append(f"{label}: {detail}")


def _read_http(path: str) -> dict[str, Any]:
    return {
        "method": "GET",
        "base_url": "OA_BASE",
        "path": path,
        "auth": "oa_gateway_token",
        "query_map": {"keyword": "{{keyword}}", "owner": "{{owner}}"},
        "success_when": {"path": "$.code", "in": [0]},
        "timeout_ms": 2000,
    }


def _spec(cid: str, path: str) -> CapabilitySpec:
    return CapabilitySpec(
        capability_id=cid,
        kind="http",
        description="步骤契约验收",
        args_schema={
            "type": "object",
            "properties": {
                "keyword": {"type": "string"},
                "owner": {"type": "string"},
            },
            "additionalProperties": True,
        },
        tags=("oa",),
        side_effect="read",
        risk_level="low",
        when_to_use="步骤契约验收",
        visibility={"departments": ["all"], "roles": ["all"]},
        http=_read_http(path),
    )


def _register(cid: str, path: str, *, payload: Any = None, exc=None) -> FakeHttpTransport:
    spec = _spec(cid, path)
    tx = FakeHttpTransport(payload=payload if payload is not None else {"code": 0, "data": {}}, exc=exc)
    register(
        spec,
        GenericHttpAdapter(
            spec, transport=tx, vault=StaticCredentialVault({"oa_gateway_token": "s3cret"})
        ),
    )
    return tx


def _plan(with_consumes: bool, run_id: str) -> list[dict]:
    t2: dict[str, Any] = {
        "id": "t2",
        "type": "tool",
        "tool": "sc.step2",
        "input": "乙",
        "args": {"keyword": "乙"},
    }
    if with_consumes:
        t2["depends_on"] = ["t1"]
        t2["consumes"] = {"t1": ["owner"]}
    plan, errors, _ = _issue_plan(
        [
            {
                "id": "t1",
                "type": "tool",
                "tool": "sc.step1",
                "input": "甲",
                "args": {"keyword": "报销"},
                "produces": ["owner"],
            },
            t2,
        ],
        run_id=run_id,
        seq=0,
    )
    assert not errors, errors
    return plan


async def _drive(plan: list[dict], terminals: dict[str, dict], *, prefix: list[str] | None = None):
    """归并 → 派发 → 真执行工具节点。返回 (执行的 id, 被拦行, 出站请求数)。"""
    state: dict[str, Any] = {
        "subtasks": plan,
        "subtask_results": list(terminals.values()),
        "inflight_subtask_ids": [],
        "supervisor_step_count": 1,
        "run_id": "sc-run",
        "messages": [],
    }
    if prefix is not None:
        state["plan_prefix_ids"] = list(prefix)
    out = await _join_subtasks(state)
    blocked = {str(r.get("subtask_id")): r for r in (out.get("subtask_results") or [])}
    executed: list[str] = []
    for sid in out.get("inflight_subtask_ids") or []:
        routed = route_next_subtask({**state, "inflight_subtask_ids": [sid]})
        if not isinstance(routed, list):
            continue
        for send in routed:
            if send.node != "tool_exec":
                continue
            executed.append(str(send.arg["assigned_subtask"]["subtask_id"]))
            await tool_exec_node(send.arg)
    return executed, blocked


def main() -> int:
    # ---- 1) 前驱失败 ⇒ 后继零请求（请求层面：只放行 t1，t1 的失败是 transport）----
    tx1 = _register("sc.step1", "/api/v1/step1", exc=RuntimeError("connect fail"))
    tx2 = _register(
        "sc.step2", "/api/v1/step2", payload={"code": 0, "data": {"owner": "张三"}}
    )
    try:
        plan = _plan(True, "sc-run")
        t1, t2 = plan[0]["subtask_id"], plan[1]["subtask_id"]

        async def _round1():
            # 先真跑 t1（它失败），再让 join 决定 t2
            executed: list[str] = []
            state = {
                "subtasks": plan,
                "subtask_results": [],
                "inflight_subtask_ids": [t1],
                "supervisor_step_count": 1,
                "run_id": "sc-run",
                "messages": [],
            }
            for send in route_next_subtask(state) or []:
                if send.node == "tool_exec":
                    executed.append(str(send.arg["assigned_subtask"]["subtask_id"]))
                    await tool_exec_node(send.arg)
            err_row = {
                "id": t1,
                "subtask_id": t1,
                "type": "tool",
                "error": "upstream_error: transport",
            }
            return executed, await _drive(plan, {t1: err_row})

        first_exec, (second_exec, blocked) = asyncio.run(_round1())

        check(
            "前驱失败 ⇒ t1 真出过网（闸门没把该跑的也拦了）",
            len(tx1.calls) == 1,
            f"step1 出站 {len(tx1.calls)} 次",
        )
        check(
            "前驱失败 ⇒ 后继零请求（step2 一次都没出网）",
            t2 not in second_exec and len(tx2.calls) == 0,
            f"executed={second_exec} step2 出站 {len(tx2.calls)} 次",
        )
        check(
            "被拦的步骤带 blocked_by（可审计，不是静默跳过）",
            blocked.get(t2, {}).get("blocked_by") == sc.BLOCKED_PREDECESSOR_FAILED,
            f"blocked={blocked.get(t2, {}).get('blocked_by')}",
        )

        # ---- 2) 前驱成功但缺 consumes 字段 ⇒ 后继零请求 ----
        terminals = {t1: {"id": t1, "subtask_id": t1, "type": "tool", "output": {"items": []}}}
        _exec, blocked = asyncio.run(_drive(plan, terminals))
        check(
            "缺 consumes 字段 ⇒ 后继零请求（未声明前缀 ⇒ 判契约缺失）",
            len(tx2.calls) == 0
            and blocked.get(t2, {}).get("blocked_by") == sc.BLOCKED_CONTRACT_MISSING,
            f"step2 出站 {len(tx2.calls)} 次 blocked={blocked.get(t2, {}).get('blocked_by')}",
        )
        # 同一个缺失，声明了前缀 ⇒ 变成"要改历史"，交人
        _exec, blocked = asyncio.run(_drive(plan, terminals, prefix=[t1]))
        check(
            "同一个缺失落在声明前缀上 ⇒ prefix_touch + hitl（Q4/Q8 交汇）",
            blocked.get(t2, {}).get("blocked_by") == sc.BLOCKED_PREFIX_TOUCH
            and blocked.get(t2, {}).get("hitl_required") is True
            and len(tx2.calls) == 0,
            f"blocked={blocked.get(t2, {}).get('blocked_by')}",
        )

        # ---- 3) 契约满足 ⇒ 两步都执行，且绑定值真的进了**出站请求参数** ----
        ok_terminals = {
            t1: {"id": t1, "subtask_id": t1, "type": "tool", "output": {"owner": "张三"}}
        }
        executed, blocked = asyncio.run(_drive(plan, ok_terminals))
        before = len(tx2.calls)
        check(
            "契约满足 ⇒ 后继照常执行（反向对照：不是一律不派）",
            t2 in executed and before == 1 and not blocked,
            f"executed={executed} step2 出站 {before} 次 blocked={blocked}",
        )
        sent = tx2.calls[-1]["params"] if tx2.calls else {}
        check(
            "绑定值真的进了出站请求参数（不是只留在派发载荷里）",
            sent.get("owner") == "张三",
            f"params={sent}",
        )

        # ---- 4) 未声明 consumes ⇒ 不拦（反向对照）----
        plain = _plan(False, "sc-run")
        executed, blocked = asyncio.run(_drive(plain, ok_terminals))
        check(
            "未声明契约 ⇒ 不拦截（否则'一律不派'也能满足所有正向断言）",
            not blocked and t2 in executed,
            f"executed={executed} blocked={sorted(blocked)}",
        )
    finally:
        for cid in ("sc.step1", "sc.step2"):
            with contextlib.suppress(Exception):
                unregister(cid)

    # ---- 5) 可恢复点是一份**声明**，且重规划只动后缀 ----
    caps = [
        type("S", (), {"capability_id": "sc.step1", "description": "d", "risk_level": "low"})()
    ]

    async def _replan():
        from unittest.mock import AsyncMock, patch

        from langchain_core.messages import HumanMessage

        first = (
            '{"subtasks":[{"id":"t1","type":"tool","tool":"sc.step1","input":"甲",'
            '"args":{"keyword":"报销"}},{"id":"t2","type":"tool","tool":"sc.step1",'
            '"input":"乙","depends_on":["t1"]}]}'
        )
        suffix = (
            '{"subtasks":[{"id":"s1","type":"tool","tool":"sc.step1","input":"丙",'
            '"depends_on":["t1"]}]}'
        )
        base = {
            "messages": [HumanMessage(content="复合问题")],
            "run_id": "sc-run2",
            "allowed_capability_ids": ["sc.step1"],
            "supervisor_step_count": 0,
            "host_subtask_seq": 0,
            "subtasks": [],
            "subtask_results": [],
        }
        with patch(
            "app.ops.lg_rag.multi.nodes.list_capabilities", new=lambda *a, **k: caps
        ), patch(
            "app.ops.lg_rag.multi.nodes.get_llm_provider",
            new=lambda *a, **k: type(
                "P", (), {"complete": AsyncMock(side_effect=[first])}
            )(),
        ):
            out1 = await supervisor_node(dict(base))
        a, b = out1["subtasks"][0]["subtask_id"], out1["subtasks"][1]["subtask_id"]
        state2 = dict(base)
        state2.update(
            {
                "subtasks": out1["subtasks"],
                "subtask_results": SubtaskResultBatch(
                    [{"id": a, "subtask_id": a, "type": "tool", "output": {"owner": "张三"}}],
                    {a, b},
                ),
                "host_subtask_seq": out1["host_subtask_seq"],
                "supervisor_step_count": 1,
            }
        )
        with patch(
            "app.ops.lg_rag.multi.nodes.list_capabilities", new=lambda *a, **k: caps
        ), patch(
            "app.ops.lg_rag.multi.nodes.get_llm_provider",
            new=lambda *a, **k: type(
                "P", (), {"complete": AsyncMock(side_effect=[suffix])}
            )(),
        ):
            out2 = await supervisor_node(state2)
        return out1, out2, a

    out1, out2, a = asyncio.run(_replan())
    check(
        "首次规划：可恢复点 = 0（前缀逻辑不得影响正常规划）",
        out1["recoverable_point"] == 0 and len(out1["subtasks"]) == 2,
        f"recoverable_point={out1['recoverable_point']}",
    )
    check(
        "重规划：前缀逐字段保留 + 后缀拿新 id",
        [r["subtask_id"] for r in out2["subtasks"]] == [a, "sc-run2:3"]
        and out2["subtasks"][0]["args"] == {"keyword": "报销"},
        f"plan={[r['subtask_id'] for r in out2['subtasks']]}",
    )
    check(
        "重规划：可恢复点声明出来了（= 下一个真要执行的下标）",
        out2["recoverable_point"] == 1 and out2["plan_prefix_ids"] == [a],
        f"recoverable_point={out2['recoverable_point']} prefix={out2['plan_prefix_ids']}",
    )

    if problems:
        print(f"\n步骤契约 / 可恢复点检查不通过：{len(problems)} 项")
        for p in problems:
            print(f"  - {p}")
        return 1
    print("\n步骤契约 / 可恢复点检查通过")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
