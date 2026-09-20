"""HITL（人工审批）回路。

只有一处会触发：``step_contract`` 判出 ``prefix_touch_required`` ——
"要满足这一步，得重跑一个**已执行**的步骤"。按 Q8 §2.2，改已执行步骤的
``args`` 就是换一个幂等键 = 一次**新的写**，所以必须有人批。

回路四段：

1. ``observe_node``（编排层，async）发现 pending 的拦截 → ``store.acreate`` 落库；
2. OA / 审批端 ``GET /api/ops/hitl/requests?status=pending`` 拉待办（HMAC 鉴权）；
3. 审批端 ``POST /api/v1/hitl/.../decision``（mock-oa）→ 回调本服务
   ``POST /api/ops/hitl/callback``（HMAC 鉴权）→ 落库决定；
4. 批准后 ``POST /api/ops/hitl/requests/{id}/resume``：
   把 ``unlock_subtask_id`` 从不可变前缀里**摘出来** ⇒ 可恢复点回退到它 ⇒ 重跑。

第 4 步是"审批通过"的**唯一**效果：授权改历史，而不是自动改历史。
"""

from app.ops.hitl.persistence import (
    configure_hitl_from_env,
    describe_hitl_persistence,
    get_hitl_store,
    reset_hitl_store,
    set_hitl_store,
)
from app.ops.hitl.store import (
    STATUS_APPROVED,
    STATUS_PENDING,
    STATUS_REJECTED,
    HitlStore,
    InMemoryHitlStore,
    NullHitlStore,
    new_request_id,
)

__all__ = [
    "STATUS_APPROVED",
    "STATUS_PENDING",
    "STATUS_REJECTED",
    "HitlStore",
    "InMemoryHitlStore",
    "NullHitlStore",
    "configure_hitl_from_env",
    "describe_hitl_persistence",
    "get_hitl_store",
    "new_request_id",
    "reset_hitl_store",
    "set_hitl_store",
]
