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
from collections.abc import Callable
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Any

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


# ---------------- R10：声明了结果契约就必须校验 ----------------


def _r10_spec(cid: str, contract: dict[str, Any] | None, **over: Any) -> CapabilitySpec:
    if contract is None:
        return _spec(cid, **over)
    return _spec(cid, output_schema=contract, **over)


@redline("R10")
def test_r10_declared_contract_rejects_nonconforming_result():
    """结果缺必填字段必须判失败（upstream_error + 契约 detail）；
    合规结果必须成功；**未声明契约**的能力不得被推测性拦截。"""
    contract = {"required": ["$.data.ticketId"]}
    spec = _r10_spec("r10.write", contract)
    bad = FakeHttpTransport(payload={"code": 0, "data": {}})  # 声明了 ticketId 却没有
    _register(spec, bad)
    try:
        violated = invoke("r10.write", {"subject": "x"}, ctx=dict(_CTX_WRITE))
        detail = str(violated.error or "")
        holds = (
            violated.ok is False
            and detail.startswith("upstream_error")  # ★ 不新造错误码
            and "result_contract" in detail
            and violated.meta.get("result_contract_violated") is True
        )
    finally:
        unregister("r10.write")

    # 对照一：合规结果必须照常成功（不是"一律失败"）
    good = FakeHttpTransport(payload={"code": 0, "data": {"ticketId": "T-R10"}})
    _register(_r10_spec("r10.write", contract), good)
    try:
        ok_call = invoke("r10.write", {"subject": "x"}, ctx=dict(_CTX_WRITE))
        control_ok = ok_call.ok is True and _inner_data(ok_call).get("ticketId") == "T-R10"
    finally:
        unregister("r10.write")

    # 对照二：没声明契约 → 同样残缺的返回**照旧成功**（契约是显式声明出来的，
    # 系统不替你猜；擅自拦截会把"能用"变成"随机不可用"）
    _register(_r10_spec("r10.free", None), bad)
    try:
        free = invoke("r10.free", {"subject": "x"}, ctx=dict(_CTX_WRITE))
        control_free = free.ok is True and not free.meta.get("result_contract_violated")
    finally:
        unregister("r10.free")

    assert_redline(
        redline_id="R10",
        holds=holds,
        control=control_ok and control_free,
        detail=f"violated={violated.error!r} ok={ok_call.ok} free={free.ok}",
    )


def test_r10_is_not_vacuous(monkeypatch: pytest.MonkeyPatch):
    """变异检验：把契约校验摘掉，上面那条红线的正向断言必须**翻掉**。

    不翻 = 说明它被别的东西（比如本来就失败）满足了，是空真。
    """
    import app.ops.capability.gateway as gw

    monkeypatch.setattr(gw, "_result_contract_verdict", lambda spec, output: None)
    spec = _r10_spec("r10.mut", {"required": ["$.data.ticketId"]})
    tx = FakeHttpTransport(payload={"code": 0, "data": {}})
    _register(spec, tx)
    try:
        res = invoke("r10.mut", {"subject": "x"}, ctx=dict(_CTX_WRITE))
    finally:
        unregister("r10.mut")
    # 摘掉校验后，残缺结果重新变回 ok=True —— 证明拦住它的确实是契约，不是别的
    assert res.ok is True, f"变异未翻转：契约被摘掉后仍然失败 err={res.error!r}"


# ---------------- R11：会话配额 + kill switch ----------------


@redline("R11")
def test_r11_session_budget_and_kill_switch_block_before_downstream(
    monkeypatch: pytest.MonkeyPatch,
):
    """配额耗尽 / kill switch 命中 → 拦下且下游零请求；
    换会话仍能打；**被拦下的调用不计数**（否则兜底会误伤正常调用）。"""
    from app.ops.capability import budget

    monkeypatch.setenv("OPS_CAPABILITY_MAX_WRITES_PER_SESSION", "1")
    monkeypatch.setenv("OPS_CAPABILITY_MAX_CALLS_PER_SESSION", "0")  # 0 = 不限，只测写数
    budget.reset()

    tx = FakeHttpTransport(payload={"code": 0, "data": {"ticketId": "T-R11"}})
    _register(_spec("r11.write"), tx)
    try:
        sess = {"tenant_id": "t1", "run_id": "run-A", "_host_policy": {"allow_write": True}}
        first = invoke("r11.write", {"subject": "a"}, ctx=dict(sess))
        second = invoke("r11.write", {"subject": "b"}, ctx=dict(sess))
        detail = str(second.error or "")
        holds = (
            first.ok is True
            and second.ok is False
            and detail.startswith("policy_blocked")  # ★ 不新造错误码
            and "budget_exhausted" in detail
            and second.meta.get("blocked") == "budget"
            and len(tx.calls) == 1  # 第二次根本没出门
        )

        # 对照一：换一个会话照样能打（配额是 per-session，不是全局一律拒绝）
        other = invoke(
            "r11.write",
            {"subject": "c"},
            ctx={"tenant_id": "t1", "run_id": "run-B", "_host_policy": {"allow_write": True}},
        )
        control_other_session = other.ok is True and len(tx.calls) == 2

        # 对照二：被拦下的调用**不计数** ——否则"反复尝试都被拒"会打满配额，
        # 让一次正常调用也被误伤（兜底变成另一种不可用）
        budget.reset()
        blocked_ctx = {
            "tenant_id": "t1",
            "run_id": "run-C",
            # 故意不给 allow_write：这次会被 Policy 拦下，不该消耗配额
        }
        for _ in range(3):
            invoke("r11.write", {"subject": "z"}, ctx=dict(blocked_ctx))
        snap = budget.snapshot()
        used = snap["sessions"].get("run-C", {"writes": 0})
        control_not_counted = used["writes"] == 0
    finally:
        unregister("r11.write")

    assert_redline(
        redline_id="R11",
        holds=holds,
        control=control_other_session and control_not_counted,
        detail=(
            f"second={second.error!r} calls={len(tx.calls)} "
            f"other={other.ok} used_runC={used}"
        ),
    )


@redline("R11")
def test_r11_kill_switch_disables_capability(monkeypatch: pytest.MonkeyPatch):
    """kill switch 命中 → disabled 且下游零请求；不命中/关掉开关 → 照常放行。"""
    from app.ops.capability import budget

    monkeypatch.setenv("OPS_CAPABILITY_KILL_SWITCH", "r11.*")
    budget.reset()
    tx = FakeHttpTransport(payload={"code": 0, "data": {"ticketId": "T-KS"}})
    _register(_spec("r11.killed"), tx)
    try:
        killed = invoke("r11.killed", {"subject": "x"}, ctx=dict(_CTX_WRITE))
        detail = str(killed.error or "")
        holds = (
            killed.ok is False
            and detail.startswith("disabled")  # ★ 不新造错误码
            and "kill_switch" in detail
            and killed.meta.get("blocked") == "kill_switch"
            and tx.calls == []
        )
    finally:
        unregister("r11.killed")

    # 对照：关掉开关 → 同一个能力照常放行（开关是"停用"，不是"这个 id 永久坏了"）
    monkeypatch.delenv("OPS_CAPABILITY_KILL_SWITCH")
    budget.reset()
    tx2 = FakeHttpTransport(payload={"code": 0, "data": {"ticketId": "T-KS"}})
    _register(_spec("r11.killed"), tx2)
    try:
        alive = invoke("r11.killed", {"subject": "x"}, ctx=dict(_CTX_WRITE))
        control = alive.ok is True and len(tx2.calls) == 1
    finally:
        unregister("r11.killed")

    assert_redline(
        redline_id="R11",
        holds=holds,
        control=control,
        detail=f"killed={killed.error!r} alive={alive.ok} calls={len(tx2.calls)}",
    )


def test_r11_is_not_vacuous(monkeypatch: pytest.MonkeyPatch):
    """变异检验：把配额检查摘掉，超配额那次必须**真的打到了下游**。

    不翻 = 说明拦住它的是别的东西（比如 Policy），这条红线是空真。
    """
    import app.ops.capability.gateway as gw

    monkeypatch.setenv("OPS_CAPABILITY_MAX_WRITES_PER_SESSION", "1")
    monkeypatch.setenv("OPS_CAPABILITY_MAX_CALLS_PER_SESSION", "0")
    monkeypatch.setattr(gw, "budget_check", lambda spec, *, ctx: None)

    tx = FakeHttpTransport(payload={"code": 0, "data": {"ticketId": "T-MUT"}})
    _register(_spec("r11.mut"), tx)
    try:
        sess = {"tenant_id": "t1", "run_id": "run-M", "_host_policy": {"allow_write": True}}
        invoke("r11.mut", {"subject": "a"}, ctx=dict(sess))
        second = invoke("r11.mut", {"subject": "b"}, ctx=dict(sess))
    finally:
        unregister("r11.mut")
    assert second.ok is True and len(tx.calls) == 2, (
        f"变异未翻转：配额被摘掉后第二次仍被拦 err={second.error!r}"
    )


# ---------------- R10：声明了结果契约就必须校验 ----------------


def _r10_spec(cid: str, contract: dict[str, Any] | None, **over: Any) -> CapabilitySpec:
    if contract is None:
        return _spec(cid, **over)
    return _spec(cid, output_schema=contract, **over)


@redline("R10")
def test_r10_declared_contract_rejects_nonconforming_result():
    """结果缺必填字段必须判失败（upstream_error + 契约 detail）；
    合规结果必须成功；**未声明契约**的能力不得被推测性拦截。"""
    contract = {"required": ["$.data.ticketId"]}
    spec = _r10_spec("r10.write", contract)
    bad = FakeHttpTransport(payload={"code": 0, "data": {}})  # 声明了 ticketId 却没有
    _register(spec, bad)
    try:
        violated = invoke("r10.write", {"subject": "x"}, ctx=dict(_CTX_WRITE))
        detail = str(violated.error or "")
        holds = (
            violated.ok is False
            and detail.startswith("upstream_error")  # ★ 不新造错误码
            and "result_contract" in detail
            and violated.meta.get("result_contract_violated") is True
        )
    finally:
        unregister("r10.write")

    # 对照一：合规结果必须照常成功（不是"一律失败"）
    good = FakeHttpTransport(payload={"code": 0, "data": {"ticketId": "T-R10"}})
    _register(_r10_spec("r10.write", contract), good)
    try:
        ok_call = invoke("r10.write", {"subject": "x"}, ctx=dict(_CTX_WRITE))
        control_ok = ok_call.ok is True and _inner_data(ok_call).get("ticketId") == "T-R10"
    finally:
        unregister("r10.write")

    # 对照二：没声明契约 → 同样残缺的返回**照旧成功**（契约是显式声明出来的，
    # 系统不替你猜；擅自拦截会把"能用"变成"随机不可用"）
    _register(_r10_spec("r10.free", None), bad)
    try:
        free = invoke("r10.free", {"subject": "x"}, ctx=dict(_CTX_WRITE))
        control_free = free.ok is True and not free.meta.get("result_contract_violated")
    finally:
        unregister("r10.free")

    assert_redline(
        redline_id="R10",
        holds=holds,
        control=control_ok and control_free,
        detail=f"violated={violated.error!r} ok={ok_call.ok} free={free.ok}",
    )


def test_r10_is_not_vacuous(monkeypatch: pytest.MonkeyPatch):
    """变异检验：把契约校验摘掉，上面那条红线的正向断言必须**翻掉**。

    不翻 = 说明它被别的东西（比如本来就失败）满足了，是空真。
    """
    import app.ops.capability.gateway as gw

    monkeypatch.setattr(gw, "_result_contract_verdict", lambda spec, output: None)
    spec = _r10_spec("r10.mut", {"required": ["$.data.ticketId"]})
    tx = FakeHttpTransport(payload={"code": 0, "data": {}})
    _register(spec, tx)
    try:
        res = invoke("r10.mut", {"subject": "x"}, ctx=dict(_CTX_WRITE))
    finally:
        unregister("r10.mut")
    # 摘掉校验后，残缺结果重新变回 ok=True —— 证明拦住它的确实是契约，不是别的
    assert res.ok is True, f"变异未翻转：契约被摘掉后仍然失败 err={res.error!r}"


# ---------------- R11：会话配额 + kill switch ----------------


@redline("R11")
def test_r11_session_budget_and_kill_switch_block_before_downstream(
    monkeypatch: pytest.MonkeyPatch,
):
    """配额耗尽 / kill switch 命中 → 拦下且下游零请求；
    换会话仍能打；**被拦下的调用不计数**（否则兜底会误伤正常调用）。"""
    from app.ops.capability import budget

    monkeypatch.setenv("OPS_CAPABILITY_MAX_WRITES_PER_SESSION", "1")
    monkeypatch.setenv("OPS_CAPABILITY_MAX_CALLS_PER_SESSION", "0")  # 0 = 不限，只测写数
    budget.reset()

    tx = FakeHttpTransport(payload={"code": 0, "data": {"ticketId": "T-R11"}})
    _register(_spec("r11.write"), tx)
    try:
        sess = {"tenant_id": "t1", "run_id": "run-A", "_host_policy": {"allow_write": True}}
        first = invoke("r11.write", {"subject": "a"}, ctx=dict(sess))
        second = invoke("r11.write", {"subject": "b"}, ctx=dict(sess))
        detail = str(second.error or "")
        holds = (
            first.ok is True
            and second.ok is False
            and detail.startswith("policy_blocked")  # ★ 不新造错误码
            and "budget_exhausted" in detail
            and second.meta.get("blocked") == "budget"
            and len(tx.calls) == 1  # 第二次根本没出门
        )

        # 对照一：换一个会话照样能打（配额是 per-session，不是全局一律拒绝）
        other = invoke(
            "r11.write",
            {"subject": "c"},
            ctx={"tenant_id": "t1", "run_id": "run-B", "_host_policy": {"allow_write": True}},
        )
        control_other_session = other.ok is True and len(tx.calls) == 2

        # 对照二：被拦下的调用**不计数** ——否则"反复尝试都被拒"会打满配额，
        # 让一次正常调用也被误伤（兜底变成另一种不可用）
        budget.reset()
        blocked_ctx = {
            "tenant_id": "t1",
            "run_id": "run-C",
            # 故意不给 allow_write：这次会被 Policy 拦下，不该消耗配额
        }
        for _ in range(3):
            invoke("r11.write", {"subject": "z"}, ctx=dict(blocked_ctx))
        snap = budget.snapshot()
        used = snap["sessions"].get("run-C", {"writes": 0})
        control_not_counted = used["writes"] == 0
    finally:
        unregister("r11.write")

    assert_redline(
        redline_id="R11",
        holds=holds,
        control=control_other_session and control_not_counted,
        detail=(
            f"second={second.error!r} calls={len(tx.calls)} "
            f"other={other.ok} used_runC={used}"
        ),
    )


@redline("R11")
def test_r11_kill_switch_disables_capability(monkeypatch: pytest.MonkeyPatch):
    """kill switch 命中 → disabled 且下游零请求；不命中/关掉开关 → 照常放行。"""
    from app.ops.capability import budget

    monkeypatch.setenv("OPS_CAPABILITY_KILL_SWITCH", "r11.*")
    budget.reset()
    tx = FakeHttpTransport(payload={"code": 0, "data": {"ticketId": "T-KS"}})
    _register(_spec("r11.killed"), tx)
    try:
        killed = invoke("r11.killed", {"subject": "x"}, ctx=dict(_CTX_WRITE))
        detail = str(killed.error or "")
        holds = (
            killed.ok is False
            and detail.startswith("disabled")  # ★ 不新造错误码
            and "kill_switch" in detail
            and killed.meta.get("blocked") == "kill_switch"
            and tx.calls == []
        )
    finally:
        unregister("r11.killed")

    # 对照：关掉开关 → 同一个能力照常放行（开关是"停用"，不是"这个 id 永久坏了"）
    monkeypatch.delenv("OPS_CAPABILITY_KILL_SWITCH")
    budget.reset()
    tx2 = FakeHttpTransport(payload={"code": 0, "data": {"ticketId": "T-KS"}})
    _register(_spec("r11.killed"), tx2)
    try:
        alive = invoke("r11.killed", {"subject": "x"}, ctx=dict(_CTX_WRITE))
        control = alive.ok is True and len(tx2.calls) == 1
    finally:
        unregister("r11.killed")

    assert_redline(
        redline_id="R11",
        holds=holds,
        control=control,
        detail=f"killed={killed.error!r} alive={alive.ok} calls={len(tx2.calls)}",
    )


def test_r11_is_not_vacuous(monkeypatch: pytest.MonkeyPatch):
    """变异检验：把配额检查摘掉，超配额那次必须**真的打到了下游**。

    不翻 = 说明拦住它的是别的东西（比如 Policy），这条红线是空真。
    """
    import app.ops.capability.gateway as gw

    monkeypatch.setenv("OPS_CAPABILITY_MAX_WRITES_PER_SESSION", "1")
    monkeypatch.setenv("OPS_CAPABILITY_MAX_CALLS_PER_SESSION", "0")
    monkeypatch.setattr(gw, "budget_check", lambda spec, *, ctx: None)

    tx = FakeHttpTransport(payload={"code": 0, "data": {"ticketId": "T-MUT"}})
    _register(_spec("r11.mut"), tx)
    try:
        sess = {"tenant_id": "t1", "run_id": "run-M", "_host_policy": {"allow_write": True}}
        invoke("r11.mut", {"subject": "a"}, ctx=dict(sess))
        second = invoke("r11.mut", {"subject": "b"}, ctx=dict(sess))
    finally:
        unregister("r11.mut")
    assert second.ok is True and len(tx.calls) == 2, (
        f"变异未翻转：配额被摘掉后第二次仍被拦 err={second.error!r}"
    )


# ---------------- R12：下游熔断（三态 + 只计环境类失败）----------------


def _r12_env(monkeypatch: pytest.MonkeyPatch, fail_max: int = 3) -> None:
    monkeypatch.setenv("OPS_CAPABILITY_CB_ENABLED", "1")
    monkeypatch.setenv("OPS_CAPABILITY_CB_FAIL_MAX", str(fail_max))
    monkeypatch.setenv("OPS_CAPABILITY_CB_RESET_TIMEOUT", "60")
    monkeypatch.setenv("OPS_CAPABILITY_CB_SUCCESS_THRESHOLD", "1")
    monkeypatch.setenv("OPS_CAPABILITY_CB_SCOPE", "capability")
    monkeypatch.setenv("OPS_CAPABILITY_CB_HALFOPEN_WRITES", "0")


@redline("R12")
def test_r12_environmental_failures_trip_then_zero_egress(monkeypatch: pytest.MonkeyPatch):
    """环境类失败达阈值 → 熔断，后续**零出网**；60s 后放行一次探测。"""
    from app.ops.capability import circuit

    _r12_env(monkeypatch)
    circuit.reset()

    spec = _spec("r12.read", side_effect="read")
    try:
        ctx = {"tenant_id": "t1"}
        # 连续 3 次超时（环境类）
        down = FakeHttpTransport(payload=None, exc=TimeoutError("t"))
        _register(spec, down)
        for _ in range(3):
            invoke("r12.read", {"subject": "x"}, ctx=dict(ctx))

        cb = circuit.breaker_for(spec)
        # 闸已合上：换成能成功的传输，请求也必须**一次都出不去**
        unregister("r12.read")
        tx = FakeHttpTransport(payload={"code": 0, "data": {"ok": 1}})
        _register(spec, tx)
        blocked = invoke("r12.read", {"subject": "x"}, ctx=dict(ctx))
        detail = str(blocked.error or "")
        holds = (
            cb.current_state == "open"
            and blocked.ok is False
            and detail.startswith("upstream_error")
            and "circuit_open" in detail
            and blocked.meta.get("blocked") == "circuit"
            and tx.calls == []  # ★ 零出网
        )

        # 60s 到点 → 放行一次探测；成功 → 恢复
        circuit.advance(spec, 61)
        probed = invoke("r12.read", {"subject": "x"}, ctx=dict(ctx))
        control = (
            probed.ok is True
            and len(tx.calls) == 1
            and circuit.breaker_for(spec).current_state == "closed"
        )
    finally:
        unregister("r12.read")

    assert_redline(
        redline_id="R12",
        holds=holds,
        control=control,
        detail=f"state={cb.current_state} blocked={blocked.error!r} calls={len(tx.calls)}",
    )


@redline("R12")
def test_r12_business_failures_never_trip(monkeypatch: pytest.MonkeyPatch):
    """★ 反向对照：业务类失败连打 20 次，断路器必须**始终闭合**。

    这条防的是"把用户填错参数熔了整个能力"——那等于用可用性问题换可用性问题。
    """
    from app.ops.capability import circuit

    _r12_env(monkeypatch)
    circuit.reset()

    spec = _spec("r12.biz", side_effect="read")
    # 下游返回 200 + 业务失败码（下游活着且正确响应）
    tx = FakeHttpTransport(payload={"code": 1001, "data": {}})
    _register(spec, tx)
    try:
        ctx = {"tenant_id": "t1"}
        for _ in range(20):
            invoke("r12.biz", {"subject": "x"}, ctx=dict(ctx))
        cb = circuit.breaker_for(spec)
        holds = cb.current_state == "closed" and cb.fail_counter == 0
        # 对照：业务失败不熔断 ≠ 请求没打出去（下游确实被调用了 20 次）
        control = len(tx.calls) == 20
    finally:
        unregister("r12.biz")

    assert_redline(
        redline_id="R12",
        holds=holds,
        control=control,
        detail=f"state={cb.current_state} counter={cb.fail_counter} calls={len(tx.calls)}",
    )


@redline("R12")
def test_r12_one_capability_trip_does_not_affect_another(monkeypatch: pytest.MonkeyPatch):
    """反向对照：A 熔断不影响 B（per capability 独立性）。"""
    from app.ops.capability import circuit

    _r12_env(monkeypatch)
    circuit.reset()

    down = FakeHttpTransport(payload=None, exc=TimeoutError("t"))
    good = FakeHttpTransport(payload={"code": 0, "data": {"ok": 1}})
    _register(_spec("r12.a", side_effect="read"), down)
    _register(_spec("r12.b", side_effect="read"), good)
    try:
        ctx = {"tenant_id": "t1"}
        for _ in range(3):
            invoke("r12.a", {"subject": "x"}, ctx=dict(ctx))
        # B 从头到尾正常
        for _ in range(3):
            invoke("r12.b", {"subject": "x"}, ctx=dict(ctx))
        cb_a = circuit.breaker_for(_spec("r12.a", side_effect="read"))
        cb_b = circuit.breaker_for(_spec("r12.b", side_effect="read"))
        holds = cb_a.current_state == "open"
        control = cb_b.current_state == "closed" and len(good.calls) == 3
    finally:
        unregister("r12.a")
        unregister("r12.b")

    assert_redline(
        redline_id="R12",
        holds=holds,
        control=control,
        detail=f"a={cb_a.current_state} b={cb_b.current_state} b_calls={len(good.calls)}",
    )


def test_r12_is_not_vacuous(monkeypatch: pytest.MonkeyPatch):
    """变异检验：把分类器改成"所有失败都算环境类" → 业务类对照必须**翻掉**。

    不翻 = 说明上面那条对照是被别的东西满足的，是空真。
    """
    import app.ops.capability.circuit as circuit_mod

    _r12_env(monkeypatch)
    circuit_mod.reset()
    # 变异：一切失败皆环境类（这正是最容易写错的实现）
    monkeypatch.setattr(circuit_mod, "_is_business_error", lambda exc: False)

    spec = _spec("r12.mut", side_effect="read")
    tx = FakeHttpTransport(payload={"code": 1001, "data": {}})
    _register(spec, tx)
    try:
        for _ in range(3):
            invoke("r12.mut", {"subject": "x"}, ctx={"tenant_id": "t1"})
    finally:
        unregister("r12.mut")
    cb = circuit_mod.breaker_for(spec)
    assert cb.current_state == "open", (
        f"变异未翻转：业务类失败被算作环境类后仍未熔断（state={cb.current_state}），"
        "说明 R12 的业务类对照是空真"
    )


# ---------------- R13：降级链（声明即行为，且绝不静默）----------------
#
# 熔断回答"打得通吗"，降级回答"打不通给什么"。后者与业务强相关，所以：
#   - **降级成什么**必须由清单声明（走 Git + PR + 人闸），框架不猜
#   - 默认**不降级**（action=none）——让"不降级"成为需要显式改掉的默认
#   - 降级结果必须带 degraded 标记（否则等于用兜底掩盖了故障）

_READ_HTTP = {
    "method": "GET",
    "base_url": "OA_BASE",
    "path": "/api/v1/read",
    "auth": "oa_gateway_token",
    "query_map": {"subject": "{{subject}}"},
    # ★ _spec 是「以 _WRITE_HTTP 为底再 update」，所以写能力的 body_map /
    #   idempotency_key 会被继承下来。这两个模板都引用 {{subject}}，
    #   对只声明了 keyword 的降级目标就成了"未声明模板变量"——降级目标失败，
    #   于是整条降级链失效（**降级失败要看得见**，正是这里想证明的）。
    "body_map": {},
    "idempotency_key": "",
    "timeout_ms": 2000,
    "success_when": {"path": "$.code", "in": [0]},
    "error_map": {"1001": "args_schema_invalid", "5001": "upstream_error"},
}

_ARGS_KEYWORD = {"type": "object", "properties": {"keyword": {"type": "string"}}}
# 降级目标用自己的参数名（query_map 必须引用自己 schema 里声明的字段，
# 否则加载期/运行期会因"未声明模板变量"失败——那正是"降级失败要看得见"的样例）
_READ_HTTP_KW = {**_READ_HTTP, "query_map": {"keyword": "{{keyword}}"}}


def _r13_kw(cid: str, **over: Any) -> CapabilitySpec:
    """降级目标：参数名是 keyword（与源能力的 subject 不同，用于验证 args_map）。"""
    over.setdefault("args_schema", dict(_ARGS_KEYWORD))
    return _spec(cid, side_effect="read", http=dict(_READ_HTTP_KW), **over)
# 降级目标用自己的参数名（query_map 必须引用自己 schema 里声明的字段，
# 否则加载期/运行期会因"未声明模板变量"失败——那正是"降级失败要看得见"的样例）
_READ_HTTP_KW = {**_READ_HTTP, "query_map": {"keyword": "{{keyword}}"}}


def _r13_kw(cid: str, **over: Any) -> CapabilitySpec:
    """降级目标：参数名是 keyword（与源能力的 subject 不同，用于验证 args_map）。"""
    over.setdefault("args_schema", dict(_ARGS_KEYWORD))
    return _spec(cid, side_effect="read", http=dict(_READ_HTTP_KW), **over)


def _r13_read(cid: str, **over: Any) -> CapabilitySpec:
    return _spec(cid, side_effect="read", http=dict(_READ_HTTP), **over)


def _r13_down() -> FakeHttpTransport:
    """下游不可用（超时 = transport，最典型的降级触发条件）。"""
    return FakeHttpTransport(payload=None, exc=TimeoutError("t"))


def _without_marker(output: Any) -> Any:
    """去掉注入的降级标记，用于比对"业务内容本身"。"""
    if isinstance(output, dict):
        return {k: v for k, v in output.items() if k != "_degraded"}
    return output


@redline("R13")
def test_r13_declared_fallback_degrades_with_marker():
    """声明了降级 + 下游不可用 → **成功但带 degraded 标记**；未声明 → 明确失败。"""
    from app.ops.capability import fallback

    fallback.reset()
    down_a = _r13_down()
    good_b = FakeHttpTransport(payload={"code": 0, "data": {"items": [{"id": 1}]}})
    spec_a = _r13_read(
        "r13.a",
        fallback={
            "triggers": ["transport"],
            "action": "capability",
            "capability_id": "r13.b",
            "args_map": {"keyword": "subject"},  # 目标参数名 ← 源参数名
        },
    )
    spec_b = _r13_kw("r13.b")
    _register(spec_a, down_a)
    _register(spec_b, good_b)

    down_c = _r13_down()
    good_d = FakeHttpTransport(payload={"code": 0, "data": {}})
    _register(_r13_read("r13.c"), down_c)
    _register(_r13_kw("r13.d"), good_d)
    try:
        ctx = {"tenant_id": "t1"}
        res = invoke("r13.a", {"subject": "报销"}, ctx=dict(ctx))
        holds = (
            res.ok is True  # ★ 成功但降级
            and res.meta.get("degraded") is True  # ★ B2：必须显式标记
            and res.meta.get("degraded_from") == "r13.a"
            and res.meta.get("degraded_action") == "capability"
            and res.meta.get("degraded_to") == "r13.b"
            and res.meta.get("degrade_depth") == 1
            and res.meta.get("degraded_at")  # 时间也要有：编排层才知道有多旧
            and len(good_b.calls) == 1  # ★ 降级目标真的被调用了
            # args_map 生效：源参数 subject → 目标参数 keyword
            and good_b.calls[0]["params"] == {"keyword": "报销"}
        )

        # 对照：**没声明**降级 → 明确失败，降级目标零调用
        res2 = invoke("r13.c", {"subject": "报销"}, ctx=dict(ctx))
        control = (
            res2.ok is False
            and res2.meta.get("degraded") is not True
            and good_d.calls == []
        )
    finally:
        for cid in ("r13.a", "r13.b", "r13.c", "r13.d"):
            unregister(cid)
        fallback.reset()

    assert_redline(
        redline_id="R13",
        holds=holds,
        control=control,
        detail=(
            f"degraded={res.meta.get('degraded')} ok={res.ok} err={res.error!r} "
            f"fb={spec_a.fallback} b_calls={len(good_b.calls)} "
            f"undeclared_ok={res2.ok} err2={res2.error!r}"
        ),
    )


@redline("R13")
def test_r13_only_downstream_unavailability_degrades():
    """★ 反向对照：业务码失败 / 参数错不得降级（换接口参数还是错的）。"""
    from app.ops.capability import fallback

    fallback.reset()
    biz = FakeHttpTransport(payload={"code": 1001, "data": {}})
    good = FakeHttpTransport(payload={"code": 0, "data": {"items": []}})
    _register(
        _r13_read(
            "r13.biz",
            fallback={"action": "capability", "capability_id": "r13.bizfb"},
        ),
        biz,
    )
    _register(_r13_kw("r13.bizfb"), good)

    down = _r13_down()
    good2 = FakeHttpTransport(payload={"code": 0, "data": {"items": []}})
    _register(
        _r13_read(
            "r13.env",
            fallback={"action": "capability", "capability_id": "r13.envfb"},
        ),
        down,
    )
    _register(_r13_kw("r13.envfb"), good2)
    try:
        ctx = {"tenant_id": "t1"}
        # 下游活着并返回了业务失败码 → 不该降级
        res = invoke("r13.biz", {"subject": "x"}, ctx=dict(ctx))
        holds = (
            res.ok is False
            and res.meta.get("degraded") is not True
            and "args_schema_invalid" in str(res.error or "")
            and good.calls == []  # ★ 降级目标零调用
        )
        # 对照：同一个声明，换成 transport 失败 → 确实降级（证明声明本身接上了）
        res2 = invoke("r13.env", {"subject": "x"}, ctx=dict(ctx))
        control = res2.ok is True and res2.meta.get("degraded") is True
    finally:
        for cid in ("r13.biz", "r13.bizfb", "r13.env", "r13.envfb"):
            unregister(cid)
        fallback.reset()

    assert_redline(
        redline_id="R13",
        holds=holds,
        control=control,
        detail=f"biz_ok={res.ok} biz_err={res.error!r} env_degraded={res2.meta.get('degraded')}",
    )


@redline("R13")
def test_r13_write_capability_never_degrades(tmp_path: Path):
    """B1：写能力永不降级——运行期 + 加载期两道闸。"""
    from app.ops.capability import fallback

    fallback.reset()
    good = FakeHttpTransport(payload={"code": 0, "data": {"ticketId": "T-X"}})
    _register(
        _spec(
            "r13.w",
            fallback={"action": "capability", "capability_id": "r13.wfb"},
        ),
        _r13_down(),
    )
    _register(_r13_kw("r13.wfb"), good)
    try:
        res = invoke("r13.w", {"subject": "x"}, ctx=dict(_CTX_WRITE))
        holds = (
            res.ok is False
            and res.meta.get("degraded") is not True
            and good.calls == []  # ★ 写失败就是失败，没有"降级成建了一半"
        )
    finally:
        unregister("r13.w")
        unregister("r13.wfb")

    # 对照（加载期 V12）：写能力声明降级 → 整文件拒；**同样的声明用在读能力上放行**
    def _manifest(cid: str, side: str, fb: dict[str, Any], http: dict[str, Any]) -> str:
        return json.dumps(
            {
                "version": 1,
                "capabilities": [
                    {
                        "id": cid,
                        "kind": "http",
                        "description": "R13 加载期",
                        "when_to_use": "R13 加载期",
                        "args_schema": dict(_ARGS),
                        "side_effect": side,
                        "hitl": {"required": side == "write"},
                        "visibility": {"departments": ["all"]},
                        "http": http,
                        "fallback": fb,
                    }
                ],
            },
            ensure_ascii=False,
        )

    bad = tmp_path / "write_fallback.json"
    bad.write_text(
        _manifest("r13.mw", "write", {"action": "static", "value": {"ok": 1}}, dict(_WRITE_HTTP)),
        encoding="utf-8",
    )
    try:
        load_capability_manifest(bad)
        rejected = False
        why = ""
    except ManifestError as exc:
        rejected = "V12" in str(exc)
        why = str(exc)

    read_http = {k: v for k, v in _WRITE_HTTP.items() if k != "idempotency_key"}
    ok_file = tmp_path / "read_fallback.json"
    ok_file.write_text(
        _manifest("r13.mr", "read", {"action": "static", "value": {"ok": 1}}, read_http),
        encoding="utf-8",
    )
    loaded = load_capability_manifest(ok_file).registered_ids == ("r13.mr",)
    unregister("r13.mr")

    control = rejected and loaded
    assert_redline(
        redline_id="R13",
        holds=holds,
        control=control,
        detail=f"write_ok={res.ok} degraded={res.meta.get('degraded')} V12={why} loaded={loaded}",
    )


@redline("R13")
def test_r13_chain_is_bounded():
    """B3：成环不死循环；``max_depth`` 真的生效（1 与 2 行为不同）。"""
    from app.ops.capability import fallback

    fallback.reset()
    # ① 成环：A → B → A
    a_tx = _r13_down()
    b_tx = _r13_down()
    _register(
        _r13_read(
            "r13.cyc.a",
            fallback={"action": "capability", "capability_id": "r13.cyc.b"},
        ),
        a_tx,
    )
    _register(
        _r13_read(
            "r13.cyc.b",
            fallback={"action": "capability", "capability_id": "r13.cyc.a"},
        ),
        b_tx,
    )
    try:
        res = invoke("r13.cyc.a", {"subject": "x"}, ctx={"tenant_id": "t1"})
        # 不死循环：A / B 各只被打了「自己那一次」的量（GET 会重试一次 = 2 次）。
        # 真递归的话这里会是 4、6、… 或直接 RecursionError。
        holds = (
            res.ok is False
            and 0 < len(a_tx.calls) <= 2
            and 0 < len(b_tx.calls) <= 2
        )
    finally:
        unregister("r13.cyc.a")
        unregister("r13.cyc.b")

    # ② 两级链：A → B → C，max_depth=2 时第二级**必须**跑得到
    c_payload = {"code": 0, "data": {"items": [{"id": 9}]}}
    a2 = _r13_down()
    b2 = _r13_down()
    c2 = FakeHttpTransport(payload=c_payload)
    _register(
        _r13_read(
            "r13.d2.a",
            fallback={
                "action": "capability",
                "capability_id": "r13.d2.b",
                "max_depth": 2,
            },
        ),
        a2,
    )
    _register(
        _r13_read(
            "r13.d2.b",
            fallback={
                "action": "capability",
                "capability_id": "r13.d2.c",
                "max_depth": 2,
            },
        ),
        b2,
    )
    _register(_r13_read("r13.d2.c"), c2)
    try:
        res2 = invoke("r13.d2.a", {"subject": "x"}, ctx={"tenant_id": "t1"})
        control = (
            res2.ok is True
            and res2.meta.get("degraded") is True
            and len(c2.calls) == 1  # ★ 第二级真的跑到了
            # 拿到的确实是 C 的结果（http 适配器把下游响应体放在 output["result"]）
            and isinstance(res2.output, dict)
            and res2.output.get("result") == c_payload
        )
    finally:
        for cid in ("r13.d2.a", "r13.d2.b", "r13.d2.c"):
            unregister(cid)

    # ③ max_depth=1：第二级**不得**发生（上界是真的，不是摆设）
    a3 = _r13_down()
    b3 = _r13_down()
    c3 = FakeHttpTransport(payload={"code": 0, "data": {}})
    _register(
        _r13_read(
            "r13.d1.a",
            fallback={
                "action": "capability",
                "capability_id": "r13.d1.b",
                "max_depth": 1,
            },
        ),
        a3,
    )
    _register(
        _r13_read(
            "r13.d1.b",
            fallback={
                "action": "capability",
                "capability_id": "r13.d1.c",
                "max_depth": 1,
            },
        ),
        b3,
    )
    _register(_r13_read("r13.d1.c"), c3)
    try:
        res3 = invoke("r13.d1.a", {"subject": "x"}, ctx={"tenant_id": "t1"})
        bounded = res3.ok is False and c3.calls == []
    finally:
        for cid in ("r13.d1.a", "r13.d1.b", "r13.d1.c"):
            unregister(cid)
        fallback.reset()

    assert_redline(
        redline_id="R13",
        holds=holds and bounded,
        control=control,
        detail=(
            f"cycle_a_calls={len(a_tx.calls)} depth1_ok={res3.ok} c3={len(c3.calls)} "
            f"depth2_ok={res2.ok} c2={len(c2.calls)}"
        ),
    )


@redline("R13")
def test_r13_cache_action_is_tenant_and_args_scoped():
    """action=cache：重放上次成功结果 + 陈旧标记；**换租户/换参数不得命中**。"""
    from app.ops.capability import fallback

    fallback.reset()
    payload = {"code": 0, "data": {"items": [{"id": 1}]}}
    tx_ok = FakeHttpTransport(payload=payload)
    spec = _r13_read(
        "r13.cache",
        fallback={"action": "cache", "ttl_seconds": 60},
    )
    _register(spec, tx_ok)
    try:
        first = invoke("r13.cache", {"subject": "报销"}, ctx={"tenant_id": "t1"})
        # 下游挂了 → 只能吃缓存
        tx_down = _r13_down()
        unregister("r13.cache")
        _register(spec, tx_down)
        second = invoke("r13.cache", {"subject": "报销"}, ctx={"tenant_id": "t1"})
        holds = (
            first.ok is True
            and first.meta.get("degraded") is not True  # 真实结果不带标记
            and second.ok is True
            and second.meta.get("degraded") is True
            and second.meta.get("degraded_action") == "cache"
            and second.meta.get("stale_at")  # ★ 多旧，必须看得见
            # 重放的是**上次真实结果**，不是"一个像样的结果"
            # （去掉 _degraded 标记后应与首次输出逐字相同）
            and _without_marker(second.output) == first.output
        )
        # 对照：换租户 / 换参数 → 缓存不命中 → 明确失败（不能拿别人的结果兜底）
        other_tenant = invoke("r13.cache", {"subject": "报销"}, ctx={"tenant_id": "t2"})
        other_args = invoke("r13.cache", {"subject": "年假"}, ctx={"tenant_id": "t1"})
        control = (
            other_tenant.ok is False
            and other_tenant.meta.get("degraded") is not True
            and other_args.ok is False
            and other_args.meta.get("degraded") is not True
        )
    finally:
        unregister("r13.cache")
        fallback.reset()

    assert_redline(
        redline_id="R13",
        holds=holds,
        control=control,
        detail=(
            f"second_degraded={second.meta.get('degraded')} "
            f"tenant2_ok={other_tenant.ok} args2_ok={other_args.ok}"
        ),
    )


def test_r13_is_not_vacuous(monkeypatch: pytest.MonkeyPatch):
    """变异检验：把触发判定改成"什么失败都降级" → 业务类失败那半必须**翻掉**。

    不翻 = 说明"业务类失败没降级"是被别的东西满足的，R13 是空真。
    """
    import app.ops.capability.gateway as gw

    gw.fallback_mod.reset()
    monkeypatch.setattr(
        gw.fallback_mod, "trigger_of", lambda *a, **k: gw.fallback_mod.TRIGGER_TRANSPORT
    )

    biz = FakeHttpTransport(payload={"code": 1001, "data": {}})
    good = FakeHttpTransport(payload={"code": 0, "data": {"items": []}})
    _register(
        _r13_read(
            "r13.mut",
            fallback={"action": "capability", "capability_id": "r13.mutfb"},
        ),
        biz,
    )
    _register(_r13_kw("r13.mutfb"), good)
    try:
        res = invoke("r13.mut", {"subject": "x"}, ctx={"tenant_id": "t1"})
    finally:
        unregister("r13.mut")
        unregister("r13.mutfb")
        gw.fallback_mod.reset()

    assert res.ok is True and res.meta.get("degraded") is True, (
        f"变异未翻转：把所有失败都判成「下游不可用」后业务类失败仍未降级"
        f"（ok={res.ok} err={res.error!r}），说明 R13 的触发条件对照是空真"
    )


@redline("R13")
def test_r13_marker_travels_with_the_output_not_only_meta():
    """★ 标记必须**跟着数据走**：模型只看工具输出，看不到 meta。

    只把 degraded 写进 meta 等于没写——模型拿到静态兜底值会当成真实结果，
    语气还很确定。这是"降级"这个机制最危险的一种静默错误。
    """
    from app.ops.capability import fallback

    fallback.reset()
    _register(
        _r13_read(
            "r13.mark",
            fallback={
                "action": "static",
                "value": {"code": 503, "message": "服务暂不可用", "data": {"items": []}},
            },
        ),
        _r13_down(),
    )
    try:
        res = invoke("r13.mark", {"subject": "x"}, ctx={"tenant_id": "t1"})
        out = res.output
        marker = out.get("_degraded") if isinstance(out, dict) else None
        notice = str((marker or {}).get("notice") or "")
        holds = (
            res.ok is True
            and isinstance(marker, dict)
            and marker.get("action") == "static"
            and marker.get("capability") == "r13.mark"
            and bool(notice)
            and "不是查询结果" in notice  # ★ 说清楚"这不是真的"
            and res.meta.get("degraded_marker_inline") is True
            # 真实原因也要跟着走：模型才知道为什么拿到的不是真数据
            and "upstream_error" in str(marker.get("reason") or "")
        )
        # 对照：标记**只**加在降级结果上，真实成功结果必须干干净净
        good = FakeHttpTransport(payload={"code": 0, "data": {"items": [{"id": 1}]}})
        unregister("r13.mark")
        _register(_r13_read("r13.mark"), good)
        plain = invoke("r13.mark", {"subject": "x"}, ctx={"tenant_id": "t1"})
        control = (
            plain.ok is True
            and plain.meta.get("degraded") is not True
            and "_degraded" not in (plain.output or {})
        )
    finally:
        unregister("r13.mark")
        fallback.reset()

    assert_redline(
        redline_id="R13",
        holds=holds,
        control=control,
        detail=f"marker={marker} plain_has_marker={' _degraded' in str(plain.output)}",
    )


def test_r13_marker_is_not_vacuous(monkeypatch: pytest.MonkeyPatch):
    """变异检验：把注入摘掉（只留 meta 标记）→ 模型侧必须**看不到**降级。

    不翻 = 说明"标记进输出"这条是被别的东西满足的，R13 的后半句是空真。
    """
    import app.ops.capability.gateway as gw

    gw.fallback_mod.reset()
    monkeypatch.setattr(
        gw.fallback_mod,
        "annotate_output",
        lambda output, *, cid, action, meta: (output, False),
    )
    _register(
        _r13_read("r13.mut2", fallback={"action": "static", "value": {"ok": 1}}),
        _r13_down(),
    )
    try:
        res = invoke("r13.mut2", {"subject": "x"}, ctx={"tenant_id": "t1"})
        leaked = res.ok is True and "_degraded" not in (res.output or {})
    finally:
        unregister("r13.mut2")
        gw.fallback_mod.reset()

    assert leaked, (
        "变异未翻转：注入被摘掉后输出里仍然有 _degraded，"
        f"说明 R13 的『标记跟着数据走』是空真（output={res.output!r}）"
    )


# ---------------- R14：步骤契约（编排层 · 八问 Q4） ----------------


async def _drive_step_contract(plan: list[dict], terminals: dict[str, dict]):
    """跑一遍「归并 → 派发 → 执行工具」，返回 (被执行的 id, 被拦的 id→行, 调用计数)。

    "零请求"不是靠"没出现在 ready 里"推断的，而是**真去执行**派发的步骤、
    数工具被调用了几次。
    """
    from types import SimpleNamespace
    from unittest.mock import patch

    from app.ops.lg_rag.multi.nodes import _join_subtasks, route_next_subtask, tool_exec_node

    state = {
        "subtasks": plan,
        "subtask_results": list(terminals.values()),
        "inflight_subtask_ids": [],
        "supervisor_step_count": 1,
        "run_id": "r14run",
        "messages": [],
    }
    out = await _join_subtasks(state)
    blocked = {
        str(r.get("subtask_id")): r for r in (out.get("subtask_results") or [])
    }
    ready = list(out.get("inflight_subtask_ids") or [])
    executed: list[str] = []
    calls: list[str] = []

    async def _cap(name, args, ctx=None):
        calls.append(str((ctx or {}).get("subtask_id")))
        return SimpleNamespace(
            ok=True, output={"assignee": "张三", "status": "open"}, error=None, meta={}
        )

    with patch("app.ops.lg_rag.multi.nodes.capability_ainvoke", new=_cap):
        for sid in ready:
            routed = route_next_subtask({**state, "inflight_subtask_ids": [sid]})
            if not isinstance(routed, list):
                continue
            for send in routed:
                if send.node != "tool_exec":
                    continue
                executed.append(str(send.arg["assigned_subtask"]["subtask_id"]))
                await tool_exec_node(send.arg)
    return executed, blocked, calls


def _r14_plan(consumes_field: bool):
    from app.ops.lg_rag.multi.nodes import _issue_plan

    t2 = {"id": "t2", "type": "tool", "tool": "mock_get_issue_status", "input": "乙"}
    if consumes_field:
        t2["depends_on"] = ["t1"]
        t2["consumes"] = {"t1": ["assignee"]}
    plan, _errors, _seq = _issue_plan(
        [
            {
                "id": "t1",
                "type": "tool",
                "tool": "mock_get_issue_status",
                "input": "甲",
                "produces": ["assignee"],
            },
            t2,
        ],
        run_id="r14run",
        seq=0,
    )
    return plan


@redline("R14")
async def test_r14_step_contract_gate_and_binding():
    """前驱失败 / 缺 consumes 字段 ⇒ 后继零执行；契约满足 ⇒ 照常执行且真绑定。"""
    from app.ops.lg_rag.multi import step_contract as sc

    plan = _r14_plan(consumes_field=True)
    t1, t2 = plan[0]["subtask_id"], plan[1]["subtask_id"]

    # 正向 1：前驱失败终态
    executed, blocked, calls = await _drive_step_contract(
        plan, {t1: {"id": t1, "subtask_id": t1, "type": "tool", "error": "下游 500"}}
    )
    # t1 已有终态 ⇒ 本轮谁都不该被执行；calls 全空才是"后继零请求"
    holds_1 = t2 not in executed and calls == []
    assert_redline(
        redline_id="R14",
        holds=holds_1,
        control=True,
        detail=f"前驱失败后后继仍被执行 executed={executed} calls={calls}",
    )
    assert blocked[t2]["blocked_by"] == sc.BLOCKED_PREDECESSOR_FAILED

    # 正向 2：前驱成功但缺 consumes 声明的字段
    executed, blocked, calls = await _drive_step_contract(
        plan, {t1: {"id": t1, "subtask_id": t1, "type": "tool", "output": {"status": "open"}}}
    )
    holds_2 = t2 not in executed and calls == []
    assert_redline(
        redline_id="R14",
        holds=holds_2,
        control=True,
        detail=f"缺字段后后继仍被执行 executed={executed} calls={calls}",
    )
    assert blocked[t2]["blocked_by"] == sc.BLOCKED_CONTRACT_MISSING

    # 反向对照：字段齐全 ⇒ 两步都执行，且第二步拿到的是**绑定值**
    executed, blocked, calls = await _drive_step_contract(
        plan, {t1: {"id": t1, "subtask_id": t1, "type": "tool", "output": {"assignee": "张三"}}}
    )
    assert_redline(
        redline_id="R14",
        holds=True,
        control=(t2 in executed) and (t2 in calls) and not blocked,
        detail=f"该放行的被拦了 executed={executed} blocked={blocked}",
    )

    # 反向对照 2：未声明 consumes ⇒ 前驱成功时不拦（否则"一律不派"也能满足正向）
    undecided = _r14_plan(consumes_field=False)
    executed, blocked, calls = await _drive_step_contract(
        undecided,
        {t1: {"id": t1, "subtask_id": t1, "type": "tool", "output": {"whatever": 1}}},
    )
    assert_redline(
        redline_id="R14",
        holds=True,
        control=not blocked,
        detail=f"未声明契约却被拦截 blocked={blocked}",
    )

    # 绑定必须真的发生（只校验不绑定 = 空门）
    from app.ops.lg_rag.multi.nodes import _worker_state

    bound = _worker_state(
        {
            "subtasks": plan,
            "subtask_results": [
                {"id": t1, "subtask_id": t1, "type": "tool", "output": {"assignee": "张三"}}
            ],
            "messages": [],
            "supervisor_step_count": 1,
        },
        {**plan[1], "args": {"assignee": "待填"}},
    )["assigned_subtask"]
    assert_redline(
        redline_id="R14",
        holds=bound["args"]["assignee"] == "张三",
        control=True,
        detail=f"契约命中但没绑定：args={bound.get('args')}",
    )


# ---------------- R15：可恢复点 / 不可变前缀（编排层 · 八问 Q8） ----------------


@redline("R15")
async def test_r15_recoverable_point_keeps_prefix():
    """重规划只动后缀；前缀逐字段不变、不被重跑；首次规划照常。"""
    from types import SimpleNamespace
    from unittest.mock import AsyncMock, patch

    from langchain_core.messages import HumanMessage

    from app.ops.lg_rag.multi.nodes import supervisor_node
    from app.ops.lg_rag.state import SubtaskResultBatch, success_terminal_ids
    from app.ops.strategy.critic import critic_node

    tool = "mock_get_issue_status"
    caps = [SimpleNamespace(capability_id=tool, description="d", risk_level="low")]

    def _prov(*outputs):
        return SimpleNamespace(complete=AsyncMock(side_effect=list(outputs)))

    def _state(**kw):
        base = {
            "messages": [HumanMessage(content="复合问题")],
            "run_id": "r15run",
            "allowed_capability_ids": [tool],
            "supervisor_step_count": 0,
            "host_subtask_seq": 0,
            "subtasks": [],
            "subtask_results": [],
        }
        base.update(kw)
        return base

    first = '{"subtasks":[{"id":"t1","type":"tool","tool":"mock_get_issue_status",' \
            '"input":"甲","args":{"k":"v"}},{"id":"t2","type":"tool",' \
            '"tool":"mock_get_issue_status","input":"乙","depends_on":["t1"]}]}'
    suffix = '{"subtasks":[{"id":"s1","type":"tool","tool":"mock_get_issue_status",' \
             '"input":"丙","depends_on":["t1"]}]}'

    with patch(
        "app.ops.lg_rag.multi.nodes.list_capabilities", new=lambda *a, **k: caps
    ), patch("app.ops.lg_rag.multi.nodes.get_llm_provider", new=lambda *a, **k: _prov(first)):
        out1 = await supervisor_node(_state())

    # 反向对照：首次规划无前缀，计划照常签发、可恢复点为 0
    assert_redline(
        redline_id="R15",
        holds=True,
        control=len(out1["subtasks"]) == 2 and out1["recoverable_point"] == 0,
        detail=f"首次规划被前缀逻辑影响 {out1.get('recoverable_point')}",
    )

    t1, t2 = out1["subtasks"][0]["subtask_id"], out1["subtasks"][1]["subtask_id"]
    done = SubtaskResultBatch(
        [{"id": t1, "subtask_id": t1, "type": "tool", "output": {"assignee": "张三"}}],
        {t1, t2},
    )
    state2 = _state(
        subtasks=out1["subtasks"],
        subtask_results=done,
        host_subtask_seq=out1["host_subtask_seq"],
        supervisor_step_count=1,
    )

    with patch(
        "app.ops.lg_rag.multi.nodes.list_capabilities", new=lambda *a, **k: caps
    ), patch("app.ops.lg_rag.multi.nodes.get_llm_provider", new=lambda *a, **k: _prov(suffix)):
        out2 = await supervisor_node(state2)

    plan2 = out2["subtasks"]
    prefix_kept = (
        [r["subtask_id"] for r in plan2] == [t1, "r15run:3"]
        and plan2[0]["tool"] == tool
        and plan2[0]["args"] == {"k": "v"}
        and plan2[0]["input"] == "甲"
    )
    assert_redline(
        redline_id="R15",
        holds=prefix_kept,
        control=True,
        detail=f"重规划改写了前缀 {plan2}",
    )
    # 可恢复点显式声明 = 下一个真正要执行的下标
    assert_redline(
        redline_id="R15",
        holds=out2["recoverable_point"] == 1 and out2["plan_prefix_ids"] == [t1],
        control=True,
        detail=f"可恢复点未声明 {out2.get('recoverable_point')}",
    )

    # critic 回环不得抹掉前缀结果（这是最容易被写错的地方）
    crit = await critic_node(
        {
            "subtask_results": [
                {"subtask_id": t1, "output": {"assignee": "张三"}},
                {"subtask_id": t2, "error": "boom"},
            ],
            "allowed_capability_ids": [tool],
            "inner_retry_count": 0,
            "rebinding_count": 0,
            "subtasks": out1["subtasks"],
        }
    )
    # ★ 未解决后缀（t2 失败）必须跟着走。只留前缀是错的：
    #   t2 一从计划里消失，它的失败记录就变成"计划外 id"，
    #   observe 按 plan_ids 过滤看不见、aggregator 更看不见，
    #   结论会写成"已覆盖全部子任务" —— 失败被静默抹掉（2026-09-20 实测）。
    kept = crit["subtask_results"].plan_ids == frozenset({t1, t2})
    assert_redline(
        redline_id="R15",
        holds=kept and crit["recoverable_point"] == 1,
        control=True,
        detail=f"回环把前缀结果清掉了 {crit.get('subtask_results')}",
    )
    # 失败步骤本身也必须留在计划里（不然 observe 无从判定"没做完"）
    assert_redline(
        redline_id="R15",
        holds=[str(r["subtask_id"]) for r in crit["subtasks"]] == [t1, t2],
        control=True,
        detail=f"回环把未解决步骤从计划里删掉了 {crit.get('subtasks')}",
    )
    # 失败终态不进前缀（它没有要保护的东西，锁进去会让链卡死）
    assert_redline(
        redline_id="R15",
        holds=success_terminal_ids(
            out1["subtasks"],
            [
                {"subtask_id": t1, "output": {"a": 1}},
                {"subtask_id": t2, "error": "boom"},
            ],
        )
        == [t1],
        control=True,
        detail="失败终态不应进入不可变前缀",
    )
