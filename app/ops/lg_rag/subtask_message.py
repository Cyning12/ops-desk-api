"""lg-rag §10.7 · subtask.progress 可读 message（确定性模板 · freeze lg-rag-sse-v1）。

约束（task lg-rag-sse-subtask-message 00 定夺）：
- **纯同步**、不调 LLM、不塞模型 CoT / raw prompt / evidence 全文；
- 仅消费既有 step + detail（及 running/done 上下文轻量键）；
- SUBTASK_MESSAGE_MAX_LEN = 200 统一截断；
- 未知 step / 缺 detail 走兜底短句（含 step 名），**禁止**空串。
"""

from __future__ import annotations

from typing import Any

SUBTASK_MESSAGE_MAX_LEN = 200

_DETAIL_TEXT_MAX = 60  # detail 内嵌文本（current_query / output 预览）截断

_TYPE_LABEL = {
    "rag": "检索子任务",
    "extract": "信息抽取",
    "tool": "工具调用",
}

_GATE_ACTION_LABEL = {
    "answer": "证据充分，直接作答",
    "answer_partial": "证据不全，部分作答",
    "refuse": "证据不足，拒答",
}


def _truncate(text: str, max_len: int = SUBTASK_MESSAGE_MAX_LEN) -> str:
    text = str(text)
    if len(text) <= max_len:
        return text
    return text[: max_len - 1] + "…"


def _clip(value: Any, max_len: int = _DETAIL_TEXT_MAX) -> str:
    return _truncate(str(value).strip(), max_len)


def build_subtask_running_message(*, type: str = "", input_preview: str = "") -> str:
    """running 帧：含 type / input 摘要的一句。"""
    label = _TYPE_LABEL.get(type) or (f"子任务（{type}）" if type else "子任务")
    preview = (input_preview or "").strip()
    if preview:
        return _truncate(f"开始{label}：{_clip(preview)}")
    return f"开始{label}…"


def build_subtask_step_message(*, step: str = "", detail: dict[str, Any] | None = None) -> str:
    """step 帧：step + detail 的确定性模板映射；未知 step 兜底短句。"""
    step = (step or "").strip()
    detail = detail if isinstance(detail, dict) else {}
    phase = str(detail.get("phase") or "")

    if step == "retrieve":
        if phase == "start":
            return "开始检索…"
        if phase == "done":
            hit = detail.get("hit_count")
            if isinstance(hit, int) and not isinstance(hit, bool):
                return f"检索完成，命中 {hit} 条"
            return "检索完成"
    if step == "grade":
        if phase == "start":
            return "评估检索结果…"
        if phase == "done":
            parts: list[str] = []
            kept = detail.get("kept_count")
            if isinstance(kept, int) and not isinstance(kept, bool):
                parts.append(f"保留 {kept} 条")
            action = str(detail.get("gate_action") or "")
            if action:
                parts.append(_GATE_ACTION_LABEL.get(action, f"动作：{action}"))
            if parts:
                return _truncate("评估完成：" + "，".join(parts))
            return "评估完成"
    if step == "rewrite":
        query = str(detail.get("current_query") or "").strip()
        if query:
            return _truncate(f"改写查询：{_clip(query)}")
        return "改写查询…"
    if step == "answer":
        if phase == "start":
            return "生成回答…"
        if phase == "done":
            chars = detail.get("answer_chars")
            if isinstance(chars, int) and not isinstance(chars, bool):
                return f"回答生成完成（{chars} 字）"
            return "回答生成完成"
    if step:
        return _truncate(f"步骤：{step}")
    return "子任务进行中"


def build_subtask_done_message(*, subtask_result: Any = None, answer_preview: str = "") -> str:
    """done 帧：基于 subtask_result 轻量键的一句结果摘要（勿塞全文）。"""
    if isinstance(subtask_result, dict):
        error = str(subtask_result.get("error") or "").strip()
        if error:
            return _truncate(f"子任务失败：{_clip(error)}")
        output = subtask_result.get("output")
        if isinstance(output, str) and output.strip():
            return _truncate(f"子任务完成：{_clip(output, 80)}")
        if isinstance(output, dict):
            non_empty = sum(1 for v in output.values() if v)
            if non_empty:
                return f"信息抽取完成（{non_empty} 类有结果）"
            return "信息抽取完成（无结果）"
        if output is not None:
            return _truncate(f"子任务完成：{_clip(output, 80)}")
    preview = (answer_preview or "").strip()
    if preview:
        return _truncate(f"子任务完成：{_clip(preview, 80)}")
    return "子任务完成"
