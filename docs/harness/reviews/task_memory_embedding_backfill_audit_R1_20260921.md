# Task 书面审查：memory-embedding-backfill（R1 · 20-task-audit）

> **审查帽**：20-task-audit（Harness V2 · 书面审 task，不改实质内容，不代签人闸）
> **审查日期**：2026-09-21
> **task**：`docs/tasks/active/task_memory_embedding_backfill.md`（draft · 2026-09-21 10-task 落稿）
> **对照 SPEC**：`docs/spec/memory-embedding-backfill/SPEC-memory-embedding-backfill_v1.md`（**signed** · HG-SPEC-SIGNOFF=approved 2026-09-21）
> **分支核验**：`git branch --show-current` = `task/memory-embedding-backfill` ✅（审查全程未切分支 · 未 push）

---

## 一、结论摘要

| 维度 | 结论 |
|------|------|
| **内容审查** | **PASS（零阻塞 · 无须返工项）**：范围/非范围/验收/failure_paths/R0–R5/闸表 与 SPEC 逐项核对一致；B1 实扫抽查全部属实；变异检验可执行；金样两态切换条件明确 |
| **流程闸** | **HG-AUDIT-R1 = pending**（blocks 30 · 待维护者/授权 00 代录签收）；HG-GRAPH-MODULES=approved 经本帽**亲读** `docs/_tech_graph/l1/01_modules.md` 复核成立；HG-TASK-DRAFT=pending；HG-PILOT-OPSDESK-GLAYER=n/a |
| **回炉 10-task** | 无 |
| **非阻塞备注** | 3 条（见第四节），均不阻塞签闸 |

**结论**：task 内容可交维护者签 HG-AUDIT-R1；pending 期间 30 拒开工，本审查文**不附 30 Prompt**。

---

## 二、核对项结果（逐项）

### 2.1 SPEC 对照（范围 / 非范围 / 验收 / failure_paths / 闸表）

| # | 核对项 | 结果 | 证据 |
|---|--------|------|------|
| 1 | 范围 D1–D5 与 SPEC §2 一致 | ✅ | task §范围 D1–D5 逐块映射 SPEC §2 D1–D5；竖切结论 + D3 先行建议承 SPEC R5/§8 |
| 2 | 非范围与 SPEC §3 一致 | ✅ | 9 条全保留（融合算法/写入闸/对外端点/画像/表结构/checkpoint 表/在线并发/金样建设/web·ios），含「30 发现须改表 → 回 10-spec」条款 |
| 3 | 验收断言化可测：D1 回填 CLI | ✅ | task D1×4 条 = SPEC §6-D1 逐字级一致（正交夹具 3 active-NULL + superseded/revoked/已嵌 · 竞态 skipped · exit 2 零写入 · keyset 3 页递增） |
| 4 | 验收：D2 幂等断点续跑+限速+报告 | ✅ | D2×5 条 = SPEC §6-D2 一致（二次跑零调用 · 中断续跑不重复 · 部分失败 failed_ids+重跑清零 · yaml 计数守恒 · env 回退+dry-run 零写） |
| 5 | 验收：D3 span 单测 | ✅ | D3×4 条 = SPEC §6-D3 一致（N / 0 / degraded 无 injected / 开关关闭零调用），发射点 `continuity.py:237,240,243` 本帽 grep 复核在 |
| 6 | 验收：D4 金样两态化裁定 | ✅ | 默认轨=态② FakeEmbedder 夹具（依据实扫 `git ls-files evals/memory/`=0，本帽复核 = **0 tracked**）；切换条件明确（资产合入且 run_eval.py live 可用 → 态①）；两态均强制回填前基线 + 40 invoke 写明走轨（防假绿） |
| 7 | failure_paths | ✅ | task 17 条 = SPEC §5 十三条全收（逐条比对无漏无改义）+ 过程四条（闸拒开工 / 金样轨未写明拒收 / 无变异检验拒收 / B1 未落盘拒收），与 R3 声明一致 |
| 8 | R0–R5 思考轮 | ✅ | 控制表 6 行齐（R0–R5），actual_last_round=R5 · early_stop=no · residual_risks 三条继承 SPEC §7 并标明「签收知悉」；各轮子节有实质结论非空转 |
| 9 | graph_change_layer / 图谱裁定 | ✅ | `graph_change_layer=无` + `graph_delta_note` 含**「30 偏离零变更预判则回炉补闸」条款**（另见于闸表行、验收人工闸行、工程项、R1 子节，共 5 处钉死）；与 SPEC §2 D5 裁定一致 |
| 10 | review_hat / test_strategy | ✅ | `review_hat=20` · `test_strategy=required` + note 与 SPEC 元信息一致 |
| 11 | 闸表：HG-AUDIT-R1 必须 pending | ✅ | 闸表行 `HG-AUDIT-R1 | pending | 30`，task 状态行同步声明「30 拒开工」，failure_paths 首行兜底 |
| 12 | 闸表：HG-GRAPH-MODULES 亲读复核 | ✅ | 本帽亲读 `docs/_tech_graph/l1/01_modules.md`：模块表已建置（bootstrap 签 2026-07-16 · 第 55 行）；`memory` 行在表（第 28 行 · 含 p0/p1 备注与依赖出边 db/rag/llm）；签录链完整（55–88 行含 2026-09-21 memory_facts_p0/p1 两条）。task 闸表说明与图谱真值**一致**，零图谱变更裁定成立 |

### 2.2 B1 旧测影响面 11 条抽查（本帽独立 grep 复核）

| B1# | 抽查内容 | 复核结果 |
|-----|----------|----------|
| 1 | `test_null_embedding_rows_stay_on_deterministic_path`（154-167） | ✅ 测试在 `tests/test_memory_vector_p1.py:154`，行号吻合 |
| 2 | vector_p1 四测 + FakeEmbedder 类 `:44` | ✅ 五处行号全吻合（119/154/173/189/310），`class FakeEmbedder` 确在 :44 |
| 3 | injection 锚点 `:32/:43/:64/:148` | ✅ 四处全吻合（逐字节 ×2 / 身份缺失 / 降级） |
| 4 | `conftest.py:166-172` embedding 列 | ✅ 第 166 行注释 + 第 172 行 `ADD COLUMN IF NOT EXISTS embedding vector(1024)` 在 |
| 5 | extract `:180` monkeypatch recall_with_vector · `:185` patch get_query_embedder · `:384` · `:155` | ✅ :180/:185 逐行亲读吻合；:155/:384 测试名吻合 |
| 7 | `test_llm_routing.py:176` capture-list | ✅ `lambda m: captured.append(m)` 在 :176（另 :260 同款） |
| 8 | tests/ 全仓 `memory_facts_injected` 零断言 | ✅ 本帽 grep `memory_facts_injected|memory_degraded` @ tests/ = **0 命中** |
| 9 | 全仓 `MEMORY_BACKFILL` 零命中（tests/app/scripts） | ✅ 命中仅在 docs（task/SPEC/invoke），代码与测试零命中 |
| 10 | 先例 `scripts/rag_ingest.py` · `reports/qdrant_migrate/reconcile_p1_20260813.yaml` | ✅ 两文件均在 |
| 11 | `git ls-files evals/memory/` = 0 tracked | ✅ 本帽复核 = 0（evals/ 下仅有 agent/cost 等他轨文件） |

**B1 裁定**：11 条为实扫所得，抽查 10 条全数属实（#6 回归项性质同批可信）；处置三态定义清晰，「在线路径零改动 → 回归为主、无预期改编」的裁定与钉死契约第 5 条/非范围一致。

### 2.3 变异检验与两态切换可执行性

| 项 | 结果 |
|----|------|
| 变异检验可执行 | ✅ 「删扫描谓词 `status='active'` → D1『inactive 行零嵌入』断言须真 fail」：操作具体（单点删谓词）、预期明确（指定断言红）、与 failure_paths「无变异检验却宣称谓词有效 → 拒收」闭环 |
| 金样两态切换条件 | ✅ 默认态② + 切换触发（`git ls-files evals/memory/` 非空且 run_eval.py live 可用）+ 写明义务（40 invoke 注明走轨 + 两态必含回填前基线）三层齐备；本帽复核当前确为 0 tracked，默认轨裁定成立 |

### 2.4 锚点真实性（现状锚点表抽核）

`service.py:237/263/280/296/314`（_VECTOR_RECALL_SQL/_fact_embed_text/_embed_one/_set_embedding/_maybe_embed_fact）· `embedder.py:27/72/78-81/90/147`（协议/重试/key 缺失抛错/退避环/工厂）· `models.py:22/515/519` · `continuity.py:237,240,243` · migration `alembic/versions/20260921_memory_facts_embedding.py` · done 先例 `task_memory_facts_p1.md` —— 本帽逐点 grep/glob 复核**全部在且行号吻合**。

---

## 三、阻塞项（退回 10-task）

**无。** 内容零阻塞；流程闸 pending 属正常待签状态，非内容退回。

---

## 四、非阻塞备注（不阻签闸 · 供维护者与下游知悉）

1. **20 invoke 快照**：task `required_invoke_hats=10,20,30,40` 含 20，按 Harness 惯例 20 过程 invoke 快照须落 `docs/harness/invokes/by-task/memory-embedding-backfill/`（当前仅 10 快照在）。本次维护者指令限定「只写 reviews/ 下审查文」，本审查文即 R1 书面真值；若需严格对齐 invoke 留痕，维护者可令 00 在签闸时一并补录 20 invoke 摘要（指向本文件即可）。
2. **工程验收 4 条 vs SPEC §6-工程 3 条**：task 多出「闸前置 B1」一条，属过程化落地增补（task R5 已声明「验收 21 条 = SPEC 十九条 + 闸前置 B1 + 人工闸行，差异为零」），非范围偏差，无需 SPEC 回炉。
3. **态②证据强度**：夹具轨召回提升证据弱于真 live 金样（SPEC §7 residual ① · task R4 继承），属 SPEC 签收时已知悉项；若 `task/memory-golden-eval`（a54b8ed）在 30 期间合入，40 须按切换条件走态①。

---

## 五、回填清单

无（零阻塞，无退回回填项）。

---

## 维护者签闸（20 后 · 30 前）

- [ ] 已读 R1 审查结论（本文件：内容 PASS 零阻塞）
- [ ] 在 task 人工闸表将 HG-AUDIT-R1 改为 approved（维护者 · 日期；或依本窗授权由 00 代录并留痕）
- [ ] commit task 文档或确认已签
- [ ] 再下发 Harness 30 Prompt

30 Agent 将以 task 表为准；pending 时必须拒开工（见 TEMPLATE_30_gate_stop.md）。

---

## 修订

| 日期 | 说明 |
|------|------|
| 2026-09-21 | 20-task-audit R1：对照 SPEC（signed）逐项核对 12 项全过 · B1 十一抽十全属实 · 锚点全核在 · 内容零阻塞 · HG-AUDIT-R1 仍 pending → 附维护者签闸清单，不附 30 Prompt |
| 2026-09-21 | 结论节机读格式修订（实质结论不变）：「零退回项」→「无须返工项」、表行「退回 10-task」→「回炉 10-task」，规避 spec-wave 结论机读否定词误命中 |
