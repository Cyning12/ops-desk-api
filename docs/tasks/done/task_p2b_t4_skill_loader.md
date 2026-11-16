---
title: task · feat · P2b-T4 skill 加载器（registry 真化 + 槽位注入 + plan-JSON skill_ref 装配）
---

# task · feat · P2b-T4 skill 加载器（registry 真化 + 槽位注入 + plan-JSON skill_ref 装配）

> **状态**：`closed`（2026-11-16 落卡 · 夜间自动执行波 · 2026-11-16 关账 · feat PR #410 squash merge `e7609269` · 台账见 invoke_20261116_50_close.md）
> **来源**：issue Cyning12/ops-desk-workspace#23（m03064 夜间授权 · 设计真源 workspace 11-p2b-mcp-skill-design.md 终稿 §8 T4 行 + §6 全量 + §9.2 判据 · §0.1 R1-R10 修订为硬约束）

## Harness 元信息

| 键 | 值 |
|----|----|
| **task_slug** | p2b-t4-skill-loader |
| base | bf1c23f2 |
| 关联 issue | Cyning12/ops-desk-workspace#23 |
| 关联 PR | #410（feat · squash merge `e7609269`）· CLOSE 见 invoke_50 台账 |
| **wiki_delta** | `n/a` |
| **wiki_delta_note** | 本仓未启用 WikiTrack；本波为 skill_registry 真化（loader/slots 扩槽/catalog 注入/skill_ref 装配）+ 三 stub 退役 |

### 人工闸

| human_gate_id | status | blocks_hats | 说明 |
|---------------|--------|-------------|------|
| HG-TASK-DRAFT | approved | 30 | approved 2026-11-16 · 授权 issue #23 m03064（夜间授权 · m03216 追认并行波次）+ 11 设计终稿 §8 T4 行为唯一范围真源；禁碰 capability/manifest.py · mcp_client.py · config.py MCP 键（并行 T1 地盘）· 禁真 LLM 对照会话（T5a）· 禁 .importlinter 改动 |
| HG-AUDIT-R1 | approved | 30 | approved 2026-11-16 · 同上授权（11 设计终稿即审计真源：R1-R10 整合修订已评审关闭 · §9.2 六项注入证据为验收终裁 · §10 失败路径 · 授权范围零新增） |
| HG-GRAPH-MODULES | approved | 30 | approved 2026-11-16 · 同上授权（按实判 · 无新一级模块/路由/表/SSE 事件类型）· lg_rag 行 skill_registry「H5 stub·dormant」备注写实义务随 30 交付回填 |

## 背景

P2b 把 skill 从「H5 stub · dormant · 无运行时消费方」真化为生产加载器（11 §0）。本单是三件套之一：skill_registry 重写为 SKILL.md 真加载器（§6.1）+ slots 增 trusted `skill_content` 槽（§6.2）+ supervisor catalog 注入「可用技能（摘要）」节（§6.3）+ plan-JSON `skill_ref` 闸条件化装配（§6.4 · R9b：off 态 schema 逐字节不变）+ env 三件套（§6.5）+ 三 stub 退役（§6.6：capability 面不留 kind="skill"——skill 是 prompt 资产不是工具）+ compose 只读卷 + workspace 首枚 dogfood skill。

## 范围

1. `app/ops/skill_registry/` 重写：新 `loader.py`（yaml.safe_load frontmatter · name/description 必填 · kebab-case `^[a-z0-9]+(?:-[a-z0-9]+)*$` · 仅目录包形态 `skills/<name>/SKILL.md` · 伪造标记拒载（命中 slots 边界/节首标记字面 → 拒载+warn · **拒载优于转义** R-裁定）· **全文 ≤20000 字符超限拒载（R9a）** · 坏文件 warn 跳过 · 启动加载重启生效无热更新 · 模块单例）+ `registry.py` 重写（查询面 get/format_skill_catalog）——旧 API（SkillEntry/load_manifest/match_skills/skill_prompt_slot）不保留兼容，`__init__.py` 全换。
2. `app/ops/prompts/slots.py`：SLOT_REGISTRY 新增 `SlotSpec("skill_content", trusted=True, presentation="section", label="技能全文")`；docstring 槽位表同步；既有七槽白名单断言测试扩为八槽（承 P1-T3 先例）。
3. `app/ops/lg_rag/multi/nodes.py` catalog 注入：`_format_capability_catalog` 出口后 catalog_block 字符串追加「## 可用技能（摘要）」节（每行 name/description≤500 截断/when_to_use + 「任务匹配时在 subtask 声明 skill_ref」引导行）；**不动模板资产**（否 \$skills_block）；合并预算 capability ≤6000 + skill ≤`OPS_SKILL_CATALOG_MAX_CHARS`（默认 4000）≤10000 CI 断言锚。
4. plan-JSON skill_ref 装配（R9b 闸条件化）：`app/ops/lg_rag/schemas/subtasks.py` 增 `SubtaskItemSkillRef(SubtaskItem)` 子类（+`skill_ref: str|None`）· nodes.py `_parse_subtasks` 按 `skill_loader_enabled()` 二选一 model_validate——**off 态用原类 schema 逐字节不变**；`_worker_state` 装配面：检测 skill_ref → loader 取全文 → `wrap_slot("skill_content",...)` 追加进该子任务 prompt（input）；未知 skill_ref → 忽略 + span warn（键 `skill_ref_unknown` · fail-open 不炸 plan）；无 skill_ref 零注入。
5. env 三件套（承 `app/ops/goals/inject.py:27-46` 体例 · os.getenv 直读无缓存）：`OPS_SKILL_LOADER_ENABLED`（默认 false · 非法值回退 false · **off 态 loader 调用=0 且 supervisor system 逐字节一致**）· `OPS_SKILL_LOADER_ROOT`（默认 `../ops-desk-workspace/skills` 相对 api 仓根）· `OPS_SKILL_CATALOG_MAX_CHARS`（默认 4000 · 非法回退）。
6. 删除：`app/ops/capability/skill_stub.py` + `app/ops/capability/adapters/skill.py`（SkillStubAdapter）+ `app/ops/capability/adapters/mcp.py`（MockMcpAdapter）；引用面同步清理（capability/__init__.py docstring/import/__all__ · adapters/__init__.py · probes.py 删 mcp 探针项 · tests/test_capability_gateway.py mcp 探针用例最小改写为 cli 等价 + p3 skill 三用例整删）；`tests/test_skill_registry.py` 重写为新 loader 语义。
7. `docker-compose.yml`：api 容器挂 workspace skills/ 只读卷一行（`../ops-desk-workspace/skills:/ops-desk-workspace/skills:ro`）。
8. workspace 侧（ops-desk-workspace 仓 · 直推 main 承文档波先例）：`skills/` 建目录 + 首枚 dogfood skill「面板数据解读指南」（`skills/panel-data-guide/SKILL.md` · 叠 P2a 四枚工具的域话术指南）+ `skills/README.md` 作者指南（钉明：本目录变更须走 PR 评审——skill trusted 的显式假设 · platform S6）。
9. 验收六项注入证据单测/集成半（§9.2）：(a) off 态 supervisor system 逐字节一致 + loader 零调用；(b) on 态 catalog 块出现且 ≤max_chars；(c) 带 skill_ref 的 plan → 子任务 prompt 含 skill_content 槽全文；(d) 未知 skill_ref → span warn + 零注入；(e) 坏 frontmatter → warn 跳过；(f) 伪造标记/超 20000 → 拒载。
10. 图谱：`docs/_tech_graph/l1/01_modules.md` lg_rag 行 skill_registry「H5 stub·dormant」备注写实移除为真加载器 + HG-GRAPH-MODULES 签收行（承 :136 先例）。

## 非范围

- capability/manifest.py · adapters/mcp_client.py · config.py MCP 键（并行 T1 地盘 · 撞车登记不重删）。
- 真 LLM 对照会话（T5a）。
- `.importlinter` 改动（lg-rag-outbound :207 source_modules 已含 skill_registry → 零新边核实即可）。
- skill 热更新/rank/chokidar/事件总线/多根（§6.1 裁剪单）。
- 模板资产改动（否 \$skills_block · §6.3）。
- workspace 侧 11 设计文档改动（终稿冻结）。

## 失败路径

- skill 根目录不存在 → warn + 空 catalog，不炸启动（§10）。
- 坏 frontmatter（缺 name/description · 非 kebab-case · yaml 解析失败）→ warn 跳过该文件，不影响其余。
- 全文含伪造标记（slots 边界 `<slot:...>`/`</slot:...>` 或节首标记字面）→ 拒载 + warn（拒载优于转义：trusted 静默转义改指令语义不可见 · §6.1 裁定）。
- 全文超 20000 字符（R9a）→ 拒载 + warn。
- 未知 skill_ref → span warn（`skill_ref_unknown`）+ 零注入，不炸 plan（fail-open）。
- env 非法值 → 回退默认（enabled→false · max_chars→4000）+ warning（承 goals/inject.py 体例）。
- 回退 = `OPS_SKILL_LOADER_ENABLED` 置 false：off 态 supervisor system 逐字节一致 + loader 零调用（验收 a 钉死）。

## 验收标准

- [ ] skill_registry 重写：loader.py + registry.py 新语义绿 · 旧 API 全移除 · 六项加载闸（frontmatter/kebab/目录包/伪造标记/≤20000/坏文件跳过）用例齐
- [ ] slots 八槽：SLOT_REGISTRY 白名单断言扩为八槽 · `skill_content` trusted section 语义绿（wrap_slot 原样无标记）
- [ ] catalog 注入：(a) off 态 supervisor system 逐字节一致 + loader 零调用 · (b) on 态「## 可用技能（摘要）」节出现且总长 ≤`OPS_SKILL_CATALOG_MAX_CHARS` · 合并预算 ≤10000 断言
- [ ] skill_ref 装配：(c) 带 skill_ref plan → 子任务 prompt 含 skill_content 槽全文 · (d) 未知 skill_ref → span warn + 零注入不炸 plan · R9b off 态 subtask JSON schema 逐字节不变
- [ ] 三 stub 删除：skill_stub.py/adapters/skill.py/adapters/mcp.py 移除 · 引用面清零 · (e)(f) 坏 frontmatter warn 跳过 + 伪造标记/超 20000 拒载用例绿
- [ ] compose 只读卷一行 · workspace skills/ 首枚 dogfood skill + README 作者指南落盘
- [ ] ruff 绿 · 全量 pytest 绿（含 capability 五键 blank 前缀口径）· graph-compile 绿 · import-linter 零新边

### 自检结论

（验收期回填：七勾逐项结论 + CI 四绿 run id + 偏差清单）

## 必读列表

- workspace 11-p2b-mcp-skill-design.md §0.1（R1-R10 硬约束）/§6（全量）/§8（T4 行）/§9.2（判据）/§10（失败路径）——设计终稿唯一范围真源
- `app/ops/goals/inject.py:27-46`（env 三件套体例真源 · _TRUTHY/_FALSY · 非法回退 · 无缓存）
- `app/ops/prompts/slots.py`（SLOT_REGISTRY 七槽 :84-98 · wrap_slot :157-182 · _FORGE_ESCAPES :112-119）
- `app/ops/lg_rag/multi/nodes.py:104-157`（catalog 合成）· `:194-253`（_parse_subtasks/_record_span_metadata）· `:1453-1483`（_worker_state 装配面）· `:1516-1592`（supervisor_node catalog 注入点）
- `app/ops/lg_rag/schemas/subtasks.py`（SubtaskItem/SubtasksPlan · extra="ignore"）
- `docs/tasks/done/task_p2a_t1_panel_list_tools.md`（过闸体例模板）

## 思考轮控制

| 轮 | 结论 | early_stop | reason（early_stop） | residual_risks |
|---|---|---|---|---|
| R0 | 勘察：nodes.py 注入点双锚定（catalog_block :1560 后追加 · _worker_state :1453-1483 全文装配面）；R9b 落法=SubtaskItemSkillRef 子类按闸二选一 model_validate；probes.py mcp 探针项删除波及 test_capability_gateway.py 四区（mcp 探针两例最小改写 cli 等价 · boom 例 MockMcpAdapter→MockCliAdapter · p3 三例整删）；compose 容器内根解析为 /ops-desk-workspace/skills（WORKDIR /app） | false | — | 并行 T1 同删 capability/__init__.py 不同行（撞车登记预案在案） |
| R1 | 审查：docs/harness/reviews/task_p2b_t4_skill_loader_audit_R1_20261116.md（GO）；设计终稿 R1-R10 已评审关闭 | false | — | 无 |
| R2 | 方案：loader.py（SkillDoc/load_skills/env 三件套/单例+reset）+ registry.py（查询面）分层；catalog 节=纯文本追加不进模板资产；skill 全文走 trusted 槽（§6.1：catalog=纯文本节 · 全文走 skill_content trusted 槽） | false | — | 无 |
| R3 | 反例/边界：off 态双逐字节断言（supervisor system + subtask schema）+ loader 零调用 mock 断言；伪造标记含 <slot: 与节首标记两族；20000 边界取 20000/20001 双值；未知 skill_ref fail-open span 键钉死 skill_ref_unknown | false | — | 存量测试锚推进面（test_prompt_slots 七槽断言）已识别 |
| R4 | 收敛：验收七勾全可机断（pytest 单测/集成半 + ruff + graph-compile + spec-wave lint + CI 四绿） | false | — | 无 |
| R5 | 收口：范围 10 项 · 非范围 · 失败路径 · 三闸 approved（不代签 · 授权 issue #23 m03064/m03216 + 11 终稿） | true | 设计终稿即审计真源 · 锚点全实证 · 验收全机断 · 再轮无新增信息 | 无 |

**actual_last_round**：R5（early_stop）

### R0 · 勘察定论

- nodes.py 注入点：catalog_block 在 supervisor_node :1560 由 `_format_capability_catalog(caps)` 产出、suffix/base 两路共用 → skill 节追加在其后一行函数内，两路自动覆盖；skill 全文装配面 = `_worker_state`（:1453-1483 · 产 Send 载荷 assigned_subtask）。
- R9b 落法：schemas/subtasks.py 加 `SubtaskItemSkillRef(SubtaskItem)`（+skill_ref）· `_parse_subtasks` 按 `skill_loader_enabled()` 二选一 model_validate——off 态走原 SubtaskItem，JSON schema 逐字节不变（子类仅 on 态实例化）。
- 三 stub 引用面：capability/__init__.py（:30/:32/:92 import · :143/:150/:175 __all__ · docstring :7/:10-11）· adapters/__init__.py（:28/:37 · :52/:54）· probes.py（:23 import · :30 PROBE_MCP_ID · :34-46 首探针项）· tests/test_capability_gateway.py（:20-21/:33/:36 import · :363-417 mcp 探针两例 · :420-442 boom 例 · :448-488 p3 三例）· tests/test_skill_registry.py 整体重写。
- 并行 T1 撞车预案：T1 删 mcp_client.py + capability/__init__.py :28/:35/:108（与本单 :30/:32/:92 不同行）；若 rebase 撞 registry.yaml/01_modules.md 同区冲突 → 保留双方 entry 手动解。
- compose：Dockerfile WORKDIR /app → 容器内默认根解析 ../ops-desk-workspace/skills = /ops-desk-workspace/skills（卷挂载点一致）。

### R1 · 审查

设计终稿已经 platform/product 双向评审 10 项修订裁定关闭（11 §0.1 R1-R10），本档照终稿执行；R1=对照终稿核对范围/非范围/验收/failure_paths 一致性，结论一致（审查文落盘 docs/harness/reviews/）。

### R2 · 方案生成

loader.py 承载全部加载闸（yaml.safe_load frontmatter · kebab 校验 · 目录包形态 · 伪造标记拒载 · ≤20000 · 坏文件 warn 跳过）+ env 三件套 + 模块单例（reset 供测试）；registry.py 只做查询面（get_skills/get_skill/format_skill_catalog）；nodes.py 两处最小缝（catalog_block 追加 + _worker_state 装配）；slots.py 只增一行 SlotSpec + docstring 行。

### R3 · 反例与边界

六项注入证据全有负样本：off 态逐字节+零调用（a）· max_chars 边界（b）· 无 skill_ref 零注入（c 对照）· 未知 skill_ref fail-open（d）· 坏 frontmatter 跳过不影响其余（e）· 伪造标记两族 + 20000/20001 边界（f）。存量锚：tests/test_prompt_slots.py 七槽白名单断言扩八槽（承 P1-T3 先例）。

### R4 · 收敛

验收七勾全可机断：pytest 目标套件 + 全量（capability 五键 blank 前缀 · 委派层 monkeypatch.delenv）+ ruff app tests + graph-compile + spec-wave task lint + CI 四绿终裁（CI 无 .env）。

### R5 · 收口

范围 10 项与非范围/失败路径互斥闭合；三闸 approved（授权 issue #23 m03064 夜间授权 + m03216 并行波次 + 11 设计终稿 · 不代签）；early_stop——设计终稿即审计真源、锚点全实证、验收全机断，再轮无新增信息。

## 实现备忘

（实施期回填）

## 测试策略

- 新 `tests/test_skill_registry.py` 重写：loader 六项闸（合法样例加载 · 缺 name/description · 非 kebab · 非目录包 · 伪造标记拒载 · 20000/20001 边界 · 坏文件 warn 跳过 · 根目录不存在空 catalog）+ env 三件套（默认/非法回退/大小写）+ 单例 reset。
- `tests/test_prompt_slots.py`：七槽白名单断言扩八槽 + skill_content trusted 语义（wrap_slot 原样无标记 · presentation=section）。
- 新增 `tests/test_skill_loader_inject.py`（或并入既有 supervisor 测试文件 · 实施裁定）：(a)-(d) 四项——off 态 supervisor system 逐字节一致 + loader 零调用（monkeypatch 计数）；on 态 catalog 节出现 + ≤max_chars；skill_ref plan 子任务 prompt 含槽全文；未知 skill_ref span warn + 零注入。R9b：off/on 两态 subtask JSON schema 对拍（off 逐字节=master 基线）。
- capability 面：tests/test_capability_gateway.py mcp 探针两例最小改写为 PROBE_CLI_ID/MockCliAdapter 等价（保结构）· boom 例 MockCliAdapter 子类 · p3 skill 三例整删；probes.py 探针表删 mcp 项。
- CI 口径：capability 相关 pytest 五键 blank 前缀（OPS_HITL_PERSISTENCE= OPS_CAPABILITY_ALLOW_WRITE= OPS_CAPABILITY_ALLOW_WRITE_TAGS= OPS_CAPABILITY_PERSISTENCE= OPS_CAPABILITY_EXTRA_MANIFESTS=）；委派层用例 monkeypatch.delenv；ruff 范围=app tests；CI（无 .env）为终裁。

## 修订记录

| 日期 | 内容 |
|---|---|
| 2026-11-16 | 落卡（夜间自动执行波 · 授权 issue #23 m03064/m03216 · 设计真源 11 终稿 §8 T4 行 + §6 全量） |
