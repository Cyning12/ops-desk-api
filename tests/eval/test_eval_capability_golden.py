"""Capability 黑盒题集（E3）的 pytest 包装。

**黑盒不是口号，是这里守着的三条**：

1. `expect` 只允许引用**出口字段**（ALLOWED_EXIT_FIELDS）。一旦有人开始断言
   内部函数/字段/日志文案，"不关心内部怎么改"就失效了。
2. 每个 case 的出口面必须**非空** —— 否则 `empty == empty` 是假通过。
3. 与**基线**无漂移 —— 覆盖 `expect` 没写到的字段。
   漂移了要么是改坏了，要么是**有意的产出变化**（那就显式 `--update-baseline`）。
"""

from __future__ import annotations

import json

import pytest
import yaml

from evals.agent.golden.capability.runner import (
    BASELINE_PATH,
    CASES_PATH,
    compare_expect,
    diff_baseline,
    run_all,
)

pytestmark = pytest.mark.redline  # 题集漂移与红线同级：都是"不能悄悄坏掉"

#: 黑盒出口面 —— **只允许这些键出现在 `expect` 里**。
#: 新增出口字段时必须同时改这里，那是个刻意的动作（防止顺手断言内部实现）。
ALLOWED_EXIT_FIELDS = frozenset(
    {
        # catalog
        "visible_ids",
        "hidden",
        "kept_count",
        "anonymous",
        "undeclared_count",
        # manifest
        "registered_ids",
        "error_contains",
        # invoke / sequence
        "ok",
        "error_code",
        "downstream_calls",
        "duplicated",
        "duplicated_flags",
        "error_codes",
        "receipt_id_present",
        "side_effect",
    }
)


def _cases() -> list[dict]:
    return yaml.safe_load(CASES_PATH.read_text(encoding="utf-8"))["cases"]


def _case_ids() -> list[str]:
    return [str(c["id"]) for c in _cases()]


@pytest.fixture(scope="module")
def exits() -> dict[str, dict]:
    return run_all()


# ---------------- 黑盒约束 ----------------


def test_every_case_expect_uses_only_exit_fields():
    """★ 黑盒的落地保证：`expect` 不得引用出口字段之外的东西。"""
    offenders: list[str] = []
    for case in _cases():
        unknown = sorted(set(case.get("expect") or {}) - ALLOWED_EXIT_FIELDS)
        if unknown:
            offenders.append(f"{case['id']}: {unknown}")
    assert not offenders, "expect 引用了非出口字段（黑盒约束被破坏）: " + "; ".join(offenders)


def test_every_case_has_non_empty_exit_surface(exits: dict[str, dict]):
    """★ 防假通过：出口面全空的话，`expect` 怎么写都能过。"""
    empty = [
        cid
        for cid, surface in exits.items()
        if not any(v not in (None, "", [], {}) for v in surface.values())
    ]
    assert not empty, f"这些 case 的出口面是空的（假通过风险）: {empty}"


def test_every_case_declares_expect():
    """沿用既有范式：fixture 必须含非空 expect，禁止 silent skip。"""
    for case in _cases():
        assert case.get("expect"), f"{case['id']} 缺 expect"
        assert case.get("scenario"), f"{case['id']} 缺 scenario"


def test_case_ids_are_unique():
    ids = _case_ids()
    assert len(ids) == len(set(ids))


# ---------------- expect 比对 ----------------


@pytest.mark.parametrize("case_id", _case_ids())
def test_case_matches_expect(case_id: str, exits: dict[str, dict]):
    case = next(c for c in _cases() if c["id"] == case_id)
    problems = compare_expect(exits[case_id], case["expect"])
    assert not problems, f"{case_id}:\n" + "\n".join(f"  - {p}" for p in problems)


# ---------------- 基线无漂移 ----------------


def test_no_drift_against_committed_baseline(exits: dict[str, dict]):
    """★ 覆盖 `expect` **没写到**的字段。

    漂移不一定是坏——可能是**有意的产出变化**。那就显式更新基线：
    ``python -m evals.agent.golden.capability.runner --update-baseline``
    （跑一遍自动覆盖 = 等于没有基线，所以必须是显式动作。）
    """
    assert BASELINE_PATH.is_file(), (
        f"基线不存在：{BASELINE_PATH}；首次须显式 "
        "`python -m evals.agent.golden.capability.runner --update-baseline` 建立"
    )
    baseline = json.loads(BASELINE_PATH.read_text(encoding="utf-8"))
    diff = diff_baseline(exits, baseline)
    assert not diff["drift"], (
        "与基线不一致（这些字段可能没写进 expect）：\n"
        f"  新增 case: {diff['added']}\n"
        f"  消失 case: {diff['removed']}\n"
        f"  字段变化: {json.dumps(diff['changed'], ensure_ascii=False, indent=2)}"
    )
