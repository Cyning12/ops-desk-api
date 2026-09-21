"""PromptAssembly · 模板 + 变量 + slot 装配（H4）；C2 起增 Prompt Pack 层。

安全槽位（security-input-isolation W1 · `slots.py`）：`SLOT_REGISTRY` 六槽位
白名单（user_query/history_turn/rag_evidence/tool_result/memory_fact/
system_instruction · 注册表外不存在）+ `wrap_slot` 强制包装（边界标记 +
不可信声明 + 伪造标记转义的唯一生成点）+ `assert_slots_declared` 装配校验
纯函数（未声明/未包装段显式炸不静默降级）。开关
`SECURITY_INPUT_ISOLATION_ENABLED` 默认关（非法值回退 false + warning ·
off 态各装配面与现网逐字节一致且校验零触达）。故障语义分立：内容违例 →
显式炸请求不发出（下游零请求 + span `input_isolation_rejected`）；机制自身
故障 → 该请求降级 off 态装配（span `input_isolation_degraded`）。
命名纪律：本「槽位」（不可信内容归因）与 packs/render 的 pack/模板槽位
（`REQUIRED_SLOTS`/`<!-- slot:{name} -->`）命名邻近、语义两套，互不相干。
"""

from app.ops.prompts.packs import (
    PromptPack,
    PromptPackError,
    PromptPackNotFoundError,
    render_pack,
    route_intent,
)
from app.ops.prompts.render import PromptTemplateNotFoundError, get_template, render

__all__ = [
    "PromptPack",
    "PromptPackError",
    "PromptPackNotFoundError",
    "PromptTemplateNotFoundError",
    "get_template",
    "render",
    "render_pack",
    "route_intent",
]
