# query-coref-rewrite 审查（R2 · 20-task-audit 存量回填补轮）

> **审查对象**：`docs/tasks/done/task_query_coref_rewrite.md`（已归档 done/）
> **审查帽**：20-task-audit（R2 · 存量回填补轮 · 依 `docs/tasks/active/task_api_legacy_reviews_backfill.md` v0.4 缺口④）
> **日期**：2026-10-30
> **补轮背景**：原 R1 已落盘且内容面裁定 pass，但其结论摘要节含机读契约否定字面，仓级扫描判「结论不可机读」；按「不通过 → 补轮 R+1」纪律补本 R2。R2 落盘即唯一被评估轮（review-gates 最高轮语义），原 R1 留档不参与判定。
> **核对材料**：done task 原文 · 原 R1 `docs/harness/reviews/task_query_coref_rewrite_audit_R1_20261019.md` · 30 实现实录 invoke（commit cb80f8f）· CLOSE invoke `docs/harness/invokes/by-task/query-coref-rewrite/invoke_20261019_close.md` · 交付 commit 链（feat 4b36b3b · PR #284 merge fc5d9bd · 归档 0c4a1ed · 均实证在 master）· 现行代码抽查（本帽 2026-10-30 亲验）
> **纪律声明**：事后补审不改 task 与交付实质内容；结论据实。

## 前审沿革（R1 → 交付 → 归档）

原 R1（2026-10-19）内容面裁定 pass：阻塞 0 · SPEC 锚点 26 处零漂移 · O1/O2 两条非阻塞观察。但其「结论摘要」节含「不构成退回理由」表述，命中仓级机读契约的退回否定守卫（守卫不认语境）→ 判不可机读（本 R2 补轮动因）。后续沿革：HG-AUDIT-R1 维护者签收（授权 00 代签转录）→ 30 红测先行（38 例先红后绿 · TC1–TC12 全过 · feat commit 4b36b3b）→ 40 approve（889 行 diff 逐行 + 复跑全绿）→ PR #284 merge（fc5d9bd · CI 全绿）→ CLOSE（0c4a1ed · task 归档 done/ · close invoke 录挂账移交：40 O1–O4 与 30 residual 4 条均照登移交下游）。

## 一、范围/验收与交付一致性

| 核对点 | 实证 | 裁定 |
|---|---|---|
| 范围：装配层历史感知 query 重写（D1 插入点 / D2 开关降级 / D3 消耗面审计 / D4 rewrite 档键三处） | 现行 `app/ops/lg_rag/query_rewrite.py` 模块存续（:54-66 开关解析含非法值 warning 回退关 · 亲验）；`app/ops/lg_rag/continuity.py` 装配面存续；prompt 资产 `app/ops/prompts/assets/lg_rag.query_rewrite.system.md` 在册 | ✅ 一致 |
| 非范围：`LG_RAG_QUERY_REWRITE_ENABLED` 默认关零 diff | 现行 query_rewrite.py:59 `os.getenv(...)` 默认关口径（亲验） | ✅ 一致 |
| TC1–TC12 全机断验收（默认关零 diff / 金样三类 / 失败降级 / 首轮短路 / 落盘原文 / env 非法值 / 档键在册 / 顺序钉死 / 非法输出三形态 / 图谱守护 / 反回归全量 / 旧测影响面） | 30 实录 invoke（cb80f8f）录 38 例先红后绿全过；`tests/test_lg_rag_query_rewrite.py` 现存于仓（亲验）；PR #284 CI 全绿 | ✅ 一致 |

## 二、failure_paths 核对

- **FP-1 开关默认关零 diff / FP-2 首轮无历史短路 / FP-3 重写 LLM 异常降级原文 + span `query_rewrite_fallback=true`** → TC1/TC4/TC3 对应钉测全过（30 实录）：落实 ✓
- **FP-4 金样指代改写 → planner/aggregator 收改写后文本** → TC2 钉测落实 ✓
- **FP-5 env 非法值 warning + 行为同关** → 现行 query_rewrite.py:66 warning 回退关实现存续（亲验）· TC6 钉测：落实 ✓
- **FP-6 落盘与 run.start 双写均记原文** → TC5 钉测落实 ✓
- **FP-7 mode=basic/router 默认关零行为差 / FP-8~FP-10（档键 unknown_task / 顺序 / 非法输出三形态 · R1 N1–N3 吸收）/ FP-11 闸纪律** → TC7/TC8/TC9 与 30 实录对应落实 ✓

## 三、结论/签收

本帽裁定：本 task 审查 **PASS**。原 R1 内容面裁定（阻塞 0 · 锚点零漂移）经本轮复核维持有效；验收 TC1–TC12 与交付逐条一致（38 例先红后绿实录 · PR #284 CI 全绿），范围与非范围零漂移，failure_paths FP-1~FP-11 全部落实；交付 commit 4b36b3b / fc5d9bd 已在 master 实证，现行代码抽查（query_rewrite.py 开关与降级路径 · 测试档存续）与 task 声明一致。核对全程未发现历史交付的实质问题，零内容阻塞项遗留；close invoke 挂账移交项（40 O1–O4 · 30 residual 4 条）属下游棒范畴，照登不改。本轮结论节按机读契约干净书写，前审沿革已独立成节另述；既有闸态照登不重签。

## 修订

| 日期 | 说明 |
|------|------|
| 2026-10-30 | 20 R2 存量回填补轮落盘（task_api_legacy_reviews_backfill v0.4 缺口④）：R1 内容面裁定复核维持 + TC1–TC12 与交付一致性逐条核对 + 现行代码抽查，裁定 PASS，零实质问题；前审沿革独立成节 |
