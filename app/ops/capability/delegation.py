"""委派令牌（Agent Host V1-A · DelegationToken）。

SPEC：docs/spec/host-v1-delegation-token/SPEC-host-v1-delegation-token_v0.md（signed）。

设计纪律（承 SPEC §1 签收锁死）：

1. **Host 权威**：令牌由分发路径签发、验签门强制，**不是模型可选 tool**；
   签名密钥进程内 env 注入，模型不可见；主体绑定取自 ctx/ContextVar，
   **模型产出不得参与身份构造**。
2. **自包含凭据**：令牌可序列化入 state/checkpoint；验签零 LLM、零 IO、
   **禁查库禁网络**（HMAC 对称验签微秒级，承 SPEC FP-3）。
3. **TTL 锚定墙钟**：expires_at 是墙钟时刻；HITL 挂起不延长令牌寿命
   （防挂起囤令牌）；resume 后过期即拒（R-c），由分发路径重签发。
4. **一次性防重放**：one_shot 默认 True；nonce 消费登记在**进程内**
   TTL 缓存（防重放窗口 = 进程生命周期，承 SPEC FP-5 如实定性；
   跨进程防重放 v2.0）。同 subtask 重签发 = 新例生效 + 旧 nonce 作废
   （supersede）；**禁续期**（续期 = 防重放开口子，SPEC FP-1）。
5. **安全默认**：未知参数约束类型 → **拒绝签发**（不静默放行）；
   enforce 缺密钥 → 拒绝签发 + 告警（不降级为不签名）。
6. **记动作不记内容**：审计只记 token_id / version / 集合基数 / 过期时刻；
   参数约束命中记字段名**哈希**，不记参数原值。

本模块与 step_contract 同形态：零 LLM、零 IO，纯函数 + 进程内 registry。
"""

from __future__ import annotations

import hashlib
import hmac
import json
import logging
import re
import threading
import time
import uuid
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)

# ---- env 键（密钥禁硬编码；非法值一律回退，承 step_contract._env_int 纪律）----
ENV_SECRET = "LG_RAG_DELEGATION_TOKEN_SECRET"
ENV_TTL_SECONDS = "LG_RAG_DELEGATION_TOKEN_TTL_SECONDS"
ENV_MODE = "LG_RAG_DELEGATION_TOKEN_MODE"

DEFAULT_TTL_SECONDS = 600
TOKEN_VERSION = 1

MODE_OFF = "off"
MODE_OBSERVE = "observe"
MODE_ENFORCE = "enforce"
_MODES = frozenset({MODE_OFF, MODE_OBSERVE, MODE_ENFORCE})

# ---- 六类拒绝（+ 篡改/缺密钥归 R-a 伞，审计单列 class，承 SPEC §2 D3）----
REJECT_NO_TOKEN = "no_token"  # R-a：无令牌 / 反序列化失败
REJECT_SIGNATURE_INVALID = "signature_invalid"  # 篡改（R-a 伞 · 审计单列）
REJECT_SECRET_MISSING = "secret_missing"  # enforce 缺密钥（R-a 伞 · 审计单列）
REJECT_OUT_OF_SET = "out_of_set"  # R-b：capability_id ∉ capability_set
REJECT_EXPIRED = "expired"  # R-c：墙钟过期
REJECT_NONCE_REUSED = "nonce_reused"  # R-d：一次性 nonce 已消费
REJECT_PARAM_VIOLATION = "param_violation"  # R-e：参数越约束
REJECT_SUBJECT_MISMATCH = "subject_mismatch"  # R-f：主体不符

# ---- 审计动作词表（记动作不记内容 · 不落新表）----
AUDIT_TOKEN_ISSUED = "token_issued"
AUDIT_TOKEN_ISSUE_HITL_REQUIRED = "token_issue_hitl_required"
AUDIT_TOKEN_SUPERSEDED = "token_superseded"
AUDIT_TOKEN_VERIFIED = "token_verified"
AUDIT_TOKEN_REJECTED = "token_rejected"  # 形如 token_rejected:<class>

# v1 参数约束子集（未知类型 → 拒绝签发 · 安全默认）
_CONSTRAINT_ENUM = "enum"
_CONSTRAINT_MAX_LEN = "max_len"
_CONSTRAINT_PATTERN = "pattern"
KNOWN_CONSTRAINT_TYPES = frozenset({_CONSTRAINT_ENUM, _CONSTRAINT_MAX_LEN, _CONSTRAINT_PATTERN})

# 只读副作用（Q2 自动放行边界 · 承 types.SIDE_EFFECTS 词表）
READONLY_SIDE_EFFECTS = frozenset({"none", "read"})
# 沙箱 / cli 类不进自动放行（Q2 · 复用 policy.py 门类判定）
NON_AUTO_KINDS = frozenset({"sandbox", "cli"})


def _env_int(name: str, default: int, *, low: int, high: int) -> int:
    """读 env 覆盖；非法 / 越界一律回退默认（承 step_contract._env_int 纪律）。"""
    import os

    raw = os.environ.get(name, "")
    try:
        value = int(str(raw).strip())
    except (TypeError, ValueError):
        return default
    return value if low <= value <= high else default


def delegation_mode() -> str:
    """验签门三档：off|observe|enforce；默认 off（零 diff）；非法值回退 off。"""
    import os

    raw = os.environ.get(ENV_MODE, "").strip().lower()
    return raw if raw in _MODES else MODE_OFF


def delegation_ttl_seconds() -> int:
    """令牌 TTL（墙钟秒）；默认 600，非法 / 越界回退默认。"""
    return _env_int(ENV_TTL_SECONDS, DEFAULT_TTL_SECONDS, low=1, high=86400)


def delegation_secret() -> str | None:
    """签名密钥（env 注入 · **禁硬编码**）；缺失 / 空白 → None。"""
    import os

    raw = os.environ.get(ENV_SECRET, "")
    value = str(raw).strip()
    return value or None


def _kid_of(secret: str) -> str:
    """密钥代标识（轮换 = 重启 · 预留多密钥并存 v2.0）；不含密钥本体。"""
    return hashlib.sha256(secret.encode("utf-8")).hexdigest()[:12]


def field_hash(name: str) -> str:
    """参数字段名哈希（审计记哈希不记原名 · 无 PII 泄漏面）。"""
    return hashlib.sha256(str(name).encode("utf-8")).hexdigest()[:12]


# ---------------------------------------------------------------------------
# 审计（记动作不记内容：logger 结构化行 + span metadata）
# ---------------------------------------------------------------------------


def audit_delegation(action: str, **fields: Any) -> None:
    """委派令牌台账：logger + 当前 span metadata（观测失败不挡主流程）。"""
    safe = {k: v for k, v in fields.items() if v is not None}
    logger.info(
        "delegation %s %s",
        action,
        json.dumps(safe, ensure_ascii=False, sort_keys=True),
    )
    try:
        from app.ops.tracing import update_current_span_metadata

        metadata: dict[str, Any] = {f"delegation_{action}": True}
        metadata.update({f"delegation_{k}": v for k, v in safe.items()})
        update_current_span_metadata(metadata)
    except Exception:  # 观测面故障绝不拖垮主流程
        pass


def _token_audit_fields(token: DelegationToken) -> dict[str, Any]:
    """令牌审计字段（**只记动作锚点**：id / version / 集合基数 / 过期时刻）。"""
    return {
        "token_id": token.token_id,
        "version": token.version,
        "capability_count": len(token.capability_set),
        "expires_at": token.expires_at,
    }


# ---------------------------------------------------------------------------
# 令牌模型（frozen · 可序列化入 state/checkpoint · 自包含凭据）
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class DelegationToken:
    """委派令牌（六字段 + 标识/序号/签名；任何字段改动 → 签名失效）。"""

    token_id: str
    version: int
    kid: str
    capability_set: frozenset[str]
    ttl_seconds: int
    issued_at: float
    expires_at: float
    one_shot: bool
    nonce: str
    param_constraints: dict[str, Any] = field(default_factory=dict)
    subject_binding: dict[str, str] = field(default_factory=dict)
    signature: str = ""


def canonical_payload(token: DelegationToken) -> dict[str, Any]:
    """签名载荷：除 signature 外全字段（集合排序成 list 以保 canonical）。"""
    return {
        "token_id": token.token_id,
        "version": token.version,
        "kid": token.kid,
        "capability_set": sorted(token.capability_set),
        "ttl_seconds": token.ttl_seconds,
        "issued_at": token.issued_at,
        "expires_at": token.expires_at,
        "one_shot": token.one_shot,
        "nonce": token.nonce,
        "param_constraints": token.param_constraints,
        "subject_binding": token.subject_binding,
    }


def canonical_json(payload: dict[str, Any]) -> str:
    """canonical JSON：排序键 + 紧凑分隔符（签名 / 验签两侧必须逐字节一致）。"""
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def sign_payload(payload: dict[str, Any], secret: str) -> str:
    """HMAC-SHA256（Q1 裁定 · 对称签名：签发方与验签方同进程同密钥）。"""
    return hmac.new(
        secret.encode("utf-8"), canonical_json(payload).encode("utf-8"), hashlib.sha256
    ).hexdigest()


def token_to_dict(token: DelegationToken) -> dict[str, Any]:
    """序列化（checkpoint 形态 · 纯 JSON 类型）。"""
    payload = canonical_payload(token)
    payload["signature"] = token.signature
    return payload


def token_from_dict(raw: Any) -> DelegationToken:
    """反序列化；形态非法 → ValueError（调用方归入 R-a 无令牌）。"""
    if not isinstance(raw, dict):
        raise ValueError("delegation token 必须是 dict")
    try:
        capability_set = frozenset(str(c) for c in raw["capability_set"])
        constraints = raw.get("param_constraints") or {}
        binding = raw.get("subject_binding") or {}
        if not isinstance(constraints, dict) or not isinstance(binding, dict):
            raise ValueError("delegation token 字段形态非法")
        return DelegationToken(
            token_id=str(raw["token_id"]),
            version=int(raw["version"]),
            kid=str(raw["kid"]),
            capability_set=capability_set,
            ttl_seconds=int(raw["ttl_seconds"]),
            issued_at=float(raw["issued_at"]),
            expires_at=float(raw["expires_at"]),
            one_shot=bool(raw["one_shot"]),
            nonce=str(raw["nonce"]),
            param_constraints=dict(constraints),
            subject_binding={str(k): str(v) for k, v in binding.items()},
            signature=str(raw["signature"]),
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError(f"delegation token 反序列化失败: {exc}") from exc


# ---------------------------------------------------------------------------
# 参数约束（v1 子集：enum / max_len / pattern · 未知类型拒绝签发）
# ---------------------------------------------------------------------------


def validate_param_constraints(constraints: Any) -> str | None:
    """签发前校验约束声明；合法 → None，非法 → 原因（**拒绝签发**）。

    形状：{capability_id: {arg_name: {约束类型: 约束值}}}；
    约束类型只认 enum / max_len / pattern，**未知类型一律拒**
    （安全默认：静默跳过等于给模型开了一条绕约束的暗道）。
    """
    if constraints is None:
        return None
    if not isinstance(constraints, dict):
        return "param_constraints 必须是 dict"
    for cap_id, per_args in constraints.items():
        if not isinstance(per_args, dict):
            return f"param_constraints[{cap_id}] 必须是 dict"
        for arg_name, rule in per_args.items():
            if not isinstance(rule, dict) or not rule:
                return f"param_constraints[{cap_id}][{arg_name}] 约束必须是非空 dict"
            unknown = set(rule) - KNOWN_CONSTRAINT_TYPES
            if unknown:
                return f"未知约束类型 {sorted(unknown)}（{cap_id}.{arg_name}）→ 拒绝签发"
            if _CONSTRAINT_ENUM in rule and not isinstance(rule[_CONSTRAINT_ENUM], list):
                return f"enum 约束必须是 list（{cap_id}.{arg_name}）"
            if _CONSTRAINT_MAX_LEN in rule:
                raw = rule[_CONSTRAINT_MAX_LEN]
                if not isinstance(raw, int) or isinstance(raw, bool) or raw < 0:
                    return f"max_len 约束必须是非负 int（{cap_id}.{arg_name}）"
            if _CONSTRAINT_PATTERN in rule:
                raw = rule[_CONSTRAINT_PATTERN]
                if not isinstance(raw, str):
                    return f"pattern 约束必须是 str（{cap_id}.{arg_name}）"
                try:
                    re.compile(raw)
                except re.error:
                    return f"pattern 约束不是合法正则（{cap_id}.{arg_name}）"
    return None


def check_param_constraints(token: DelegationToken, capability_id: str, args: Any) -> str | None:
    """验签时校验调用参数；违规 → 字段名，通过 → None（纯代码校验 · 零 IO）。"""
    per_args = (token.param_constraints or {}).get(capability_id) or {}
    if not per_args:
        return None
    values = args if isinstance(args, dict) else {}
    for arg_name, rule in per_args.items():
        value = values.get(arg_name)
        if _CONSTRAINT_ENUM in rule and value not in rule[_CONSTRAINT_ENUM]:
            return str(arg_name)
        if _CONSTRAINT_MAX_LEN in rule and (
            not isinstance(value, str) or len(value) > int(rule[_CONSTRAINT_MAX_LEN])
        ):
            return str(arg_name)
        if _CONSTRAINT_PATTERN in rule and (
            not isinstance(value, str) or re.search(rule[_CONSTRAINT_PATTERN], value) is None
        ):
            return str(arg_name)
    return None


# ---------------------------------------------------------------------------
# nonce 消费 registry（进程内 TTL 缓存 · 防重放窗口 = 进程生命周期 · FP-5）
# ---------------------------------------------------------------------------


class _NonceRegistry:
    """一次性 nonce 消费登记；TTL 清理（条目活到对应令牌过期即止）。"""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._consumed: dict[str, float] = {}

    def _cleanup(self, now: float) -> None:
        expired = [n for n, exp in self._consumed.items() if exp <= now]
        for n in expired:
            del self._consumed[n]

    def is_consumed(self, nonce: str, *, now: float | None = None) -> bool:
        with self._lock:
            self._cleanup(now if now is not None else time.time())
            return nonce in self._consumed

    def consume(self, nonce: str, *, expires_at: float, now: float | None = None) -> bool:
        """登记消费；已消费 → False（R-d 重用）。"""
        with self._lock:
            current = now if now is not None else time.time()
            self._cleanup(current)
            if nonce in self._consumed:
                return False
            self._consumed[nonce] = expires_at
            return True

    def reset(self) -> None:
        with self._lock:
            self._consumed.clear()


_nonce_registry = _NonceRegistry()


# ---------------------------------------------------------------------------
# 签发器（进程内单调签发序号 + 同 subtask supersede · Tier 1 语义）
# ---------------------------------------------------------------------------


class DelegationIssuer:
    """签发器：签发序号单调；同 subtask_id 重签发 → 旧 nonce 作废（禁续期）。"""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._seq = 0
        self._latest_nonce_by_subtask: dict[str, str] = {}
        self._latest_token_by_subtask: dict[str, str] = {}

    def next_seq(self) -> int:
        with self._lock:
            self._seq += 1
            return self._seq

    def supersede(self, subtask_id: str, *, new_nonce: str, new_token_id: str) -> str | None:
        """登记新例；旧例 nonce 作废（消费登记 → 再用即 R-d）。返回旧 token_id。"""
        with self._lock:
            old_nonce = self._latest_nonce_by_subtask.get(subtask_id)
            old_token_id = self._latest_token_by_subtask.get(subtask_id)
            self._latest_nonce_by_subtask[subtask_id] = new_nonce
            self._latest_token_by_subtask[subtask_id] = new_token_id
        if old_nonce and old_nonce != new_nonce:
            # 旧 nonce 登记消费：再用即 R-d（supersede 语义）
            _nonce_registry.consume(old_nonce, expires_at=time.time() + DEFAULT_TTL_SECONDS)
        return old_token_id if old_nonce else None

    def reset(self) -> None:
        with self._lock:
            self._seq = 0
            self._latest_nonce_by_subtask.clear()
            self._latest_token_by_subtask.clear()


_default_issuer = DelegationIssuer()


def get_issuer() -> DelegationIssuer:
    return _default_issuer


def reset_delegation_state() -> None:
    """测试用：清空签发序号 / supersede 台账 / nonce registry。"""
    _default_issuer.reset()
    _nonce_registry.reset()


def issue_token(
    *,
    capability_set: set[str] | frozenset[str] | list[str],
    subject_binding: dict[str, str],
    param_constraints: dict[str, Any] | None = None,
    one_shot: bool = True,
    ttl_seconds: int | None = None,
    secret: str | None = None,
    issuer: DelegationIssuer | None = None,
    now: float | None = None,
) -> DelegationToken | None:
    """签发令牌；安全默认拒（缺密钥 / 未知约束类型）→ None + 告警。

    subject_binding = {tenant_id, user_id, run_id, subtask_id} 四元组，
    必须由 Host 侧 ctx/ContextVar 构造（模型产出不得参与身份构造）。
    """
    actual_secret = secret if secret is not None else delegation_secret()
    if not actual_secret:
        logger.warning(
            "delegation 缺签名密钥 %s，拒绝签发（安全默认拒 · 不降级为不签名） subtask=%s",
            ENV_SECRET,
            subject_binding.get("subtask_id", ""),
        )
        return None
    constraints = dict(param_constraints or {})
    invalid = validate_param_constraints(constraints)
    if invalid is not None:
        logger.warning("delegation 参数约束非法，拒绝签发：%s", invalid)
        return None
    active_issuer = issuer or _default_issuer
    current = now if now is not None else time.time()
    ttl = ttl_seconds if ttl_seconds is not None else delegation_ttl_seconds()
    seq = active_issuer.next_seq()
    token_id = f"dt-{seq}-{uuid.uuid4().hex[:12]}"
    nonce = uuid.uuid4().hex
    subtask_id = str(subject_binding.get("subtask_id") or "")
    old_token_id = active_issuer.supersede(subtask_id, new_nonce=nonce, new_token_id=token_id)
    binding = {
        "tenant_id": str(subject_binding.get("tenant_id") or ""),
        "user_id": str(subject_binding.get("user_id") or ""),
        "run_id": str(subject_binding.get("run_id") or ""),
        "subtask_id": subtask_id,
    }
    token = DelegationToken(
        token_id=token_id,
        version=TOKEN_VERSION,
        kid=_kid_of(actual_secret),
        capability_set=frozenset(str(c) for c in capability_set),
        ttl_seconds=int(ttl),
        issued_at=current,
        expires_at=current + int(ttl),
        one_shot=bool(one_shot),
        nonce=nonce,
        param_constraints=constraints,
        subject_binding=binding,
    )
    token = DelegationToken(
        **{
            **token.__dict__,
            "signature": sign_payload(canonical_payload(token), actual_secret),
        }
    )
    if old_token_id:
        audit_delegation(
            AUDIT_TOKEN_SUPERSEDED,
            old_token_id=old_token_id,
            new_token_id=token_id,
            subtask_id=subtask_id,
        )
    audit_delegation(AUDIT_TOKEN_ISSUED, **_token_audit_fields(token), subtask_id=subtask_id)
    return token


# ---------------------------------------------------------------------------
# 审批口径（Q2 裁定：只读自动 · 其余 HITL）
# ---------------------------------------------------------------------------


def auto_approve_ok(
    specs: list[Any],
    *,
    effective_scope: set[str] | frozenset[str],
) -> tuple[bool, str]:
    """自动放行边界三条件（全部纯代码判定 · 复用 policy 门类真值）：

    1. capability_set ⊆ 有效 scope（D5 声明∩裁剪后的上界）；
    2. 集合内能力全部 side_effect ∈ {none, read}（只读）；
    3. 无 sandbox / cli 类。

    specs 为 Host 侧注册表真值（manifest 声明 · 非模型产出）。
    返回 (是否自动放行, 不放行原因)。
    """
    scope = {str(c) for c in effective_scope}
    for spec in specs:
        cid = str(getattr(spec, "capability_id", "") or "")
        if cid not in scope:
            return False, f"capability {cid} 越出有效 scope"
        if str(getattr(spec, "side_effect", "") or "") not in READONLY_SIDE_EFFECTS:
            return (
                False,
                f"capability {cid} 非只读（side_effect={getattr(spec, 'side_effect', '')}）",
            )
        if str(getattr(spec, "kind", "") or "") in NON_AUTO_KINDS:
            return False, f"capability {cid} 为 sandbox/cli 类"
    return True, ""


# ---------------------------------------------------------------------------
# 验签（纯函数 · 零 LLM 零 IO 禁查库 · 六类拒绝）
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Verdict:
    """验签判定；ok=False 时 reject_class 为六类拒绝之一（+ R-a 伞单列）。"""

    ok: bool
    reject_class: str = ""
    detail: str = ""
    violated_field: str | None = None


_VERDICT_OK = Verdict(ok=True)


def verify_token(
    token: DelegationToken | None,
    *,
    secret: str | None,
    capability_id: str,
    args: Any,
    subject: dict[str, Any],
    now: float | None = None,
) -> Verdict:
    """验签：签名 → 集合 → 过期 → 一次性 → 参数约束 → 主体绑定。

    全部判定零 IO；subject = ctx 四元组（tenant/user/run/subtask）。
    一次性 nonce 只在**全部通过**后消费（被拒调用不烧 nonce）。
    """
    if token is None:
        return Verdict(False, REJECT_NO_TOKEN, "委派调用未携带令牌或令牌反序列化失败")
    if not secret:
        return Verdict(False, REJECT_SECRET_MISSING, f"缺签名密钥 {ENV_SECRET}，无法验签")
    expected = sign_payload(canonical_payload(token), secret)
    if not hmac.compare_digest(expected, str(token.signature or "")):
        return Verdict(False, REJECT_SIGNATURE_INVALID, "令牌签名验不过（篡改或密钥不符）")
    cid = str(capability_id or "")
    if cid not in token.capability_set:
        return Verdict(False, REJECT_OUT_OF_SET, f"capability {cid} 不在令牌能力集内")
    current = now if now is not None else time.time()
    if current > token.expires_at:
        return Verdict(False, REJECT_EXPIRED, "令牌已过期（墙钟 TTL · 禁续期）")
    if token.one_shot and _nonce_registry.is_consumed(token.nonce, now=current):
        return Verdict(False, REJECT_NONCE_REUSED, "一次性令牌 nonce 已消费（重用 / 已作废）")
    violated = check_param_constraints(token, cid, args)
    if violated is not None:
        return Verdict(
            False,
            REJECT_PARAM_VIOLATION,
            f"参数越约束 field_hash={field_hash(violated)}",
            violated_field=violated,
        )
    binding = token.subject_binding or {}
    mismatched = [
        key
        for key in ("tenant_id", "user_id", "run_id", "subtask_id")
        if str(binding.get(key) or "") != str((subject or {}).get(key) or "")
    ]
    if mismatched:
        return Verdict(False, REJECT_SUBJECT_MISMATCH, f"主体绑定不符 keys={sorted(mismatched)}")
    if token.one_shot and not _nonce_registry.consume(
        token.nonce, expires_at=token.expires_at, now=current
    ):
        # 并发撞 nonce（判过之后被另一路抢先消费）
        return Verdict(False, REJECT_NONCE_REUSED, "一次性令牌 nonce 已消费（并发重用）")
    return _VERDICT_OK


def verify_serialized(
    raw: Any,
    *,
    secret: str | None,
    capability_id: str,
    args: Any,
    subject: dict[str, Any],
    now: float | None = None,
) -> Verdict:
    """从 ctx 里的序列化形态验签；反序列化失败归 R-a。"""
    try:
        token = token_from_dict(raw)
    except ValueError:
        token = None
    return verify_token(
        token,
        secret=secret,
        capability_id=capability_id,
        args=args,
        subject=subject,
        now=now,
    )
