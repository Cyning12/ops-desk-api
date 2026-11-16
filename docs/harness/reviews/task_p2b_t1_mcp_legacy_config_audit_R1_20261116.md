# task_p2b_t1_mcp_legacy_config · R1 审查文（20 帽）

- 时刻：2026-11-16
- 审查人：exec-p2b-t1（20 帽 · 夜间授权 issue Cyning12/ops-desk-workspace#23 m03064/m03216 · 00 代签体系）
- 对象：`docs/tasks/active/task_p2b_t1_mcp_legacy_config.md` v1

## 审查项

1. **范围对账**：task 范围 10 条与 11-p2b-mcp-skill-design.md 终稿 §8 T1 行
   （旧 MCP 遗产清除 + mcp_servers.yaml 配置面）1:1；§2 删除面（mcp_client.py 全文件 ·
   capability/__init__.py:108 调用 · config.py 两键留总闸）逐条落入；§7-② 键面
   （key/transport/url|command+args/cwd/env_allowlist/protocol_version 钉版/
   expected_server/connect_timeout_s=10/call_timeout_s=30/default_side_effect/
   tool_overrides 含 description_override/exclude_tools）全落入 schema。GO。
2. **非范围**：manifest.py kind 词表（T3）、skill_registry/slots/nodes 与
   adapters/skill.py、skill_stub.py、adapters/mcp.py 整删（T4）、连接/握手/注册（T2）
   均已明示排除；P2 mock 探针用例（test_capability_gateway.py:357-441）不动。GO。
3. **删除面实证**：五符号（register_mcp_client_if_enabled/McpClientAdapter/
   HttpJsonRpcTransport/ops_capability_mcp_endpoint/ops_capability_mcp_default_tool）
   全部命中点已 grep 定位；R8 四处（.env.example:137-140 · capability README:23 ·
   ROADMAP:52 · 01_modules:34）行号实证。档案豁免面（task_cap_mcp_real 族）明示。GO。
4. **偏差登记**：D1（adapters/mcp.py:5 一行 docstring 含 McpClientAdapter 字样，
   验收 grep 零命中要求必清；整删属 T4）理由成立、改动最小、无行为变化。GO。
5. **验收可机判**：grep 零命中清单 + 范围/豁免面明示；解析单测拒载场景枚举完整；
   pytest/ruff/import-linter/CI 终裁口径明。GO。
6. **思考轮**：R0-R5 表 + R0/R2/R3/R4 小节齐备；R3 记录 McpTransport Protocol 不保留
   决策与钉版/fail-closed/传输互斥决策。GO。
7. **registry N3 entry**：base=bf1c23f2 · allowed_app_files 八件精确列举 ·
   allowed_tree_files 十一件 · banned_prefixes=[alembic/, scripts/, app/ops/lg_rag/] ·
   yaml safe_load 验证通过（19 waves）。GO。
8. **人工闸**：HG-TASK-DRAFT / HG-AUDIT-R1 / HG-GRAPH-MODULES 三行 approved，
   依据 issue #23 m03064/m03216 夜间授权；01_modules.md 签收承 :135/:136 先例。GO。

## 结论

**GO · 通过（零阻塞项）** —— task v1 可进 30 实施（夜间授权窗口 · 30 台账见 invoke_20261116_30_impl.md · 40 验收台账见 invoke_20261116_40_acceptance.md）。
