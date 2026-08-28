# 可复制 Prompt · 30 执行（Eval E3 · Dataset / Experiment mock）

> **给谁**：**30** 子代理或新窗。00 **不**执行。

---

## 复制区（整段粘贴）

`````text
你是 ops-desk-api 的 30。只实现 Eval E3。00 已授权 commit + push。禁止 merge、force push、改 git config。

工作区：/Users/cyning/Desktop/Ops-desk/ops-desk-api
分支：task/eval-langfuse-experiment-ci

开工前
1. 读 docs/tasks/active/task_eval_langfuse_experiment_ci.md 闸表
2. npx dsh-coding-kit verify --target . --task docs/tasks/active/task_eval_langfuse_experiment_ci.md
3. pending → 拒改码
4. 读 eval ROADMAP §3 score 名、§4.1；复用 tests/eval/eval_agent_graders.py 与 evals/agent/golden/（不扩条数）

必须
- GUIDE 一页：git 为 SoT；Dataset 名 golden-<module>-v1；dry-run vs --push；CI 不连云。链到 docs/spec/agent-infra/eval/README.md
- evals/agent/run_experiment.py（或 scripts 等价）：默认 dry-run，stdout JSON；复用已有评估器；score 名仅 acc.route_match / acc.strategy.allowlist_match / acc.plan_match
- pytest：文件名含 eval_experiment；mock Langfuse；无 key 时 dry-run 绿；grader 失败则非 0
- 落盘 invoke_*_30_*.md（真实命令与退出码）

禁止
- 新 GitHub Actions workflow 或给 pytest.yml 加 Langfuse secret
- 改 app/、chat/graph.py、tracing.py、score_current_trace
- 改 RAG evals/golden、扩 E2 fixture 条数
- E4/E5、Langfuse SDK v4、自己 merge PR

验收
- pytest tests -q --tb=short -k eval_experiment 必须绿
- 再确认 pytest tests -q --tb=short -k eval_agent 仍绿
- ruff 触及路径
- commit 例：feat(eval): E3 Dataset 映射与 mock Experiment runner
- git push origin HEAD

交还：sha、pytest 两命令 exit、有无 app/ diff、GUIDE 路径。
`````
