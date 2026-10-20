# 合并前审查（40 帽）：scenario-stage-rewire

> **审查帽**：Harness 40（合并前代码审查 · 书面审 · 只审不改 · 唯一写入面=本文）
> **被审 diff**：`a1591e9..HEAD`（3 提交：`76c506c` 摘除实施 · `9dd5c79` 跨波次基线修正（00 裁定）· `277d69a` invoke 落盘；合计 9 文件 +460/-187）
> **对照真值**：task `docs/tasks/active/task_scenario_stage_rewire.md`（闸全 approved · 裁定 (a) 摘除）· SPEC v0.1 signed · R1 审查文 `docs/harness/reviews/task_scenario_stage_rewire_audit_R1_20261020.md`（conditional_pass · nits×3）· invoke：`invoke_20261020_30_implement.md` + `invoke_20261020_30_cross_wave_base_fix.md`
> **审查日期**：2026-10-20 · **审查方式**：逐行读全量 diff（9 文件）+ D1–D6 逐条对拍 + grep/g log 实测 + 本机独立复跑（park .env CI 等价跑法 · 跑后已复原）+ 模拟合并 worktree 独立复验

## 结论摘要

- **结论：approve（可合并）** —— 阻塞项 0，非阻塞观察 5 条（§7 O1–O5，均不构成退回理由；O1 建议报 00 裁定处置时点）。
- 摘除面与 task D1–D6 **逐条对拍全过**（§1）；R1 nits N1–N3 全部吸收（§5）；红测先行记录独立复验为真（4 红 test id 逐字一致 → 35 绿，§5）。
- 跨波次基线修正（00 裁定授权）四态语义核验全过：态 1/3/4 有实证或蓝本互锁，态 2 保牙逻辑核验成立；分类器 `_touched_in_wave` 四个真值点全部独立复测命中（§2）。
- 复跑矩阵全绿：全量 pytest **1743 passed / 183 skipped / 0 failed**（#2 闸 1 skipped 态 3 · #3 套件 35 passed · 无其他失败）；ruff / graph-compile / lint-imports 全过；模拟合并后 master 形态两闸不红（§3）。
- freeze 核验通过：SSE 帧 / HTTP 契约零变化，零新 event_type/路由/表，写入侧零改动（§4）。
- 授权链完整：枚举外连带仅跨波次修正一件，00 裁定链在册；遗留挂账 4 项口径逐一核验一致（§6）。

---

## 1. 逐行 diff × task D1–D6 对拍

| D 项 | task 要求 | diff 实证 | 裁定 |
|---|---|---|---|
| D1 import | `builder.py:17-21` 三件 import 整句删（N1 校正） | diff `@@ -14,11 +14,6`：`from app.ops.strategy.scenario import (...)` 五连行含闭合括号整体删除 | ✅ |
| D1 本体 | `_apply_scenario_stage` 函数本体删 | `@@ -108,26 +103,6` 整函数 21 行删除 | ✅ |
| D1 调用点 | `:158` 唯一调用点删 | `visible = _apply_scenario_stage(visible, state)` 删除；grep 全仓 app/ 零命中 | ✅ |
| D1 注释改写 | docstring/两阶段注释 → 直接求交口径 | `builder.py:124-125` docstring 与 `:131-133` 调用点注释均改写为「candidates ∩ 基线可见集直接求交（scenario 阶段已摘除 · 2026-10-20 · 逐值等价）」 | ✅ |
| D1 nodes.py | `multi/nodes.py` 仅注释行改写 · 零逻辑 | diff 仅 `-4/+4` 注释段（:1263-1269 域），无 `scenario_trim` 字样残留（grep 实测零命中）；`multi/graph.py:82-83` 不动 ✓ | ✅ |
| D2 scenario.py | 本体 dormant 保留 · 仅文件头注释 | diff 仅 `+10/-1` 头注块（含「LG_RAG_VISIBILITY_SCENARIO_MODE 已废弃（2026-10-20）」「全仓零生产调用方」「复用须另立 SPEC」）；`scenario_trim`/`audit_scenario_stripped`/`ENV_SCENARIO_MODE`/`scenario_mode`/`os.environ.get` 全部零逻辑改动 | ✅ |
| D3 env 台账 | `GUIDE_env_inventory_v1.md:35` 加 deprecated | :35 行备注列追加「已废弃 deprecated（2026-10-20 · scenario 阶段摘除 · 生产零消费 · scenario.py 本体 dormant 保留）」· 键本体保留 | ✅ |
| D4 图谱 | `01_modules.md` lg_rag 行备注追加 · 不新行 | :35 lg_rag 行 V1-B 备注处追加「scenario 裁剪已摘除（恒短路清理 · 2026-10-20 · 模块 dormant 保留）」；不新行/不新边/不增 implementedBy | ✅ |
| D5 删六 | env 三档+台账六用例删 | `test_mode_off_zero_diff_zero_log`/`test_mode_invalid_falls_back_off`/`test_mode_observe_would_strip_not_applied`/`test_mode_enforce_applies_and_audits`/`test_audit_does_not_log_intent_content`/`test_enforce_fallback_empties_with_audit` 全删 | ✅ |
| D5 改四 | 去 env 耦合改写 | ①`test_no_intent_short_circuits_all_modes`→`test_builder_no_intent_allowlist_equals_baseline_intersection`（Builder 直出逐 id 对拍）；②enforce no-intent→`test_builder_no_intent_passes_baseline_through`（去 setenv）；③enforce high 裁 medium→`test_builder_high_intent_present_no_trim`（「intent 在场亦不裁」断言·语义忠实）；④delegation_scope→`test_supervisor_delegation_scope_never_exceeds_allowlist`（去 `sc.ENV_SCENARIO_MODE` setenv · 保留 ⊆ 断言）；import 行 `_apply_scenario_stage` 去除 | ✅ |
| D5 保留 | S1–S5+畸形+Q2+smoke 原样保绿 | `test_s1..s5`/`test_malformed_*`×3/`test_is_composite_and_summary_not_trim_keys`（:88-193）与 `test_scenario_trim_timing_smoke`（:354）逐字保留 · 单跑全绿 | ✅ |
| D5 新增 | env 失效矩阵 | `test_env_mode_has_no_effect_on_builder_output`：{None,off,observe,enforce,bogus}×{无/有 high intent}=10 参数矩阵 · 逐值相等断言 | ✅ |
| D6 留尸互锁 | sse_stream.py:64 / intent.py:94 不动 | name-status 9 文件不含两者；实测 `sse_stream.py:64` `"intent_node": "intent"` 与 `intent.py:94` `return {**bump, "intent": intent, ...}` 原样在位 | ✅ |
| TC8 白名单 | _resolve_base 三级探测照抄蓝本 | `tests/test_strategy_scenario.py:444-472` `_resolve_base` 与蓝本 `test_memory_injection_consumer.py:608-631` 形态逐字对应（钉锚 `a1591e9` → merge-base 双 ref → skip 带 tried 清单）；三路 diff + untracked 枚举口径一致；`test_diff_whitelist_scenario_stage_rewire` 本分支 1 passed | ✅ |
| TC9 引用清单 | 全仓引用点落 invoke · 残留登记 | invoke_20261020_30_implement.md §5 清单含 `sse_stream.py:64`/`intent.py:94`/`multi/__init__.py:5` 三件「已知残留 · 不动」登记；本审查 grep 复测结论一致 | ✅ |

## 2. 跨波次基线修正专项（00 裁定 · `9dd5c79`）

### 2.1 四态语义核验（`tests/test_memory_injection_consumer.py`）

| 态 | 语义要求 | 核验 | 裁定 |
|---|---|---|---|
| 1 | 钉锚命中 ∧ diff⊆白名单 → pass | violations 空时不进第四态分支直落 `assert not violations` pass；模拟合并 worktree 中 #3 闸同款形态 1 passed 旁证 | ✅ |
| 2 | 钉锚命中 ∧ 越界含波内文件 → **fail 保牙** | `internal = [p for p in violations if _touched_in_wave(root, p)]` → `assert not internal` 带清单 fail；分类器实测 `continuity.py`=True / done task=True 确会判 internal | ✅（逻辑核验 · 未人工构造触发） |
| 3 | 钉锚命中 ∧ 越界全 foreign → 可审计 skip | **本分支实测 1 skipped**（`-rs` reason 列 10 件越界文件全 #3 产物）；**模拟合并 worktree 实测 1 skipped**（同一 reason 清单） | ✅ |
| 4 | 锚不可解析 → skip 带 tried 清单 | `_resolve_base` 本体零改动（diff 纯增量 · grep 无删除行命中），承 #2 已验证蓝本 | ✅ |

### 2.2 分类器 `_touched_in_wave` 独立复测（`git log 414270d..51e75c9 -- <path>`）

| 路径 | 预期 | 实测（命中 commit 数） | 裁定 |
|---|---|---|---|
| `app/ops/lg_rag/continuity.py`（波内 · 已白名单） | True | 1 → True | ✅ |
| `app/ops/strategy/builder.py`（#3 后续波次） | False | 0 → False | ✅ |
| `docs/tasks/done/task_memory_injection_consumer.md`（CLOSE 移动面 · 波内 55424d4） | True | 1 → True | ✅ |
| `invoke_20261020_30_implement.md`（#3） | False | 0 → False | ✅ |

保守退化核验：`_WAVE_TIP` 不可解析或 log 异常 → `return True`（按波内处理 · fail 牙保留 · 绝不静默 skip）——代码路径 `tests/test_memory_injection_consumer.py:593-606` 逐行读确认。

### 2.3 CLOSE done/ 面补登记合规性

`_UPSTREAM_SIGN_PATHS` 增补 `docs/tasks/done/task_memory_injection_consumer.md`（注释注明 `55424d4 [00]` 移动面 · 00 裁定 2026-10-20）。因该文件被判波内（True），登记是唯一自洽处置（skip 态 3 放行不到它）；与登记表中既有 00 落签面（review40 等）同类。**合规**。

## 3. 复跑验证（park .env CI 等价 · 跑后已复原）

.env（3629B）park 至 `/tmp/ops-desk-api.env.parked-by-40`，全部跑完后已复原在位。

| 项 | 命令 | 结果 | 裁定 |
|---|---|---|---|
| 全量 pytest | `.venv/bin/python -m pytest tests -q` | **1743 passed, 183 skipped, 0 failed**（25.87s）——#2 闸 1 skipped（态 3）· 无其他失败 | ✅ |
| #3 套件单跑 | `pytest tests/test_strategy_scenario.py -q` | **35 passed** | ✅ |
| #2 闸本分支单跑 | `pytest ::test_phase_b_diff_whitelist -rs` | **1 skipped** · reason 列 10 件越界文件全 #3 产物 | ✅ |
| ruff | `ruff check app tests` | All checks passed! | ✅ |
| 图谱 | `./scripts/graph-compile.sh` | EXIT=0（mermaid normalize 9 md OK） | ✅ |
| import 分层 | `lint-imports` | Contracts: 12 kept, 0 broken | ✅ |
| 模拟合并 master | worktree `origin/master`（51e75c9）`--ff-only` 至 `277d69a` → 两闸 | **#2 闸 1 skipped（态 3 · 不红）· #3 闸 1 passed** | ✅ |

数字与 invoke §4 完全互洽：invoke 记修正前「1 failed, 1743 passed, 182 skipped」（唯一失败=#2 闸），本审查复跑 = 同一失败转 skip（182→183 · 0 failed）· passed 总数一致。

## 4. freeze 核验

- `sse_stream.py` / router 面不在 diff（name-status 9 文件：builder/scenario/nodes/01_modules/env guide/两 invoke/两测试）· 零帧形/事件变化。
- 零新 event_type / 路由 / 表；写入侧零改动（app/ 改动=删死路径+注释 · 无新写路径）。
- freeze `lg-rag-sse-v1` / `lg-rag-http-v1` 不升 ✓。

## 5. R1 nits 吸收与红测先行

| 项 | 要求 | 实证 | 裁定 |
|---|---|---|---|
| N1 | import 整句 :17-21 删 | 五连行含 `:21` 闭合括号整体删除 | ✅ |
| N2 | 保留面按实 :75-181 | S1–S5 段（现 :88-193 · 含畸形三例+Q2）逐字保留，仅段头注释行改 | ✅ |
| N3 | 测试文件头 docstring 同步 | :1-20 全文改写为摘除后 TC 映射口径，被删三档模式描述清除 | ✅ |
| 红测先行 | 4 红 → 35 绿 | **独立复验**：a1591e9 worktree + 仅覆贴新测试文件（生产码保持旧）→ `4 failed, 31 passed`，红集合四件 test id 与 invoke §3 **逐字一致**（`test_env_mode_has_no_effect_on_builder_output[True-enforce]` / `test_builder_has_no_scenario_residue` / `test_scenario_module_dormant_but_importable` / `test_graph_and_env_inventory_synced`） | ✅ |

## 6. 授权链与遗留挂账

- **枚举外连带**：仅跨波次基线修正一件（触 `tests/test_memory_injection_consumer.py` · #3 原白名单外）；授权链 = 00 裁定（`invoke_20261020_30_cross_wave_base_fix.md` 裁定来源节在册）+ #3 自有 `_TREE_ALLOWED_FILES` 同步补登记（注释注明 00 裁定）· 双登记闭合。**授权链完整**。
- **遗留挂账 4 项**（invoke §5/§6 登记 · 逐一实测）：
  1. `multi/__init__.py:5` 拓扑 docstring 过期（仍述 `START → intent_node → strategy_builder`）——未动 ✓（TC8 白名单外 · 登记）
  2. `sse_stream.py:64` 死映射——未动 ✓（D6 互锁）
  3. `intent.py:94` 留尸——未动 ✓（D6 互锁）
  4. builder 循环 import 预存——**独立复验**：HEAD 与基线 a1591e9 worktree 直导均现同一 `ImportError: cannot import name 'effective_scope_from_requested' from partially initialized module` → 确为预存非本次引入 ✓

## 7. 非阻塞观察（O1–O5 · 均不阻塞合并）

- **O1（建议报 00）**：#3 闸 `test_diff_whitelist_scenario_stage_rewire` **无第四态**。CLOSE 时 task 文件 `active/→done/` 移动面将使 `docs/tasks/done/task_scenario_stage_rewire.md` 越出 `_TREE_ALLOWED_FILES`（仅登记 active/ 路径）→ 该闸在 master 转红（#2 同款前车 · 本次 00 裁定正是治此病）。建议：CLOSE 前由 00 裁定同款处置（补登记 done/ 路径或为 #3 闸套第四态）。
- **O2**：态 3 `pytest.skip` 先于 `_banned` 前缀断言触发——越界全 foreign 时 scripts//alembic/ 禁改检查被跳过（skip 即终态）。闸使命已完成语境下风险可接受；若该四态模式被后续波次复用，建议 banned 断言前置于 skip 之前。
- **O3**：被删六用例含「台账不记内容」安全性质断言（`test_audit_does_not_log_intent_content`）；dormant `audit_scenario_stripped` 的该性质现无测试覆盖。dormant 模块无生产路径可达 + 头注已声明「复用须另立 SPEC」，风险闭环 · 记录即可。
- **O4**：`builder.py:122-125` docstring 两个「allowlist = …」句行文重复（`:122-123` 既述 S1 求交口径，`:124-125` 又述直接求交口径 · 语义一致不矛盾 · nit 级）。
- **O5**：`/tmp/ops-desk-api.env.parked` 为 30 复跑时 .env park 残留副本（仓外 /tmp · 仓内 .env 已复原在位 3629B）——环境卫生提示，无仓内影响。

## 8. 禁区自查（40 侧）

- 只审不改：本帽唯一写入面=本审查文；.env park/复原成对 · 临时 worktree（m40-sim/m40-red/m40-ci）已全部 remove。
- 工作区预存 untracked `backups/` 与 `docs/harness/reviews/task_query_coref_rewrite_review40_20261019.md` 为他务 · 本审查不纳管；二者在场时全量 pytest 0 failed（untracked 不进 violations · 与蓝本口径一致）。
- 本文按既定裁定路径**留工作区不 commit**，报 00 后由 30 走白名单增补入库。

---

## 修订记录

| 日期 | 摘要 |
|---|---|
| 2026-10-20 | 40 合并前审查：**approve**（阻塞 0）· D1–D6 逐条对拍全过 · 四态语义+分类器四真值独立复测全命中 · 复跑 1743p/183s/0f + ruff/graph-compile/lint-imports 全绿 + 模拟合并两闸不红 · 红测先行独立复验（4 红 id 逐字一致→35 绿）· freeze 零动 · 授权链完整 · 非阻塞观察 O1–O5（O1 建议报 00 裁定 #3 闸 CLOSE 移动面处置） |
