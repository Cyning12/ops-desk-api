# task 审查（R1 · 20-task-audit）：capability manifest 补 output_fields

> **审查对象**：docs/tasks/active/task_lg_rag_capability_output_schema.md（65 行 · HG-AUDIT-R1 approved · 2026-10-27 维护者签收，00 转录）
> **审查人**：Harness 20（task-audit，书面审查）· 2026-10-27
> **审查性质**：只书面核对，不改 task 实质内容；发现问题列出，由维护者/10-task 决定。

## 元信息

- task 分支：task/lg-rag-capability-output-schema
- 根因钉案：2026-10-27 双 run 实证（cb25483697624aafbb1cf864015c3b10 + d3a49527929248cc953b7a5327cae2d0）：planner 声明 produces 猜 `status`（实际 `state`）
- 修复设计三层：①CapabilitySpec 增 `output_fields: tuple[str, ...] = ()`；②defaults.py 五能力 + testing.write.echo 填真值；③catalog 渲染 + 计划期「裁剪+留痕」fail-fast
- **SPEC 缺失说明**：本 task 无独立 SPEC 文档。承仓内先例（task_supervisor_replan_error_feedback 等），以 task 文件自身为审查对象。task 含根因 / 修复设计（范围）/ 非范围 / 验收标准 / failure_paths / 人工闸表，**自足可审**。
- 姊妹 task B（task_lg_rag_gate_produces_unfulfilled.md，闸语义收窄）互指非范围、独立可合，**不在本次审查范围**。

## 结论摘要

| 维度 | 结论 |
|------|------|
| 内容审查 | **BLOCKED · 1 项内容阻塞（B1：范围漏 builtin.v1.yaml 主加载面）** |
| 流程闸 HG-AUDIT-R1 | **approved**（task 表 2026-10-27 维护者签收 m00272，00 转录；本审查文不改动） |

> 流程闸虽 approved，但存在**内容阻塞**：按 Harness 纪律不附 30 Prompt，退回 10-task/维护者修订后复查。

## 逐项核对

### 1. 技术锚点 —— 逐条读码核对（2026-10-27 现码）

| task 声称 | 现码核对 | 结果 |
|---|---|---|
| `CapabilitySpec`（types.py:72）无输出字段**清单**声明 | :72-73 为 dataclass 装饰器+类行；现码 :115 已有 `output_schema: dict | None`（结果契约 P0-1：required JSONPath / min_items / empty_is_suspicious，运行期调用结果校验用），但**无面向 planner 的字段名清单**；且 builtin/testing manifest 五+一枚均未声明 output_schema | ✓ 方向成立，措辞不确（见 N1） |
| catalog 渲染 `_format_capability_catalog`（nodes.py:1219 调用点） | 函数体 nodes.py:103-108，调用点恰为 :1219（supervisor_node 内）；实渲染 `- {id}：{description}（risk={risk_level}）` | ✓ 精确 |
| 根因「可见信息只有能力 id/描述/入参 schema」 | catalog 实际只渲染 id/描述/risk（nodes.py:107），**args_schema 不在 catalog 内**（provider.complete 仅 system+user，无 tools 参数，nodes.py:1258-1264） | ⚠ 不确但不影响根因结论（见 N2） |
| `get_issue_by_number`（lookups.py:69-89）返回 number/title/state/html_url/updated_at/labels/body | lookups.py:69-91 逐 key 对拍：83-91 恰为 7 key `number/title/state/html_url/updated_at/labels/body` | ✓ 精确 |
| defaults.py 五能力 | `_DEFAULT_SPECS`（defaults.py:93-156）恰 5 枚：mock_get_issue_status / mock_get_deploy_info / utc_now_iso / get_issue_by_number / get_pr_by_number | ✓ 精确 |
| testing.write.echo（manifests/testing.v1.yaml） | 文件存在，adapter 指 defaults.testing_write_echo（罐头纯函数，:77-90） | ✓ |
| step_contract.py:176-185 `output_fields()` 不校验纪律 | :176-185 函数体逐字一致；:179-181 docstring 原文「不替模型猜」 | ✓ 精确 |
| step_contract.py:273-279 `collect_values` 只收真实存在字段 | :273-289；:288 `vals = {f: mapping[f] for f in ... if f in mapping}` | ✓ 精确 |

### 2. 范围 / 非范围边界 —— 1 项阻塞

- 非范围 4 条清晰：闸语义收窄归姊妹 task B；前缀不可变/critic 策略不动；MCP/http 远端 schema 不自动抓取（空即退回现状）；不动 args_schema 既有语义。✓
- **B1（阻塞）**：修复设计 2「真值回填」只点名 `defaults.py 五能力 + testing.write.echo（manifests/testing.v1.yaml）`，**漏列 builtin.v1.yaml 主加载面**。现码证据：
  - `ensure_default_capabilities`（defaults.py:159-173）：`if BUILTIN_MANIFEST_PATH.is_file(): load_capability_manifest(...); return` —— **builtin.v1.yaml 存在时是唯一生效路径**，`_DEFAULT_SPECS` 硬编码五能力仅为 YAML 缺失时的回退；
  - `app/ops/capability/__init__.py:106` import 期即调 `ensure_default_capabilities()`；
  - builtin.v1.yaml 现码五枚能力均**无** output 字段声明（:13-113 逐字段读过）。
  - 后果：按 task 字面执行 → 运行期注册表（走 YAML）五能力 `output_fields` 全空 → 空=不校验 → catalog 仍无输出字段信息，**修复在主加载面不生效**，验收 5（40 live 复跑 d3a49）无法收敛；且 testing.v1.yaml:18 纪律「字段族对齐 builtin.v1.yaml 范式（逐字段齐）」会被破坏。
  - 回填位置：修复设计 2「真值回填」节（补 builtin.v1.yaml，defaults.py 回退面同步填保持一致）。

### 3. 验收标准 5 条 —— 可测性核对

1. catalog 渲染含 output_fields + 未声明能力行逐字节零 diff —— **可测**；零 diff 口径与 FP-3 先例一致，且是旧测近零影响的前提（见 N3）。
2. 清单外字段 → 裁剪+留痕断言；清单内 → 原样通过 —— **可测**（纯函数/计划期逻辑，不依赖 LLM）。
3. 防漂移钉：直接调 adapter 对拍 output_fields == 实际返回 keys —— **可测**，是 failure_paths 1 的对应拦截。注意对拍落点须覆盖**实际生效的声明源**（与 B1 联动：builtin.v1.yaml 漏填时对拍 defaults.py 硬编码是绿的、运行期却是空的）。
4. ruff 钉版 0.15.21 + pytest 不引入新红（既有 28 红基线，承 PR #293 裁决）—— **可测**。
5. 40 live 复跑 d3a49 场景（LLM 弹性项，失败须附 run 事件链分析）—— 同先例 P3，弹性措辞**可接受**；但依赖 B1 修复后才有意义。

### 4. failure_paths 3 条 —— 核对

- 声明漂移 → 验收 3 对拍 + B 层闸（PR #293）兜底 ✓；
- MCP/远端无法静态声明 → 空=不校验退回现状，不退化 ✓（现码 MCP adapter 不进 `ensure_default_capabilities`，probes 显式启用，覆盖口径成立）；
- catalog prompt 变长 → 仅字段名清单量级可控 ✓。
- 未列但轻微：裁剪过度（某步声明字段全被裁空 → 退化为空声明=不校验）语义未写明（见 N4）。

### 5. 「裁剪+留痕」vs「拒签」口径 —— 可执行可测试 ✓

- task 明写：声明字段 ∉ 前驱 output_fields（**非空时**）→ 裁剪该字段 + span/事件留痕；不拒整 plan、不替模型改语义；空声明前驱不触发裁剪（承 step_contract.py:176-185 既有纪律）。
- 20-audit 裁定：**裁剪+留痕可执行、可测试（验收 2 两条对称断言），认可该口径**。理由：被裁字段是「前驱绝不可能产出的字段」，裁剪不改变任何可达语义；拒整 plan 会把一枚幻觉字段升级为整 plan 失败，代价倒挂；运行期 B 层闸（PR #293）仍是最终防线，双层不矛盾。
- graph_delta「留痕复用既有 span/事件通道，不新增事件类型」与 nodes.py 既有 `_record_span_metadata` 通道一致 ✓。

### 6. Harness 元信息 —— 13 行全预填 ✓

- task_slug / git_branch / implement_repo / test_strategy(required) / test_strategy_note / code_quality_bar(L2_backend) / graph_change_layer(none) / graph_delta(n/a) / **wiki_delta(n/a)**（承 K4/lint-wiki-delta 首红教训）/ review_hat(20) / required_invoke_hats(10,30,40) / invoke_retention_profile(default) / close_pr_policy(required)。
- graph_change_layer=none 成立：不改模块/路由/事件类型，只增 dataclass 字段 + manifest 键 + 渲染内容。

## 发现的问题

### 阻塞项（退回 10-task/维护者修订）

- **B1（范围漏 builtin.v1.yaml 主加载面）**：见 §2。修复设计 2「真值回填」须补 builtin.v1.yaml（defaults.py 回退面同步）；验收 3 对拍测试的声明源须覆盖运行期实际生效的 manifest。不修补则修复在主路径不生效、验收 5 无法收敛。

### 非阻塞记录项（退回与否由维护者裁定）

- **N1（措辞）**：根因「CapabilitySpec 无输出字段声明」不确——types.py:115 已有 `output_schema`（结果契约 P0-1，运行期调用结果校验：required JSONPath / min_items / empty_is_suspicious）。缺的是**面向 planner 的字段名清单**。新字段 `output_fields` 与既有 `output_schema` 命名相邻，建议 30 实现时在字段注释写明二者分工（planner 声明辅助 vs 运行期结果校验），避免后来者混淆。
- **N2（措辞）**：根因「可见信息只有能力 id/描述/入参 schema」不确——catalog 实渲染仅 id/描述/risk（nodes.py:107），args_schema 不在内。模型信息面比 task 所述更窄，根因方向（无输出字段信息）不受影响。
- **N3（K7 checklist · 已代查）**：本 task 属行为变更类（catalog 渲染 + 计划期裁剪），验收未单列「旧测 grep 影响面」。审查代查：tests/test_lg_rag_supervisor_capability_catalog.py:112 仅子串断言 `"risk=" in system`；test_prompt_assets.py:46-48 / test_prompt_assembly.py:29,38 用字面 catalog_block fixture（不经 `_format_capability_catalog`）；test_hitl_approved_replan_quality.py:209 / test_supervisor_replan_error_feedback.py:253 用 `_fake_caps()` 构造无 output_fields 的 CapabilitySpec → 空声明行逐字节零 diff（验收 1 钉死）。**影响面近零，不因此退回**，记录在案。
- **N4（实现提示）**：裁剪落点未钉（计划期 `_parse_subtasks` / `_stamp_host_plan` 之间），30 自由度可接受；但「某步声明字段全被裁空 → 退化为空声明=不校验」语义未写明，建议 30 在实现注释/测试中注明。
- **N5（记录）**：无独立 SPEC，以 task 自足文件为审查对象（承先例，可接受）。
- **N6（记录）**：验收 5 为 LLM 弹性项（同先例 P3 口径，可接受）；其有效性依赖 B1 修复（40 live 走 builtin.v1.yaml 主加载面）。

## 结论

**内容审查：BLOCKED**（B1 一项阻塞；N1–N6 非阻塞记录项）。

**流程闸：HG-AUDIT-R1 = approved**（task 表为准，本审查文不改动）；但**内容阻塞未清前不附 30 Prompt**。

## 回填清单（→ 10-task / 维护者）

| # | 回填位置（task 小节） | 内容 |
|---|---|---|
| B1 | 修复设计 2「真值回填」 | 补 `manifests/builtin.v1.yaml`（主加载面，ensure_default_capabilities 优先路径）；defaults.py `_DEFAULT_SPECS` 回退面同步填真值保持一致 |
| B1' | 验收标准 3（防漂移钉） | 明确对拍的声明源覆盖运行期实际生效 manifest（builtin.v1.yaml），否则硬编码绿、运行期空 |
| N1 | 修复设计 1（契约类型） | 可选：注明 `output_fields` 与既有 `output_schema`（types.py:115 结果契约 P0-1）分工 |
| N4 | 修复设计 3（fail-fast） | 可选：写明「声明字段全被裁空 → 空声明=不校验」语义 |

回填完成 → 维护者确认（HG-AUDIT-R1 已 approved，无需重签，除非范围实质扩大维护者认为须重审）→ 方可下发 30 Prompt。30 Agent 以 task 表 + 本审查文为准。
