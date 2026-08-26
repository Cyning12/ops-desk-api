# PROMPT · 30 · structured-output-gateway-p3

`````text
你是 ops-desk-api 的 30（可含 40）。只实现 structured-output-gateway-p3。

工作目录：/Users/cyning/Desktop/Ops-desk/ops-desk-api
分支：task/structured-output-gateway。勿 push；未授权勿 commit。

GATE_VERIFY + npx dsh-coding-kit verify --target . --task docs/tasks/active/task_structured_output_gateway_p3.md
落盘 invoke_20260826_30_40_structured-output-gateway-p3.md

必读：task_p3；SPEC §3 步骤4–5 / §4 P3；app/ops/structured_output/parse.py 与 complete.py（ensure_keys/validate 现为 P3 预留 del）；FRAGMENT_30；CODING_BACKEND_L2。

范围：
1. 接通 ensure_keys（必填路径 presence/not_null；路径约定写注释）
2. 接通 custom validate callable
3. no_retry：失败不写敏感规则进 OUTPUT CORRECTION（单测）
4. 文档：docs/guides/DESIGN_structured-output-gateway-coexistence_v0.md（与 with_structured_output 并存策略）
5. SPEC 修订记录追加 P0–P3 落地状态一行
6. 单测

硬约束：不新接业务节点；不改 chat/graph.py；无 Capability/Agently；无真 LLM。

40：pytest+ruff+graph.py 0。报告 00。简体中文。
`````
