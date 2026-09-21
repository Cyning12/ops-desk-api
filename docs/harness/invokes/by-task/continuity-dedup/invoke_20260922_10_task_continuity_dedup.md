# invoke · 10 · continuity-dedup · task 落稿

| 项 | 内容 |
|----|------|
| **时间** | 2026-09-22 |
| **帽** | 10-task（维护者授权「授权00签收所有过程文档」承前令 · SPEC signed 后落稿） |
| **文件** | `docs/tasks/active/task_continuity_dedup.md` |
| **上游** | `docs/spec/continuity-dedup/SPEC-continuity-dedup_v1.md`（signed · HG-SPEC-SIGNOFF=approved 2026-09-21 · d0152e4/8fdd859） |
| **格式基准** | `docs/tasks/done/task_memory_embedding_backfill.md`（真读对齐字段 · PR #151 已合） |

## 结论

**PASS（落稿）** · 范围 D1 单真源硬删除 / D2 测试收敛（删 2 留 2 · 对账 lg_rag 覆盖）/ D3 图谱零变更按实判同竖切（一次提交 · 纯删除无先行切分空间）；非范围沿用 SPEC §3 九条；验收 **17 条**全否定性断言化逐块映射 SPEC §6（人工闸 1 / D1×4 / D2×3 / 行为零变化×2 / 变异检验×3 / 工程×3）· 与 SPEC 实质差异**零**；failure_paths **12 条**（SPEC §5 九条翻四列 + 闸/变异/B1 三）；R0–R5 全轮无 early_stop。

## 实扫留痕（本帽真跑）

- `git branch --show-current` = `task/continuity-dedup` ✓
- B1 口径真跑：`grep -oE 'compress_window|continuity|ops\.session' tests/test_session_continuity.py tests/test_lg_rag_session_continuity.py` = **17 处命中**（8+9 · 两测试文件）· 逐条处置落盘（回归×8 真源守护 + 删除×6 session 收敛 + 辅扫×3 · 改编×0）
- pytest 基线真跑：`python -m pytest tests --collect-only -q` = **1178 collected** → 删除后应 1176（**用例数差值 == 2** 验收锚）
- 锚点实读复核：`app/ops/session/__init__.py`（`:3` import + `:8` `__all__` 与 SPEC 一致）· `tests/test_session_continuity.py` 全文件（4 用例 = 2 删 + 2 留）· `tests/test_lg_rag_session_continuity.py` 全文件（方向闸 `:22-37` · 守护三用例 `:65-85`）
- **SPEC 措辞偏差留痕**：SPEC 表述「sse_replay 四用例（:30-45）」与实测 2 个 test 函数（`:30-37` · `:40-45`）不符 → 范围语义零影响（删 2 留 2 · 差值==2 不变）· task 按实测如实写 · 不改 SPEC（修措辞走 10-spec 修订轨）
- HG-GRAPH-MODULES 真值核验：**真读** `docs/_tech_graph/l1/01_modules.md` —— 模块表已建置 · chat 行 `app/ops/chat/**` · `app/ops/session/**` 在表 · 出边 `llm, db, rag`（**无 lg_rag** → S2 re-export 必污染拓扑）→ approved；SPEC §2 D3 零图谱变更裁定采纳 + **回炉补闸条款**（30 改走 re-export/新增依赖边 → 退 10-spec + 补闸 · 不得沿用本裁定）
- 图谱登记复核：`docs/_tech_graph/` grep `continuity` 仅 lg_rag 侧登记（l1 `10_flow_lg_rag.graph.yaml` + l2 indexes）· `session/continuity.py` 零登记（承 SPEC 2026-09-21 实扫 · 本帽复核一致）

## 闸态

- `HG-TASK-DRAFT` = **pending**（00 验收代录 · 本帽不签）
- `HG-AUDIT-R1` = **pending**（blocks 30 · 20 审后 00 依维护者授权代录）→ **30 拒开工**
- `HG-GRAPH-MODULES` = approved（真读模块表 · 零图谱变更 + 回炉补闸条款）
- `HG-PILOT-OPSDESK-GLAYER` = n/a

## 下一棒

20-task-audit 书面审（对照 SPEC）→ 00 代录 HG-TASK-DRAFT + HG-AUDIT-R1 → 30（`task/continuity-dedup` · D1–D3 一次提交 · 真源零触碰）。后续 20/30/40 invoke 由各棒落盘本目录（命名对齐 `invoke_<yyyymmdd>_<hat>_<verb>_continuity_dedup.md`）。
