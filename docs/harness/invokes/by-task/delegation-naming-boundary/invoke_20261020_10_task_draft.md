# invoke：delegation-naming-boundary · 10_task_draft · 2026-10-20

- **hat**：10-task（task 起草）
- **task**：`docs/tasks/active/task_delegation_naming_boundary.md`（draft v0.1 · 187 行）
- **建议序**：4/5（query-coref-rewrite 已合 PR #284 · memory-injection-consumer 已合 PR #285 · scenario-stage-rewire 已合 PR #286 → 本 task）
- **分支**：`docs/task-delegation-naming-boundary`（自 master `31924af` 切出）；30 实施分支 `task/delegation-naming-boundary` 另行切
- **写入面**：仅 task 文件 + 本 invoke（两处分 · 零 `app/` 改码 · 未改 SPEC · 未代签任何闸）

## 一、签收与审查依据

| 依据 | 结论 |
|---|---|
| `docs/spec/delegation-naming-boundary/SPEC-delegation-naming-boundary_v0.md` | v0.1 · signed · HG-SPEC-SIGNOFF=approved（2026-10-19 维护者）· D1 正名 / D2 护栏解耦默认开 / D3 图谱写实 |
| `docs/harness/reviews/spec_delegation-naming-boundary_audit_R1_20261019.md` | R1 conditional_pass（阻塞 0 · 锚点 8/9）→ v0.1 闭合 → R2 pass；N3/N5/N6/N7 移交项全部吸收（见第二节） |
| `docs/spec/host-v1-delegation-token/SPEC-host-v1-delegation-token_v0.md` §4 Q3 | 不新增一级模块裁定（图谱义务=capability/lg_rag 行内备注 · 不增 implementedBy） |

## 二、N3/N5/N6/N7 吸收位置索引（task 行号 · v0.1）

| 移交项 | 吸收落点 |
|---|---|
| N3（护栏门控真锚点） | task D2 门控真锚点表——master `31924af` 亲读校正为**两处真门控** `nodes.py:903`/`:931`（+ 关联行 :930/:987-988）；R1 第三处 `:970` 系签发审批门（`_delegation_issue_block_reason`）同形 if 行误并，**不在解耦面**，task 显式注明（`:1271` 同理不动） |
| N5（上游名实审查报告未落盘） | task 非范围：不补落盘——SPEC §1 转述为 10 项超名清单唯一真值载体（承 R1 N5 备选口径） |
| N6（worktree 脏改动声明不可证） | task 非范围：master 实证 `tests/test_lg_rag_supervisor_capability_catalog.py:15` 单次 import，task 不依赖、不处置 |
| N7（SPEC :159 第 4 处 Q3 dangling 引用） | task 非范围：v0.1 后仍在、非阻塞；task 不代改 SPEC，移交维护者择机闭合（40 复核） |

## 三、亲读复核实录（master `31924af` · 行号 30 按实校正）

| 锚点 | 实录 |
|---|---|
| `app/ops/capability/delegation.py` | :479-505 `def auto_approve_ok(specs, *, effective_scope)` 三条件纯函数（D1 改名唯一定义点） |
| `app/ops/lg_rag/multi/nodes.py` | :408 docstring 提及 · :420 唯一调用 `dl.auto_approve_ok([entry[0]], effective_scope=scope)` · **:903 条件建索引**（`if _delegation_active() else {}`）· **:931 guard-skip 块头**（块内 :932 write_key · :933-963 异 sid 命中 · **:941-942 台账键 `write_replay_guard_skip`/`replay_of` 金样钩子** · :964-967 同批双胞胎挂起）· :930 `write_key = None` 初始化 · :987-988 首发登记（门控块外 · write_key 惰性控）· :970 签发审批门（**非解耦面**）· :1271 delegation 耦合（不动） |
| `tests/test_capability_delegation.py` | :338-360 `test_auto_approve_*` 三例（:338/:352/:359）+ 调用 :340/:354/:360（改名同步面） |
| `docs/_tech_graph/l1/01_modules.md` | capability 行 :34（无 delegation 独立行 · 承 Q3）· lg_rag 行 :35 T1 备注含「auto_approve_ok 纯函数零 IO」字样 · 闸登记表先例 :110-128 |
| `docs/guides/GUIDE_env_inventory_v1.md` | lg_rag 段在册（:35 `LG_RAG_VISIBILITY_SCENARIO_MODE` 先例行）；delegation 系 env 未登记在先，新键补登记落此 |
| 蓝本 | `tests/test_memory_injection_consumer.py:608-632` _resolve_base 三级 + :635-660 三路 diff/untracked/第四态可审计 skip（:648-657）+ banned 置尾（:659-660）· `tests/test_strategy_scenario.py:451-536` _WAVE_TIP 第四态波次判定（_WAVE_TIP 已钉 `63bad3d`） |

## 四、开放点收口（task 裁定）

| 开放点 | 裁定 |
|---|---|
| 新名 | `issuance_policy_allows`（承 SPEC D1 首选 · 30 不另择 · 偏离回炉 10/20） |
| 开关键名/形态 | `LG_RAG_WRITE_REPLAY_GUARD_ENABLED` 布尔 · **默认 true=开** · 非法值回退开（承 `SESSION_SUMMARY_ENABLED` 解析先例 · 键名对齐台账 `write_replay_guard_*`） |
| 改名兼容处置 | 承 SPEC：**直接改名不留别名 · 无 deprecation 过渡**（TC1 零残留 grep 牙） |

## 五、产出与闸态

| 产出 | 状态 |
|---|---|
| `docs/tasks/active/task_delegation_naming_boundary.md` | draft v0.1 · 191 行 · `npx dsh-coding-kit task lint --file` **PASS**（仅 W5 思考轮槽位 warn-only 过渡提醒 · E 零） |
| HG-SPEC-SIGNOFF | approved（2026-10-19 维护者） |
| HG-AUDIT-R1 | **pending**（blocks 30 · 落闸在 20-task-audit 后 00 代签授权在） |
| HG-GRAPH-MODULES | approved（graph_change_layer=none 预期口径：行内备注回写 · 不增行/边/implementedBy/路由/表/SSE 事件类型 · 越出回炉补签） |
