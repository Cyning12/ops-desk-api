# 20-task-audit R1 书面审：task_scenario_stage_rewire（draft v0.1 · 188 行）

> **hat_id**：20-task-audit（R1）
> **审查对象**：`docs/tasks/active/task_scenario_stage_rewire.md`（188 行 · 分支 `docs/task-scenario-stage-rewire` · commit `2751303` · 基于 master `51e75c9`）
> **对照**：`docs/spec/scenario-stage-rewire/SPEC-scenario-stage-rewire_v0.md`（v0.1 signed · 裁定分支 (a) 摘除）+ `docs/harness/reviews/spec_scenario-stage-rewire_audit_R1_20261019.md`（R1 conditional_pass → R2 pass · N1–N4 移交）
> **审查日期**：2026-10-20 · **审查人**：Harness 20-task-audit（书面审 · 不改 task 实质 · **不代签** HG-AUDIT-R1）
> **结论**：**conditional_pass** —— 内容面零阻塞（范围/非范围与 SPEC 裁定 (a) 逐条对拍一致 · 锚点 22 处复核：命中 20 / 漂移 2（均行号级 · task 已自声明「30 按实校正」）· 符号与代码内容 0 错误 · TC1–TC10 全可机断 · FP-1~FP-9 完备 · N1–N4 吸收真实且语义忠实）；流程闸 HG-AUDIT-R1=**pending**（blocks 30 · 未签不得 30）
> **实证复核范围**：task 全文 188 行逐行 · SPEC v0.1 全文 · 上游 R1/R2 审查文全文 · 源码实读 `app/ops/strategy/builder.py` 全文 180 行 · `app/ops/strategy/scenario.py` 全文 128 行 · `app/ops/strategy/intent.py:80-94` · `app/ops/lg_rag/sse_stream.py:55-99` · `app/ops/lg_rag/multi/nodes.py:1255-1279` · `app/ops/lg_rag/multi/graph.py:70-105` · `tests/test_strategy_scenario.py` 全文 395 行 · `tests/test_memory_injection_consumer.py:575-627` · `docs/guides/GUIDE_env_inventory_v1.md:28-42` · `docs/_tech_graph/l1/01_modules.md`（:35 lg_rag 行 + :63-128 闸登记表）· `docs/harness/invokes/by-task/scenario-stage-rewire/invoke_20261020_10_task_draft.md` 全文 · 全仓 grep：`_apply_scenario_stage` / `LG_RAG_VISIBILITY_SCENARIO_MODE`+ `ENV_SCENARIO_MODE` / `scenario_trim`+`scenario_mode`+`audit_scenario_stripped`(app/) / `intent_node`(app/) / `路径覆盖补记` · git 核验分支/HEAD/master（`2751303` → `51e75c9` 直连）

---

## 一、结论摘要

| 面 | 裁定 | 摘要 |
|---|---|---|
| **内容** | **conditional_pass**（零阻塞 · nits 留 30） | 摘除面/留尸面/登记面与 SPEC 裁定 (a) 逐条互锁；env 口径裁定自洽；验收全机断；TC8 三级探测蓝本实测在册 |
| **流程闸** | HG-AUDIT-R1=**pending**（blocks 30） | task 表诚实标记 pending（维护者已授权 00 代签 · 落闸动作在本审查之后）；本帽不代签；**30 以 task 表为准，pending 即拒开工** |

---

## 二、委托方点名六面核对

### 1. 范围/非范围一致性（task D 节 × SPEC 裁定 (a) 逐条对拍）· **PASS**

| 核对点 | task 位置 | 实证 | 裁定 |
|---|---|---|---|
| `builder.py:111-128` 函数本体删 | D1（task:57） | :111 `def _apply_scenario_stage` 起、:128 `return final` 止，逐行在册（off :119-120 · observe :124-126 · enforce :127-128） | ✅ |
| `builder.py:158` 唯一调用点删 | D1（task:57） | :158 `visible = _apply_scenario_stage(visible, state)` 逐字；全仓 grep app/ 内调用点唯一 | ✅ |
| `builder.py:17-20` scenario 三件 import 删 | D1（task:57） | 三件符号 `audit_scenario_stripped`/`scenario_mode`/`scenario_trim` 实测在 :18-20（import 语句实为 :17-21，:21 闭合括号） | ✅（区间 nit · 见 N1） |
| `multi/nodes.py:1267` 注释改写（仅注释行） | D1（task:58） | :1266-1269 注释段在册，:1267 逐字含「Builder 两阶段（基线→scenario_trim）收窄 allowlist」 | ✅ |
| 旧测处置（删六/改写四/保留 S1–S5+smoke/新增 env 失效） | D5（task:75-80） | 删六项 :189-256 六用例逐一定位（off :189-198 · invalid :201-204 · observe :207-215 · enforce :218-225 · 台账不记内容 :228-243 · enforce fallback :246-256）全部绑定 `_apply_scenario_stage`+env 三档；改写四项 :259-270/:273-300/:308-338/:341-378 逐一在册且处置方向正确（:308-338 改写为「intent 在场亦不裁」与摘除后语义一致）；保留面 S1–S5+畸形+Q2 实测 :75-181、smoke :386-395 | ✅（保留面区间漂移 · 见 N2） |
| `sse_stream.py:64` 死映射不动 × `intent.py:94` 留尸互锁 | D6（task:82-86） | `sse_stream.py:64` `"intent_node": "intent"` 逐字在册（:62-66 `_ROLE_ALIAS`）；`intent.py:94` `return {**bump, "intent": intent, "intent_fallback": fallback}` 逐字在册；D6「不动」与 SPEC §3「不顺手做其他 strategy 目录清理」及非范围五条（task:90-97）互锁，freeze `lg-rag-sse-v1` 不升 | ✅ |
| env 口径协调（SPEC「读取处删除」×「本体不删」） | D2（task:65）+ R1 思考轮（task:149） | **自洽**。实证：摘除后 `scenario_mode()` 全仓零生产调用方（grep：仅 `scenario.py:49` def + `builder.py:19` import + `builder.py:118` 调用，后两者均在摘除面内）；SPEC §3「❌ 删 scenario.py 模块文件/内部函数」与 D1「留」行互锁，故「读取处删除」的唯一自洽读法 = 生产消费侧读取调用删除（`builder.py:118` 随本体一并删），dormant 模块内 `os.environ.get`（:51）定义保留但无生产路径可达。task 在 D2 显式裁定并在 R1 residual_risks 诚实记录该张力；TC3 用「app/ 生产路径 grep 该 env 键仅命中 dormant scenario.py」把终态机断钉死 | ✅ |

### 2. 锚点实测（以 master `51e75c9` 为准 · 当前 HEAD `2751303` 文档线在其上）· **命中 20 / 漂移 2 / 错误 0**

命中（行号+符号+内容三重一致，共 20 处）：`builder.py:111-128` · `:118` · `:149` · `:155-157` · `:158` · `:161`（+`:165` agent_type=None）· `scenario.py` 128 行总数 · `scenario.py:38` · `:49-52`（`:51` os.environ.get）· `:55-96` · `:71-75` 恒短路 · `:99-128` · `intent.py:94` · `sse_stream.py:62-66`/`:64` · `multi/nodes.py:1267` · `multi/graph.py:82-83` · `tests/test_strategy_scenario.py` 395 行总数 + `:34-35` import + `:189-256` 删六项 + `:259-270`/`:273-300`/`:308-338`/`:341-378` 改写四项 + `:386-395` smoke · `tests/test_memory_injection_consumer.py:585-609` `_resolve_base` + `:612-627` 三路 diff 白名单 · `GUIDE_env_inventory_v1.md:35` env 行 · `01_modules.md:35` lg_rag 行「路径覆盖补记」strategy 段（闸登记表 :63-128 在册）· invoke 占位件真实存在（`invoke_20261020_10_task_draft.md` · N1–N4 索引与 task 行号对拍一致）。

漂移 2 处（均行号级 · 内容/符号零错误 · task D5/D1 已自声明「行号 30 按实校正」）→ 见 §三 N1/N2。

### 3. 验收可机断性 · **PASS**

TC1–TC10 逐条过机断性：TC1 grep 断言（摘除面四符号 + nodes.py 注释残留）✅；TC2 逐 id 对拍含顺序 ✅；TC3 env 5 值 × intent 2 态矩阵 + app/ 范围 grep ✅；TC4 import 存活 + S1–S5 保绿 + 注释字样断言 ✅；TC5 freeze 不升 + 白名单拦截 + 既有测试绿 ✅；TC6 图谱/env 台账字样断言 + `graph-compile` EXIT=0 ✅；TC7 D5 枚举逐项 + 枚举外保绿（K7）✅；TC9 invoke 引用清单存在性 + 残留登记字样 ✅；TC10 pytest/ruff exit code ✅。

**TC8 专项**：强制 `_resolve_base` 式三级探测——① `git rev-parse --verify {钉锚}^{commit}` → ② merge-base 双 ref（`GITHUB_BASE_REF` 或 master）退化 → ③ `pytest.skip` 带实测 ref 状态（绝不静默 pass/fail）；蓝本钉 `tests/test_memory_injection_consumer.py:585-609`——实读确认该函数在册且形态逐字对应（:594 钉锚 verify · :598-608 双 ref merge-base 退化 · :609 skip 带 tried 清单），`:612-627` 三路 diff（工作区/暂存/已提交）+ untracked 枚举口径亦在册。白名单枚举 8 项含 invoke 目录与 task 文件自身，闭合。✅

### 4. failure_paths 完备性（FP-1~FP-9）· **PASS**

委托方点名五面全覆盖：摘除连带破坏可见性（FP-1 逐值回归 + FP-8 隐藏依赖引用清单兜底）、SSE 残留/契约（FP-3 freeze 不升 + TC8 白名单）、图谱不同步（FP-4 备注断言 + graph-compile）、闸纪律（FP-7 GATE_VERIFY 拒开工）、基线退化（FP-9 三级探测可审计 skip）。另补 env 残留（FP-2）、dormant 存活（FP-5）、旧测处置越界（FP-6 · K7）。五列（触发/行为/可重试/用户可见）齐全，均 CI 拦截级、用户不可见，定性准确。

### 5. 闸表合规 · **PASS**

| 闸 | task 表记 | 实证 | 裁定 |
|---|---|---|---|
| HG-SPEC-SIGNOFF | approved（2026-10-19 维护者）· blocks 20 | SPEC :3/:34 签收记录 + 裁定分支 (a) 摘除在册 | ✅ |
| HG-AUDIT-R1 | **pending** · blocks 30 | task:38 诚实标记「起草时一律 pending · 未签不得 30」；维护者授权 00 代签、落闸在本审查之后的编排（task:30）与仓纪律一致 | ✅（维持 pending · 本帽不代签） |
| HG-GRAPH-MODULES | approved（在册）· blocks 30 | `01_modules.md:63-128` 闸登记表序列完整；`graph_change_layer=none` 口径成立——D4 仅为 `:35` lg_rag 行既有「路径覆盖补记」strategy 段备注追加，不新行/不新边/不增 implementedBy，与闸登记表中数十条同形态「行备注 · 不新增一级模块」先例一致；task:39 写明「30 实判越出 → 回炉补签」兜底 | ✅ |

### 6. N1–N4 吸收核验 · **PASS（四项落点真实存在且语义忠实）**

| 移交项 | 上游原文要旨 | task 落点 | 裁定 |
|---|---|---|---|
| N1（图谱无 strategy 独立行） | 备注应落 lg_rag 行「路径覆盖补记」段而非新行 | task:20-22（graph_delta/graph_delta_note）+ task:71-73（D4）：lg_rag 行 strategy 段备注追加、不新行、30 越出回炉补签 | ✅ 语义忠实 |
| N2（旧测绑定被删函数） | 删 env 三档/台账用例 · 保留 S1–S5 纯函数与 TC6 短路断言（改造为 Builder 直出逐值回归） | task:75-80（D5 删六/改写四/保留/新增）+ task:121（TC7 机断） | ✅ 语义忠实（保留面区间漂移见 N2 nit） |
| N3（sse_stream.py:64 死映射） | 不动 · 引用清单登记「已知残留 · 不动」 | task:82-86（D6）+ task:123（TC9） | ✅ 语义忠实 |
| N4（invoke 目录缺失） | 00 起草时补 invoke 文件 | task:27（invoke_retention_profile）+ `docs/harness/invokes/by-task/scenario-stage-rewire/invoke_20261020_10_task_draft.md` 实存（含 N1–N4 索引 + 锚点实录 · 与本次实测一致） | ✅ 真实落盘 |

附：行为变更类 task 的 K7 checklist（旧测 grep 影响面）——D5 即显式枚举 + TC7 机断，满足。

---

## 三、非阻塞 nits（留 30 按实处理 · 不阻塞人签）

| ID | 位置 | 内容 | 30 处置建议 |
|---|---|---|---|
| N1 | task:57（D1）/ 依赖节 task:130 | import 区间写「:17-20」，实测 import 语句为 `builder.py:17-21`（三件符号在 :18-20，:21 为闭合 `)`）；删除时应整句 :17-21 移除 | 30 摘除时按整句删（task 已声明「行号 30 按实校正」） |
| N2 | task:79（D5 保留面）/ invoke:34 | 「S1–S5 用例（:76-169）」区间两端漂移：实测 scenario_trim 纯函数保留面为 `tests/test_strategy_scenario.py:75-181`——test_s1 起于 :75（:76-169 漏首行 def）；:143-164 畸形 intent 三例与 :167-181 `test_is_composite_and_summary_not_trim_keys` 同属纯函数保留面，:169 右端切入该用例中部 | 30 按实校正为 :75-181；保留语义不变（全部为 scenario_trim 纯函数用例） |
| N3 | task D5（task:75-80）未列 | `tests/test_strategy_scenario.py:1-11` 文件头 docstring 仍述「三档模式：off 零 diff 零日志 · observe would_strip 不生效 · enforce 生效」「Builder 集成 + supervisor 交集输入=场景维后有效可见集」等被删/被改写行为，摘除后失真 | 30 顺手同步改写该 docstring（在 TC8 白名单 `tests/test_strategy_scenario.py` 内 · 不越面） |

---

## 四、阻塞项

**无内容阻塞。**

---

## 五、回填清单

零阻塞故无退回回填；三项 nits 已由 task 既有「行号 30 按实校正」条款覆盖或由 30 顺手处理，无需退回 10-task 修订。

---

## 维护者签闸（20 后 · 30 前）

- [ ] 已读 R1 审查结论（conditional_pass · 零内容阻塞 · nits×3 留 30）
- [ ] 在 task 人工闸表将 HG-AUDIT-R1 改为 approved（维护者或经授权的 00 代签 · 日期）
- [ ] commit task 文档或确认已签
- [ ] 再下发 Harness 30 Prompt

30 Agent 将以 task 表为准；pending 时必须拒开工（见 TEMPLATE_30_gate_stop.md）。

---

## 修订记录

| 日期 | 摘要 |
|---|---|
| 2026-10-20 | R1：六面核对全过（范围对拍/锚点实测 20 命中 2 漂移 0 错误/TC1–TC10 全机断含 TC8 三级探测蓝本实测/FP-1~FP-9 完备/闸表合规/N1–N4 吸收忠实）；**conditional_pass** · 零内容阻塞 · nits×3（import 区间 :17-21 · 保留面 :75-181 · 测试 docstring :1-11 同步）留 30 · HG-AUDIT-R1 维持 pending 待人签 · 本帽不代签 |
