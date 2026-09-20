"""降级链（P1 · 八问 Q3 下半）。

**与熔断的分工（这是本模块存在的理由）**

============  ===========================================  ======================
              熔断                                         降级链
============  ===========================================  ======================
回答的问题    这个下游**还打得通吗**                        打不通时**给什么**
要不要业务知识  不要：只判通不通，任何能力一样                要：每个能力"退到哪一步"不同
框架能替业务定吗  能（阈值/时长是运维参数）                    **不能**
失败形态      明确失败（``circuit_open``）                  **成功但降级**（ok + degraded）
============  ===========================================  ======================

所以切分是硬的：

- **框架做**（本模块）：什么时候降级、降级了怎么标记、链条多深、怎么观测、缓存怎么存。
- **业务做**（manifest 声明，走 Git + PR + 人闸）：**降级成什么**。

框架**绝不猜**降级结果。反例（不要做）：工具失败时"自动换一个相似工具"、
或"返回上一次的结果"。前者是猜；后者可能把三小时前的数据当成实时数据回答——
**静默降级比明确报错危险得多**，因为不会有人来查。

四条硬边界
----------
**B1 · 写能力永不降级。** 单据没建就是没建，不存在"降级成建了一半"。
写操作失败必须**看得见**，否则会出现"用户以为提交了、实际没提交"的最坏结果。

**B2 · 降级结果必须显式标记。** ``meta.degraded`` + 来源 + 动作 + 时间。
不标记的话编排层分不清真实结果与降级结果，拿缓存当实时回答是静默错误。

**B3 · 链条有界。** ``max_depth``（默认 2）+ ``visited`` 防环。
``A → B → C → A`` 会成环，``A → B → C → …`` 会拖长延迟。

**B4 · 只有"下游不可用"才降级。** 参数错 / 没权限 / 业务码失败 / 契约不符
降级没有意义——换个接口，参数还是错的。见 :func:`trigger_of`。

触发条件只认四类（全是**结构化**判定，不解析错误文案——文案一改就静默失效）：
``transport``（超时/连接失败/不响应）、``5xx``、``429``、``circuit_open``。
"""

from __future__ import annotations

import hashlib
import json
import threading
import time
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from app.ops.capability.errors import (
    CAUSE_HTTP_STATUS,
    CAUSE_TRANSPORT,
    TRIP_HTTP_STATUS_MIN,
    TRIP_HTTP_STATUSES,
)
from app.ops.capability.types import WRITE_SIDE_EFFECTS

# ---- 触发条件（框架判定的**全部**词表；业务只能从中挑子集）----
TRIGGER_TRANSPORT = "transport"  # 超时 / 连接失败 / DNS / 不响应
TRIGGER_5XX = "5xx"
TRIGGER_429 = "429"
TRIGGER_CIRCUIT_OPEN = "circuit_open"  # 熔断中（下游已知不可用，正是降级的时机）

TRIGGERS: frozenset[str] = frozenset(
    {TRIGGER_TRANSPORT, TRIGGER_5XX, TRIGGER_429, TRIGGER_CIRCUIT_OPEN}
)
#: 声明了 action 但没写 ``on`` 时的默认：全部触发条件。
#: 窄化是业务的选择，放宽不是——框架不接受"业务发明一种新的不可用"。
DEFAULT_ON: tuple[str, ...] = (
    TRIGGER_TRANSPORT,
    TRIGGER_5XX,
    TRIGGER_429,
    TRIGGER_CIRCUIT_OPEN,
)

# ---- 降级动作 ----
ACTION_NONE = "none"  # **默认**：不降级，明确失败
ACTION_CAPABILITY = "capability"  # 换成另一个能力
ACTION_CACHE = "cache"  # 返回上次成功结果（带 TTL）
ACTION_STATIC = "static"  # 返回声明好的静态兜底值

ACTIONS: frozenset[str] = frozenset(
    {ACTION_NONE, ACTION_CAPABILITY, ACTION_CACHE, ACTION_STATIC}
)
DEFAULT_ACTION = ACTION_NONE

DEFAULT_MAX_DEPTH = 2
MAX_DEPTH_CEILING = 5
DEFAULT_TTL_SECONDS = 300

# ---- 缓存（action=cache 的存储）----
# 进程内、有界（与 budget._SESSIONS 同一纪律：按 key 累积的字典必须设上界）。
_CACHE_MAX_ENTRIES = 512
_LOCK = threading.Lock()
_CACHE: dict[str, tuple[float, Any]] = {}


@dataclass(frozen=True)
class Chain:
    """一次调用链上的降级进度（防环 + 限深）。

    ``depth=0`` 表示**还没降级**（正在跑原始能力）。
    """

    depth: int = 0
    visited: frozenset[str] = frozenset()

    def next(self, target: str, *, max_depth: int) -> Chain | None:
        """能不能再退一级到 ``target``；不能则返回 ``None``（不是异常——
        降级失败应当表现为**原始的明确失败**，不是一个新错误）。"""
        if not target or target in self.visited:
            return None  # 成环 / 空目标
        if self.depth + 1 > max_depth:
            return None  # 深度到顶（B3）
        return Chain(depth=self.depth + 1, visited=self.visited | {target})


def plan_of(spec: Any) -> dict[str, Any]:
    """取能力声明的降级计划；未声明 → ``{}``（即 action=none）。"""
    raw = getattr(spec, "fallback", None)
    return dict(raw) if isinstance(raw, dict) else {}


def action_of(spec: Any) -> str:
    action = str(plan_of(spec).get("action") or DEFAULT_ACTION).strip()
    return action if action in ACTIONS else DEFAULT_ACTION


def trigger_of(
    exc: BaseException | None = None, *, blocked: str | None = None
) -> str | None:
    """这次失败属不属于「下游不可用」；不属于 → ``None``（**不降级**，B4）。

    判定**只用结构化字段**（异常上的 ``cause`` / ``http_status``），不解析文案：
    文案一改，降级就会静默变成"永远不降级"或"什么都降级"。
    """
    if blocked == "circuit":
        return TRIGGER_CIRCUIT_OPEN
    if exc is None:
        return None
    cause = getattr(exc, "cause", None)
    if cause == CAUSE_TRANSPORT:
        return TRIGGER_TRANSPORT
    if cause == CAUSE_HTTP_STATUS:
        status = getattr(exc, "http_status", None)
        if not isinstance(status, int):
            # 标了状态码层却没给状态码：不敢判定，按"不降级"处理（宁可少降）
            return None
        if status >= TRIP_HTTP_STATUS_MIN:
            return TRIGGER_5XX
        if status in TRIP_HTTP_STATUSES:
            return TRIGGER_429
    return None


def should_degrade(spec: Any, *, trigger: str | None) -> bool:
    """该不该降级（B1 写能力 + B4 触发条件 + 声明检查）。

    注意这里**不判断深度**——深度是链条属性，由 :meth:`Chain.next` 管。
    """
    if trigger is None or trigger not in TRIGGERS:
        return False
    # B1：写能力永不降级。加载期 V12 已拒，这里再守一次——
    # CapabilitySpec 可以在代码里直接构造，绕开 manifest 校验。
    if str(getattr(spec, "side_effect", "") or "") in WRITE_SIDE_EFFECTS:
        return False
    if action_of(spec) == ACTION_NONE:
        return False
    return trigger in _triggers_of(spec)


def _triggers_of(spec: Any) -> frozenset[str]:
    """声明的触发条件集合；没写 → 全集（窄化是业务的选择，放宽不是）。

    字段名用 ``triggers`` 而不是 ``on``：YAML 1.1 会把裸键 ``on`` 解析成布尔
    ``True``（``on/off/yes/no`` 都是），写成 ``on: [...]`` 的清单会被读成
    ``{True: [...]}``——声明静默失效，且报错指向一个看起来不存在的字段。
    """
    raw = plan_of(spec).get("triggers")
    if not isinstance(raw, list) or not raw:
        return frozenset(DEFAULT_ON)
    return frozenset(str(x).strip() for x in raw if str(x).strip() in TRIGGERS)


def max_depth_of(spec: Any) -> int:
    raw = plan_of(spec).get("max_depth", DEFAULT_MAX_DEPTH)
    try:
        n = int(raw)
    except (TypeError, ValueError):
        return DEFAULT_MAX_DEPTH
    return max(1, min(MAX_DEPTH_CEILING, n))


def ttl_of(spec: Any) -> int:
    raw = plan_of(spec).get("ttl_seconds", DEFAULT_TTL_SECONDS)
    try:
        n = int(raw)
    except (TypeError, ValueError):
        return DEFAULT_TTL_SECONDS
    return n if n > 0 else DEFAULT_TTL_SECONDS


def map_args(args: Any, args_map: Any) -> Any:
    """按 ``args_map``（**目标参数名 ← 源参数名**）改写参数。

    刻意只做**键改名**，不支持模板：模板会把"降级"变成一门小语言，
    而降级的参数语义必须由业务在清单里想清楚。改不动时原样传——
    目标能力有自己的 args_schema，不兼容会被它自己拒绝（失败可见）。
    """
    if not isinstance(args_map, dict) or not args_map:
        return args
    if not isinstance(args, dict):
        return args
    return {
        str(dst): args.get(str(src)) for dst, src in args_map.items() if str(src) in args
    }


# ---------------- action=cache 的存储 ----------------


def _cache_key(capability_id: str, *, args: Any, ctx: dict[str, Any] | None) -> str:
    """缓存分桶 = (能力, 租户, 参数)。

    **不能只按能力 id 分桶**：``oa.todo.mine`` 这类个人数据，只按 id 缓存会让
    A 用户的待办出现在 B 用户的回答里——那是一次跨租户数据泄漏，
    而它长得完全像一次"成功的降级"。
    """
    tenant = str((ctx or {}).get("tenant_id") or (ctx or {}).get("_host_tenant") or "")
    try:
        canon = json.dumps(args, ensure_ascii=False, sort_keys=True, default=str)
    except TypeError:
        canon = str(args)
    digest = hashlib.sha256(f"{tenant}|{canon}".encode()).hexdigest()[:16]
    return f"{capability_id}:{digest}"


def remember(
    capability_id: str, output: Any, *, args: Any, ctx: dict[str, Any] | None
) -> None:
    """记下**真实成功**的结果（降级结果不入库，否则陈旧数据会被当成新结果再降一次）。"""
    key = _cache_key(capability_id, args=args, ctx=ctx)
    with _LOCK:
        _CACHE.pop(key, None)  # 重插以保证 FIFO 顺序（dict 保序）
        _CACHE[key] = (time.time(), output)
        while len(_CACHE) > _CACHE_MAX_ENTRIES:
            _CACHE.pop(next(iter(_CACHE)))


def recall(
    capability_id: str,
    *,
    args: Any,
    ctx: dict[str, Any] | None,
    ttl_seconds: int,
) -> tuple[Any, float] | None:
    """取上次成功结果；过期或没有 → ``None``（**过期即不降级**，陈旧数据更危险）。"""
    key = _cache_key(capability_id, args=args, ctx=ctx)
    with _LOCK:
        hit = _CACHE.get(key)
    if hit is None:
        return None
    stored_at, output = hit
    if time.time() - stored_at > float(ttl_seconds):
        return None
    return output, stored_at


def reset() -> None:
    """测试用：清空缓存（进程内全局状态，与注册表 / 配额同源）。"""
    with _LOCK:
        _CACHE.clear()


def cache_snapshot() -> dict[str, Any]:
    """/runtime 观测：缓存里有多少条、上界多少。"""
    with _LOCK:
        return {
            "entries": len(_CACHE),
            "max_entries": _CACHE_MAX_ENTRIES,
            "scope": "process-local",
        }


def iso(ts: float | None = None) -> str:
    return datetime.fromtimestamp(ts if ts is not None else time.time(), tz=UTC).isoformat()
