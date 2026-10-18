"""回调鉴权：HMAC-SHA256 签名 + 时间戳窗 + nonce 防重放。

为什么不是"传个静态 token 就行"
--------------------------------
审批回调是**外部系统（OA）打进来**的接口，而且它的效果是"授权一次新的写"
（见 ``store.py`` 文档）。静态 token 一旦泄露，谁都能批准。所以最小可用形态是：

- **签名**：``HMAC-SHA256(secret, "{ts}.{nonce}.{raw_body}")``；
- **时间窗**：±300s，过期拒（防止拿到旧请求无限重放）；
- **nonce**：窗内只认一次（防止同一秒内重放）。

没有现成的 SSO / mTLS 时这就是底线；``secret`` 走环境变量
``OPS_HITL_CALLBACK_SECRET``，**不进代码、不进清单**。

为什么不用"thread_id 当密钥"
---------------------------
用户提的"传 thread_id 等 checkpoint 标识"是**关联标识**（知道要恢复哪一次 run），
不是密钥。标识可以明文传——它需要被读出来用；密钥不行。两者别混。
"""

from __future__ import annotations

import hashlib
import hmac
import os
import time
from typing import Any

ENV_SECRET = "OPS_HITL_CALLBACK_SECRET"

HEADER_SIGNATURE = "X-Ops-Signature"
HEADER_TIMESTAMP = "X-Ops-Timestamp"
HEADER_NONCE = "X-Ops-Nonce"

_TOLERANCE_SECONDS = 300
_MAX_NONCES = 1024
_seen_nonces: dict[str, float] = {}


class SignatureError(Exception):
    """签名校验失败。

    消息只说**哪一步没过**（缺头 / 超窗 / nonce 重放 / 不匹配），
    **不泄露期望值**——否则这个异常本身就成了攻击者校对签名的工具。
    """


def _secret() -> str:
    return os.environ.get(ENV_SECRET, "").strip()


def secret_configured() -> bool:
    return bool(_secret())


def sign(*, body: bytes, timestamp: int, nonce: str, secret: str | None = None) -> str:
    """生成签名（客户端 / 测试 / mock 服务用）。"""
    key = (secret or _secret()).encode("utf-8")
    message = f"{timestamp}.{nonce}.".encode() + body
    return "sha256=" + hmac.new(key, message, hashlib.sha256).hexdigest()


def _prune_nonces(now: float) -> None:
    for nonce, ts in list(_seen_nonces.items()):
        if now - ts > _TOLERANCE_SECONDS:
            _seen_nonces.pop(nonce, None)
    # 上界兜底：即便窗内 nonce 暴涨也不让字典无限长
    while len(_seen_nonces) > _MAX_NONCES:
        _seen_nonces.pop(next(iter(_seen_nonces)), None)


def verify(*, body: bytes, headers: Any, now: float | None = None) -> None:
    """校验回调签名；不通过直接抛 ``SignatureError``。

    ``headers`` 需支持大小写不敏感的 ``get``（FastAPI ``Headers`` / dict 均可）。
    """
    if not secret_configured():
        raise SignatureError(f"{ENV_SECRET} 未配置：回调端点拒绝所有请求（不设密钥 = 不开放）")

    def _h(name: str) -> str:
        try:
            value = headers.get(name)
        except Exception:
            value = None
        return str(value or "").strip()

    signature = _h(HEADER_SIGNATURE)
    raw_ts = _h(HEADER_TIMESTAMP)
    nonce = _h(HEADER_NONCE)
    if not signature or not raw_ts or not nonce:
        raise SignatureError("缺少签名头（signature / timestamp / nonce）")

    try:
        ts = int(raw_ts)
    except (TypeError, ValueError):
        raise SignatureError("timestamp 非法") from None

    clock = time.time() if now is None else now
    if abs(clock - ts) > _TOLERANCE_SECONDS:
        raise SignatureError("timestamp 超出 ±300s 时间窗（重放？）")

    _prune_nonces(clock)
    if nonce in _seen_nonces:
        raise SignatureError("nonce 已用过（重放）")

    expected = sign(body=body, timestamp=ts, nonce=nonce)
    if not hmac.compare_digest(expected, signature):
        raise SignatureError("签名不匹配")

    _seen_nonces[nonce] = clock


def reset_nonces() -> None:
    """测试隔离用。"""
    _seen_nonces.clear()
