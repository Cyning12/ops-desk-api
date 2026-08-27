"""lg_rag 域 Structured Output 用的 Pydantic schema。

与 SO 内核（extract/parse/complete）解耦；仅含业务模型，无管道逻辑。
"""

from app.ops.lg_rag.schemas.extract import ExtractResult
from app.ops.lg_rag.schemas.intent import IntentV1
from app.ops.lg_rag.schemas.route import RouteDecision
from app.ops.lg_rag.schemas.subtasks import SubtaskItem, SubtasksPlan

__all__ = [
    "ExtractResult",
    "IntentV1",
    "RouteDecision",
    "SubtaskItem",
    "SubtasksPlan",
]
