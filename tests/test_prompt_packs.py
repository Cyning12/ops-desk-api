"""C2 · comms Prompt Pack + 意图路由单测（全纯函数 · 不连真 LLM）。"""

from __future__ import annotations

import inspect
from pathlib import Path

import pytest

from app.ops.prompts import (
    PromptPack,
    PromptPackError,
    PromptPackNotFoundError,
    get_template,
    render,
    render_pack,
    route_intent,
)
from app.ops.prompts.templates import TEMPLATES

REPO_ROOT = Path(__file__).resolve().parents[1]
FRAGMENT_DIR = REPO_ROOT / "docs" / "harness" / "prompts"
FRAGMENT_00 = FRAGMENT_DIR / "FRAGMENT_00_delegate_only_v1_zh.md"
FRAGMENT_REANCHOR = FRAGMENT_DIR / "FRAGMENT_hat_reanchor_v1_zh.md"


# ---------- render_pack("comms") 槽位链 ----------


def test_render_pack_comms_contains_fragment_substrings():
    pack = render_pack("comms")
    for truth in (FRAGMENT_00, FRAGMENT_REANCHOR):
        assert truth.exists(), f"真值文件缺失: {truth}"
        # 子串断言：真值文件的关键行逐行在 pack 输出中
        body = truth.read_text(encoding="utf-8")
        for marker in ("FRAGMENT", "禁止", "verify"):
            assert marker in pack.system_prompt
        assert body.splitlines()[0] in pack.system_prompt


def test_render_pack_fragment_truth_consistency_no_drift():
    """FRAGMENT 注入内容与仓内真值文件逐字一致（防拷贝漂移）。"""
    pack = render_pack("comms")
    for truth in (FRAGMENT_00, FRAGMENT_REANCHOR):
        content = truth.read_text(encoding="utf-8").strip()
        assert content in pack.system_prompt, f"FRAGMENT 注入与真值漂移: {truth.name}"


def test_render_pack_prohibition_clauses():
    pack = render_pack("comms")
    assert "永不签发 human_gate" in pack.system_prompt
    assert "docs/tasks/" in pack.system_prompt
    assert "docs/harness/invokes/by-task/" in pack.system_prompt
    assert "Skills ≠ verify" in pack.system_prompt
    # SPEC 06 §6：不得出现「已代签」之外的签闸授权语义
    assert "待人签" in pack.system_prompt


def test_render_pack_task_field_checklist():
    pack = render_pack("comms")
    for field_name in ("task_slug", "范围", "非范围", "验收", "failure_paths", "人工闸"):
        assert field_name in pack.system_prompt


def test_render_pack_dialog_policy():
    pack = render_pack("comms")
    assert "澄清" in pack.system_prompt
    assert "起草" in pack.system_prompt
    assert "人闸" in pack.system_prompt


def test_render_pack_missing_fragment_raises(tmp_path):
    with pytest.raises(PromptPackError, match="FRAGMENT"):
        render_pack("comms", base_dir=tmp_path)


def test_render_pack_empty_fragment_raises(tmp_path):
    frag_dir = tmp_path / "docs" / "harness" / "prompts"
    frag_dir.mkdir(parents=True)
    (frag_dir / "FRAGMENT_00_delegate_only_v1_zh.md").write_text("", encoding="utf-8")
    with pytest.raises(PromptPackError, match="为空"):
        render_pack("comms", base_dir=tmp_path)


def test_render_pack_unknown_name():
    with pytest.raises(PromptPackNotFoundError):
        render_pack("product")


def test_render_pack_slots_appended():
    pack = render_pack("comms", slots={"task_slug": "demo", "hat_id": "30"})
    assert "<!-- slot:task_slug -->" in pack.system_prompt
    assert "<!-- slot:hat_id -->" in pack.system_prompt


def test_render_pack_slots_missing_required_names_slot():
    with pytest.raises(PromptPackError, match="缺少槽位.*hat_id"):
        render_pack("comms", slots={"task_slug": "demo"})


def test_render_pack_is_pure_and_repeatable():
    assert render_pack("comms") == render_pack("comms")


# ---------- pack 元信息 ----------


def test_pack_meta():
    pack = render_pack("comms")
    assert isinstance(pack, PromptPack)
    assert pack.name == "comms"
    assert pack.session_scope == "comms"
    assert pack.version
    # capability 仅声明不调用
    assert pack.capabilities == ("harness.verify", "harness.task_lint")


# ---------- route_intent ----------


@pytest.mark.parametrize(
    "text",
    [
        "帮我开个 task",
        "我要立项",
        "帮我写个 SPEC",
        "写spec",
        "帮我起草 task 文件",
        "这个需求拆波次吧",
        "走 harness 流程",
        "走harness流程立项",
        "开TASK跟踪一下",
    ],
)
def test_route_intent_comms(text):
    assert route_intent(text) == "comms"


@pytest.mark.parametrize(
    "text",
    [
        "这个 issue 为什么挂了",
        "数据库怎么迁移",
        "lg-rag stream 的游标语义是什么",
        "这个 spec 字段含义解释一下",  # 业务问句提到 spec 字样仍回退 product
        "嗯",
        "你好",
        "帮我看看 PR #114",
    ],
)
def test_route_intent_product(text):
    assert route_intent(text) == "product"


@pytest.mark.parametrize("text", ["", "   ", None, 123, b"bytes", ["立项"], {"立项"}])
def test_route_intent_fallback_product(text):
    assert route_intent(text) == "product"


@pytest.mark.parametrize(
    "text",
    ["立项", "帮我开个 task", "issue 挂了", "", None, 123, "嗯", "走 harness 流程"],
)
def test_route_intent_strict_binary(text):
    assert route_intent(text) in ("comms", "product")


def test_route_intent_signature():
    sig = inspect.signature(route_intent)
    assert len(sig.parameters) == 1


# ---------- product 侧零影响 ----------


def test_product_templates_unchanged():
    # 2026-09-20：不再断言"集合恒等"。步骤契约（Q4/Q8）新增了
    # lg_rag.supervisor.suffix.system，这是**加法**——既有两枚的 key 与渲染
    # 行为都没动。真正的"product 侧零影响"是下面这条：既有 key 仍在。
    assert {"lg_rag.intent.system", "lg_rag.supervisor.system"} <= set(TEMPLATES)


def test_product_render_unchanged():
    tmpl = get_template("lg_rag.supervisor.system")
    # v1 → v2：body 增加了 produces / consumes 声明说明。
    # v2 → v3：body 文档化 args 结构化对象（fix-planner-args-schema · issue #339）。
    # version 必须跟着内容走，否则版本号本身就成了假信号。
    assert tmpl.version == "v3"
    text = render("lg_rag.supervisor.system", {"catalog_block": "(无)"})
    assert "Capability 目录" in text
    text_with_slot = render(
        "lg_rag.supervisor.system", {"catalog_block": "(无)"}, slots={"skill": "S"}
    )
    assert "<!-- slot:skill -->" in text_with_slot


def test_packs_module_no_session_or_chat_imports():
    import ast

    import app.ops.prompts.packs as packs_mod

    tree = ast.parse(inspect.getsource(packs_mod))
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module)
    offenders = {name for name in imported if name.startswith(("app.ops.session", "app.ops.chat"))}
    assert not offenders, f"packs 不得 import session/chat 流路径: {offenders}"
