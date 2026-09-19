"""通用 HTTP adapter（kind=http）· 声明式调用。

目标：**让 80% 的能力注册变成写配置，而不是写代码。**

一条 manifest 条目声明 ``http`` 块后，本 adapter 负责：
参数模板渲染 → 凭证注入（按名取，永不落日志）→ 租户谓词下推 →
幂等键 → 调用 → 成功判定 → 错误归一化 → 回执捕获。

分工纪律（不可越界）：
- 本 adapter **不做业务判断**。业务不变量（金额能不能批、有没有权报这个部门）
  属于 Policy 或**业务级自定义 adapter**，不在这里。
- **写操作绝不自动重试**：超时不代表失败，可能已经成功。重试会产生第二张单据。
  写操作的失败必须靠幂等键 + 主动查询确认（见 ``_call``）。
- 老 OA 的错误码一律在 ``error_map`` 里归一化到 ``errors.STABLE_ERROR_CODES``；
  不归一化的下游错误串**不外泄给模型**。

测试接缝：``transport`` 可注入；CI 用 ``FakeHttpTransport`` 零 socket / 零外网。
"""

from __future__ import annotations

import json
import re
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import UTC
from typing import Any, Protocol, runtime_checkable

from app.ops.capability.errors import (
    ARGS_SCHEMA_INVALID,
    PERMISSION_DENIED,
    UPSTREAM_ERROR,
    format_error,
)
from app.ops.capability.types import WRITE_SIDE_EFFECTS, CapabilitySpec

_VAR_RE = re.compile(r"\{\{(\w+)\}\}")
_EXACT_VAR_RE = re.compile(r"^\{\{(\w+)\}\}$")

# Host 注入变量（不需在 args_schema.properties 里声明）
HOST_INJECTED_VARS: frozenset[str] = frozenset(
    {"_user_id", "_date", "_tenant_id", "_subtask_id"}
)

_MISSING = object()


class HttpCapabilityError(Exception):
    """HTTP 能力失败；``code`` 必须是稳定错误码。"""

    def __init__(self, code: str, detail: str = "") -> None:
        self.code = code
        self.detail = detail
        super().__init__(format_error(code, detail))

    def __repr__(self) -> str:  # gateway._err_result 用 repr(exc)
        return format_error(self.code, self.detail)


@dataclass(frozen=True)
class HttpResponse:
    """transport 返回面：状态码 + 已解析 payload。"""

    status: int
    payload: Any = None


@runtime_checkable
class HttpTransport(Protocol):
    """可注入的 HTTP 传输面（urllib / Fake 均可）。"""

    def request(
        self,
        *,
        method: str,
        url: str,
        headers: dict[str, str],
        params: dict[str, Any],
        body: dict[str, Any] | None,
        timeout_s: float,
    ) -> HttpResponse: ...


@runtime_checkable
class CredentialVault(Protocol):
    """凭证保险箱：**只按名字取，名字可在仓里出现，值不可。**"""

    def auth_headers(self, auth_name: str) -> dict[str, str]: ...


class EnvCredentialVault:
    """env 取值：``OPS_CAP_CRED_<UPPER_NAME>``（与既有 env-gated 约定一致）。"""

    _PREFIX = "OPS_CAP_CRED_"

    def auth_headers(self, auth_name: str) -> dict[str, str]:
        import os

        key = f"{self._PREFIX}{str(auth_name or '').strip().upper()}"
        value = os.environ.get(key, "").strip()
        if not value:
            raise HttpCapabilityError(
                PERMISSION_DENIED, f"未配置凭证: {auth_name}（env {key} 缺失）"
            )
        return {"Authorization": f"Bearer {value}"}


class StaticCredentialVault:
    """测试 / 内网直连用；**禁止**把值写进 manifest。"""

    def __init__(self, creds: dict[str, str] | None = None) -> None:
        self._creds = dict(creds or {})

    def auth_headers(self, auth_name: str) -> dict[str, str]:
        value = self._creds.get(auth_name)
        if not value:
            raise HttpCapabilityError(
                PERMISSION_DENIED, f"未配置凭证: {auth_name}"
            )
        return {"Authorization": f"Bearer {value}"}


class FakeHttpTransport:
    """单测用假传输：零 socket / 零外网。记录调用便于断言。"""

    def __init__(
        self,
        *,
        payload: Any = None,
        status: int = 200,
        exc: BaseException | None = None,
    ) -> None:
        self._payload = {"code": 0, "data": {}} if payload is None else payload
        self._status = status
        self._exc = exc
        self.calls: list[dict[str, Any]] = []

    def request(
        self,
        *,
        method: str,
        url: str,
        headers: dict[str, str],
        params: dict[str, Any],
        body: dict[str, Any] | None,
        timeout_s: float,
    ) -> HttpResponse:
        self.calls.append(
            {
                "method": method,
                "url": url,
                "headers": dict(headers),
                "params": dict(params),
                "body": None if body is None else dict(body),
                "timeout_s": timeout_s,
            }
        )
        if self._exc is not None:
            raise self._exc
        return HttpResponse(status=self._status, payload=self._payload)


class UrllibHttpTransport:
    """真传输：stdlib ``urllib``（不引入 httpx，与 mcp_client 约定一致）。"""

    def request(
        self,
        *,
        method: str,
        url: str,
        headers: dict[str, str],
        params: dict[str, Any],
        body: dict[str, Any] | None,
        timeout_s: float,
    ) -> HttpResponse:
        if params:
            query = urllib.parse.urlencode(
                {k: v for k, v in params.items() if v is not None}
            )
            if query:
                url = f"{url}{'&' if '?' in url else '?'}{query}"
        data = None
        send_headers = dict(headers)
        if body is not None:
            data = json.dumps(body).encode("utf-8")
            send_headers.setdefault("Content-Type", "application/json")
        req = urllib.request.Request(
            url, data=data, headers=send_headers, method=method.upper()
        )
        try:
            with urllib.request.urlopen(req, timeout=timeout_s) as resp:
                raw = resp.read().decode("utf-8", errors="replace")
                status = int(getattr(resp, "status", 200) or 200)
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")[:200]
            # 注意：不回显请求头/请求体（可能含凭证）
            raise HttpCapabilityError(
                UPSTREAM_ERROR, f"HTTP {exc.code}: {detail}"
            ) from exc
        except urllib.error.URLError as exc:
            raise HttpCapabilityError(
                UPSTREAM_ERROR, f"网络错误: {exc.reason!r}"
            ) from exc
        except TimeoutError as exc:
            raise HttpCapabilityError(UPSTREAM_ERROR, "请求超时") from exc
        return HttpResponse(status=status, payload=_parse_payload(raw))


def _parse_payload(raw: str) -> Any:
    text = (raw or "").strip()
    if not text:
        return {}
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {"_raw": text[:500]}


def jsonpath_get(data: Any, expr: str) -> Any:
    """极简 JSONPath 子集：``$`` / ``$.a.b`` / ``$.a[0].b``。取不到 → ``_MISSING``。"""
    path = str(expr or "").strip()
    if path in ("", "$"):
        return data
    if path.startswith("$"):
        path = path[1:]
    if path.startswith("."):
        path = path[1:]
    cur = data
    for token in [t for t in path.split(".") if t]:
        name, _, indexes = token.partition("[")
        if name:
            if not isinstance(cur, dict) or name not in cur:
                return _MISSING
            cur = cur[name]
        while indexes:
            idx_str, _, rest = indexes.partition("]")
            try:
                idx = int(idx_str)
            except ValueError:
                return _MISSING
            if not isinstance(cur, list) or idx >= len(cur) or idx < -len(cur):
                return _MISSING
            cur = cur[idx]
            indexes = rest.lstrip("[").lstrip("]")
    return cur


class GenericHttpAdapter:
    """声明式 HTTP 能力；``kind=http``。

    契约与 ``LocalFnAdapter`` 相同：``invoke(args, *, ctx) -> Any``（可 JSON 化 dict）。
    """

    kind = "http"

    def __init__(
        self,
        spec: CapabilitySpec,
        *,
        transport: HttpTransport | None = None,
        vault: CredentialVault | None = None,
    ) -> None:
        self._spec = spec
        self._transport = transport
        self._vault = vault

    # ---- 对外 ----
    def invoke(self, args: Any, *, ctx: dict[str, Any] | None = None) -> Any:
        http = self._spec.http or {}
        safe_args = self._apply_defaults(args if isinstance(args, dict) else {})
        self._assert_declared_vars(http)

        rendered = self._render(http, safe_args, ctx)
        # 顺序要紧：先下推租户谓词，再取 headers。
        # 否则租户头写进了 rendered 而 headers 是它的副本，静默丢失。
        self._push_tenant(http, rendered, ctx)
        headers = dict(rendered["headers"])
        headers.update(self._vault_headers(str(http.get("auth") or "")))

        idem = self._idempotency_key(http, safe_args, ctx)
        if idem:
            # 写操作必带（V1 已在加载期强制；此处兜运行期）
            headers.setdefault("Idempotency-Key", idem)

        method = str(http.get("method") or "GET").upper()
        url = self._resolve_url(http)
        resp = self._call(
            method=method,
            url=url,
            headers=headers,
            params=rendered["params"],
            body=rendered["body"],
            timeout_s=float(http.get("timeout_ms", 8000)) / 1000.0,
        )

        payload = resp.payload if isinstance(resp.payload, dict) else {}
        if not self._is_success(resp, payload, http):
            raise self._map_upstream_error(payload, http, resp.status)

        out: dict[str, Any] = {
            "protocol": "http",
            "kind": self.kind,
            "capability_id": self._spec.capability_id,
            "status": resp.status,
            "result": payload,
        }
        if self._spec.receipt_capture:
            out["receipt"] = self._capture(payload)
        if idem:
            out["idempotency_key"] = idem
        return out

    # ---- 渲染 ----
    def _apply_defaults(self, args: dict[str, Any]) -> dict[str, Any]:
        """补齐 args_schema 里声明的 default。

        否则缺省参数会渲染成空串，变成 ``limit=`` 这种把语义交给下游猜的请求。
        """
        props = (self._spec.args_schema or {}).get("properties") or {}
        out = dict(args)
        for name, schema in props.items():
            if name in out or not isinstance(schema, dict):
                continue
            if "default" in schema:
                out[name] = schema["default"]
        return out

    def _assert_declared_vars(self, http: dict[str, Any]) -> None:
        """运行期兜底：模板变量必须在 args_schema 或 Host 注入集合内（与加载期 V5 双保险）。"""
        declared = set((self._spec.args_schema or {}).get("properties", {}) or {})
        allowed = declared | set(HOST_INJECTED_VARS)
        for match in _VAR_RE.finditer(json.dumps(http, ensure_ascii=False, default=str)):
            if match.group(1) not in allowed:
                raise HttpCapabilityError(
                    ARGS_SCHEMA_INVALID, f"未声明模板变量: {match.group(1)}"
                )

    def _render(
        self, http: dict[str, Any], args: dict[str, Any], ctx: dict[str, Any] | None
    ) -> dict[str, Any]:
        scope = {**args, **self._host_vars(ctx)}
        return {
            "params": self._render_map(http.get("query_map"), scope),
            "body": self._render_map(http.get("body_map"), scope),
            "headers": {
                str(k): str(v)
                for k, v in self._render_map(http.get("header_map"), scope).items()
            },
        }

    @staticmethod
    def _render_map(mapping: Any, scope: dict[str, Any]) -> dict[str, Any]:
        if not isinstance(mapping, dict):
            return {}
        return {
            str(k): GenericHttpAdapter._render_value(v, scope)
            for k, v in mapping.items()
        }

    @staticmethod
    def _render_value(value: Any, scope: dict[str, Any]) -> Any:
        if not isinstance(value, str):
            return value  # 字面量（int / bool / None）原样
        exact = _EXACT_VAR_RE.match(value)
        if exact:
            # 整串就是一个变量 → 保留原类型（不要在 int 上做字符串化）
            return scope.get(exact.group(1), "")
        return _VAR_RE.sub(
            lambda m: str(scope.get(m.group(1), "") or ""), value
        )

    @staticmethod
    def _host_vars(ctx: dict[str, Any] | None) -> dict[str, Any]:
        from datetime import datetime

        c = ctx or {}
        tenant = c.get("tenant_id") or c.get("_host_tenant")
        return {
            "_user_id": c.get("user_id") or c.get("_host_user_id") or "",
            "_tenant_id": tenant or "",
            "_subtask_id": c.get("subtask_id") or "",
            "_date": datetime.now(UTC).date().isoformat(),
        }

    # ---- 凭证 / 租户 / 幂等 ----
    def _vault_headers(self, auth_name: str) -> dict[str, str]:
        if not auth_name:
            return {}
        vault = self._vault or EnvCredentialVault()
        return vault.auth_headers(auth_name)

    def _push_tenant(
        self,
        http: dict[str, Any],
        rendered: dict[str, Any],
        ctx: dict[str, Any] | None,
    ) -> None:
        """租户谓词下推（V4 保证 ``tenant_param`` 已声明）。

        没有这一步，``tenant_scoped`` 就只是 Policy 里的一个检查——
        **检查了但没传给下游**，等于没做。
        """
        if not self._spec.tenant_scoped:
            return
        param = http.get("tenant_param")
        if not isinstance(param, dict):
            raise HttpCapabilityError(
                ARGS_SCHEMA_INVALID, "tenant_scoped 能力缺 tenant_param"
            )
        c = ctx or {}
        value = c.get("tenant_id") or c.get("_host_tenant")
        if value is None or not str(value).strip():
            raise HttpCapabilityError(PERMISSION_DENIED, "缺租户谓词")
        where = str(param.get("in") or "").strip().lower()
        name = str(param.get("name") or "").strip()
        if not name:
            raise HttpCapabilityError(ARGS_SCHEMA_INVALID, "tenant_param.name 为空")
        if where == "query":
            rendered["params"][name] = value
        elif where == "body":
            if rendered["body"] is None:
                rendered["body"] = {}
            rendered["body"][name] = value
        elif where == "header":
            rendered["headers"][name] = str(value)
        else:
            raise HttpCapabilityError(
                ARGS_SCHEMA_INVALID, f"tenant_param.in 非法: {where or '(空)'}"
            )

    def _idempotency_key(
        self, http: dict[str, Any], args: dict[str, Any], ctx: dict[str, Any] | None
    ) -> str | None:
        if self._spec.side_effect not in WRITE_SIDE_EFFECTS:
            return None
        template = str(http.get("idempotency_key") or "").strip()
        if not template:
            # 加载期 V1 已拦；此处为运行期兜底（例如手工 register 绕过 manifest）
            raise HttpCapabilityError(
                ARGS_SCHEMA_INVALID, "写操作缺 idempotency_key"
            )
        scope = {**args, **self._host_vars(ctx)}
        return str(self._render_value(template, scope))

    # ---- 调用 ----
    def _call(
        self,
        *,
        method: str,
        url: str,
        headers: dict[str, str],
        params: dict[str, Any],
        body: dict[str, Any] | None,
        timeout_s: float,
    ) -> HttpResponse:
        transport = self._transport or UrllibHttpTransport()
        attempts = 2 if method == "GET" else 1  # 写操作**绝不**自动重试
        last: HttpCapabilityError | None = None
        for _ in range(attempts):
            try:
                return transport.request(
                    method=method,
                    url=url,
                    headers=headers,
                    params=params,
                    body=body,
                    timeout_s=timeout_s,
                )
            except HttpCapabilityError as exc:
                last = exc
            except (TimeoutError, OSError) as exc:
                # 第三方 transport 可能抛裸异常；在边界处统一归一化，
                # 免得原始异常文本一路冒到模型面前。
                last = HttpCapabilityError(
                    UPSTREAM_ERROR, f"传输失败: {type(exc).__name__}"
                )
        assert last is not None
        raise last

    def _resolve_url(self, http: dict[str, Any]) -> str:
        import os

        base_name = str(http.get("base_url") or "").strip()
        base = os.environ.get(base_name, "").strip()
        if not base:
            raise HttpCapabilityError(
                UPSTREAM_ERROR, f"未配置 base_url 环境变量: {base_name}"
            )
        path = str(http.get("path") or "").strip()
        return f"{base.rstrip('/')}/{path.lstrip('/')}"

    def _is_success(
        self, resp: HttpResponse, payload: dict[str, Any], http: dict[str, Any]
    ) -> bool:
        rule = http.get("success_when")
        if not isinstance(rule, dict):
            return 200 <= resp.status < 300
        got = jsonpath_get(payload, str(rule.get("path") or "$"))
        if got is _MISSING:
            return False
        allowed = rule.get("in")
        return got in allowed if isinstance(allowed, list) else False

    def _map_upstream_error(
        self, payload: dict[str, Any], http: dict[str, Any], status: int
    ) -> HttpCapabilityError:
        """下游业务码 → 稳定错误码。**未映射的一律 upstream_error，不回显原文。**"""
        error_map = http.get("error_map")
        code_raw = jsonpath_get(payload, "$.code")
        if isinstance(error_map, dict) and code_raw is not _MISSING:
            mapped = error_map.get(str(code_raw))
            if mapped:
                return HttpCapabilityError(str(mapped), f"upstream_code={code_raw}")
        return HttpCapabilityError(UPSTREAM_ERROR, f"HTTP {status}")

    def _capture(self, payload: dict[str, Any]) -> dict[str, Any]:
        out: dict[str, Any] = {}
        for expr in self._spec.receipt_capture:
            got = jsonpath_get(payload, expr)
            if got is not _MISSING:
                out[expr] = got
        return out
