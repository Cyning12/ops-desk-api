# invoke · 10 · security-input-isolation · task 落稿

| 项 | 内容 |
|----|------|
| **时间** | 2026-09-22 |
| **帽** | 10-task（SPEC signed 后落稿 · 本棒由 00 委派 10-task 帽 Agent 执行） |
| **文件** | `docs/tasks/active/task_security_input_isolation.md` |
| **上游** | `docs/spec/security-hardening/SPEC-security-hardening_v1.md`（signed · HG-SPEC-SIGNOFF=approved 2026-09-22 · c4d42df · 四波全景签收 · 本波只做 W1） |
| **格式基准** | `docs/tasks/done/task_session_summary_fallback.md`（真读对齐字段 · PR #159 已合 · CLOSE 归档） |

## 结论

**PASS（落稿）** · 总轨四波本 task = W1；范围 D1 槽位声明机制（`app/ops/prompts/slots.py` 新增 · `SLOT_REGISTRY` 六槽位注册表（user_query/history_turn/rag_evidence/tool_result/memory_fact/system_instruction · trusted 声明 · 表外显式炸）· `wrap_slot` 强制包装（边界标记+不可信声明引导语+伪造标记转义 · 唯一生成点）· `assert_slots_declared` 装配校验纯函数（未声明段显式炸不静默降级 · off 态零触达）· 方案 S3 承 SPEC §4 裁决不重演）/ D2 四面接线（RAG 片段 `rag_evidence` 槽保留 `[{i}] {anchor}` 格式 · 工具回执 `tool_result` 槽 `_degraded` 保留块内 · 用户/历史 `user_query`/`history_turn` 归因角色序不变 · memory 并入 `memory_fact` 语义不变）/ D3 开关回退（`SECURITY_INPUT_ISOLATION_ENABLED` 默认关三件套逐字复刻 continuity.py:117-130 · off 三态逐字节对拍=上线前提 · on 态机制故障降级 span `input_isolation_degraded` 与内容违例显式炸分立）/ D4 金样零请求（`evals/security/input_isolation_v1.yaml` + `tests/eval/test_input_isolation.py` 一一对应 · sentinel 槽位归因+结构不变量与 sentinel 无关 · **越权零请求双断言 mock 计数=0 且拒收 span 标记缺一不算过** · 伪造标记转义用例 · 热路径零 LLM-as-judge）/ D5 图谱文档（零 alembic · lc_evidence_chain 行 +prompts 备注级依赖边 + lg_rag 行备注 + 人签新行 00 代录位 · graph-compile 绿）；非范围沿用 SPEC §3（W2/W3/W4 · Policy/visibility 语义 · 护栏 · 检索/规划逻辑 · ingest · 热路径 judge · chat 轨 · 历史回改 12 条 + 命名邻近补钉 1 条）；验收 **25 条**全否定性断言化逐块映射 SPEC §6（人工闸 1 / D1×4 / D2×4 / D3×3 / D4×5 / D5×2 / 变异检验×3 / 工程×3）· 与 SPEC 实质差异**零**；failure_paths **13 条**（SPEC §5 十条翻四列 + 过程三）；R0–R5 全轮无 early_stop。

## 实扫留痕（本帽真跑）

- `git branch --show-current` = `task/security-hardening` ✓（SPEC 签收 c4d42df 后）
- RAG 面：`answer.py` `format_evidence_block` :73（snippet 原文排版）· `.format(retrieved_chunks=...)` :109 进 user 模板——与 SPEC §1 一致（裸奔复核成立）
- 工具回执面：`multi/nodes.py` `json.dumps(results)` :1484 · `子任务结果：{payload}` :1495 · `_degraded` 写进 output 先例 :1097-1098（SPEC 作 :1095-1102 微漂移语义一致）——裸奔复核成立
- 越权拒收先例：`invalid_tool_id` :753/:768 → fallback + span `supervisor_invalid_tool_id` :834-835（SPEC 作 :764-773 微漂移）；单测锚 `tests/test_lg_rag_multi.py:231`
- 开关先例：`memory_facts_enabled` 三件套 continuity.py:117-130（`_TRUTHY/_FALSY` :117-118 · 非法值 warning :130）；引导语 `MEMORY_PREFERENCES_GUIDE` :114 · 转义 `_render_rows` :191 · memory 块 :205/:230
- prompts 包：ls 实证 `__init__/loader/render/templates/packs/assets` **无 slots.py**；packs.py 既有 `REQUIRED_SLOTS` :38 + `<!-- slot:{name} -->` :148 = pack 模板槽位语义（**命名邻近** · 纪律入钉死契约 · 既有 `test_render_pack_slots_*`/`test_render_slots_appended` 用例零改动）
- 命名冲突扫：`grep -rn 'SLOT_REGISTRY\|wrap_slot\|assert_slots_declared\|SECURITY_INPUT_ISOLATION\|slots\.py\|input_isolation' app/ tests/ evals/ docs/_tech_graph/` = **零命中**
- pytest 基线真跑：`python -m pytest tests --collect-only -q` = **1278 collected**
- evals：`evals/security/` 目录**不存在**（新增义务）；金样先例 `evals/memory/preference_redline_v1.yaml` + `tests/eval/test_memory_preference_redline.py` 真读对齐
- B1 落盘 **11 行**（回归×9 · **改编×0** · 新增×1 · 迁移无×1 · 删除×0）；关键实证：tests 全仓**无 `format_evidence_block`/`retrieved_chunks`/`子任务结果` 裸格式断言**（grep 双零命中）→ 改编面为零钉死；用例计数 14 文件真跑（lc_evidence_chain 19 / lg_rag_multi 11 / memory_injection 23 / lg_rag_session_continuity 15 / prompt_packs 20 / prompt_assets 13 / prompt_assembly 5 / supervisor 面 45 / 等）
- HG-GRAPH-MODULES 真值核验：**真读** `docs/_tech_graph/l1/01_modules.md`——模块表已建置（bootstrap 签 2026-07-16 · 签录链完整至 :91）· `lg_rag` 行 :27（C2 裁定 `app/ops/prompts/**` 归属本行 → lg_rag→prompts 行内路径不构成新跨模块边）· `lc_evidence_chain` 行 :24（出边 rag/llm/db · **无 prompts** · 新边落此）· `memory` 行 :28（+prompts 备注级先例形态）→ 有图谱义务按实判（lc_evidence_chain 行 +prompts 备注级 + lg_rag 行备注 + 人签**新行留 00 代录位**随 30 交付落盘 · llm-layer-hardening/session-summary-fallback 先例）+ **偏离回炉补闸条款**钉死
- SPEC §1 锚点复核**零语义偏差**（nodes.py 两处行号微漂移如实记录属锚点精确化）

## 闸态

- `HG-TASK-DRAFT` = **落稿时待签**（00 验收代录/人签 · 本帽不签）
- `HG-AUDIT-R1` = **落稿时待签**（blocks 30 · 20 审后人签/授权代录）→ **30 拒开工**
- `HG-GRAPH-MODULES` = **approved（模块表已建置 · 本帽真读）** + 本 task 新签义务（lc_evidence_chain 行依赖出边 +prompts 备注级 + lg_rag 行备注 + 人签记录新行 00 代录位 · 随 30 交付落盘）；偏离（新增一级模块/路由/SSE 事件/改 Policy·visibility·规划语义）→ 回炉补闸
- `HG-PILOT-OPSDESK-GLAYER` = n/a

## lint

`npx spec-wave task lint --file docs/tasks/active/task_security_input_isolation.md` = **PASS**（exit 0 · 2026-09-22 真跑；初跑 E3（验收节结构）已修：人工闸勾选项置顶对齐 session-summary-fallback 先例形态后复跑 PASS）

## 下一棒

20-task-audit 书面审（对照 SPEC）→ HG-TASK-DRAFT + HG-AUDIT-R1 人签 → 30（`task/security-hardening` · 承 SPEC §8 序：D5 图谱 → D1 slots 机制 → D2 四面接线 → D3 开关+对拍 → D4 金样 · 执行层/检索/规划逻辑零改动）→ 40（off 对拍 + 变异检验三条 + 零请求双断言）→ CLOSE。后续 20/30/40 invoke 由各棒落盘本目录（命名对齐 `invoke_<yyyymmdd>_<hat>_<verb>_security_input_isolation.md`）。后续波（W2 检测 / W3 PII 出口脱敏 / W4 真沙箱）各自回 10-spec 起 task，不得回改本波语义。
