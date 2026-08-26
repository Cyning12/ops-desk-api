"""Capability Gateway · P0 Registry/invoke + P1 schemas_for_llm + P2 probes + P3 skill stub。"""

from __future__ import annotations

import json
from unittest.mock import patch

import pytest
from langchain_core.messages import AIMessage

from app.ops.capability import (
    CapabilityFilter,
    CapabilitySpec,
    LocalFnAdapter,
    as_structured_tools,
    as_tool_node,
    get_registry,
    invoke,
    list_capabilities,
    provide,
    register,
    register_p2_probes,
    register_skill_stub,
    schemas_for_llm,
    unregister,
)
from app.ops.capability.defaults import (
    ensure_default_capabilities,
    mock_get_deploy_info,
    mock_get_issue_status,
)
from app.ops.capability.probes import (
    PROBE_CLI_ID,
    PROBE_MCP_ID,
    PROBE_SANDBOX_ID,
)
from app.ops.capability.skill_stub import STUB_SKILL_ID, STUB_SKILL_REF

_P1_ARGS_SCHEMA = {
    "type": "object",
    "properties": {
        "q": {"type": "string", "description": "查询串"},
    },
    "required": ["q"],
}


@pytest.fixture(autouse=True)
def _restore_default_mocks():
    """每个用例后恢复默认 mock，避免 clear / 临时注册污染后续。"""
    yield
    get_registry().clear()
    ensure_default_capabilities()


def test_default_mocks_registered_and_invoke_ok():
    ids = {s.capability_id for s in list_capabilities()}
    assert "mock_get_issue_status" in ids
    assert "mock_get_deploy_info" in ids

    issue = invoke("mock_get_issue_status", "查 #128")
    assert issue.ok is True
    assert issue.output == mock_get_issue_status("查 #128")
    assert issue.capability_id == "mock_get_issue_status"

    deploy = invoke("mock_get_deploy_info", "prod")
    assert deploy.ok is True
    assert deploy.output == mock_get_deploy_info("prod")


def test_unknown_id_returns_ok_false_not_raise():
    result = invoke("no_such_capability", "x")
    assert result.ok is False
    assert "未知工具" in (result.error or "")
    assert result.output is None


def test_empty_id_unknown():
    result = invoke("", None)
    assert result.ok is False
    assert "(未指定)" in (result.error or "")


def test_local_fn_adapter_exception_ok_false():
    def _boom(_payload: str) -> dict:
        raise RuntimeError("boom")

    cid = "test_boom_local_fn"
    register(
        CapabilitySpec(
            capability_id=cid,
            kind="local_fn",
            description="抛错探针",
        ),
        LocalFnAdapter(_boom),
    )
    result = invoke(cid, "in")
    assert result.ok is False
    assert "boom" in (result.error or "")
    unregister(cid)


def test_duplicate_register_raises_value_error():
    """重复 id 行为钉死：拒绝覆盖（raise ValueError），须先 unregister。"""
    with pytest.raises(ValueError, match="已注册"):
        register(
            CapabilitySpec(
                capability_id="mock_get_issue_status",
                kind="local_fn",
                description="重复注册应失败",
            ),
            LocalFnAdapter(lambda x: x),
        )


def test_unregister_then_reregister_ok():
    cid = "mock_get_issue_status"
    assert unregister(cid) is True
    register(
        CapabilitySpec(
            capability_id=cid,
            kind="local_fn",
            description="重新注册",
            tags=("mock",),
        ),
        LocalFnAdapter(mock_get_issue_status),
    )
    assert invoke(cid, "x").ok is True


def test_list_filter_kinds_and_tags():
    specs = list_capabilities(
        filter=CapabilityFilter(kinds=frozenset({"local_fn"}), tags_any=frozenset({"deploy"}))
    )
    assert len(specs) == 1
    assert specs[0].capability_id == "mock_get_deploy_info"


def test_invoke_writes_span_metadata_on_current_span():
    """兼容 tool_exec：不另开根 span，只 update_current_span_metadata。"""
    with patch("app.ops.capability.gateway.update_current_span_metadata") as upd:
        invoke("mock_get_issue_status", "span-check")
        upd.assert_called_once()
        meta = upd.call_args[0][0]
        assert meta["capability_id"] == "mock_get_issue_status"
        assert meta["kind"] == "local_fn"
        assert meta["ok"] is True
        assert "error" not in meta

        invoke("missing_tool", "x")
        meta2 = upd.call_args[0][0]
        assert meta2["ok"] is False
        assert "error" in meta2
        assert len(meta2["error"]) <= 200


# --- P1：schemas_for_llm + 可选 ToolNode ---


def test_schemas_for_llm_skips_without_args_schema():
    """钉死：默认 mock 无 args_schema → schemas_for_llm 跳过（不吐残缺条目）。"""
    assert schemas_for_llm() == []


def test_schemas_for_llm_shape_and_filter():
    cid = "p1_schema_probe"
    register(
        CapabilitySpec(
            capability_id=cid,
            kind="local_fn",
            description="P1 schema 探针",
            args_schema=_P1_ARGS_SCHEMA,
            tags=("p1", "schema"),
        ),
        LocalFnAdapter(lambda args: args),
    )
    # 无 filter：仅含带 schema 的条目
    all_schemas = schemas_for_llm()
    assert len(all_schemas) == 1
    item = all_schemas[0]
    assert item["type"] == "function"
    assert item["function"]["name"] == cid
    assert item["function"]["description"] == "P1 schema 探针"
    assert item["function"]["parameters"] == _P1_ARGS_SCHEMA
    # 可序列化（OpenAI / LangChain tools 风格）
    json.dumps(all_schemas)

    # Filter：tags / kinds
    filtered = schemas_for_llm(
        filter=CapabilityFilter(
            kinds=frozenset({"local_fn"}),
            tags_any=frozenset({"schema"}),
        )
    )
    assert len(filtered) == 1
    assert filtered[0]["function"]["name"] == cid

    empty = schemas_for_llm(filter=CapabilityFilter(tags_any=frozenset({"nope"})))
    assert empty == []
    unregister(cid)


def test_as_structured_tools_and_tool_node_smoke():
    """可选 adapter smoke：StructuredTool.invoke + ToolNode；不挂 multi 图。"""
    cid = "p1_toolnode_probe"

    def _echo(args: dict) -> dict:
        return {"echo": args}

    register(
        CapabilitySpec(
            capability_id=cid,
            kind="local_fn",
            description="ToolNode smoke",
            args_schema=_P1_ARGS_SCHEMA,
            tags=("p1", "toolnode"),
        ),
        LocalFnAdapter(_echo),
    )
    flt = CapabilityFilter(tags_any=frozenset({"toolnode"}))
    tools = as_structured_tools(filter=flt)
    assert len(tools) == 1
    assert tools[0].name == cid
    assert tools[0].invoke({"q": "hi"}) == {"echo": {"q": "hi"}}

    node = as_tool_node(filter=flt)
    msg = AIMessage(
        content="",
        tool_calls=[
            {
                "name": cid,
                "args": {"q": "via-node"},
                "id": "call_1",
                "type": "tool_call",
            }
        ],
    )
    out = node.invoke({"messages": [msg]})
    assert len(out["messages"]) == 1
    content = out["messages"][0].content
    payload = json.loads(content) if isinstance(content, str) else content
    assert payload == {"echo": {"q": "via-node"}}
    unregister(cid)


# --- P2：mcp / sandbox / cli mock 探针（默认不进 defaults）---


def test_p2_probes_not_in_defaults():
    """默认 Gateway 仅 local_fn mock；探针不暴露、无外网路径。"""
    ids = {s.capability_id for s in list_capabilities()}
    assert PROBE_MCP_ID not in ids
    assert PROBE_SANDBOX_ID not in ids
    assert PROBE_CLI_ID not in ids
    kinds = {s.kind for s in list_capabilities()}
    assert kinds == {"local_fn"}


def test_p2_probes_register_and_invoke_mock():
    """三 kind 探针可 register + invoke（mock · 零网络）。"""
    register_p2_probes(enabled=True)
    mcp = invoke(PROBE_MCP_ID, {"q": "mcp"})
    assert mcp.ok is True
    assert mcp.output["protocol"] == "mcp-mock"
    assert mcp.output["kind"] == "mcp"
    assert mcp.meta.get("kind") == "mcp"

    sandbox = invoke(PROBE_SANDBOX_ID, "echo")
    assert sandbox.ok is True
    assert sandbox.output["sandbox"] == "mock"
    assert sandbox.output["exit_code"] == 0
    assert sandbox.meta.get("kind") == "sandbox"

    cli = invoke(PROBE_CLI_ID, ["echo", "hi"])
    assert cli.ok is True
    assert cli.output["cli"] == "mock"
    assert cli.output["stdout"] == "cli-mock-ok"
    assert cli.meta.get("kind") == "cli"

    # Filter 按 kind
    mcp_only = list_capabilities(filter=CapabilityFilter(kinds=frozenset({"mcp"})))
    assert {s.capability_id for s in mcp_only} == {PROBE_MCP_ID}


def test_p2_probes_default_disabled_blocks_invoke():
    """register_p2_probes() 默认 enabled=False → invoke blocked；filter 下不可见。"""
    register_p2_probes()  # enabled=False
    entry = get_registry().get(PROBE_MCP_ID)
    assert entry is not None
    assert entry[0].enabled is False

    # 带 filter 时 disabled 被裁掉
    visible = list_capabilities(filter=CapabilityFilter(kinds=frozenset({"mcp"})))
    assert PROBE_MCP_ID not in {s.capability_id for s in visible}

    result = invoke(PROBE_MCP_ID, "x")
    assert result.ok is False
    assert result.meta.get("blocked") == "disabled"


def test_p2_probe_adapter_exception_ok_false():
    """探针异常 → ok=False（failure_paths）。"""
    from app.ops.capability.adapters.mcp import MockMcpAdapter

    class _BoomMcp(MockMcpAdapter):
        def invoke(self, args, *, ctx=None):
            raise RuntimeError("mcp-probe-boom")

    cid = "probe_mcp_boom"
    register(
        CapabilitySpec(
            capability_id=cid,
            kind="mcp",
            description="异常探针",
            tags=("probe",),
            enabled=True,
        ),
        _BoomMcp(),
    )
    result = invoke(cid, None)
    assert result.ok is False
    assert "mcp-probe-boom" in (result.error or "")
    unregister(cid)


# --- P3：kind=skill provide / invoke stub（非完整引擎）---


def test_p3_skill_stub_not_in_defaults():
    """默认 Gateway 无 skill；stub 须显式 register_skill_stub。"""
    ids = {s.capability_id for s in list_capabilities()}
    assert STUB_SKILL_ID not in ids
    kinds = {s.kind for s in list_capabilities()}
    assert "skill" not in kinds


def test_p3_skill_provide_ok_invoke_not_implemented():
    """provide → stub 上下文；invoke → NotImplementedError → ok=False。"""
    register_skill_stub(enabled=True)
    provided = provide(STUB_SKILL_ID, ctx={"node_role": "tool_exec"})
    assert provided.ok is True
    assert provided.output["mode"] == "provide"
    assert provided.output["engine"] == "stub"
    assert provided.output["skill_ref"] == STUB_SKILL_REF
    assert "node_role" in provided.output["ctx_keys"]
    assert provided.meta.get("kind") == "skill"
    assert provided.meta.get("mode") == "provide"

    invoked = invoke(STUB_SKILL_ID, {"step": 1})
    assert invoked.ok is False
    assert "NotImplementedError" in (invoked.error or "")
    assert "完整 Skill 执行引擎未实现" in (invoked.error or "")
    assert invoked.meta.get("kind") == "skill"
    assert invoked.meta.get("mode") == "invoke"


def test_p3_skill_stub_default_disabled_blocks():
    """register_skill_stub() 默认 enabled=False → provide/invoke blocked。"""
    register_skill_stub()  # enabled=False
    entry = get_registry().get(STUB_SKILL_ID)
    assert entry is not None
    assert entry[0].enabled is False

    visible = list_capabilities(filter=CapabilityFilter(kinds=frozenset({"skill"})))
    assert STUB_SKILL_ID not in {s.capability_id for s in visible}

    assert provide(STUB_SKILL_ID).ok is False
    assert provide(STUB_SKILL_ID).meta.get("blocked") == "disabled"
    assert invoke(STUB_SKILL_ID, None).meta.get("blocked") == "disabled"


def test_p3_provide_on_local_fn_ok_false():
    """非 skill / 无 provide 的 adapter → provide 返回 ok=False。"""
    result = provide("mock_get_issue_status")
    assert result.ok is False
    assert "无 provide()" in (result.error or "")
