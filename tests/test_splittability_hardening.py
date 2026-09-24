"""V1-E 可拆性硬化 · D2/D3/D4 新增断言 + 变异钩子。"""

from __future__ import annotations

import subprocess
import sys
import textwrap
from pathlib import Path

import pytest

from app.llm import model_catalog
from app.llm.strategy_pack import clear_strategy_pack_cache
from app.ops.capability.gateway import get_registry, set_registry
from app.ops.capability.registry import CapabilityRegistry
from app.ops.capability.types import CapabilitySpec

REPO = Path(__file__).resolve().parents[1]


def _lint_imports_cmd() -> list[str]:
    """优先本解释器旁 lint-imports；否则 worktree/主仓 .venv。"""
    cand = [
        Path(sys.executable).parent / "lint-imports",
        REPO / ".venv" / "bin" / "lint-imports",
        Path("/Users/cyning/Desktop/Ops-desk/ops-desk-api/.venv/bin/lint-imports"),
    ]
    for c in cand:
        if c.is_file():
            return [str(c), "--config", str(REPO / ".importlinter")]
    return [
        sys.executable,
        "-c",
        "from importlinter.cli import lint_imports; raise SystemExit(lint_imports())",
    ]


def test_d2_import_linter_contracts_kept() -> None:
    """D2：contracts 与 01_modules 出边一致 · CI 同口径绿。"""
    cmd = _lint_imports_cmd()
    if not Path(cmd[0]).is_file() and cmd[0] == sys.executable:
        pytest.skip("lint-imports 不可用")
    proc = subprocess.run(cmd, cwd=str(REPO), capture_output=True, text=True, check=False)
    assert proc.returncode == 0, proc.stdout + proc.stderr


def test_d2_mutation_forbidden_import_breaks_then_recovers() -> None:
    """变异①：临时引入 capability→lg_rag 直 import → 闸必挂；恢复后绿。"""
    cmd = _lint_imports_cmd()
    if not Path(cmd[0]).is_file() and cmd[0] == sys.executable:
        pytest.skip("lint-imports 不可用")

    probe = REPO / "app" / "ops" / "capability" / "_il_mutation_probe.py"
    assert not probe.exists()
    probe.write_text(
        textwrap.dedent(
            """\
            # temporary mutation probe — do not commit
            from app.ops.lg_rag import state  # noqa: F401
            """
        ),
        encoding="utf-8",
    )
    try:
        broken_rc = subprocess.run(cmd, cwd=str(REPO), capture_output=True, text=True, check=False)
        assert broken_rc.returncode != 0, "越界 import 应使 import-linter 失败"
        out = broken_rc.stdout + broken_rc.stderr
        assert "BROKEN" in out or "broken" in out.lower()
    finally:
        probe.unlink(missing_ok=True)

    recovered = subprocess.run(cmd, cwd=str(REPO), capture_output=True, text=True, check=False)
    assert recovered.returncode == 0, recovered.stdout + recovered.stderr


def test_d3_registry_reader_writer_protocols_and_mock_inject() -> None:
    """D3：本地 dict 实现协议；mock 注入后调用方读侧一致；恢复零副作用。"""
    original = get_registry()
    local = CapabilityRegistry()

    class _Fn:
        kind = "local_fn"

        def invoke(self, args, *, ctx=None):  # noqa: ANN001
            return {"ok": True}

    spec = CapabilitySpec(
        capability_id="splittability.mock_cap",
        kind="local_fn",
        description="mock",
        risk_level="low",
        side_effect="none",
        enabled=True,
        tags=(),
    )
    local.register(spec, _Fn())
    snap = local.snapshot()
    assert snap["count"] == 1
    assert snap["backend"] == "local_dict"
    assert "splittability.mock_cap" in snap["capability_ids"]

    class MockReader:
        def get(self, capability_id: str):
            if capability_id == "splittability.mock_cap":
                return (spec, _Fn())
            return None

        def list_specs(self, *, filter=None):  # noqa: A002
            return [spec]

        def snapshot(self):
            return {"capability_ids": ["splittability.mock_cap"], "count": 1, "backend": "mock"}

        def register(self, spec, adapter):  # noqa: ANN001
            raise AssertionError("mock writer unused")

        def unregister(self, capability_id: str) -> bool:
            return False

        def reload(self) -> None:
            return None

        def clear(self) -> None:
            return None

    set_registry(MockReader())  # type: ignore[arg-type]
    try:
        entry = get_registry().get("splittability.mock_cap")
        assert entry is not None
        assert entry[0].capability_id == "splittability.mock_cap"
        assert get_registry().snapshot()["backend"] == "mock"
    finally:
        set_registry(original)


def test_d3_mutation_broken_local_impl_detectable() -> None:
    """变异②：故意改本地 get 语义 → 读侧断言必挂；恢复后绿。"""
    original = get_registry()

    class Broken(CapabilityRegistry):
        def get(self, capability_id: str):
            return None  # 故意失真：永远 miss

    set_registry(Broken())
    try:
        with pytest.raises(AssertionError):
            entry = get_registry().get("does_not_matter")
            assert entry is not None  # 故意期望非空 → 必挂
    finally:
        set_registry(original)
        assert isinstance(get_registry(), CapabilityRegistry)


def test_d4_strategy_pack_absent_zero_diff(monkeypatch: pytest.MonkeyPatch) -> None:
    """D4：策略包缺省未设 = resolve 与代码默认一致。"""
    clear_strategy_pack_cache()
    monkeypatch.delenv("OPS_LLM_STRATEGY_PACK", raising=False)
    monkeypatch.delenv("OPS_LLM_TIER_GRADER_MODEL", raising=False)
    monkeypatch.delenv("RAG_GRADER_MODEL", raising=False)
    model, source = model_catalog.resolve_task_model("grader")
    assert model == model_catalog.TASK_TIER_MODELS["grader"]
    assert source == "tier_default"


def test_d4_env_overrides_strategy_pack(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """D4：env > 策略包；变异③ 若包盖过 env 则本断言必挂。"""
    clear_strategy_pack_cache()
    pack = tmp_path / "pack.yaml"
    pack.write_text(
        textwrap.dedent(
            """\
            schema_version: "0"
            surface: llm_tiers
            task_tier_models:
              grader: "deepseek-ai/DeepSeek-V4-Flash"
            task_tier_fallbacks: {}
            model_unit_prices: {}
            """
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("OPS_LLM_STRATEGY_PACK", str(pack))
    monkeypatch.setenv("OPS_LLM_TIER_GRADER_MODEL", "deepseek-ai/DeepSeek-V4-Pro")
    monkeypatch.delenv("RAG_GRADER_MODEL", raising=False)
    model, source = model_catalog.resolve_task_model("grader")
    assert model == "deepseek-ai/DeepSeek-V4-Pro"
    assert source == "env_tier"


def test_d4_mutation_pack_must_not_override_env(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """变异③：若实现错误让策略包盖过 env → 本测必挂。"""
    clear_strategy_pack_cache()
    pack = tmp_path / "pack.yaml"
    pack.write_text(
        textwrap.dedent(
            """\
            schema_version: "0"
            surface: llm_tiers
            task_tier_models:
              grader: "deepseek-ai/DeepSeek-V4-Flash"
            task_tier_fallbacks: {}
            model_unit_prices: {}
            """
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("OPS_LLM_STRATEGY_PACK", str(pack))
    monkeypatch.setenv("OPS_LLM_TIER_GRADER_MODEL", "deepseek-ai/DeepSeek-V4-Pro")
    model, source = model_catalog.resolve_task_model("grader")
    # 破坏条件：若 source==strategy_pack 且 model 为包内值 → 失败
    assert not (
        source == "strategy_pack" and model == "deepseek-ai/DeepSeek-V4-Flash"
    ), "策略包不得盖过 env"
    assert source == "env_tier"
