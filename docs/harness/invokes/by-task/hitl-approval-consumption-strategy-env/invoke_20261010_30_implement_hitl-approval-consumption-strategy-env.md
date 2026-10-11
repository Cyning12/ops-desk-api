# 30 invoke · hitl-approval-consumption-strategy-env（T3 · 全量交付 · 三 commit · 未 push 未开 PR）

> **帽**：30-implement · **task**：docs/tasks/active/task_hitl_approval_consumption_strategy_env.md（T3 · D3 strategy 候选 map env 追加口 · 最小独立）
> **分支**：task/hitl-approval-consumption（worktree task-hitl-approval-consumption · 开工基线 8843b4c）
> **日期**：2026-10-10 · **结论**：**交付完成**（F1–F4 全量 · TC1–TC3 全绿 · B1 八文件亲跑 114 passed · nit×3 全吸收）
> **分支备注**：task 表 git_branch 字段为 `task/hitl-approval-consumption-strategy-env`，实际 worktree 分支为 `task/hitl-approval-consumption`（与委托令一致 · 同 worktree 内有 T1/T2 兄弟任务并行过程文档）——已以委托令 + verify EXIT=0 为准开工，差异留 00/40 知会（见留转清单 4）

---

## 人工闸扫描（GATE_VERIFY · 首输出）

| human_gate_id | task表status | 用户/invoke声称 | 一致？ | blocks_30 | 30可开工？ |
|---------------|--------------|-----------------|--------|-----------|------------|
| HG-TASK-DRAFT | approved（维护者签 · 00 代录 2026-10-10 · task :38） | approved（委托令「T3 三闸 approved」） | Y | Y | — |
| HG-AUDIT-R1 | approved（R1 PASS · 00 代录 2026-10-10 · task :39） | approved | Y | Y | ✅ |
| HG-GRAPH-MODULES | approved（维护者签「在册」· 00 代录 · task :40 · lg_rag 行备注回写义务 F4/TC3 在案） | approved | Y | Y | ✅ |
| HG-PILOT-OPSDESK-GLAYER | n/a | — | Y | N | — |

reviews：task_hitl_approval_consumption_strategy_env_audit_R1_20261010.md 存在且 R1 PASS（内容零阻塞 · nit×3 非阻塞留 30/40）？ **是**
pre-30 invoke：required ∩ {10,20,00} 齐全（10/20 已落位本 slug 目录）？ **是**
机械辅助：`npx spec-wave verify --target . --task docs/tasks/active/task_hitl_approval_consumption_strategy_env.md` → **VERIFY: PASS · EXIT=0**（本帽亲跑 2026-10-10）

**结论：可进入读码/改码。**

---

## Commit 拆分（中文 conventional · 未 push 未开 PR）

| # | hash | 内容 |
|---|------|------|
| 1 | cd253f0 | feat(strategy): 候选 map 增 env 追加口 OPS_STRATEGY_EXTRA_CANDIDATE_CAPABILITY_IDS（F1+F2 台账） |
| 2 | 3c1c9d1 | test(strategy): T3 env 追加口验收单测 TC1–TC3（18 枚 · F3） |
| 3 | （本 invoke 所在 docs commit · hash 见 git log） | docs(graph+invoke): lg_rag 行备注回写 + 闸表 00 代录行 + 本 invoke（F4） |

---

## 改动面（钉死契约对账 · 越界零）

- `app/ops/strategy/config.py`（唯一码改文件）：模块 docstring 补 env 口说明；增 `EXTRA_CANDIDATE_CAPABILITY_IDS_ENV` 常量 + `_extra_candidate_capability_ids()`（逗号分隔 · strip · 去空 · 保序去重 · 全空白→[] · 函数内读 os.environ）；`get_candidate_capability_ids` map 解析结果之后追加（含未知 key [] 分支）· 生效 logger.info 记 count+ids
- **一行未动核验**：覆盖口直返分支（原 :39-40）原样 · `CAPABILITY_ALLOWLIST_BY_KEY`/`MINIMAL_READONLY_CAPABILITY_IDS` 静态成员原样 · builder.py / registry.py / policy.py / scenario.py / nodes.py **零触碰**
- 下游核验：`git diff --stat master...HEAD -- app/ops/capability/registry.py app/ops/capability/policy.py` → **空**（diff 空实证）

---

## 验收自证（TC1–TC3 逐项 · 实跑留证）

### TC1（env 口零 diff/追加语义 · SPEC A4 · nit-3 字面量断言形态采纳）✅

测试文件 `tests/test_strategy_env_extra_candidates.py`（autouse fixture：delenv + 覆盖口置 None 防跨文件漂移）：

- **① 不设 env 逐字节对拍（字面量断言）**：`test_tc1_unset_env_supervisor_byte_identical`（supervisor 静态五枚字面 list：utc_now_iso/mock_get_issue_status/mock_get_deploy_info/get_issue_by_number/get_pr_by_number · agent_type 与 mode 两入参形态）· `test_tc1_unset_env_default_byte_identical`（default==["utc_now_iso"]）· `test_tc1_unset_env_unknown_key_fail_closed`（未知 key==[]）· `test_tc1_blank_env_equals_unset`（"   "/"  , ,  "/",,," 三态 == 不设）
- **② 设 env 追加语义**：`test_tc1_env_appended_after_map_hit`（supervisor+1 · map 本体不被改）· `test_tc1_env_appended_for_unknown_key`（未知 key 也追加）· `test_tc1_env_intersection_visible_semantics_unchanged`（∩visible：可见 env id 放行 / 不可见写 id 入 stripped · allowed/stripped 字面断言）
- **③ 解析四例**：`test_tc1_env_parse_cases` 参数化——strip（"alpha, beta ,gamma"）/ 连续逗号去空（"alpha,,beta,,"）/ 保序去重（"alpha,beta,alpha,beta"→["alpha","beta"]）/ 全空白=不设
- **④ 覆盖口隔离**：`test_tc1_override_not_polluted_by_env`（CANDIDATE_CAPABILITY_IDS=["utc_now_iso"] + env 双 id → 两 key 调用均 == ["utc_now_iso"] · env 不混入）
- **实操-B 调用点读取**：`test_env_read_at_call_point_no_reload`（setenv 后直读生效 · delenv 后即复原 · 无需 reload）

### TC2（FP-5 · 下游闸不动 · 三层）✅

**选型留痕**（task TC2「按既有测试面选型断言并留痕」· R1 §五）：层 1 选**真实 builder 路径**（不打 patch 候选函数 · 直接经 `strategy_builder_node` 全链）而非 B1 点名文件的复写——新增断言落在 registry/policy 公共入口，与 B1 钉死面（`test_allow_tags_does_not_waive_deny_write` 等）互补而非重复；B1 两钉死面原样绿见下。

- **层 1 ∩visible**：`test_tc2_fp5_env_write_id_stripped_by_visible_intersection`——env 注入 `testing.write.echo`（写 capability）→ 候选层确含（追加口生效断言）→ 真实 builder 节点输出 `allowed_capability_ids` 不含 · span `strategy_builder_stripped_ids == ["testing.write.echo"]` 台账照旧
- **层 2 deny 判序**：`test_tc2_fp5_deny_order_still_cuts_write_and_high_risk`——BUILDER_CAP_FILTER 下写/高危 spec 皆裁；`allow_write_tags_any` 只豁免 deny_write 一层（write spec 放 · high+write spec 仍裁 · deny_high_risk 判序在前永不豁免）
- **层 3 Policy 写闸**：`test_tc2_fp5_policy_write_gate_still_blocks`——check_invoke 写 spec 无确认 → `allowed=False · write_not_confirmed`
- **机械层**：registry.py / policy.py diff 空（见改动面节）· `test_allow_tags_does_not_waive_deny_write`（domain_allowlist:102-112 钉死）B1 亲跑原样绿

### TC3（工程面 · SPEC A8 本 task 面）✅

| 项 | 命令 | 结果 |
|----|------|------|
| pytest 全量 | `pytest tests -q --tb=short`（SILICONFLOW_API_KEY=dummy-probe · 见下注） | **1679 passed, 1 skipped in 27.85s** |
| ruff 触及路径 | `ruff check app/ops/strategy/config.py tests/test_strategy_env_extra_candidates.py` | **All checks passed! EXIT=0**（初跑 C408 一处已修 · 复跑零新增） |
| graph-compile | `./scripts/graph-compile.sh` | **EXIT=0**（9 md OK · graph.json 143 nodes/210 edges · 时间戳噪音已 checkout 还原） |
| task lint | `npx spec-wave task lint --file docs/tasks/active/task_hitl_approval_consumption_strategy_env.md` | **LINT: PASS · EXIT=0** |
| lint-wiki-delta | `npx --yes spec-wave@3.0.1 task lint-wiki-delta --target .` | **PASS · scanned 152 · issues 0 · EXIT=0** |
| 台账断言 | `test_tc3_env_effective_audit_logged` / `test_tc3_no_audit_log_when_env_unset` | 设则记（count=2+ids）· 未设不记 · 双向绿 |

> **pytest 环境注记（如实留痕）**：裸跑（worktree 无 `.env`）1678 passed + 1 failed——`tests/test_memory_vector_p1.py::test_embedder_failure_degrades_with_marker` 因缺 `SILICONFLOW_API_KEY` 在 embedder 构造期 raise（memory/embedder 面 · 与本改动零耦合 · grep 无 strategy 引用）。**反证三连**：①master 主 checkout（有 .env）同测试单跑 PASS；②worktree 内设 `SILICONFLOW_API_KEY=dummy-probe` 单跑 PASS（3.57s · 走降级路径）；③worktree 分支与 master 码面 diff 仅本 task 两文件（config.py 增改 + 新测试文件 · 均不触 memory/embedder）。结论：环境性既有条件（worktree 缺 .env），非本 task 回归；带 key 全量 1679 passed 为有效绿。

### B1 旧测清单亲跑（含 nit-1 补登 · 八文件）✅

```
pytest tests/test_strategy_builder.py tests/test_strategy_scenario.py \
  tests/test_lg_rag_supervisor_capability_catalog.py tests/test_prompt_assets.py \
  tests/test_prompt_assembly.py tests/test_capability_domain_allowlist.py \
  tests/test_capability_testing_write.py tests/eval/test_eval_agent_golden.py -q
→ 114 passed in 0.36s
```

- 清单六文件全绿 + **nit-1 补登行** `tests/eval/test_eval_agent_golden.py:32`（`_CANDIDATE_PATCH` patch builder 绑定名 · 对 config.py 内部 env 追加天然零 diff）显式纳入亲跑——采纳 R1 §十一 nit-1 选项乙（不改 task 文档 B1 表 · 亲跑记录显式含该文件 · 留 40 复核）

### F4 图谱同步（HG-GRAPH-MODULES「在册」附带义务）✅

- `docs/_tech_graph/l1/01_modules.md` lg_rag 行「路径覆盖补记」strategy 段（行 35）备注回写：env 追加口形态/零 diff/含未知 key/覆盖口隔离/调用点读取/台账/下游不动七要素
- 闸表追加 00 代录行（承 chat-history-api / hitl-browser-decide 行先例形态 · 维护者签「在册」2026-10-10 · 30 回写本文）
- graph-compile.sh EXIT=0 复核在案；**不新增一级模块 · 零新跨模块边 · 不增 implementedBy**
- nit-2 吸收：回写备注基于图谱行**原文**实读（含「Builder/Intent/Critic」片段 · 非 task 转述引文）

---

## nit×3 吸收记录（R1 审查 §十一）

| nit | 处置 |
|-----|------|
| nit-1 B1 漏登 eval golden 行 | ✅ 亲跑显式含 `tests/eval/test_eval_agent_golden.py`（114 passed 含其内）· 留 40 复核 |
| nit-2 图谱行引文为转述 | ✅ 图谱回写以 01_modules.md:35 原文为准实读 · task 文档无需改（审查文裁定语义无损） |
| nit-3 TC1① 字面量断言 | ✅ 采纳：supervisor/default/未知 key 三组字面期望 list 断言 + 不设/全空白两态相等 |

---

## 自检结论（执行者回填 · task :209 对应）

30 自检：改动面单文件 + 图谱行备注 · 钉死契约七行逐条落地（env 形态/追加含未知 key/覆盖口隔离/调用点读取/下游不动/静态成员零改/台账设则记未设不记）· TC1–TC3 全机断绿 · B1 八文件亲跑绿 · 双 lint PASS · 非范围零触碰（T1/T2 面/覆盖口语义/builder 裁剪/deny/Policy/gateway/新 capability 注册/SPEC 文档均未动）。

---

## 留转 40 清单

1. **全量 pytest 复跑口径**：40 复跑须带 `SILICONFLOW_API_KEY`（或于主 checkout / 备 .env）——裸 worktree 缺 .env 时 `test_memory_vector_p1.py::test_embedder_failure_degrades_with_marker` 环境性红（本 invoke TC3 注记已反证非本 task 回归）；40 若复跑遇同红按此口径判
2. **B1 亲跑记录**：40 invoke 须显式含 `tests/eval/test_eval_agent_golden.py`（nit-1 选项乙落点 · 本帽 114 passed 记录在案待 40 复核）
3. **TC2 选型复核**：层 1 选真实 builder 路径断言（非复写 B1 点名文件）——选型理由已留痕，40 复检断言充分性
4. **分支字段差异知会**：task 表 git_branch=`task/hitl-approval-consumption-strategy-env` vs 实际 worktree 分支 `task/hitl-approval-consumption`——PR 合并前由 00/维护者确认以何者为准（或随 T1/T2 合流策略一并裁定）
5. **图谱闸表 00 ratify**：01_modules.md 闸表新增行按「30 回写 · 00 代录在案」先例落盘，00 ratify 复核
6. **不 push 不开 PR**：三 commit 待 40 验收 + 维护者令后走 PR 流程（CI 绿 + graph-compile 前置）
