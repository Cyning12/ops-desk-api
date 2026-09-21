# 20-task-audit 审查文：task_memory_preference_profile（R1）

> **审查帽**：20-task-audit（书面审 · 不改 task 实质内容）
> **审查对象**：`docs/tasks/active/task_memory_preference_profile.md`（draft · 2026-09-22 10-task 落稿）
> **对照 SPEC**：`docs/spec/memory-preference-profile/SPEC-memory-preference-profile_v1.md`（signed · HG-SPEC-SIGNOFF=approved 2026-09-22 · commit `4a2f4d9` 已实查：该 commit 即签收 commit，`git show --stat` 证实仅签收行变更，SPEC 自此无后续改动）
> **审查日期**：2026-09-22 · **分支**：`task/memory-preference-profile`（实查一致）
> **审查方式**：逐项机读对照 + 锚点亲跑亲读复核（命令真跑，非引述）

---

## 结论摘要

**内容审查：通过（PASS · R1 · 零内容阻塞）。**

task 与 SPEC 实质零差异：范围 D1–D5、非范围、failure_paths、验收 27 条、思考轮 R0–R5 全部承 SPEC 并过程化落地；钉死契约 14 项与 SPEC §2/§4 裁决（B1 单消息双节 · E1 通路约束+双向绑定）一致；B1 旧测影响面 13 行实扫落盘且抽查属实；现状锚点亲跑复核成立。

**流程闸：`HG-AUDIT-R1` = pending（blocks 30）。** 本审查文落盘即 R1 书面审完成；30 开工以维护者签 task 人工闸表 `approved` 为唯一真值。本帽不代签、不附 30 Prompt。

---

## 逐项核对（SPEC → task）

### 范围 D1–D5

| 块 | SPEC 约定 | task 落地 | 核对 |
|----|-----------|-----------|------|
| D1 闸放开 + key_kind_mismatch | `ALLOWED_KINDS = {"fact","preference"}` · 双向 key 域绑定 · 新原因码入 REJECT_REASONS · 抽取管道永远 fact | 钉死契约 3 行 + 范围 D1 + 验收 D1×5 | 一致 |
| D2 权重 + 双节注入 + span | 显式 1.0 断言 · B1 单 SystemMessage 双节 · 无偏好→节物理不存在 · fact 节逐字节 · span 双计数 · SQL 不加 kind 谓词 | 钉死契约 4 行 + 验收 D2×6 | 一致 |
| D3 supersede + revoke_by_key | 查重谓词加 kind 双保险 · revoke_by_key（tenant+user 谓词 · 幂等 · 审计 · 清除后零召回）· 物理删除不做 | 钉死契约 3 行 + 验收 D3×3 | 一致 |
| D4 幻觉红线三态变异 | 结构断言 + 离线金样（热路径零 LLM-as-judge）+ 三态全链路变异检验（缺第一态不算过）+ 锚点断言 | 范围 D4 + 验收 D4×3 + 变异检验①②③ | 一致 |
| D5 alembic CHECK 放宽可逆 | CHECK 改 `IN ('fact','preference')` · 回滚注释「先清 preference 行」· 无新列无新索引 · models.py 同步 · 可逆往返 | 钉死契约 alembic 行 + 验收 D5×3（含 upgrade→downgrade→upgrade 往返） | 一致 |

### 非范围

task 非范围 10 条 ⊇ SPEC §3 九条（推断型物理拒收 · 跨用户聚合 · 推荐 · 改 fact 语义 · 对外端点 · 热路径抽取/prompt 文案 · 权重调参 · 物理删除 · UI · TTL），并据工程面扩列「新增 env / SSE 事件 / 列 / 索引」「历史文档回改」——扩列方向与 SPEC 钉死契约同向，无范围回渗。

### failure_paths

SPEC §5 十一条全收并翻四列（含「用户可见」列），另补过程四行（闸未签拒开工 · B1 闸前置拒收 · 无变异检验拒收 · 回滚卡死先清 preference 行）共 15 条，与 task R3 自述一致；三静默错各有断言 + 变异检验兜底。

### 思考轮 R0–R5

R0–R5 全轮 done · early_stop=no · residual_risks 三条全承 SPEC §7（挤占预算 · 显式-only 维持方式 · 金样判定确定性）；R4 验收 27 条逐块映射 SPEC §6（人工闸 1 / D1×5 / D2×6 / D3×3 / D4×3 / D5×3 / 变异×3 / 工程×3）清点属实。

### 人工闸表

- `HG-AUDIT-R1` = **pending**（blocks 30）——符合 20 审前人签前状态，本审查文即其前置书面审。
- `HG-TASK-DRAFT` = pending · `HG-PILOT-OPSDESK-GLAYER` = n/a —— 如实。
- `HG-GRAPH-MODULES` = approved（10-task 称真读）——**本帽亲读复核**：`docs/_tech_graph/l1/01_modules.md` 模块表已建置；`memory` 行确在 **:28**（路径 glob `app/ops/memory/**` · 出边 `db, rag（embedder）, llm（抽取）, prompts（extract 模板加载）` · P0/P1/prompt-asset 三级备注留痕，逐字一致）；`lg_rag` 行覆盖 `app/ops/lg_rag/**`（continuity.py 在内）；`db` 行（:33）覆盖 `app/db/**`, `alembic/**`。零图谱变更裁定（不新增路由/表/事件类型/一级模块 · CHECK 放宽属 db 行 migrations 既有面）成立；回炉补闸条款（形态偏离即退 10-spec + 补闸 + 图谱登记）在闸表行与 graph_delta_note 双处钉死。

---

## 重点抽查（亲跑亲读）

### B1 旧测影响面 13 行 · 抽 5 条实核

| # | 抽查项 | 实核结果 |
|---|--------|----------|
| 1 | `tests/test_memory_gate.py:37-40` `test_kind_not_allowed` 用 `_candidate(kind="preference")` 断言拒 | **属实**（:37 def · :38 候选 · :40 `assert d.reason_code == "kind_not_allowed"`）——preference 放开后语义反转必挂，改编处置（换集合外值）正确 |
| 2 | `tests/test_memory_gate.py:103-106` enumerable 覆盖断言 | **属实**（:103 `def test_reject_reasons_enumerable_and_cover_all_rejections` · :106 候选含 `kind="preference"`）——增 `key_kind_mismatch` 后 7→8 码须同步改编，处置正确 |
| 3 | `tests/test_memory_service_db.py:93-96` `test_gate_rejection_writes_nothing` | **属实**（:93 def · :95 `write_fact(_candidate(kind="preference"))` · :96 断言 `kind_not_allowed`）——触发方式失效判断正确，改编处置（换 `key_kind_mismatch` 或集合外值）保持「闸拒不落库」语义 |
| 4 | kind 直引断言全仓 tests 仅 3 处 | **属实**：`grep -n 'kind' tests/test_memory_*.py` 命中恰为上述 3 处（gate×2 · service_db×1），injection/extract_p1/vector_p1 零命中——改编面钉死无遗漏 |
| 5 | 用例计数 9 文件（gate 12 / injection 15 / service_db 7 / extract_p1 12 / vector_p1 8 / time_decay_tz 6 / embedding_backfill 15 / session_continuity 2 / lg_rag_session_continuity 15） | **属实**：逐文件 `grep -c 'def test_'` 九项全中；「改编×3 · 删除×0」与抽查一致 |

### pytest 基线复跑

`python -m pytest tests --collect-only -q` 真跑 = **1210 tests collected**，与 task 基线一致。

### alembic head 实查

`alembic heads` 真跑 = `20260921_llm_usage (head)`；链序亲查 down_revision：`20260921_memory_facts` → `20260921_memory_facts_embedding` → `20260921_llm_usage`，与 task 一致；`20260921_memory_facts.py:48` `CONSTRAINT ck_ops_memory_facts_kind CHECK (kind = 'fact')` 落库属实（:37 kind 列 DEFAULT 'fact' 同属实），「有 alembic 义务」裁定成立。

### evals/memory 无金样复核

`evals/` 全树 `*.yaml` 清单亲查：`evals/memory/` 下**无金样 yaml**（红线金样为新增义务成立）；先例形态 `evals/agent/redlines/capability_v1.yaml` 在位属实。

### 代码锚点抽核（10 处全中）

`gate.py:27` ALLOWED_KIND · `:89` FactCandidate.kind 预留 · `:103-104` kind 判拒 · `:31-49` REJECT_REASONS 7 码；`models.py:470` CHECK · `:501` kind 列；`extract.py:47-57` schema 无 kind 字段 · `:105` render 资产化 · `:129-131` 构造点默认 fact；`service.py:53-58` 谓词不含 kind · `:128-157` revoke_by_source 幂等+审计 · `:233-234` 权重 1.0/0.8 · `:340-342` _source_weight；`continuity.py:98` header · `:105-115` 开关默认 false · `:149/:169/:187` 渲染/注入/装配 · `:240/:243` span；`README.md:21` pref 域已预留 · `:144` 非范围「画像 / preference」。

---

## 非阻塞备注（不影响本轮回填 · 供 10-task/30 知悉）

1. **evals/memory 锚点措辞**：task 现状锚点记「evals/memory/ 现仅 `__init__.py` + `run_eval.py`」，本分支实查该目录无任何源文件（仅陈旧 `__pycache__`）；`run_eval.py` 先例出自**未合并分支** `task/memory-golden-eval` 的 commit `a54b8ed`（经 `git merge-base --is-ancestor` 实证非本分支祖先）。核心裁定「无金样 · 金样为新增」反而更强地成立；建议 10-task 顺手修正锚点措辞为「本分支无源文件 · run_eval.py 先例见 task/memory-golden-eval」，或由 30 开工时知悉（D4 落点本就 30 定，实质影响为零）。
2. **B1 统计口径小疵**：B1 表「回归」主处置行实为 8 行（#3/#5/#6/#7/#8/#9/#10/#11），R4 与修订节记「回归×7」（系将 service_db 三行并为两组计）。总数 13、改编×3、删除×0 均无误，纯计数口径瑕疵，建议顺手对齐。
3. **SPEC 侧观察**（非本 task 问题 · 不回改）：SPEC 签收 commit `4a2f4d9` 仅改状态行，其 §人工闸表 `HG-SPEC-SIGNOFF` 行字面值仍 pending，与头部 signed 状态以头部+commit 为真值一致即可，task 引用（signed · 4a2f4d9）准确。

---

## 回填清单

零内容阻塞，无退回回填项。

---

## 签收

**R1 书面审查通过：task 内容可执行，与 SPEC（signed · 4a2f4d9）实质零差异，锚点与基线亲跑复核成立。**

流程闸状态：`HG-AUDIT-R1` = **pending**（blocks 30）——待维护者签 task 人工闸表为 approved 后 30 方可开工。

## 维护者签闸（20 后 · 30 前）

- [ ] 已读 R1 审查结论
- [ ] 在 task 人工闸表将 HG-AUDIT-R1 改为 approved（维护者 · 日期）
- [ ] commit task 文档或确认已签
- [ ] 再下发 Harness 30 Prompt

30 Agent 将以 task 表为准；pending 时必须拒开工（见 TEMPLATE_30_gate_stop.md）。
