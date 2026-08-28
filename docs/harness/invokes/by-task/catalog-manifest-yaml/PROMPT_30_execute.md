# PROMPT · 30 · catalog-manifest-yaml（S3）

> **给谁**：新开的 **30**（可含 40）。  
> **Open Folder**：`ops-desk-api/` 仓根。  
> **分支**：`task/catalog-manifest-yaml`。

---

## 复制区（整段粘贴）

`````text
你是 ops-desk-api 的 30（可含 40）。只实现 catalog-manifest-yaml（Strategy Builder S3）。

工作目录：以维护者 worktree 为准的 ops-desk-api 仓根
分支：task/catalog-manifest-yaml。勿 push；未授权勿 commit。

GATE_VERIFY（首输出必填表 · 真值读 task 人工闸表）
  + npx dsh-coding-kit verify --target . --task docs/tasks/active/task_catalog_manifest_yaml.md
落盘 docs/harness/invokes/by-task/catalog-manifest-yaml/invoke_20260828_30_40_catalog-manifest-yaml.md

必读
  docs/tasks/active/task_catalog_manifest_yaml.md
  docs/spec/agent-infra/03_strategy_and_intent_plan_v0.md §6
  docs/spec/agent-infra/strategy/ROADMAP_strategy_builder_v0.md §5 / §8
  docs/harness/reviews/task_catalog_manifest_yaml_audit_R1_20260828.md
  app/ops/capability/defaults.py
  app/ops/capability/gateway.py（register / 重复 id）
  app/ops/capability/types.py
  app/ops/capability/adapters/local_fn.py
  docs/harness/prompts/FRAGMENT_30_gate_verify_v1_zh.md
  docs/standards/CODING_BACKEND_L2_v1_zh.md

范围（S3-a–b only）
  S3-a：
    load_capability_manifest(path) → Host register
    内置 app/ops/capability/manifests/builtin.v1.yaml（三枚默认 local_fn，对齐 defaults.py）
    YAML + JSON；yaml.safe_load（勿 PyYAML 新大版本依赖除非 import 失败再写入 requirements）
    kind 仅 local_fn；adapter 仅 local_fn:app.ops.capability.defaults:<attr>
    enabled:false 跳过
    非法 adapter / 未知 kind / 缺 id → 整文件失败（不半套注册）
    ensure_default_capabilities：优先 load builtin；文件缺失回退 _DEFAULT_SPECS；幂等 skip 已注册
  S3-b：
    manifest version + capability_manifest_count metadata
    显式 reload_capability_manifest（测试/运维）；禁止每请求 / HTTP 钩子加载
  G-L1 capability 行备注 + 10_flow_capability.graph.yaml 增 load 节点 + graph-compile
  单测 + ruff；无密钥进仓

硬约束
  不改 app/ops/chat/graph.py、lg_rag/multi/graph.py 拓扑
  Builder 不解析 YAML
  不从 manifest 注册 MCP/sandbox/cli/skill
  不实现 S4 Critic / Eval
  不混改无关 active task
  S1/S2 语义不回归

40
  pytest 触及路径 + ruff + chat/graph.py 与 multi/graph.py 0 拓扑 diff + ./scripts/graph-compile.sh
  报告 00。简体中文。勾选 task 验收项；勿伪造测试结果。
`````

---

## 修订

| 日期 | 说明 |
|---|---|
| 2026-08-28 | 初版 S3 30 Prompt |
