"""Capability 黑盒题集 runner（E3）。

**黑盒的含义是可执行的、不是口头的**：case 只能通过 `expect` 引用**出口字段**
（`visible_ids` / `hidden` / `ok` / `error_code` / `downstream_calls` …），
不允许断言内部函数名、内部字段、日志文案。谁重写了 `http_generic` 的内部实现，
这套 case 都不该动。

runner 产出**归一化出口（exit surface）**，用途有二：

1. `expect` 子集比对 —— 你**想到**的字段
2. **基线 diff** —— 你**没想到**的字段（`--against-baseline`）

第 2 条是刻意的：漂移往往发生在没写进 `expect` 的地方。
基线更新必须是显式动作（`--update-baseline`）——跑一遍自动覆盖就等于没有基线。

CLI::

    python -m evals.agent.golden.capability.runner                    # 只看 expect 比对
    python -m evals.agent.golden.capability.runner --against-baseline # 再看漂移
    python -m evals.agent.golden.capability.runner --update-baseline  # 显式更新基线
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from pathlib import Path
from typing import Any

import yaml

CASES_PATH = Path(__file__).resolve().parent / "cases_v1.yaml"
BASELINE_PATH = Path(__file__).resolve().parent / "baseline_v1.json"

# 假传输在跑，但 _prepare 仍会从 env 解析 base_url —— 给一个不存在的域即可
os.environ.setdefault("OA_BASE", "http://golden.capability.invalid")

from app.ops.capability import (  # noqa: E402
    GenericHttpAdapter,
    InMemoryIdempotencyStore,
    InMemoryReceiptSink,
    Principal,
    capability_catalog_snapshot,
    invoke,
    register,
    set_idempotency_store,
    set_receipt_sink,
    unregister,
)
from app.ops.capability.adapters import (  # noqa: E402
    FakeHttpTransport,
    StaticCredentialVault,
)
from app.ops.capability.baseline import baseline_filter  # noqa: E402
from app.ops.capability.defaults import ensure_default_capabilities  # noqa: E402
from app.ops.capability.errors import STABLE_ERROR_CODES  # noqa: E402
from app.ops.capability.gateway import get_registry  # noqa: E402
from app.ops.capability.manifest import (  # noqa: E402
    ManifestError,
    load_capability_manifest,
)

_EXC_BY_NAME: dict[str, type[BaseException]] = {
    "TimeoutError": TimeoutError,
    "ConnectionError": ConnectionError,
}

_FAKE_TOKEN = "golden-token"


# ---------------- 场景执行：产出「出口面」 ----------------


def _principal(raw: dict[str, Any] | None) -> Principal:
    raw = raw or {}
    return Principal(
        user_id=str(raw.get("user_id", "")),
        tenant_id=str(raw.get("tenant_id", "")),
        departments=frozenset(raw.get("departments") or ()),
        roles=frozenset(raw.get("roles") or ()),
        projects=frozenset(raw.get("projects") or ()),
        classification_max=str(raw.get("classification_max") or Principal().classification_max),
    )


def _register_probe_caps(items: list[dict[str, Any]] | None) -> list[str]:
    """注册题集内联声明的探针能力。

    注意：`run_case` 已经清空过注册表，所以**场景运行时注册表里只有这些探针**——
    否则内置五枚会混进 `visible_ids`，期望值就没法写成等式了。
    """
    from app.ops.capability.types import CapabilitySpec

    registered: list[str] = []
    for item in items or []:
        cid = str(item["id"])
        spec = CapabilitySpec(
            capability_id=cid,
            kind=str(item.get("kind", "http")),
            description="golden 探针",
            args_schema={"type": "object", "properties": {}},
            tags=tuple(item.get("tags") or ()),
            side_effect=str(item.get("side_effect", "read")),
            when_to_use="题集",
            visibility=item.get("visibility"),
            http={},
        )
        register(spec, GenericHttpAdapter(spec))
        registered.append(cid)
    return registered


def _scenario_catalog(setup: dict[str, Any]) -> dict[str, Any]:
    _register_probe_caps(setup.get("register"))
    cap_filter = (
        baseline_filter(node_role="golden")
        if setup.get("baseline", True)
        else None
    )
    visible, summary = capability_catalog_snapshot(
        filter=cap_filter, principal=_principal(setup.get("principal"))
    )
    return {
        "visible_ids": sorted(s.capability_id for s in visible),
        "hidden": sorted(
            (
                {"capability_id": h["capability_id"], "reason": h["reason"]}
                for h in summary["visibility_hidden"]
            ),
            key=lambda h: h["capability_id"],
        ),
        "kept_count": summary["visibility_kept_count"],
        "anonymous": summary["visibility_principal_anonymous"],
        "undeclared_count": summary["visibility_undeclared_count"],
    }


def _scenario_manifest(setup: dict[str, Any]) -> dict[str, Any]:
    """把 manifest 片段写到临时文件后**走真实加载器**（而不是另写一套解析）。"""
    payload = {"version": 1, "capabilities": setup.get("capabilities") or []}
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "case.json"
        path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
        try:
            result = load_capability_manifest(path)
        except ManifestError as exc:
            return {
                "ok": False,
                "error_code": "manifest_invalid",
                "error_contains": str(exc),
                "registered_ids": [],
            }
        return {
            "ok": True,
            "error_code": None,
            "error_contains": None,
            "registered_ids": sorted(result.registered_ids),
        }


def _register_with_fake_transport(spec, downstream: dict[str, Any]) -> None:
    """把 manifest 加载出来的能力换成"假传输"版本（题目必须不打网络）。"""
    exc_name = downstream.get("exc")
    tx = FakeHttpTransport(
        payload=downstream.get("payload", {"code": 0, "data": {}}),
        status=int(downstream.get("status", 200)),
        exc=_EXC_BY_NAME[exc_name](exc_name) if exc_name else None,
    )
    adapter = GenericHttpAdapter(
        spec,
        transport=tx,
        vault=StaticCredentialVault({"oa_gateway_token": _FAKE_TOKEN}),
    )
    # register 对重复 id 会抛（这是刻意的）——这里要的是"替换"，所以先注销
    unregister(spec.capability_id)
    register(spec, adapter)
    return tx


def _scenario_invoke(setup: dict[str, Any]) -> dict[str, Any]:
    manifest = _scenario_manifest({"capabilities": setup.get("capabilities") or []})
    if not manifest["ok"]:
        return {"ok": False, "error_code": manifest["error_code"], "downstream_calls": 0}

    downstream = setup.get("downstream") or {}
    transports: dict[str, Any] = {}
    for cid in manifest["registered_ids"]:
        entry = get_registry().get(cid)
        if entry is None:  # pragma: no cover
            continue
        transports[cid] = _register_with_fake_transport(entry[0], downstream)

    call = setup.get("invoke") or {}
    cid = str(call.get("capability_id") or (manifest["registered_ids"] or [""])[0])
    result = invoke(cid, call.get("args"), ctx=call.get("ctx"))

    err = str(result.error or "")
    error_code = next((c for c in STABLE_ERROR_CODES if err.startswith(c)), None)
    return {
        "ok": result.ok,
        "error_code": error_code,
        "downstream_calls": len(transports[cid].calls) if cid in transports else 0,
        "duplicated": bool(result.meta.get("duplicated")),
        "receipt_id_present": bool(result.meta.get("receipt_id")),
        "side_effect": result.meta.get("side_effect"),
    }


def _scenario_sequence(setup: dict[str, Any]) -> dict[str, Any]:
    """连续多次调用（验防重/重试纪律这类"次数"性质的主张）。"""
    manifest = _scenario_manifest({"capabilities": setup.get("capabilities") or []})
    if not manifest["ok"]:
        return {"ok": False, "error_code": manifest["error_code"], "downstream_calls": 0}

    downstream = setup.get("downstream") or {}
    transports: dict[str, Any] = {}
    for cid in manifest["registered_ids"]:
        entry = get_registry().get(cid)
        if entry is not None:
            transports[cid] = _register_with_fake_transport(entry[0], downstream)

    results: list[dict[str, Any]] = []
    calls = setup.get("calls") or []
    for call in calls:
        cid = str(call.get("capability_id") or (manifest["registered_ids"] or [""])[0])
        result = invoke(cid, call.get("args"), ctx=call.get("ctx"))
        err = str(result.error or "")
        results.append(
            {
                "ok": result.ok,
                "error_code": next(
                    (c for c in STABLE_ERROR_CODES if err.startswith(c)), None
                ),
                "duplicated": bool(result.meta.get("duplicated")),
            }
        )
    first_cid = str((calls[0] if calls else {}).get("capability_id") or
                    (manifest["registered_ids"] or [""])[0])
    return {
        "ok": all(r["ok"] for r in results),
        "error_codes": [r["error_code"] for r in results],
        "duplicated_flags": [r["duplicated"] for r in results],
        "downstream_calls": len(transports[first_cid].calls) if first_cid in transports else 0,
    }


_SCENARIOS = {
    "catalog": _scenario_catalog,
    "manifest": _scenario_manifest,
    "invoke": _scenario_invoke,
    "sequence": _scenario_sequence,
}


def run_case(case: dict[str, Any]) -> dict[str, Any]:
    scenario = case.get("scenario")
    fn = _SCENARIOS.get(str(scenario))
    if fn is None:
        raise ValueError(f"case {case.get('id')} 未知 scenario: {scenario!r}")
    get_registry().clear()
    set_idempotency_store(InMemoryIdempotencyStore())
    set_receipt_sink(InMemoryReceiptSink())
    try:
        return fn(case.get("setup") or {})
    finally:
        get_registry().clear()
        set_idempotency_store(None)
        set_receipt_sink(None)
        ensure_default_capabilities()


def run_all(cases_path: Path = CASES_PATH) -> dict[str, dict[str, Any]]:
    doc = yaml.safe_load(cases_path.read_text(encoding="utf-8"))
    out: dict[str, dict[str, Any]] = {}
    for case in doc["cases"]:
        out[str(case["id"])] = run_case(case)
    return out


# ---------------- 比对 ----------------


def compare_expect(exit_surface: dict[str, Any], expect: dict[str, Any]) -> list[str]:
    """`expect` 里的键做**子集**比对；不在 `expect` 里的字段交给基线 diff。"""
    problems: list[str] = []
    for key, want in expect.items():
        got = exit_surface.get(key)
        if key == "hidden":
            want_norm = sorted(
                [{"capability_id": h["capability_id"], "reason": h["reason"]} for h in want],
                key=lambda h: h["capability_id"],
            )
            if got != want_norm:
                problems.append(f"{key}: 期望 {want_norm} 实际 {got}")
        elif key == "error_contains":
            if not isinstance(got, str) or want not in got:
                problems.append(f"{key}: {want!r} 不在 {got!r} 中")
        elif got != want:
            problems.append(f"{key}: 期望 {want!r} 实际 {got!r}")
    return problems


def diff_baseline(
    current: dict[str, dict[str, Any]], baseline: dict[str, dict[str, Any]]
) -> dict[str, Any]:
    """逐 case、逐字段给差异——覆盖 `expect` **没写**的字段。"""
    added = sorted(set(current) - set(baseline))
    removed = sorted(set(baseline) - set(current))
    changed: dict[str, dict[str, Any]] = {}
    for cid in sorted(set(current) & set(baseline)):
        cur, base = current[cid], baseline[cid]
        field_diff = {
            key: {"baseline": base.get(key), "current": cur.get(key)}
            for key in sorted(set(cur) | set(base))
            if cur.get(key) != base.get(key)
        }
        if field_diff:
            changed[cid] = field_diff
    return {"added": added, "removed": removed, "changed": changed, "drift": bool(added or removed or changed)}


# ---------------- CLI ----------------


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="capability 黑盒题集 runner")
    parser.add_argument("--cases", type=Path, default=CASES_PATH)
    parser.add_argument("--baseline", type=Path, default=BASELINE_PATH)
    parser.add_argument("--against-baseline", action="store_true")
    parser.add_argument("--update-baseline", action="store_true")
    parser.add_argument("--json", action="store_true", help="打印归一化出口（供调试）")
    args = parser.parse_args(argv)

    doc = yaml.safe_load(args.cases.read_text(encoding="utf-8"))
    current = run_all(args.cases)

    if args.json:
        print(json.dumps(current, ensure_ascii=False, indent=2, sort_keys=True))

    failures = 0
    for case in doc["cases"]:
        cid = str(case["id"])
        problems = compare_expect(current[cid], case.get("expect") or {})
        if problems:
            failures += 1
            print(f"[FAIL] {cid}")
            for p in problems:
                print(f"       {p}")
        else:
            print(f"[ ok ] {cid}")

    if args.update_baseline:
        args.baseline.write_text(
            json.dumps(current, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        print(f"\n已显式更新基线：{args.baseline}")
    elif args.against_baseline:
        if not args.baseline.is_file():
            print(f"\n[FAIL] 基线不存在：{args.baseline}（首次须 --update-baseline 显式建立）")
            return 2
        diff = diff_baseline(current, json.loads(args.baseline.read_text(encoding="utf-8")))
        if diff["drift"]:
            failures += 1
            print("\n[DRIFT] 与基线不一致（这些字段可能没写进 expect）")
            if diff["added"]:
                print(f"  新增 case: {diff['added']}")
            if diff["removed"]:
                print(f"  消失 case: {diff['removed']}")
            for cid, fields in diff["changed"].items():
                print(f"  {cid}:")
                for key, pair in fields.items():
                    print(f"    {key}: {pair['baseline']!r} → {pair['current']!r}")
        else:
            print("\n无漂移（与基线一致）")

    print(f"\n=== 题集 {len(doc['cases'])} 条，失败 {failures} ===")
    return 1 if failures else 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
