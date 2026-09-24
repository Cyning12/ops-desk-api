"""LLM 预算硬闸（Agent Host V1-C · llm-factory-closure D1/D2/D5）。

SPEC：docs/spec/host-v1-llm-factory-closure/SPEC-host-v1-llm-factory-closure_v0.md
（signed · Q1 llm 层单检查点锁死）。

设计纪律（SPEC §1 签收锁死）：

1. **默认观测**：``OPS_LLM_BUDGET_MODE=off|observe|enforce`` 默认 **off**
   （零行为：不计数不检查）；非法值回退 off。
   ``OPS_LLM_BUDGET_ENFORCE_TASKS`` 白名单默认空 = **全观测**
   （enforce 只对白名单内 task_type 真拦截，FP-4 灰度防误伤）。
2. **预算声明**：会话级 ``OPS_LLM_BUDGET_SESSION_TOKENS`` / 任务级
   ``OPS_LLM_BUDGET_TASK_TOKENS``，默认 0 = 不限制；非法/负值回退 0
   （承 ``_env_int`` 纪律）。任务级计数键 = TASK_TYPES 五档
   （answer/grader/extract/structured/summary）；未声明 task_type 的调用
   只受会话级约束。
3. **检查点**（Q1 单检查点）：check_budget 于 complete/stream 调用前
   判定（接线在 providers/base.py 统一入口）；**调用前预估 = 保守下限**
   （该档近 N 次 P50 折半，无样本用档级固定下限常量 · 是下限不是承诺），
   **调用后 usage 真实记账为准**（record_actual 复用 usage 末帧钩点，
   ContextVar 同源 app/llm/usage.py）。
4. **拦截语义**：超限在**下一次调用前拦截**，不截进行中流（FP-1）；
   enforce 拦截走 D2 声明降级链（providers/base.py walker），不直接拒。
5. **进程内边界**：会话/任务计数器进程内 dict + 锁（承 capability/budget.py
   先例形态）；**重启归零如实定性**（FP-5：热路径保护非持久配额，持久对账
   由 ops_llm_usage 表 + D5 指标面兜底；不伪造超额）。
6. **防假降级（U3）**：降级必带 ``degraded`` 标记跟数据走（degraded_meta），
   ok=True 也可能降级；链末端 ok=False+degraded 不伪造成功。

D5 指标面：Cost per Successful Task = Σ(成功 run LLM cost) / 成功任务数
（cost_per_successful_task 纯函数口径 + span metadata 产出面；
单价表在 model_catalog，**估算口径非对账**，缺单价 → unknown 不伪造 0）。
"""

from __future__ import annotations

import logging
import os
import threading
from collections import deque
from dataclasses import dataclass
from typing import Any

from app.llm.model_catalog import TASK_TYPES, estimate_cost
from app.llm.usage import LlmRunContext, current_run_context

logger = logging.getLogger(__name__)

# ---- env 键（非法值一律回退默认，承 delegation._env_int 纪律）----
ENV_SESSION_TOKENS = "OPS_LLM_BUDGET_SESSION_TOKENS"
ENV_TASK_TOKENS = "OPS_LLM_BUDGET_TASK_TOKENS"
ENV_MODE = "OPS_LLM_BUDGET_MODE"
ENV_ENFORCE_TASKS = "OPS_LLM_BUDGET_ENFORCE_TASKS"

MODE_OFF = "off"
MODE_OBSERVE = "observe"
MODE_ENFORCE = "enforce"
_MODES = frozenset({MODE_OFF, MODE_OBSERVE, MODE_ENFORCE})

#: 降级原因词表（D2 · degraded meta 的 reason 值）
DEGRADE_REASON_BUDGET_EXHAUSTED = "budget_exhausted"

#: 档级 token 预估固定下限（无样本时的保守下限 · 是下限不是承诺 · FP-1）
TIER_TOKEN_FLOOR: dict[str, int] = {
    "answer": 512,
    "grader": 256,
    "extract": 384,
    "structured": 384,
    "summary": 512,
}
DEFAULT_TOKEN_FLOOR = 128

#: P50 样本窗口（每档近 N 次调用 total tokens）
_SAMPLE_WINDOW = 32
#: P50 保守下限折扣（下限不是承诺：样本 P50 折半仍可能低于实际，宁可不拦
#: 正常调用也不误伤；真实约束由调用后记账兜底）
_P50_LOWER_FACTOR = 0.5

#: 追踪的会话桶上界（承 capability/budget.MAX_TRACKED_SESSIONS 先例：
#: key=run_id 会随长跑进程累积，无界 dict = 缓慢内存泄漏；超界按插入序淘汰）
MAX_TRACKED_SESSIONS = 512

_LOCK = threading.Lock()
#: session_key → 已记账 total tokens
_SESSIONS: dict[str, int] = {}
#: task_type（TASK_TYPES 五档）→ 已记账 total tokens
_TASKS: dict[str, int] = {}
#: task_type → 近 N 次 total tokens 样本（P50 预估用）
_SAMPLES: dict[str, deque[int]] = {}
_BLOCKED = 0
_WOULD_BLOCK = 0
_EVICTED_SESSIONS = 0

def _env_int(name: str, default: int) -> int:
    """读 env；非法 / 负值一律回退默认（承 step_contract._env_int 纪律）。"""
    raw = os.environ.get(name, "").strip()
    if not raw:
        return default
    try:
        n = int(raw)
    except ValueError:
        return default
    return n if n >= 0 else default


def budget_mode() -> str:
    """预算三档：off|observe|enforce；默认 off（零 diff）；非法值回退 off。"""
    raw = os.environ.get(ENV_MODE, "").strip().lower()
    return raw if raw in _MODES else MODE_OFF


def enforce_tasks() -> frozenset[str]:
    """enforce 白名单（逗号分隔 task_type）；默认空 = 全观测（FP-4）。"""
    raw = os.environ.get(ENV_ENFORCE_TASKS, "").strip()
    return frozenset(p.strip().lower() for p in raw.split(",") if p.strip())


def effective_mode(task_type: str | None) -> str:
    """该 task 的生效档：off→off；observe→observe；enforce→白名单内才真 enforce。"""
    mode = budget_mode()
    if mode != MODE_ENFORCE:
        return mode
    task = (task_type or "").strip().lower()
    return MODE_ENFORCE if task in enforce_tasks() else MODE_OBSERVE


def limits() -> dict[str, int]:
    """预算声明：默认 0 = 不限制；非法/负值回退 0。"""
    return {
        "session_tokens": _env_int(ENV_SESSION_TOKENS, 0),
        "task_tokens": _env_int(ENV_TASK_TOKENS, 0),
    }

def _session_key(ctx: LlmRunContext) -> str:
    """会话维度 = run_id（usage ContextVar 同源）；缺失 → 匿名共享桶（不因此
    放行：匿名调用照样计数，否则无上下文就成绕过捷径——承
    capability/budget.session_key 先例纪律）。"""
    return str(ctx.run_id or "")


def estimate_tokens(task_type: str | None) -> int:
    """调用前保守下限预估：有样本 = max(档级下限, 样本 P50 折半)；无样本 = 档级下限。

    预估是**保守下限不是承诺**（FP-1）：流式 token 不可预知，真实约束由
    调用后 record_actual 记账兜底；超限在下一次调用前拦截，不截流。
    """
    task = (task_type or "").strip().lower()
    floor = TIER_TOKEN_FLOOR.get(task, DEFAULT_TOKEN_FLOOR)
    with _LOCK:
        samples = list(_SAMPLES.get(task, ()))
    if not samples:
        return floor
    ordered = sorted(samples)
    p50 = ordered[len(ordered) // 2]
    return max(floor, int(p50 * _P50_LOWER_FACTOR))

@dataclass(frozen=True)
class BudgetVerdict:
    """预算检查点判定（调用前）。

    - ``allowed``：enforce 超限时 False（调用方走 D2 降级链，不直接拒答）；
      off/observe 恒 True。
    - ``would_block``：观测口径「若 enforce 会不会拦」（observe 灰度报告用）。
    - 计数快照（used/limit/estimated）进 span metadata（D5 产出面）。
    """

    allowed: bool
    mode: str
    would_block: bool = False
    reason: str = ""
    task_type: str = ""
    session_used: int = 0
    session_limit: int = 0
    task_used: int = 0
    task_limit: int = 0
    estimated_tokens: int = 0


_VERDICT_OFF = BudgetVerdict(allowed=True, mode=MODE_OFF)

def check_budget(task_type: str | None, *, ctx: LlmRunContext | None = None) -> BudgetVerdict:
    """预算检查点（Q1 单检查点 · 调用前判定 · 纯读计数不记账）。

    off → 零行为直通；observe → 只记 would_block 不拦；
    enforce（白名单内）超限 → allowed=False + reason=budget_exhausted，
    **下一次调用前拦截**（进行中流不截断），调用方走 D2 声明降级链。
    """
    mode = effective_mode(task_type)
    if mode == MODE_OFF:
        return _VERDICT_OFF

    run_ctx = ctx if ctx is not None else current_run_context()
    task = (task_type or "").strip().lower()
    lim = limits()
    estimated = estimate_tokens(task)
    with _LOCK:
        session_used = _SESSIONS.get(_session_key(run_ctx), 0)
        task_used = _TASKS.get(task, 0) if task in TASK_TYPES else 0

    task_limited = task in TASK_TYPES and lim["task_tokens"] > 0
    over_session = lim["session_tokens"] > 0 and (
        session_used + estimated > lim["session_tokens"]
    )
    over_task = task_limited and (task_used + estimated > lim["task_tokens"])
    over = over_session or over_task

    global _BLOCKED, _WOULD_BLOCK
    if over and mode == MODE_ENFORCE:
        with _LOCK:
            _BLOCKED += 1
        return BudgetVerdict(
            allowed=False,
            mode=mode,
            would_block=True,
            reason=DEGRADE_REASON_BUDGET_EXHAUSTED,
            task_type=task,
            session_used=session_used,
            session_limit=lim["session_tokens"],
            task_used=task_used,
            task_limit=lim["task_tokens"] if task_limited else 0,
            estimated_tokens=estimated,
        )
    if over:
        with _LOCK:
            _WOULD_BLOCK += 1
    return BudgetVerdict(
        allowed=True,
        mode=mode,
        would_block=over,
        reason=DEGRADE_REASON_BUDGET_EXHAUSTED if over else "",
        task_type=task,
        session_used=session_used,
        session_limit=lim["session_tokens"],
        task_used=task_used,
        task_limit=lim["task_tokens"] if task_limited else 0,
        estimated_tokens=estimated,
    )

def record_actual(
    task_type: str | None,
    total_tokens: int,
    *,
    ctx: LlmRunContext | None = None,
) -> None:
    """调用后真实记账（usage 末帧钩点调用 · 真实值覆盖预估 · FP-1）。

    off 模式零行为（不计数）。任务级只记 TASK_TYPES 五档键。
    """
    if budget_mode() == MODE_OFF:
        return
    tokens = max(0, int(total_tokens))
    if tokens == 0:
        return
    run_ctx = ctx if ctx is not None else current_run_context()
    task = (task_type or "").strip().lower()
    global _EVICTED_SESSIONS
    with _LOCK:
        key = _session_key(run_ctx)
        if key not in _SESSIONS:
            # 先淘汰再插入，保证字典长度有界（承 capability/budget 先例）
            while len(_SESSIONS) >= MAX_TRACKED_SESSIONS:
                _SESSIONS.pop(next(iter(_SESSIONS)), None)
                _EVICTED_SESSIONS += 1
            _SESSIONS[key] = 0
        _SESSIONS[key] += tokens
        if task in TASK_TYPES:
            _TASKS[task] = _TASKS.get(task, 0) + tokens
            buf = _SAMPLES.get(task)
            if buf is None:
                buf = deque(maxlen=_SAMPLE_WINDOW)
                _SAMPLES[task] = buf
            buf.append(tokens)

# ---- D2 · 防假降级标记（U3：标记跟数据走 · ok=True 也可能降级）----

META_DEGRADED = "degraded"
META_DEGRADE_REASON = "degrade_reason"
META_DEGRADE_CHAIN = "degrade_chain"


def degraded_meta(task_type: str | None, chain_used: list[str] | tuple[str, ...]) -> dict[str, Any]:
    """降级标记（承 capability/fallback B2 显式标记铁律）。

    每次降级必带：degraded=true + degrade_reason=budget_exhausted +
    degrade_chain=[原档, 实际走的档...]；链末端失败同样带标记 + ok=False
    （**不伪造成功** · SPEC FP-3）。
    """
    return {
        META_DEGRADED: True,
        META_DEGRADE_REASON: DEGRADE_REASON_BUDGET_EXHAUSTED,
        META_DEGRADE_CHAIN: [task_type or "", *[str(c) for c in chain_used]],
    }

# ---- D5 · 指标面：Cost per Successful Task（估算口径 · 非对账）----


@dataclass(frozen=True)
class UsageCostRow:
    """一次成功 run 内 LLM 调用的成本聚合入参（usage 账本行投影）。"""

    run_id: str | None
    model: str | None
    prompt_tokens: int
    completion_tokens: int


def cost_per_successful_task(
    rows: list[UsageCostRow] | tuple[UsageCostRow, ...],
) -> dict[str, Any]:
    """Cost per Successful Task = Σ(成功 run LLM cost) / 成功任务数。

    口径（SPEC §2 D5 锁死）：成功任务 = run 终态 done 的 run_id 集合（由调用方
    按 run_events 落盘面筛好后传入本函数 · 本函数只做成本聚合）；
    cost = usage token × 档级单价（model_catalog.MODEL_UNIT_PRICES ·
    **估算口径非对账**）；**任一贡献行缺单价 → 聚合标 unknown 不伪造 0**
    （FP-7 · 承「不写 0 假账」铁律）。
    """
    successful_runs: set[str | None] = set()
    total = 0.0
    unknown = False
    for row in rows:
        successful_runs.add(row.run_id)
        cost = estimate_cost(row.model, row.prompt_tokens, row.completion_tokens)
        if cost is None:
            unknown = True
        else:
            total += cost
    tasks = len(successful_runs)
    value: float | str = "unknown" if unknown else (total / tasks if tasks else 0.0)
    return {
        "cost_per_successful_task": value,
        "successful_tasks": tasks,
        "total_cost": "unknown" if unknown else total,
        "basis": "estimate_only_not_billing",
    }

# ---- 观测（记动作不记内容 · span metadata 失败不挡主流程）----


def report_span(metadata: dict[str, Any]) -> None:
    """预算/降级/成本观测进当前 span metadata（Langfuse 聚合面 · 不建新看板）。"""
    try:
        from app.ops.tracing import update_current_span_metadata

        update_current_span_metadata(metadata)
    except Exception:  # 观测面故障绝不拖垮主流程（承 delegation.audit 先例）
        pass


def report_verdict(verdict: BudgetVerdict) -> None:
    """检查点 verdict 进 span（budget_mode/would_block/used/limit/estimated）。"""
    if verdict.mode == MODE_OFF:
        return
    report_span(
        {
            "llm_budget_mode": verdict.mode,
            "llm_budget_would_block": verdict.would_block,
            "llm_budget_allowed": verdict.allowed,
            "llm_budget_session_used": verdict.session_used,
            "llm_budget_session_limit": verdict.session_limit,
            "llm_budget_task_used": verdict.task_used,
            "llm_budget_task_limit": verdict.task_limit,
            "llm_budget_estimated_tokens": verdict.estimated_tokens,
        }
    )


def report_estimated_cost(model: str | None, prompt_tokens: int, completion_tokens: int) -> None:
    """估算成本进 span metadata（缺单价 → unknown 不伪造 0 · FP-7）。"""
    cost = estimate_cost(model, prompt_tokens, completion_tokens)
    report_span({"llm_estimated_cost": cost if cost is not None else "unknown"})

def reset(*, key: str | None = None) -> None:
    """清空计数（测试**必须**每个用例前调一次：进程内全局状态，承先例）。"""
    global _BLOCKED, _WOULD_BLOCK
    with _LOCK:
        if key is not None:
            _SESSIONS.pop(key, None)
            return
        _SESSIONS.clear()
        _TASKS.clear()
        _SAMPLES.clear()
        _BLOCKED = 0
        _WOULD_BLOCK = 0


def snapshot() -> dict[str, Any]:
    """/runtime 观测用。**显式标出进程内边界**，不假装是全局计数（承先例）。"""
    with _LOCK:
        sessions = dict(_SESSIONS)
        tasks = dict(_TASKS)
        blocked = _BLOCKED
        would_block = _WOULD_BLOCK
        evicted = _EVICTED_SESSIONS
    return {
        "mode": budget_mode(),
        "enforce_tasks": sorted(enforce_tasks()),
        "limits": limits(),
        "sessions": sessions,
        "tasks": tasks,
        "blocked": blocked,
        "would_block": would_block,
        "tracked_sessions": len(sessions),
        "max_tracked_sessions": MAX_TRACKED_SESSIONS,
        "evicted_sessions": evicted,
        # 已知边界（FP-5）：进程内热路径保护 · 重启归零 · 非持久配额
        "scope": "process-local",
    }
