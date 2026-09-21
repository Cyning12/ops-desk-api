# Task：bugfix · 记忆融合 tz 混算修复（naive/aware datetime）

> **状态**：`done`（2026-09-21 闭环：三闸 approved · 30 F1–F3 交付（最小改动 · 扫描清单 7 类点位）· 40 独立核验 PASS（8/8 · 真 PG aware 实证复跑）· 代码在 `fix/memory-fuse-tz`（worktree）· **PR 待开**）  
> **类型**：**bugfix**（双轨：可跳 SPEC · live 裁决记录 ≈ mini-SPEC）  
> **依据**：`docs/harness/invokes/by-task/memory-golden-eval/invoke_20260921_00_live_verdict.md` 发现 1（PR #146 分支）  
> **分支**：`fix/memory-fuse-tz`（base：`master` · **worktree `../ops-desk-api-tzfix`**——主检出已被 llm-layer-hardening 任务占用，全程 worktree 作业）  
> **00 注**：2026-09-21 · 维护者令「开工」（P0/P1/M1 同模式授权延续：00 代录闸 · 30/40 子 Agent）

---

## Harness 元信息

| 字段 | 值 |
|------|-----|
| **task_slug** | `memory-fuse-tz-fix` |
| **git_branch** | `fix/memory-fuse-tz` |
| **implement_repo** | `ops-desk-api`（**worktree `../ops-desk-api-tzfix`**） |
| **test_strategy** | `required` |
| **test_strategy_note** | 纯函数回归：aware/naive 四象限组合不抛 + 衰减值正确；真 PG 路径现有 95 条 memory 测试全绿；不连外网 |
| **code_quality_bar** | `L2_backend` |
| **graph_change_layer** | `none` |
| **graph_delta** | `n/a` |
| **graph_delta_note** | bugfix · 无模块/契约改动 · HG-GRAPH-MODULES 以 `none` 代录 |
| **wiki_delta** | `n/a` |
| **wiki_delta_note** | 依据=live 裁决记录（mini-SPEC） |
| **review_hat** | `20` |
| **required_invoke_hats** | `10,20,30,40` |
| **invoke_retention_profile** | `default` |
| **experience_capture** | `recommended` |
| **kpi_aggregator** | `CLOSE` |
| **orchestration** | 10 落稿 → 20 R1 → 00 代录 → 30 → 40 → CLOSE → 重跑 live 裁决向量开关 |
| **freeze_id** | 无 |

### 人工闸

| human_gate_id | status | blocks_hats | 说明 |
|---------------|--------|-------------|------|
| HG-TASK-DRAFT | **approved** | 20-R1, 30 | 2026-09-21 维护者令「开工」 |
| HG-AUDIT-R1 | **approved** | **30** | 2026-09-21 维护者令「开工」（同模式授权延续）· 00 代录（20 R1 终轮零阻塞已落盘） |
| HG-GRAPH-MODULES | **approved** | **30** | 2026-09-21 00 代录 · `graph_change_layer=none`（bugfix 无模块改动） |

---

## 背景与目标

live 真跑（PR #146 裁决记录 · 发现 1）：migration 建 `timestamptz` → 真库读回 **aware**；`now_utc()=datetime.utcnow()` 为 **naive**；`_time_decay`（`app/ops/memory/service.py:347`）`(now - fact.updated_at)` 直接 `TypeError: can't subtract offset-naive and offset-aware datetimes`。

**测试库 schema 漂移掩盖**：`opsdesk_test` 由 ORM `create_all` 建表（plain DateTime → naive）→ P1 全部测试绿；真库（migration schema）才暴露。生产后果：开向量开关后每次记忆召回抛错 → 降级不注入 → **记忆功能静默失效**（chat 不炸）。

**一句话目标**：tz 归一化修复（naive 视为 UTC）+ aware 回归测试 + schema 漂移注记。**最小改动，不顺手重构**。

---

## 现状锚点（只读 · 30 必读 · 10 已扫）

| 主题 | 路径 · 锚点 | 现状 |
|------|-------------|------|
| 故障点 | `app/ops/memory/service.py:345-348` `_time_decay` | naive/aware 直接相减 |
| now 来源 | `service.py:464` `now = now or now_utc()`（naive） | `recall_active` 同样语义（`expires_at` 比较在 SQL 侧 · 无 Python 算术 · 须 30 复核确认） |
| 融合调用 | `service.py:446` `_fuse_recall` 在向量降级 try 块**外** | 本次只修 tz · 不改 try 结构（改结构另议） |
| ORM 默认 | `app/db/models.py:26-28` `now_utc=datetime.utcnow`（naive · 13 表共用） | **不改** now_utc（仓级影响面 · 另议） |
| schema 漂移 | migration `timestamptz` vs conftest `create_all` plain DateTime | 注记到测试/README · 不重建测试库（大改另议） |

---

## 钉死契约（30 不得静默改义）

| 项 | 钉死 |
|----|------|
| **修复语义** | naive 一律视为 UTC（不是"aware 转 naive"· 不是改用本地时区）；归一化点后移最小（`_time_decay` 内部或入口处单侧归一） |
| **最小改动** | 只碰 tz 混算路径；不改 `now_utc` · 不改 try 结构 · 不改模型列定义 · 不重建测试库 |
| **回归测试** | aware(now)×naive(fact) · naive(now)×aware(fact) · 双 aware · 双 naive 四象限不抛 + 衰减值正确（半衰期边界：0 天=1.0 · 30 天≈0.5） |
| **扫描义务** | 30 须全仓 grep `app/ops/memory/` 内所有 Python 侧 datetime 算术/比较点，逐一确认 tz 安全或一并归一（清单入报告） |
| **注记** | 测试库 schema 漂移（create_all naive vs migration timestamptz）写入 `app/ops/memory/README.md` 或测试 docstring |

---

## 范围

- [x] **F1 · 修复**：tz 归一化（naive→UTC）落在 `_time_decay` 及扫描发现的所有 Python 侧 datetime 算术点
- [x] **F2 · 回归测试**：四象限组合 + 半衰期边界值（`tests/` 新增或并入既有 memory 测试文件）
- [x] **F3 · 注记**：schema 漂移写 README/docstring；30 报告附 datetime 算术点扫描清单

### 非范围

- 改 `now_utc` / 模型列定义 / migration；重建测试库为 migration schema；改 try 结构与降级语义
- 抽取 prompt 校准（另 task）；重跑 live 裁决（维护者/00 动作 · 本 task 合并后）
- 其它表的 tz 审计（仓级议题 · 本 task 只扫 `app/ops/memory/`）

---

## failure_paths

| 触发条件 | 系统行为 | 可重试 | 用户可见 |
|----------|----------|--------|----------|
| `HG-AUDIT-R1` pending 即 30 | **拒开工** | 是 | 是 |
| 修复后仍有 naive/aware 算术点 | 扫描清单缺失 → 40 拒收 | 是 | 否 |
| 顺手改 now_utc/列定义 | 审查拒收（最小改动契约） | 是 | 否 |
| 归一化语义漂移（如转本地时区） | 40 拒收（钉死：naive=UTC） | 是 | 否 |
| 修复后 P1 既有 95 测试红 | 回归失败 → 30 返工 | 是 | 否 |

---

## 验收标准

- [x] 人工闸：`HG-AUDIT-R1` approved 后方可勾选下列码项
- [x] F1：四象限组合不再抛 TypeError；衰减值正确（0 天=1.0 · 半衰期≈0.5）
- [x] F2：回归测试绿；`app/ops/memory/` datetime 算术点扫描清单在 30 报告
- [x] F3：schema 漂移注记落盘
- [x] `app/db/models.py`（now_utc）· migration · conftest **零 diff**
- [x] `ruff` 触及路径绿；`pytest` 本波 + memory 全量（95 条基线）+ lg_rag/session 回归绿
- [x] **旧测 grep 影响面**：memory 系 5 测试文件（P0 34 + P1 22 + golden 10 基线全绿）；`_time_decay`/`_fuse_recall` 调用方仅 `recall_with_vector`（30 复核）
- [x] `npx spec-wave task lint --file docs/tasks/active/task_memory_fuse_tz_fix.md` PASS

---

## 依赖

| 依赖 | 说明 |
|------|------|
| 依据（mini-SPEC） | `docs/harness/invokes/by-task/memory-golden-eval/invoke_20260921_00_live_verdict.md`（PR #146 分支） |
| 被修代码 | `app/ops/memory/service.py`（P1 · PR #145 merged） |
| 编码规范 | `docs/standards/CODING_BACKEND_L2_v1_zh.md` |

---

## 给执行帽的必读列表

1. `AGENTS.md` · 2. 本 task · 3. live 裁决记录发现 1 · 4. `docs/standards/CODING_BACKEND_L2_v1_zh.md` · 5. `app/ops/memory/service.py` 全文（datetime 扫描）· 6. `FRAGMENT_30_gate_verify_v1_zh.md`

---

## 思考轮控制

| 轮 | 结论 | early_stop | reason（early_stop） | residual_risks |
|----|------|------------|----------------------|----------------|
| R0 | bugfix · 故障链已由 live 裁决记录完整给出 | no | — | none |
| R1 | 范围=归一化+回归+注记；最小改动 | no | — | 无 |
| R2 | 修复点单侧归一（`_time_decay` 为主）；now_utc 不动 | yes | bugfix · 故障点明确 · 方案唯一（naive=UTC 归一）；无方案分叉值得展开 | 其它表同模式隐患存在但属仓级另议 |
| R3 | （未开） | — | early_stop at R2 | — |
| R4 | （未开） | — | early_stop at R2 | — |
| R5 | （未开） | — | early_stop at R2 | — |

**actual_last_round**：R2 · **early_stop**：yes · **residual_risks**：见 R2

### R0 · 问题框定
live 裁决记录已给出完整故障链与生产后果，无需重开分析。

### R1 · 范围钉死
归一化 + 四象限回归 + 漂移注记；一切顺手项（now_utc/列定义/测试库重建）明确非范围。

### R2 · 方案
naive=UTC 单侧归一（与 PG 对 naive→timestamptz 的解释一致 · 语义无损）；无第二方案值得对比，提前停。

### R3 ·（未开 · early_stop）

本轮不展开；bugfix 故障点明确，方案已于 R2 钉死。

### R4 ·（未开 · early_stop）

本轮不展开。

### R5 ·（未开 · early_stop）

本轮不展开。

---

### 自检结论（执行者）

> **hat 40** · 2026-09-21 · **40 PASS**（独立核验 · 未复信 30 · 亲跑亲读）

| 命令 | 退出码 | 摘要 |
|------|--------|------|
| git diff --stat（models/alembic/conftest） | 0 | 空输出 · 最小改动契约达成（service.py +16/-2 · README +10 · 新测试 1 文件） |
| ruff check service.py + 新测试 | 0 | All checks passed |
| pytest tests/test_memory_time_decay_tz.py | 0 | 18 passed（四象限×边界值 + naive≡UTC 逐位相等 + +08:00 偏移证不转本地） |
| pytest P0/P1 memory 五文件 | 0 | 76 passed · 基线全绿 |
| pytest tests（全量） | 1 | 1107 passed / 1 skipped / 2 failed（仅 chat_ws×2 既有环境失败 · 无新增） |
| pytest -k memory | 0 | 99 passed（≥95 基线） |
| 真 PG aware 实证（独立 tenant · 临时脚本已删） | 0 | updated_at 实核 timestamptz 读回 aware · recall_with_vector 全路径不抛 TypeError · 清场残留 0 |
| npx spec-wave task lint | 0 | LINT: PASS |

**验收摘要**：8/8 全 ✅。修复语义钉死达成——`_as_utc` naive→`replace(tzinfo=UTC)`（不转本地/不转 naive）· `_time_decay` 双侧归一 · 半衰公式逐字未变；扫描清单独立复核无遗漏（唯一 Python 算术点已修 · sort key 同源一致 · 其余全 SQL 侧）；`now_utc`/列定义/migration/conftest 零 diff；主检出零痕迹（另一窗口任务未受影响）。

**已知未测项**：① live 真跑重测（本 task 合并后 · 裁决向量开关的前置）；② 测试库 schema 漂移重建（非范围 · 已注记）；③ 显式 aware `now` 走全路径被 asyncpg 绑参层拒（既有行为 · 非故障链 · 仅记录）。

**结论**：**40 PASS** · 无阻塞 · 可进 PR 流程

---

## 修订

| 日期 | 说明 |
|------|------|
| 2026-09-21 | 10-task 落稿（bugfix 双轨 · early_stop at R2）· HG-AUDIT-R1 pending → 30 拒开工 |
| 2026-09-21 | 20 R1 终轮零阻塞签收 · 00 代录 AUDIT-R1 · 30 开工 |
| 2026-09-21 | 30 交付 F1–F3 → 40 独立核验 PASS（8/8）→ 00 回写 · 归档 done · CLOSE |
