# 20-task-audit invoke · hitl-approval-consumption-strategy-env（T3 R1 · SPEC v1 D3 env 口承接审查）

> **帽**：20-task-audit（R1）· **task**：docs/tasks/active/task_hitl_approval_consumption_strategy_env.md（commit 07f9cc1 · T3 最小独立 · 无依赖可插队）
> **分支**：task/hitl-approval-consumption（worktree task-hitl-approval-consumption）
> **对照 SPEC**：SPEC-hitl-approval-consumption_v1.md（spec-hitl-approval-consumption worktree · 只读 · HG-SPEC-SIGNOFF=approved 2026-10-10）
> **日期**：2026-10-10 · **结论**：**PASS**（内容零阻塞 · 非阻塞 nit×3）· 审查文 `docs/harness/reviews/task_hitl_approval_consumption_strategy_env_audit_R1_20261010.md`

---

## 触发

00 拆分三 task（T1/T2/T3 · commit 07f9cc1 · 三闸 pending）→ 维护者令 20-task-audit R1 书面审 T3（审查帽并行 · 本帽只审 T3 一件）。

## 实证面（本帽实读/实跑留证）

- `strategy/config.py:1-45` 全实读：docstring 禁 None=全开（:1-6）· 静态 map supervisor 五枚+default（:14-23 · :11 最小只读集）· 覆盖口 `CANDIDATE_CAPABILITY_IDS`（:25-26）· 三分支结构（覆盖口直返 :39-40 · 未命中 [] :43-44 · 命中 list(mapped) :45）——task 锚点表逐行吻合，「追加点=map 解析结果之后」钉有实码支撑。
- `strategy/builder.py:177-182`：节点函数内每轮调 `get_candidate_capability_ids` → `build_allowlist_from_candidates(candidates, visible_ids)`——「调用点读取 · 禁 import 固化」钉可行（函数内读 env 即每轮生效 · 无模块级固化消费方）。
- 下游闸实读：`registry.py::_match_filter :112-140`（deny_high_risk :128 在 deny_write :130 前 · docstring :118 永不豁免）· `policy.py:96-105`（high_risk 闸 + write_not_confirmed）——FP-5「env 注入高危/写 id 仍被裁」四层链成立。
- env 先例实读：`delegation.py:99-107`（函数内 strip/lower/回退 + `_env_int` low/high）· `baseline.py:40,44`（`OPS_CAPABILITY_ALLOW_WRITE_TAGS` 逗号分隔 · 空/未设→None）。
- 图谱：`01_modules.md` 行 35 lg_rag 行「路径覆盖补记」段载 `app/ops/strategy/**` 非一级模块归属裁定——回写落点正确（task 引文为转述 · nit-2）。
- 证据源：`invoke_20261009_40_verify_testing-write-capability.md` :33 逐字吻合（live 静态五枚 + shim 补位登记）。
- B1 行号复核：`test_lg_rag_supervisor_capability_catalog.py:50-57` · `test_capability_domain_allowlist.py:102-112` 逐字吻合。
- B1 复扫（grep 触点全集）：漏登 `tests/eval/test_eval_agent_golden.py:32`（patch 同函数 · nit-1 非阻塞 · `pyproject.toml:77` testpaths=tests 全量回归兜底）。
- env 名 `OPS_STRATEGY_EXTRA_CANDIDATE_CAPABILITY_IDS` 全仓 grep：代码零使用 · 无冲突。

## SPEC 承接闭合（摘要）

D3/Q4-S1/FP-5/A4 逐条映射闭合（A4①②→TC1 · A4③=FP-5→TC2 · A5/A8 本 task 面→TC2/TC3）；R2 留转「覆盖口生效时不追加 env」经本帽复核**认可**（不违 Q4-S1「map 解析后追加」字面 · 守测试钩子纯净 · TC1④+实操-D 断言化兜底）。

## 机械闸复跑

- `npx spec-wave task lint --file docs/tasks/active/task_hitl_approval_consumption_strategy_env.md` → **LINT: PASS · EXIT=0**
- `npx spec-wave verify --target . --task docs/tasks/active/task_hitl_approval_consumption_strategy_env.md` → **VERIFY: BLOCKED · EXIT=2**（HG-TASK-DRAFT / HG-AUDIT-R1 / HG-GRAPH-MODULES 三闸 pending · 属实时序 · 符合预期）

## 本帽边界

- 未改 task 实质内容；未代签任何 human_gate；未执行 30；未触 `app/`/`tests/`。
- 交付：R1 审查文 + 本 invoke（task required_invoke_hats=`10,20,30,40` 含 20 · 强制落盘）。

## 留转

1. 维护者签闸清单见审查文文末（HG-TASK-DRAFT / HG-AUDIT-R1 / HG-GRAPH-MODULES 三闸 · 00 代录 · 图谱闸承 testing-write-capability「在册」先例：30 前签 approved · lg_rag 行备注回写为 30 交付义务）。
2. 30 开工后吸收三 nit：B1 补登 eval golden 行（或 40 invoke 亲跑显式含该文件）· TC1① 以字面期望 list 断言落地 · FP-5 断言选型落 30 invoke 留痕。
