# 可复制 Prompt · 30 执行（Eval E5 · Token/费用账本）

> **给谁**：**30** 子代理。00 **不**执行。

---

## 复制区（整段粘贴）

`````text
你是 ops-desk-api 的 30。只实现 Eval E5。00 已授权 commit + push。禁止 merge、force push、改 git config。

工作区：/Users/cyning/Desktop/Ops-desk/ops-desk-api
分支：task/eval-token-cost-ledger（PR 将开；先 git pull）

开工前
1. 读 docs/tasks/active/task_eval_token_cost_ledger.md 闸表，输出 GATE_VERIFY
2. npx dsh-coding-kit verify --target . --task docs/tasks/active/task_eval_token_cost_ledger.md
3. pending → 拒改码
4. 读 04 §2.5、eval ROADMAP E5、app/ops/tracing.py update_current_generation_usage、app/config.py LLM 字段

必须
- GUIDE：docs/spec/agent-infra/eval/GUIDE_token_cost_ledger_v0.md
  · usage 审计清单（已上报路径 / 缺帧 usage_missing）
  · Host 价表 vs Langfuse model 单价对齐
  · price_missing / usage_missing 语义
  · 链到 eval/README.md
- 价表：evals/agent/cost/price_table_v1.yaml（provider+model、input/output 单价、币种、effective_from）；≥1 行真实默认模型价可占位注释
- 脚本：evals/agent/cost/export_cost.py（或 scripts 等价）：读 fixture usage → 算费用 → CSV/stdout；禁止 LLM 估费
- pytest：文件名含 eval_cost；离线绿
- invoke_*_30_*.md（真实退出码）
- 中文注释简洁

可选（非阻塞）：若触达成本低，可在 1 处 generation 路径钉 model/provider metadata；禁止大改 chat/graph.py

禁止
- 用 LLM 估 cost.usd_est
- 新 GHA Langfuse secret job；SDK v4
- 扩 E2 金标；改 RAG evals/golden
- 自建完整计费中台 / 租户账单 HTTP（除非极薄且 task 未禁止——本 task 禁止）
- 自己 merge PR

验收
- pytest tests -q --tb=short -k eval_cost 必须绿
- pytest tests -q --tb=short -k 'eval_agent or eval_experiment or eval_sample' 仍绿
- ruff 触及路径
- chat/graph.py git diff 空
- commit 例：feat(eval): E5 价表与费用导出账本
- git push origin HEAD

交还 00：sha、pytest 命令与 exit、GUIDE 路径、价表/脚本路径、app/ 是否有 diff。
`````
