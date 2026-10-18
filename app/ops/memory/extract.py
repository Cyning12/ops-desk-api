"""LLM 离线候选抽取（memory-facts-p1 · V2 · 默认关）。

纪律（SPEC §2 D2 钉死）：
- **run 完成后离线触发**（对齐 T5.1 后台 persist 模式）：invoke / SSE 两入口
  在 run 结束后 `schedule_memory_extraction` 点火（create_task 不 await），
  **热路径零抽取调用、零额外延迟**。
- 产出仅为 **候选**：逐条过 `should_write` → 过闸走 `write_fact`
  （P0 事务 supersede 复用），写入必带 `source_run_id` + `source_turn`
  （`revoke_by_source` 一键全撤）。
- 输出走 structured_output 管道（parse → repair → validate），不手撕 JSON。
- LLM 失败 / 非法 JSON / 超时 → **零写入** + log；管道内 correction 重试 ≤1；
  每 run 至多 1 次抽取调用（`schedule_*` 每入口一次）。
- 抽取输入只传必要文本窗（本轮 query + 终答，截断）；证据本体不进 prompt。
- prompt 走 prompts 资产（``memory.extract.system`` · system）+ 文本窗
  （user 消息）分离传递，不做插值——规避 JSON 示例花括号转义痛点。
"""

from __future__ import annotations

import asyncio
import logging
import os

from pydantic import BaseModel, Field

from app.llm.model_catalog import resolve_task_model
from app.llm.schema import BaseProvider
from app.llm.usage import use_run_context
from app.ops.memory.gate import FactCandidate, should_write
from app.ops.memory.service import write_fact
from app.ops.prompts import render
from app.ops.structured_output import acomplete_structured
from app.ops.structured_output.complete import LlmCtx
from app.ops.tracing import update_current_span_metadata

logger = logging.getLogger(__name__)

_TRUTHY = ("1", "true", "yes", "on")
_FALSY = ("0", "false", "no", "off")

#: 抽取管道内 correction 重试上限（总 LLM 尝试 ≤ 2，契约"有限重试 ≤1"）
EXTRACT_MAX_RETRIES = 1
#: 抽取整体超时（秒）；超时 = 零写入 + log
EXTRACT_TIMEOUT_S = 60.0
#: 抽取文本窗单侧截断上限（证据本体不进 prompt；只传必要窗）
EXTRACT_WINDOW_MAX_CHARS = 4000


class ExtractedFactItem(BaseModel):
    """单条抽取候选（value 限定标量；闸仍逐条复判）。"""

    key: str
    value: str | int | float | bool


class MemoryFactExtraction(BaseModel):
    """抽取管道输出 schema（structured_output validate 目标）。"""

    facts: list[ExtractedFactItem] = Field(default_factory=list)


def memory_facts_extract_enabled() -> bool:
    """`MEMORY_FACTS_EXTRACT_ENABLED`：默认 false；非法值回退 false + warning。"""
    raw = (os.getenv("MEMORY_FACTS_EXTRACT_ENABLED") or "").strip().lower()
    if not raw:
        return False
    if raw in _TRUTHY:
        return True
    if raw in _FALSY:
        return False
    logger.warning("invalid MEMORY_FACTS_EXTRACT_ENABLED=%r; fallback to false", raw)
    return False


def _build_window(query: str, answer: str) -> str:
    """必要文本窗：本轮 query + 终答，单侧截断；证据本体不进。"""
    q = (query or "").strip()[:EXTRACT_WINDOW_MAX_CHARS]
    a = (answer or "").strip()[:EXTRACT_WINDOW_MAX_CHARS]
    return f"用户问题：\n{q}\n\n助手回答：\n{a}"


async def run_memory_extraction(
    *,
    tenant_id: str,
    user_id: str,
    run_id: str,
    source_turn: int | None = None,
    query: str,
    answer: str,
    _provider: BaseProvider | None = None,
) -> tuple[int, int]:
    """一次抽取调用 → 候选逐条过闸 → 落库。返回 (candidates, written)。

    任何 LLM/解析/超时失败 → 零写入 + log（绝不静默写入）；单条写库故障
    不连坐其它候选（log exception 可查）。开关关闭 → (0, 0) 不触 LLM。
    """
    if not memory_facts_extract_enabled():
        return (0, 0)
    # 分层路由（D3）：OPS_LLM_TIER_EXTRACT_MODEL > 档默认（None → 沿用现网默认，
    # 未配置档时逐字节一致）；D4：usage 落表上下文（source run_id · extract 档）
    tier_model, _route_source = resolve_task_model("extract")
    llm_ctx = LlmCtx(model=tier_model) if tier_model else None
    try:
        with use_run_context(run_id=run_id, surface="background", task_type="extract"):
            result = await asyncio.wait_for(
                acomplete_structured(
                    system=render("memory.extract.system"),
                    user=_build_window(query, answer),
                    schema=MemoryFactExtraction,
                    ensure_keys=["facts"],
                    max_retries=EXTRACT_MAX_RETRIES,
                    raise_on_failure=True,
                    llm_ctx=llm_ctx,
                    _provider=_provider,
                ),
                timeout=EXTRACT_TIMEOUT_S,
            )
    except Exception:
        # LLM 失败 / 非法 JSON / 超时：零写入（候选不是事实）
        logger.warning("memory extraction failed run_id=%s; zero writes", run_id, exc_info=True)
        update_current_span_metadata({"memory_extract_candidates": 0, "memory_extract_written": 0})
        return (0, 0)
    assert isinstance(result, MemoryFactExtraction)

    written = 0
    for item in result.facts:
        candidate = FactCandidate(
            tenant_id=tenant_id, user_id=user_id, key=item.key, value=item.value
        )
        decision = should_write(candidate)
        if not decision.allowed:
            logger.info(
                "memory extract candidate rejected reason=%s key=%s run_id=%s",
                decision.reason_code,
                item.key,
                run_id,
            )
            continue
        try:
            await write_fact(candidate, source_run_id=run_id, source_turn=source_turn)
            written += 1
        except Exception:
            logger.exception("memory extract write failed key=%s run_id=%s", item.key, run_id)
    logger.info(
        "memory_extract_candidates=%d written=%d run_id=%s",
        len(result.facts),
        written,
        run_id,
    )
    update_current_span_metadata(
        {"memory_extract_candidates": len(result.facts), "memory_extract_written": written}
    )
    return (len(result.facts), written)


#: 在途后台抽取任务（对齐 T5.1 persist_tasks 模式：持有引用防 GC）
_extract_tasks: set[asyncio.Task[tuple[int, int]]] = set()


def schedule_memory_extraction(
    *,
    tenant_id: str | None,
    user_id: str | None,
    run_id: str,
    source_turn: int | None = None,
    query: str,
    answer: str,
) -> asyncio.Task[tuple[int, int]] | None:
    """run 完成后离线点火：**只 create_task 不 await**（热路径零额外延迟）。

    开关关闭 / 身份缺失 / 无运行中事件循环 → 返回 None 不触发。
    """
    if not memory_facts_extract_enabled():
        return None
    if not (tenant_id or "").strip() or not (user_id or "").strip():
        logger.warning("MEMORY_FACTS_EXTRACT_ENABLED on but tenant/user missing; skip extraction")
        return None
    try:
        task = asyncio.create_task(
            run_memory_extraction(
                tenant_id=(tenant_id or "").strip(),
                user_id=(user_id or "").strip(),
                run_id=run_id,
                source_turn=source_turn,
                query=query,
                answer=answer,
            )
        )
    except RuntimeError:
        logger.warning("no running event loop; skip memory extraction run_id=%s", run_id)
        return None
    _extract_tasks.add(task)
    task.add_done_callback(_extract_tasks.discard)
    return task


async def drain_memory_extraction() -> None:
    """等待在途抽取任务收尾（测试 / 关停用；请求路径不得调用）。"""
    if _extract_tasks:
        await asyncio.gather(*tuple(_extract_tasks), return_exceptions=True)
