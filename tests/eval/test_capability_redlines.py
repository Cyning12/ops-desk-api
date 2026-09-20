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
