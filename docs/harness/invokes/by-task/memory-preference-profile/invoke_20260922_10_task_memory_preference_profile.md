# invoke · 10 · memory-preference-profile · task 落稿

| 项 | 内容 |
|----|------|
| **时间** | 2026-09-22 |
| **帽** | 10-task（SPEC signed 后落稿 · 本棒由 00 委派 10-task 帽 Agent 执行） |
| **文件** | `docs/tasks/active/task_memory_preference_profile.md` |
| **上游** | `docs/spec/memory-preference-profile/SPEC-memory-preference-profile_v1.md`（signed · HG-SPEC-SIGNOFF=approved 2026-09-22 · 4a2f4d9） |
| **格式基准** | `docs/tasks/done/task_prompt_asset_roadmap_p1.md`（真读对齐字段 · PR #155 已合） |

## 结论

**PASS（落稿）** · 范围 D1 闸放开 kind=preference（`ALLOWED_KINDS` 集合 + 双向 key 域绑定 `key_kind_mismatch` + 显式-only 通路约束）/ D2 来源分级与注入区分（显式 1.0 权重断言 · `[已知事实]`/`[用户偏好]` 分节单 SystemMessage · 无偏好节物理不存在 · fact 节逐字节对拍 · span `memory_preferences_injected`）/ D3 supersede 谓词加 kind 双保险 + `revoke_by_key`（幂等 · 审计 · 清除后零召回）/ D4 幻觉偏好红线（结构断言 + evals 金样 + 写入→污染→撤销→消失三态变异检验）/ D5 alembic CHECK 放宽（可逆往返 · 回滚注释先清 preference 行 · 零新列零新索引）+ README 同步；非范围沿用 SPEC `3（推断型偏好物理拒收等 10 条）；验收 **27 条**全否定性断言化逐块映射 SPEC `6（人工闸 1 / D1×5 / D2×6 / D3×3 / D4×3 / D5×3 / 变异检验×3 / 工程×3）· 与 SPEC 实质差异**零**；failure_paths **15 条**（SPEC `5 十一条翻四列 + 过程四）；R0–R5 全轮无 early_stop。

## 实扫留痕（本帽真跑）

- `git branch --show-current` = `task/memory-preference-profile` ✓（SPEC 签收 4a2f4d9 后）
- 闸：`gate.py:27` `ALLOWED_KIND = "fact"` · :103-104 kind≠fact → `kind_not_allowed` · `REJECT_REASONS` 7 码 :39-49 · `FactCandidate.kind` 默认 fact :89（与 SPEC `1 一致）
- CHECK：`models.py:470` `CheckConstraint("kind = 'fact'", name="ck_ops_memory_facts_kind")` · kind 列 :501 已存在 · alembic `20260921_memory_facts.py:37,48` 同 CHECK 落库 → **有 alembic 义务**复核成立
- 迁移链：`alembic heads` 真跑 = `20260921_llm_usage`（链序 memory_facts → memory_facts_embedding → llm_usage · 新迁移挂 head 后）
- 抽取管道：`extract.py` schema `ExtractedFactItem` 仅 key/value 无 kind（:47-51）· `MemoryFactExtraction` :54-57 · 构造点 :129-131 默认 kind=fact（显式-only 落点复核成立）
- service：`_write_in_session` 谓词 :53-58 不含 kind · `revoke_by_source` :128-157 幂等审计 :154-156 · 权重 `SOURCE_WEIGHT_EXPLICIT=1.0` :233 > `SOURCE_WEIGHT_EXTRACTED=0.8` :234 · `_source_weight` :340-342 · recall/SQL 无 kind 谓词
- 注入：`continuity.py` `MEMORY_FACTS_HEADER = "[已知事实]"` :98 · 渲染 :149-166 单循环 · 注入 :169-184 独立 SystemMessage · span `memory_facts_injected` :240/:243 · 开关默认 false :105-115
- README：`app/ops/memory/README.md:21` 域约定已列 `pref` · :144 非范围「画像 / preference」
- evals：`evals/memory/` 仅 `__init__.py` + `run_eval.py`（无金样 yaml → 新增义务）；先例 `evals/agent/redlines/capability_v1.yaml`
- pytest 基线真跑：`python -m pytest tests --collect-only -q` = **1210 collected**；memory 面用例计数（gate 12 / injection 15 / service_db 7 / extract_p1 12 / vector_p1 8 / time_decay_tz 6 / embedding_backfill 15 / continuity 2+15）
- B1 落盘 **13 行**（回归×7 · 改编×3 · 新增×2 · 迁移×1 · 删除×0）；tests 全仓 kind 直引断言仅 **3 处**（gate :37-40 · gate :103-106 enumerable · service_db :93-96）——preference 语义反转改编面钉死
- HG-GRAPH-MODULES 真值核验：**真读** `docs/_tech_graph/l1/01_modules.md` —— 模块表已建置 · memory 行 :28 在表（出边 db/rag/llm/prompts）· continuity 在 lg_rag 行覆盖 · models/alembic 在 db 行覆盖 → 零图谱变更 approved；memory 行**备注级更新预期** + **偏离回炉补闸条款**钉死
- SPEC `1 锚点复核**零措辞偏差**（对照 prompt-asset-roadmap-p1 留痕两处先例 · 本 SPEC 无）

## 闸态

- `HG-TASK-DRAFT` = **pending**（00 验收代录/人签 · 本帽不签）
- `HG-AUDIT-R1` = **pending**（blocks 30 · 20 审后人签/授权代录）→ **30 拒开工**
- `HG-GRAPH-MODULES` = approved（真读模块表 · 零图谱变更 + memory 行备注级更新预期 + 回炉补闸条款）
- `HG-PILOT-OPSDESK-GLAYER` = n/a

## 下一棒

20-task-audit 书面审（对照 SPEC）→ HG-TASK-DRAFT + HG-AUDIT-R1 人签 → 30（`task/memory-preference-profile` · 承 SPEC `8 序：D1 闸 → D5 迁移 → D3 service → D2 渲染 → D4 评测 · fact 语义零变化）。后续 20/30/40 invoke 由各棒落盘本目录（命名对齐 `invoke_<yyyymmdd>_<hat>_<verb>_memory_preference_profile.md`）。
