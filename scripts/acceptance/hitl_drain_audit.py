"""升级前排空审计：把"在飞的审批"逐条判成 可恢复 / 已成历史 / 升级后恢复不了。

**为什么必须有这个**：实测 langgraph 0.2 → 1.2 升级，旧栈挂起的 checkpoint
**读得回 values 和 pending task，但 interrupt 元数据新栈认不出**
（``task.interrupts`` 为空）。硬喂 ``Command(resume=...)`` 会在 pregel 内部炸
``TypeError: 'Interrupt' object is not subscriptable``。

也就是说：**升级时正好挂在"等待授权"的那些 run，升级之后就废了** ——
它们既不会被拦成一句人话，也没法再恢复，只是永远停在那一帧。
所以升级前必须先跑这个脚本把在飞的审批排空（批完恢复，或人工作废重开）。

用法（PG 已起、.env 指向目标库）：

    ./.venv/bin/python scripts/acceptance/hitl_drain_audit.py

退出码：
  0 = 没有在飞的审批（可以安全升级）
  1 = 还有没排空的（**先处理再升**）
  2 = 审计本身做不了（**绝不等于"没有"**，人工确认前不要升级）
"""

from __future__ import annotations

import asyncio
import sys

from sqlalchemy import text

_STATE_LABEL = {
    "resumable": "可恢复（升级前先批掉）",
    "stranded": "★ 升级后恢复不了 —— 必须现在处理",
    "finished": "已无挂起（历史残留，无需处理）",
    "missing": "checkpoint 不存在（无需处理）",
}


class AuditUnavailable(RuntimeError):
    """审计做不了。**绝不能**当成"没东西要排空" —— 那是最危险的假阴性。"""


async def _pending_requests() -> list[dict]:
    from app.db.session import AsyncSessionLocal

    try:
        async with AsyncSessionLocal() as db:
            rows = (
                await db.execute(
                    text(
                        "SELECT id, run_id, thread_id, subtask_id, unlock_subtask_id, "
                        "created_at FROM ops_hitl_requests "
                        "WHERE status = 'pending' ORDER BY created_at ASC"
                    )
                )
            ).fetchall()
    except Exception as exc:
        # 表不存在 / 连不上 / 迁移没跑 —— 一律显式失败。
        # "查不到 pending" 和 "压根没查成" 必须分开，否则审计就成了绿灯。
        raise AuditUnavailable(f"读不到 ops_hitl_requests：{exc!r}") from exc
    return [
        {
            "id": r[0],
            "run_id": r[1],
            "thread_id": r[2],
            "subtask_id": r[3],
            "unlock_subtask_id": r[4],
        }
        for r in rows
    ]


async def _classify(graph, thread_id: str) -> str:
    if not thread_id:
        return "missing"
    try:
        snap = await graph.aget_state({"configurable": {"thread_id": thread_id}})
    except Exception:
        return "missing"
    tasks = list(getattr(snap, "tasks", None) or ())
    if not tasks:
        return "finished"
    if any(getattr(t, "interrupts", None) for t in tasks):
        return "resumable"
    return "stranded"


async def main() -> int:
    from app.ops.lg_rag.checkpointer import apostgres_saver
    from app.ops.lg_rag.multi.graph import build_supervisor_agent

    try:
        rows = await _pending_requests()
    except AuditUnavailable as exc:
        print(f"审计无法完成：{exc}")
        print("—— 这不等于'没有在飞的审批'。人工确认前不要升级。")
        return 2
    print(f"pending 审批申请：{len(rows)} 条")
    if not rows:
        print("没有在飞的审批 —— 可以安全升级")
        return 0

    counts = {"resumable": 0, "stranded": 0, "finished": 0, "missing": 0}
    async with apostgres_saver(setup=True) as saver:
        # 用**真图**判：task 重建依赖图的拓扑，拿最小图判会给出错的结论
        graph = build_supervisor_agent(checkpointer=saver)
        for row in rows:
            kind = await _classify(graph, row["thread_id"])
            counts[kind] += 1
            print(
                f"  [{kind:9s}] {row['id']}  thread={row['thread_id'] or '(空)'}  "
                f"unlock={row['unlock_subtask_id'] or '(空)'}  —— {_STATE_LABEL[kind]}"
            )

    print()
    for kind in ("resumable", "stranded", "finished", "missing"):
        print(f"  {kind:10s} {counts[kind]}")

    outstanding = counts["resumable"] + counts["stranded"]
    if outstanding:
        print(f"\n还有 {outstanding} 条没排空 —— 升级会丢掉它们，先处理再升")
        return 1
    print("\n在飞的都已无挂起，可以安全升级")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
