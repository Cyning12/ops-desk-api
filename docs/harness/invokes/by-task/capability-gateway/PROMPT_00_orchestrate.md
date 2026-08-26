# 可复制 Prompt · 00 统筹（capability-gateway）

`````text
你是 ops-desk-api 的 00 统筹。不要实现 app/、tests/ 业务代码。
Open Folder = ops-desk-api/。分支 task/capability-gateway（从最新 master）。
SPEC：docs/spec/agent-infra/SPEC-capability-gateway_v0.md（HG-SPEC-SIGNOFF=approved）。
姊妹 structured-output 已落地（PR #58）；勿回改其范围。
切分 P0–P3 见 SPEC §4；每子 task 验收后再下一波；禁未签 HG-AUDIT-R1 就 30。
硬约束：不改 chat/graph.py；不引 Agently；不混 Structured Output 大改；过程闸可代签（须 20 R1）。
`````
