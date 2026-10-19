---
hat: 40-empirical
task_slug: rag_golden_eval_live_run
date: 2026-10-19
---

# invoke · 40 实证 · rag_golden_eval_live_run（R-4 结案真跑：现集 73 条全量真跑 + 结案报告 + R-5 Demo 证据表）

## GATE_VERIFY（开工首输出 · 真值=task 人工闸表）

| 闸 | 状态 | blocks | 结论 |
|---|---|---|---|
| HG-TASK-DRAFT | approved | 20,40 | 放行 |
| HG-AUDIT-R1 | approved | 40 | 放行 |
| HG-EVAL-LIVE-RUN | approved | 40 | 放行（核心闸 · 授权本地库+真 key+配额消耗） |
| HG-GRAPH-MODULES | approved | 30 | 放行（graph_change_layer=none · 零落码无 30 棒） |
| 关联 HG-PROD-READONLY-ACCESS | pending | 生产侧 | 本 task 零涉生产，不受阻不消解 |

四闸全 approved → 开工。`npx spec-wave verify --target . --task docs/tasks/active/task_rag_golden_eval_live_run.md` → **VERIFY: PASS**。
真读在案：task 全文 + R1 审查文（docs/harness/reviews/task_rag_golden_eval_live_run_audit_R1_20261019.md）+ 10/20 invoke。

## F1 · TC-LR-1 前置核验（2026-10-19 亲跑）

| 项 | 命令 | 实测 |
|---|---|---|
| 双容器 | `docker ps` | ops-desk-api-db-1 / ops-desk-api-qdrant-1 均 **Up 2 days (healthy)** |
| LLM key | `grep -c '^SILICONFLOW_API_KEY=.' .env` | **1**（存在非空 · 值零落档） |
| PG 计数 | `docker exec ops-desk-api-db-1 psql -U ops -d opsdesk -t -c 'select count(*) from ops_knowledge_chunks'` | **8648** |
| Qdrant 计数 | `curl -s :6333/collections/ops_knowledge` | **points_count=8648** · status=green · dim=1024 · Cosine |
| 现集计数 | `grep -o 'quadrant: [a-z0-9]*' evals/golden/queries_v1.yaml \| sort \| uniq -c` | **zh2en=26 / zh2zh=20 / en2en=16 / negative=11 = 73** |
| 报告头开关 | .env 现态 | RAG_RERANK_ENABLED=true · backend=siliconflow · min_score=0.4 · score_ratio=0.75 · GRADER_PROVIDER=siliconflow · GRADER_MODEL=Qwen/Qwen3.6-27B · LC_ANSWER_PROVIDER=siliconflow · VECTOR_BACKEND=qdrant · KW_EXPAND=false |

## F1 · TC-LR-2 真跑实录（含 FP-3 两连处置 · FP-2 不假绿）

1. **冒烟先行**：`env -u NO_PROXY -u no_proxy PYTHONPATH=$PWD <主仓>.venv/bin/python evals/golden/run_eval.py --limit 3 --out /tmp/r4_live_smoke.yaml` → **pass=2/3 · stability=1.0**（产物 /tmp 不入仓 · 附件 evidence_r4_live_smoke_20261019.yaml 为留档副本）。
   - 插曲①（FP-3 先例复现）：首轮未洗代理即 `httpx.InvalidURL: Invalid port: ':1]'`（shell NO_PROXY 含 [::1] · 承 close_local_rag_knowledge_rebuild §三.1）；② 单洗 `env -u NO_PROXY` 仍炸——实测 shell **NO_PROXY/no_proxy 双写**（大小写两份均含 [::1]），改 `env -u NO_PROXY -u no_proxy` 后冒烟通过。**增量教训：双写面需双洗**。
2. **全量真跑**：`env -u NO_PROXY -u no_proxy PYTHONPATH=$PWD <主仓>.venv/bin/python evals/golden/run_eval.py --out reports/r4_live_20261019T032150Z.yaml`（命令全文见证据附件 :1）。
   - 插曲②（FP-3 中途失败 · FP-2 如实记）：7/73 后 LLM 连接中断 `app.llm.schema.LlmProviderError: LLM request failed: peer closed connection without sending complete message body (incomplete chunked read)` → EXIT=1（6m14s · 证据附件 :148）。报告逐条落盘保 7 条，**未凑数未冒充全量**。
   - 处置：判本地代理（127.0.0.1:7890）长连接不稳 → **全洗代理变量走直连**（env -u NO_PROXY -u no_proxy -u http_proxy -u https_proxy -u all_proxy -u HTTP_PROXY -u HTTPS_PROXY -u ALL_PROXY）+ `--resume` 断点续跑（承分批续跑先例 · 命令全文附件 :152）。
3. **续跑完成**：73/73 全量 · partial=false · 50m22s（两段合计 ≈56.6 min）· 报告 `reports/r4_live_20261019T032150Z.yaml`。
   - SUMMARY（附件 :615）：**pass=54/73 · zh2en=19/26 · zh2zh=18/20 · en2en=15/16 · neg=10/11 · stability=1.0 · SPEC={observed, low, not_comparable}**。
   - 退出码照登：RESUME_EXIT=1 = run_eval.py:812 `return 1 if failed else 0`（verdict fail 19 条所致 · **非进程失败** · 报告 completed=73 partial=false 有效）。
4. **配额消耗台账（诚实照登）**：本地无计量面，实录口径 = embed BAAI/bge-m3 ×(73+冒烟3+中断重跑7) 查询向量 + CE rerank（BAAI/bge-reranker-v2-m3）×73 + grader Qwen/Qwen3.6-27B ×73 案评级（含 stability 抽查 ×3 复评）· 墙钟 ≈56.6 min · 中断重跑 7 条重复消耗照登。逐案调用数未本地计量（照登：无实证）。

## F2 · TC-LR-3 结案报告

- `PYTHONPATH=$PWD <主仓>.venv/bin/python evals/golden/summarize_r4.py --report reports/r4_live_20261019T032150Z.yaml --out-yaml reports/r4_final_live_20261019T032150Z.yaml --out-md reports/r4_final_live_20261019T032150Z.md` → EXIT=0 · `SUMMARY zh2en=19/26 gate=MET refuse=10/11`。
- 七节核对（模板工作流：summarize 初稿 → 40 补齐 §1 commit/§5/§6 结论/§7 判定建议+签字位留维护者）：
  - §1 运行标识 ✓（run id · commit 4a5e755 · 语料 N=8648 显式 · arm=rerank 参数全录）· §2 逐象限 ✓ · §3 门槛判定 ✓ **zh2en 19/26（73.08%）vs ≥1/3 → MET**（n=26 · Wilson 95% CI=[0.54, 0.86] · confidence=low）· 拒答 10/11（90.91% · CI=[0.62, 0.98]）· 误答 G63 · 疑似误拒 G03/G05/G37/G44/G47/G49/G56/G57/G61（9 条）· §4 未达成项 19 条全列 ✓ · §5 观测口径注记（FP-8 照登）✓ · §6 契约漂移=**零漂移**（§4c 拒答话术三面逐字一致实证）✓ · §7 结论与签字：整体判定建议**有条件通过**（门槛 MET · 19 条 verdict fail 待归因复核）· 签字位留维护者 ✓。
- 机断旁证：`pytest tests/test_golden_eval_r4_summary.py -q` → **12 passed** · `pytest tests/test_golden_eval_runner.py -q` → **13 passed**（零新增红 · 管线零 diff 活证）。

## F3 · TC-LR-4 Demo 证据表

- `reports/demo_evidence_20261019T033800Z.md`：4 条（zh2en G01 answer/exact · zh2zh G21 answer/exact · en2en G41 answer_partial/relevant · **negative G62 拒答演示**）。
- 拒答文案逐字核对：契约 §4c（:183）= `app/ops/rag/grader.py:30` REFUSAL_TEXT = grader.py:63 refuse 返回 = 「未查询到相关内容，无法针对此问题进行回答」三面一致。
- 引用标题实证：chunks content `[Document Context] Title:` 前缀 PG 查询提取（命令全文见证据附件区）。
- 照登（模板 nit 上抛）：demo_evidence_TEMPLATE.md 示例复现命令 `--only/--report` 参数现版 run_eval.py 不支持（--help 实证）；模板零 diff 约束下未改模板，证据表内已照登并给可执行口径。

## TC-LR-5 零 diff 硬约束

- `git diff --stat HEAD -- app/ scripts/ alembic/ docker-compose.yml evals/golden/{run_eval.py,summarize_r4.py,queries_v1.yaml,hygiene_denylist.yaml} reports/r4_final_TEMPLATE.md evals/golden/demo_evidence_TEMPLATE.md` → **空输出（零 diff）**；`git status --short` 同面零改动。
- 契约 `ops-desk-workspace/docs/contracts/rag-knowledge-contract-v1.md` 零 diff（workspace 仓 git status 干净 · 最新 commit 7560560 为历史变更非本 task）。
- FP-6：全程零落码冲动触发（唯一环境面处置 = shell 变量清洗 + --resume · 无仓码改动）。

## F4 · 留档

- 证据附件（本目录）：`evidence_r4_live_run_log_20261019T032150Z.txt`（617 行全量真跑原始输出 · 命令全文/中断/续跑/SUMMARY 全链）· `evidence_r4_live_smoke_20261019.yaml`（冒烟报告副本）。
- 产物索引：`reports/r4_live_20261019T032150Z.yaml`（源报告 73/73）· `reports/r4_final_live_20261019T032150Z.{yaml,md}`（结案报告）· `reports/demo_evidence_20261019T033800Z.md`（Demo 证据表）。
- 任务档验收勾选 + 自检结论 + 修订记录已回填；`npx --yes spec-wave task lint` PASS（见任务档自检结论节）。

## 偏差与教训（照登）

1. **NO_PROXY 双写**：shell 同时存在 NO_PROXY 与 no_proxy（均含 [::1]），先例「env -u NO_PROXY」单洗不足，需双洗——建议后续棒次直接双洗或全洗。
2. **代理长连接不稳**：经 127.0.0.1:7890 代理的 LLM 流式响应 7/73 处中断（incomplete chunked read）；全洗代理直连后 66 条零中断跑完——本地真跑建议直连口径。
3. **模板 --only nit**：demo 模板复现命令参数与现版 runner 不符（上抛维护者裁定是否另 task 勘误 · 本 task 零 diff 不动模板）。
4. **判定面**：zh2en MET（73.08% vs ≥1/3）；误答 G63 + 疑似误拒 9 条 + 评级未达期望 9 条 = verdict fail 19 条待归因复核（另 task · 不改默认参数不改管线）。
