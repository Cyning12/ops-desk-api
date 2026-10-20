# invoke：scenario-stage-rewire · 10_task_draft · 2026-10-20

- **hat**：10-task（task 起草）
- **task**：`docs/tasks/active/task_scenario_stage_rewire.md`（draft v0.1 · 188 行）
- **建议序**：3/5（query-coref-rewrite 已合 PR #284 · memory-injection-consumer 已合 PR #285 → 本 task）
- **分支**：`docs/task-scenario-stage-rewire`（自 master `51e75c9` 切出）；30 实施分支 `task/scenario-stage-rewire` 另行切
- **写入面**：仅 task 文件 + 本 invoke（两处分 · 零 `app/` 改码 · 未改 SPEC · 未代签任何闸）

## 一、签收与审查依据

| 依据 | 结论 |
|---|---|
| `docs/spec/scenario-stage-rewire/SPEC-scenario-stage-rewire_v0.md` | v0.1 · signed · HG-SPEC-SIGNOFF=approved（2026-10-19 维护者）· 裁定分支 **(a) 摘除** |
| `docs/harness/reviews/spec_scenario-stage-rewire_audit_R1_20261019.md` | R1 conditional_pass（B1=env 键误写已修正为 LG_RAG_VISIBILITY_SCENARIO_MODE）→ v0.1 闭合 → R2 pass |

## 二、N1–N4 吸收位置索引（task 行号 · v0.1）

| 移交项 | 吸收落点 |
|---|---|
| N1（图谱无 strategy 独立行 · lg_rag 行 :35 段） | task :22（graph_delta_note 口径裁定）+ :71（### D4 图谱 · lg_rag 行 strategy 段备注追加，不新行） |
| N2（tests/test_strategy_scenario.py 删改口径） | task :75（### D5 旧测处置 · 删六项/改写四项/保留 S1–S5+smoke/新增 env 失效断言）+ :121（TC7 机断） |
| N3（sse_stream.py:64 死映射登记） | task :82（### D6 登记不动 · 含 intent.py:94 留尸口径）+ :123（TC9 引用清单落 invoke） |
| N4（invoke 目录补建） | task :27（invoke_retention_profile）+ 本文件（目录占位） |

## 三、亲读复核实录（master `51e75c9` · 行号 30 按实校正）

| 锚点 | 实录 |
|---|---|
| `app/ops/strategy/builder.py` | :17-20 scenario 三件 import · :111-128 `_apply_scenario_stage` 本体（:118 `scenario_mode()` 真读取点）· :149/:155-157 过期 docstring/两阶段注释 · :158 唯一调用点 · :167 `build_allowlist_from_candidates(candidates, visible_ids=visible_ids)` |
| `app/ops/strategy/scenario.py`（128 行） | :38 `ENV_SCENARIO_MODE="LG_RAG_VISIBILITY_SCENARIO_MODE"` · :49-52 `scenario_mode()`（:51 os.environ.get）· :55-96 `scenario_trim` S1–S5（:71-75 无 intent 恒短路 `return specs, []`）· :99-128 `audit_scenario_stripped` |
| `app/ops/strategy/intent.py` | :94 `return {**bump, "intent": intent, "intent_fallback": fallback}` 唯一写入方 · 未挂载（multi/graph.py · lg_rag/graph.py 均无 intent_node） |
| `app/ops/lg_rag/sse_stream.py` | :62-66 `_ROLE_ALIAS`（:64 `"intent_node": "intent"` 死映射 · N3 登记不动） |
| `app/ops/lg_rag/multi/nodes.py` / `multi/graph.py` | nodes.py:1267 注释「Builder 两阶段（基线→scenario_trim）收窄 allowlist」摘除后过期需改写（仅注释行）；graph.py:82-83 注释已述直接求交口径不动 |
| `tests/test_strategy_scenario.py`（395 行） | :34-35 import · :76-169 S1–S5 纯函数用例（保留）· :189-256 env 三档+台账六用例（删）· :259-270 TC6 短路断言（改写）· :273-300/:308-338/:341-378 三项 env 耦合用例（改写去耦合）· :386-395 计时 smoke（保留） |
| `docs/_tech_graph/l1/01_modules.md` | :35 lg_rag 行「路径覆盖补记」strategy 段 + host-v1-visibility-scenario-policy V1-B 备注（图谱同步落点）· HG-GRAPH-MODULES approved 在册 |
| `docs/guides/GUIDE_env_inventory_v1.md` | :35 LG_RAG_VISIBILITY_SCENARIO_MODE 行在册（deprecated 标注落点） |
| `tests/test_memory_injection_consumer.py` | :585-609 `_resolve_base` 三级探测 + :612-627 diff 白名单断言（TC8 实现蓝本 · 吸收 #2 教训） |

## 四、产出与闸态

- 产出：`docs/tasks/active/task_scenario_stage_rewire.md`（188 行 · `npx dsh-coding-kit task lint` **PASS**）+ 本 invoke
- 闸态：HG-SPEC-SIGNOFF=**approved**（2026-10-19）· HG-AUDIT-R1=**pending**（blocks 30 · 维护者已授权 00 代签，落闸动作在 20-task-audit 之后）· HG-GRAPH-MODULES=**approved**（在册 · none 预期不再签 · 越出回炉补签）
- 下一步：20-task-audit R1 书面审 → HG-AUDIT-R1 落签（00 代签）→ 30 开工分支 `task/scenario-stage-rewire`
