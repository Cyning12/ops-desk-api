# PROMPT · 30(+40) · so-schema-hygiene

## 复制区

`````text
你是 ops-desk-api 的 30（可含 40）。只实现 task so-schema-hygiene（Structured Output 域 schema 卫生 H1）。

Open Folder：ops-desk-api 仓根。
分支：task/so-schema-hygiene。勿擅自 push；未授权勿开新 PR。可本地 commit。

首动作（零 diff）：
1. 输出 GATE_VERIFY 表（读 task 人工闸；docs/harness/prompts/FRAGMENT_30_gate_verify_v1_zh.md）
2. npx dsh-coding-kit verify --target . --task docs/tasks/active/task_so_schema_hygiene.md
任一 blocks 30 闸 pending 或 VERIFY 非 PASS → STOP。

落盘：docs/harness/invokes/by-task/so-schema-hygiene/invoke_20260826_30_40_so-schema-hygiene.md

必读：
- docs/tasks/active/task_so_schema_hygiene.md
- docs/spec/agent-infra/structured-output/ROADMAP_kernel_hygiene_v0.md §H1
- docs/spec/agent-infra/00_architecture_and_boundaries.md §5
- docs/standards/CODING_BACKEND_L2_v1_zh.md
- app/ops/structured_output/schemas/**
- app/ops/lg_rag/nodes.py · app/ops/lg_rag/multi/nodes.py
- tests/test_structured_output_*.py · tests/test_lg_rag_structured_output_p2.py（若存在）及相关 multi 测试

实现（H1）：
1. 新建 app/ops/lg_rag/schemas/，迁入 RouteDecision / SubtasksPlan / SubtaskItem / ExtractResult
2. lg_rag 节点改 import 到新路径
3. structured_output.schemas：可留短期 deprecated re-export，或删除；structured_output 包顶 __all__ 不含业务 schema
4. 更新单测 import；全仓 rg 旧路径清干净（除 deprecate 指针）
5. 可选 G-L1 备注「域 schema 在 lg_rag」；触及图谱则 ./scripts/graph-compile.sh

硬约束：
- 只搬家 + 改 import；不改 parse_only / acomplete 管道语义
- 禁止把 Host/SO 校验做成可选 Capability/MCP tool
- 禁止改 app/ops/chat/graph.py
- 禁止 Agently / instructor 运行时
- 单测 mock；不连真 LLM
- 注意避免 lg_rag ↔ schemas 循环 import

40：
- pytest tests/test_structured_output_parse_only.py tests/test_structured_output_complete.py tests/test_structured_output_p3.py tests/test_lg_rag_structured_output_p2.py tests/test_lg_rag_multi.py（缺文件则跳过并说明）
- ruff check 触及路径
- chat/graph.py 零 diff
- verify PASS
报告 00。简体中文。不要 push。
`````
