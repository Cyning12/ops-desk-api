---
title: task · P2c-T1 · planner 工具感知硬化 + 选定率回归基线
---

# task · P2c-T1 · planner 工具感知硬化 + 选定率回归基线

> **状态**：`active`（2026-11-17 落卡 · 夜间自动执行波）
> **来源**：P2b/P2b-skill 验证轮登记缺口（workspace docs/01-scope/03-general-agent/12-p2b-verification.md §5-1/§5-2 · 13-p2b-skill-verification.md §7-2）· 授权 issue Cyning12/ops-desk-workspace#23（m03064/m03734 夜间授权 · 委派书 p2c-t1-planner-tool-awareness）

## Harness 元信息

| 键 | 值 |
|----|----|
| **task_slug** | p2c-t1-planner-tool-awareness |
| base | b8d11262 |
| 关联 issue | issue Cyning12/ops-desk-workspace#23（授权真源）· workspace 12 文 §5-1/§5-2 + 13 文 §7-2（需求真源） |
| 关联 PR | feat 本 PR · close chore PR（收口登记） |
| **wiki_delta** | `n/a` |
| **wiki_delta_note** | 本仓未启用 WikiTrack；本波为 lg_rag supervisor prompt 面小修 + 图谱登记 |
| graph_change_layer | G-L1（01_modules.md lg_rag 行 p2c-t1 备注 + HG-GRAPH-MODULES 签收行） |
| review_hat | 20（R1 审查文已落盘 · GO） |

### 人工闸

| human_gate_id | status | blocks_hats | 说明 |
|---------------|--------|-------------|------|
| HG-TASK-DRAFT | approved | 30 | approved 2026-11-17 · 授权 issue Cyning12/ops-desk-workspace#23 m03064/m03734（夜间授权）+ 委派书 p2c-t1-planner-tool-awareness 为唯一范围真源 |
| HG-AUDIT-R1 | approved | 30 | approved 2026-11-17 · 同上授权 + R1 审查文 docs/harness/reviews/task_p2c_t1_planner_tool_awareness_audit_R1_20261117.md（GO） |
| HG-GRAPH-MODULES | approved | 30 | approved 2026-11-17 · 同上授权（lg_rag 行 p2c-t1 备注属图谱登记义务 · 随 30 交付回填） |

## 背景

P2b 验证轮（workspace 12 文 §5-1）实测：泛化中文问法（不显式点名 capability）时 planner 退化 rag 直答、不选工具——hit-echo 首跑未命中，显式命名 capability 后 3/3 命中。§5-2 登记 tool shadowing 残余：Host 侧重写 when_to_use 已部分覆盖，但 translator description 原样透传占比高（~100%，仅追加 simplification note）。13 文 §7-2 实测域外 query（数学题）首轮 supervisor 输出 `{"subtasks": []}` 判非法、`LG_RAG_SUPERVISOR_PLAN_ON_FAIL` blank 时 fail-closed 停图，复跑正常——硬化设计不得恶化域外 query（负例必须保住 fail-closed 或 rag 直答的正确行为）。

退化机理（勘察结论）：supervisor system 模板 `app/ops/prompts/assets/lg_rag.supervisor.system.md` v3 只说明 type=rag|extract|tool 三种类型 + 注入 `$catalog_block`（「可用工具（Capability 目录）」），并钉「单一简单问题就只给一个 rag 子任务」——全 prompt 无任何「何时该选工具」的正向引导、无 few-shot、无负例引导；catalog 行仅被动罗列 `- {id}：{description}（risk/output_fields/args_schema）`。模型在无点名 id 的泛化问法下缺「按描述匹配选工具」的决策锚，叠加「简单问题只给 rag」的单边引导，退化 rag 直答为省力解。

## 范围

1. **硬化设计**（最小有效组合 · 委派书候选 ①③ · 不突破 §6.5 catalog ≤6000 预算锚）：
   - `app/ops/lg_rag/multi/nodes.py`：新增 `_TOOL_AWARENESS_GUIDANCE` 静态常量（选择原则引导语 + 1 条泛化问法 JSON few-shot + rag 兜底从句——兜底从句明确「仅当目录中没有工具能覆盖该问题时才纯 rag」，保 13 §7-2 域外负例）；新增 `_build_catalog_block(caps)` 为 supervisor catalog 块唯一装配点：非空 caps 节首注入引导语，空 caps 原样返回空目录占位（零追加 · 承 `_format_capability_catalog` 空集口径）；`supervisor_node` catalog_block 装配改调 `_build_catalog_block`（suffix/base 两路共用自动覆盖）；`_format_capability_catalog` 本体零改（精确相等断言零 diff 口径不动 · 模板资产 v3 不动，注入在装配层）。
   - 引导语为静态恒定文本、不含任何 capability id（窄 allowlist 场景零泄漏）。
2. **回归基线**（mock LLM 驱动 planner 基建扩 `tests/test_lg_rag_supervisor_capability_catalog.py`）：
   - catalog 含工具时 mock LLM 捕获的 system 断言含引导语标记 + few-shot 标记 + rag 兜底从句；catalog 空时 `_build_catalog_block([])` 零追加（不含引导语）；
   - 注入后行渲染保持（block 以原 `_format_capability_catalog` 输出结尾）；
   - 引导语静态文本不含任何默认 registry capability id（泄漏守卫）；
   - 预算锚断言 `len(_build_catalog_block(默认可见目录))` ≤6000（§6.5）；
   - 窄 allowlist（仅 utc_now_iso）下 system 含引导语且不含被隐藏工具 id。
3. **FP 迁移**：`tests/test_hitl_approved_replan_quality.py` 与 `tests/test_supervisor_replan_error_feedback.py` 两处逐字节预期构造从 `_format_capability_catalog(_fake_caps())` 改走同一装配点 `_build_catalog_block(_fake_caps())`（prompt 文本变更为本波标的 · intentional behavior change 登记）。
4. **测试**：新增用例真 PG 绿（postgresql+asyncpg://ops:ops_password@localhost:5432/opsdesk_test · 五键 blank 前缀）；目标回归（catalog/panel/translator/output_fields/args_schema/FP 两文件）零红；全量 pytest 绿（环境性红与 base b8d11262 同路径基线逐签对照 · CI 终裁）；`ruff check app tests` 绿。
5. **图谱**：`docs/_tech_graph/l1/01_modules.md` lg_rag 行（:35）补 p2c-t1 备注（supervisor catalog 节首引导语 + few-shot · 装配点 `_build_catalog_block`）+ HG-GRAPH-MODULES 签收行（承 :41-:46 先例）。
6. **落盘**：registry entry（status=active → close 波 closed 钉 wave_tip）· invokes by-task/p2c-t1-planner-tool-awareness/{10,30,40,50} · R1 审查文 · task 档 active→done。

## 非范围

- 不做真 LLM 冒烟（真选定率冒烟归 T2 · 本波交付 mock 面回归基线）。
- 不动 translator 安全语义（M1-M3 fail-closed 词表不变）；Host 侧 description 首句二次蒸馏本波不做（裁定见 R2/R3：透传 ~100% 属实，但重写同源不可信文本无法语义中和投毒、蒸馏增预算无选定率收益 · 真缓解属 server 向翻译器策略，12 §5-4 已登记 server 向单独立项）。
- 不动 `_format_capability_catalog` 行渲染与 mcp 节引导语（精确相等断言零 diff 口径保持）；不动模板资产 `lg_rag.supervisor.system.md` v3 / suffix v2（注入在装配层 · 模板零 bump）。
- 不动 `LG_RAG_SUPERVISOR_PLAN_ON_FAIL` fail-closed 解析面与执行路径（空 plan 判非法语义保持）。
- 不引新依赖；不碰 alembic/ · scripts/ · skill_registry/（skill 闸 off 态 `_append_skill_catalog` 零调用零 diff 口径保持）。

## 失败路径

- 预算锚突破：默认 registry supervisor 可见 9 条目录实测 3916 字符，引导语+few-shot 注入后须 ≤6000（§6.5 锚）——由预算锚断言守；若引导语膨胀超锚则锚内重分配（压缩行渲染）为预案。
- 引导语含 capability id 泄漏：窄 allowlist 场景引导语若含默认 id 会泄漏被隐藏工具——引导语静态恒定零 id，由泄漏守卫断言守。
- few-shot 诱导域外 query 过度选工具（13 §7-2 负例恶化）：引导语含 rag 兜底从句（「仅当目录中没有工具能覆盖该问题时才纯 rag」），由兜底从句断言结构性守；fail-closed 解析面零改。
- FP 两测试红：prompt 文本变更咬逐字节断言——预期构造迁移同一装配点 `_build_catalog_block`（单一真源防漂移）。
- skill 闸 on 态叠加：`_append_skill_catalog` 在 `_build_catalog_block` 输出尾部追加，合并预算 ≤10000 锚（capability ≤6000 内引导语已计入）。
- 并行 agent 撞 registry.yaml / 01_modules.md 同区冲突 → rebase origin/master 保留双方 entry 手动解，冲突块如实登记。
- 仓根 .env 经 tests/test_check_vector_waterline.py 裸 load_dotenv 渗入收集期致全量 pytest 环境性红 → 与 base b8d11262 同路径基线逐签对照登记，CI 终裁。
- 脏树期 wave_gate_registry 红为结构性常态（委派书钉明）。

## 验收标准

- [x] 引导语注入：catalog 含工具时 mock LLM 捕获的 supervisor system 含引导语标记 + few-shot 标记 + rag 兜底从句（新断言）
- [x] 空目录零追加：`_build_catalog_block([])` 返回空目录占位且不含引导语（新断言 · catalog 空时不含）
- [x] 行渲染零 diff：`_format_capability_catalog` 本体零改（test_capability_output_fields / test_fix_planner_args_schema / test_capability_panel_tools / test_capability_mcp_translator 精确相等与子串断言全绿）
- [x] 窄 allowlist 零泄漏：引导语静态文本不含任何默认 registry capability id（新断言）；窄 allowlist（utc_now_iso）下 system 含引导语且不含被隐藏工具（新断言）
- [x] 预算锚：`len(_build_catalog_block(默认可见目录))` ≤6000（§6.5 · 新断言）
- [x] FP 迁移：两处逐字节预期构造走 `_build_catalog_block` 后全绿（intentional behavior change 登记）
- [x] 目标回归零红；全量 pytest 绿（环境性红逐签对照 base b8d11262 · CI 终裁）；`ruff check app tests` 绿
- [x] 01_modules.md lg_rag 行 p2c-t1 备注 + HG-GRAPH-MODULES 签收行
- [x] registry entry active · invokes 四件 · R1 审查文 · spec-wave task lint PASS

### 自检结论

验收 9 条全绿（2026-11-17 · 40 收口）：

1. **引导语注入**：mock LLM 捕获 supervisor system 含「工具选择原则」+ few-shot「现在几点了」+ rag 兜底从句（`test_supervisor_prompt_contains_tool_awareness_guidance` 绿）。
2. **空目录零追加**：`_build_catalog_block([])` 返回「（当前无可用 local_fn 工具）」原样不含引导语（`test_build_catalog_block_empty_no_guidance` 绿）。
3. **行渲染零 diff**：`_format_capability_catalog` 本体零改——精确相等断言（test_capability_output_fields · test_fix_planner_args_schema）与子串断言（test_capability_panel_tools · test_capability_mcp_translator）全绿。
4. **零泄漏**：引导语静态文本对默认 registry 全 id 扫描零命中（`test_tool_awareness_guidance_no_capability_id_leak`）；窄 allowlist=[`local.time.utc_now_iso`] 下 system 含引导语且不含被隐藏工具（`test_supervisor_restricted_allowlist_guidance_no_leak`）。
5. **预算锚**：默认 9 条目录 `_build_catalog_block` 全长 4186 ≤6000（`test_tool_awareness_catalog_budget_anchor` · §6.5 锚）。
6. **FP 迁移**：test_hitl_approved_replan_quality / test_supervisor_replan_error_feedback 预期构造改走 `_build_catalog_block(_fake_caps())` 全绿（intentional behavior change 登记于下）。
7. **目标回归七件 103 passed 零红 · 全量 2430 passed/26 failed/3 skipped 与 base b8d11262 同路径基线（2427/25/1）逐签对照**（明细见下）· `ruff check app tests` 绿。
8. **图谱两件**：01_modules.md lg_rag 行 p2c-t1 备注 + HG-GRAPH-MODULES 签收行（承 :46 先例）。
9. **过闸四件**：registry entry active · invokes {10,30,40}（50 归 CLOSE）· R1 审查文 GO · `npx --yes spec-wave@3.5.0 task lint` PASS。

全量失败 26 件逐签：25 件与 base b8d11262 同路径基线**逐件一致**（`/tmp/opsdesk-rfc/p2c-t1-pytest-base.log` vs `p2c-t1-pytest-full-2.log` diff 空集）——全量期并发/注册表污染型环境性红，目标七件窗口与本波新断言全绿；唯 +1 件 `test_wave_gate_registry` 为脏树期结构性红（在途 nodes.py 只在本波 active entry 白名单 → 其余 closed 波报禁改面触碰 · 委派书钉明常态 · 提交后闭窗复跑确认 + CI 终裁）。skipped +2 为 TC8/TC5 白名单闸因本波在途文件入其越界清单转 skip 分支（结构性 · 合并后回常）。

## 必读列表

- 需求真源：`../ops-desk-workspace/docs/01-scope/03-general-agent/12-p2b-verification.md` §5-1（hit-echo 首跑未命中 · 显式命名后 3/3）· §5-2（tool shadowing 残余）· `13-p2b-skill-verification.md` §7-2（域外 query 空 plan fail-closed）
- 代码锚：`app/ops/lg_rag/multi/nodes.py:108-150`（`_format_capability_catalog` · `_MCP_CATALOG_GUIDANCE`）· `:152-191`（`_append_skill_catalog` · `_build_supervisor_system/suffix`）· `:1599-1655`（`supervisor_node` catalog 装配）· `app/ops/prompts/assets/lg_rag.supervisor.system.md`（v3 模板 · `$catalog_block` 占位）· `app/ops/capability/mcp/translator.py:349-355/:370`（M3 when_to_use 合成 · description 透传）
- 预算锚：`app/ops/skill_registry/loader.py:41-42` · `registry.py:41`（§6.5 合并预算 capability ≤6000 + skill ≤4000 ≤10000）· `tests/test_capability_mcp_translator.py:620-640`（≤6000 CI 锚先例）
- 测试先例：`tests/test_lg_rag_supervisor_capability_catalog.py`（mock LLM 捕获基建）· `tests/test_hitl_approved_replan_quality.py:209` · `tests/test_supervisor_replan_error_feedback.py:252-258`（FP 逐字节预期构造）· `tests/test_hitl_approval_consumption.py:604-610`（`_fake_caps`）
- 体例先例：`docs/tasks/done/task_fix_planframe_truncation.md` · registry `docs/harness/audit_gates/registry.yaml` · 图谱签收承 01_modules.md:41-:46

## 思考轮

| 轮 | 结论 | early_stop |
|----|------|-----------|
| R0 | 范围对账（委派书五条 vs 12/13 文锚 vs 代码锚）done | false |
| R1 | 失败路径推演（预算锚 · id 泄漏 · 域外恶化 · FP 咬断言 · skill 叠加 · 并行冲突 · 环境性红）done | false |
| R2 | 非范围边界（真冒烟 T2 · translator 安全语义不动 · description 首句蒸馏本波不做裁定）done | false |
| R3 | 关键决策记录（装配点 `_build_catalog_block` · 引导语静态零 id · few-shot 选型 · FP 迁移单一真源）done | false |
| R4 | 体例对账（fix-planframe 模板 · registry/invokes/审查文/图谱登记）done | false |
| R5 | 收尾复核（验收 checklist 全锚定）done | false |

actual_last_round: R5

### R0 · 范围对账

委派书五条与 12/13 文锚逐条对齐：勘察（退化机理已定位——模板无正向选工具引导 · 无 few-shot · 「简单问题只给 rag」单边引导）· 硬化设计（候选 ①catalog 节级引导语强化 + ③few-shot 注入 · 预算锚 ≤6000 实测余量 ~2084）· 回归基线（mock LLM 基建已存在可扩 · 真冒烟 T2）· 测试（真 PG 绿 + 目标回归零红 + 全量 + ruff）· 图谱登记。§5-2 蒸馏评估给裁定（R2/R3）。

### R1 · 失败路径推演

见「失败路径」节。推演增补：引导语注入点在 `_format_capability_catalog` 输出之前（节首），与 R3 P2b-T3 mcp 节引导语（节内）位置不同——mcp 节引导语位置断言（test_capability_mcp_translator.py:610-617 子串 + index 比较）只钉 mcp 节内部相对顺序，不受影响。

### R2 · 非范围边界

真 LLM 冒烟归 T2（委派书钉明 · 本波交付 mock 面回归基线 + 冒烟问法清单草案）；translator M1-M3 fail-closed 词表不动（委派书安全线）；模板资产 v3 零 bump（注入在 catalog_block 装配层 · render 占位不动）；fail-closed 解析面（空 plan 判非法）零改。

### R3 · 关键决策记录

- **装配点 `_build_catalog_block`**：注入集中于 supervisor catalog 块唯一装配函数，`_format_capability_catalog` 行渲染本体零改——保 test_capability_output_fields:119/:131 与 test_fix_planner_args_schema:487/:500 精确相等断言零 diff；suffix/base 两路共用 catalog_block 自动同覆盖；FP 两测试预期构造迁移同一装配点（单一真源防漂移）。
- **引导语静态恒定零 id**：`_TOOL_AWARENESS_GUIDANCE` 不含任何 capability id——窄 allowlist（allowlist ∩ visible 过滤在装配前完成）下引导语不泄漏被隐藏工具；文本恒定使 prompt 可缓存、断言可钉。
- **few-shot 选型（1 条 JSON 例）**：泛化时间问法「现在几点了」→ `{"subtasks": [{"id": "t1", "type": "tool", "input": "查询当前时间", "tool": "<目录中对应工具的 capability_id>", "args": {}}]}`——覆盖「未点名 id 按描述匹配」决策锚；占位符 `<目录中对应工具的 capability_id>` 显式指示从目录取 id 防幻觉；预算友好（单例 ~400 字符内，余量充足）。
- **rag 兜底从句**：「仅当目录中没有工具能覆盖该问题时才纯 rag」——给域外 query（13 §7-2 数学负例）保留 rag 直答正道，硬化不恶化负例。
- **§5-2 裁定（Host 侧 description 首句二次蒸馏本波不做）**：translator.py:370 description 原样透传占比 ~100% 属实；但 ①when_to_use 合成面（M3 :349-355）已存在且 catalog 渲染面未消费 when_to_use，Host 重写 description 首句与 M3 同源同文，无法语义中和投毒（重写文本仍源自同一不可信 server 描述）；②真缓解属 server 向翻译器策略（G12 文本镜像 · 12 §5-4 已登记 server 向单独立项），Host 侧蒸馏不替代 server 向修复；③蒸馏增 catalog 预算占用、对泛化问法选定率无直接收益（选定率缺口在决策锚缺失而非描述质量）。登记为后续项（server 向 G12 立项承接）。
- **模板资产不动**：v3 模板 + suffix v2 保持，注入经 catalog_block——模板 bump 面零扩散（prompts 资产修订记录零触）。

### R4 · 体例对账

照 fix-planframe-truncation：task 档结构/人工闸表/registry entry（base=b8d11262 · allowed_app_files=[app/ops/lg_rag/multi/nodes.py] · banned_prefixes=[alembic/, scripts/]）/invokes by-task 四件 {10,30,40,50}/R1 审查文 GO 机读词/spec-wave@3.5.0 task lint PASS 为闸；图谱签收承 :41-:46 先例。仓规条款一遵守（走 20-R1 审查文非 --allow-no-review）。

### R5 · 收尾复核

验收 9 条逐条锚：引导语注入（新断言）· 空目录零追加（新断言）· 行渲染零 diff（既有断言）· 零泄漏两锚（新断言）· 预算锚（新断言）· FP 迁移（既有断言走新装配点）· 目标回归+全量+ruff · 图谱两件 · 过闸四件。回退 = revert nodes.py + 三测试文件零迁移。

## 实现备忘

### 偏差登记

1. **FP 两测试预期构造迁移**（intentional behavior change · 委派书预案内）：tests/test_hitl_approved_replan_quality.py 与 tests/test_supervisor_replan_error_feedback.py 的逐字节 expected 改走 `_build_catalog_block(_fake_caps())`——prompt 文本变更为本波目标行为，单一装配点防漂移；`_format_capability_catalog` 本体零改，行渲染零 diff 口径不动。
2. 其余无偏差：范围/非范围/预算锚/安全线（translator M1-M3 词表零改）全部按 10 档执行。

### 限制登记

1. 真 LLM 选定率冒烟归 T2（委派书钉明 · 本波交付 mock 面回归基线）。
2. §5-2 Host 侧 description 首句二次蒸馏本波不做（R3 裁定 · 真缓解属 server 向翻译器策略 · G12 文本镜像 12 §5-4 已登记 server 向单独立项）。
3. 全量 pytest 环境性红（25 件）与 base 同路径一致，非本波引入；CI 终裁。

## 测试策略

pytest tests（CI 终裁 · 真 PG postgresql+asyncpg://ops:ops_password@localhost:5432/opsdesk_test · 五键 blank 前缀 OPS_HITL_PERSISTENCE= OPS_CAPABILITY_ALLOW_WRITE= OPS_CAPABILITY_ALLOW_WRITE_TAGS= OPS_CAPABILITY_PERSISTENCE= OPS_CAPABILITY_EXTRA_MANIFESTS=）；目标回归 tests/test_lg_rag_supervisor_capability_catalog.py / test_capability_output_fields.py / test_fix_planner_args_schema.py / test_capability_panel_tools.py / test_capability_mcp_translator.py / test_hitl_approved_replan_quality.py / test_supervisor_replan_error_feedback.py 全绿；全量回归环境性红与 base b8d11262 同路径基线逐签对照；ruff check app tests 绿；allowed_app_files=[app/ops/lg_rag/multi/nodes.py] 机判。

## 修订记录

| 日期 | 修订 |
|------|------|
| 2026-11-17 | 落卡（夜间自动执行波 · 授权 issue Cyning12/ops-desk-workspace#23 m03064/m03734 · 来源 workspace 12 文 §5-1/§5-2 + 13 文 §7-2） |
