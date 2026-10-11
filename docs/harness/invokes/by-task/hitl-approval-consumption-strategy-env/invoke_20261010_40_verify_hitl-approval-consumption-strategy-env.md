# 40 invoke · hitl-approval-consumption-strategy-env（T3 交付核验 · 独立复跑不采信自报）

> **帽**：40-verify · **task**：docs/tasks/active/task_hitl_approval_consumption_strategy_env.md（T3 · D3 strategy 候选 map env 追加口）
> **核验对象**：cd253f0（config.py env 追加口）· 3c1c9d1（18 枚测试）· 86f7cde（图谱+30 invoke）
> **分支**：task/hitl-approval-consumption（worktree task-hitl-approval-consumption · T1 复核棒并行 · 本帽仅 add 自产文件：本 invoke + task 自检段）
> **日期**：2026-10-10 · **结论**：**PASS（七项核验全绿 · 可进 PR 队列 · 不 push 不开 PR 待维护者令）**
> **环境注记**：worktree 无 .venv · 复跑统一用主 checkout 解释器 /Users/cyning/Desktop/Ops-desk/ops-desk-api/.venv/bin/python（rootdir 为 worktree · 码面以 worktree 为准）

---

## 人工闸终态扫描（40 复验 · 非代签）

| human_gate_id | task 表 status | blocks | 核验 |
|---------------|----------------|--------|------|
| HG-TASK-DRAFT | approved（维护者签 · 00 代录 2026-10-10 · task :38） | 20-R1, 30 | ✅ |
| HG-AUDIT-R1 | approved（R1 PASS · nit×3 非阻塞 · task :39） | 30 | ✅ |
| HG-GRAPH-MODULES | approved（在册 · task :40）· 图谱闸表 00 代录行在案（01_modules.md 行 114） | 30 | ✅ |
| HG-PILOT-OPSDESK-GLAYER | n/a | — | ✅ |

机械辅助复跑：`npx spec-wave verify --target . --task docs/tasks/active/task_hitl_approval_consumption_strategy_env.md` → **VERIFY: PASS · EXIT=0**（本帽亲跑）。

---

## 核验项逐项结论（独立复跑 · 不采信自报）

### 核验 1 · diff 面对拍 ✅

`git diff origin/master --stat -- app/ tests/`（origin/master=4d905e0）：

```
app/ops/strategy/config.py                  |  49 +++++-
tests/test_strategy_env_extra_candidates.py | 260 ++++++++++++++++++++++++++++
2 files changed, 305 insertions(+), 4 deletions(-)
```

- 与 30 自报一致：唯一码改文件 config.py + 新测试文件 · 越界零。
- `git diff origin/master -- app/ops/capability/registry.py app/ops/capability/policy.py app/ops/strategy/builder.py` → **输出为空**（闸链/裁剪面零 diff 实证）。
- config.py diff 全文亲读：覆盖口直返分支（`if CANDIDATE_CAPABILITY_IDS is not None: return list(...)`）一行不动且在 env 逻辑之前短路；`CAPABILITY_ALLOWLIST_BY_KEY`/`MINIMAL_READONLY_CAPABILITY_IDS` 静态成员零改；`_extra_candidate_capability_ids()` 函数内读 os.environ（调用点读取）；追加点=map 解析结果之后（`list(mapped) if mapped is not None else []` 统一走追加 · 含未知 key）；台账仅 extra 非空时 logger.info（count+ids）。**钉死契约七行逐条吻合。**

### 核验 2 · TC1 抽跑 ✅

`SILICONFLOW_API_KEY=dummy-probe pytest tests/test_strategy_env_extra_candidates.py -v` → **18 passed in 0.07s**。

18 枚清单与 30 自报逐一吻合：TC1① 不设 env 字面量对拍 3 枚（supervisor 五枚/default==["utc_now_iso"]/未知 key==[]）+ 全空白=不设 1 枚；TC1② 追加语义 3 枚（map 命中追加且 map 本体不改/未知 key 追加/∩visible 语义不变）；TC1③ 解析参数化 4 枚（strip/连续逗号去空/保序去重/全空白）；TC1④ 覆盖口隔离 1 枚；实操-B 调用点读取 1 枚；TC2 三层 3 枚；TC3 台账双向 2 枚。

### 核验 3 · TC2 层1 选型复检 + registry/policy 零 diff ✅

- **层1 选型充分性（留转 3 复检）**：亲读 tests/test_strategy_env_extra_candidates.py:186-208——`test_tc2_fp5_env_write_id_stripped_by_visible_intersection` 直调真实 `strategy_builder_node`（不打 patch 候选函数），仅 patch 观测侧 `_record_builder_span`/`trace_span`；断言链完整：env id 确进候选层（追加口生效）→ 真实节点输出 `allowed_capability_ids` 不含 → `strategy_builder_stripped_ids == ["testing.write.echo"]` 台账照旧。**裁定：真实 builder 路径选型充分**，与 B1 钉死面（test_allow_tags_does_not_waive_deny_write 等）互补不重复，选型留痕成立。
- 层2（deny 判序 · :211-228）/层3（Policy 写闸 · :231-235）断言形态亲读吻合 registry.py:112-140 / policy.py:96-105 既有语义。
- registry.py / policy.py 对 master diff 空（核验 1 实证 · 机械层闭合）。

### 核验 4 · TC3 工程面 ✅

| 项 | 命令 | 本帽复跑结果 |
|----|------|--------------|
| pytest 全量 | `SILICONFLOW_API_KEY=dummy-probe pytest tests -q --tb=short` | **1679 passed, 1 skipped in 28.56s · EXIT=0**（与 30 自报 1679 passed 一致 · 带 key 直接全绿 · 三连反证口径本次无需启用） |
| ruff 触及路径 | `ruff check app/ops/strategy/config.py tests/test_strategy_env_extra_candidates.py` | **All checks passed! · EXIT=0** |
| ruff 全量基线 | `ruff check app tests` | 55 errors 全部归属既有文件（concise 逐文件核对：config.py 与新测试文件**零命中** · 触及路径零新增成立 · 全量红为 master 既有基线噪音非本 task 引入） |
| graph-compile | `./scripts/graph-compile.sh` | **EXIT=0**（9 md OK · mermaid normalize check ok · 时间戳噪音已 checkout 还原） |
| task lint | `npx spec-wave task lint --file ...` | **LINT: PASS · EXIT=0** |
| lint-wiki-delta | `npx --yes spec-wave@3.0.1 task lint-wiki-delta --target .` | **PASS · scanned 152 · issues 0 · EXIT=0** |

### 核验 5 · B1 八文件亲跑（显式含 eval golden · nit-1）✅

```
SILICONFLOW_API_KEY=dummy-probe pytest tests/test_strategy_builder.py tests/test_strategy_scenario.py \
  tests/test_lg_rag_supervisor_capability_catalog.py tests/test_prompt_assets.py \
  tests/test_prompt_assembly.py tests/test_capability_domain_allowlist.py \
  tests/test_capability_testing_write.py tests/eval/test_eval_agent_golden.py -q
→ 114 passed in 0.35s
```

八文件（B1 六文件 + nit-1 补登 tests/eval/test_eval_agent_golden.py + 依 30 invoke 口径）全绿 · 与 30 自报 114 passed 一致。**nit-1 吸收复核通过。**

### 核验 6 · 闸面终态 ✅

- verify：**EXIT=0 · VERIFY: PASS**（三闸 approved 与 task 表一致）。
- task lint：**PASS · EXIT=0**；lint-wiki-delta：**PASS · issues 0**。
- 图谱 lg_rag 行实证（01_modules.md 行 35 亲读）：「路径覆盖补记」strategy 段内含 **2026-10-10（hitl-approval-consumption-strategy-env · T3）** 备注，七要素（env 形态/零 diff/含未知 key/覆盖口隔离/调用点读取/台账/下游不动）全在案；嵌于行原文（含「Builder/Intent/Critic」片段）之内——**nit-2「以图谱原文为准实读」吸收复核通过**；闸表 00 代录行（行 114）在案。
- graph-compile EXIT=0 复核在案；未新增一级模块/跨模块边。

### 核验 7 · task 自检结论段回填 ✅

task :209「自检结论（执行者）」段原为空占位「（30/40 回填）」——本帽已回填 40 核验结论（docs(task) commit 随本 invoke 一并落盘）。

---

## nit×3 吸收复核（R1 §十一 · 留 40 项）

| nit | 30 处置 | 40 复核 |
|-----|---------|---------|
| nit-1 B1 漏登 eval golden 行 | 亲跑显式含 tests/eval/test_eval_agent_golden.py | ✅ 本帽亲跑八文件 114 passed 含其内（核验 5） |
| nit-2 图谱行引文为转述 | 回写以 01_modules.md:35 原文实读 | ✅ 图谱行 35 亲读 · 备注嵌于原文 strategy 段（核验 6） |
| nit-3 TC1① 字面量断言形态 | 三组字面期望 list + 不设/全空白两态相等 | ✅ 18 枚全绿 · 断言形态与 R1 §四建议一致（核验 2） |

---

## 留转清单复核（30 invoke §留转 40 · 六条）

| # | 留转项 | 40 处置 |
|---|--------|---------|
| 1 | 全量 pytest 带 SILICONFLOW_API_KEY | ✅ 已带 dummy-probe 复跑 · 1679 passed · 未触发环境性红 |
| 2 | B1 亲跑显式含 eval golden | ✅ 核验 5 落实 |
| 3 | TC2 层1 选型复检 | ✅ 核验 3 裁定充分 |
| 4 | 分支字段差异（task 表 task/hitl-approval-consumption-strategy-env vs 实际 task/hitl-approval-consumption） | **存续 · 转 PR 队列前由 00/维护者裁定**（非本帽权限 · 不阻塞验收） |
| 5 | 图谱闸表 00 ratify | ✅ 行 114 在案 · 00 ratify 复核面已具备 |
| 6 | 不 push 不开 PR | ✅ 本帽遵守 · 待维护者令 |

---

## 总结论

**PASS**。30 交付（cd253f0 / 3c1c9d1 / 86f7cde）经独立复跑核验：改动面与钉死契约逐条吻合零越界 · TC1–TC3 全机断绿 · B1 八文件亲跑绿 · 双 lint + verify + graph-compile 全 EXIT=0 · 图谱回写实证在案 · nit×3 吸收复核通过 · 无造假迹象。**可进 PR 队列**（留转 4 分支字段差异随 PR 流程由 00/维护者裁定 · 不 push 不开 PR 待维护者令）。
