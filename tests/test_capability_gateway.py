"""Capability Gateway · P0 Registry/invoke + P1 schemas_for_llm + P2 probes（P2b-T4 起 P3 skill stub 退役——skill 是 prompt 资产不是工具）。"""

from __future__ import annotations

import json
from unittest.mock import patch

import pytest
from langchain_core.messages import AIMessage

from app.ops.capability import (
    CapabilityFilter,
    CapabilitySpec,
    LocalFnAdapter,
    get_registry,
    invoke,
    list_capabilities,
    provide,
    register,
    register_p2_probes,
    schemas_for_llm,
    unregister,
)
from app.ops.capability.defaults import (
    ensure_default_capabilities,
    mock_get_deploy_info,
    mock_get_issue_status,
)
from app.ops.capability.extras.langchain import as_structured_tools, as_tool_node
from app.ops.capability.probes import (
    PROBE_CLI_ID,
    PROBE_SANDBOX_ID,
)

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


def test_list_filter_node_role_is_placeholder_passthrough():
    """U2：node_role 为占位字段，单独传入不裁剪；推荐仍用 kinds/tags_any。"""
    by_role = list_capabilities(filter=CapabilityFilter(node_role="supervisor"))
    ids = {s.capability_id for s in by_role}
    assert "mock_get_issue_status" in ids
    assert "mock_get_deploy_info" in ids

    # supervisor 赋能列表推荐：kinds + tags（例：仅 issue 类给规划侧）
    planner_view = list_capabilities(
        filter=CapabilityFilter(
            node_role="supervisor",
            kinds=frozenset({"local_fn"}),
            tags_any=frozenset({"issue"}),
        )
    )
    assert {s.capability_id for s in planner_view} == {
        "mock_get_issue_status",
        "get_issue_by_number",
    }

    # tool_exec 侧同样用 tags/kinds 裁剪（node_role 不参与匹配）
    tool_view = list_capabilities(
        filter=CapabilityFilter(
            node_role="tool_exec",
            kinds=frozenset({"local_fn"}),
            tags_any=frozenset({"deploy"}),
        )
    )
    assert {s.capability_id for s in tool_view} == {"mock_get_deploy_info"}


def test_default_package_export_has_no_langgraph_bridge():
    """U1：默认 from app.ops.capability 不含 ToolNode 桥，也不拖 langgraph。"""
    import app.ops.capability as cap

    assert "as_tool_node" not in cap.__all__
    assert "as_structured_tools" not in cap.__all__
    assert not hasattr(cap, "as_tool_node")
    assert not hasattr(cap, "as_structured_tools")
    assert "langgraph" not in getattr(cap, "__dict__", {})


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
        assert "args_summary" in meta
        assert "policy" in meta
        assert "approval_id" in meta

        invoke("missing_tool", "x")
        meta2 = upd.call_args[0][0]
        assert meta2["ok"] is False
        assert "error" in meta2
        assert len(meta2["error"]) <= 200


def test_invoke_span_metadata_includes_subtask_and_args_summary():
    """阶段 H：ctx.subtask_id + args 摘要写入 span。"""
    with patch("app.ops.capability.gateway.update_current_span_metadata") as upd:
        invoke(
            "utc_now_iso",
            "",
            ctx={"subtask_id": "t9", "approval_id": None},
        )
        meta = upd.call_args[0][0]
        assert meta["subtask_id"] == "t9"
        assert meta["args_summary"] is not None
        assert meta["policy"] == "allowed"
        assert meta.get("approval_id") is None


def test_args_schema_invalid_returns_ok_false():
    """有 args_schema 时非法 args → ok=False · args_schema_invalid。"""
    result = invoke("utc_now_iso", [1, 2, 3])
    assert result.ok is False
    assert "args_schema_invalid" in (result.error or "")


def test_args_schema_lookup_rejects_wrong_number_type():
    result = invoke(
        "get_issue_by_number",
        {"number": ["bad"]},
        ctx={"tenant_id": "pilot"},
    )
    assert result.ok is False
    assert "args_schema_invalid" in (result.error or "")


# --- P1：schemas_for_llm + 可选 ToolNode ---


def test_schemas_for_llm_includes_default_builtins_with_schema():
    """阶段 H：默认能力已声明 args_schema → schemas_for_llm 含 builtin。"""
    names = {s["function"]["name"] for s in schemas_for_llm()}
    assert "utc_now_iso" in names
    assert "get_issue_by_number" in names
    assert "mock_get_issue_status" in names


def test_schemas_for_llm_skips_without_args_schema():
    """钉死：无 args_schema 的条目仍跳过（不吐残缺）。"""
    cid = "no_schema_probe"
    register(
        CapabilitySpec(
            capability_id=cid,
            kind="local_fn",
            description="无 schema",
            args_schema=None,
        ),
        LocalFnAdapter(lambda x: x),
    )
    names = {s["function"]["name"] for s in schemas_for_llm()}
    assert cid not in names
    unregister(cid)


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
    # 无 filter：含 builtin + 探针
    all_schemas = schemas_for_llm()
    by_name = {s["function"]["name"]: s for s in all_schemas}
    assert cid in by_name
    item = by_name[cid]
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
    """extras.langchain smoke：StructuredTool.invoke + ToolNode；不挂 multi 图。"""
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
    # ⚠️ langgraph 1.x 起 ToolNode **不能脱离图裸调**：它的内部 runnable 需要
    # config 里带 Runtime（图编译时注入），裸 ``node.invoke(...)`` 会抛
    # ``ValueError: Missing required config key 'N/A' for 'tools'``。
    # 所以这里按真实用法挂一个最小图（仍**不是** multi 主路径）。
    from langgraph.checkpoint.memory import InMemorySaver
    from langgraph.graph import END, START, MessagesState, StateGraph

    builder = StateGraph(MessagesState)
    builder.add_node("tools", node)
    builder.add_edge(START, "tools")
    builder.add_edge("tools", END)
    graph = builder.compile(checkpointer=InMemorySaver())

    # langgraph 1.x：挂了 checkpointer 就必须给 thread_id（否则直接 ValueError）
    out = graph.invoke({"messages": [msg]}, {"configurable": {"thread_id": "toolnode-smoke"}})
    assert len(out["messages"]) == 2, out["messages"]
    content = out["messages"][-1].content
    payload = json.loads(content) if isinstance(content, str) else content
    assert payload == {"echo": {"q": "via-node"}}
    unregister(cid)


# --- P2：sandbox / cli mock 探针（默认不进 defaults · P2b-T4 起 mcp mock 探针退役）---


def test_p2_probes_not_in_defaults():
    """默认 Gateway 仅 local_fn mock；探针不暴露、无外网路径。"""
    ids = {s.capability_id for s in list_capabilities()}
    assert PROBE_SANDBOX_ID not in ids
    assert PROBE_CLI_ID not in ids
    kinds = {s.kind for s in list_capabilities()}
    assert kinds == {"local_fn"}


def test_p2_probes_register_and_invoke_mock():
    """两 kind 探针可 register + invoke（mock · 零网络）。"""
    register_p2_probes(enabled=True)
    sandbox = invoke(
        PROBE_SANDBOX_ID,
        "echo",
        ctx={"_host_policy": {"allow_sandbox": True}},
    )
    assert sandbox.ok is True
    assert sandbox.output["sandbox"] == "mock"
    assert sandbox.output["exit_code"] == 0
    assert sandbox.meta.get("kind") == "sandbox"

    cli = invoke(
        PROBE_CLI_ID,
        ["echo", "hi"],
        ctx={"_host_policy": {"allow_cli": True}},
    )
    assert cli.ok is True
    assert cli.output["cli"] == "mock"
    assert cli.output["stdout"] == "cli-mock-ok"
    assert cli.meta.get("kind") == "cli"

    # Filter 按 kind
    cli_only = list_capabilities(filter=CapabilityFilter(kinds=frozenset({"cli"})))
    assert {s.capability_id for s in cli_only} == {PROBE_CLI_ID}


def test_p2_probes_default_disabled_blocks_invoke():
    """register_p2_probes() 默认 enabled=False → invoke blocked；filter 下不可见。"""
    register_p2_probes()  # enabled=False
    entry = get_registry().get(PROBE_CLI_ID)
    assert entry is not None
    assert entry[0].enabled is False

    # 带 filter 时 disabled 被裁掉
    visible = list_capabilities(filter=CapabilityFilter(kinds=frozenset({"cli"})))
    assert PROBE_CLI_ID not in {s.capability_id for s in visible}

    result = invoke(PROBE_CLI_ID, "x")
    assert result.ok is False
    assert result.meta.get("blocked") == "disabled"


def test_p2_probe_adapter_exception_ok_false():
    """探针异常 → ok=False（failure_paths）。"""
    # kind=sandbox（cli 默认 policy_disabled 会先于 adapter 拦截 · 不覆盖异常映射面）
    from app.ops.capability.adapters.sandbox import MockSandboxAdapter

    class _BoomSandbox(MockSandboxAdapter):
        def invoke(self, args, *, ctx=None):
            raise RuntimeError("sandbox-probe-boom")

    cid = "probe_sandbox_boom"
    register(
        CapabilitySpec(
            capability_id=cid,
            kind="sandbox",
            description="异常探针",
            tags=("probe",),
            enabled=True,
        ),
        _BoomSandbox(),
    )
    # sandbox kind 须 host 键放行（policy 门先于 adapter · :105 闸序）
    result = invoke(cid, None, ctx={"_host_policy": {"allow_sandbox": True}})
    assert result.ok is False
    assert "sandbox-probe-boom" in (result.error or "")
    unregister(cid)


# --- provide 负样本（P2b-T4：kind=skill stub 已退役——skill 是 prompt 资产不是工具）---


def test_provide_on_local_fn_ok_false():
    """无 provide 的 adapter → provide 返回 ok=False。"""
    result = provide("mock_get_issue_status")
    assert result.ok is False
    assert "无 provide()" in (result.error or "")

