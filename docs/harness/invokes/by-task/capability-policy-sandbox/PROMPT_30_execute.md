# PROMPT · 30 · capability-policy-sandbox（H2）

`````text
你是 ops-desk-api 的 30（可含 40）。只实现 capability-policy-sandbox（Agent Host H2）。

工作目录：/Users/cyning/Desktop/Ops-desk/ops-desk-api
分支：task/capability-policy-sandbox。勿 push；未授权勿 commit。

GATE_VERIFY + npx dsh-coding-kit verify --target . --task docs/tasks/active/task_capability_policy_sandbox.md
落盘 invoke_20260827_30_40_capability-policy-sandbox.md

必读
  docs/tasks/active/task_capability_policy_sandbox.md
  docs/spec/agent-infra/capability/ROADMAP_policy_and_sandbox_v0.md
  docs/spec/agent-infra/capability/SPEC-capability-gateway_v0.md
  app/ops/capability/gateway.py · probes.py · adapters/sandbox.py · adapters/cli.py

范围（H2-a–f）
  policy.py：check_invoke(spec, ctx) → allow|block|reason
  invoke() 统一过 policy；blocked → ok=False + error 含 policy_blocked
  Host-only 策略键文档 + 单测
  sandbox/cli 样例注册 env 默认关
  span：policy_blocked · risk_level · capability_id
  test_lg_rag_multi 不回归

硬约束
  不改 chat/graph.py；CI 不跑真 shell
  维护者未说 push 则不 push

40：pytest + ruff + graph-compile。报告 00。简体中文。
`````
