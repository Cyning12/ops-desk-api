"""结果契约校验（P0-1）：**这次调用的成功长什么样**。

为什么要有这个模块
------------------
没有它，工具返回缺字段、字段类型变了、列表为空，**一律 ok=True**。
于是「查到 0 条」和「被限流返回空」在系统里长得一模一样——Agent 拿着一个
残缺/为空的结果继续规划，整条链路从这一步开始就错了，而且没人报错。

这是八问里 Q2/Q4 的根因，也是当时盘点出的**唯一"错了还报成功"的口子**。

契约形状（manifest 里声明）
--------------------------
.. code-block:: yaml

    output_schema:
      required: ["$.data.ticketId", "$.data.url"]   # 必须存在且非 null
      min_items: {"$.data.items": 1}                # 列表最小条数
      empty_is_suspicious: true                     # 命中"空"→ 判失败，不静默成功

失败口径
--------
稳定错误码词表是**七个、不增**（见 ``errors.py`` 的设计约束），所以新增失败
**不新造码**，落在既有的 ``upstream_error`` 上、用 detail 区分：

    ``upstream_error: result_contract: 缺字段 $.data.ticketId``

理由：结果不符合契约是**下游的问题**，语义上就是 upstream_error；模型侧按
"换参数/换工具/上报"处理，与既有口径一致。

空结果：默认**不判失败**，但必须**显式标记**
--------------------------------------------
``empty_is_suspicious`` 默认 false —— 一刀切把空结果判失败会误伤正常查无。
但空结果必须留下 ``meta["result_empty"] = True`` 这个显式状态，
让编排层能区分"确实没有"与"可疑的空"，而不是两者都长成 ok=True。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.ops.capability.jsonpath import MISSING, jsonpath_get

#: detail 前缀（便于日志/指标按契约类问题聚合）
PREFIX = "result_contract"


@dataclass(frozen=True)
class Verdict:
    """一次结果校验的结论。"""

    ok: bool = True
    reason: str = ""
    #: 命中了"空"（None / "" / [] / {}）
    empty: bool = False
    #: 空且被声明为可疑（``empty_is_suspicious`` 且命中空）
    suspicious: bool = False
    #: 契约实际校验了哪些路径（可观测：没声明契约的能力这里为空）
    checked: tuple[str, ...] = field(default_factory=tuple)

    def error_detail(self) -> str:
        """失败时的 detail（形如 ``result_contract: 缺字段 $.x``）。"""
        return f"{PREFIX}: {self.reason}" if self.reason else PREFIX


def _is_empty(value: Any) -> bool:
    """什么叫"空"——**None 与缺失不算空**，那是"没这个字段"，由 required 管。"""
    if value is None or value is MISSING:
        return False
    if isinstance(value, (str, bytes)):
        return len(value) == 0
    if isinstance(value, (list, tuple, dict, set)):
        return len(value) == 0
    return False


def validate(contract: dict[str, Any] | None, payload: Any) -> Verdict:
    """校验 ``payload`` 是否符合 ``contract``。

    ``contract is None`` → 不校验（钉死行为：未声明契约的能力**维持原样**，
    不做任何推测性拦截——契约是**显式声明**出来的，不是系统替你猜的）。
    """
    if not contract:
        return Verdict()

    required = contract.get("required") or []
    min_items = contract.get("min_items") or {}
    empty_is_suspicious = bool(contract.get("empty_is_suspicious", False))

    checked: list[str] = []
    empty_hit: list[str] = []

    for expr in required if isinstance(required, (list, tuple)) else []:
        expr_s = str(expr)
        checked.append(expr_s)
        got = jsonpath_get(payload, expr_s)
        if got is MISSING:
            return Verdict(ok=False, reason=f"缺字段 {expr_s}", checked=tuple(checked))
        if got is None:
            return Verdict(ok=False, reason=f"字段为 null {expr_s}", checked=tuple(checked))
        if _is_empty(got):
            empty_hit.append(expr_s)

    if isinstance(min_items, dict):
        for expr_s, want in min_items.items():
            checked.append(str(expr_s))
            got = jsonpath_get(payload, str(expr_s))
            if got is MISSING:
                return Verdict(
                    ok=False,
                    reason=f"缺字段 {expr_s}",
                    checked=tuple(checked),
                )
            if not isinstance(got, list):
                return Verdict(
                    ok=False,
                    reason=f"{expr_s} 不是列表（{type(got).__name__}）",
                    checked=tuple(checked),
                )
            try:
                need = int(want)
            except (TypeError, ValueError):
                return Verdict(
                    ok=False,
                    reason=f"min_items 配置非法 {expr_s}={want!r}",
                    checked=tuple(checked),
                )
            if len(got) < need:
                # 条数不足**同时**是"空/少"的信号
                if len(got) == 0:
                    empty_hit.append(str(expr_s))
                return Verdict(
                    ok=False,
                    reason=f"{expr_s} 条数={len(got)} < {need}",
                    empty=len(got) == 0,
                    checked=tuple(checked),
                )

    if empty_hit:
        verdict = Verdict(
            ok=not empty_is_suspicious,
            reason=(f"空结果可疑 {','.join(empty_hit)}" if empty_is_suspicious else ""),
            empty=True,
            suspicious=empty_is_suspicious,
            checked=tuple(checked),
        )
        return verdict

    return Verdict(checked=tuple(checked))
