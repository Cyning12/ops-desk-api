# 可复制 Prompt · 30 执行（Eval E2 · lg_rag 模块金标）

> **给谁**：新开的 **30** 会话。00 **不**执行本 Prompt。  
> **Open Folder**：`ops-desk-api/` 仓根。  
> **分支**：`task/eval-goldenset-lg-rag`（相对 `origin/master`）。  
> **task**：`docs/tasks/active/task_eval_goldenset_lg_rag.md`  
> 闸表 **已** `HG-AUDIT-R1=approved`（以 task 文件为准，勿信聊天口头）。

---

## 复制区（整段粘贴）

`````text
你是 ops-desk-api 的 30 执行帽。只实现 Eval E2 金标与确定性评估器。

Open Folder = ops-desk-api/ 仓根。
分支 = task/eval-goldenset-lg-rag（已有 00/10/20 文档；在此继续 commit，禁止另开无关分支，禁止直推 master）。

开工前（强制）
1. 读 docs/tasks/active/task_eval_goldenset_lg_rag.md 人工闸表，输出 GATE_VERIFY 表。
2. 运行：npx dsh-coding-kit verify --target . --task docs/tasks/active/task_eval_goldenset_lg_rag.md
3. 任一 blocks 30 的闸 pending → 拒改码。
4. 读 docs/spec/agent-infra/eval/ROADMAP_eval_observability_v0.md §3 字典与 §4 颗粒度。
5. 读 docs/standards/CODING_BACKEND_L2_v1_zh.md。
6. 对照 tests/test_strategy_builder.py、tests/test_lg_rag_supervisor_capability_catalog.py 的 mock 手法。

范围（必须）
- 目录 evals/agent/golden/router/ 、strategy_builder/ 、supervisor/ 、e2e/
- router ≥3 条：query + expect.route（枚举对照现 lg_rag router 出口）
- strategy_builder ≥2 条：expect.allowed_capability_ids 集合相等
- supervisor ≥2 条：plan 结构（subtask_types 和/或 supervisor_fallback）
- e2e 恰好 1 条：mock 全链到 END
- tests/eval/ 或 tests/test_eval_agent_*.py：确定性评估器（枚举相等、tool id ∈ allowlist、plan JSON schema）
- pytest 须能被 tests 收集；建议文件名含 eval_agent 以便 -k eval_agent
- mock LLM；不连真模型、真库、Langfuse API

非范围（禁止）
- E3：Langfuse Dataset / Experiment / 新 GitHub Actions workflow
- E4：tracing.score_current_trace、线上抽样
- E5：价表 / usage 账本
- 改 app/ops/chat/graph.py
- 改 evals/golden/queries_v1.yaml 或 evals/golden/run_eval.py（RAG 检索金标不是 E2）
- 改 evals/router/labeled_router_v1.yaml 语义（可抽样复制 query 文本到新 fixture）
- 补 span metadata module=（本波非阻塞，默认不改 app/）
- LLM-as-judge
- 自己 merge PR、改无关 task

验收
- pytest tests -q --tb=short -k eval_agent   （或 pytest tests/eval -q --tb=short）
- ruff check 触及路径
- git diff 确认 chat/graph.py 与 RAG golden runner 无改
- 落盘 docs/harness/invokes/by-task/eval-goldenset-lg-rag/invoke_*_30_*.md（命令与结果）
- 不要伪造测试；失败就停并写进 invoke

commit
- 仅在维护者已授权本窗 commit 时提交；message 例：test(eval): E2 lg_rag 模块金标最小集
- 不要 push --force；不要改 git config

完成后交还 00：列文件、pytest 命令与退出码、未做的 module= 声明。
`````
