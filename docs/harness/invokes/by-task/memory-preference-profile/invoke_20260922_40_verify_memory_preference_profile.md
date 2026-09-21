# invoke · 40-verify · memory-preference-profile

| 项 | 内容 |
|----|------|
| **时间** | 2026-09-22 |
| **帽** | 40 核验（不改实现码 · 不签闸 · 不 push · 只写过程文档） |
| **分支** | `task/memory-preference-profile`（每次 commit 前 `git branch --show-current` 核验 ✓） |
| **核验对象** | 30 交付 1975ab5 + f1faf80 + 图谱 ratify f90d74d |
| **task** | `docs/tasks/active/task_memory_preference_profile.md`（验收 27 条 · B1 13 行） |
| **SPEC** | `docs/spec/memory-preference-profile/SPEC-memory-preference-profile_v1.md`（signed 4a2f4d9） |

## 总判定：**PASS**（27 条全过 · 2 项 30 文档措辞偏差如实列问题清单，均不影响码面结论）

## 一、真跑证据

### 1. pytest 全量 + 基线对照（亲跑）

| 面 | collected | passed | failed | skipped | 红名单 |
|----|-----------|--------|--------|---------|--------|
| 分支 f90d74d | **1239** | **1235** | **3** | 1 | capability proxy ×1 + chat_ws ×2 |
| 基线 worktree @ origin/master d253c5e（+同 .env，/tmp/opsdesk-baseline-master） | **1210** | 1206 | **3** | 1 | **同款 3 红逐名一致** |

- 3 红 = 基线环境性（本机代理 / WS 环境），逐名对照一致，非本波引入。memory_backfill flaky 两轮（分支+基线）均未复现，无需复跑区分。
- 新增守护：**+29 collected**（1210→1239）；nodeid 级 diff 核验**零既有用例删除**——唯一"消失" nodeid 是 `test_kind_not_allowed` 单测被 B1 #1 改编为 4 个参数化变体（`[profile]/[PREFERENCE]/[prefs]/[]`），属声明内改编非删除。
- ⚠️ 30 invoke 自称「collected 1210→1235（+25）」**不准确**：1235 是 passed 数而非 collected；实际 +29（见问题清单 P-1）。

### 2. ruff 零新增（亲跑）

分支 `ruff check app tests` = **57 errors**；基线 worktree 同命令 = **57 errors** → 零新增 ✓。

### 3. alembic 往返（dev 库 opsdesk 亲跑 · 终态回 head 数据零触碰）

1. 起点：`alembic current` = 20260921_llm_usage（落后 head 一阶），表 0 行，CHECK = `kind = 'fact'`。
2. `upgrade head` → 20260922_memory_kind_preference；CHECK 变 `IN ('fact','preference')`；直插 preference 行**收** ✓。
3. **脏 downgrade**（库内留 1 preference 行）→ **显式炸** `CheckViolationError: check constraint "ck_ops_memory_facts_kind" ... is violated by some row`，事务回滚**停在 head 原地** ✓（与迁移 docstring「回滚须先清 preference 行」注释路径一致）。
4. 清 scratch 行 → `downgrade -1` ✓ → 旧 CHECK 下：preference 插入**拒**（CheckViolationError）· fact 插入**收** ✓。
5. `upgrade head` 再升 → head · CHECK 放宽 · 表 0 行（scratch 全清，**数据零触碰**）✓。

### 4. graph-compile（亲跑）

`./scripts/graph-compile.sh` **绿**（done · mermaid normalize check 9 md OK）；`shared/graph.json` 仅时间戳漂移，已 `git checkout` 还原不提交 ✓。

### 5. 断言抽查（亲跑 + 真读码）

- **双节注入结构**：`render_memory_facts_block` 分节（`[已知事实]` / `[用户偏好]` + 引导语「显式陈述 · 非客观事实 · 无偏好不要假设或编造」）；`inject_memory_facts_block` 在 diff 中**零改动** → 仍单条独立 SystemMessage ✓。
- **无偏好节物理不存在**：码面 `if pref_items: sections.append(...)`——空集节不生成（非空节）；redline P1（G1–G4 金样 + 反向对照）亲跑绿 ✓。
- **fact-only 逐字节**：40 独立重做一次性对拍——同 7 组输入（str/int/bool/float/换行转义/多行/空集）分支 vs master worktree 渲染输出 diff 为空 → **逐字节一致 ✓**（输出存档 /tmp/render_branch.json vs /tmp/render_master.json）。
- **key_kind_mismatch**：gate.py:131 双向绑定（`(kind==preference) != (key 首段==pref)`）；`test_key_kind_mismatch_bidirectional` 3 变体 + `test_preference_with_pref_key_allowed` 亲跑绿；`REJECT_REASONS` 真读 = **8 码** ✓。
- **revoke_by_key**：service.py 真读——必带 tenant+user 谓词 · 只动 active（幂等 0 行）· 审计日志记 affected（含 0）· 不物理删；`test_revoke_by_key_semantics` + 三态全链路 `test_mutation_wrong_preference_pollutes_then_revoke_by_key_erases`（写入→污染出现→revoke_by_key→消失+偏好节物理不存在）亲跑绿 ✓。
- **金样判定面**：`evals/memory/preference_redline_v1.yaml`（P0 清单↔实现对应 / P1 无记忆偏好类提问零偏好节 G1–G4 / P2 引导语锚点 / P3 偏好不污染事实节 · 各带反向对照）真读 + `tests/eval/test_memory_preference_redline.py` 真读——**判定面 = 注入上下文结构**（SystemMessage 文本节存在性断言），热路径零 LLM-as-judge，非自由文本裁判 ✓。
- **零新 env / 零新 SSE**：`git diff origin/master -- app/` grep `os.getenv|environ` 新增 = 0；SSE/event 相关新增行 = 0 ✓。
- **span 双计数**：continuity.py:278-282 `memory_facts_injected` / `memory_preferences_injected`（preference=0 不出该 key → fact-only 观测面零变化）✓。

### 6. 变异检验复做（③ 亲复做 · ② 测试亲跑）

- **③ 显式-only 可检（亲复做）**：extract.py:129-131 构造点临时传 `kind="preference"` → `pytest tests/test_memory_extract_p1.py` **恰 2 挂**（`test_extract_constructed_candidates_are_fact_kind` + `test_extract_noise_candidates_rejected_table_zero`）· 14 passed；`git checkout` 还原 → 16 全绿 · `git diff origin/master -- app/ops/memory/extract.py` = **0 行** ✓（与 30 自称完全一致）。
- **② 清除可检**：三态全链路测试真 PG 亲跑绿（见上）。
- **① 污染可检**：采用 30 记录（临时渲 preference 进事实节 → 8 挂 → 恢复 31 绿），40 未重做（动作要求≥1 条，已复做 ③ 并亲跑 ②）。

### 7. B1 抽核（5 条实核）

| # | 30 处置 | 40 实核 |
|---|---------|---------|
| 1（改编 gate :37-40） | 换集合外值参数化 | ✓ nodeid `test_kind_not_allowed[profile/PREFERENCE/prefs/]` 4 变体在册且绿 |
| 5（回归+新增 supersede） | 同 kind 零改动 + 跨 kind 新断言 | ✓ `test_cross_kind_same_key_no_supersede`（直插 ORM 绕闸）· `test_preference_same_key_supersedes_old_value` 在册且绿；service.py:53-58 谓词真读含 `kind == candidate.kind` |
| 8（injection 回归+新增） | 既有 15 零改动 + 8 新断言 | ✓ master 19 → 分支 27 collected（+8 与自称一致）；fact-only 逐字节 40 独立对拍一致 |
| 12（新增守护计数） | 自称 +25 · collected 1210→1235 | ⚠️ **数字偏差**：实际 **+29 · 1210→1239**（1235 为 passed 数）；其自列分文件总数 40/27/13/16/9/4 与 40 实测逐文件一致——错在汇总算术非测试本身（问题清单 P-1） |
| 13（迁移挂 head） | slug 缩短（varchar(32) 溢出） | ✓ revision = `20260922_memory_kind_preference`（28 字符）挂 `20260921_llm_usage` 后；既有迁移零改动；往返亲跑全过 |
| 特例 | extract.py 零 diff | ✓ `git diff origin/master -- app/ops/memory/extract.py` = 0 行（变异复做还原后再核一次仍 0） |

### 8. diff 白名单与图谱 ratify

- `git diff origin/master --stat`：alembic 迁移 / models CHECK / continuity 渲染 / memory README / gate / service + evals 金样 + tests（conftest 在测试面对齐 CHECK）——**零偏离零变更预判**（无新一级模块/路由/表/事件类型/列/索引）✓。
- f90d74d 真读：docs-only；HG-GRAPH-MODULES 行 pending（00 代录位）→ **approved**（00 ratify）；`01_modules.md:28` memory 行备注「kind=preference 放开…零新路由/表/事件类型/列/索引」在册 ✓。

## 二、验收 27 条结论：**27/27 过**

- 人工闸（1）：HG-AUDIT-R1/HG-GRAPH-MODULES/HG-TASK-DRAFT 全 approved（f90d74d ratify 真读）✓
- D1（5）：ALLOWED_KINDS 集合 / 双向绑定 8 码按码断言 / enumerable 改编 / extract schema+构造点 / fact 回归 —— 全过 ✓
- D2（6）：权重 1.0 断言 / 分节互不串节 / 无偏好节物理不存在 / 单 SystemMessage+逐字节 / span 双计数零新 SSE / 锚点断言 —— 全过 ✓
- D3（3）：supersede 谓词含 kind 跨 kind 互不影响 / revoke_by_key（幂等·审计·清除后零召回）/ 物理删除零发生 —— 全过 ✓
- D4（3）：结构断言 / 金样 P0–P3+G1–G4 反向对照零 LLM-as-judge / 三态全链路变异 —— 全过 ✓
- D5（3）：迁移可逆往返+回滚注释 / 零新列索引+graph-compile 绿+图谱一致 / README 同步（非范围移除·偏好节样例·故障语义·env 表）—— 全过 ✓
- 变异检验（3）：③ 40 亲复做（2 挂→还原绿→diff 0）· ② 三态亲跑绿 · ① 采 30 记录 —— 过 ✓
- 工程（3）：B1 闸前置逐条回填（抽 5 实核）/ 全量 pytest+ruff 口径（见问题清单 P-1 措辞偏差）/ diff 白名单 —— 过 ✓

## 三、问题清单（均文档措辞级 · 不阻塞）

- **P-1（轻）**：30 invoke「collected 1210→1235（+25 新增守护）」数字不准——实际 collected **1210→1239（+29）**，1235 是 passed 数；其自列分文件总数与 40 实测一致，错在汇总。建议 CLOSE 时按 40 实测数入账。
- **P-2（提示）**：task test_strategy_note 写「基线 1210 collected 真跑」与 40 实测一致 ✓；但 30 invoke 同句复用时未更新，同 P-1 并案。
- **P-3（提示）**：dev 库在 40 前落后 head 一阶（current=20260921_llm_usage）——非问题（恰为往返实测提供真起点），终态已回 head。

## 四、遗留（承 R4/R5 residual · 40 复核成立）

- 统一预算下 preference 挤占 fact 召回：span 双计数可观测，另案。
- 显式-only 靠构造点单测+非范围维持：变异检验 ③ 40 亲复做有效；未来新增写入通路必须复判。
- 金样判定面=注入上下文结构（确定性）：模型端残余由引导语+结构断言双保险承接。

## 五、下一棒

CLOSE：按 40 实测数（+29 · 1210→1239）入 kpi_aggregator；PR 合并前保持 graph-compile 绿 + CI 绿；禁止 push 由维护者执行合并。
