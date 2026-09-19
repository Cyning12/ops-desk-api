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
import os
import re
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import UTC
from typing import Any, Protocol, runtime_checkable

from app.ops.capability.errors import (
    ARGS_SCHEMA_INVALID,
    DUPLICATE_ID,
    PERMISSION_DENIED,
    POLICY_BLOCKED,
    UPSTREAM_ERROR,
    format_error,
)
from app.ops.capability.idempotency import get_idempotency_store
from app.ops.capability.types import WRITE_SIDE_EFFECTS, CapabilitySpec

#: 这些失败**确知下游没有产生副作用**，可以释放幂等键允许重试。
#: 其余（超时 / 连接错误 / 未知业务码）一律保持 in_flight，交给租约过期 —— fail-closed。
RELEASE_SAFE_ERROR_CODES: frozenset[str] = frozenset(
    {ARGS_SCHEMA_INVALID, POLICY_BLOCKED, PERMISSION_DENIED}
)

_VAR_RE = re.compile(r"\{\{(\w+)\}\}")
_EXACT_VAR_RE = re.compile(r"^\{\{(\w+)\}\}$")

# Host 注入变量（不需在 args_schema.properties 里声明）
HOST_INJECTED_VARS: frozenset[str] = frozenset(
    {"_user_id", "_date", "_tenant_id", "_subtask_id"}
)

_MISSING = object()

# 显式指定能力调用走的代理；不设 → **不走任何代理**（见 UrllibHttpTransport）
_ENV_HTTP_PROXY = "OPS_CAPABILITY_HTTP_PROXY"

# 幂等键百分号编码后保留的可读分隔符（其余非 ASCII 一律编码）
_IDEMPOTENCY_SAFE_CHARS = ":._-"


def ascii_idempotency_key(value: str) -> str:
    """把幂等键规范成 **ASCII 安全**的形态。

    为什么必须做：HTTP 头只能承载 latin-1。而幂等键的模板通常会嵌**用户输入**
    （如 ``"oa.ticket.create:{{_user_id}}:{{subject}}:{{_date}}"`` 里的中文标题），
    直接塞进头里会让 ``urllib`` 抛 ``UnicodeEncodeError: 'latin-1'`` ——
    **结果是所有含非 ASCII 参数的写操作都发不出去**。

    这是联调才暴露出来的：单测参数全是 ASCII，永远踩不到。

    用百分号编码而非哈希：同一输入必须得到同一键（否则去重失效），
    同时保留可读的分隔符便于对账。
    """
    return urllib.parse.quote(str(value), safe=_IDEMPOTENCY_SAFE_CHARS)


def assert_header_latin1(name: str, value: str) -> None:
    """头值必须 latin-1 可编码；否则**显式失败**，不做静默改写。

    与幂等键不同：幂等键是我们自己的不透明令牌（编码无损），而 ``header_map``
    里的值往往有业务含义，悄悄改写会让对端看不懂。所以这里选择早失败、报清楚。
    """
    text = "" if value is None else str(value)
    try:
        text.encode("latin-1")
    except UnicodeEncodeError as exc:
        raise HttpCapabilityError(
            ARGS_SCHEMA_INVALID,
            f"头 {name} 的值含非 latin-1 字符（HTTP 头不支持），"
            f"请改用 query/body 承载：{text[:40]!r}",
        ) from exc


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
    """真传输：stdlib ``urllib``（不引入 httpx，与 mcp_client 约定一致）。

    **默认不走环境代理**（``HTTP_PROXY`` / ``http_proxy`` 等）。理由：能力的
    ``base_url`` 是运维选定的**内网**端点，把内网调用经环境里的出口代理转发
    几乎总是错的；而且失败形态是一个看不懂的 502/407，看起来像网络故障而非配置问题。
    （联调时实测踩到：本机设了 ``HTTP_PROXY``，所有能力调用被劫持到出口代理。）

    确实需要代理时显式开：``OPS_CAPABILITY_HTTP_PROXY=http://proxy:3128``。
    """

    def __init__(self) -> None:
        self._opener = _capability_opener()

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
            with self._opener.open(req, timeout=timeout_s) as resp:
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


def _capability_opener() -> urllib.request.OpenerDirector:
    """构造能力调用的 opener：默认不挂代理；配了 ``OPS_CAPABILITY_HTTP_PROXY`` 才挂。"""
    explicit = os.environ.get(_ENV_HTTP_PROXY, "").strip()
    if explicit:
        handler = urllib.request.ProxyHandler({"http": explicit, "https": explicit})
    else:
        handler = urllib.request.ProxyHandler({})  # 空 dict = 不走任何代理
    return urllib.request.build_opener(handler)


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


@dataclass(frozen=True)
class _Prepared:
    """一次调用的全部就绪要素（同步 / 异步路径共用，避免两套逻辑漂移）。"""

    http: dict[str, Any]
    method: str
    url: str
    headers: dict[str, str]
    params: dict[str, Any]
    body: dict[str, Any] | None
    timeout_s: float
    idempotency_key: str | None
    tenant_id: str


class GenericHttpAdapter:
    """声明式 HTTP 能力；``kind=http``。

    契约与 ``LocalFnAdapter`` 相同：``invoke(args, *, ctx) -> Any``（可 JSON 化 dict），
    另提供 ``ainvoke``。

    ⚠️ **async 应用里必须走 ``ainvoke``**：``urllib`` 传输是**阻塞**的，
    在事件循环里同步调用会把整个循环按住（一次 8 秒的下游请求 = 8 秒内所有请求排队）。
    ``ainvoke`` 用 ``asyncio.to_thread`` 把它挪出事件循环。
    """

    kind = "http"

    def __init__(
        self,
        spec: CapabilitySpec,
        *,
        transport: HttpTransport | None = None,
        vault: CredentialVault | None = None,
        store: Any = None,
    ) -> None:
        self._spec = spec
        self._transport = transport
        self._vault = vault
        # 显式注入优先；否则用模块级单例（`set_idempotency_store` 装配）
        self._store = store

    # ---- 对外 ----
    def invoke(self, args: Any, *, ctx: dict[str, Any] | None = None) -> Any:
        """同步调用。**传输阻塞**——async 应用请用 :meth:`ainvoke`。"""
        prepared = self._prepare(args, ctx)
        short_circuit = self._claim(prepared)
        if short_circuit is not None:
            return short_circuit
        try:
            resp = self._call(
                method=prepared.method,
                url=prepared.url,
                headers=prepared.headers,
                params=prepared.params,
                body=prepared.body,
                timeout_s=prepared.timeout_s,
            )
        except HttpCapabilityError as exc:
            self._settle_failure(prepared, exc)
            raise
        return self._finish(prepared, resp)

    async def ainvoke(self, args: Any, *, ctx: dict[str, Any] | None = None) -> Any:
        """异步调用：把阻塞传输挪到线程里，不占住事件循环。

        **DB 版防重存储只有异步接口**，所以生产路径必须走这里。
        """
        import asyncio

        prepared = self._prepare(args, ctx)
        short_circuit = await self._aclaim(prepared)
        if short_circuit is not None:
            return short_circuit
        try:
            resp = await asyncio.to_thread(
                self._call,
                method=prepared.method,
                url=prepared.url,
                headers=prepared.headers,
                params=prepared.params,
                body=prepared.body,
                timeout_s=prepared.timeout_s,
            )
        except HttpCapabilityError as exc:
            await self._asettle_failure(prepared, exc)
            raise
        return await self._afinish(prepared, resp)

    # ---- 就绪 / 防重 / 收束 ----
    def _prepare(self, args: Any, ctx: dict[str, Any] | None) -> _Prepared:
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

        # 头值必须 latin-1 可编码——早失败，别留给 urllib 抛看不懂的 UnicodeEncodeError
        for name, value in headers.items():
            assert_header_latin1(name, value)

        c = ctx or {}
        return _Prepared(
            http=http,
            method=str(http.get("method") or "GET").upper(),
            url=self._resolve_url(http),
            headers=headers,
            params=rendered["params"],
            body=rendered["body"],
            timeout_s=float(http.get("timeout_ms", 8000)) / 1000.0,
            idempotency_key=idem,
            tenant_id=str(c.get("tenant_id") or c.get("_host_tenant") or ""),
        )

    def _store_impl(self) -> Any:
        if self._store is not None:
            return self._store
        return get_idempotency_store()

    async def _astore_call(self, async_name: str, sync_name: str, *args: Any, **kwargs: Any) -> Any:
        """调防重存储：有异步接口就 await，否则把同步实现丢线程。

        **不要直接在事件循环里调同步 store**——那正是刚修掉的阻塞问题。
        """
        import asyncio

        store = self._store_impl()
        fn = getattr(store, async_name, None)
        if callable(fn):
            return await fn(*args, **kwargs)
        return await asyncio.to_thread(getattr(store, sync_name), *args, **kwargs)

    def _claim_from(self, claim: Any, prepared: _Prepared) -> dict[str, Any] | None:
        """把存储层的判定翻成"要不要发请求"。"""
        if claim.should_execute:
            return None
        if claim.duplicate:
            # 已完成过：不再执行，回一个形状一致的载荷，便于调用方对账
            return {
                "protocol": "http",
                "kind": self.kind,
                "capability_id": self._spec.capability_id,
                "status": 0,
                "result": {
                    "code": 0,
                    "msg": "duplicated",
                    "data": {"duplicated": True, "duplicate_of": claim.receipt_id},
                },
                "duplicated": True,
                "duplicate_of": claim.receipt_id,
                "idempotency_key": prepared.idempotency_key,
            }
        raise HttpCapabilityError(DUPLICATE_ID, "同一幂等键正在执行中（in-flight）")

    def _claim(self, prepared: _Prepared) -> dict[str, Any] | None:
        """抢执行权。返回非 ``None`` 表示**不该真的发请求**（已完成 / 正在执行）。"""
        if not prepared.idempotency_key:
            return None
        store = self._store_impl()
        claim_fn = getattr(store, "claim", None)
        if not callable(claim_fn):
            # DB 版只有异步接口：同步路径用它会是错的（而且会阻塞事件循环）
            raise HttpCapabilityError(
                UPSTREAM_ERROR,
                f"{type(store).__name__} 只支持异步接口，请走 ainvoke",
            )
        return self._claim_from(
            claim_fn(
                prepared.idempotency_key,
                capability_id=self._spec.capability_id,
                tenant_id=prepared.tenant_id,
            ),
            prepared,
        )

    async def _aclaim(self, prepared: _Prepared) -> dict[str, Any] | None:
        if not prepared.idempotency_key:
            return None
        claim = await self._astore_call(
            "aclaim",
            "claim",
            prepared.idempotency_key,
            capability_id=self._spec.capability_id,
            tenant_id=prepared.tenant_id,
        )
        return self._claim_from(claim, prepared)

    def _settle_failure(self, prepared: _Prepared, exc: HttpCapabilityError) -> None:
        """失败后的防重状态处理——**只在下游确无副作用时释放**。

        超时 / 连接错误 / 未知业务码一律保持 ``in_flight``，交给租约过期，
        由人工或后续查询确认。宁可拒，也不冒重复执行的风险（fail-closed）。
        """
        if not prepared.idempotency_key or exc.code not in RELEASE_SAFE_ERROR_CODES:
            return
        self._store_impl().release(
            prepared.idempotency_key, tenant_id=prepared.tenant_id
        )

    async def _asettle_failure(
        self, prepared: _Prepared, exc: HttpCapabilityError
    ) -> None:
        if not prepared.idempotency_key or exc.code not in RELEASE_SAFE_ERROR_CODES:
            return
        await self._astore_call(
            "arelease", "release", prepared.idempotency_key, tenant_id=prepared.tenant_id
        )

    def _evaluate(
        self, prepared: _Prepared, resp: HttpResponse
    ) -> tuple[dict[str, Any] | None, HttpCapabilityError | None]:
        """纯评估：成功给 ``(out, None)``；失败给 ``(None, err)``。不含任何存储副作用。"""
        http = prepared.http
        payload = resp.payload if isinstance(resp.payload, dict) else {}
        if not self._is_success(resp, payload, http):
            return None, self._map_upstream_error(payload, http, resp.status)
        out: dict[str, Any] = {
            "protocol": "http",
            "kind": self.kind,
            "capability_id": self._spec.capability_id,
            "status": resp.status,
            "result": payload,
        }
        if self._spec.receipt_capture:
            out["receipt"] = self._capture(payload)
        if prepared.idempotency_key:
            out["idempotency_key"] = prepared.idempotency_key
        return out, None

    def _finish(self, prepared: _Prepared, resp: HttpResponse) -> dict[str, Any]:
        out, err = self._evaluate(prepared, resp)
        if err is not None:
            self._settle_failure(prepared, err)
            raise err
        assert out is not None
        if prepared.idempotency_key:
            # 成功就把键标完成——**"执行完成了"是适配器掌握的事实**，
            # 不能等上层来标（否则直接用适配器的调用会一直卡在 in_flight）。
            # 回执 id 由 gateway 在落完回执后补上（complete 支持二次调用更新关联）。
            self._store_impl().complete(
                prepared.idempotency_key, tenant_id=prepared.tenant_id
            )
        return out

    async def _afinish(self, prepared: _Prepared, resp: HttpResponse) -> dict[str, Any]:
        out, err = self._evaluate(prepared, resp)
        if err is not None:
            await self._asettle_failure(prepared, err)
            raise err
        assert out is not None
        if prepared.idempotency_key:
            await self._astore_call(
                "acomplete",
                "complete",
                prepared.idempotency_key,
                tenant_id=prepared.tenant_id,
            )
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
        # 幂等键进 HTTP 头 → 必须 ASCII 安全（否则含中文参数的写操作全发不出去）
        return ascii_idempotency_key(self._render_value(template, scope))

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
