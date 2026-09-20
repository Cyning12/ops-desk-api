"""Capability 层红线（否决项）。

**红线不是准确率。** 准确率掉分可以接受，红线被突破**整体不通过**——
不允许"用别处的高分补一处红线"。

每条红线有两个断言，缺一不可：

- **正向**：该拦的拦住了
- **反向对照**：该放行的放行了

只做正向会得到**假通过**——"一律拒绝"天然满足"未授权访问被拒绝"，
一个坏掉的闸门和一个严到不可用的闸门，在正向断言下长得一模一样。

清单在 `evals/agent/redlines/capability_v1.yaml`；本文件是它的实现，
两者必须一一对应（R0 守这条）。

跑这一层：`pytest -m redline`
"""

from __future__ import annotations

import asyncio
import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Any, Callable

import pytest
import yaml

from app.ops.capability import (
    GenericHttpAdapter,
    InMemoryIdempotencyStore,
    InMemoryReceiptSink,
    ainvoke,
    invoke,
    register,
    reset_idempotency_store,
    reset_receipt_sink,
    set_idempotency_store,
    set_receipt_sink,
    unregister,
)
from app.ops.capability.adapters import (
    FakeHttpTransport,
    HttpCapabilityError,
    StaticCredentialVault,
)
from app.ops.capability.defaults import ensure_default_capabilities
from app.ops.capability.gateway import get_registry
from app.ops.capability.manifest import ManifestError, load_capability_manifest
from app.ops.capability.types import CapabilitySpec

pytestmark = pytest.mark.redline

_INVENTORY = (
    Path(__file__).resolve().parents[2] / "evals" / "agent" / "redlines" / "capability_v1.yaml"
)

#: redline_id → 实现它的测试函数名（由 @redline 装饰器登记）
IMPLEMENTED: dict[str, str] = {}


def redline(redline_id: str) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    def decorate(fn: Callable[..., Any]) -> Callable[..., Any]:
        IMPLEMENTED[redline_id] = fn.__name__
        fn.__doc__ = f"[{redline_id}] {fn.__doc__ or ''}"
        return fn

    return decorate


def assert_redline(
    *, redline_id: str, holds: bool, control: bool, detail: str = ""
) -> None:
    """正向必须成立；反向对照也必须成立，否则说明这条红线是空真。"""
    assert holds, f"[{redline_id}] 红线被突破：{detail}"
    assert control, (
        f"[{redline_id}] 反向对照不成立——该放行的被拦住了，"
        f"这条红线可能是'一律拒绝'造成的假通过：{detail}"
    )


def _declared_redlines() -> list[dict[str, Any]]:
    return yaml.safe_load(_INVENTORY.read_text(encoding="utf-8"))["redlines"]


def _declared_ids() -> set[str]:
    return {r["id"] for r in _declared_redlines()}


# ---------------- 公共装置 ----------------

_ARGS = {"type": "object", "properties": {"subject": {"type": "string"}}}
_WRITE_HTTP = {
    "method": "POST",
    "base_url": "OA_BASE",
    "path": "/api/v1/ticket/create",
    "auth": "oa_gateway_token",
    "query_map": {},
    "body_map": {"subject": "{{subject}}"},
    "idempotency_key": "t:{{subject}}",
    "timeout_ms": 2000,
    "success_when": {"path": "$.code", "in": [0]},
    "error_map": {"1001": "args_schema_invalid", "2003": "permission_denied"},
}


def _spec(cid: str, **over: Any) -> CapabilitySpec:
    http = dict(_WRITE_HTTP)
    http.update(over.pop("http", {}))
    base: dict[str, Any] = dict(
        capability_id=cid,
        kind="http",
        description="红线单测",
        args_schema=dict(_ARGS),
        tags=("oa",),
        side_effect="write",
        hitl_required=True,
        when_to_use="红线单测",
        visibility={"departments": ["all"], "roles": ["all"]},
        http=http,
    )
    base.update(over)
    return CapabilitySpec(**base)


def _adapter(spec: CapabilitySpec, tx: Any) -> GenericHttpAdapter:
    return GenericHttpAdapter(
        spec,
        transport=tx,
        vault=StaticCredentialVault({"oa_gateway_token": "s3cret"}),
    )


def _register(spec: CapabilitySpec, tx: Any) -> None:
    register(spec, _adapter(spec, tx))


@pytest.fixture(autouse=True)
def _clean(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("OA_BASE", "http://oa.test.local")
    monkeypatch.delenv("OPS_CAPABILITY_HTTP_PROXY", raising=False)
    reset_idempotency_store()
    reset_receipt_sink()
    yield
    get_registry().clear()
    reset_idempotency_store()
    reset_receipt_sink()
    ensure_default_capabilities()


_CTX_WRITE = {"tenant_id": "t1", "_host_policy": {"allow_write": True}}


def _inner_data(result: Any) -> dict[str, Any]:
    """取代理侧信封里的下游响应体（``output["result"]["data"]``）。"""
    if not result.ok or not isinstance(result.output, dict):
        return {}
    inner = result.output.get("result")
    return (inner or {}).get("data") or {}


# ---------------- R0：清单与实现对齐 ----------------


@redline("R0")
def test_r0_inventory_matches_implementation():
    """清单里声明的红线必须都有实现，实现的红线必须都在清单里。"""
    declared = _declared_ids()
    implemented = set(IMPLEMENTED) | {"R0"}  # R0 由本测试自身实现

    missing_impl = sorted(declared - implemented)
    undeclared = sorted(implemented - declared)
    assert_redline(
        redline_id="R0",
        holds=not missing_impl and not undeclared,
        control=len(declared) >= 7,
        detail=f"声明未实现={missing_impl} 实现未声明={undeclared}",
    )


# ---------------- R1：无放行时写必须拒，且下游零请求 ----------------


@redline("R1")
def test_r1_write_blocked_without_host_policy_and_no_downstream_request():
    """无写放行 → 拒绝且请求不出门；有放行 → 放行且请求出门。"""
    spec = _spec("r1.write")
    tx = FakeHttpTransport(payload={"code": 0, "data": {"ticketId": "T-R1"}})
    _register(spec, tx)
    try:
        blocked = invoke("r1.write", {"subject": "x"}, ctx={"tenant_id": "t1"})
        holds = (
            blocked.ok is False
            and str(blocked.error).startswith("policy_blocked")
            and tx.calls == []
        )

        allowed = invoke("r1.write", {"subject": "x"}, ctx=dict(_CTX_WRITE))
        control = allowed.ok is True and len(tx.calls) == 1
    finally:
        unregister("r1.write")

    assert_redline(
        redline_id="R1",
        holds=holds,
        control=control,
        detail=f"blocked={blocked.error if not blocked.ok else 'ok'} calls={len(tx.calls)}",
    )


# ---------------- R2：未声明模板变量不得静默 ----------------


@redline("R2")
def test_r2_undeclared_template_variable_never_silently_renders(tmp_path: Path):
    """未声明变量 → 加载期就拒；声明了就通过（对照）。"""
    bad = tmp_path / "bad.json"
    bad.write_text(
        json.dumps(
            {
                "version": 1,
                "capabilities": [
                    {
                        "id": "r2.bad",
                        "kind": "http",
                        "description": "x",
                        "when_to_use": "红线",
                        "side_effect": "read",
                        "tags": ["oa"],
                        "visibility": {"departments": ["all"]},
                        "args_schema": {"type": "object", "properties": {}},
                        "http": {
                            "method": "GET",
                            "base_url": "OA_BASE",
                            "path": "/x",
                            "auth": "oa_gateway_token",
                            "query_map": {"q": "{{not_declared}}"},
                            "success_when": {"path": "$.code", "in": [0]},
                            "error_map": {"1001": "args_schema_invalid"},
                        },
                    }
                ],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    try:
        load_capability_manifest(bad)
        holds = False
    except ManifestError as exc:
        holds = "模板变量未声明" in str(exc)

    # 对照：把变量声明进 args_schema 就能过（证明拒绝是因为"未声明"，不是别的）
    ok = tmp_path / "ok.json"
    ok.write_text(
        bad.read_text(encoding="utf-8")
        .replace("{{not_declared}}", "{{keyword}}")
        .replace('"properties": {}', '"properties": {"keyword": {"type": "string"}}'),
        encoding="utf-8",
    )
    control = load_capability_manifest(ok).registered_ids == ("r2.bad",)
    unregister("r2.bad")

    assert_redline(redline_id="R2", holds=holds, control=control)


# ---------------- R3：错误不得泄漏下游原文 ----------------


@redline("R3")
def test_r3_downstream_message_never_leaks_to_caller():
    """下游错误原文不外泄；同时错误串必须是"有内容的稳定码"而非空。"""
    leaky = "内部堆栈: at com.oa.internal.Foo.bar(Foo.java:42)"
    spec = _spec("r3.read", side_effect="read", http={"method": "GET", "body_map": {},
                                                       "idempotency_key": None,
                                                       "query_map": {"q": "{{subject}}"}})
    tx = FakeHttpTransport(payload={"code": 1001, "msg": leaky})
    _register(spec, tx)
    try:
        result = invoke("r3.read", {"subject": "x"})
        err = str(result.error)
        holds = (not result.ok) and "com.oa.internal" not in err and leaky not in err
        # 对照：错误串必须是可决策的稳定码，不能是空/None（否则"没泄漏"是假通过）
        control = err.startswith("args_schema_invalid") and len(err) > len(
            "args_schema_invalid"
        )
    finally:
        unregister("r3.read")

    assert_redline(
        redline_id="R3", holds=holds, control=control, detail=f"error={result.error!r}"
    )


# ---------------- R4：含非 ASCII 参数的写调用必须成功 ----------------


@redline("R4")
def test_r4_non_ascii_write_succeeds_with_ascii_safe_key():
    """中文参数的写调用必须发得出去；同时幂等键仍能区分不同输入（不是被抹平）。"""
    spec = _spec("r4.write")
    tx = FakeHttpTransport(payload={"code": 0, "data": {"ticketId": "T-R4"}})
    _register(spec, tx)
    try:
        first = invoke("r4.write", {"subject": "打印机故障"}, ctx=dict(_CTX_WRITE))
        key1 = tx.calls[0]["headers"]["Idempotency-Key"]
        key1.encode("latin-1")  # 不抛即 ASCII 安全
        holds = first.ok is True and len(tx.calls) == 1

        second = invoke("r4.write", {"subject": "复印件故障"}, ctx=dict(_CTX_WRITE))
        key2 = tx.calls[1]["headers"]["Idempotency-Key"]
        # 对照：不同输入必须得到不同键，否则"能把中文塞进去"是靠抹平换来的
        control = second.ok is True and key1 != key2 and "打印机" not in key1
    finally:
        unregister("r4.write")

    assert_redline(redline_id="R4", holds=holds, control=control, detail=f"key={key1}")


# ---------------- R5：写超时不得重发 ----------------


@redline("R5")
def test_r5_write_timeout_never_retries_but_read_may():
    """写超时只发 1 次；读超时可重试（证明"不重试"是写特有的策略，不是全局禁重试）。"""
    wspec = _spec("r5.write")
    wtx = FakeHttpTransport(exc=TimeoutError("timeout"))
    _register(wspec, wtx)

    rspec = _spec(
        "r5.read",
        side_effect="read",
        http={"method": "GET", "body_map": {}, "idempotency_key": None,
              "query_map": {"q": "{{subject}}"}},
    )
    rtx = FakeHttpTransport(exc=TimeoutError("timeout"))
    _register(rspec, rtx)
    try:
        invoke("r5.write", {"subject": "x"}, ctx=dict(_CTX_WRITE))
        invoke("r5.read", {"subject": "x"})
        holds = len(wtx.calls) == 1
        control = len(rtx.calls) == 2
    finally:
        unregister("r5.write")
        unregister("r5.read")

    assert_redline(
        redline_id="R5",
        holds=holds,
        control=control,
        detail=f"write_calls={len(wtx.calls)} read_calls={len(rtx.calls)}",
    )


# ---------------- R6：不得经环境代理 ----------------


def _local_server() -> tuple[HTTPServer, str]:
    class _H(BaseHTTPRequestHandler):
        def do_GET(self) -> None:  # noqa: N802
            body = b'{"code":0,"data":{}}'
            self.send_response(200)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *args: Any) -> None:
            return

    server = HTTPServer(("127.0.0.1", 0), _H)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server, f"http://127.0.0.1:{server.server_address[1]}/probe"


@redline("R6")
def test_r6_ambient_proxy_never_hijacks_but_explicit_proxy_is_honored(
    monkeypatch: pytest.MonkeyPatch,
):
    """环境代理不可劫持内网调用；显式配的代理仍然生效（对照——证明不是"代理被整体禁用"）。"""
    from app.ops.capability.adapters import UrllibHttpTransport

    server, url = _local_server()
    try:
        monkeypatch.setenv("HTTP_PROXY", "http://127.0.0.1:1")
        monkeypatch.setenv("http_proxy", "http://127.0.0.1:1")
        monkeypatch.delenv("NO_PROXY", raising=False)
        monkeypatch.delenv("no_proxy", raising=False)
        monkeypatch.delenv("OPS_CAPABILITY_HTTP_PROXY", raising=False)
        resp = UrllibHttpTransport().request(
            method="GET", url=url, headers={}, params={}, body=None, timeout_s=5
        )
        holds = resp.status == 200

        monkeypatch.setenv("OPS_CAPABILITY_HTTP_PROXY", "http://127.0.0.1:1")
        try:
            UrllibHttpTransport().request(
                method="GET", url=url, headers={}, params={}, body=None, timeout_s=3
            )
            control = False
        except HttpCapabilityError:
            control = True  # 显式代理确实被用上了
    finally:
        server.shutdown()

    assert_redline(redline_id="R6", holds=holds, control=control)


# ---------------- R7：命中幂等键不得再发请求、不得留第二条回执 ----------------


@redline("R7")
def test_r7_duplicate_hits_do_not_call_downstream_and_leave_no_second_receipt():
    """同 key 第二次：零请求、零新回执；换 key 则正常执行（对照）。"""
    store = InMemoryIdempotencyStore()
    set_idempotency_store(store)
    sink = InMemoryReceiptSink()
    set_receipt_sink(sink)

    spec = _spec("r7.write")
    tx = FakeHttpTransport(payload={"code": 0, "data": {"ticketId": "T-R7"}})
    _register(spec, tx)
    try:
        invoke("r7.write", {"subject": "same"}, ctx=dict(_CTX_WRITE))
        dup = invoke("r7.write", {"subject": "same"}, ctx=dict(_CTX_WRITE))
        calls_after_dup = len(tx.calls)
        receipts_after_dup = len(sink)

        holds = (
            dup.ok is True
            and dup.meta.get("duplicated") is True
            and calls_after_dup == 1
            and receipts_after_dup == 1
        )

        # 对照：换一个 args → 新 key → 必须真的执行（防重不是"只允许一次"）
        invoke("r7.write", {"subject": "other"}, ctx=dict(_CTX_WRITE))
        control = len(tx.calls) == 2 and len(sink) == 2
    finally:
        unregister("r7.write")

    assert_redline(
        redline_id="R7",
        holds=holds,
        control=control,
        detail=f"calls={len(tx.calls)} receipts={len(sink)}",
    )


# ---------------- R8：db 持久化下同步 invoke 必须 fail-closed ----------------


class _AsyncOnlyIdempotencyStore:
    """``DbIdempotencyStore`` 的形态：**只有异步接口**，没有同步 claim / complete。

    用替身而不是真连数据库：这条红线守的性质（"拿不到同步防重判定就必须 fail-closed"）
    与数据库无关；而且红线层必须在**没有 DB 的 CI** 里也跑得起来——
    真连库的话 DB 不可用时红线会静默失效，那正是 R0 要防的事。
    """

    def __init__(self, inner: InMemoryIdempotencyStore) -> None:
        self._inner = inner

    async def aclaim(self, key: str, *, capability_id: str = "", tenant_id: str = ""):
        return await self._inner.aclaim(
            key, capability_id=capability_id, tenant_id=tenant_id
        )

    async def acomplete(self, key: str, *, receipt_id: str = "", tenant_id: str = ""):
        await self._inner.acomplete(
            key, receipt_id=receipt_id, tenant_id=tenant_id
        )


@redline("R8")
def test_r8_async_only_store_fails_closed_on_sync_invoke():
    """存储只有异步接口时：同步 invoke 必须失败且**请求不出门**；ainvoke 必须正常执行。"""
    inner = InMemoryIdempotencyStore()
    set_idempotency_store(_AsyncOnlyIdempotencyStore(inner))
    sink = InMemoryReceiptSink()
    set_receipt_sink(sink)

    spec = _spec("r8.write")
    tx = FakeHttpTransport(payload={"code": 0, "data": {"ticketId": "T-R8"}})
    _register(spec, tx)
    try:
        blocked = invoke("r8.write", {"subject": "x"}, ctx=dict(_CTX_WRITE))
        holds = (
            blocked.ok is False
            and "ainvoke" in str(blocked.error)
            and tx.calls == []  # ★ 防重没生效就绝不能发请求
        )

        async def _run() -> Any:
            return await ainvoke("r8.write", {"subject": "x"}, ctx=dict(_CTX_WRITE))

        allowed = asyncio.run(_run())
        # 注意：被拦下的同步调用**也留了一条回执**（写能力无论成败都落回执，是既有设计），
        # 所以这里不能数"回执条数 == 1"，而要断言"确实执行过一次写并留下了 write_confirmed"。
        control = (
            allowed.ok is True
            and len(tx.calls) == 1
            and any(r.write_confirmed for r in sink.all())
        )
    finally:
        unregister("r8.write")

    assert_redline(
        redline_id="R8",
        holds=holds,
        control=control,
        detail=f"blocked={blocked.error!r} calls={len(tx.calls)} receipts={len(sink)}",
    )


# ---------------- R9：幂等命中必须重放上次的业务结果 ----------------


@redline("R9")
def test_r9_duplicate_hit_replays_previous_business_fields():
    """命中必须重放上次业务字段；换 key 必须真执行（对照——防重不是"永远返回第一次的结果"）。"""
    set_idempotency_store(InMemoryIdempotencyStore())
    sink = InMemoryReceiptSink()
    set_receipt_sink(sink)

    spec = _spec("r9.write", receipt_capture=("$.data.ticketId",))
    tx = FakeHttpTransport(payload={"code": 0, "data": {"ticketId": "T-R9"}})
    _register(spec, tx)
    try:
        first = invoke("r9.write", {"subject": "same"}, ctx=dict(_CTX_WRITE))
        dup = invoke("r9.write", {"subject": "same"}, ctx=dict(_CTX_WRITE))
        d1 = _inner_data(first)
        d2 = _inner_data(dup)
        holds = (
            dup.ok is True
            and dup.meta.get("duplicated") is True
            and d2.get("ticketId") == d1.get("ticketId") == "T-R9"
            and len(tx.calls) == 1  # 重放不是"再打一次下游换结果"
        )

        # 对照：换 key 必须真的执行，而不是命中缓存
        other = invoke("r9.write", {"subject": "other"}, ctx=dict(_CTX_WRITE))
        control = (
            len(tx.calls) == 2
            and not other.meta.get("duplicated")
            and _inner_data(other).get("ticketId") == "T-R9"
        )
    finally:
        unregister("r9.write")

    assert_redline(
        redline_id="R9",
        holds=holds,
        control=control,
        detail=f"first={d1} dup={d2} calls={len(tx.calls)}",
    )
