"""步骤契约（Q4 · consumes/produces）：解析、喂入前校验、确定性绑定。

说明书：docs/07-design/06_step-contract-and-recoverable-point-plan_v1_zh.md §1。

三条纪律（改这块前先读）：

1. **契约是显式声明出来的**。不声明就不校验——系统不替模型猜"这一步大概需要什么
   字段"。否则"一步都不派工人"就能满足所有断言，红线变成空真（与 R10
   「未声明契约的能力不得被推测性拦截」同一条纪律）。
2. **校验点在喂入前**。不合格即停，下游**零请求**。事后校验只能"发现错了"，
   挡不住"已经在错的数据上继续跑"。
3. **绑定是确定性的**。取哪些字段由模型声明，**怎么拼由代码决定**——
   不把插值权交给模型（与 capability ``args_map`` 只做键重命名同一条纪律）。

本模块零 LLM、零 IO，全部纯函数，便于红线直接打在它上面。
"""

from __future__ import annotations

from typing import Any

# 单步 declares 字段数上界：防止模型一次性声明几百个字段把绑定撑爆
MAX_FIELDS = 16

# 绑定进 rag/extract 文本的**单值**截断长度：长值污染 prompt
MAX_VALUE_CHARS = 200

# 上下文块的**整块**预算：单值截断挡不住"16 个字段 × 200 字"这种累加污染，
# 所以还要有总量闸。超了就按字段顺序丢弃尾部字段（宁少给，不超预算）。
MAX_CONTEXT_BLOCK_CHARS = 800


def _env_int(name: str, default: int, *, low: int, high: int) -> int:
    """读 env 覆盖；非法 / 越界一律回退默认（禁"配错就静默生效"）。"""
    import os

    raw = os.environ.get(name, "")
    try:
        value = int(str(raw).strip())
    except (TypeError, ValueError):
        return default
    return value if low <= value <= high else default


def max_value_chars() -> int:
    return _env_int("LG_RAG_STEP_CONTEXT_VALUE_CHARS", MAX_VALUE_CHARS, low=16, high=4000)


def max_block_chars() -> int:
    return _env_int("LG_RAG_STEP_CONTEXT_BLOCK_CHARS", MAX_CONTEXT_BLOCK_CHARS, low=64, high=16000)


# 上下文块的固定抬头：编排层生成，模型写不出来
CONTEXT_HEAD = "【上游产出】"

# 拦截原因（稳定词表，与 capability 的七个错误码同规格：不新增码，用 detail 区分）
BLOCKED_PREDECESSOR_FAILED = "predecessor_failed"
BLOCKED_CONTRACT_MISSING = "contract_missing_field"
BLOCKED_PREFIX_TOUCH = "prefix_touch_required"

BLOCKED_REASONS = (
    BLOCKED_PREDECESSOR_FAILED,
    BLOCKED_CONTRACT_MISSING,
    BLOCKED_PREFIX_TOUCH,
)

# 只有这个原因需要人来批：它意味着"要满足新计划，得重跑一个已执行的步骤"
HITL_REASONS = frozenset({BLOCKED_PREFIX_TOUCH})

_LABELS = {
    BLOCKED_PREDECESSOR_FAILED: "前驱步骤失败，本步未执行",
    BLOCKED_CONTRACT_MISSING: "前驱输出缺少本步 consumes 声明的字段，本步未执行",
    BLOCKED_PREFIX_TOUCH: "本步需要重跑已执行的前缀步骤才能满足，需人工确认",
}


def label_of(reason: str) -> str:
    """拦截原因 → 人类可读理由（写进错误终态）。"""
    return _LABELS.get(reason, f"步骤契约拦截（{reason}），本步未执行")


def needs_hitl(reason: str) -> bool:
    """该拦截是否需要人工确认（Q8 §2.4）。"""
    return reason in HITL_REASONS


# ---------------------------------------------------------------------------
# 声明解析（宽容：解析不出来就当作没声明，不抛、不整单作废）
# ---------------------------------------------------------------------------


def _clean_fields(raw: Any) -> list[str]:
    """把任意输入收拾成字段名列表；去重保序；超上限截断。"""
    if not isinstance(raw, list):
        return []
    out: list[str] = []
    for item in raw:
        token = str(item or "").strip()
        if not token or token in out:
            continue
        out.append(token)
        if len(out) >= MAX_FIELDS:
            break
    return out


def normalize_produces(raw: Any) -> list[str]:
    """``produces``：本步承诺产出的字段名。"""
    return _clean_fields(raw)


def normalize_consumes(raw: Any) -> dict[str, list[str]]:
    """``consumes``：``{前驱别名: [字段名...]}``。非 dict 一律 {}。"""
    if not isinstance(raw, dict):
        return {}
    out: dict[str, list[str]] = {}
    for alias, fields in raw.items():
        token = str(alias or "").strip()
        cleaned = _clean_fields(fields)
        if not token or not cleaned:
            continue
        out[token] = cleaned
        if len(out) >= MAX_FIELDS:
            break
    return out


def remap_consumes(
    consumes: dict[str, list[str]], alias_map: dict[str, str]
) -> dict[str, list[str]]:
    """把 consumes 的键从旧别名换到新别名（重规划时后缀被强制重命名）。"""
    out: dict[str, list[str]] = {}
    for alias, fields in consumes.items():
        target = alias_map.get(alias)
        if not target:
            continue
        bucket = out.setdefault(target, [])
        for field in fields:
            if field not in bucket:
                bucket.append(field)
    return out


def resolve_consumes(
    consumes: dict[str, list[str]],
    alias_to_sid: dict[str, list[str]],
) -> dict[str, list[str]]:
    """别名 → 已签发的 subtask_id。

    与 ``depends_on`` 同规格：别名指向多个 / 零个签发项 → 该别名整体丢弃，
    不猜。返回 ``{subtask_id: [字段...]}``。
    """
    out: dict[str, list[str]] = {}
    for alias, fields in consumes.items():
        targets = alias_to_sid.get(alias) or []
        if len(targets) != 1:
            continue
        sid = targets[0]
        bucket = out.setdefault(sid, [])
        for field in fields:
            if field not in bucket:
                bucket.append(field)
    return out


def consumes_implied_deps(consumes_by_sid: dict[str, list[str]]) -> list[str]:
    """``consumes`` 隐含依赖：吃了谁的产出就必须等谁。"""
    return list(consumes_by_sid.keys())


# ---------------------------------------------------------------------------
# 校验（喂入前）
# ---------------------------------------------------------------------------


def output_fields(output: Any) -> dict | None:
    """可校验的产出。

    只有 dict 才有"字段"；str / list / None 一律返回 ``None`` ⇒ **不校验**
    （第 1 条纪律：不替模型猜）。rag/extract 的产出是自由文本，本就没有字段
    可言，声明 ``produces`` 也不该被兑现性校验。
    """
    if isinstance(output, dict):
        return output
    return None


def missing_fields(output: Any, fields: list[str]) -> list[str]:
    """output 里缺哪些字段。output 不可校验时返回空（不判缺）。"""
    mapping = output_fields(output)
    if mapping is None:
        return []
    return [f for f in fields if f not in mapping]


def _missing_field_detail(head: str, dep: str, output: Any) -> str:
    """缺字段拦截 detail：附前驱**实际可用字段清单**（sorted keys）。

    supervisor-replan-error-feedback（实测 run cb2548）：被拦步的错误终态
    会反哺重规划 prompt——把「猜字段名」变成「从清单选字段名」。能走到
    这里说明 missing 非空 ⇒ output_fields 判过 output 是 dict（非 dict
    不校验、不替模型猜，既有语义不变）。
    """
    available = sorted(str(key) for key in (output_fields(output) or {}))
    return (
        f"{head}；前驱 {dep} 实际产出字段 {available}"
        "（声明的字段不存在，请从实际产出字段中选择）"
    )


def gate(
    *,
    row: dict,
    terminals: dict[str, dict],
    by_id: dict[str, dict],
    prefix_ids: frozenset[str],
) -> tuple[str | None, str]:
    """派工前的步闸门。返回 ``(reason, detail)``；``reason`` 为 None 表示放行。

    判定顺序（先挡最贵的）：
    1. 前驱失败终态 → ``predecessor_failed``（Q4 缺陷二的字面病灶）；
    2. ``consumes`` 字段在产出里找不到 → 前驱在不可变前缀内 ⇒ ``prefix_touch_required``
       （Q8：要满足它得改历史，交人），否则 ``contract_missing_field``；
    3. 前驱自己声明的 ``produces`` 没兑现 → 同上分类。
    """
    deps = [str(d) for d in (row.get("depends_on") or [])]
    consumed = row.get("consumes_resolved") or {}
    watched = sorted(set(deps) | set(consumed.keys()))
    for dep in watched:
        term = terminals.get(dep)
        if term is None:
            continue
        if "error" in term:
            return BLOCKED_PREDECESSOR_FAILED, f"前驱 {dep} 为失败终态"

    for dep in sorted(consumed.keys()):
        term = terminals.get(dep)
        if term is None:
            continue
        missing = missing_fields(term.get("output"), list(consumed[dep] or []))
        if missing:
            reason = BLOCKED_PREFIX_TOUCH if dep in prefix_ids else BLOCKED_CONTRACT_MISSING
            head = f"前驱 {dep} 输出缺少字段 {missing}"
            return reason, _missing_field_detail(head, dep, term.get("output"))

    for dep in deps:
        promised = list((by_id.get(dep) or {}).get("produces") or [])
        if not promised:
            continue
        term = terminals.get(dep)
        if term is None:
            continue
        missing = missing_fields(term.get("output"), promised)
        if missing:
            reason = BLOCKED_PREFIX_TOUCH if dep in prefix_ids else BLOCKED_CONTRACT_MISSING
            head = f"前驱 {dep} 未兑现自己声明的 produces {missing}"
            return reason, _missing_field_detail(head, dep, term.get("output"))
    return None, ""


# ---------------------------------------------------------------------------
# 绑定（确定性渲染）
# ---------------------------------------------------------------------------


def _render_value(value: Any, *, limit: int) -> str:
    text = value if isinstance(value, str) else str(value)
    if len(text) > limit:
        return text[: limit - 1] + "…"
    return text


def collect_values(
    *,
    consumes_by_sid: dict[str, list[str]],
    terminals: dict[str, dict],
    sid_to_alias: dict[str, str],
) -> dict[str, dict[str, Any]]:
    """取待绑定的值：``{dep_sid: {field: value}}``，只收产出里真实存在的。"""
    out: dict[str, dict[str, Any]] = {}
    for dep in sorted(consumes_by_sid):
        term = terminals.get(dep)
        if term is None:
            continue
        mapping = output_fields(term.get("output"))
        if mapping is None:
            continue
        vals = {f: mapping[f] for f in (consumes_by_sid[dep] or []) if f in mapping}
        if vals:
            out[dep] = vals
    return out


def bind_args(args: Any, values: dict[str, dict[str, Any]]) -> dict:
    """tool 步：按字段名注入 args（**覆盖** planner 写死的占位值）。

    为什么必须覆盖而不是"缺了才补"：占位值就是缺陷一的来源——planner 写了个
    看起来对的字符串，不覆盖的话下游拿到的还是那个字符串，契约等于没接上。
    """
    base = dict(args) if isinstance(args, dict) else {}
    for dep in sorted(values):
        for field, value in values[dep].items():
            base[field] = value
    return base


def render_context_block(
    values: dict[str, dict[str, Any]], *, sid_to_alias: dict[str, str]
) -> tuple[str, list[str]]:
    """rag / extract 步：编排层生成的固定格式上下文块。

    返回 ``(块文本, 实际进块的字段列表)``。两层截断：
    **单值**截断（防一个超长值吃掉整块）+ **整块**预算（防多字段累加污染）。
    触发整块预算时**按字段顺序丢尾部**，并把丢掉的字段返回去——
    静默丢字段等于给模型一份看起来完整但不完整的数据。
    """
    limit = max_value_chars()
    budget = max_block_chars()
    lines = [CONTEXT_HEAD]
    included: list[str] = []
    used = len(CONTEXT_HEAD)
    for dep in sorted(values):
        alias = sid_to_alias.get(dep) or dep
        for field, value in values[dep].items():
            rendered = _render_value(value, limit=limit)
            line = f"{alias}.{field} = {rendered}"
            if used + len(line) + 1 > budget and included:
                break
            lines.append(line)
            included.append(f"{dep}:{field}")
            used += len(line) + 1
    return "\n".join(lines), included


def bind_input(text: str, values: dict[str, dict[str, Any]], **kw: Any) -> tuple[str, list[str]]:
    """rag / extract 步：在 input 尾部追加上下文块（不改写用户问句本身）。

    返回 ``(新文本, 实际绑定的字段)``；末尾追加的是被**整块预算挤掉**的字段名，
    便于观测"其实没给全"。
    """
    if not values:
        return text, []
    block, included = render_context_block(values, **kw)
    return f"{text}\n\n{block}", included


def dropped_fields(values: dict[str, dict[str, Any]], included: list[str]) -> list[str]:
    """声明了但被整块预算挤掉的字段（观测用：不能假装都给到了）。"""
    wanted = bound_field_names(values)
    return [name for name in wanted if name not in set(included)]


def bound_field_names(values: dict[str, dict[str, Any]]) -> list[str]:
    """已绑定字段名（观测用）。"""
    out: list[str] = []
    for dep in sorted(values):
        for field in sorted(values[dep]):
            name = f"{dep}:{field}"
            if name not in out:
                out.append(name)
    return out
