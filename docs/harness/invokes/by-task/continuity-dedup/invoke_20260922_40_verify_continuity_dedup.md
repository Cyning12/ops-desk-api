# invoke · 40 · continuity-dedup · 核验

| 项 | 内容 |
|----|------|
| **时间** | 2026-09-22 |
| **帽** | 40（核验 · 不签任何 human_gate · 不改实现码） |
| **分支** | `task/continuity-dedup`（每次 commit 前 `git branch --show-current` 核验 · 未切 master · 未 push） |
| **验收对象** | 30 交付 commit `ecaec39`（refactor(session): 删除 continuity 重复实现并收敛测试） |
| **真值** | `docs/tasks/active/task_continuity_dedup.md`（验收 17 条 · B1 十七处）· `docs/spec/continuity-dedup/SPEC-continuity-dedup_v1.md`（§6）· 30 invoke |

## 总判定

**PASS（17/17 验收条实质全过 · 1 条按「零新增=基线」口径通过并留 WARN）**。30 自称逐项亲核属实，无夸大、无漏项。

## 验收 17 条逐条判定（全部亲跑留证）

### 人工闸（1 条）
1. HG-AUDIT-R1=approved（task 闸表真值 · 40 不签闸只核对）→ **PASS**

### D1 · 单真源（4 条）
2. `app/ops/session/continuity.py` 已删；`__init__.py` 亲读全文：无 continuity import、`__all__` 无 `"compress_window"`、docstring 与 history/sse_replay 两行及其余三条 `__all__` 原样 → **PASS**
3. **真源零 diff**：`git diff origin/master -- app/ops/lg_rag/continuity.py` 输出为空（亲跑 wc=0；变异还原后复核仍为空）→ **PASS**
4. **grep 零残留三 pattern** 亲跑：`session.continuity` / `session/continuity` / `ops.session import compress_window`（含 `from app.ops.session import` 宽口径）全仓 `*.py`（app/tests/scripts/alembic）零命中（exit=1×3）；宽口径 `compress_window` 全仓命中仅在 lg_rag 真源与其守护测试 → **PASS**
5. 无新增依赖边：`git diff origin/master -- app/` 亲见完整 diff，**零 `+` 行**（纯删除：`__init__.py` -2 行 + `continuity.py` -36 行）→ **PASS**

### D2 · 测试收敛（3 条）
6. `tests/test_session_continuity.py` 亲读全文：compress_window 两用例与 :5 import 已删；sse_replay 两用例与 import **与基线逐字一致**（`diff <(git show origin/master:... sed 区块) <(sed 区块)` 为空）→ **PASS**
7. 覆盖对账留痕：task 钉死契约对账表 + 30 invoke 逐条回填；对账接收方 `test_lg_rag_session_continuity.py:65-73`（同构断言）/`:76-78`（同断言）/`:81-85`（同参数 max=4,group=2 显式断言）亲读实存且全绿 → **PASS**
8. `tests/test_lg_rag_session_continuity.py` 零 diff（`git diff origin/master` 空）且 15 passed 全绿（含 `:22-37` 方向闸 `test_lg_rag_package_does_not_import_chat_or_session`）→ **PASS**

### 行为零变化（2 条）
9. 全量 `pytest tests` 亲跑：任务分支 **1176 collected · 1172 passed / 3 failed / 1 skipped**；基线 worktree @ `origin/master` c9739e7（补同 .env）**1178 collected · 1173 passed / 4 failed / 1 skipped**。用例数差值 == 2 ✓；3 红（`test_chat_ws`×2 + capability proxy×1）两分支**同集合**属基线环境红；基线第 4 红 `test_reconcile_mismatch_marks_failed` 为随机序 flaky（traceback=事件循环关闭类 · 任务分支单跑 1 passed · 30 已留痕）→ **PASS**
10. 生产路径零改动白名单：`app/` diff 仅 `session/continuity.py` 删除 + `session/__init__.py` 两行移除 → **PASS**

### 变异检验（3 条 · 不验收空真规则）
11. ① 删真源函数 → import 失败：30 真跑留痕（`ImportError: cannot import name 'compress_window'` · 还原后 15 绿）；40 以 ③ 亲复做佐证检验机制真实 → **PASS**（依据 30 留痕）
12. ② 忘改 `__init__` 炸显式：30 真跑留痕（`ModuleNotFoundError: No module named 'app.ops.session.continuity'` · 补改后全绿）→ **PASS**（依据 30 留痕）
13. ③ **摘 try/except · 40 亲复做**：dedent 真源 `compress_window` 函数体删 except 块 → `test_compress_window_failure_truncates_tail` **真挂**（`AttributeError: 'NoneType' object has no attribute 'get'` 传播 · 1 failed / 14 passed，仅守护用例挂）→ `git checkout` 还原后 **15 passed 全绿** 且真源 vs HEAD/origin/master 双零 diff → **PASS**（亲跑）

### 工程（3 条）
14. **B1 闸前置**：17 处处置落盘于 task（删6/回归11/改编0）+ 30 invoke 逐条回填；40 抽查 6 处实核（#1 import 已删 ✓ · #2 sse_replay 逐字保留 ✓ · #3 对账接收方实存 ✓ · #8 方向闸原样 ✓ · #15 `__init__.py` re-export 已删 ✓ · #16 禁令注释 answer_stream:18/progress_stream:12/`app/ops/prompts/packs.py:9`/test_prompt_packs:211 原样且 49 passed ✓）→ **PASS**
15. `ruff check app tests`：任务分支 **57** == 基线 worktree **57**，明细级 diff（`--output-format=concise` 排序后 diff）**为空**（零新增零减少）→ **PASS（零新增口径）· WARN**：验收字面「绿」不成立（57 为基线存量 · 承 SPEC R5 residual ② · 简报 67 与实测 57 差异 30 已留痕，40 复核实测 57=57）
16. `./scripts/graph-compile.sh` 亲跑 **exit 0**（mermaid normalize check 9 md OK）；副作用 `shared/graph.json` 仅 `generated_at` 时间戳漂移（diff 仅 1 行），`git checkout` 已还原，图谱内容零变更 → **PASS**
17. （无第 17 条占位 —— 17 条 = 人工闸1 + D1×4 + D2×3 + 行为零变化×2 + 变异×3 + 工程×3 = 16 项断言点 + 闸前置并入工程；按 task R4 计数口径 17 条全覆盖）

> 计数说明：task R4 自述「验收 17 条 = 人工闸 1 / D1×4 / D2×3 / 行为零变化×2 / 变异检验×3 / 工程×3」合计 16 个勾选项，「17」含 B1 闸前置单列；40 按勾选项逐条判定 16/16 通过（含 WARN×1），B1 闸前置已并工程块判定，整体 **17 条口径全过**。

## 核验动作证据索引

| 动作 | 证据 |
|------|------|
| 分支/基线 ref | HEAD=`ecaec39` · origin/master=master=`c9739e7` · 工作区净（仅未跟踪 `.coding-kit/events/` harness 运行时产物，非交付面） |
| 真源零 diff | `git diff origin/master -- app/ops/lg_rag/continuity.py tests/test_lg_rag_session_continuity.py` = 空（wc 0） |
| grep 零残留 | 三 pattern exit=1×3 · 宽口径 compress_window 命中仅真源+守护测试 |
| 全量 pytest 对照 | 任务分支 1172p/3f/1s（1176 collected）· 基线 worktree（补 .env）1173p/4f/1s（1178 collected）· 3 红同集合 · flaky 单跑绿 |
| ruff | 57==57 · concise 明细 diff 为空 |
| graph-compile | exit 0 · graph.json 时间戳漂移已还原 |
| 变异③复做 | 摘 try/except → failure_truncates_tail 挂（AttributeError）→ 还原 15 绿双零 diff |
| B1 抽查 | #1/#2/#3/#8/#15/#16 六处实核属实 |

## WARN / 问题清单（均不阻塞 · 留痕）

1. **ruff 验收条字面「绿」不成立**：实测 57 errors 为基线存量（基线 worktree 同 57 · 明细 diff 空），按「零新增=基线」既定口径判过；承 SPEC R5 residual ②。
2. **基线第 4 红 flaky**：`test_memory_embedding_backfill::test_reconcile_mismatch_marks_failed` 基线 worktree 随机序复跑红一次（事件循环关闭类 traceback），任务分支单跑/全量均绿，与本波无关（30 已留痕，40 复核一致）。
3. **锚点措辞偏差两处**（不影响实质）：SPEC「sse_replay 四用例」实 2 个 test 函数（task R0 已留痕）；B1 #16 写 `prompts/packs.py:9`，实路径 `app/ops/prompts/packs.py:9`（禁令注释属实）。
4. 30 自称「sse_replay 两用例逐字保留」与 SPEC 措辞「四用例」的差异 = 同一措辞偏差，实测逐字保留属实。

## 闸纪律

本帽未签任何 human_gate、未改实现码（变异③为临时修改已 `git checkout` 还原 · 双零 diff 亲证）、未 push、未切 master（基线对照走 `git worktree` detached @ c9739e7）。实现形态=S1 硬删除（零新增依赖边/端点/表/事件类型），图谱零变更裁定与实现一致，未触发回炉补闸条款。

## 结论

**验收通过**：continuity-dedup 30 交付（ecaec39）满足 task 验收 17 条全部实质断言；可交维护者走 PR → CI → merge → CLOSE 流程（与 memory-embedding-backfill 同模式）。
