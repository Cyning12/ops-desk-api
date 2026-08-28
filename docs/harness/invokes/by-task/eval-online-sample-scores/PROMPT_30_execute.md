# 可复制 Prompt · 30 执行（Eval E4 · 线上抽样 score）

> **给谁**：**30** 子代理。00 **不**执行。

---

## 复制区（整段粘贴）

`````text
你是 ops-desk-api 的 30。只实现 Eval E4。00 已授权 commit + push。禁止 merge、force push、改 git config。

工作区：/Users/cyning/Desktop/Ops-desk/ops-desk-api
分支：task/eval-online-sample-scores（已有 00 文档；先 git pull）

开工前
1. 读 docs/tasks/active/task_eval_online_sample_scores.md 闸表，输出 GATE_VERIFY
2. npx dsh-coding-kit verify --target . --task docs/tasks/active/task_eval_online_sample_scores.md
3. pending → 拒改码
4. 读 app/ops/tracing.py、app/ops/lg_rag/multi/nodes.py（supervisor_fallback）、eval ROADMAP §3.2

必须
- app/ops/tracing.py：score_current_trace(name, value, ...)；tracing 关 / 异常 → 静默 no-op
- 采样：OPS_EVAL_SCORE_SAMPLE_RATE（0.0–1.0，默认 0）；非法值当 0 + warning
- 至少 1 调用点：supervisor_fallback=True 时 stab.fallback=1（Boolean/0-1 与字典一致）
- GUIDE：docs/spec/agent-infra/eval/GUIDE_online_sample_annotation_v0.md（抽样 + Annotation Queue 回流流程）；链到 eval/README.md
- pytest：文件名含 eval_sample 或 score_current；mock；rate=0 零调用；rate=1 + mock 写分
- invoke_*_30_*.md（真实退出码）
- 中文注释简洁

禁止
- 热路径 LLM-as-judge / acc.answer_judge
- E5 价表；扩金标；改 chat/graph.py
- 新 GHA secret workflow；Langfuse SDK v4
- 全图节点打分（最多 2 调用点）
- 自己 merge PR

验收
- pytest tests -q --tb=short -k eval_sample   （或 -k score_current）必须绿
- pytest tests -q --tb=short -k 'eval_agent or eval_experiment' 仍绿
- ruff 触及路径
- chat/graph.py git diff 空
- commit 例：feat(eval): E4 score_current_trace 与 stab.fallback 抽样
- git push origin HEAD

交还 00：sha、pytest 命令与 exit、GUIDE 路径、app/ 触达文件列表。
`````
