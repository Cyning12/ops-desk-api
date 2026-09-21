"""Capability Gateway · 契约类型（SPEC §3）。

进程内**注册表**条目（非跨进程「注册中心」）。``args_schema`` 仅描述参数形态；
**业务不变量不进 schema**（见 CODING P-16）：例如「这个金额能不能批」
「这个人有没有权给这个部门报」属于业务不变式，应落在 Policy 或 adapter 代码里。

``risk_level`` 与 ``side_effect`` 是**两个维度**，不可互相代理：
- ``risk_level``：做错之后的**危险程度**（low / medium / high）
- ``side_effect``：这次调用**有没有副作用**（none / read / write / irreversible）

历史缺口：早期只有 ``risk_level``，导致「medium + write」一档在 Policy 下
完全放行。``side_effect`` 是写操作闸（与 HITL）的唯一挂钩点，必须在能力
**第一次注册时**就声明——事后补需要重新盘每个接口。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

# 词表（manifest 校验与 Policy 共用）
RISK_LEVELS: frozenset[str] = frozenset({"low", "medium", "high"})
SIDE_EFFECTS: frozenset[str] = frozenset(
    {"none", "read", "write", "irreversible"}
)
WRITE_SIDE_EFFECTS: frozenset[str] = frozenset({"write", "irreversible"})

# 密级序（低 → 高）。可见集求值时按序比较：principal 需 ≥ capability。
CLASSIFICATION_ORDER: tuple[str, ...] = (
    "public",
    "internal",
    "confidential",
    "secret",
)
CLASSIFICATION_LEVELS: frozenset[str] = frozenset(CLASSIFICATION_ORDER)
# 未识别身份时的密级。取 internal 而非 public：企业内网默认口径，
# 同时保证 confidential/secret 能力对匿名主体仍然不可见（fail-closed）。
DEFAULT_CLASSIFICATION = "internal"

# 可见性声明里的通配
VISIBILITY_ANY = "all"


def classification_rank(value: str) -> int:
    """密级序号；未知值按最低（public）处理，不抛异常。"""
    text = str(value or "").strip().lower()
    return (
        CLASSIFICATION_ORDER.index(text) if text in CLASSIFICATION_LEVELS else 0
    )


@dataclass(frozen=True)
class Principal:
    """已认证主体（谁在调）。

    **必须由代码从会话/请求上下文构造，不取自模型产出**——与
    ``tenant_scoped`` 的租户谓词同一条纪律（见 policy._tenant_predicate）。
    """

    user_id: str = ""
    tenant_id: str = ""
    departments: frozenset[str] = frozenset()
    roles: frozenset[str] = frozenset()
    projects: frozenset[str] = frozenset()
    classification_max: str = DEFAULT_CLASSIFICATION

    def is_anonymous(self) -> bool:
        return not (self.user_id or self.tenant_id or self.departments or self.roles)


@dataclass(frozen=True)
class CapabilitySpec:
    """进程内注册表条目（SPEC §3.1）。"""

    capability_id: str
    kind: str
    description: str
    args_schema: dict[str, Any] | None = None
    tags: tuple[str, ...] = ()
    risk_level: str = "low"  # low | medium | high
    enabled: bool = True
    # True：invoke 须 ctx 含租户谓词（tenant_id / _host_tenant）；缺则拒
    tenant_scoped: bool = False
    # ---- 副作用与写操作闸（H4）----
    # none | read | write | irreversible
    side_effect: str = "none"
    # 面向模型的**选择依据**：何时该用 / 何时不该用。
    # 这是「模型能不能选中」的关键，不是给人看的注释。
    when_to_use: str = ""
    when_not_to_use: str = ""
    # kind=http 时的绑定声明（method / base_url 环境变量名 / path / auth 凭证名 /
    # *_map 模板 / idempotency_key / tenant_param / success_when / error_map）。
    # **只存引用（环境变量名、凭证名），不存密钥值。**
    http: dict[str, Any] | None = None
    # 高危写需单次人工确认（加载期强校验：write/irreversible/high 必须为 True）
    hitl_required: bool = False
    # 单次确认时冻结进快照的字段（复核「参数变了则旧审批作废」用）
    hitl_snapshot_fields: tuple[str, ...] = ()
    # 副作用回执捕获路径（JSONPath 子集），副作用以收据为真
    receipt_capture: tuple[str, ...] = ()
    # ---- 结果契约（P0-1）----
    # 声明"这次调用的成功**长什么样**"：必填字段 / 最小条数 / 空结果是否可疑。
    # 没有它，工具返回缺字段、类型变了、列表为空**一律 ok=True**——
    # 而"查到 0 条"和"被限流返回空"在系统里长得一模一样，会污染整条链路。
    # 形状见 result_contract.py；加载期校验见 manifest V10。
    output_schema: dict[str, Any] | None = None
    # 可见性声明（departments / roles / projects / classification_max）。
    # None = **未声明**：不受可见性规则裁剪（沿用 CapabilityFilter 语义），
    # 但会在 span 上留 ``visibility_undeclared`` 痕，让遗漏可度量。
    # kind=http 的**对外接入**能力必须声明（加载期 V9）。
    visibility: dict[str, Any] | None = None
    # ---- 降级声明（P1 · 八问 Q3 下半）----
    # 「打不通时给什么」是**业务决策**，必须由清单声明（走 Git + PR + 人闸），
    # 框架只忠实执行，绝不自己发明降级结果。形状见 fallback 模块：
    #   {on: [transport, 5xx, 429, circuit_open], action: none|capability|cache|static,
    #    capability_id, args_map, max_depth, ttl_seconds, value}
    # ``None`` = 未声明 = **不降级**，明确失败——让"不降级"成为需要显式改掉的默认。
    fallback: dict[str, Any] | None = None


@dataclass(frozen=True)
class CapabilityFilter:
    """可见集合裁剪（SPEC §3.3 · v0 最小）。

    ``tags_any`` 与 ``allow_tags_any`` **方向相反，别搞混**：

    | 字段 | 方向 | 语义 |
    |---|---|---|
    | ``tags_any`` | **收窄** | 只看带这些 tag 的能力（交集） |
    | ``allow_tags_any`` | **放宽** | 命中这些 tag 的能力**豁免 ``kinds`` 裁剪** |

    为什么需要 ``allow_tags_any``：新 kind（如 ``http``）一次性放开风险大，
    按**业务域**逐批放开更稳，而"域"天然落在 ``tags`` 上。用法::

        CapabilityFilter(kinds={"local_fn"}, allow_tags_any={"oa"})

    → 存量 local_fn 照旧可见；命中 ``oa`` 标签的 http 能力也放行；
      新增一个域只是往集合里加一个 tag，不动 kind 语义。
    """

    node_role: str | None = None
    mode: str | None = None
    tags_any: frozenset[str] | None = None
    kinds: frozenset[str] | None = None
    # 命中任一 tag → 豁免 kinds 裁剪（按域逐批放开新 kind 用）
    allow_tags_any: frozenset[str] | None = None
    deny_high_risk: bool = False
    # 与 deny_high_risk 对称：可见集裁剪阶段就把写能力挡在模型视野之外
    deny_write: bool = False


@dataclass
class CapabilityResult:
    """统一 invoke 结果（SPEC §3.2）。"""

    ok: bool
    output: Any = None
    error: str | None = None
    capability_id: str = ""
    duration_ms: float | None = None
    meta: dict[str, Any] = field(default_factory=dict)
