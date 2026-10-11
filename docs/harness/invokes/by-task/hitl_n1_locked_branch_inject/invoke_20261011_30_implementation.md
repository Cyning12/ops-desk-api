# invoke · 30 implementation · hitl-n1-locked-branch-inject

> 帽：30 implementation · 分支：task/hitl-n1-locked-branch-inject · 日期：2026-10-11
> task：docs/tasks/active/task_hitl_n1_locked_branch_inject.md（唯一真值）

## GATE_VERIFY（开工首步 · 首输出闸扫描）

- 读 FRAGMENT_30_gate_verify_v1_zh.md → 跑 `npx spec-wave verify --target . --task docs/tasks/active/task_hitl_n1_locked_branch_inject.md`（重定向 /tmp/verify30_hitl_n1_locked_branch_inject.log 取真码）→ **EXIT=0 · VERIFY: PASS**。
- 闸表读值（task §人工闸 真值）：HG-TASK-DRAFT=approved · HG-AUDIT-R1=approved · HG-GRAPH-MODULES=approved（均 00 代录 授权 m00106）；R1 审查文 docs/harness/reviews/task_hitl_n1_locked_branch_inject_audit_R1_20261011.md 在案。
- 分支 = task/hitl-n1-locked-branch-inject（base master 286d825 + 3 枚纯 docs commit）· 开工时工作树干净。

## 锚点亲读核真（必读列表第 1 项 · 行号逐字复核无漂移）

- nodes.py:1141 `locked = _locked_prefix(state)`（:694-711 成功终态前缀 − hitl_unlocked_ids）。
- nodes.py:1143 `preserved = _unlocked_preserved_rows(state, locked)` **无条件算出**（:755-778 hitl_unlocked_ids ∩ 无终态 ∩ 不在 locked）——locked 空不蕴涵 preserved 空。
- nodes.py:1161-1172 `if locked:` 走 suffix v2 注入（preserved_block 消费点）。
- nodes.py:1173-1174 `else:` 基础 prompt —— **preserved 算出但丢弃**（N1 缺口原位）。
- :803 `_format_prefix_block([])` 返「（无）」字面（方案 A 退化路径已处理）。
- :806-825 `_format_preserved_block` 注入文含「切勿为同一目的再规划新步骤或孪生步骤」。
- :985-1002 write 护栏段（write_replay_guard_skip/replay_of）——本 task 零触碰（交付 diff 单 hunk 实证）。
- :1206 fallback `if locked:` 与 :1242 `_stamp_host_plan(..., preserved=preserved)` 无条件落位——方案 A 不波及（locked 空 + LLM 失败仍走单 rag fallback，与 master 同形）。

## 方案裁定：A（实证后定案 · task 开放性条款履行）

- **A 当选**：分支条件 `if locked:` → `if locked or preserved:`（一行 + 注释块）。复用已验收的 suffix v2 `$preserved_block` 注入面（PR #233）· 零模板资产变动 · 最小 diff。
- **B 排除**：`_build_supervisor_system` 加槽 = 模板 v2→v3 + assets README + test_prompt_assets.py 三连动（R2 残险「B 案牵连面未实估」实估坐实：面大且无额外收益）。
- **C 排除**：task 目标钉死「保号行名单对 supervisor LLM 可见（可机断）」，维持现状不达标；且 C 须维护者明确裁定、不默许。
- **FP-2 评估照登**：注入文逐行摘要（sid+type+input+tool · 无截断）与 locked 非空已验收路径同口径；locked 空分支不新增膨胀面。限量/截断属新策略，非本 task 范围，不顺势加。

## RED → GREEN 时序证据（git 历史可查）

- **RED**：commit 97bb7b9 `test(hitl-n1-locked-branch-inject): TC1-N1 红测先行 + TC2-b 零diff钉死`（仅测试文件 +66 行）。
  - `test_tc1_locked_empty_preserved_injected_into_prompt` **FAILED**：AssertionError「locked 空分支保号行（approved 待重跑）须注入 prompt」· 实测 prompt 为基础模板且不含 s1（run-2a9a8c60:1）——与 N1 缺口同形签名（/tmp/red_n1.log · EXIT=1）。
  - `test_tc2_locked_empty_preserved_empty_prompt_zero_diff` PASSED（零 diff 钉死先行在位）。
- **GREEN**：实现 commit（本 invoke 同批）后 `pytest tests/test_hitl_approved_replan_quality.py tests/test_prompt_assets.py` → **47 passed · EXIT=0**（/tmp/green_n1.log）。

## 验收 TC 对照（30 帽面 · TC5 属 40 不在本棒）

- **TC1** ✅ RED（97bb7b9）→ GREEN（实现 commit）时序在 git 历史；prompt 含 preserved 行（sid + 钉死措辞）+ 落位契约 [s1, :2] 断言。
- **TC2** ✅ (a) TC1-N1 注入断言绿；(b) TC2-b 逐字节零 diff 断言绿（`system_prompt == _build_supervisor_system(_format_capability_catalog(_fake_caps()))`）；(c) 既有 TC1-b/TC2 组六枚 + test_prompt_assets.py 原样绿（47 passed 零新增红）。
- **TC3** ✅ 既有 TC2 组六枚原样绿（护栏存续）；nodes.py 交付 diff 为单 hunk（:1158-1170 分支条件 + 注释），护栏段 :985-1002 diff 空。
- **TC4** ✅ 全量对拍：baseline（改动前 · 码面=master）7 failed/1782 passed/1 skipped（capability_lookups×3 + test_hitl asyncpg×1 + lg_rag_multi×1 + multi_replica_dualproc×2 · 环境性钉案同名同因）；现状 9 failed/1782 passed/1 skipped——**+2 枚 test_memory_purge_db 经隔离复跑 7 passed 证为真 DB 环境性 flake**（stderr asyncpg「attached to a different loop」连接池跨 loop 污染 · 与基线 asyncpg 红同族 · 非码因）；ruff 触及路径对拍 master 同 6 枚既有（逐枚同源）· 零新增；`./scripts/graph-compile.sh` EXIT=0（shared/graph.json 再生噪音 git checkout 还原）。

## 图谱回写（HG-GRAPH-MODULES 义务履行）

docs/_tech_graph/l1/01_modules.md 两处（手工真值 · 无 01_modules.graph.yaml 源）：
1. `lg_rag` 行备注追加「hitl-n1-locked-branch-inject（2026-10-11 · N1 收口）」条目（分支条件改动 · 注入面 · 零 diff 钉死 · 护栏零触碰 · 不新增一级模块/implementedBy）。
2. HG-GRAPH-MODULES 台账表追加本 task 回写行（00 代录 授权 m00106 · 30 回写本文）。

## 偏离 task 记录

- **零范围偏离**。commit 前缀：RED 测试 commit 用 `test(...)` 而非 feat/fix——30 纪律「feat/fix 前缀」指实现 commit；测试先行 commit 用 test 前缀为 conventional 诚实标注（实现 commit 仍 fix 前缀），留痕备查。
- NO_PROXY 含 [::1] 坑位：本棒纯单测无 live 触达（TC5 属 40），未触发；坑位已悉（live 前置先剥 no_proxy + 核容器归属）。

## 遗留

- TC5 live 行为对照属 40 帽（N2 观测口径限制存续 · 间接实证照登）。
- 环境性红基线（7 枚钉案 + memory_purge_db 偶发 flake 族）不修（task 明示勿当回归修）。
- FP-2 超大 preserved 集合限量/截断策略未定（现口径与已验收面一致 · 如后续需限量另立案）。
