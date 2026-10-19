# 20-spec-audit R1 书面审：SPEC-supervisor-first-fail-closed v0

> **hat_id**：20-spec-audit（R1 · 轻量路径：10-spec 思考轮 R0–R5 已内联 SPEC §8，单轮 R1）
> **审查对象**：`docs/spec/supervisor-first-fail-closed/SPEC-supervisor-first-fail-closed_v0.md`（draft · 185 行 · HG-SPEC-SIGNOFF=pending）
> **审查日期**：2026-10-19 · **审查人**：Harness 20-spec-audit（书面审 · 不改 SPEC 实质 · **不代签** HG-SPEC-SIGNOFF）
> **结论**：**conditional_pass（PASS-WITH-NITS）** · 三大重点全部核对通过 · 阻塞项 0 · 非阻塞 N1–N4 移交 00 起草 task 时吸收 · **建议维护者可签 HG-SPEC-SIGNOFF**
> **实证复核范围**：SPEC 全文 185 行逐行 · 源码实读 `app/ops/lg_rag/multi/graph.py:80-106`（图边）· `app/ops/strategy/intent.py:52-94`（intent_fallback）· `app/ops/lg_rag/multi/nodes.py:1070-1230`（supervisor_node fallback/沿用后缀分叉）· `app/ops/strategy/builder.py:111-190`（scenario 二阶段 + allowlist）· `app/ops/strategy/scenario.py:40-91`（S1–S5 规则表）· freeze 先例 grep（`task_lg_rag_sse_run_worker.md` / `task_lg_rag_sse_disconnect_completion.md` / 05 §4.2 回写纪律）· `LG_RAG_SUPERVISOR_PLAN_ON_FAIL` 全仓 grep（仅 SPEC 命中 = 新 env）

## 一、三大重点核对（委托方点名）

### 1. 首次规划失败 vs 重规划沿用后缀：分叉清楚 · **PASS**

| 核对点 | SPEC 位置 | 实证 |
|---|---|---|
| 判据同一变量 | D2 触发行「首次规划（**无 locked 前缀**）」· 重规划例外行「**已有 locked 前缀**时沿用未解决后缀」 | nodes.py:1094 `locked = _locked_prefix(state)`；:1157-1193 fallback 分叉正是 `if locked:` → `_carry_plan`（沿用后缀，:1170-1189）/ `else` → 单 rag `t1`（:1193）。SPEC 判据与实现**同构同变量** |
| 两分支语义互斥 | D2：首次失败「**不**写入单 rag 子任务；图收口为失败」；例外行「这不是新规划成功，也不是首次失败的单 rag 兜底」 | 现网 :1181-1186 沿用后缀分支仍标 `supervisor_fallback=True` + `replan_suffix_only=True`（观测不冒充成功）；SPEC 保留该分支语义、只改无 locked 分支 |
| failure_paths 成对 | FP-1/FP-2（首次 → error）vs FP-5（重规划 → 沿用后缀 · 不发 `supervisor_plan` 错误终态 · 不收缩成只剩前缀） | FP-5「不收缩成只剩前缀」与 nodes.py:1160-1166 注释「绝不把计划收缩成只剩前缀」逐字同源 |
| 非范围兜底 | §3 末条「❌ 重规划沿用后缀改成也硬失败（本波保留现网该分支）」 | 双向锁死：既防「重规划被误伤成硬失败」，也防「首次失败继续静默单 rag」 |

**裁定**：分叉判据（locked 前缀有无）、两分支各自语义、FP 成对、非范围互锁，四层闭合。唯一残留边缘形态见 N2（locked 空 + preserved 非空），非阻塞。

### 2. 无 intent 时 scenario 不得按 S1 清空 · **PASS**（附 N1）

代码实证逐规则推演（scenario.py:70-91 · builder.py:121-122 只读 `state.intent` + `state.intent_fallback` 两键）：

| 规则 | 触发条件 | intent_node 退出主路径后（两键缺省） |
|---|---|---|
| S1 | `intent_fallback=True` → 空集 | `bool(state.get("intent_fallback"))` = False → **不触发** ✅ |
| S2 | `needs_tool=False` → 空集 | mapping={} → needs_tool=None ≠ False → **不触发** ✅ |
| S3 | domain=unknown **且** needs_tool=True → 空集 | needs_tool=None ≠ True → **不触发** ✅ |
| S4 | risk_hint 缺/畸形**视同 high** → 只留 low | 缺省 → 视同 high → **enforce 模式下会收紧**（非空集但裁掉 medium）⚠️ → N1 |

SPEC 侧闭合件：D3 状态行「主路径**不写** `intent` / 不把缺省当成 `intent_fallback=true`」+ scenario 行「无本轮 intent 时**短路、不裁**（等价本轮不做 S1–S5）· **禁止**把「没跑意图」映射成 S1 空集」+ FP-6 + 验收条「allowlist 与『只跑基线 ∩ candidates』一致，不被 S1 清空」。注意 scenario 默认 `off`（scenario.py:49-52 零 diff），S4 残留面仅在 `LG_RAG_VISIBILITY_SCENARIO_MODE=enforce` 下存在——但 SPEC 的「短路不裁（S1–S5）」措辞已正确覆盖该面，验收条「与只跑基线∩candidates一致」可机断（S4 收紧后 allowlist ≠ 基线∩candidates 即红）。

**裁定**：S1 清空路径被 D3+FP-6+验收三层钉死；S4 残留面被 D3 正文措辞覆盖但 FP-6/验收只点名 S1「裁空」——立 N1（措辞精确化，移交 task）。

### 3. 不新增 SSE event_type · **PASS**

- SPEC 三处钉死：元信息 freeze_id 行「复用既有 `error` 事件类型，只新增 stage 词 `supervisor_plan`」· §3 非范围「❌ 改 SSE 路径、新增 `event_type`、改鉴权」· 验收条「不新增 SSE `event_type`」。
- 先例核查（同 freeze 内扩 `error.stage` 字面量合法）：run-worker 已产 `error{stage:lg_rag.worker_failed}`（01_modules.md 在册）；`task_lg_rag_sse_disconnect_completion.md:29` freeze 行「收尾语义优先复用既有 `error` / `done`+status 扩展键 · **禁** silent 新 `event_type`」；`task_lg_rag_sse_run_worker.md:31`「可扩 `error.stage` / 可选 `done.status` 字面量**并回写 05**」。
- SPEC freeze_id 行的 hedge「`error.stage=supervisor_plan` 若被 freeze 词表锁死，则本波先改 SPEC 再动码」审慎可接受——先例口径是「同 freeze 扩 stage 字面量 + 回写 05 §4.2」，不构成升 freeze。
- 图谱回写义务：graph_change_layer=none 预期 + 「若 30 新增 SSE `event_type` → 回本 SPEC 判 G-L* 并升 freeze」留好了升级回路。回写 05 §4.2 的具体义务 SPEC 未显式挂（§7 只说「文档写明」）→ N3。

## 二、结构核对表（范围 / 非范围 / 验收 / failure_paths / 思考轮）

| 项 | 裁定 | 摘要 |
|---|---|---|
| 现状锚点真实性 | ✅ | graph.py:96-98 `START → intent_node → strategy_builder → supervisor` 逐行在册；intent.py:94 `return {**bump, "intent": intent, "intent_fallback": fallback}`；nodes.py:1193 无 locked 失败 → `[{"id": "t1", "type": "rag", "input": query}]` 单 rag；builder.py:147 `needs_tool is False` → 空 allowlist。四处锚点全部实证，无虚构 |
| 范围 D1/D2/D3 内聚 | ✅ | 「三块一起做否则不闭合」论证成立：D1 去前置意图节点（graph.py:86,96-97 两处）、D2 改 :1193 单 rag 分支为 error、D3 防 Builder/scenario 因 intent 缺省误裁——任缺一块即假成功或误清空 |
| 非范围与范围互斥 | ✅ | §3 八条与 D1–D3 无重叠；「不切 mode=router」与 D2「明确不做」、FP-7「router/basic 逐行为一致」三方互锁；「不删 IntentV1 schema / intent_node 可留包内」与 D3「代码去向」行一致（graph 编译路径不挂 ≠ 删模块） |
| 验收可机断 | ✅ | 七条全部可假 LLM/抛错注入单测（R4 已申明不必打真模型）；图边断言、SSE error 帧 stage 断言、env 两档、无 intent allowlist 对拍、router/basic 回归，无一条依赖人工判断 |
| failure_paths 充分 | ✅ | FP-1~FP-8 覆盖：LLM 异常 / 解析失败 / env 三档（single_rag / 非法回退 error）/ 重规划例外 / 无 intent / 对照轨零 diff / Policy Host-only 回归。env `LG_RAG_SUPERVISOR_PLAN_ON_FAIL` 全仓 grep 仅 SPEC 命中 = 新 env 无冲突 |
| R0–R5 思考轮闭合 | ✅ | §8 表 + 各轮小节齐全；`actual_last_round=R5`；R5 reason=「人签未发生」、residual=`HG-SPEC-SIGNOFF=pending`——诚实标记 draft 不可当已签收；R2 方案对比（§4 A/B/C/D 四案三弃一采，弃案理由机制性非敷衍）；R3 安全面（不扩权 / 不读模型放行字段 / high 可见性不动）与 FP-8 互锁 |
| 人工闸纪律 | ✅ | HG-SPEC-SIGNOFF=pending 在表；本帽不代签；SPEC 自身亦声明「签前不出 task / 不改码」 |

## 三、非阻塞 nits（移交 00 起草 task 吸收；**不**退回 10-spec · 不改 SPEC 实质）

| ID | 位置 | 内容 |
|---|---|---|
| N1 | FP-6 / 验收条第 5 条 | 「裁空」措辞只点名 S1/S2/S3 空集路径；代码实证 scenario.py:81-90 **缺省 risk_hint 视同 high**（S4），enforce 模式下「没跑意图」会触发 S4 收紧（只留 low，非空集）。D3 正文「等价本轮不做 S1–S5」已覆盖，验收条「与只跑基线∩candidates一致」隐含可机断——建议 task 验收把 S4 显式写入断言（无 intent 轮：scenario_trim 短路，`visible` 进 = `visible` 出逐 id 对拍） |
| N2 | D2 触发行 / FP-5 | 分叉判据「locked 前缀有无」与 nodes.py:1158 `if locked:` 一致；但 hitl-n1 形态（**locked 空 + preserved 非空**，hitl 批准单步写）的重规划失败按现网代码落 `else` 单 rag 分支，本波将被归入「首次失败 → error」。SPEC 未显式讨论该形态归属。边缘形态，建议 00/task 钉死：接受为 error（失败可见，与 SPEC 精神一致）或将判据扩为 `locked or preserved` |
| N3 | freeze_id 行 / 验收 | 承 run-worker / disconnect-completion 先例：同 freeze 扩 `error.stage` 字面量须**回写 05 §4.2 词表**。SPEC §7 只说「文档写明」，未挂具体回写义务。建议 task 验收条显式挂「回写 05 §4.2 `error.stage` 词表 + 01_modules.md 备注」 |
| N4 | invoke_slug | SPEC 声明 `invoke_slug=supervisor-first-fail-closed`，但 `docs/harness/invokes/by-task/supervisor-first-fail-closed/` 当前为空（SPEC 阶段思考轮已内联 §8，轻量路径可接受）。按仓纪律 pre-30 invoke 缺失拒改码——移交 00 起草 task 时同步补 invoke 文件 |

## 四、HG-SPEC-SIGNOFF 建议

**建议维护者可签 HG-SPEC-SIGNOFF**（conditional_pass：nits 不阻塞人签，移交 task 阶段吸收）。本帽**不代签**；人签前维持：不出 task / 不改码 / 30 拒开工。

## 五、下一棒

人签（或维护者授权）→ **00 起草 task**（slug=`supervisor-first-fail-closed`，分支 `task/supervisor-first-fail-closed`）：
1. 吸收 N1–N4 进 task 验收/failure_paths；
2. 补 `docs/harness/invokes/by-task/supervisor-first-fail-closed/` invoke；
3. task 草稿 → 20-task-audit → HG-AUDIT-R1 人签 → 30。

---

## 修订记录

| 日期 | 摘要 |
|------|------|
| 2026-10-19 | R1：三大重点（首次/重规划分叉 · 无 intent 不 S1 清空 · 不新增 event_type）全部 PASS；conditional_pass · N1–N4 移交 task；建议可签 HG-SPEC-SIGNOFF（不代签） |
