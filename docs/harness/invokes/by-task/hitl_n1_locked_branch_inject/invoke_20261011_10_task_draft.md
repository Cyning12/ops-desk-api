---
hat: 10
task_slug: hitl_n1_locked_branch_inject
date: 2026-10-11
---

# invoke · 10-task 起草 · hitl_n1_locked_branch_inject（N1 locked 空分支注入缺口）

## 输入

- 委派令：序1 N1 注入缺口起草棒（交接档 docs/harness/invokes/by-task/_prompts/PROMPT_00_spec-campaign-handoff_20261011.md §2.2 第 1 项）。
- 上游 SPEC：docs/spec/hitl-approval-consumption/SPEC-hitl-approval-consumption_v1.md §9 序1（LLM 盲循环 + approved 恒 replan 后续项）。
- N1 钉案两源：docs/tasks/close/close_hitl_approved_replan_quality_20261011.md §四.1 + §七.1；40 裁定过程见 docs/harness/invokes/by-task/hitl-approved-replan-quality/invoke_20261011_40_verify.md。
- 代码锚点亲读（base master 286d825）：app/ops/lg_rag/multi/nodes.py:1141-1174（locked/preserved 计算与 if/else 分支）· :755-778（_unlocked_preserved_rows · locked 空不蕴涵 preserved 空）· :806-825（_format_preserved_block）· :985-1002（write 护栏）。
- 模板/规范：docs/harness/templates/TASK_TEMPLATE.md · skill harness-10-task · docs/_tech_graph/LAYER_README.md（G-L 分层）。
- 格式先例：docs/tasks/done/task_hitl_approved_replan_quality.md / task_hitl_auto_resume_claim_race.md（思考轮控制表五列 · ### R0–R5 槽 · 自检结论节）。

## 产出

- docs/tasks/active/task_hitl_n1_locked_branch_inject.md（v0 落稿 · 三闸 pending · graph_change_layer=G-L1 预判 · review_hat=20 · required_invoke_hats=10,20,30,40）。
- 分支 task/hitl-n1-locked-branch-inject（自 master 286d825 新拉 · 未带源分支改动）。

## 关键裁定（10 帽）

1. **真实锚点校正**：委派令引 nodes.py:1172 系旧行号口径（CLOSE 文档同引 :1172-1173）；master 现真值为 app/ops/lg_rag/multi/nodes.py:1173-1174 else 分支 system_content = _build_supervisor_system(catalog_block)——preserved（:1143 无条件算出）在该分支不注入。task 内按真值锚并保留旧引对照。
2. **机理核实**：_unlocked_preserved_rows（:755-778）= hitl_unlocked_ids ∩ 无终态 ∩ 不在 locked——locked 空不蕴涵 preserved 空（40 run1 单写步 approved 形态即实证），故 else 分支确为去盲覆盖缺口；off 模式 preserved 恒空 ⇒ 天然零 diff。
3. **方案开放**：候选 A（分支条件 if locked or preserved 复用 suffix · 10 倾向）/ B（基础模板加槽 v3）/ C（维持现状文档钉案 · 须维护者明确裁定）；最终裁量留 30 实证 + 20 审。
4. **护栏红线照登**：write 护栏（write_replay_guard_skip/replay_of · :985-1002）兜底现状不触碰，TC3 钉 diff 空 + 台账断言存续。
5. **思考轮**：R0–R5 全槽回填，early_stop at R5（缺口机理单一明确 · 锚点全亲读 · 方案开放性显式留 30）。

## 移交/待办

- 三人工闸 pending（HG-TASK-DRAFT / HG-AUDIT-R1 / HG-GRAPH-MODULES）待维护者签；HG-AUDIT-R1 pending 期间 30 拒开工。
- 20-task-audit R1 待派（审查文落盘后人签）。
- 30 首步：锚点行号漂移按实校正 + TC1 红测先行（RED 签名 = prompt 不含保号行）。
- live 前置坑位：NO_PROXY 含 [::1] 须剥（历 task 两度复发）。
