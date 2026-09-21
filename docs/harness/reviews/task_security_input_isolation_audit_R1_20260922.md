# task 审查 · security-input-isolation · R1（20-task-audit）

| 项 | 内容 |
|----|------|
| **日期** | 2026-09-22 |
| **帽** | 20-task-audit（书面审 · 不实现代码 · 不代签人闸） |
| **被审对象** | `docs/tasks/active/task_security_input_isolation.md`（10-task 落稿 · commit a718659 · 状态 draft） |
| **对照基准** | `docs/spec/security-hardening/SPEC-security-hardening_v1.md`（**signed** · HG-SPEC-SIGNOFF=approved 2026-09-22 · commit c4d42df · 四波全景签收 · 本波只做 W1） |
| **分支** | `task/security-hardening`（本帽 `git branch --show-current` 复核一致） |
| **invoke 快照** | `docs/harness/invokes/by-task/security-input-isolation/invoke_20260922_20_task_audit_security_input_isolation.md`（required_invoke_hats 含 20 · 同批落盘） |

---

## 结论

**通过（内容零阻塞）**：范围 D1–D5 / 非范围 13 条 / failure_paths 13 条 / 验收 25 条 / R0–R5 思考轮与 SPEC 实质**零差异**；B1 抽 5 行亲跑属实；pytest 基线 **1278 collected** 复跑一致；命名冲突扫复核零命中；「下游零请求」双断言可测性核验成立；SPEC 锚点行号漂移留痕复核成立；HG-GRAPH-MODULES 亲读 `docs/_tech_graph/l1/01_modules.md` 复核成立。

**流程闸（与内容分列）**：`HG-TASK-DRAFT` = pending · `HG-AUDIT-R1` = **pending（blocks 30）**——两闸均待维护者签，本帽不签；闸签前 30 拒开工。本审查文**不附 30 Prompt**，文末仅维护者签闸清单。

**签收**：20-task-audit R1 书面审通过，内容面可交维护者签闸。

---

## 逐项核对（对照 SPEC）

### 1. 范围（SPEC §2 W1 D1–D5）

- D1 槽位声明机制（`app/ops/prompts/slots.py` 新增 · `SLOT_REGISTRY` 六槽位 user_query/history_turn/rag_evidence/tool_result/memory_fact/system_instruction · 注册表外显式炸 · `wrap_slot` 唯一生成点 · `assert_slots_declared` 纯函数显式炸 · off 态零触达）——逐字对应 SPEC §2-D1 五行表 ✓
- D2 四面接线（RAG `rag_evidence` 保留 `[{i}] {anchor}` · 工具回执 `tool_result` `_degraded` 保留块内 · 用户/历史 `user_query`/`history_turn` 角色序不变 · memory 并入 `memory_fact` 语义不变）——对应 SPEC §2-D2 四面表 ✓
- D3 开关回退（`SECURITY_INPUT_ISOLATION_ENABLED` 默认关三件套逐字复刻 continuity.py:117-130 · off 三态逐字节对拍 · 机制故障降级 span `input_isolation_degraded` 与内容违例显式炸分立）——对应 SPEC §2-D3 ✓
- D4 金样零请求（`evals/security/input_isolation_v1.yaml` + `tests/eval/test_input_isolation.py` 一一对应 · sentinel 槽位归因 + 结构不变量与 sentinel 无关 · 越权零请求双断言 · 伪造标记转义 · 热路径零 LLM-as-judge）——对应 SPEC §2-D4 ✓
- D5 图谱/文档（零 alembic · lc_evidence_chain 行 +prompts 备注级 + lg_rag 行备注 + 人签新行 00 代录位 · graph-compile 绿）——对应 SPEC §2-D5 ✓
- 竖切结论与实现序（D5 → D1 → D2 → D3 → D4）承 SPEC §2 波次裁定与 §8，不重演 ✓

### 2. 非范围（SPEC §3）

SPEC §3 十二条全收（W2 检测层 / W3 PII 出口脱敏 / W4 真沙箱 / Policy 门语义 / visibility 求值 / 提示词护栏 / 检索 grade / supervisor 规划语义 / ingest 投毒 / 热路径 judge / chat 轨 / 历史回改）✓；**W2/W3/W4 与提示词护栏均在非范围** ✓。task 新增第 9 条「改 packs/render 既有 slot 语义」为命名邻近纪律补钉（packs.py:38/:148 既有 pack/模板槽位 vs 本波安全槽位两套语义 · 既有用例零改动），task R5 已自述对应关系，属过程化补钉、不改 SPEC 语义 ✓。

### 3. 验收断言化（SPEC §6）

task 验收 **25 条** = SPEC §6 二十二条（D1×4 / D2×4 / D3×3 / D4×5 / D5×2 / 变异检验×3 / 工程×1）+ task 工程条扩三条（B1 闸前置 / pytest+ruff / diff 白名单）+ 人工闸行 1 条，逐块映射标注齐备 ✓。关键断言化质量抽核：

- `SLOT_REGISTRY` 注册表外显式炸（单测）✓ · `wrap_slot` 伪造标记转义哨兵断言 ✓ · `assert_slots_declared` 显式炸（非返回 False）✓ · off 态零触达 mock/spy 计数 ✓
- 默认关三件套 + off 三态（未设/false/非法值）逐字节对拍 + 非法值 warning 日志断言 ✓
- **下游零请求双断言**：mock provider/gateway 调用计数=0 **且**拒收路径 span/log 标记出现，缺一不算过 ✓（详见抽查节可测性核验）
- 金样清单=实现一一对应（P0 同款）+ 正反双断言 + 热路径零 LLM-as-judge ✓
- 变异检验三条（开关可检 / 校验可检 / 拒收可检 · 「必挂→恢复全绿」句式）逐字对应 SPEC §6 ✓

### 4. failure_paths（SPEC §5）

task 13 条 = SPEC §5 十条逐条翻四列（注入穿透静默执行 / 未声明注入点漏网 / 标记伪造 / 开关失效 / 越权 prompt 构造被发出 / 校验误伤 / 槽位机制自身故障 / 脱敏漏出口 / 沙箱假隔离 / 身份租户语义漂移）+ 过程三条（HG-AUDIT-R1 未签拒开工 · B1 未落盘拒收 · 缺对拍/双断言/变异检验拒收防空真规则）✓。两静默错各有断言+变异检验兜底 ✓；注入穿透诚实定性（文本边界非硬边界 · W1 声称归因+机检+零请求 · W2 真兜底）与 SPEC §5/§7 一致 ✓。

### 5. R0–R5 思考轮

全轮无 early_stop ✓；actual_last_round=R5 回填 ✓。R0 实扫复核留痕详实（分支/锚点/命名扫/基线/目录存在性）；R2 竖切理由承 SPEC §2 不重演；R3 失败语义 13 条闭合；R4 residual 留「校验误伤面」（承 SPEC §7 ③）✓；R5 残余四条全承 SPEC §7 ✓。自检结论（draft 期 PASS）与正文一致 ✓。

### 6. 闸表

| 闸 | task 表值 | 本帽复核 |
|----|-----------|----------|
| HG-TASK-DRAFT | pending（blocks 20-R1, 30） | 一致 · 待维护者签 |
| HG-AUDIT-R1 | **pending**（blocks **30**） | 一致 · 待维护者签 · **本审查文不附 30 Prompt** |
| HG-GRAPH-MODULES | approved（模块表已建置）+ 新签义务 | 亲读复核成立（见抽查节） |
| HG-PILOT-OPSDESK-GLAYER | n/a | 一致（本 task 不涉物理分层试点） |

新签义务留 **00 代录位**（随 30 交付落盘）有先例支撑：01_modules.md :88（prompt_asset_roadmap_p1 · 00 代录 · 30 回写）· :89（llm-layer-hardening · 00 代录 · 30 交付核验后）· :91（session-summary-fallback · 00 代录 ratify）✓。偏离回炉补闸条款（graph_delta_note + 闸表 + 验收人工闸行三处钉死）✓。

---

## 重点抽查（本帽亲跑）

### B1 11 行抽 5 条实核（全对）

| # | task 声称 | 本帽亲跑 | 结果 |
|---|-----------|----------|------|
| #1 | test_lc_evidence_chain.py **19** 用例 | `grep -c 'def test_'` = 19 | ✓ |
| #3 | test_lg_rag_multi.py **11** 用例 · invalid_tool_id 锚 :231 | 计数=11 · `grep -n` = :231 `async def test_invalid_tool_id_in_plan_fallback_single_rag` | ✓ |
| #5 | test_memory_injection.py **23** 用例 | 计数=23 | ✓ |
| #7 | supervisor 四面 10/14/12/9 | test_supervisor_budget=10 · test_supervisor_parallel_join=14 · test_critic_rebind=12 · test_lg_rag_supervisor_capability_catalog=9 | ✓ |
| #8 | test_session_summary.py **29** | 计数=29 | ✓ |

补核 B1 扫描口径：`grep -rn 'format_evidence_block\|retrieved_chunks' tests/` = **零命中**（exit 1 亲跑）——「改编面为零」裁定有实证 ✓；`ls evals/` 确认 `evals/security/` 不存在（新增义务）✓；`ls app/ops/prompts/` 确认无 slots.py ✓；tests/eval/ 实有 10 文件（__init__ + eval_agent_graders + 8 个 test_ 文件）与 B1#9 一致 ✓。

### pytest 基线复跑

`python -m pytest tests --collect-only -q` = **1278 tests collected**（2026-09-22 本帽真跑 · 与 task :77/:200 基线一致）✓

### 命名冲突扫复核

`grep -rn 'SLOT_REGISTRY\|wrap_slot\|assert_slots_declared\|SECURITY_INPUT_ISOLATION\|slots\.py\|input_isolation' app/ tests/ evals/ docs/_tech_graph/` = **零命中**（exit 1 亲跑）✓——新机制名/env 名/文件名无冲突；packs/render 既有 `slots` 参数为 pack/模板槽位语义（不同域 · 命名邻近纪律已入钉死契约）。

### 「下游零请求」双断言可测性

- 断言锚点真实存在：nodes.py `invalid_tool_id` :753（初始化）/:768（置位）→ 整单 fallback + span `supervisor_invalid_tool_id` :834-835（本帽 grep -n 实证）；单测锚 tests/test_lg_rag_multi.py:231 在位 ✓
- 双断言可区分「没发出去 vs 没走到」：mock provider/gateway 调用计数=0（证明未发出）+ 拒收路径 span/log 标记出现（证明走了拒收路径而非根本没走到）——承 SPEC §4 A2 裁决（弃 A1 仅计数假通过）；变异检验 ③（临时放行 → 计数断言必挂且 span 标记消失可区分 → 恢复全绿）兜底防空真 ✓
- 可测性结论：双断言形态可执行、锚点真实、变异检验闭合 ✓

### SPEC 锚点行号漂移留痕复核

| 锚点 | SPEC | task | 本帽实核 | 判定 |
|------|------|------|----------|------|
| answer.py format_evidence_block | :73-83 | :73 | def 实 :73 | ✓ 一致 |
| answer.py .format(retrieved_chunks) | :107-110 | :109 | `.format(` 实 :107 · `retrieved_chunks=` 实 :109 | ✓ task 取值在 SPEC 区间内 |
| nodes.py _degraded 注释 | :1095-1102 | :1097-1098 | 注释块实 :1095-1099 | ✓ task 已如实记录微漂移（R0/:68） |
| nodes.py invalid_tool_id 面 | :764-773 | :753-835 | 实 :753/:768/:834-835 | ✓ task 已如实记录微漂移（R0/:69） |
| nodes.py json.dumps / 子任务结果 | :1484-1495 | :1484/:1495 | 实 :1484/:1495 | ✓ 一致 |
| continuity.py 三件套 | :121-131 | :117-130 | _TRUTHY 实 :117 · def 实 :121 · warning 实 :130 | ✓ 两口径均落真实区间（task 从 _TRUTHY 起算） |
| continuity.py _render_rows | :196-201（§4） | :191 | def 实 :191 | ✓ 同一函数取行口径差 · 语义零偏差（见非阻塞观察 1） |
| packs.py REQUIRED_SLOTS / slot 标记 | — | :38/:148 | 实 :38/:148 | ✓ 一致 |

漂移留痕纪律成立：两处实质微漂移（nodes.py）task 均已如实记录并标「语义一致」，无一静默改义 ✓。

### HG-GRAPH-MODULES 亲读复核（01_modules.md）

- `lc_evidence_chain` 行 :24：依赖出边 → rag, llm, db · **无 prompts**（本波新边落此）✓
- `lg_rag` 行 :27：glob `app/ops/lg_rag/**` · **C2（2026-09-01）裁定 `app/ops/prompts/**` 归属本行**（lg_rag→prompts 为行内路径不构成新跨模块边）✓
- `memory` 行 :28：依赖出边已含 `prompts`（extract 模板加载 · prompt-asset-roadmap-p1 备注级先例形态）✓
- 签录链完整至 :91（session-summary-fallback）；00 代录位先例 :88/:89 ✓
- 复核结论：task 闸表 HG-GRAPH-MODULES=approved（模块表已建置）+ 新签义务（lc_evidence_chain 行 +prompts 备注级 + lg_rag 行备注 + 人签新行 00 代录位）+ 回炉补闸条款——全部与图谱真值一致 ✓

---

## 非阻塞观察（记录备查 · 不构成退回）

1. SPEC §4 引 `_render_rows` 作 continuity.py:196-201，task 锚点作 :191（def 行）——同一函数取行口径差，语义零偏差；30 阶段按 def 行 :191 起读即可。
2. task 工程验收「生产路径 diff 白名单」以 `git diff master -- app/` 为口径，而本仓默认主分支实际以 PR 合并到 main（AGENTS.md 口径）；30/40 阶段执行时按实际主干分支名取值即可，不影响断言语义。

---

## 闸态汇总

- `HG-TASK-DRAFT` = **pending**（blocks 20-R1, 30 · 待维护者/00 验收代录）
- `HG-AUDIT-R1` = **pending**（blocks **30** · 本审查 R1 通过待人签 · 本帽不签）
- `HG-GRAPH-MODULES` = approved（模块表已建置 · 本帽亲读复核成立）+ 新签义务随 30 交付落盘（00 代录位）+ 偏离回炉补闸
- `HG-PILOT-OPSDESK-GLAYER` = n/a

---

## 维护者签闸（20 后 · 30 前）

- [ ] 已读 R1 审查结论（本文）
- [ ] 在 task 人工闸表将 HG-TASK-DRAFT 改为 approved（维护者 · 日期）
- [ ] 在 task 人工闸表将 HG-AUDIT-R1 改为 approved（维护者 · 日期）
- [ ] commit task 文档或确认已签
- [ ] 再下发 Harness 30 Prompt

30 Agent 将以 task 表为准；pending 时必须拒开工（见 TEMPLATE_30_gate_stop.md）。
