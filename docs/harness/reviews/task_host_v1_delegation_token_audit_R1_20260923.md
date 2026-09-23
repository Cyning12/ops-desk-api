# 审查文：task_host_v1_delegation_token · 20-task-audit R1（2026-09-23）

> **hat_id**：20-task-audit · **轮次**：R1 · **审查对象**：`docs/tasks/active/task_host_v1_delegation_token.md`（draft · 277 行）
> **对照真值**：SPEC `docs/spec/host-v1-delegation-token/SPEC-host-v1-delegation-token_v0.md`（signed · 231 行）· 种子 `08_host_v1_wave_spec_outlines_v0.md` §1 · 规划 `07_host_v1_landing_plan_v0.md`（双 signed）
> **方法**：全部真读真跑——task/SPEC/种子/规划逐行读；代码锚点 5 处亲读；grep 亲跑；pytest collect 亲跑；图谱签录链亲读

---

## 结论摘要

| 维度 | 结论 |
|------|------|
| **内容**（范围/非范围/验收/failure_paths/钉死契约/思考轮/B1/锚点） | **PASS-WITH-NITS**（零阻塞项 · 5 条非阻塞修正/建议 · 见下） |
| **流程闸** HG-AUDIT-R1 | **pending（如实）** → 30 拒开工维持；本帽不签发，由维护者授权 00 代录 |

**总结论：PASS-WITH-NITS** —— task 与 signed SPEC 实质差异为零，锚点与数据全部经得起复核（仅 1 处先例行号错误、1 处计数不符，均为文档精度问题而非语义偏移）；无阻塞项，**不退回 10-task**；修正建议可由 00 在签 HG-AUDIT-R1 前一并微修或留痕豁免。

---

## 一、逐面核对（证据带行号）

### 面 1 · 范围 / 非范围 / 验收 / failure_paths 与 SPEC 一致性 ✅

| 核对项 | task 证据 | SPEC 证据 | 结论 |
|--------|-----------|-----------|------|
| 范围 D1–D6 | task :105-110（六块必做 · 实现序 D1→D5→D2→D3→D4→D6） | SPEC §2 :54-118（D1–D6）· SPEC :106（有效 scope 作 D2 签发上界 → 实现序合理） | 一致 |
| 竖切不拆论证 | task :112（不配验签门=无强制面等三句） | 种子 08 §1.2 :41-46（D 块为展开单位） | 一致 · 论证成立 |
| 非范围 | task :116 | SPEC §3 :124-130（七条 ❌） | SPEC 七条全收；task 增「历史文档回改」为 Harness 标准项，无越界 |
| failure_paths | task :124-135（12 行：SPEC FP-1~FP-7 + 过程三 + 额外二） | SPEC §5 :170-176（FP-1~FP-7） | FP 七条逐条翻四列且语义一致（FP-1 禁续期 task :127 ↔ SPEC :170；FP-2 墙钟 task :128 ↔ SPEC :171；FP-5 进程窗口如实定性 task :129 ↔ SPEC :174「不作持久化承诺」） |
| 验收 | task :143-174（19 条 + 变异检验 3 条） | SPEC §6 :182-190（9 条） | SPEC §6-1~8 全部映射入 19 条（详见面 3）；§6-9 PR/CI 由 orchestration 行 task :32 承载（见建议 N4） |
| 与种子方向偏离 | task 全文 | 种子 08 §1 :31-68 · 规划 07 §3 :72（V1-A 字段级起点：六字段 · 签发审批 · subtask_id 绑定 · requested_scope） | **零偏离**：种子三开放裁定 Q1/Q2/Q3 已由 SPEC 作答（SPEC §4），task 未重开辩论 |

### 面 2 · R0–R5 思考轮控制 ✅（1 处计数 nit）

- 控制表 task :232-239：R0–R5 六轮齐全 · early_stop 全 no · residual_risks 在 R3 如实携带两条（进程重启防重放窗口 · 灰度观察期报告质量）并贯穿至 R5/:241。
- 回填小节 :243-265 与 :241 actual_last_round=R5 闭合；无跳轮、无早停。
- R2 :236 正确地「继承 SPEC §4 三组裁定不重演」（Q1 HMAC 弃 Ed25519 · Q2 分级弃全 HITL/全自动 · Q3 不新模块弃独立模块），符合种子 08 §6-2「开放裁定不许带入 task」。
- **N2（nit）**：R3 结论行 :237 与 R3 小节 :257 称「failure_paths **10 条**（FP-1~7+过程三）」，但正文 :124-135 实为 **12 行**（7 SPEC + 3 过程 + 2 额外面：模型伪造 :134 · 审批误判 :135）。正文行本身有价值且与 SPEC Host 权威/Q2 一致，是计数行不准而非内容缺漏。

### 面 3 · 验收 19 条可执行断言（防空真）✅

逐条清点 task :141-174：人工闸 1（:141）+ D1×4（:145-148）+ D2×4（:152-155）+ D3×4（:159-162）+ D5×3（:166-168）+ D6×3（:172-174）= **19 条**，与 R4 :238 自述一致 ✅。

- 全部否定性/可机验形态：篡改必拒（:146 自带「缺本条则验签通过是假通过」防空真注解）· 六类拒绝逐类（:159）· 旧 nonce 拒 R-d（:154）· 三档模式（:161）· 声明∩裁剪矩阵（:166-168）· 迁移 diff 为空断言（:172）· diff 白名单（:174 · 超 SPEC 的加码项，方向正确）。
- **变异检验三条** :178-180（签名/一次性/审计各配「临时破坏→断言必挂→恢复全绿」），满足「不验收空真」硬规则。
- off 零 diff 的证明路径诚实：:161「既有用例零改动全绿即证」+ 基线 1368 真跑（见面 5）。

### 面 4 · B1 旧测影响面处置三态 ✅（1 处分组 nit）

- 三态齐全：回归×6 组（:188-193）· 新增×1（:194 两个新测试文件）· 迁移无×1（:195）。
- **亲跑复核扫描口径**：`ls tests/ | grep -iE 'capab|lg_rag|strategy|subtask|delegation|gateway|policy|hitl|builder|supervisor'` → **32 文件**（2026-09-23 本帽真跑），与 task :184 自述一致；8 组归并的并集覆盖全 32 文件无缺漏。
- **N5（nit）**：组 5（:192 · 含 `test_lg_rag_sse_hitl.py`）与组 6（:193 · `test_lg_rag_sse_*.py（5 文件）` glob 含同文件）双计一文件；处置同为「回归零改动」无冲突，建议分组注记去重。

### 面 5 · 钉死契约与 SPEC §2/§4/§5 锁死一致 ✅

逐项比对 task :86-99 ↔ SPEC：

| 钉死项 | task | SPEC | 结论 |
|--------|------|------|------|
| 令牌 12 字段 frozen dataclass | :86 | SPEC D1 表 :60-69 | 一致（字段名/类型/不可变/可序列化全对齐） |
| Q1 HMAC-SHA256 · canonical JSON · env 密钥禁硬编码 · enforce 缺密钥拒签发 · kid 预留 | :87 | SPEC :140-143 · :78 | 一致 |
| Q2 自动放行三条件（scope 内 ∩ 全只读 ∩ 非沙箱 cli）· 其余 HITL 复用既有回路留痕 ops_hitl_requests | :89 | SPEC :149-153 · :76 | 一致 |
| Q3 不新增一级模块 · 图谱两行备注 · 不增 implementedBy | :98 · 元信息 :22 | SPEC :159-162 | 一致 |
| 验签门插 lookup 之前 · 仅 `_delegation_required` 口径 · 六类拒绝 ok=False 不落回执 | :90 | SPEC :82-84 | 一致 |
| TTL 墙钟默认 600 非法回退 · HITL 挂起不延寿命 | :91 | SPEC :171 | 一致 |
| one_shot 默认 True · 禁续期 · 重签发 supersede | :92 · :88 | SPEC :170 · :77 | 一致 |
| 参数约束 v1 三子集 · 未知类型拒签发 | :93 | SPEC :67 | 一致 |
| 主体绑定四元组 · 模型产出不入身份 | :94 | SPEC :68 | 一致 |
| requested_scope 只收窄不放宽 · MAX_SCOPE_IDS=64 · 未声明兼容现状 | :95 | SPEC :104-107 · :176 | 一致 |
| 三档模式 off 默认 · observe would_block · 非法值回退 off | :96 | SPEC :96 | 一致 |
| 审计五类动作 · 记动作不记内容 · 不落新表 | :97 | SPEC :100 | 一致 |

### 面 6 · 闸表四行诚实 ✅

| 闸 | task 表 :39-42 | 本帽复核 | 结论 |
|----|----------------|----------|------|
| HG-TASK-DRAFT approved（00 代录） | :39 维护者令原话留痕 | invoke `invoke_20260923_00_host-v1-landing.md` :5-6 原话一致，授权面明列 HG-TASK-DRAFT | 诚实 |
| **HG-AUDIT-R1 pending（blocks 30）** | :40「pending → 30 拒开工」 | 本审查文落盘前确为 pending；本帽不代签 | **诚实 · 必须维持 pending 至维护者授权 00 代录** |
| HG-GRAPH-MODULES approved | :41 | 亲读 `docs/_tech_graph/l1/01_modules.md`：模块表已建置；capability 行 :34 · lg_rag 行 :35 在表；签录链完整至 2026-09-23 主线裁定行（末行 task_agent_host_framework_alignment）；Q3 不新增一级模块 → 本 task 图谱义务=两行备注+人签新行随 30 落盘，定性准确 | 诚实 |
| HG-PILOT-OPSDESK-GLAYER n/a | :42 | 本 task 不涉物理分层试点改码 | 诚实 |

---

## 二、代码锚点抽验（B1 抽 5 · 全部亲读）+ 命名冲突亲跑

| # | 锚点 | 复核结果 |
|---|------|----------|
| 1 | `gateway.py:258` `_prepare_call` | ✅ 亲读 :258-319：函数起于 258；闸链序 lookup（:268 `_registry.get`）→ enabled（:280）→ Policy（:297 `check_invoke`）→ 后续熔断/配额/args_schema，与 task :67 描述一致；「验签门插 lookup 之前」落点真实可执行 |
| 2 | `_blocked_result` :219-255 | ✅ 亲读：docstring :230-234 明言「**不落回执**……被闸门拦下的调用没有执行」，被拒不留回执先例属实 |
| 3 | `graph.py:94-102` 分发 | ✅ 亲读：:94 `add_node("subtask_join", _join_subtasks)` · :99 supervisor→subtask_join · :100 `add_conditional_edges("subtask_join", route_next_subtask, ...)` · :101-102 工人回边；签发注入位真实 |
| 4 | `nodes.py:1050-1091` tool_exec ctx | ✅ 亲读：`tool_exec_node` 起于 :1050；cap_ctx 含 `tenant_id`（:1081-1083 ContextVar 先例）+ `subtask_id` + `run_id`（:1088）；`capability_ainvoke(tool_name, call_args, ctx=cap_ctx)` 在 :1091，与 task :69 一致 |
| 5 | `schemas/subtasks.py` | ✅ 亲读全文 38 行：`SubtasksPlan` 在 :29-38 · `extra="ignore"` :36 · cap 外坏项不整单作废纪律 :32-33 docstring 在案；现无 `requested_scope` 字段，新增落点成立 |
| 6 | `builder.py:38-59` | ✅ 亲读：`build_allowlist_from_candidates` :38-59 · stripped 审计 :54-58 在案；「声明∩裁剪」升级复用同函数形态可行 |
| 7 | 先例 step_contract | ✅ 亲读：零 LLM 零 IO :15 · MAX_FIELDS :23 · `_env_int` 非法回退 :33-42，全部属实 |
| 8 | **命名冲突扫** | ✅ 亲跑 grep `delegation|requested_scope|DelegationToken` 于 `app/` 与 `tests/`：**零命中**；`LG_RAG_DELEGATION` 于 `app/` 零命中——task :76 自述属实 |
| 9 | 测试基线 | ✅ 亲跑 `.venv/bin/python -m pytest tests --collect-only -q` → **1368 collected**，与 task :77 自述一致 |
| 10 | 当前分支 | ✅ `master`；task :245 如实声明「30 阶段必须切 task/host-v1-delegation-token」，无隐瞒 |

**⚠ 唯一锚点错误（N1）**：task :75 与 :210 引「承 result_contract :557-559 先例」——亲验 `app/ops/capability/result_contract.py` **全文仅 155 行**，:557-559 不存在。所述先例（不新造码 · 用 detail 区分）真实存在于 `result_contract.py:23/:44/:61-62` 与 `errors.py:102-103`（`format_error(code, detail)` · 词表「七个、不增」errors.py:4 已亲验属实）。属行号笔误而非先例虚构，但 30 必读列表带错行号会误导执行帽，须修正。

---

## 三、阻塞项清单

**无。**（FAIL 级别事项：零）

## 四、非阻塞修正 / 建议清单（PASS-WITH-NITS 的 NITS）

| # | 级别 | 内容 | 建议处置 |
|---|------|------|----------|
| N1 | 修正建议 | 先例锚点行号错误：task :75/:210「result_contract :557-559」不存在（文件仅 155 行）；真实先例 = result_contract.py:23/:44/:61-62 + errors.py:102-103 | 00 签闸前微修两处行号（不改语义），或在 task 修订记录留痕豁免 |
| N2 | 修正建议 | 思考轮 R3 行（:237）与 R3 小节（:257）称「failure_paths 10 条」，正文实为 12 行（7 SPEC + 3 过程 + 2 额外面 :134-135） | 计数行改为「12 条（7+3+2）」并点名两个额外面 |
| N3 | 建议 | SPEC FP-3（:172）「单测附朴素计时 smoke（<1ms/次量级声明 · 不设硬 CI 阈值）」未落入 task 验收或 failure 行（task :130 只复述性能裁定） | 建议在 D1 或 D3 验收补一条弱断言（不计 19 条可作为注记），或注明承 SPEC 不设硬阈值故并入新测试文件 |
| N4 | 建议 | SPEC §6-9「PR 到 master 经 CI 绿后 merge」未列验收勾选（仅 orchestration :32 承载）；SPEC §2 D6-8「SSE 零新事件类型断言」无独立勾选（由 B1 组 6 回归 + off 零 diff :161 隐含覆盖） | 建议在 D6 补注「PR+CI 绿+merge 承 orchestration 流程项 · SSE 零新事件由 freeze 守护回归覆盖」，显式化映射 |
| N5 | 提示 | B1 组 5/组 6 双计 `test_lg_rag_sse_hitl.py`（组 6 glob 含之）；并集仍覆盖全 32 文件无缺漏、处置一致 | 分组注记去重即可 |

以上五条均**不触及 SPEC 锁死语义**，不构成退回 10-task 的实质问题；若维护者/00 选择豁免，须在签闸记录留痕。

---

## 五、纪律自查

- 本帽未改 task/SPEC 实质内容 · 未动 `app/` 代码 · 未签发任何 human_gate。
- HG-AUDIT-R1 在 task 闸表仍 **pending**（task :40），本审查文不附 30 Prompt。

## 维护者签闸（20 后 · 30 前）

- [ ] 已读 R1 审查结论（PASS-WITH-NITS · 零阻塞 · N1–N5 五条微修/豁免留痕）
- [ ] 在 task 人工闸表将 HG-AUDIT-R1 改为 approved（维护者授权 · 00 代录 · 日期 + 原话留痕）
- [ ] commit task 文档或确认已签
- [ ] 再下发 Harness 30 Prompt（30 由 00 委派子 Agent · 分支 `task/host-v1-delegation-token` · 当前在 master 须先切分支）

30 Agent 将以 task 表为准；pending 时必须拒开工（见 TEMPLATE_30_gate_stop.md）。

---

## 修订记录

| 日期 | 摘要 |
|------|------|
| 2026-09-23 | 20-task-audit R1：六面全核（一致性/思考轮/验收可执行/B1 三态/钉死契约/闸表诚实）+ 锚点 5+5 亲读亲跑（grep 零命中 · pytest 1368 · 图谱签录链至 2026-09-23）→ **PASS-WITH-NITS**（零阻塞 · N1–N5）· HG-AUDIT-R1 维持 pending |
