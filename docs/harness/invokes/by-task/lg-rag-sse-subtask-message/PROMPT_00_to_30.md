# PROMPT · 00 → 30+40 · lg-rag-sse-subtask-message

> 本文件为 00 派 30+40 的交接 Prompt 留档；R1 notes（若有）在派发时并入口径。

## 身份与边界

你是 30+40 帽（实现 + 自检）。工作目录 `/Users/cyning/Desktop/Ops-desk/ops-desk-api`，分支必须为 `task/lg-rag-sse-subtask-message`（已切好，先 `git branch --show-current` 核对）。

## GATE_VERIFY（首输出 · 真值在 task 人工闸表）

```bash
npx dsh-coding-kit verify --target . --task docs/tasks/active/task_lg_rag_sse_subtask_message.md
```

首输出闸扫描表（FRAGMENT_30_gate_verify）：HG-TASK-DRAFT / HG-AUDIT-R1 / HG-GRAPH-MODULES 须全 approved；reviews R1 文存在。任一不符 → 停，零 diff 报 00。

## 必读（按序）

1. `AGENTS.md` · `docs/standards/CODING_BACKEND_L2_v1_zh.md`
2. `docs/tasks/active/task_lg_rag_sse_subtask_message.md`（00 定夺表 / 验收 / failure_paths 全遵照）
3. `docs/spec/agent-infra/05_lg_rag_transport_and_session_plan_v0.md` §10.7
4. `app/ops/lg_rag/progress_stream.py` · `app/ops/lg_rag/sse_stream.py`（done 映射）· `app/ops/lg_rag/lc_evidence_chain/step_hook.py`
5. 前置实现参照：`docs/tasks/done/task_lg_rag_sse_subtask_steps.md`

## 实现要点（task 00 定夺为准）

- `payload.message`：可选 string；**确定性模板**（代码内映射表）；**禁止**调 LLM 生成；**禁止**塞 CoT/raw prompt/evidence 全文；≤200 字截断；**禁止**空串冒充
- running / step / done 三态尽量带；未知 step/缺 detail 用兜底短句（含 step 名）；message 生成异常打日志不中断帧
- 集中生成：`progress_stream.py`（或同目录小模块），`emit_subtask_running` / `emit_subtask_step` / done 映射处挂载
- step 示例：`retrieve`+`phase:start`→「开始检索…」；`retrieve`+`phase:done`+`hit_count`→「检索完成，命中 N 条」；`grade`+`gate_action` 含动作语义；`rewrite`+`current_query`→「改写查询：…」（截断）

## 交付物

1. 上述实现 + 单测（mock emit：running/step/done 帧含非空 message；文案与 detail 数字/动作一致；截断上限断言；未知 step 兜底；旧测不回归）
2. 05 §10.7 增补 `message` 行（payload 表 + 联调项「过程区可见中文短句」+ 旧客户端忽略未知键兼容说明）
3. `docs/_tech_graph/l1/01_modules.md` / `10_flow_lg_rag` 备注（不新增一级模块；新符号进 G-L2 indexes）
4. `docs/coding_wiki/volatile.md` 短注
5. invoke：`docs/harness/invokes/by-task/lg-rag-sse-subtask-message/invoke_20260908_30_lg-rag-sse-subtask-message.md`（含 GATE_VERIFY 表）与 `invoke_20260908_40_*.md`（40 自检：命令真跑 + 退出码 + 验收逐条对照回填 task「自检结论」节）

## 质量门（全真跑，逐条给退出码）

```bash
ruff check app tests
pytest tests            # 至少 lg_rag sse 相关全量
./scripts/graph-compile.sh
npx --yes dsh-coding-kit task lint-wiki-delta --target .
npx dsh-coding-kit verify --target . --task docs/tasks/active/task_lg_rag_sse_subtask_message.md
```

## 收口

git add 业务码 + 测试 + 文档（**勿**提交 `uv.lock` 本地噪音）→ commit（conventional，题头 `feat(lg-rag): ...`）→ push origin `task/lg-rag-sse-subtask-message`。**不开 PR**（00 收口开）。回报 ≤10 行：改动文件清单 / 测试结果 / 验收勾选情况 / 残余风险。
