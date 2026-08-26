# 可复制 Prompt · 30（+40 自检）· structured-output-gateway-p0

> **给谁**：子 agent（hat 30，可含 40 自检）。  
> **Open Folder**：`ops-desk-api/` 仓根。  
> **分支**：必须在 `task/structured-output-gateway`。

---

## 复制区（整段粘贴）

`````text
你是 ops-desk-api 的 30 执行帽（可含 40 自检）。只实现当前子 task：structured-output-gateway-p0。

Open Folder = ops-desk-api/ 仓根。
分支 = task/structured-output-gateway（禁止改 master；勿擅自 push；维护者未说 commit 则不要 commit）。

首输出（改码前强制）
1. 读 task 人工闸表，输出 GATE_VERIFY 表（见 docs/harness/prompts/FRAGMENT_30_gate_verify_v1_zh.md）。
2. 运行：npx dsh-coding-kit verify --target . --task docs/tasks/active/task_structured_output_gateway_p0.md
3. 任一 blocks 30 的闸 pending → 零 diff 停工。
4. 落盘 invoke：docs/harness/invokes/by-task/structured-output-gateway-p0/invoke_*_30_*.md（可含 40）

必读
- docs/tasks/active/task_structured_output_gateway_p0.md（验收 / 非范围 / failure_paths）
- docs/spec/agent-infra/SPEC-structured-output-gateway_v0.md（§3 管道 · §3.2 Host · §3.3 Repair · §4 P0）
- docs/standards/CODING_BACKEND_L2_v1_zh.md
- app/ops/lg_rag/multi/nodes.py 的 _extract_json_object
- docs/harness/prompts/FRAGMENT_30_gate_verify_v1_zh.md

范围（P0 only）
- 新建 app/ops/structured_output/：parse_only(text, *, schema) -> ParseOutcome（或等价公开 API）
- 管道：extract/parse →（可选）deterministic repair → Pydantic validate
- 公共 JSON 提取：封装/替换 multi/nodes.py 的 _extract_json_object（委托公共实现；不改 supervisor fallback / router / info_extract 业务语义）
- 单测 mock：合法 JSON / fence / 杂讯 / 结构坏引号 repair / schema 失败不得当成功
- G-L1：docs/_tech_graph/l1/01_modules.md 的 lg_rag 行备注一句（不新增一级模块）+ ./scripts/graph-compile.sh

硬约束
- Host 校验权威：schema 失败不得当成功业务数据
- 确定性 repair 仅修结构符号；不改字符串语义
- 不实现 complete_structured / max_retries / OUTPUT CORRECTION（P1）
- 不接入 supervisor/router/info_extract 业务路径与 fallback span（P2）
- 不实现 ensure_keys / custom validate / 并存文档（P3）
- 不改 app/ops/chat/graph.py
- 不实现 Capability Gateway
- 不引入 Agently 运行时依赖
- 单测不连真 LLM/真库
- 无关 active task 文件勿改
- app/tools/ 若存在未跟踪草稿，勿擅自纳入本 task 范围（除非委托必须）

验收自检（40）
- pytest 触及本 task 测试 + 既有 test_lg_rag_multi 不回归
- ruff check 触及路径
- git diff 确认 chat/graph.py 零改动
- graph-compile.sh（若改图谱）
- 回填 30/40 invoke 验证命令与结论

完成后告诉 00：变更路径列表、测试命令与结果、是否可机械关账。
`````
