# invoke · 10 · memory-embedding-backfill · task 落稿

| 项 | 内容 |
|----|------|
| **时间** | 2026-09-21 |
| **帽** | 10-task（维护者授权「授权00签收所有过程文档」承前令 · SPEC signed 后落稿） |
| **文件** | `docs/tasks/active/task_memory_embedding_backfill.md` |
| **上游** | `docs/spec/memory-embedding-backfill/SPEC-memory-embedding-backfill_v1.md`（signed · HG-SPEC-SIGNOFF=approved 2026-09-21） |
| **格式基准** | `docs/tasks/done/task_llm_layer_hardening.md`（真读对齐字段 · PR #148 已合） |

## 结论

**PASS（落稿）** · 范围 D1 回填主体 / D2 幂等限速报告 / D3 span 单测 / D4 对账金样两态 / D5 文档同竖切（建议 D3 先行提交，D1/D2/D4 随后 · 承 SPEC R5/§8）；非范围沿用 SPEC §3 九条；验收 **21 条**全否定性断言化逐块映射 SPEC §6（D1×4 / D2×5 / D3×4 / D4×3 / 工程×4 + 人工闸行）· 与 SPEC 差异**零**；failure_paths **17 条**（SPEC §5 十三 + 闸/金样轨/变异/B1 四）；R0–R5 全轮无 early_stop。

## 实扫留痕（本帽真跑）

- `git branch --show-current` = `task/memory-embedding-backfill` ✓
- `git ls-files evals/memory/` = **0 tracked** → 金样两态裁定：**默认态② FakeEmbedder 集成夹具轨**；切换条件 = `evals/memory/` 金样资产合入本分支 → 态① live 金样轨；40 invoke 须写明实际走轨 + 回填前基线（防假绿）
- HG-GRAPH-MODULES 真值核验：`docs/_tech_graph/l1/01_modules.md` 模块表已建置（bootstrap 签 2026-07-16 · `memory` 行在表 · 签录链完整含当日四行）→ approved；SPEC §2 D5 零图谱变更裁定采纳 + **回炉补闸条款**（30 偏离零变更预判 → 退回 10-task 补闸）
- B1 旧测影响面 11 条实扫落盘（grep 口径见 task B1 节首）：tests/ 全仓 `memory_facts_injected` **零断言**（P0 遗留①确认）· `MEMORY_BACKFILL` 全仓零命中（新 env 无冲突）· 在线路径零改动 → 处置全为回归/新增，无预期改编
- 先例锚点在位：`scripts/rag_ingest.py` · `reports/qdrant_migrate/reconcile_p1_20260813.yaml` · `tests/test_memory_service_db.py` · `tests/conftest.py:166-172`（embedding 列保障）· `tests/test_llm_routing.py:176`（capture-list）

## 闸态

- `HG-TASK-DRAFT` = **pending**（00 验收代录 · 本帽不签）
- `HG-AUDIT-R1` = **pending**（blocks 30 · 20 审后 00 依维护者授权代录）→ **30 拒开工**
- `HG-GRAPH-MODULES` = approved（模块表已建置 · 零图谱变更 + 回炉补闸条款）
- `HG-PILOT-OPSDESK-GLAYER` = n/a

## 下一棒

20-task-audit 书面审（对照 SPEC）→ 00 代录 HG-TASK-DRAFT + HG-AUDIT-R1 → 30（`task/memory-embedding-backfill` · D3 先行）。后续 20/30/40 invoke 由各棒落盘本目录（命名对齐 `invoke_<yyyymmdd>_<hat>_<verb>_memory_embedding_backfill.md`）。
