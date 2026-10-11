# Task：hitl-n1-locked-branch-inject（locked 空分支 preserved_block 不注入 · 读步去盲路径覆盖缺口收口）

> **状态**：active（20 R1 PASS · 三闸 approved · 00 代录 授权 m00106 · 30 可开工）  
> **类型**：功能缺口收口（hitl-approved-replan-quality CLOSE N1 钉案 · SPEC §9 序1 后续项 · 消费回路血统延续）  
> **依据**：SPEC `docs/spec/hitl-approval-consumption/SPEC-hitl-approval-consumption_v1.md` §9 序1 · CLOSE 文档 `docs/tasks/close/close_hitl_approved_replan_quality_20261011.md` §四.1（N1 钉案）+ §七.1（另立 task 建议 · 最高优先）· 交接档 `docs/harness/invokes/by-task/_prompts/PROMPT_00_spec-campaign-handoff_20261011.md` §2.2 第 1 项  
> **分支**：`task/hitl-n1-locked-branch-inject`（base master `286d825`）

## Harness 元信息

| 字段 | 值 |
|------|-----|
| **task_slug** | `hitl_n1_locked_branch_inject` |
| **git_branch** | `task/hitl-n1-locked-branch-inject` |
| **implement_repo** | `ops-desk-api` |
| **test_strategy** | `required` |
| **test_strategy_note** | 红测先行（locked 空+保号非空场景 prompt 断言 RED→GREEN）→ 实现 → 全量对拍；live 行为对照留 40 |
| **code_quality_bar** | `L2_backend` |
| **graph_change_layer** | `G-L1`（改 `app/ops/lg_rag/multi/nodes.py` supervisor 节点 prompt 组装分支逻辑 · 图谱模块行为表述面 · 30 按实判回写） |
| **graph_delta** | 预期 `docs/_tech_graph/l1/01_modules.md` lg_rag/multi 行备注回写（按实判 · 无模块增删） |
| **graph_delta_note** | 若 30 实证后确认零图谱表述面变化，改填 `none` 并注理由 |
| **wiki_delta** | `n/a` |
| **wiki_delta_note** | 无文档站/WikiTrack 变更（纯图节点 prompt 组装逻辑收口） |
| **review_hat** | `20` |
| **required_invoke_hats** | `10,20,30,40` |
| **invoke_retention_profile** | `default` |
| **experience_capture** | `required` |
| **kpi_aggregator** | `n/a` |
| **orchestration** | 10 落稿 → 20 R1 → 维护者签 → 30（红测先行）→ 40（含 live 对照）→ PR+CI 绿 → CLOSE |
| **freeze_id** | 无（预期零新表/零迁移/零新 SSE 事件/零新 payload 键） |

### 人工闸

| human_gate_id | status | blocks_hats | 说明 |
|---------------|--------|-------------|------|
| HG-TASK-DRAFT | approved | 20, 30 | 初稿人扫 · 00 代录（授权 m00106 · 2026-10-11） |
| HG-AUDIT-R1 | approved | 30 | R1 PASS（docs/harness/reviews/task_hitl_n1_locked_branch_inject_audit_R1_20261011.md · nit N1 行号双口径留痕豁免）· 00 代录（授权 m00106） |
| HG-GRAPH-MODULES | approved | 30 | 预判 G-L1（modules.md lg_rag/multi 行行为表述面）· 30 按实判回写义务钉死（实证免动须交免动说明）· 00 代录（授权 m00106） |

---

## 背景与目标

### N1 钉案原文（两源在案）

1. **CLOSE §四.1**：locked=空时 supervisor 走 `_build_supervisor_system` 基础 prompt（nodes.py:1172-1173 else 分支），保号行注入仅覆盖 suffix v2 路径——契约红线不破（护栏兜底 · run1 实证），但「读步去盲」存在路径覆盖缺口；40 裁定不阻塞收口，建议另立 task 裁定（基础 prompt 路径是否同注保号行）。
2. **CLOSE §七.1（最高优先后续建议）**：locked 空走基础 prompt 时 preserved_block 不注入——裁定基础 prompt 路径是否同注保号行/终态摘要，消「读步去盲」路径缺口。

### 实证锚点（10 亲读核真 · base master `286d825` · 锚点行号逐字复核）

| 锚点 | 实证 |
|---|---|
| `app/ops/lg_rag/multi/nodes.py:1141` | `locked = _locked_prefix(state)`（Q8 重规划入口先算不可变前缀 · 空 ⇒ 首次规划语义） |
| `app/ops/lg_rag/multi/nodes.py:1143` | `preserved = _unlocked_preserved_rows(state, locked)`——**无条件计算**，locked 空时仍可能非空（hitl_unlocked_ids ∩ 无终态 ∩ 不在 locked · :755-778） |
| `app/ops/lg_rag/multi/nodes.py:1161-1172` | `if locked:` 分支走 `_build_supervisor_suffix_system(..., preserved_block=_format_preserved_block(preserved))`（suffix v2 注入保号行名单 + 前缀终态摘要） |
| `app/ops/lg_rag/multi/nodes.py:1173-1174` | `else:` 分支 `system_content = _build_supervisor_system(catalog_block)`——**preserved 已算出但不注入**，LLM 不知晓保号行 |
| `app/ops/lg_rag/multi/nodes.py:806-825` | `_format_preserved_block`：保号行执行摘要文本生成（空集合返空串 · 注入文钉「切勿为同一目的再规划新步骤或孪生步骤」） |
| `app/ops/lg_rag/multi/nodes.py:985-1002` | `_join_subtasks` 分发层 write 孪生护栏：`write_replay_guard_skip`/`replay_of` 台账（结构兜底 · 本 task 不触碰） |

**机理一句话**：HITL 批准单步写场景（40 run1 实证形态）中，被批准步经 `_apply_hitl_decision` 剪结果后无终态、locked 前缀为空，preserved 集合非空；supervisor 重规划走 else 基础 prompt 分支，保号行名单不注入 → LLM 仍盲，可再规划同语义孪生步（写步由 `write_replay_guard_skip` 护栏兜底中性化，读步重放无护栏、浪费 LLM 轮）。

### 候选修复方向（开放给 30 实证后裁定 · 起草不锁死）

- **A · else 分支同注**：locked 空且 preserved 非空时也走注入路径——最小面 = 分支条件改 `if locked or preserved` 复用 suffix 组装（prefix_block 退化为「（无）」 · `_format_prefix_block([])` 已返「（无）」字面 · :803），或 else 分支单独拼接 preserved_block 段。
- **B · 基础模板加槽**：`_build_supervisor_system` 增可选 preserved_block 参数（模板 v2→v3 · 牵连 prompt_assets 测试与 assets README）。
- **C · 维持现状 + 文档钉案**：若 30 实证裁定 locked 空+preserved 非空形态下护栏兜底已足（写步零重发 · 读步浪费可接受），则本 task 降级为钉案文档化——须 20/维护者明确裁定，不默许。

**10 倾向 A**（最小 diff · 复用已验收的 suffix 注入面 · 不动模板资产），最终裁量留 30 实证 + 20 审。

**目标**：locked 空分支下 preserved 非空时，保号行名单对 supervisor LLM 可见（prompt 注入 · 可机断）；preserved 空时行为对 master 零 diff；write 护栏兜底现状不破坏（`write_replay_guard_skip`/`replay_of` 台账键与触发语义零 diff）。

## 范围

- **F1**：locked 空 + preserved 非空分支的 preserved_block 注入裁定落地（30 实证后 A/B/C 定案）。
- **F2**：prompt 组装断言测试（红测先行：注入前 RED · 注入后 GREEN；含 preserved 空零 diff 断言）。
- **F3**：write 护栏兜底反回归断言（locked 空+孪生写步仍 guard-skip 命中 · 台账键零 diff）。
- **F4**：invoke 留档 / 图谱备注按实回写 / 经验捕获。

## 非范围

- **write 护栏本体**（`_join_subtasks` guard-skip 机制 · :985-1002）——现状兜底不触碰、不增强。
- **locked 非空 suffix 路径**（:1161-1172）——已验收（TC2/TC3 在案），零 diff。
- **prompt 内容级直证观测增强**（CLOSE N2 · langfuse GENERATION input / 台账注入标记）——CLOSE §七.2 另项，非本 task 面。
- **approved 恒 replan 决策点 / done{completed} 语义 / 保号机制本体**——历 task 已收口或已另立钉案（T4/T5/T6 CLOSE 在案）。
- **LLM 规划质量泛化优化**、仓级 logging（序2 已 CLOSE）、verify 基线（序3 已 CLOSE）。

---

## 失败路径

| 触发条件 | 系统行为 | 可重试 | 用户可见 |
|----------|----------|--------|----------|
| FP-1 注入后 LLM 仍产孪生步（prompt 约束非结构保证） | write 孪生由 `_join_subtasks` 护栏 guard-skip 中性化（`write_replay_guard_skip`/`replay_of` 台账 · 先于签发不派发不消费）；读步重放仅浪费 LLM 轮 | 是（下一轮重规划自然收敛） | 无（写副作用零重发由护栏结构保证 · 非本 task 改变） |
| FP-2 preserved 集合过大致 prompt 膨胀 | `_format_preserved_block` 逐行摘要（无截断 · 现形态行= sid+type+input+tool）；30 实证评估是否需限量/截断（超阈值截断并照登） | 是 | 无 |
| FP-3 分支条件改动误伤 locked 空 + preserved 空形态（首次规划主路径） | 验收标准 TC2-b 钉死：preserved 空时 system_content 对 master 逐字节零 diff；pytest 断言拦截 | 是（回退 diff） | 无 |
| FP-4 模板/组装改动破坏 prompt_assets 契约 | `tests/test_prompt_assets.py` 红（CI 拦）；模板改动须同步 assets README + 槽位测试 | 是 | 无 |
| FP-5 HG-AUDIT-R1 pending 即 30 改码 | 执行 Agent **拒开工**（GATE_VERIFY · task 人工闸表为真值） | 是 | 须先 20 R1 + 维护者签 |

---

## 验收标准

- [ ] **TC1 红测先行**：构造 supervisor 重规划场景（`hitl_unlocked_ids` 非空 · 被批准步无终态 · locked 空 ⇒ preserved 非空），断言修复前 system prompt **不含**保号行名单（RED · 与 N1 缺口同形签名）→ 实现后断言 prompt **含** preserved 行（sid/type/input · GREEN）；RED→GREEN 时序在 git 历史可查。
- [ ] **TC2 注入行为与零 diff 双断言**：(a) preserved 非空+locked 空 → prompt 含保号行名单（`_format_preserved_block` 输出或其等价段）；(b) preserved 空（含 locked 空首次规划主路径）→ system_content 对 master 同输入逐字节零 diff；(c) locked 非空 suffix 路径既有断言原样绿（`tests/test_hitl_approved_replan_quality.py` + `tests/test_prompt_assets.py` 零新增红）。
- [ ] **TC3 write 护栏兜底不破坏**：locked 空 + 孪生写步场景护栏仍命中（`write_replay_guard_skip=True`/`replay_of` 台账断言存续 · 既有 TC2 组六枚原样绿）；护栏 diff 面为零（`_join_subtasks` guard 段 git diff 空）。
- [ ] **TC4 反回归全量对拍**：`pytest tests` 全量对拍 master 基线零新增红（环境性红逐枚同名同因照登）；`ruff check app tests` 触及路径零新增；`./scripts/graph-compile.sh` EXIT=0（再生噪音文件一律还原）。
- [ ] **TC5 live 行为对照（40 帽）**：单写步 approved → resume 场景（承 40 run1 形态）复跑，观测 LLM 是否仍产孪生步；结果如实照登（N2 观测口径限制存续：prompt 内容级直证不可观测 · 以行为对照+台账链间接实证）。

## 依赖

- SPEC `docs/spec/hitl-approval-consumption/SPEC-hitl-approval-consumption_v1.md` §9 序1（现象与建议方向原文）。
- CLOSE 文档 `docs/tasks/close/close_hitl_approved_replan_quality_20261011.md`（§四.1 N1 钉案 · §七.1 另立 task 建议 · §三 TC3 run1 实证形态）。
- 40 invoke `docs/harness/invokes/by-task/hitl-approved-replan-quality/invoke_20261011_40_verify.md`（run1/run2 双 run 对照实证 · N1 裁定过程）。
- 仓级 logging 初始化已 CLOSE（`docs/tasks/close/close_repo_logging_init_20261011.md`）——live 台账观测前提已具备。
- 无代码面阻塞依赖（master `286d825` 已含 PR #233 注入面与护栏面）。

## 给执行帽的必读列表

1. 本 task 全部锚点行（`app/ops/lg_rag/multi/nodes.py:1141-1174` / `:755-825` / `:985-1002` · 逐一亲读复核 · 禁信转述 · 行号漂移按实校正）。
2. CLOSE 文档 `docs/tasks/close/close_hitl_approved_replan_quality_20261011.md` §四.1 / §七.1 / §三（TC3 run1 形态）。
3. SPEC `docs/spec/hitl-approval-consumption/SPEC-hitl-approval-consumption_v1.md` §9 序1。
4. `tests/test_hitl_approved_replan_quality.py`（TC2 组六枚 + 红测先例）· `tests/test_prompt_assets.py`（模板槽位契约）。
5. `docs/standards/CODING_BACKEND_L2_v1_zh.md`（涉码 task）。
6. 验收环境坑位：`NO_PROXY` 含 `[::1]` 致 httpx InvalidURL（两度复发 · live 前置先剥 no_proxy + 核容器归属）。

## 思考轮控制

| 轮 | 结论 | early_stop | reason（early_stop） | residual_risks |
|---|---|---|---|---|
| R0 | 问题框定：N1 钉案两源原文 + 锚点亲读（else 分支 :1173-1174 · preserved :1143 无条件算出但不注入）· 机理链闭合 | false | — | 无 |
| R1 | 证据收集：`_unlocked_preserved_rows`（:755-778）证实 preserved 可独立于 locked 非空；40 run1 live 形态（locked 空+护栏命中孪生）在案 | false | — | run1 未留存 prompt 原文（N2 观测口径） |
| R2 | 方案生成：A 分支条件复用 suffix / B 基础模板加槽 / C 维持现状文档钉案；10 倾向 A · 裁定留 30 实证 | false | — | B 案牵连 prompt_assets 面未实估 |
| R3 | 反例与边界：preserved 空主路径零 diff 钉死（FP-3）· 护栏面零 diff 钉死（TC3）· prompt 膨胀边界（FP-2） | false | — | 超大 preserved 集合限量策略未定（留 30） |
| R4 | 验收/可测性：TC1 红测先行 + TC2 双断言 + TC3 护栏存续 + TC4 全量对拍 + TC5 live 对照 · 全可机断 | false | — | TC5 受 N2 观测口径限（间接实证照登） |
| R5 | 收口：范围/非范围/失败路径/依赖/必读齐备 · 三闸 pending 不代签 · graph_change_layer=G-L1 预判 | true | 缺口机理单一明确（单分支注入缺口）· 锚点全亲读核真 · 方案开放性显式留 30 · 再轮无新增信息 | 方案 A/B/C 未锁死（刻意）· graph_delta 为预判 |

**actual_last_round**：R5（early_stop）

### R0 · 问题框定

hitl-approved-replan-quality（PR #233 · 已 merge）交付 suffix v2 `$preserved_block` 注入去盲 + write 孪生结构护栏；40 live 双 run 对照发现 N1：locked 空分支（multi/nodes.py:1173-1174 else）走 `_build_supervisor_system` 基础 prompt，preserved_block 不注入——保号行对 LLM 不可见的路径覆盖缺口。契约红线不破（护栏兜底 · run1 实证 `write_replay_guard_skip` 命中），40 裁定不阻塞收口、另立 task。本 task = 该缺口的收口立案（维护者令 · 交接档 §2.2 第 1 项 · SPEC §9 序1 后续项）。

### R1 · 证据收集

亲读核真（base master `286d825`）：`_unlocked_preserved_rows`（:755-778）= hitl_unlocked_ids ∩ 无终态 ∩ 不在 locked —— **locked 空不蕴涵 preserved 空**（40 run1 形态即实证：单写步 approved · 无已完成前缀 · locked 空 · preserved 非空）。:1143 preserved 无条件算出；:1161-1172 仅 `if locked` 分支消费之；:1173-1174 else 分支丢弃。注入文（:806-825）已含「切勿为同一目的再规划新步骤或孪生步骤」钉死措辞。

### R2 · 方案生成

候选三案（开放 · 不锁死）：A 分支条件 `if locked or preserved` 复用 suffix 组装（最小 diff · prefix_block 退化「（无）」字面已在 :803 处理）；B `_build_supervisor_system` 加槽（模板 v3 · 牵连 assets README + prompt_assets 测试）；C 维持现状仅文档钉案（须维护者明确裁定）。10 倾向 A：复用已验收注入面 · 零模板资产变动 · 行为差集中在新断言覆盖内。

### R3 · 反例与边界

- 首次规划主路径（locked 空 + preserved 空）必须逐字节零 diff——FP-3 验收钉死，防「顺手统一」误伤。
- 护栏面（:985-1002）零 diff——本 task 是去盲注入收口，不是护栏增强；写步安全已由结构兜底，不可借本 task 松动。
- preserved 超大 → prompt 膨胀（FP-2）：现注入文无截断；30 实证评估是否限量，裁定照登。
- off 模式（`LG_RAG_DELEGATION_TOKEN_MODE=off`）hitl_unlocked_ids 恒空 ⇒ preserved 恒空 ⇒ 零触达（天然零 diff · TC2-b 覆盖）。

### R4 · 验收/可测性

TC1 红测先行防恒绿假象（RED 签名 = N1 缺口同形：prompt 不含保号行）；TC2 双断言（注入有/零 diff 无）机断；TC3 护栏存续机断（台账键 + diff 空双重）；TC4 仓级反回归对拍基线；TC5 live 行为对照（N2 观测口径限制照登 · 间接实证闭环承前例）。

### R5 · 收口

范围 F1–F4、非范围五条、失败路径五行、验收五条勾选、依赖五条、必读六项齐备；三人工闸 pending 不代签；graph_change_layer=G-L1 预判（改图节点 prompt 组装分支逻辑 · 图谱行为表述面 · 30 按实判回写）。lint 形态对齐历 task 实证教训（验收 - [ ] 清单 · 思考轮控制表五列 · 闸表四列纯 status）。裁定收口，early_stop at R5。

### 自检结论（执行者）

（30/40 回填）

---

## 修订记录

| 日期 | 说明 |
|------|------|
| 2026-10-11 | v0 · 10 落稿：N1 钉案两源原文 + 锚点亲读核真（base master `286d825` · else 分支 multi/nodes.py:1173-1174）· 候选 A/B/C 开放（倾向 A）· TC1–TC5 验收 · R0–R5 思考轮（early_stop at R5）· 三闸 pending 待人签 |
| 2026-10-11 | 三闸 approved（**00 代录 · 授权 m00106**）：HG-TASK-DRAFT 初稿人扫 · HG-AUDIT-R1（R1 PASS · 审查文址A 在案 · nit N1 豁免）· HG-GRAPH-MODULES（G-L1 预判 · 30 回写义务钉死）→ 30 解锁 |
