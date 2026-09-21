"""事实型记忆 P0（memory-facts-p0）：写入闸 + 状态机 service + 召回注入。

- `gate`：`should_write(candidate)` 纯函数，三判据（可复用 / 稳定 / 与主体相关）
  落成显式规则；拒绝返回稳定可枚举的原因码，**拒绝 = 不落库**。
- `service`：`write_fact`（过闸 + 同事务 supersede）· `revoke_by_source`
  （批量 revoked + 审计日志）· `sweep_expired` · `recall_active`（查询路径
  自带过期过滤的双保险）。
- 装配注入在 `app.ops.lg_rag.continuity.assemble_graph_messages_with_memory`
  （默认关，关闭时与现网逐字节一致）。

P0 候选来源只有显式调用（service API / 测试）；**LLM 自动抽取是 P1**。
无对外 HTTP 端点；无向量召回；无画像。
"""

from app.ops.memory.gate import Decision, FactCandidate, should_write
from app.ops.memory.service import (
    GateRejectedError,
    recall_active,
    revoke_by_source,
    sweep_expired,
    write_fact,
)

__all__ = [
    "Decision",
    "FactCandidate",
    "should_write",
    "GateRejectedError",
    "write_fact",
    "revoke_by_source",
    "sweep_expired",
    "recall_active",
]
